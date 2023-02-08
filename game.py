import os
from hacktools import common, nitro

binrange = [(474960, 501390)]
childrange = [(1470840, 1475000)]
wordwrap = 220
wordwrap2 = 216
scriptinject = {
    # Intro part 1
    "dat_script.bin/file003_PACK2/file009.bin": {
        "offsets": [0x9a, 0x101],
        "pointers": [],
        "strings": [
            "<toggle>",
            "Allow me to ask a few questions.",
        ],
        "changes": [],
        # Remove the "wait for click" part
        "removes": [
            (0x10a, 0xb),
        ],
    },
    # Intro part 2
    "dat_script.bin/file003_PACK2/file010.bin": {
        "offsets": [0xb4, 0xea, 0x100, 0x12e, 0x137],
        "pointers": [0xd5, 0xeb],
        "strings": [
            "By the way, how do you feel about sweets?",
            "I see. I think we'll get along just fine.",
            "Is that so? I quite like them, myself.",
            "One last thing. Do you have what it takes|to stand up to evil?",
            "<toggle>",
        ],
        "changes": [],
        # Remove the "wait for click" part
        "removes": [
            (0x109, 0xb),
        ],
    },
}


def readShiftJIS(f, encoding="shift_jisx0213"):
    sjis = ""
    while True:
        b1 = f.readByte()
        if b1 == 0x0:
            break
        if b1 == 0xa:
            sjis += "|"
        elif b1 == 0x9:
            sjis += "\\t"
        elif b1 == 0xb:
            sjis += "\\v"
        elif b1 >= 0x20 and b1 <= 0x7e:
            sjis += chr(b1)
        else:
            b2 = f.readByte()
            f.seek(-2, 1)
            try:
                sjis += f.read(2).decode(encoding).replace("〜", "～")
            except UnicodeDecodeError:
                common.logDebug("UnicodeDecodeError at", f.tell() - 2)
                sjis += "UNK(" + common.toHex(b1) + common.toHex(b2) + ")"
    return replaceCharcodes(sjis)


def writeShiftJIS(f, s, encoding="shift_jisx0213"):
    s = restoreCharcodes(s)
    s = s.replace("\\t", "\t").replace("\\v", "\v")
    s = s.replace("—", "ー").replace("～", "〜")
    x = 0
    while x < len(s):
        c = s[x]
        x += 1
        if c == "|":
            f.writeByte(0xa)
        elif c == "\t":
            f.writeByte(0x9)
        elif c == "\v":
            f.writeByte(0xb)
        elif ord(c) >= 0x20 and ord(c) <= 0x7e:
            f.writeByte(ord(c))
        else:
            f.write(c.encode(encoding))
    f.writeByte(0)


def replaceCharcodes(sjis):
    sjis = sjis.replace("㍑㍑㍑㍑", "<last>")
    sjis = sjis.replace("㌘㌘㌘㌘", "<first>")
    sjis = sjis.replace("㍗㍗㍗㍗", "<name>")
    sjis = sjis.replace("=R", "<red>")
    sjis = sjis.replace("=W", "<white>")
    return sjis


def restoreCharcodes(sjis):
    sjis = sjis.replace("<last>", "㍑㍑㍑㍑")
    sjis = sjis.replace("<first>", "㌘㌘㌘㌘")
    sjis = sjis.replace("<name>", "㍗㍗㍗㍗")
    sjis = sjis.replace("<red>", "=R")
    sjis = sjis.replace("<white>", "=W")
    return sjis


def detectTextCode(s, i=0):
    if s[i] == "\\" and s[1] == "t":
        return 1
    if s[i] == "\\" and s[1] == "v":
        return 1
    if s[i] == "<":
        return len(s[i:].split(">", 1)[0]) + 1
    return 0


def readImage(infolder, file, extension):
    palettefile = file.replace(extension, ".NCLR")
    mapfile = file.replace(extension, ".NSCR")
    cellfile = file.replace(extension, ".NCER")
    ignoredupes = False
    if "dat_adv_menu.bin/file003_PACK2/file002" in infolder + file:
        ignoredupes = True
    if "dat_trap_etc.bin" in infolder + file:
        ignoredupes = True
    # Read the image
    palettes, image, map, cell, width, height = nitro.readNitroGraphic(infolder + palettefile, infolder + file, infolder + mapfile, infolder + cellfile, ignoredupes=ignoredupes)
    if map is not None and map.width == map.height == 512 and image.width == image.height == 256:
        width = height = image.width
    return palettes, image, map, cell, width, height, mapfile, cellfile
