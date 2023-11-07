#coding: utf-8
import os,sys,json,time,re,psutil
os.chdir('/www/server/panel')
sys.path.insert(0,'class/')

import public
from datetime import datetime


class syssafe_pub:
    __plugin_path = '/www/server/panel/plugin/syssafe/'
    __state = {True: '开启', False: '关闭'}
    __name = u'系统加固'
    __deny = '/etc/hosts.deny'
    __allow = '/etc/hosts.allow'
    __months = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09', 'Sept': '09',
                'Oct': '10', 'Nov': '11', 'Dec': '12'}
    __deny_list = None
    __config = None
    __last_ssh_time = 0
    __last_ssh_size = 0
    __log_file = None
    __sys_process = []
    access_defs = ['start', 'set_open']

    # 开始处理
    def start(self):
        try:
            # import threading
            # p = threading.Thread(target=self.ssh_task)
            # p.setDaemon(True)
            # p.start()
            self.process_task()
        except:
            print('【{}正在停止系统加固相关进程...'.format(public.getDate()))
            self.set_open(None, 0,0)
            print('【{}】系统加固监控进程已关闭'.format(public.getDate()))
    # 锁定目录或文件
    def __lock_path(self, pathInfo):
        try:
            if not os.path.exists(pathInfo['path']): return False
            if pathInfo['d_mode']:
                os.chmod(pathInfo['path'], pathInfo['d_mode'])
            if pathInfo['chattr']:
                public.ExecShell('chattr -R +%s %s' % (pathInfo['chattr'], pathInfo['path']))
            return True
        except:
            return False

    # 目录或文件解锁
    def __unlock_path(self, pathInfo):
        try:
            if not os.path.exists(pathInfo['path']): return False
            if pathInfo['chattr']:
                public.ExecShell('chattr -R -%s %s' % (pathInfo['chattr'], pathInfo['path']))
            if pathInfo['s_mode']:
                os.chmod(pathInfo['path'], pathInfo['s_mode'])
            return True
        except:
            return False

    # 设置指定项的锁定状态
    def __set_safe_state(self, paths, lock=True):
        for path_info in paths:
            if lock:
                self.__lock_path(path_info)
            else:
                self.__unlock_path(path_info)
        return True

    # 写配置文件
    def __write_config(self, data):
        public.writeFile(self.__plugin_path + 'config.json', json.dumps(data))
        return True

    # 读配置文件
    def __read_config(self):
        return json.loads(public.readFile(self.__plugin_path + 'config.json'))
    
    # 取deny_list
    def get_deny_list_all(self):
        deny_file = self.__plugin_path + 'deny.json'
        if not os.path.exists(deny_file): public.writeFile(deny_file, '{}')
        deny_list = json.loads(public.readFile(deny_file))
        return deny_list

    # clear deny_list
    def clear_deny_list(self):
        deny_list = self.get_deny_list_all()
        if not deny_list: return
        host_dyne_file = '/etc/hosts.deny'
        for ip in deny_list.keys():
            public.ExecShell("sed -i '/:{}:/d' {}".format(ip, host_dyne_file))

    # 写deny_list
    def set_deny_list(self):
        deny_list = self.get_deny_list_all()
        if not deny_list: return
        host_deny_file = '/etc/hosts.deny'
        host_deny_body = public.readFile(host_deny_file)
        if not host_deny_body: return
        host_deny_body_list = host_deny_body.strip().split('\n')

        for ip in deny_list.keys():
            _deny = 'sshd:{}:deny'.format(ip)
            if host_deny_body.find(_deny) != -1: continue
            host_deny_body_list.append(_deny)
        host_deny_body = '\n'.join(host_deny_body_list)
        public.writeFile(host_deny_file, host_deny_body + "\n")
    

    # 设置系统加固开关
    def set_open(self, get=None, is_hit=-1,status = 1):
        data = self.__read_config()
        # if not data['open'] and is_hit == 1: return True
        if is_hit != -1:
            data['open'] = is_hit == 0
        if get: 
            if 'status' in get: status = int(get.status)

        data['open'] = status == 1

        if status == 0:
            self.clear_deny_list()
        else:
            self.set_deny_list()

        for s_name in data.keys():
            if type(data[s_name]) == bool: continue
            if not data['open']:
                data[s_name]['last_open'] = data[s_name]['open']
                data[s_name]['open'] = False
            elif is_hit == -1:
                data[s_name]['open'] = data[s_name].get('last_open', False)
            # if not 'name' in data[s_name]: continue
            if not 'paths' in data[s_name]: continue
            self.__set_safe_state(data[s_name]['paths'], data[s_name]['open'])
        if is_hit == -1:
            self.__write_config(data)
        msg = u'已[%s]宝塔系统加固功能' % self.__state[data['open']]
        public.WriteLog(self.__name, msg)
        is_write = public.ExecShell('bash {}/init.sh status'.format(self.__plugin_path))[0].find("already running") != -1
        if data['open'] and not is_write:
            public.ExecShell('bash {}/init.sh start &'.format(self.__plugin_path))

        if not data['open'] and is_write and get:
            public.ExecShell('bash {}/init.sh stop &'.format(self.__plugin_path))
        return public.returnMsg(True, msg)
    
    # 取deny_list
    def get_deny_list(self):
        deny_file = self.__plugin_path + 'deny.json'
        if not os.path.exists(deny_file): public.writeFile(deny_file, '{}')
        self.__deny_list = json.loads(public.readFile(self.__plugin_path + 'deny.json'))

    # 存deny_list
    def save_deay_list(self):
        deny_file = self.__plugin_path + 'deny.json'
        public.writeFile(deny_file, json.dumps(self.__deny_list))

    # 获取当前SSH禁止IP
    def get_ssh_limit(self, get=None):
        denyConf = public.readFile(self.__deny)
        if not denyConf:
            public.writeFile(self.__deny, '')
            return []
        return re.findall(r"sshd:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):deny", denyConf)
    
    # 删除IP黑名单
    def remove_ssh_limit(self, get):
        if get:
            ip = get.ip
        else:
            ip = self.ip

        if not self.__deny_list: self.get_deny_list()
        if ip in self.__deny_list: del (self.__deny_list[ip])
        self.save_deay_list()
        if not ip in self.get_ssh_limit():
            return public.returnMsg(True, '指定IP黑名单不存在!')

        denyConf = public.readFile(self.__deny).strip()
        while denyConf[-1:] == "\n" or denyConf[-1:] == " ":
            denyConf = denyConf[:-1]
        denyConf = re.sub("\nsshd:" + ip + ":deny\n?", "\n", denyConf)
        public.writeFile(self.__deny, denyConf + "\n")

        msg = u'从SSH-IP黑名单中解封[%s]' % ip
        # print(msg)
        public.WriteLog(self.__name, msg)
        return public.returnMsg(True, '解封成功!')

    

    # 转换时间格式
    def __to_date(self, date_str):
        tmp = re.split('\s+', date_str)
        s_date = str(datetime.now().year) + '-' + self.__months.get(tmp[0]) + '-' + tmp[1] + ' ' + tmp[2]
        time_array = time.strptime(s_date, "%Y-%m-%d %H:%M:%S")
        time_stamp = int(time.mktime(time_array))
        return time_stamp
    


    # 添加SSH目标IP
    def add_ssh_limit(self, get):
        if get:
            ip = get.ip
        else:
            ip = self.ip

        if ip in self.get_ssh_limit():
            return public.returnMsg(False, '指定IP黑名单已存在!')
        denyConf = public.readFile(self.__deny).strip()
        while denyConf[-1:] == "\n" or denyConf[-1:] == " ":
            denyConf = denyConf[:-1]
        denyConf += "\nsshd:" + ip + ":deny\n"
        public.writeFile(self.__deny, denyConf)
        if ip in self.get_ssh_limit():
            msg = u'添加IP[%s]到SSH-IP黑名单' % ip
            public.WriteLog(self.__name, msg)
            self.get_deny_list()
            if not ip in self.__deny_list: self.__deny_list[ip] = 0
            self.save_deay_list()
            return public.returnMsg(True, '添加成功!')
        return public.returnMsg(False, '添加失败!')

    # 删除IP黑名单
    def remove_ssh_limit(self, get):
        if get:
            ip = get.ip
        else:
            ip = self.ip

        if not self.__deny_list: self.get_deny_list()
        if ip in self.__deny_list: del (self.__deny_list[ip])
        self.save_deay_list()
        if not ip in self.get_ssh_limit():
            return public.returnMsg(True, '指定IP黑名单不存在!')

        denyConf = public.readFile(self.__deny).strip()
        while denyConf[-1:] == "\n" or denyConf[-1:] == " ":
            denyConf = denyConf[:-1]
        denyConf = re.sub("\nsshd:" + ip + ":deny\n?", "\n", denyConf)
        public.writeFile(self.__deny, denyConf + "\n")

        msg = u'从SSH-IP黑名单中解封[%s]' % ip
        # print(msg)
        public.WriteLog(self.__name, msg)
        return public.returnMsg(True, '解封成功!')

    # 获取当前SSH禁止IP
    def get_ssh_limit(self, get=None):
        denyConf = public.readFile(self.__deny)
        if not denyConf:
            public.writeFile(self.__deny, '')
            return []
        return re.findall(r"sshd:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):deny", denyConf)

    # 获取deny信息
    def get_ssh_limit_info(self, get):
        self.get_deny_list()
        conf_list = self.get_ssh_limit(None)
        data = []
        for c_ip in conf_list:
            tmp = {}
            tmp['address'] = c_ip
            tmp['end'] = 0
            if c_ip in self.__deny_list: tmp['end'] = self.__deny_list[c_ip]
            data.append(tmp)
        return data

    # 取deny_list
    def get_deny_list(self):
        deny_file = self.__plugin_path + 'deny.json'
        if not os.path.exists(deny_file): public.writeFile(deny_file, '{}')
        self.__deny_list = json.loads(public.readFile(self.__plugin_path + 'deny.json'))

    # 存deny_list
    def save_deay_list(self):
        deny_file = self.__plugin_path + 'deny.json'
        public.writeFile(deny_file, json.dumps(self.__deny_list))

    # SSH日志分析任务
    def ssh_login_task(self, get=None):
        if not self.__log_file:
            log_file = '/var/log/secure'
            if not os.path.exists(log_file):
                log_file = '/var/log/auth.log'
            if not os.path.exists(log_file):
                return
            self.__log_file = log_file

        if not self.__log_file:
            return

        log_size = os.path.getsize(self.__log_file)
        if self.__last_ssh_size == log_size:
            return
        self.__last_ssh_size = log_size
        try:
            self.__config = self.__read_config()
            my_config = self.__config['ssh']
            line_num = my_config['limit_count'] * 20
            secure_logs = public.GetNumLines(self.__log_file, line_num).split('\n')

            total_time = '/dev/shm/ssh_total_time.pl'
            if not os.path.exists(total_time):
                public.writeFile(total_time, str(int(time.time())))
            last_total_time = int(public.readFile(total_time))
            now_total_time = int(time.time())

            self.get_deny_list()
            deny_list = list(self.__deny_list.keys())
            for i in range(len(deny_list)):
                c_ip = deny_list[i]
                if self.__deny_list[c_ip] > now_total_time or self.__deny_list[c_ip] == 0:
                    continue
                self.ip = c_ip
                self.remove_ssh_limit(None)

            ip_total = {}
            for log in secure_logs:
                if log.find('Failed password for') != -1:
                    login_time = self.__to_date(re.search(r'^\w+\s+\d+\s+\d+:\d+:\d+', log).group())
                    if now_total_time - login_time >= my_config['cycle']:
                        continue
                    client_ip = re.search(r'(\d+\.)+\d+', log).group()
                    if client_ip in self.__deny_list: continue
                    if not client_ip in ip_total: ip_total[client_ip] = 0
                    ip_total[client_ip] += 1
                    if ip_total[client_ip] <= my_config['limit_count']:
                        continue
                    self.__deny_list[client_ip] = now_total_time + my_config['limit']
                    # print(u"[%s]在[%s]秒内连续[%s]次登录SSH失败,封锁[%s]秒" % (client_ip,my_config['cycle'], my_config['limit_count'], my_config['limit']))
                    self.save_deay_list()
                    self.ip = client_ip
                    self.add_ssh_limit(None)
                    public.WriteLog(u'SSH登录', u"[%s]在[%s]秒内连续[%s]次登录SSH失败,封锁[%s]秒" % (
                        client_ip, my_config['cycle'], my_config['limit_count'], my_config['limit']))

                elif log.find('Accepted p') != -1:
                    login_time = self.__to_date(re.search(r'^\w+\s+\d+\s+\d+:\d+:\d+', log).group())
                    if login_time < last_total_time: continue
                    client_ip = re.search(r'(\d+\.)+\d+', log).group()
                    login_user = re.findall(r"(\w+)\s+from", log)[0]
                    public.WriteLog(u'SSH登录', u"用户[%s]成功登录服务器,用户IP:[%s],登录时间:[%s]" % (
                        login_user, client_ip, time.strftime('%Y-%m-%d %X', time.localtime(login_time))))
            public.writeFile(total_time, str(int(time.time())))
        except:
            print(public.get_error_info())
        return 'success'
    

    __last_cloud_time = 0  # 上次从云端读取数据的时间
    __last_return_time = 0  # 上次返回结果的时间
    __cloud_timeout = 86400  # 重新从云端更新一次时间间隔
    __return_timeout = 360  # 重新读取文件间隔
    __check_timeout = 3600  # 检查系统进程白名单更新时间

    def get_sys_process(self, get):
        '''
            @name 获取系统进程白名单
            @author hwliang<2021-09-04>
            @return list
        '''
        # 是否直接从属性中获取
        stime = time.time()
        if stime - self.__last_return_time < self.__return_timeout:
            if self.__sys_process: return True
        self.__last_return_time = stime

        # 本地是否存在系统进程白名单文件
        config_file = self.__plugin_path + '/sys_process.json'
        is_force = False
        if not os.path.exists(config_file):
            public.writeFile(config_file, json.dumps([]))
            is_force = True

        # 检查是否有需要更新的系统进程白名单
        if stime - self.__last_cloud_time > self.__check_timeout:
            # 从云端更新系统进程白名单
            mtime = os.path.getmtime(config_file)
            if stime - mtime > self.__cloud_timeout or is_force:
                try:
                    result = public.httpGet(public.get_url() + '/rules/sys_process.json')
                    self.__last_cloud_time = stime
                    process_list = json.loads(result)
                    if isinstance(process_list, list):
                        public.writeFile(config_file, json.dumps(process_list))
                except:
                    print(public.get_error_info())
                    self.__last_cloud_time = stime

        data = json.loads(public.readFile(config_file))
        self.__sys_process = data
        return True
    


    # 取进程白名单列表
    def get_process_white(self, get):
        data = self.__read_config()
        return data['process']['process_white']

    # 取进程关键词
    def get_process_rule(self, get):
        data = self.__read_config()
        return data['process']['process_white_rule']

    # 取进程排除名单
    def get_process_exclude(self, get):
        data = self.__read_config()
        return data['process']['process_exclude']
    
    # 检查白名单
    def check_white(self, name):
        if not self.__elist: self.__elist = self.get_process_exclude(None)
        if not self.__wlist: self.__wlist = self.get_process_white(None)
        if not self.__wslist: self.__wslist = self.get_process_rule(None)
        self.get_sys_process(None)
        if name in ['BT-Panel', 'BT-Task', 'dnf', 'yum', 'apt', 'apt-get', 'baota_coll', 'baota_side', 'grep', 'awk', 'bt', 'python', 'btpython',
                    'node', 'php', 'mysqld', 'httpd', 'nginx', 'wget', 'curl', 'openssl', 'rspamd', 'supervisord', 'BT-Socks5', 'tlsmgr', 'opendkim']:
            return True
        if name in self.__elist: return True
        if name in self.__sys_process: return True
        if name in self.__wlist: return True
        for key in self.__wslist:
            if name.find(key) != -1: return True
        return False

    __limit = 30
    __vmsize = 1048576 * 100
    __wlist = None
    __wslist = None
    __elist = None
    __last_pid_count = 0

    def check_main(self):
        pids = psutil.pids()
        pid_count = len(pids)
        if self.__last_pid_count == pid_count: return
        self.__last_pid_count = pid_count
        try:
            for pid in pids:
                if pid < 1100: continue
                fname = '/proc/' + str(pid) + '/comm'
                if not os.path.exists(fname): continue
                name = public.readFile(fname).strip()
                is_num_name = re.match(r"^\d+$", name)
                if not is_num_name:
                    if self.check_white(name): continue
                try:
                    p = psutil.Process(pid)
                    percent = p.cpu_percent(interval=0.1)
                    vm = p.memory_info().vms
                    if percent > self.__limit or vm > self.__vmsize:
                        cmdline = ' '.join(p.cmdline())
                        if cmdline.find("/tmp/") == -1: continue
                        p.kill()
                        public.WriteLog(self.__name, "已强制结束异常进程:[%s],PID:[%s],CPU:[%s],CMD:[%s]" % (name, pid, percent, cmdline))
                except:
                    print("[" + public.format_date() + "] PID[" + str(pid) + "]")
                    print(public.get_error_info())
                    continue
        except:
            print(public.get_error_info())
            return
    



    # 处理进程检测任务
    def process_task(self):
        if not self.__config: self.__config = self.__read_config()
        if not self.__config: return
        # if not self.__config['open']:
        #     print("未开启系统加固")
        #     return
        print("配置加固检测服务...")
        self.set_open(None, 1,1)
        # close_msg = "未开启SSH防御或异常进程监控功能，无需启动加固检测服务"
        # if not self.__config['ssh']['open'] and self.__config['process']['open']:
        #     print(close_msg)
        #     return
        is_open = 0
        print("启动异常进程和SSH登录检测进程...",end="")
        print("[成功]")
        print("===========================================")
        while True:
            if self.__config['ssh']['open']:
                is_open += 1
                self.ssh_login_task()
            # if self.__config['process']['open']:
            #     is_open += 1
            #     self.check_main()

            if is_open > 60:
                self.__config = self.__read_config()
                is_open = 0
            time.sleep(1)
    
    def uninstall(self):
        self.clear_deny_list()
        self.set_open(None, 0,0)


if __name__ == "__main__":
    c = syssafe_pub()
    if len(sys.argv) == 1:
        c.start()
    else:
        status = int(sys.argv[1])
        if status in [0,1]:
            c.set_open(None, status,status)
        elif status == 2:
            c.uninstall()