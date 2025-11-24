import uuid
from datetime import datetime

from app.config import settings
from app.constant.constants import MediaCategory


def set_media_filename(category: MediaCategory, is_temp=False):
    media_path = f"{category.value}"
    if is_temp:
        media_path = settings.MEDIA_PATH_TMP_PREFIX + media_path
    random_name = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{media_path}/{random_name}_{timestamp}"
    return filename
