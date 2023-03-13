import os
import codecs
import struct
import game
from hacktools import common, nitro


class ScriptFile:
    def __init__(self):
        self.size = 0
        self.codesize = 0
        self.unk = 0
        self.stringsection = 0
        self.stringoffs = []
        self.strings = []


def readScript(f, filesize, parsescript=False):
    script = ScriptFile()
    script.size = f.readUInt()
    if script.size != filesize:
        common.logDebug("Malformed bin file", script.size, filesize)
        return None
    script.codesize = f.readUInt()
    script.unk = f.readUInt()
    script.stringsection = f.readUInt()
    common.logDebug("size", common.toHex(script.size), "codesize", common.toHex(script.codesize), "unk", common.toHex(script.unk), "stringsection", common.toHex(script.stringsection))
    if parsescript:
        f.seek(0x10)
        try:
            while f.tell() < script.codesize:
                offset = f.tell()
                opcode = f.readByte()
                if opcode == 0:
                    break
                opdata = ""
                while True:
                    data = f.readByte()
                    opdata += common.toHex(data).zfill(2) + " "
                    if data == 0xfe:
                        break
                    # This jump opcode has no 0xfe termination
                    if opcode == 0x25 and len(opdata) == 3 * 4:
                        break
                common.logDebug("  offset", common.toHex(offset).zfill(4), "codeoff", common.toHex(offset - 0x10).zfill(4), "opcode", common.toHex(opcode).zfill(2), "data", opdata)
        except struct.error:
            common.logDebug("Malformed file")
    if script.stringsection != filesize:
        f.seek(script.stringsection)
        firstptr = strptr = f.readUInt()
        while strptr != 0:
            ptrpos = f.tell()
            f.seek(strptr)
            sjis = game.readShiftJIS(f)
            script.strings.append(sjis)
            if ptrpos == firstptr:
                break
            f.seek(ptrpos)
            strptr = f.readUInt()
    return script


def repack(data):
    infile = data + "script_input.txt"
    fontfile = data + "replace_PACK/dat_font_00.bin/file002.NFTR"
    infolder = data + "extract_PACK/"
    outfolder = data + "repack_PACK/"
    chartot = transtot = 0

    common.logMessage("Repacking SCRIPT from", infile, "...")
    glyphs = nitro.readNFTR(fontfile).glyphs
    with codecs.open(infile, "r", "utf-8") as scriptin:
        allsections = common.getSection(scriptin, "", justone=False)
        for file in common.showProgress(common.getFiles(infolder, ".bin")):
            if "file000.bin" in file:
                continue
            #if file not in game.scriptinject:
            #    continue
            common.logDebug("Processing", file, "...")
            filesize = os.path.getsize(infolder + file)
            with common.Stream(infolder + file, "rb") as fin:
                script = readScript(fin, filesize)
                if script is None or (len(script.strings) == 0 and file not in game.scriptinject):
                    continue
                section = common.getSection(scriptin, file)
                chartot, transtot = common.getSectionPercentage(section, chartot, transtot)
                fin.seek(0)
                common.makeFolders(os.path.dirname(outfolder + file))
                common.copyFile(infolder + file, outfolder + file)
                with common.Stream(outfolder + file, "rb+") as f:
                    if len(script.strings) > 0:
                        f.write(fin.read(script.stringsection))
                        ptrpos = fin.tell()
                        firstptr = fin.readUInt()
                        f.seek(firstptr)
                        for i in range(len(script.strings)):
                            addv = False
                            oldstring = script.strings[i]
                            if oldstring.endswith("\\v"):
                                oldstring = oldstring[:-2]
                                addv = True
                            newstring = oldstring
                            if oldstring in section and section[oldstring][0] != "":
                                newstring = section[oldstring][0]
                                if len(section[oldstring]) > 1:
                                    section[oldstring].pop(0)
                            elif oldstring in allsections and allsections[oldstring][0] != "":
                                newstring = allsections[oldstring][0]
                            if newstring != oldstring:
                                newstring = common.wordwrap(newstring, glyphs, game.wordwrap, game.detectTextCode, sectionsep="\\v")
                                # Check wordwrapping results for long lines
                                newstringcheck = newstring.split("\\v")
                                for check in newstringcheck:
                                    if check.count("|") > 2:
                                        common.logWarning("Line too long:", newstring)
                                        break
                            f.writeUIntAt(ptrpos, f.tell())
                            ptrpos += 4
                            if addv:
                                newstring += "\\v"
                            script.strings[i] = newstring
                            common.logDebug("Writing string", newstring)
                            game.writeShiftJIS(f, newstring)
                            # Pad with 0s
                            if f.tell() % 4 > 0:
                                f.writeZero(4 - (f.tell() % 4))
                        # Pad with 0s
                        if f.tell() % 16 > 0:
                            f.writeZero(16 - (f.tell() % 16))
                        f.truncate()
                        f.writeUIntAt(0, f.tell())
                    if file in game.scriptinject:
                        injectdata = game.scriptinject[file]
                        for change in injectdata["changes"]:
                            f.writeByteAt(change[0], change[1])
                        if len(injectdata["offsets"]) > 0:
                            inject(f, script, injectdata["offsets"], injectdata["strings"], injectdata["pointers"], injectdata["removes"])


