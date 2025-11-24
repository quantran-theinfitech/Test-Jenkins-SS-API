import re


def optimize_name(name: str):
    ja_stopwords = [
        "株式会社",
        "(株)",
        "（株）",
        "有限会社",
        "(有)",
        "（有）",
        "合同会社",
        "(同)",
        "（同）",
        "合資会社",
        "(資)",
        "（資）",
        "合名会社",
        "(名)",
        "（名）",
        "医療法人社団",
        "（医療法人財団）",
        "(医療法人財団)公益財団法人",
        "（公益財団法人）",
        "(公益財団法人)",
        "医療法人",
        "（医療法人）",
        "(医療法人)",
        "医療法人社団慶北会",
    ]

    en_stopwords = ["PTE", "LTD.", "Co.", "Corp.", "Inc.", "Group"]

    for word in ja_stopwords:
        name = name.replace(word, "")

    # Regex lookahead negative. Example: / a(?!b) /  will match all a not followed by b.
    # hence it will match: ad, ae, az but will not match ab
    name = re.sub(r" (%s)\.?(?![\w+])" % ("|".join(en_stopwords)), "", name, flags=re.I)
    return name


def translate_roles(roles: list):
    translations = {
        "PRESIDENT": "社長",
        "EXECUTIVE_LEVEL": "役員クラス",
        "MANAGER_LEVEL": "責任者クラス",
        "SALES": "営業",
        "BUSINESS_PLANNING_DEVELOPMENT": "事業企画/事業開発",
        "CORPORATE_PLANNING": "経営企画",
        "CUSTOMER_SUPPORT_SUCCESS": "カスタマーサポート/サクセス",
        "MARKETING": "マーケティング",
        "PROJECT_MANAGER": "プロジェクトマネジャー",
        "PUBLIC_RELATIONS_IR": "広報/IR",
        "HUMAN_RESOURCES_PERSONNEL": "人事/人材",
        "ACCOUNTING_FINANCE": "経理/財務",
        "LEGAL": "法務",
        "RESEARCH_DEVELOPMENT": "研究開発 (R&D)",
        "TECHNOLOGY_ENGINEERING": "技術/エンジニアリング",
        "EDUCATION_TRAINING": "教育/トレーニング",
        "DESIGN_CREATIVE": "デザイン/クリエイティブ",
        "PROCUREMENT_PURCHASING": "調達/購買",
        "SALES_SUPPORT_PLANNING": "営業支援/営業企画",
        "SOLE_PROPRIETOR": "個人事業主",
        "QUALITY_ASSURANCE_CONTROL": "品質保証/品質管理",
        "MANUFACTURING_PRODUCTION": "製造/生産",
        "LOGISTICS_SUPPLY_CHAIN": "物流/サプライチェーン",
        "CUSTOMER_SERVICE_FRONT_OFFICE": "顧客対応/フロント",
        "FACILITY_MANAGEMENT": "設備・施設管理",
        "FIELD_OPERATIONS": "現場・フィールドオペレーション",
        "HSE_HEALTH_SAFETY_ENVIRONMENT": "HSE（健康、安全、環境）",
        "AUDIT_INTERNAL_AUDIT": "監査・内部監査",
        "GENERAL_AFFAIRS": "総務",
        "MEDICAL_WELFARE": "医療/福祉",
        "ADMINISTRATIVE_SUPPORT_SALES_PLANNING": "事務支援/営業企画",
        "CONSULTING": "コンサルティング",
        "TRANSLATION_INTERPRETATION": "翻訳/通訳",
        "STORE_OPERATIONS_MANAGER": "店舗運営/店長",
        "INTERNATIONAL_BUSINESS": "国際ビジネス",
        "OTHER": "その他",
    }

    translated_roles = [translations.get(role, "N/A") for role in roles]
    return translated_roles
