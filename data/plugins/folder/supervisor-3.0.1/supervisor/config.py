#!/usr/bin/python
# coding: utf-8

import sys,os
# 设置运行目录  
os.chdir("/www/server/panel")
# 添加包引用位置并引用公共包  
sys.path.insert(0, "class/")
import public


def deloy():
    basedir = "/www/server/panel/plugin/supervisor"
    supervisor_conf_file = "/etc/supervisor/supervisord.conf"
    supervisor_conf_back = "/etc/supervisor/supervisord_back.conf"
    config = "%s/config.txt" % basedir

    if not os.path.isfile(config):
        os.system(r"touch {}".format(config))
    res = public.ExecShell("cat /etc/supervisor/supervisord.conf > %s" % config)
    with open(config, "r") as fr:
        infos = fr.readlines()
    fr.close()
    os.remove(config)

    # str_conf = ""
    # for m in infos:
    #     if "file=/tmp/supervisor.sock" in m:
    #         str_conf = str_conf + "file=/var/run/supervisor.sock" + "\n"
    #         continue
    #     if "logfile=/tmp/supervisord.log" in m:
    #         str_conf = str_conf + "logfile=/var/log/supervisor.log" + "\n"
    #         continue
    #     if "pidfile=/tmp/supervisord.pid" in m:
    #         str_conf = str_conf + "pidfile=/var/run/supervisor.pid" + "\n"
    #         continue
    #     if "serverurl=unix:///tmp/supervisor.sock" in m:
    #         str_conf = str_conf + "serverurl=unix:///var/run/supervisor.sock" + "\n"
    #         continue
    #     if m == ";[include]"+"\n":
    #         str_conf = str_conf + "[include]" + "\n"
    #         str_conf = str_conf + "files = /www/server/panel/plugin/supervisor/profile/*.ini" + "\n"
    #         break  
    #     str_conf += m
    if not os.path.isfile(supervisor_conf_back):
        os.system(r"touch {}".format(supervisor_conf_back))
    # res = public.writeFile(supervisor_conf_back, str_conf)
    
    os.rename('/etc/supervisor/supervisord.conf', '/etc/supervisor/supervisordp.conf')
    os.rename('/etc/supervisor/supervisord_back.conf', '/etc/supervisor/supervisord.conf')
    os.remove('/etc/supervisor/supervisordp.conf')

deloy()
# if __name__ == "__main__":
#     deloy()