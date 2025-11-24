from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.sequence.mailboxes import MailboxBase
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.gsuite import (
    google_callback_service,
    google_login_service,
)

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


# Đăng nhập qua Google và chuyển hướng tới Google OAuth 2.0
@router.get("/google/login")
def google_login():
    auth_url = google_login_service()
    return {"redirect_url": auth_url}


@router.get("/google/callback", response_model=MailboxBase)
def callback(
    code: str,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    response = google_callback_service(code, db, current_user)
    return MailboxBase(**response.dict())


# @router.get("/google/notification")
# async def pubsub_webhook(request: Request):
#     # Lấy dữ liệu từ Pub/Sub
#     payload = await request.json()

#     # In ra thông báo từ Pub/Sub
#     print(f"Received notification: {json.dumps(payload)}")

#     # Ở đây bạn có thể xử lý thông báo như cập nhật dữ liệu, gửi cảnh báo, v.v.
#     # Ví dụ: Phân tích nội dung và thực hiện hành động tương ứng
#     if 'message' in payload:
#         message_data = payload['message']
#         print(f"Message Data: {message_data}")

#     return {"message": "Notification received"}
