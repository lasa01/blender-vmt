import bpy
from pathlib import Path

import re

from .vmt import VMT

re_mtl_path = re.compile(r'^# (?P<path>.+)\nnewmtl (?P<mat>.+)', flags=re.I)

class CraftyMtl:
    def __init__(self, filepath: Path):
        self.material_map = dict()
        content = ""
        with open(filepath, "r") as file:
            content = file.read()
        mats = content.split("\n\n")
        for mat in mats:
            match = re_mtl_path.match(mat)
            if match:
                self.material_map[match.group('mat')] = match.group('path').lower()

    def replace_materials(self, texturepath: Path, textureext: str, suffix: str="", rename: bool=False):
        for mat_name in self.material_map:
            fullpath = texturepath / "materials" / (self.material_map[mat_name] + ".vmt")
            if not fullpath.exists():
                print("CraftyReplace: Did not find mtl file: {}".format(fullpath))
                continue
            vmt = VMT(fullpath, textureext, texturepath)
            vmt.make_material(mat_name + suffix, True)
            if rename:
                bpy.data.materials[mat_name + suffix].name = Path(self.material_map[mat_name]).stem
