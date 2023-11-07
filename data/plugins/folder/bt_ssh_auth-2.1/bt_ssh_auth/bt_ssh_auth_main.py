# coding: utf-8
# +-------------------------------------------------------------------
# | version :1.0
# +-------------------------------------------------------------------
# | Author: 梁凯强 <1249648969@qq.com>
# +-------------------------------------------------------------------
# | SSH 双因子认证
# +--------------------------------------------------------------------
import requests

import config
import public, re, os
import platform, time, json


class bt_ssh_auth_main:
    __SSH_CONFIG = '/etc/ssh/sshd_config'
    __PAM_CONFIG = '/etc/pam.d/sshd'
    __python_pam = '/usr/pam_python_so'
    __config_pl = '/www/server/panel/data/pam_btssh_authentication.pl'
    __bt_timestamp = '/www/server/panel/data/bt_timestamp.pl'
    __local_timestamp = '/www/server/panel/data/local_timestamp.pl'
    __uname_info = '/www/server/panel/data/uname_data'

    def __init__(self):
        '''检查pam_python目录是否存在'''
        if not os.path.exists(self.__python_pam):
            public.ExecShell("mkdir -p " + self.__python_pam)
            public.ExecShell("chmod 600 " + self.__python_pam)
        if not os.path.exists(self.__config_pl):
            public.ExecShell("echo  '%s' >>%s" % (public.GetRandomString(64), self.__config_pl))
            public.ExecShell("chmod 600 " + self.__config_pl)


    def wirte(self, file, ret):
        result = public.writeFile(file, ret)
        return result

    # 重启SSH
    # def restart_ssh(self):
    #     act = 'restart'
    #     if os.path.exists('/etc/redhat-release'):
    #         version = public.readFile('/etc/redhat-release')
    #         if isinstance(version, str):
    #             if version.find(' 7.') != -1 or version.find(' 8.') != -1:
    #                 public.ExecShell("systemctl " + act + " sshd.service")
    #             else:
    #                 public.ExecShell("/etc/init.d/sshd " + act)
    #         else:
    #             public.ExecShell("/etc/init.d/sshd " + act)
    #     else:
    #         public.ExecShell("/etc/init.d/sshd " + act)

    # 重启SSH
    def restart_ssh(self):
        distro = None
        # centos
        if os.path.exists('/etc/redhat-release'):
            version = public.readFile('/etc/redhat-release')
            if isinstance(version, str):
                # Alibaba Cloud ECS
                if version.find('Alibaba Cloud') != -1:
                    distro = 'centos'
                # Stream测试环境
                elif version.find('Stream') != -1:
                    distro = 'centos'
                if version.find(' 7.') != -1:
                    distro = 'centos'
                elif version.find(' 8.') != -1:
                    distro = 'centos'
        # Ubuntu
        elif os.path.exists('/etc/lsb-release'):
            version = public.readFile('/etc/lsb-release')
            if isinstance(version, str):
                if version.find('16.') != -1:
                    distro = 'ubuntu'
                elif version.find('20.') != -1:
                    distro = 'ubuntu'
                elif version.find('18.') != -1:
                    distro = 'ubuntu'
        # debian
        elif os.path.exists('/etc/debian_version'):
            version = public.readFile('/etc/debian_version')
            if isinstance(version, str):
                if version.find('9.') != -1:
                    distro = 'debian'
                elif version.find('10.') != -1:
                    distro = 'debian'
        if distro == 'debian' or distro == 'ubuntu':
            public.ExecShell('systemctl restart ssh')
        elif distro == 'centos':
            public.ExecShell('systemctl restart sshd')
        else:
            return False

    # 查找PAM目录
    def get_pam_dir(self):
        # Centos 系列
        if os.path.exists('/etc/redhat-release'):
            version = public.readFile('/etc/redhat-release')
            if isinstance(version, str):
                # Alibaba Cloud ECS
                if version.find('Alibaba Cloud') != -1:
                    return 'auth  requisite  %s/pam_btssh_authentication.so' % (self.__python_pam)
                # Stream测试环境
                elif version.find('Stream') != -1:
                    return 'auth  requisite  %s/pam_btssh_authentication.so' % (self.__python_pam)
                if version.find(' 7.') != -1:
                    return 'auth  requisite  %s/pam_btssh_authentication.so' % (self.__python_pam)
                elif version.find(' 8.') != -1:
                    return 'auth  requisite  %s/pam_btssh_authentication.so' % (self.__python_pam)
                else:
                    return False
        # Ubuntu
        elif os.path.exists('/etc/lsb-release'):
            version = public.readFile('/etc/lsb-release')
            if isinstance(version, str):
                if version.find('16.') != -1:
                    return 'auth  requisite  %s/pam_btssh_authentication.so' % (self.__python_pam)
                elif version.find('20.') != -1:
                    return 'auth  requisite  %s/pam_btssh_authentication.so' % (self.__python_pam)
                elif version.find('18.') != -1:
                    return 'auth  requisite  %s/pam_btssh_authentication.so' % (self.__python_pam)
                else:
                    return False
        # debian
        elif os.path.exists('/etc/debian_version'):
            version = public.readFile('/etc/debian_version')
            if isinstance(version, str):
                if version.find('9.') != -1:
                    return 'auth  requisite  %s/pam_btssh_authentication.so' % (self.__python_pam)
                elif version.find('10.') != -1:
                    return 'auth  requisite  %s/pam_btssh_authentication.so' % (self.__python_pam)
                else:
                    return False
        return False

    # 判断PAMSO文件是否存在
    def isPamSoExists(self):
        check2 = self.get_pam_dir()  # 'auth  requisite  /usr/pam_python_so/pam_btssh_authentication.so'
        if not check2: return False
        check = check2.split()
        if len(check) < 3: return False
        if os.path.exists(check[2]):
            # 判断文件MD5
            # if public.FileMd5(check[2]) != "7916c2ede1c4d7eecc437443e7be5b70":
                # self.install_pam_python(check)
                # return False
            # if os.path.getsize(check[2]) < 10240:
            #     # 删除文件后重新下载
            #     try:
            #         os.remove(check[2])
            #     except:
            #         return False
            #     self.install_pam_python(check)
            #     return self.isPamSoExists()
            return check2
        # else:
        #     self.install_pam_python(check)
        #     return self.isPamSoExists()

    # 安装pam_python
    def install_pam_python(self, check):
        so_path = check[2]
        so_name = check[2].split('/')[-1]
        public.ExecShell(
            '/usr/local/curl/bin/curl -o %s http://download.bt.cn/btwaf_rule/pam_python_so/%s' % (so_path, so_name))
        public.ExecShell("chmod 600 " + so_path)
        return True

    # 开启双因子认证
    def start_ssh_authentication(self):
        check = self.isPamSoExists()  # 'auth  requisite  /usr/pam_python_so/pam_btssh_authentication.so'
        if not check: return False
        if os.path.exists(self.__PAM_CONFIG):  # 'etc/pam.d/sshd'
            auth_data = public.readFile(self.__PAM_CONFIG)
            if isinstance(auth_data, str):
                if auth_data.find("\n" + check) != -1:
                    return True
                else:
                    auth_data = auth_data + "\n" + check
                    public.writeFile(self.__PAM_CONFIG, auth_data)
                    return True
        return False

    # 关闭双因子认证
    def stop_ssh_authentication(self):
        check = self.isPamSoExists()
        if not check: return False
        if os.path.exists(self.__PAM_CONFIG):
            auth_data = public.readFile(self.__PAM_CONFIG)
            if isinstance(auth_data, str):
                if auth_data.find("\n" + check) != -1:
                    auth_data = auth_data.replace("\n" + check, '')
                    public.writeFile(self.__PAM_CONFIG, auth_data)
                    return True
                else:
                    return False
        return False

    # 检查是否开启双因子认证
    def check_ssh_authentication(self):
        check = self.isPamSoExists()
        if not check: return False
        if os.path.exists(self.__PAM_CONFIG):
            auth_data = public.readFile(self.__PAM_CONFIG)
            if isinstance(auth_data, str):
                if auth_data.find("\n" + check) != -1:
                    return True
                else:
                    return False
        return False

    # 关闭空密码登录
    def stop_empty_password(self):
        '''
        关闭空密码登录
        无参数传递
        '''
        file = public.readFile(self.__SSH_CONFIG)
        if isinstance(file, str):
            if file.find('PermitEmptyPasswords') != -1:
                file_result = file.replace('\nPermitEmptyPasswords yes', '\nPermitEmptyPasswords no')
                self.wirte(self.__SSH_CONFIG, file_result)
                self.restart_ssh()
                return public.returnMsg(True, '关闭空密码认证成功')
            else:
                return public.returnMsg(False, '没有空密码认证')
        return public.returnMsg(False, '没有空密码认证')

    # 设置SSH应答模式
    def set_ssh_login_user(self):
        ssh_password = '\nChallengeResponseAuthentication\s\w+'
        file = public.readFile(self.__SSH_CONFIG)
        if isinstance(file, str):
            if len(re.findall(ssh_password, file)) == 0:
                file_result = file + '\nChallengeResponseAuthentication yes'
            else:
                file_result = re.sub(ssh_password, '\nChallengeResponseAuthentication yes', file)
            self.wirte(self.__SSH_CONFIG, file_result)
            if not self.restart_ssh():
                public.returnMsg(False, 'ssh重启失败')
        return public.returnMsg(True, '开启成功')

    # 关闭SSH应答模式
    def close_ssh_login_user(self):
        file = public.readFile(self.__SSH_CONFIG)
        ssh_password = '\nChallengeResponseAuthentication\s\w+'
        if isinstance(file, str):
            file_result = re.sub(ssh_password, '\nChallengeResponseAuthentication no', file)
            self.wirte(self.__SSH_CONFIG, file_result)
            if not self.restart_ssh():
                public.returnMsg(False, 'ssh重启失败')
        return public.returnMsg(True, '关闭成功')

    # 查看SSH应答模式
    def check_ssh_login_user(self):
        file = public.readFile(self.__SSH_CONFIG)
        ssh_password = '\nChallengeResponseAuthentication\s\w+'
        if isinstance(file, str):
            ret = re.findall(ssh_password, file)
            if not ret:
                return False
            else:
                if ret[-1].split()[-1] == 'yes':
                    return True
                else:
                    return False
        return False

    # 关闭密码访问
    def stop_password(self):
        '''
        关闭密码访问
        无参数传递
        '''
        file = public.readFile(self.__SSH_CONFIG)
        if isinstance(file, str):
            if file.find('PasswordAuthentication') != -1:
                file_result = file.replace('\nPasswordAuthentication yes', '\nPasswordAuthentication no')
                self.wirte(self.__SSH_CONFIG, file_result)
                self.restart_ssh()
                return public.returnMsg(True, '关闭密码认证成功')
            else:
                return public.returnMsg(False, '没有密码认证')
        return public.returnMsg(False, '没有密码认证')

    # 开启密码登录
    def start_password(self):
        '''
        开启密码登陆
        get: 无需传递参数
        '''
        file = public.readFile(self.__SSH_CONFIG)
        if isinstance(file, str):
            if file.find('PasswordAuthentication') != -1:
                file_result = file.replace('\nPasswordAuthentication no', '\nPasswordAuthentication yes')
                self.wirte(self.__SSH_CONFIG, file_result)
                self.restart_ssh()
                return public.returnMsg(True, '开启密码认证成功')
            else:
                file_result = file + '\nPasswordAuthentication yes'
                self.wirte(self.__SSH_CONFIG, file_result)
                self.restart_ssh()
                return public.returnMsg(True, '开启密码认证成功')
        return public.returnMsg(False, '没有密码认证')

    # 查看密码登录状态
    def check_password(self):
        '''
        查看密码登录状态
        无参数传递
        '''
        file = public.readFile(self.__SSH_CONFIG)
        ssh_password = '\nPasswordAuthentication\s\w+'
        if isinstance(file, str):
            ret = re.findall(ssh_password, file)
            if not ret:
                return False
            else:
                if ret[-1].split()[-1] == 'yes':
                    return True
                else:
                    return False
        return False

    # 检查是否设置了钉钉
    def check_dingding(self, get):
        '''
        检查是否设置了钉钉
        '''
        # 检查文件是否存在
        if not os.path.exists('/www/server/panel/data/dingding.json'): return False
        dingding_config = public.ReadFile('/www/server/panel/data/dingding.json')
        if not dingding_config: return False
        # 解析json
        try:
            dingding = json.loads(dingding_config)
            if dingding['dingding_url']:
                return True
        except:
            return False

    # 检查是否设置了飞书
    def check_feishu(self, get):
        '''
        检查是否设置了飞书
        '''
        # 检查文件是否存在
        if not public.init_msg("feishu"): return False
        if not os.path.exists('/www/server/panel/data/feishu.json'): return False
        feishu_config = public.ReadFile('/www/server/panel/data/feishu.json')
        if not feishu_config: return False
        # 解析json
        try:
            feishu = json.loads(feishu_config)
            if feishu['feishu_url']:
                return True
        except:
            return False


    # 开启SSH 双因子认证
    def start_ssh_auth(self, get):
        if not self.get_pam_dir(): return public.returnMsg(False, '不支持该系统')
        if not self.check_feishu(get): return public.returnMsg(False, '未配置发送飞书设置')
        check = self.isPamSoExists()  # 'auth  requisite  /usr/pam_python_so/pam_btssh_authentication.so'
        if not check: return 'False'
        if not self.check_ssh_login_user():
            self.set_ssh_login_user()
        if not self.check_ssh_authentication():
            self.start_ssh_authentication()
        # 如果开启的话，就关闭密码认证
        # if self.check_password():
        #     self.stop_password()
        self.stop_empty_password()
        if not self.restart_ssh():
            public.returnMsg(False, 'ssh重启失败')
        # 检查是否开启双因子认证
        if self.check_ssh_authentication() and self.check_ssh_login_user():
            return public.returnMsg(True, '开启成功')
        return public.returnMsg(True, '开启失败')

    # 关闭SSH 双因子认证
    def stop_ssh_auth(self, get):
        if not self.get_pam_dir(): return public.returnMsg(False, '不支持该系统')
        if not self.check_feishu(get): return public.returnMsg(False, '未配置发送飞书设置')
        check = self.isPamSoExists()
        if not check: return False
        if self.check_ssh_authentication():
            self.stop_ssh_authentication()
        # 检查是否关闭双因子认证
        # 如果是关闭的SSH，那么就开启
        # if not self.check_password():
        #     self.start_password()
        if not self.restart_ssh():
            public.returnMsg(False, 'ssh重启失败')
        if not self.check_ssh_authentication():
            return public.returnMsg(True, '已关闭')
        if self.stop_ssh_authentication():
            return public.returnMsg(True, '已关闭')

    def is_check(self, get):
        if not self.get_pam_dir(): return public.returnMsg(False, '不支持该系统')
        if not self.check_feishu(get): return public.returnMsg(False, '未配置发送飞书设置')
        return public.returnMsg(True, '已经配置')

    # 检查是否开启双因子认证
    def check_ssh_auth(self, get):
        if not self.get_pam_dir(): return public.returnMsg(False, '不支持该系统')
        if not self.check_feishu(get): return public.returnMsg(False, '未配置发送飞书设置')
        check = self.isPamSoExists()
        if not check: return False
        if not self.check_ssh_login_user():
            return public.returnMsg(False, '未开启')
        if not self.check_ssh_authentication():
            return public.returnMsg(False, '未开启')
        return public.returnMsg(True, '已开启')

    def is_check_so(self):
        '''判断SO文件是否存在'''
        if not self.get_pam_dir(): return public.returnMsg(False, '不支持该系统')
        config_data = self.get_pam_dir()
        if not config_data: return False
        config_data2 = config_data.split()
        ret = {}
        ret['so_path'] = config_data2[2].split('/')[-1]
        if os.path.exists(config_data2[2]):
            ret['so_status'] = True
        else:
            ret['so_status'] = False
        return public.returnMsg(True, ret)

    def download_so(self):
        '''下载so文件'''
        if not self.get_pam_dir(): return public.returnMsg(False, '不支持该系统')
        config_data = self.get_pam_dir()
        if not config_data: return False
        config_data = config_data.split()
        self.install_pam_python(config_data)
        # 判断下载的文件大小
        if os.path.exists(config_data[2]):
            if os.path.getsize(config_data[2]) > 10240:
                return public.returnMsg(True, "下载文件成功")
        return public.returnMsg(False, "下载失败")

    # 获取Linux系统的主机名
    def get_pin(self, get):
        if not self.check_feishu(get): return public.returnMsg(False, '未配置发送飞书设置')
        if not os.path.exists(self.__bt_timestamp):
            if not self.sync_time():
                return {'pin': 'error', 'time': 60}
        if not os.path.exists(self.__local_timestamp):
            public.WriteFile(self.__local_timestamp, str(time.time()))
        # 本地时间
        local_time = time.time()
        # 从文件中读取上一次本地时间
        last_local_time = self.read_timestamp_from_file(self.__local_timestamp)
        # 从文件中读取上一次云端时间
        last_bt_time = self.read_timestamp_from_file(self.__bt_timestamp)
        tmp = time.strftime('%S', time.localtime(last_bt_time))
        # 对比若本地时间与上一次本地时间的差值大于等于上次云端时间离下一个整分钟的值，则重新取云端时间，并保存本地时间
        if int(local_time-last_local_time) >= (60-int(tmp)):
            if not self.sync_time():
                return {'pin': 'error', 'time': 60}
            public.WriteFile(self.__local_timestamp, str(local_time))
        bt_time = time.localtime(self.read_timestamp_from_file(self.__bt_timestamp))
        last_local_time = self.read_timestamp_from_file(self.__local_timestamp)
        tme_data = time.strftime('%Y-%m-%d%H:%M', bt_time)
        # 获取秒
        tis_data = time.strftime('%S', bt_time)
        ip_list = public.ReadFile('/www/server/panel/data/pam_btssh_authentication.pl')
        data = platform.uname()[0] + platform.uname()[1] + platform.uname()[2]
        ret = {}
        if isinstance(ip_list, str):
            info = data + tme_data + ip_list
            md5_info = public.Md5(info)
            ret['pin'] = md5_info[:6]
            ret['time'] = 60 - int(tis_data) - int(local_time - last_local_time)
            return ret
        else:
            ret['pin'] = 'error'
            ret['time'] = 60
            return ret

    # 返回IP 验证码 过期时间
    def get_pin_msg(self, get):
        if not self.get_pam_dir(): return public.returnMsg(False, '不支持该系统')
        if not self.check_feishu(get): return public.returnMsg(False, '未配置发送飞书设置')
        if not os.path.exists(self.__bt_timestamp):
            if not self.sync_time():
                return {'pin': 'error', 'time': 60}
        if not os.path.exists(self.__local_timestamp):
            public.WriteFile(self.__local_timestamp, str(time.time()))
        bt_time = time.localtime(self.read_timestamp_from_file(self.__bt_timestamp))
        tme_data = time.strftime('%Y-%m-%d%H:%M', bt_time)
        # 获取秒
        tis_data = time.strftime('%S', bt_time)
        ip_list = public.ReadFile('/www/server/panel/data/pam_btssh_authentication.pl')
        ret = {}
        data = platform.uname()[0] + platform.uname()[1] + platform.uname()[2]
        if isinstance(ip_list, str):
            info = data + tme_data + ip_list
            md5_info = public.Md5(info)
            ret['pin'] = md5_info[:6]
            # 本地时间
            local_time = time.time()
            # 从文件中读取上一次本地时间
            last_local_time = self.read_timestamp_from_file(self.__local_timestamp)
            ret['time'] = 60 - int(tis_data) - int(local_time - last_local_time)
            qrcode = (public.getPanelAddr() + "|" + str(60 - int(tis_data) - int(local_time - last_local_time)) + "|" + ret['pin']).encode('utf-8')
            ret['qrcode'] = public.base64.b64encode(qrcode).decode('utf-8')
            return ret
        else:
            key = public.GetRandomString(64)
            public.ExecShell("echo  '%s' >>%s" % (key, self.__config_pl))
            public.ExecShell("chmod 600 " + self.__config_pl)
            tme_data = time.strftime('%Y-%m-%d%H:%M', bt_time)
            info = data + tme_data + key
            md5_info = public.Md5(info)
            ret['pin'] = md5_info[:6]
            ret['time'] = 60
            qrcode = (public.getPanelAddr() + "|" + str(60 - int(tis_data)) + "|" + ret['pin']).encode('utf-8')
            ret['qrcode'] = public.base64.b64encode(qrcode).decode('utf-8')
            return ret

    # 从云端同步时间
    def sync_time(self):
        import requests
        try:
            source = requests.get('https://www.bt.cn/api/bt_waf/timestamp').text
            time_struct = time.localtime(float(source))
            public.WriteFile(self.__bt_timestamp, source)
            return time_struct
        except Exception as e:
            return False

    # 从文件中读取时间戳
    def read_timestamp_from_file(self, filename):
        with open(filename, 'r') as f:
            return float(f.read().strip())

    # 校验uname是否有变化
    # def check_uname(self):
    #     uname = platform.uname()[0] + platform.uname()[1] + platform.uname()[2]
    #     if not os.path.exists(self.__uname_info):
    #         public.WriteFile(self.__uname_info, uname)
    #         return False
    #     last_uname = public.ReadFile(self.__uname_info).strip()
    #     if uname != last_uname:
    #         public.WriteFile(self.__uname_info, uname)
    #         return False
    #     return uname
