def get_element_xpath(element):
    segments = []
    while element.parent is not None:
        segment = element.name
        if element.get("id"):
            segment += f"[@id='{element.get('id')}']"
            segment = "//" + segment
            segments.insert(0, segment)
            break
        elif element.name == "tbody":
            element = element.parent
            continue
        else:
            seg = (
                element.parent.find_all(element.name, recursive=False).index(element)
                + 1
            )
            segment += f"[{seg}]"
        if element.name == "tr":
            segment = "/" + segment
        segments.insert(0, segment)
        element = element.parent
    xpath = "/".join(segments)
    return xpath.lower()


def validate_and_clean_domain(domain: str) -> str:
    if domain.endswith("/"):
        domain = domain.rstrip("/")
    return domain
