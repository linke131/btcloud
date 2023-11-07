# coding: utf-8
# -----------------------------
# 宝塔Linux面板 springboot项目管理
# Author: HUB

import sys, os, time, re, psutil, json
from xml.etree.ElementTree import ElementTree, Element

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
sys.path.append("class/")
import public, files, firewalls

class mobj:
    port = ps = ''


class springboot_manager(object):

    def __init__(self):
        pass

    # 开启springboot端口
    def release_springboot_port(self,port):
        import firewalls
        fs = firewalls.firewalls()
        get = mobj()
        get.port = port
        get.ps = 'springboot服务外部端口'
        fs.AddAcceptPort(get)
        return True

    # 启动服务
    def start_springboot_service(self,get):
        project_name = get.project_name.strip()
        port = get.port if 'port' in get else 0
        self.release_springboot_port(port)
        path = get.path
        shell_str = "cd /tmp && wget -O springboot.sh %s/install/src/webserver/shell/springboot.sh && bash -x springboot.sh install %s %s %s >>/tmp/web.json" % (public.get_url(), project_name,path,port)
        print('运行springboot启动命令：', shell_str)
        public.ExecShell(shell_str)
        return public.returnMsg(True, "启动项目{}成功".format(project_name))
         
    # 删除项目
    def delete_springboot_project(self,project_info):
        project_name = project_info['project_name']
        path = project_info['path']
        shell_str = "cd /tmp && wget -O springboot.sh %s/install/src/webserver/shell/springboot.sh && bash -x springboot.sh uninstall %s %s >>/tmp/web.json" % (public.get_url(), project_name,path)
        print('停止springboot命令：', shell_str)
        public.ExecShell(shell_str)
        return public.returnMsg(True, "停止项目{}成功".format(project_name))
    # 服务管理
    def startSpringboot(self,get,project_info):
        project_name = project_info['project_name']
        path = project_info['path'] 
        port = project_info['port'] 
        s_type = get.type.strip() if 'type' in get else 'install'
        if s_type == 'start':
            shell_str = "cd /tmp && wget -O springboot.sh %s/install/src/webserver/shell/springboot.sh && bash -x springboot.sh install %s %s %s >>/tmp/web.json" % (public.get_url(), project_name,path,port)
            print('运行springboot启动命令：', shell_str)
            public.ExecShell(shell_str)
            return public.returnMsg(True, "启动项目{}成功".format(project_name))
        elif s_type == 'stop':
            shell_str = "cd /tmp && wget -O springboot.sh %s/install/src/webserver/shell/springboot.sh && bash -x springboot.sh uninstall %s %s >>/tmp/web.json" % (public.get_url(), project_name,path)
            print('停止springboot命令：', shell_str)
            public.ExecShell(shell_str)
            return public.returnMsg(True, "停止项目{}成功".format(project_name))