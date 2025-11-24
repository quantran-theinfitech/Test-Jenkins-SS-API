from sqlmodel import Session

from app.models.team_credit import ServiceCode

from utils.credit_utils import consume_credit as consume_credit_utils


def consume_credit(db: Session, team_id: int, amount: int, service_code: ServiceCode):
    consume_credit_utils(db, team_id, amount, service_code)
