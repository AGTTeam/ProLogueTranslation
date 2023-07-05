import codecs
import os
import struct
import game
import format_pack
from hacktools import common, nds, nitro


def detectEncodedString(f, encoding):
    return game.replaceCharcodes(common.detectEncodedString(f, encoding, [0x23, 0x25, 0x61]).replace("#W", "<white>").replace("#R", "<red>"))


def writeEncodedString(f, s, maxlen=0, encoding="shift_jis"):
    global glyphs
    # Wordwrap the string
    wordwrap = game.wordwrap
    if s.startswith(">>"):
        s = s[2:]
        wordwrap = game.wordwrap2
    s = common.wordwrap(s, glyphs, wordwrap, game.detectTextCode, sectionsep="\\v")
    return common.writeEncodedString(f, game.restoreCharcodes(s.replace("<white>", "#W").replace("<red>", "#R")), maxlen, encoding)


def repack(data):
    binfile = data + "bin_input.txt"
    binfilein = data + "extract/arm9_dec.bin"
    binfileout = data + "repack/arm9_dec.bin"
    headerin = data + "extract/header.bin"
    headerout = data + "repack/header.bin"
    childheaderin = data + "extract_CHILD/header.bin"
    childheaderout = data + "repack_CHILD/header.bin"
    ovtablein = data + "extract/y9.bin"
    ovtableout = data + "repack/y9.bin"
    overlayfile = data + "overlay_input.txt"
    overlayfolderin = data + "extract/overlay/"
    overlayfolderout = data + "repack/overlay/"
    childfile = data + "child_input.txt"
    childfilein = data + "extract_CHILD/arm9_dec.bin"
    childfileout = data + "repack_CHILD/arm9_dec.bin"
    childfilepack = data + "repack_CHILD/pack/"
    fontfile = data + "replace_PACK/dat_font_00.bin/file002.NFTR"

    global glyphs
    glyphs = nitro.readNFTR(fontfile).glyphs
    # Expand and repack the bin files
    fallbackf = common.Stream().__enter__()
    injectfallback = 0x02330020
    injectsize = 0x13c80
    injectoffset = nds.expandBIN(binfilein, binfileout, headerin, headerout, injectsize, injectfallback)
    nds.repackBIN(game.binrange, readfunc=detectEncodedString, writefunc=writeEncodedString, encoding="shift_jisx0213", binin=binfilein, binout=binfileout, binfile=binfile, fallbackf=fallbackf, injectfallback=injectfallback, nocopy=True)
    childfallbackf = common.Stream().__enter__()
    childinjectfallback = 0x0226e7a0
    childinjectsize = 0x50000
    childinjectoffset = nds.expandBIN(childfilein, childfileout, childheaderin, childheaderout, childinjectsize, childinjectfallback)
    nds.repackBIN(game.childrange, readfunc=detectEncodedString, writefunc=writeEncodedString, encoding="shift_jisx0213", binin=childfilein, binout=childfileout, binfile=childfile, fallbackf=childfallbackf, injectfallback=childinjectfallback, nocopy=True)
    # Pad to 0x10
    if childfallbackf.tell() % 0x10 > 0:
        childfallbackf.writeZero(0x10 - (childfallbackf.tell() % 0x10))
    # Update the embedded PACK files
    with common.Stream(childfilein, "rb") as f:
        embeds = getEmbeddedPACK(f)
    ptrs = []
    with common.Stream(childfileout, "rb+") as f:
        f.seek(0x2e988)
        currentf = f
        for i in reversed(range(len(embeds))):
            embed = embeds[i]
            filename = childfilepack + embed["filename"]
            if os.path.isfile(filename):
                with common.Stream(filename, "rb") as fin:
                    newdata = fin.read()
            else:
                with common.Stream(filename.replace("repack_", "extract_"), "rb") as fin:
                    newdata = fin.read()
            common.logDebug(i, "old size", common.toHex(embed["size"]), "new size", common.toHex(len(newdata)))
            if currentf == f and f.tell() + len(newdata) > 0x124e08:
                currentf = childfallbackf
                common.logDebug(" moving to fallback")
            oldptr = 0x02000000 + embed["offset"]
            if currentf == f:
                newptr = 0x02000000 + currentf.tell()
            else:
                newptr = childinjectfallback + currentf.tell()
            ptrs.append((oldptr, newptr))
            currentf.write(newdata)
    # Update the pointers
    with common.Stream(childfileout, "rb+") as f:
        allbin = f.read()
        for ptr in ptrs:
            pointersearch = struct.pack("<I", ptr[0])
            index = 0
            common.logDebug("Searching for pointer", common.toHex(ptr[0]))
            while index < len(allbin):
                index = allbin.find(pointersearch, index)
                if index < 0:
                    break
                common.logDebug("Replaced pointer at", common.toHex(index))
                f.seek(index)
                f.writeUInt(ptr[1])
                index += 4
    # Repack the overlays
    common.copyFile(ovtablein, ovtableout)
    with common.Stream(ovtableout, "rb+") as ovt:
        common.logMessage("Repacking overlays from", overlayfile, "...")
        chartot = transtot = 0
        ovfiles = common.getFiles(overlayfolderin, ".bin")
        with codecs.open(overlayfile, "r", "utf-8") as overlayf:
            for i in range(len(ovfiles)):
                overlay = ovfiles[i]
                if "_dec" not in overlay:
                    continue
                common.logDebug("Processing", overlay)
                common.copyFile(overlayfolderin + overlay, overlayfolderout + overlay)
                section = common.getSection(overlayf, overlay)
                chartot, transtot = common.getSectionPercentage(section, chartot, transtot)
                filesize = os.path.getsize(overlayfolderin + overlay)
                # Read the ram address from the overlay table
                ovt.seek(((i - 1) // 2) * 0x20 + 0x4)
                ramaddr = ovt.readUInt()
                notfound = common.repackBinaryStrings(section, overlayfolderin + overlay, overlayfolderout + overlay, [(0, filesize)], [], readfunc=detectEncodedString, writefunc=writeEncodedString, encoding="shift_jisx0213", pointerstart=ramaddr, injectstart=ramaddr, fallbackf=fallbackf, injectfallback=injectfallback)
                for pointer in notfound:
                    common.logError("Pointer", common.toHex(pointer.old), "->", common.toHex(pointer.new), "not found for string", pointer.str)
        common.logMessage("Done! Translation is at {0:.2f}%".format((100 * transtot) / chartot))
        # Write the fallback files
        if fallbackf.tell() > injectsize:
            common.logError("Fallback file is too big by", (fallbackf.tell() - injectsize), "bytes")
            fallbackf.seek(injectsize)
            fallbackf.truncate()
        else:
            fallbackf.writeZero(injectsize - fallbackf.tell())
        fallbackf.seek(0)
        with common.Stream(binfileout, "rb+") as binf:
            binf.seek(injectoffset)
            binf.write(fallbackf.read(injectsize))
        if childfallbackf.tell() > childinjectsize:
            common.logError("Child fallback file is too big by", (childfallbackf.tell() - childinjectsize), "bytes")
            childfallbackf.seek(childinjectsize)
            childfallbackf.truncate()
        else:
            childfallbackf.writeZero(childinjectsize - childfallbackf.tell())
        childfallbackf.seek(0)
        with common.Stream(childfileout, "rb+") as binf:
            binf.seek(childinjectoffset)
            binf.write(childfallbackf.read(childinjectsize))
        # Apply armips patches, compress and update overlay table
        common.armipsPatch(common.bundledFile("bin_patch.asm"))
        common.armipsPatch(common.bundledFile("bin_child_patch.asm"))
        common.logMessage("Compressing files ...")
        nds.compressBinary(binfileout, binfileout.replace("_dec", ""))
        nds.compressBinary(childfileout, childfileout.replace("_dec", ""))
        ovfiles = common.getFiles(overlayfolderout, ".bin")
        for i in range(len(ovfiles)):
            overlay = ovfiles[i]
            if "_dec" not in overlay:
                continue
            nds.compressBinary(overlayfolderout + overlay, overlayfolderout + overlay.replace("_dec", ""), False)
            # Update uncompressed and compressed size
            ovt.seek(((i - 1) // 2) * 0x20 + 0x8)
            ovt.writeUInt(os.path.getsize(overlayfolderout + overlay))
            ovt.seek(((i - 1) // 2) * 0x20 + 0x1c)
            ovt.writeUShort(os.path.getsize(overlayfolderout + overlay.replace("_dec", "")))
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
                # overlayf.write(str(positions[i]) + "!" + strings[i] + "=\n")
                overlayf.write(strings[i] + "=\n")
    common.logMessage("Done! Extracted", totstrings, "lines")
    common.logMessage("Extracting embedded PACKs ...")
    common.makeFolder(outfolder)
    with common.Stream(childfiledec, "rb") as f:
        embeds = getEmbeddedPACK(f)
        for embed in embeds:
            f.seek(embed["offset"])
            with common.Stream(outpack + embed["filename"], "wb") as fout:
                fout.write(f.read(embed["size"]))
    common.logMessage("Done! Extracted", i, "files.")


def getEmbeddedPACK(f):
    ret = []
    all = f.read()
    search = b"KCAP"
    find = all.find(search)
    i = 0
    while find >= 0:
        f.seek(find)
        size = format_pack.getPackSize(f)
        filename = "child" + str(i).zfill(3) + ".bin"
        ret.append({"offset": find, "size": size, "filename": filename})
        common.logDebug("Embbeded pack at", common.toHex(find), "with size", common.toHex(size))
        f.seek(find + size)
        find = all.find(search, f.tell())
        i += 1
    return ret
