pluginPath=/www/server/panel/plugin/total

if hash btpython 2>/dev/null; then
    btpython $pluginPath/total_patch.py
else
    python $pluginPath/total_patch.py
fi