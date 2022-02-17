import codecs
import os
import game
import pack
from hacktools import common, nds


def extract(data):
    binfile = data + "extract/arm9.bin"
    binfiledec = data + "extract/arm9_dec.bin"
    childfile = data + "extract_CHILD/arm9.bin"
    childfiledec = data + "extract_CHILD/arm9_dec.bin"
    binout = data + "bin_output.txt"
    childout = data + "child_output.txt"
    outpack = data + "extract_CHILD/pack/"
    outfolder = data + "extract_CHILD/pack/"
    outlist = data + "filelist_output.txt"

    common.logMessage("Decompressing binary files ...")
    nds.decompressBinary(binfile, binfiledec)
    nds.decompressBinary(childfile, childfiledec)
    common.logMessage("Done!")
    common.logMessage("Extracting file list ...")
    with codecs.open(outlist, "w", "utf-8") as out:
        with common.Stream(binfiledec, "rb") as f:
            f.seek(0x07a5d8)
            for i in range(0x2b0):
                strpointer = f.readUInt() - 0x02000000
                num = f.readUInt()
                pos = f.tell()
                f.seek(strpointer)
                name = f.readNullString()
                f.seek(pos)
                out.write(str(num) + "=" + name + "\n")
    common.logMessage("Done!")
    nds.extractBIN(game.binrange, encoding="shift_jisx0213", binin=binfiledec, binfile=binout)
    nds.extractBIN(game.childrange, encoding="shift_jisx0213", binin=childfiledec, binfile=childout)
    common.logMessage("Extracting embedded PACKs ...")
    common.makeFolder(outfolder)
    size = os.path.getsize(childfiledec)
    with common.Stream(childfiledec, "rb") as f:
        all = f.read()
        search = b"KCAP"
        find = all.find(search)
        i = 0
        while find >= 0:
            f.seek(find)
            size = pack.getSize(f)
            filename = "child" + str(i).zfill(3) + ".bin"
            f.seek(find)
            with common.Stream(outpack + filename, "wb") as fout:
                fout.write(f.read(size))
            i += 1
            find = all.find(search, f.tell())
    common.logMessage("Done! Extracted", i, "files.")
