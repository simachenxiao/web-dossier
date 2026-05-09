from dataclasses import dataclass
from hashlib import sha256

from sqlalchemy.orm import Session

from app.models import Draft, Task
from app.rules.material_element_mapping import resolve_material_elements

TASK_KEYWORDS = ("补齐", "创建", "任务", "制作", "开具", "上传")
MATERIAL_RESULT_KEYWORDS = ("上传", "回写", "完成", "生成")
FACT_UPDATE_KEYWORDS = ("违法事实", "伤势", "伤情", "处罚", "认错", "认罚", "到案")
CONFLICT_KEYWORDS = ("矛盾", "不一致", "冲突")
APPROVAL_KEYWORDS = ("审批", "通过", "驳回")

KNOWN_MATERIALS = (
    "医院诊断证明",
    "诊断证明结论告知书",
    "伤情检查结论",
    "询问笔录",
    "证据保全决定书",
    "证据保全清单",
    "证据保全审批表",
    "传唤证",
    "行政处罚决定书",
    "行政处罚告知笔录",
    "行政处罚审批表",
    "发还清单",
    "自书材料",
    "认罪认罚材料",
    "前科核验",
)


@dataclass(frozen=True)
class EventAnalysis:
    event_type: str
    normalized_text: str
    related_person: str | None = None
    related_material_title: str | None = None
    metadata: dict | None = None


class ConversationTaskAI:
    def normalize_message(self, text: str) -> str:
        return " ".join(text.split())

    def analyze(self, text: str) -> EventAnalysis:
        normalized = self.normalize_message(text)
        return EventAnalysis(
            event_type=self.classify(normalized),
            normalized_text=normalized,
            related_person=self.extract_person(normalized),
            related_material_title=self.extract_material_title(normalized),
            metadata={"matched_keywords": self.matched_keywords(normalized)},
        )

    def classify(self, text: str) -> str:
        if any(keyword in text for keyword in CONFLICT_KEYWORDS):
            return "conflict_clue"
        if self.is_task_intent(text):
            return "task_intent"
        if any(keyword in text for keyword in APPROVAL_KEYWORDS):
            return "approval_result"
        if any(keyword in text for keyword in MATERIAL_RESULT_KEYWORDS):
            return "material_result"
        return "message"

    def is_task_intent(self, text: str) -> bool:
        intent_markers = ("请", "需要", "创建", "任务", "补齐", "制作", "开具")
        return any(marker in text for marker in intent_markers) and any(keyword in text for keyword in TASK_KEYWORDS)

    def generate_drafts(self, db: Session, event) -> list[Draft]:
        generators = {
            "task_intent": self.generate_task_draft,
            "material_result": self.generate_material_binding_draft,
            "approval_result": self.generate_fact_update_draft,
            "conflict_clue": self.generate_conflict_review_draft,
        }
        generator = generators.get(event.event_type)
        if not generator:
            return []
        drafts = generator(db, event)
        for draft in drafts:
            existing = db.query(Draft).filter(
                Draft.case_id == draft.case_id,
                Draft.idempotency_key == draft.idempotency_key,
            ).one_or_none()
            if existing:
                continue
            db.add(draft)
        db.flush()
        return drafts

    def generate_task_draft(self, db: Session, event) -> list[Draft]:
        material_title = event.related_material_title or self.extract_material_title(event.normalized_text) or "待补齐材料"
        element_key = self.infer_element_key(material_title, event.related_person)
        if self._active_task_exists(db, event.case_id, element_key, material_title):
            return []
        title = self._task_title(material_title, event.normalized_text)
        payload = {
            "title": title,
            "task_type": material_title,
            "priority": "P1",
            "expected_materials": [material_title],
            "depends_on": [],
            "idempotency_key": f"conversation-task:{event.id}:{material_title}",
        }
        return [self._draft(event, "task", title, element_key, payload)]

    def generate_fact_update_draft(self, db: Session, event) -> list[Draft]:
        element_key = self.infer_fact_element(event.normalized_text)
        title = f"更新{self._element_label(element_key)}事实"
        payload = {
            "fact_text": event.normalized_text,
            "source_event_id": event.id,
        }
        return [self._draft(event, "fact_update", title, element_key, payload)]

    def generate_material_binding_draft(self, db: Session, event) -> list[Draft]:
        material_title = event.related_material_title or self.extract_material_title(event.normalized_text) or "回写材料"
        element_key = self.infer_element_key(material_title, event.related_person)
        payload = {
            "title": material_title,
            "material_type": material_title,
            "owner": event.related_person,
            "supports_elements": resolve_material_elements(material_title, event.related_person),
            "source_event_id": event.id,
        }
        return [self._draft(event, "material_binding", f"绑定{material_title}", element_key, payload)]

    def generate_conflict_review_draft(self, db: Session, event) -> list[Draft]:
        payload = {
            "description": event.normalized_text,
            "priority": "P0",
            "source_event_id": event.id,
        }
        return [self._draft(event, "conflict_review", "复核材料矛盾线索", None, payload)]

    def extract_person(self, text: str) -> str | None:
        for person in ("李江", "周枫", "吴渔"):
            if person in text:
                return person
        return None

    def extract_material_title(self, text: str) -> str | None:
        for material in KNOWN_MATERIALS:
            if material in text:
                return material
        if "笔录" in text:
            return "询问笔录"
        if "诊断" in text:
            return "医院诊断证明"
        if "处罚" in text:
            return "行政处罚决定书"
        return None

    def matched_keywords(self, text: str) -> list[str]:
        keywords = TASK_KEYWORDS + MATERIAL_RESULT_KEYWORDS + FACT_UPDATE_KEYWORDS + CONFLICT_KEYWORDS + APPROVAL_KEYWORDS
        return [keyword for keyword in keywords if keyword in text]

    def infer_element_key(self, material_title: str, owner: str | None) -> str | None:
        elements = resolve_material_elements(material_title, owner)
        return elements[0] if elements else None

    def infer_fact_element(self, text: str) -> str | None:
        if any(keyword in text for keyword in ("伤势", "伤情", "诊断")):
            return "consequence"
        if any(keyword in text for keyword in ("处罚", "拘留", "罚款")):
            return "result"
        if any(keyword in text for keyword in ("认错", "认罚", "到案", "初犯")):
            return "circumstance"
        return None

    def _draft(self, event, draft_type: str, title: str, element_key: str | None, payload: dict) -> Draft:
        raw_key = f"{event.case_id}:{event.id}:{draft_type}:{title}:{payload}"
        return Draft(
            case_id=event.case_id,
            source_event_id=event.id,
            draft_type=draft_type,
            title=title,
            element_key=element_key,
            payload=payload,
            status="pending_confirmation",
            generated_by="conversation_task_ai",
            idempotency_key=sha256(raw_key.encode("utf-8")).hexdigest(),
        )

    def _active_task_exists(self, db: Session, case_id: int, element_key: str | None, material_title: str) -> bool:
        tasks = db.query(Task).filter(Task.case_id == case_id, Task.status != "completed").all()
        return any(
            task.element_key == element_key
            and any(material_title in expected or expected in material_title for expected in task.expected_materials)
            for task in tasks
        )

    def _task_title(self, material_title: str, text: str) -> str:
        if "上传" in text:
            return f"上传{material_title}"
        if "制作" in text:
            return f"制作{material_title}"
        return f"补齐{material_title}"

    def _element_label(self, element_key: str | None) -> str:
        return {
            "consequence": "后果",
            "result": "处罚结果",
            "circumstance": "情节",
        }.get(element_key or "", "案件")
