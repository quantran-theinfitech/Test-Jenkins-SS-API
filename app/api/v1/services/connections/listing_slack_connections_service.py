from sqlalchemy import text
from sqlmodel import Session

from app.api.v1.schemas.users import UserBase


def listing_slack_connections(db: Session, current_user: UserBase):
    query = """
        SELECT id, workspace_name, channel_name
        FROM slack_connections
        WHERE team_id = :team_id
        """
    slack_connections = db.execute(text(query), {"team_id": current_user.team_id}).all()
    data = [dict(x) for x in slack_connections]
    return data
