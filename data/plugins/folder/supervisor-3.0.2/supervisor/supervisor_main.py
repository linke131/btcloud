#!/www/server/panel/pyenv/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Author: 刘佳东 <1548429568@qq.com>
# | Author: wzz <wzz@bt.cn>
# +-------------------------------------------------------------------
# |   守护进程管理器
# +-------------------------------------------------------------------
import sys, os, json, re, time, unicodedata
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

    supervisord_pid = "/var/run/supervisor.pid"
    supervisord_sock = "/var/run/supervisor.sock"
    supervisord_log = "/var/log/supervisord.log"

    proxy_client = None

    def __init__(self):
        if os.path.exists('/www/server/panel/pyenv'):
            self.supervisord_path = '/www/server/panel/pyenv/bin/supervisord'
            self.supervisorctl_path = '/www/server/panel/pyenv/bin/supervisorctl'
        else:
            self.supervisord_path = 'supervisord'
            self.supervisorctl_path = 'supervisorctl'
        if not self.proxy_client:
            self.proxy_client = client.ServerProxy('http://localhost',
                                                   transport=UnixStreamTransport(
                                                       self.supervisord_sock))

    # -----------------------------新加功能区域--------------------------------------
    def GetServerStatus(self, get):
        '''
        获取supervisord服务运行状态
        @param get: 不需要传参
        @return:
        '''
        ps_process = public.ExecShell("ps -ef|grep supervisord|grep -v grep")
        systemcd_status = public.ExecShell("systemctl status supervisord")
        if ps_process[0] and "active (running)" in systemcd_status[0]:
            return public.ReturnMsg(True, "服务运行正常")
        return public.ReturnMsg(False, "服务运行异常或停止状态")

    def __ServerOption(self, get):
        '''
        systemd服务状态设置
        @param get: get["cmd"]: str(start|stop|restart)   get["status"]: str(重启|停止|启动)
        @return:
        '''
        # if get["cmd"] == "restart" or get["cmd"] == "start":
        #     public.ExecShell("systemctl {} supervisord".format("stop"))
        # c_result = public.ExecShell(f"systemctl {get['cmd']} supervisord")
        # if c_result[1] == "": return public.ReturnMsg(True, f"服务已{get['status']}")
        # return public.ReturnMsg(False, f"服务{get['status']}失败")
        os.system(f"systemctl {get['cmd']} supervisord")
        if get["cmd"] == "stop":
            if os.path.exists(self.supervisord_pid): os.remove(self.supervisord_pid)
            if os.path.exists(self.supervisord_sock): os.remove(self.supervisord_sock)
        s_status = self.GetServerStatus(None)
        if get["cmd"] == "start" or get["cmd"] == "restart":
            if s_status["status"]: return public.ReturnMsg(True, f"服务{get['status']}成功")
        if get["cmd"] == "stop":
            if not s_status["status"]: return public.ReturnMsg(True, f"服务{get['status']}成功")
        if get["cmd"] == "start":
            return public.ReturnMsg(False, f"服务{get['status']}失败,请点击右边【重启】按钮尝试")
        return public.ReturnMsg(False, f"服务{get['status']}失败,请到命令行执行次命令尝试"
                                       f"-->【systemctl {get['cmd']} supervisord】")

    def __KillPid(self):
        '''
        kill掉supervisord的进程
        @return:
        '''
        # pid = public.ExecShell("ps -ef|grep supervisord|grep -v grep|awk '{print $2}'")
        # if pid[0]: public.ExecShell(f"kill -9 {pid[0]}")
        os.system(
            "pid=`ps -ef|grep supervisord|grep -v grep|awk '{print $2}'` && [[ $pid != \"\" ]] && "
            "for i in $pid;do kill -9 $i;done")

    def SetServerStatus(self, get):
        '''
        设置服务状态
        @param get: get.status: str(0|1|2)
        @return:
        '''
        if not hasattr(get, "status"): return public.ReturnMsg(False, "参数不正确")
        s_status = self.GetServerStatus(None)
        if get.status == "0" and not s_status["status"]: return public.ReturnMsg(True, "服务已停止")
        if get.status == "1" and s_status["status"]: return public.ReturnMsg(True, "服务已启动")
        op_data = {"cmd": "", "status": ""}
        if get.status == "2":
            self.__KillPid()
            op_data["cmd"] = "restart"
            op_data["status"] = "重启"
            result = self.__ServerOption(op_data)
        if get.status == "1" and not s_status["status"]:
            self.__KillPid()
            op_data["cmd"] = "start"
            op_data["status"] = "启动"
            result = self.__ServerOption(op_data)
        if get.status == "0" and s_status["status"]:
            op_data["cmd"] = "stop"
            op_data["status"] = "停止"
            result = self.__ServerOption(op_data)
            self.__KillPid()
        if result: return result
        return public.ReturnMsg(False, "服务设置异常,请手动重启supervisord服务!")

    def GetRunLog(self, get):
        '''
        获取最新1000条supervisord运行日志
        @param get: 不需要传参
        @return:
        '''
        if os.path.exists(self.supervisord_log):
            result = public.ExecShell("tail -n 1000 %s" % self.supervisord_log)[0]
            return public.xssencode2(result)
        else:
            return "日志内容为空"

    def GetServerLog(self, get):
        '''
        获取最新30条supervisord的服务日志
        @param get: 不需要传参
        @return:
        '''
        result = public.ExecShell("journalctl -u supervisord -n 30")[0]
        if result != "":
            return public.xssencode2(result)
        else:
            return public.ReturnMsg(False, "日志获取失败,请到【服务管理】重启服务后再试!")

    # -----------------------------新加功能区域--------------------------------------

    def GetPorcessList(self, get):
        return self.GetProcessList(get)

    # 守护进程列表
    def GetProcessList(self, get):
        calls = [{"methodName": "supervisor.getAllProcessInfo"},
                 {"methodName": "supervisor.getAllConfigInfo"}]
        # 获取进程相关配置信息和任务相关配置信息
        try:
            process_infos, config_infos = self.proxy_client.system.multicall(calls)
        except:
            return public.ReturnMsg(False, "守护进程列表获取异常,请到【服务管理】重启服务后再试!")

        if type(process_infos) == dict:
            return
        if type(config_infos) == dict:
            return

        new_info = []
        for i in range(0, len(process_infos)):
            pinfo = process_infos[i]
            cinfo = config_infos[i]
            # 取指定字符最后一次出现的索引
            under_inx = pinfo["name"].rfind("_")
            # 通过索引从0-under_inx取任务名称
            program_name = pinfo["name"][:under_inx]
            # 取对应配置文件中的运行状态
            statename = pinfo["statename"]
            if pinfo["name"][under_inx + 1:] != "00":
                continue

            d = {}
            d["program"] = program_name
            d["runStatus"] = statename
            if statename == "RUNNING":
                d["status"] = "1"
                d["pid"] = pinfo["pid"]
            else:
                d["status"] = 0
                d["pid"] = ""

            d["command"] = cinfo["command"]
            if "user" not in cinfo or "numprocs" not in cinfo:
                try:
                    ini_f = public.readFile(self.profile + "/" + program_name + ".ini").split("\n")
                except:
                    continue
                for i in ini_f:
                    if "user" in i: d["user"] = i.split('=')[1]
                    if "numprocs" in i: d["numprocs"] = i.split('=')[1]
            else:
                d["user"] = cinfo["user"]
                d["numprocs"] = cinfo["numprocs"]
            d["priority"] = cinfo["process_prio"]
            d["ps"] = ''
            conf = self.__read_config(self.conf)
            for f in conf:
                if program_name == f["program"] and "ps" in f: d["ps"] = public.xssencode2(f["ps"])

            new_info.append(d)
        return new_info

    # 守护进程列表
    def GetPorcessList2(self, get):
        if not os.path.isfile(self.status):
            os.system(r"touch {}".format(self.status))
        public.ExecShell("%s update; %s status > %s" % (
            self.supervisorctl_path, self.supervisorctl_path, self.status))
        with open(self.status, "r") as fr:
            lines = fr.readlines()
        if lines:
            for r in lines:
                if "supervisor.sock" in r:
                    public.ExecShell(
                        "%s -c /etc/supervisor/supervisord.conf" % self.supervisord_path)
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
        # profile = "/www/server/panel/plugin/supervisor/profile/"
        if not os.path.exists(self.profile):
            os.makedirs(self.profile)
        # log = "/www/server/panel/plugin/supervisor/profile/"
        if not os.path.exists(self.log):
            os.makedirs(self.log)
        program = get.pjname
        user = get.user
        path = get.path
        command = get.command
        numprocs = get.numprocs
        # projectfile = "/www/server/panel/plugin/supervisor/profile/ + get.pjname + '.ini'"
        projectfile = self.profile + program + ".ini"
        if not program:
            return public.ReturnMsg(False, '请输入管理进程的名称!')
        if re.fullmatch(r'[\u4e00-\u9fff]+', program):
            return public.ReturnMsg(False, '任务名称不支持中文!')
        if not os.path.exists(path) or not os.path.isdir(path):
            return public.ReturnMsg(False, '该运行目录不存在!')
        if os.path.isfile(path):
            return public.ReturnMsg(False, '不能选择文件,请选择目录!')

        # 检测是否已经存在这个进程名的任务
        dir_or_files = os.listdir(self.profile)
        files = []
        for file in dir_or_files:
            if os.path.isfile(self.profile + file):
                files.append(file)
        if files:
            if program + ".ini" in files:
                return public.ReturnMsg(False, '该进程名已被使用!')

        # 构造配置文件信息
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
        # projectfile = "/www/server/panel/plugin/supervisor/profile/ + get.pjname + '.ini'"
        result = public.WriteFile(projectfile, w_body, mode='w+')
        if result:  # True
            cmd_result = public.ExecShell("{0} update".format(self.supervisorctl_path))
            if "error" in cmd_result[0]:
                args = public.dict_obj()
                args.status = "2"
                self.SetServerStatus(args)
            d = dict()
            d["program"] = program
            d["command"] = command  # 启动命令
            d["directory"] = path  # 运行目录
            d["user"] = user
            d["priority"] = "999"
            d["numprocs"] = numprocs
            result2 = public.ExecShell(
                "{0} status ".format(self.supervisorctl_path) + program + " | awk '{print $2}'")
            d["runStatus"] = result2[0].replace("\n", "")
            d["ps"] = public.xssencode2(get.ps)
            conf = self.__read_config(self.conf)
            conf.append(d)
            self.__write_config(self.conf, conf)
            time.sleep(3)
            return public.ReturnMsg(True, '增加守护进程成功!')

    def RemoveProcess(self, get):
        name = get.program
        result = public.ExecShell("{0} stop ".format(self.supervisorctl_path) + name)
        program = self.profile + name + ".ini"

        # 删除config.json文件里的进程信息
        conf = self.__read_config(self.conf)
        for i in conf:
            if name == i["program"]:
                conf.remove(i)
        self.__write_config(self.conf, conf)

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
            cmd_result = public.ExecShell("{0} update".format(self.supervisorctl_path))
            if "error" in cmd_result[0]:
                args = public.dict_obj()
                args.status = "2"
                self.SetServerStatus(args)
            return public.ReturnMsg(True, '删除守护进程成功!')
        else:
            result = public.ExecShell("{0} update".format(self.supervisorctl_path))
            return public.ReturnMsg(False, '该守护进程不存在!')

    def UpdateProcess(self, get):
        user = get.user
        oldname = get.pjname
        priority = get.level.strip()
        numprocs = get.numprocs.strip()
        path = get.path
        command = get.command
        ps = public.xssencode2(get.ps.strip())
        if re.fullmatch(r'[\u4e00-\u9fff]+', oldname):
            return public.ReturnMsg(False, '任务名称不支持中文!')
        if not priority: return public.returnMsg(False, "启动优先级不能为空")
        if not numprocs: return public.returnMsg(False, "进程数量不能为空")
        if priority == "0": return public.returnMsg(False, "启动优先级不能为0")
        if numprocs == "0": return public.returnMsg(False, "进程数量不能为0")
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
                d["command"] = command
                d["directory"] = path
                d["ps"] = ps
                conf.append(d)
                break
        else:
            # 兼容旧版本没有备注和启动命令的情况
            ini_conf = public.readFile(self.profile + oldname + ".ini").split("\n")
            for i in ini_conf:
                if "directory" in i:
                    i = i.split("=")
                    d["directory"] = i[1]
                if "command" in i:
                    i = i.split("=")
                    d["command"] = i[1]
            if path: d["directory"] = path
            if command: d["command"] = command
            d["runStatus"] = ''
            d["program"] = oldname
            d["priority"] = priority
            d["user"] = user
            d["numprocs"] = numprocs
            d["ps"] = ps
            conf.append(d)
        self.__write_config(self.conf, conf)
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
            elif re.match('directory=.*', i):
                content += "directory=" + path + "\n"
            elif re.match('command=.*', i):
                content += "command=" + command + "\n"
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
        cmd_result = public.ExecShell("{0} update".format(self.supervisorctl_path))
        if "error" in cmd_result[0]:
            args = public.dict_obj()
            args.status = "2"
            self.SetServerStatus(args)
        time.sleep(3)
        return public.ReturnMsg(True, '修改守护进程成功!')

    def StartProcess(self, get):
        name = get.program
        res = self.Check_name(name)
        profile = self.profile + name + ".ini"
        content = public.readFile(profile)
        if res:
            if content.find('numprocs') != -1:
                cmd = "{0} start ".format(self.supervisorctl_path) + name + ":"
                result = public.ExecShell(cmd)
            else:
                cmd = "{0} start ".format(self.supervisorctl_path) + name
                result = public.ExecShell(cmd)
            if "ERROR" in result[0] and "already started" in result[0]:
                return public.ReturnMsg(False, '进程已经启动!')
            elif "ERROR" in result[0] and "spawn error" in result[0]:
                return public.ReturnMsg(False, '进程启动异常!')
            else:
                return public.ReturnMsg(True, '进程启动成功!')
        else:
            cmd_result = public.ExecShell("{0} update".format(self.supervisorctl_path))
            if "error" in cmd_result[0]:
                args = public.dict_obj()
                args.status = "2"
                self.SetServerStatus(args)
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
                return public.ReturnMsg(False, '进程已经停止!')
            return public.ReturnMsg(True, '进程停止成功!')
        else:
            cmd_result = public.ExecShell("{0} update".format(self.supervisorctl_path))
            if "error" in cmd_result[0]:
                args = public.dict_obj()
                args.status = "2"
                self.SetServerStatus(args)
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
        special = ["bin", "daemon", "adm", "lp", "shutdown", "halt", "mail", "operator", "games",
                   "avahi-autoipd", "systemd-bus-proxy", "systemd-network", "dbus", "polkitd",
                   "tss", "ntp"]
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
        with open(file, "r") as fr:
            infos = fr.readlines()
        for line in infos:
            if "user=" in line.strip():
                mess["user"] = line.strip().split('=')[1]
            if "numprocs=" in line.strip():
                mess["numprocs"] = line.strip().split('=')[1]
            if "priority=" in line.strip():
                mess["priority"] = line.strip().split('=')[1]
            if "directory=" in line.strip():
                mess["directory"] = line.strip().split('=')[1]
            if "command=" in line.strip():
                mess["command"] = line.strip().split('=')[1]
        conf = self.__read_config(self.conf)
        mess["ps"] = [i["ps"] for i in conf if name == i["program"]]
        mess["ps"] = "" if len(mess["ps"]) == 0 else mess["ps"][0]
        mess["ps"] = public.xssencode2(mess["ps"])
        userlist = self.GetUserList({})
        info["userlist"] = userlist
        info["daemoninfo"] = mess
        return info

    def Check_name(self, name):
        '''
        查看指定任务名的配置文件是否存在
        @param name: 任务名称
        @return:
        '''
        profile = self.profile + name + ".ini"
        if os.path.isfile(profile):
            return True
        else:
            return False

    # 读守护进程日志
    def GetProjectLog(self, get):
        name = get.pjname
        log_type = "normal"
        if "log_type" in get:
            log_type = get.log_type

        if log_type != "normal":
            log_path = self.log + name + ".err.log"
        else:
            log_path = self.log + name + ".out.log"
        if os.path.exists(log_path):
            result = public.ExecShell("tail -n 800 %s" % log_path)[0]
            return public.xssencode2(result)
        else:
            return "日志内容为空"

    # 清理进程日志
    def clear_record(self, get):
        filename = get.filename
        log_type = "normal"
        if "log_type" in get:
            log_type = get.log_type
        if log_type != "normal":
            log_name = self.log + filename + '.err.log'
        else:
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
        if not os.path.isfile(self.logpath):
            os.system(r"touch {}".format(self.logpath))
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
        if not os.path.exists(get.path): return public.ReturnMsg(False, "配置文件不存在!")
        profile = get.path
        with open(profile, "r") as fr:
            lines = fr.readlines()
        f_string = get.data.split("\n")
        if lines[0] != f_string[0]: return public.ReturnMsg(False, "不支持修改进程名,若要修改请重新添加守护进程任务!")
        res = f.SaveFileBody(get)
        reload_cmd = "%s reload" % self.supervisorctl_path
        public.ExecShell(reload_cmd)
        return res

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
