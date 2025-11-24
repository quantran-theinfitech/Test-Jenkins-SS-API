from typing import Optional

from bs4 import BeautifulSoup


def has_signature(email_signature: Optional[str]) -> bool:
    if email_signature is None:
        return False
    else:
        soup = BeautifulSoup(email_signature, "html.parser")
        text = soup.get_text(strip=True)
        if not text:
            return False
        else:
            return True
