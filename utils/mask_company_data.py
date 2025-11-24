from utils.extract_domain import extract_full_domain_url


def mask_company_data(companies, corporate_numbers_downloaded):
    display_fields = [
        "id",
        "establish_at",
        "name",
        "address",
        "industry_code",
        "sub_industries_code",
        "listing_market_code",
        "president_name",
        "corporate_number",
        "postal_code",
        "favicon_url",
        "original_tags",
    ]

    sort_fields = [
        "employees_count",
        "revenue",
        "capital",
    ]

    for company in companies:
        # Tạo favicon_url với /favicon.ico
        domain_url = extract_full_domain_url(company.get("hp_url"))
        if domain_url:
            company["favicon_url"] = f"{domain_url}/favicon.ico"
        else:
            company["favicon_url"] = None

        mask_fields = [
            x
            for x in company.keys()
            if x not in display_fields
            and x not in sort_fields
            and x != "id"
            and x != "corporate_number"
        ]
        available_fields = []
        if company["corporate_number"] not in corporate_numbers_downloaded:
            for field in mask_fields:
                if company[field] is not None:
                    available_fields.append(field)
                    company[field] = None
            company["downloaded_flag"] = False

        else:
            company["downloaded_flag"] = True
        company["available_fields"] = available_fields

    return companies
