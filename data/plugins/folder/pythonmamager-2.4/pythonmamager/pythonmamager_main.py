#!/www/server/panel/pyenv/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <baozi@bt.cn>
# +-------------------------------------------------------------------

# +--------------------------------------------------------------------
# |   pythone管理器
# +--------------------------------------------------------------------
import os, sys
from typing import Dict, List, Union, Optional

os.chdir("/www/server/panel")
sys.path.append("class/")
import public, time, json, re, platform

try:
    from plugin.supervisor.supervisor_main import supervisor_main
except:
    pass


class PythonProjectShell:
    start = ''
    stop = ''
    check = ''
    start_spr = ''

    def __str__(self):
        return "<<\nstart: {}\nstop: {}\ncheck: {}\nstart_spr: {}\n>>".format(
            self.start, self.stop, self.check, self.start_spr
        )


class pythonmamager_main:
    basedir = "/www/server/panel/plugin/pythonmamager"
    __conf_path = "%s/config.json" % basedir
    _conf: Optional[List[Dict]] = None
    logpath = "%s/logs" % basedir
    pipsource = "https://mirrors.aliyun.com/pypi/simple/"
    access_defs = ['auto_start']
    supervisor_msg = ''
    # 0: 没有， 1.有， 2.版本低于3
    supervisor_type = 0
    psh: Optional[PythonProjectShell] = None

    def __init__(self):
        self.pyenv_path = "/root/.pyenv"
        if not os.path.exists(self.pyenv_path):
            self.pyenv_path = "/.pyenv"
        self._get_conf()
        self.__check_supervisor_install()
        self._supervisor_list: Optional[List[Dict]] = None

    # 获取supervisor_list
    @property
    def supervisor_list(self) -> List[Dict]:
        if self._supervisor_list is not None:
            return self._supervisor_list
        if self.supervisor_type:
            self._supervisor_list = supervisor_main().GetProcessList(None)
            return self._supervisor_list
        else:
            return []

    # 检查supervisord是否可用
    def __check_supervisor_install(self) -> str:
        panel_path = public.get_panel_path()
        supervisord_path = '{}/pyenv/bin/supervisord'.format(panel_path)
        supervisor_path = '{}/pyenv/bin/supervisorctl'.format(panel_path)
        supervisor_main = '{}/plugin/supervisor/supervisor_main.py'.format(panel_path)
        supervisor_info = '{}/plugin/supervisor/info.json'.format(panel_path)
        msg = '进程守护管理插件未安装或相关依赖未成功安装，请按以下方式排查：<br/>1、进程守护管理器插件是否安装<br/>2、{}文件是否存在<br/>3、{}文件是否存在'.format(
            supervisor_main, supervisor_path)
        if os.path.isfile(supervisord_path) and os.path.isfile(supervisor_path) and \
                os.path.isfile(supervisor_main) and os.path.isfile(supervisor_info):
            info = json.loads(public.readFile(supervisor_info))
            if int(info["versions"][0]) < 3:
                self.supervisor_type = 2
                self.supervisor_msg = "进程守护管理插件版本较低，可能会出现问题"
            else:
                self.supervisor_type = 1
                self.supervisor_msg = ""
        else:
            self.supervisor_type = 0
            self.supervisor_msg = msg
        return self.supervisor_msg

    # 检查端口
    @staticmethod
    def __check_port(port) -> Dict:
        try:
            if 1 < int(port) < 65535:
                data = public.ExecShell("ss  -nultp | grep ':%s '" % port)[0]
                if data:
                    return public.returnMsg(False, "该端口已经被占用")
            else:
                return public.returnMsg(False, "请输入正确的端口范围 1 < 端口 < 65535")
        except ValueError:
            return public.returnMsg(False, "端口请输入整数")

    # 加载所有数据
    def _get_conf(self) -> None:
        if self._conf is not None:
            return
        if not os.path.exists(self.__conf_path):
            public.writeFile(self.__conf_path, '[]')
            self._conf = []
            return
        _conf_data = public.readFile(self.__conf_path)
        if not _conf_data:
            public.writeFile(self.__conf_path, '[]')
            self._conf = []
        try:
            self._conf = json.loads(_conf_data)
        except:
            self._conf = []
            public.writeFile(self.__conf_path, '[]')

    # 检查输入参数
    def __check_args(self, get) -> Dict:
        values = {}
        if hasattr(get, "pjname"):
            pjname = get.pjname.strip()
            if sys.version_info.major < 3:
                if len(pjname) < 3 or len(pjname) > 15:
                    return public.returnMsg(False, '名称必须大于3小于15个字符串')
            else:
                if len(pjname.encode("utf-8")) < 3 or len(pjname.encode("utf-8")) > 15:
                    return public.returnMsg(False, '名称必须大于3小于15个字符串')
            values["pjname"] = pjname
        if hasattr(get, "port"):
            port = get.port.strip()
            if port != "":
                result = self.__check_port(port)
                if result:
                    return result
            values["port"] = port
        if hasattr(get, "path"):
            values["path"] = get.path.strip()
            if values["path"][-1] == '/':
                values["path"] = values["path"][:-1]
        if hasattr(get, "version"):
            values["version"] = get.version.strip()
        if hasattr(get, "install_module"):
            values["install_module"] = get.install_module.strip()
        if hasattr(get, "framework"):
            danger_args = ["rm -f", "rm -rf"]
            for i in danger_args:
                if i in get.framework:
                    return public.returnMsg(False, '命令行含有危险命令。。')
            values["framework"] = get.framework
            # if values["framework"] not in frameworks:
            #     get.rfile = ""
        if hasattr(get, "rtype"):
            values["rtype"] = get.rtype.strip()
        if hasattr(get, "rfile"):
            values["rfile"] = get.rfile.strip()
        if hasattr(get, "auto_start"):
            values["auto_start"] = get.auto_start.strip()
        if hasattr(get, "user"):
            if get.user in ['root', 'www']:
                values["user"] = get.user.strip()
        if hasattr(get, "parm"):
            values["parm"] = get.parm.strip()
        else:
            values["parm"] = ''
        if hasattr(get, "logpath"):
            values["log_path"] = get.logpath.strip()
        else:
            values["log_path"] = values["path"] + "/logs"
        values["numprocs"] = 0
        if hasattr(get, 'numprocs'):
            values["numprocs"] = get.numprocs.strip()
        values["is_supervisor"] = 0
        if hasattr(get, 'is_supervisor'):
            values["is_supervisor"] = get.is_supervisor.strip()
        return values

    # 检查项目是否存在
    def __check_project_exist(self, data: Dict) -> Union[str, bool]:
        self._get_conf()
        for i in self._conf:
            if data["pjname"] == i["pjname"]:
                return "已存在相同名称的项目"
            if data["path"] == i["path"]:
                return "已存在相同路径的项目【{}】".format(i["pjname"])
        return False

    # 获取虚拟环境pip
    @staticmethod
    def _get_v_pip(v_path):
        if os.path.exists('{}/bin/pip3'.format(v_path)):
            return '{}/bin/pip3'.format(v_path)
        else:
            return '{}/bin/pip'.format(v_path)

    # 获取虚拟环境python
    @staticmethod
    def _get_v_python(v_path):
        if os.path.exists('{}/bin/python3'.format(v_path)):
            return '{}/bin/python3'.format(v_path)
        else:
            return '{}/bin/python'.format(v_path)

    # 获取依赖文件requirements.txt
    @staticmethod
    def _get_requirements(path) -> Union[bool, str]:
        requirements = "%s/requirements.txt" % path
        if not os.path.exists(requirements):
            return False
        return requirements

    # 安装模块
    def __install_module(self, v_path, requirements_path) -> None:
        if requirements_path is False:
            self._write_log("未找到依赖包文件requirements.txt")
            return
        else:
            self._write_log("开始安装依赖包")
        path = "%s/py.log" % self.basedir
        _sh = "{} -m pip install -i {} -r {} &>> {}".format(
            self._get_v_python(v_path), self.pipsource, requirements_path, path
        )
        public.ExecShell(_sh)

    # 安装服务器运行应用库
    def __install_run_server(self, values) -> None:
        """安装服务器部署应用
        @author baozi <202-02-22>
        @param:
            values  ( dict ):  用户输入信息
        @return bool : 返回是否安装成功
        """
        self._write_log("开始安装服务器应用")
        log_path = "%s/py.log" % self.basedir
        _sh = "{} install -i {} %s &>> {}".format(self._get_v_pip(values['vpath']), self.pipsource, log_path)
        public.ExecShell(_sh % ("uwsgi",))
        public.ExecShell(_sh % ("gunicorn",))
        public.ExecShell(_sh % ("uvicorn",))

    # 准备启动的配置文件
    def __prepare_start_conf(self, values) -> None:
        """准备启动的配置文件,python运行不需要,uwsgi和gunicorn需要
        @author baozi <202-02-22>
        @param:
            values  ( dict ):  用户传入的参数
        @return   :
        """
        # 加入默认配置
        values["user"] = values['user'] if 'user' in values else 'root'
        if not os.path.exists(values['log_path']):
            os.makedirs(values['log_path'], mode=0o777)
        if values["rtype"] == "uwsgi":
            self.__prepare_uwsgi_start_conf(values)
        elif values["rtype"] == "gunicorn":
            self.__prepare_gunicorn_start_conf(values)

    # 构造uwsgi配置文件
    @staticmethod
    def __prepare_uwsgi_start_conf(values):
        # uwsgi
        config_body = """[uwsgi]
master = true
processes = 1
threads = 2
master = true
chdir = {path}
wsgi-file= {rfile}
http = 0.0.0.0:{port}
logto = {path}/logs/error.log
chmod-socket = 660
vacuum = true
uid={user}
gid={user}
max-requests = 1000""".format(path=values["path"], port=values["port"], rfile=values["rfile"], user=values["user"])
        uwsgi_file = "{}/uwsgi.ini".format(values['path'])
        public.writeFile(uwsgi_file, config_body)

    # 构造gunicorn配置文件
    @staticmethod
    def __prepare_gunicorn_start_conf(values):
        # gunicorn
        worker_class = "sync" if values["framework"] != "sanic" else 'uvicorn.workers.UvicornWorker'
        logformat = '%(t)s %(p)s %(h)s "%(r)s" %(s)s %(L)s %(b)s %(f)s" "%(a)s"'
        config_body = """bind = '0.0.0.0:{port}'
user = '{user}'
workers = 1
threads = 2
backlog = 512
chdir = '{chdir}'
access_log_format = '{log}'
loglevel = 'info'
worker_class = '{worker}'
errorlog = chdir + '/logs/error.log'
accesslog = chdir + '/logs/access.log'
pidfile = chdir + '/logs/{pjname}.pid'""".format(
            port=values["port"], chdir=values["path"], log=logformat,
            worker=worker_class, pjname=values["pjname"], user=values["user"])
        gconf_file = f"{values['path']}/gunicorn_conf.py"
        public.writeFile(gconf_file, config_body)

    # 构造系统服务文件
    @staticmethod
    def create_system_file(name, start_sh, stop_sh, cover=False):
        run_file = "/etc/init.d/{}_pymanager".format(name)
        service_file = "/lib/systemd/system/{}_pymanager".format(name)
        if os.path.isfile(run_file) and os.path.isfile(service_file) and not cover:
            return True
        _sh = """#!/bin/bash
# chkconfig: 2345 55 25
# description: {name}

### BEGIN INIT INFO
# Provides:          {name}
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: {name}
# Description:       {name}
### END INIT INFO
start() {{
  echo "Starting {name} service..."
  {sh}
}}
stop() {{
  echo "Stopping {name} service..."
  {check_sh}
}}
restart() {{
  echo "Restarting {name} service..."
  stop
  sleep 1
  start
}}
case "$1" in
  start)
    start
    ;;
  stop)
    stop
    ;;
  restart)
    restart
    ;;
  *)
    echo "Usage: $0 {{start|stop|restart}}"
    exit 1
esac
exit 0
""".format(name=name, sh=start_sh, check_sh=stop_sh)
        public.writeFile(run_file, _sh)
        os.chmod(run_file, 755)
        service_sh = """[Unit]
Description=-------{name}---------
After=network.target
[Service]
Type=forking
ExecStart=/bin/sh -c '{file} start'

ExecReload=/bin/sh -c '{file} restart'

ExecStop=/bin/sh -c '{file} stop'

Restart=on-failure

[Install]
WantedBy=multi-user.target""".format(name=name, file=run_file)
        public.writeFile(service_file, service_sh)
        public.ExecShell('systemctl daemon-reload')

    # 构造和获取管理这个项目的shell脚本
    def get_pj_sh(self, project_conf: Dict, change_project: bool = False) -> PythonProjectShell:
        """
        @name 取启动脚本
        @auther baozi
        PS：使用 change_project 改变其他调用了get_pj_sh时所指向的项目，当出现批量操作时，在每个循环内必须先调用并change_project=True
        """
        if isinstance(self.psh, PythonProjectShell) and not change_project:
            return self.psh
        psh = PythonProjectShell()
        if project_conf["rtype"] not in ("python", "gunicorn", "uwsgi"):
            run_user = ""
            v_python = self._get_v_python(project_conf['vpath'])
            if 'user' in project_conf and project_conf['user'] == 'www':
                run_user = "sudo -u {}".format(project_conf['user'])
            psh.start = " nohup {} {} {} &".format(run_user, v_python, project_conf['rfile'])
            psh.start_spr = " {} {} {}".format(run_user, v_python, project_conf['rfile'])
            psh.check = "ps aux|grep '{}'|grep -v 'grep'|wc -l".format(project_conf['rfile'])
            psh.stop = "kill -s 9 `ps aux|grep '%s' |grep -v 'grep' | awk '{print $2}'`" % project_conf['rfile']
        elif project_conf["rtype"] == "python":
            v_python = self._get_v_python(project_conf['vpath'])
            psh.start = "nohup {vpath} -u {run_file} {parm} >> {log} 2>&1 &".format(
                vpath=v_python,
                run_file=project_conf['rfile'],
                log=project_conf['log_path'] + "/error.log".replace("//", "/"),
                parm=project_conf['parm']
            )
            psh.start_spr = psh.start[6:-1]
            psh.check = "ps aux|grep '{}'|grep -v 'grep'|wc -l".format(project_conf['rfile'])
            psh.stop = "kill -s 9 `ps aux|grep '%s' |grep -v 'grep' | awk '{print $2}'`" % project_conf['rfile']
        elif project_conf["rtype"] == "uwsgi":
            if not os.path.exists(project_conf['path'] + "/uwsgi.ini"):
                self.__prepare_uwsgi_start_conf(project_conf)
            psh.start = "%s/bin/uwsgi -d --ini %s/uwsgi.ini" % (project_conf['vpath'], project_conf['path'])
            psh.start_spr = "%s/bin/uwsgi --ini %s/uwsgi.ini" % (project_conf['vpath'], project_conf['path'])
            psh.check = "ps aux|grep '{}/bin/uwsgi'|grep -v 'grep'|wc -l".format(project_conf['vpath'])
            psh.stop = "kill -s 9 `ps aux|grep '%s/bin/uwsgi' |grep -v 'grep' | awk '{print $2}'`" % project_conf['vpath']
        else:
            if not os.path.exists(project_conf['path'] + "/gunicorn_conf.py"):
                self.__prepare_gunicorn_start_conf(project_conf)
            _app = project_conf['rfile'].replace((project_conf['path'] + "/"), "")[:-3]
            _app = _app.replace("/", ".")
            if project_conf['framework'] == "django":
                _app += ":application"
            else:
                _app += ":app"
            log_file = '{}/gunicorn_error.log'.format(project_conf["log_path"])
            psh.start = "nohup %s/bin/gunicorn -c %s/gunicorn_conf.py %s &>> %s &" % (
                project_conf['vpath'], project_conf['path'], _app, log_file)
            psh.start_spr = "%s/bin/gunicorn -c %s/gunicorn_conf.py %s &>> %s" % (
                project_conf['vpath'], project_conf['path'], _app, log_file)
            psh.check = "ps aux|grep '{}/bin/gunicorn' |grep -v 'grep'|wc -l".format(project_conf['vpath'])
            psh.stop = "kill -s 15 `ps aux|grep '%s/bin/gunicorn' |grep -v 'grep' | awk '{print $2}'`" % project_conf['vpath']
        return psh

    # 启动服务的核心代码
    def _start_project(self, conf: Dict, with_out_supervisor: bool = False, try_again: bool = True) -> bool:
        psh = self.get_pj_sh(conf)
        now_run = int(public.ExecShell(psh.check)[0].strip("\n")) != 0
        if now_run:
            return True
        if "is_supervisor" in conf and conf["is_supervisor"] in (1, "1") and not with_out_supervisor:
            return self.__start_supervisor(conf)
        self.create_system_file(conf["pjname"], psh.start, psh.stop)
        public.ExecShell('systemctl start {}_pymanager'.format(conf["pjname"]))
        time.sleep(0.5)
        if int(public.ExecShell(psh.check)[0].strip("\n")) == 0:
            public.ExecShell('/etc/init.d/{}_pymanager start'.format(conf["pjname"]))
            time.sleep(0.5)
        if int(public.ExecShell(psh.check)[0].strip("\n")) == 0 and try_again:
            # 都启动失败就尝试重写文件再启动
            self.create_system_file(conf["pjname"], psh.start, psh.stop, cover=True)
            self._start_project(conf, with_out_supervisor, try_again=False)
        return int(public.ExecShell(psh.check)[0].strip("\n")) != 0

    # 是否是通过守护进程启动的
    def is_run_by_supervisor(self, conf: Dict) -> bool:
        if not self.supervisor_type:
            return False
        for prj in self.supervisor_list:
            if prj["program"] == conf["supervisor_name"] and bool(prj["status"]):
                return True
        return False

    # 停止服务的核心代码
    def _stop_project(self, conf: Dict, try_again: bool = True) -> bool:
        psh = self.get_pj_sh(conf)
        now_run = int(public.ExecShell(psh.check)[0].strip("\n")) != 0
        if not now_run:
            return True
        if "is_supervisor" in conf and conf["is_supervisor"] in (1, "1") and self.is_run_by_supervisor(conf):
            return self.__stop_supervisor(conf)
        self.create_system_file(conf["pjname"], psh.start, psh.stop)
        public.ExecShell('systemctl stop {}_pymanager'.format(conf["pjname"]))
        time.sleep(0.5)
        if int(public.ExecShell(psh.check)[0].strip("\n")) != 0:
            public.ExecShell('/etc/init.d/{}_pymanager stop'.format(conf["pjname"]))
            time.sleep(0.5)
        if int(public.ExecShell(psh.check)[0].strip("\n")) != 0 and try_again:
            # 都启动失败就尝试重写文件再启动
            self.create_system_file(conf["pjname"], psh.start, psh.stop, cover=True)
            self._stop_project(conf, try_again=False)
        return int(public.ExecShell(psh.check)[0].strip("\n")) == 0

    def save_conf(self, data: Optional[Dict] = None) -> None:
        if data:
            self._conf.append(data)
        public.writeFile(self.__conf_path, json.dumps(self._conf))

    def del_conf(self, data: Dict) -> None:
        idx = -1
        for i in range(len(self._conf)):
            if self._conf[i] is data:
                idx = i
        if idx == -1:
            return
        del self._conf[idx]
        self.save_conf()

    # 判断当前项目是否在守护中
    def _supervisor_exists(self, supervisor_name: str) -> bool:
        for i in self.supervisor_list:
            if i["program"] == supervisor_name:
                return True
        return False

    # 从守护开启
    def __start_supervisor(self, conf: Dict) -> bool:
        if not self.supervisor_type:
            return False
        if not self._supervisor_exists(conf["supervisor_name"]):
            return False
        args = public.dict_obj()
        args.program = conf["supervisor_name"]
        res = supervisor_main().StartProcess(args)
        return res["status"]

    # 停止守护
    def __stop_supervisor(self, conf: Dict) -> bool:
        if not self.supervisor_type:
            return False
        if not self._supervisor_exists(conf["supervisor_name"]):
            return False
        args = public.dict_obj()
        args.program = conf["supervisor_name"]
        res = supervisor_main().StopProcess(args)
        return res["status"]

    # 移除守护
    def __remove_supervisor(self, conf: Dict) -> None:
        if not self.supervisor_type:
            return None
        if not self._supervisor_exists(conf["supervisor_name"]):
            return None
        args = public.dict_obj()
        args.program = conf["supervisor_name"]
        supervisor_main().RemoveProcess(args)

    # 添加守护
    def __set_supervisor(self, conf: Dict) -> bool:
        if not self.supervisor_type:
            return False
        psh = self.get_pj_sh(conf)
        args = public.dict_obj()
        args.pjname = conf['supervisor_name']
        args.user = 'root'
        args.path = (conf['path'] + '/').replace('//', '/')
        args.command = psh.start_spr
        args.ps = "python项目管理器:{}".format(conf["pjname"])
        args.numprocs = str(conf['numprocs'] if conf['numprocs'] else '3')
        res = supervisor_main().AddProcess(args)
        public.print_log(res["msg"].encode().decode("utf-8"))
        return res["status"]

    def get_conf_by_name(self, name: str) -> Optional[Dict]:
        for i in self._conf:
            if i["pjname"] == name:
                return i
        return None

    # 自定义启动
    # def __start_with_customize(self, values):
    #     run_user = ""
    #     if 'user' in values and values['user'] == 'www':
    #         run_user = "sudo -u {}".format(values['user'])
    #     sh = " nohup {} {} {} &".format(run_user, self._get_v_python(values['vpath']), values['rfile'])
    #     check_sh = "{} {}".format(values['vpath'], values['rfile'])
    #     self._create_sh(values['pjname'], sh, check_sh)
    #     public.ExecShell('systemctl restart {}_pymanager'.format(['pjname']))
    #
    # # 使用python启动
    # def __start_with_python(self, values):
    #     if not os.path.exists(values['log_path']):
    #         public.ExecShell("mkdir -p %s" % values['log_path'])
    #     sh, check_sh = self.get_start_sh(values)
    #     self._write_log(sh)
    #     self._create_sh(values['pjname'], sh, check_sh)
    #     # public.ExecShell(sh)
    #     public.ExecShell('systemctl restart {}_pymanager'.format(values['pjname']))
    #     time.sleep(1)
    #
    # # 使用uwsgi启动
    # def __start_with_wsgi(self, values):
    #     path = values['path']
    #     vpath = values['vpath']
    #     pjname = values['pjname']
    #     user = values['user'] if 'user' in values else 'root'
    #     port = values['port']
    #     rfile = values['rfile']
    #     run = values['run']
    #     framework = values['framework']
    #     if path[-1] == "/":
    #         path = path[:-1]
    #     if framework == "sanic":
    #         return public.returnMsg(False, "sanic框架项目请使用gunicorn或pyhton启动")
    #     a = public.ExecShell("{} install -i {} uwsgi".format(
    #         self.get_vpath_pip(vpath), self.pipsource))
    #     self._write_log(a[0])
    #     # 添加uwcgi配置
    #     uconf = """[uwsgi]
    # master = true
    # processes = 1
    # threads = 2
    # chdir = {path}
    # wsgi-file= {rfile}
    # http = 0.0.0.0:{port}
    # logto = {path}/logs/error.log
    # chmod-socket = 660
    # vacuum = true
    # uid={user}
    # gid={user}
    # max-requests = 1000""".format(path=path, port=port, rfile=rfile, user=user)
    #     uwsgi_file = "%s/uwsgi.ini" % path
    #     if not os.path.exists(uwsgi_file):
    #         public.writeFile(uwsgi_file, uconf)
    #     public.ExecShell("mkdir %s/logs" % path)
    #     sh, check_sh = self.get_start_sh(values)
    #     self._create_sh(pjname, sh, check_sh)
    #     # public.ExecShell(sh)
    #     public.ExecShell('systemctl restart {}_pymanager'.format(pjname))
    #     time.sleep(1)
    #
    # # 使用gunicorn启动
    # def __start_with_gunicorn(self, values):
    #     path = values['path']
    #     vpath = values['vpath']
    #     pjname = values['pjname']
    #     user = values['user'] if 'user' in values else 'root'
    #     worker = values['worker']
    #     port = values['port']
    #     run = values['run']
    #     a = public.ExecShell(
    #         "{} install -i {} gunicorn gevent-websocket".format(
    #             self.get_vpath_pip(vpath), self.pipsource))
    #     self._write_log(a[0])
    #     # 添加gunicorn配置
    #     logformat = '%(t)s %(p)s %(h)s "%(r)s" %(s)s %(L)s %(b)s %(f)s" "%(a)s"'
    #     gconf = """bind = '0.0.0.0:{port}'
    # user = '{user}'
    # workers = 1
    # threads = 2
    # backlog = 512
    # chdir = '{chdir}'
    # access_log_format = '{log}'
    # loglevel = 'info'
    # {worker}
    # errorlog = chdir + '/logs/error.log'
    # accesslog = chdir + '/logs/access.log'
    # pidfile = chdir + '/logs/{pjname}.pid'""".format(
    #         port=port, chdir=path, log=logformat, worker=worker, pjname=pjname, user=user)
    #     gunicorn_file = "%s/gunicorn_conf.py" % path
    #     if not os.path.exists(gunicorn_file):
    #         public.writeFile(gunicorn_file, gconf)
    #     public.ExecShell("mkdir %s/logs" % path)
    #     sh, check_sh = self.get_start_sh(values)
    #
    # # 选择启动方式
    # def __select_framework(self, values):
    #     rtype = values['rtype']
    #     rtypes = ["python", "gunicorn", "uwsgi"]
    #     if rtype not in rtypes:
    #         self.__start_with_customize(values)
    #         return
    #     start_args = self.__structure_start_args(values)
    #     values['run'] = start_args["run"]
    #     values['worker'] = start_args["worker"]
    #     # framework = start_args["framework"]
    #     # rproject = start_args["rproject"]
    #     if rtype == "python":
    #         self.__start_with_python(values)
    #
    #     if rtype == "uwsgi":
    #         self.__start_with_wsgi(values)
    #
    #     if rtype == "gunicorn":
    #         self.__start_with_gunicorn(values)

    @staticmethod
    def __remove_python_cron(conf: Dict) -> None:
        import crontab
        name = conf["pjname"]
        cron_name = '[勿删]python项目管理器日志切割任务[{}]'.format(name)
        cron_path = public.GetConfigValue('setup_path') + '/cron/'
        cron_list = public.M('crontab').where("name=?", (cron_name,)).select()
        for i in cron_list:
            if not i:
                continue
            cron_echo = i['echo']
            args = {"id": i['id']}
            crontab.crontab().DelCrontab(args)
            del_cron_file = cron_path + cron_echo
            public.ExecShell("crontab -u root -l| grep -v '{}'|crontab -u root -".format(del_cron_file))

    # 执行定时任务
    def exec_crontab(self, name):
        from datetime import date, timedelta
        conf = self.get_conf_by_name(name)
        yesterday = (date.today() + timedelta(days=-1)).strftime("%Y-%m-%d")
        try:
            _sh = 'cd {} && tar -zcvf {}_{}.tar.gz access.log error.log'.format(
                conf['log_path'], conf['pjname'], yesterday)
            public.ExecShell(_sh)
            return True
        except:
            return False

    # 添加日志切割任务
    @staticmethod
    def add_crontab(data: Dict):
        python_path = '/www/server/panel/plugin/pymanager/bin/python'
        try:
            python_path = public.ExecShell('which btpython')[0].strip("\n")
        except:
            try:
                python_path = public.ExecShell('which python')[0].strip("\n")
            except:
                pass
        args = {
            "name": "[勿删]python项目管理器日志切割任务[{}]".format(data['pjname']),
            "type": 'day',
            "where1": '',
            "hour": '0',
            "minute": '1',
            "sName": data['pjname'],
            "sType": 'toShell',
            "notice": '0',
            "notice_channel": '',
            "save": '',
            "save_local": '1',
            "backupTo": '',
            "sBody": '{} /www/server/panel/plugin/pythonmamager/python_crontab.py  --cron_name {}'.format(
                python_path, data['pjname'], data['pjname']),
            "urladdress": ''
        }
        import crontab
        res = crontab.crontab().AddCrontab(args)
        if res and "id" in res.keys():
            return True
        return False

    # 获取新的 supervisor_name
    def get_new_supervisor_name(self, pjname):
        while True:
            supervisor_name = pjname + "-python-" + public.GetRandomString(5)
            if not self._supervisor_exists(supervisor_name):
                break
        return supervisor_name

    # 创建python项目
    def CreateProject(self, get):
        values = self.__check_args(get)
        if 'is_supervisor' in values and values['is_supervisor'] in ['1', 1]:
            if values["user"] != 'root':
                return public.returnMsg(False, "非root用户可能导致添加进程守护失败，请选择root用户")
            if not self.supervisor_type:
                return public.returnMsg(False, self.supervisor_msg)
        if "status" in values:
            return values
        msg = self.__check_project_exist(values)
        if msg:
            return public.returnMsg(False, msg)
        vpath = values["path"] + "/" + public.md5(values["pjname"]) + "_venv"
        vpath = vpath.replace("//", "/")
        get.vpath = vpath
        values["vpath"] = vpath
        if not os.path.exists(vpath):
            self._write_log("开始复制环境 {}".format(vpath))
            self.copy_pyv(get)
        self.__install_run_server(values)
        if values["install_module"] in ("1", 1):
            self.__install_module(vpath, self._get_requirements(values["path"]))
        data = {
            "pjname": values["pjname"],
            "version": values["version"],
            "rfile": values["rfile"],
            "path": values["path"],
            "vpath": vpath,
            "status": "0",
            "port": values["port"],
            "rtype": values["rtype"],
            "proxy": "",
            "framework": values["framework"],
            "auto_start": values['auto_start'],
            "user": values["user"],
            "parm": values["parm"],
            "log_path": os.path.join(values["path"], 'logs') if "log_path" not in values else values["log_path"],
            "is_supervisor": values["is_supervisor"],
            "numprocs": values["numprocs"],
            "supervisor_name": ''
        }
        psh = self.get_pj_sh(data)
        self.__prepare_start_conf(data)
        self.create_system_file(data["pjname"], psh.start, psh.stop)
        self._set_sys_auto_start(values["pjname"], values['auto_start'])
        self.add_crontab(data)
        tip = "项目建立成功"
        if self.supervisor_type == 2:
            tip += '<br>' + self.supervisor_msg
        if values['is_supervisor'] in ['1', 1]:
            data["supervisor_name"] = self.get_new_supervisor_name(values["pjname"])
            if not self.__set_supervisor(data):
                self.save_conf(data)
                return public.returnMsg(True, "进程守护管理插件添加项目失败,请检查该运行目录是否存在!")
        if not self._start_project(data):
            tip += '<br>项目启动失败'
        time.sleep(1)
        self.save_conf(data)
        return public.returnMsg(True, tip)

    # 获取项目详细信息
    def GetLoad(self, pjname):
        conf = self.get_conf_by_name(pjname)
        if not conf:
            return {"cpu": 0, "mem": 0}
        cpunum = int(public.ExecShell('cat /proc/cpuinfo |grep "processor"|wc -l')[0])
        try:
            cpu_sh = "ps aux|grep '%s'|awk '{cpusum += $3};END {print cpusum}'" % conf["path"]
            cpu = round(float(public.ExecShell(cpu_sh)[0]) / cpunum, 2)
            mem_sh = "ps aux|grep '%s'|grep -v 'grep'|awk '{memsum+=$6};END {print memsum}'" % conf["path"]
            mem = round(float(public.ExecShell(mem_sh)[0]) / 1024, 2)
            return {"cpu": cpu, "mem": mem}
        except:
            return {"cpu": 0, "mem": 0}

    # 取文件配置
    def GetConfFile(self, get):
        import files
        conf = self.get_conf_by_name(get.pjname.strip())
        if not conf:
            return public.returnMsg(False, "没有该项目")
        if conf["rtype"] == "gunicorn":
            get.path = conf["path"] + "/gunicorn_conf.py"
        elif conf["rtype"] == "uwsgi":
            get.path = conf["path"] + "/uwsgi.ini"
        else:
            return public.returnMsg(False, "Python启动方式没有配置文件可修改")
        f = files.files()
        return f.GetFileBody(get)

    # 检测修改的port
    def __change_conf_port(self, config, py_conf):
        rep_socket = "\n\s?socket\s{0,4}="
        socket = re.search(rep_socket, config)
        if socket:
            py_conf["port"] = ""
        rep_port = r"\n[^#]+:(\d+)\n"
        try:
            search_result = re.search(rep_port, config)
            new_port = None
            if search_result:
                new_port = search_result.group(1)
            if new_port:
                result = self.__check_port(new_port)
                if result is not None:
                    return result
                if new_port != py_conf["port"]:
                    py_conf["port"] = new_port
                return None
        except Exception as e:
            return e

    # 保存文件配置
    def SaveConfFile(self, get):
        import files
        conf = self.get_conf_by_name(get.pjname.strip())
        if not conf:
            return public.returnMsg(False, "没有该项目")

        result = self.__change_conf_port(get.data, conf)
        if not result:
            self.save_conf()
        else:
            return result
        if conf["rtype"] == "python":
            return public.returnMsg(False, "Python启动方式没有配置文件可修改")
        elif conf["rtype"] == "gunicorn":
            get.path = conf["path"] + "/gunicorn_conf.py"
        else:
            get.path = conf["path"] + "/uwsgi.ini"
        f = files.files()
        result = f.SaveFileBody(get)
        if result["status"]:
            return public.returnMsg(True, "配置修改成功，请手动重启项目")
        else:
            return public.returnMsg(False, "保存失败")

    # 获取项目列表
    def GetPorjectList(self, get):
        """
        @name 获取项目列表
        @author baozi
        return 增加supervisor状态（is_supervisor：是否添加到守护进程，supervisor_status：守护进程状态）
        """
        res = []
        for pj in self._conf:
            _psh = self.get_pj_sh(pj, change_project=True)
            tmp = {
                'cpu': 0,
                'mem': 0,
                'supervisor_status': 0,
            }
            if int(public.ExecShell(_psh.check)[0].strip("\n")) != 0:
                pj["status"] = "1"
                load = self.GetLoad(pj["pjname"])
                tmp["cpu"] = load["cpu"]
                tmp["mem"] = load["mem"]
            else:
                pj["status"] = "0"
            if bool(pj["supervisor_name"]) and self._supervisor_exists(pj["supervisor_name"]):
                pj["is_supervisor"] = "1"
                for spr_pj in self.supervisor_list:
                    if pj["supervisor_name"] == spr_pj["program"]:
                        tmp["supervisor_status"] = spr_pj["status"]
            else:
                pj["is_supervisor"] = 0
                pj["supervisor_name"] = ""
                tmp["supervisor_status"] = 0
            tmp.update(**pj)
            res.append(tmp)
        self.save_conf()
        return res

    # 获取framework兼容老版本
    @staticmethod
    def __get_framework(path) -> str:
        requirements = "%s/requirements.txt" % path
        if "django" in requirements:
            framework = "django"
        elif "flask" in requirements:
            framework = "flask"
        elif "sanic" in requirements:
            framework = "sanic"
        else:
            framework = "python"
        return framework

    # 启动项目
    def StartProject(self, get):
        pj_name = get if isinstance(get, str) else getattr(get, "pjname", "")
        conf = self.get_conf_by_name(pj_name.strip())
        if not conf:
            return public.returnMsg(False, "没有该项目")
        if not os.path.exists(self.logpath):
            public.ExecShell("mkdir -p %s" % self.logpath)

        psh = self.get_pj_sh(conf)
        running = int(public.ExecShell(psh.check)[0].strip("\n")) != 0
        with_out_supervisor = int(getattr(get, "is_supervisor", 0)) == 0
        spr_status = bool(conf["supervisor_name"]) and self._supervisor_exists(conf["supervisor_name"])
        if running:
            if with_out_supervisor:  # 不以守护进程的方式启动，且现在已经启动
                return public.returnMsg(True, "项目已启动")
            else:  # 以守护进程的方式启动，且现在已经启动
                self._stop_project(conf)
                if not spr_status and self.supervisor_type:
                    conf["supervisor_name"] = self.get_new_supervisor_name(pj_name)
                    self.__set_supervisor(conf)
        else:
            if not with_out_supervisor and not spr_status and self.supervisor_type:
                conf["supervisor_name"] = self.get_new_supervisor_name(pj_name)
                self.__set_supervisor(conf)

        self.save_conf()
        if not self._start_project(conf, with_out_supervisor):
            return public.returnMsg(False, "启动失败,请查看日志")
        else:
            return public.returnMsg(True, "启动成功")

    # 停止项目
    def StopProject(self, get):
        pj_name = get if isinstance(get, str) else getattr(get, "pjname", "")
        conf = self.get_conf_by_name(pj_name.strip())
        if not conf:
            return public.returnMsg(False, "没有该项目")
        psh = self.get_pj_sh(conf)
        running = int(public.ExecShell(psh.check)[0].strip("\n")) != 0
        if int(getattr(get, "is_supervisor", 0)) == 1 and running:
            if self.__stop_supervisor(conf) and self._start_project(conf, with_out_supervisor=True):
                return public.returnMsg(True, "停止守护进程成功")
            else:
                return public.returnMsg(False, "停止守护进程失败")
        if self._stop_project(conf):
            return public.returnMsg(True, "停止成功")
        else:
            return public.returnMsg(False, "停止失败")

    # 命令启动
    def auto_start(self):
        for i in self._conf:
            _psh = self.get_pj_sh(i, change_project=True)
            if i["auto_start"] == "1":
                argv = i["pjname"]
                self.StartProject(argv)

    # 编辑开机启动
    def edit_auto_start(self, get):
        self.set_auto_start()
        auto_start = getattr(get, "auto_start", None)
        if auto_start is None:
            return public.returnMsg(False, "参数错误")
        conf = self.get_conf_by_name(get.pjname.strip())
        if not conf:
            return public.returnMsg(False, "没有该项目")

        conf["auto_start"] = auto_start
        self.save_conf()
        if auto_start == "1":
            public.ExecShell('systemctl enable {}_pymanager'.format(conf["pjname"]))
        else:
            public.ExecShell('systemctl disable {}_pymanager'.format(conf["pjname"]))
        return public.returnMsg(True, "设置成功")

    # 设置开机启动
    @staticmethod
    def set_auto_start() -> None:
        rc_local = public.readFile("/etc/rc.local")
        public.ExecShell('chmod +x /etc/rc.d/rc.local')
        if not re.search(r"pythonmamager_main\.py", rc_local):
            body = "/usr/bin/python /www/server/panel/plugin/pythonmamager/pythonmamager_main.py"
            public.writeFile("/etc/rc.local", body, "a+")

    # 设置自启动
    @staticmethod
    def _set_sys_auto_start(pj_name, auto_start) -> None:
        if auto_start == "1":
            public.ExecShell('systemctl enable {}_pymanager'.format(pj_name))

    # 删除系统服务中的内容
    @staticmethod
    def _del_sh(name) -> None:
        filename = "/etc/init.d/{}_pymanager".format(name)
        if os.path.exists(filename):
            os.remove(filename)
        filename = "/lib/systemd/system/{}_pymanager".format(name)
        if os.path.exists(filename):
            public.ExecShell('systemctl disable {}_pymanager'.format(name))
            os.remove(filename)
            public.ExecShell('systemctl daemon-reload')

    def StartSupervisor(self, get):
        """
        @name 启动supervisor守护进程
        @auther baozi
        """
        if not self.supervisor_type:
            return public.returnMsg(False, self.supervisor_msg)
        pj_name = get.pjname.strip()
        conf = self.get_conf_by_name(pj_name.strip())
        if not conf:
            return public.returnMsg(False, "没有该项目")

        get.is_supervisor = 1
        conf["numprocs"] = get.numprocs
        return self.StartProject(get)

    def StopSupervisor(self, get):
        """
        @name 停止守护进程
        @auther baozi
        """
        if not self.supervisor_type:
            return public.returnMsg(False, self.supervisor_msg)
        pj_name = get.pjname.strip()
        conf = self.get_conf_by_name(pj_name.strip())
        if not conf:
            return public.returnMsg(False, "没有该项目")
        psh = self.get_pj_sh(conf)
        running = int(public.ExecShell(psh.check)[0].strip("\n")) != 0
        spr_status = bool(conf["supervisor_name"]) and self._supervisor_exists(conf["supervisor_name"])
        if not spr_status:
            return public.returnMsg(True, "停止成功")
        if running:
            self._stop_project(conf)
        self.__remove_supervisor(conf)
        conf["supervisor_name"] = ""
        conf["is_supervisor"] = 0
        if running:
            self._start_project(conf)
        self.save_conf()
        return public.returnMsg(True, "停止成功")

    # 站点映射
    def ProxyProject(self, get):
        domain = get.domain.strip()
        pj_name = get.pjname.strip()
        conf = self.get_conf_by_name(pj_name.strip())
        if not conf:
            return public.returnMsg(False, "没有该项目")

        port = conf["port"]
        if not port:
            return public.returnMsg(False, "该项目没有端口无法映射，uwsgi模式现阶段不支持sock文件模式映射")

        import panelSite

        sql = public.M('sites')
        if sql.where("name=?", (domain,)).count(): return public.returnMsg(False, 'SITE_ADD_ERR_EXISTS');
        ret = {"domain": domain, "domainlist": [], "count": 0}
        get.webname = json.dumps(ret)
        get.port = "80"
        get.ftp = 'false'
        get.sql = 'false'
        get.version = '00'
        get.ps = 'Python项目[' + pj_name + ']的映射站点'
        get.path = public.M('config').where("id=?", ('1',)).getField('sites_path') + '/' + domain
        result = self.create_site(get)
        if 'status' in result:
            return result
        s = panelSite.panelSite()
        get.sitename = domain
        x = pj_name if len(pj_name) < 13 else pj_name[:10] + "..."
        get.proxyname = "to%s" % x
        get.proxysite = 'http://127.0.0.1:%s' % port
        get.todomain = "$host"
        get.proxydir = '/'
        get.type = 1
        get.cache = 0
        get.cachetime = 1
        get.advanced = 0
        get.subfilter = "[{\"sub1\":\"\",\"sub2\":\"\"},{\"sub1\":\"\",\"sub2\":\"\"},{\"sub1\":\"\",\"sub2\":\"\"}]"
        result = s.CreateProxy(get)
        if result['status']:
            conf["proxy"] = domain
            self.save_conf()
            return public.returnMsg(True, '添加成功!')
        else:
            return public.returnMsg(False, '添加失败!')

    # 创建站点
    def create_site(self, get):
        import panelSite
        s = panelSite.panelSite()
        result = s.AddSite(get)
        if 'status' in result:
            return result
        result['id'] = public.M('sites').where('name=?', (get.domain,)).getField('id')
        self.set_ssl_check(get.domain)
        return result

    # 设置SSL验证目录过滤
    def set_ssl_check(self, siteName):
        rewriteConf = '''#一键申请SSL证书验证目录相关设置
        location ~ \.well-known{
            allow all;
        }'''
        public.writeFile('vhost/rewrite/' + siteName + '.conf', rewriteConf)

    # 删除映射
    def RemoveProxy(self, get):
        pj_name = get.pjname.strip()
        conf = self.get_conf_by_name(pj_name.strip())
        if not conf:
            return public.returnMsg(False, "没有该项目")

        import panelSite

        get.id = public.M('sites').where('name=?', (conf["proxy"],)).getField("id")
        get.webname = conf["proxy"]
        get.path = 1
        get.domain = conf["proxy"]
        panelSite.panelSite().DeleteSite(get)
        conf["proxy"] = ""
        self.save_conf()
        return public.returnMsg(True, '取消成功!')

    # 删除项目
    def RemoveProject(self, get):
        pj_name = get.pjname.strip()
        conf = self.get_conf_by_name(pj_name.strip())
        if not conf:
            return public.returnMsg(False, "没有该项目")
        is_stop = self._stop_project(conf)
        self.__remove_python_cron(conf)
        logfile = self.logpath + "/%s.log" % conf["pjname"]
        if bool(conf["supervisor_name"]) and self._supervisor_exists(conf["supervisor_name"]):
            self.__remove_supervisor(conf)
        if not is_stop:
            return public.returnMsg(False, "请将项目停止后再删除")
        public.ExecShell("rm -rf %s" % conf["vpath"])
        public.ExecShell("rm -f %s" % logfile)
        public.ExecShell("rm -f %s/uwsgi.ini" % conf["path"])
        public.ExecShell("rm -f %s/gunicorn_conf.py" % conf["path"])
        public.ExecShell('systemctl disable {}_pymanager'.format(conf["pjname"]))
        public.ExecShell('rm -f /etc/init.d/{}_pymanager'.format(conf["pjname"]))
        public.ExecShell('rm -f /lib/systemd/system/{}_pymanager'.format(conf["pjname"]))
        self.del_conf(conf)
        return public.returnMsg(True, "删除成功")

    # 获取项目日志
    def GetProjectLog(self, get):
        pj_name = get.pjname.strip()
        conf = self.get_conf_by_name(pj_name.strip())
        if not conf:
            return public.returnMsg(False, "没有该项目")

        logpath = "%s/logs/error.log" % (conf["path"])
        if 'log_path' in conf:
            logpath = conf['log_path'] + '/error.log'
        supervisor_status = bool(conf["supervisor_name"]) and self._supervisor_exists(conf["supervisor_name"])
        if os.path.exists(logpath):
            result = public.ExecShell("tail -n 300 %s" % logpath)[0]
            return result
        elif supervisor_status and self.supervisor_type:
            result = supervisor_main().GetProjectLog(get)
            if result != '该进程没有日志':
                return result
        return "该项目没有日志"

    # python安装
    def InstallPythonV(self, get):
        return self.new_python_install(get)
        # download_url = "http://download.bt.cn"
        # v = get.version
        # v = v.split()[0]
        # exist_pv = self.GetPythonV(get)
        # if v in exist_pv:
        #     return public.returnMsg(False, "该Python版本已经安装 %s " % v)
        # cache_path = "{}/cache/".format(self.pyenv_path)
        # if not os.path.exists(cache_path):
        #     public.ExecShell("mkdir -p %s" % cache_path)
        # fname = "Python-%s.tar.xz" % v
        # pycache = cache_path + fname
        # if not os.path.exists(pycache):
        #     public.ExecShell("/usr/bin/wget -P %s http://download.bt.cn/src/Python-%s.tar.xz -t 2 -T 5" % (cache_path, v))
        # public.ExecShell("%s/bin/pyenv install %s" % (self.pyenv_path,v))
        # exist_pv = self.GetPythonV(get)
        # if v in exist_pv:
        #     public.ExecShell("rm -rf /tmp/python-build.*")
        #     return public.returnMsg(True, "安装完成")
        # else:
        #     return public.returnMsg(False, "安装失败")

    # python卸载
    def RemovePythonV(self, get):
        sysv = platform.python_version()
        v = get.version
        v = v.split()[0]
        # if v == sysv:
        #     return public.returnMsg(False, "该版本为系统默认python，无法卸载")
        for i in self._conf:
            if i["version"] == v:
                return public.returnMsg(False, "该版本有项目正在使用，请先删除项目后再卸载")
        exist_pv = self.GetPythonV(get)
        if v not in exist_pv:
            return public.returnMsg(False, "没有安装该Python版本")
        self.remove_python(v)
        exist_pv = self.GetPythonV(get)
        if v in exist_pv:
            return public.returnMsg(False, "卸载Python失败，请再试一次")
        return public.returnMsg(True, "卸载Python成功")

    # 删除管理的python版本
    @staticmethod
    def remove_python(pyv):
        py = '/www/server/python_manager/versions/{}'.format(pyv)
        if os.path.exists(py):
            import shutil
            shutil.rmtree(py)

    # 显示已经安装的python
    # def GetPythonV(self, get):
    #     versions = []
    #     sysv = platform.python_version()
    #     data = public.ExecShell("%s/bin/pyenv versions" % self.pyenv_path)[0].split("\n")
    #     n = 0
    #     for v in data:
    #         if n == 0:
    #             n += 1
    #             continue
    #         if v == '':
    #             continue
    #         versions.append(v.strip())
    #
    #     versions.append(sysv)
    #     versions.sort()
    #     versions.reverse()
    #     return versions

    # 显示可以安装的python版本
    # def GetCloudPython(self, get):
    #     data = public.ExecShell("{}/bin/pyenv install --list".format(self.pyenv_path))[0].split("\n")
    #     bt_node_version = ['3.8','3.7.4','3.7.3','3.7.2','3.6.8']
    #     v = []
    #     l = {}
    #     for i in data:
    #         i = i.strip()
    #         if re.match("[\d\.]+", i):
    #             v.append(i)
    #     existpy = self.GetPythonV(get)
    #     for i in v:
    #         if i in bt_node_version:
    #             i = i + " 国内节点"
    #         if i.split()[0] in existpy:
    #             l[i] = "1"
    #         else:
    #             l[i] = "0"
    #
    #     l = sorted(l.items(), key=lambda d: d[0], reverse=True)
    #     return l

    # 显示可以安装的python版本
    def GetCloudPython(self, get):
        data = self.get_cloud_version()
        v = []
        l = {}
        for i in data:
            i = i.strip()
            if re.match("[\d\.]+", i):
                v.append(i)
        existpy = self.GetPythonV(get)
        for i in v:
            if i.split()[0] in existpy:
                l[i] = "1"
            else:
                l[i] = "0"

        l = sorted(l.items(), key=lambda d: d[0], reverse=True)
        return l

    # 获取已经安装的模块
    def GetPackages(self, get):
        pip_list = {}
        conf = self.get_conf_by_name(get.pjname.strip())
        if not conf:
            return pip_list
        _list = public.ExecShell("%s list" % self._get_v_pip(conf["vpath"]))[0].split("\n")
        for d in _list[2:]:
            try:
                p, v = d.split()
                pip_list[p] = v
            except:
                pass
        return pip_list

    # 安装卸载虚拟环境模块
    def MamgerPackage(self, get):
        conf = self.get_conf_by_name(get.pjname.strip())
        if not conf:
            return public.returnMsg(False, "没有该虚拟环境")
        pkg = get.p.strip()
        if "v" in get:
            pkg_v = get.v.strip()
            if bool(pkg_v):
                pkg += "==" + pkg_v
        if get.act == "install":
            shell = "%s install -i %s %s"
            public.ExecShell(shell % (self._get_v_pip(conf["vpath"]), self.pipsource, pkg))
            packages = public.ExecShell("%s list" % self._get_v_pip(conf["vpath"]))[0].lower()
            _pkg = pkg.lower()
            if '_' in _pkg:
                _pkg = _pkg.replace("_", "-")
            if _pkg in packages:
                return public.returnMsg(True, "安装成功")
            else:
                return public.returnMsg(False, "安装失败")
        else:
            if pkg.startswith("pip"):
                return public.returnMsg(False, "PIP不能卸载。。。。")
            shell = "echo 'y' | %s uninstall %s"
            public.ExecShell(shell % (self._get_v_pip(conf["vpath"]), pkg))
            packages = public.ExecShell("%s list" % self._get_v_pip(conf["vpath"]))[0]
            if pkg.lower() not in packages.lower():
                return public.returnMsg(True, "卸载成功")
            else:
                return public.returnMsg(False, "卸载失败")

    # 写日志
    def _write_log(self, msg):
        path = "%s/py.log" % self.basedir
        localtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        if not os.path.exists(path):
            public.writeFile(path, localtime + "\n" + msg + "\n", "w+")
        public.writeFile(path, localtime + "\n" + msg + "\n", "a+")

    # 获取云端python版本
    def get_cloud_version(self, get=None):
        import requests
        res = requests.get('http://dg1.bt.cn/install/plugin/pythonmamager/pyv.txt')
        text = res.text.split('\n')
        public.writeFile('{}/pyv.txt'.format(self.basedir), json.dumps(text))
        return text

    # 获取那些版本的python能安装
    def get_pyv_can_install(self):
        pyv = public.readFile('{}/pyv.txt'.format(self.basedir))
        if not pyv:
            return self.get_cloud_version()
        try:
            return json.loads(pyv)
        except:
            return self.get_cloud_version()

    # 获取已经安装的python版本
    def GetPythonV(self, get):
        path = '/www/server/python_manager/versions'
        if not os.path.exists(path):
            return []
        data = os.listdir(path)
        return data

    # 首次安装python
    def new_python_install(self, get):
        """
        get.version  2.7.18
        :param get:
        :return:
        """
        can_install = self.get_pyv_can_install()
        if get.version not in can_install:
            return public.returnMsg(False, '该版本尚未支持，请到论坛反馈。')
        public.ExecShell(
            'bash {plugin_path}/install_python.sh {pyv} &> {log}'.format(plugin_path=self.basedir, pyv=get.version,
                                                                         log="%s/py.log" % self.basedir))
        path = '/www/server/python_manager/versions/{}/bin/'.format(get.version)
        if "2.7" in get.version:
            path = path + "python"
        else:
            path = path + "python3"
        if os.path.exists(path):
            public.writeFile("%s/py.log" % self.basedir, '')
            return public.returnMsg(True, "安装成功！")
        return public.returnMsg(False, "安装失败！{}".format(path))

    def install_pip(self, vpath, pyv):
        if [int(i) for i in pyv.split('.')] > [3, 6]:
            pyv = "3.6"
        public.ExecShell('bash {plugin_path}/install_python.sh {pyv} {vpath} &>> {log}'.format(
            plugin_path=self.basedir,
            pyv=pyv,
            log="%s/py.log" % self.basedir,
            vpath=vpath))

    # 复制python环境到项目内
    def copy_pyv(self, get):
        import files
        get.sfile = "/www/server/python_manager/versions/{}".format(get.version)
        get.dfile = get.vpath
        self._write_log(str(files.files().CopyFile(get)))
        import pwd
        res = pwd.getpwnam('www')
        uid = res.pw_uid
        gid = res.pw_gid
        os.chown(get.dfile, uid, gid)
        self.install_pip(get.vpath, get.version)

    def find_file(self, path, file, l):
        if os.path.isfile(path):
            if file in path:
                l.append(path)
        else:
            for i in os.listdir(path):
                self.find_file(os.path.join(path, i), file, l)
        return l

    # 获取django项目的启动目录
    def get_django_wsgi_path(self, get):
        l = []
        res = self.find_file(get.path, "wsgi.py", l)
        if not res:
            return False
        return "/".join(res[0].split('/')[:-1])

    # 获取manager文件路径
    def get_manager_path(self, get):
        l = []
        res = self.find_file(get.path, "manage.py", l)
        if not res:
            return False
        return "/".join(res[0].split('/')[:-1]) + "/manage.py"

    # 获取日志
    def get_logs(self, get):
        import files
        return files.files().GetLastLine("%s/py.log" % self.basedir, 20)


if __name__ == '__main__':
    p = pythonmamager_main()
    p.auto_start()
