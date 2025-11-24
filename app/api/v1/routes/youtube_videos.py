from fastapi import APIRouter, Depends

import requests

from app.api.base.deps import custom_generate_unique_id
from app.api.v1.schemas.users import UserBase
from app.api.v1.dependencies import get_current_user
from app.config import settings

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)

@router.get('/')
def listing_youtube_videos(current_user: UserBase = Depends(get_current_user())):
    url = (
        "https://youtube.googleapis.com/youtube/v3/playlistItems"
        "?part=snippet&maxResults=50"
        f"&playlistId={settings.PLAYLIST_ID}&key={settings.YOUTUBE_API_KEY}"
    )
    response = requests.get(url)
    return response.json()
    
    