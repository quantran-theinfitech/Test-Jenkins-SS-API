from typing import Any, Dict, Optional

from pydantic import BaseSettings, EmailStr, validator
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    PROJECT_NAME: str = "Theinfitech"

    DB_CONNECTION: Optional[str]
    DB_HOST: Optional[str]
    DB_PORT: Optional[str]
    DB_DATABASE: Optional[str]
    DB_USERNAME: Optional[str]
    DB_PASSWORD: Optional[str]
    ES_HOST: Optional[str]
    ES_SCHEME: Optional[str]
    ES_PORT: Optional[str]
    ES_USERNAME: str
    ES_PASSWORD: str
    SECURITY_BCRYPT_DEFAULT_ROUNDS: int = 12
    # REFRESH_TOKEN_EXPIRE_MINUTES: int

    SECRET_KEY: str
    VERIFY_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    SQLALCHEMY_DATABASE_URI: str = ""

    FE_URL: str
    APP_URL: str
    LP_URL: str

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM: EmailStr
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool

    AMOUNT_PER_DOWNLOAD: int
    AMOUNT_PER_JOB_ITEM: int
    HASHIDS_SALT: str

    CLIENT_ID: str
    CLIENT_SECRET: str
    SLACK_HOST: str
    HUBSPOT_HOST: str
    HUBSPOT_CLIENT_ID: str
    HUBSPOT_CLIENT_SECRET: str
    REDIRECT_URI: str

    AWS_SERVER_PUBLIC_KEY: str
    AWS_SERVER_SECRET_KEY: str
    AWS_REGION_NAME: str
    AWS_JOB_QUEUE: str
    AWS_JOB_DEFINITION: str


    HUB_AWS_BATCH_JOB_DEFINITION: str
    HUB_AWS_BATCH_JOB_QUEUE: str

    MAUTIC_BASE_URL: str
    MAUTIC_USERNAME: str
    MAUTIC_PASSWORD: str
    MAUTIC_VERIFY_SSL: bool

    GOOGLE_PROJECT_ID: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    GOOGLE_SCOPES: str

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Salesforce
    SALESFORCE_CLIENT_ID: str
    SALESFORCE_CLIENT_SECRET: str
    SALESFORCE_AUTH_URL: str
    SALESFORCE_TOKEN_URL: str
    SALESFORCE_REDIRECT_URI: str
    SALESFORCE_USER_INFO_URL: str

    HUBSPOT_GOOGLE_SERVICE_ACCOUNT: str
    HUBSPOT_GOOGLE_SHEET_URL: str

    S3_BUCKET_NAME: str
    MEDIA_PATH_TMP_PREFIX: str = "tmp/"

    SENTRY_DSN: str
    SENTRY_ENV: str
    PLAYLIST_ID: str
    YOUTUBE_API_KEY: str
    # Form Job
    JOB_DEFINITION: Optional[str]
    JOB_QUEUE: Optional[str]

    MAX_VCPUS: Optional[int]
    JOB_NAME_PREFIX: Optional[str]
    BUCKET_NAME: Optional[str]
    PREFIX_TRACKING_URL: Optional[str]
    TEST_MODE: Optional[str]

    INVITATION_TOKEN_LENGTH: int = 32
    UNIPILE_DSN: Optional[str]
    UNIPILE_APIKEY: Optional[str]
    UNIPILE_NOTIFY_URL: Optional[str]
    UNIPILE_SUCCESS_URL: Optional[str]

    REDIS_HOST: Optional[str]
    REDIS_PORT: Optional[str]
    REDIS_CACHE_TTL: Optional[int] = 60 * 60 * 5

    SALESMART_GOOGLE_SERVICE_ACCOUNT: str
    SALESMART_GOOGLE_SHEET_URL: str

    # LangGraph API
    LANGGRAPH_URL_API: str = "https://nichelle-semicalcined-quarrellingly.ngrok-free.dev"
    LANGGRAPH_USERNAME: str = "admin"
    LANGGRAPH_PASSWORD: str = "admin"
    CHAT_API_URL: str = "http://host.docker.internal:5000/api/chat/stream"

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str) and v:
            return v
        if not (connection := values.get("DB_CONNECTION")):
            raise ValueError(
                "must specify at least DB_CONNECTION or SQLALCHEMY_DATABASE_URI",
            )
        username = values.get("DB_USERNAME")
        password = values.get("DB_PASSWORD")
        host = values.get("DB_HOST")
        port = values.get("DB_PORT")
        database = values.get("DB_DATABASE")
        return URL(
            connection,
            username,
            password,
            host,
            port,
            database,
        ).render_as_string(False)

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()  # type: ignore
