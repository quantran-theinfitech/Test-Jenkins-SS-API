def format_size(size_bytes: float):
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def calculate_binary_size_from_base64(base64_str: str) -> int:
    """
    Trả về số byte gốc của chuỗi base64
    """
    # Xóa ký tự xuống dòng và khoảng trắng nếu có
    base64_str = base64_str.strip().replace("\n", "").replace(" ", "")

    # Đếm padding '='
    padding = base64_str.count("=")

    # Tính số byte
    return (len(base64_str) * 3) // 4 - padding
