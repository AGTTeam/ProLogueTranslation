import os
from hacktools import common, nitro

binrange = [(474960, 501390)]
childrange = [(1470840, 1475000)]


def readShiftJIS(f, encoding="shift_jisx0213"):
    sjis = ""
    while True:
        b1 = f.readByte()
        if b1 == 0x00:
            break
        if b1 == 0x0A:
            sjis += "|"
        elif b1 == 0x09:
            sjis += "\\t"
        elif b1 == 0x0b:
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


def replaceCharcodes(sjis):
    sjis = sjis.replace("㍑㍑㍑㍑", "<last>")
    sjis = sjis.replace("㌘㌘㌘㌘", "<first>")
    sjis = sjis.replace("㍗㍗㍗㍗", "<name>")
    return sjis


def readImage(infolder, file, extension):
    palettefile = file.replace(extension, ".NCLR")
    mapfile = file.replace(extension, ".NSCR")
    cellfile = file.replace(extension, ".NCER")
    # Read the image
    palettes, image, map, cell, width, height = nitro.readNitroGraphic(infolder + palettefile, infolder + file, infolder + mapfile, infolder + cellfile)
    if map is not None and map.width == map.height == 512 and image.width == image.height == 256:
        width = height = image.width
    return palettes, image, map, cell, width, height, map, cellfile
