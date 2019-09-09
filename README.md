# blender-vmt
Tools for importing Source Engine material (.vmt) files into Blender

Blender 2.80 only

## Installation
1. Clone the repository.
2. Run `install.sh`. (You can use Git Bash under Windows.)
3. Run `python pack_addon.py`.
4. Install the addon .zip file in Blender.

## Features

### VTF Importer
`File -> Import -> Source Engine Image (.vtf)`

Allows importing a single .vtf file into Blender.
The file will be opened with the included VTFLib and packed into the .blend file as a png.

### VMT Importer
`File -> Import -> Source Engine Material (.vmt)`

Allows importing a single material from a .vmt file into Blender.

You need to have the extracted texture files in the original directory structure (`<game>/materials/[subfolder]/<textures>`).
These can be extracted from Source game files using [GCFScape](http://nemesis.thewavelength.net/index.php?p=25).
If your VMT files are in the same directory as your textures, then you don't need to specify the texture path seperately.
If you specify the texture path, the addon will look there for the texture files, instead of the folder the .vmt file is in.

If you have already converted your texture files, you can specify the texture file format.
By default it is the original .vtf format, and the textures will be imported by the addon.

You can also override the material name to whatever you want, otherwise it will use the file name.
The path should point to the game directory, which has a materials subdir (`<game>/materials/[subfolder]/<textures>`).

By default, existing materials will not be overridden but this can be toggled.

### Crafty Material Replacer
`F3 -> Replace imported Crafty materials`

Allows replacing the basic materials (diffuse map only)
that maps exported as .obj from [Crafty](http://nemesis.thewavelength.net/index.php?p=45)
contain with ones imported with this addon (diffuse, specular, roughness, normal maps etc.).

You need to first import the Crafty OBJ file into Blender.
After that, you should have the materials in the blend file, named material_xx.

Then, use this feature (`F3 -> Replace imported Crafty materials`) and select the .mtl file associated with the Crafty OBJ.
This will then load the comments from the MTL file, which include the proper material names, and load them with the addon.

You need to supply the materials path, otherwise this will not work (see VMT Importer section for more details).
You can also specify the texture extension.
The path should point to the game directory, which has a materials subdir (`<game>/materials/[subfolder]/<textures>`).

If you have duplicate materials, they might have suffixes such as .001.
You can specify this in the options.

There is also an option to rename the materials to their original names.

### Source Tools Models Materials Importer
`F3 -> Import materials for Source Models`

[Blender Source Tools](http://steamreview.org/BlenderSourceTools/) can be used to import Source Engine models.
However, it cannot import materials and instead creates empty materials with random colors.
This allows automatic importing of these materials.
It will try to import every material in the scene, so it is recommended to import them right after models, before doing anything else.

Using the feature will open a folder select dialog.
You should select the path to the materials here (see VMT Importer section for more details).
The path should point to the game directory, which has a materials subdir (`<game>/materials/[subfolder]/<textures>`).

You can also select a separate texture path and extension here (see VMT Importer section for more details).

If you select to import only empty materials, the addon will ignore materials with nodes enabled.
Materials imported from Source Tools don't have nodes enabled by default.

If you select to skip Crafty materials, the addon will skip materials that start with material_.
This is useful if you have already imported a Crafty OBJ.

Prefer higher quality weapons is useful when importing CSGO weapons.
It will prefer the higher quality materials found in v_models (view models?) directory over w_models (world models?).

The addon will search the materials directory for corresponding .vmt files.
If there are multiple .vmt files found for the same material, the first one is used.
Some directories that contain false positives (gui elements or weapon skin files) are excluded from the search.

### Currently supported .mtl parameters
All parameters are mapped to a Principled BSDF node.

- `$basetexture` -> Base Texture
- `$translucent` -> Enables Alpha (basetexture alpha channel)
- `$alphatest` -> Enables Alpha (basetexture alpha channel)
- `$bumpmap` -> Normal Map
- `$phong` -> Specular to 0.5 (or bumpmap alpha channel) and Roughness to 0.3
- `$basemapalphaphongmask` -> Basetexture alpha to Specular
- `$basemapalphaenvmapmask` -> Basetexture alpha to Specular
- `$phongexponent` -> Inverted Roughness * 0.5
- `$phongexponenttexture`-> Inverted Roughness * 0.5 (red channel)
- `$phongalbedotint` -> Enables Specular Tint (phongexponenttexture green channel)
- `$envmap` -> Specular to 0.7 and Roughness to 0.1
- `$envmapmask` -> Specular
- `$selfillum` -> Enables Emission (basetexture alpha channel)
- `$selfillummask` -> Emission

Other parameters are ignored.

## Troubleshooting
Open console in Blender to see the error messages the addon generates.

If it complains about files not existing, ensure that the file it is trying to open exists.
CSGO, for example, has some files that have a space at the end of the filename, before the extension.
This extra space needs to be removed for the addon to work.

If you get unexpected end of file when parsing materials, the .mtl file probably has invalid or unsupported syntax.
To fix this, open the .mtl file and navigate to the line that caused the error.
If the line has no relevant data (such as an empty block {}), you can safely delete it.
If the line specifies relevant data, try surrounding both the key and the value in double quotes (""), in case they aren't already.
