"""QR codes for the buttons of a slide, without any package: byte mode, error correction level M (15 %), the smallest
version that holds the text, the mask with the lowest penalty (ISO/IEC 18004). svg() gives an inline SVG with a white
quiet zone, so the code reads on dark and coloured slides as well."""

# error correction codewords per block and number of blocks for level M, by version 1 to 40
_ECC_M = [-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26, 26, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28]
_BLOCKS_M = [-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5, 5, 8, 9, 9, 10, 10, 11, 13, 14, 16, 17, 17, 18, 20, 21, 23, 25, 26, 28, 29, 31, 33, 35, 37, 38, 40, 43, 45, 47, 49]
_FORMAT_M = 0                                               # the two format bits of level M


def _raw_modules(ver):
    """Modules left for data and error correction once the function patterns are drawn."""
    n = (16 * ver + 128) * ver + 64
    if ver >= 2:
        a = ver // 7 + 2
        n -= (25 * a - 10) * a - 55
        if ver >= 7:
            n -= 36
    return n

def _data_codewords(ver):
    return _raw_modules(ver) // 8 - _ECC_M[ver] * _BLOCKS_M[ver]

def _gf_mul(x, y):
    z = 0
    for i in reversed(range(8)):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z

def _rs_divisor(degree):
    out, root = [0] * (degree - 1) + [1], 1
    for _ in range(degree):
        for j in range(degree):
            out[j] = _gf_mul(out[j], root)
            if j + 1 < degree:
                out[j] ^= out[j + 1]
        root = _gf_mul(root, 0x02)
    return out

def _rs_remainder(data, divisor):
    out = [0] * len(divisor)
    for b in data:
        f = b ^ out.pop(0)
        out.append(0)
        for i, c in enumerate(divisor):
            out[i] ^= _gf_mul(c, f)
    return out

def _alignment(ver, size):
    if ver == 1:
        return []
    a = ver // 7 + 2
    step = (ver * 8 + a * 3 + 5) // (a * 4 - 4) * 2
    return [6] + sorted(size - 7 - i * step for i in range(a - 1))


