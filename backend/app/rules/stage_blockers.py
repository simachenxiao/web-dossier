STAGE_BLOCKERS: dict[str, list[str]] = {
    "filing": ["身份核验", "立案文书"],
    "investigation": ["矛盾复核"],
    "closing": ["处罚决定书"],
}


def is_stage_blocker(stage: str, task_type: str) -> bool:
    return any(keyword in task_type for keyword in STAGE_BLOCKERS.get(stage, []))
