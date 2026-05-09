TYPE_PRIORITY: list[tuple[str, str]] = [
    ("身份核验", "P0"),
    ("立案", "P0"),
    ("矛盾复核", "P0"),
    ("询问笔录", "P1"),
    ("嫌疑人陈述", "P1"),
    ("伤情检查结论", "P1"),
    ("证据保全", "P1"),
    ("传唤证", "P1"),
    ("证人", "P2"),
    ("认罪认罚", "P2"),
    ("快办", "P2"),
    ("前科核验", "P2"),
    ("发还清单", "P3"),
    ("处罚告知", "P3"),
    ("处罚决定书", "P3"),
]


def priority_for(task_type: str) -> str:
    for keyword, priority in TYPE_PRIORITY:
        if keyword in task_type:
            return priority
    return "P2"
