from hacktools import common, nds


def getSubname(i, magic):
    subname = "file"
    if i < 10:
        subname += "00"
    elif i < 100:
        subname += "0"
    subname += str(i)
    extension = "bin"
    if magic in ["RGCN", "RLCN", "RCSN", "RECN", "RNAN", "RTFN", "KCAP"]:
        extension = magic[::-1]
    elif magic in ["BCA0", "BMD0"]:
        extension = magic[:-1]
    elif magic == "SDAT":
        extension = magic
    return subname + "." + extension, extension


def extractFolders(packin, packout):
    common.logMessage("Extracting PACK ...")
    common.makeFolder(packout)
    for packfolder in packin:
        files = common.getFiles(packfolder, ".bin")
        for file in common.showProgress(files):
            common.logDebug("Processing", file, "...")
            extract(packfolder + file, packfolder, packout)
    common.logMessage("Done!")


def getSize(f):
    start = f.tell()
    f.seek(4, 1)
    numfiles = f.readUInt() - 1
    lastfile = numfiles - 1
    f.seek(start + 40 + 8 * lastfile)
    offset = f.readUInt()
    size = f.readUInt()
    return offset + size


def extract(pack, folderin, folderout, add=""):
    packfolder = pack.replace(folderin, folderout).replace(".PACK", "_PACK" + add) + "/"
    common.makeFolders(packfolder)
    with common.Stream(pack, "rb") as f:
        if f.readString(4) != "KCAP":
            return
        common.makeFolder(packfolder)
        numfiles = f.readUInt() - 1
        for i in range(numfiles):
            f.seek(40 + 8 * i)
            offset = f.readUInt()
            size = f.readUInt()
            f.seek(32 + offset)
            compbyte = f.peek(1)[0]
            magic = f.readString(4)
            f.seek(-4, 1)
            subname, extension = getSubname(i, magic)
            # Compressed files
            if compbyte == 0x10 and "script" not in pack:
                data = nds.decompress(f, size)
                # Check magic again after decompression
                magic = data[:4].decode()
                subname, extension = getSubname(i, magic)
            else:
                # Check for NCGR compression
                if extension == "NCGR":
                    header = f.read(48)
                    compbyte = f.peek(1)[0]
                    if compbyte == 0x10:
                        data = header + nds.decompress(f, size - 48)
                    else:
                        f.seek(-48, 1)
                        data = f.read(size)
                else:
                    data = f.read(size)
            if extension == "bin" and data.find(b"function") >= 0:
                subname = subname.replace(".bin", ".lua")
            with common.Stream(packfolder + subname, "wb") as fout:
                fout.write(data)
            # Nested pack files
            if subname.endswith(".PACK"):
                extract(packfolder + subname, folderin, folderout, "2")
