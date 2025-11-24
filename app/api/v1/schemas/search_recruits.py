from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional, Union

from pydantic import BaseModel


class EmploymentType(str, Enum):
    INTERN = "INTERN"
    PART_TIME = "PART_TIME"
    FREELANCE = "FREELANCE"
    FULL_TIME = "FULL_TIME"
    TEMPORARY = "TEMPORARY"
    OTHER = "OTHER"
    CONTRACTOR = "CONTRACTOR"


class KeywordSearch(BaseModel):
    or_keywords: Optional[List[str]]
    exclude_keywords: Optional[List[str]]


class Salary(BaseModel):
    exclude_unknown_flag: Optional[bool]
    gte: Optional[float]
    lte: Optional[float]


class Location(BaseModel):
    prefectures: Optional[List[int]]
    cities: Optional[List[int]]


class PostingPeriod(str, Enum):
    ONE_MONTH = "ONE_MONTH"
    ONE_TO_THREE_MONTH = "ONE_TO_THREE_MONTH"
    THREE_TO_SIX_MONTH = "THREE_TO_SIX_MONTH"
    SIX_TO_ONE_YEAR = "SIX_TO_ONE_YEAR"
    ONE_YEAR_OR_MORE = "ONE_YEAR_OR_MORE"


class MediaCode(str, Enum):
    AMBI = "AMBI"
    BIZREACH = "BIZREACH"
    BOXIL = "BOXIL"
    DAIJOB = "DAIJOB"
    DODA = "DODA"
    GOWORKSHIP = "GOWORKSHIP"
    GREEN = "GREEN"
    HELLOWORK = "HELLOWORK"
    MYNAVI_SHINSOTSU = "MYNAVI_SHINSOTSU"
    MYNAVI_TENSHOKU = "MYNAVI_TENSHOKU"
    PLEX_JOB = "PLEX_JOB"
    RIKUNABI = "RIKUNABI"
    RIKUNABI_SHINSOTSU = "RIKUNABI_SHINSOTSU"
    TYPE = "TYPE"
    WANTEDLY = "WANTEDLY"
    OPENWORK = "OPENWORK"
    EAIDEM = "EAIDEM"
    HERP = "HERP"
    WORKPORT = "WORKPORT"


class Keyword(BaseModel):
    and_keywords: Optional[List[str]]
    or_keywords: Optional[List[str]]
    exclude_keywords: Optional[List[str]]
    is_exact: Optional[bool]


class ApplicationFlow(str, Enum):
    INTERVIEW_1_ROUND = "INTERVIEW_1_ROUND"
    INTERVIEW_2_ROUNDS = "INTERVIEW_2_ROUNDS"
    WRITTEN_TEST = "WRITTEN_TEST"
    OTHER = "OTHER"


