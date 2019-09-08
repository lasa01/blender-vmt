import os
import zipfile

ignore = ["__pycache__", ".vscode", ".git", ".gitignore", ".gitmodules", "install.sh", "pack_addon.py", "blender-vmt.zip"]

relroot = os.path.abspath(os.path.join(".", os.pardir))
with zipfile.ZipFile("blender-vmt.zip", "w", zipfile.ZIP_DEFLATED) as zip:
    for root, dirs, files in os.walk("."):
        print(root)
        cont = False
        for thing in ignore:
            if thing in root:
                cont = True
                break
        if cont:
            continue
        # add directory (needed for empty dirs)
        zip.write(root, os.path.relpath(root, relroot))
        for file in files:
            if file in ignore:
                continue
            filename = os.path.join(root, file)
            if os.path.isfile(filename): # regular files only
                arcname = os.path.join(os.path.relpath(root, relroot), file)
                zip.write(filename, arcname)