import codecs
import os
from hacktools import common, nds


class Pack:
    def __init__(self):
        self.numfiles = 0
        self.files = []


class PackFile:
    def __init__(self):
        self.offset = 0
        self.size = 0
        self.compbyte = 0
        self.magic = ""
        self.subname = ""
        self.extension = ""


def readPack(data, f, packname, section, section2):
    if f.readString(4) != "KCAP":
        return None
    pack = Pack()
    pack.numfiles = f.readUInt() - 1
    for i in range(1, pack.numfiles + 1):
        file = PackFile()
        f.seek(40 + 8 * (i - 1))
        file.offset = f.readUInt() + 32
        file.size = f.readUInt()
        f.seek(file.offset)
        file.compbyte = f.peek(1)[0]
        file.magic = f.readString(4)
        f.seek(-4, 1)
        file.subname, file.extension = getSubname(i, section2, file.magic)
        common.logDebug("Processing file", i, file.subname, "offset", common.toHex(file.offset), "size", common.toHex(file.size), "compbyte", common.toHex(file.compbyte))
        with common.Stream() as memf:
            # Compressed files
            if file.compbyte == 0x10 and "script" not in packname:
                common.logDebug("Compressed PACK file")
                packdata = nds.decompress(f, file.size)
                memf.write(packdata)
                # Check magic again after decompression
                file.magic = packdata[:4].decode()
                file.subname, file.extension = getSubname(i, section2, file.magic)
            if str(i) in section:
                if file.extension == "bin" and section[str(i)][0].startswith("LUA_"):
                    file.extension = "lua"
                    file.subname = file.subname.replace(".bin", ".lua")
                file.subname = section[str(i)][0] + "." + file.extension
                if file.subname.startswith("PAC_") or file.subname.startswith("CGX_") or file.subname.startswith("SCR_") or file.subname.startswith("PAL_"):
                    file.subname = file.subname[4:]
        pack.files.append(file)
    return pack


def repackFolders(data, debon=False, deboff=False):
    packin = [data + "extract/data/", data + "extract_CHILD/pack/"]
    packout = data + "extract_PACK/"
    packrepack = data + "repack_PACK/"
    replacefolder = data + "replace_PACK/"
    debfilein = data + "extract_PACK/dat_word_battle.bin/LUA_OPENING.lua"
    debfileout = debfilein.replace("extract_", "repack_")

    if debon or deboff:
        common.copyFile(debfilein, debfileout)
        with codecs.open(debfileout, "r", "shift_jisx0213") as f:
            alldeb = f.read()
        if debon:
            alldeb = alldeb.replace("seq_change(\"GameTitle\")", "--seq_change(\"GameTitle\")")
            alldeb = alldeb.replace("--seq_change(\"LaunchI\")", "seq_change(\"LaunchI\")")
        with codecs.open(debfileout, "w", "shift_jisx0213") as f:
            f.write(alldeb)
    if os.path.isdir(replacefolder):
        common.mergeFolder(replacefolder, packrepack)
    common.logMessage("Repacking nested PACK ...")
    for pack in common.showProgress(common.getFiles(packout, ".PACK")):
        subpackfolder = pack.replace(".PACK", "_PACK2") + "/"
        if os.path.isdir(packrepack + subpackfolder):
            repack(data, packout + pack, packrepack + pack, packrepack + subpackfolder)
    common.logMessage("Done!")
    common.logMessage("Repacking PACK ...")
    common.makeFolder(data + "repack_CHILD/pack/")
    for packfolder in packin:
        files = common.getFiles(packfolder, ".bin")
        for file in common.showProgress(files):
            subpackfolder = packrepack + file + "/"
            if os.path.isdir(subpackfolder):
                repack(data, packfolder + file, packfolder.replace("/extract", "/repack") + file, subpackfolder)
    common.logMessage("Done!")


