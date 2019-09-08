# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy
from pathlib import Path

from .vmt import VMT
from . import vtf
from .crafty import CraftyMtl
from .models import ModelsMtl

bl_info = {
    "name": "import-vmt",
    "author": "lasa01",
    "description": "Import Source Engine VMT files as materials",
    "blender": (2, 80, 0),
    "version": (0, 1, 0),
    "location": "File > Import > Source Material (.vmt)",
    "warning": "",
    "category": "Import-Export"
}


def menu_func_import(self, context):
    self.layout.operator(VmtImporter.bl_idname, text="Source Engine Material (.vmt)")
    self.layout.operator(VtfImporter.bl_idname, text="Source Engine Image (.vtf)")


class VmtImporter(bpy.types.Operator):
    """Import Source Engine VMT file as a material"""
    bl_idname = "import_scene.vmt"
    bl_label = "Import VMT"
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(subtype='FILE_PATH', options={'HIDDEN'})
    filter_glob: bpy.props.StringProperty(default="*.vmt", options={'HIDDEN'})
    texturepath: bpy.props.StringProperty(name="Path to the textures", default="", description="Leave empty to use the same folder the selected MTL file is in")
    textext: bpy.props.EnumProperty(items=[
        (".vtf", "VTF (default)", "VTF (Original format)"),
        (".png", "PNG", "PNG (Converted)"),
        (".jpeg", "JPEG", "JPEG (Converted)"),
        (".tga", "TGA", "TGA (Converted)"),
        (".bmp", "BMP", "BMP (Converted)")
    ], name="Texture file format", default=".vtf")
    materialname: bpy.props.StringProperty(default="", name='Override material name', description="Leave empty to use the name from the file")
    override: bpy.props.BoolProperty(default=False, name='Override existing material')

    def execute(self, context):
        vmt = VMT(Path(self.filepath), self.textext, Path(self.texturepath) if self.texturepath else None)
        if not vmt.make_material(self.materialname, self.override):
            self.report({'INFO'}, 'Material already exists')
            return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class VtfImporter(bpy.types.Operator):
    """Import Source Engine VTF file as a image"""
    bl_idname = "import_scene.vtf"
    bl_label = "Import VTF"
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(subtype='FILE_PATH', options={'HIDDEN'})
    filter_glob: bpy.props.StringProperty(default="*.vtf", options={'HIDDEN'})

    def execute(self, context):
        vtf.import_image(Path(self.filepath))
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class SourceModelsMtlImporter(bpy.types.Operator):
    """Import materials for Source Engine models imported in the scene"""
    bl_idname = "import_scene.sourcemodelsmtl"
    bl_label = "Import materials for Source Models"
    bl_options = {'UNDO'}

    directory: bpy.props.StringProperty(name="Path to materials", subtype='DIR_PATH')

    texturepath: bpy.props.StringProperty(name="Path to the textures", default="", description="Leave empty to use the materials path")
    textext: bpy.props.EnumProperty(items=[
        (".vtf", "VTF (default)", "VTF (Original format)"),
        (".png", "PNG", "PNG (Converted)"),
        (".jpeg", "JPEG", "JPEG (Converted)"),
        (".tga", "TGA", "TGA (Converted)"),
        (".bmp", "BMP", "BMP (Converted)")
    ], name="Texture file format", default=".vtf")
    only_empty: bpy.props.BoolProperty(name="Import only empty materials", description="Only imports materials that don't have nodes enabled", default=True)
    skip_crafty: bpy.props.BoolProperty(name="Skip Crafty-imported materials", description="Skip materials starting with material_", default=True)
    prefer_v: bpy.props.BoolProperty(name="Prefer higher quality weapons", description="Prefer higher quality materials in v_models folder over materials in w_models folder (CSGO)", default=True)

    def execute(self, context):
        models = ModelsMtl(Path(self.directory), self.textext, Path(self.texturepath) if self.texturepath else None)
        models.replace_materials(self.only_empty, self.skip_crafty, self.prefer_v)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class CraftyMtlImporter(bpy.types.Operator):
    """Import Crafty-exported MTL to replace the materials with properly imported ones"""
    bl_idname = "import_scene.craftymtl"
    bl_label = "Replace imported Crafty materials"
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(subtype='FILE_PATH', options={'HIDDEN'})
    filter_glob: bpy.props.StringProperty(default="*.mtl", options={'HIDDEN'})

    texturepath: bpy.props.StringProperty(name="Path to the textures", default="", description="Path to the folder containing 'materials' folder containing textures")
    textext: bpy.props.EnumProperty(items=[
        (".vtf", "VTF (default)", "VTF (Original format)"),
        (".png", "PNG", "PNG (Converted)"),
        (".jpeg", "JPEG", "JPEG (Converted)"),
        (".tga", "TGA", "TGA (Converted)"),
        (".bmp", "BMP", "BMP (Converted)")
    ], name="Texture file format", default=".vtf")
    materialsuffix: bpy.props.StringProperty(name="Material name suffix", default="", description="Suffix to append to material names when finding materials")
    rename: bpy.props.BoolProperty(name="Rename materials", default=True)

    def execute(self, context):
        if not self.texturepath:
            self.report({'INFO'}, 'Texture path was not specified')
            return {'CANCELLED'}
        crafty = CraftyMtl(Path(self.filepath))
        crafty.replace_materials(Path(self.texturepath), self.textext, self.materialsuffix, self.rename)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def register():
    bpy.utils.register_class(VmtImporter)
    bpy.utils.register_class(VtfImporter)
    bpy.utils.register_class(SourceModelsMtlImporter)
    bpy.utils.register_class(CraftyMtlImporter)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(VmtImporter)
    bpy.utils.unregister_class(VtfImporter)
    bpy.utils.unregister_class(SourceModelsMtlImporter)
    bpy.utils.unregister_class(CraftyMtlImporter)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
