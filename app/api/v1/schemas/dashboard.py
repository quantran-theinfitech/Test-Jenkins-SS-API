from typing import Optional

from pydantic import BaseModel


class DashBoardResponse(BaseModel):
    count_month_downloaded: Optional[int] = 0
    total_downloaded: Optional[int] = 0
    count_month_sent_forms: Optional[int] = 0
    total_sent_forms: Optional[int] = 0