def repack(data, pack, packout, workfolder):
    with codecs.open(data + "filelist.txt", "r", "utf-8") as flist:
        section = common.getSection(flist, pack)
    with codecs.open(data + "filelist2.txt", "r", "utf-8") as flist:
        section2 = common.getSection(flist, pack)
    common.logDebug("Processing", pack, "...")
    with common.Stream(pack, "rb") as fin:
        packfile = readPack(data, fin, pack, section, section2)
        if packfile is None:
            return
        fin.seek(0)
        with common.Stream(packout, "wb") as f:
            # Copy the header
            f.write(fin.read(40))
            # Go to the first offset
            f.seek(packfile.files[0].offset)
            for i in range(len(packfile.files)):
                file = packfile.files[i]
                common.logDebug("  Repacking file", i, file.subname, "offset", common.toHex(file.offset), "size", common.toHex(file.size), "compbyte", common.toHex(file.compbyte))
                offset = f.tell()
                if os.path.isfile(workfolder + file.subname):
                    with common.Stream(workfolder + file.subname, "rb") as subf:
                        filedata = subf.read()
                    if file.compbyte == 0x10 and "script" not in pack:
                        filedata = nds.compress(filedata, nds.CompressionType.LZ10)
                    f.write(filedata)
                    '''newsize = os.path.getsize(workfolder + file.subname)
                    common.logDebug("    New size", common.toHex(newsize))
                    with common.Stream() as memf:
                        with common.Stream(workfolder + file.subname, "rb") as subf:
                            if file.compbyte == 0x10 and "script" not in pack:
                                memf.write(nds.compress(subf.read(), nds.CompressionType.LZ10))
                            # Check for NCGR/NSCR compression
                            elif file.extension == "NCGR":
                                memf.write(subf.read(40))
                                ncgrsize = subf.readUInt()
                                fin.seek(file.offset + 40)
                                oldncgrsize = fin.readUInt()
                                unk = subf.readUInt()
                                fin.seek(4, 1)
                                oldcompbyte = fin.peek(1)[0]
                                if oldcompbyte == 0x10 and (oldncgrsize & 0xff000000) >> 24 == 0x10:
                                    memf.writeUInt((ncgrsize & 0x00ffffff) | (0x10 << 24))
                                    memf.writeUInt(unk)
                                    memf.write(nds.compress(subf.read(newsize - 44), nds.CompressionType.LZ10))
                                else:
                                    subf.seek(-48, 1)
                                    memf.seek(0)
                                    memf.write(subf.read(newsize))
                            elif file.extension == "NSCR":
                                memf.write(subf.read(32))
                                fin.seek(file.offset + 32)
                                nscrsize = subf.readUInt()
                                oldnscrsize = fin.readUInt()
                                oldcompbyte = fin.peek(1)[0]
                                if oldcompbyte == 0x10 and (oldnscrsize & 0xff000000) >> 24 == 0x10:
                                    memf.writeUInt((nscrsize & 0x00ffffff) | (0x10 << 24))
                                    memf.write(nds.compress(subf.read(newsize - 36), nds.CompressionType.LZ10))
                                else:
                                    subf.seek(-36, 1)
                                    memf.seek(0)
                                    memf.write(subf.read(newsize))
                            else:
                                memf.write(subf.read())
                        if memf.tell() != newsize:
                            common.logDebug("    After compression", common.toHex(memf.tell()))
                        memf.seek(0)
                        f.write(memf.read())'''
                else:
                    fin.seek(file.offset)
                    f.write(fin.read(file.size))
                # Write the offset and size
                f.writeUIntAt(40 + 8 * i, offset - 32)
                f.writeUIntAt(40 + 8 * i + 4, f.tell() - offset)
                # Align
                if f.tell() % 32 > 0:
                    f.writeZero(32 - (f.tell() % 32))
            # There's some additional data between the last file and the first offset
            f.seek(40 + 8 * len(packfile.files))
            fin.seek(f.tell())
            while f.tell() < packfile.files[0].offset:
                f.writeUInt(fin.readUInt())
                f.writeUInt(fin.readUInt())


