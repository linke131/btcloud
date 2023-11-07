# coding: utf-8
# -----------------------------
# 宝塔Linux面板 java项目管理器
# Author: HUB

import sys, os, time

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
sys.path.append("class/")
import public, files, firewalls
from public_check import public_check
from tomcat_manager import tomcat_manager
from springboot_manager import springboot_manager
from BTPanel import session
import random,string
#from weblogic_manager import weblogic_manager
# from jboss_manager import jboss_manager
# from glassfish_manager import glassfish_manager
# from websphere_manager import websphere_manager
# from jetty_manager import jetty_manager
# from resion_manager import resion_manager


class file:
    path = encoding = ''


class mobj:
    port = ps = ''


class liang:
    version = ''


class java_manager_main(object):

    def __init__(self):
        self.__create_table()

    def __create_table(self):
        # 创建java_project表储存项目
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'java_project')).count():
            public.M('').execute('''CREATE TABLE "java_project" (
                                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                                "stype" TEXT,
                                "domain" TEXT,
                                "path" TEXT,
                                "webserver" TEXT,
                                "port" INTEGER,
                                "auto_start" INTEGER,
                                "add_time" INTEGER);''')
        # 创建springboot表储存项目
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'springboot_project')).count():
            public.M('').execute('''CREATE TABLE "springboot_project" (
                                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                                "project_version" TEXT,
                                "project_name" TEXT,
                                "path" TEXT,
                                "service_order" TEXT,
                                "port" INTEGER,
                                "add_time" INTEGER);''')



    # web容器服务安装
    def install_webserver(self, get):
        webserver = get.webserver.strip().lower()
        if 'tomcat' in webserver:
            return tomcat_manager().install_tomcat(get)
        elif 'weblogic' in webserver:
            return weblogic_manager().install_weblogic(get)
        elif 'wildfly' in webserver:
            return self.install_jboss(get)
        elif 'glassfish' in webserver:
            return self.install_glassfish(get)
        elif 'websphere' in webserver:
            return self.install_websphere(get)
        elif 'jetty' in webserver:
            return self.install_jetty(get)
        elif 'resin' in webserver:
            return self.install_resion(get)
        else:
            return public.returnMsg(False, '不支持的webserver类型！')

    # 获取已安装web容器列表
    def get_installed_webserver(self, get):
        data = {}
        data['tomcat7'] = True if os.path.exists('/www/server/tomcat7/conf/server.xml') else False
        data['tomcat8'] = True if os.path.exists('/www/server/tomcat8/conf/server.xml') else False
        data['tomcat9'] = True if os.path.exists('/www/server/tomcat9/conf/server.xml') else False
        data['tomcat10'] = True if os.path.exists('/www/server/tomcat10/conf/server.xml') else False
        #data['weblogic10.3.6'] = True if os.path.exists('/www/server/weblogic10.3.6') else False
        # data['weblogic12.2.1.4'] = True if os.path.exists('/www/server/weblogic12.2.1.4') else False
        # data['weblogic14.1.1.0'] = True if os.path.exists('/www/server/weblogic14.1.1.0') else False
        #data['wildfly19.1.0'] = True if os.path.exists('/www/server/wildfly19.1.0') else False
        #data['wildfly20.0.1 '] = True if os.path.exists('/www/server/wildfly20.0.1 ') else False
        #data['glassfish4.1.2'] = True if os.path.exists('/www/server/glassfish4.1.2') else False
        #data['glassfish5.0.1'] = True if os.path.exists('/www/server/glassfish5.0.1') else False
        #data['jetty9.3.28'] = True if os.path.exists('/www/server/jetty9.3.28') else False
        #data['jetty9.4.31'] = True if os.path.exists('/www/server/jetty9.4.31') else False
        #data['resin4.0.65'] = True if os.path.exists('/www/server/resin4.0.65') else False
        #data['resin3.1.16'] = True if os.path.exists('/www/server/resin3.1.16') else False
        result = {'install_log': public.GetNumLines('/tmp/web.json', 3000), 'webserver': data}
        return result

    # 获取项目列表
    def get_project_list(self, get):
        p = int(get.p) if 'p' in get else 1
        rows = int(get.size) if 'size' in get else 9
        callback = get.callback if 'callback' in get else ''

        count = public.M('java_project').count()
        # 获取分页数据
        page_data = public.get_page(count, p, rows, callback)
        # 获取当前页的数据列表
        data_list = public.M('java_project').order('id desc').limit(page_data['shift'] + ',' + page_data['row']).select()
        # 返回数据到前端
        return {'data': data_list, 'page': page_data['page']}

    # 添加项目
    def add_project(self, get):
        pdata = {}
        pdata['domain'] = get.domain.strip()
        if public.M('java_project').where('domain=?', pdata['domain']).count():
            return public.returnMsg(False, '该网站已经存在，不能重复添加！')
        pdata['stype'] = get.stype.strip()
        if pdata['stype'] not in ['independent', 'built']:
            return public.returnMsg(False, '非法的项目类型！')
        pdata['webserver'] = get.webserver.strip().lower()
        pdata['path'] = get.path
        pdata['port'] = get.port if 'port' in get else 0
        pdata['auto_start'] = get.auto_start if 'auto_start' in get else 0
        pdata['add_time'] = int(time.time())
        if 'tomcat' in pdata['webserver']:
            result = tomcat_manager().add_tomcat_project(get)
        elif 'weblogic' in pdata['webserver']:
            result = weblogic_manager().add_weblogic_project(get)
        elif 'wildfly' in pdata['webserver']:
            result = self.add_jboss_project(get)
        elif 'glassfish' in pdata['webserver']:
            result = self.add_glassfish_project(get)
        elif 'jetty' in pdata['webserver']:
            result = self.add_jetty_project(get)
        elif 'resion' in pdata['webserver']:
            result = self.add_resion_project(get)
        else:
            result = public.returnMsg(False, '不支持的webserver类型！')
        if not result['status']: return result
        public.M('java_project').insert(pdata)
        return public.returnMsg(True, '添加成功!')

    # 删除项目
    def delete_project(self, get):
        project_info = public.M('java_project').where('id=?', get.id).find()
        if 'tomcat' in project_info['webserver']:
            tomcat_manager().delete_tomcat_project(project_info)
        elif 'weblogic' in project_info['webserver']:
            weblogic_manager().delete_weblogic_project(project_info)
        elif 'wildfly' in project_info['webserver']:
            pass
        elif 'glassfish' in project_info['webserver']:
            pass
        elif 'websphere' in project_info['webserver']:
            pass
        elif 'jetty' in project_info['webserver']:
            pass
        elif 'resion' in project_info['webserver']:
            pass
        else:
            return public.returnMsg(True, '删除失败')

        public.M('java_project').where('id=?', get.id).delete()
        return public.returnMsg(True, '删除成功')

    # 映射项目
    def mapping_project(self, get):
        project_info = public.M('java_project').where('id=?', get.id).find()
        if 'tomcat' in project_info['webserver']:
            get.domain = project_info['domain']
            if project_info['stype'] == 'independent':
                result = tomcat_manager().Mapping2(get)
            else:
                get.version = project_info['webserver']
                result = tomcat_manager().Mapping(get)
        elif 'weblogic' in project_info['webserver']:
            if project_info['stype'] == 'independent':
                result = weblogic_manager().Mapping2(get)
            else:
                get.version = project_info['webserver']
                result = weblogic_manager().Mapping(get)
        elif 'wildfly' in project_info['webserver']:
            pass
        elif 'glassfish' in project_info['webserver']:
            pass
        elif 'websphere' in project_info['webserver']:
            pass
        elif 'jetty' in project_info['webserver']:
            pass
        elif 'resion' in project_info['webserver']:
            pass
        else:
            result = public.returnMsg(False, '不支持的webserver类型！')
        return result

    # 获取当前运行的容器服务
    def get_services(self, get):
        tomcat_services = tomcat_manager().get_tomcat_services()
        # weblogic_services = weblogic_manager().get_weblogic_services()
        # allweb_services = tomcat_services + weblogic_services
        ret=[]

        if session.get('tomcat_site',''):
            for i in tomcat_services:
                if i['service_name']==session.get('tomcat_site',''):
                    ret.insert(0,i)
                else:
                    ret.append(i)
            return ret
        else:
            return tomcat_services

    # 服务状态管理
    def service_status_manage(self, get):
        service_name = get.service_name.strip()
        webserver = get.webserver.strip()
        if 'tomcat' in webserver:
            if public_check().is_domain(service_name):
                get.domain = service_name
                return tomcat_manager().StartTomcat2(get)
            else:
                return tomcat_manager().StartTomcat(get)
        # if 'weblogic' in webserver:
        #     if self.is_domain(service_name):
        #         get.domain = service_name
        #         return weblogic_manager().StartWeblogic2(get)
        #     else:
        #         return weblogic_manager().StartWeblogic(get)

    # 修改服务端口
    def modify_port(self, get):
        service_name = get.service_name.strip()
        webserver = get.webserver.strip()
        if 'tomcat' in webserver:
            if public_check().is_domain(service_name):
                get.domain = service_name
                return tomcat_manager().SetTomcatPort2(get)
            else:
                return tomcat_manager().SetTomcatPort(get)
        # if 'weblogic' in webserver:
        #     if public_check().is_domain(service_name):
        #         get.domain = service_name
        #         return weblogic_manager().SetWeblogicPort2(get)
        #     else:
        #         return weblogic_manager().SetWeblogicPort(get)

    # 修改服务配置
    def modify_conf(self, get):
        service_name = get.service_name.strip()
        webserver = get.webserver.strip()
        session['tomcat_site']=service_name


        if 'tomcat' in webserver:
            if public_check().is_domain(service_name):
                get.path = '/www/server/web_site/{}/conf/server.xml'.format(service_name)
                get.encoding = 'utf-8'
                return tomcat_manager().save_conf(get)
            else:
                get.path = '/www/server/{}/conf/server.xml'.format(webserver)
                get.encoding = 'utf-8'
                return tomcat_manager().save_conf(get)
        # if 'weblogic' in webserver:
        #     if self.is_domain(service_name):
        #         get.path = '/www/server/web_site/{}/domains/base_domain/config/config.xml'.format(service_name)
        #         get.encoding = 'utf-8'
        #         return tomcat_manager().save_conf(get)
        #     else:
        #         get.path = '/www/server/{}/conf/domains/base_domain/config/config.xml'.format(webserver)
        #         get.encoding = 'utf-8'
        #         return tomcat_manager().save_conf(get)


    def get_config_jdk_version(self,get):
        ret=[]
        if os.path.exists('/usr/bin/java'):
            ret.append(['JDK', '/usr/bin/java'])
        if os.path.exists('/usr/java/jdk1.8.0_121/bin/java'):
            ret.append(['jdk8','/usr/java/jdk1.8.0_121/bin/java'])
        if os.path.exists('/usr/java/jdk1.7.0_80/bin/java'):
            ret.append(['jdk7','/usr/java/jdk1.7.0_80/bin/java'])
        return ret

    # 随机生成端口
    def generate_random_port(self):
        import random
        port = str(random.randint(5000, 10000))
        while True:
            if not self.IsOpen(port): break
            port = str(random.randint(5000, 10000))
        return port

    #获取当前的命令
    def return_cmd(self,get):
        port = get.port if 'port' in get else self.generate_random_port()
        get.jdk_path = get.jdk_path if 'jdk_path' in get else '/usr/java/jdk1.8.0_121/bin/java'
        if not os.path.exists(get.jdk_path):return public.returnMsg(False, '传入的JDK路径不存在！！')
        get.jdk_path = get.jdk_path if 'jdk_path' in get else '/usr/java/jdk1.7.0_80/bin/java'
        if not os.path.exists(get.jdk_path): return public.returnMsg(False, '传入的JDK路径不存在！！')
        if not os.path.exists(get.jdk_path.strip()):return public.returnMsg(False, '传入的JDK路径不存在！！')
        is_root = get.is_root if 'is_root' in get else '0'
        log = get.log_path if 'log_path' in get else '/tmp/'+''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))+'.log'
        path=get.path
        if is_root=='1':
            return public.returnMsg(True, {"zui":'>> %s 2>&1 &'%log,"qian":"nohup %s -jar %s"%(get.jdk_path, path+'/'+get.project_name.strip()),"args":"--server.port=%s "%port,"user":"root","jdk_path":get.jdk_path,"java_jar":path+'/'+get.project_name.strip(),"port":port,"log":log,"cmd":'nohup %s -jar  %s --server.port=%s >> %s 2>&1 &' % (get.jdk_path, path+'/'+get.project_name.strip(), port, log)})
        else:
            return public.returnMsg(True,{"zui":'>> %s 2>&1 &'%log,"qian":"sudo -u springboot nohup %s -jar %s"%(get.jdk_path, path+'/'+get.project_name.strip()),"args":"--server.port=%s "%port,"user":"springboot","jdk_path":get.jdk_path,"java_jar":path+'/'+get.project_name.strip(),"port":port,"log":log,"cmd":'sudo -u springboot nohup %s -jar  %s --server.port=%s >> %s 2>&1 &'%(get.jdk_path,path+'/'+get.project_name.strip(),port,log)})

        # 开机自启
    def auto_start_spring_boot(self, get):
            domain = get.domain
            shell_cmd = get.cmd
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
    %s''' % shell_cmd
            public.WriteFile('/etc/init.d/' + 'spring_boot_' + domain, data)
            start_tomcat = '/etc/init.d/' + 'spring_boot_' + domain
            public.ExecShell('chmod +x %s && chkconfig --add %s && chkconfig --level 2345 %s on' % (
                start_tomcat, 'spring_boot_' + domain, 'spring_boot_' + domain))
            return True

    # 添加项目
    def add_springboot_projects(self, get):
        pdata = {}
        public.ExecShell('useradd -s /sbin/nologin springboot')
        port = get.port if 'port' in get else 0
        auto = get.auto if 'auto' in get else 0
        cmd_shell = get.cmd_shell if 'cmd_shell' in get else False
        if self.IsOpen(port): return public.returnMsg(False, '端口已经被占用!')
        domain=get.domain.strip()
        log_path = get.log_path.strip()
        pdata['port'] = port
        pdata['project_name'] = get.project_name.strip()
        pdata['project_version'] = log_path+'||'+domain
        pdata['path'] = get.path
        pdata['add_time'] = int(time.time())
        qian=get.qian.strip()
        zui=get.zui.strip()
        args=get.args.strip()
        cmd=qian+' '+args+' '+zui
        ##cmd 命令合法性
        if not cmd[-1]=='&':return public.returnMsg(False, '命令中最后一个位必须位&')
        pdata['service_order'] = cmd_shell
        public.ExecShell(pdata['service_order'])
        public.M('springboot_project').insert(pdata)
        if auto==1:
            get.cmd=pdata['service_order']
            self.auto_start_spring_boot(get)
        return public.returnMsg(True, '添加成功')

    # 删除项目
    def delete_springboot_project(self, get):
        project_info = public.M('springboot_project').where('id=?', get.id).find()
        # 开始停服务
        port=project_info['port']
        project_name=project_info['project_name']
        log=project_info['project_version'].split("||")[0]
        #获取pid
        ret=public.ExecShell('ps -aux |grep %s |grep %s |awk \'{print $2}\''%(project_name,port))
        if ret[0]:
            ret2=ret[0].split('\n')
            for i in ret2:
                if i:
                    public.ExecShell('kill -9 %s'%i)
        if log:
            if os.path.exists(log):
                os.remove(log)
        if os.path.exists('/etc/init.d/spring_boot_' +project_name):
            os.remove('/etc/init.d/spring_boot_' +project_name)
        public.M('springboot_project').where('id=?', get.id).delete()

        return public.returnMsg(True, '删除成功')

    # 获取springboot项目列表
    def get_springboot_list(self, get):
        p = int(get.p) if 'p' in get else 1
        rows = int(get.size) if 'size' in get else 9
        callback = get.callback if 'callback' in get else ''
        count = public.M('springboot_project').count()
        # 获取分页数据
        page_data = public.get_page(count, p, rows, callback)
        # 获取当前页的数据列表
        data_list = public.M('springboot_project').order('id desc').limit(page_data['shift'] + ',' + page_data['row']).select()
        for item in data_list:
            port = item['port']
            project_name = item['project_name'].split('||')[0]
            isexsit_service = public.ExecShell('ps -ef | grep {} |grep {} | grep -v grep'.format(project_name,port))[0]
            log = item['project_version'].split("||")[0]
            item['log_path']=log
            domain=''
            if len(item['project_version'].split("||"))>1:
                domain=item['project_version'].split("||")[1]
            item['domain']=domain
            if not isexsit_service:
                item['status'] = False
            else:
                item['status'] = True
            pro_name=os.path.splitext(item['project_name'])[0]
            item['log'] =  public.GetNumLines('{}/{}.log'.format(item['path'],pro_name), 3000) 
        # 返回数据到前端
        random_log='/tmp/'+''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))+'.log'
        return {'data': data_list, 'page': page_data['page'],'random_log':random_log}
        
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
    # 服务状态管理
    def springboot_services_manage(self, get):
        project_name = get.project_name.strip()
        project_info = public.M('springboot_project').where('project_name=?', project_name).find()
        project_version = get.project_version.strip()
        if get.type.strip()=='stop':
            port = project_info['port']
            project_name = project_info['project_name']
            # 获取pid
            ret = public.ExecShell('ps -aux |grep %s |grep %s |awk \'{print $2}\'' % (project_name, port))
            if ret[0]:
                ret2 = ret[0].split('\n')
                for i in ret2:
                    if i:
                        public.ExecShell('kill -9 %s' % i)
            return public.returnMsg(True, '停止成功')
        elif get.type.strip()=='start':
            cmd=project_info['service_order']
            public.ExecShell(cmd)
            return public.returnMsg(True, '启动成功')

    def springboot_mapping(self, get):
        project_info = public.M('springboot_project').where('id=?', get.id).find()
        # 开始停服务
        port = project_info['port']
        domain=False
        if len(project_info['project_version'].split("||")) > 1:
            domain = project_info['project_version'].split("||")[1]
        if not domain:return public.returnMsg(True, '域名不存在.建议删除重新建立')
        # 检查服务是否启动
        # 取到端口
        sql = public.M('sites')
        if sql.where("name=?", (domain,)).count(): return public.returnMsg(False, 'SITE_ADD_ERR_EXISTS');
        ret = {"domain": domain, "domainlist": [], "count": 0}
        import json
        get.webname = json.dumps(ret)
        get.port = "80"
        get.ftp = 'false'
        get.sql = 'false'
        get.version = '00'
        get.ps = 'springboot[' + domain + ']的映射站点'
        get.path = public.M('config').where("id=?", ('1',)).getField('sites_path') + '/' + domain
        result = public_check().create_site(get)
        if 'status' in result: return result
        import panelSite
        s = panelSite.panelSite()
        get.sitename = domain
        get.proxyname = 'springboot'
        get.proxysite = 'http://' + str(domain) + ':' + str(port)
        get.todomain = str(domain)
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
        return public.returnMsg(True, '添加成功!')
    def get_logs(self,get):
        return public.returnMsg(True, public.GetNumLines(get.path.strip(), 3000))