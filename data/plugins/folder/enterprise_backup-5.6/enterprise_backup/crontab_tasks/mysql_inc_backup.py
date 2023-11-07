# coding: utf-8

import sys,os
os.chdir("/www/server/panel/")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(u'参数错误')
        sys.exit()
    sys.path.insert(0, '/www/server/panel/plugin/enterprise_backup')
    from eb_tools import request_plugin

    result = request_plugin("mysql_inc_backup",sys.argv[1])
    print(result['msg'])
    request_plugin("mysql_ddl_backup",sys.argv[1])