def matrix(text):
    """The modules of the code for text, as rows of booleans (True is dark)."""
    data = text.encode("utf-8")
    for ver in range(1, 41):
        bits = 4 + (8 if ver < 10 else 16) + 8 * len(data)
        if bits <= _data_codewords(ver) * 8:
            break
    else:
        raise ValueError("too long for a QR code")
    size = ver * 4 + 17
    # the bit stream: byte mode, count, data, terminator, padding
    bb = []
    put = lambda v, n: bb.extend((v >> i) & 1 for i in reversed(range(n)))
    put(0b0100, 4); put(len(data), 8 if ver < 10 else 16)
    for b in data:
        put(b, 8)
    cap = _data_codewords(ver) * 8
    put(0, min(4, cap - len(bb)))
    put(0, (8 - len(bb) % 8) % 8)
    pad = 0xEC
    while len(bb) < cap:
        put(pad, 8); pad ^= 0xEC ^ 0x11
    words = [int("".join(map(str, bb[i:i + 8])), 2) for i in range(0, len(bb), 8)]
    # error correction in blocks, interleaved
    nb, ecl, raw = _BLOCKS_M[ver], _ECC_M[ver], _raw_modules(ver) // 8
    short, slen = nb - raw % nb, raw // nb
    div, blocks, k = _rs_divisor(ecl), [], 0
    for i in range(nb):
        dat = words[k:k + slen - ecl + (0 if i < short else 1)]
        k += len(dat)
        ecc = _rs_remainder(dat, div)
        if i < short:
            dat = dat + [0]
        blocks.append(dat + ecc)
    stream = [blk[i] for i in range(len(blocks[0])) for j, blk in enumerate(blocks) if i != slen - ecl or j >= short]

    mods = [[False] * size for _ in range(size)]
    fn = [[False] * size for _ in range(size)]
    def setf(x, y, dark):
        mods[y][x] = dark; fn[y][x] = True
    for i in range(size):                                   # timing patterns
        setf(6, i, i % 2 == 0); setf(i, 6, i % 2 == 0)
    for cx, cy in ((3, 3), (size - 4, 3), (3, size - 4)):   # finder patterns with their separators
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                x, y = cx + dx, cy + dy
                if 0 <= x < size and 0 <= y < size:
                    setf(x, y, max(abs(dx), abs(dy)) not in (2, 4))
    al = _alignment(ver, size)
    for i, ax in enumerate(al):
        for j, ay in enumerate(al):
            if (i == 0 and j == 0) or (i == 0 and j == len(al) - 1) or (i == len(al) - 1 and j == 0):
                continue
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    setf(ax + dx, ay + dy, max(abs(dx), abs(dy)) != 1)
    def format_bits(mask):
        d = _FORMAT_M << 3 | mask
        r = d
        for _ in range(10):
            r = (r << 1) ^ ((r >> 9) * 0x537)
        return (d << 10 | r) ^ 0x5412
    def draw_format(mask):
        b = format_bits(mask)
        bit = lambda i: (b >> i) & 1 == 1
        for i in range(6):
            setf(8, i, bit(i))
        setf(8, 7, bit(6)); setf(8, 8, bit(7)); setf(7, 8, bit(8))
        for i in range(9, 15):
            setf(14 - i, 8, bit(i))
        for i in range(8):
            setf(size - 1 - i, 8, bit(i))
        for i in range(8, 15):
            setf(8, size - 15 + i, bit(i))
        setf(8, size - 8, True)
    draw_format(0)
    if ver >= 7:                                            # version information, twice
        r = ver
        for _ in range(12):
            r = (r << 1) ^ ((r >> 11) * 0x1F25)
        vb = ver << 12 | r
        for i in range(18):
            d, a, b = (vb >> i) & 1 == 1, size - 11 + i % 3, i // 3
            setf(a, b, d); setf(b, a, d)
    # data in the zigzag of two-module columns, bottom right first
    i, right, total = 0, size - 1, len(stream) * 8
    while right >= 1:
        if right == 6:
            right = 5
        for vert in range(size):
            for j in range(2):
                x = right - j
                y = size - 1 - vert if ((right + 1) & 2) == 0 else vert
                if not fn[y][x] and i < total:
                    mods[y][x] = (stream[i >> 3] >> (7 - (i & 7))) & 1 == 1
                    i += 1
        right -= 2
    masks = [lambda x, y: (x + y) % 2 == 0, lambda x, y: y % 2 == 0, lambda x, y: x % 3 == 0, lambda x, y: (x + y) % 3 == 0,
             lambda x, y: (x // 3 + y // 2) % 2 == 0, lambda x, y: x * y % 2 + x * y % 3 == 0,
             lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0, lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0]
    def apply(m):
        for y in range(size):
            for x in range(size):
                if not fn[y][x] and masks[m](x, y):
                    mods[y][x] = not mods[y][x]
    best, low = 0, None
    for m in range(8):                                      # each mask once, the one with the lowest penalty stays
        apply(m); draw_format(m)
        p = _penalty(mods)
        if low is None or p < low:
            best, low = m, p
        apply(m)
    apply(best); draw_format(best)
    return mods

def _penalty(m):
    size, p = len(m), 0
    lines = [row for row in m] + [[m[y][x] for y in range(size)] for x in range(size)]
    for line in lines:
        run, prev = 0, None
        for v in line:
            if v == prev:
                run += 1
                if run == 5: p += 3
                elif run > 5: p += 1
            else:
                run, prev = 1, v
        s = "".join("1" if v else "0" for v in line)
        p += 40 * (s.count("10111010000") + s.count("00001011101"))
    for y in range(size - 1):
        for x in range(size - 1):
            if m[y][x] == m[y][x + 1] == m[y + 1][x] == m[y + 1][x + 1]:
                p += 3
    dark = sum(map(sum, m))
    p += (abs(dark * 20 - size * size * 10) // (size * size)) * 10
    return p


def svg(text, border=4):
    """An inline SVG of the code: dark modules as one path on a white field with the quiet zone around it.
    It has no size of its own, the stylesheet gives it one."""
    mods = matrix(text)
    n = len(mods) + 2 * border
    path = []
    for y, row in enumerate(mods):
        x = 0
        while x < len(row):
            if row[x]:
                s = x
                while x < len(row) and row[x]:
                    x += 1
                path.append(f"M{s + border} {y + border}h{x - s}v1h{s - x}z")
            else:
                x += 1
    return (f'<svg viewBox="0 0 {n} {n}" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges" role="img" aria-label="QR">'
            f'<rect width="{n}" height="{n}" fill="#fff"/><path fill="#000" d="{"".join(path)}"/></svg>')
