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
from .vmt import VMT

bl_info = {
    "name": "import-vmt",
    "author": "lasa01",
    "description": "Import Source Engine VMT files as materials",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "F3 > Import VMT",
    "warning": "",
    "category": "Import-Export"
}


class IMPORT_SCENE_OT_vmt_material(bpy.types.Operator):
    """Import Source Engine VMT file as a material"""
    bl_idname = "import_scene.vmt_material"
    bl_label = "Import VMT"
    bl_options = {'UNDO'}

    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filter_glob: bpy.props.StringProperty(default="*.vmt", options={'HIDDEN'})
    texturepath: bpy.props.StringProperty(name="Path to the converted textures", default="")
    textext: bpy.props.StringProperty(default=".png", name='Converted texture file extensions')
    materialname: bpy.props.StringProperty(default="", name='Override material name (leave empty to use name from file)')
    override: bpy.props.BoolProperty(default=False, name='Override existing material')

    def execute(self, context):
        vmt = VMT(self.filepath, self.textext, self.texturepath)
        if not vmt.make_material(self.materialname, self.override):
            self.report({'INFO'}, 'Material already exists')
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def register():
    bpy.utils.register_class(IMPORT_SCENE_OT_vmt_material)


def unregister():
    bpy.utils.unregister_class(IMPORT_SCENE_OT_vmt_material)


if __name__ == "__main__":
    register()
