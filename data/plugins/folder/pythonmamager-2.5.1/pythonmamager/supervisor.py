#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Author: 刘佳东 <1548429568@qq.com>
# +-------------------------------------------------------------------
# |   守护进程管理器
# +-------------------------------------------------------------------
import sys, os, json, re, time
from http.client import HTTPConnection
from xmlrpc import client
import socket

os.chdir("/www/server/panel")
sys.path.insert(0, "class/")

import public


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

class supervisor_main:
    basedir = "/www/server/panel/plugin/supervisor"
    supervisor_conf_file = "/etc/supervisor/supervisord.conf"
    # 所有进程配置文件夹
    profile = "%s/profile/" % basedir
    # 所有进程日志文件夹
    log = "%s/log/" % basedir
    # 进程信息详情文件
    conf = "%s/config.json" % basedir

    # 终端输出日志文件
    logpath = "%s/terminal.out" % basedir
    # 进程状态临时文件
    status = "%s/status.txt" % basedir
    # 用户列表临时文件
    user = "%s/user.txt" % basedir

    proxy_client = None
    
    def __init__(self):
        if os.path.exists('/www/server/panel/pyenv'):
            self.supervisord_path = '/www/server/panel/pyenv/bin/supervisord'
            self.supervisorctl_path='/www/server/panel/pyenv/bin/supervisorctl'
        else:
            self.supervisord_path = 'supervisord'
            self.supervisorctl_path='supervisorctl'
        if not self.proxy_client:
            self.proxy_client = client.ServerProxy('http://localhost', 
                transport=UnixStreamTransport("/var/run/supervisor.sock"))

    # 守护进程列表
    def GetProcessList(self, get):
        calls = [
            {"methodName": "supervisor.getAllProcessInfo"}, 
            {"methodName": "supervisor.getAllConfigInfo"}
        ]
        # print("Methods:", proxy.system.listMethods())
        process_infos, config_infos = self.proxy_client.system.multicall(calls)
        if type(process_infos) == dict: 
            print(process_infos)
            return
        if type(config_infos) == dict:
            print(config_infos)
            return

        new_info = []
        # print(len(process_infos), type(process_infos))
        # print(len(config_infos), type(config_infos))
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
            d["user"] = cinfo["user"]
            d["priority"] = cinfo["process_prio"]
            d["numprocs"] = cinfo["numprocs"]
            if "is_python" in cinfo:
                new_info.append(d)
        return new_info

    # 守护进程列表
    def GetPorcessList2(self, get):
        if not os.path.isfile(self.status):
            os.system(r"touch {}".format(self.status))
        public.ExecShell("%s update; %s status > %s" % (self.supervisorctl_path, self.supervisorctl_path, self.status))
        with open(self.status, "r") as fr:
            lines = fr.readlines()
        if lines:
            for r in lines:
                if "supervisor.sock" in r:
                    public.ExecShell("%s -c /etc/supervisor/supervisord.conf" % self.supervisord_path)
                    public.ExecShell("%s status > %s" % (self.supervisorctl_path, self.status))
                    with open(self.status, "r") as fr:
                        lines = fr.readlines()
                if "未找到命令" in r:
                    return public.ReturnMsg(False, '请先安装supervisor!')

        array_list = []
        process_list = []
        for r in lines:
            array = r.split()
            if array:
                d = dict()
                program = array[0].split(':')[0]
                if program in process_list: continue
                process_list.append(program)
                d["program"] = program
                d["runStatus"] = array[1]
                if array[1] == "RUNNING":
                    d["status"] = "1"
                    d["pid"] = array[3][:-1]
                else:
                    d["status"] = "0"
                    d["pid"] = ""
                file = self.profile + program + ".ini"
                if not os.path.exists(file): continue
                with open(file, "r") as fr:
                    infos = fr.readlines()
                for line in infos:
                    if "command=" in line.strip():
                        d["command"] = line.strip().split('=')[1]
                    if "user=" in line.strip():
                        d["user"] = line.strip().split('=')[1]
                    if "priority=" in line.strip():
                        d["priority"] = line.strip().split('=')[1]
                    if "numprocs=" in line.strip():
                        d["numprocs"] = line.strip().split('=')[1]
                array_list.append(d)
        return array_list

    def AddProcess(self, get):
        if not os.path.exists(self.profile):
            os.makedirs(self.profile)
        if not os.path.exists(self.log):
            os.makedirs(self.log)
        program = get.pjname
        user = get.user
        path = get.path
        command = get.command
        numprocs = get.numprocs
        projectfile = self.profile + program + ".ini"
        if not program:
            return False
            return public.ReturnMsg(False, '请输入管理进程的名称!')
        if not os.path.exists(path) or not os.path.isdir(path):
            return False
            return public.ReturnMsg(False, '该运行目录不存在!')

        dir_or_files = os.listdir(self.profile)
        files = []
        for file in dir_or_files:
            if os.path.isfile(self.profile + file):
                files.append(file)
        if files:
            if program + ".ini" in files:
                return False
                return public.ReturnMsg(False, '该进程名已被使用!')

        w_body = ""
        w_body += "[program:" + program + "]" + "\n"
        w_body += "command=" + command + "\n"
        w_body += "directory=" + path + "\n"
        w_body += "autorestart=true" + "\n"
        w_body += "startsecs=3" + "\n"
        w_body += "startretries=3" + "\n"
        w_body += "stdout_logfile=" + self.log + program + ".out.log" + "\n"
        w_body += "stderr_logfile=" + self.log + program + ".err.log" + "\n"
        w_body += "stdout_logfile_maxbytes=2MB" + "\n"
        w_body += "stderr_logfile_maxbytes=2MB" + "\n"
        w_body += "user=" + user + "\n"
        w_body += "priority=999" + "\n"
        w_body += "numprocs={0}".format(numprocs) + "\n"
        w_body += "process_name=%(program_name)s_%(process_num)02d"

        # 进程信息写入ini文件
        result = public.WriteFile(projectfile, w_body, mode='w+')
        if result:
            public.ExecShell("{0} update".format(self.supervisorctl_path))
            d = dict()
            d["program"] = program
            d["command"] = command  # 启动命令
            d["directory"] = path   # 运行目录
            d["user"] = user
            d["priority"] = "999"
            d["numprocs"] = numprocs
            d["is_python"]='true' if 'is_supervisor' in get else 'false'
            result2 = public.ExecShell("{0} status ".format(self.supervisorctl_path) + program + " | awk '{print $2}'")
            d["runStatus"] = result2[0].replace("\n", "")
            conf = self.__read_config(self.conf)
            conf.append(d)
            ress = self.__write_config(self.conf, conf)
            time.sleep(3)
            if 'is_supervisor' not in get:return public.ReturnMsg(True, '增加守护进程成功!')
            return True
            

    def RemoveProcess(self, get):
        name = get.program
        result = public.ExecShell("{0} stop ".format(self.supervisorctl_path) + name)
        program = self.profile + name + ".ini"

        # 删除config.json文件里的进程信息
        conf = self.__read_config(self.conf)
        for i in conf:
            if name == i["program"]:
                conf.remove(i)
        ress = self.__write_config(self.conf, conf)

        # 删除日志文件
        outlog = self.log + name + ".out.log"
        if os.path.isfile(outlog):
            os.remove(outlog)
        errlog = self.log + name + ".err.log"
        if os.path.isfile(errlog):
            os.remove(errlog)

        # 删除ini文件
        if os.path.isfile(program):
            os.remove(program)
            result = public.ExecShell("{0} update".format(self.supervisorctl_path))
            return public.ReturnMsg(True, '删除守护进程成功!')
        else:
            result = public.ExecShell("{0} update".format(self.supervisorctl_path))
            return public.ReturnMsg(False, '该守护进程不存在!')

    def UpdateProcess(self, get):
        user = get.user
        oldname = get.pjname
        priority = get.level
        numprocs = get.numprocs
        # 修改config.json文件
        conf = self.__read_config(self.conf)
        d = dict()
        for i in conf:
            if oldname == i["program"]:
                d = i
                conf.remove(i)
                d["priority"] = priority
                d["user"] = user
                d["numprocs"] = numprocs
                conf.append(d)
                break
        ress = self.__write_config(self.conf, conf)
        # 修改ini文件
        profile = self.profile + oldname + ".ini"
        with open(profile, "r") as fr:
            lines = fr.readlines()
        content = ""
        for i in lines:
            if re.match('user=.*', i):
                content += "user=" + user + "\n"
            elif re.match('priority=.*', i):
                content += "priority=" + priority + "\n"
            elif re.match('numprocs=.*', i):
                content += "numprocs=" + numprocs + "\n"
            else:
                content += i
        if content.find('numprocs') == -1:
            content += 'numprocs=1\n'
            content += 'process_name=%(program_name)s_%(process_num)02d'
        with open(profile, "r+") as f:
            read_data = f.read()
            f.seek(0)
            f.truncate()
            f.write(content)
        public.ExecShell("{0} update".format(self.supervisorctl_path))
        time.sleep(3)
        return public.ReturnMsg(True, '修改守护进程成功!')

    def StartProcess(self, get):
        name = get.program
        res = self.Check_name(name)
        profile = self.profile + name + ".ini"
        content = public.readFile(profile)
        print("content:")
        print(content)
        if res:
            if content.find('numprocs') != -1:
                cmd = "{0} start ".format(self.supervisorctl_path) + name + ":"
                result = public.ExecShell(cmd)
            else:
                cmd = "{0} start ".format(self.supervisorctl_path) + name
                print(cmd)
                result = public.ExecShell(cmd)
            print("start result:")
            print(result)
            if "ERROR" in result[0] and "already started" in result[0]:
                return public.ReturnMsg(False, '进程已经启动!')
            elif "ERROR" in result[0] and "spawn error" in result[0]:
                return public.ReturnMsg(False, '进程启动异常!')
            else:
                return public.ReturnMsg(True, '进程启动成功!')
        else:
            public.ExecShell("{0} update".format(self.supervisorctl_path))
            return public.ReturnMsg(False, '该守护进程不存在!')

    def StopProcess(self, get):
        name = get.program
        res = self.Check_name(name)
        profile = self.profile + name + ".ini"
        with open(profile, "r") as fr:
            content = fr.read()
        if res:
            if content.find('numprocs') != -1:
                result = public.ExecShell("{0} stop ".format(self.supervisorctl_path) + name + ":")
            else:
                result = public.ExecShell("{0} stop ".format(self.supervisorctl_path) + name)
            if "ERROR" in result[0]:
                return True
                return public.ReturnMsg(False, '进程已经停止!')
            return True
            return public.ReturnMsg(True, '进程停止成功!')
        else:
            public.ExecShell("{0} update".format(self.supervisorctl_path))
            return False
            return public.ReturnMsg(False, '该守护进程不存在!')

    # 获取用户列表
    def GetUserList(self, get):
        if not os.path.isfile(self.user):
            os.system(r"touch {}".format(self.user))
        res = public.ExecShell("cat /etc/passwd > %s" % self.user)
        with open(self.user, "r") as fr:
            users = fr.readlines()
        fr.close()
        os.remove(self.user)

        user_list = []
        special = ["bin", "daemon", "adm", "lp", "shutdown", "halt", "mail", "operator", "games", "avahi-autoipd", "systemd-bus-proxy", "systemd-network", "dbus", "polkitd", "tss", "ntp"]
        for u in users:
            user = re.split(':', u)[0]
            if user in special:
                continue
            user_list.append(user)
        return user_list

    def GetProgressInfo(self, get):
        name = get.program
        info = dict()
        mess = dict()
        mess["program"] = name
        file = self.profile + name + '.ini'
        conf = ""
        with open(file, "r") as fr:
            infos = fr.readlines()
        for line in infos:
            if "user=" in line.strip():
                mess["user"] = line.strip().split('=')[1]
            if "numprocs=" in line.strip():
                mess["numprocs"] = line.strip().split('=')[1]
            if "priority=" in line.strip():
                mess["priority"] = line.strip().split('=')[1]
        userlist = self.GetUserList({})
        info["userlist"] = userlist
        info["daemoninfo"] = mess
        return info

    def Check_name(self, name):
        profile = self.profile + name + ".ini"
        if os.path.isfile(profile):
            return True
        else:
            return False

    # 读守护进程日志
    def GetProjectLog(self, get):
        name = get.pjname
        log_path = self.log + name + ".out.log"
        if os.path.exists(log_path):
            result = public.ExecShell("tail -n 800 %s" % log_path)[0]
            return result
        else:
            return "该进程没有日志"

    # 清理进程日志
    def clear_record(self, get):
        filename = get.filename
        log_name = self.log + filename + '.out.log'
        if not os.path.exists(log_name):
            return public.ReturnMsg(False, "日志文件不存在!")
        with open(log_name, 'r+') as fr:
            fr.truncate()
        return public.ReturnMsg(True, "删除日志成功!")

    # 读日志(终端)
    def GetTerminalLog(self, get):
        if os.path.exists(self.logpath):
            result = public.ExecShell("tail -n 800 %s" % self.logpath)[0]
            return result
        else:
            return ""

    # 写日志(终端)
    def WriteLog(self, msg):
        # localtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        if not os.path.isfile(self.logpath):
            os.system(r"touch {}".format(self.logpath))
        # public.writeFile(self.logpath, localtime + "\n" + msg + "\n", "a+")
        public.writeFile(self.logpath, msg + "\n", "a+")

    # 读取supervisord.conf文件配置
    def GetSupervisorFile(self, get):
        import files
        f = files.files()
        return f.GetFileBody(get)

    # 保存supervisord.conf文件配置
    def SaveSupervisorFile(self, get):
        import files
        f = files.files()
        return f.SaveFileBody(get)

    # 读config.json配置
    def __read_config(self, path):
        if not os.path.exists(path):
            public.writeFile(path, '[]')
        upBody = public.readFile(path)
        if not upBody:
            upBody = '[]'
        return json.loads(upBody)

    # 写config.json配置
    def __write_config(self, path, data):
        return public.writeFile(path, json.dumps(data))
