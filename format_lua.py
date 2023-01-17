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
                for luareplace in luareplaces.keys():
                    lua = lua.replace(luareplace.replace("\n", "\r\n"), luareplaces[luareplace].replace("\n", "\r\n"))
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
            # Inject the new code for the BTL_SETTING file
            if "LUA_BTL_SETTING" in file:
                lua = lua_inject_bltsettings.split("\n") + lua[17:]
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


luareplaces = {
# Add a new getVWF function
'''-- tools''':
'''-- tools
function getVWF(subchar, default)
  if vwf[subchar] == nil then
    return default
  end
  return vwf[subchar]
end''',
# Change the lineLen function to return the actual width of a line
'''    elseif s:byte(i) == string.byte("=") then
      i = i + 2
    else
      i = i + 1
      c = c + 1
    end''':
'''    elseif s:byte(i) == string.byte("=") then
      i = i + 2
    elseif s:byte(i) <= 0x7f then
      c = c + getVWF(s:sub(i, i), 6)
      i = i + 1
    else
      c = c + getVWF(s:sub(i, i+1), 12)
      i = i + 2
    end''',
# Use the new lineLen function
"local x = t.box.w * 4 - lineLen(s)   * 3": "local x = t.box.w * 4 - lineLen(s) / 2",
"x = t.box.w * 4 - lineLen(s:sub(i)) * 3": "x = t.box.w * 4 - lineLen(s:sub(i)) / 2",
# Handle ASCII/VWF in this box:print call
'''
        box:print(x, y, s:sub(i, i+1));
        i = i + 2
        x = x + 12
        sp = t:waitSay(0.9, sp);''':
'''
        if s:byte(i) <= 0x7f then
          local subchar = s:sub(i, i)
          box:print(x, y, subchar);
          x = x + getVWF(subchar, 6)
          i = i + 1
          sp = t:waitSay(0.45, sp);
        else
          local subchar = s:sub(i, i+1)
          box:print(x, y, subchar);
          x = x + getVWF(subchar, 12)
          i = i + 2
          sp = t:waitSay(0.9, sp);
        end'''
,
# Handle ASCII/VWF in this box:print call
'''
        t.box:print(x, y, s:sub(i, i+1));
        i = i + 2
        x = x + 12
        sp = t:waitSay(0.9, sp);''':
'''
        if s:byte(i) <= 0x7f then
          local subchar = s:sub(i, i)
          t.box:print(x, y, subchar);
          x = x + getVWF(subchar, 6)
          i = i + 1
          sp = t:waitSay(0.45, sp);
        else
          local subchar = s:sub(i, i+1)
          t.box:print(x, y, subchar);
          x = x + getVWF(subchar, 12)
          i = i + 2
          sp = t:waitSay(0.9, sp);
        end'''
}
# The LUA_INJECT file has a centerPuts function at the top we need to change
lua_inject_bltsettings = '''
function centerPuts(txt, s)
  local x = txt.w * 4 - lineLen(s) / 2
  local y = txt.h * 3 - lineCount(s) * 6
  local i = 1
  while i <= s:len() do
    if s:byte(i) == string.byte("\\n") then
      i = i + 1
      x = txt.w * 4 - lineLen(s:sub(i)) / 2
      y = y + 13
    elseif s:byte(i) <= 0x7f then
      txt:print(x, y, s:sub(i, i));
      x = x + getVWF(s:sub(i, i), 6)
      i = i + 1
    else
      txt:print(x, y, s:sub(i, i+1));
      x = x + getVWF(s:sub(i, i+1), 12)
      i = i + 2
    end
  end
end'''
