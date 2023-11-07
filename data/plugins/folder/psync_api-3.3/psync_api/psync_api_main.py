#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang
# +-------------------------------------------------------------------


# +-------------------------------------------------------------------
# | 宝塔一键迁移重制版
# +-------------------------------------------------------------------
import os,sys
os.chdir("/www/server/panel")
sys.path.insert(0,'class/')
import json,public,time,hashlib,panelMysql,re,pwd
class psync_api_main:
    _PLUGIN_PATH = "/www/server/panel/plugin/psync_api"
    _API_FILE = _PLUGIN_PATH +  '/config/api.json'
    _INFO_FILE = _PLUGIN_PATH + '/config/sync_info.json'
    _PAN_FILE = _PLUGIN_PATH + '/config/sync_panel.json'
    _SPEED_FILE = _PLUGIN_PATH + '/config/speed.json'
    _API = None
    _API_INFO = None

    def __init__(self):
        path = self._PLUGIN_PATH + '/config'
        if not os.path.exists(path): os.makedirs(path,384)
        self.get_panel_api()
        if self._API_INFO:
            self._API = panel_api(self._API_INFO)

    #设置面板API信息
    def set_panel_api(self,args):
        try:
            if not 'api_info' in args: return public.returnMsg(False,'参数不正确!')
            self._API_INFO = json.loads(args.api_info)
            self._API = panel_api(self._API_INFO)
            result = self._API.send_panel('/system?action=GetSystemTotal',{},30)
            if type(result) != dict:
                if result.find('this exception is only raised in debug mode') != -1:
                    return public.returnMsg(False,'目标服务器当前为【开发者模式】不能使用一键迁移!')
                return public.returnMsg(False,'目标面板连接失败，可能的原因：<br>1、目标面板地址错误<br>2、API密钥错误<br>3、目标面板版本低于6.9.8<br>4、未在目标API配置中放行IP白名单<br>')
            if 'status' in result: return result
            if not 'version' in result: return public.returnMsg(False,'请更新目标面板到最新版!')
            if result['version'] < "6.9.8": return public.returnMsg(False,'目标面板版本为{},需要6.9.8以上!'.format(result['version']))
            public.writeFile(self._API_FILE,json.dumps(self._API_INFO))
            return public.returnMsg(True,'设置成功!')
        except:
            #write_log(public.get_error_info())
            return public.returnMsg(False,'连接目标面板失败：<br>1、检查面板地址和密钥是否正确。<br>2、检查目标面板API配置中是否添加IP白名单[{}]'.format(public.GetLocalIp()))

    #取面板API信息
    def get_panel_api(self,args = None):
        try:
            if not os.path.exists(self._API_FILE): return public.returnMsg(False,'没有API配置信息')
            data = json.loads(public.readFile(self._API_FILE))
            self._API_INFO = data
            return public.returnMsg(True,data)
        except:
            write_log(public.get_error_info())
            if not os.path.exists(self._API_FILE): os.remove(self._API_FILE)
            return public.returnMsg(False,'没有API配置信息')

    #检查服务器环境
    def chekc_surroundings(self,get):
        ret={}
        ret['local']=self.get_src_config(None)
        api_panel=self.get_dst_config(None)
        if not api_panel:
            return public.returnMsg(False, "获取不到对方机器的环境信息。请修复面板再尝试一下")
        ret['api_panel']=api_panel
        return ret

    #获取目标服务器和环境配置
    def get_dst_config(self,args):
        ret = self._API.send_panel('/system?action=GetConcifInfo',{})
        disk = self._API.send_panel('/system?action=GetDiskInfo',{})
        if ret['status']:
            result={}
            result['php'] = []
            if 'webserver' in ret:
                result['webserver'] = ret['webserver']
            if 'mysql' in ret:
                result['mysql'] = ret['mysql']['status']
            if 'pure-ftpd' in ret:
                result['ftp'] = ret['pure-ftpd']['status']
            if 'php' in ret:
                for i in ret['php']:
                    result['php'].append(i['version'])
            result['status'] = True
            result['version'] = 6
            result['disk'] = disk
            return result
        else:
            return False

    #获取本地服务器和环境配置
    def get_src_config(self,args):
        serverInfo = {}
        serverInfo['status']=True
        serverInfo['webserver'] = '未安装'
        if os.path.exists('/www/server/nginx/sbin/nginx'): serverInfo['webserver'] = 'nginx'
        if os.path.exists('/www/server/apache/bin/httpd'): serverInfo['webserver'] = 'apache'
        if os.path.exists('/usr/local/lsws/bin/lswsctrl'): serverInfo['webserver'] = 'openlitespeed'
        serverInfo['php'] = []
        phpversions = ['52', '53', '54', '55', '56', '70', '71','72','73','74','80','81','82','83','84']
        phpPath = '/www/server/php/'
        for pv in phpversions:
            if not os.path.exists(phpPath + pv + '/bin/php'): continue
            serverInfo['php'].append(pv)
        serverInfo['mysql'] = False
        if os.path.exists('/www/server/mysql/bin/mysql'): serverInfo['mysql'] = True
        serverInfo['ftp'] = False
        if os.path.exists('/www/server/pure-ftpd/bin/pure-pw'): serverInfo['ftp'] = True
        if os.path.exists('/www/server/panel/runserver.py'):
            serverInfo['version'] = 6
        else:
            serverInfo['version'] = 5
        import psutil
        try:
            diskInfo = psutil.disk_usage('/www')
        except:
            diskInfo = psutil.disk_usage('/')
        serverInfo['disk'] = diskInfo[2]
        return serverInfo

    #获取目标服务器网站、数据库、FTP信息
    def get_dst_info(self,args):
        data = {}
        data['sites'] = self._API.send_panel('/data?action=getData',{"table":"sites","limit":100000,"p":1,"order":"id desc"})['data']
        data['ftps'] = self._API.send_panel('/data?action=getData',{"table":"ftps","limit":100000,"p":1,"order":"id desc"})['data']
        data['databases'] = self._API.send_panel('/data?action=getData',{"table":"databases","limit":100000,"p":1,"order":"id desc"})['data']
        return data

    #获取本地服务器网站、数据库、FTP信息
    def get_src_info(self,args):
        data = {}
        data['sites'] = public.M('sites').field("id,name,path,ps,status,addtime").order("id desc").select()
        data['ftps'] = public.M('ftps').field('id,name,ps').order("id desc").select()
        data['databases'] = public.M('databases').field('id,name,ps').order("id desc").select()
        return data

    def get_site_info(self,args):
        return self.get_src_info(args)

    #设置要被迁移的网站、数据库、FTP信息
    def set_sync_info(self,args):
        if not 'sync_info' in args: return public.returnMsg(False,'参数不正确!')
        sync_info = json.loads(args.sync_info)
        sync_info['total'] = 0
        sync_info['speed'] = 0
        for i in range(len(sync_info['sites'])):
            sync_info['sites'][i]['error'] = ''
            sync_info['sites'][i]['state'] = 0
            sync_info['total'] +=1
        for i in range(len(sync_info['databases'])):
            sync_info['databases'][i]['error'] = ''
            sync_info['databases'][i]['state'] = 0
            sync_info['total'] +=1
        for i in range(len(sync_info['ftps'])):
            sync_info['ftps'][i]['error'] = ''
            sync_info['ftps'][i]['state'] = 0
            sync_info['total'] +=1
        for i in range(len(sync_info['paths'])):
            if sync_info['paths'][i]['path'] in ['/','/etc','/var','/usr','/opt','/dev','/root']:
                return public.returnMsg(False,'不能迁移系统关键目录!')
            if sync_info['paths'][i]['to_path'] in ['/','/etc','/var','/usr','/opt','/dev','/root']:
                return public.returnMsg(False,'不能迁移到系统关键目录!')
            sync_info['paths'][i]['error'] = ''
            sync_info['paths'][i]['state'] = 0
            sync_info['total'] +=1
        public.writeFile(self._INFO_FILE,json.dumps(sync_info))
        self.fock_process(None)
        return public.returnMsg(True,'设置成功!')

    #获取要被迁移的网站、数据库、FTP信息
    def get_sync_info(self,args):
        if not os.path.exists(self._INFO_FILE): return public.returnMsg(False,'迁移信息不存在!')
        sync_info = json.loads(public.readFile(self._INFO_FILE))
        if not args: return sync_info
        result = []
        for i in sync_info['sites']:
            i['type'] = "网站"
            result.append(i)
        for i in sync_info['databases']:
            i['type'] = "数据库"
            result.append(i)
        for i in sync_info['ftps']:
            i['type'] = "FTP"
            result.append(i)
        for i in sync_info['paths']:
            i['type'] = "目录"
            result.append(i)

        return result

    #设置要被迁移的面板和环境配置信息
    def set_sync_panel(self,args):
        if not 'sync_panel' in args: return public.returnMsg(False,'参数不正确!')
        sync_panel = json.loads(args.sync_panel)
        public.writeFile(self._PAN_FILE,json.dumps(sync_panel))
        return public.returnMsg(True,'设置成功!')

    #获取要被迁移的网站、数据库、FTP信息
    def get_sync_panel(self,args):
        if not os.path.exists(self._PAN_FILE): return public.returnMsg(False,'迁移信息不存在!')
        sync_panel = json.loads(public.readFile(self._PAN_FILE))
        return sync_panel

    #取迁移进度
    def get_speed(self,args):
        if not os.path.exists(self._SPEED_FILE): return public.returnMsg(False,'正在准备..')
        try:
            speed_info = json.loads(public.readFile(self._SPEED_FILE))
        except:
            return False
        sync_info = self.get_sync_info(None)
        speed_info['all_total'] = sync_info['total']
        speed_info['all_speed'] = sync_info['speed']
        speed_info['total_time']= speed_info['end_time'] - speed_info['time']
        speed_info['total_time'] = str(int(speed_info['total_time'] // 60))+"分" + str(int(speed_info['total_time'] % 60)) + "秒"
        log_file = '/www/server/panel/logs/psync.log'
        speed_info['log'] = public.ExecShell("tail -n 10 {}".format(log_file))[0]
        #if len(speed_info['log']) > 20480 and speed_info['action'] != 'True': return False
        return speed_info

    #取迁移进程PID
    def get_pid(self):
        result = public.ExecShell("ps aux|grep psync_api_main.py|grep -v grep|awk '{print $2}'|xargs")[0].strip()
        if not result:
            import psutil
            for pid in psutil.pids():
                if not os.path.exists('/proc/{}'.format(pid)): continue #检查pid是否还存在
                p = psutil.Process(pid)
                cmd = p.cmdline()
                if len(cmd) < 2: continue
                if cmd[1].find('psync_api_main.py') != -1:
                    return pid
            return None

    #取消迁移
    def close_sync(self,args):
        public.ExecShell("kill -9 {}".format(self.get_pid()))
        public.ExecShell("kill -9 $(ps aux|grep psync_api_main.py|grep -v grep|awk '{print $2}')")
        #删除迁移配置
        time.sleep(1)
        if os.path.exists(self._INFO_FILE): os.remove(self._INFO_FILE)
        if os.path.exists(self._PAN_FILE): os.remove(self._PAN_FILE)
        if os.path.exists(self._SPEED_FILE): os.remove(self._SPEED_FILE)
        return public.returnMsg(True,'已取消迁移任务!')

    #确认
    def set_ok(self,args):
        if os.path.exists(self._INFO_FILE): os.remove(self._INFO_FILE)
        if os.path.exists(self._PAN_FILE): os.remove(self._PAN_FILE)
        if os.path.exists(self._SPEED_FILE): os.remove(self._SPEED_FILE)
        return public.returnMsg(True,'设置成功!')

    #创建迁移进程
    def fock_process(self,args):
        time.sleep(3)
        if self.get_pid(): return public.returnMsg(False,'当前已经有迁移进程在执行!')

        #获取当前python解释器位置, 防止默认Python版本与面板使用的不一致
        import psutil
        py_bin = psutil.Process(os.getpid()).exe()

        #处理旧日志
        log_file = '/www/server/panel/logs/psync_err.log'
        log_file_acc = '/www/server/panel/logs/psync.log'
        if os.path.exists(log_file_acc): os.remove(log_file_acc)
        if os.path.exists(log_file): os.remove(log_file)

        #在后台执行任务
        exe = "cd {0} && nohup {1} psync_api_main.py &>{2} &".format(self._PLUGIN_PATH,py_bin,log_file)
        public.ExecShell(exe)
        time.sleep(2)
        #检查是否执行成功
        if not self.get_pid(): return public.returnMsg(False,'创建进程失败!<br>{}'.format(public.readFile(log_file)))
        return public.returnMsg(True,"迁移进程创建成功!")

#迁移类
class psync(psync_api_main):
    _SYNC_INFO = None
    _SYNC_PANEL = None
    _SPEED_INFO = {}
    _VHOST_PATH = '/www/server/panel/vhost'
    _TO_PATHS = []
    _TO_FILES = []
    _TO_PORTS = []
    _REQUESTS = None
    def __init__(self):
        psync_api_main.__init__(self)
        self._SYNC_INFO = self.get_sync_info(None)
        if 'status' in self._SYNC_INFO: self.error('没有找到站点迁移配置',True)
        #self._SYNC_PANEL = self.get_sync_panel(None)
        #if 'status' in self._SYNC_PANEL: self.error('没有找到面板迁移配置',True)
        import requests
        if not self._REQUESTS:
            self._REQUESTS = requests.session()

    #发生错误
    def error(self,error_msg,is_exit = False):
        write_log("="*50)
        write_log("|-发生时间: {}".format(format_date()))
        write_log("|-错误信息: {}".format(error_msg))
        if is_exit:
            write_log("|-处理结果: 终止迁移任务")
            sys.exit(0)
        write_log("|-处理结果: 忽略错误, 继续执行")

    #保存迁移配置
    def save(self):
        public.writeFile(self._INFO_FILE,json.dumps(self._SYNC_INFO))

    #设置状态
    def state(self,stype,index,state,error=''):
        self._SYNC_INFO[stype][index]['state'] = state
        self._SYNC_INFO[stype][index]['error'] = error
        if self._SYNC_INFO[stype][index]['state'] != 1:
            self._SYNC_INFO['speed'] += 1
        self.save()

    #开始迁移
    def run(self):
        public.CheckMyCnf()
        self.sync_other()
        self.sync_site()
        self.sync_database()
        self.sync_ftp()
        self.sync_path()
        self.write_speed('action','True')
        write_log('|-所有项目迁移完成!')

    #迁移自定义目录
    def sync_path(self):
        for i in range(len(self._SYNC_INFO['paths'])):
            self.state('paths',i,1)
            sp_msg = "|-迁移自定义目录: [{}]".format(self._SYNC_INFO['paths'][i]['path'])
            self.write_speed('action',sp_msg)
            write_log(sp_msg)
            if not self._SYNC_INFO['paths'][i]['path'] in self._TO_PATHS:
                self.send(self._SYNC_INFO['paths'][i]['path'],self._SYNC_INFO['paths'][i]['to_path'])
            write_log("="*50)
            self.state('paths',i,2)

    #迁移站点
    def sync_site(self):
        self._API.send_panel('/firewall?action=AddAcceptPort',{"port":'443',"type":"port","ps":"HTTPS"},30)
        for i in range(len(self._SYNC_INFO['sites'])):
            try:
                self.state('sites',i,1)
                site = self._SYNC_INFO['sites'][i]
                sp_msg = "|-迁移网站: [{}]".format(site['name'])
                self.write_speed('action',sp_msg)
                write_log(sp_msg)
                id = site['id']
                siteInfo = public.M('sites').where('id=?',(id,)).field('id,name,path,ps,status,edate,addtime').find()
                if not siteInfo:
                    err_msg = "指定站点[{}]不存在!".format(site['name'])
                    self.state('sites',i,-1,err_msg)
                    self.error(err_msg)
                    continue

                siteInfo['port'] = public.M('domain').where('pid=? and name=?',(id,site['name'])).getField('port')
                if not siteInfo['port']: siteInfo['port'] = 80
                siteInfo['domain'] = public.M('domain').where('pid=? and name!=?',(id,site['name'])).field('name,port').select()
                siteInfo['binding'] = public.M('binding').where('pid=?',(id,)).field('domain,path,port').select()
                siteInfo['redirect'] = self.get_redirect(siteInfo['name'])
                siteInfo['proxy'] = self.get_proxy(siteInfo['name'])
                siteInfo['dir_auth'] = self.get_dir_auth(siteInfo['name'])
                if self.send_site(siteInfo,i): self.state('sites',i,2)
                write_log("="*50)
            except:
                self.error(public.get_error_info())

    #发送站点文件
    def send_site(self,siteInfo,index):
        if not os.path.exists(siteInfo['path']):
            err_msg = "网站根目录[{}]不存在,跳过!".format(siteInfo['path'])
            self.state('sites',index,-1,err_msg)
            self.error(err_msg)
            return False
        if not self.create_site(siteInfo,index): return False

        #准备文件和目录路径
        s_files = [
            [self._VHOST_PATH + '/nginx/{}.conf'.format(siteInfo['name']),"网站配置文件"],
            [self._VHOST_PATH + '/apache/{}.conf'.format(siteInfo['name']),"网站配置文件"],
            [self._VHOST_PATH + '/cert/{}'.format(siteInfo['name']),"网站SSL证书"],
            [self._VHOST_PATH + '/ssl/{}'.format(siteInfo['name']),"相关的证书夹"],
            [self._VHOST_PATH + '/rewrite/{}.conf'.format(siteInfo['name']),"伪静态配置"],
            [self._VHOST_PATH + '/nginx/redirect/{}'.format(siteInfo['name']),"重定向配置"],
            [self._VHOST_PATH + '/nginx/proxy/{}'.format(siteInfo['name']),"反向代理配置"],
            [self._VHOST_PATH + '/nginx/dir_auth/{}'.format(siteInfo['name']),"目录保护配置"],
            [self._VHOST_PATH + '/apache/redirect/{}'.format(siteInfo['name']),"重定向配置"],
            [self._VHOST_PATH + '/apache/proxy/{}'.format(siteInfo['name']),"反向代理配置"],
            [self._VHOST_PATH + '/apache/dir_auth/{}'.format(siteInfo['name']),"目录保护配置"],
            ["/etc/letsencrypt/live/{}".format(siteInfo['name']),"网站SSL证书"]
            ]

        #处理日志路径
        nginx_conf = self._VHOST_PATH + '/nginx/{}.conf'.format(siteInfo['name'])
        httpd_conf = self._VHOST_PATH + '/apache/{}.conf'.format(siteInfo['name'])
        tmp = None
        if os.path.exists(nginx_conf):
            ng_config = public.readFile(httpd_conf)
            if ng_config:
                tmp = re.findall(r'access_log\s+(.{10,128});',ng_config)

        if os.path.exists(httpd_conf):
            httpd_config = public.readFile(httpd_conf)
            if httpd_config:
                tmp = re.findall(r'ErrorLog\s+"(.+)"',httpd_config)

        if tmp:
            log_path = os.path.dirname(tmp[0])
            if log_path != '/www/wwwlogs':
                self._API.send_panel('/files?action=CreateDir',{"path":log_path})

        #删除默认创建的index.html
        self._API.send_panel('/files?action=DeleteFile',{"path":siteInfo['path'] + '/index.html'})

        #子目录绑定伪静态
        for bind in siteInfo['binding']:
            filename = self._VHOST_PATH + '/rewrite/{}_{}.conf'.format(siteInfo['name'],bind['path'])
            if os.path.exists(filename): s_files.append([filename,"子目录绑定配置"])

        #发送文件列表
        self.send_list(s_files)

        #发送反向代理/重定向/目录保护配置列表
        self.send_proxy_redirect_dir_auth(siteInfo)

        #重载nginx/httpd
        self._API.send_panel('/system?action=ServiceAdmin',{"name":self._get_stype(),"type":"reload"})

        #迁移网站文件
        if not siteInfo['path'] in self._TO_PATHS:
            self._TO_PATHS.append(siteInfo['path'])
            if not self.send(siteInfo['path'],siteInfo['path']):
                self.state('sites',index,-1,'数据传输失败!')
                return False
        return True

    #迁移反向代理/重定向/目录保护配置列表
    def send_proxy_redirect_dir_auth(self,siteInfo):
        if siteInfo['redirect']:
            fname = "/www/server/panel/data/redirect.conf"
            result = self._API.send_panel('/files?action=GetFileBody',{"path":fname})
            if result['status']:
                data = json.loads(result['data'])
                if not data: data = []
                for n in siteInfo['redirect']:
                    data.append(n)
                result = self._API.send_panel('/files?action=SaveFileBody',{"path":fname,"data":json.dumps(data),"encoding":"utf-8"})

        if siteInfo['proxy']:
            fname = "/www/server/panel/data/proxyfile.json"
            result = self._API.send_panel('/files?action=GetFileBody',{"path":fname})
            if result['status']:
                data = json.loads(result['data'])
                if not data: data = []
                for n in siteInfo['proxy']:
                    data.append(n)
                result = self._API.send_panel('/files?action=SaveFileBody',{"path":fname,"data":json.dumps(data),"encoding":"utf-8"})

        if siteInfo['dir_auth']:
            fname = "/www/server/panel/data/site_dir_auth.json"
            result = self._API.send_panel('/files?action=GetFileBody',{"path":fname})
            if result['status']:
                data = json.loads(result['data'])
                if not data: data = {}
                data[siteInfo['name']] = siteInfo['dir_auth']
                result = self._API.send_panel('/files?action=SaveFileBody',{"path":fname,"data":json.dumps(data),"encoding":"utf-8"})

    #发送文件列表
    def send_list(self,s_files):
        for f in s_files:
            if not os.path.exists(f[0]): continue
            self.send(f[0],f[0],True)

    #获取web服务器类型
    def _get_stype(self):
        webserver = ''
        if os.path.exists('/www/server/nginx/sbin/nginx'): webserver = 'nginx'
        elif os.path.exists('/www/server/apache/bin/httpd'): webserver = 'httpd'
        elif os.path.exists('/usr/local/lsws/bin/lswsctrl'): webserver = 'lswsctrl'
        return webserver


    #创建远程站点
    def create_site(self,siteInfo,index):
        self.write_speed('done','正在创建站点配置')
        pdata = {}
        domains = self.format_domain(siteInfo['domain'])
        pdata['webname'] = json.dumps({"domain":siteInfo['name'],"domainlist":domains,"count":len(domains)})
        pdata['ps'] = siteInfo['ps']
        pdata['path'] = siteInfo['path']
        pdata['ftp'] = 'false'
        pdata['sql'] = 'false'
        pdata['codeing'] = 'utf-8'
        pdata['type'] = 'PHP'
        pdata['version'] = '00'
        pdata['type_id'] = '0'
        pdata['port'] = siteInfo['port']
        if not pdata['port']: pdata['port'] = 80

        result = self._API.send_panel('/site?action=AddSite',pdata)
        if not 'siteStatus' in result:
            err_msg = '站点[{}]创建失败, {}'.format(siteInfo['name'],result['msg'])
            self.state('sites',index,-1,err_msg)
            self.error(err_msg)
            return False
        if not result['siteStatus']:
            err_msg = '站点[{}]创建失败!'.format(siteInfo['name'])
            self.state('sites',index,-1,err_msg)
            self.error(err_msg)
            return False
        id = result['siteId']
        #修改到期时间
        if siteInfo['edate'] != '0000-00-00':
            self._API.send_panel('/site?action=SetEdate',{"id":id,"edate":siteInfo['edate']})
        #修改站点状态
        if siteInfo['status'] == '0':
            self._API.send_panel('/site?action=SiteStop',{"id":id,"name":siteInfo['name']})

        #设置子目录绑定
        if siteInfo['binding']:
            for binding in siteInfo['binding']:
                self._API.send_panel('/files?action=CreateDir',{"path":siteInfo['path'] + '/' + binding['path']})
                self._API.send_panel('/site?action=AddDirBinding',{"dirName":binding['path'],"domain":binding['domain'],"id":id})

        #设置301重定向
        if siteInfo['redirect']:
            for red_info in siteInfo['redirect']:
                self._API.send_panel('/site?action=CreateRedirect',red_info)
        return True

    #格式化域名
    def format_domain(self,domain):
        domains = []
        for d in domain:
            domains.append("{}:{}".format(d['name'],d['port']))
        return domains

    #取指定站点的重定向信息
    def get_redirect(self,siteName):
        try:
            r_file = '/www/server/panel/data/redirect.conf'
            if not os.path.exists(r_file): return []
            result = []
            r_data = json.loads(public.readFile(r_file))
            for s in r_data:
                if s['sitename'] == siteName: result.append(s)
            return result
        except: return []

    #取指定站点的反代配置信息
    def get_proxy(self,siteName):
        try:
            r_file = '/www/server/panel/data/proxyfile.json'
            if not os.path.exists(r_file): return []
            result = []
            r_data = json.loads(public.readFile(r_file))
            for s in r_data:
                if s['sitename'] == siteName: result.append(s)
            return result
        except: return []

    #取指定站点目录保护配置信息
    def get_dir_auth(self,siteName):
        try:
            r_file = '/www/server/panel/data/site_dir_auth.json'
            if not os.path.exists(r_file): return {}
            r_data = json.loads(public.readFile(r_file))
            if not r_data: return {}
            if siteName in r_data: return r_data[siteName]
            return {}
        except: return {}

    #迁移数据库
    def sync_database(self):
        for i in range(len(self._SYNC_INFO['databases'])):
            try:
                self.state('databases',i,1)
                db = self._SYNC_INFO['databases'][i]
                sp_msg = "|-迁移数据库: [{}]".format(db['name'])
                self.write_speed('action',sp_msg)
                write_log(sp_msg)
                id = db['id']
                dbInfo = public.M('databases').where('id=?',(id,)).field('id,name,username,password,ps').find()
                dbInfo['accept'] = self.GetDatabaseAccess(dbInfo['name'])
                dbInfo['character'] = self.get_database_character(dbInfo['name'])
                if self.send_database(dbInfo,i): self.state('databases',i,2)
                write_log("="*50)
            except:
                self.error(public.get_error_info())

    #取数据库字符集
    def get_database_character(self,db_name):
        try:
            import panelMysql
            tmp = panelMysql.panelMysql().query("show create database `%s`" % db_name.strip())
            c_type = str(re.findall(r"SET\s+([\w\d-]+)\s",tmp[0][1])[0])
            c_types = ['utf8','utf-8','gbk','big5','utf8mb4']
            if not c_type.lower() in c_types: return 'utf8'
            return c_type
        except:
            return 'utf8'
    #发送数据库
    def send_database(self,dbInfo,index):
        #创建远程库
        if not self.create_database(dbInfo,index): return False
        #导出
        filename = self.export_database(dbInfo['name'],index)
        if not filename: return False
        upload_file = '/www/backup/database/psync_import_{}.sql.gz'.format(dbInfo['name'])
        self._API.send_panel('/files?action=ExecShell',{"shell": "rm -f "+upload_file,"path":"/www"},30)
        #上传
        if self.send(filename,upload_file):
            #导入
            self.write_speed('done','正在导入数据库')
            write_log("|-正在导入数据库{}...".format(dbInfo['name']))
            self._API.send_panel('/database?action=InputSql',{"name":dbInfo['name'],"file":upload_file},7300)
            self._API.send_panel('/files?action=ExecShell',{"shell": "rm -f "+upload_file,"path":"/www"},30)
            return True
        self.state('databases',index,-1,"数据传输失败")
        return False

    #创建远程数据库
    def create_database(self,dbInfo,index):
        pdata = {}
        pdata['name'] = dbInfo['name']
        pdata['db_user'] = dbInfo['username']
        pdata['password'] = dbInfo['password']
        pdata['dtype'] = 'MySQL'
        pdata['dataAccess'] = dbInfo['accept']
        if dbInfo['accept'] != '%' and dbInfo['accept'] != '127.0.0.1':
            pdata['dataAccess'] = 'ip'
        pdata['address'] = dbInfo['accept']
        pdata['ps'] = dbInfo['ps']
        pdata['codeing'] = dbInfo['character']
        result = self._API.send_panel('/database?action=AddDatabase',pdata)

        if result['status']: return True
        err_msg = '数据库[{}]创建失败,{}'.format(dbInfo['name'],result['msg'])
        self.state('databases',index,-1,err_msg)
        self.error(err_msg)
        return False


    #检测数据库执行错误
    def IsSqlError(self,mysqlMsg):
        mysqlMsg=str(mysqlMsg)
        if "MySQLdb" in mysqlMsg: return public.returnMsg(False,'DATABASE_ERR_MYSQLDB')
        if "2002," in mysqlMsg or '2003,' in mysqlMsg: return public.returnMsg(False,'DATABASE_ERR_CONNECT')
        if "using password:" in mysqlMsg: return public.returnMsg(False,'DATABASE_ERR_PASS')
        if "Connection refused" in mysqlMsg: return public.returnMsg(False,'DATABASE_ERR_CONNECT')
        if "1133" in mysqlMsg: return public.returnMsg(False,'DATABASE_ERR_NOT_EXISTS')
        return None

    #map to list
    def map_to_list(self,map_obj):
        try:
            if type(map_obj) != list and type(map_obj) != str: map_obj = list(map_obj)
            return map_obj
        except: return []

    #取数据库权限
    def GetDatabaseAccess(self,name):
        try:
            users = panelMysql.panelMysql().query("select Host from mysql.user where User='" + name + "' AND Host!='localhost'")
            users = self.map_to_list(users)

            if len(users)<1:
                return "127.0.0.1"

            accs = []
            for c in users:
                accs.append(c[0])
            userStr = ','.join(accs)
            return userStr
        except:
            return '127.0.0.1'

    #数据库密码处理
    def mypass(self,act,root):
        conf_file = '/etc/my.cnf'
        public.ExecShell("sed -i '/user=root/d' {}".format(conf_file))
        public.ExecShell("sed -i '/password=/d' {}".format(conf_file))
        if act:
            mycnf = public.readFile(conf_file)
            src_dump = "[mysqldump]\n"
            sub_dump = src_dump + "user=root\npassword=\"{}\"\n".format(root)
            if not mycnf: return False
            mycnf = mycnf.replace(src_dump,sub_dump)
            if len(mycnf) > 100: public.writeFile(conf_file,mycnf)
            return True
        return True

    #导出数据库
    def export_database(self,name,index):
        self.write_speed('done','正在导出数据库')
        write_log("|-正在导出数据库{}...".format(name)),
        import panelMysql
        result = panelMysql.panelMysql().execute("show databases")
        isError=self.IsSqlError(result)
        if isError:
            err_msg = '数据库[{}]导出失败,{}!'.format(name,isError['msg'])
            self.state('databases',index,-1,err_msg)
            self.error(err_msg)
            return None

        root = public.M('config').where('id=?',(1,)).getField('mysql_root')
        backup_path = self._PLUGIN_PATH + '/backup'
        if not os.path.exists(backup_path): os.makedirs(backup_path,384)
        self.mypass(True, root)
        backup_name = backup_path + '/psync_import.sql.gz'
        if os.path.exists(backup_name): os.remove(backup_name)
        public.ExecShell("/www/server/mysql/bin/mysqldump --default-character-set="+ public.get_database_character(name) +" --force --opt \"" + name + "\" | gzip > " + backup_name)
        self.mypass(False, root)
        if not os.path.exists(backup_name) or os.path.getsize(backup_name) < 30:
            if os.path.exists(backup_name): os.remove(backup_name)
            err_msg = '数据库[{}]导出失败!'.format(name)
            self.state('databases',index,-1,err_msg)
            self.error(err_msg)
            write_log("失败")
            return None
        write_log("成功")
        return backup_name

    #迁移FTP
    def sync_ftp(self):
        for i in range(len(self._SYNC_INFO['ftps'])):
            try:
                self.state('ftps',i,1)
                db = self._SYNC_INFO['ftps'][i]
                sp_msg = "|-迁移FTP: [{}]..".format(db['name'])
                self.write_speed('action',sp_msg)
                write_log(sp_msg)
                id = db['id']
                ftpInfo = public.M('ftps').where('id=?',(id,)).field('id,name,password,path,status,ps').find()
                if self.send_ftp(ftpInfo,i): self.state('ftps',i,2)
                write_log("="*50)
            except:
                self.error(public.get_error_info())

    #发送FTP
    def send_ftp(self,ftpInfo,index):
        if not os.path.exists(ftpInfo['path']):
            self.state('ftps',index,-1,'指定FTP目录不存在{}!'.format(ftpInfo['path']))
            return False
        if not self.create_ftp(ftpInfo,index): return False
        if not ftpInfo['path'] in self._TO_PATHS:
            self._TO_PATHS.append(ftpInfo['path'])
            if not self.send(ftpInfo['path'],ftpInfo['path']):
                self.state('ftps',index,-1,'数据传输失败!')
                return False
        return True

    #创建远程FTP
    def create_ftp(self,ftpInfo,index):
        pdata = {}
        pdata['ftp_username'] = ftpInfo['name']
        pdata['ftp_password'] = ftpInfo['password']
        pdata['path'] = ftpInfo['path']
        pdata['ps'] = ftpInfo['ps']

        result = self._API.send_panel('/ftp?action=AddUser',pdata)
        if not result['status']:
            err_msg = 'FTP帐户[{}]创建失败, {}'.format(ftpInfo['name'],result['msg'])
            self.state('ftps',index,-1,err_msg)
            self.error(err_msg)
            return False
        #判断是否需要设置FTP状态
        if ftpInfo['status'] != '1':
            #获取当前FTP标识
            result = self._API.send_panel('/data?action=getData',{"table":"ftps","limit":1,"p":1,"order":"id desc"})
            if 'data' in result:
                if len(result['data']) > 0:
                    #设置FTP状态
                    id = result['data'][0]['id']
                    self._API.send_panel('/ftp?action=SetStatus',{"id":id,"username":ftpInfo['name'],"status":'0'})
        return True

    #迁移其它
    def sync_other(self):
        sp_msg = "|-正在迁移前置配置..."
        self.write_speed('action',sp_msg)
        self.write_speed('done','正在传输文件')
        write_log(sp_msg)
        write_log("="*50)
        s_files = [
            ["/www/server/pass","密码文件"],
            ["/www/server/vhost/letsencrypt","lets证书"],
            ["/www/server/panel/config/letsencrypt.json","lets帐户信息"]
            ]
        self.send_list(s_files)
        write_log("="*50)

    #设置文件权限
    def set_mode(self,filename,mode):
        if not os.path.exists(filename): return False
        mode = int(str(mode),8)
        os.chmod(filename,mode)
        return True


    #发送文件
    def send(self,spath,dpath,force = False):
        if not os.path.isdir(spath):
            return self._API.upload_file(spath,dpath,True)

        #创建目录
        self._API.send_panel('/files?action=CreateDir',{"path":dpath})

        #是否压缩目录后上传
        if self._SYNC_INFO['zip'] and not force:
            backup_path = self._PLUGIN_PATH + '/backup'
            if not os.path.exists(backup_path): os.makedirs(backup_path,384)
            zip_file = backup_path + "/psync_tmp_{}.tar.gz".format(os.path.basename(spath))
            zip_dst = '/www/server/panel/temp/psync_tmp_{}.tar.gz'.format(os.path.basename(dpath))
            write_log("|-正在压缩目录[{}]...".format(spath))
            self.write_speed('done','正在压缩')
            public.ExecShell("cd {} && tar zcvf {} ./ > /dev/null".format(spath,zip_file))
            if not os.path.exists(zip_file):
                self.error("目录[{}]打包失败!".format(spath))
                return False
            self.set_mode(zip_file,600)
            if not self._API.upload_file(zip_file,zip_dst,True):
                self.error("目录[{}]上传失败!".format(spath))
                if os.path.exists(zip_file): os.remove(zip_file)
                return False

            if os.path.exists(zip_file): os.remove(zip_file)
            write_log("|-正在解压文件到目录[{}]...".format(dpath))
            self.write_speed('done','正在解压')
            self._API.send_panel('/files?action=UnZip',{"sfile":zip_dst,"dfile":dpath,"type":"tar","coding":"UTF-8","password":"undefined"})
            n = 0
            while True:
                time.sleep(3)
                result = self._API.send_panel('/task?action=get_task_lists',{"status":'-1'})
                if not result or n > 20: break
                n+=1

            self._API.send_panel('/files?action=ExecShell',{"shell": "rm -f "+zip_dst,"path":"/www"},30)
            return True


        #遍历上传
        for name in os.listdir(spath):
            sfile = os.path.join(spath,name)
            dfile = os.path.join(dpath,name)
            self.send(sfile,dfile)
        return True

    #写进度
    def write_speed(self,key,value):
        if os.path.exists(self._SPEED_FILE):
            try:
                speed_info = json.loads(public.readFile(self._SPEED_FILE))
            except:
                speed_info = {"time":int(time.time()),"size":0,"used":0,"total_size":0,"speed":0,"action":"等待中","done":"等待中","end_time":int(time.time())}
        else:
            speed_info = {"time":int(time.time()),"size":0,"used":0,"total_size":0,"speed":0,"action":"等待中","done":"等待中","end_time":int(time.time())}
        if not key in speed_info: speed_info[key] = 0
        if key == 'total_size':
            speed_info[key] += value
        else:
            speed_info[key] = value
        public.writeFile(self._SPEED_FILE,json.dumps(speed_info))




class panel_api:
    __BT_KEY = None
    __BT_PANEL = None
    _REQUESTS = None
    _PLUGIN_PATH = "/www/server/panel/plugin/psync_api"
    _SPEED_FILE = _PLUGIN_PATH + '/config/speed.json'
    _buff_size = 1024 * 1024 * 2

    #如果希望多台面板, 可以在实例化对象时, 将面板地址与密钥传入
    def __init__(self,api_info = None):
        if api_info:
            self.__BT_PANEL = api_info['panel']
            self.__BT_KEY = api_info['token']
        import requests
        if not self._REQUESTS:
            self._REQUESTS = requests.session()

    #计算MD5
    def __get_md5(self,s):
        m = hashlib.md5()
        m.update(s.encode('utf-8'))
        return m.hexdigest()

    #构造带有签名的关联数组
    def __get_key_data(self):
        now_time = int(time.time())
        p_data = {
                    'request_token':self.__get_md5(str(now_time) + '' + self.__get_md5(self.__BT_KEY)),
                    'request_time':now_time
                 }
        return p_data


    #发送POST请求并保存Cookie
    #@url 被请求的URL地址(必需)
    #@data POST参数, 可以是字符串或字典(必需)
    #@timeout 超时时间默认1800秒
    #return string
    def __http_post_cookie(self,url,p_data,timeout=1800):
        try:
            res = self._REQUESTS.post(url,p_data,timeout= timeout)
            return res.text
        except Exception as ex:
            ex = str(ex)
            if ex.find('Max retries exceeded with') != -1:
                return public.returnJson(False,'连接服务器失败!')
            if ex.find('Read timed out') != -1 or ex.find('Connection aborted') != -1:
                return public.returnJson(False,'连接超时!')
            return public.returnJson(False,'连接服务器失败!')

    #上传文件
    def upload_file(self,sfile,dfile,chmod = None):
        if not os.path.exists(sfile):
            write_log("|-指定目录不存在{}".format(sfile))
            return False
        pdata = self.__get_key_data()
        pdata['f_name'] = os.path.basename(dfile)
        pdata['f_path'] = os.path.dirname(dfile)
        pdata['f_size'] = os.path.getsize(sfile)
        pdata['f_start'] = 0
        if chmod:
            mode_user = self.get_mode_and_user(os.path.dirname(sfile))
            pdata['dir_mode'] = mode_user['mode'] + ',' + mode_user['user']
            mode_user = self.get_mode_and_user(sfile)
            pdata['file_mode'] = mode_user['mode'] + ',' + mode_user['user']
        f = open(sfile,'rb')
        return self.send_file(pdata,f)

    #发送文件
    def send_file(self,pdata,f):
        success_num = 0 #连续发送成功次数
        max_buff_size = int(1024 * 1024 * 2)  #最大分片大小
        min_buff_size = int(1024 * 32) #最小分片大小
        err_num = 0 #连接错误计数
        max_err_num = 10 #最大连接错误重试次数
        up_buff_num = 5 #调整分片的触发次数
        timeout = 60 #每次发送分片的超时时间
        split_num = 0
        split_done = 0
        total_time = 0
        self.write_speed('done',"正在传输文件")
        self.write_speed('size',pdata['f_size'])
        self.write_speed('used',0)
        self.write_speed('speed',0)
        write_log("|-上传文件[{}], 总大小：{}, 当前分片大小为：{}".format(pdata['f_name'],to_size(pdata['f_size']),to_size(self._buff_size)))
        while True:
            buff_size = self._buff_size
            max_buff = int(pdata['f_size'] - pdata['f_start'])
            if max_buff < buff_size: buff_size = max_buff #判断是否到文件尾
            files = {"blob":f.read(buff_size)}
            start_time = time.time()
            try:
                res = self._REQUESTS.post(self.__BT_PANEL + '/files?action=upload',data=pdata,files=files,timeout=timeout)
                success_num +=1
                err_num = 0
                #连续5次分片发送成功的情况下尝试调整分片大小, 以提升上传效率
                if success_num > up_buff_num and self._buff_size <  max_buff_size:
                    self._buff_size = int(self._buff_size * 2)
                    success_num = up_buff_num - 3 #如再顺利发送3次则继续提升分片大小
                    if self._buff_size > max_buff_size: self._buff_size = max_buff_size
                    write_log("|-发送顺利, 尝试调整分片大小为: {}".format(to_size(self._buff_size)))
            except Exception as ex:
                times = time.time() - start_time
                total_time += times
                ex = str(ex)
                if ex.find('Read timed out') != -1 or ex.find('Connection aborted') != -1:
                    #发生超时的时候尝试调整分片大小, 以确保网络情况不好的时候能继续上传
                    self._buff_size = int(self._buff_size / 2)
                    if self._buff_size < min_buff_size: self._buff_size = min_buff_size
                    success_num = 0
                    write_log("|-发送超时, 尝试调整分片大小为: {}".format(to_size(self._buff_size)))
                    continue

                #如果连接超时
                if ex.find('Max retries exceeded with') != -1 and err_num <= max_err_num:
                    err_num +=1
                    write_log("|-连接超时, 第{}次重试".format(err_num))
                    time.sleep(1)
                    continue

                #超过重试次数
                write_log("|-上传失败, 跳过本次上传任务")
                write_log(public.get_error_info())
                return False

            result = res.json()
            times = time.time() - start_time
            total_time += times
            if type(result) == int:
                if result == split_done:
                    split_num += 1
                else:
                    split_num = 0
                split_done = result
                if split_num > 10:
                    write_log("|-上传失败, 跳过本次上传任务")
                    return False
                if result > pdata['f_size']:
                    write_log("|-上传失败, 跳过本次上传任务")
                    return False
                self.write_speed('used',result)
                self.write_speed('speed',int(buff_size/times))
                write_log("|-已上传 {},上传速度 {}/s, 共用时 {}分{:.2f}秒,  {:.2f}%".format(to_size(float(result)), to_size(buff_size/times),int(total_time // 60),total_time % 60,(float(result) / float(pdata['f_size']) * 100)))
                pdata['f_start'] = result #设置断点
            else:
                if not result['status']:  #如果服务器响应上传失败
                    write_log(result['msg'])
                    return False

                if pdata['f_size']:
                    self.write_speed('used',pdata['f_size'])
                    self.write_speed('speed',int(buff_size/times))
                    write_log("|-已上传 {},上传速度 {}/s, 共用时 {}分{:.2f}秒,  {:.2f}%".format(to_size(float(pdata['f_size'])), to_size(buff_size/times),int(total_time // 60),total_time % 60,(float(pdata['f_size']) / float(pdata['f_size']) * 100)))
                break
        self.write_speed('total_size',pdata['f_size'])
        self.write_speed('end_time',int(time.time()))
        write_log("|-总耗时：{} 分钟, {:.2f} 秒, 平均速度：{}/s".format(int(total_time // 60), total_time % 60,to_size(pdata['f_size']/total_time)))
        return True

    #写进度
    def write_speed(self,key,value):
        if os.path.exists(self._SPEED_FILE):
            speed_info = json.loads(public.readFile(self._SPEED_FILE))
        else:
            speed_info = {"time":int(time.time()),"size":0,"used":0,"total_size":0,"speed":0,"action":"等待中","done":"等待中","end_time":int(time.time())}
        if not key in speed_info: speed_info[key] = 0
        if key == 'total_size':
            speed_info[key] += value
        else:
            speed_info[key] = value
        public.writeFile(self._SPEED_FILE,json.dumps(speed_info))


    #发送请求到面板
    def send_panel(self,uri,data,timeout = 360):
        pdata = self.__get_key_data()
        data['request_token'] = pdata['request_token']
        data['request_time'] = pdata['request_time']
        result = self.__http_post_cookie(self.__BT_PANEL + '/' + uri,data,timeout)
        try:
            result = json.loads(result)
            return result
        except:
            return result

    def get_mode_and_user(self,path):
        '''取文件或目录权限信息'''
        data = {}
        if not os.path.exists(path): return None
        stat = os.stat(path)
        data['mode'] = str(oct(stat.st_mode)[-3:])
        try:
            data['user'] = pwd.getpwuid(stat.st_uid).pw_name
        except:
            data['user'] = str(stat.st_uid)
        return data



f = None
def write_log(log_str):
    log_file = '/www/server/panel/logs/psync.log'
    f = open(log_file,'ab+')
    log_str += "\n"
    f.write(log_str.encode('utf-8'))
    f.close()
    return True

#字节单位转换
def to_size(size):
    d = ('b','KB','MB','GB','TB')
    s = d[0]
    for b in d:
        if size < 1024: return ("%.2f" % size) + ' ' + b
        size = size / 1024
        s = b
    return ("%.2f" % size) + ' ' + b

#格式化指定时间戳
def format_date(format="%Y-%m-%d %H:%M:%S",times = None):
    if not times: times = int(time.time())
    time_local = time.localtime(times)
    return time.strftime(format, time_local)

if __name__ == '__main__':
    p = psync()
    p.run()