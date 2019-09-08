# Slightly inspired by https://github.com/Ganonmaster/io_texture_VTF/blob/blender280/vmt.py

import bpy
from pathlib import Path

from .libraries import vdf
from . import vtf


class VMT:
    def _get_root_path(self, path: Path):
        if path.parts[-1] == 'materials':
            return path.parent
        else:
            return self._get_root_path(path.parent)

    def __init__(self, filepath: Path, textureext: str, texturepath: Path=None):
        self.filepath = Path(filepath)
        self.textureext = textureext
        self.convert = textureext == ".vtf"
        if not texturepath:
            texturepath = self._get_root_path(self.filepath)
        self.texturepath = texturepath
        print("VMT: Parsing VMT file {}".format(filepath))
        kv = vdf.parse(open(filepath), escaped=False)
        self.shader = next(iter(kv))
        self.shader_data = kv[self.shader]
        self.texture_files = dict()  # tuples, if first is string, then refers another member
        self.texture_consts = dict() # const values that override textures
        self.texture_defaults = dict() # const values that are overridden by textures
        self.images = dict()
        for param, value in self.shader_data.items():
            param = param.lower()  # ignore case
            # Handle supported texture parameters
            if param == "$basetexture":
                self.texture_files['base'] = (self.get_text_file(value), "rgb")
            elif (param == "$translucent" or param == "$alphatest") and int(value) == 1:
                self.texture_files['alpha'] = ("base", "a")
            elif (param == "$basemapalphaphongmask" or param == "$basemapalphaenvmapmask") and int(value) == 1:
                self.texture_files['specular'] = ("base", "a")
            elif param == "$bumpmap":
                self.texture_files['normal'] = (self.get_text_file(value), "rgb")
                if 'specular' not in self.texture_files:
                    self.texture_files['specular'] = ("normal", "a")
            elif param == "$phong" and int(value) == 1:
                # Estimate for source-like appearance
                self.texture_defaults['roughness'] = 0.3
                self.texture_defaults['specular'] = 0.5
            elif param == "$phongexponent":
                # Roughness needs to be inverted and converted to float
                # Source range 0-255 is approx blender range 0.5-0
                # Overrides textures, so goes to consts
                self.texture_consts['roughness'] = (255 - int(value)) / 510
            elif param == "$phongexponenttexture":
                self.texture_files['roughness'] = (self.get_text_file(value), "r")
            elif param == "$phongalbedotint" and int(value) == 1:
                self.texture_files['specular_tint'] = ("roughness", "g")
            elif param == "$envmap":
                # Envmap probably means clearer reflections than phong
                self.texture_defaults['roughness'] = 0.1
                self.texture_defaults['specular'] = 0.7
            elif param == "$envmapmask":
                self.texture_files['specular'] = (self.get_text_file(value), "rgb")
            elif param == "$selfillum" and int(value) == 1:
                if 'emission' not in self.texture_files:
                    self.texture_files['emission'] = ("base", "a")
            elif param == "$selfillummask":
                self.texture_files['emission'] = (self.get_text_file(value), "rgb")

    def get_text_file(self, name: str) -> Path:
        path = self.texturepath / "materials" / name
        return path.with_suffix(self.textureext)

    def make_material(self, mat_name: str=None, override: bool=False) -> bool:
        if not mat_name:
            mat_name = self.filepath.stem
        mat = bpy.data.materials.get(mat_name)
        if mat:
            if not override:
                return False
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    mat.node_tree.nodes.remove(node)
        else:
            mat = bpy.data.materials.new(mat_name)
        print("VMT: Building material")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        out = nodes.get('Material Output', None)
        if not out:
            out = nodes.new('ShaderNodeOutputMaterial')
        out.location = (0, 0)
        bsdf = nodes.get('Principled BSDF')
        if not bsdf:
            bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.location = (-500, 0)
        links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
        bsdf.inputs['Specular'].default_value = 0.1
        bsdf.inputs['Roughness'].default_value = 1.0
        texnodes = dict()
        separatornodes = dict()
        # Where different textures are connected
        texnames = {
            "base": "Base Color",
            "specular": "Specular",
            "specular_tint": "Specular Tint",
            "roughness": "Roughness",
            "emission": "Emission",
            "alpha": "Alpha",
            "normal": "Normal"
        }
        texnodelocationy = 300
        for name in texnames:
            if name in self.texture_consts:
                # No texture, but a constant value
                # Overrides possible texture value
                print("VMT: Overriding {} with constant value".format(name))
                bsdf.inputs[texnames[name]].default_value = self.texture_consts[name]
            elif name in self.texture_files:
                pair = self.texture_files[name]
                filepath = pair[0]
                tex = None
                texname = None
                if type(filepath) is str:
                    # Relative reference, solve it
                    # The texture might already have a node, so check it
                    texname = filepath
                    if texnodes.get(texname, None):
                        tex = texnodes[texname]
                    else:
                        filepath = self.texture_files[filepath][0]
                else:
                    texname = name
                    if texnodes.get(texname, None):
                        tex = texnodes[texname]
                # Create texture node if not already created
                if not tex:
                    tex = nodes.new('ShaderNodeTexImage')
                    tex.image = self._load_image(filepath)
                    # Set to non-color data for other images than base color
                    if texname == "base":
                        tex.image.colorspace_settings.name = "sRGB"
                    else:
                        tex.image.colorspace_settings.name = "Non-Color"
                    # Alpha channel has always seperate data
                    tex.image.alpha_mode = "CHANNEL_PACKED"
                    tex.location = (-1000, texnodelocationy)
                    texnodelocationy -= 300
                    texnodes[texname] = tex
                out_type = pair[1]
                out = None
                out_node = tex
                if out_type == "rgb":
                    out = "Color"
                elif out_type == "a":
                    out = "Alpha"
                else:
                    # Need to get a single channel probably
                    separator = None
                    if (separatornodes.get(texname, None)):
                        separator = separatornodes[texname]
                    else:
                        # Create the node
                        separator = nodes.new('ShaderNodeSeparateRGB')
                        separator.location = (-750, tex.location[1])
                        links.new(tex.outputs['Color'], separator.inputs['Image'])
                        separatornodes[texname] = separator
                    out_node = separator
                    out = out_type.upper()
                # Special cases
                if name == "normal":
                    # Need to create a normal map node
                    normal = nodes.new("ShaderNodeNormalMap")
                    normal.location = (-750, tex.location[1] - 150)
                    links.new(out_node.outputs[out], normal.inputs['Color'])
                    out_node = normal
                    out = "Normal"
                elif name == "roughness":
                    # Need to invert value since source format is different
                    # And multiply by 0.5 for more accurate results
                    invert = nodes.new("ShaderNodeMath")
                    invert.operation = 'SUBTRACT'
                    invert.inputs[0].default_value = 1.0
                    invert.location = (-750, tex.location[1] - 150)
                    links.new(out_node.outputs[out], invert.inputs[1])
                    multiply = nodes.new("ShaderNodeMath")
                    multiply.operation = 'MULTIPLY'
                    multiply.inputs[1].default_value = 0.5
                    multiply.location = (-750, tex.location[1] - 300)
                    links.new(invert.outputs[0], multiply.inputs[0])
                    texnodelocationy -= 150
                    out_node = multiply
                    out = 0
                links.new(out_node.outputs[out], bsdf.inputs[texnames[name]])
            elif name in self.texture_defaults:
                bsdf.inputs[texnames[name]].default_value = self.texture_defaults[name]
        return True
    
    def _load_image(self, path: Path) -> bpy.types.Image:
        if path not in self.images:
            print("VMT: Loading texture {}".format(path))
            if self.convert:
                if path.stem in bpy.data.images:
                    result = bpy.data.images[path.stem]
                else:
                    result = vtf.import_image(path)
                self.images[path] = result
            else:
                self.images[path] = bpy.data.images.load(str(path), check_existing=True)
        return self.images[path]