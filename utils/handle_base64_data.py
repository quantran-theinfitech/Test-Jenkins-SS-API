import re
from typing import Tuple


def parse_base64_data_uri(data_uri: str) -> Tuple[str, str, str]:
    """
    Tách chuỗi base64 dạng đầy đủ 'data:<mime-type>;base64,<data>' thành:
    - mime_type: ví dụ 'image/png'
    - header: ví dụ 'data:image/png;base64'
    - base64_data: phần dữ liệu base64 thuần

    Trả về tuple: (mime_type, header, base64_data)
    """
    pattern = r"^data:(?P<mime>[\w/+.-]+);base64,(?P<data>.+)$"
    match = re.match(pattern, data_uri)
    if not match:
        raise ValueError("Base64 format needed")

    mime_type = match.group("mime")
    base64_data = match.group("data")
    header = f"data:{mime_type};base64,"

    return mime_type, header, base64_data
