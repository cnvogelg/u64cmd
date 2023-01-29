# map {ctrl_code} to byte code
CTRL_TABLE = {"": 0x00, "nl": 0x0A, "cr": 0x0D}


def gen_split_ctrl_iter(input):
    """split input text into normal text and ctrl chars.

    (False, normal_txt) or (True, ctrl_cmd)
    """
    cur = bytearray()
    in_cmd = False
    for ch in input:
        if ch == ord("{"):
            assert not in_cmd
            if cur:
                yield (False, cur)
            cur = bytearray()
            in_cmd = True
        elif ch == ord("}"):
            assert in_cmd
            yield (True, cur)
            cur = bytearray()
            in_cmd = False
        else:
            cur.append(ch)
    if cur:
        yield (False, cur)


def decode_text(text):
    """decode input string to be used by device"""
    data = text.encode("ascii")
    result = bytearray()
    for is_cmd, field in gen_split_ctrl_iter(data):
        if is_cmd:
            key = field.decode("ascii").lower()
            code = CTRL_TABLE[key]
            result.append(code)
        else:
            result += field
    return result


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
