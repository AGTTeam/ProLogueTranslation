import os
import click
import game
from hacktools import common, nds, nitro

version = "1.1.1"
data = "ProLogueData/"
romfile = "dn3.nds"
rompatch = data + "dn3_patched.nds"
infolder = data + "extract/"
replacefolder = data + "replace/"
outfolder = data + "repack/"
patchfile = data + "patch.xdelta"
packout = data + "extract_PACK/"
packrepack = data + "repack_PACK/"
childfile = data + "extract/data/mb/dn3_child.srl"
childfileout = data + "repack/data/mb/dn3_child.srl"
childin = data + "extract_CHILD/"
childout = data + "repack_CHILD/"


@common.cli.command()
@click.option("--rom", is_flag=True, default=False)
@click.option("--bin", is_flag=True, default=False)
@click.option("--img", is_flag=True, default=False)
@click.option("--bmd", is_flag=True, default=False)
@click.option("--script", is_flag=True, default=False)
@click.option("--lua", is_flag=True, default=False)
def extract(rom, bin, img, bmd, script, lua):
    all = not rom and not bin and not img and not bmd and not script and not lua
    if all or rom:
        nds.extractRom(romfile, infolder, outfolder)
        nds.extractRom(childfile, childin, childout)
    if all or rom or bin:
        import format_bin
        format_bin.extract(data)
    if all or rom or bin:
        import format_pack
        format_pack.extractFolders(data)
    if all or img:
        nitro.extractIMG(packout, data + "out_IMG/", readfunc=game.readImage)
    if all or bmd:
        nitro.extractNSBMD(packout, data + "out_BMD/", ".BMD")
    if all or script:
        import format_script
        format_script.extract(data)
    if all or lua:
        import format_lua
        format_lua.extract(data)


@common.cli.command()
@click.option("--no-rom", is_flag=True, default=False, hidden=True)
@click.option("--bin", is_flag=True, default=False)
@click.option("--img", is_flag=True, default=False)
@click.option("--script", is_flag=True, default=False)
@click.option("--lua", is_flag=True, default=False)
@click.option("--pack", is_flag=True, default=False)
@click.option("--deb-on", is_flag=True, default=False, hidden=True)
@click.option("--deb-off", is_flag=True, default=False, hidden=True)
def repack(no_rom, bin, img, script, lua, pack, deb_on, deb_off):
    all = not bin and not img and not script and not lua and not pack
    if all or script:
        import format_script
        format_script.repack(data)
    if all or lua:
        import format_lua
        format_lua.repack(data)
    if all or img:
        nitro.repackIMG(data + "work_IMG/", packout, packrepack, readfunc=game.readImage, clean=True)
    if all or pack or img or script or lua or deb_on or deb_off:
        import format_pack
        format_pack.repackFolders(data, deb_on, deb_off)
    if all or bin:
        import format_bin
        format_bin.repack(data)
    if not no_rom:
        if os.path.isdir(replacefolder):
            common.mergeFolder(replacefolder, outfolder)
        nds.repackRom(childfile, childfileout, childout)
        nds.repackRom(romfile, rompatch, outfolder, patchfile)


if __name__ == "__main__":
    common.setupTool("ProLogueTranslation", version, data, romfile, 0x259cf66b)
