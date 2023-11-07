#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 邹浩文 <627622230@qq.com>
# +-------------------------------------------------------------------

# +--------------------------------------------------------------------
# |   微擎优化脚本v1
# +--------------------------------------------------------------------

import sys,re
sys.path.append('/www/server/panel/class')
import public
def check(sitepath):
    version_file = sitepath + "/framework/version.inc.php"
    version_conf = public.readFile(version_file)
    version = None
    stype = None
    if version_conf:
        stype = version_conf.find('WeEngine')
        version = re.search('[\'\"]IMS_VERSION[\'\"],\s*[\'\"]([\.\d]+)[\'\"]',version_conf)
    if version:
        version = "v" + version.groups(1)[0]
    if stype and version:
        result = {'type':'微擎','version':version}
        return result

if __name__ == '__main__':
    sitepath = sys.argv[1]
    check(sitepath)