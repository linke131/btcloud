#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: zhwen <zhw@bt.cn>
# +-------------------------------------------------------------------

# +--------------------------------------------------------------------
# |   pythone管理器
# +--------------------------------------------------------------------
import os, sys

os.chdir("/www/server/panel")
sys.path.append("class/")
import public, time, json, re, platform
from http.client import HTTPConnection
from xmlrpc import client
import socket


class UnixStreamHTTPConnection(HTTPConnection):
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.host)


class UnixStreamTransport(client.Transport, object):
    def __init__(self, socket_path):
        self.socket_path = socket_path
        super(UnixStreamTransport, self).__init__()

    def make_connection(self, host):
        return UnixStreamHTTPConnection(self.socket_path)


class pythonmamager_main:
    basedir = "/www/server/panel/plugin/pythonmamager"
    __conf = "%s/config.json" % basedir
    logpath = "%s/logs" % basedir
    pipsource = "https://mirrors.aliyun.com/pypi/simple/"
    access_defs = ['auto_start']
    __sh = ''
    proxy_client = None
    supervisord_path = ''
    supervisorctl_path = ''
    supervisor_error = ''

    def __init__(self):
        self.pyenv_path = "/root/.pyenv"
        if not os.path.exists(self.pyenv_path):
            self.pyenv_path = "/.pyenv"
        if not self.proxy_client and self.__check_supervisor_install():
            self.proxy_client = client.ServerProxy('http://localhost',
                                                   transport=UnixStreamTransport("/var/run/supervisor.sock"))

    def __check_supervisor_install(self):
        if os.path.exists('/www/server/panel/pyenv'):
            self.supervisord_path = '/www/server/panel/pyenv/bin/supervisord'
            self.supervisorctl_path = '/www/server/panel/pyenv/bin/supervisorctl'
            supervisorctl_main = '/www/server/panel/plugin/supervisor/supervisor_main.py'
            supervisorctl_html = '/www/server/panel/plugin/supervisor/index.html'
            self.supervisor_error = '进程守护管理插件未安装或相关依赖未成功安装，请按以下方式排查：<br/>1、进程守护管理器插件是否安装<br/>2、{}文件是否存在<br/>3、{}文件是否存在'.format(
                self.supervisord_path, self.supervisorctl_path)
            if os.path.isfile(supervisorctl_main) and os.path.isfile(supervisorctl_html) and os.path.isfile(
                    self.supervisord_path) and os.path.isfile(self.supervisorctl_path):
                return True
        return False

    # 检查端口
    def __check_port(self, port):
        try:
            if int(port) < 65535 and int(port) > 0:
                data = public.ExecShell("ss  -nultp|grep ':%s '" % port)[0]
                if data:
                    return public.returnMsg(False, "该端口已经被占用")
            else:
                return public.returnMsg(False, "请输入正确的端口范围 1 < 端口 < 65535")
        except:
            return public.returnMsg(False, "端口请输入整数")

    # 检查输入参数
    def __check_args(self, get):
        values = {}
        # frameworks = ["python", "django", "flask", "sanic"]
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
            if values["path"][-1] == '/': values["path"] = values["path"][:-1]
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
            values["logpath"] = get.logpath.strip()
        values["numprocs"] = 0
        values["is_supervisor"] = 0
        if hasattr(get, 'numprocs'):
            values["numprocs"] = get.numprocs.strip()
        if hasattr(get, 'is_supervisor'):
            values["is_supervisor"] = get.is_supervisor.strip()
        return values

    def __get_project_info(self, pjname, pkey):
        """
        @name 取项目指定字段配置信息
        @auther hezhihong
        return 
        """
        conf = self.__read_config(self.__conf)
        result = {}
        result['status'] = False
        result['msg'] = ''
        for i in conf:
            if pjname == i["pjname"]:
                try:
                    result['msg'] = i[pkey]
                    result['status'] = True
                except:
                    pass
        return result

    # 检查项目是否存在
    def __check_project_exist(self, pjname):
        conf = self.__read_config(self.__conf)
        for i in conf:
            if pjname == i["pjname"]:
                return public.returnMsg(False, "项目已经存在")

    def get_vpath_pip(self, vpath):
        if os.path.exists('{}/bin/pip'.format(vpath)):
            return '{}/bin/pip'.format(vpath)
        else:
            return '{}/bin/pip3'.format(vpath)

    def get_vpath_python(self, vpath):
        if os.path.exists('{}/bin/python'.format(vpath)):
            return '{}/bin/python'.format(vpath)
        else:
            return '{}/bin/python3'.format(vpath)

    # 安装模块
    def __install_module(self, install_module, path, vpath):
        requirementsconf = {}
        requirements = "%s/requirements.txt" % path
        if install_module == "1":
            if not os.path.exists(requirements):
                return public.returnMsg(False, "运行目录没有找到依赖文件requirements.txt，请添加后再创建")
            requirementsconf = public.readFile(requirements).splitlines()
            for i in requirementsconf:
                # a = public.ExecShell("source %s/bin/activate && pip install -i %s %s" % (vpath, self.pipsource, i))
                a = public.ExecShell("{} install -i {} {}".format(self.get_vpath_pip(vpath), self.pipsource, i))
                self.WriteLog(a[0])
            return requirementsconf
        else:
            return requirementsconf

    # 读取requirements内容
    def __read_requirements(self, path):
        requirements = "%s/requirements.txt" % path
        if os.path.exists(requirements):
            requirements_data = public.readFile(requirements)
            return requirements_data

    # 构造启动参数
    def __structure_start_args(self, values):
        rfile = values['rfile']
        framework = values['framework']
        rproject = rfile.split("/")[-1].split(".")[0]
        if rproject == "":
            rproject = rfile.split("/")[-2].split(".")[0]
        run = "%s:app" % rproject
        if framework == "django":
            run = "%s.wsgi:application" % rproject
        if framework == "sanic":
            worker = "worker_class = 'sanic.worker.GunicornWorker'"
        else:
            worker = "worker_class = 'sync'"
        return {"run": run, "worker": worker, "framework": framework, "rproject": rproject}

    # 自定义启动
    def __start_with_customize(self, values):
        run_user = ""
        if 'user' in values and values['user'] == 'www':
            run_user = "sudo -u {}".format(values['user'])
        sh = " nohup {} {} {} &".format(run_user, self.get_vpath_python(values['vpath']), values['rfile'])
        check_sh = "{} {}".format(values['vpath'], values['rfile'])
        self._create_sh(values['pjname'], sh, check_sh)
        public.ExecShell('systemctl restart {}_pymanager'.format(['pjname']))

    def get_start_sh(self, values):
        """
        @name 取启动脚本
        @auther hezhihong
        """
        sh = ''
        check_sh = ""
        if values['rtype'] == 'python':
            sh = "{vpath} -u {run_file} {parm} >> {log} 2>&1 &".format(
                vpath=self.get_vpath_python(values['vpath']),
                run_file=values['rfile'],
                log=values['log_path'] + "/error.log".replace("//", "/"),
                parm=values['parm']
            )
            check_sh = " {} ".format(self.get_vpath_python(values['vpath']))
        elif values['rtype'] == 'uwsgi':
            sh = "nohup %s/bin/uwsgi --ini %s/uwsgi.ini -w %s &" % (values['vpath'], values['path'], values['run'])
            check_sh = "%s/bin/uwsgi --ini %s/uwsgi.ini" % (values['vpath'], values['path'])
        elif values['rtype'] == 'gunicorn':
            logfile = values['path'] + "/logs/error.log"
            sh = "nohup %s/bin/gunicorn -c %s/gunicorn_conf.py %s &>> %s &" % (values['vpath'], values['path'], values['run'], logfile)
            check_sh = "%s/bin/uwsgi --ini %s/uwsgi.ini" % (values['vpath'], values['path'])
        else:
            return sh, check_sh
        sh = sh.replace('//', '/')
        self.__sh = sh
        return sh, check_sh

    # 使用python启动
    def __start_with_python(self, values):
        if not os.path.exists(values['log_path']):
            public.ExecShell("mkdir -p %s" % values['log_path'])
        sh, check_sh = self.get_start_sh(values)
        self.WriteLog(sh)
        self._create_sh(values['pjname'], sh, check_sh)
        # public.ExecShell(sh)
        public.ExecShell('systemctl restart {}_pymanager'.format(values['pjname']))
        time.sleep(1)

    # 使用uwsgi启动
    def __start_with_wsgi(self, values):
        path = values['path']
        vpath = values['vpath']
        pjname = values['pjname']
        user = values['user'] if 'user' in values else 'root'
        port = values['port']
        rfile = values['rfile']
        run = values['run']
        framework = values['framework']
        if path[-1] == "/":
            path = path[:-1]
        if framework == "sanic":
            return public.returnMsg(False, "sanic框架项目请使用gunicorn或pyhton启动")
        a = public.ExecShell("{} install -i {} uwsgi".format(
            self.get_vpath_pip(vpath), self.pipsource))
        self.WriteLog(a[0])
        # 添加uwcgi配置
        uconf = """[uwsgi]
master = true
processes = 1
threads = 2
chdir = {path}
wsgi-file= {rfile}
http = 0.0.0.0:{port}
logto = {path}/logs/error.log
chmod-socket = 660
vacuum = true
uid={user}
gid={user}
max-requests = 1000""".format(path=path, port=port, rfile=rfile, user=user)
        uwsgi_file = "%s/uwsgi.ini" % path
        if not os.path.exists(uwsgi_file):
            public.writeFile(uwsgi_file, uconf)
        public.ExecShell("mkdir %s/logs" % path)
        sh, check_sh = self.get_start_sh(values)
        self._create_sh(pjname, sh, check_sh)
        # public.ExecShell(sh)
        public.ExecShell('systemctl restart {}_pymanager'.format(pjname))
        time.sleep(1)

    # 使用gunicorn启动
    def __start_with_gunicorn(self, values):
        path = values['path']
        vpath = values['vpath']
        pjname = values['pjname']
        user = values['user'] if 'user' in values else 'root'
        worker = values['worker']
        port = values['port']
        run = values['run']
        a = public.ExecShell(
            "{} install -i {} gunicorn gevent-websocket".format(
                self.get_vpath_pip(vpath), self.pipsource))
        self.WriteLog(a[0])
        # 添加gunicorn配置
        logformat = '%(t)s %(p)s %(h)s "%(r)s" %(s)s %(L)s %(b)s %(f)s" "%(a)s"'
        gconf = """bind = '0.0.0.0:{port}'
user = '{user}'
workers = 1
threads = 2
backlog = 512
chdir = '{chdir}'
access_log_format = '{log}'
loglevel = 'info'
{worker}
errorlog = chdir + '/logs/error.log'
accesslog = chdir + '/logs/access.log'
pidfile = chdir + '/logs/{pjname}.pid'""".format(
            port=port, chdir=path, log=logformat, worker=worker, pjname=pjname, user=user)
        gunicorn_file = "%s/gunicorn_conf.py" % path
        if not os.path.exists(gunicorn_file):
            public.writeFile(gunicorn_file, gconf)
        public.ExecShell("mkdir %s/logs" % path)
        sh, check_sh = self.get_start_sh(values)
        public.writeFile("/tmp/tmp.aa", sh)
        self._create_sh(pjname, sh, check_sh)
        # public.ExecShell(sh)
        public.ExecShell('systemctl restart {}_pymanager'.format(pjname))
        time.sleep(1)
        pid = public.ExecShell("ps aux|grep '%s'|grep -v 'grep'|wc -l" % vpath)[0].strip("\n")

        if pid == "0":
            public.ExecShell('/etc/init.d/{}_pymanager'.format(pjname))

    # 选择启动方式
    def __select_framework(self, values):
        rtype = values['rtype']
        rtypes = ["python", "gunicorn", "uwsgi"]
        if rtype not in rtypes:
            self.__start_with_customize(values)
            return
        start_args = self.__structure_start_args(values)
        values['run'] = start_args["run"]
        values['worker'] = start_args["worker"]
        # framework = start_args["framework"]
        # rproject = start_args["rproject"]
        if rtype == "python":
            self.__start_with_python(values)

        if rtype == "uwsgi":
            self.__start_with_wsgi(values)

        if rtype == "gunicorn":
            self.__start_with_gunicorn(values)

    # 检查项目状态并写入配置
    def __check_project_status(self, data, path):
        pid = public.ExecShell("ps aux|grep '%s'|grep -v 'grep'|wc -l" % path)[0].strip("\n")
        conf = self.__read_config(self.__conf)
        if pid != "0":
            data["status"] = "1"
            conf.append(data)
            self.__write_config(self.__conf, conf)
            return public.returnMsg(True, "创建成功")
        else:
            data["status"] = "0"
            conf.append(data)
            self.__write_config(self.__conf, conf)
            return public.returnMsg(False, "创建失败")

    def get_superviosr_process(self):
        calls = [
            {"methodName": "supervisor.getAllProcessInfo"},
            {"methodName": "supervisor.getAllConfigInfo"}
        ]
        src_conf = public.readFile('/www/server/panel/plugin/supervisor/config.json')
        try:
            src_conf = json.loads(src_conf)
        except:
            pass
        process_infos = config_infos = []
        try:
            process_infos, config_infos = self.proxy_client.system.multicall(calls)
        except:
            pass
        if not process_infos or not config_infos: return []
        if type(process_infos) == dict:
            print(process_infos)
            return
        if type(config_infos) == dict:
            print(config_infos)
            return

        new_info = []
        add_str = []
        for i in range(0, len(process_infos)):
            pinfo = process_infos[i]
            cinfo = config_infos[i]
            d = {}
            # pinfo.update(cinfo)
            d["program"] = pinfo["name"].split("_")[0]
            statename = pinfo["statename"]
            d["runStatus"] = statename
            if statename == "RUNNING":
                d["status"] = "1"
                d["pid"] = pinfo["pid"]
            else:
                d["status"] = 0
                d["pid"] = ""

            d["command"] = cinfo["command"]
            d["user"] = cinfo["user"] if "user" else "root"
            d["priority"] = cinfo["process_prio"]
            d["numprocs"] = cinfo["numprocs"]
            for src in src_conf:
                if d["program"] == src["program"] and "is_python" in src:
                    if d["program"] not in add_str: new_info.append(d)
                    add_str.append(d["program"])
        return new_info

    def __remove_python_cron(self, pjname):
        """
        @name 删除项目定时清理任务
        @auther hezhihong<2022-10-31>
        @return 
        """
        cron_name = '[勿删]python项目管理器日志切割任务[{}]'.format(pjname)
        cron_path = public.GetConfigValue('setup_path') + '/cron/'
        cron_list = public.M('crontab').where("name=?", (cron_name,)).select()
        if cron_list:
            for i in cron_list:
                if not i: continue
                cron_echo = public.M('crontab').where("id=?", (i['id'],)).getField('echo')
                args = {"id": i['id']}
                import crontab
                crontab.crontab().DelCrontab(args)
                del_cron_file = cron_path + cron_echo
                public.ExecShell("crontab -u root -l| grep -v '{}'|crontab -u root -".format(del_cron_file))

    def exec_crontab(self, name):
        """
        @name 执行定时任务
        @auther hezhihong<2022-10-31>
        @return 
        """
        from datetime import date, timedelta
        conf = json.loads(public.readFile(self.__conf))
        yesterday = (date.today() + timedelta(days=-1)).strftime("%Y-%m-%d")
        try:
            for i in conf:
                if i['pjname'] == name:
                    public.ExecShell(
                        'cd {} && tar -zcvf {}_{}.tar.gz access.log error.log'.format(
                            i['log_path'], i['pjname'],yesterday))
                    print('执行成功')
                    return True
        except:
            pass
        print('执行失败')
        return False

    def add_crontab(self, data):
        """
        @name 构造日志切割任务
        """
        # conf = json.loads(public.readFile(self.__conf))
        # data = conf[0]
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
                python_path,data['pjname'],data['pjname']),
            "urladdress": ''
        }
        import crontab
        res = crontab.crontab().AddCrontab(args)
        if res and "id" in res.keys():
            return True
        return False

    def get_supervisor_name(self, pjname):
        """
        @name 获取supervisor项目名
        @auther hezhihong
        @return supervisor_name
        """
        while True:
            supervisor_name = pjname + "-python-" + public.GetRandomString(5)
            if not self.supervisor_exists(supervisor_name):
                break
        return supervisor_name

    # 创建python项目
    def CreateProject(self, get):
        # self.set_auto_start()
        values = self.__check_args(get)
        if 'is_supervisor' in values and values['is_supervisor'] in ['1', 1]:
            if values["user"] != 'root':
                return public.returnMsg(False, "非root用户可能导致添加进程守护失败，请选择root用户")
            if not self.__check_supervisor_install():
                return public.returnMsg(False, self.supervisor_error)

        if "status" in values:
            return values
        result = self.__check_project_exist(values["pjname"])
        if result:
            return result
        vpath = values["path"] + "/" + public.md5(values["pjname"]) + "_venv"
        vpath = vpath.replace("//", "/")
        get.vpath = vpath
        if not os.path.exists(vpath):
            self.WriteLog("开始复制环境 {}".format(vpath))
            self.copy_pyv(get)
        requirements = self.__install_module(values["install_module"], values["path"], vpath)
        if "status" in requirements:
            return requirements
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
            "log_path": os.path.join(values["path"], 'logs') if "logpath" not in values else values["logpath"],
            "is_supervisor": values["is_supervisor"],
            "numprocs": values["numprocs"],
            "supervisor_name": ''
        }
        # public.ExecShell("chown -R www.www {}".format(values["path"]))
        self.__select_framework(data)
        self._set_sys_auto_start(values["pjname"], values['auto_start'])
        self.add_crontab(data)
        # conf = self.__read_config(self.__conf)
        # conf.append(data)
        # self.__write_config(self.__conf, conf)
        if 'is_supervisor' in values and values['is_supervisor'] in ['1', 1] and self.__check_supervisor_install():
            if self.__sh:
                data["command"] = self.__sh
            data["supervisor_name"] = self.get_supervisor_name(values["pjname"])
            if not self.__set_supervisor(data):
                return public.returnMsg(True, "进程守护管理插件添加项目失败,请检查该运行目录不存在或该进程名是否被使用!")
            if self.proxy_client:
                s_path = data["path"] if data['rtype'] != 'python' else data["vpath"]
                pids = public.ExecShell("ps aux|grep '%s'|awk '{print $2}'" % s_path)[0].split("\n")
                for pid in pids:
                    public.ExecShell("sync && kill -9 %s" % pid)
                self.__start_supervisor(data["supervisor_name"])
                time.sleep(1)
            # if supervisor_list:
            #     for i in supervisor_list:
            #         if i['program'] == supervisor_name and i['status'] == '0':
            #             self.__start_supervisor(supervisor_name)

        return self.__check_project_status(data, values["path"])

    # 获取项目详细信息
    def GetLoad(self, pjname):
        conf = self.__read_config(self.__conf)
        cpunum = int(public.ExecShell('cat /proc/cpuinfo |grep "processor"|wc -l')[0])
        for i in conf:
            if i["pjname"] == pjname:
                try:
                    cpu = round(float(
                        public.ExecShell("ps aux|grep '%s'|awk '{cpusum += $3};END {print cpusum}'" % i["path"])[
                            0]) / cpunum, 2)
                    mem = round(float(public.ExecShell(
                        "ps aux|grep '%s'|grep -v 'grep'|awk '{memsum+=$6};END {print memsum}'" % i["path"])[0]) / 1024,
                                2)
                    return {"cpu": cpu, "mem": mem}
                except:
                    return {"cpu": 0, "mem": 0}

    # 获取已经安装的模块
    def GetPackages(self, get):
        conf = self.__read_config(self.__conf)
        piplist = {}
        for i in conf:
            if i["pjname"] == get.pjname:
                l = public.ExecShell("%s list" % self.get_vpath_pip(i["vpath"]))[0].split("\n")
                for d in l[2:]:
                    try:
                        p, v = d.split()
                        piplist[p] = v
                    except:
                        pass
                return piplist

    # 取文件配置
    def GetConfFile(self, get):
        conf = self.__read_config(self.__conf)
        pjname = get.pjname.strip()
        import files
        for i in conf:
            if pjname == i["pjname"]:
                if i["rtype"] == "python":
                    return public.returnMsg(False, "Python启动方式没有配置文件可修改")
                elif i["rtype"] == "gunicorn":
                    get.path = i["path"] + "/gunicorn_conf.py"
                else:
                    get.path = i["path"] + "/uwsgi.ini"
                f = files.files()
                return f.GetFileBody(get)

    def __get_conf_port(self, config, py_conf):
        rep_socket = "socket\s*="
        socket = re.search(rep_socket, config)
        if socket:
            py_conf["port"] = ""
        rep_port = ".+:(\d+)"
        try:
            search_result = re.search(rep_port, config)
            new_port = None
            if search_result: new_port = search_result.group(1)
            if new_port:
                result = self.__check_port(new_port)
                if not result or new_port == py_conf["port"]:
                    py_conf["port"] = new_port
                else:
                    return result
        except Exception as e:
            return e

    # 保存文件配置
    def SaveConfFile(self, get):
        conf = self.__read_config(self.__conf)
        import files
        pjname = get.pjname.strip()
        for i in conf:
            if pjname == i["pjname"]:
                result = self.__get_conf_port(get.data, i)
                # return result
                if result:
                    return result
                if i["rtype"] == "python":
                    return public.returnMsg(False, "Python启动方式没有配置文件可修改")
                elif i["rtype"] == "gunicorn":
                    get.path = i["path"] + "/gunicorn_conf.py"
                else:
                    get.path = i["path"] + "/uwsgi.ini"
                f = files.files()
                result = f.SaveFileBody(get)
                if result["status"]:
                    public.writeFile(self.__conf, json.dumps(conf))
                    return public.returnMsg(True, "配置修改成功，请手动重启项目")
                else:
                    return public.returnMsg(False, "保存失败")

    # 安装卸载虚拟环境模块
    def MamgerPackage(self, get):
        conf = self.__read_config(self.__conf)
        for i in conf:
            if i["pjname"] == get.pjname:
                shell = "%s install -i %s %s"
                if get.act == "install":
                    if get.v:
                        v = "%s==%s" % (get.p, get.v)
                        public.ExecShell(shell % (self.get_vpath_pip(i["vpath"]), self.pipsource, v))
                    else:
                        public.ExecShell(shell % (self.get_vpath_pip(i["vpath"]), self.pipsource, get.p))
                    packages = public.ExecShell("%s list" % self.get_vpath_pip(i["vpath"]))[0]
                    if get.p in packages.lower():
                        return public.returnMsg(True, "安装成功")
                    else:
                        return public.returnMsg(False, "安装失败")
                else:
                    if get.p == "pip":
                        return public.returnMsg(False, "PIP不能卸载。。。。")
                    shell = "echo 'y' | %s uninstall %s"
                    public.ExecShell(shell % (self.get_vpath_pip(i["vpath"]), get.p))
                    packages = public.ExecShell("%s list" % self.get_vpath_pip(i["vpath"]))[0]
                    if get.p not in packages.lower():
                        return public.returnMsg(True, "卸载成功")
                    else:
                        return public.returnMsg(False, "卸载失败")

    # 获取项目列表
    def GetPorjectList(self, get):
        """
        @name 获取项目列表
        @author hezhihong
        return 增加supervisor状态（is_supervisor：是否添加到守护进程，supervisor_status：守护进程状态）
        """
        conf = self.__read_config(self.__conf)
        supervisor_list = []
        if self.proxy_client and self.__check_supervisor_install():
            supervisor_list = self.get_superviosr_process()
        if conf:
            # 取项目状态
            for i in conf:
                s_path = i["path"] if i['rtype'] != 'python' else i["vpath"]
                i['is_supervisor'] = '0'
                if 'supervisor_name' not in i or not i['supervisor_name']:
                    i['supervisor_name'] = ''
                    i["supervisor_status"] = 0
                a = public.ExecShell("ps aux|grep '%s'|grep -v 'grep'|wc -l" % s_path)[0].strip("\n")
                if a == "0":
                    i["status"] = "0"
                    i["cpu"] = 0
                    i["mem"] = 0
                else:
                    i["status"] = "1"
                    load = self.GetLoad(i["pjname"])
                    i["cpu"] = load["cpu"]
                    i["mem"] = load["mem"]
                if not supervisor_list: continue
                is_True = False
                for ii in supervisor_list:
                    if i["supervisor_name"] == ii["program"]:
                        is_True = True
                        i['is_supervisor'] = "1"
                        i["supervisor_status"] = ii["status"]
                        break
                if not is_True:
                    i["supervisor_status"] = 0
                    i['is_supervisor'] = "0"
                    i["supervisor_name"] = ''
            self.__write_config(self.__conf, conf)
        return conf

    def __get_supervisor_program_list(self, pjname):
        """
        @name 判断项目是否已经添加到supervisor中
        """
        program_list = []
        try:
            conf = public.readFile('/www/server/panel/plugin/supervisor/config.json')
            conf = json.loads(conf)
            for i in conf:
                program_list.append(i['program'])
        except:
            pass
        if pjname in program_list:
            return True
        return False

    # 获取framework兼容老版本
    def __get_framework(self, path):
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
        conf = self.__read_config(self.__conf)
        if hasattr(get, "pjname"):
            pjname = get.pjname
        else:
            pjname = get
        if conf:
            result = self.__get_project_info(pjname, 'supervisor_name')
            if not os.path.exists(self.logpath):
                public.ExecShell("mkdir -p %s" % self.logpath)
            for i in conf:
                if pjname == i["pjname"]:
                    # if "is_supervisor" in get and  get.is_supervisor in ['1',1]:
                    #         #如守护进程未启动，启动守护进程
                    #         self.__start_supervisor(pjname)
                    if i["status"] == "0":
                        s_path = i["path"] if i['rtype'] != 'python' else i["vpath"]
                        if "framework" not in i:
                            i["framework"] = self.__get_framework(i["path"])
                            self.__write_config(self.__conf, conf)
                        pid = public.ExecShell("ps aux|grep '%s'|grep -v 'grep'|wc -l" % s_path)[0].strip("\n")
                        if pid == "0": self.__select_framework(i)
                        if 'is_supervisor' in get and get.is_supervisor == '1':
                            if result['msg']:
                                self.__start_supervisor(result['msg'])
                            else:
                                self.StartSupervisor(get)
                        pid = public.ExecShell("ps aux|grep '%s'|grep -v 'grep'|wc -l" % s_path)[0].strip("\n")
                        if pid != "0":
                            print("启动成功")
                            if 'is_stop' not in get: return public.returnMsg(True, "启动成功")
                        else:
                            print("项目启动失败,请查看项目日志")
                            if 'is_stop' not in get: return public.returnMsg(False, "项目启动失败,请查看项目日志")
                    else:
                        print("项目已经启动")
                        if 'is_supervisor' in get and get.is_supervisor == '1':
                            if result['msg']:
                                self.__start_supervisor(result['msg'])
                            else:
                                self.StartSupervisor(get)
                        if 'is_stop' not in get: return public.returnMsg(False, "项目已经启动")

    # 命令启动
    def auto_start(self):
        conf = self.__read_config(self.__conf)
        for i in conf:
            if i["auto_start"] == "1":
                argv = i["pjname"]
                self.StartProject(argv)

    # 编辑开机启动
    def edit_auto_start(self, get):
        self.set_auto_start()
        vaules = self.__check_args(get)
        conf = self.__read_config(self.__conf)
        for i in conf:
            if vaules["pjname"] == i["pjname"]:
                i["auto_start"] = vaules["auto_start"]
                self.__write_config(self.__conf, conf)
                if vaules["auto_start"] == "1":
                    public.ExecShell('systemctl enable {}_pymanager'.format(vaules["pjname"]))
                else:
                    public.ExecShell('systemctl disable {}_pymanager'.format(vaules["pjname"]))
                return public.returnMsg(True, "设置成功")

    def set_auto_start(self):
        rc_local = public.readFile("/etc/rc.local")
        public.ExecShell('chmod +x /etc/rc.d/rc.local')
        if not re.search("pythonmamager_main\.py", rc_local):
            body = "/usr/bin/python /www/server/panel/plugin/pythonmamager/pythonmamager_main.py"
            public.writeFile("/etc/rc.local", body, "a+")

    def _set_sys_auto_start(self, pjname, auto_start):
        if auto_start == "1":
            public.ExecShell('systemctl enable {}_pymanager'.format(pjname))

    def _del_sh(self, name):
        filename = "/etc/init.d/{}_pymanager".format(name)
        if os.path.exists(filename):
            os.remove(filename)
        filename = "/lib/systemd/system/{}_pymanager".format(name)
        if os.path.exists(filename):
            public.ExecShell('systemctl disable {}_pymanager'.format(name))
            os.remove(filename)
            public.ExecShell('systemctl daemon-reload')

    def _create_sh(self, name, sh, check_sh):
        string = """#!/bin/bash
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
  pkill -f "{check_sh}"
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
""".format(name=name, sh=sh, check_sh=check_sh)
        filename = "/etc/init.d/{}_pymanager".format(name)
        public.writeFile(filename, string)
        os.chmod(filename, 755)

        service_string = """[Unit]
Description=-------{name}---------
After=network.target
[Service]
Type=forking
ExecStart=/bin/sh -c '{file} start'

ExecReload=/bin/sh -c '{file} restart'

ExecStop=/bin/sh -c '{file} stop'

Restart=on-failure

[Install]
WantedBy=multi-user.target
""".format(name=name, file=filename)
        self.WriteLog(service_string)
        service_file = "/lib/systemd/system/{}_pymanager".format(name)
        public.writeFile(service_file, service_string)
        public.ExecShell('systemctl daemon-reload')

    def __get_supervisor_list(self):
        """
        @name 取守护进程列表
        """
        import supervisor
        args = public.dict_obj()
        return supervisor.supervisor_main().GetProcessList(args)

    def __set_supervisor(self, values):
        """
        @name 设置supervisor守护进程
        @auther hezhihong<2022-10-31>
        @return 
        """
        import supervisor
        args = public.dict_obj()
        args.pjname = values['supervisor_name']
        # args.user=values['user']
        args.user = 'root'
        args.path = values['path'] + '/'.replace('//', '/')
        args.command = values['command']
        if args.command.endswith("&"):
            args.command = args.command[:-1]
        args.numprocs = values['numprocs'] if values['numprocs'] else '1'
        args.is_supervisor = values['is_supervisor']
        return supervisor.supervisor_main().AddProcess(args)

    def StartSupervisor(self, get):
        """
        @name 启动supervisor守护进程
        @auther hezhihong
        """
        if not self.__check_supervisor_install(): return public.returnMsg(False, self.supervisor_error)
        pjname = get.pjname
        self.StopProject(get)
        result = self.__get_project_info(pjname, 'supervisor_name')
        if not (result['msg'] and self.supervisor_exists(result['msg'])):
            supervisor_name = self.get_supervisor_name(pjname)
            if not supervisor_name: return public.returnMsg(False, "进程守护管理插件已存在项目名称,请重试")
            conf = self.__read_config(self.__conf)
            for i in range(len(conf)):
                if pjname == conf[i]["pjname"]:
                    conf[i]["supervisor_name"] = supervisor_name
                    conf[i]['is_supervisor'] = '1'
                    conf[i]['supervisor_status'] = '1'
                    command = self.get_start_sh(conf[i])[0]
                    if command.endswith("&"):
                        command = command[:-1]
                    conf[i]['command'] = command
                    self.__set_supervisor(conf[i])
                    args = public.dict_obj()
                    import supervisor
                    args.program = pjname
                    supervisor.supervisor_main().StartProcess(args)
                    self.__write_config(self.__conf, conf)
                    break

        else:
            self.__start_supervisor(result['msg'])
        return public.returnMsg(True, "启动成功")

    def StopSupervisor(self, get):
        """
        @name 停止守护进程
        """
        conf = self.__read_config(self.__conf)
        get.is_stop = True
        is_run = self.__get_project_info(get.pjname, 'status')
        is_type = self.__get_project_info(get.pjname, 'rtype')
        result = self.__get_project_info(get.pjname, 'supervisor_name')
        if result['msg']: self.__remove_supervisor(result['msg'])
        s_path = ''
        if is_type['msg'] == 'python':
            s_path = self.__get_project_info(get.pjname, 'vpath')
        else:
            s_path = self.__get_project_info(get.pjname, 'path')
        pid = public.ExecShell("ps aux|grep '%s'|grep -v 'grep'|wc -l" % s_path)[0].strip("\n")
        # return is_run['msg'],pid

        for i in conf:
            if i['pjname'] == get.pjname:
                if is_run['msg'] in ['1', 1] and pid == "0": self.__select_framework(i)
                i['supervisor_name'] = ''
                i['is_supervisor'] = '0'
                i['supervisor_status'] = '0'
                self.__write_config(self.__conf, conf)
                break
        time.sleep(1)
        return public.returnMsg(True, "停止成功")

    def __stop_supervisor(self, pjname):
        """
        @name 停止supervisor守护进程
        @auther hezhihong<2022-10-31>
        @return 
        """
        import supervisor
        args = public.dict_obj()
        args.program = pjname
        supervisor.supervisor_main().StopProcess(args)

    def __start_supervisor(self, pjname):
        """
        @name 开启supervisor守护进程
        @auther hezhihong<2022-10-31>
        @return 
        """
        import supervisor
        args = public.dict_obj()
        args.program = pjname
        args.pjname = pjname
        # self.StartSupervisor(args)
        supervisor.supervisor_main().StartProcess(args)

    def __remove_supervisor(self, pjname):
        """
        @name 删除supervisor守护进程
        @auther hezhihong
        @return 
        """
        import supervisor
        args = public.dict_obj()
        args.program = pjname
        supervisor.supervisor_main().RemoveProcess(args)

    # 停止项目
    def StopProject(self, get):
        conf = self.__read_config(self.__conf)
        pjname = get.pjname
        is_supervisor = self.__get_project_info(pjname, 'is_supervisor')
        supervisor_status = self.__get_project_info(pjname, 'supervisor_status')
        result = self.__get_project_info(pjname, 'supervisor_name')
        if result['msg'] and 'is_stop' not in get and is_supervisor['status'] and is_supervisor['msg'] in ['1', 1] and \
                supervisor_status['status'] and supervisor_status['msg'] in [1, '1']: self.__remove_supervisor(
            result['msg'])
        if conf:
            for i in conf:
                if pjname == i["pjname"]:
                    s_path = i["path"] if i['rtype'] != 'python' else i["vpath"]
                    if i["status"] == "1":
                        pid = public.ExecShell(
                            "ps aux|grep '%s'|awk '{print $2}'" % s_path)[0].split(
                            "\n")
                        for p in pid:
                            public.ExecShell("sync && kill -9 %s" % p)
                        i["status"] = "0"
                    else:
                        return public.returnMsg(False, "项目已经停止")
                    self.__write_config(self.__conf, conf)
                    pid = public.ExecShell("ps aux|grep '%s'|grep -v 'grep'|wc -l" % s_path)[0].strip("\n")
                    if pid == "0":
                        return public.returnMsg(True, "停止成功")
                    else:
                        return public.returnMsg(False, "停止失败")

    # 站点映射
    def ProxyProject(self, get):
        conf = self.__read_config(self.__conf)
        pjname = get.pjname.strip()
        domain = get.domain.strip()
        n = 0
        j = 0
        for i in conf:
            if i["pjname"] == pjname:
                port = i["port"]
                j += n
                n += 1
                if not port:
                    return public.returnMsg(False, "该项目没有端口无法映射，uwsgi模式现阶段不支持sock文件模式映射")
            else:
                n += 1

        sql = public.M('sites')
        if sql.where("name=?", (domain,)).count(): return public.returnMsg(False, 'SITE_ADD_ERR_EXISTS');
        ret = {"domain": domain, "domainlist": [], "count": 0}
        get.webname = json.dumps(ret)
        get.port = "80"
        get.ftp = 'false'
        get.sql = 'false'
        get.version = '00'
        get.ps = 'Python项目[' + pjname + ']的映射站点'
        get.path = public.M('config').where("id=?", ('1',)).getField('sites_path') + '/' + domain
        result = self.create_site(get)
        if 'status' in result: return result
        import panelSite
        s = panelSite.panelSite()
        get.sitename = domain
        x = pjname if len(pjname) < 13 else pjname[:10] + "..."
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
            conf[j]["proxy"] = domain
            self.__write_config(self.__conf, conf)
            return public.returnMsg(True, '添加成功!')
        else:
            return public.returnMsg(False, '添加失败!')

    def create_site(self, get):
        import panelSite
        s = panelSite.panelSite()
        result = s.AddSite(get)
        if 'status' in result: return result
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
        conf = self.__read_config(self.__conf)
        pjname = get.pjname.strip()
        import panelSite
        for i in conf:
            if pjname == i["pjname"]:
                get.id = public.M('sites').where('name=?', (i["proxy"],)).getField("id")
                get.webname = i["proxy"]
                get.path = 1
                get.domain = i["proxy"]
                panelSite.panelSite().DeleteSite(get)
                i["proxy"] = ""
                self.__write_config(self.__conf, conf)
                return public.returnMsg(True, '取消成功!')

    # 删除项目
    def RemoveProject(self, get):
        conf = self.__read_config(self.__conf)
        pjname = get.pjname
        get.is_stop = True
        is_supervisor = self.__get_project_info(pjname, 'is_supervisor')
        supervisor_status = self.__get_project_info(pjname, 'supervisor_status')
        supervisor_name = self.__get_project_info(pjname, 'supervisor_name')
        if conf:
            for i in range(len(conf)):
                if pjname == conf[i]["pjname"]:
                    self.__remove_python_cron(pjname)
                    logfile = self.logpath + "/%s.log" % pjname
                    if is_supervisor['status'] and supervisor_status['status'] and supervisor_name['msg']:
                        self.__remove_supervisor(supervisor_name['msg'])
                    if conf[i]["status"] == "1":
                        result = self.StopProject(get)
                        if not result['status'] and result['msg'] != '停止失败': 
                            return public.returnMsg(False, "请将项目停止后再删除")
                    public.ExecShell("rm -rf %s" % conf[i]["vpath"])
                    public.ExecShell("rm -f %s" % logfile)
                    public.ExecShell("rm -f %s/uwsgi.ini" % conf[i]["path"])
                    public.ExecShell("rm -f %s/gunicorn_conf.py" % conf[i]["path"])
                    public.ExecShell('systemctl disable {}_pymanager'.format(pjname))
                    public.ExecShell('rm -f /etc/init.d/{}_pymanager'.format(pjname))
                    public.ExecShell('rm -f /lib/systemd/system/{}_pymanager'.format(pjname))
                    del (conf[i])
                    self.__write_config(self.__conf, conf)
                    return public.returnMsg(True, "删除成功")

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
        conf = self.__read_config(self.__conf)
        sysv = platform.python_version()
        v = get.version
        v = v.split()[0]
        # if v == sysv:
        #     return public.returnMsg(False, "该版本为系统默认python，无法卸载")
        for i in conf:
            if i["version"] == v:
                return public.returnMsg(False, "该版本有项目正在使用，请先删除项目后再卸载")
        exist_pv = self.GetPythonV(get)
        if v not in exist_pv:
            return public.returnMsg(False, "没有安装该Python版本")
        # public.ExecShell("echo 'y'|%s/bin/pyenv uninstall %s" % (self.pyenv_path,v))
        self.remove_python(v)
        exist_pv = self.GetPythonV(get)
        if v in exist_pv:
            return public.returnMsg(False, "卸载Python失败，请再试一次")
        return public.returnMsg(True, "卸载Python成功")

    def remove_python(self, pyv):
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

    # 获取项目日志
    def GetProjectLog(self, get):
        pjname = get.pjname
        conf = self.__read_config(self.__conf)
        for i in conf:
            if i["pjname"] == pjname:
                logpath = "%s/logs/error.log" % (i["path"])
                if 'log_path' in i: logpath = i['log_path'] + '/error.log'
                if os.path.exists(logpath):
                    result = public.ExecShell("tail -n 300 %s" % logpath)[0]
                    return result
                else:
                    get.pjname = self.__get_project_info(pjname, 'supervisor_name')['msg']
                    import supervisor
                    result = supervisor.supervisor_main().GetProjectLog(get)
                    if result != '该进程没有日志':
                        return result
                    return "该项目没有日志"

    # 写日志
    def WriteLog(self, msg):
        path = "%s/py.log" % self.basedir
        localtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        if not os.path.exists(path):
            public.ExecShell("touch %s" % path)
        public.writeFile(path, localtime + "\n" + msg + "\n", "a+")

    # 读配置
    def __read_config(self, path):
        if not os.path.exists(path):
            public.writeFile(path, '[]')
        upBody = public.readFile(path)
        if not upBody: upBody = '[]'
        return json.loads(upBody)

    # 写配置
    def __write_config(self, path, data):
        return public.writeFile(path, json.dumps(data))

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
            'bash {plugin_path}/install_python.sh {pyv} &> {log}'.format(plugin_path=self.basedir, pyv=get.version, log="%s/py.log" % self.basedir))
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
        self.WriteLog(str(files.files().CopyFile(get)))
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

    # 判断当前项目是否在守护中
    def supervisor_exists(self, supervisor_name):
        import supervisor
        args = public.dict_obj()
        if not hasattr(self, "_supervisor_list"):
            res = supervisor.supervisor_main().GetProcessList(args)
            setattr(self, "_supervisor_list", res)
        else:
            res = self._supervisor_list
        for i in res:
            if i["program"] == supervisor_name:
                return True
        return False

    def supervisor_list(self):
        import supervisor
        args = public.dict_obj()
        if not hasattr(self, "_supervisor_list"):
            res = supervisor.supervisor_main().GetProcessList(args)
            setattr(self, "_supervisor_list", res)
        else:
            res = self._supervisor_list
        return res


if __name__ == '__main__':
    p = pythonmamager_main()
    p.auto_start()
