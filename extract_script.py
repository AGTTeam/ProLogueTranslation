import os
import codecs
import game
from hacktools import common


def run():
    infolder = "data/extract_PACK/"
    outfile = "data/script_output.txt"

    common.logMessage("Extracting SCRIPT to", outfile, "...")
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
                    common.logError("Malformed bin file", file, size, filesize)
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
                    if first:
                        first = False
                        out.write("!FILE:" + file + "\n")
                    sjis = game.readShiftJIS(f)
                    out.write(sjis + "=\n")
                    if ptrpos == firstptr:
                        break
                    f.seek(ptrpos)
                    strptr = f.readUInt()
    common.logMessage("Done! Extracted", len(files), "files")
