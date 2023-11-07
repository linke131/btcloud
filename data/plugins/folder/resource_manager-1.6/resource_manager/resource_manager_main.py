# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 王张杰 <750755014@qq.com>
# +-------------------------------------------------------------------

# +--------------------------------------------------------------------
# |   宝塔资源管理器
# +--------------------------------------------------------------------
import sys
import os
import time
import json
import psutil

os.chdir("/www/server/panel")
sys.path.append('class/')
import public


class resource_manager_main:
    __plugin_path = '/www/server/panel/plugin/resource_manager'
    __data_path = os.path.join(__plugin_path, 'data')
    cpu_old_path = os.path.join(__data_path, 'cpu_old.json')
    disk_read_old_path = os.path.join(__data_path, 'disk_read_old.json')
    disk_write_old_path = os.path.join(__data_path, 'disk_write_old.json')
    old_net_path = os.path.join(__data_path, 'network_old.json')
    old_disk_path = os.path.join(__data_path, 'disk_old.json')
    old_site_path = os.path.join(__data_path, 'site_old.json')

    iftop_out = os.path.join(__data_path, 'iftop.log')
    iftop_lo = os.path.join(__data_path, 'iftop_lo.log')
    nethogs_out = os.path.join(__data_path, 'process_flow.log')

    pids = None
    __cpu_time = None
    cpu_new_info = {}
    cpu_old_info = {}
    disk_read_new_info = {}
    disk_read_old_info = {}
    disk_write_new_info = {}
    disk_write_old_info = {}
    new_net_info = {}
    old_net_info = {}
    new_disk_info = {}
    old_disk_info = {}
    new_site_info = {}
    old_site_info = {}
    panel_pid = None
    task_pid = None
    setupPath = '/www/server'

    def __init__(self):
        if not os.path.isdir(self.__data_path):
            os.makedirs(self.__data_path, 384)
        self.add_nethogs_task()
        # self.add_iftop_task()

    # 按cpu资源获取进程列表
    def get_process_cpu(self, get):
        self.pids = psutil.pids()
        process_list = []
        if type(self.cpu_new_info) != dict: self.cpu_new_info = {}
        self.cpu_new_info['cpu_time'] = self.get_cpu_time()
        self.cpu_new_info['time'] = time.time()

        if 'sort' not in get: get.sort = 'cpu_percent'
        get.reverse = bool(int(get.reverse)) if 'reverse' in get else True
        info = {}
        info['activity'] = 0
        info['cpu'] = 0.00
        status_ps = {'sleeping': '睡眠', 'running': '活动'}
        limit = 1000
        for pid in self.pids:
            tmp = {}
            try:
                p = psutil.Process(pid)
            except:
                continue
            with p.oneshot():
                p_cpus = p.cpu_times()
                p_state = p.status()
                if p_state == 'running': info['activity'] += 1
                if p_state in status_ps: p_state = status_ps[p_state]
                else: continue
                tmp['exe'] = p.exe()
                tmp['name'] = p.name()
                tmp['pid'] = pid
                tmp['ppid'] = p.ppid()
                # tmp['create_time'] = int(p.create_time())
                tmp['status'] = p_state
                tmp['user'] = p.username()
                tmp['cpu_percent'] = self.get_cpu_percent(str(pid), p_cpus, self.cpu_new_info['cpu_time'])
                tmp['threads'] = p.num_threads()
                tmp['ps'] = self.get_process_ps(tmp['name'], pid)
                if tmp['cpu_percent'] > 100: tmp['cpu_percent'] = 0.1
                info['cpu'] += tmp['cpu_percent']
            process_list.append(tmp)
            limit -= 1
            if limit <= 0: break
            del p
            del tmp
        public.writeFile(self.cpu_old_path, json.dumps(self.cpu_new_info))
        # process_list = self.handle_process_list(process_list)
        process_list = sorted(process_list, key=lambda x: x[get.sort], reverse=get.reverse)
        info['load_average'] = self.get_load_average()
        data = {}
        data['process_list'] = process_list
        info['cpu'] = round(info['cpu'], 2)
        data['info'] = info
        return data

    # 处理进程的父子关系
    def handle_process_list(self, process_list):
        master_list = []
        child_list = []
        for item in process_list:
            if item['ppid'] in [0, 1]:
                master_list.append(item)
            else:
                child_list.append(item)
        for m_item in master_list:
            m_item['child_process'] = []
            for c_item in child_list:
                if c_item['ppid'] == m_item['pid']:
                    m_item['child_process'].append(c_item)

        return master_list

    # 按内存资源获取进程列表
    def get_process_mem(self, get):
        self.pids = psutil.pids()
        process_list = []

        if 'sort' not in get: get.sort = 'uss'
        get.reverse = bool(int(get.reverse)) if 'reverse' in get else True
        limit = 1000
        for pid in self.pids:
            tmp = {}
            try:
                p = psutil.Process(pid)
            except:
                continue
            with p.oneshot():
                p_mem = p.memory_full_info()
                if p_mem.uss + p_mem.rss + p_mem.pss + p_mem.data == 0: continue
                tmp['uss'] = p_mem.uss
                tmp['rss'] = p_mem.rss
                tmp['pss'] = p_mem.pss
                tmp['vms'] = p_mem.vms
                tmp['shared'] = p_mem.shared
                # tmp['text'] = p_mem.text
                # tmp['data'] = p_mem.data
                tmp['swap'] = p_mem.swap
                tmp['exe'] = p.exe()
                tmp['name'] = p.name()
                tmp['pid'] = pid
                tmp['ppid'] = p.ppid()
                tmp['create_time'] = int(p.create_time())
                tmp['user'] = p.username()
                tmp['ps'] = self.get_process_ps(tmp['name'], pid)
            process_list.append(tmp)
            limit -= 1
            if limit <= 0: break
            del p
            del tmp
        process_list = sorted(process_list, key=lambda x: x[get.sort], reverse=get.reverse)
        # process_list = self.handle_process_list(process_list)
        data = {}
        data['process_list'] = process_list
        info = self.get_mem_info()
        data['info'] = info
        return data

    # 取内存信息
    def get_mem_info(self, get=None):
        mem = psutil.virtual_memory()
        memInfo = {'memTotal': int(mem.total/1024/1024), 'memFree': int(mem.free/1024/1024), 'memBuffers': int(mem.buffers/1024/1024), 'memCached': int(mem.cached/1024/1024)}
        memInfo['memRealUsed'] = memInfo['memTotal'] - memInfo['memFree'] - memInfo['memBuffers'] - memInfo['memCached']
        return memInfo

    # 按磁盘资源获取进程列表
    def get_process_disk(self, get):
        self.pids = psutil.pids()
        process_list = []
        if type(self.disk_read_new_info) != dict: self.disk_read_new_info = {}
        self.disk_read_new_info['time'] = time.time()
        if type(self.disk_write_new_info) != dict: self.disk_write_new_info = {}
        self.disk_write_new_info['time'] = time.time()

        if 'sort' not in get: get.sort = 'io_total_speed'
        get.reverse = bool(int(get.reverse)) if 'reverse' in get else True
        limit = 1000
        for pid in self.pids:
            tmp = {}
            try:
                p = psutil.Process(pid)
            except:
                continue
            with p.oneshot():
                pio = p.io_counters()
                tmp['io_write_bytes'] = pio.write_bytes
                tmp['io_read_bytes'] = pio.read_bytes
                tmp['io_write_speed'] = self.get_io_write(str(pid), pio.write_bytes)
                tmp['io_read_speed'] = self.get_io_read(str(pid), pio.read_bytes)
                tmp['io_total_speed'] = tmp['io_write_speed'] + tmp['io_read_speed']
                tmp['exe'] = p.exe()
                tmp['name'] = p.name()
                tmp['pid'] = pid
                tmp['ppid'] = p.ppid()
                # tmp['create_time'] = int(p.create_time())
                tmp['user'] = p.username()
                tmp['ps'] = self.get_process_ps(tmp['name'], pid)
            process_list.append(tmp)
            limit -= 1
            if limit <= 0: break
            del p
            del tmp
        public.writeFile(self.disk_read_old_path, json.dumps(self.disk_read_new_info))
        public.writeFile(self.disk_write_old_path, json.dumps(self.disk_write_new_info))
        # process_list = self.handle_process_list(process_list)
        process_list = sorted(process_list, key=lambda x: x[get.sort], reverse=get.reverse)
        data = {}
        data['process_list'] = process_list
        data['disk_info'] = self.get_disk_info()
        return data

    def get_disk_info(self, get=None):
        self.get_disk_old()
        disk_io = psutil.disk_io_counters()[:4]
        self.new_disk_info['read_count'] = disk_io[0]
        self.new_disk_info['write_count'] = disk_io[1]
        self.new_disk_info['read_bytes'] = disk_io[2]
        self.new_disk_info['write_bytes'] = disk_io[3]
        self.new_disk_info['time'] = time.time()

        if not self.old_disk_info: self.old_disk_info = {}
        if 'read_count' not in self.old_disk_info:
            time.sleep(0.1)
            disk_io = psutil.disk_io_counters()[:4]
            self.old_disk_info['read_count'] = disk_io[0]
            self.old_disk_info['write_count'] = disk_io[1]
            self.old_disk_info['read_bytes'] = disk_io[2]
            self.old_disk_info['write_bytes'] = disk_io[3]
            self.old_disk_info['time'] = time.time()

        s = self.new_disk_info['time'] - self.old_disk_info['time']
        disk_info = {}
        disk_info['read_count'] = disk_io[0]
        disk_info['write_count'] = disk_io[1]
        disk_info['read_count_s'] = int((disk_io[0] - self.old_disk_info['read_count']) / s)
        disk_info['write_count_s'] = int((disk_io[1] - self.old_disk_info['write_count']) / s)
        disk_info['read_bytes'] = disk_io[2]
        disk_info['write_bytes'] = disk_io[3]
        disk_info['read_bytes_s'] = round((float(disk_io[2]) - self.old_disk_info['read_bytes']) / s, 2)
        disk_info['write_bytes_s'] = round((float(disk_io[3]) - self.old_disk_info['write_bytes']) / s, 2)
        public.writeFile(self.old_disk_path, json.dumps(self.new_disk_info))
        return disk_info

    def get_disk_old(self):
        if self.old_disk_info: return True
        if not os.path.exists(self.old_disk_path): return False
        data = public.readFile(self.old_disk_path)
        if not data: return False
        data = json.loads(data)
        if not data: return False
        self.old_disk_info = data
        del data
        return True

    def get_process_ps(self, name, pid):
        processPs = {'mysqld': 'MySQL服务', 'php-fpm': 'PHP子进程', 'php-cgi': 'PHP-CGI进程',
                     'nginx': 'Nginx服务', 'httpd': 'Apache服务', 'sshd': 'SSH服务', 'pure-ftpd': 'FTP服务',
                     'sftp-server': 'SFTP服务', 'mysqld_safe': 'MySQL服务', 'firewalld': '防火墙服务',
                     'NetworkManager': '网络管理服务', 'svlogd': '日志守护进程', 'memcached': 'Memcached缓存器',
                     'gunicorn': "宝塔面板", "BT-Panel": '宝塔面板', 'baota_coll': "堡塔云控-主控端", 'baota_client': "堡塔云控-被控端"}
        if name in processPs: return processPs[name]
        if name == 'python':
            if self.is_panel_process(pid): return '宝塔面板'
        return name

    # 获取负载
    def get_load_average(self, get=None):
        b = public.ExecShell("uptime")[0].replace(',', '')
        c = b.split()
        data = {}
        data['1'] = float(c[-3])
        data['5'] = float(c[-2])
        data['15'] = float(c[-1])
        return data

    # 获取进程的网络连接数
    def get_connects(self, pid):
        connects = 0
        try:
            if pid == 1: return connects
            tp = '/proc/' + str(pid) + '/fd/'
            if not os.path.exists(tp): return connects
            for d in os.listdir(tp):
                fname = tp + d
                if os.path.islink(fname):
                    l = os.readlink(fname)
                    if l.find('socket:') != -1: connects += 1
        except:
            pass
        return connects

    # 判断是否是面板进程
    def is_panel_process(self, pid):
        if not self.panel_pid:
            self.panel_pid = os.getpid()
        if pid == self.panel_pid: return True
        if not self.task_pid:
            try:
                self.task_pid = int(public.ExecShell("ps aux | grep 'python task.py'|grep -v grep|head -n1|awk '{print $2}'")[0])
            except:
                self.task_pid = -1
        if pid == self.task_pid: return True
        return False

    # 获取总的cpu时间
    def get_cpu_time(self, get=None):
        if self.__cpu_time: return self.__cpu_time
        self.__cpu_time = 0.00
        s = psutil.cpu_times()
        self.__cpu_time = s.user + s.system + s.nice + s.idle
        return self.__cpu_time

    # 获取进程占用的cpu时间
    def get_process_cpu_time(self, cpu_times):
        cpu_time = 0.00
        for s in cpu_times: cpu_time += s
        return cpu_time

    # 获取进程cpu利用率
    def get_cpu_percent(self, pid, cpu_times, cpu_time):
        self.get_cpu_old()
        percent = 0.00
        process_cpu_time = self.get_process_cpu_time(cpu_times)
        if not self.cpu_old_info: self.cpu_old_info = {}
        if pid not in self.cpu_old_info:
            self.cpu_new_info[pid] = {}
            self.cpu_new_info[pid]['cpu_time'] = process_cpu_time
            return percent
        percent = round(100.00 * (process_cpu_time - self.cpu_old_info[pid]['cpu_time']) / (cpu_time - self.cpu_old_info['cpu_time']), 2)
        self.cpu_new_info[pid] = {}
        self.cpu_new_info[pid]['cpu_time'] = process_cpu_time
        if percent > 0: return percent
        return 0.00

    # 获取io写速度
    def get_io_write(self, pid, io_write):
        self.get_disk_write_old()
        disk_io_write = 0
        if not self.disk_write_old_info: self.disk_write_old_info = {}
        if pid not in self.disk_write_old_info:
            self.disk_write_new_info[pid] = {}
            self.disk_write_new_info[pid]['io_write'] = io_write
            return disk_io_write
        if 'time' not in self.disk_write_old_info: self.disk_write_old_info['time'] = self.disk_write_new_info['time']
        if 'io_write' not in self.disk_write_old_info[pid]: self.disk_write_old_info[pid]['io_write'] = self.disk_write_new_info[pid]['io_write']
        io_end = (io_write - self.disk_write_old_info[pid]['io_write'])
        if io_end > 0:
            disk_io_write = io_end / (time.time() - self.disk_write_old_info['time'])
        self.disk_write_new_info[pid] = {}
        self.disk_write_new_info[pid]['io_write'] = io_write
        if disk_io_write > 0: return int(disk_io_write)
        return 0

    # 获取io读速度
    def get_io_read(self, pid, io_read):
        self.get_disk_read_old()
        disk_io_read = 0
        if not self.disk_read_old_info: self.disk_read_old_info = {}
        if pid not in self.disk_read_old_info:
            self.disk_read_new_info[pid] = {}
            self.disk_read_new_info[pid]['io_read'] = io_read
            return disk_io_read
        if 'time' not in self.disk_read_old_info: self.disk_read_old_info['time'] = self.disk_read_new_info['time']
        if 'io_read' not in self.disk_read_old_info[pid]: self.disk_read_old_info[pid]['io_read'] = self.disk_read_new_info[pid]['io_read']
        io_end = (io_read - self.disk_read_old_info[pid]['io_read'])
        if io_end > 0:
            disk_io_read = io_end / (time.time() - self.disk_read_old_info['time'])
        self.disk_read_new_info[pid] = {}
        self.disk_read_new_info[pid]['io_read'] = io_read
        if disk_io_read > 0: return int(disk_io_read)
        return 0

    def get_cpu_old(self):
        if self.cpu_old_info: return True
        if not os.path.exists(self.cpu_old_path): return False
        data = public.readFile(self.cpu_old_path)
        if not data: return False
        data = json.loads(data)
        if not data: return False
        self.cpu_old_info = data
        del data
        return True

    def get_disk_read_old(self):
        if self.disk_read_old_info: return True
        if not os.path.exists(self.disk_read_old_path): return False
        data = public.readFile(self.disk_read_old_path)
        if not data: return False
        data = json.loads(data)
        if not data: return False
        self.disk_read_old_info = data
        del data
        return True

    def get_disk_write_old(self):
        if self.disk_write_old_info: return True
        if not os.path.exists(self.disk_write_old_path): return False
        data = public.readFile(self.disk_write_old_path)
        if not data: return False
        data = json.loads(data)
        if not data: return False
        self.disk_write_old_info = data
        del data
        return True

    # 获取指定进程的详情
    def get_process_info(self, pid):
        pid = int(pid)
        p = psutil.Process(pid)
        processInfo = {}
        p_mem = self.object_to_dict(p.memory_full_info())
        pio = p.io_counters()
        processInfo['p_cpus'] = p.cpu_times()
        processInfo['exe'] = p.exe()
        processInfo['name'] = p.name()
        processInfo['pid'] = pid
        processInfo['ppid'] = p.ppid()
        processInfo['pname'] = 'sys'
        if processInfo['ppid'] != 0: processInfo['pname'] = psutil.Process(processInfo['ppid']).name()
        processInfo['comline'] = p.cmdline()
        processInfo['create_time'] = int(p.create_time())
        processInfo['open_files'] = self.list_to_dict(p.open_files())
        processInfo['status'] = p.status()
        processInfo['user'] = p.username()
        processInfo['memory_full'] = p_mem
        processInfo['io_write_bytes'] = pio.write_bytes
        processInfo['io_read_bytes'] = pio.read_bytes
        processInfo['connects'] = self.get_connects(pid)
        processInfo['threads'] = p.num_threads()
        processInfo['ps'] = self.get_process_ps(processInfo['name'], pid)

        return processInfo

    # 获取进程详情对外接口
    def get_process_info_api(self, get):
        if not get.pid:
            return public.returnMsg(False, '请传入进程id')
        pid = int(get.pid)
        if pid not in psutil.pids(): return public.returnMsg(False, '指定进程不存在!')
        return self.get_process_info(pid)

    # 对象转字典
    def object_to_dict(self, obj):
        result = {}
        for name in dir(obj):
            value = getattr(obj, name)
            if not name.startswith('__') and not callable(value) and not name.startswith('_'): result[name] = value
        return result

    # 列表转字典
    def list_to_dict(self, data):
        result = []
        for s in data:
            result.append(self.object_to_dict(s))
        return result

    # 结束进程
    def kill_process(self, get):
        pid = int(get.pid)
        if pid < 30: return public.returnMsg(False, '不能结束系统关键进程!')
        if pid not in psutil.pids(): return public.returnMsg(False, '指定进程不存在!')
        if 'killall' not in get:
            p = psutil.Process(pid)
            if self.is_panel_process(pid): return public.returnMsg(False, '不能结束面板服务进程')
            p.kill()
            return public.returnMsg(True, '进程已结束')
        return self.kill_process_all(pid)

    # 结束进程树
    def kill_process_all(self, pid):
        if pid < 30: return public.returnMsg(True, '已结束此进程树!')
        if self.is_panel_process(pid): return public.returnMsg(False, '不能结束面板服务进程')
        try:
            if pid not in psutil.pids(): public.returnMsg(True, '已结束此进程树!')
            p = psutil.Process(pid)
            ppid = p.ppid()
            name = p.name()
            p.kill()
            public.ExecShell('pkill -9 ' + name)
            if name.find('php-') != -1:
                public.ExecShell("rm -f /tmp/php-cgi-*.sock")
            elif name.find('mysql') != -1:
                public.ExecShell("rm -f /tmp/mysql.sock")
            elif name.find('mongod') != -1:
                public.ExecShell("rm -f /tmp/mongod*.sock")
            self.kill_process_lower(pid)
            if ppid: return self.kill_process_all(ppid)
        except:
            pass
        return public.returnMsg(True, '已结束此进程树!')

    def kill_process_lower(self, pid):
        pids = psutil.pids()
        for lpid in pids:
            if lpid < 30: continue
            if self.is_panel_process(lpid): continue
            p = psutil.Process(lpid)
            ppid = p.ppid()
            if ppid == pid:
                p.kill()
                return self.kill_process_lower(lpid)
        return True

    # 获取TCP连接列表
    def get_tcp_list(self, get=None):
        if 'tcp_sort' not in get: get.tcp_sort = 'status'
        get.tcp_reverse = bool(int(get.tcp_reverse)) if 'tcp_reverse' in get else True
        netstats = psutil.net_connections(kind='tcp')
        networkList = []
        limit = 1000
        connect_count = 0
        for netstat in netstats:
            try:
                tmp = {}
                if netstat.type == 1:
                    tmp['type'] = 'tcp'
                else:
                    tmp['type'] = 'udp'
                tmp['family'] = netstat.family
                tmp['laddr'] = netstat.laddr
                tmp['raddr'] = netstat.raddr
                tmp['status'] = netstat.status
                if tmp['status'] in ['LISTEN']: continue
                p = psutil.Process(netstat.pid)
                tmp['process'] = p.name()
                # if tmp['process'] in ['gunicorn', 'baota_coll', 'baota_client']: continue
                tmp['pid'] = netstat.pid
                networkList.append(tmp)
                connect_count += 1
                limit -= 1
                if limit <= 0: break
                del p
                del tmp
            except:
                continue
        networkList = sorted(networkList, key=lambda x: x[get.tcp_sort], reverse=get.tcp_reverse)
        return networkList, connect_count

    def get_network_info(self, get=None):
        self.get_net_old()
        networkIo = psutil.net_io_counters()[:4]
        self.new_net_info['upTotal'] = networkIo[0]
        self.new_net_info['downTotal'] = networkIo[1]
        self.new_net_info['upPackets'] = networkIo[2]
        self.new_net_info['downPackets'] = networkIo[3]
        self.new_net_info['time'] = time.time()

        if not self.old_net_info: self.old_net_info = {}
        if 'upTotal' not in self.old_net_info:
            time.sleep(0.1)
            networkIo = psutil.net_io_counters()[:4]
            self.old_net_info['upTotal'] = networkIo[0]
            self.old_net_info['downTotal'] = networkIo[1]
            self.old_net_info['upPackets'] = networkIo[2]
            self.old_net_info['downPackets'] = networkIo[3]
            self.old_net_info['time'] = time.time()

        s = self.new_net_info['time'] - self.old_net_info['time']
        networkInfo = {}
        networkInfo['upTotal'] = networkIo[0]
        networkInfo['downTotal'] = networkIo[1]
        networkInfo['up'] = round((float(networkIo[0]) - self.old_net_info['upTotal']) / s, 2)
        networkInfo['down'] = round((float(networkIo[1]) - self.old_net_info['downTotal']) / s, 2)
        networkInfo['upPackets'] = networkIo[2]
        networkInfo['downPackets'] = networkIo[3]
        networkInfo['upPackets_s'] = int((networkIo[2] - self.old_net_info['upPackets']) / s)
        networkInfo['downPackets_s'] = int((networkIo[3] - self.old_net_info['downPackets']) / s)
        public.writeFile(self.old_net_path, json.dumps(self.new_net_info))
        return networkInfo

    def get_net_old(self):
        if self.old_net_info: return True
        if not os.path.exists(self.old_net_path): return False
        data = public.readFile(self.old_net_path)
        if not data: return False
        data = json.loads(data)
        if not data: return False
        self.old_net_info = data
        del data
        return True

    # 获取侦听端口列表
    def get_listen_list(self, get=None):
        if 'listen_sort' not in get: get.listen_sort = 'listen_port'
        get.listen_reverse = bool(int(get.listen_reverse)) if 'listen_reverse' in get else True
        netstats = psutil.net_connections()
        networkList = []
        limit = 1000
        listen_count = 0
        for netstat in netstats:
            try:
                tmp = {}
                if netstat.type == 1:
                    tmp['type'] = 'tcp'
                else:
                    tmp['type'] = 'udp'
                tmp['family'] = netstat.family
                tmp['listen_addr'] = netstat.laddr[0]
                tmp['listen_port'] = netstat.laddr[1]
                tmp['is_port_release'] = self.check_port_status(tmp['listen_port'])
                if netstat.status != 'LISTEN': continue
                p = psutil.Process(netstat.pid)
                tmp['process'] = p.name()
                # if tmp['process'] in ['gunicorn', 'baota_coll', 'baota_client']: continue
                tmp['pid'] = netstat.pid
                networkList.append(tmp)
                listen_count += 1
                limit -= 1
                if limit <= 0: break
                del p
                del tmp
            except:
                continue
        networkList = sorted(networkList, key=lambda x: x[get.listen_sort], reverse=get.listen_reverse)
        return networkList, listen_count

    # 判断端口在防火墙是否放行
    def check_port_status(self, port):
        release_ports = public.M('firewall').field('port').select()
        release_ports_list = [item['port'] for item in release_ports]
        for release_port in release_ports_list:
            try:
                if '-' in release_port:
                    start, end = release_port.split('-')
                    if int(start) <= port <= int(end):
                        return True
                else:
                    if port == int(release_port):
                        return True
            except:
                pass
        return False

    # 增加使用iftop收集网卡流量定时任务
    def add_iftop_task(self, get=None):
        import crontab

        if public.M('crontab').where('name=?', u'[勿删]资源管理器-获取网卡流量').count():
            return public.returnMsg(True, '定时任务已存在!')

        s_body = '''count=0
while [ $count -lt 2 ]
do
    count=$(($count+1))
    /usr/sbin/iftop -B -t -l -P -N -n -s 10 2>/dev/null |grep -A 1 -E '^   [0-9]' > {0}
    /usr/sbin/iftop -B -t -l -P -N -n -s 10 -i lo 2>/dev/null |grep -A 1 -E '^   [0-9]' > {1}
    if [[ $count == 2 ]];then
        exit
    else
        sleep 10
    fi
done'''.format(self.iftop_out, self.iftop_lo)

        p = crontab.crontab()
        args = {
            "name": u'[勿删]资源管理器-获取网卡流量',
            "type": 'minute-n',
            "where1": 1,
            "hour": '',
            "minute": '',
            "week": '',
            "sType": "toShell",
            "sName": "",
            "backupTo": "",
            "save": '',
            "sBody": s_body,
            "urladdress": "undefined"
        }
        p.AddCrontab(args)
        return public.returnMsg(True, '设置成功!')

    # 转换成以KB为单位
    def change_unit(self, unit):
        if "MB" in unit:
            flow = float(unit.strip("MB")) * 1024
        elif "KB" in unit:
            flow = float(unit.strip("KB"))
        else:
            flow = float(unit.strip("B")) / 1024
        return round(flow, 2)

    # 使用iftop命令获取网卡的流量
    def get_flow(self, get):
        if 'sort' not in get: get.sort = 'send'
        if 'reverse' not in get:
            get.reverse = True
        else:
            if int(get.reverse) == 1:
                get.reverse = True
            else:
                get.reverse = False
        # 传入lo参数代表获取内网网卡的流量
        if 'lo' in get:
            mes = public.readFile(self.iftop_lo)
        else:
            mes = public.readFile(self.iftop_out)
        iftop_list = mes.split("\n")
        count = len(iftop_list)
        flow_list = []

        for i in range(count // 2):
            try:
                tmp = {}
                # 获取发送的流量
                location_li_s = iftop_list[i*2]
                send_flow_lists = location_li_s.split()
                print(send_flow_lists)
                tmp['local_addr'] = send_flow_lists[1]
                send_flow = send_flow_lists[3]
                send_flow_float = self.change_unit(send_flow)
                tmp['send'] = send_flow_float

                # 获取接收的流量
                location_li_r = iftop_list[i*2+1]
                rec_flow_lists = location_li_r.split()
                print(rec_flow_lists)
                tmp['remote_addr'] = rec_flow_lists[0]
                rec_flow = rec_flow_lists[2]
                rec_flow_float = self.change_unit(rec_flow)
                tmp['recv'] = rec_flow_float
                flow_list.append(tmp)
                del tmp
            except:
                continue
        flow_list = sorted(flow_list, key=lambda x: x[get.sort], reverse=get.reverse)
        return flow_list

    # 增加进程到系统加固白名单
    def add_process_white(self, process_name):
        if os.path.exists('/www/server/panel/plugin/syssafe'):
            sys.path.append('/www/server/panel/plugin/syssafe')
            try:
                from syssafe_main import syssafe_main

                get = public.dict_obj()
                c = syssafe_main()
                safe_status = c.get_safe_status(get)

                if safe_status['open'] and safe_status['list'][6]['open']:
                    get.process_name = process_name
                    c.add_process_white(get)
            except:pass

    # 增加使用nethogs收集进程流量定时任务
    def add_nethogs_task(self, get=None):
        #self.add_process_white('nethogs')
        import crontab

        if public.M('crontab').where('name=?', u'[勿删]资源管理器-获取进程流量').count():
            return public.returnMsg(True, '定时任务已存在!')

        s_body = '''ps -ef | grep nethogs | grep -v grep | awk '{print $2}' | xargs kill 2>/dev/null
count=0
while [ $count -lt 2 ]
do
    count=$(($count+1))
    /usr/sbin/nethogs -t -a -d 2 -c 5 > %s 2>/dev/null
    if [[ $count == 2 ]];then
        exit
    else
        sleep 20
    fi
done''' % self.nethogs_out

        p = crontab.crontab()
        args = {
            "name": u'[勿删]资源管理器-获取进程流量',
            "type": 'minute-n',
            "where1": 5,
            "hour": '',
            "minute": '',
            "week": '',
            "sType": "toShell",
            "sName": "",
            "backupTo": "",
            "save": '',
            "sBody": s_body,
            "urladdress": "undefined"
        }
        p.AddCrontab(args)
        return public.returnMsg(True, '设置成功!')

    # 获取进程的流量
    def get_process_flow(self, get=None):
        if not os.path.exists('/usr/sbin/nethogs'):
            return public.returnMsg(False, 'nethogs未安装成功!')
        if 'flow_sort' not in get: get.flow_sort = 'send'
        get.flow_reverse = bool(int(get.flow_reverse)) if 'flow_reverse' in get else True
        try:
            message = public.readFile(self.nethogs_out)
            mes_sp = message.split("Refreshing:")
            resu_str = mes_sp[-1].strip("\n")
            resu_li = resu_str.split("\n")
            process_list = []
            for proc in resu_li:
                try:
                    proc_li = proc.split("\t")
                    if len(proc_li) == 3:
                        tmp = {}
                        tmp_list = proc_li[0].split('/')
                        pid = int(tmp_list[-2])
                        if pid in [0, 1, 2]: continue
                        process_info = self.get_process_info(pid)
                        tmp['pid'] = process_info['pid']
                        tmp['name'] = process_info['name']
                        tmp['exe'] = process_info['exe']
                        tmp['ps'] = process_info['ps']
                        tmp['send'] = round(float(proc_li[1]), 2)
                        tmp['recv'] = round(float(proc_li[2]), 2)
                        process_list.append(tmp)
                        del tmp
                except: continue
            process_list = sorted(process_list, key=lambda x: x[get.flow_sort], reverse=get.flow_reverse)
            return process_list
        except:
            return public.returnMsg(False, public.get_error_info())

    # 获取网络相关
    def get_network(self, get):
        data = {}
        data['network_info'] = self.get_network_info(get)
        data['process_flow_list'] = self.get_process_flow(get)
        data['tcp_list'], data['network_info']['tcp_count'] = self.get_tcp_list(get)
        data['listen_list'], data['network_info']['listen_count'] = self.get_listen_list(get)
        return data

    # 将json格式的文件转换成字典
    def __get_file_json(self, filename):
        try:
            if not os.path.exists(filename): return {}
            return json.loads(public.readFile(filename))
        except:
            return {}

    # 获取指定网站当天的请求数
    def get_site_request(self, site_name):
        today = time.strftime('%Y-%m-%d', time.localtime())

        # path = '/www/server/total/total/' + site_name + '/request/' + today + '.json'
        path = '/www/server/total/logs/' + site_name + '/total.db'
        request_count = 0
        if os.path.exists(path):
            try:
                pass
                conn = None
                cur = None
                import sqlite3
                conn = sqlite3.connect(path)
                cur = conn.cursor()
                local_time = time.localtime()
                time_key_format = "%Y%m%d00"
                start = int(time.strftime(time_key_format, local_time))
                time_key_format = "%Y%m%d23"
                end = int(time.strftime(time_key_format, local_time))
                select_sql = "select sum(req) from request_stat where time>={} and time<={}".format(start, end)
                selector = cur.execute(select_sql)
                result = selector.fetchone()
                request_count = result[0]
                if request_count is None:
                    request_count = 0
            except:
                pass
            finally:
                cur and cur.close()
                conn and conn.close()
        return request_count

    # 获取网站列表
    def get_sites(self, get=None):
        sites = public.M('sites').field('id,name,status').select()
        site_list = []
        if type(self.new_site_info) != dict: self.new_site_info = {}
        self.new_site_info['time'] = time.time()

        if 'sort' not in get: get.sort = 'day_request'
        get.reverse = bool(int(get.reverse)) if 'reverse' in get else True
        for site in sites:
            tmp = site
            tmp['day_request'] = self.get_site_request(site['name'])
            tmp['qps'] = self.get_site_qps(site['name'])
            site_list.append(tmp)
            del tmp
        public.writeFile(self.old_site_path, json.dumps(self.new_site_info))
        site_list = sorted(site_list, key=lambda x: x[get.sort], reverse=get.reverse)
        data = {}
        data['site_list'] = site_list
        return data

    def get_realtime_request(self, site=None):
        """获取实时请求数"""
        request_count = 0
        if site is not None:
            log_file = "/www/server/total/logs/{}/req_sec.json".format(site)
            if not os.path.isfile(log_file):
                return 0
            import datetime
            datetime_now = datetime.datetime.now()
            req_data = public.readFile(log_file)
            lines = req_data.split("\n")
            for line in lines:
                if not line: continue
                try:
                    _rt_req, _write_time = line.split(",")
                    datetime_log = datetime.datetime.fromtimestamp(
                        float(_write_time))
                    # print(datetime_log.strftime("%y%m%d %H:%M:%S"))
                    datetime_interval = datetime_now - datetime_log
                    # print("interval:", datetime_interval.seconds)
                    if datetime_interval.seconds < 3:
                        req = int(_rt_req)
                        request_count += req
                        # data = {"timestamp": _write_time, "req": int(_rt_req)}
                        # res_data.append(data)
                except Exception as e:
                    print("Real-time data error:", str(e))
        return request_count

    # 获取网站qps
    def get_site_qps(self, site_name):
        return self.get_realtime_request(site=site_name)

    # 获取网站旧的请求数
    def get_site_old(self):
        if self.old_site_info: return True
        if not os.path.exists(self.old_site_path): return False
        data = public.readFile(self.old_site_path)
        if not data: return False
        data = json.loads(data)
        if not data: return False
        self.old_site_info = data
        del data
        return True

    # 停止站点
    def stop_site(self, get):
        path = self.setupPath + '/stop'
        id = get.id
        if not os.path.exists(path):
            os.makedirs(path)
            public.downloadFile('http://download.bt.cn/stop.html', path + '/index.html')

        binding = public.M('binding').where('pid=?', (id,)).field('id,pid,domain,path,port,addtime').select()
        for b in binding:
            bpath = path + '/' + b['path']
            if not os.path.exists(bpath):
                public.ExecShell('mkdir -p ' + bpath)
                public.ExecShell('ln -sf ' + path + '/index.html ' + bpath + '/index.html')

        site_path = public.M('sites').where("id=?", (id,)).getField('path')
        site_name = public.M('sites').where("id=?", (id,)).getField('name')

        # nginx
        file = self.setupPath + '/panel/vhost/nginx/' + site_name + '.conf'
        conf = public.readFile(file)
        if conf:
            conf = conf.replace(site_path, path)
            conf = conf.replace("include", "#include")
            public.writeFile(file, conf)

        # apache
        file = self.setupPath + '/panel/vhost/apache/' + site_name + '.conf'
        conf = public.readFile(file)
        if conf:
            conf = conf.replace(site_path, path)
            conf = conf.replace("IncludeOptional", "#IncludeOptional")
            public.writeFile(file, conf)
        public.M('sites').where("id=?", (id,)).setField('status', '0')
        public.serviceReload()
        public.WriteLog('TYPE_SITE', 'SITE_STOP_SUCCESS', (site_name,))
        return public.returnMsg(True, 'SITE_STOP_SUCCESS')

    # 启动站点
    def start_site(self, get):
        id = get.id
        Path = self.setupPath + '/stop'
        site_path = public.M('sites').where("id=?", (id,)).getField('path')
        site_name = public.M('sites').where("id=?", (id,)).getField('name')

        # nginx
        file = self.setupPath + '/panel/vhost/nginx/' + site_name + '.conf'
        conf = public.readFile(file)
        if conf:
            conf = conf.replace(Path, site_path)
            conf = conf.replace("#include", "include")
            public.writeFile(file, conf)
        # apaceh
        file = self.setupPath + '/panel/vhost/apache/' + site_name + '.conf'
        conf = public.readFile(file)
        if conf:
            conf = conf.replace(Path, site_path)
            conf = conf.replace("#IncludeOptional", "IncludeOptional")
            public.writeFile(file, conf)

        public.M('sites').where("id=?", (id,)).setField('status', '1')
        public.serviceReload()
        public.WriteLog('TYPE_SITE', 'SITE_START_SUCCESS', (site_name,))
        return public.returnMsg(True, 'SITE_START_SUCCESS')
