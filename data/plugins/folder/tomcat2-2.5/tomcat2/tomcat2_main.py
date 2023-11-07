#!/usr/bin/python
# coding: utf-8
# -----------------------------
# 宝塔Linux面板 tomcat 管理器
# Author: <1249648969@qq.com>
'''
//      ┏┛ ┻━━━━━┛ ┻┓
//      ┃　　　━　　　┃
//      ┃　┳┛　  ┗┳　┃
//      ┃　　　-　　　┃
//      ┗━┓　　　┏━━━┛   你瞅啥，瞅你咋地！
//        ┃　　　┗━━━━━━━━━┓
//        ┗━┓ ┓ ┏━━━┳ ┓ ┏━┛
//          ┗━┻━┛   ┗━┻━┛
'''
import sys, os, time

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
sys.path.append("class/")
import public, re, psutil, files, json, firewalls
from xml.etree.ElementTree import ElementTree, Element

class file: path = encoding = ''
class mobj: port = ps = ''
class liang: version = ''


def check_port(port):
    a = public.ExecShell("netstat -nltp|awk '{print $4}'")
    if a[0]:
        if re.search(':'+port+'\n',a[0]):
            return True
        else:return False
    else:return False


class tomcat2_main(object):
    __tomcat7 = '/www/server/tomcat7'
    __tomcat8 = '/www/server/tomcat8'
    __tomcat9 = '/www/server/tomcat9'
    __tomcat7_config = '/etc/init.d/tomcat7'
    __tomcat8_config = '/etc/init.d/tomcat8'
    __tomcat9_config = '/etc/init.d/tomcat9'
    __tomcat7_server = '/www/server/tomcat7/conf/server.xml'
    __tomcat8_server = '/www/server/tomcat8/conf/server.xml'
    __tomcat9_server = '/www/server/tomcat9/conf/server.xml'
    __site_path='/www/server/tomcat_site/'
    __jdk_7 = '/usr/java/jdk1.7.0_80'
    __jdk_8 = '/usr/java/jdk1.8.0_121'
    __jdk_11 = '/usr/java/jdk-11.0.2'
    __jdk_8_191 = '/usr/java/jdk1.8.0_191-amd64'
    __tomcat7_log = '/www/server/tomcat7/logs/catalina-daemon.out'
    __tomcat8_log = '/www/server/tomcat8/logs/catalina-daemon.out'
    __tomcat9_log = '/www/server/tomcat9/logs/catalina-daemon.out'
    __tomcat7_jkd = '/www/server/tomcat7/bin/daemon.sh'
    __tomcat8_jkd = '/www/server/tomcat8/bin/daemon.sh'
    __tomcat9_jkd = '/www/server/tomcat9/bin/daemon.sh'
    __files = ''
    __TREE = None
    __ENGINE = None
    __ROOT = None
    __version_dict = {}
    __CONF_FILE = ''
    __user_config = '/www/server/panel/plugin/tomcat/user.json'
    __CONNECTROR = ''
    __tmp = '/tmp/firelll.json'

    def __init__(self):
        if not os.path.exists(self.__site_path):
            os.system('mkdir -p /www/server/tomcat_site/')
        if not self.__files: files.files()


    # 开启端口
    def SetPort(self):
        import firewalls
        fs = firewalls.firewalls()
        get = mobj()
        for i in range(8080, 8083):
            get.port = str(i)
            get.ps = 'tomcat外部端口'
            fs.AddAcceptPort(get)
        return True

    # 下载jdk
    def __install_jdk(self, downloadurl, jdkv):
        bit = public.ExecShell("getconf LONG_BIT")[0].split()[0]
        localjdk = "/www/server/panel/plugin/tomcat2/jdk-%s-linux-x%s.rpm" % (jdkv, bit)
        if not os.path.exists(localjdk):
            url = "%s/install/src/jdk-%s-linux-x%s.rpm" % (downloadurl, jdkv, bit)
            self.__download_file(url, localjdk)
            os.system("rm -f {target} && cp {source} {target}".format(source=localjdk, target="/tmp/java-jdk.rpm"))
        else:
            os.system("rm -f {target} && cp {source} {target}".format(source=localjdk, target="/tmp/java-jdk.rpm"))

    # 下载文件
    def __download_file(self, url, filename):
        try:
            path = os.path.dirname(filename)
            if not os.path.exists(path): os.makedirs(path)
            import urllib, socket
            socket.setdefaulttimeout(10)
            if sys.version_info[0] == 2:
                urllib.urlretrieve(url, filename=filename)
            else:
                urllib.request.urlretrieve(url, filename=filename)
        except:
            time.sleep(5)
            self.__download_file(url, filename)

    # 安装接口
    def InstallTomcat(self, get):
        self.SetPort()
        version = get.version.strip()
        type = get.type.strip()
        version_list = ["7", "8", "9"]
        jdkv = "7u80"
        if version == 'tomcat7':
            version = "7"
        if version == 'tomcat8':
            version = "8"
            jdkv = "8u121"
        if version == 'tomcat9':
            version = "9"
            jdkv = "8u121"
        if version in version_list:
            if type == 'install':
                self.__install_jdk(str(public.get_url()), jdkv)
                if os.path.exists("/tmp/tomcat2.sh"):
                    public.ExecShell(
                        "cd /tmp && rm -rf /tmp/tomcat2.sh && wget -O tomcat2.sh %s/install/0/tomcat2.sh && bash -x  tomcat2.sh install %s >>/tmp/tomcat.json" % (
                        str(public.get_url()), str(version)))
                else:
                    public.ExecShell(
                        "cd /tmp && wget -O tomcat2.sh %s/install/0/tomcat2.sh && bash -x  tomcat2.sh install %s >>/tmp/tomcat.json" % (
                        str(public.get_url()), str(version)))
                return public.returnMsg(True, "安装成功")
            elif type == 'uninstall':
                if os.path.exists("/tmp/tomcat2.sh"):
                    public.ExecShell(
                        "cd /tmp && rm -rf /tmp/tomcat2.sh && wget -O tomcat2.sh %s/install/0/tomcat2.sh && bash -x  tomcat2.sh uninstall %s >>/tmp/tomcat.json" % (
                        str(public.get_url()), str(version)))
                else:
                    public.ExecShell(
                        "cd /tmp && wget -O tomcat2.sh %s/install/0/tomcat2.sh && bash -x  tomcat2.sh uninstall %s >>/tmp/tomcat.json" % (
                        str(public.get_url()), str(version)))
                return public.returnMsg(True, "卸载成功")
            else:
                return public.returnMsg(False, "类型错误")
        else:
            return public.returnMsg(False, "类型错误")

    # 查看安装日志
    def GetSetLog(self, get):
        log_path = '/tmp/tomcat.json'
        if os.path.exists(log_path):
            ret = self.GetLog(log_path)
            if ret:
                return public.returnMsg(True, ret)
            else:
                return public.returnMsg(True, "日志为空")
        else:
            return public.returnMsg(True, "日志为空")

    # xml 初始化
    def Xml_init(self, path):
        try:
            self.__CONF_FILE = str(path)
            self.__TREE = ElementTree()
            self.__TREE.parse(self.__CONF_FILE)
            self.__ROOT = self.__TREE.getroot()
            self.__ENGINE = self.__TREE.findall('Service/Engine')[0]
            self.__CONNECTROR = self.__TREE.findall('Service/Connector')
            return True
        except:
            return False

        # 获取文件夹
    def file_name2(self):
        data = self.file_return()
        if len(data) == 0: return []
        result = []
        for i in data:
            ret = {}
            site_config = self.__site_path + i + '/conf/server.xml'
            if not os.path.exists(site_config): continue
            version_path = self.__site_path + i + '/version.pl'
            if not os.path.exists(version_path): continue
            try:
                version=public.ReadFile(version_path).strip().split('.')[0]
                list = self.GetServerJdk2(version='tomcat%s'%version,site=i)
                if list:
                    ret[i] = list
                    get = liang()
                    get.version = version
                    if not self.Initialization2(version,i):
                        ret[i]['port'] = False
                    else:
                        port = self.GetPort()
                        ret[i]['port'] = port
            except:
                continue
            result.append(ret)
        return result

    # 返回安装的tomcat 版本 服务状态 和JDK 版本
    def TomcatVersion(self, get):
        ret = {}
        if os.path.exists(self.__tomcat7) and os.path.exists(self.__tomcat7_config):
            # 取服务状态
            # JDK 版本
            list = self.GetServerJdk(version='tomcat7')
            if list:
                ret['tomcat7'] = list
                get = liang()
                get.version = '7'
                if not self.Initialization(get.version):
                    ret['tomcat7']['port'] = False
                else:
                    port = self.GetPort()
                    ret['tomcat7']['port'] = port
            else:
                ret['tomcat7'] = False
        else:
            ret['tomcat7'] = False
        if os.path.exists(self.__tomcat8) and os.path.exists(self.__tomcat8_config):
            list = self.GetServerJdk(version='tomcat8')
            if list:
                ret['tomcat8'] = list
                get = liang()
                get.version = '8'
                if not self.Initialization(get.version):
                    ret['tomcat8']['port'] = False
                else:
                    port = self.GetPort()
                    ret['tomcat8']['port'] = port
            else:
                ret['tomcat8'] = False
        else:
            ret['tomcat8'] = False
        if os.path.exists(self.__tomcat9) and os.path.exists(self.__tomcat9_server):
            list = self.GetServerJdk(version='tomcat9')
            if list:
                ret['tomcat9'] = list
                get = liang()
                get.version = '9'
                if not self.Initialization(get.version):
                    ret['tomcat9']['port'] = False
                else:
                    port = self.GetPort()
                    ret['tomcat9']['port'] = port
            else:
                ret['tomcat9'] = False
        else:
            ret['tomcat9'] = False
        data=self.file_name2()
        for i in range(len(data)):
            for i2 in data[i]:
                ret[i2] = data[i][i2]
        return public.returnMsg(True, ret)


    # 取jdk和服务状态
    def GetServerJdk2(self, version,site):
        ret = {}
        jdk_version = self.GetJdk(version)
        server = self.GetServer2(site)
        if jdk_version or server:
            ret['jdk_version'] = jdk_version
            if server:
                ret['status'] = True
            else:
                ret['status'] = False
            return ret
        else:
            return False

    # 取服务状态
    def GetServer2(self, site):
        pid_path = '/www/server/tomcat_site/%s/logs/catalina-daemon.pid' % site
        if os.path.exists(pid_path):
            try:
                pid = int(public.ReadFile(pid_path).strip())
                ret = psutil.Process(pid)
                return True
            except:
                return False
        else:
            return False

    # 取jdk和服务状态
    def GetServerJdk(self, version):
        ret = {}
        jdk_version = self.GetJdk(version)
        server = self.GetServer(version)
        if jdk_version or server:
            ret['jdk_version'] = jdk_version
            if server:
                ret['status'] = True
            else:
                ret['status'] = False
            return ret

        else:
            return False

    # 取JDK 版本
    def GetJdk(self, version):
        path = '/www/server/%s/bin/daemon.sh' % version
        if os.path.exists(path):
            ret = public.ReadFile(path)
            rec = "\nJAVA_HOME=.+"
            if re.search(rec, ret):

                jdk = re.search(rec, ret).group(0).split('/')[-1]
                return jdk
            else:
                return False
        else:
            return False

    # 取服务状态
    def GetServer(self, version):
        pid_path = '/www/server/%s/logs/catalina-daemon.pid' % version
        if os.path.exists(pid_path):
            
            try:
                pid = int(public.ReadFile(pid_path).strip())
                ret = psutil.Process(pid)
                return True
            except:
                return False
        else:
            return False

    def StartTomcat2(self,get):
        domain = get.domain.strip()
        type = get.type.strip()
        if type == 'start':
            pid_path = '/www/server/tomcat_site/%s/logs/catalina-daemon.pid' % domain
            if os.path.exists(pid_path):
                os.remove(pid_path)
            public.ExecShell('/www/server/tomcat_site/%s/bin/daemon.sh start'%domain)
            return public.returnMsg(True, '%s启动成功'%domain)
        elif type == 'stop':
            public.ExecShell('/www/server/tomcat_site/%s/bin/daemon.sh stop'%domain)
            return public.returnMsg(True, '%s关闭成功'%domain)
        elif type == 'reload':
            public.ExecShell('/www/server/tomcat_site/%s/bin/daemon.sh stop' % domain)
            public.ExecShell('/www/server/tomcat_site/%s/bin/daemon.sh start' % domain)
            return public.returnMsg(True, '%s重载成功' % domain)

    # 服务管理
    def StartTomcat(self, get):
        version = get.version.strip()
        type = get.type.strip()
        # 判断服务是否正常
        execStr = '/etc/init.d/%s stop && /etc/init.d/%s start' % (version, version)
        start = '/etc/init.d/%s start' % (version)
        stop = '/etc/init.d/%s stop' % (version)
        if type == 'start':
            ret = self.GetServer(version)
            if not ret:
                pid_path = '/www/server/%s/logs/catalina-daemon.pid' % version
                if os.path.exists(pid_path):
                    os.remove(pid_path)
                public.ExecShell(start)
            return public.returnMsg(True, '%s启动成功' % version)
        elif type == 'stop':
            public.ExecShell(stop)
            if self.GetServer(version):
                public.ExecShell(stop)
            return public.returnMsg(True, '%s关闭成功' % version)
        elif type == 'reload':
            public.ExecShell(execStr)
            ret = self.GetServer(version)
            if not ret:
                public.ExecShell(execStr)
            return public.returnMsg(True, '%s重载成功' % version)
        else:
            return public.returnMsg(False, '类型错误')

        # 获取文件夹
    def file_name3(self):
        data = self.file_return()
        if len(data) == 0: return []
        result = []
        for i in data:
            ret = {}
            site_config = self.__site_path + i + '/conf/server.xml'
            if not os.path.exists(site_config): continue
            version_path = self.__site_path + i + '/version.pl'
            if not os.path.exists(version_path): continue
            if not self.__files: files.files()
            if os.path.exists(site_config):
                tomcat7_file = self.GetFile(site_config)
                if tomcat7_file:
                    ret[i] = tomcat7_file
                    ret[i]['files']=site_config
                else:
                    ret[i] = False
            result.append(ret)
        return result

    # 网站配置文件
    def GetConfig(self, get):
        ret = {}
        if not self.__files: files.files()
        if os.path.exists(self.__tomcat7_server):
            tomcat7_file = self.GetFile(self.__tomcat7_server)
            if tomcat7_file:
                ret['tomcat7'] = tomcat7_file

            else:
                ret['tomcat7'] = False
        else:
            ret['tomcat7'] = False
        if os.path.exists(self.__tomcat8_server):
            tomcat8_file = self.GetFile(self.__tomcat8_server)
            if tomcat8_file:
                ret['tomcat8'] = tomcat8_file

            else:
                ret['tomcat8'] = False
        else:
            ret['tomcat8'] = False
        if os.path.exists(self.__tomcat9_server):
            tomcat9_file = self.GetFile(self.__tomcat9_server)
            if tomcat9_file:
                ret['tomcat9'] = tomcat9_file

            else:
                ret['tomcat9'] = False
        else:
            ret['tomcat9'] = False

        data=self.file_name3()
        for i in range(len(data)):
            for i2 in data[i]:
                ret[i2] = data[i][i2]
        return public.returnMsg(True, ret)

    # 查看文件函数
    def GetFile(self, path):
        if os.path.exists(path):
            get = file()
            get.path = path
            files2 = files.files()
            _file = files2.GetFileBody(get)
            return _file
        else:
            return False

    # 保存文件函数
    def WriteFile(self, get):
        '''
        三个参数：
        data
        path
        encoding
        :param get:
        :return:
        '''
        files2 = files.files()
        _file = files2.SaveFileBody(get)
        return _file


        # 获取文件夹
    def file_name4(self):
        data = self.file_return()
        if len(data) == 0: return []
        result = []
        for i in data:
            ret = {}
            site_config = self.__site_path + i + '/conf/server.xml'
            if not os.path.exists(site_config): continue
            version_path = self.__site_path + i + '/logs/catalina-daemon.out'
            if not os.path.exists(version_path): continue
            if os.path.exists(version_path):
                retc = self.GetLog(version_path)
                if retc:
                    ret[i] = retc
                else:
                    ret[i] = False
            result.append(ret)
        return result


    # 日志
    def GetOpeLogs(self, get):
        ret = {}
        if os.path.exists(self.__tomcat7_log):
            retc = self.GetLog(self.__tomcat7_log)
            if retc:
                ret['tomcat7'] = retc
            else:
                ret['tomcat7'] = False
        else:
            ret['tomcat7'] = False
        if os.path.exists(self.__tomcat8_log):
            retc = self.GetLog(self.__tomcat8_log)
            if retc:
                ret['tomcat8'] = retc
            else:
                ret['tomcat8'] = False
        else:
            ret['tomcat8'] = False
        if os.path.exists(self.__tomcat9_log):
            retc = self.GetLog(self.__tomcat9_log)
            if retc:
                ret['tomcat9'] = retc
            else:
                ret['tomcat9'] = False
        else:
            ret['tomcat9'] = False

        data=self.file_name4()
        for i in range(len(data)):
            for i2 in data[i]:
                ret[i2] = data[i][i2]
        return public.returnMsg(True, ret)

    # Log 取100行操作
    def GetLog(self, path):
        if not os.path.exists(path): return False
        return public.GetNumLines(path, 3000)

    # 更换JDK 版本
    def SetJdk(self, get):
        version = get.version.strip()
        jdk_version = get.jdk_version.strip()
        if version == '7':
            # 判断是否存在
            if os.path.exists(self.__tomcat7_config) and os.path.exists(self.__tomcat7_server) and os.path.exists(
                    self.__tomcat7) and os.path.exists(self.__tomcat7_jkd):
                ret = self.PassJDk(self.__tomcat7_jkd, jdk_version)
                if ret:
                    return public.returnMsg(True, '更换成功')
                else:
                    return public.returnMsg(False, '更换失败')
            else:
                return public.returnMsg(False, "tomcat%s 环境有问题，请检查一下是否正常" % version)
        elif version == '8':
            if os.path.exists(self.__tomcat8_config) and os.path.exists(self.__tomcat8_server) and os.path.exists(
                    self.__tomcat8) and os.path.exists(self.__tomcat8_jkd):
                ret = self.PassJDk(self.__tomcat8_jkd, jdk_version)
                if ret:
                    return public.returnMsg(True, '更换成功')
                else:
                    return public.returnMsg(False, '更换失败')
            else:
                return public.returnMsg(False, "tomcat%s 环境有问题，请检查一下是否正常" % version)
        elif version == '9':
            if os.path.exists(self.__tomcat9_config) and os.path.exists(self.__tomcat9_server) and os.path.exists(
                    self.__tomcat9) and os.path.exists(self.__tomcat9_jkd):
                ret = self.PassJDk(self.__tomcat9_jkd, jdk_version)
                if ret:
                    return public.returnMsg(True, '更换成功')
                else:
                    return public.returnMsg(False, '更换失败')
            else:
                return public.returnMsg(False, "tomcat%s 环境有问题，请检查一下是否正常" % version)

    def PassJDk(self, path, jdk_version):
        if not os.path.exists(jdk_version): return public.returnMsg(False, "此JDK未安装")
        jdk_file = public.ReadFile(path)
        rec = '\nJAVA_HOME=.*'
        if re.search(rec, jdk_file):
            ret = re.sub('\nJAVA_HOME=.*', '\nJAVA_HOME=%s' % jdk_version, jdk_file)
            public.WriteFile(jdk_file, ret)
            return True
        else:
            return False

    # 本地做一个本地hosts
    def SetHosts(self, domain):
        ret = public.ReadFile('/etc/hosts')
        import re
        rec = '%s' % domain
        if re.search(rec, ret):
            pass
        else:
            public.ExecShell('echo "127.0.0.1 ' + domain + '" >> /etc/hosts')

    # 更新domain
    def PullHost(self, domain, domain2):
        ret = public.ReadFile('/etc/hosts')
        import re
        rec = '%s' % domain
        if re.search(rec, ret):
            re.sub(domain, domain2, ret)
            public.WriteFile('/etc/hosts', ret)
        else:
            public.ExecShell('echo "127.0.0.1 ' + domain + '" >> /etc/hosts')

    # 更改端口
    def set_site_port(self, port,version,domain):
        if self.IsOpen(port): return public.returnMsg(False, '端口已经被占用!')
        if not self.Initialization2(version,domain): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.TomcatSetPort(port=port)
        if ret:
            fs = firewalls.firewalls()
            get = mobj()
            get.port = port
            get.ps = 'tomcat外部端口'
            fs.AddAcceptPort(get)
            return public.returnMsg(True, '更改成功!')
        else:
            return public.returnMsg(False, '更改失败')

    # 创建项目
    def AddProject2(self, get):
        # 保存之后重载配置
        domain = get.domain.strip()
        if not self.is_domain(domain.strip()): return public.returnMsg(False, "请输入正确的域名")
        path = get.path.strip()
        version = get.version.strip()
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请。或者服务未安装")
        # 先改他的端口
        ret = self.AddVhost(path=path, domain=domain)
        if ret:
            self.SetHosts(domain)
            # 启动实例
            get.type='reload'
            self.StartTomcat(get)
            return public.returnMsg(True, "添加成功")
        else:
            return public.returnMsg(False, "已经存在")

    #开机自动启
    def start_tomcat(self,get):
        domain=get.domain
        if os.path.exists(self.__site_path+domain+'/bin/daemon.sh'):
            path=self.__site_path+domain+'/bin'
            data='''#!/bin/bash
# chkconfig: 2345 55 25
# description: tomcat Service
### BEGIN INIT INFO
# Provides:          tomcat
# Required-Start:    
# Required-Stop:     
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts tomcat
# Description:       starts the tomcat
### END INIT INFO
path=%s
cd $path
bash daemon.sh $1'''%path
            public.WriteFile('/etc/init.d/'+'tomcat_'+domain,data)
            start_tomcat='/etc/init.d/'+'tomcat_'+domain
            public.ExecShell('chmod +x %s && chkconfig --add %s && chkconfig --level 2345 %s on'%(start_tomcat,'tomcat_'+domain,'tomcat_'+domain))
        return True

    # 创建项目
    def AddProject(self, get):
        # 保存之后重载配置
        type_list=['independent','built']
        if not 'stype' in get:
            get.stype='independent'
        if get.stype=='built':
            domain = get.domain.strip()
            if not self.is_domain(domain.strip()): return public.returnMsg(False, "请输入正确的域名")
            path = get.path.strip()
            version = get.version.strip()
            if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请。或者服务未安装")
            # 先改他的端口
            ret = self.AddVhost(path=path, domain=domain)
            if ret:
                self.SetHosts(domain)
                # 启动实例
                get.type = 'reload'
                self.StartTomcat(get)
                return public.returnMsg(True, "添加成功")
            else:
                return public.returnMsg(False, "已经存在")
        else:
            domain = get.domain.strip()
            if not self.is_domain(domain.strip()): return public.returnMsg(False, "请输入正确的域名")
            path = get.path.strip()
            version = get.version.strip()
            port =get.port.strip()
            start_tomcat=get.start_tomcat.strip()
            if int(port) < 1 or int(port) > 65535: return public.returnMsg(False, '端口范围不合法')
            if check_port(port):return public.returnMsg(False, "端口被占用。请更换其他端口")
            #判断是否存在
            if os.path.exists(self.__site_path+domain):return public.returnMsg(False, "该网站已经存在。如想建立请删除%s"%self.__site_path+domain)
            if not os.path.exists(path): os.makedirs(path)
            # 首先需要先复制好文件过去
            if not  os.path.exists(self.__site_path+domain):
                public.ExecShell('mkdir -p %s'%self.__site_path+domain)
            if version=='tomcat7' or version=='7':
                if not os.path.exists(self.__tomcat7_server): return public.returnMsg(False, "tomcat7 的配置文件不存在。你需要重新安装一下tomcat7")
                public.ExecShell('cp -r /www/server/tomcat7/* %s  && chown -R www:www %s'%(self.__site_path+domain,self.__site_path+domain))
            if version=='tomcat8' or version=='8':
                if not os.path.exists(self.__tomcat8_server): return public.returnMsg(False, "tomcat8 的配置文件不存在。你需要重新安装一下tomcat8")
                public.ExecShell('cp -r /www/server/tomcat8/* %s && chown -R www:www %s'%(self.__site_path+domain,self.__site_path+domain))
            if version=='tomcat9' or version=='9':
                if not os.path.exists(self.__tomcat9_server):return public.returnMsg(False, "tomcat9 的配置文件不存在。你需要重新安装一下tomcat9")
                public.ExecShell('cp -r /www/server/tomcat9/* %s && chown -R www:www %s'%(self.__site_path+domain,self.__site_path+domain))
            #server.xml
            if os.path.exists(self.__site_path+domain+'/conf/server.xml'):
                ret='''<Server port="{}" shutdown="SHUTDOWN">
      <Listener className="org.apache.catalina.startup.VersionLoggerListener" />
      <Listener SSLEngine="on" className="org.apache.catalina.core.AprLifecycleListener" />
      <Listener className="org.apache.catalina.core.JreMemoryLeakPreventionListener" />
      <Listener className="org.apache.catalina.mbeans.GlobalResourcesLifecycleListener" />
      <Listener className="org.apache.catalina.core.ThreadLocalLeakPreventionListener" />
      <GlobalNamingResources>
        <Resource auth="Container" description="User database that can be updated and saved" factory="org.apache.catalina.users.MemoryUserDatabaseFactory" name="UserDatabase" pathname="conf/tomcat-users.xml" type="org.apache.catalina.UserDatabase" />
      </GlobalNamingResources>
      <Service name="Catalina">
        <Connector connectionTimeout="20000" port="8083" protocol="HTTP/1.1" redirectPort="8490" />
        <Engine defaultHost="localhost" name="Catalina">
          <Realm className="org.apache.catalina.realm.LockOutRealm">
            <Realm className="org.apache.catalina.realm.UserDatabaseRealm" resourceName="UserDatabase" />
          </Realm>
          <Host appBase="webapps" autoDeploy="true" name="localhost" unpackWARs="true">
            <Valve className="org.apache.catalina.valves.AccessLogValve" directory="logs" pattern="%h %l %u %t &quot;%r&quot; %s %b" prefix="localhost_access_log" suffix=".txt" />
          </Host>
        </Engine>
      </Service>
    </Server>'''.format(self.generate_random_port())
                public.WriteFile(self.__site_path+domain+'/conf/server.xml',ret)
            else:
                os.system('rm -rf %s'%self.__site_path+domain)
                return public.returnMsg(False, "配置文件不存在请重新安装tomcat后尝试新建网站")

            if not self.Initialization2(get.version,domain): return public.returnMsg(False, "配置文件错误请。或者服务未安装")
            # 先改他的端口
            if not self.set_site_port(port,version,domain)['msg']:return self.set_site_port(port,version,domain)
            ret = self.AddVhost(path=path, domain=domain)
            if ret:
                self.SetHosts(domain)
                # 启动实例
                pid_path = '/www/server/tomcat_site/%s/logs/catalina-daemon.pid' % domain
                if os.path.exists(pid_path):
                    os.remove(pid_path)
                public.ExecShell('sh %s'%self.__site_path+domain+'/bin/daemon.sh start')
                if start_tomcat=='1':
                    self.start_tomcat(get)

                return public.returnMsg(True, "添加成功")
            else:
                return public.returnMsg(False, "已经存在")

    # 随机生成端口
    def generate_random_port(self):
        import random

        port = str(random.randint(5000, 10000))
        while True:
            if not check_port(port): break
            port = str(random.randint(5000, 10000))
        return port

    def RestarTomcat(self, version):
        if version == '7': version = 'tomcat7'
        if version == '8': version = 'tomcat8'
        if version == '9': version = 'tomcat9'
        execStr = '/etc/init.d/%s stop && /etc/init.d/%s start' % (version, version)
        public.ExecShell(execStr)

    def file_return(self):
        for root, dirs, files in os.walk(self.__site_path):
             return dirs


    # 获取文件夹
    def file_name(self):
        data=self.file_return()

        if len(data)==0:return []
        result=[]
        for i in data:
            ret = {}
            site_config=self.__site_path+i+'/conf/server.xml'
            if not os.path.exists(site_config):continue
            version_path=self.__site_path+i+'/version.pl'
            if not os.path.exists(version_path):continue
            ret2 = self.Xml_init(site_config)
            if ret2:
                if len(self.GetVhosts()) >= 1:
                    ret[i] = self.GetVhosts()
                    version = public.ReadFile(version_path)
                    ret[i].append(version.strip())
            else:
                ret[i] = False
            if ret:
                result.append(ret)
        return result

    # 查看项目列表
    def GetSite(self, get):
        ret = {}
        if os.path.exists(self.__tomcat7_server):
            ret2 = self.Xml_init(self.__tomcat7_server)
            if ret2:
                if len(self.GetVhosts())>=1:
                    ret['tomcat7'] = self.GetVhosts()
                    version = self.GetVersion('7')
                    if not version: version == '7.0.76'
                    ret['tomcat7'].append(version)
            else:
                ret['tomcat7'] = False
        if os.path.exists(self.__tomcat8_server):
            ret2 = self.Xml_init(self.__tomcat8_server)
            if ret2:
                if len(self.GetVhosts()) >= 1:
                    ret['tomcat8'] = self.GetVhosts()
                    version = self.GetVersion('8')
                    if not version: version == '8.5.12'
                    ret['tomcat8'].append(version)
            else:
                ret['tomcat8'] = False
        if os.path.exists(self.__tomcat9_server):
            ret2 = self.Xml_init(self.__tomcat9_server)
            if ret2:
                if len(self.GetVhosts()) >= 1:
                    ret['tomcat9'] = self.GetVhosts()
                    version = self.GetVersion('9')
                    if not version: version == '9.0.0'
                    ret['tomcat9'].append(version)
            else:
                ret['tomcat9'] = False
        data=self.file_name()
        for i in range(len(data)):
            for i2 in data[i]:
                ret[i2]=data[i][i2]
        return public.returnMsg(True, ret)

    # 查看版本号
    def GetVersion(self, version):
        tomcat_version = 'tomcat' + version
        path = '/www/server/%s/version.pl' % tomcat_version
        if os.path.exists(path):
            ret = public.ReadFile(path)
            return ret.strip()
        else:
            return False

    def DelProject2(self, get):
        domain = get.domain.strip()
        if not self.is_domain(domain.strip()): return public.returnMsg(False, "请输入正确的域名")
        if os.path.exists('/www/server/tomcat_site/%s/'%domain):
            public.ExecShell('/www/server/tomcat_site/%s/bin/daemon.sh stop'%domain)
            public.ExecShell('rm -rf /www/server/tomcat_site/%s/'% domain)
            if os.path.exists('/etc/init.d/tomcat_'+domain):
                public.ExecShell("rm -rf /etc/init.d/tomcat_%s"%domain)
            if public.M('sites').where("name=?", (domain,)).count():
                data=public.M('sites').where("name=?", (domain,)).field('id,name,ps').select()
                if len(data)>=1:
                    data=data[0]
                    if 'tomcat' in data['ps']:
                        get.webname=domain
                        get.id=data['id']
                        get.path='1'
                        import panelSite
                        s = panelSite.panelSite()
                        s.DeleteSite(get)

            return public.returnMsg(True, '删除成功')
        else:
            return public.returnMsg(False, '网站目录不存在')

    def DelProject(self, get):
        version = get.version.strip()
        domain = get.domain.strip()
        if not self.is_domain(domain.strip()): return public.returnMsg(False, "请输入正确的域名")
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.DelVhost(domain)
        if ret:
            self.RestarTomcat(version)
            return public.returnMsg(True, '删除成功')
        return public.returnMsg(False, '不存在')

    #
    def ReplacePath(self, get):
        version = get.version.strip()
        domain = get.domain.strip()
        path = get.path.strip()
        if not self.is_domain(domain): return public.returnMsg(False, "请输入正确的域名")
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.SetPath(domain, path)
        if ret:
            self.RestarTomcat(version)
            return public.returnMsg(True, '更改成功')
        else:
            return public.returnMsg(True, '更改失败,目录不存在')

    # 添加二级目录
    def AddSitePath(self, get):
        version = get.version.strip()
        domain = get.domain.strip()
        if not self.is_domain(domain.strip()): return public.returnMsg(False, "请输入正确的域名")
        path = get.path.strip()
        name = get.name2.strip()
        if not os.path.exists(path): os.makedirs(path)
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.AddPath(domain, path, name)
        if ret:
            self.RestarTomcat(version)
            return public.returnMsg(True, '添加成功')
        else:
            return public.returnMsg(False, '已经存在')

    def DelSitePath(self, get):
        version = get.version.strip()
        domain = get.domain.strip()
        path = get.path.strip()
        if not self.is_domain(domain.strip()): return public.returnMsg(False, "请输入正确的域名")
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.DelPath(domain, path)
        self.RestarTomcat(version)
        return public.returnMsg(True, '删除成功')

    def Reloadable2(self, get):
        version = get.version.strip()
        domain = get.domain.strip()
        if not self.is_domain(domain.strip()): return public.returnMsg(False, "请输入正确的域名")
        reloadable = int(get.reloadable)
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.SetVhost(domain=domain, reloadable=reloadable)
        self.RestarTomcat(version)
        return public.returnMsg(True, '更改成功!')

    def GetReloadable(self, get):
        if not self.is_domain(get.domain.strip()): return public.returnMsg(False, "请输入正确的域名")
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.GetdomainVhost(get.domain)
        if ret: return public.returnMsg(True, ret)
        return public.returnMsg(False, '获取失败')

    # 初始化xml 进行配置
    def Initialization2(self, version,site):
        if version == '7' or version == 'tomcat7':
            if self.Xml_init(self.__site_path+site+'/conf/server.xml'):
                return True
            else:
                return False
        elif version == '8' or version == 'tomcat8':
            if self.Xml_init(self.__site_path + site + '/conf/server.xml'):
                return True
            else:
                return False
        elif version == '9' or version == 'tomcat9':
            if self.Xml_init(self.__site_path + site + '/conf/server.xml'):
                return True
            else:
                return False
        else:
            return False


    # 初始化xml 进行配置
    def Initialization(self, version):
        if version == '7' or version == 'tomcat7':
            if self.Xml_init(self.__tomcat7_server):
                return True
            else:
                return False
        elif version == '8' or version == 'tomcat8':
            if self.Xml_init(self.__tomcat8_server):
                return True
            else:
                return False
        elif version == '9' or version == 'tomcat9':
            if self.Xml_init(self.__tomcat9_server):
                return True
            else:
                return False
        else:
            return False

    # 映射
    def Mapping(self, get):
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        domain = get.domain.strip()
        version = get.version.strip()
        if not self.ChekcDomain(domain): return public.returnMsg(False, "tomcat中未存在此域名")
        sql = public.M('sites')
        if sql.where("name=?", (domain,)).count(): return public.returnMsg(False, 'SITE_ADD_ERR_EXISTS');
        ret = {"domain": domain, "domainlist": [], "count": 0}
        get.webname = json.dumps(ret)
        get.port = "80"
        get.ftp = 'false'
        get.sql = 'false'
        get.version = '00'
        get.ps = 'tomcat[' + version + ']的映射站点'
        get.path = public.M('config').where("id=?", ('1',)).getField('sites_path') + '/' + domain
        result = self.create_site(get)
        if 'status' in result: return result
        import panelSite
        s = panelSite.panelSite()
        get.sitename = domain
        get.proxyname = 'tomcat'
        get.proxysite = 'http://' + domain + ':' + str(self.GetPort())
        get.todomain = domain
        get.proxydir = '/'
        get.type = 1
        get.cache = 0
        get.cachetime = 1
        get.advanced = 0
        get.subfilter = "[{\"sub1\":\"\",\"sub2\":\"\"},{\"sub1\":\"\",\"sub2\":\"\"},{\"sub1\":\"\",\"sub2\":\"\"}]"
        result = s.CreateProxy(get)
        if result['status']:
            public.WriteLog('tomcat' + str(get.version), '添加映射[' + str(domain) + ']' + '成功')
        else:
            public.WriteLog('tomcat' + str(get.version), '添加映射[' + str(domain) + ']' + '失败')
        os.system('chown www:www %s' % public.M('config').where("id=?", ('1',)).getField('sites_path') + '/' + domain)
        return public.returnMsg(True, '添加成功!')

    # 映射
    # 首先检查服务是否启动
    # 然后当前网站的端口
    # 然后做映射

    def Mapping2(self, get):
        domain = get.domain.strip()
        if not os.path.exists(self.__site_path+domain+'/conf/server.xml'):
            return public.returnMsg(False, "配置文件错误请检查配置文件")
        #检查服务是否启动
        if not self.GetServer2(site=domain):return public.returnMsg(False, "当前映射的网站的服务未启动,请在服务中启动该网站")
        if not self.Initialization2('7',domain): return public.returnMsg(False, "配置文件错误请检查配置文件")
        if not self.ChekcDomain(domain): return public.returnMsg(False, "tomcat中未存在此域名")
        #取到端口
        sql = public.M('sites')
        if sql.where("name=?", (domain,)).count(): return public.returnMsg(False, 'SITE_ADD_ERR_EXISTS');
        ret = {"domain": domain, "domainlist": [], "count": 0}
        get.webname = json.dumps(ret)
        get.port = "80"
        get.ftp = 'false'
        get.sql = 'false'
        get.version = '00'
        get.ps = 'tomcat[' + domain + ']的映射站点'
        get.path = public.M('config').where("id=?", ('1',)).getField('sites_path') + '/' + domain
        result = self.create_site(get)
        if 'status' in result: return result
        import panelSite
        s = panelSite.panelSite()
        get.sitename = domain
        get.proxyname = 'tomcat'
        get.proxysite = 'http://' + domain + ':' + str(self.GetPort())
        get.todomain = domain
        get.proxydir = '/'
        get.type = 1
        get.cache = 0
        get.cachetime = 1
        get.advanced = 0
        get.subfilter = "[{\"sub1\":\"\",\"sub2\":\"\"},{\"sub1\":\"\",\"sub2\":\"\"},{\"sub1\":\"\",\"sub2\":\"\"}]"
        result = s.CreateProxy(get)
        if result['status']:
            public.WriteLog('java项目管理器', '添加映射[' + str(domain) + ']' + '成功')
        else:
            public.WriteLog('java项目管理器', '添加映射[' + str(domain) + ']' + '失败')
        os.system('chown www:www %s' % public.M('config').where("id=?", ('1',)).getField('sites_path') + '/' + domain)
        return public.returnMsg(True, '添加成功!')


    # 作为标识ID
    def GetRandomString(self, length):
        from random import Random
        strings = ''
        chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
        chrlen = len(chars) - 1
        random = Random()
        for i in range(length):
            strings += chars[random.randint(0, chrlen)]
        return strings

    def create_site(self, get):
        import panelSite
        s = panelSite.panelSite()
        result = s.AddSite(get)
        if 'status' in result: return result;
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

    # 更改域名
    def RenameDomain(self, get):
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        domain = get.domain.strip()
        appbase = get.appbase.strip()
        domain2 = get.domain2.strip()
        if not self.is_domain(domain2.strip()): return public.returnMsg(False, "请输入正确的域名")
        mapping = get.mapping.strip()
        import time
        # 解决时效问题
        time.sleep(0.1)
        domain_file = self.GetServerDomain(domain)

        if len(domain_file) >= 1:
            for i in domain_file:
                # 主域名
                if 'domain_main' in i:
                    # if i.has_key('domain_main'):
                    if i['domain_main'] == domain and i['appBase'] == appbase:
                        sql = public.M('sites')
                        self.GetDomainPath2(domain, domain2)
                        self.RestarTomcat(get.version)
                        if mapping == '1':
                            if sql.where("name=?", (domain,)).count(): return public.returnMsg(False,
                                                                                               '域名已经映射或者已经存在,请删除之后再更换')
                            get.domain = domain2
                            self.PullHost(domain, domain2)
                            ret = self.Mapping(get)
                            return ret
                        else:
                            self.PullHost(domain, domain2)
                            return public.returnMsg(True, '更换成功!')
                else:
                    # 其他域名
                    if 'domain' in i:
                        # if i.has_key('domain'):
                        if i['domain'] == domain and i['appBase'] == appbase:
                            sql = public.M('sites')
                            self.GetDomainPath2(domain, domain2)
                            self.RestarTomcat(get.version)
                            if mapping == '1':
                                if sql.where("name=?", (domain,)).count(): return public.returnMsg(False,
                                                                                                   '域名已经映射或者已经存在,请删除之后再更换')

                                get.domain = domain2
                                ret = self.Mapping(get)
                                self.PullHost(domain, domain2)
                                return ret
                            else:
                                self.PullHost(domain, domain2)
                                return public.returnMsg(True, '更换成功!')
        return public.returnMsg(False, '获取域名列表失败!')

    def GetProxy(self, get):
        import panelSite
        try:
            s = panelSite.panelSite()
            ret = s.GetProxyList(get)
            # return str(type(ret))
            if type(ret) == list:
                return public.returnMsg(True, 'ok')
            else:
                return public.returnMsg(False, 'false')
        except:
            return public.returnMsg(False, 'false')

    # 更改端口
    def SetTomcatPort2(self, get):
        port = get.port.strip()
        site = get.domain.strip()
        if 'check' not in get:
            get.check=False
        else:
            if get.check=='0':
                get.check=False
        if self.IsOpen(port): return public.returnMsg(False, '端口已经被占用!')
        if not self.Initialization2(version='7',site=site): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.TomcatSetPort(port=port)
        if ret:
            # 判断是否需要修改映射的
            if get.check:
                if public.M('sites').where("name=?", (site,)).count():
                    data=public.M('sites').where("name=?", (site,)).field('id,name,ps').select()
                    if len(data)>=1:
                        data=data[0]
                        if 'tomcat' in data['ps']:
                            get.webname=site
                            get.id=data['id']
                            import panelSite
                            s = panelSite.panelSite()
                            s.DeleteSite(get)
                            #删除之后重新建立
                            self.Mapping2(get)
            get.type ='reload'
            self.StartTomcat2(get)
            fs = firewalls.firewalls()
            get = mobj()
            get.port = port
            get.ps = 'tomcat外部端口'
            fs.AddAcceptPort(get)
            return public.returnMsg(True, '更改成功!')
        else:
            public.returnMsg(False, '更改失败')
    # 更改端口
    def SetTomcatPort(self, get):
        port = get.port.strip()
        version = get.version.strip()
        if self.IsOpen(port): return public.returnMsg(False, '端口已经被占用!')
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.TomcatSetPort(port=port)
        if ret:
            self.RestarTomcat(get.version)
            fs = firewalls.firewalls()
            get = mobj()
            get.port = port
            get.ps = 'tomcat外部端口'
            fs.AddAcceptPort(get)
            return public.returnMsg(True, '更改成功!')
        else:
            public.returnMsg(False, '更改失败')

    # 查看端口
    def GetTomcatPort(self, get):
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.GetPort()
        return public.returnMsg(True, ret)

    # 查看二级目录
    def GeterPath(self, get):
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.GetDomain(get.domain)
        if not ret: return public.returnMsg(True, ret)
        return public.returnMsg(True, ret)

    ##################################XML 操作部分#########################
    # 获取虚拟主机列表
    def GetVhosts(self):
        Hosts = self.__ENGINE.getchildren()
        data = []
        for host in Hosts:
            if host.tag != 'Host': continue;
            tmp = host.attrib
            if 'appBase' in tmp:
                if tmp['appBase']=='webapps':continue
            ch = host.getchildren()
            tmp['item'] = {}
            for c in ch:
                tmp['item'][c.tag] = c.attrib
            data.append(tmp)
        return data

    # 添加虚拟主机
    def AddVhost(self, path, domain):
        if not os.path.exists(path): os.makedirs(path)
        if self.GetVhost(domain): return 111
        attr = {"autoDeploy": "true", "name": domain, "unpackWARs": "true",
                "xmlNamespaceAware": "false", "xmlValidation": "false"}
        Host = Element("Host", attr)
        attr = {"docBase": path, "path": "", "reloadable": "true", "crossContext": "true", }
        Context = Element("Context", attr)
        Host.append(Context)
        self.__ENGINE.append(Host)
        self.Save()

        return True

    # 删除虚拟主机
    def DelVhost(self, domain):
        if domain == 'localhost': return False
        host = self.GetVhost(domain)
        if not host: return False
        self.__ENGINE.remove(host)
        self.Save()
        return True

    # 获取指定虚拟主机
    def GetVhost(self, domain):
        Hosts = self.__ENGINE.getchildren()
        for host in Hosts:
            if host.tag != 'Host': continue;
            if host.attrib['name'] == domain:
                return host
        return None

    # 修改根目录
    def SetPath(self, domain, path):
        if not os.path.exists(path): public.ExecShell('mkdir -p %s' % path)
        host = self.GetVhost(domain)
        if not host: return False
        # if host.attrib['appBase']=='webapps':return False
        # host.attrib['appBase'] = path
        host.getchildren()[0].attrib['docBase'] = path
        self.Save()
        return True

    # 添加二级目录
    def AddPath(self, domain, name, path):
        # if self.ChekcDomain(domain):return False
        if self.CheckPath(domain, name): return False
        if not os.path.exists(path): os.makedirs(path)
        ret = self.GetVhost(domain)
        attr = {"docBase": path, "path": name, "reloadable": "true", }
        Context = Element("Context", attr)
        ret.append(Context)
        self.Save()
        return True

    # 判断是否存在这个二级目录
    def CheckPath(self, domain, path):
        ret = self.GetVhost(domain)
        for i in ret:
            if 'path' in i.attrib:
                # if i.attrib.has_key('path'):
                if i.attrib['path'] == path:
                    return True
        else:
            return False

    # 删除二级目录
    def DelPath(self, domain, path):
        ret = self.GetVhost(domain)
        if not ret: return False
        for i in ret:
            if 'path' in i.attrib:
                # if i.attrib.has_key('path'):
                if i.attrib['path'] == path:
                    ret.remove(i)
        self.Save()
        return True

    # 获取当前配置文件的端口

    # 修改虚拟主机属性
    def SetVhost2(self, domain, key, value):
        host = self.GetVhost(domain)
        if not host: return False
        host.attrib[key] = value
        self.Save()
        return True

    # 修改虚拟主机属性
    def SetVhost(self, domain, reloadable):
        Hosts = self.GetVhost(domain)
        if not Hosts: return False
        if reloadable:
            for i in Hosts:
                if 'reloadable' in i.attrib:
                    # if i.attrib.has_key('reloadable'):
                    i.attrib['reloadable'] = "true"
        else:
            for i in Hosts:
                if 'reloadable' in i.attrib:
                    # if i.attrib.has_key('reloadable'):
                    i.attrib['reloadable'] = "false"
        self.Save()
        return True

    # 查看 reloadable 信息
    def GetdomainVhost(self, domain):
        Hosts = self.GetVhost(domain)
        if not Hosts: return False

        for i in Hosts:
            if 'reloadable' in i.attrib:
                # if i.attrib.has_key('reloadable'):
                if i.attrib['reloadable'] == "true":
                    return True
                else:
                    return False
        else:
            return False

    # 获取端口号
    def GetPort(self):
        for i in self.__CONNECTROR:
            if 'protocol' in i.attrib and 'port' in i.attrib:
                # if i.attrib.has_key('protocol') and i.attrib.has_key('port'):
                if i.attrib['protocol'] == 'HTTP/1.1':
                    return int(i.attrib['port'])
        else:
            return int(8080)

    # 判断域名是否存在
    def ChekcDomain(self, domain):
        ret = self.GetVhosts()
        for i in ret:
            if 'name' in i:
                if i['name'] == domain:
                    return True
        else:
            return False

    def is_domain(self, domain):
        import re
        domain_regex = re.compile(
            r'(?:[A-Z0-9_](?:[A-Z0-9-_]{0,247}[A-Z0-9])?\.)+(?:[A-Z]{2,6}|[A-Z0-9-]{2,}(?<!-))\Z',
            re.IGNORECASE)
        return True if domain_regex.match(domain) else False

    # 整理配置文件格式
    def format(self, em, level=0):
        i = "\n" + level * "  "
        if len(em):
            if not em.text or not em.text.strip():
                em.text = i + "  "
            for e in em:
                self.format(e, level + 1)
            if not e.tail or not e.tail.strip():
                e.tail = i
        if level and (not em.tail or not em.tail.strip()):
            em.tail = i

    # 给根节点加项目地址路径
    def AddLocalHost(self, name, path, domain='localhost'):
        ret = self.GetVhost(domain)
        if not ret: return False
        for i in ret:
            if 'path' in i.attrib:
                # if  i.attrib.has_key('path'):
                if i.attrib['path'] == name:
                    return False
        attr = {"docBase": path, "path": name, "reloadable": "true", }
        Context = Element("Context", attr)
        ret.append(Context)
        self.Save()
        return True

    # 取主域名
    def GetMainDomain(self):
        ret = self.GetVhosts()
        for i in ret:
            if 'Valve' in i['item']:
                # if i['item'].has_key('Valve'):
                return str(i['name'])
        else:
            return str('localhost')

    # 获取域名的appBase 信息
    def GetDomainPath(self, doamin):
        ret = self.GetVhosts()
        for i in ret:
            if i['name'] == doamin:
                return str(i['appBase'])
        return False

        # 获取域名和路径信息

    def GetServerDomain2(self, get):
        ret = []
        ret2 = self.GetVhosts()
        host = self.GetVhost(get.domain)
        docbase = host.getchildren()[0].attrib['docBase']
        for i in ret2:
            rec = {}
            if 'Valve' in i['item']:
                # if i['item'].has_key('Valve'):
                rec['domain_main'] = i['name']

                rec['appBase'] = docbase
                ret.append(rec)
            else:
                rec['appBase'] = docbase
                rec['domain'] = i['name']
                ret.append(rec)
        return ret

    # 获取域名和路径信息
    def GetServerDomain(self, doamin):
        ret = []
        host = self.GetVhost(doamin)
        docbase = host.getchildren()[0].attrib['docBase']
        ret2 = self.GetVhosts()
        for i in ret2:
            rec = {}
            if 'Valve' in i['item']:
                # if i['item'].has_key('Valve'):
                rec['domain_main'] = i['name']
                rec['appBase'] = docbase
                ret.append(rec)
            else:
                rec['appBase'] = docbase
                rec['domain'] = i['name']
                ret.append(rec)
        return ret

    # 更新域名信息
    def GetDomainPath2(self, doamin, doamin2):
        self.__TREE.parse(self.__CONF_FILE)
        self.__ENGINE = self.__TREE.findall('Service/Engine')[0]
        Hosts = self.__ENGINE.getchildren()
        for host in Hosts:
            if host.tag != 'Host': continue;
            if host.attrib['name'] == doamin:
                host.attrib['name'] = doamin2
        self.Save()
        return True

    # 判断端口是否被占用
    def IsOpen(self, port):
        ip = '0.0.0.0'
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((ip, int(port)))
            s.shutdown(2)
            return True
        except:
            return False

    # 更换端口
    def TomcatSetPort(self, port):
        for i in self.__CONNECTROR:
            if 'protocol' in i.attrib and 'port' in i.attrib:
                if i.attrib['protocol'] == 'HTTP/1.1':
                    i.attrib['port'] = port
        self.Save()
        if self.GetPort() == int(port):
            return True
        else:
            return False

    # 查看二级目录
    def GetDomain(self, domain):
        ret = self.GetVhost(domain)
        resulet = []
        if not ret: return False
        try:
            for i in ret:
                if i.attrib['path']:
                    resulet.append(i.attrib)
        except:
            return resulet
        return resulet

    # 保存配置
    def Save(self):
        self.format(self.__ROOT)
        self.__TREE.write(self.__CONF_FILE, 'utf-8')


if __name__ == '__main__':
    print(111)
    tom = tomcat2_main()
    tom.Xml_init('/www/server/tomcat9/conf/server.xml')
    print(tom.AddVhost(domain='www.aa2222.com', path='/tomcat/aa'))
