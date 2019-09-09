mkdir -p ./libraries
pip install -t ./libraries vdf
# fix a bad reference in vdf
sed -i 's/vdf.vdict/.vdict/g' libraries/vdf/__init__.py
# add support for nonquoted keys starting with $ and nonquoted values with / by replacing the regex inside the library
# I know, it looks scary
sed -i 's/(?P<key>#?\[a-z0-9\\-\\_\\\\\\?\]+))/(?P<key>#?\\$?[a-z0-9\\-\\_\\\\\\?]+))/g' libraries/vdf/__init__.py
sed -i 's/|(?P<val>\[a-z0-9\\-\\_\\\\\\?\\\*\\\.\]+)/|(?P<val>[a-z0-9\\-\\_\\\\\\?\\*\\.\\\/]+)/g' libraries/vdf/__init__.py

git clone https://github.com/Ganonmaster/VTFLibWrapper ./libraries/VTFLibWrapper
