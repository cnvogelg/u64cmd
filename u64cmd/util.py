# map {ctrl_code} to byte code like petcat does
CTRL_TABLE = {
    "": 0x00,
    "stop": 0x03,
    "wht": 0x05,
    "dish": 0x08,
    "ensh": 0x09,
    "nl": 0x0A,
    "$0a": 0x0A,
    "cr": 0x0D,
    "return": 0x0D,
    "swlc": 0x0E,
    "down": 0x11,
    "rvon": 0x12,
    "home": 0x13,
    "del": 0x14,
    "esc": 0x1B,
    "red": 0x1C,
    "right": 0x1D,
    "grn": 0x1E,
    "blu": 0x1F,
    "space": 0x20,
    "orng": 0x81,
    "f1": 0x85,
    "f3": 0x86,
    "f5": 0x87,
    "f7": 0x88,
    "f2": 0x89,
    "f4": 0x8A,
    "f6": 0x8B,
    "f8": 0x8C,
    "sret": 0x8D,
    "swuc": 0x8E,
    "blk": 0x90,
    "up": 0x91,
    "rvof": 0x92,
    "clr": 0x93,
    "inst": 0x94,
    "brn": 0x95,
    "lred": 0x96,
    "gry1": 0x97,
    "gry2": 0x98,
    "lgrn": 0x99,
    "lblu": 0x9A,
    "gry3": 0x9B,
    "pur": 0x9C,
    "left": 0x9D,
    "yel": 0x9E,
    "cyn": 0x9F,
    "sspace": 0xA0,
}


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
            if key in CTRL_TABLE:
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
