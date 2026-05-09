UNIVERSAL_REQUIRED: dict[str, list[str]] = {
    "victim": ["人像照片", "身份核验", "询问笔录"],
    "suspect": ["人像照片", "身份核验", "传唤证", "陈述材料"],
    "circumstance": ["前科核验"],
    "procedure": ["立案登记表", "立案告知书", "接报审批表"],
}


def required_materials_for(element_key: str) -> list[str]:
    return UNIVERSAL_REQUIRED.get(element_key, [])
