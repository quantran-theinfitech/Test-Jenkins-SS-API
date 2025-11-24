from app.constant.constants import INDUSTRIES_CATEGORIES, LISTING_MARKET_CODE
from utils.extension import validate_and_clean_domain


def get_field_value(
    ss_company,
    company,
    salesmart_field,
    hubspot_field,
    company_city=None,
    company_prefecture=None,
):
    salesmart_field_value = getattr(ss_company, salesmart_field, None)

    # Các trường đặc biệt có thể lấy từ cơ sở dữ liệu
    if salesmart_field == "nta_city_id":
        value = company_city if company_city else salesmart_field_value
    elif salesmart_field == "nta_prefecture_id":
        value = company_prefecture if company_prefecture else salesmart_field_value
    elif (salesmart_field == "industry_code") and salesmart_field_value is not None:
        value = INDUSTRIES_CATEGORIES[salesmart_field_value]["text"]
    elif (
        salesmart_field == "main_sub_industry_code"
        and salesmart_field_value is not None
    ):
        for industry in INDUSTRIES_CATEGORIES.values():
            for child in industry.get("child", []):
                if child["code"] == salesmart_field_value:
                    value = child["text"]
                    break
    elif salesmart_field == "establish_at":
        value = (
            str(ss_company.establish_at.year)
            if ss_company.establish_at
            else salesmart_field_value
        )
    elif salesmart_field == "domain" and salesmart_field_value is not None:
        value = validate_and_clean_domain(salesmart_field_value)
    elif salesmart_field == "listing_market_code" and salesmart_field_value is not None:
        value = LISTING_MARKET_CODE[salesmart_field_value]
    elif salesmart_field == "is_listed_market":
        value = (
            getattr(ss_company, "listing_market_code", None) is not None
            and getattr(ss_company, "listing_market_code", None) != "UNLISTED"
        )
    else:
        value = (
            salesmart_field_value
            if salesmart_field_value
            else getattr(ss_company, salesmart_field, None)
        )

    # Nếu không có giá trị, sử dụng giá trị HubSpot
    return value if value is not None else company.properties.get(hubspot_field)


def get_field_value_salesforce(
    ss_company,
    company,
    salesmart_field,
    salesforce_field,
    company_city=None,
    company_prefecture=None,
):
    salesmart_field_value = getattr(ss_company, salesmart_field, None)

    if salesmart_field == "nta_city_id":
        value = company_city if company_city else salesmart_field_value
    elif salesmart_field == "nta_prefecture_id":
        value = company_prefecture if company_prefecture else salesmart_field_value
    elif salesmart_field == "industry_code" and salesmart_field_value is not None:
        value = INDUSTRIES_CATEGORIES[salesmart_field_value]["text"]
    elif (
        salesmart_field == "main_sub_industry_code"
        and salesmart_field_value is not None
    ):
        for industry in INDUSTRIES_CATEGORIES.values():
            for child in industry.get("child", []):
                if child["code"] == salesmart_field_value:
                    value = child["text"]
                    break
    elif salesmart_field == "establish_at":
        value = (
            str(ss_company.establish_at.year)
            if ss_company.establish_at
            else salesmart_field_value
        )
    elif salesmart_field == "domain" and salesmart_field_value is not None:
        value = validate_and_clean_domain(salesmart_field_value)
    elif salesmart_field == "listing_market_code" and salesmart_field_value is not None:
        value = LISTING_MARKET_CODE[salesmart_field_value]
    elif salesmart_field == "is_listed_market":
        value = (
            "はい"
            if getattr(ss_company, "listing_market_code", None) is not None
            and getattr(ss_company, "listing_market_code", None) != "UNLISTED"
            else "いいえ"
        )
    else:
        value = (
            salesmart_field_value
            if salesmart_field_value
            else getattr(ss_company, salesmart_field, None)
        )

    return value if value is not None else company.get(salesforce_field)
