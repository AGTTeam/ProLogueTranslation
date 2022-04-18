import os
import click
import game
from hacktools import common, nds, nitro

version = "0.4.0"
data = "ProLogueData/"
romfile = data + "dn3.nds"
rompatch = data + "dn3_patched.nds"
infolder = data + "extract/"
replacefolder = data + "replace/"
outfolder = data + "repack/"
patchfile = data + "patch.xdelta"
packout = data + "extract_PACK/"
packrepack = data + "repack_PACK/"
childfile = data + "extract/data/mb/dn3_child.srl"
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
    if all or bin:
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
@click.option("--no-rom", is_flag=True, default=False)
@click.option("--bin", is_flag=True, default=False)
@click.option("--img", is_flag=True, default=False)
@click.option("--script", is_flag=True, default=False)
@click.option("--lua", is_flag=True, default=False)
@click.option("--pack", is_flag=True, default=False)
def repack(no_rom, bin, img, script, lua, pack):
    all = not bin and not img and not script and not lua and not pack
    if all or bin:
        import format_bin
        format_bin.repack(data)
    if all or script:
        import format_script
        format_script.repack(data)
    if all or pack or img or script or lua:
        import format_pack
        format_pack.repackFolders(data)
    if not no_rom:
        if os.path.isdir(replacefolder):
            common.mergeFolder(replacefolder, outfolder)
        nds.repackRom(romfile, rompatch, outfolder, patchfile)


if __name__ == "__main__":
    click.echo("ProLogueTranslation version " + version)
    if not os.path.isdir(data):
        common.logError(data, "folder not found.")
        quit()
    common.runCLI(common.cli)
