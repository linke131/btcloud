# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   宝塔系统加固程序
# +--------------------------------------------------------------------
import os, sys, json, time, re, psutil,pwd,grp,socket
from datetime import datetime

os.chdir('/www/server/panel')
if not 'class/' in sys.path:
    sys.path.insert(0, 'class/')
import public


class syssafe_main:
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
    is_number = re.compile(r'^[-+]?[-0-9]\d*\.\d*|[-+]?\.?[0-9]\d*$')
    __service_ps = {}
    __server_ip = None
    __is_start = False

    # 检测关键目录是否可以被写入文件
    def check_sys_write(self):
        test_file = '/etc/init.d/bt_10000100.pl'
        public.writeFile(test_file, 'True')
        if os.path.exists(test_file):
            os.remove(test_file)
            return True
        return False

    # 获取防护状态
    def get_safe_status(self, get):
        data = self.__read_config()
        if not data['open']:
            if not self.check_sys_write():
                self.set_open(None, 0)
                if not self.check_sys_write():
                    return public.returnMsg(False, '检测到第三方系统加固软件,无需再使用本插件!')
        result = []
        for s_name in data.keys():
            if type(data[s_name]) == bool: continue
            if not 'name' in data[s_name]: continue

            tmp = {}
            tmp['key'] = s_name
            tmp['name'] = data[s_name]['name']
            tmp['open'] = data[s_name]['open']
            tmp['ps'] = data[s_name]['ps']
            result.append(tmp)

        safe_list = {}
        safe_list['open'] = data['open']
        if safe_list['open']:
            if public.ExecShell('bash {}/init.sh status'.format(self.__plugin_path))[0].find("already running") == -1:
                safe_list['open'] = False
                # self.set_open(None,0)
        safe_list['list'] = result
        return safe_list

    # 设置防护状态
    def set_safe_status(self, get):
        data = self.__read_config()
        if data['open'] is False:
            return public.returnMsg(False, "请先打开 系统加固总开关！")
        data[get.s_key]['open'] = not data[get.s_key]['open']
        self.__write_config(data)
        if type(data[get.s_key]) != bool:
            if 'paths' in data[get.s_key]:
                self.__set_safe_state(data[get.s_key]['paths'], data[get.s_key]['open'])
        msg = u'已将[%s]状态设置为[%s]' % (data[get.s_key]['name'], self.__state[data[get.s_key]['open']])
        public.WriteLog(self.__name, msg)

        is_write = public.ExecShell('bash {}/init.sh status'.format(self.__plugin_path))[0].find("already running") != -1
        if data['open'] and not is_write:
            public.ExecShell('bash {}/init.sh start &'.format(self.__plugin_path))
        return public.returnMsg(True, msg)

    # 设置系统加固开关
    def set_open(self, get=None, is_hit=-1,status = -1):
        data = self.__read_config()
        # if not data['open'] and is_hit == 1: return True
        if is_hit != -1:
            data['open'] = is_hit == 0
        if get: 
            if 'status' in get: 
                status = int(get.status)
                data['open'] = status == 1
            else:
                data['open'] = not data['open']
        else:
            data['open'] = status == 1

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

        if not data['open'] and is_write:
            public.ExecShell('bash {}/init.sh stop &'.format(self.__plugin_path))
        return public.returnMsg(True, msg)

    # 获取防护配置
    def get_safe_config(self, get):
        data = self.__read_config()
        data[get.s_key]['paths'] = self.__list_safe_state(data[get.s_key]['paths'])
        return data[get.s_key]

    # 添加防护对象
    def add_safe_path(self, get):
        islink = False
        if get.path[-1] == '/': get.path = get.path[:-1]
        if not os.path.exists(get.path): return public.returnMsg(False, u'指定文件或目录不存在!')
        data = self.__read_config()

        if os.path.islink(get.path):
            islink = True
            get.path = os.readlink(get.path)
            path = 1
            while path:
                path += 1
                if "../" not in get.path: path = 0
                if path == 10: path = 0
                if get.path[:3] == "../": get.path = get.path[3:]
            if get.path[0] != "/": get.path = "/" + get.path

        msg = u'指定文件或目录已经添加过了!'
        if islink: msg = u'您添加的防护对象是软链接，真实路劲[%s]指定文件或目录已经添加过了!' % get.path
        for m_path in data[get.s_key]['paths']:
            if get.path == m_path['path']: return public.returnMsg(False, msg)

        path_info = {}
        path_info['path'] = get.path
        path_info['chattr'] = get.chattr
        path_info['s_mode'] = int(oct(os.stat(get.path).st_mode)[-3:], 8)
        if get.d_mode:
            path_info['d_mode'] = int(get.d_mode, 8)
        else:
            path_info['d_mode'] = path_info['s_mode']

        data[get.s_key]['paths'].insert(0, path_info)
        if 'paths' in data[get.s_key]:
            public.ExecShell('chattr -R -%s %s' % (path_info['chattr'], path_info['path']))
            if data['open']: self.__set_safe_state([path_info], data[get.s_key]['open'])
        self.__write_config(data)
        msg = u'添加防护对象[%s]到[%s]' % (get.path, data[get.s_key]['name'])
        if islink: msg = u'您添加的防护对象是软链接，已添加真实路劲[%s]到[%s]' % (get.path, data[get.s_key]['name'])
        public.WriteLog(self.__name, msg)
        return public.returnMsg(True, msg)

    # 删除防护对象
    def remove_safe_path(self, get):
        data = self.__read_config()
        is_exists = False
        for m_path in data[get.s_key]['paths']:
            if get.path == m_path['path']:
                is_exists = True
                data[get.s_key]['paths'].remove(m_path)
                if os.path.exists(get.path):
                    self.__set_safe_state([m_path], False)
                break

        if not is_exists: return public.returnMsg(False, '指定保护对象不存在!')
        self.__write_config(data)
        if data['open']:
            self.__set_safe_state(data[get.s_key]['paths'], data[get.s_key]['open'])
        msg = u'从[%s]删除保护对象[%s]' % (data[get.s_key]['name'], get.path)
        public.WriteLog(self.__name, msg)
        return public.returnMsg(True, msg)

    # 添加进程白名单
    def add_process_white(self, get):
        data = self.__read_config()
        get.process_name = get.process_name.strip()
        if get.process_name in data['process']['process_white']:
            return public.returnMsg(False, '指定进程名已在白名单')
        data['process']['process_white'].insert(0, get.process_name)
        self.__write_config(data)
        msg = u'添加进程名[%s]到进程白名单' % get.process_name
        public.WriteLog(self.__name, msg)
        public.ExecShell('bash {}/init.sh restart'.format(self.__plugin_path))
        return public.returnMsg(True, msg)

    # 删除进程白名单
    def remove_process_white(self, get):
        data = self.__read_config()
        get.process_name = get.process_name.strip()
        if not get.process_name in data['process']['process_white']:
            return public.returnMsg(False, '指定进程名不存在')
        data['process']['process_white'].remove(get.process_name)
        self.__write_config(data)
        msg = u'从进程白名单删除进程名[%s]' % get.process_name
        public.WriteLog(self.__name, msg)
        public.ExecShell('bash {}/init.sh restart'.format(self.__plugin_path))
        return public.returnMsg(True, msg)

    # 添加进程关键词白名单
    def add_process_rule(self, get):
        data = self.__read_config()
        get.process_key = get.process_key.strip()
        if get.process_key in data['process']['process_rule']:
            return public.returnMsg(False, '指定关键词已在白名单')
        data['process']['process_rule'].insert(0, get.process_key)
        self.__write_config(data)
        msg = u'添加关键词[%s]到进程关键词白名单' % get.process_key
        public.WriteLog(self.__name, msg)
        return public.returnMsg(True, msg)

    # 删除进程关键词白名单
    def remove_process_rule(self, get):
        data = self.__read_config()
        get.process_key = get.process_key.strip()
        if not get.process_key in data['process']['process_rule']:
            return public.returnMsg(False, '指定关键词不存在')
        data['process']['process_rule'].remove(get.process_key)
        self.__write_config(data)
        msg = u'从进程关键词白名单删除关键词[%s]' % get.process_key
        public.WriteLog(self.__name, msg)
        return public.returnMsg(True, msg)

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

    # 取SSH加固策略
    def get_ssh_config(self, get):
        data = self.__read_config()
        return data['ssh']

    # 保存SSH加固策略
    def save_ssh_config(self, get):
        get.cycle = int(get.cycle)
        get.limit = int(get.limit)
        get.limit_count = int(get.limit_count)
        if get.cycle > get.limit:
            return public.returnMsg(False, '封锁时间不能小于检测周期!')
        if get.cycle < 30 or get.cycle > 1800:
            return public.returnMsg(False, '检测周期的值必需在30 - 1800秒之间!')
        if get.limit < 60: return public.returnMsg(False, '封锁时间不能小于60秒')
        if get.limit_count < 3 or get.limit_count > 100:
            return public.returnMsg(False, '检测阈值必需在3 - 100秒之间!')
        data = self.__read_config()
        data['ssh']['cycle'] = get.cycle
        data['ssh']['limit'] = get.limit
        data['ssh']['limit_count'] = get.limit_count
        self.__write_config(data)
        msg = u'修改SSH策略: 在[%s]秒内,登录错误[%s]次,封锁[%s]秒' % (data['ssh']['cycle'], data['ssh']['limit_count'], data['ssh']['limit'])
        public.WriteLog(self.__name, msg)
        public.ExecShell('bash {}/init.sh restart'.format(self.__plugin_path))
        return public.returnMsg(True, '配置已保存!')

    # 获取SSH登录日志
    def get_ssh_login_logs(self, get):
        import page
        page = page.Page()
        count = public.M('logs').where('type=?', (u'SSH登录',)).count()
        limit = 12
        info = {}
        info['count'] = count
        info['row'] = limit
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        info['uri'] = {}
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs
        data = {}
        data['page'] = page.GetPage(info, '1,2,3,4,5')
        data['data'] = public.M('logs').where('type=?', (u'SSH登录',)).order('id desc').limit(str(page.SHIFT) + ',' + str(page.ROW)).field(
            'log,addtime').select()
        return data

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

    # 存deny_list
    def save_deay_list(self):
        deny_file = self.__plugin_path + 'deny.json'
        public.writeFile(deny_file, json.dumps(self.__deny_list))

    # 取操作日志
    def get_logs(self, get):
        import page
        page = page.Page()
        count = public.M('logs').where('type=? or type=?', (self.__name, u'SSH登录')).count()
        limit = 12
        info = {}
        info['count'] = count
        info['row'] = limit
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        info['uri'] = {}
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs
        data = {}
        data['page'] = page.GetPage(info, '1,2,3,4,5')
        data['data'] = public.M('logs').where('type=? or type=?', (self.__name, u'SSH登录')).order('id desc').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).field('log,addtime').select()
        return data

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

    # 取文件或目录锁定状态
    def __get_path_state(self, path):
        if not os.path.exists(path): return 'i'
        if os.path.isfile(path):
            shell_cmd = "lsattr %s|awk '{print $1}'" % path
        else:
            shell_cmd = "lsattr {}/ |grep '{}$'|awk '{{print $1}}'".format(os.path.dirname(path), path)
        result = public.ExecShell(shell_cmd)[0]
        if result.find('-i-') != -1: return 'i'
        if result.find('-a-') != -1: return 'a'
        return False

    # 遍历当前防护状态
    def __list_safe_state(self, paths):
        result = []
        for i in range(len(paths)):
            if not os.path.exists(paths[i]['path']): continue
            if os.path.islink(paths[i]['path']): continue
            mstate = self.__get_path_state(paths[i]['path'])
            paths[i]['state'] = mstate == paths[i]['chattr']
            paths[i]['s_mode'] = oct(paths[i]['s_mode'])
            paths[i]['d_mode'] = oct(paths[i]['d_mode'])
            result.append(paths[i])
        return result

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
                        if cmdline.find('/www/server/cron') != -1: continue
                        if cmdline.find('/www/server') != -1: continue
                        if name.find('kworker') != -1 or name.find('bt_') == 0:
                            continue
                        p.kill()
                        public.WriteLog(self.__name, "已强制结束异常进程:[%s],PID:[%s],CPU:[%s],CMD:[%s]" % (name, pid, percent, cmdline))
                except:
                    print(public.get_error_info())
                    continue
        except:
            print(public.get_error_info())
            return

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

    def get_log_title(self, log_name):
        '''
            @name 获取日志标题
            @author hwliang<2021-09-03>
            @param log_name<string> 日志名称
            @return <string> 日志标题
        '''
        log_name = log_name.replace('.1', '')
        if log_name in ['auth.log', 'secure'] or log_name.find('auth.') == 0:
            return '授权日志'
        if log_name in ['dmesg'] or log_name.find('dmesg') == 0:
            return '内核缓冲区日志'
        if log_name in ['syslog'] or log_name.find('syslog') == 0:
            return '系统警告/错误日志'
        if log_name in ['btmp']:
            return '失败的登录记录'
        if log_name in ['utmp', 'wtmp']:
            return '登录和重启记录'
        if log_name in ['lastlog']:
            return '用户最后登录'
        if log_name in ['yum.log']:
            return 'yum包管理器日志'
        if log_name in ['anaconda.log']:
            return 'Anaconda日志'
        if log_name in ['dpkg.log']:
            return 'dpkg日志'
        if log_name in ['daemon.log']:
            return '系统后台守护进程日志'
        if log_name in ['boot.log']:
            return '启动日志'
        if log_name in ['kern.log']:
            return '内核日志'
        if log_name in ['maillog', 'mail.log']:
            return '邮件日志'
        if log_name.find('Xorg') == 0:
            return 'Xorg日志'
        if log_name in ['cron.log']:
            return '定时任务日志'
        if log_name in ['alternatives.log']:
            return '更新替代信息'
        if log_name in ['debug']:
            return '调试信息'
        if log_name.find('apt') == 0:
            return 'apt-get相关日志'
        if log_name.find('installer') == 0:
            return '系统安装相关日志'
        if log_name in ['messages']:
            return '综合日志'
        return '{}日志'.format(log_name.split('.')[0])

    def get_sys_logfiles(self, get):
        '''
            @name 获取系统日志文件列表
            @author hwliang<2021-09-02>
            @param get<dict_obj>
            @return list
        '''
        log_dir = '/var/log'
        log_files = []
        for log_file in os.listdir(log_dir):
            if log_file[-3:] in ['.gz', '.xz']: continue
            if log_file in ['.', '..', 'faillog', 'fontconfig.log', 'unattended-upgrades', 'tallylog']:
                continue
            filename = os.path.join(log_dir, log_file)
            if os.path.isfile(filename):
                file_size = os.path.getsize(filename)
                if not file_size: continue
                tmp = {'name': log_file, 'size': file_size, 'log_file': filename, 'title': self.get_log_title(log_file),
                       'uptime': os.path.getmtime(filename)}

                log_files.append(tmp)
            else:
                for next_name in os.listdir(filename):
                    if next_name[-3:] in ['.gz', '.xz']: continue
                    next_file = os.path.join(filename, next_name)
                    if not os.path.isfile(next_file): continue
                    file_size = os.path.getsize(next_file)
                    if not file_size: continue
                    log_name = '{}/{}'.format(log_file, next_name)
                    tmp = {'name': log_name, 'size': file_size, 'log_file': next_file, 'title': self.get_log_title(log_name),
                           'uptime': os.path.getmtime(next_file)}
                    log_files.append(tmp)
        log_files = sorted(log_files, key=lambda x: x['name'], reverse=True)
        return log_files

    def get_sys_log(self, get):
        '''
            @name  获取指定系统日志
            @author hwliang<2021-09-02>
            @param get<dict_obj>
            @return list
        '''
        if get.log_name in ['wtmp', 'btmp', 'utmp'] or get.log_name.find('wtmp') == 0 or get.log_name.find('btmp') == 0 or get.log_name.find(
                'utmp') == 0:
            return self.get_last(get)

        if get.log_name.find('lastlog') == 0:
            return self.get_lastlog(get)

        if get.log_name.find('sa/sa') == 0:
            if get.log_name.find('sa/sar') == -1:
                return public.ExecShell("sar -f /var/log/{}".format(get.log_name))[0]
        log_dir = '/var/log'
        log_file = log_dir + '/' + get.log_name
        if not os.path.exists(log_file):
            return public.returnMsg(False, '日志文件不存在!')
        result = public.GetNumLines(log_file, 1000)
        log_list = []
        is_string = True
        for _line in result.split("\n"):
            if not _line.strip(): continue
            if get.log_name.find('sa/sa') == -1:
                if _line[:3] in self.__months:
                    _msg = _line[16:]
                    _tmp = _msg.split(": ")
                    _act = ''
                    if len(_tmp) > 1:
                        _act = _tmp[0]
                        _msg = _tmp[1]
                    else:
                        _msg = _tmp[0]
                    _line = {"时间": public.xssencode2(self.__to_date4(_line[:16].strip())), "角色": public.xssencode2(_act),
                             "事件": public.xssencode2(_msg)}
                    is_string = False
                elif _line[:2] in ['19', '20', '21', '22', '23', '24']:
                    _msg = _line[19:]
                    _tmp = _msg.split(" ")
                    _act = _tmp[1]
                    _msg = ' '.join(_tmp[2:])
                    _line = {"时间": public.xssencode2(_line[:19].strip()), "角色": public.xssencode2(_act), "事件": public.xssencode2(_msg)}
                    is_string = False
                elif get.log_name.find('alternatives') == 0:
                    _tmp = _line.split(": ")
                    _last = _tmp[0].split(" ")
                    _act = _last[0]
                    _msg = ' '.join(_tmp[1:])
                    _line = {"时间": public.xssencode2(' '.join(_last[1:]).strip()), "角色": public.xssencode2(_act), "事件": public.xssencode2(_msg)}
                    is_string = False
                else:
                    if not is_string:
                        if type(_line) != dict: continue

            log_list.append(_line)
        try:
            # if len(log_list) > 1:
            #     if type(log_list[0]) != type(log_list[1]):
            #         del(log_list[0])
            # log_list = sorted(log_list,key=lambda x:x['时间'],reverse=True)
            # return log_list

            _string = []
            _dict = []
            _list = []
            for _line in log_list:
                if isinstance(_line, str):
                    _string.append(public.xssencode2(_line.strip()))
                elif isinstance(_line, dict):
                    _dict.append(_line)
                elif isinstance(_line, list):
                    _list.append(_line)
                else:
                    continue
            _str_len = len(_string)
            _dict_len = len(_dict)
            _list_len = len(_list)
            if _str_len > _dict_len + _list_len:
                return "\n".join(_string)
            elif _dict_len > _str_len + _list_len:
                return _dict
            else:
                return _list

        except:
            return '\n'.join(log_list)

    def __to_date2(self, date_str):
        tmp = date_str.split()
        s_date = str(tmp[-1]) + '-' + self.__months.get(tmp[1], tmp[1]) + '-' + tmp[2] + ' ' + tmp[3]
        return s_date

    def __to_date3(self, date_str):
        tmp = date_str.split()
        s_date = str(datetime.now().year) + '-' + self.__months.get(tmp[1], tmp[1]) + '-' + tmp[2] + ' ' + tmp[3]
        return s_date

    def __to_date4(self, date_str):
        tmp = date_str.split()
        s_date = str(datetime.now().year) + '-' + self.__months.get(tmp[0], tmp[0]) + '-' + tmp[1] + ' ' + tmp[2]
        return s_date

    def get_lastlog(self, get):
        '''
            @name 获取lastlog日志
            @author hwliang<2021-09-02>
            @param get<dict_obj>
            @return list
        '''
        cmd = '''LANG=en_US.UTF-8
lastlog|grep -v Username'''
        result = public.ExecShell(cmd)
        lastlog_list = []
        for _line in result[0].split("\n"):
            if not _line: continue
            tmp = {}
            sp_arr = _line.split()
            tmp['用户'] = sp_arr[0]
            # tmp['_line'] = _line
            if _line.find('Never logged in') != -1:
                tmp['最后登录时间'] = '0'
                tmp['最后登录来源'] = '-'
                tmp['最后登录端口'] = '-'
                lastlog_list.append(tmp)
                continue
            tmp['最后登录来源'] = sp_arr[2]
            tmp['最后登录端口'] = sp_arr[1]
            tmp['最后登录时间'] = self.__to_date2(' '.join(sp_arr[3:]))

            lastlog_list.append(tmp)
        lastlog_list = sorted(lastlog_list, key=lambda x: x['最后登录时间'], reverse=True)
        for i in range(len(lastlog_list)):
            if lastlog_list[i]['最后登录时间'] == '0':
                lastlog_list[i]['最后登录时间'] = '从未登录过'
        return lastlog_list

    def get_last(self, get):
        '''
            @name 获取用户会话日志
            @author hwliang<2021-09-02>
            @param get<dict_obj>
            @return list
        '''
        cmd = '''LANG=en_US.UTF-8
last -n 1000 -x -f {}|grep -v 127.0.0.1|grep -v " begins"'''.format('/var/log/' + get.log_name)
        result = public.ExecShell(cmd)
        lastlog_list = []
        for _line in result[0].split("\n"):
            if not _line: continue
            tmp = {}
            sp_arr = _line.split()
            tmp['用户'] = sp_arr[0]
            if sp_arr[0] == 'runlevel':
                tmp['来源'] = sp_arr[4]
                tmp['端口'] = ' '.join(sp_arr[1:4])
                tmp['时间'] = self.__to_date3(' '.join(sp_arr[5:])) + ' ' + ' '.join(sp_arr[-2:])
            elif sp_arr[0] in ['reboot', 'shutdown']:
                tmp['来源'] = sp_arr[3]
                tmp['端口'] = ' '.join(sp_arr[1:3])
                if sp_arr[-3] == '-':
                    tmp['时间'] = self.__to_date3(' '.join(sp_arr[4:])) + ' ' + ' '.join(sp_arr[-3:])
                else:
                    tmp['时间'] = self.__to_date3(' '.join(sp_arr[4:])) + ' ' + ' '.join(sp_arr[-2:])
            elif sp_arr[1] in ['tty1', 'tty', 'tty2', 'tty3', 'hvc0', 'hvc1', 'hvc2'] or len(sp_arr) == 9:
                tmp['来源'] = ''
                tmp['端口'] = sp_arr[1]
                tmp['时间'] = self.__to_date3(' '.join(sp_arr[2:])) + ' ' + ' '.join(sp_arr[-3:])
            else:
                tmp['来源'] = sp_arr[2]
                tmp['端口'] = sp_arr[1]
                tmp['时间'] = self.__to_date3(' '.join(sp_arr[3:])) + ' ' + ' '.join(sp_arr[-3:])

            # tmp['_line'] = _line
            lastlog_list.append(tmp)
        # lastlog_list = sorted(lastlog_list,key=lambda x:x['时间'],reverse=True)
        return lastlog_list

    # 开始处理
    def start(self):
        try:
            # import threading
            # p = threading.Thread(target=self.ssh_task)
            # p.setDaemon(True)
            # p.start()
            self.process_task()
        except:
            print('【{}】系统加固监控进程已关闭'.format(public.getDate()))

    # 处理进程检测任务
    def process_task(self):
        # time.sleep(600)
        if not self.__config: self.__config = self.__read_config()
        if not self.__config: return
        # if not self.__config['open']:
        #     print("未开启系统加固")
        #     return
        self.set_open(None, 1)
        # close_msg = "未开启SSH防御或异常进程监控功能，无需启动加固检测服务"
        # if not self.__config['ssh']['open'] and self.__config['process']['open']:
        #     print(close_msg)
        #     return
        is_open = 0
        while True:
            if self.__config['ssh']['open']:
                is_open += 1
                self.ssh_login_task()
            if self.__config['process']['open']:
                is_open += 1
                self.check_main()

            if is_open > 60:
                self.__config = self.__read_config()
                is_open = 0
            time.sleep(1)

    # 处理SSH日志分析任务
    def ssh_task(self):
        if not self.__config: self.__config = self.__read_config()
        while True:
            if self.__config['ssh']['open']: self.ssh_login_task()
            time.sleep(1)


    def ssh_restart(self):
        '''
            @name 重启SSH服务
            @return bool
        '''

        if os.path.exists('/etc/init.d/sshd'):
            public.ExecShell('/etc/init.d/sshd restart')
        elif os.path.exists('/etc/init.d/ssh'):
            public.ExecShell('/etc/init.d/ssh restart')
        else:
            public.ExecShell('systemctl restart sshd.service')
        
        return True


    def get_ssh_config_file(self):
        '''
            @name 获取SSH配置文件路径
            @author hwliang
            @return dict
        '''
        ssh_config_file = '{}/config/ssh_config.json'.format(self.__plugin_path)
        if not os.path.exists(ssh_config_file):
            return {}

        try:
            ssh_config = json.loads(public.readFile(ssh_config_file))
            return ssh_config
        except:
            return {}


    # 获取SSH配置项
    def get_ssh_config_options(self,get):
        '''
            @name 获取SSH配置项
            @author hwliang
            @return dict {
                'port':{
                    'name':'端口',
                    'value':22,
                    'default':22
                    'very': 0,
                    'ps': '建议使用10001-65535之间的端口'
                }
                ....
            }
        '''
        ssh_config_dict = self.get_ssh_config_file()
        ssh_config_file = '/etc/ssh/sshd_config'
        if not os.path.exists(ssh_config_file): return {}
        sshd_config = public.readFile(ssh_config_file)
        is_NaN = re.compile(r"[\d\-]+")
        ssh_keys = ssh_config_dict.keys()
        for _line in sshd_config.split("\n"):
            if not _line: continue
            if _line[0] == '#': continue
            tmp = _line.split()
            if len(tmp) < 2: continue
            if tmp[0] in ssh_keys:
                if is_NaN.match(tmp[1]):
                    ssh_config_dict[tmp[0]]['value'] = int(tmp[1])
                else:
                    ssh_config_dict[tmp[0]]['value'] = tmp[1]     
        return public.returnMsg(True,ssh_config_dict)
    
    # 设置SSH配置项
    def set_ssh_config_options(self,get):
        '''
            @name 设置SSH配置项
            @param get<dict_obj>{
                'Port': '22',
                'PermitRootLogin': 'yes',
                'PasswordAuthentication': 'yes',
                'PermitEmptyPasswords': 'no',
                'MaxAuthTries': '6',
                'MaxSessions': '10',
                'ClientAliveInterval': '0',
                'ClientAliveCountMax': '3',
                'LoginGraceTime': '120',
                'LogLevel': 'INFO',
                'Protocol': '2'
            }
            @return dict
        '''

        ssh_config_dict = self.get_ssh_config_file()
        for _key in ssh_config_dict.keys():
            if _key not in get: return public.returnMsg(False,'缺少参数:{}'.format(_key))

        ssh_config_file = '/etc/ssh/sshd_config'
        if not os.path.exists(ssh_config_file): return public.returnMsg(False,'配置文件不存在')

        ssh_config = public.readFile(ssh_config_file)
        
        for _key in ssh_config_dict.keys():
            ssh_config = re.sub(r'^\s*#?\s*{}.*'.format(_key), '{} {}'.format(_key,get[_key]), ssh_config, flags=re.M)
        
        attr = self.unlock_file(ssh_config_file)
        public.writeFile(ssh_config_file,ssh_config)
        self.lock_file(ssh_config_file,attr)
        self.ssh_restart()

        import firewalls
        get.port = get['Port']
        firewalls.firewalls().SetSshPort(get)
        public.WriteLog(self.__name,"修改SSH配置项")
        return public.returnMsg(True,'设置成功')



    

    def get_password_expire(self):
        '''
            @name 获取密码过期时间
            @author hwliang
            @return int
        '''
        login_defs = '/etc/login.defs'
        if not os.path.exists(login_defs): return 0
        for _line in public.readFile(login_defs).split("\n"):
            if not _line: continue
            if _line[0] == '#': continue
            tmp = _line.split()
            if len(tmp) < 2: continue
            if tmp[0] in ['PASS_MAX_DAYS']:
                try:
                    if tmp[1].find('-') == -1:
                        res = int(tmp[1])
                    else:
                        res = 99999
                except:
                    res = 99999
                return res
        return 0
    
    def set_password_expire(self,expire):
        '''
            @name 设置密码过期时间
            @param expire int 过期时间(天)
            @return bool
        '''
        login_defs = '/etc/login.defs'
        if not os.path.exists(login_defs): return False
        login_defs_body = public.readFile(login_defs)
        if not login_defs_body: return False
        body_list = login_defs_body.split("\n")
        for _line in body_list:
            if not _line: continue
            if _line[0] == '#': continue
            tmp = _line.split()
            if len(tmp) < 2: continue
            if tmp[0] in ['PASS_MAX_DAYS']:
                body_list[body_list.index(_line)] = "{}\t{}\n".format(tmp[0],expire)
                attr = self.unlock_file(login_defs)
                public.writeFile(login_defs,"\n".join(body_list))
                public.ExecShell("chage -M {} root".format(expire))  # 设置root密码过期时间
                self.lock_file(login_defs,attr)
                public.WriteLog(self.__name,"设置密码过期时间为:{}天".format(expire))
                return True
        return False

    

    def get_pma_config(self):
        '''
            @name 获取PMA配置信息
            @author hwliang
            @return dict
        '''
        config_file = "{}/config/pma_config.json".format(self.__plugin_path)
        body = public.readFile(config_file)
        if not body: return {}
        try:
            return json.loads(body)
        except:
            return {}
        
    def get_ssh_password_auth(self,get):
        '''
            @name 获取SSH帐用密码复杂度配置
            @author hwliang
            @return dict{
                retry=N：指定密码验证失败后重试的次数。N 是一个整数值，默认为3次。
                difok=N：指定在新密码中至少有 N 个字符不同于旧密码。这可用于防止用户只是轻微更改密码而不选择更强的密码。
                minlen=N：指定密码的最小长度为 N 个字符。
                dcredit=N：指定数字字符（0-9）的最小数量为 N。
                ucredit=N：指定大写字母的最小数量为 N。
                lcredit=N：指定小写字母的最小数量为 N。
                ocredit=N：指定非字母数字字符（例如符号）的最小数量为 N。
                minclass=N：指定密码中必须包含的字符类的最小数目为 N。字符类是数字、大写字母、小写字母和其他字符的组合。
                maxrepeat=N：指定在密码中允许重复字符的最大次数为 N。
                maxsequence=N：指定允许的最大字符序列长度为 N。这是防止使用连续字符的常见模式，例如"12345"或"abcd"。
                maxclassrepeat=N：指定在密码中允许重复字符类的最大次数为 N。字符类是数字、大写字母、小写字母和其他字符的组合。
                gecoscheck=N：指定是否检查密码中的用户名和全名。如果启用此功能，则密码中的用户名或全名将被拒绝。
            }
        '''
        ssh_password_auth = self.get_pma_config()
        _auth_file = '/etc/pam.d/system-auth'
        if not os.path.exists(_auth_file): 
            _auth_file='/etc/pam.d/common-password'
            if not os.path.exists(_auth_file): return public.returnMsg(False,ssh_password_auth)
        

        is_NaN = re.compile(r"[\d\-]+")
        for _line in public.readFile(_auth_file).split("\n"):
            if not _line: continue
            if _line[0] == '#': continue
            tmp = _line.split()
            if len(tmp) < 2: continue
            if tmp[0] in ['password']:
                j = 0
                for i in range(len(tmp)):
                    if tmp[i] in ['pam_pwquality.so','pam_unix.so']:
                        j = i
                        break

                if tmp[j] in ['pam_pwquality.so','pam_unix.so']:
                    for _tmp in tmp[j+1:]:
                        _tmp = _tmp.split('=')
                        if _tmp[0] not in ssh_password_auth:
                            continue
                        # 处理无值参数的情况
                        if len(_tmp) < 2:
                            ssh_password_auth[_tmp[0]]['value'] = 1
                            continue
                        # 整数值处理
                        if is_NaN.match(_tmp[1]): _tmp[1] = int(_tmp[1])
                        if _tmp[0] in ssh_password_auth: 
                            ssh_password_auth[_tmp[0]]['value'] = _tmp[1]

        if 'PASS_MAX_DAYS' in ssh_password_auth:
            ssh_password_auth['PASS_MAX_DAYS']['value'] = self.get_password_expire()
        
            
        return public.returnMsg(True,ssh_password_auth)
    

    def set_pam_pwquality(self,get):
        '''
            @name 设置SSH帐用密码复杂度配置
            @author hwliang
            @param get <dict_obj>{
                retry: <int> 重试次数 0为不限制
                difok: <int> 最小不同字符数
                minlen: <int> 最小长度
                dcredit: <int> 数字字符数
                ucredit: <int> 大写字符数
                ocredit: <int> 特殊字符数
                lcredit: <int> 小写字符数
                minclass: <int> 最小类别数
                gecoscheck: <int> 是否检查用户名
                maxrepeat: <int> 最大重复字符数
                maxclassrepeat: <int> 最大类别重复字符数
                maxsequence: <int> 最大字符序列长度
            }
            @return dict
        '''

        # 检查参数
        pma_list = ['retry','difok','minlen','dcredit','ucredit','ocredit','lcredit','minclass','gecoscheck','maxrepeat','maxclassrepeat','maxsequence']
        is_NaN = re.compile(r"[\d\-]+")
        for _key in pma_list:
            if not _key in get: return public.returnMsg(False,'参数错误!')
            if not is_NaN.match(str(get[_key])): return public.returnMsg(False,'参数错误!')
            if int(get[_key]) < 0: return public.returnMsg(False,'参数错误!')
        
        # 检查配置文件
        _auth_file = '/etc/security/pwquality.conf'
        if not os.path.exists(_auth_file): return public.returnMsg(False,'配置文件不存在!')
        _auth_conf = public.readFile(_auth_file)
        if not _auth_conf: return public.returnMsg(False,'配置文件不存在!')

        # 设置配置
        for _key in pma_list:
            _auth_conf = re.sub(r"^\s*#?\s*%s\s*=\s*\S+" % _key,"%s = %s" % (_key,get[_key]),_auth_conf,flags=re.M)
        
        # 写入配置
        attr = self.unlock_file(_auth_file)
        public.writeFile(_auth_file,_auth_conf)
        self.lock_file(_auth_file,attr)
        
        return public.returnMsg(True,'设置成功!')


    def set_ssh_password_auth(self,get):
        '''
            @name 设置SSH帐用密码复杂度配置
            @author hwliang
            @param get <dict_obj>{
                retry: <int> 重试次数 0为不限制
                difok: <int> 最小不同字符数
                minlen: <int> 最小长度
                dcredit: <int> 数字字符数
                ucredit: <int> 大写字符数
                ocredit: <int> 特殊字符数
                lcredit: <int> 小写字符数
                minclass: <int> 最小类别数
                gecoscheck: <int> 是否检查用户名是否在密码中 0.否 1.是
                maxrepeat: <int> 最大重复字符数，防止用户使用1111111111这样的密码 0.不限制
                maxclassrepeat: <int> 最大连续重复字符数，防止用户使用1111111111这样的密码 0.不限制
                maxsequence: <int> 最大字符序列长度，防止用户使用1234567890这样的密码 0.不限制
                enforce_for_root: <int> 是否强制root用户也使用此配置 0.否 1.是
                remember: <int> 密码至少多少次内不能重复
                PASS_MAX_DAYS: <int> 密码过期时间
            }
            @return dict
        '''
        # 检查参数
        is_NaN = re.compile(r"[\d\-]+")
        pma_config = self.get_pma_config()
        pma_list = pma_config.keys()
        for _key in pma_list:
            if _key not in get: return public.returnMsg(False,'缺少参数: ' + _key)
            if not is_NaN.match(get[_key]): return public.returnMsg(False,'不兼容的参数值，只支持整数')

        # centos 7/8/9
        _auth_file = '/etc/pam.d/system-auth'
        if not os.path.exists(_auth_file): 
            _auth_file='/etc/pam.d/common-password' # ubuntu 16/18/20/22、debian 9/10/11
            if not os.path.exists(_auth_file): return public.returnMsg(False,'不兼容的操作系统，目前兼容: CentOS 7/8/9、Ubuntu 16/18/20/22、Debian 9/10/11')
        
        # 读取配置文件
        _conf = public.readFile(_auth_file)
        if not _conf: return public.returnMsg(False,'配置文件读取失败')
        _conf_list = _conf.split("\n")

        # 要查找的模块列表
        find_so_list = ['pam_pwquality.so','pam_unix.so']
        
        # 初始化标记
        is_pam_pwquality = False
        is_pam_unix = False
        pam_pwquality_modify_list = {}
        for pk in pma_list:
            pam_pwquality_modify_list[pk] = False
            
        for _line in _conf_list:
            if not _line: continue # 跳过空行
            if _line[0] == '#': continue  # 跳过注释行

            tmp = _line.split()
            if len(tmp) < 2: continue # 跳过无效行
            
            if tmp[0] in ['password']: # 找到password主模块

                # 定位模块位置
                j = 0
                for i in range(len(tmp)):
                    if tmp[i] in find_so_list:
                        j = i
                        break
                
                # 匹配目标模块
                if tmp[j] in find_so_list:
                    # 标记找到的模块
                    if tmp[j] == find_so_list[0]: is_pam_pwquality = True
                    if tmp[j] == find_so_list[1]: is_pam_unix = True

                    # 遍历模块参数
                    for _tmp in tmp[j+1:]:
                        _arr = _tmp.split('=')
                        if len(_arr) < 2: continue # 跳过无值参数

                        # 匹配要修改的参数
                        if _arr[0] in get: 
                            if _arr[0] in ['PASS_MAX_DAYS']: continue
                            
                            # 修改参数值    
                            tmp[tmp.index(_tmp)] = _arr[0] + '=' + str(get[_arr[0]])
                            if _arr[0] in pam_pwquality_modify_list: pam_pwquality_modify_list[_arr[0]] = True

                    # 补充缺失的参数
                    if tmp[j] == find_so_list[0]:
                        for _key in pam_pwquality_modify_list:
                            if _key in ['PASS_MAX_DAYS']: continue
                            if _key in ['enforce_for_root']: # 处理没有值的参数
                                if not pam_pwquality_modify_list[_key]:
                                    if int(get[_key]) == 1:
                                        if _key in tmp: continue
                                        tmp.append(_key)
                                    else:
                                        if _key in tmp: tmp.remove(_key)
                                    pam_pwquality_modify_list[_key] = True
                            else:
                                if not pam_pwquality_modify_list[_key]: 
                                    # 标记是否修改了remember参数
                                    tmp.append('{}={}'.format(_key,get[_key]))
                                    pam_pwquality_modify_list[_key] = True

                        
                    # 将修改的结果放回配置列表
                    _conf_list[_conf_list.index(_line)] = ' '.join(tmp)
                    public.print_log(tmp)

        # 如果没有找到模块，则添加模块
        if not is_pam_pwquality:
            _conf_list.append('password    requisite     pam_pwquality.so try_first_pass local_users_only authtok_type= retry={} difok={} minlen={} dcredit={} ucredit={} ocredit={} lcredit={} enforce_for_root'.format(
                get['retry'],get['difok'],get['minlen'],get['dcredit'],get['ucredit'],get['ocredit'],get['lcredit']
            ))
        if not is_pam_unix:
            _conf_list.append('password    sufficient    pam_unix.so sha512 shadow nullok try_first_pass use_authtok remember={}'.format(get['remember']))
        

        # 写入配置文件
        attr = self.unlock_file(_auth_file)
        public.writeFile(_auth_file,"\n".join(_conf_list))
        self.lock_file(_auth_file,attr)
        # 设置密码策略配置文件
        self.set_pam_pwquality(get)

        # 设置密码过期时间
        if 'PASS_MAX_DAYS' in get:
            self.set_password_expire(get.PASS_MAX_DAYS)
        public.WriteLog(self.__name,"修改SSH密码复杂度配置!")
        return public.returnMsg(True,'设置成功')
            
        
    def to_umask(self,mode):
        '''
            @name 将权限值转换为umask值
            @param mode 权限值
            @return string
        '''
        mode = int(mode)
        if mode < 0 or mode > 777: return '022'
        umask = str(777 - mode)
        if len(umask) < 3: umask = '0' + umask
        return umask
    
    def to_mode(self,umask):
        '''
            @name 将umask值转换为权限值
            @param umask umask值
            @return string
        '''
        umask = int(umask)
        if umask < 0 or umask > 777: return '755'
        return str(777 - umask)
    

    def get_umask(self,get):
        '''
            @name 获取umask值
            @author hwliang
            @return dict
        '''
        umask_dict = {
            "name": "默认文件权限",
            "value": "755",
            "mask": "022",
            "default": "755",
            "default_mask": "022",
            "very": "750",
            "very_mask": "027",
            "ps": "修改文件和目录的缺省权限(UMASK)，建议设置为750，<span style='color:red;'>注意：在创建目录时才能完整使用缺省权限，创建文件时将自动移除所有执行权限的，修改后需重新登录SSH终端才生效，通过面板创建文件不受此设置影响</span>"
        }
        umask_file = '/etc/profile'
        if not os.path.exists(umask_file): return public.returnMsg(False,'不兼容的操作系统，目前兼容: CentOS 7/8/9、Ubuntu 16/18/20/22、Debian 9/10/11')

        # 读取配置文件
        _conf = public.readFile(umask_file)
        if not _conf: return public.returnMsg(False,'配置文件读取失败')

        # 匹配umask值
        _conf_list = _conf.split("\n")
        for _line in _conf_list:
            if not _line: continue
            if _line[0] == '#': continue
            tmp = _line.split()
            if len(tmp) < 2: continue
            if tmp[0] in ['umask']:
                umask_dict['mask'] =  tmp[1]
                umask_dict['value'] = self.to_mode(tmp[1])
                break
        
        return public.returnMsg(True,umask_dict)
    

    def set_umask(self,get):
        '''
            @name 设置umask值
            @param get.umask string umask值
            @return dict
        '''
        umask_file = '/etc/profile'
        if not os.path.exists(umask_file): return public.returnMsg(False,'不兼容的操作系统，目前兼容: CentOS 7/8/9、Ubuntu 16/18/20/22、Debian 9/10/11')

        # 读取配置文件
        _conf = public.readFile(umask_file)
        if not _conf: return public.returnMsg(False,'配置文件读取失败')

        # 匹配umask值
        _conf_list = _conf.split("\n")
        _is_set = False
        for _line in _conf_list:
            if not _line: continue
            if _line[0] == '#': continue
            tmp = _line.split()
            if len(tmp) < 2: continue
            if tmp[0] in ['umask']:
                _conf_list[_conf_list.index(_line)] = 'umask {}'.format(self.to_umask(get.umask))
                _is_set = True
        
        # 如果没有找到umask值，则添加umask值
        if not _is_set:
            _conf_list.append('umask {}'.format(get.umask))

        
        # 写入配置文件
        attr = self.unlock_file(umask_file)
        public.writeFile(umask_file,"\n".join(_conf_list))
        self.lock_file(umask_file,attr)
        public.WriteLog(self.__name,"修改默认文件权限(UMASK)为: {}".format(get.umask))
        return public.returnMsg(True,'设置成功')
        

    def get_keyfile_config(self):
        '''
            @name 获取keyfile配置
            @return list
        '''
        config_file = "{}/config/keyfile_config.json".format(self.__plugin_path)
        if not os.path.exists(config_file): return []
        try:
            return json.loads(public.readFile(config_file))
        except:
            return []
        
    def lsattr(self,filename):
        '''
            @name 获取文件属性
            @param filename 文件名
            @return str
        '''
        if not os.path.exists(filename): return ''
        try:
            return public.ExecShell("lsattr {}".format(filename))[0].strip().split(' ')[0].replace('-','')
        except:
            return ''


        
    def get_mode_and_user(self,path):
        '''取文件或目录权限信息'''
        if not os.path.exists(path): return 0,'',''
        stat = os.stat(path)
        mode = int(oct(stat.st_mode)[-3:])
        try:
            user = pwd.getpwuid(stat.st_uid).pw_name
            group = grp.getgrgid(stat.st_gid).gr_name
        except:
            user = str(stat.st_uid)
            group = str(stat.st_gid)
        return mode,user,group
        
    def get_keyfile_list(self,get):
        '''
            @name 获取keyfile列表
            @return dict
        '''
        config_list = self.get_keyfile_config()
        if not config_list: return public.returnMsg(False,'配置文件读取失败')

        result = []
        for i in config_list:
            if not os.path.exists(i['fullpath']): continue
            i['mode'],i['user'],i['group'] = self.get_mode_and_user(i['fullpath'])
            result.append(i)
        return public.returnMsg(True,result)
    

    def check_user_lock_status(self,username):
        '''
            @name 检查用户是否被锁定
            @param username 用户名
            @return bool
        '''
        with open('/etc/shadow', 'r') as shadow_file:
            for line in shadow_file.readlines():
                fields = line.strip().split(':')
                if fields[0] == username:
                    if fields[1].startswith('!'):
                        return True  # 用户被锁定
                    else:
                        return False  # 用户未被锁定
        return False  # 用户不存在或无法读取 /etc/shadow 文件

    

    def get_linux_user_list(self,get=None):
        '''
            @name 获取linux用户列表
            @return dict
        '''
        result = {}
        for i in pwd.getpwall():
            result[i.pw_name] = {
                'user': {
                    'title':'用户名',
                    'value':i.pw_name,
                    'ps':'用户名称，一般为英文'
                },
                'group': {
                    'title':'用户组',
                    'value':grp.getgrgid(i.pw_gid).gr_name,
                    'ps':'用户所属组'
                },
                'uid': {
                    'title':'UID',
                    'value':i.pw_uid,
                    'ps':'用户ID'
                },
                'gid': {
                    'title':'GID',
                    'value':i.pw_gid,
                    'ps':'用户组ID'
                },
                'dir': {
                    'title':'主目录',
                    'value':i.pw_dir,
                    'ps':'用户主目录'
                },
                'shell': {
                    'title':'Shell',
                    'value':i.pw_shell,
                    'ps':'登录用户时默认执行的Shell，一般为/bin/bash，如果为/sbin/nologin则表示禁止登录'
                },
                'gecos': {
                    'title':'备注',
                    'value':i.pw_gecos,
                    'ps':'该用户的备注信息'
                },
                'is_lock': {
                    'title':'锁定',
                    'value':self.check_user_lock_status(i.pw_name),
                    'ps':'该用户是否被锁定'
                }
            }

        return result
    
    def get_linux_group_list(self,get=None):
        '''
            @name 获取linux用户组列表
            @return dict
        '''
        result = {}
        if get: 
            user_list = pwd.getpwall()

        for i in grp.getgrall():
            if get: # 获取用户组成员
                for j in user_list:
                    if j.pw_gid == i.gr_gid:
                        i.gr_mem.append(j.pw_name)
                        break
            result[i.gr_name] = {
                'name': {
                    'title':'组名',
                    'value':i.gr_name,
                    'ps':'用户组名称'
                },
                'gid': {
                    'title':'GID',
                    'value':i.gr_gid,
                    'ps':'用户组ID'
                },
                'members': {
                    'title':'成员',
                    'value':i.gr_mem,
                    'ps':'用户组成员列表'
                }
            }
        return result
    
    

    def set_keyfile(self,get):
        '''
            @name 设置keyfile
            @param get.fullpath string 文件名
            @param get.mode string 权限值
            @param get.user string 用户名
            @param get.group string 用户组
            @return dict
        '''

        # 检查文件是否存在
        if not os.path.exists(get.fullpath): return public.returnMsg(False,'文件不存在')

        # 检查权限值是否合法
        if not re.match(r'^[0-7]{3}$',get.mode): return public.returnMsg(False,'权限值不合法')

        # 检查用户是否存在
        user_list = self.get_linux_user_list()
        if get.user not in user_list.keys(): return public.returnMsg(False,'用户不存在')

        # 检查用户组是否存在
        group_list = self.get_linux_group_list()
        if get.group not in group_list.keys(): return public.returnMsg(False,'用户组不存在')

        # 设置文件权限
        self.unlock_file()
        res = public.ExecShell("chown -R {}:{} {}".format(get.user,get.group,get.fullpath))
        if res[1]:
            self.lock_file()
            return public.returnMsg(False,res[1])
        res = public.ExecShell("chmod -R {} {}".format(get.mode,get.fullpath))
        if res[1]:
            self.lock_file()
            return public.returnMsg(False,res[1])
        self.lock_file()
        
        public.WriteLog(self.__name,'设置文件[{}]的权限={}，所属用户={}，所属组={}'.format(get.fullpath,get.mode,get.user,get.group))
        return public.returnMsg(True,'设置成功')
    

    def create_linux_user(self,get):
        '''
            @name 创建linux用户
            @param get.user string 用户名
            @param get.group string 用户组
            @param get.password string 密码
            @param get.shell string shell
            @param get.gecos string 备注
            @return dict
        '''
        # 检查用户是否存在
        user_list = self.get_linux_user_list()
        if get.user in user_list.keys(): return public.returnMsg(False,'用户已存在')

        # 检查用户组是否存在
        group_list = self.get_linux_group_list()
        if get.group not in group_list.keys(): return public.returnMsg(False,'用户组不存在')

        self.unlock_file()
        # 创建用户
        public.ExecShell("useradd -g {} -s {} {}".format(get.group,get.shell,get.user))

        # 设置备注
        public.ExecShell("usermod -c {} {}".format(get.gecos,get.user))

        # 设置密码
        if get.password:
            res = public.ExecShell("echo {} | passwd --stdin {}".format(get.password,get.user))
        
            if res[1]:
                public.ExecShell("userdel -r {}".format(get.user)) # 删除用户
                self.lock_file()
                return public.returnMsg(False,'密码设置失败：`{}`'.format(res[1]))
        self.lock_file()
        public.WriteLog(self.__name,'创建用户[{}]，所属用户组={}，备注={}'.format(get.user,get.group,get.gecos))
        return public.returnMsg(True,'创建成功')
    

    def create_linux_group(self,get):
        '''
            @name 创建linux用户组
            @param get.group string 用户组
            @return dict
        '''
        # 检查用户组是否存在
        group_list = self.get_linux_group_list()
        if get.group in group_list.keys(): return public.returnMsg(False,'用户组已存在')

        # 创建用户组
        self.unlock_file()
        public.ExecShell("groupadd {}".format(get.group))
        self.lock_file()
        public.WriteLog(self.__name,'创建用户组[{}]'.format(get.group))
        return public.returnMsg(True,'创建成功')
    

    def set_linux_user(self,get):
        '''
            @name 修改指定linux用户
            @param get.user string 用户名
            @param get.group string 用户组
            @param get.password string 密码
            @param get.shell string shell
            @param get.gecos string 用户备注信息
            @return dict
        '''
        # if not 'user' in get or 'group' not in get or 'password' not in get or 'shell' not in get or 'gecos' not in get: return public.returnMsg(False,'参数错误')
        if get.user in ['root']: return public.returnMsg(False,'禁止修改root用户')
        # 检查用户是否存在
        user_list = self.get_linux_user_list()
        if get.user not in user_list.keys(): return public.returnMsg(False,'用户不存在')

        # 检查用户组是否存在
        group_list = self.get_linux_group_list()
        if get.group not in group_list.keys(): return public.returnMsg(False,'用户组不存在')

        self.unlock_file()
        # 设置用户组
        public.ExecShell("usermod -g {} {}".format(get.group,get.user))

        # 设置shell
        public.ExecShell("usermod -s {} {}".format(get.shell,get.user))

        # 设置备注信息
        if get.gecos:
            public.ExecShell("usermod -c {} {}".format(get.gecos,get.user))

        # 设置密码
        if get.password and get.password not in ['x','*','********']:
            res = public.ExecShell("echo {} | passwd --stdin {}".format(get.password,get.user))
            if res[1]:
                self.lock_file()
                return public.returnMsg(False,'修改密码失败：`{}`'.format(res[1].strip().split('\n')[-1]))
            
        self.lock_file()
        public.WriteLog(self.__name,'修改用户[{}]，所属用户组={}，备注={}'.format(get.user,get.group,get.gecos))
        return public.returnMsg(True,'修改成功')
    
    def lock_linux_user(self,get):
        '''
            @name 锁定linux用户
            @param get.user string 用户名
            @return dict
        '''
        if not 'user' in get: return public.returnMsg(False,'参数错误')
        if get.user in ['root']: return public.returnMsg(False,'禁止锁定root用户')
        # 检查用户是否存在
        user_list = self.get_linux_user_list()
        if get.user not in user_list.keys(): return public.returnMsg(False,'用户不存在')
        if user_list[get.user]['shell']['value'] in ['/sbin/nologin','/usr/sbin/nologin']: return public.returnMsg(False,'失败：shell=/sbin/nologin的用户无需锁定')

        # 锁定用户
        self.unlock_file()
        res = public.ExecShell("usermod -L {}".format(get.user))
        self.lock_file()
        if res[1]:
                return public.returnMsg(False,'锁定失败：`{}`'.format(res[1]))
        public.WriteLog(self.__name,'锁定用户[{}]'.format(get.user))
        return public.returnMsg(True,'锁定成功')
    

    def unlock_linux_user(self,get):
        '''
            @name 解锁linux用户
            @param get.user string 用户名
            @return dict
        '''
        if not 'user' in get: return public.returnMsg(False,'参数错误')
        # 检查用户是否存在
        user_list = self.get_linux_user_list()
        if get.user not in user_list.keys(): return public.returnMsg(False,'用户不存在')

        # 解锁用户
        self.unlock_file()
        res = public.ExecShell("usermod -U {}".format(get.user))
        self.lock_file()
        if res[1]:
            if res[1].find('usermod -p') != -1:
                return public.returnMsg(False,'解锁失败，用户密码为空以及shell为/sbin/nologin时无需解锁')
        public.WriteLog(self.__name,'解锁用户[{}]'.format(get.user))
        return public.returnMsg(True,'解锁成功')
    

    def delete_linux_user(self,get):
        '''
            @name 删除linux用户
            @param get.user string 用户名
            @return dict
        '''

        # 检查用户是否存在
        user_list = self.get_linux_user_list()
        if get.user not in user_list.keys(): return public.returnMsg(False,'用户不存在')
        if user_list[get.user]['uid']['value'] < 1000: return public.returnMsg(False,'系统用户，无法删除')

        # 删除用户
        self.unlock_file()
        res = public.ExecShell("userdel -r {}".format(get.user))
        self.lock_file()
        if res[1]:
            return public.returnMsg(False,'删除失败：`{}`'.format(res[1]))
        public.WriteLog(self.__name,'删除用户[{}]'.format(get.user))
        return public.returnMsg(True,'删除成功')
    

    def delete_linux_group(self,get):
        '''
            @name 删除linux用户组
            @param get.group string 用户组
            @return dict
        '''
        
        # 检查用户组是否存在
        group_list = self.get_linux_group_list(True)
        if get.group not in group_list.keys(): return public.returnMsg(False,'用户组不存在')

        if group_list[get.group]['user_list']['value']: return public.returnMsg(False,'用户组下存在关联用户，无法删除，请先删除关联用户')

        if group_list[get.group]['gid']['value'] < 1000: return public.returnMsg(False,'系统用户组，无法删除')
        

        # 删除用户组
        self.unlock_file()
        res = public.ExecShell("groupdel {}".format(get.group))
        self.lock_file()
        if res[1]:
            return public.returnMsg(False,'删除失败：`{}`'.format(res[1]))
        public.WriteLog(self.__name,'删除用户组[{}]'.format(get.group))
        return public.returnMsg(True,'删除成功')
    


    def get_selinux_status(self,get):
        '''
            @name 获取selinux状态
            @return dict
        '''
        # 获取selinux状态
        status = 'Disabled'
        selinux_config_file = '/etc/selinux/config'
        if os.path.exists(selinux_config_file):
            with open(selinux_config_file,'r') as f:
                for line in f:
                    if line.startswith('SELINUX='):
                        status = line.split('=')[-1].strip()
                        break

        status = status.capitalize()

        options = {
            "Disabled": "关闭",
            "Enforcing": "开启",
            "Permissive": "宽容模式"
        }
        return public.returnMsg(True,{
            "title": "SELinux状态",
            "value":status,
            "ps": "当前SELinux状态, Disabled为关闭, Enforcing为开启, Permissive为宽容模式",
            "options": options
        })
    

    def set_selinux_status(self,get):
        '''
            @name 修改selinux状态
            @param get.status string 状态
            @return dict
        '''
        status = get.status.strip().lower()
        if status not in ['enforcing','permissive','disabled']: return public.returnMsg(False,'状态错误')
        # 设置selinux状态
        public.ExecShell("setenforce {}".format(status))

        # 写入配置文件
        selinux_config_file = '/etc/selinux/config'
        if os.path.exists(selinux_config_file):
            public.ExecShell("sed -i 's/SELINUX=.*/SELINUX={}/g' {}".format(status,selinux_config_file))

        public.WriteLog(self.__name,'修改selinux状态为: {}'.format(status))
        return public.returnMsg(True,'修改成功，重启系统后生效')
    

    def install_audit(self,get =None):
        '''
            @name 安装审计
            @return dict
        '''
        auditcli = '/sbin/auditctl'

        if os.path.exists(auditcli): return public.returnMsg(False,'已安装')

        if os.path.exists('/usr/bin/yum'):
            public.ExecShell("yum install -y audit")
        elif os.path.exists('/usr/bin/apt-get'):
            public.ExecShell("apt-get install -y auditd")
        elif os.path.exists('/usr/bin/dnf'):
            public.ExecShell("dnf install -y audit")

        if not os.path.exists(auditcli): return public.returnMsg(False,'安装失败')
        return public.returnMsg(True,'安装成功')
    


    def get_audit_status(self,get):
        '''
            @name 获取审计配置
            @return dict
        '''

        self.install_audit()

        # 获取审计配置
        config = {}
        config['status'] = {
            "service_status": {
                "title": "服务状态",
                "value": False,
                "ps": "True:运行,False:停止"
            },
            "enabled": {
                "title": "审计功能启用状态",
                "value": 0,
                "ps": "1:启用,0:禁用"
            },
            "failure": {
                "title": "审计失败状态",
                "value": 1,
                "ps": "该值为1表示在某些情况下，审计功能由于问题（例如审计日志存储满）而无法正常工作"
            },
            "pid": {
                "title": "PID",
                "value": 0,
                "ps": "当前运行的auditd进程的进程ID"
            },
            "rate_limit": {
                "title": "审计事件的速率限制",
                "value": 0,
                "ps": "该值为0表示没有限制，所有审计事件都将被记录"
            },
            "backlog_limit": {
                "title": "审计事件的队列长度限制",
                "value": 8192,
                "ps": "当达到此限制时，新的审计事件将被丢弃"
            },
            "lost": {
                "title": "丢弃的事件数量",
                "value": 0,
                "ps": "由于队列溢出而丢弃的审计事件的数量"
            },
            "backlog": {
                "title": "活跃队列长度",
                "value": 0,
                "ps": "当前队列中的审计事件数量"
            },
            "loginuid_immutable": {
                "title": "登录UID的不可变性状态",
                "value": '0 unlocked',
                "ps": "该值为0表示登录UID是可变的，即可在登录会话中更改"
            }
        }

        keys = config['status'].keys()
        public.print_log(keys)
        # 获取审计状态
        config['status']['service_status']['value'] = not not public.ExecShell("systemctl status auditd | grep Active|grep running")[0].strip()
        audit_status = public.ExecShell("auditctl -s")[0].strip()
        for i in audit_status.split('\n'):
            i = i.strip()
            if i:
                if not i: continue
                tmp = i.split()
                tmp_len = len(tmp)
                if not tmp or  tmp_len < 2: continue

                if not tmp[0] in keys: continue
                
                if tmp_len == 2:
                    if tmp[1].isdigit():
                        config['status'][tmp[0]]['value'] = int(tmp[1])
                    else:
                        config['status'][tmp[0]]['value'] = tmp[1]
                else:
                    config['status'][tmp[0]]['value'] = ' '.join(tmp[1:])

        # 获取审计规则
        config['rules'] = [] 
        for i in public.ExecShell("auditctl -l")[0].strip().strip("No rules").split('\n'):
            if not i: continue
            config['rules'].append(i)

        return public.returnMsg(True,config)
    
    def get_network_ip(self):
        """
        @name 获取本机ip
        @return string
        """

        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            return ip
        finally:
            s.close()

    def set_audit_status(self,get):
        '''
            @name 设置审计配置
            @param get.status string 状态
            @return dict
        '''
        if get.status not in ['1','0']: return public.returnMsg(False,'状态错误')
        # 设置审计状态
        public.ExecShell("auditctl -e {}".format(get.status))
        public.WriteLog(self.__name,'设置审计状态:{}'.format(get.status))
        return public.returnMsg(True,'设置成功')
    

    
    def is_port_allow(self,port):
        '''
            @name 检查端口是否允许外网访问
            @param port int 端口
            @return bool
        '''
        if not port: return False
        socket.setdefaulttimeout(0.2)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if not self.__server_ip: 
            self.__server_ip = public.GetHost().split(':')[0]
            if not self.__server_ip or self.__server_ip == '127.0.0.1':
                self.__server_ip = self.get_network_ip()
        try:
            s.connect((self.__server_ip,port))
            s.shutdown(2)
            return True
        except:
            return False
        finally:
            s.close()
        


    def get_listen_list(self):
        '''
            @name 获取监听列表
            @return dict
        '''
        listen_list = []
        for i in psutil.net_connections():
            if i.status == 'LISTEN':
                try:
                    exe = psutil.Process(i.pid).exe()
                except:
                    exe = ""
                listen_list.append({
                    "ip":{
                        "title":"监听地址",
                        "value":i.laddr.ip,
                        "ps":"通常为127.0.0.1或0.0.0.0，如果监听地址为127.0.0.1或::1说明该端口只能本地访问"
                        },
                    "port":{
                        "title":"监听端口",
                        "value":i.laddr.port,
                        "ps":"应用监听的端口，如：80，443通常为HTTP服务端口"
                    },
                    "pid":{
                        "title":"进程ID",
                        "value":i.pid,
                        "ps":"监听该端口的进程ID"
                    },
                    "process_exe":{
                        "title":"进程路径",
                        "value": exe,
                        "ps":"监听该端口的进程路径"
                    },
                    "is_allow":{
                        "title":"是否允许外网访问",
                        "value":self.is_port_allow(i.laddr.port),
                        "ps":"检测该端口是否允许外网访问，如果允许外网访问，建议在【安全页面】 - 【系统防火墙】中配置防火墙规则"
                    }
                })

        return listen_list


    def get_firewall_status(self,get):
        '''
            @name 获取防火墙状态
            @return dict
        '''
        # 获取防火墙状态
        result = {
            "status":{
                "title":"系统防火墙状态",
                "value":public.get_firewall_status(),
                "ps":"建议开启系统防火墙，并在【安全页面】 - 【系统防火墙】中配置合适的防火墙规则"
            },
            "listen_list": {
                "title":"监听列表",
                "value":self.get_listen_list(),
                "ps": "检测系统中所有应用监听的端口，其中【是否允许外网访问】的检测由于检测方法的原因，我们无法保证绝对准确，建议核实后再做下一步处理"
            }
        }
        return public.returnMsg(True,result)
    
    def set_firewall_status(self,get):
        '''
            @name 设置防火墙状态
            @param get.status string 状态 0.关闭 1.开启
            @return dict
        '''
        status = int(get.status)
        try:
            import panelController
            _obj = panelController.Controller()
        except:
            return public.returnMsg(False,'当前面板版本过低，不支持此功能，请升级到最新版')
        get.mod_name = 'firewall'
        get.model_index = 'safe'
        get.action = 'model'
        get.mod_name = 'firewall'
        get.def_name = 'firewall_admin'
        status_options = ['stop','start','restart','reload']
        get.data = json.dumps({"status" :status_options[status]})
        res = _obj.model(get)
        del(_obj)
        return res
    
    def create_firewall_rule(self,get):
        '''
            @name 创建防火墙规则
            @param get.port int 端口
            return dict
        '''
        port = int(get.port)
        if port < 1 or port > 65535: return public.returnMsg(False,'端口范围错误')
        try:
            import panelController
            _obj = panelController.Controller()
        except:
            return public.returnMsg(False,'当前面板版本过低，不支持此功能，请升级到最新版')
        
        get.mod_name = 'firewall'
        get.model_index = 'safe'
        get.action = 'model'
        get.mod_name = 'firewall'
        get.def_name = 'create_rules'
        get.data = json.dumps({"ports" :str(port),"protocol":'tcp','is_add':'1','source':'0.0.0.0/0','type':'accept'})
        res = _obj.model(get)
        del(_obj)
        return res
    

    

    

    
    def check_plugin_accept(self,plugin_name):
        '''
            @name 检查插件是否过期
            @param plugin_name string 插件名称
            @return bool
        '''
        import panelPlugin
        plugin_obj = panelPlugin.panelPlugin()
        plugin_list =  plugin_obj.get_cloud_list()
        now_time = time.time()

        # 是否为企业版
        if 'ltd' in plugin_list:
            if plugin_list['ltd'] > now_time: return True
        
        # 是否为专业版
        if 'pro' in plugin_list:
            if plugin_list['pro'] > now_time or plugin_list['pro'] == 0: return True
        

        for i in plugin_list['list']:
            if i['name'] == plugin_name:
                if i['endtime'] > now_time or i['endtime'] == 0: return True
                break
        
        return False


    def get_bywaf_status(self,get):
        '''
            @name 获取WAF安装状态
            @return dict
        '''
        server_type = public.get_webserver()
        is_waf = False
        pay_status = False
        httpd_waf = False
        nginx_waf = False
        if server_type == 'nginx':
            nginx_waf = os.path.exists('/www/server/panel/plugin/btwaf/info.json')
            pay_status = self.check_plugin_accept('btwaf')  
        elif server_type == 'apache':
            httpd_waf = os.path.exists('/www/server/panel/plugin/btwaf_httpd/info.json')
            pay_status = self.check_plugin_accept('btwaf_httpd')  
        
        if nginx_waf or httpd_waf: is_waf = True

        result = {
            "title":"WAF安装状态",
            "value":is_waf,
            "pay_status":pay_status,
            "ps":"建议安装WAF，并在【WAF页面】中配置合适的WAF防火墙拦截规则，以保护您的网站安全"
        }
        return public.returnMsg(True,result)
    
    def get_service_ps_config(self):
        '''
            @name 获取服务备注配置文件
            @return void
        '''
        service_ps_config = '{}/config/service_ps.json'.format(self.__plugin_path)
        if not os.path.exists(service_ps_config): return
        try:
            self.__service_ps = json.loads(public.readFile(service_ps_config))
        except:
            pass

    def get_run_ps(self,name):
        '''
            @name 获取服务备注
            @param name string 服务名称
            @return string
        '''

        if not self.__service_ps:
            self.get_service_ps_config()
        if name in self.__service_ps: return self.__service_ps[name]

        runPs = {'netconsole':'网络控制台日志','network':'网络服务','jexec':'JAVA','tomcat8':'Apache Tomcat','tomcat7':'Apache Tomcat','mariadb':'Mariadb','plymouth-halt':'关机动画','plymouth-quit':'启动动画',
                 'plymouth-kexec': '内核动画','plymouth-poweroff':'关机动画','plymouth-reboot':'重启动画','plymouth-start':'启动动画','plymouth-switch-root':'切换根目录动画','plymouth-upstart-bridge':'启动动画',
                 'tomcat9':'Apache Tomcat','tomcat':'Apache Tomcat','memcached':'Memcached缓存器','bt-tamper':'堡塔企业级防篡改','bt_ipfilter':'宝塔IP过滤服务','svnserve':'SVN服务',
                 'rsync_inotify':'rsync实时同步','pure-ftpd':'FTP服务','bt_tamper_proof':'宝塔网站防篡改','btcloudmonitorclient':'堡塔云安全监控-客户端','ntpdate':'时间同步服务',
                 'httpd':'Web服务器(Apache)','bt':'宝塔面板','mysqld':'MySQL数据库','rsynd':'rsync文件同步服务','rsyncd':'rsync文件同步服务','php-fpm':'PHP服务','systemd':'系统核心服务',
                 '/etc/rc.local':'用户自定义启动脚本','/etc/profile':'全局用户环境变量','/etc/inittab':'用于自定义系统运行级别','/etc/rc.sysinit':'系统初始化时调用的脚本',
                 'sshd':'SSH服务','crond':'计划任务服务','udev-post':'设备管理系统','auditd':'审核守护进程','rsyslog':'rsyslog服务','sendmail':'邮件发送服务','blk-availability':'lvm2相关',
                 'local':'用户自定义启动脚本','netfs':'网络文件系统','lvm2-monitor':'lvm2相关','xensystem':'xen云平台相关','iptables':'iptables防火墙','ip6tables':'iptables防火墙 for IPv6','firewalld':'firewall防火墙'}
        
        if name in runPs: return runPs[name]

        # public.print_log(name)
        return name
    
    def get_my_runlevel(self):
        '''
            @name 获取当前运行级别
            @return string
        '''
        try:
            runlevel = public.ExecShell('runlevel')[0].split()[1]
        except:
            runlevel_dict = {"multi-user.target":'3','rescue.target':'1','poweroff.target':'0','graphical.target':'5',"reboot.target":'6'}
            r_tmp = public.ExecShell('systemctl get-default')[0].strip()
            if r_tmp in runlevel_dict:
                runlevel = runlevel_dict[r_tmp]
            else:
                runlevel = '3'
        return runlevel
    
    def get_service_list(self,get):
        '''
            @name 获取服务列表
            @return dict
        '''
        init_d = '/etc/init.d/'
        serviceList = []
        data = {}
        data['runlevel'] = self.get_my_runlevel()
        for sname in os.listdir(init_d):
            try:
                if str(oct(os.stat(init_d + sname).st_mode)[-3:]) == '644': continue
                serviceInfo = {}
                runlevels = self.get_runlevel(sname)
                serviceInfo['name'] = sname
                serviceInfo['status'] = runlevels[int(data['runlevel'])]
                serviceInfo['ps'] = self.get_run_ps(sname)
                serviceList.append(serviceInfo)
            except:
                continue

        
        
        data['serviceList'] = sorted(serviceList, key=lambda x : x['name'], reverse=False)
        data['serviceList'] = self.get_systemctl_list(data['serviceList'])
        return data

    def get_systemctl_list(self,serviceList):
        '''
            @name 获取systemctl服务列表
            @param serviceList list 服务列表
            @return list
        '''
        systemctl_user_path = '/usr/lib/systemd/system/'
        systemctl_run_path = '/etc/systemd/system/multi-user.target.wants/'
        if not os.path.exists(systemctl_user_path) or not os.path.exists(systemctl_run_path): return serviceList
        r = '.service'
        for d in os.listdir(systemctl_user_path):
            if d.find(r) == -1: continue
            serviceInfo = {}
            serviceInfo['name'] = d.replace(r,'')
            serviceInfo['status'] = True
            if os.path.exists(systemctl_run_path + d):
                serviceInfo['status'] = False

            serviceInfo['ps'] = self.get_run_ps(serviceInfo['name'])
            serviceList.append(serviceInfo)
        return serviceList

    def set_runlevel_state(self,get):
        '''
            @name 设置服务状态
            @param get.name string 服务名称
            @param get.runlevel string 服务状态
            @return dict
        '''
        if get.runlevel == '0' or get.runlevel == '6': return public.returnMsg(False,'为安全考虑,不能通过面板直接修改此运行级别')
        systemctl_user_path = '/usr/lib/systemd/system/'
        systemctl_run_path = '/etc/systemd/system/multi-user.target.wants/'
        if os.path.exists(systemctl_user_path + get.serviceName + '.service'):
            runlevel = public.ExecShell('runlevel')[0].split()[1]
            if get.runlevel != runlevel: return public.returnMsg(False,'Systemctl托管的服务不能设置非当前运行级别的状态')
            action = 'enable'
            if os.path.exists(systemctl_run_path + get.serviceName + '.service'): action = 'disable'
            public.ExecShell('systemctl ' + action + ' ' + get.serviceName + '.service')
            return public.returnMsg(True,'设置成功!')

        rc_d = '/etc/rc' + get.runlevel + '.d/'
        import shutil;
        for d in os.listdir(rc_d):
            if d[3:] != get.serviceName: continue
            sfile = rc_d + d
            c = 'S'
            if d[:1] == 'S': c = 'K'
            dfile = rc_d + c + d[1:]
            shutil.move(sfile, dfile)
            return public.returnMsg(True,'设置成功!')
        return public.returnMsg(False,'设置失败!')

    def get_runlevel(self,name):
        '''
            @name 获取服务运行状态
            @param name string 服务名称
            @return list
        '''
        rc_d = '/etc/'
        runlevels = []
        for i in range(7):
            isrun = False
            for d in os.listdir(rc_d + 'rc' + str(i) + '.d'):
                if d[3:] == name:
                    if d[:1] == 'S': isrun = True
            runlevels.append(isrun)
        return runlevels

    def remove_service(self,get):
        if get.serviceName == 'bt': return public.returnMsg(False,'不能通过面板结束宝塔面板服务!')
        systemctl_user_path = '/usr/lib/systemd/system/'
        if os.path.exists(systemctl_user_path + get.serviceName + '.service'):  return public.returnMsg(False,'Systemctl托管的服务不能通过面板删除');
        public.ExecShell('service ' + get.serviceName + ' stop')
        if os.path.exists('/usr/sbin/update-rc.d'):
            public.ExecShell('update-rc.d '+get.serviceName+' remove')
        elif os.path.exists('/usr/sbin/chkconfig'):
            public.ExecShell('chkconfig --del ' + get.serviceName)
        else:
            public.ExecShell("rm -f /etc/rc0.d/*" + get.serviceName)
            public.ExecShell("rm -f /etc/rc1.d/*" + get.serviceName)
            public.ExecShell("rm -f /etc/rc2.d/*" + get.serviceName)
            public.ExecShell("rm -f /etc/rc3.d/*" + get.serviceName)
            public.ExecShell("rm -f /etc/rc4.d/*" + get.serviceName)
            public.ExecShell("rm -f /etc/rc5.d/*" + get.serviceName)
            public.ExecShell("rm -f /etc/rc6.d/*" + get.serviceName)
        filename = '/etc/init.d/' + get.serviceName
        if os.path.exists(filename): os.remove(filename)
        return public.returnMsg(True,'删除成功!')
    

    def set_service_state(self,get):
        '''
            @name 设置服务状态
            @param get.service_name str 服务名称
            @param get.status int 服务状态
            @return dict
        '''
        service_name = get.service_name.strip()
        service_status = int(get.status)
        if not service_status in [0,1]: return public.returnMsg(False,'状态值错误!')
        if service_name == 'bt': return public.returnMsg(False,'不能通过面板结束宝塔面板服务!')
        status_options=['关闭','开启']
        self.unlock_file()
        systemctl_user_path = '/usr/lib/systemd/system/'
        if os.path.exists(systemctl_user_path + service_name + '.service'):
            actions = ['disable','enable']
            action = actions[service_status]
            public.ExecShell('systemctl ' + action + ' ' + service_name + '.service')
            actions = ['stop','start']
            public.ExecShell("systemctl "+actions[service_status]+" " + service_name + ".service")
            self.lock_file()
            public.WriteLog(self.__name,'设置服务[{}]的状态为:{}'.format(service_name,status_options[service_status]))
            return public.returnMsg(True,'设置成功!')
        
        init_d = '/etc/init.d/'
        if not os.path.exists(init_d + service_name): return public.returnMsg(False,'服务不存在!')
        open_config = self.__read_config()
        if open_config['open']: self.set_open(None,status=0)
        if os.path.exists('/usr/sbin/update-rc.d'):
            actions = ["defaults-disabled","defaults"]
            public.ExecShell('update-rc.d '+service_name+' ' + actions[service_status])
        elif os.path.exists('/usr/sbin/chkconfig'):
            actions = ["off","on"]
            public.ExecShell("chkconfig --level 2345 {} {}".format(service_name,actions[service_status]))

        actions = ['stop','start']
        public.ExecShell(init_d + service_name + ' ' + actions[service_status])
        if open_config['open']: self.set_open(None,status=1)
        
        self.lock_file()
        public.WriteLog(self.__name,'设置服务[{}]的状态为:{}'.format(service_name,status_options[service_status]))
        return public.returnMsg(True,'设置成功!')
    

    def get_antivirus_list(self):
        '''
            @name 获取杀毒软件列表
            @return list
        '''
        config_file = '{}/config/anivirus.json'.format(self.__plugin_path)
        if not os.path.exists(config_file): return []
        with open(config_file,'r') as f:
            antivirus_list = json.loads(f.read())
            return antivirus_list
    
    def check_antivirus_installed(self,get):
        '''
            @name 检查杀毒软件是否安装
            @return dict
        '''
        antivirus_list = self.get_antivirus_list()

        installed_antivirus = []
        pay_status = True

        for antivirus in antivirus_list:
            # 检查文件是否存在
            if any(os.path.exists(file) for file in antivirus["files"]):
                installed_antivirus.append({"name": antivirus["name"],"pay_status":pay_status})

        if not installed_antivirus: return public.returnMsg(False,'未检测到杀毒软件!')

        return public.returnMsg(True,installed_antivirus)
    

    def get_hosts_deny_list(self,get = None):
        '''
            @name 获取hosts.deny列表
            @return list
        '''
        hosts_deny_file = '/etc/hosts.deny'
        if not os.path.exists(hosts_deny_file): return []
        with open(hosts_deny_file,'r') as f:
            hosts_deny_list = []
            for i in f.readlines():
                i = i.strip()
                if not i: continue
                if i[:1] == '#': continue
                _line = [ x.strip() for x in i.split(':') if x != '']
                hosts_deny_list.append({
                    "app_name":{
                        "title":"应用名称",
                        "value":_line[0].strip(),
                        "ps": "指定应用名称，如sshd,pure-ftpd等"
                    },
                    "host":{
                        "title":"主机",
                        "value":_line[1].strip(),
                        "ps": "禁止访问的主机，可以是IP地址，也可以是主机名，如果设置为ALL，则表示所有主机都禁止访问"
                    },
                    "type":{
                        "title":"策略",
                        "value":'deny',
                        "ps": "指定策略，deny表示禁止访问，allow表示允许访问"
                    }
                })
            return hosts_deny_list
        
    def get_hosts_allow_list(self,get = None):
        '''
            @name 获取hosts.allow列表
            @return list
        '''
        hosts_allow_file = '/etc/hosts.allow'
        if not os.path.exists(hosts_allow_file): return []
        with open(hosts_allow_file,'r') as f:
            hosts_allow_list = []
            for i in f.readlines():
                i = i.strip()
                if not i: continue
                if i[:1] == '#': continue
                _line = [ x.strip() for x in i.split(':') if x != '']
                if len(_line) < 3: _line.append('allow')
                hosts_allow_list.append({
                    "app_name":{
                        "title":"应用名称",
                        "value":_line[0].strip(),
                        "ps": "指定应用名称，如sshd,pure-ftpd等"
                    },
                    "host":{
                        "title":"主机",
                        "value":_line[1].strip(),
                        "ps": "允许访问的主机，可以是IP地址，也可以是主机名，如果设置为ALL，则表示所有主机都允许访问"
                    },
                    "type":{
                        "title":"策略",
                        "value":_line[2].strip(),
                        "ps": "指定策略类型，如：allow"
                    }
                })
            return hosts_allow_list
        
    def get_hosts_all_list(self,get=None):
        '''
            @name 获取hosts列表
            @return list
        '''
        hosts_list = []
        hosts_list.extend(self.get_hosts_allow_list(get=None))
        hosts_list.extend(self.get_hosts_deny_list(get=None))
        return public.returnMsg(True,hosts_list)
        
    def create_hosts_deny(self,get):
        '''
            @name 创建hosts.deny
            @param get.app_name str 应用名称,如sshd,如果为ALL，则表示所有应用
            @param get.host str 主机  通常为IP地址，也可以是主机名，如果设置为ALL，则表示所有主机
            @return dict
        '''
        if not 'app_name' in get or not 'host' in get: return public.returnMsg(False,'参数错误!')

        app_name = get.app_name.strip()
        host = get.host.strip()

        if not app_name or not host: return public.returnMsg(False,'参数错误!')

        
        hosts_deny_list = self.get_hosts_deny_list()
        is_exists = False
        for i in hosts_deny_list:
            if i['app_name']['value'].lower() == app_name.lower() and i['host']['value'].lower() == host.lower():
                is_exists = True
                break

        if is_exists: return public.returnMsg(False,'指定规则已存在!')
        
        hosts_deny_file = '/etc/hosts.deny'

        hosts_deny_body = public.readFile(hosts_deny_file)
        if not hosts_deny_body: hosts_deny_body = ''

        hosts_deny_body = hosts_deny_body.strip() + '\n' + app_name + ':' + host + '\n'
        attr = self.unlock_file(hosts_deny_file)
        public.writeFile(hosts_deny_file,hosts_deny_body)
        self.lock_file(hosts_deny_file,attr)
        public.WriteLog(self.__name,'添加hosts.deny规则: ' + app_name + ':' + host)
        return public.returnMsg(True,'添加成功!')
    

    def create_hosts_allow(self,get):
        '''
            @name 创建hosts.allow
            @param get.app_name str 应用名称,如sshd,如果为ALL，则表示所有应用
            @param get.host str 主机  通常为IP地址，也可以是主机名，如果设置为ALL，则表示所有主机
            @return dict
        '''
        if 'app_name' not in get or 'host' not in get: return public.returnMsg(False,'参数错误!')
        app_name = get.app_name.strip()
        host = get.host.strip()

        if not app_name or not host: return public.returnMsg(False,'参数错误!')
        
        hosts_allow_list = self.get_hosts_allow_list()
        is_exists = False
        for i in hosts_allow_list:
            if i['app_name']['value'].lower() == app_name.lower() and i['host']['value'].lower() == host.lower(): 
                is_exists = True
                break
        
        if is_exists: return public.returnMsg(False,'指定规则已存在!')
        hosts_allow_file = '/etc/hosts.allow'

        hosts_allow_body = public.readFile(hosts_allow_file)
        if not hosts_allow_body: hosts_allow_body = ''

        hosts_allow_body = hosts_allow_body.strip() + '\n' + app_name + ':' + host + ':allow\n'
        attr = self.unlock_file(hosts_allow_file)
        public.writeFile(hosts_allow_file,hosts_allow_body)
        self.lock_file(hosts_allow_file,attr)
        public.WriteLog(self.__name,'添加hosts.allow规则: ' + app_name + ':' + host)
        return public.returnMsg(True,'添加成功!')
    

    def delete_hosts_deny(self,get):
        '''
            @name 删除hosts.deny
            @param get.app_name str 应用名称,如sshd,如果为ALL，则表示所有应用
            @param get.host str 主机  通常为IP地址，也可以是主机名，如果设置为ALL，则表示所有主机
            @return dict
        '''
        if 'app_name' not in get or 'host' not in get: return public.returnMsg(False,'参数错误!')
        app_name = get.app_name.strip()
        host = get.host.strip()

        if not app_name or not host: return public.returnMsg(False,'参数错误!')
        
        hosts_deny_list = self.get_hosts_deny_list()
        is_exists = False
        for i in hosts_deny_list:
            if i['app_name']['value'].lower() == app_name.lower() and i['host']['value'].lower() == host.lower(): 
                is_exists = True
                break
        
        if not is_exists:return public.returnMsg(False,'指定规则不存在!')
        
        hosts_deny_file = '/etc/hosts.deny'

        hosts_deny_body = public.readFile(hosts_deny_file)

        hosts_deny_list = []
        for i in hosts_deny_body.split('\n'):
            i = i.strip()
            if not i: continue
            if i[:1] == '#':
                hosts_deny_list.append(i)
                continue
            _line = [ x.strip() for x in i.split(':') if x != '']
            if _line[0].lower() == app_name.lower() and _line[1].lower() == host.lower():
                continue
            hosts_deny_list.append(i)

        attr = self.unlock_file(hosts_deny_file)
        public.writeFile(hosts_deny_file,'\n'.join(hosts_deny_list))
        self.lock_file(hosts_deny_file,attr)
        public.WriteLog(self.__name,'删除hosts.deny规则: ' + app_name + ':' + host)
        return public.returnMsg(True,'删除成功!')
    

    def delete_hosts_allow(self,get):
        '''
            @name 删除hosts.allow
            @param get.app_name str 应用名称,如sshd,如果为ALL，则表示所有应用
            @param get.host str 主机  通常为IP地址，也可以是主机名，如果设置为ALL，则表示所有主机
            @return dict
        '''
        if 'app_name' not in get or 'host' not in get: return public.returnMsg(False,'参数错误!')
        app_name = get.app_name.strip()
        host = get.host.strip()

        if not app_name or not host: return public.returnMsg(False,'参数错误!')
        
        hosts_allow_list = self.get_hosts_allow_list()
        is_exists = False
        for i in hosts_allow_list:
            if i['app_name']['value'].lower() == app_name.lower() and i['host']['value'].lower() == host.lower(): 
                is_exists = True
                break

        if not is_exists:return public.returnMsg(False,'指定规则不存在!')
        
        
        hosts_allow_file = '/etc/hosts.allow'

        hosts_allow_body = public.readFile(hosts_allow_file)

        hosts_allow_list = []
        for i in hosts_allow_body.split('\n'):
            i = i.strip()
            if not i: continue
            if i[:1] == '#':
                hosts_allow_list.append(i)
                continue
            _line = [ x.strip() for x in i.split(':') if x != '']
            if _line[0].lower() == app_name.lower() and _line[1].lower() == host.lower():
                continue
            hosts_allow_list.append(i)

        attr = self.unlock_file(hosts_allow_file)
        public.writeFile(hosts_allow_file,'\n'.join(hosts_allow_list))
        self.lock_file(hosts_allow_file,attr)
        public.WriteLog(self.__name,'删除hosts.allow规则: ' + app_name + ':' + host)
        return public.returnMsg(True,'删除成功!')
    
    

    def get_ssh_tmout(self,get):
        '''
            @name 获取SSH超时时间
            @return dict
        '''

        res = public.ExecShell("source /etc/profile && echo $TMOUT")[0].strip()
        if not res: res = '0'
        return public.returnMsg(True,{
            "title": "SSH超时时间",
            "value": int(res),
            "unit": "秒",
            "very": 300,
            "ps": "设置SSH连接超时时间，如果设置为0，则表示不超时"
        })
    
    def set_ssh_tmout(self,get):
        '''
            @name 设置SSH超时时间
            @param get.tmout int 超时时间，单位为秒
            @return dict
        '''
        if 'tmout' not in get: return public.returnMsg(False,'参数错误!')
        tmout = int(get.tmout)
        if not tmout: tmout = 0
        if tmout < 0: tmout = 0
        profile = '/etc/profile'
        attr = self.unlock_file(profile)
        public.ExecShell("sed -i '/TMOUT=/d' {}".format(profile))
        public.ExecShell("echo 'export TMOUT={}' >> {}".format(tmout,profile))
        self.lock_file(profile,attr)
        public.WriteLog(self.__name,'设置SSH超时时间为: {}秒'.format(tmout))
        return public.returnMsg(True,'设置成功!')
    
    def unlock_file(self,filename=None):
        '''
            @name 解锁文件
            @param filename str 文件名
            @return str
        '''
        if filename:
            if not os.path.exists(filename): return ''
            attr = self.lsattr(filename)
            if attr:
                public.ExecShell("chattr -%s %s" % (attr,filename))
        
        if public.ExecShell('bash {}/init.sh status'.format(self.__plugin_path))[0].find("already running") != -1:
            public.ExecShell("/etc/init.d/bt_syssafe stop")
            self.__is_start = True
        else:
            self.__is_start = False
            
        
    
    def lock_file(self,filename=None,attr=None):
        '''
            @name 锁定文件
            @param filename str 文件名
            @param attr str 文件属性
            @return bool
        '''
        # if not attr: return False
        # if not os.path.exists(filename): return False
        # public.ExecShell("chattr +%s %s" % (attr,filename))
        if self.__is_start: 
            public.ExecShell("/etc/init.d/bt_syssafe start")
            self.__is_start = False
        return True

    

if __name__ == "__main__":
    c = syssafe_main()
    if len(sys.argv) == 1:
        c.start()
    else:
        c.set_open(None, int(sys.argv[1]))
