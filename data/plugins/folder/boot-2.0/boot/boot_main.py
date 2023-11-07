#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | 系统启动项
# +-------------------------------------------------------------------
import sys,os,json,re,time
os.chdir("/www/server/panel")
sys.path.append("class/")
import public
  
  
class boot_main:
    __os_info = None
    __basic_path = '/www/server/panel/plugin/boot'
    __basic_conf = "%s/config.json" % __basic_path
    __environment_file = '%s/environment.json' % __basic_path
    
    def __init__(self):
        self.os_info = self.get_os_info()
        if self.os_info["osname"] == "CentOS":
            if self.os_info["version"].startswith("6"):
                self.__os_info = "CentOS6"
            else:
                self.__os_info = "CentOS7"
        elif self.os_info["osname"] == "Ubuntu":
            self.__os_info = "Ubuntu"
        elif self.os_info["osname"] == "Debian":
            self.__os_info = "Debian"
        
    # 添加系统启动项
    def create_server(self, get):
        server_name = get.server_name
        server_path = get.server_path.split()[-1]
        if not os.path.exists(server_path) or not os.path.isfile(server_path):
            return public.returnMsg(False, "请输入正确文件路径哦!")
        public.ExecShell("chmod +x {}".format(server_path))
        if not os.path.exists("/etc/rc.local"):
            result = self.handle_file()
            if result:
                return public.returnMsg(False, result['msg'])
        content = self.get_profile("/etc/rc.local")
        content += '\n' + server_path
        self.save_profile("/etc/rc.local", content)
        result = self.__read_config(self.__basic_conf)
        d = dict()
        d["server_name"] = server_name
        d["server_path"] = server_path
        result.append(d)
        self.__write_config(self.__basic_conf, result)
        return public.returnMsg(True, "添加开机启动脚本成功!")
        
    # 删除系统启动项
    def remove_server(self, get):
        server_path = get.server_path
        server_name = server_path.split("/")[-1]
        if server_name == "rc.local":
            return public.returnMsg(False, "该插件暂不支持删除该启动文件!")
        if os.path.exists('/etc/profile.d/{0}'.format(server_name)):
            os.remove('/etc/profile.d/{0}'.format(server_name))
            return public.returnMsg(True, "删除开机启动脚本成功!")
        try:
            content = self.__read_config(self.__basic_conf)
            for c in content:
                if c["server_path"] == server_path:
                    content.remove(c)
                    res = self.get_profile('/etc/rc.local')
                    res = res.replace(c["server_path"], '')
                    self.save_profile("/etc/rc.local", res)
            self.__write_config(self.__basic_conf, content)
            os.remove(server_path)
            return public.returnMsg(True, "删除开机启动脚本成功!")
        except:
            return public.returnMsg(False, "删除开机启动脚本失败!")
        # if self.__os_info.startswith("CentOS"):
        #     public.ExecShell("chkconfig {0} off;chkconfig --del {1}".format(server_name, server_name))
        # elif self.__os_info=="Ubuntu":
        #     public.ExecShell("update-rc.d -f {0} remove".format(server_name))
        # elif self.__os_info=="Debian":
        #     public.ExecShell("update-rc.d -f {0} remove".format(server_name))
       
    # 获取系统启动项 
    def get_run_list(self, get):
        runFile = ['/etc/rc.local','/etc/profile','/etc/inittab','/etc/rc.sysinit'];
        runList = []
        for rfile in runFile:
            if not os.path.exists(rfile): continue;
            bodyR = self.clear_comments(public.readFile(rfile))
            if not bodyR: continue
            stat = os.stat(rfile)
            accept = str(oct(stat.st_mode)[-3:]);
            if accept == '644': continue
            tmp = {}
            tmp['name'] = rfile
            tmp['srcfile'] = rfile
            tmp['size'] = os.path.getsize(rfile)
            tmp['access'] = accept
            tmp['ps'] = self.get_run_ps(rfile)
            tmp["status"] = "allow"
            runList.append(tmp)
        runlevel = self.get_my_runlevel()
        runPath = ['/etc/init.d','/etc/rc' + runlevel + '.d'];
        tmpAll = []
        islevel = False;
        for rpath in runPath:
            if not os.path.exists(rpath): continue;
            if runPath[1] == rpath: islevel = True;
            for f in os.listdir(rpath):
                if f[:1] != 'S' and f[:1] != 'K': continue;
                tmp = {}
                tmp["status"] = "allow"
                if f[:1] != 'S': 
                    tmp["status"] = "deny"
                filename = rpath + '/' + f;
                if not os.path.exists(filename): continue;
                if os.path.isdir(filename): continue;
                if os.path.islink(filename):
                    flink = os.readlink(filename).replace('../','/etc/');
                    if not os.path.exists(flink): continue;
                    filename = flink;
                tmp['name'] = f;
                if islevel: tmp['name'] = f[3:];
                if tmp['name'] in tmpAll: continue;
                stat = os.stat(filename);
                accept = str(oct(stat.st_mode)[-3:]);
                if accept == '644': continue;
                tmp['srcfile'] = filename;
                tmp['access'] = accept;
                tmp['size'] = os.path.getsize(filename);
                tmp['ps'] = self.get_run_ps(tmp['name']);
                runList.append(tmp);
                tmpAll.append(tmp['name']);
        for sh_path in os.listdir("/etc/profile.d"):
            if sh_path.find('.sh') == -1: continue;
            filename = '/etc/profile.d/{}'.format(sh_path)
            stat = os.stat(filename);
            accept = str(oct(stat.st_mode)[-3:]);
            # if accept == '644': continue;
            tmp = {}
            tmp['name'] = sh_path
            tmp['srcfile'] = filename
            tmp['access'] = accept
            tmp['size'] = os.path.getsize(filename)
            tmp['ps'] = self.get_run_ps(tmp['name'])
            tmp["status"] = "allow"
            runList.append(tmp);
        runList = self.get_script_list(runList)
        data = {}
        data['run_level'] = runlevel
        data['run_list'] = sorted(runList, key=lambda x : x['srcfile'], reverse=True);
        if get.query:
            for service in runList:
                if get.query == service['name']:
                    data['run_list'] = [service]
                    return data
        return data;

    # 设置启动项开机启用/禁用
    def set_server_status(self, get):
        status = get.status
        filename = get.filename
        key = "S"
        if status == "stop":
            key = "K"
        
        dirs_files = os.listdir("/etc/init.d/")
        files = []
        for file in dirs_files:
            if os.path.isfile("/etc/init.d/" + file):
                files.append("/etc/init.d/" + file)
        if not filename in files:
            return public.returnMsg(False, "该插件暂不支持设置该启动项状态!")
            
        array = ['/etc/rc2.d/', '/etc/rc3.d/', '/etc/rc4.d/', '/etc/rc5.d/']
        filename = filename.split("/")[-1]
        import shutil
        try:
            for rc_d in array:
                for d in os.listdir(rc_d):
                    if d[3:] != filename: continue;
                    sfile = rc_d + d;
                    dfile = rc_d + key + d[1:]
                    shutil.move(sfile, dfile);
            return public.returnMsg(True, '设置成功!')
        except:
            return public.returnMsg(False, '设置失败!')
            
    # 获取自己添加的启动项脚本
    def get_script_list(self, runList):
        result = self.__read_config(self.__basic_conf)
        for d in result:
            filename = d["server_path"]
            if not os.path.exists(filename):
                continue
            stat = os.stat(filename);
            accept = str(oct(stat.st_mode)[-3:]);
            tmp = {}
            tmp['name'] = d["server_name"]
            tmp['srcfile'] = filename
            tmp['access'] = accept
            tmp['size'] = os.path.getsize(filename)
            tmp['ps'] = self.get_run_ps(tmp['name'])
            tmp["status"] = "allow"
            runList.append(tmp);
        return runList
        
    # 获取服务列表
    def get_systemctl_list(self, get):
        serviceList = []
        if os.path.exists('/usr/lib/systemd/system/'):
            systemctl_user_path = '/usr/lib/systemd/system/'
        elif os.path.exists('/lib/systemd/system/'):
            systemctl_user_path = '/lib/systemd/system/'
        systemctl_run_path = '/etc/systemd/system/multi-user.target.wants/'
        data = {}
        data['runlevel'] = self.get_my_runlevel()
        if not os.path.exists(systemctl_user_path) or not os.path.exists(systemctl_run_path): 
            return serviceList
        r = '.service'
        status_list = public.ExecShell("systemctl list-units --type=service | awk '{print $1}'")[0].split('\n')
        enable_list = public.ExecShell("systemctl list-unit-files | grep enable | awk '{print $1}'")[0].split('\n')
        for d in os.listdir(systemctl_user_path):
            if d.find(r) == -1: continue;
            if not self.cont_systemctl(d): continue;
            serviceInfo = {}
            serviceInfo['name'] = d.replace(r,'')
            serviceInfo['srcfile'] = systemctl_user_path + d
            serviceInfo['ps'] = self.get_run_ps(serviceInfo['name'])
            serviceInfo["status"] = False
            serviceInfo['is_boot'] = '<span style="color:red;" title="点击关闭" data-status="deny">已禁用</span>'
            if d in status_list:
                serviceInfo["status"] = True
            # res = public.ExecShell('systemctl status {0}; systemctl is-enabled {1}'.format(d, d))[0]
            # if res.find('Active: inactive')!=-1:
            #     serviceInfo["status"] = False
            # elif res.find('Active: active')!=-1:
            #     serviceInfo["status"] = True
            
            # if res.split('\n')[-2] == "enabled":
            #     isrun = '<span style="color:green;" title="点击开启" data-status="allow">已启用</span>'
            #     serviceInfo['is_boot'] = isrun
            if d in enable_list:
                isrun = '<span style="color:green;" title="点击开启" data-status="allow">已启用</span>'
                serviceInfo['is_boot'] = isrun
            serviceList.append(serviceInfo)
        data['serviceList'] = sorted(serviceList, key=lambda x: x['name'], reverse=False)
        if get.query:
            for service in data['serviceList']:
                if get.query == service['name']:
                    data['serviceList'] = [service]
                    return data
        return data
        
    # 设置服务运行状态
    def set_run_status(self,get):
        if os.path.exists('/usr/lib/systemd/system/'):
            systemctl_user_path = '/usr/lib/systemd/system/'
        elif os.path.exists('/lib/systemd/system/'):
            systemctl_user_path = '/lib/systemd/system/'
        if get.status == "true":
            public.ExecShell('systemctl stop {0}'.format(get.serviceName))
            return public.returnMsg(True,'设置成功!')
        else:
            public.ExecShell('systemctl start {0}'.format(get.serviceName))
            return public.returnMsg(True,'设置成功!')
        return public.returnMsg(False,'设置失败!')
        
    # 设置服务开机状态
    def set_boot_status(self, get):
        status = get.status
        if os.path.exists('/usr/lib/systemd/system/'):
            systemctl_user_path = '/usr/lib/systemd/system/'
        elif os.path.exists('/lib/systemd/system/'):
            systemctl_user_path = '/lib/systemd/system/'
        systemctl_run_path = '/etc/systemd/system/multi-user.target.wants/'
        if os.path.exists(systemctl_user_path + get.serviceName + '.service'):
            if status == "allow":
                public.ExecShell('systemctl disable {}'.format(get.serviceName))
            else:
                public.ExecShell('systemctl enable {}'.format(get.serviceName))
            return public.returnMsg(True, '设置成功！')
        return public.returnMsg(True, '设置失败！')
        
    # 添加服务
    def add_service(self, get):
        service_path = get.service_path
        boot_status = get.boot_status
        if os.path.exists('/usr/lib/systemd/system/'):
            systemctl_user_path = '/usr/lib/systemd/system/'
        elif os.path.exists('/lib/systemd/system/'):
            systemctl_user_path = '/lib/systemd/system/'
        if self.__os_info == "CentOS6":
            return public.returnMsg(False, 'CentOS6暂不支持使用systemctl管理服务，请在启动项里面管理服务！')
        if not os.path.isfile(service_path):
            return public.returnMsg(False, '您输入的不是一个有效的文件！')
        service_name = service_path.split('/')[-1]
        if not service_name.endswith(".service"):
            return public.returnMsg(False, '请选择一个.service文件！')
        path = systemctl_user_path + '{0}'.format(service_name)
        if os.path.isfile(path):
            return public.returnMsg(False, '该服务名称已存在，请重新命名服务文件名称！')
        public.ExecShell('cp {0} {1}'.format(service_path, systemctl_user_path))
        if boot_status == "allow":
            public.ExecShell('systemctl daemon-reload;systemctl enable {0}'.format(service_name))
        else:
            public.ExecShell('systemctl daemon-reload;systemctl disable {0}'.format(service_name))
        return public.returnMsg(True, '添加服务成功！')
        
    # 删除服务
    def del_service(self, get):
        if get.serviceName == 'bt': return public.returnMsg(False,'不能通过面板结束宝塔面板服务!');
        if os.path.exists('/usr/lib/systemd/system/'):
            systemctl_user_path = '/usr/lib/systemd/system/'
        elif os.path.exists('/lib/systemd/system/'):
            systemctl_user_path = '/lib/systemd/system/'
        systemctl_run_path = '/etc/systemd/system/multi-user.target.wants/'
        if os.path.exists(systemctl_run_path + get.serviceName + '.service'):
            os.remove(systemctl_run_path + get.serviceName + '.service');
        if os.path.exists(systemctl_user_path + get.serviceName + '.service'):
            public.ExecShell('systemctl stop ' + get.serviceName);
            os.remove(systemctl_user_path + get.serviceName + '.service')
            return public.returnMsg(True,'删除成功!')
        return public.returnMsg(False,'请确认【'+ get.serviceName +'】服务是否存在!');
      
     # 获取系统变量
    def get_environment_list(self, get):
        environmentList = []
        sys_environment_path = ['/etc/environment', '/etc/profile', '/etc/bash_profile', '/etc/bashrc', '/etc/bash.bashrc']
        for epath in sys_environment_path:
            if not os.path.exists(epath): continue;
            arry = self.get_list(epath)
            if not arry: continue
            environmentList = self.get_environment_value(arry, environmentList, epath, 'system')
        for epath in os.listdir("/etc/profile.d"):
            if epath.find('.sh') == -1: continue;
            filename = '/etc/profile.d/{}'.format(epath)
            arry = self.get_list(filename)
            environmentList = self.get_environment_value(arry, environmentList, filename, 'system')
        user_list = self.get_system_user()
        for user in user_list:
            if user == 'root':
                user_environment_path = ['/root/.bashrc', '/root/.profile', '/root/.bash_profile']
            else:
                user_environment_path = ['/home/{0}/.bashrc'.format(user), '/home/{0}/.profile'.format(user), '/home/{0}/.bash_profile'.format(user)]
            for epath in user_environment_path:
                if not os.path.exists(epath): continue;
                arry = self.get_list(epath)
                environmentList = self.get_environment_value(arry, environmentList, epath, user)
        return environmentList
        
    # 添加环境变量
    def create_environment(self, get):
        env_type = get.env_type
        env_name = get.env_name
        env_value = get.env_value
        user = public.ExecShell("whoami")[0].replace('\n', '')
        if env_type == "system":
            _string = 'export {0}={1}'.format(env_name, env_value)
            public.ExecShell('echo %s >> /etc/profile' % _string)
            public.ExecShell('source /etc/profile')
        elif env_type == "user":
            _string = 'export {0}={1}'.format(env_name, env_value)
            public.ExecShell('echo %s >> /%s/.bashrc' % (_string, user))
            public.ExecShell('source /%s/.bashrc' % user)
        return public.returnMsg(True, "添加变量成功！")
        
    # 删除环境变量
    def remove_environment(self, get):
        env_name = get.env_name
        env_value = get.env_value
        env_path = get.env_path
        if env_name == "PATH":
            return public.returnMsg(False, "该插件不支持删除【PATH】变量！")
        _string = 'export {0}={1}\n'.format(env_name, env_value)
        if not os.path.exists(env_path): 
            return public.returnMsg(False, "该路径不存在！")
        content = self.get_profile(env_path)
        if content.find(_string)!=-1:
            content = content.replace(_string, "")
            self.save_profile(env_path, content)
        else:
            public.ExecShell('echo export {0}="" >> {1}'.format(env_name, env_path))
            public.ExecShell('source {0}'.format(env_path))
        return public.returnMsg(True, "删除变量成功！")
        
    def get_environment_value(self, arry, environmentList, file_path, user):
        for a in arry:
            if user!='system':
                if a=='PATH':continue
            res = os.popen("/bin/bash {0}; source {1}; echo ${2}".format(file_path, file_path, a)).read().replace('\n', '')
            if not res: continue
            if a=='PATH':
                res =  ':'.join(list(set(res.split(':'))))
            tmp = {}
            tmp['key'] = a
            tmp['val'] = res
            tmp['path'] = file_path
            tmp['type'] = user
            environmentList.append(tmp)
        return environmentList
       
    def get_list(self, epath):
        arry = []
        content = self.get_profile(epath)
        res = re.findall(r'export .+=.*|export \w+.*', content)
        for r in res:
            r = r.replace('export ', '')
            tmp = {}
            if r.find('=')!=-1:
                arry.append(r.split('=')[0])
            else:
                m = r.split(' ')
                arry.extend(m)
        if content.find('[ -z "$PS1" ] && return')!=-1:
            if content.find('# [ -z "$PS1" ] && return')==-1:
                content = content.replace('[ -z "$PS1" ] && return', '# [ -z "$PS1" ] && return')
            self.save_profile(epath, content)
        return list(set(arry))
       
    def get_system_user(self):
        user_list = []
        res = public.ExecShell("cat /etc/passwd")[0].split('\n')
        for r in res:
            user = r.split(':')[0]
            if not user: continue
            if not os.path.exists('/home/{0}'.format(user)): continue
            user_list.append(user)
        user_list.append('root')
        return user_list
        
    # 获取系统类型(具体到哪个版本)
    def get_os_info(self):
        tmp = {}
        if os.path.exists('/etc/redhat-release'):
            sys_info = public.ReadFile('/etc/redhat-release')
        elif os.path.exists('/usr/bin/yum'):
            sys_info = public.ReadFile('/etc/issue')
        elif os.path.exists('/etc/issue'):
            sys_info = public.ReadFile('/etc/issue')
        tmp['osname'] = sys_info.split()[0]
        tmp['version'] = re.search(r'\d+(\.\d*)*', sys_info).group()
        return tmp
      
    def get_run_ps(self,name):
        runPs = {'netconsole':'网络控制台日志','network':'网络服务','jexec':'JAVA','tomcat8':'Apache Tomcat','tomcat7':'Apache Tomcat','mariadb':'Mariadb',
                 'tomcat9':'Apache Tomcat','tomcat':'Apache Tomcat','memcached':'Memcached缓存器','php-fpm-53':'PHP-5.3','php-fpm-52':'PHP-5.2',
                 'php-fpm-54':'PHP-5.4','php-fpm-55':'PHP-5.5','php-fpm-56':'PHP-5.6','php-fpm-70':'PHP-7.0','php-fpm-71':'PHP-7.1',
                 'php-fpm-72':'PHP-7.2','rsync_inotify':'rsync实时同步','pure-ftpd':'FTP服务','mongodb':'MongoDB','nginx':'Web服务器(Nginx)',
                 'httpd':'Web服务器(Apache)','bt':'宝塔面板','mysqld':'MySQL数据库','rsynd':'rsync主服务','php-fpm':'PHP服务','systemd':'系统核心服务',
                 '/etc/rc.local':'用户自定义启动脚本','/etc/profile':'全局用户环境变量','/etc/inittab':'用于自定义系统运行级别','/etc/rc.sysinit':'系统初始化时调用的脚本',
                 'sshd':'SSH服务','crond':'计划任务服务','udev-post':'设备管理系统','auditd':'审核守护进程','rsyslog':'rsyslog服务','sendmail':'邮件发送服务','blk-availability':'lvm2相关',
                 'local':'用户自定义启动脚本','netfs':'网络文件系统','lvm2-monitor':'lvm2相关','xensystem':'xen云平台相关','iptables':'iptables防火墙','ip6tables':'iptables防火墙 for IPv6','firewalld':'firewall防火墙'}
        if name in runPs: return runPs[name]
        return name;
    
    def clear_comments(self,body):
        bodyTmp = body.split("\n");
        bodyR = ""
        for tmp in bodyTmp:
            if tmp.startswith('#'): continue;
            if tmp.strip() == '': continue;
            bodyR += tmp;
        return bodyR
        
    # 获取当前系统运行级别
    def get_my_runlevel(self):
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
        
    # 获取某个服务各个运行级别的启动状况
    def get_runlevel(self,name):
        rc_d = '/etc/'
        runlevels = []
        for i in range(7):
            isrun = '<span style="color:red;" title="点击开启">关闭</span>'
            for d in os.listdir(rc_d + 'rc' + str(i) + '.d'):
                if d[3:] == name:
                    if d[:1] == 'S': isrun = '<span style="color:green;" title="点击关闭">开启</span>'
            runlevels.append(isrun)
        return runlevels
        
    def cont_systemctl(self,name):
        conts = ['systemd','rhel','plymouth','rc-','@','init','ipr','dbus','-local']
        for c in conts:
            if name.find(c) != -1: return False
        return True
        
    def handle_file(self):
        if self.os_info["osname"] == "Ubuntu":
            version = self.os_info["version"]
            if version.startswith("18") or version.startswith("20"):
                if not os.path.exists('/etc/systemd/system/rc-local.service'):
                    return {'status':False, 'msg':'rc-local.service not exists!'}
                public.ExecShell('ln -fs /lib/systemd/system/rc-local.service /etc/systemd/system/rc-local.service')
                content = self.get_profile('/etc/systemd/system/rc-local.service')
                content += '[Install]\n' + 'WantedBy=multi-user.target\n' + 'Alias=rc-local.service'
                self.save_profile("/etc/systemd/system/rc-local.service", content)
                public.ExecShell('touch /etc/rc.local;chmod a+x /etc/rc.local')
                content = self.get_profile('/etc/rc.local')
                content += '#!/bin/bash'
                self.save_profile('/etc/rc.local', content)
        
    # 添加系统启动项
    def create_server1(self, get):
        file_path = get.server_path
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return public.returnMsg(False, "请输入正确文件路径哦!")
        public.ExecShell("chmod +x {}".format(file_path))
        if self.__os_info.startswith("CentOS"):
            file_name = file_path.split(r"/")[-1]
            self.handle_centos_boot(file_path, file_name)
            public.ExecShell("cp {0} {1};cd /etc/rc.d/init.d".format(file_path, "/etc/rc.d/init.d/"))
            public.ExecShell("chkconfig --add {0};chkconfig {1} on".format(file_name, file_name))
        elif self.__os_info=="Ubuntu" or self.__os_info=="Debian":
            file_name = file_path.split(r"/")[-1]
            self.handle_ubuntu_boot(file_path, file_name)
            public.ExecShell("cp {0} {1};cd /etc/init.d".format(file_path, "/etc/init.d/"))
            public.ExecShell("update-rc.d {0} defaults".format(file_name)) 
        return public.returnMsg(True, "添加服务开机启动成功!")
        
    # 处理centos添加开机启动项
    def handle_centos_boot(self, file_path, file_name):
        content = self.get_profile(file_path)
        if content.find("chkconfig") != -1:
            _string = ""
        else:
            _string = "# chkconfig: 2345 55 25\n" + "# description: {}\n".format(file_name)
        if content.find("#!/bin/bash") != -1:
            _string = "#!/bin/bash\n" + _string
            content = content.replace("#!/bin/bash\n", _string)
        else:
            content = _string + content
        self.save_profile(file_path, content)
        
    # 处理ubuntu添加开机启动项
    def handle_ubuntu_boot(self, file_path, file_name):
        content = self.get_profile(file_path)
        if content.find("# Default-Start") != -1:
            _string = ""
        else:
            _string = "### BEGIN INIT INFO\n" + "# Provides:{}\n".format(file_name) + "# Required-Start:$all\n" + "# Required-Stop:$all\n" + "# Default-Start:2 3 4 5\n" + "# Default-Stop:0 1 6\n" + "# Short-Description: start MyService\n" + "# description:start the MyService\n" + "### END INIT INFO\n"
        if content.find("#!/bin/bash") != -1:
            _string = "#!/bin/bash\n" + _string
            content = content.replace("#!/bin/bash\n", _string)
        else:
            content = _string + content
        self.save_profile(file_path, content)
        
    # 读取文件
    def get_profile(self, path):
        content = ""
        with open(path, "r") as fr:
            content = fr.read()
        return content
        
    # 保存配置文件  
    def save_profile(self, path, data):
        with open(path, "w") as fw:
            fw.write(data)
            
    # 读config.json配置
    def __read_config(self, path):
        if not os.path.exists(path):
            public.writeFile(path, '[]')
        upBody = public.readFile(path)
        if not upBody: 
            upBody = '[]'
        return json.loads(upBody)

    # 写config.json配置
    def __write_config(self ,path, data):
        return public.writeFile(path, json.dumps(data))
    
    