import codecs
from hacktools import common, nds


def extractFolders(data, packin, packout):
    common.logMessage("Extracting PACK ...")
    common.makeFolder(packout)
    for packfolder in packin:
        files = common.getFiles(packfolder, ".bin")
        for file in common.showProgress(files):
            extract(data, packfolder + file, packfolder, packout)
    common.logMessage("Done!")


def getSize(f):
    start = f.tell()
    f.seek(4, 1)
    numfiles = f.readUInt() - 1
    lastfile = numfiles - 1
    f.seek(start + 40 + 8 * lastfile)
    offset = f.readUInt() + 32
    size = f.readUInt()
    return offset + size


def extract(data, pack, folderin, folderout, add=""):
    common.logDebug("Processing", pack, "...")
    packfolder = pack.replace(folderin, folderout).replace(".PACK", "_PACK" + add) + "/"
    common.makeFolders(packfolder)
    filelist = []
    with codecs.open(data + "filelist.txt", "r", "utf-8") as flist:
        section = common.getSection(flist, pack)
    with codecs.open(data + "filelist2.txt", "r", "utf-8") as flist:
        section2 = common.getSection(flist, pack)
    with common.Stream(pack, "rb") as f:
        if f.readString(4) != "KCAP":
            return
        common.makeFolder(packfolder)
        numfiles = f.readUInt() - 1
        for i in range(1, numfiles + 1):
            f.seek(40 + 8 * (i - 1))
            offset = f.readUInt() + 32
            size = f.readUInt()
            f.seek(offset)
            compbyte = f.peek(1)[0]
            magic = f.readString(4)
            f.seek(-4, 1)
            subname, extension = getSubname(i, section2, magic)
            common.logDebug("Extracting file", i, subname, common.toHex(offset), common.toHex(size), common.toHex(compbyte))
            with common.Stream() as memf:
                # Compressed files
                if compbyte == 0x10 and "script" not in pack:
                    common.logDebug("Compressed PACK file")
                    packdata = nds.decompress(f, size)
                    memf.write(packdata)
                    # Check magic again after decompression
                    magic = packdata[:4].decode()
                    subname, extension = getSubname(i, section2, magic)
                else:
                    # Check for NCGR compression
                    if extension == "NCGR":
                        memf.write(f.read(40))
                        ncgrsize = f.readUInt()
                        unk = f.readUInt()
                        compbyte = f.peek(1)[0]
                        if compbyte == 0x10 and (ncgrsize & 0xff000000) >> 24 == 0x10:
                            memf.writeUInt(ncgrsize & 0x00ffffff)
                            memf.writeUInt(unk)
                            memf.write(nds.decompress(f, size - 44))
                        else:
                            f.seek(-48, 1)
                            memf.seek(0)
                            memf.write(f.read(size))
                    elif extension == "NSCR":
                        memf.write(f.read(32))
                        nscrsize = f.readUInt()
                        compbyte = f.peek(1)[0]
                        if compbyte == 0x10 and (nscrsize & 0xff000000) >> 24 == 0x10:
                            memf.writeUInt(nscrsize & 0x00ffffff)
                            memf.write(nds.decompress(f, size - 32))
                        else:
                            f.seek(-36, 1)
                            memf.seek(0)
                            memf.write(f.read(size))
                    else:
                        memf.write(f.read(size))
                if str(i) in section:
                    if extension == "bin" and section[str(i)][0].startswith("LUA_"):
                        extension = "lua"
                        subname = subname.replace(".bin", ".lua")
                    subname = section[str(i)][0] + "." + extension
                    if subname.startswith("PAC_") or subname.startswith("CGX_") or subname.startswith("SCR_") or subname.startswith("PAL_"):
                        subname = subname[4:]
                subfiles = subname.split(",")
                for subfile in subfiles:
                    with common.Stream(packfolder + subfile, "wb") as fout:
                        memf.seek(0)
                        fout.write(memf.read())
            # Nested pack files
            if subname.endswith(".PACK"):
                extract(data, packfolder + subname, folderin, folderout, "2")


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