class SkillCode(str, Enum):
    ADS = "ADS"
    ADVANCEDENG = "ADVANCEDENG"
    AI = "AI"
    ANALYSTIC = "ANALYSTIC"
    BASICENG = "BASICENG"
    BIGDATA = "BIGDATA"
    BITOOL = "BITOOL"
    BUSSINESSENG = "BUSSINESSENG"
    BUSSINESSPLANNING = "BUSSINESSPLANNING"
    CHINESE = "CHINESE"
    COACHING = "COACHING"
    COMMUNICATION = "COMMUNICATION"
    CONTENTPLANNING = "CONTENTPLANNING"
    CORPORATEPLANNING = "CORPORATEPLANNING"
    CREATIVE = "CREATIVE"
    CRM = "CRM"
    DATA = "DATA"
    DESIGN = "DESIGN"
    DESIGNPLANNING = "DESIGNPLANNING"
    DEVPLANNING = "DEVPLANNING"
    ERP_SAP = "ERP_SAP"
    EVENTPLANNING = "EVENTPLANNING"
    EXCEL = "EXCEL"
    EXECUTIONPLANNING = "EXECUTIONPLANNING"
    FINANCE = "FINANCE"
    FINANCIAL = "FINANCIAL"
    FLEXIBILITY = "FLEXIBILITY"
    GGANALYTICS = "GGANALYTICS"
    GOODSPLANNING = "GOODSPLANNING"
    HUMANMANAGEMENT = "HUMANMANAGEMENT"
    HUMANPLANNING = "HUMANPLANNING"
    IDEA = "IDEA"
    INTERENG = "INTERENG"
    KOREAN = "KOREAN"
    LANGUAGE = "LANGUAGE"
    LEADERSHIP = "LEADERSHIP"
    MAINTAINPLANNING = "MAINTAINPLANNING"
    MANAGEMENT = "MANAGEMENT"
    MANAGEMENTSTATEGY = "MANAGEMENTSTATEGY"
    MANAGEPLANNING = "MANAGEPLANNING"
    MARKETING = "MARKETING"
    MKPLANNING = "MKPLANNING"
    OFFICEPLANNING = "OFFICEPLANNING"
    OPERATIONPLANNING = "OPERATIONPLANNING"
    ORACLE = "ORACLE"
    PLANNING = "PLANNING"
    POWERBI = "POWERBI"
    POWERPOINT = "POWERPOINT"
    PRESENTATION = "PRESENTATION"
    PRODUCTPLANNING = "PRODUCTPLANNING"
    PROGRAMMING = "PROGRAMMING"
    PROJECTPLANNING = "PROJECTPLANNING"
    PROMOTIONPLANNING = "PROMOTIONPLANNING"
    PROPOSAL = "PROPOSAL"
    QLIK = "QLIK"
    RESEARCH = "RESEARCH"
    SALES = "SALES"
    SALESFORCE = "SALESFORCE"
    SALESPLANNING = "SALESPLANNING"
    SEO = "SEO"
    SERVICEPLANNING = "SERVICEPLANNING"
    SFA = "SFA"
    SOLVING = "SOLVING"
    SQL = "SQL"
    STATEGYPLANNING = "STATEGYPLANNING"
    STATISTICS = "STATISTICS"
    SYSTEMPLANNING = "SYSTEMPLANNING"
    TABLEAU = "TABLEAU"
    TEAMWORK = "TEAMWORK"
    WORD = "WORD"
    WORKPLANNING = "WORKPLANNING"


class SkillCodeRequest(BaseModel):
    skill_codes: Optional[List[SkillCode]]
    exclude_skill_codes: Optional[List[SkillCode]]


class TechLanguage(str, Enum):
    ASSEMBLY = "ASSEMBLY"
    CPLUS = "CPLUS"
    CSHARP = "CSHARP"
    CSS = "CSS"
    DART = "DART"
    GO = "GO"
    GROOVY = "GROOVY"
    HASKELL = "HASKELL"
    HTML = "HTML"
    JAVA = "JAVA"
    JS = "JS"
    JULIA = "JULIA"
    KOTLIN = "KOTLIN"
    LISP = "LISP"
    LUA = "LUA"
    MATLAB = "MATLAB"
    OBJC = "OBJC"
    PERL = "PERL"
    PHP = "PHP"
    PROLOG = "PROLOG"
    PYTHON = "PYTHON"
    RUBY = "RUBY"
    RUST = "RUST"
    SCALA = "SCALA"
    SQL = "SQL"
    SS = "SS"
    SWIFT = "SWIFT"
    TCL = "TCL"
    TS = "TS"
    VISUAL = "VISUAL"


class TechFramework(str, Enum):
    ACTIX = "ACTIX"
    ANGULAR = "ANGULAR"
    ASP = "ASP"
    BACKBONEJS = "BACKBONEJS"
    BEEGO = "BEEGO"
    BOTTLE = "BOTTLE"
    CAKEPHP = "CAKEPHP"
    CODEIGNITER = "CODEIGNITER"
    DJANGO = "DJANGO"
    DOTNET = "DOTNET"
    ECHO = "ECHO"
    EMBERJS = "EMBERJS"
    FASTAPI = "FASTAPI"
    FLASK = "FLASK"
    GIN = "GIN"
    GRAILS = "GRAILS"
    HANAMI = "HANAMI"
    JQUERY = "JQUERY"
    KTOR = "KTOR"
    LARAVEL = "LARAVEL"
    MICRONAUT = "MICRONAUT"
    NESTJS = "NESTJS"
    NEXTJS = "NEXTJS"
    NUXTJS = "NUXTJS"
    PADRINO = "PADRINO"
    PERFECT = "PERFECT"
    PHALCON = "PHALCON"
    PLAYFRAMEWORK = "PLAYFRAMEWORK"
    PYRAMID = "PYRAMID"
    RAILS = "RAILS"
    REACT = "REACT"
    REVEL = "REVEL"
    ROCKET = "ROCKET"
    SINATRA = "SINATRA"
    SPRING = "SPRING"
    STRUTS = "STRUTS"
    SYMFONY = "SYMFONY"
    VAADIN = "VAADIN"
    VAPOR = "VAPOR"
    VUEJS = "VUEJS"
    WARP = "WARP"
    YII = "YII"


