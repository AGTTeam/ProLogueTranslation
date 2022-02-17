import codecs
import re
from hacktools import common


def extract(data):
    infolder = data + "extract_PACK/"
    outfile = data + "lua_output.txt"

    common.logMessage("Extracting LUA to", outfile, "...")
    with codecs.open(outfile, "w", "utf-8") as out:
        files = common.getFiles(infolder, ".lua")
        for file in common.showProgress(files):
            common.logDebug("Processing", file, "...")
            first = True
            with codecs.open(infolder + file, "r", "shift_jisx0213") as luaf:
                lua = luaf.read()
            luastrings = re.findall('"([^"]*)"', lua) + re.findall("'([^']*)'", lua)
            for luastring in luastrings:
                luastring = luastring.replace("¥", "\\").replace("\\n", "|")
                if not common.isAscii(luastring):
                    if first:
                        out.write("!FILE:" + file + "\n")
                        first = False
                    out.write(luastring + "==\n")
    common.logMessage("Done! Extracted", len(files), "files")
