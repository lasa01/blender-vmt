import bpy
from pathlib import Path
from .libraries import vdf


class VMT:
    def _get_root_path(self, path: Path):
        if path.parts[-1] == 'materials':
            return path.parent
        else:
            return self._get_root_path(path.parent)

    def __init__(self, filepath: str, textureext: str, texturepath: Path=None):
        self.filepath = Path(filepath)
        self.textureext = textureext
        if not texturepath:
            texturepath = self._get_root_path(self.filepath)
        self.texturepath = texturepath
        kv = vdf.parse(open(filepath))
        self.shader = next(iter(kv))
        self.shader_data = kv[self.shader]
        self.texture_files = dict()  # tuples, if first is string, then refers another member
        self.texture_flags = dict()
        for param, value in self.shader_data.items():
            param = param.lower()  # ignore case
            # Handle supported texture parameters
            if param == "$basetexture":
                self.texture_files['base'] = (self.get_text_file(value), "rgb")
                self.texture_flags['base'] = True
            elif (param == "$translucent" or param == "$alphatest") and int(value) == 1:
                self.texture_files['alpha'] = ("base", "a")
                self.texture_flags['alpha'] = True
            elif (param == "$basemapalphaphongmask" or param == "$basemapalphaenvmapmask") and int(value) == 1:
                self.texture_files['specular'] = ("base", "a")
            elif param == "$bumpmap":
                self.texture_files['normal'] = (self.get_text_file(value), "rgb")
                if 'specular' not in self.texture_files:
                    self.texture_files['specular'] = ("normal", "a")
                self.texture_flags['normal'] = True
            elif param == "$phong" and int(value) == 1:
                self.texture_flags['specular'] = 1
            elif param == "$phongexponenttexture":
                self.texture_files['roughness'] = (self.get_text_file(value), "r")
                self.texture_flags['roughness'] = True
            elif param == "$phongalbedotint" and int(value) == 1:
                self.texture_files['specular_tint'] = ("roughness", "g")
                self.texture_flags['specular_tint'] = True
            elif param == "$envmap":
                self.texture_flags['specular'] = True
            elif param == "$envmapmask":
                self.texture_files['specular'] = (self.get_text_file(value), "rgb")
            elif param == "$selfillum" and int(value) == 1:
                if 'emission' not in self.texture_files:
                    self.texture_files['emission'] = ("base", "a")
                self.texture_flags['emission'] = True
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
        else:
            mat = bpy.data.materials.new(mat_name)
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
            if self.texture_flags.get(name, None):
                pair = self.texture_files[name]
                filepath = pair[0]
                tex = None
                texname = None
                if type(filepath) is str:
                    # Relative reference, solve it
                    # If the filepath is relative, it might already have a node, so check it
                    texname = filepath
                    if texnodes.get(filepath, None):
                        tex = texnodes[filepath]
                    else:
                        filepath = self.texture_files[filepath][0]
                else:
                    texname = name
                    if texnodes.get(name, None):
                        tex = texnodes[name]
                # Create texture node if not already created
                if not tex:
                    tex = nodes.new('ShaderNodeTexImage')
                    tex.image = bpy.data.images.load(str(filepath), check_existing=True)
                    # Set to non-color data for other images than base color
                    if texname == "base":
                        tex.image.colorspace_settings.name = "sRGB"
                    else:
                        tex.image.colorspace_settings.name = "Non-Color"
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
                if name == "normal":
                    # Need to create a normal map node
                    normal = nodes.new("ShaderNodeNormalMap")
                    normal.location = (-750, tex.location[1] - 150)
                    links.new(out_node.outputs[out], normal.inputs['Color'])
                    out_node = normal
                    out = "Normal"
                if name == "roughness":
                    # Need to invert value since source format is different
                    invert = nodes.new("ShaderNodeInvert")
                    invert.location = (-750, tex.location[1] - 150)
                    links.new(out_node.outputs[out], invert.inputs['Color'])
                    out_node = invert
                    out = "Color"
                links.new(out_node.outputs[out], bsdf.inputs[texnames[name]])
        return True
