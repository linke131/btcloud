# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2023-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: xiaopacai <xiaopacai@bt.cn>
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   BBR算法管理器
# +--------------------------------------------------------------------
import json
import re
import shutil
import math
import subprocess
import sys
import traceback
from typing import List, Dict

sys.path.append('/www/server/panel/class')
import psutil, os, time, public

try:
    from BTPanel import cache
except:
    import cachelib

    cache = cachelib.SimpleCache()


# 检查内核是否支持BBR
def check(func):
    def wrapper(*args, **kwargs):
        if not check_linux_version():
            return public.returnMsg(False, '当前系统版本过旧，请升级系统！')
        res = public.ExecShell('uname -r')
        if res[0]:
            data = res[0].split('.')
            if int(data[0]) >= 4:
                if int(data[1]) < 9 and int(data[0]) == 4:
                    return public.returnMsg(False, '当前内核版本不支持BBR，请升级内核版本到4.9以上！')     
                return func(*args, **kwargs)
        return public.returnMsg(False, '当前内核版本不支持BBR，请升级内核版本到4.9以上！')

    return wrapper

# 检查linux的版本是否支持BBR的内核
def check_linux_version() -> bool:
    if not os.path.exists('/etc/os-release'):
        return False
    with open('/etc/os-release', 'r') as f:
        info = {}
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=')
                info[key] = value.strip('"')
    os_name = info.get('PRETTY_NAME', '').lower()
    version_id = int(float(info.get('VERSION_ID', 0)))
    if 'centos' in os_name and version_id < 6:
        return False
    if 'debian' in os_name and version_id < 8:
        return False
    if 'ubuntu' in os_name and version_id < 14:
        return False
    return True


# 检查BBR是否开启
def check_bbr(func):
    def wrapper(*args, **kwargs):
        res = public.ExecShell('sysctl net.ipv4.tcp_congestion_control')
        if res[0] and 'bbr' in res[0]:
            return func(*args, **kwargs)
        else:
            return public.returnMsg(False, 'BBR未开启')

    return wrapper