class HolidayYear(BaseModel):
    gte: Optional[int]
    lte: Optional[int]


class Holiday(BaseModel):
    holiday_codes: Optional[List[Literal["SAT_SUN", "COMPANY_CALENDAR"]]]
    holiday_year: Optional[HolidayYear]


class RecruitQualification(str, Enum):
    ACCOUNTING = "ACCOUNTING"
    ADMINPROCEDURE = "ADMINPROCEDURE"
    ADVANCEDENG = "ADVANCEDENG"
    ADVANCEDJPN = "ADVANCEDJPN"
    ARCCONTRUCT = "ARCCONTRUCT"
    ARCHITECT = "ARCHITECT"
    AWSCERT = "AWSCERT"
    AWSCSA = "AWSCSA"
    BASICENG = "BASICENG"
    CAREWORKER = "CAREWORKER"
    CHILDCAREWORKER = "CHILDCAREWORKER"
    CHINESE = "CHINESE"
    CIA = "CIA"
    CISA = "CISA"
    CIVCONTRUCT = "CIVCONTRUCT"
    CONCRETEDX = "CONCRETEDX"
    CONTRUCT = "CONTRUCT"
    CPA = "CPA"
    DATABASECERT = "DATABASECERT"
    ENGCERT = "ENGCERT"
    INTERENG = "INTERENG"
    INTERJPN = "INTERJPN"
    ISTQB = "ISTQB"
    ITAPPLIED = "ITAPPLIED"
    ITBASIC = "ITBASIC"
    ITPASSPORT = "ITPASSPORT"
    JAPANESE = "JAPANESE"
    JSTQB = "JSTQB"
    KOREAN = "KOREAN"
    LAWYER = "LAWYER"
    LDSCONTRUCT = "LDSCONTRUCT"
    MENTALWORKER = "MENTALWORKER"
    NETWORKCERT = "NETWORKCERT"
    NISSHO = "NISSHO"
    ORACLE = "ORACLE"
    PMCERT = "PMCERT"
    REALESTATE = "REALESTATE"
    SALESFORCE = "SALESFORCE"
    SECURITYCERT = "SECURITYCERT"
    SOCIAL_LABOR = "SOCIAL_LABOR"
    SOCIALWORKER = "SOCIALWORKER"
    TAXACCOUNTING = "TAXACCOUNTING"


class JobSubCategoryItem(BaseModel):
    large: Optional[str]
    sub: Optional[str]


class JobCategory(BaseModel):
    large_category: Optional[List[str]]
    sub_category: Optional[List[JobSubCategoryItem]]


class AnnualIncome(BaseModel):
    exclude_unknown_flag: Optional[bool]
    gte: Optional[int]
    lte: Optional[int]


class FeatureFlag(str, Enum):
    EDUCATIONAL = "EDUCATIONAL"
    COLLEGE = "COLLEGE"
    UNIVERSITY_GRADUATION = "UNIVERSITY_GRADUATION"
    POST_GRADUATE = "POST_GRADUATE"


class SearchRecruitRequest(BaseModel):
    keyword: Optional[Keyword]
    employment_type: Optional[List[str]]
    media: Optional[List[str]]
    feature_flag: Optional[List[FeatureFlag]]
    salary_year: Optional[Salary]
    salary_month: Optional[Salary]
    sales_approach_reject_flag_exclude: Optional[bool]
    locations: Optional[Location]
    address: Optional[str]
    job_skill_codes: Optional[KeywordSearch]
    job_category: Optional[JobCategory]
    posting_period: Optional[List[PostingPeriod]]
    application_flow: Optional[List[str]]
    tech_frameworks: Optional[KeywordSearch]
    tech_languages: Optional[KeywordSearch]
    recruit_qualifications: Optional[KeywordSearch]
    holiday: Optional[Holiday]

    class Config:
        extra = "allow"


