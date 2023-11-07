# coding: utf-8
# -----------------------------
# 宝塔Linux面板 tomcat项目管理
# Author: HUB

import sys, os, time, re, psutil, json
from xml.etree.ElementTree import ElementTree, Element

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
sys.path.append("class/")
import public, files, firewalls
from public_check import public_check

class mobj:
    port = ps = ''


class tomcat_manager(object):
    __tomcat7_server = '/www/server/tomcat7/conf/server.xml'
    __tomcat8_server = '/www/server/tomcat8/conf/server.xml'
    __tomcat9_server = '/www/server/tomcat9/conf/server.xml'
    __site_path = '/www/server/web_site/'

    __TREE = None
    __ENGINE = None
    __ROOT = None
    __CONF_FILE = ''
    __CONNECTROR = ''

    def __init__(self):
        if not os.path.exists(self.__site_path):
            os.system('mkdir -p {}'.format(self.__site_path))
	
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
    # 开启tomcat端口
    def release_tomcat_port(self):
        import firewalls
        fs = firewalls.firewalls()
        get = mobj()
        for i in range(8080, 8083):
            get.port = str(i)
            get.ps = 'tomcat外部端口'
            fs.AddAcceptPort(get)
        return True

    # 安装tomcat
    def install_tomcat(self, get):
        self.release_tomcat_port()
        webserver = get.webserver.strip().lower()
        s_type = get.type.strip() if 'type' in get else 'install'
        if webserver == 'tomcat7':
            version = "7"
        elif webserver == 'tomcat8':
            version = "8"
        elif webserver == 'tomcat9':
            version = "9"
        else:
            return public.returnMsg(False, "不支持的tomcat版本！")
        if s_type == 'install':
            if os.path.exists('/www/server/tomcat' + version + '/conf/server.xml'):
                return public.returnMsg(True, 'tomcat{}已安装'.format(version))
            shell_str = "cd /tmp && wget -O newtomcat.sh %s/install/src/webserver/shell/newtomcat.sh && bash -x newtomcat.sh install %s >>/tmp/web.json" % (public.get_url(), version)
            print('安装tomcat命令：', shell_str)
            public.ExecShell(shell_str)
            return public.returnMsg(True, "安装tomcat{}成功".format(version))
        elif s_type == 'uninstall':
            if not os.path.exists('/www/server/tomcat' + version):
                return public.returnMsg(True, 'tomcat{}未安装'.format(version))
            shell_str = "cd /tmp && wget -O newtomcat.sh %s/install/src/webserver/shell/newtomcat.sh && bash -x newtomcat.sh uninstall %s >>/tmp/web.json" % (public.get_url(), version)
            print('卸载tomcat命令：', shell_str)
            public.ExecShell(shell_str)
            return public.returnMsg(True, "卸载tomcat{}成功".format(version))

    # 创建tomcat项目
    def add_tomcat_project(self, get):
        if get.stype not in ['built', 'independent']:
            return public.returnMsg(False, '不支持的项目类型')
        domain = get.domain.strip()
        if not public_check().is_domain(domain): return public.returnMsg(False, "请输入正确的域名")
        path = get.path.strip()
        # 安装tomcat
        self.install_tomcat(get)
        webserver = get.webserver.strip()
        if get.stype == 'built':
            if not self.Initialization(webserver): return public.returnMsg(False, "配置文件错误或者服务未安装")
            # 先改端口
            ret = self.AddVhost(path=path, domain=domain)
            if ret:
                public_check().SetHosts(domain)
                # 启动实例
                get.type = 'reload'
                self.StartTomcat(get)
                return public.returnMsg(True, "添加成功")
            else:
                return public.returnMsg(False, "已经存在")
        else:
            port = get.port.strip()
            start_tomcat = get.auto_start.strip()
            if int(port) < 1 or int(port) > 65535: return public.returnMsg(False, '端口范围不合法')
            if public_check().check_port(port): return public.returnMsg(False, "端口被占用, 请更换其他端口")
            # 判断是否存在
            if os.path.exists(self.__site_path + domain): return public.returnMsg(False, "该网站已经存在。如想建立请删除%s" % self.__site_path + domain)
            if not os.path.exists(path): os.makedirs(path)
            # 首先需要先复制好文件过去
            if not os.path.exists(self.__site_path + domain):
                public.ExecShell('mkdir -p %s' % self.__site_path + domain)
            if webserver == 'tomcat7' or webserver == '7':
                if not os.path.exists(self.__tomcat7_server): return public.returnMsg(False, "tomcat7的配置文件不存在，请重新安装tomcat7")
                public.ExecShell('cp -r /www/server/tomcat7/* %s  && chown -R www:www %s' % (self.__site_path + domain, self.__site_path + domain))
            if webserver == 'tomcat8' or webserver == '8':
                if not os.path.exists(self.__tomcat8_server): return public.returnMsg(False, "tomcat8的配置文件不存在，请重新安装tomcat8")
                public.ExecShell('cp -r /www/server/tomcat8/* %s && chown -R www:www %s' % (self.__site_path + domain, self.__site_path + domain))
            if webserver == 'tomcat9' or webserver == '9':
                if not os.path.exists(self.__tomcat9_server): return public.returnMsg(False, "tomcat9的配置文件不存在，请重新安装tomcat9")
                public.ExecShell('cp -r /www/server/tomcat9/* %s && chown -R www:www %s' % (self.__site_path + domain, self.__site_path + domain))
            # server.xml
            if os.path.exists(self.__site_path + domain + '/conf/server.xml'):
                ret = '''<Server port="{}" shutdown="SHUTDOWN">
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
    </Server>'''.format(public_check().generate_random_port())
                public.WriteFile(self.__site_path + domain + '/conf/server.xml', ret)
            else:
                os.system('rm -rf %s' % self.__site_path + domain)
                return public.returnMsg(False, "配置文件不存在请重新安装tomcat后尝试新建网站")

            if not self.Initialization2(get.webserver, domain): return public.returnMsg(False, "配置文件错误或者服务未安装")
            # 先改他的端口
            ret = self.set_site_port(port, webserver, domain)
            if not ret['status']: return ret
            ret = self.AddVhost(path=path, domain=domain)
            if ret:
                public_check().SetHosts(domain)
                # 启动实例
                pid_path = '/www/server/web_site/%s/logs/catalina-daemon.pid' % domain
                if os.path.exists(pid_path):
                    os.remove(pid_path)
                public.ExecShell('sh %s' % self.__site_path + domain + '/bin/daemon.sh start')
                if start_tomcat == '1':
                    self.auto_start_tomcat(get)
                return public.returnMsg(True, "添加成功")
            else:
                return public.returnMsg(False, "已经存在")

    # 删除tomcat项目
    def delete_tomcat_project(self, project_info):
        if project_info['stype'] not in ['built', 'independent']:
            return public.returnMsg(False, '不支持的项目类型')
        if project_info['stype'] == 'built':
            webserver = project_info['webserver']
            domain = project_info['domain']
            if not public_check().is_domain(domain): return public.returnMsg(False, "请输入正确的域名")
            if not self.Initialization(webserver): return public.returnMsg(False, "配置文件错误请检查配置文件")
            ret = self.DelVhost(domain)
            if ret:
                self.RestarTomcat(webserver)
                # self.delete_mapping_site(domain)
                return public.returnMsg(True, '删除成功')
            return public.returnMsg(False, '不存在')
        else:
            domain = project_info['domain']
            if not public_check().is_domain(domain): return public.returnMsg(False, "请输入正确的域名")
            if os.path.exists('/www/server/web_site/%s/' % domain):
                public.ExecShell('/www/server/web_site/%s/bin/daemon.sh stop' % domain)
                public.ExecShell('rm -rf /www/server/web_site/%s/' % domain)
                if os.path.exists('/etc/init.d/tomcat_' + domain):
                    public.ExecShell("rm -rf /etc/init.d/tomcat_%s" % domain)
                self.delete_mapping_site(domain)
                return public.returnMsg(True, '删除成功')
            else:
                return public.returnMsg(False, '网站目录不存在')

    # 删除映射网站
    def delete_mapping_site(self, domain):
        if public.M('sites').where("name=?", domain).count():
            data = public.M('sites').where("name=?", domain).field('id,name,ps').find()
            if 'tomcat' in data['ps']:
                get = public.dict_obj()
                get.webname = domain
                get.id = data['id']
                get.path = '1'
                import panelSite
                s = panelSite.panelSite()
                s.DeleteSite(get)

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

    # 初始化xml进行配置
    def Initialization2(self, version, site):
        if version == '7' or version == 'tomcat7':
            if self.Xml_init(self.__site_path + site + '/conf/server.xml'):
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

    # 初始化xml进行配置
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

    # 获取端口号
    def GetPort(self):
        for i in self.__CONNECTROR:
            if 'protocol' in i.attrib and 'port' in i.attrib:
                if i.attrib['protocol'] == 'HTTP/1.1':
                    return int(i.attrib['port'])
        else:
            return int(8080)

    # 更改端口
    def set_site_port(self, port, version, domain):
        if public_check().IsOpen(port): return public.returnMsg(False, '端口已经被占用!')
        if not self.Initialization2(version, domain): return public.returnMsg(False, "配置文件错误请检查配置文件")
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

    # 开机自启
    def auto_start_tomcat(self, get):
        domain = get.domain
        if os.path.exists(self.__site_path + domain + '/bin/daemon.sh'):
            path = self.__site_path + domain + '/bin'
            data = '''#!/bin/bash
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
bash daemon.sh $1''' % path
            public.WriteFile('/etc/init.d/' + 'tomcat_' + domain, data)
            start_tomcat = '/etc/init.d/' + 'tomcat_' + domain
            public.ExecShell('chmod +x %s && chkconfig --add %s && chkconfig --level 2345 %s on' % (start_tomcat, 'tomcat_' + domain, 'tomcat_' + domain))
        return True

    # 获取虚拟主机列表
    def GetVhosts(self):
        Hosts = self.__ENGINE.getchildren()
        data = []
        for host in Hosts:
            if host.tag != 'Host': continue;
            tmp = host.attrib
            if 'appBase' in tmp:
                if tmp['appBase'] == 'webapps': continue
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

    # 重启Tomcat
    def RestarTomcat(self, version):
        if version == '7': version = 'tomcat7'
        if version == '8': version = 'tomcat8'
        if version == '9': version = 'tomcat9'
        execStr = '/etc/init.d/%s stop && /etc/init.d/%s start' % (version, version)
        public.ExecShell(execStr)

    # Tomcat服务管理
    def StartTomcat(self, get):
        version = get.webserver.strip().lower()
        s_type = get.type.strip()
        # 判断服务是否正常
        execStr = '/etc/init.d/%s stop && /etc/init.d/%s start' % (version, version)
        start = '/etc/init.d/%s start' % version
        stop = '/etc/init.d/%s stop' % version
        if s_type == 'start':
            ret = self.GetServer(version)
            if not ret:
                pid_path = '/www/server/%s/logs/catalina-daemon.pid' % version
                if os.path.exists(pid_path):
                    os.remove(pid_path)
                public.ExecShell(start)
            return public.returnMsg(True, '%s启动成功' % version)
        elif s_type == 'stop':
            public.ExecShell(stop)
            if self.GetServer(version):
                public.ExecShell(stop)
            return public.returnMsg(True, '%s关闭成功' % version)
        elif s_type == 'reload':
            public.ExecShell(execStr)
            ret = self.GetServer(version)
            if not ret:
                public.ExecShell(execStr)
            return public.returnMsg(True, '%s重载成功' % version)
        else:
            return public.returnMsg(False, '类型错误')

    # 独立的网站服务管理
    def StartTomcat2(self, get):
        domain = get.domain.strip()
        type = get.type.strip()
        if type == 'start':
            pid_path = '/www/server/web_site/%s/logs/catalina-daemon.pid' % domain
            if os.path.exists(pid_path):
                os.remove(pid_path)
            public.ExecShell('/www/server/web_site/%s/bin/daemon.sh start' % domain)
            return public.returnMsg(True, '%s启动成功' % domain)
        elif type == 'stop':
            public.ExecShell('/www/server/web_site/%s/bin/daemon.sh stop' % domain)
            return public.returnMsg(True, '%s关闭成功' % domain)
        elif type == 'reload':
            public.ExecShell('/www/server/web_site/%s/bin/daemon.sh stop' % domain)
            public.ExecShell('/www/server/web_site/%s/bin/daemon.sh start' % domain)
            return public.returnMsg(True, '%s重载成功' % domain)

    # 取服务状态
    def GetServer(self, version):
        pid_path = '/www/server/%s/logs/catalina-daemon.pid' % version
        if os.path.exists(pid_path):
            pid = int(public.ReadFile(pid_path).strip())
            try:
                ret = psutil.Process(pid)
                return True
            except:
                return False
        else:
            return False

    # 取服务状态
    def GetServer2(self, site):
        pid_path = '/www/server/web_site/%s/logs/catalina-daemon.pid' % site
        if os.path.exists(pid_path):
            try:
                pid = int(public.ReadFile(pid_path).strip())
                ret = psutil.Process(pid)
                return True
            except:
                return False
        else:
            return False

    # 保存配置
    def Save(self):
        self.format(self.__ROOT)
        self.__TREE.write(self.__CONF_FILE, 'utf-8')

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

    # 获取当前运行的tomcat服务
    def get_tomcat_services(self):
        ret = []
        if os.path.exists(self.__tomcat7_server):
            tmp = {'service_name': 'tomcat7', 'webserver': 'tomcat7'}
            if not self.Initialization('tomcat7'):
                tmp['port'] = False
            else:
                tmp['port'] = self.GetPort()
            tmp['status'] = self.GetServer('tomcat7')
            tmp['conf'] = public.readFile(self.__tomcat7_server)
            tmp['jdk'] = self.get_jdk('tomcat7')
            tmp['log'] = public.GetNumLines('/www/server/tomcat7/logs/catalina-daemon.out', 3000)
            tmp['stype'] = 'built'
            ret.append(tmp)
        if os.path.exists(self.__tomcat8_server):
            tmp = {'service_name': 'tomcat8', 'webserver': 'tomcat8'}
            if not self.Initialization('tomcat8'):
                tmp['port'] = False
            else:
                tmp['port'] = self.GetPort()
            tmp['status'] = self.GetServer('tomcat8')
            tmp['conf'] = public.readFile(self.__tomcat8_server)
            tmp['jdk'] = self.get_jdk('tomcat8')
            tmp['log'] = public.GetNumLines('/www/server/tomcat8/logs/catalina-daemon.out', 3000)
            tmp['stype'] = 'built'
            ret.append(tmp)
        if os.path.exists(self.__tomcat9_server):
            tmp = {'service_name': 'tomcat9', 'webserver': 'tomcat9'}
            if not self.Initialization('tomcat9'):
                tmp['port'] = False
            else:
                tmp['port'] = self.GetPort()
            tmp['status'] = self.GetServer('tomcat9')
            tmp['conf'] = public.readFile(self.__tomcat9_server)
            tmp['jdk'] = self.get_jdk('tomcat9')
            tmp['stype'] = 'built'
            tmp['log'] = public.GetNumLines('/www/server/tomcat9/logs/catalina-daemon.out', 3000)
            ret.append(tmp)
        # 获取独立项目列表
        independent_project = public.M('java_project').where('stype=?', 'independent').select()
        for item in independent_project:
            if 'tomcat' not in item['webserver']: continue
            tmp = {'service_name': item['domain'], 'webserver': item['webserver'], 'port': item['port'], 'status': self.GetServer2(item['domain'])}
            tmp['conf'] = public.readFile(self.__site_path + item['domain'] + '/conf/server.xml')
            tmp['jdk'] = self.get_jdk(item['domain'], is_independent=True)
            tmp['log'] = public.GetNumLines('/www/server/web_site/{}/logs/catalina-daemon.out'.format(item['domain']), 3000)
            tmp['stype'] = 'independent'
            ret.append(tmp)

        return ret

    # 取JDK版本
    def get_jdk(self, version, is_independent=False):
        path = '/www/server/%s/bin/daemon.sh' % version
        if is_independent:
            path = '/www/server/web_site/%s/bin/daemon.sh' % version
        if os.path.exists(path):
            ret = public.ReadFile(path)
            rec = "\nJAVA_HOME=.+"
            if re.search(rec, ret):
                jdk = re.search(rec, ret).group(0).split('/')[-1]
                return jdk
            else:
                return ''
        else:
            return ''

    # 更改独立服务端口
    def SetTomcatPort2(self, get):
        port = get.port.strip()
        site = get.domain.strip()
        webserver = get.webserver.strip()
        if 'check' not in get:
            get.check = False
        else:
            if get.check == '0':
                get.check = False
        if public_check().IsOpen(port): return public.returnMsg(False, '端口已经被占用!')
        if not self.Initialization2(version=webserver, site=site): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.TomcatSetPort(port=port)
        if ret:
            # 判断是否需要修改映射的
            if get.check:
                if public.M('sites').where("name=?", site).count():
                    data = public.M('sites').where("name=?", site).field('id,name,ps').select()
                    if len(data) >= 1:
                        data = data[0]
                        if 'tomcat' in data['ps']:
                            get.webname = site
                            get.id = data['id']
                            import panelSite
                            s = panelSite.panelSite()
                            s.DeleteSite(get)
                            # 删除之后重新建立
                            self.Mapping2(get)
            get.type = 'reload'
            self.StartTomcat2(get)
            fs = firewalls.firewalls()
            get = mobj()
            get.port = port
            get.ps = 'tomcat外部端口'
            fs.AddAcceptPort(get)
            public.M('java_project').where('domain=?', site).setField('port', port)
            return public.returnMsg(True, '更改成功!')
        else:
            public.returnMsg(False, '更改失败')

    # 更改端口
    def SetTomcatPort(self, get):
        port = get.port.strip()
        webserver = get.webserver.strip()
        if self.IsOpen(port): return public.returnMsg(False, '端口已经被占用!')
        if not self.Initialization(webserver): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.TomcatSetPort(port=port)
        if ret:
            self.RestarTomcat(webserver)
            fs = firewalls.firewalls()
            get = mobj()
            get.port = port
            get.ps = 'tomcat外部端口'
            fs.AddAcceptPort(get)
            return public.returnMsg(True, '更改成功!')
        else:
            public.returnMsg(False, '更改失败')

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
        result = public_check().create_site(get)
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
        # 检查服务是否启动
        if not self.GetServer2(site=domain):return public.returnMsg(False, "当前映射的网站的服务未启动,请在服务中启动该网站")
        if not self.Initialization2('7',domain): return public.returnMsg(False, "配置文件错误请检查配置文件")
        if not self.ChekcDomain(domain): return public.returnMsg(False, "tomcat中未存在此域名")
        # 取到端口
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
        result = public_check().create_site(get)
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

    # 判断域名是否存在
    def ChekcDomain(self, domain):
        ret = self.GetVhosts()
        for i in ret:
            if 'name' in i:
                if i['name'] == domain:
                    return True
        else:
            return False

    # 保存配置文件
    def save_conf(self, get):
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
