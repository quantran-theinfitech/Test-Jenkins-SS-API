def chunk_lists(lst, sublist_len=4, max_len=8192):
    """
    split list into chunks
    """
    chunks = []
    current_chunk = []
    current_length = 0

    for s in lst:
        current_length = len(str(current_chunk))
        if len(current_chunk) < sublist_len and current_length <= max_len:
            current_chunk.append(s)
        else:
            chunks.append(current_chunk)
            current_chunk = [s]

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def trim_email(email):
    local, domain = email.split('@')
    if '+' in local:
        local = local.split('+')[0]
    return f"{local}@{domain}"