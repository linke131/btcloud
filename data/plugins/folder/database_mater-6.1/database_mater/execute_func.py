import os, sys
sys.path.append("class/")
os.chdir("/www/server/panel")

import argparse
import PluginLoader
import public


if __name__ == '__main__':
    args_obj = argparse.ArgumentParser(usage="必要的参数:--api 执行方法")
    args_obj.add_argument("--api", help="执行方法!")
    args_obj.add_argument("-d","--db_name", help="优化数据库!",  nargs='?')
    args_obj.add_argument("-s", "--sql_id", help="sql_id!",  nargs='?')
    args = args_obj.parse_args()
    get = public.dict_obj()
    get.fun = "execute_func"
    get.s = "execute_func"
    if args.db_name:
        print(args.db_name)
        get.db_name = args.db_name
    elif args.sql_id:
        get.sql_id = args.sql_id
    else:
        args_obj.print_help()
    get.api = args.api
    get.func = "func"
    print("开始执行")
    resp = PluginLoader.plugin_run("database_mater", "execute_func", get)
    print(resp)
    # public.print_log(f">>resp:{resp}")
