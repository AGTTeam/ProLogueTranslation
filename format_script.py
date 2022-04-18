import os
import codecs
import game
from hacktools import common, nitro


class ScriptFile:
    def __init__(self):
        self.size = 0
        self.stringsection = 0
        self.strings = []


def readScript(f, filesize):
    script = ScriptFile()
    script.size = f.readUInt()
    if script.size != filesize:
        common.logWarning("Malformed bin file", script.size, filesize)
        return None
    f.seek(8, 1)
    script.stringsection = f.readUInt()
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
        allsections = common.getSection(scriptin, "")
        for file in common.showProgress(common.getFiles(infolder, ".bin")):
            if "file000.bin" in file:
                continue
            common.logDebug("Processing", file, "...")
            filesize = os.path.getsize(infolder + file)
            with common.Stream(infolder + file, "rb") as fin:
                script = readScript(fin, filesize)
                if script is None or len(script.strings) == 0:
                    continue
                section = common.getSection(scriptin, file)
                chartot, transtot = common.getSectionPercentage(section, chartot, transtot)
                fin.seek(0)
                common.makeFolders(os.path.dirname(outfolder + file))
                with common.Stream(outfolder + file, "wb") as f:
                    f.write(fin.read(script.stringsection))
                    ptrpos = fin.tell()
                    firstptr = fin.readUInt()
                    f.seek(firstptr)
                    for oldstring in script.strings:
                        addv = False
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
                        f.writeUIntAt(ptrpos, f.tell())
                        ptrpos += 4
                        if addv:
                            newstring += "\\v"
                        game.writeShiftJIS(f, newstring)
                        # Pad with 0s
                        if f.tell() % 4 > 0:
                            f.writeZero(4 - (f.tell() % 4))
                    # Pad with 0s
                    if f.tell() % 16 > 0:
                        f.writeZero(16 - (f.tell() % 16))
                    f.writeUIntAt(0, f.tell())


def extract(data):
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
                    if string not in foundstr:
                        foundstr.append(string)
                        out.write(string + "=\n")
    common.logMessage("Done! Extracted", len(files), "files")
