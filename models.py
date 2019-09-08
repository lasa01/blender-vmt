import bpy
from pathlib import Path
import os

from .vmt import VMT

class ModelsMtl:
    def __init__(self, materialpath: Path, textureext: str, texturepath: Path=None):
        self.materialpath = materialpath
        self.texturepath = texturepath or materialpath
        self.textureext = textureext
        self.materials = dict()


    def replace_materials(self, only_empty: bool=True, skip_crafty: bool=True, prefer_v: bool=True):
        print("ModelsReplace: Replacing materials")
        required_materials = dict()
        for material in bpy.data.materials:
            if only_empty and material.use_nodes:
                continue
            if skip_crafty and material.name.startswith('material_'):
                continue
            required_materials[material.name.lower()] = material.name
        print("ModelsReplace: {} materials to replace".format(len(required_materials)))
        print("ModelsReplace: Looking for materials in {}".format(self.materialpath / "materials" / "models"))
        for root, folders, files in os.walk(self.materialpath / "materials" / "models"):
            # Ignore directories that don't contain proper textures
            if "customization" in root or "gui" in root:
                continue
            for file in files:
                file = Path(file)
                if file.suffix == ".vmt" and file.stem.lower() in required_materials:
                    print("ModelsReplace: Found material {}".format(file))
                    name = required_materials[file.stem.lower()]
                    root = Path(root)
                    if name in self.materials:
                        if prefer_v and 'v_models' in root.parts and 'w_models' in self.materials[name].parts:
                            self.materials[name] = root / file
                        else:
                            print("ModelsReplace: ignoring multiple possible materials found for {}".format(name))
                    else:
                        self.materials[name] = root / file
        for name in self.materials:
            mat_path = self.materials[name]
            fullpath = self.materialpath / "materials" / "models" / mat_path
            vmt = VMT(fullpath, self.textureext, self.texturepath)
            vmt.make_material(name, True)
