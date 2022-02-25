import os
import codecs
import game
from hacktools import common


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
                first = True
                size = f.readUInt()
                if size != filesize:
                    common.logWarning("Malformed bin file", file, size, filesize)
                    continue
                f.seek(8, 1)
                stringsection = f.readUInt()
                if stringsection == filesize:
                    continue
                f.seek(stringsection)
                firstptr = strptr = f.readUInt()
                while strptr != 0:
                    ptrpos = f.tell()
                    f.seek(strptr)
                    sjis = game.readShiftJIS(f)
                    if sjis.endswith("\\v"):
                        sjis = sjis[:-2]
                    if sjis not in foundstr:
                        if first:
                            first = False
                            out.write("!FILE:" + file + "\n")
                        foundstr.append(sjis)
                        out.write(sjis + "=\n")
                    if ptrpos == firstptr:
                        break
                    f.seek(ptrpos)
                    strptr = f.readUInt()
    common.logMessage("Done! Extracted", len(files), "files")
