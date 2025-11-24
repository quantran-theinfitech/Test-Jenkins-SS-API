from sqlmodel import create_engine

from app.config import settings
from utils.query_prefixer import FilenamePrefixer

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)

prefixer = FilenamePrefixer(
    include_line_number=True, include_function_name=True, full_path=True
)
prefixer.register(engine)