def inject(f:common.Stream, script, injectoffs, newstrs, ptrs, removes):
    # Read the original code before we inject
    codes = []
    remi = 0
    for i in range(len(injectoffs)):
        f.seek(injectoffs[i])
        if i + 1 == len(injectoffs):
            copylen = script.stringsection - injectoffs[i]
        else:
            copylen = injectoffs[i+1] - injectoffs[i]
        code = f.read(copylen)
        if remi < len(removes) and removes[remi][0] < injectoffs[i] + copylen:
            remove = removes[remi][0] - injectoffs[i]
            codes.append(code[:remove] + code[remove + removes[remi][1]:])
            remi += 1
        else:
            codes.append(code)
    # Inject the new string codes
    injectsizes = []
    for i in range(len(injectoffs)):
        injectoff = injectoffs[i] + sum(injectsizes)
        for j in range(len(removes)):
            if injectoffs[i] >= removes[j][0]:
                injectoff -= removes[j][1]
        f.seek(injectoff)
        if newstrs[i] == "<toggle>":
            f.writeByte(0xf0)
        else:
            script.strings.append(newstrs[i])
            injectStringCode(f, len(script.strings) - 1)
        injectsizes.append(f.tell() - injectoff)
        f.write(codes[i])
    # Pad with 0s before string pointers offset
    if f.tell() % 16 > 0:
        f.writeZero(16 - (f.tell() % 16))
    stringoff = f.tell()
    # Update the in-script pointers
    for i in range(len(ptrs)):
        ptroff = ptrs[i]
        for j in range(len(injectoffs)):
            if ptrs[i] >= injectoffs[j]:
                ptroff += injectsizes[j]
        for j in range(len(removes)):
            if ptrs[i] >= removes[j][0]:
                ptroff -= removes[j][1]
        f.seek(ptroff)
        originalptr = ptr = f.readUInt()
        for j in range(len(injectoffs)):
            if originalptr >= injectoffs[j]:
                ptr += injectsizes[j]
        for j in range(len(removes)):
            if originalptr >= removes[j][0]:
                ptr -= removes[j][1]
        f.writeUIntAt(ptroff, ptr)
    # Make room for the string pointers and pad with 0s
    f.seek(stringoff)
    for i in range(len(script.strings)):
        f.writeUInt(0)
    if f.tell() % 16 > 0:
        f.writeZero(16 - (f.tell() % 16))
    # Write the strings and their pointers
    for i in range(len(script.strings)):
        f.writeUIntAt(stringoff + i * 4, f.tell())
        game.writeShiftJIS(f, script.strings[i])
        if f.tell() % 4 > 0:
            f.writeZero(4 - (f.tell() % 4))
    if f.tell() % 16 > 0:
        f.writeZero(16 - (f.tell() % 16))
    # Write the new header
    f.seek(0, 2)
    f.writeUIntAt(0x0, f.tell())
    codesize = f.readUIntAt(0x4)
    f.writeUIntAt(0x4, codesize + sum(injectsizes))
    f.writeUIntAt(0x8, stringoff)
    f.writeUIntAt(0xc, stringoff)


def injectStringCode(f:common.Stream, index):
    f.writeByte(0x44)
    # 30 02 31 xx 00 00 00 03 ff (xx = screen, 0 = bottom, 1 = top)
    f.writeByte(0x30)
    f.writeByte(0x2)
    f.writeByte(0x31)
    f.writeByte(0x1)
    f.writeByte(0x0)
    f.writeByte(0x0)
    f.writeByte(0x0)
    f.writeByte(0x3)
    f.writeByte(0xff)
    # 30 02 31 00 00 00 00 03 10
    f.writeByte(0x30)
    f.writeByte(0x2)
    f.writeByte(0x31)
    f.writeByte(0x0)
    f.writeByte(0x0)
    f.writeByte(0x0)
    f.writeByte(0x0)
    f.writeByte(0x3)
    f.writeByte(0x10)
    # 31 xx 00 00 00 ff (xx = nameplate)
    f.writeByte(0x31)
    f.writeByte(0x2)
    f.writeByte(0x0)
    f.writeByte(0x0)
    f.writeByte(0x0)
    f.writeByte(0xff)
    # 32 xx 00 00 00 fe (xx = string index)
    f.writeByte(0x32)
    f.writeByte(index)
    f.writeByte(0x0)
    f.writeByte(0x0)
    f.writeByte(0x0)
    f.writeByte(0xfe)


def extract(data, skipdupes=True):
    infolder = data + "extract_PACK/"
    outfile = data + "script_output.txt"

    common.logMessage("Extracting SCRIPT to", outfile, "...")
    foundstr = []
    with codecs.open(outfile, "w", "utf-8") as out:
        files = common.getFiles(infolder, ".bin")
        for file in common.showProgress(files):
            if "file000.bin" in file:
                continue
            common.logDebug("Processing", file, "...")
            filesize = os.path.getsize(infolder + file)
            with common.Stream(infolder + file, "rb") as f:
                script = readScript(f, filesize)
                if script is None or len(script.strings) == 0:
                    continue
                out.write("!FILE:" + file + "\n")
                for string in script.strings:
                    if string.endswith("\\v"):
                        string = string[:-2]
                    if not skipdupes or string not in foundstr:
                        foundstr.append(string)
                        out.write(string + "=\n")
    common.logMessage("Done! Extracted", len(files), "files")