def extractFolders(data):
    packin = [data + "extract/data/", data + "extract_CHILD/pack/"]
    packout = data + "extract_PACK/"

    common.logMessage("Extracting PACK ...")
    common.makeFolder(packout)
    for packfolder in packin:
        files = common.getFiles(packfolder, ".bin")
        for file in common.showProgress(files):
            extract(data, packfolder + file, packfolder, packout)
    common.logMessage("Done!")


def extract(data, pack, folderin, folderout, add=""):
    common.logDebug("Processing", pack, "...")
    with codecs.open(data + "filelist.txt", "r", "utf-8") as flist:
        section = common.getSection(flist, pack)
    with codecs.open(data + "filelist2.txt", "r", "utf-8") as flist:
        section2 = common.getSection(flist, pack)
    packfolder = pack.replace(folderin, folderout).replace(".PACK", "_PACK" + add) + "/"
    common.makeFolders(packfolder)
    with common.Stream(pack, "rb") as f:
        packfile = readPack(data, f, pack, section, section2)
        if packfile is None:
            return
        common.makeFolder(packfolder)
        for i in range(1, packfile.numfiles + 1):
            file = packfile.files[i - 1]
            f.seek(file.offset)
            with common.Stream() as memf:
                # Compressed files
                if file.compbyte == 0x10 and "script" not in pack:
                    packdata = nds.decompress(f, file.size)
                    memf.write(packdata)
                else:
                    # Check for NCGR/NSCR compression
                    if file.extension == "NCGR":
                        memf.write(f.read(40))
                        ncgrsize = f.readUInt()
                        unk = f.readUInt()
                        compbyte = f.peek(1)[0]
                        if compbyte == 0x10 and (ncgrsize & 0xff000000) >> 24 == 0x10:
                            memf.writeUInt(ncgrsize & 0x00ffffff)
                            memf.writeUInt(unk)
                            memf.write(nds.decompress(f, file.size - 44))
                        else:
                            f.seek(-48, 1)
                            memf.seek(0)
                            memf.write(f.read(file.size))
                    elif file.extension == "NSCR":
                        memf.write(f.read(32))
                        nscrsize = f.readUInt()
                        compbyte = f.peek(1)[0]
                        if compbyte == 0x10 and (nscrsize & 0xff000000) >> 24 == 0x10:
                            memf.writeUInt(nscrsize & 0x00ffffff)
                            memf.write(nds.decompress(f, file.size - 36))
                        else:
                            f.seek(-36, 1)
                            memf.seek(0)
                            memf.write(f.read(file.size))
                    else:
                        memf.write(f.read(file.size))
                subfiles = file.subname.split(",")
                for subfile in subfiles:
                    with common.Stream(packfolder + subfile, "wb") as fout:
                        memf.seek(0)
                        fout.write(memf.read())
            # Nested pack files
            if file.subname.endswith(".PACK"):
                extract(data, packfolder + file.subname, folderin, folderout, "2")


def getSubname(i, section, magic):
    extension = "bin"
    if magic in ["RGCN", "RLCN", "RCSN", "RECN", "RNAN", "RTFN", "KCAP"]:
        extension = magic[::-1]
    elif magic in ["BCA0", "BMD0"]:
        extension = magic[:-1]
    elif magic == "SDAT":
        extension = magic
    subname = "file" + str(i).zfill(3) + "." + extension
    if str(i) in section:
        subname = section[str(i)][0]
    return subname, extension


def getPackSize(f):
    start = f.tell()
    f.seek(4, 1)
    numfiles = f.readUInt() - 1
    lastfile = numfiles - 1
    f.seek(start + 40 + 8 * lastfile)
    offset = f.readUInt() + 32
    size = f.readUInt()
    return offset + size
