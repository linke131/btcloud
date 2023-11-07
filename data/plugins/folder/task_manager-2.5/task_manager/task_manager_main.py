# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import json
import re
# +--------------------------------------------------------------------
# |   宝塔任务管理器
# +--------------------------------------------------------------------
import sys
import traceback
from typing import List, Dict

if not 'class/' in sys.path:
    sys.path.append('class/')
import psutil, os, time, public

try:
    from BTPanel import cache
except:
    import cachelib

    cache = cachelib.SimpleCache()


class task_manager_main:
    Pids = None
    __cpu_time = None
    new_info = {}
    old_info = {}
    new_net_info = {}
    old_net_info = {}
    old_path = '/tmp/bt_task_old.json'
    old_net_path = '/tmp/bt_network_old.json'
    panel_pid = None
    task_pid = None
    __process_net_list = {}
    meter_head = {}

    # 获取当前网络连接信息
    def get_network_list(self, get):
        netstats = psutil.net_connections()
        networkList = []
        for netstat in netstats:
            tmp = {}
            if netstat.type == 1:
                tmp['type'] = 'tcp'
            else:
                tmp['type'] = 'udp'
            tmp['family'] = netstat.family
            tmp['laddr'] = netstat.laddr
            tmp['raddr'] = netstat.raddr
            tmp['status'] = netstat.status
            p = psutil.Process(netstat.pid)
            tmp['process'] = p.name()
            if tmp['process'] in ['BT-Panel', 'gunicorn', 'baota_coll', 'baota_client']: continue
            tmp['pid'] = netstat.pid
            networkList.append(tmp)
            del (p)
            del (tmp)
        networkList = sorted(networkList, key=lambda x: x['status'], reverse=True)
        data = {}
        data['list'] = networkList
        data['state'] = self.get_network()
        if hasattr(get, 'search'):
            if get.search != '':
                data['list'] = self.search_network(data['list'], get.search)
        return data

    # 查询网络
    def search_network(self, data, search):
        try:
            ldata = []
            for i in data:
                if search in i['process'] or search in i['status'] or search in str(i['pid']) or search in i['laddr'][
                    0] or search in str(
                    i['laddr'][1]):
                    ldata.append(i)
                    continue
                if i['raddr'] != 'NONE':
                    for j in i['raddr']:
                        if search in str(j):
                            ldata.append(i)
            return ldata
        except:
            return data

    # get_network_list ——>引用get_network
    def get_network(self):
        try:
            self.get_net_old()
            networkIo = psutil.net_io_counters()[:4]
            self.new_net_info['upTotal'] = networkIo[0]
            self.new_net_info['downTotal'] = networkIo[1]
            self.new_net_info['upPackets'] = networkIo[2]
            self.new_net_info['downPackets'] = networkIo[3]
            self.new_net_info['time'] = time.time()

            if not self.old_net_info: self.old_net_info = {}
            if not 'upTotal' in self.old_net_info:
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
            networkInfo['downPackets'] = networkIo[3]
            networkInfo['upPackets'] = networkIo[2]
            networkInfo['downPackets_s'] = int((networkIo[3] - self.old_net_info['downPackets']) / s)
            networkInfo['upPackets_s'] = int((networkIo[2] - self.old_net_info['upPackets']) / s)
            cache.set(self.old_net_path, self.new_net_info, 600)
            return networkInfo
        except:
            return None

    # 获取用户列表  从/etc/passwd文件中读取
    def get_user_list(self, get):
        tmpList = public.readFile('/etc/passwd').split("\n")
        userList = []
        self.groupList = self.get_group_list(get)
        for ul in tmpList:
            tmp = ul.split(':')
            if len(tmp) < 6: continue
            userInfo = {}
            userInfo['username'] = tmp[0]
            userInfo['uid'] = tmp[2]
            userInfo['gid'] = tmp[3]
            userInfo['group'] = self.get_group_name(tmp[3])
            userInfo['ps'] = self.get_user_ps(tmp[0], tmp[4])
            userInfo['home'] = tmp[5]
            userInfo['login_shell'] = tmp[6]
            userList.append(userInfo)
        if hasattr(get, 'search'):
            if get.search != '':
                userList = self.search_user(userList, get.search)
        return userList

    # 查询用户
    def search_user(self, data, search):
        try:
            ldata = []
            for i in data:
                if search in i['username'] or search in i['ps'] or search in i['login_shell'] or search in i[
                    'home'] or search in i['group']:
                    ldata.append(i)
            return ldata
        except:
            public.print_log(traceback.format_exc())
            return data

    # 用户名注释：ps   get_user_list——>引用get_user_ps
    def get_user_ps(self, name, ps):
        userPs = {'www': '宝塔面板', 'root': '超级管理员', 'mysql': '用于运行MySQL的用户',
                  'mongo': '用于运行MongoDB的用户',
                  'git': 'git用户', 'mail': 'mail', 'nginx': '第三方nginx用户', 'postfix': 'postfix邮局用户',
                  'lp': '打印服务帐号',
                  'daemon': '控制后台进程的系统帐号', 'nobody': '匿名帐户', 'bin': '管理大部分命令的帐号',
                  'adm': '管理某些管理文件的帐号', 'smtp': 'smtp邮件'}
        if name in userPs: return userPs[name]
        if not ps: return name
        return ps

    # 外部接口，删除用户，不能删除系统运行环境用户
    def remove_user(self, get):
        users = ['www', 'root', 'mysql', 'shutdown', 'postfix', 'smmsp', 'sshd', 'systemd-network', 'systemd-bus-proxy',
                 'avahi-autoipd', 'mail', 'sync', 'lp', 'adm', 'bin', 'mailnull', 'ntp', 'daemon', 'sys'];
        if get.user in users: return public.returnMsg(False, '不能删除系统和环境关键用户!')
        r = public.ExecShell("userdel " + get.user)
        if r[1].find('process') != -1:
            try:
                pid = r[1].split()[-1]
                p = psutil.Process(int(pid))
                pname = p.name()
                p.kill()
                public.ExecShell("pkill -9 " + pname)
                r = public.ExecShell("userdel " + get.user)
            except:
                pass
        if r[1].find('userdel:') != -1: return public.returnMsg(False, r[1]);
        return public.returnMsg(True, '删除成功!')

    # 获取用户组处理函数  get_user_list——>引用get_group_name
    def get_group_name(self, gid):
        for g in self.groupList:
            if g['gid'] == gid: return g['group']
        return ''

    # 获取服务器的组名和id，从/etc/group中读取。存储到self.groupList,get_user_list——>引用get_group_list
    def get_group_list(self, get):
        tmpList = public.readFile('/etc/group').split("\n")
        groupList = []
        for gl in tmpList:
            tmp = gl.split(':')
            if len(tmp) < 3: continue
            groupInfo = {}
            groupInfo['group'] = tmp[0]
            groupInfo['gid'] = tmp[2]
            groupList.append(groupInfo)
        return groupList;

    # 外部接口 查询服务启动级别 /etc/init.d/
    def get_service_list(self, get):
        init_d = '/etc/init.d/'
        serviceList = []
        for sname in os.listdir(init_d):
            try:
                if str(oct(os.stat(init_d + sname).st_mode)[-3:]) == '644': continue
                serviceInfo = {}
                runlevels = self.get_runlevel(sname)
                serviceInfo['name'] = sname
                serviceInfo['runlevel_0'] = runlevels[0]
                serviceInfo['runlevel_1'] = runlevels[1]
                serviceInfo['runlevel_2'] = runlevels[2]
                serviceInfo['runlevel_3'] = runlevels[3]
                serviceInfo['runlevel_4'] = runlevels[4]
                serviceInfo['runlevel_5'] = runlevels[5]
                serviceInfo['runlevel_6'] = runlevels[6]
                serviceInfo['ps'] = self.get_run_ps(sname)
                serviceList.append(serviceInfo)
            except:
                continue

        data = {}
        data['runlevel'] = self.get_my_runlevel()
        data['serviceList'] = sorted(serviceList, key=lambda x: x['name'], reverse=False)
        data['serviceList'] = self.get_systemctl_list(data['serviceList'], data['runlevel'])
        if hasattr(get, 'search'):
            if get.search != '':
                data['serviceList'] = self.search_service(data['serviceList'], get.search)
        return data

    def search_service(self, data, search):
        try:
            ldata = []
            for i in data:
                if search in i['name'] or search in i['ps']:
                    ldata.append(i)
            return ldata
        except:
            return data

    # 获取系统服务运行级别   get_service_list——>引用get_systemctl_list
    def get_systemctl_list(self, serviceList, runlevel):
        systemctl_user_path = '/usr/lib/systemd/system/'
        systemctl_run_path = '/etc/systemd/system/multi-user.target.wants/'
        if not os.path.exists(systemctl_user_path) or not os.path.exists(systemctl_run_path): return serviceList
        r = '.service'
        for d in os.listdir(systemctl_user_path):
            if d.find(r) == -1: continue;
            if not self.cont_systemctl(d): continue;
            isrun = '<span style="color:red;" title="点击开启">关闭</span>'
            serviceInfo = {}
            serviceInfo['name'] = d.replace(r, '')
            serviceInfo['runlevel_0'] = isrun
            serviceInfo['runlevel_1'] = isrun
            serviceInfo['runlevel_2'] = isrun
            serviceInfo['runlevel_3'] = isrun
            serviceInfo['runlevel_4'] = isrun
            serviceInfo['runlevel_5'] = isrun
            serviceInfo['runlevel_6'] = isrun
            if os.path.exists(systemctl_run_path + d):
                isrun = '<span style="color:green;" title="点击关闭">开启</span>'
                serviceInfo['runlevel_' + runlevel] = isrun
                serviceInfo['runlevel_3'] = isrun
                serviceInfo['runlevel_5'] = isrun

            serviceInfo['ps'] = self.get_run_ps(serviceInfo['name'])
            serviceList.append(serviceInfo)
        return serviceList

    # 检查服务是否为系统服务get_systemctl_list——>引用cont_systemctl
    def cont_systemctl(self, name):
        conts = ['systemd', 'rhel', 'plymouth', 'rc-', '@', 'init', 'ipr', 'dbus', '-local']
        for c in conts:
            if name.find(c) != -1: return False
        return True

    # 外部接口，设置软件运行环境，不能设置0，6
    def set_runlevel_state(self, get):
        if get.runlevel == '0' or get.runlevel == '6': return public.returnMsg(False,
                                                                               '为安全考虑,不能通过面板直接修改此运行级别')
        systemctl_user_path = '/usr/lib/systemd/system/'
        systemctl_run_path = '/etc/systemd/system/multi-user.target.wants/'
        if os.path.exists(systemctl_user_path + get.serviceName + '.service'):
            runlevel = public.ExecShell('runlevel')[0].split()[1]
            if get.runlevel != runlevel: return public.returnMsg(False,
                                                                 'Systemctl托管的服务不能设置非当前运行级别的状态')
            action = 'enable'
            if os.path.exists(systemctl_run_path + get.serviceName + '.service'): action = 'disable'
            public.ExecShell('systemctl ' + action + ' ' + get.serviceName + '.service')
            return public.returnMsg(True, '设置成功!')

        rc_d = '/etc/rc' + get.runlevel + '.d/'
        import shutil;
        for d in os.listdir(rc_d):
            if d[3:] != get.serviceName: continue
            sfile = rc_d + d
            c = 'S'
            if d[:1] == 'S': c = 'K'
            dfile = rc_d + c + d[1:]
            shutil.move(sfile, dfile)
            return public.returnMsg(True, '设置成功!')
        return public.returnMsg(False, '设置失败!')

    # 获取name服务的运行级别 get_service_list ——>引用get_runlevel
    def get_runlevel(self, name):
        rc_d = '/etc/'
        runlevels = []
        for i in range(7):
            isrun = '<span style="color:red;" title="点击开启">关闭</span>'
            for d in os.listdir(rc_d + 'rc' + str(i) + '.d'):
                if d[3:] == name:
                    if d[:1] == 'S': isrun = '<span style="color:green;" title="点击关闭">开启</span>'
            runlevels.append(isrun)
        return runlevels

    # 外部接口，删除服务。不能删除bt
    def remove_service(self, get):
        if get.serviceName == 'bt': return public.returnMsg(False, '不能通过面板结束宝塔面板服务!')
        systemctl_user_path = '/usr/lib/systemd/system/'
        if os.path.exists(systemctl_user_path + get.serviceName + '.service'):  return public.returnMsg(False,
                                                                                                        'Systemctl托管的服务不能通过面板删除');
        public.ExecShell('service ' + get.serviceName + ' stop')
        if os.path.exists('/usr/sbin/update-rc.d'):
            public.ExecShell('update-rc.d ' + get.serviceName + ' remove')
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
        return public.returnMsg(True, '删除成功!')

    # 外部接口，结束进程，pid30以上
    def kill_process(self, get):
        pid = int(get.pid)
        if pid < 30: return public.returnMsg(False, '不能结束系统关键进程!')
        if not pid in psutil.pids(): return public.returnMsg(False, '指定进程不存在!')
        if not 'killall' in get:
            p = psutil.Process(pid)
            if self.is_panel_process(pid): return public.returnMsg(False, '不能结束面板服务进程')
            p.kill()
            return public.returnMsg(True, '进程已结束')
        return self.kill_process_all(pid)

    # 结束进程树 kill_process——>引用kill_process_all
    def kill_process_all(self, pid):
        public.print_log(pid)
        if pid < 30: return public.returnMsg(True, '已结束此进程树!')
        if self.is_panel_process(pid): return public.returnMsg(False, '不能结束面板服务进程')
        try:
            if not pid in psutil.pids(): public.returnMsg(True, '已结束此进程树!')
            p = psutil.Process(pid)
            ppid = p.ppid()
            name = p.name()
            p.kill()
            public.ExecShell('pkill -9 ' + name)
            if name.find('php-') != -1:
                public.ExecShell("rm -f /tmp/php-cgi-*.sock")
            elif name.find('mysql') != -1:
                public.ExecShell("rm -f /tmp/mysql.sock")
            elif name.find('nginx') != -1:
                public.ExecShell("rm -f /tmp/mysql.sock")
            self.kill_process_lower(pid)
            if ppid: return self.kill_process_all(ppid)
        except:
            pass
        return public.returnMsg(True, '已结束此进程树!')

    # 遍历结束pid的子进程 kill_process_all——>引用kill_process_lower
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

    # 是否为面板进程
    def is_panel_process(self, pid):
        if not self.panel_pid:
            self.panel_pid = os.getpid()
        if pid == self.panel_pid: return True
        if not self.task_pid:
            try:
                self.task_pid = int(
                    public.ExecShell("ps aux | grep 'python task.py'|grep -v grep|head -n1|awk '{print $2}'")[0])
            except:
                self.task_pid = -1
        if pid == self.task_pid: return True
        return False

    # 外部接口 强制结束会话
    def pkill_session(self, get):
        public.ExecShell("pkill -kill -t " + get.pts)
        return public.returnMsg(True, '已强行结束会话[' + get.pts + ']')

    # 获取启动项
    def get_run_list(self, get):
        runFile = ['/etc/rc.local', '/etc/profile', '/etc/inittab', '/etc/rc.sysinit']
        runList = []
        for rfile in runFile:
            if not os.path.exists(rfile): continue
            bodyR = self.clear_comments(public.readFile(rfile))
            if not bodyR: continue
            stat = os.stat(rfile)
            accept = str(oct(stat.st_mode)[-3:])
            if accept == '644': continue
            tmp = {}
            tmp['name'] = rfile
            tmp['srcfile'] = rfile
            tmp['size'] = os.path.getsize(rfile)
            tmp['access'] = accept
            tmp['ps'] = self.get_run_ps(rfile)
            # tmp['body'] = bodyR
            runList.append(tmp)
        runlevel = self.get_my_runlevel()
        runPath = ['/etc/init.d', '/etc/rc' + runlevel + '.d']
        tmpAll = []
        islevel = False
        for rpath in runPath:
            if not os.path.exists(rpath): continue
            if runPath[1] == rpath: islevel = True
            for f in os.listdir(rpath):
                if f[:1] != 'S': continue
                filename = rpath + '/' + f
                if not os.path.exists(filename): continue
                if os.path.isdir(filename): continue
                if os.path.islink(filename):
                    flink = os.readlink(filename).replace('../', '/etc/')
                    if not os.path.exists(flink): continue
                    filename = flink
                tmp = {}
                tmp['name'] = f
                if islevel: tmp['name'] = f[3:]
                if tmp['name'] in tmpAll: continue
                stat = os.stat(filename)
                accept = str(oct(stat.st_mode)[-3:])
                if accept == '644': continue
                tmp['srcfile'] = filename
                tmp['access'] = accept
                tmp['size'] = os.path.getsize(filename)
                tmp['ps'] = self.get_run_ps(tmp['name'])
                runList.append(tmp)
                tmpAll.append(tmp['name'])
        data = {}
        data['run_list'] = runList
        data['run_level'] = runlevel
        if hasattr(get, 'search'):
            if get.search != '':
                data['run_list'] = self.search_run(data['run_list'], get.search)
        return data

    # 启动项查询
    def search_run(self, data, search):
        try:
            ldata = []
            for i in data:
                if search in i['name'] or search in i['srcfile'] or search in i['ps']:
                    ldata.append(i)
            return ldata
        except:
            return data

    # 服务注释 get_service_list——>引用 get_run_ps
    def get_run_ps(self, name):
        runPs = {'netconsole': '网络控制台日志', 'network': '网络服务', 'jexec': 'JAVA', 'tomcat8': 'Apache Tomcat',
                 'tomcat7': 'Apache Tomcat', 'mariadb': 'Mariadb',
                 'tomcat9': 'Apache Tomcat', 'tomcat': 'Apache Tomcat', 'memcached': 'Memcached缓存器',
                 'php-fpm-53': 'PHP-5.3', 'php-fpm-52': 'PHP-5.2',
                 'php-fpm-54': 'PHP-5.4', 'php-fpm-55': 'PHP-5.5', 'php-fpm-56': 'PHP-5.6', 'php-fpm-70': 'PHP-7.0',
                 'php-fpm-71': 'PHP-7.1',
                 'php-fpm-72': 'PHP-7.2', 'rsync_inotify': 'rsync实时同步', 'pure-ftpd': 'FTP服务',
                 'mongodb': 'MongoDB', 'nginx': 'Web服务器(Nginx)',
                 'httpd': 'Web服务器(Apache)', 'bt': '宝塔面板', 'mysqld': 'MySQL数据库', 'rsynd': 'rsync主服务',
                 'php-fpm': 'PHP服务', 'systemd': '系统核心服务',
                 '/etc/rc.local': '用户自定义启动脚本', '/etc/profile': '全局用户环境变量',
                 '/etc/inittab': '用于自定义系统运行级别', '/etc/rc.sysinit': '系统初始化时调用的脚本',
                 'sshd': 'SSH服务', 'crond': '计划任务服务', 'udev-post': '设备管理系统', 'auditd': '审核守护进程',
                 'rsyslog': 'rsyslog服务', 'sendmail': '邮件发送服务', 'blk-availability': 'lvm2相关',
                 'local': '用户自定义启动脚本', 'netfs': '网络文件系统', 'lvm2-monitor': 'lvm2相关',
                 'xensystem': 'xen云平台相关', 'iptables': 'iptables防火墙', 'ip6tables': 'iptables防火墙 for IPv6',
                 'firewalld': 'firewall防火墙'}
        if name in runPs: return runPs[name]
        return name

    # 清除注释
    def clear_comments(self, body):
        bodyTmp = body.split("\n")
        bodyR = ""
        for tmp in bodyTmp:
            if tmp.startswith('#'): continue
            if tmp.strip() == '': continue
            bodyR += tmp
        return bodyR

    # 外部接口，获取启动项的文件
    def get_file_body(self, get):
        get.path = get.path.encode('utf-8')
        if not os.path.exists(get.path): return public.returnMsg(False, 'FILE_NOT_EXISTS')
        if os.path.getsize(get.path) > 2097152: return public.returnMsg(False, '不能在线获取大于2MB的文件内容!')
        return self.clear_comments(public.readFile(get.path))

    # 外部接口，获取计划任务列表
    def get_cron_list(self, get):
        filename = self.get_cron_file()
        tmpList = public.readFile(filename).split("\n")
        cronList = []
        for c in tmpList:
            c = c.strip()
            if c.startswith('#'): continue
            tmp = c.split(' ')
            if len(tmp) < 6: continue
            cronInfo = {}
            cronInfo['cycle'] = self.decode_cron_cycle(tmp)
            if not cronInfo['cycle']: continue
            ctmp = self.decode_cron_connand(tmp)
            cronInfo['command'] = c
            cronInfo['ps'] = ctmp[1]
            cronInfo['exe'] = ctmp[2]
            cronInfo['test'] = ctmp[0]
            cronList.append(cronInfo)
        if hasattr(get, 'search'):
            if get.search != '':
                cronList = self.search_cron(cronList, get.search)
        return cronList

    def search_cron(self, data, search):
        try:
            ldata = []
            for i in data:
                if search in i['command'] or search in i['cycle'] or search in i['ps']:
                    ldata.append(i)
            return ldata
        except:
            return data

    # 外部接口，删除计划任务
    def remove_cron(self, get):
        index = int(get.index)
        cronList = self.get_cron_list(get)
        if index > len(cronList) + 1: return public.returnMsg(False, '指定任务不存在!')
        toCron = []
        for i in range(len(cronList)):
            if i == index: continue
            toCron.append(cronList[i]['command'])
        cronStr = "\n".join(toCron) + "\n\n"
        filename = self.get_cron_file()
        public.writeFile(filename, cronStr)
        public.ExecShell("chmod 600 " + filename)
        self.CrondReload()
        return public.returnMsg(True, '删除成功!')

    # 重启cron服务
    def CrondReload(self):
        if os.path.exists('/etc/init.d/crond'):
            public.ExecShell('/etc/init.d/crond reload')
        elif os.path.exists('/etc/init.d/cron'):
            public.ExecShell('service cron restart')
        else:
            public.ExecShell("systemctl reload crond")

    # 添加计划任务备注
    def decode_cron_connand(self, tmp):
        command = ''
        for i in range(len(tmp)):
            if i < 5: continue
            command += tmp[i] + ' '
        ps = '未知任务'
        if command.find('/www/server/cron') != -1:
            ps = '通过宝塔面板添加的计划任务'
        elif command.find('.acme.sh') != -1:
            ps = '基于acme.sh的Let\'s Encrypt证书续签任务'
        elif command.find('certbot-auto renew') != -1:
            ps = '基于certbot的Let\'s Encrypt证书续签任务'

        tmpScript = command.split('>')[0].strip()
        filename = tmpScript.replace('"', '').split()[0]
        # if not os.path.exists(filename): filename = '';
        return command.strip(), ps, filename

    # 解析计划任务执行周期
    def decode_cron_cycle(self, tmp):
        if not tmp[4]: tmp[4] = '*'
        if tmp[4] != '*':
            cycle = '每周' + self.toWeek(int(tmp[4])) + '的' + tmp[1] + '时' + tmp[0] + '分'
        elif tmp[2] != '*':
            if tmp[2].find('*') == -1:
                cycle = '每月的' + tmp[2] + '日,' + tmp[1] + '时' + tmp[0] + '分'
            else:
                cycle = '每隔' + tmp[2].split('/')[1] + '天' + tmp[1] + '时' + tmp[0] + '分'
        elif tmp[1] != '*':
            if tmp[1].find('*') == -1:
                cycle = '每天的' + tmp[1] + '时' + tmp[0] + '分'
            else:
                cycle = '每隔' + tmp[1].split('/')[1] + '小时' + tmp[0] + '分钟'
        elif tmp[0] != '*':
            if tmp[0].find('*') == -1:
                cycle = '每小时的第' + tmp[0] + '分钟'
            else:
                cycle = '每隔' + tmp[0].split('/')[1] + '分钟'
        else:
            return None
        return cycle

    # 数转周
    def toWeek(self, num):
        if num > 6: return ''
        wheres = {
            0: public.getMsg('CRONTAB_SUNDAY'),
            1: public.getMsg('CRONTAB_MONDAY'),
            2: public.getMsg('CRONTAB_TUESDAY'),
            3: public.getMsg('CRONTAB_WEDNESDAY'),
            4: public.getMsg('CRONTAB_THURSDAY'),
            5: public.getMsg('CRONTAB_FRIDAY'),
            6: public.getMsg('CRONTAB_SATURDAY')
        }

        return wheres[num]

    # 获取存放计划任务的路径
    def get_cron_file(self):
        filename = '/var/spool/cron/crontabs/root'
        if os.path.exists(filename): return filename
        filename = '/var/spool/cron/root'
        if not os.path.exists(filename):
            public.writeFile(filename, "")
        return filename

    # ？？？
    def get_exp_user(self, get):
        exp = {}
        exp['bash_profile'] = self.clear_comments(public.readFile('/root/.bash_profile'))
        exp['bash_logout'] = self.clear_comments(public.readFile('/root/.bash_logout'))
        return exp

    # 获取当前会话
    def get_who(self, get):
        whoTmp = public.ExecShell('who')[0]
        tmpList = whoTmp.split("\n")
        whoList = []
        for w in tmpList:
            tmp = w.split()
            if len(tmp) < 5: continue
            whoInfo = {}
            whoInfo['user'] = tmp[0]
            whoInfo['pts'] = tmp[1]
            whoInfo['date'] = tmp[2] + ' ' + tmp[3]
            whoInfo['ip'] = tmp[4].replace('(', '').replace(')', '')
            if len(tmp) > 5:
                whoInfo['date'] = tmp[2] + ' ' + tmp[3] + ' ' + tmp[4]
                whoInfo['ip'] = tmp[5].replace('(', '').replace(')', '')
            whoList.append(whoInfo)
        if hasattr(get, 'search'):
            if get.search != '':
                whoList = self.search_who(whoList, get.search)
        return whoList

    def search_who(self, data, search):
        try:
            ldata = []
            for i in data:
                if search in i['user'] or search in i['ip'] or search in i['date']:
                    ldata.append(i)
            return ldata
        except:
            return data

    # 获取python的路径
    def get_python_bin(self):
        bin_file = '/www/server/panel/pyenv/bin/python'
        if os.path.exists(bin_file):
            return bin_file
        return '/usr/bin/python'

    # 检查process_network_total.py是否运行
    def check_process_net_total(self):
        '''
            @name 检查网络监控进程是否运行
            @author hwliang<2021-09-13>
            @return void
        '''
        _pid_file = '/www/server/panel/logs/process_network_total.pid'
        if os.path.exists(_pid_file):
            pid = public.readFile(_pid_file)
            if os.path.exists('/proc/' + pid): return True

        cmd_file = '/www/server/panel/plugin/task_manager/process_network_total.py'
        python_bin = self.get_python_bin()
        _cmd = 'nohup {} {} 600 &> /tmp/net.log &'.format(python_bin, cmd_file)
        public.ExecShell(_cmd)

    last_net_process = None
    last_net_process_time = 0

    def get_process_net_list(self):
        w_file = '/dev/shm/bt_net_process'
        if not os.path.exists(w_file): return
        self.last_net_process = cache.get('net_process')
        self.last_net_process_time = cache.get('last_net_process')
        net_process_body = public.readFile(w_file)
        if not net_process_body: return
        net_process = net_process_body.split('\n')
        for np in net_process:
            if not np: continue
            tmp = {}
            np_list = np.split()
            if len(np_list) < 5: continue
            tmp['pid'] = int(np_list[0])
            tmp['down'] = int(np_list[1])
            tmp['up'] = int(np_list[2])
            tmp['down_package'] = int(np_list[3])
            tmp['up_package'] = int(np_list[4])
            self.__process_net_list[tmp['pid']] = tmp
        cache.set('net_process', self.__process_net_list, 600)
        cache.set('last_net_process', time.time(), 600)

    def get_process_network(self, pid):
        '''
            @name 获取进程网络流量
            @author hwliang<2021-09-13>
            @param pid<int> 进程ID
            @return tuple
        '''
        if not self.__process_net_list:
            self.get_process_net_list()
        if not self.last_net_process_time: return 0, 0, 0, 0
        if not pid in self.__process_net_list: return 0, 0, 0, 0

        if not pid in self.last_net_process:
            return self.__process_net_list[pid]['up'], self.__process_net_list[pid]['up_package'], \
                self.__process_net_list[pid]['down'], self.__process_net_list[pid]['down_package']

        up = int((self.__process_net_list[pid]['up'] - self.last_net_process[pid]['up']) / (
                time.time() - self.last_net_process_time))
        down = int((self.__process_net_list[pid]['down'] - self.last_net_process[pid]['down']) / (
                time.time() - self.last_net_process_time))
        up_package = int((self.__process_net_list[pid]['up_package'] - self.last_net_process[pid]['up_package']) / (
                time.time() - self.last_net_process_time))
        down_package = int(
            (self.__process_net_list[pid]['down_package'] - self.last_net_process[pid]['down_package']) / (
                    time.time() - self.last_net_process_time))
        return up, up_package, down, down_package

    def get_process_name(self, pid):
        '''
            @name 获取进程名称
            @author hwliang<2021-09-13>
            @param pid<str> 进程ID
            @return str
        '''
        pid_path = '/proc/' + str(pid) + '/comm'
        if not os.path.exists(pid_path): return ''
        pid_file = open(pid_path, 'rb')
        pid_name = pid_file.read().decode('utf-8').strip()
        pid_file.close()
        return pid_name

    # 获取进程信息
    def get_process_list(self, get):
        self.check_process_net_total()
        self.Pids = psutil.pids()
        processList = []
        if type(self.new_info) != dict: self.new_info = {}
        self.new_info['cpu_time'] = self.get_cpu_time()
        self.new_info['time'] = time.time()
        self.get_process_net_list()
        if not 'sortx' in get: get.sortx = 'all'
        info = {}
        info['activity'] = 0
        info['cpu'] = 0.00
        info['mem'] = 0
        info['disk'] = 0
        status_ps = {'sleeping': '睡眠', 'running': '活动'}
        for pid in self.Pids:
            tmp = {}
            try:
                p = psutil.Process(pid)
                with p.oneshot():
                    p_mem = p.memory_full_info()
                    if p_mem.rss == 0: continue
                    pio = p.io_counters()
                    p_cpus = p.cpu_times()
                    p_state = p.status()
                    if p_state == 'running': info['activity'] += 1
                    if p_state in status_ps: p_state = status_ps[p_state]
                    tmp['exe'] = p.exe()
                    tmp['name'] = p.name()
                    tmp['pid'] = pid
                    tmp['ppid'] = p.ppid()
                    # tmp['create_time'] = int(p.create_time())
                    tmp['status'] = p_state
                    tmp['user'] = p.username()
                    tmp['memory_used'] = p_mem.uss
                    tmp['cpu_percent'] = self.get_cpu_percent(str(pid), p_cpus, self.new_info['cpu_time'])
                    if tmp['name'] == 'BT-Panel' and tmp['cpu_percent'] > 1:
                        tmp['cpu_percent'] = round(tmp['cpu_percent'] % 1, 2)
                    tmp['io_write_bytes'] = pio.write_bytes
                    tmp['io_read_bytes'] = pio.read_bytes
                    tmp['io_write_speed'] = self.get_io_write(str(pid), pio.write_bytes)
                    tmp['io_read_speed'] = self.get_io_read(str(pid), pio.read_bytes)
                    tmp['connects'] = self.get_connects(pid)
                    tmp['threads'] = p.num_threads()
                    tmp['ps'] = self.get_process_ps(tmp['name'], pid, tmp['exe'], p)
                    tmp['up'], tmp['up_package'], tmp['down'], tmp['down_package'] = self.get_process_network(pid)
                    if tmp['cpu_percent'] > 100: tmp['cpu_percent'] = 0.1
                    info['cpu'] += tmp['cpu_percent']
                    info['disk'] += tmp['io_write_speed'] + tmp['io_read_speed']
                processList.append(tmp)
                del (p)
                del (tmp)
            except:
                continue

        cache.set(self.old_path, self.new_info, 600)
        processList = self.__pro_s_s(processList)
        res = True
        if get.sortx == 'status': res = False
        if 'reverse' in get:
            if get.reverse in ['undefined', 'null']:
                get.reverse = 'True'
                get.sortx = 'all'
            if not get.reverse in ['True', 'False']: get.reverse = 'True'
            res_list = {'True': True, 'False': False}
            res = res_list[get.reverse]
        else:
            get.reverse = True
        if get.reverse in ['undefined', 'null']:
            get.reverse = 'True'
            get.sortx = 'all'
        if get.sortx not in ['all']:
            processList = sorted(processList, key=lambda x: x[get.sortx], reverse=res)
        else:
            processList = sorted(processList, key=lambda x: [x['cpu_percent'], x['up'], x['down'], x['io_write_speed'],
                                                             x['io_read_speed'], x['connects'], x['threads'],
                                                             x['memory_used']], reverse=res)
        info['load_average'] = self.get_load_average()
        data = {}
        data['process_list'] = processList
        info['cpu'] = round(info['cpu'], 2)
        info['mem'] = self.get_mem_info()
        data['info'] = info
        if hasattr(get, 'search'):
            if get.search != '':
                data['process_list'] = self.search_pro(data['process_list'], get.search)
        # public.readFile('/www/server/panel/plugin/task_manager/')
        # public.writeFile('/jupyter/data.json', json.dumps(data))
        self.get_meter_head()
        data['meter_head'] = self.meter_head
        return data

    def get_meter_head(self, get=None):
        if self.meter_head == {}:
            if os.path.exists('/www/server/panel/plugin/task_manager/meter_head.json'):
                self.meter_head = json.loads(public.readFile('/www/server/panel/plugin/task_manager/meter_head.json'))
            else:
                self.meter_head = {
                    'name': True,
                    'pid': True,
                    'cpu_percent': True,
                    'down': True,
                    'up': True,
                    'status': True,
                    'threads': True,
                    'user': True,
                    'ps': True,
                    'memory_used': True,
                    'io_read_bytes': True,
                    'io_write_bytes': True,
                    'connects': True
                }
                public.writeFile('/www/server/panel/plugin/task_manager/meter_head.json', json.dumps(self.meter_head))
        return self.meter_head

    def set_meter_head(self, get):
        try:
            self.get_meter_head()
            if get.meter_head_name not in self.meter_head.keys():
                return False
            if get.meter_head_name in ['ps', 'memory_used', 'cpu_percent', 'name']:
                return False
            self.meter_head[get.meter_head_name] = not self.meter_head[get.meter_head_name]
            public.writeFile('/www/server/panel/plugin/task_manager/meter_head.json', json.dumps(self.meter_head))
            return True
        except:
            return False

    def get_mem_info(self, get=None):
        mem = psutil.virtual_memory()
        memInfo = {'memTotal': mem.total, 'memFree': mem.free, 'memBuffers': mem.buffers, 'memCached': mem.cached}
        memInfo['memRealUsed'] = memInfo['memTotal'] - memInfo['memFree'] - memInfo['memBuffers'] - memInfo['memCached']
        return memInfo['memRealUsed']

    # 进程备注，name,pid,启动命令
    def get_process_ps(self, name, pid, p_exe=None, p=None):
        processPs = {
            'irqbalance': '系统进程-优化系统性能服务',
            'containerd': 'docker管理服务',
            'qmgr': '系统进程-管理和控制邮件进程',
            'pickup': '系统进程-接收和处理待发送的邮件',
            'cleanup': '系统进程-服务器释放资源进程',
            'trivial-rewrite': '系统进程-邮件重写和转发服务',
            'bt-ipfilter': '宝塔网络的IP过滤器',
            'oneav': '微步木马检测服务',
            'rhsmcertd': '系统进程-验证系统的订阅状态服务',
            'tamperuser': '宝塔-企业级防篡改服务',
            'lvmetad': '系统进程-元数据守护进程',
            'containerd-shim-runc-v2': 'docker容器管理服务',
            'tuned': '系统进程-优化系统服务',
            'chronyd': '系统进程-时间同步服务',
            'auditd': '系统进程-系统安全日志记录服务',
            'gssproxy': '系统进程-身份验证和授权服务',
            'ossfs': '阿里云对象存储挂载服务',
            'cosfs': '腾讯云对象存储挂载服务',
            'obsfs': '华为云对象存储挂载服务',
            's3fs': '对象存储挂载服务',
            'bosfs': '百度云对象存储挂载服务',
            'jsvc': 'tomcat服务',
            'oneavd': '微步木马检测服务',
            'btsync': 'MySQL服务',
            'mysqld': 'MySQL服务',
            'php-fpm': 'PHP子进程',
            'php-cgi': 'PHP-CGI进程',
            'nginx': 'Nginx服务',
            'httpd': 'Apache服务',
            'sshd': 'SSH服务',
            'pure-ftpd': 'FTP服务',
            'sftp-server': 'SFTP服务',
            'mysqld_safe': 'MySQL服务',
            'firewalld': '防火墙服务',
            'BT-Panel': '宝塔面板-主进程',
            'BT-Task': '宝塔面板-后台任务进程',
            'NetworkManager': '网络管理服务',
            'svlogd': '日志守护进程',
            'memcached': 'Memcached缓存器',
            'gunicorn': "宝塔面板",
            "BTPanel": '宝塔面板',
            'baota_coll': "堡塔云控-主控端",
            'baota_client': "堡塔云控-被控端",
            'node': 'Node.js程序',
            'supervisord': 'Supervisor进程',
            'rsyslogd': 'rsyslog日志服务',
            'crond': '计划任务服务',
            'cron': '计划任务服务',
            'rsync': 'rsync文件同步进程',
            'ntpd': '网络时间同步服务',
            'rpc.mountd': 'NFS网络文件系统挂载服务',
            'sendmail': 'sendmail邮件服务',
            'postfix': 'postfix邮件服务',
            'npm': 'Node.js NPM管理器',
            'PM2': 'Node.js PM2进程管理器',
            'htop': 'htop进程监控软件',
            'btpython': '宝塔面板-独立Python环境进程',
            'btappmanagerd': '宝塔应用管理器插件',
            'dockerd': 'Docker容器管理器',
            'docker-proxy': 'Docker容器管理器',
            'docker-registry': 'Docker容器管理器',
            'docker-distribution': 'Docker容器管理器',
            'docker-network': 'Docker容器管理器',
            'docker-volume': 'Docker容器管理器',
            'docker-swarm': 'Docker容器管理器',
            'docker-systemd': 'Docker容器管理器',
            'docker-containerd': 'Docker容器管理器',
            'docker-containerd-shim': 'Docker容器管理器',
            'docker-runc': 'Docker容器管理器',
            'docker-init': 'Docker容器管理器',
            'docker-init-systemd': 'Docker容器管理器',
            'docker-init-upstart': 'Docker容器管理器',
            'docker-init-sysvinit': 'Docker容器管理器',
            'docker-init-openrc': 'Docker容器管理器',
            'docker-init-runit': 'Docker容器管理器',
            'docker-init-systemd-resolved': 'Docker容器管理器',
            'rpcbind': 'NFS网络文件系统服务',
            'dbus-daemon': 'D-Bus消息总线守护进程',
            'systemd-logind': '登录管理器',
            'systemd-journald': 'Systemd日志管理服务',
            'systemd-udevd': '系统设备管理服务',
            'systemd-timedated': '系统时间日期服务',
            'systemd-timesyncd': '系统时间同步服务',
            'systemd-resolved': '系统DNS解析服务',
            'systemd-hostnamed': '系统主机名服务',
            'systemd-networkd': '系统网络管理服务',
            'systemd-resolvconf': '系统DNS解析服务',
            'systemd-local-resolv': '系统DNS解析服务',
            'systemd-sysctl': '系统系统参数服务',
            'systemd-modules-load': '系统模块加载服务',
            'systemd-modules-restore': '系统模块恢复服务',
            'agetty': 'TTY登陆验证程序',
            'sendmail-mta': 'MTA邮件传送代理',
            'bash': 'bash命令行进程',
            '(sd-pam)': '可插入认证模块',
            'polkitd': '授权管理服务',
            'mongod': 'MongoDB数据库服务',
            'mongodb': 'MongoDB数据库服务',
            'mongodb-mms-monitor': 'MongoDB数据库服务',
            'mongodb-mms-backup': 'MongoDB数据库服务',
            'mongodb-mms-restore': 'MongoDB数据库服务',
            'mongodb-mms-agent': 'MongoDB数据库服务',
            'mongodb-mms-analytics': 'MongoDB数据库服务',
            'mongodb-mms-tools': 'MongoDB数据库服务',
            'mongodb-mms-backup-agent': 'MongoDB数据库服务',
            'mongodb-mms-backup-tools': 'MongoDB数据库服务',
            'mongodb-mms-restore-agent': 'MongoDB数据库服务',
            'mongodb-mms-restore-tools': 'MongoDB数据库服务',
            'mongodb-mms-analytics-agent': 'MongoDB数据库服务',
            'mongodb-mms-analytics-tools': 'MongoDB数据库服务',
            'dhclient': 'DHCP协议客户端',
            'dhcpcd': 'DHCP协议客户端',
            'dhcpd': 'DHCP服务器',
            'isc-dhcp-server': 'DHCP服务器',
            'isc-dhcp-server6': 'DHCP服务器',
            'dhcp6c': 'DHCP服务器',
            'dhcpcd': 'DHCP服务器',
            'dhcpd': 'DHCP服务器',
            'avahi-daemon': 'Zeroconf守护进程',
            'login': '登录进程',
            'systemd': '系统管理服务',
            'systemd-sysv': '系统管理服务',
            'systemd-journal-gateway': '系统管理服务',
            'systemd-journal-remote': '系统管理服务',
            'systemd-journal-upload': '系统管理服务',
            'systemd-networkd': '系统网络管理服务',
            'rpc.idmapd': 'NFS网络文件系统相关服务',
            'cupsd': '打印服务',
            'cups-browsed': '打印服务',
            'sh': 'shell进程',
            'php': 'PHP CLI模式进程',
            'blkmapd': 'NFS映射服务',
            'lsyncd': '文件同步服务',
            'sleep': '延迟进程'
        }
        if p_exe:
            if name == 'php-fpm':
                try:
                    php_version = '.'.join(p_exe.split('/')[-3])
                    return 'PHP' + php_version + '进程'
                except:
                    pass
            elif name == 'python':
                p_exe_arr = p_exe.split('/')
                if p_exe_arr[-1] in ['BT-Task', 'task.py']:
                    return '宝塔面板-后台任务进程'
                elif p_exe_arr[-1] in ['BT-Panel', 'runserver.py']:
                    return '宝塔面板-主进程'
                elif p_exe.find('process_network_total') != -1:
                    return '宝塔面板-进程网络监控'
                if p:
                    cmdline = ' '.join(p.cmdline()).strip()
                    cmdline_arr = cmdline.split('/')
                    if cmdline.find('process_network_total') != -1:
                        return '宝塔-进程网络监控'
                    if cmdline_arr[-1] in ['BT-Task', 'task.py']:
                        return '宝塔-后台任务进程'
                    elif cmdline_arr[-1] in ['BT-Panel', 'runserver.py']:
                        return '宝塔-主进程'
                    elif cmdline.find('process_network_total') != -1:
                        return '宝塔-进程网络监控'
                    elif cmdline.find('tamper_proof_service') != -1:
                        return '宝塔-网站防篡改'
                    elif cmdline.find('syssafe') != -1:
                        return '宝塔-系统加固'
                    elif cmdline.find('btwaf') != -1:
                        return '宝塔-WAF防火墙'
                    elif cmdline.find('acme') != -1:
                        return '宝塔-SSL证书签发'
                    elif cmdline.find('psync') != -1:
                        return '宝塔-一键迁移'
                    elif cmdline.find('/panel/plugin') != -1:
                        return '宝塔-插件进程'
                    elif cmdline.find('/www/server/cron/') != -1:
                        return '宝塔-计划任务'
            elif name == 'nginx':
                if p.username() == 'www':
                    return 'Nginx子进程'
                else:
                    return 'Nginx主进程'
            elif p_exe == '/usr/bin/bash':
                cmdline = ' '.join(p.cmdline()).strip()
                if cmdline.find('/www/server/cron/') != -1:
                    return '宝塔-计划任务'
                elif cmdline.find('/www/server/panel/plugin') != -1:
                    return '宝塔-插件进程'

        if name in processPs: return processPs[name]
        if name == 'python':
            if self.is_panel_process(pid): return '宝塔面板'

        if p_exe:
            exe_keys = {
                '/www/server/panel/pyenv/': '宝塔面板插件',
                '/www/server/cron/': '宝塔面板-计划任务进程',
                'pm2': 'PM2进程管理器',
                'PM2': 'PM2进程管理器',
                'nvm': 'NVM Node版本管理器',
                'npm': 'NPM Node包管理器'
            }

            for k in exe_keys.keys():
                if p_exe.find(k) != -1: return exe_keys[k]
                if name.find(k) != -1: return exe_keys[k]

        return name

    def __get_children(self, pid: int) -> List:
        try:
            p = psutil.Process(pid)  # pid为指定进程的进程号
            psutil.process_iter()
            children = p.children(recursive=True)  # 获取指定进程的所有子进程
            pids = []
            for child in children:
                pids.append(child.pid)
            return pids
        except:
            return []

    # 获取平均负载
    def get_load_average(self):
        c = os.getloadavg()
        data = {}
        data['1'] = float(c[0])
        data['5'] = float(c[1])
        data['15'] = float(c[2])
        return data

    # 获取当前运行级别  get_service_list ——> 引用get_my_runlevel
    def get_my_runlevel(self):
        try:
            runlevel = public.ExecShell('runlevel')[0].split()[1]
        except:
            runlevel_dict = {"multi-user.target": '3', 'rescue.target': '1', 'poweroff.target': '0',
                             'graphical.target': '5', "reboot.target": '6'}
            r_tmp = public.ExecShell('systemctl get-default')[0].strip()
            if r_tmp in runlevel_dict:
                runlevel = runlevel_dict[r_tmp]
            else:
                runlevel = '3'
        return runlevel

    # 获取进程的详细信息
    def get_process_info(self, get):
        pid = int(get.pid)
        try:
            p = psutil.Process(pid)
            processInfo = {}
            p_mem = self.object_to_dict(p.memory_full_info())
            pio = p.io_counters()
            # p_cpus= p.cpu_times()
            processInfo['exe'] = p.exe()
            processInfo['name'] = p.name();
            processInfo['pid'] = pid;
            processInfo['ppid'] = p.ppid()
            processInfo['pname'] = 'sys'
            if processInfo['ppid'] != 0: processInfo['pname'] = psutil.Process(processInfo['ppid']).name()
            processInfo['comline'] = p.cmdline()
            processInfo['create_time'] = int(p.create_time())
            processInfo['open_files'] = self.list_to_dict(p.open_files())
            processInfo['status'] = p.status();
            processInfo['user'] = p.username();
            processInfo['memory_full'] = p_mem
            processInfo['io_write_bytes'] = pio.write_bytes;
            processInfo['io_read_bytes'] = pio.read_bytes;
            processInfo['connects'] = self.get_connects(pid)
            processInfo['threads'] = p.num_threads()
            processInfo['ps'] = self.get_process_ps(processInfo['name'], pid, processInfo['exe'], p)
        except:
            return public.returnMsg(False, '指定进程已关闭!')
        return processInfo

    # 获取进程连接数
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

    # 获取进程io写
    def get_io_write(self, pid, io_write):
        self.get_old()
        disk_io_write = 0
        if not self.old_info: self.old_info = {}
        if not pid in self.old_info:
            self.new_info[pid]['io_write'] = io_write
            return disk_io_write
        if not 'time' in self.old_info: self.old_info['time'] = self.new_info['time']
        io_end = (io_write - self.old_info[pid]['io_write'])
        if io_end > 0:
            disk_io_write = io_end / (time.time() - self.old_info['time'])
        self.new_info[pid]['io_write'] = io_write
        if disk_io_write > 0: return int(disk_io_write)
        return 0

    # 获取io读
    def get_io_read(self, pid, io_read):
        self.get_old()
        disk_io_read = 0
        if not self.old_info: self.old_info = {}
        if not pid in self.old_info:
            self.new_info[pid]['io_read'] = io_read
            return disk_io_read
        if not 'time' in self.old_info: self.old_info['time'] = self.new_info['time']
        io_end = (io_read - self.old_info[pid]['io_read'])
        if io_end > 0:
            disk_io_read = io_end / (time.time() - self.old_info['time'])
        self.new_info[pid]['io_read'] = io_read
        if disk_io_read > 0: return int(disk_io_read)
        return 0

    # 获取cpu使用率
    def get_cpu_percent(self, pid, cpu_times, cpu_time):
        self.get_old()
        percent = 0.00
        process_cpu_time = self.get_process_cpu_time(cpu_times)
        if not self.old_info: self.old_info = {}
        if not pid in self.old_info:
            self.new_info[pid] = {}
            self.new_info[pid]['cpu_time'] = process_cpu_time
            return percent
        percent = round(
            100.00 * (process_cpu_time - self.old_info[pid]['cpu_time']) / (cpu_time - self.old_info['cpu_time']), 2)
        self.new_info[pid] = {}
        self.new_info[pid]['cpu_time'] = process_cpu_time
        if percent > 0: return percent
        return 0.00

    def get_old(self):
        if self.old_info: return True
        # if not os.path.exists(self.old_path): return False
        data = cache.get(self.old_path)
        if not data: return False
        # data = json.loads(data)
        if not data: return False
        self.old_info = data
        del (data)
        return True

    def get_net_old(self):
        if self.old_net_info: return True
        # if not os.path.exists(self.old_net_path): return False
        data = cache.get(self.old_net_path)
        if not data: return False
        # data = json.loads(data)
        if not data: return False
        self.old_net_info = data
        del (data)
        return True

    def get_process_cpu_time(self, cpu_times):
        cpu_time = 0.00
        for s in cpu_times: cpu_time += s
        return cpu_time

    def get_cpu_time(self):
        if self.__cpu_time: return self.__cpu_time
        self.__cpu_time = 0.00
        s = psutil.cpu_times()
        self.__cpu_time = s.user + s.system + s.nice + s.idle
        return self.__cpu_time

    def to_size(self, size):
        d = ('b', 'KB', 'MB', 'GB', 'TB')
        s = d[0]
        for b in d:
            if size < 1024: return size, b
            size = size / 1024
            s = b
        return size, b

    def GoToProcess(self, name):
        ps = ['sftp-server', 'login', 'nm-dispatcher', 'irqbalance', 'qmgr', 'wpa_supplicant', 'lvmetad', 'auditd',
              'master', 'dbus-daemon',
              'tapdisk', 'sshd', 'init', 'ksoftirqd', 'kworker', 'kmpathd', 'kmpath_handlerd', 'python', 'kdmflush',
              'bioset', 'crond', 'kthreadd',
              'migration', 'rcu_sched', 'kjournald', 'iptables', 'systemd', 'network', 'dhclient', 'systemd-journald',
              'NetworkManager', 'systemd-logind',
              'systemd-udevd', 'polkitd', 'tuned', 'rsyslogd']
        return name in ps

    def object_to_dict(self, obj):
        result = {}
        for name in dir(obj):
            value = getattr(obj, name)
            if not name.startswith('__') and not callable(value) and not name.startswith('_'): result[name] = value
        return result

    def list_to_dict(self, data):
        result = []
        for s in data:
            result.append(self.object_to_dict(s))
        return result

    # 添加进程查找
    def search_pro(self, data, search):
        try:
            ldata = []
            for i in data:
                if search in i['name'] or search in i['exe'] or search in i['ps'] or search in i[
                    'user'] or search in str(i['pid']) or search in i['status']:
                    ldata.append(i)
                elif hasattr(i, 'children'):
                    for k in i['children']:
                        if search in k['name'] or search in k['exe'] or search in k['ps'] or search in k[
                            'user'] or search in str(k['pid']):
                            ldata.append(i)
            return ldata
        except:
            public.print_log(traceback.format_exc())
            return data

    # 进程折叠，将子进程折叠到父进程下，并将使用资源累加。
    def __pro_s_s(self, data: List) -> List:
        """
        将子进程合并到父进程中
        :param data:进程列表
        :return:合并后的进程列表增加children字段
        """
        data1 = []
        children_set = {'childrens': []}
        for i in data:
            if i['pid'] > 30 and i['ppid'] == 1:
                children = self.__get_children(i['pid'])
                s4 = time.time()
                if children != []: children_set[i['pid']] = children
                children_set['childrens'] += children
        for i in data:
            if i['pid'] in children_set:
                i['children'] = []
                for j in data:
                    if j['pid'] in children_set[i['pid']]:
                        i['children'].append(j)
                        i['memory_used'] += j['memory_used']
                        i['cpu_percent'] = round(i['cpu_percent'] + j['cpu_percent'], 2)
                        i['io_write_bytes'] += j['io_write_bytes']
                        i['io_read_bytes'] += j['io_read_bytes']
                        i['io_write_speed'] += j['io_write_speed']
                        i['io_read_speed'] += j['io_read_speed']
                        i['connects'] += j['connects']
                        i['threads'] += j['threads']
                        i['up'] += j['up']
                        i['up_package'] += j['up_package']
                        i['down'] += j['down']
                        i['down_package'] += j['down_package']
                data1.append(i)
            elif i['pid'] not in children_set['childrens']:
                data1.append(i)
        return data1