class EsRecruitBase(BaseModel):
    id: Optional[str]
    media_code: Optional[
        Literal["DODA", "WANTEDLY", "RIKUNABI", "MYNAVI_TENSHOKU", "MYNAVI_SHINSOTSU"]
    ]
    corporate_number: Optional[str]
    title: Optional[str]
    sub_title: Optional[str]
    explain: Optional[str]
    content: Optional[str]
    summary: Optional[str]
    recruit_tels: Optional[List[str]]
    recruit_mails: Optional[List[str]]
    working_address_list: Optional[List[str]]
    working_location: Optional[str]
    working_time: Optional[str]
    application_contacts: Optional[str]
    application_flow: Optional[str]
    media_code: Optional[str]
    corporate_number: Optional[Union[str, None]]
    title: Optional[Union[str, None]]
    sub_title: Optional[Union[str, None]]
    content: Optional[Union[str, None]]
    employment_type_codes: Optional[List[Union[str, None]]]
    recruit_tels: Optional[List[Union[str, None]]]
    recruit_mails: Optional[List[Union[str, None]]]
    working_address_list: Optional[List[Union[str, None]]]
    working_location: Optional[Union[str, None]]
    working_time: Optional[Union[str, None]]
    application_contacts: Optional[Union[str, None]]
    application_flow: Optional[Union[str, None]]
    application_flow_codes: Optional[List[Union[str, None]]]
    remote_flag: Optional[bool]
    full_remote_flag: Optional[bool]
    required_educational_flag: Optional[bool]
    required_college_flag: Optional[bool]
    required_university_graduate_flag: Optional[bool]
    required_post_graduate_flag: Optional[bool]
    allow_sidejob_flag: Optional[bool]
    online_interview_flag: Optional[bool]
    attitude_test_flag: Optional[bool]
    salary_year_min: Optional[int]
    salary_year_max: Optional[int]
    salary_year_value: Optional[int]
    salary_month_min: Optional[int]
    salary_month_max: Optional[int]
    salary_month_value: Optional[int]
    holiday: Optional[Union[str, None]]
    tags: Optional[List[Union[str, None]]]
    job_recruit_qualifications: Optional[List[Union[str, None]]]
    skill_codes: Optional[List[Union[str, None]]]
    search_keywords: Optional[List[Union[str, None]]]
    categories: Optional[Union[str, List[str], None]]
    positions: Optional[List[Union[str, None]]]
    job_tech_frameworks: Optional[List[Union[str, None]]]
    job_tech_languages: Optional[List[Union[str, None]]]
    job_company_id: Optional[Union[str, None]]
    other_info: Optional[Union[str, None]]
    start_at: Optional[datetime]
    end_at: Optional[datetime]
    source_recruit_url: Optional[Union[str, None]]
    holiday_codes: Optional[List[Union[str, None]]]
    holiday_year: Optional[int]
    sub_category_codes: Optional[List[Union[str, None]]]
    category_codes: Optional[List[Union[str, None]]]
    city_codes: Optional[List[Union[str, None]]]
    prefecture_codes: Optional[List[Union[str, None]]]
    job_skill_codes: Optional[List[Union[str, None]]]


class RecruitResponse(EsRecruitBase):
    company_name: Optional[str]
    company_tel: Optional[str]
    contact_email: Optional[str]
    hp_url: Optional[str]
    contact_form_url: Optional[str]
    company_downloaded_flag: Optional[bool] = None
    available_fields: Optional[List[str]]


class SearchRecruitResponse(BaseModel):
    page: int
    per_page: int
    total: int
    unlimited_total: int
    data: List[RecruitResponse]


class RecruitOffsetData(BaseModel):
    corporate_number: Optional[str]
    recruit_phone: Optional[str]
    recruit_email: Optional[str]
    phone: Optional[str]
    contact_email: Optional[str]
    hp_url: Optional[str]
    contact_form_url: Optional[str]
