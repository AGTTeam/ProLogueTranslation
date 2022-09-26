import codecs
import os
import re
import game
from hacktools import common, nitro


def repack(data):
    infile = data + "lua_input.txt"
    fontfile = data + "replace_PACK/dat_font_00.bin/file002.NFTR"
    infolder = data + "extract_PACK/"
    outfolder = data + "repack_PACK/"
    chartot = transtot = 0

    common.logMessage("Repacking LUA from", infile, "...")
    glyphs = nitro.readNFTR(fontfile).glyphs
    with codecs.open(infile, "r", "utf-8") as luain:
        files = common.getFiles(infolder, ".lua")
        for file in common.showProgress(files):
            section = common.getSection(luain, file)
            chartot, transtot = common.getSectionPercentage(section, chartot, transtot)
            if len(section) == 0:
                continue
            common.logDebug("Processing", file, "...")
            with codecs.open(infolder + file, "r", "shift_jisx0213") as luaf:
                lua = luaf.read().replace("¥", "\\").replace("\\n", "|").split("\n")
            for i in range(len(lua)):
                lualine = game.replaceCharcodes(lua[i])
                luastrings = re.findall('"([^"]*)"', lualine) + re.findall("'([^']*)'", lualine)
                for oldstring in luastrings:
                    newstring = oldstring
                    if oldstring in section and section[oldstring][0] != "":
                        newstring = section[oldstring][0]
                        if len(section[oldstring]) > 1:
                            section[oldstring].pop(0)
                    if newstring != oldstring:
                        newstring = common.wordwrap(newstring, glyphs, game.wordwrap, game.detectTextCode, sectionsep="\\v")
                        lua[i] = lua[i].replace(game.restoreCharcodes(oldstring), game.restoreCharcodes(newstring))
            common.makeFolders(os.path.dirname(outfolder + file))
            with codecs.open(outfolder + file, "w", "shift_jisx0213") as luaf:
                luaf.write("\n".join(lua).replace("|", "\\n").replace("\\", "¥"))


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
                    luastring = game.replaceCharcodes(luastring)
                    if first:
                        out.write("!FILE:" + file + "\n")
                        first = False
                    out.write(luastring + "=\n")
    common.logMessage("Done! Extracted", len(files), "files")