class bt_bbr_main:
    now_data = []
    plugin_path = '/www/server/panel/plugin/bt_bbr'

    def __init__(self):
        if not os.path.exists('{}/data.json'.format(self.plugin_path)):
            public.writeFile('{}/data.json'.format(self.plugin_path), json.dumps({}))
            self.run_speedtest()

    # 开启BBR加速，重启失效，开启测试
    @check
    def start_test_BBR(self, get=None) -> Dict:
        if not self.get_bbr_config():
            if os.path.exists('{}/data.json'.format(self.plugin_path)):
                data = json.loads(public.readFile('{}/data.json'.format(self.plugin_path)))
                if 'unbbr' not in data.keys():
                    self.run_speedtest()
            else:
                self.run_speedtest()
        res1 = public.ExecShell('sysctl net.core.default_qdisc=fq')
        res2 = public.ExecShell('sysctl net.ipv4.tcp_congestion_control=bbr')
        time.sleep(1)
        if res1[0] and res2[0]:
            if 'fq' in res1[0] and 'bbr' in res2[0]:
                return public.returnMsg(True, 'BBR开启成功')

    # 永久开启BBR加速
    @check
    def start_keep_BBR(self, get):
        with open('/etc/sysctl.conf', 'r') as f:
            lines = f.readlines()
        with open('/etc/sysctl.conf', 'w') as f:
            for line in lines:
                if 'net.core.default_qdisc' not in line or 'net.ipv4.tcp_congestion_control' not in line:
                    f.write(line)
            f.write('net.core.default_qdisc=fq\n')
            f.write('net.ipv4.tcp_congestion_control=bbr\n')
        public.ExecShell('sysctl -p')
        time.sleep(0.5)
        if self.get_bbr_config():
            return public.returnMsg(True, '加速开启成功')
        else:
            return public.returnMsg(False, '加速开启失败，请重试！')

    # 关闭BBR
    @check_bbr
    def stop_BBR(self, get=None) -> Dict:
        try:
            with open('/etc/sysctl.conf', 'r') as f:
                lines = f.readlines()
            with open('/etc/sysctl.conf', 'w') as f:
                for line in lines:
                    if 'net.core.default_qdisc' not in line or 'net.ipv4.tcp_congestion_control' not in line:
                        f.write(line)
                f.write('net.ipv4.tcp_congestion_control=cubic\n')
            public.ExecShell('sysctl -p')
            return public.returnMsg(True, 'BBR关闭成功！')
        except:
            return public.returnMsg(False, 'BBR关闭失败！')

    def stop_test(self, get=None):
        public.ExecShell('rm -rf {}/test.lock'.format(self.plugin_path))
        public.ExecShell('pkill btpython')
        public.ExecShell('pkill curl')
        self.now_data.clear()
        time.sleep(2)
        return public.returnMsg(True, '网络测试关闭成功！')

    # 运行测试带宽
    def run_speedtest(self, get=None):
        """
        开始运行测速
        :param get:
        :return: true | false
        """
        try:
            self.now_data.clear()
            self.now_data.append('s33')  # 标志开始测速开始运行
            if os.path.exists('{}/test.lock'.format(self.plugin_path)):
                time.sleep(5)
            public.ExecShell('touch {}/test.lock'.format(self.plugin_path))
            public.ExecShell('rm -rf {}/upload.log'.format(self.plugin_path))
            public.ExecShell('tc qdisc add dev eth0 root netem loss 1%')
            public.ExecShell(
                'curl -T {}/1G http://speedtest.tele2.net/upload.php -O /dev/null >> {}/xml_stream.log 2>> {}/upload.log &'.format(
                    self.plugin_path, self.plugin_path, self.plugin_path))
            try:
                time.sleep(1)
                for lf in range(10):
                    if not os.path.exists('{}/test.lock'.format(self.plugin_path)):
                        self.now_data.clear()
                        return
                    res = public.ExecShell('ps -aux |grep curl')
                    if 'speedtest.tele2' not in res[0]:
                        public.ExecShell(
                            'curl -T {}/40M http://speedtest.tele2.net/upload.php -O /dev/null >> {}/xml_stream.log 2>> {}/upload.log &'.format(
                                self.plugin_path, self.plugin_path, self.plugin_path))
                    time.sleep(1)
                public.ExecShell('tc qdisc del dev lo eth0')
                public.ExecShell('pkill curl')
                data = public.readFile('{}/upload.log'.format(self.plugin_path)).strip()
                data = data.split('\n')

                data = [i for i in data if ':--' not in i and 'Total' not in i and 'curl:' not in i and i != '']
                if data != []:
                    data = data[-1].split(' ')
                    data = [i for i in data if i != '']
                    upload = int(data[7][:-1]) * 1024 * 8
                else:
                    upload = 0
            except:
                return traceback.format_exc()
                upload = 0
            self.now_data.append(upload)
            name = 'bbr' if self.get_bbr_config() else 'unbbr'
            if not os.path.exists('/www/server/panel/plugin/bt_bbr/data.json'):
                if name != 'bbr':
                    public.writeFile('/www/server/panel/plugin/bt_bbr/data.json',
                                     json.dumps({name: [upload]}))
                else:
                    public.writeFile('/www/server/panel/plugin/bt_bbr/data.json',
                                     json.dumps({name: [upload]}))
            else:
                json_data = json.loads(public.readFile('/www/server/panel/plugin/bt_bbr/data.json'))
                if name not in json_data.keys():
                    json_data[name] = []
                json_data[name].append(upload)
                public.writeFile('/www/server/panel/plugin/bt_bbr/data.json',
                                 json.dumps(json_data))
            public.ExecShell('rm -rf {}/test.lock'.format(self.plugin_path))
            self.now_data.clear()
            return public.returnMsg(True, upload)
        except:
            self.now_data.clear()
            public.ExecShell('rm -rf {}/test.lock'.format(self.plugin_path))
            return public.returnMsg(False, traceback.format_exc())

    def get_test_status(self, get):
        """
        获取测速进度
        :param get:
        :return:
        """
        if self.now_data.count('s33') != 1:
            self.now_data.clear()
        if len(self.now_data) == 0:
            return {'status': False, 'upload': '等待测试',
                    'upload_flag': False, 'upload_size': 0}
        # if len(self.now_data) == 1:
        #     try:
        #         ping = public.readFile('{}/ping.log'.format(self.plugin_path))
        #         ping = re.findall(r"time=(\d+) ms", ping)
        #         if len(ping) > 0:
        #             ping = ping[-1]
        #         else:
        #             ping = 0
        #     except:
        #         ping = 0
        #     return {'status': False, 'ping': '服务器正在ping测试', 'upload': '排队中', 'download': '排队中',
        #             'ping_flag': True, 'upload_flag': False, 'download_flag': False, 'ping_size': ping,
        #             'upload_size': 0,
        #             'download_size': 0}
        elif len(self.now_data) == 1:
            try:
                upload_size = public.readFile('{}/upload.log'.format(self.plugin_path)).strip()
                upload_size = upload_size.split('\n')
                upload_size = [i for i in upload_size if
                               ':--' not in i and 'Total' not in i and 'curl:' not in i and i != '']
                upload_size = upload_size[-2].split(' ')
                upload_size = [i for i in upload_size if i != '']
                upload_size = int(upload_size[-1][:-1]) * 1024 * 8
            except:
                upload_size = 0
            return {'status': False, 'upload': '服务器正在测试中',
                    'upload_flag': True,
                    'upload_size': upload_size}
        # elif len(self.now_data) == 3:
        #     try:
        #         data = public.readFile('{}/download.log'.format(self.plugin_path))
        #         data = data.split('\n')
        #         if len(data) > 10:
        #             data = data[10:-1]
        #             dl = []
        #             for i in data:
        #                 if len(i.split(' ')) > 7:
        #                     public.print_log(i.split(' ')[-2][-1])
        #                     if i.split(' ')[-2][-1].lower() == 'k':
        #                         dl.append(int(float(i.split(' ')[-2][:-1]) * 1024 * 8))
        #                     elif i.split(' ')[-2][-1].lower() == 'm':
        #                         if len(dl) > 5:
        #                             if int(float(i.split(' ')[-2][:-1]) * 1024 * 1024 * 8) > 15 * dl[-1]:
        #                                 continue
        #                         dl.append(int(float(i.split(' ')[-2][:-1]) * 1024 * 1024 * 8))
        #                     elif i.split(' ')[-2][-1].lower() == 'g':
        #                         if len(dl) > 5:
        #                             if int(float(i.split(' ')[-2][:-1]) * 1024 * 1024 * 1024 * 8) > 15 * dl[-1]:
        #                                 continue
        #                         dl.append(int(float(i.split(' ')[-2][:-1]) * 1024 * 1024 * 1024 * 8))
        #             mean = np.mean(dl)  # 计算均值
        #             std = np.std(dl)  # 计算标准差
        #             # 定义阈值，通常是均值加减标准差的倍数
        #             threshold = 2
        #             # 去除离群值
        #             dl = [x for x in dl if (mean - threshold * std) <= x <= (mean + threshold * std)]
        #             download_size = dl[-1]
        #         else:
        #             download_size = 0
        #     except:
        #         download_size = 0
        #     return {'status': False, 'ping': '服务器ping测试成功', 'upload': '服务器发送测试成功',
        #             'download': '服务器正在下载测试', 'ping_flag': True, 'upload_flag': True, 'download_flag': True,
        #             'ping_size': self.now_data[1], 'upload_size': self.now_data[2],
        #             'download_size': download_size
        #             }
        # elif len(self.now_data) == 4:
        #     self.now_data.append('s33')
        #     return {'status': True, 'ping': '服务器ping测试成功', 'upload': '服务器发送测试成功',
        #             'download': '服务器下载测试成功', 'ping_flag': True, 'upload_flag': True, 'download_flag': True,
        #             'ping_size': self.now_data[1], 'upload_size': self.now_data[2],
        #             'download_size': self.now_data[3]
        #             }
        else:
            self.now_data.append('s33')
            return {'status': True, 'upload': '状态异常',
                    'upload_flag': False, 'upload_size': 0
                    }

    def get_network(self, get=None) -> List:
        """
        获取测速结果
        :param get:
        :return:
        """
        try:
            data = {}
            ll = []
            if self.get_bbr_config():
                json_path = '/www/server/panel/plugin/bt_bbr/data.json'
                if os.path.exists(json_path):
                    json_data = json.loads(public.readFile(json_path))
                    if 'unbbr' in json_data.keys():
                        data_sort = sorted(json_data['unbbr'])
                        num = math.ceil(len(data_sort) / 2)
                        if len(data_sort) == 1:
                            num = 0
                        unbbr_data = data_sort[num]
                    else:
                        unbbr_data = 0
                    if 'bbr' in json_data.keys() and len(json_data['bbr']) > 0:
                        bbr_data = json_data['bbr'][-1]
                    else:
                        bbr_data = 0
                else:
                    bbr_data = 0
                    unbbr_data = 0
                ll = [bbr_data, unbbr_data]
            else:
                json_path = '/www/server/panel/plugin/bt_bbr/data.json'
                if os.path.exists(json_path):
                    json_data = json.loads(public.readFile(json_path))
                    if 'unbbr' in json_data.keys() and len(json_data['unbbr']) > 0:
                        unbbr_data = json_data['unbbr'][-1]
                    else:
                        unbbr_data = 0
                else:
                    unbbr_data = 0
                ll = [0, unbbr_data]
            if self.get_bbr_config():
                data = {'upload_size': ll[0], 'list': ll}
            else:
                data = {'upload_size': ll[1], 'list': ll}
        except:
            data = {'upload_size': 0, 'list': [0, 0]}
        return data

    # 获取BBR当前使用状态
    def get_bbr_config(self, get=None) -> bool:
        """
        获取当前BBR的应用状态
        如果十分钟内没有进行测速记录，则后台运行测速进程，存储到last_data.json中
        :param get:
        :return: true|false
        """
        res = public.ExecShell('sysctl net.ipv4.tcp_congestion_control')
        if res[0] and 'bbr' in res[0]:
            return True
        else:
            return False

    # 优化网络配置 -- 首先备份原有配置后进行修改
    def optimize_network(self, get):
        """
        优化网络配置，备份原先配置后，再将优化参数填入
        优化文件包括：/etc/sysctl.conf，/etc/security/limits.conf 存储地址为源地址+.bak
        :param get:
        :return:
        """
        try:
            backup_file1 = '/etc/sysctl.conf.bak'
            backup_file2 = '/etc/security/limits.conf.bak'
            if os.path.exists('/etc/sysctl.conf') and os.path.exists('/etc/security/limits.conf'):
                if not os.path.exists(backup_file1):
                    shutil.copy2('/etc/sysctl.conf', backup_file1)
                if not os.path.exists(backup_file2):
                    shutil.copy2('/etc/security/limits.conf', backup_file2)
            else:
                return public.returnMsg(False, '配置文件不存在，无法进行优化！')

            with open('/etc/sysctl.conf', 'r') as f:
                lines = f.readlines()
            with open('/etc/sysctl.conf', 'w') as f:
                for line in lines:
                    if not any(keyword in line for keyword in
                               ['fs.file-max', 'fs.inotify.max_user_instances', 'net.ipv4.tcp_tw_reuse',
                                'net.ipv4.ip_local_port_range', 'net.ipv4.tcp_rmem', 'net.ipv4.tcp_wmem',
                                'net.core.somaxconn', 'net.core.rmem_max', 'net.core.wmem_max',
                                'net.core.wmem_default',
                                'net.ipv4.tcp_max_tw_buckets', 'net.ipv4.tcp_max_syn_backlog',
                                'net.core.netdev_max_backlog', 'net.ipv4.tcp_slow_start_after_idle',
                                'net.ipv4.ip_forward']):
                        f.write(line)
            with open('/etc/sysctl.conf', 'a') as f:
                f.write('fs.file-max = 1000000\n'
                        'fs.inotify.max_user_instances = 8192\n'
                        'net.ipv4.tcp_tw_reuse = 1\n'
                        'net.ipv4.ip_local_port_range = 1024 65535\n'
                        'net.ipv4.tcp_rmem = 16384 262144 8388608\n'
                        'net.ipv4.tcp_wmem = 32768 524288 16777216\n'
                        'net.core.somaxconn = 8192\n'
                        'net.core.rmem_max = 16777216\n'
                        'net.core.wmem_max = 16777216\n'
                        'net.core.wmem_default = 2097152\n'
                        'net.ipv4.tcp_max_tw_buckets = 5000\n'
                        'net.ipv4.tcp_max_syn_backlog = 10240\n'
                        'net.core.netdev_max_backlog = 10240\n'
                        'net.ipv4.tcp_slow_start_after_idle = 0\n'
                        '# forward ipv4\n'
                        'net.ipv4.ip_forward = 1\n')
            os.system("sysctl -p")
            with open('/etc/security/limits.conf', 'w') as f:
                f.write('*               soft    nofile           1000000\n'
                        '*               hard    nofile          1000000\n')
            with open('/etc/profile', 'a') as f:
                f.write('ulimit -SHn 1000000\n')
            return public.returnMsg(True, '网络配置优化成功！')
        except:
            public.returnMsg(False, '网络配置优化失败，请恢复默认配置！')

    # 恢复到优化之前的网络配置
    def restore_network_configuration(self, get):
        """
        恢复优化前的配置文件
        :return:
        """
        traceback.format_exc()
        backup_file1 = '/etc/sysctl.conf.bak'
        backup_file2 = '/etc/security/limits.conf.bak'
        if os.path.exists(backup_file1) and os.path.exists(backup_file2):
            shutil.copy2(backup_file1, '/etc/sysctl.conf')
            shutil.copy2(backup_file2, '/etc/security/limits.conf')
            return public.returnMsg(True, "配置已恢复，<span style='color:red'>重启服务器</span>后配置生效！")
        else:
            return public.returnMsg(False, '备份文件不存在，无法进行恢复！')

    # 获取网络配置
    def get_network_conf(self, get):
        """
        :param get:
        :return: {}网络配置
        """
        kernel_params = ['fs.file-max', 'fs.inotify.max_user_instances', 'net.ipv4.tcp_tw_reuse',
                         'net.ipv4.ip_local_port_range', 'net.ipv4.tcp_rmem', 'net.ipv4.tcp_wmem',
                         'net.core.somaxconn', 'net.core.rmem_max', 'net.core.wmem_max', 'net.core.wmem_default',
                         'net.ipv4.tcp_max_tw_buckets', 'net.ipv4.tcp_max_syn_backlog',
                         'net.core.netdev_max_backlog', 'net.ipv4.tcp_slow_start_after_idle',
                         'net.ipv4.ip_forward']
        result_dict = {}
        for param in kernel_params:
            result = subprocess.run(['sysctl', '-n', param], stdout=subprocess.PIPE)
            value = result.stdout.decode().strip()
            result_dict[param] = value
        return result_dict

    # 风险操作
    # 升级内核？ --强提醒需要有快照或恢复的方法,否则不建议升级
    # def upgrade_kenel(self, get):
    #     if self.check_kernel_version():
    #         return public.returnMsg(False, '当前内核支持加速算法，升级内核将会带来位置风险，操作已中止！')
    #     if not 'centos' in platform.linux_distribution()[0].lower():
    #         return public.returnMsg(False, '当前版本仅支持Centos系统升级内核！')
    #     os.system('sh /www/server/panel/plugin/BBR/UpgradeKenel.sh')
    #     time.sleep(1)
    #     if self.check_kernel_version():
    #         return public.returnMsg(True, '内核升级成功！')
    #     else:
    #         public.returnMsg(False, '内核升级出错，请手动升级！')

    # 判断linux的内核是否升级成功
    # def check_kernel_version(self):
    #     kernel_version = os.uname().release
    #     pattern = re.compile(r'^(\d+)\.(\d+)')
    #     match = pattern.match(kernel_version)
    #     if match:
    #         major_version = int(match.group(1))
    #         minor_version = int(match.group(2))
    #         if major_version > 4 or (major_version == 4 and minor_version >= 9):
    #             return True
    #     return False

    # def get_kernel_version(self, get):
    #     kernel_version = platform.uname().release
    #     if self.check_kernel_version():
    #         return {'status': True, 'ps': '当前系统内核支持BBR加速配置，内核版本：{}'.format(kernel_version)}
    #     else:
    #         return {'status': False, 'ps': '当前系统内核不支持BBR加速配置，内核版本：{}，Centos系统请点击升级内核，其它系统请手动升级到内核4.9.0以上'.format(kernel_version)}


if __name__ == '__main__':
    bbr = bt_bbr_main()
    bbr.run_speedtest()
