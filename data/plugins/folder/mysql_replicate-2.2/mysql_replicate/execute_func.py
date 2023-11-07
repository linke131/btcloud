import os, sys
sys.path.append("class/")
os.chdir("/www/server/panel")

import argparse
import PluginLoader
import public


if __name__ == '__main__':
    args_obj = argparse.ArgumentParser(usage="必要的参数：--slave_ip 从库ip\n--api 执行方法!")
    args_obj.add_argument("--slave_ip", help="从库ip!")
    args_obj.add_argument("--api", help="执行方法!")
    args = args_obj.parse_args()
    if not args.slave_ip or not args.api:
        args_obj.print_help()

    get = public.dict_obj()
    get.fun = "execute_func"
    get.s = "execute_func"
    get.slave_ip = args.slave_ip
    get.api = args.api
    PluginLoader.plugin_run("mysql_replicate", "execute_func", get)
    # public.print_log(f">>resp:{resp}")
