from sqlmodel import Session

from utils.credit_utils import get_credit_status as get_credit_status_utils


def get_credit_status(db: Session, team_id: int):
    return get_credit_status_utils(db, team_id)
