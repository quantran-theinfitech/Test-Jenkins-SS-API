AVAILABLE_DATA = "available"
NOT_AVAILABLE_DATA = "notAvailable"


def hide_data(company, field: str):
    company[field] = AVAILABLE_DATA if company[field] else NOT_AVAILABLE_DATA
