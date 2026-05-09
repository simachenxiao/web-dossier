TASK_DEPENDENCIES: dict[str, list[str]] = {
    "传唤证": ["嫌疑人身份核验"],
    "嫌疑人笔录": ["传唤证"],
    "嫌疑人供述": ["传唤证"],
    "认罪认罚材料": ["嫌疑人陈述"],
    "处罚决定书": ["所有核心要素proved"],
    "发还清单": ["处罚决定书"],
}


def dependencies_for(task_type: str) -> list[str]:
    return TASK_DEPENDENCIES.get(task_type, [])
