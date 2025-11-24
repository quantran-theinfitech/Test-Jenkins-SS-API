from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from jose import jwt
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.api.v1.schemas.users import TokenPayload
from app.config import settings
from app.models.user import User

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.SECURITY_BCRYPT_DEFAULT_ROUNDS,
)


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def verify_password(self, plain_password: str, hashed_password: str):
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        return pwd_context.hash(password)

    def create_access_token(
        self,
        subject: str,
        listing_plan_code: Optional[str] = None,
        form_plan_code: Optional[str] = None,
        is_first_login: Optional[bool] = None,
        password_updated_at: Optional[datetime] = None,
    ) -> Tuple[str, datetime]:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode = TokenPayload(
            exp=expire,
            sub=subject,
            refresh=False,
            listing_plan_code=listing_plan_code,
            form_plan_code=form_plan_code,
            password_updated_at=password_updated_at.isoformat()
            if password_updated_at
            else None,
        )
        if is_first_login:
            to_encode.init_password = True
        encoded_jwt: str = jwt.encode(
            to_encode.dict(),
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        return encoded_jwt, expire

    def create_refresh_token(self, subject: str) -> Tuple[str, datetime]:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        to_encode = TokenPayload(exp=expire, sub=subject, refresh=True)
        encoded_jwt: str = jwt.encode(
            to_encode.dict(),
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        return encoded_jwt, expire

    def authenticate_user(self, email: str, password: str):
        statement = (
            select(User).where(User.email == email).order_by(User.updated_at.desc())
        )
        result = self.db.exec(statement)
        user = result.first()
        if not user:
            return False
        if not self.verify_password(
            plain_password=password, hashed_password=user.password
        ):
            return False
        return user

    def authenticate_user_with_init_password(self, email: str, password: str):
        statement = (
            select(User).where(User.email == email).order_by(User.updated_at.desc())
        )
        result = self.db.exec(statement)
        user = result.first()
        if not user:
            return False
        if user.password is not None:
            return False
        if not self.verify_password(
            plain_password=password, hashed_password=user.initial_password
        ):
            return False
        return user
