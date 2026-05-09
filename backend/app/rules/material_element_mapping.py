PERSON_MATERIAL_TYPES = {"人像照片", "身份核验", "询问笔录"}

MATERIAL_ELEMENT_MAPPING: dict[str, list[str]] = {
    "人像照片": ["_person"],
    "身份核验": ["_person"],
    "询问笔录": ["_person", "tool", "consequence"],
    "自书材料": ["suspect", "tool", "circumstance"],
    "证人证言": ["witness", "tool"],
    "伤情照片": ["consequence"],
    "体表伤情记录": ["consequence"],
    "伤情检查结论": ["consequence"],
    "医院诊断证明": ["consequence"],
    "诊断证明告知书": ["consequence"],
    "作案工具照片": ["tool"],
    "现场照片": ["time"],
    "证据保全决定书": ["tool"],
    "证据保全清单": ["tool"],
    "证据保全审批表": ["tool"],
    "传唤证": ["suspect"],
    "前科核验": ["circumstance"],
    "认罪认罚材料": ["circumstance"],
    "快办告知书": ["circumstance"],
    "立案登记表": ["procedure"],
    "立案告知书": ["procedure"],
    "接报审批表": ["procedure"],
    "处罚决定书": ["result"],
    "处罚告知笔录": ["suspect", "circumstance"],
    "发还清单": ["tool"],
}


def resolve_material_elements(material_type: str, owner: str | None = None, explicit_elements: list[str] | None = None) -> list[str]:
    if explicit_elements:
        return list(dict.fromkeys(explicit_elements))

    elements: list[str] = []
    for known_type, mapped_elements in MATERIAL_ELEMENT_MAPPING.items():
        if known_type in material_type:
            elements = mapped_elements
            break

    resolved: list[str] = []
    for element in elements:
        if element == "_person":
            resolved.append(resolve_person_element(owner))
        else:
            resolved.append(element)
    return list(dict.fromkeys(resolved))


def resolve_person_element(owner: str | None) -> str:
    if owner and any(keyword in owner for keyword in ("周枫", "嫌疑", "违法")):
        return "suspect"
    return "victim"
