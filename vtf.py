# Heavily inspired by https://github.com/Ganonmaster/io_texture_VTF/blob/blender280/vtf.py

import bpy
from pathlib import Path
from typing import Tuple, Optional

import numpy as np
from .libraries.VTFLibWrapper import VTFLib
from .libraries.VTFLibWrapper import VTFLibEnums

vtf_lib = VTFLib.VTFLib()

def import_image(path: Path) -> bpy.types.Image:
    name = path.stem
    vtf_lib.image_load(str(path))
    try:
        if vtf_lib.image_is_loaded():
            print('VTF: Image loaded successfully')
            pass
        else:
            raise Exception("VTF: Failed to load image :{}".format(vtf_lib.get_last_error()))
        rgba_data = vtf_lib.get_rgba8888()
        print('VTF: Converted')
        rgba_data = vtf_lib.flip_image_external(rgba_data, vtf_lib.width(), vtf_lib.height())
        print('VTF: Flipped')
        pixels = np.array(rgba_data.contents, np.uint8)
        pixels = pixels.astype(np.float16, copy=False)
        print("VTF: Saving rgb")
        flags = vtf_lib.get_image_flags()
        alpha = flags.get_flag(VTFLibEnums.ImageFlag.ImageFlagOneBitAlpha) or flags.get_flag(VTFLibEnums.ImageFlag.ImageFlagEightBitAlpha)
        image = bpy.data.images.new(name, width=vtf_lib.width(), height=vtf_lib.height(), alpha=alpha)
        pixels = np.divide(pixels, 255)
        image.pixels = pixels
        image.file_format = "PNG"
        image.pack()
        return image
    finally:
        vtf_lib.image_destroy()
