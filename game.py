import os
from hacktools import common, nitro

binrange = [(474960, 501390)]
childrange = [(1470840, 1475000)]
wordwrap = 220


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
    return sjis


def restoreCharcodes(sjis):
    sjis = sjis.replace("<last>", "㍑㍑㍑㍑")
    sjis = sjis.replace("<first>", "㌘㌘㌘㌘")
    sjis = sjis.replace("<name>", "㍗㍗㍗㍗")
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
    # Read the image
    palettes, image, map, cell, width, height = nitro.readNitroGraphic(infolder + palettefile, infolder + file, infolder + mapfile, infolder + cellfile)
    if map is not None and map.width == map.height == 512 and image.width == image.height == 256:
        width = height = image.width
    return palettes, image, map, cell, width, height, map, cellfile
