import codecs
import os
import game
import format_pack
from hacktools import common, nds


def detectEncodedString(f, encoding):
    return common.detectEncodedString(f, encoding, [0x23, 0x25, 0x61]).replace("#W", "<white>").replace("#R", "<red>")


def writeEncodedString(f, s, maxlen=0, encoding="shift_jis"):
    common.writeEncodedString(f, s.replace("<white>", "#W").replace("<red>", "#R"), maxlen, encoding)


def repack(data):
    binfile = data + "bin_input.txt"
    binfilein = data + "extract/arm9_dec.bin"
    binfileout = data + "repack/arm9_dec.bin"
    overlayfile = data + "overlay_input.txt"
    overlayfolderin = data + "extract/overlay/"
    overlayfolderout = data + "repack/overlay/"
    childfile = data + "child_input.txt"
    childfilein = data + "extract_CHILD/arm9_dec.bin"
    childfileout = data + "repack_CHILD/arm9_dec.bin"

    nds.repackBIN(game.binrange, readfunc=detectEncodedString, writefunc=writeEncodedString, encoding="shift_jisx0213", binin=binfilein, binout=binfileout, binfile=binfile)
    nds.repackBIN(game.childrange, readfunc=detectEncodedString, writefunc=writeEncodedString, encoding="shift_jisx0213", binin=childfilein, binout=childfileout, binfile=childfile)
    common.logMessage("Repacking overlays from", binfile, "...")
    chartot = transtot = 0
    with codecs.open(overlayfile, "r", "utf-8") as overlayf:
        for overlay in common.getFiles(overlayfolderin, ".bin"):
            if "_dec" not in overlay:
                continue
            common.copyFile(overlayfolderin + overlay, overlayfolderout + overlay)
            section = common.getSection(overlayf, overlay)
            chartot, transtot = common.getSectionPercentage(section, chartot, transtot)
            #common.repackBinaryStrings(section, overlayfolderin + overlay, overlayfolderout + overlay, [(0, os.path.getsize(overlayfolderin + overlay))], readfunc=detectEncodedString, writefunc=writeEncodedString, encoding="shift_jisx0213")
    common.logMessage("Done! Translation is at {0:.2f}%".format((100 * transtot) / chartot))
    common.logMessage("Compressing files ...")
    nds.compressBinary(binfileout, binfileout.replace("_dec", ""))
    nds.compressBinary(childfileout, childfileout.replace("_dec", ""))
    for overlay in common.getFiles(overlayfolderout, ".bin"):
        if "_dec" not in overlay:
            continue
        nds.compressBinary(overlayfolderout + overlay, overlayfolderout + overlay.replace("_dec", ""), False)
        os.remove(overlayfolderout + overlay)
    common.logMessage("Done!")


def extract(data):
    binfile = data + "extract/arm9.bin"
    binfiledec = data + "extract/arm9_dec.bin"
    childfile = data + "extract_CHILD/arm9.bin"
    childfiledec = data + "extract_CHILD/arm9_dec.bin"
    overlayfolder = data + "extract/overlay/"
    binout = data + "bin_output.txt"
    childout = data + "child_output.txt"
    overlayout = data + "overlay_output.txt"
    outpack = data + "extract_CHILD/pack/"
    outfolder = data + "extract_CHILD/pack/"
    outlist = data + "filelist_output.txt"

    common.logMessage("Decompressing binary files ...")
    nds.decompressBinary(binfile, binfiledec)
    nds.decompressBinary(childfile, childfiledec)
    for overlay in common.getFiles(overlayfolder, ".bin"):
        if "_dec" in overlay:
            continue
        nds.decompressBinary(overlayfolder + overlay, overlayfolder + overlay.replace(".bin", "_dec.bin"))
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
    nds.extractBIN(game.binrange, readfunc=detectEncodedString, encoding="shift_jisx0213", binin=binfiledec, binfile=binout)
    nds.extractBIN(game.childrange, readfunc=detectEncodedString, encoding="shift_jisx0213", binin=childfiledec, binfile=childout)
    common.logMessage("Extracting overlays to", overlayout, "...")
    with codecs.open(overlayout, "w", "utf-8") as overlayf:
        totstrings = 0
        for overlay in common.getFiles(overlayfolder, ".bin"):
            if "_dec" not in overlay:
                continue
            first = True
            strings, positions = common.extractBinaryStrings(overlayfolder + overlay, [(0, os.path.getsize(overlayfolder + overlay))], detectEncodedString, "shift_jisx0213")
            totstrings += len(strings)
            for i in range(len(strings)):
                if first:
                    overlayf.write("!FILE:" + overlay + "\n")
                    first = False
                overlayf.write(strings[i] + "=\n")
    common.logMessage("Done! Extracted", totstrings, "lines")
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
            size = format_pack.getPackSize(f)
            filename = "child" + str(i).zfill(3) + ".bin"
            f.seek(find)
            with common.Stream(outpack + filename, "wb") as fout:
                fout.write(f.read(size))
            i += 1
            find = all.find(search, f.tell())
    common.logMessage("Done! Extracted", i, "files.")
