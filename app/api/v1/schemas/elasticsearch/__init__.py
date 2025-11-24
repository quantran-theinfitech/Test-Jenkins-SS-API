from elasticsearch_dsl import (
    Boolean,
    Date,
    Double,
    InnerDoc,
    Integer,
    Keyword,
    Long,
    Nested,
    Short,
    Text,
)


class Category(InnerDoc):
    id = Long()
    name = Keyword()
    priority = Long()
    slug = Keyword()
    groups = Long(multi=True)


class Technology(InnerDoc):
    categories = Nested(Category, multi=True)
    confidence = Long()
    cpe = Keyword()
    description = Text()
    icon = Keyword()
    lastUrl = Keyword(multi=True)
    name = Keyword()
    pricing = Keyword(multi=True)
    rootPath = Boolean()
    slug = Keyword()
    version = Keyword()
    website = Keyword()


class CompanyInnerDoc(InnerDoc):
    name = Text(analyzer="name_index_analyzer", search_analyzer="name_search_analyzer")
    kana_name = Text(
        analyzer="name_index_analyzer", search_analyzer="name_search_analyzer"
    )
    english_name = Text()
    business_content = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    landing_html_content = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    info_html_content = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    business_html_content = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    sub_industries_code = Keyword(multi=True)
    industry_code = Keyword()
    nta_prefecture_id = Integer()
    nta_city_id = Integer()
    corporate_number = Keyword()
    domain = Keyword()
    establish_at = Date()
    closing_month = Short()
    listing_market_code = Keyword()
    average_age = Double()
    press_release_media_codes = Keyword(multi=True)
    management_tools = Keyword(multi=True)
    communication_tools = Keyword(multi=True)
    tech_languages = Keyword(multi=True)
    tech_frameworks = Keyword(multi=True)
    tech_clouds = Keyword(multi=True)
    crm_tools = Keyword(multi=True)
    tech_databases = Keyword(multi=True)
    internal_tools = Keyword(multi=True)
    employees_count = Integer()
    capital = Long()
    revenue = Long()
    revenue_ai = Long()
    contact_form_url = Keyword()
    recruit_phone = Keyword()
    phone = Keyword()
    fax = Keyword()
    recruit_email = Keyword()
    contact_email = Keyword()
    hp_url = Keyword()
    business_model_codes = Keyword(multi=True)
    latest_recruits_at = Date()
    latest_parttime_recruit_at = Date()
    original_tags = Keyword(multi=True)
    three_month_funding_flags = Keyword(multi=True)
    six_month_funding_flags = Keyword(multi=True)
    twelve_month_funding_flags = Keyword(multi=True)
    all_funding_flags = Keyword(multi=True)
    president_name = Keyword()
    technologies = Nested(Technology, multi=True)
    twitter_url = Keyword()
    facebook_url = Keyword()
    youtube_url = Keyword()
    linkedin_url = Keyword()


class PersonInnerDoc(InnerDoc):
    name = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    uuid = Keyword()
    company_name = Text(
        analyzer="name_index_analyzer",
        search_analyzer="name_search_analyzer",
    )
    role_name = Text(
        search_analyzer="jp_analyzer", analyzer="jp_analyzer"
    )  # role from crawler
    address = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    linkedin_url = Keyword()
    wantedly_url = Keyword()
    twitter_url = Keyword()
    github_url = Keyword()
    fb_url = Keyword()
    team_ids = Integer(
        multi=True,
    )

    intro = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    sub_group_codes = Keyword(
        multi=True,
    )  # role value CxO
    bio = Text(search_analyzer="jp_analyzer", analyzer="jp_analyzer")
    # role_code = Keyword()  # role from bright_data
    role_group_codes = Keyword(
        multi=True,
    )  # role group by llm
    corporate_number = Keyword(
        multi=True,
    )
    is_opt_out = Boolean()
    update_opt_out_at = Date()
