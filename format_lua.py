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
            # For the LUA_SYS file, we need to replace some code to get the ASCII strings to render correctly
            if "LUA_SYS" in file:
                vwftable = []
                vwftable.append("vwf = {}")
                for glyph in glyphs.keys():
                    if glyph == "＼":
                        continue
                    if glyphs[glyph].length == 12:
                        continue
                    if glyph == "\"":
                        vwftable.append("vwf['\"'] = " + str(glyphs[glyph].length))
                        continue
                    vwftable.append("vwf[\"" + glyph.replace('"', '"') + "\"] = " + str(glyphs[glyph].length))
                with codecs.open(infolder + file, "r", "shift_jisx0213") as luaf:
                    lua = luaf.read()
                lua = "\r\n".join(vwftable) + "\r\n\r\n" + lua
                lua = lua.replace(lua_inject_pre.replace("\n", "\r\n"), lua_inject_post.replace("\n", "\r\n")).replace(lua_inject2_pre.replace("\n", "\r\n"), lua_inject2_post.replace("\n", "\r\n"))
                common.makeFolders(os.path.dirname(outfolder + file))
                with codecs.open(outfolder + file, "w", "shift_jisx0213") as luaf:
                    luaf.write(lua)
                continue
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
                        # Check wordwrapping results for long lines
                        newstringcheck = newstring.split("\\v")
                        for check in newstringcheck:
                            if check.count("|") > 2:
                                common.logWarning("Line too long:", newstring)
                                break
                        lua[i] = lua[i].replace(game.restoreCharcodes(oldstring), game.restoreCharcodes(newstring))
            common.makeFolders(os.path.dirname(outfolder + file))
            with codecs.open(outfolder + file, "w", "shift_jisx0213") as luaf:
                luaf.write("\n".join(lua).replace("|", "\\n").replace("\\", "¥"))
    common.logMessage("Done! Translation is at {0:.2f}%".format((100 * transtot) / chartot))


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


# One of the LUA scripts features a text renderer that doesn't handle ASCII well
# This replaces it and adds VWF support
lua_inject_pre = '''
        box:print(x, y, s:sub(i, i+1));
        i = i + 2
        x = x + 12
        sp = t:waitSay(0.9, sp);'''
lua_inject_post = '''
        if s:byte(i) <= 0x7f then
          local subchar = s:sub(i, i)
          box:print(x, y, subchar);
          if vwf[subchar] == nil then
            x = x + 6
          else
            x = x + vwf[subchar]
          end
          i = i + 1
          sp = t:waitSay(0.45, sp);
        else
          local subchar = s:sub(i, i+1)
          box:print(x, y, subchar);
          if vwf[subchar] == nil then
            x = x + 12
          else
            x = x + vwf[subchar]
          end
          i = i + 2
          sp = t:waitSay(0.9, sp);
        end'''

lua_inject2_pre = '''
        t.box:print(x, y, s:sub(i, i+1));
        i = i + 2
        x = x + 12
        sp = t:waitSay(0.9, sp);'''
lua_inject2_post = '''
        if s:byte(i) <= 0x7f then
          local subchar = s:sub(i, i)
          t.box:print(x, y, subchar);
          if vwf[subchar] == nil then
            x = x + 6
          else
            x = x + vwf[subchar]
          end
          i = i + 1
          sp = t:waitSay(0.45, sp);
        else
          local subchar = s:sub(i, i+1)
          t.box:print(x, y, subchar);
          if vwf[subchar] == nil then
            x = x + 12
          else
            x = x + vwf[subchar]
          end
          i = i + 2
          sp = t:waitSay(0.9, sp);
        end'''
