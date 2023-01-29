def decode_text(text):
    """decode input string to be used by device"""
    return text.encode("UTF-8")


def gen_chunk_iter(data, offset=0, total_size=0, chunk_size=65536):
    """generate iterator for blocks of chunk_size"""
    if total_size:
        n = total_size
    else:
        n = len(data)
    num_blocks = n // chunk_size
    remainder = n % chunk_size
    for x in range(num_blocks):
        yield (offset, data[offset : offset + chunk_size])
        offset += chunk_size
    if remainder > 0:
        yield (offset, data[offset : offset + remainder])
