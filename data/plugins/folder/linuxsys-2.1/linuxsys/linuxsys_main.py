# -- coding: utf-8 --**
# !/usr/bin/python
# coding: utf-8
# -----------------------------
# 宝塔Linux面板内测插件
# -----------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hezhihong <272267659@qq.com>
import json
import sys, os, shutil, subprocess, panelTask,socket


if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
sys.path.append("class/")
import public, db, time

try:
    import distro
except:
    os.system("btpip install distro")
    import distro

public.returnMsg


class linuxsys_main:
    __setupPath = 'plugin/linuxsys'

    # 设置DNS
    def SetConfig(self, get):
        dnsStr = "nameserver " + get.dns1 + "\n"
        if get.dns2:
            dnsStr += "nameserver " + get.dns2 + '\n'
        public.writeFile('/etc/resolv.conf', dnsStr)
        return public.returnMsg(True, '设置成功!')

    # 设置IP地址
    def SetAddress(self, get):
        if not self.CheckIp(get.address): return public.returnMsg(False, 'IP地址不合法!')
        if not self.CheckIp(get.netmask): return public.returnMsg(False, '子网掩码不合法!')
        if not self.CheckIp(get.gateway): return public.returnMsg(False, '网关地址不合法!')
        cfile, devName = self.GetDevConf()
        if not os.path.exists(cfile): return public.returnMsg(False, '无法正确获取设备名称!')
        import re
        for i in range(100):
            if i < 1: continue
            pfile = cfile + ':' + str(i)
            newName = devName + ':' + str(i)
            if not os.path.exists(pfile): break
            conf = public.readFile(pfile)
            rep = "IPADDR\d*\s*=\s*(.+)\n"
            tmp = re.search(rep, conf)
            if not tmp: continue
            if tmp.groups()[0] == get.address: return public.returnMsg(False, '指定IP地址已添加过!')

        cconfig = public.readFile(cfile)
        rep = "DEVICE\s*=\s*\w+\n"
        cconfig = re.sub(rep, 'DEVICE=' + newName + '\n', cconfig)
        rep = "NAME\s*=\s*\w+\n"
        cconfig = re.sub(rep, 'NAME=' + newName + '\n', cconfig)
        rep = "IPADDR\d*\s*=\s*.+\n"
        cconfig = re.sub(rep, 'IPADDR=' + get.address + '\n', cconfig)
        rep = "NETMASK\s*=\s*.+\n"
        cconfig = re.sub(rep, "NETMASK=" + get.netmask + "\n", cconfig)
        rep = "GATEWAY\s*=\s*.+\n"
        cconfig = re.sub(rep, "GATEWAY=" + get.gateway + "\n", cconfig)

        public.writeFile(pfile, cconfig)
        self.reload_network()
        return public.returnMsg(True, '添加成功!')

    # 重启网络服务
    def reload_network(self):
        if os.path.exists('/bin/nmcli'):
            public.ExecShell("nmcli c reload")
            public.ExecShell("nmcli c up {}".format(self.GetDevConf()[1]))
        elif os.path.exists('/bin/systemctl'):
            public.ExecShell("systemctl restart network &")
        else:
            public.ExecShell('service network restart &')

    # 验证IP合法性
    def CheckIp(self, address):
        try:
            if address.find('.') == -1: return False
            iptmp = address.split('.')
            if len(iptmp) != 4: return False
            for ip in iptmp:
                if int(ip) > 255: return False
            return True
        except:
            return False

    # 删除IP
    def DelAddress(self, get):
        if not self.CheckIp(get.address): return public.returnMsg(False, 'IP地址不合法!')
        cfile, devName = self.GetDevConf()
        if not os.path.exists(cfile): return public.returnMsg(False, '无法正确获取设备名称!')
        isDel = False
        import re;
        for i in range(100):
            if i < 1: continue
            pfile = cfile + ':' + str(i)
            if not os.path.exists(pfile): continue
            conf = public.readFile(pfile)
            rep = "IPADDR\d*\s*=\s*(.+)\n"
            tmp = re.search(rep, conf)
            if not tmp: continue
            if tmp.groups()[0] == get.address:
                os.system('rm -f ' + pfile)
                isDel = True
                break
        if isDel:
            self.reload_network()
            return public.returnMsg(True, '删除成功!')

        return public.returnMsg(False, '此IP不能删除')

    # 获取网卡配置文件地址
    def GetDevConf(self):
        devName = 'eth0'
        cfile = '/etc/sysconfig/network-scripts/ifcfg-' + devName
        try:
            if not os.path.exists(cfile): devName = 'eno16777736'
            if not os.path.exists(cfile): devName = 'eno1'
            if not os.path.exists(cfile):
                devName = public.ExecShell("ip add |grep LOWER_UP|grep -v lo|sed 's/://g'|awk '{print $2}'")[0].split()[
                    0].strip()
            cfile = '/etc/sysconfig/network-scripts/ifcfg-' + devName
            return cfile, devName
        except:
            return cfile, devName

    # 网卡配置补全
    def CheckConfig(self, get):
        if not self.CheckIp(get.address): return public.returnMsg(False, 'IP地址不合法!')
        if not self.CheckIp(get.netmask): return public.returnMsg(False, '子网掩码不合法!')
        if not self.CheckIp(get.gateway): return public.returnMsg(False, '网关地址不合法!')
        cfile, devName = self.GetDevConf()
        if not os.path.exists(cfile): return public.returnMsg(False, '无法正确获取设备名称!')
        import re
        conf = public.readFile(cfile)
        rep = "ONBOOT\s*=\s*.+\n"
        if not re.search(rep, conf):
            conf += "\nONBOOT=yes"
        else:
            conf = re.sub(rep, "ONBOOT=yes\n", conf)

        rep = "BOOTPROTO\s*=\s*\w+\n"
        if not re.search(rep, conf):
            conf += "\nBOOTPROTO=static"
        else:
            conf = re.sub(rep, "BOOTPROTO=static\n", conf)

        rep = "IPADDR\s*=\s*.+\n"
        if not re.search(rep, conf):
            conf += "\nIPADDR=" + get.address
        else:
            conf = re.sub(rep, "IPADDR=" + get.address + "\n", conf)
        rep = "NETMASK\s*=\s*.+\n"
        if not re.search(rep, conf):
            conf += "\nNETMASK=" + get.netmask
        else:
            conf = re.sub(rep, "NETMASK=" + get.netmask + "\n", conf)

        rep = "GATEWAY\s*=\s*.+\n"
        if not re.search(rep, conf):
            conf += "\nGATEWAY=" + get.gateway
        else:
            conf = re.sub(rep, "GATEWAY=" + get.gateway + "\n", conf)

        public.writeFile(cfile, conf)
        return public.returnMsg(True, '初始化网卡成功')

    # 重载网络
    def ReloadNetwork(self, get):
        if os.path.exists('/usr/bin/systemctl'):
            os.system('systemctl restart network.service')
        else:
            os.system('service network reload')
        return public.returnMsg(True, '网络已重启!')

    # 获取IP地址
    def GetAddress(self, get):
        if not os.path.exists('/etc/redhat-release'): return False
        import re
        cfile, devName = self.GetDevConf()
        if not os.path.exists(cfile): return public.returnMsg(False, '无法正确获取设备名称!')
        conf = public.readFile(cfile)
        rep = r"BOOTPROTO\s*=\s*(.+)\n"
        try:
            if re.search(rep, conf).groups()[0].replace("'", '').lower() == 'dhcp': return public.returnMsg(False,
                                                                                                            '未初始化网卡!')
        except:
            return public.returnMsg(False, '未初始化网卡!')

        result = []
        for i in range(100):
            if i < 1:
                pfile = cfile
            else:
                pfile = cfile + ':' + str(i)
            if not os.path.exists(pfile): continue
            tmp = {}
            conf = public.readFile(pfile)
            rep = r"IPADDR\d*\s*=\s*(.+)\n"
            tmp['address'] = re.search(rep, conf).groups()[0].replace("'", '').replace('"', '')
            rep = r"GATEWAY\d*\s*=\s*(.+)\n"
            tmp['gateway'] = re.search(rep, conf).groups()[0].replace("'", '').replace('"', '')

            rep = r"NETMASK\d*\s*=\s*(.+)\n"
            r_tmp = re.search(rep, conf)
            if r_tmp:
                tmp['netmask'] = r_tmp.groups()[0].replace("'", '').replace('"', '')

            rep = r"PREFIX\d*\s*=\s*(.+)\n"
            r_tmp = re.search(rep, conf)
            if r_tmp:
                tmp['prefix'] = r_tmp.groups()[0].replace("'", '').replace('"', '')
                tmp['netmask'] = self.cidr(int(tmp['prefix']))

            result.append(tmp)
        return result

    # 地址转换
    def cidr(self, prefix):
        import socket, struct
        return socket.inet_ntoa(struct.pack(">I", (0xffffffff << (32 - prefix)) & 0xffffffff))

    # 取DNS信息
    def GetConfig(self, get):
        import re
        dnsStr = public.readFile('/etc/resolv.conf')
        tmp = re.findall(r"(nameserver)\s+(.+)", dnsStr)
        dnsInfo = {}
        dnsInfo['dns1'] = ''
        dnsInfo['dns2'] = ''
        if len(tmp) > 0:
            dnsInfo['dns1'] = tmp[0][1]
        if len(tmp) > 1:
            dnsInfo['dns2'] = tmp[1][1]
        return dnsInfo

    # 测试DNS
    def TestDns(self, get):
        resolv = '/etc/resolv.conf'
        dnsStr = "nameserver " + get.dns1 + "\n" + "nameserver " + get.dns2
        backupDns = public.readFile(resolv)
        public.writeFile(resolv, dnsStr)
        tmp = public.ExecShell("ping -c 1 -w 1 www.qq.com")
        isPing = False
        try:
            if tmp[0].split('time=')[1].split()[0]: isPing = True
        except:
            pass
        public.writeFile(resolv, backupDns)
        if isPing:
            return public.returnMsg(True, '当前DNS可用!<br>' + tmp[0].replace('\n', '<br>'))
        return public.returnMsg(False, '当前DNS不可用!<br>' + tmp[1])

    # 获取SWAP信息
    def GetSwap(self, get):
        swapStr = public.ExecShell('free -m|grep Swap')
        tmp = swapStr[0].split()
        swapInfo = {}
        swapInfo['total'] = int(tmp[1])
        swapInfo['used'] = int(tmp[2])
        swapInfo['free'] = int(tmp[3])
        swapInfo['size'] = 0
        if os.path.exists('/www/swap'):
            swapInfo['size'] = os.path.getsize('/www/swap')
        return swapInfo

    # 设置SWAP
    def SetSwap(self, get):
        swapFile = '/www/swap'
        if os.path.exists(swapFile):
            os.system('swapoff ' + swapFile)
            os.system('rm -f ' + swapFile)
            os.system('sed -i "/' + swapFile.replace('/', '\\/') + '/d" /etc/fstab')
        if float(get.size) > 1:
            import system
            disk = system.system().GetDiskInfo()
            dsize = 0
            isSize = True
            for d in disk:
                if d['path'] == '/www': dsize = d['size'][2]
                if d['path'] == '/':
                    if not dsize: dsize = d['size'][2]
            if dsize.find('T') != -1:
                fsize = dsize.replace('T', '')
                if (float(fsize) * 1024 * 1024) < float(get.size): isSize = False

            if dsize.find('G') != -1:
                fsize = dsize.replace('G', '')
                if (float(fsize) * 1024) < float(get.size): isSize = False

            if dsize.find('M') != -1:
                fsize = dsize.replace('M', '')
                if float(fsize) < float(get.size): isSize = False

            if not isSize:
                data = self.GetSwap(get)
                data['status'] = False
                data['msg'] = '失败，磁盘空间不足，当前可用空间：' + dsize
                return data

            os.system('dd if=/dev/zero of=' + swapFile + ' bs=1M count=' + get.size)
            os.system('mkswap -f ' + swapFile)
            os.system('swapon ' + swapFile)
            os.system('echo "' + swapFile + '    swap    swap    defaults    0 0" >> /etc/fstab')
        data = self.GetSwap(get)
        data['status'] = True
        data['msg'] = '设置成功'
        return data

    # 获取时区
    def GetZoneinfo(self, get):
        zoneList = ['Asia', 'Africa', 'America', 'Antarctica', 'Arctic', 'Atlantic', 'Australia', 'Europe', 'Indian',
                    'Pacific']
        areaList = []
        # 取具体时区地区
        result = public.ExecShell('ls -l /etc/localtime')
        res2 = ''
        zone = ''
        data = {}
        try:
            result = result[0]
            res = result[result.rfind('->') + 1:].replace('\n', '')
            res2 = res.strip().split('/')[-1]
            zone = res.strip().split('/')[-2]
        except Exception as e:
            print(e)
        if get.zone: zone = get.zone
        for area in os.listdir('/usr/share/zoneinfo/' + zone):
            areaList.append(area)
        data['zone'] = {'0': zone, '1': res2}
        data['date'] = public.ExecShell('date +"%Y-%m-%d %H:%M:%S %Z %z"')[0]
        data['zoneList'] = zoneList
        data['areaList'] = sorted(areaList)
        return data

    # 同步时间
    def syncDate(self, get):
        # 取国际标准0时时间戳
        time_str = public.HttpGet(public.GetConfigValue('home') + '/api/index/get_time')
        try:
            new_time = int(time_str) - 28800
        except:
            return public.returnMsg(False, '连接时间服务器失败!')
        if not new_time: public.returnMsg(False, '连接时间服务器失败!')
        # 取所在时区偏差秒数
        add_time = '+0000'
        try:
            add_time = public.ExecShell('date +"%Y-%m-%d %H:%M:%S %Z %z"')[0].replace('\n', '').strip().split()[-1]
        except:
            pass
        add_1 = False
        if add_time[0] == '+':
            add_1 = True
        add_v = int(add_time[1:-2]) * 3600 + int(add_time[-2:]) * 60
        if add_1:
            new_time += add_v
        else:
            new_time -= add_v
        # 设置所在时区时间
        time_local = time.localtime(new_time)
        date_str = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
        public.ExecShell('date -s "%s"' % date_str)
        public.WriteLog("TYPE_PANEL", "DATE_SUCCESS")
        if 'isreturn' not in get:
            return public.returnMsg(True, "DATE_SUCCESS")

    # 设置时区
    def SetZone(self, get):
        os.system('rm -f /etc/localtime')
        os.system("ln -s '/usr/share/zoneinfo/" + get.zone + "/" + get.area + "' '/etc/localtime'")
        get.isreturn = 'False'
        time.sleep(0.01)
        self.syncDate(get)
        data = self.GetZoneinfo(get)
        data['status'] = True
        data['msg'] = "设置成功!"

        return data

    # 取当前用户名
    def GetRoot(self, get):
        try:
            return public.ExecShell("who|awk '{print $1}'")[0].split()[0]
        except:
            return 'root'

    # 修改用户密码
    def SetRoot(self, get):
        if not get.user: return public.returnMsg(False, "用户名不能为空!")
        if get.passwd1 != get.passwd2: return public.returnMsg(False, "两次输入的密码不一致!")
        if get.passwd1.find('&') != -1 or get.passwd1.find('$') != -1:
            return public.returnMsg(False, '密码中不能包含&$符号!')
        os.system('(echo "' + get.passwd1.strip() + '";sleep 1;echo "' + get.passwd2.strip() + '")|passwd ' + get.user)
        return public.returnMsg(True, '修改成功!')

    '''
     * 挂载内存到临时目录
     * @param string path 挂载目录
     * @param string size 挂载大小
    '''

    def SetMountMemory(self, get):
        import re
        if get['size'].isdigit():
            mount_szie = int(get.size)
            conf = public.readFile("/proc/meminfo")
            mem_total = re.search(r"MemTotal:\s*(\d*) kB", conf).groups()[0]
            if mount_szie * 1024 > int(mem_total) / 2:
                return public.returnMsg(False, '内存盘最大容量不能超过物理内存的50%!')

            if get.path[:1] != "/":
                return public.returnMsg(False, '请输入绝对路径!')
            elif get.path == "/tmp":
                # 备份
                public.ExecShell('mkdir /tmp_backup')
                public.ExecShell(r'\cp -a -r /tmp/* /tmp_backup/')
                # 挂载
                return self.MountTmpfs(get.path, mount_szie)
            else:
                if not os.path.exists(get.path): public.ExecShell('mkdir -p ' + get.path)
                if os.listdir(get.path):
                    return public.returnMsg(False, '该目录已存在文件，请更换目录!')
                else:
                    # 挂载
                    return self.MountTmpfs(get.path, mount_szie)

        else:
            return public.returnMsg(False, '请输入正确参数')

    def GetMountInfo(self, get):
        import ast, re
        # 获取内存总值
        conf = public.readFile("/proc/meminfo")
        mem_total = re.search(r"MemTotal:\s*(\d*) kB", conf).groups()[0]
        # 获取挂载信息
        filename = "plugin/linuxsys/mount.json"
        mount_info = public.readFile(filename)
        mount_info = ast.literal_eval(mount_info) if mount_info else {}
        # 更新每个目录的使用值
        for i in mount_info:
            mount_info[i]['useed_szie'] = self.FileSize(i)
        public.writeFile(filename, str(mount_info))
        return {"mount_info": mount_info, "mem_total": mem_total}
    # 卸载挂载目录
    def DelMountMemory(self, get):
        import re, ast
        filename = "plugin/linuxsys/mount.json"
        mount_info = public.readFile(filename)
        mount_info = ast.literal_eval(mount_info) if mount_info else {}
        if get.path in mount_info.keys():
            del mount_info[get.path]
            if get.path == '/tmp':
                public.ExecShell('mkdir /tmp_backup')
                public.ExecShell(r'\cp -a -r /tmp/* /tmp_backup/')
            public.writeFile(filename, str(mount_info))
            # 配置文件处理
            conf_file = "/etc/fstab"
            conf = public.readFile(conf_file)
            e = r"\n"
            if conf[-1] != r"\n": e = ""
            public.writeFile(conf_file, re.sub(r"tmpfs\s*%s.*?%s" % (get.path, e), '', conf))
            public.ExecShell("umount %s" % get.path)
            if get.path == '/tmp':
                public.ExecShell(r'\cp -a -r /tmp_backup/* /tmp/')
                public.ExecShell('rm -rf /tmp_backup')
            return public.returnMsg(True, '卸载成功，部分目录可能需要重启服务器才能生效!')
        return public.returnMsg(False, '卸载失败!')

    # 挂载临时目录方法
    def MountTmpfs(self, mount_path, mount_szie):
        # 不允许挂载到已挂载的子目录下
        import re, ast
        filename = "plugin/linuxsys/mount.json"
        mount_info = public.readFile(filename)
        mount_info = ast.literal_eval(mount_info) if mount_info else {}
        k = "/".join(mount_path.split('/')[:-1])
        if k in mount_info.keys():
            return public.returnMsg(False, '不允许挂载到已挂载的子目录下')

        conf_file = "/etc/fstab"
        conf_info = public.readFile(conf_file)
        e = ''
        if conf_info[-1] != "\n": e = "\n"

        pattern = r"tmpfs\s*%s\s*tmpfs\s*[0-9a-zA-Z\s=]*"
        statement = e + "tmpfs  %s tmpfs size=%sm   0  0\n" % (mount_path, mount_szie)

        # 将记录写fstab文件
        if re.findall(pattern % mount_path, conf_info):
            # 记录存在， 则替换
            new_conf = re.sub(pattern % mount_path, statement, conf_info)
            public.writeFile(conf_file, new_conf)
        else:
            # 不存在 则插入
            public.writeFile(conf_file, '%s%s' % (conf_info, statement))

        # 重新加载
        public.ExecShell("umount %s" % mount_path)
        public.ExecShell("mount -a")

        # 成功挂载 写入文件
        filename = "plugin/linuxsys/mount.json"
        mount_info = public.readFile(filename)
        mount_info = ast.literal_eval(mount_info) if mount_info else {}
        mount_info[mount_path] = {"mount_szie": mount_szie, "useed_szie": self.FileSize(mount_path)}
        public.writeFile(filename, str(mount_info))
        return public.returnMsg(True, '挂载成功!')

    def FileSize(self, path):
        size = 0
        for root, dirs, files in os.walk(path, True):
            # 目录下文件大小累加
            size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
        return size

    # 获取/etc/hosts文件中所有的域名信息。返回1表示域名有效，0表示域名失效。
    def get_hosts_info(self, get):
        hosts = {}
        with open('/etc/hosts') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    status = 0
                    line = line[1:].strip()
                else:
                    status = 1
                parts = line.split(maxsplit=1)
                if len(parts) != 2:
                    continue
                ip, domain = parts
                if domain not in hosts:
                    hosts[domain] = {}
                hosts[domain] = {'ip': ip, 'status': status}
        return hosts


    def __check_ip_address(self,ip):
        try:
            socket.inet_pton(socket.AF_INET6, ip)
            return True
        except socket.error:
            pass
        try:
            socket.inet_pton(socket.AF_INET, ip)
            return True
        except socket.error:
            pass
        return False

    # 添加/修改 hosts
    def addHosts(self, get):
        try:
            ip = get.ip
            domain = get.domain
            hosts_file = '/etc/hosts'
            if self.__check_ip_address(ip):
                with open(hosts_file, 'r') as f:
                    lines = f.readlines()
                for i in range(len(lines)):
                    if domain in lines[i]:
                        # 修改 hosts
                        lines[i] = f"{ip}\t{domain}\n"
                        break
                else:
                    # 添加 hosts
                    lines.append(f"{ip}\t{domain}\n")
                with open(hosts_file, 'w') as f:
                    f.writelines(lines)
                os.system('systemctl restart NetworkManager.service')
                return public.returnMsg(True, '操作成功')
            else:
                raise ValueError("请检查ip格式")
        except Exception as e:
            return public.returnMsg(False, str(e))

    # 删除 hosts
    def deleteHosts(self, get):
        domain = get.domain
        hosts_file = '/etc/hosts'
        with open(hosts_file, 'r') as f:
            lines = f.readlines()
        for i in range(len(lines)):
            line = lines[i]
            if domain in line:
                # 删除 hosts
                del lines[i]
                break
        with open(hosts_file, 'w') as f:
            f.writelines(lines)
        os.system('systemctl restart NetworkManager.service')
        return public.returnMsg(True, '删除成功')

    # 暂停和启用host
    def operateHost(self, get):
        # 传入要操作的域名
        domain = get.domain
        # 传入要执行的操作
        act = get.act
        hosts_file = '/etc/hosts'
        with open(hosts_file, 'r') as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if domain in line:
                # 暂停使用
                if act == 'pause' and not line.startswith('#'):
                    lines[i] = f"#{line}"
                    with open(hosts_file, 'w') as f:
                        f.writelines(lines)
                elif act == 'pause' and line.startswith('#'):
                    return public.returnMsg(True, '已经是停用状态')
                # 重新启用
                elif act == 'resume' and line.startswith('#'):
                    lines[i] = line.replace('#', '', 1)
                    with open(hosts_file, 'w') as f:
                        f.writelines(lines)
                elif act == 'resume' and not line.startswith('#'):
                    return public.returnMsg(True, '已经是启用状态')
        # 重启网络服务
        os.system('systemctl restart NetworkManager.service')
        if act == 'pause':
            return public.returnMsg(True, '暂停成功')
        elif act == 'resume':
            return public.returnMsg(True, '启用成功')

    # 返回pip源列表
    def get_pip_sources(self, get):
        data = public.readFile('/www/server/panel/plugin/linuxsys/pip_sources.json')
        data = json.loads(data)
        source = data['pipsource']
        last_choice = data['last_choice']
        return {'source': source, 'last_choice': last_choice}

    # 设置pip源
    def set_pip_source(self, get):
        try:
            su=get.source_url
            os.system(f"btpip config set global.index-url {su}")
            os.system(f"btpip config set global.trusted-host {su.split('/')[2]}")
            os.system(f"btpip config set install.trusted-host {su.split('/')[2]}")
            data = public.readFile('/www/server/panel/plugin/linuxsys/pip_sources.json')
            data = json.loads(data)
            data['last_choice'] = su
            public.writeFile('/www/server/panel/plugin/linuxsys/pip_sources.json', json.dumps(data))
            return public.returnMsg(True, 'pip源设置成功')
        except Exception:
            return public.returnMsg(False, 'pip源设置失败')

    # 前端调用获取command的下拉框选项,以供可以选择安装的功能命令。
    def get_commands(self, get):
        with open('plugin/linuxsys/commands.json', 'r') as f:
            commands = json.load(f)
        return commands

    # 安装常用命令，仅支持centos和ubantu系统。
    def install_command(self, get):
        dist = distro.linux_distribution()
        command_name = get.command_name
        data = public.readFile('/www/server/panel/plugin/linuxsys/commands.json')
        data = json.loads(data)
        try:
            if (data[command_name]['status'] == 1):
                return public.returnMsg(False, "已经安装")
            else:
                if  'debian' in dist[0].lower() or 'ubuntu' in dist[0].lower():
                    subprocess.run(['apt-get', 'install', get.command_name], check=True)
                    data[command_name]['status'] = 1
                    public.writeFile('/www/server/panel/plugin/linuxsys/commands.json', json.dumps(data))
                    return public.returnMsg(True, "安装成功")
                elif 'centos' in dist[0].lower():
                    subprocess.run(['yum', 'install', '-y', get.command_name], check=True)
                    data[command_name]['status'] = 1
                    public.writeFile('/www/server/panel/plugin/linuxsys/commands.json', json.dumps(data))
                    return public.returnMsg(True, "安装成功")
        except Exception:
            return public.returnMsg(False, '安装失败')

    # 卸载命令
    def uninstall_commands(self, get):
        dist = distro.linux_distribution()
        command_name = get.command_name
        data = public.readFile('/www/server/panel/plugin/linuxsys/commands.json')
        data = json.loads(data)
        try:
            if (data[command_name]['status'] == 0):
                return public.returnMsg(False, "未安装")
            else:
                if 'debian' in dist[0].lower() or 'ubuntu' in dist[0].lower():
                    subprocess.run(['apt-get', 'remove', get.command_name,'-y'], check=True)
                    data[command_name]['status'] = 0
                    public.writeFile('/www/server/panel/plugin/linuxsys/commands.json', json.dumps(data))
                    return public.returnMsg(True, "卸载成功")
                elif 'centos' in dist[0].lower():
                    subprocess.run(['rpm', '-e', get.command_name], check=True)
                    data[command_name]['status'] = 0
                    public.writeFile('/www/server/panel/plugin/linuxsys/commands.json', json.dumps(data))
                    return public.returnMsg(True, "卸载成功")
        except Exception:
            return public.returnMsg(False, '卸载失败')


    # 获取apt/yum源的下拉框选项
    def get_source(self, get):
        data = public.readFile('/www/server/panel/plugin/linuxsys/sources.json')
        data = json.loads(data)
        dist = distro.linux_distribution()
        linux_name=dist[0].lower().split(' ')[0]
        if linux_name=="centos":
            source = data['centos']
        elif linux_name=="ubuntu":
            source = data['ubuntu']
        elif linux_name=="debian":
            source = data['ubuntu']
        else:
            return public.returnMsg("失败")
        last = data['last']
        return {'source': source, 'last': last}

    # 设置yum源或者apt源
    def set_source(self, get):
        try:
            dist = distro.linux_distribution()
            if 'centos' in dist[0].lower():
                repo_file = '/etc/yum.repos.d/CentOS-Base.repo'
                repo_bak_file = '/etc/yum.repos.d/CentOS-Base.repo.bak'
                if not os.path.exists(repo_bak_file):
                    shutil.copyfile(repo_file, repo_bak_file)
                # 镜像地址需要传入
                mirror = get.mirror
                with open(repo_file, 'r') as f:
                    lines = f.readlines()
                for i in range(len(lines)):
                    line = lines[i]
                    if line.startswith('baseurl='):
                        # 修改 yum源
                        lines[i] = f"baseurl={mirror}""/centos/$releasever/os/$basearch/""\n"
                with open(repo_file, 'w') as f:
                    f.writelines(lines)
                data = public.readFile('/www/server/panel/plugin/linuxsys/sources.json')
                data = json.loads(data)
                data['last'] = mirror
                public.writeFile('/www/server/panel/plugin/linuxsys/sources.json', json.dumps(data))
                os.system(f"yum clean all")
                task_obj = panelTask.bt_task()
                task_obj.create_task("生成yum缓存", 0, 'yum makecache')
                return public.returnMsg(True, 'yum源设置成功')
            elif 'ubuntu' in dist[0].lower() or 'debian' in dist[0].lower():
                # 备份原来的配置文件
                sources_file = '/etc/apt/sources.list'
                sources_bak_file = '/etc/apt/sources.list.bak'
                if not os.path.exists(sources_bak_file):
                    shutil.copyfile(sources_file, sources_bak_file)
                new_source = get.mirror
                os.system(f"sed -i 's#http://[^/]\+/#{new_source}#g' /etc/apt/sources.list")
                os.system("apt-get update")
                data = public.readFile('/www/server/panel/plugin/linuxsys/sources.json')
                data = json.loads(data)
                data['last'] = new_source
                public.writeFile('/www/server/panel/plugin/linuxsys/sources.json', json.dumps(data))
                return public.returnMsg(True, 'apt源设置成功')
        except Exception:
            return public.returnMsg(False, '配置失败，不支持的系统')
        # except Exception as err:
        #     public.print_log(traceback.format_exc())