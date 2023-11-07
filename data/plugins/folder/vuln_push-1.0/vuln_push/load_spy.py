import os, sys

os.chdir('/www/server/panel')
if not 'class/' in sys.path:
    sys.path.insert(0, 'class/')

import PluginLoader
res = PluginLoader.plugin_run("vuln_push", "vuln_spy", "")
