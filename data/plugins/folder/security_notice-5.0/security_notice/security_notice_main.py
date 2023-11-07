#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: lkq <lkq@qq.com>
#-------------------------------------------------------------------
# 宝塔php安全告警
#------------------------------

import os,time,sys
os.chdir('/www/server/panel')
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import public,re,json,db
from cachelib import SimpleCache


'''
    统计目录: plugin/security_notice/total/   
        总的统计文件 plugin/security_notice/total/total.json
        网站的统计文件:  plugin/security_notice/total/域名/total.json
        网站每天的文件：plugin/security_notice/total/域名/2023-02-13.json
    日志文件:
        plugin/security_notice/logs/
        网站日志文件：plugin/security_notice/logs/域名/2023-02-13.json
'''

class security_notice_main:
    __cache= SimpleCache(50000)
    __plugin_path = "/www/server/panel/plugin/security_notice/"
    __overall_path = __plugin_path + 'overall.json'
    __plugin_pid=__plugin_path+'security_notice.pid'
    __install_day = __plugin_path + 'install_date.pl'
    __php_path = "/www/server/php/"
    __log_name = 'PHP安全告警'
    __config = []
    __vhost_path = 'vhost/nginx/'
    __disable_php = ['52','00',None]
    __total_path = "plugin/security_notice/total/"
    __logs_path='plugin/security_notice/logs/'
    __overall_config={'ip_white':[],'url_white':[]}
    Recycle_bin = __plugin_path + 'Recycle_bin'

    plugin_path = "plugin/security_notice/"
    overall_path = plugin_path + 'overall.json'
    total_path = "plugin/security_notice/total/"
    logs_path = 'plugin/security_notice/logs/'
    __sql = None  # 监控数据库连接
    __php_ini_data = {
        "52":"",
        "53":"",
        "54":"",
        "55":"",
        "56":"",
        "70":"",
        "71":"",
        "72":"",
        "73":"",
        "74":"",
        "80":"",
        "81":"",
    }
    #构造方法
    def  __init__(self):
        self.__sql = db.Sql().dbfile("notice")  # 初始化数据库
        # 监控网站的表
        if not self.__sql.table('sqlite_master').where('type=? AND name=?', ('table', 'security_notice')).count():
            msql = '''CREATE TABLE IF NOT EXISTS `security_notice` (
                           `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                           `fun_name` varchar(30),
                           `domain` varchar(30),
                           `address` varchar(128) ,
                           `url` TEXT,
                           `intercept` TEXT,
                           `solution` TEXT,
                           `data_info` TEXT,
                           `risk` INTEGER,
                           `status` INTEGER,
                            `addtime` INTEGER
                           )'''
            self.__sql.execute(msql)
            self.__sql.execute('CREATE INDEX security_notice_domain ON security_notice (domain);', ())
            self.__sql.execute('CREATE INDEX security_notice_status ON security_notice (status);', ())
        if not os.path.exists(self.__install_day):
            public.writeFile(self.__install_day,str(int(time.time())))
        if not os.path.exists(self.__total_path):
            public.ExecShell("mkdir -p /www/server/panel/plugin/security_notice/total")
        if not os.path.exists(self.__logs_path):
            public.ExecShell("mkdir -p /www/server/panel/plugin/security_notice/logs")

    #查看告警
    def get_send_config2(self, get):
        send_type = "error"
        login_send_type_conf = "/www/server/panel/data/security_notice_send.pl"
        if os.path.exists(login_send_type_conf):
            send_type = public.ReadFile(login_send_type_conf).strip()
        if send_type == "error":
            return send_type
        return True


    #查看告警
    def get_send_config(self, get):
        send_type = "error"
        login_send_type_conf = "/www/server/panel/data/security_notice_send.pl"
        if os.path.exists(login_send_type_conf):
            send_type = public.ReadFile(login_send_type_conf).strip()
        if send_type == "error":
            return public.returnMsg(False, send_type)
        return public.returnMsg(True, send_type)

    def set_send(self,get):
        login_send_type_conf = "/www/server/panel/data/security_notice_send.pl"
        set_type=get.type.strip()
        if set_type=="error":
            if os.path.exists(login_send_type_conf):
                os.remove(login_send_type_conf)
            return public.returnMsg(True, '关闭成功')
        import config
        config=config.config()
        msg_configs = config.get_msg_configs(get)
        if set_type not in msg_configs.keys():
            return public.returnMsg(False,'不支持该发送类型')
        _conf = msg_configs[set_type]
        if "data" not in _conf or not _conf["data"]:
            return public.returnMsg(False, "该通道未配置, 请重新选择。")
        from panelMessage import panelMessage
        pm = panelMessage()
        obj = pm.init_msg_module(set_type)
        if not obj:
            return public.returnMsg(False, "消息通道未安装。")

        public.writeFile(login_send_type_conf, set_type)
        return public.returnMsg(True, '设置成功')

    def get_status(self,get):
        '''
            @name 获取服务状态
            @author lkq@bt.cn
            @time 2023.02.13
        '''
        result={}
        result['status']=False
        result['send']=False
        result['php_status']=False
        try:
            if not os.path.exists(self.__plugin_pid):
                result['status'] = False
            else:
                pid = int(public.readFile(self.__plugin_pid))
                if os.path.exists('/proc/{}/comm'.format(pid)):
                    result['status'] = True
                    if not os.path.exists("/www/server/panel/plugin/security_notice/check_status.pl"):
                        public.writeFile("/www/server/panel/plugin/security_notice/check_status.pl", "")
            is_send = self.get_send_config2(get)
            if is_send and is_send!="error":
                result['send'] = True
            if is_send and is_send=="error":
                result['send'] = True

            get_php_versions=self.get_php_versions(True)
            for i in get_php_versions:
                if i['state']==1:
                    result['php_status']=True
                    break
            return result


        except:
            return result
    def check_php(self,php_version):
        if not php_version in ["53","54","55","56","70","71","72","73","74","80","81"]:return False
        php_path = os.path.join(self.__php_path, php_version)
        php_ini = os.path.join(php_path, 'etc/php.ini')
        if not os.path.exists(php_ini): return False
        filter_so = self.get_filter_so(php_version)
        if not filter_so: return False
        php_v = public.readFile(os.path.join(php_path, 'version_check.pl'))
        if not php_v:
            php_v = php_version

        php_info = {
            "version": php_v,
            "v": php_version
        }

        # 判断是否安装
        if not os.path.exists(filter_so):
            return False
        else:
            # 是否加载
            php_ini_conf = public.readFile(php_ini)
            php_info['state'] = 1
            if php_ini_conf.find('security_notice.so') == -1:
                return False
            if re.search(r";\s*extension\s*=\s*security_notice.so", php_ini_conf):
                return False
        return True


    def start_site(self,get):
        '''
            @name 开启网站
            @author lkq@bt.cn
            @time 2023.02.13
        '''
        sitename=get.siteName
        sites = self.get_config(force=True)
        for i in range(len(sites)):
            if sites[i]['site_name']==sitename:
                if not self.check_php(sites[i]['version']):
                    return public.returnMsg(False, '指定站点使用的PHP版本未在【PHP设置】中开启防护模块，无法设置该站点!')
                sites[i]['open']=True
                sites[i]['is_stop']=0
        self.__config=sites
        self.__set_config()
        return public.returnMsg(True, '开启成功')


    def stop_site(self,get):
        '''
            @name 开启网站
            @author lkq@bt.cn
            @time 2023.02.13
        '''
        sitename=get.siteName
        sites = self.get_config(force=True)
        for i in range(len(sites)):
            if sites[i]['site_name']==sitename:
                if not self.check_php(sites[i]['version']):
                    return public.returnMsg(False, '指定站点使用的PHP版本未在【PHP设置】中开启防护模块，无法设置该站点!')
                sites[i]['open']=False
                sites[i]['is_stop']=1
        self.__config=sites
        self.__set_config()
        return public.returnMsg(True, '关闭成功')

    def start_service(self,get):
        '''
            @name 开启服务
            @author lkq@bt.cn
            @time 2023.02.13
        '''
        is_send=self.get_send_config(get)
        if is_send=='error':
            return public.returnMsg(False, '未设置异常告警,需要在告警中进行设置异常告警')
        if 'status' not in get:
            get.status='start'
        init='/etc/init.d/btnotice'
        if not os.path.exists(init):
            public.ExecShell("cp -p {} {} && chmod +x {}".format(self.__plugin_path+"btnotice.sh",init,init))
        self.site_time_uptate()
        public.ExecShell("chmod +x /www/server/panel/plugin/security_notice/check_status.sh")
        if not os.path.exists(init):
            start_path=self.__plugin_path+"btnotice.sh"
            public.ExecShell("chmod +x "+self.__plugin_path+"btnotice.sh")
        else:
            start_path=init
        if get.status=='start':
            public.writeFile("/www/server/panel/plugin/security_notice/check_status.pl","")
            public.ExecShell(start_path+" restart")
        elif get.status=='stop':
            if os.path.exists("/www/server/panel/plugin/security_notice/check_status.pl"):
                os.remove("/www/server/panel/plugin/security_notice/check_status.pl")
            public.ExecShell(start_path+" stop")
        elif get.status=='restart':
            public.writeFile("/www/server/panel/plugin/security_notice/check_status.pl", "")
            public.ExecShell(start_path+" restart")
        else:
            return public.returnMsg(False, '参数无效')
        time.sleep(0.5)
        return public.returnMsg(True, '操作成功')



    # 四层计划任务
    def site_time_uptate(self):
        id = public.M('crontab').where('name=?', (u'PHP网站安全防护守护进程',)).getField('id')
        import crontab
        if id: crontab.crontab().DelCrontab({'id': id})
        data = {}
        data['name'] = 'PHP网站安全防护守护进程'
        data['type'] = 'minute-n'
        data['where1'] = '2'
        data['sBody'] = '/www/server/panel/plugin/security_notice/check_status.sh'
        data['backupTo'] = 'localhost'
        data['sType'] = 'toShell'
        data['hour'] = ''
        data['minute'] = ''
        data['week'] = ''
        data['sName'] = ''
        data['urladdress'] = ''
        data['save'] = ''
        crontab.crontab().AddCrontab(data)
        return True


    def get_index(self,args = None):
        '''
            @name 获取统计信息
            @author 黄文良<2020-04-28>
            @param args dict_obj or None
            @return dict{
                php_versions: list(PHP版本信息)
                total: dict(统计信息)
                safe_time: int(总防护次数)
            }
        '''
        data = {}
        data['php_versions'] = self.get_php_versions(True)
        data['total'] = self.get_all_total()
        data['safe_time'] = int((time.time() - int(public.readFile(self.__install_day))) / 86400)
        # data['notice'] = self.get_notice(args)
        return data

    def get_notice(self,get):
        result={}
        result['logs']=0
        result['risk_low']=0
        result['risk_mod']=0
        result['risk_high']=0
        result['today_risk_low']=0
        result['today_risk_mod']=0
        result['today_risk_high']=0
        result['site_count']=0
        result['risk_count']=0
        try:
            site_config=self.get_sites(True)['sites']
            start_time = time.strftime("%Y-%m-%d", time.localtime(time.time()))
            start_time = start_time + ' 00:00:00'
            start_time = int(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S')))
            result['logs']=public.M("security_notice").dbfile("notice").where("status=?",0).order("id desc").field('id,fun_name,domain,address,url,intercept,solution,addtime,risk').limit(100).select()
            result['risk_low']=public.M("security_notice").dbfile("notice").where("status=? and risk=?",(0,1)).count()
            result['risk_mod']=public.M("security_notice").dbfile("notice").where("status=? and risk=?",(0,2)).count()
            result['risk_high'] = public.M("security_notice").dbfile("notice").where("status=? and risk=?", (0, 3)).count()
            result['today_risk_low']=public.M("security_notice").dbfile("notice").where("status=? and risk=? and addtime>=?", (0, 1,start_time)).count()
            result['today_risk_mod'] = public.M("security_notice").dbfile("notice").where(
                "status=? and risk=? and addtime>=?", (0, 2, start_time)).count()
            result['today_risk_high'] = public.M("security_notice").dbfile("notice").where(
                "status=? and risk=? and addtime>=?", (0, 3, start_time)).count()
            result['site_count']=len(site_config)
            result['risk_count'] = public.M("security_notice").dbfile("notice").count()
            return result

        except:

            return result

    def get_all_total(self):
        '''
            @name 获取所有网站的总防护次数
            @author 黄文良<2020-04-29>
            @return int
        '''
        return public.M('security_notice').dbfile('notice').where("status=?",0).count()


    def get_php_versions(self,args = None):
        '''
            @name 获取PHP版本列表
            @author 黄文良<2020-04-28>
            @param args dict_obj or None
            @return list [
                {
                    version: PHP版本
                    state: 内核状态 0. 未加载 1.正常 -1.未安装
                    enable: 启用状态 0.已启用， 1.未启用
                    cli_enable: CLI模式启用状态 0.已启用， 1.未启用
                    site_count: 网站数量
                }
            ]

        '''
        if args:
            sites = self.get_sites(True)
        data = []
        for php_version in os.listdir(self.__php_path):
            if php_version in self.__disable_php: continue
            php_path = os.path.join(self.__php_path,php_version)
            php_ini = os.path.join(php_path,'etc/php.ini')
            if not os.path.exists(php_ini): continue
            filter_so = self.get_filter_so(php_version)
            if not filter_so: continue
            php_v = public.readFile(os.path.join(php_path,'version_check.pl'))
            if not php_v:
                php_v = php_version

            php_info = {
                "version": php_v,
                "v": php_version,
                "attack":'''/www/server/php/%s/bin/php -d 'extension=security_notice.so' -r "gethostbyname('test.www.dnslog.cn');sleep(60);"'''%php_version
            }

            #判断是否安装
            if not os.path.exists(filter_so):
                php_info['state'] = -1
            else:
                #是否加载
                php_ini_conf = public.readFile(php_ini)
                php_info['state'] = 1
                if php_ini_conf.find('security_notice.so') == -1:
                    php_info['state'] = 0
                if re.search(r";\s*extension\s*=\s*security_notice.so",php_ini_conf):
                    php_info['state'] = 0
            php_info['site_count'] = 0
            if args:
                for i in range(len(sites['sites'])):
                    if sites['sites'][i]['version'] == php_version:
                        php_info['site_count'] += 1
            data.append(php_info)

        return sorted(data,key=lambda x: x['version'],reverse=True)



    def get_site_find(self,args = None,siteName = None):
        '''
            @name 获取指定网站信息
            @author 黄文良<2020-04-28>
            @param args dict_obj {
                site_name: 网站名称
            }
            @return list [
                {
                    name: 网站名称
                    path: 根目录
                    _server: $_SERVER过滤统计
                    _input: 输入过滤统计
                    _args: 参数过滤统计
                    _path: 目录过滤统计
                    version: PHP版本
                    state: 防护状态 0. 未加载 1.已启用
                }
            ]
        '''
        if args:
            siteName = args.siteName

        self.get_config()
        for site in self.__config:
            if site['site_name'] == siteName:
                return site

        return None

    def set_site_key(self,siteName,sKey,sValue):
        '''
            @name 设置指定站点的指定值
            @author 黄文良<2020-04-28>
            @param siteName string(网站名称)
            @param sKey string(字段名)
            @param sValue mixed(字段值)
            @return bool
        '''
        self.get_config()
        for i in range(len(self.__config)):
            if self.__config[i]['site_name'] == siteName:
                self.__config[i][sKey] = sValue

        self.__set_config()
        return True

    def sync_sites(self):
        '''
            @name 同步网站列表
            @author 黄文良<2020-04-28>
            @return void
        '''
        site_list = public.M('sites').field('name,path').where("project_type=?",'PHP').select()

        sites = []
        for site in site_list:
            sites.append(site['name'])

            s_find = self.get_site_find(None,site['name'])
            if s_find:
                if s_find['path'] != site['path']:
                    self.set_site_key(site['name'],'path',site['path'])
                continue
            self.add_site(site)

        self.get_config(force=True)
        site_list = self.__config[:]
        is_write = False
        for site in site_list:
            if not site['site_name'] in sites:
                self.__config.remove(site)
                is_write = True
            else:
                tmp_php=self.get_site_php_version(site['site_name'])

                if tmp_php and tmp_php !=site['version']:
                    site['version']=tmp_php
                    is_write=True
        if is_write:
            self.__set_config()

    def add_site(self,siteInfo):
        '''
            @name 添加网站到配置文件
            @author 黄文良<2020-04-28>
        '''

        self.get_config()

        siteInfo['open'] = False
        siteInfo['site_name'] = siteInfo['name']
        siteInfo['is_stop']=0
        siteInfo['version'] = self.get_site_php_version(siteInfo['name'])
        if self.check_php(siteInfo['version']):
            siteInfo['open'] = True
        del(siteInfo['name'])
        self.__config.append(siteInfo)
        self.__set_config()
        return True


    def get_site_php_version(self,siteName):
        '''
            @name 获取网站列表
            @author 黄文良<2020-04-28>
            @param siteName string(网站名称)
            @return string
        '''
        config_file = os.path.join(self.__vhost_path,siteName+'.conf')
        if not os.path.exists(config_file):
            return None

        v_config = public.readFile(config_file)
        if not v_config:
            return None

        php_v = re.findall(r"enable-php-(\w+)\.conf",v_config)
        if not php_v:
            return None
        return php_v[0]

    def get_site_total(self,siteName,day = None):
        '''
            @name 获取网站统计数据
            @author 黄文良<2020-04-29>
            @param siteName string(网站名称)
            @param day string(指定日期)
            @return dict{
                total: 总计
                server_black: 当日server过滤
                input_black: 当日输入过滤
                filter_funs: 当日函数过滤
            }
        '''
        data = {"total":0,'day_total':0}
        data['total'] = public.M("security_notice").dbfile("notice").where("domain=?",siteName).count()
        start_time = time.strftime("%Y-%m-%d", time.localtime(time.time()))
        start_time = start_time + ' 00:00:00'
        start_timeStamp = int(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S')))
        data['day_total'] =public.M("security_notice").dbfile("notice").where("domain=? and addtime>=? and addtime<=?",(siteName,start_timeStamp,start_timeStamp+86400)).count()
        return data

    #取php.ini配置文件
    def get_php_ini_data(self,php_version):
        '''
            @name 取php.ini配置文件
            @author 黄文良<2020-05-09>
            @param php_version string(PHP版本号，如：56)
            @return string(php.ini内容)
        '''
        if self.__php_ini_data[php_version]:
            return self.__php_ini_data[php_version]
        php_ini_file = self.__php_path + php_version+'/etc/php.ini'
        tmp = public.readFile(php_ini_file)
        if tmp:
            self.__php_ini_data[php_version] = tmp
        return self.__php_ini_data[php_version]

    def add_site_config(self,args):
        '''
            @name 添加網站告警目录和文件
        '''
        domain=args.domain
        config_type=args.type
        path=args.path
        action=args.actions
        # 增加 add 删除 del   读取 read  修改 reit
        action =action.split(',')
        if len(action)!=4:
            return public.returnMsg(False,'配置错误')
        actions = {"read": action[0], "del": action[1], "reit": action[2], "add": action[3], "type": config_type}
        if not os.path.exists(path):
            return public.returnMsg(False,'SITE_ADD_ERR_PATH')
        config_info=self.site_config_info(domain,True)
        if config_type=='file':
            if not os.path.isfile(path):
                return public.returnMsg(False, '请选择文件')
            if path in config_info[domain]['file_info']:
                return public.returnMsg(False,'文件存在列表中')
            config_info[domain]['file_info'][path]=actions
        else:
            if not os.path.isdir(path):
                return public.returnMsg(False, '请选择目录')
            if path in config_info[domain]['file_info']:
                return public.returnMsg(False,'目录存在列表中')
            if path.endswith("/"):
                path=path[:-1]
            config_info[domain]['file_info'][path]=actions
        public.writeFile(self.__plugin_path+"site_config.json",json.dumps(config_info))
        return public.returnMsg(True,'添加成功')

    def edit_site_config(self,args):
        domain = args.domain
        config_type = args.type
        path = args.path
        action = args.actions
        action = action.split(',')
        if len(action) != 4:
            return public.returnMsg(False, '配置错误')

        actions = {"read": action[0], "del": action[1], "reit": action[2], "add": action[3], "type": config_type}
        config_info = self.site_config_info(domain, True)
        if config_type == 'file':
            if path in config_info[domain]['file_info']:
                config_info[domain]['file_info'][path] = actions
                public.writeFile(self.__plugin_path + "site_config.json", json.dumps(config_info))
                return public.returnMsg(True, '修改完毕')
            else:
                return public.returnMsg(False, '修改失败')
        else:
            if path in config_info[domain]['file_info']:
                config_info[domain]['file_info'][path] = actions
                public.writeFile(self.__plugin_path + "site_config.json", json.dumps(config_info))
                return public.returnMsg(True, '修改完毕')
            else:
                return public.returnMsg(False, '修改失败')



    def del_site_config(self,args):
        '''
            @name 删除網站告警目录和文件
        '''
        domain=args.domain
        config_type=args.type
        path=args.path
        config_info=self.site_config_info(domain,True)
        if config_type=='file':
            if path not  in config_info[domain]['file_info']:
                return public.returnMsg(False,'文件不存在列表中')
            del config_info[domain]['file_info'][path]
        else:

            if path not in config_info[domain]['file_info']:
                return public.returnMsg(False, '文件不存在列表中')
            del config_info[domain]['file_info'][path]
        public.writeFile(self.__plugin_path+"site_config.json",json.dumps(config_info))
        return public.returnMsg(True,'删除成功')


    def site_config_info(self,domain,info=False):
        '''
            @name 网站的配置文件
        '''
        config_path=self.__plugin_path+"site_config.json"
        if not os.path.exists(config_path):
            config_info={}
        try:
            config_info=json.loads(public.readFile(config_path))
            if not config_info:
                config_info={}
        except:
            config_info={}
        if domain not in config_info:
            config_info[domain]={"file_info":{}}
            public.writeFile(config_path,json.dumps(config_info))
            if info:
                return config_info
            return config_info[domain]
        else:
            if info:return config_info
            return config_info[domain]

    def get_sites(self,args = None):
        '''
            @name 获取网站列表
            @author 黄文良<2020-04-28>
            @param args dict_obj or None
        '''

        self.sync_sites()
        sites = self.get_config(force=True)
        if args:
            tmp_data = []
            for i in range(len(sites)):
               try:
                    if sites[i]['version']=="82":
                        sites[i]['version']="82[暂不兼容此版本]"
                    if sites[i]['version'] in self.__disable_php: continue
                    sites[i]['total'] = self.get_site_total(sites[i]['site_name'])
                    sites[i]['config'] =self.site_config_info(sites[i]['site_name'])

                    tmp_data.append(sites[i])
               except:continue
            sites=sorted(tmp_data,key=lambda x: x['total']['day_total'],reverse=True)
        data = {}
        data['total'] = self.get_all_total()
        data['safe_time'] = int((time.time() - int(public.readFile(self.__install_day))) / 86400)
        data['sites'] = sites
        return data

    def get_filter_so(self,v):
        vfs = {
            '52':'/www/server/php/52/lib/php/extensions/no-debug-non-zts-20060613',
            '53':'/www/server/php/53/lib/php/extensions/no-debug-non-zts-20090626',
            '54':'/www/server/php/54/lib/php/extensions/no-debug-non-zts-20100525',
            '55':'/www/server/php/55/lib/php/extensions/no-debug-non-zts-20121212',
            '56':'/www/server/php/56/lib/php/extensions/no-debug-non-zts-20131226',
            '70':'/www/server/php/70/lib/php/extensions/no-debug-non-zts-20151012',
            '71':'/www/server/php/71/lib/php/extensions/no-debug-non-zts-20160303',
            '72':'/www/server/php/72/lib/php/extensions/no-debug-non-zts-20170718',
            '73':'/www/server/php/73/lib/php/extensions/no-debug-non-zts-20180731',
            '74':'/www/server/php/74/lib/php/extensions/no-debug-non-zts-20190902',
            '80':'/www/server/php/80/lib/php/extensions/no-debug-non-zts-20200930',
            '81':'/www/server/php/81/lib/php/extensions/no-debug-non-zts-20210902'
        }

        if v in vfs.keys():
            if not os.path.exists(vfs[v]):
                os.makedirs(vfs[v])
            return vfs[v] + '/security_notice.so'
        return None


    def get_config(self,force=False):
        #判断是否从文件读取配置
        if not self.__config or force:
            config_file = self.__plugin_path + 'config.json'
            if not os.path.exists(config_file): return []
            f_body = public.ReadFile(config_file)
            if not f_body: return []
            self.__config = json.loads(f_body)
            if type(self.__config) == dict:
                self.__config = []

        return self.__config

    def sync_phpini(self):
        '''
            @name 同步配置到PHP
            @author 黄文良<2020-04-28>
            @return void
        '''
        self.get_config(force=True)


    def set_php_status(self, args):
        '''
            @name 设置PHP版本状态
            @param args {
                php_version: PHP版本,如：53
                enable: 防护状态 0.关闭 1.开启

            }
            @return dict
        '''
        php_v = args.php_version.strip()
        php_ini_file = os.path.join(self.__php_path, php_v, 'etc/php.ini')
        if not os.path.exists(php_ini_file):
            return public.returnMsg(False, '指定PHP版本未正确安装')

        php_ext_so = self.get_filter_so(php_v)
        src_ext_so = "{}/modules/security_notice_{}.so".format(self.__plugin_path, php_v)
        if not os.path.exists(php_ext_so):
            if not os.path.exists(src_ext_so):
                return public.returnMsg(False, '暂不支持PHP-{}版本'.format(php_v))
            public.ExecShell("\cp -arf {} {} && chmod +x {}".format(src_ext_so, php_ext_so,php_ext_so))
            if os.path.getsize(php_ext_so) < 100000:
                return public.returnMsg(False, '文件下载失败!')
        else:
            #对比md5
            if args.enable=='1' or args.enable==1:
                if public.FileMd5(php_ext_so) !=public.FileMd5(src_ext_so):
                    public.ExecShell("\cp -arf {} {} && chmod +x {}".format(src_ext_so, php_ext_so, php_ext_so))
                    if os.path.getsize(php_ext_so) < 100000:
                        return public.returnMsg(False, '模块安装失败,请重新安装插件!')

        if 'enable' not in args:
            args.enable=1
        #开启
        phpini = public.readFile(php_ini_file)

        if args.enable==1 or args.enable=='1':
            flag=False
            openrasp = 'extension=openrasp.so'
            if re.search(openrasp, phpini):
                if not re.search(';'+openrasp, phpini):
                    flag=True
            if flag:
                return public.returnMsg(False, '请先关闭openrasp!')
            if phpini.find('security_notice') == -1:
                phpini = re.sub(r".*security_notice.+", "", phpini)
                phpini += '''
[bt_security_notice]
extension = security_notice.so
'''
                public.writeFile(php_ini_file, phpini)
            rep = r".*;\s*extension\s*=\s*security_notice.so"
            if re.search(rep, phpini):
                phpini = re.sub(rep, "extension = security_notice.so", phpini)
            public.writeFile(php_ini_file, phpini.replace("\n" * 3, "\n"))
            #开启的话，所有的网站开启,但是不包括手动关闭过的
            self.get_config()
            is_flag=False
            for i in range(len(self.__config)):
                if str(self.__config[i]['version'])== str(php_v):

                    if not self.__config[i]['is_stop']:
                        self.__config[i]['open']=True
                        is_flag=True
            if is_flag:
                self.__set_config()
        else:
            #关闭
            if phpini.find('security_notice') != -1:
                phpini=phpini.replace("[bt_security_notice]","")
                rep = r"\s*extension\s*=\s*security_notice.so"
                if re.search(rep, phpini):
                    phpini = re.sub(rep, "", phpini)
                public.writeFile(php_ini_file, phpini.replace("\n" * 3, "\n"))


                self.get_config()
                is_flag = False
                for i in range(len(self.__config)):
                    if self.__config[i]['version'] == php_v:
                        if args.enable==0:
                            self.__config[i]['open'] = False
                            is_flag = True
                        else:
                            if not self.__config[i]['is_stop']:
                                self.__config[i]['open'] = False
                                is_flag = True
                if is_flag:
                    self.__set_config()
        #self.sync_phpini()
        public.ExecShell("/etc/init.d/php-fpm-{} start".format(php_v))
        public.ExecShell("/etc/init.d/php-fpm-{} restart".format(php_v))
        return public.returnMsg(True, '设置成功!')



    def __set_config(self):
        #是否需要初始化配置项
        if not self.__config: self.__config = []
        #写入到配置文件
        config_file = self.__plugin_path + 'config.json'
        public.WriteFile(config_file,json.dumps(self.__config))
        self.sync_phpini()
        return True

    def __set_overall(self):
        #是否需要初始化配置项
        if not self.__overall_config: self.__overall_config = []
        #写入到配置文件
        public.WriteFile(self.__overall_path,json.dumps(self.__overall_config))
        return True

    def get_overall(self,get):
        if os.path.exists(self.__overall_path):
            try:
                self.__overall_config=json.loads(public.ReadFile(self.__overall_path))
            except:
                return self.__overall_config
        return self.__overall_config

    def get_overall_info(self,get):
        if os.path.exists(self.__overall_path):
            try:
                overall_config=json.loads(public.ReadFile(self.__overall_path))
                if len(overall_config['ip_white'])>=1:
                    for i in overall_config['ip_white']:
                        for i2 in range(len(i)):
                            i[i2] = self.long2ip(i[i2])
                return overall_config

            except:
                return self.__overall_config

    def __format_ip(self, ip):
        tmp = ip.split('.')
        if len(tmp) < 4: return False
        tmp[0] = int(tmp[0])
        tmp[1] = int(tmp[1])
        tmp[2] = int(tmp[2])
        tmp[3] = int(tmp[3])
        return tmp

    def __is_ipn(self, ipn):
        for i in range(4):
            if ipn[0][i] == ipn[1][i]: continue;
            if ipn[0][i] < ipn[1][i]: break;
            return False
        return True

    def long2ip(self, long):
        floor_list = []
        yushu = long
        for i in reversed(range(4)):
            res = divmod(yushu, 256 ** i)
            floor_list.append(str(res[0]))
            yushu = res[1]
        return '.'.join(floor_list)

    def get_cn_list(self,type):
        try:
            rule = self.get_overall(None)[type]
            for i in rule:
                for i2 in range(len(i)):
                    i[i2] = self.long2ip(i[i2])
            return rule
        except:
            return []

    def cn_to_ip(self, aaa):
        for i in aaa:
            for i2 in range(len(i)):
                i[i2] = self.ip2long(i[i2])
        return aaa

    def ip2long(self, ip):
        ips = ip.split('.')
        if len(ips) != 4: return 0
        iplong = 2 ** 24 * int(ips[0]) + 2 ** 16 * int(ips[1]) + 2 ** 8 * int(ips[2]) + int(ips[3])
        return iplong

    def empty_info(self,get):
        url_white = self.get_overall(None)
        if get.type=='ip_white':
            url_white['ip_white']=[]
            self.__set_overall()
        if get.type=='url_white':
            url_white['url_white']=[]
            self.__set_overall()
        return public.returnMsg(True, '清空完成!')
    def add_ip_white(self, get):
        ipn = [self.__format_ip(get.start_ip), self.__format_ip(get.end_ip)]
        if not ipn[0] or not ipn[1]: return public.returnMsg(False, 'IP段格式不正确');
        if not self.__is_ipn(ipn): return public.returnMsg(False, '起始IP不能大于结束IP');
        ipn = [get.start_ip, get.end_ip]
        iplist = self.get_cn_list('ip_white')
        if ipn in iplist: return public.returnMsg(False, '指定IP段已存在!');
        iplist.insert(0, ipn)
        self.__overall_config['ip_white']=self.cn_to_ip(iplist)
        self.__set_overall()
        return public.returnMsg(True, '添加成功!')

    def remove_ip_white(self, get):
        index = int(get.index)
        iplist = self.get_cn_list('ip_white')
        ipn = iplist[index]
        del (iplist[index])
        self.__overall_config['ip_white'] = iplist
        self.__set_overall()
        return public.returnMsg(True, '删除成功!')


    def add_url_white(self, get):
        url_white = self.get_overall(None)['url_white']
        url_rule = get.url_rule.strip()
        if url_rule == '^/' or url_rule == '/': return public.returnMsg(False, '不允许添加根目录')
        if get.url_rule in url_white: return public.returnMsg(False, '您添加的URL已存在')
        url_white.insert(0, url_rule)
        self.__overall_config['url_white'] = url_white
        self.__set_overall()
        return public.returnMsg(True, '添加成功!')


    def wubao_url_white(self, get):
        url_white = self.get_overall(None)['url_white']
        url_rule = get.url_rule.strip()
        url_rule = '^' + url_rule.split('?')[0]
        if url_rule in url_white: return public.returnMsg(False, '您添加的URL已存在')
        if url_rule == '^/': return public.returnMsg(False, '不允许添加URL为 [/] 的URL为白名单')
        url_white.insert(0, url_rule)
        self.__overall_config['url_white'] = url_white
        self.__set_overall()
        return public.returnMsg(True, '添加成功!')


    def remove_url_white(self, get):
        url_white = self.get_overall(None)['url_white']
        index = int(get.index)
        url_rule = url_white[index]
        del (url_white[index])
        self.__overall_config['url_white'] = url_white
        self.__set_overall()
        return public.returnMsg(True, '删除成功!')

    # def get_logs_list(self, get):
    #     sfind = self.__logs_path+get.siteName
    #     data = []
    #     if os.path.exists(sfind):
    #         for fname in os.listdir(sfind):
    #             if not re.search("\d+-\d+-\d+.log",fname):continue
    #             tmp = fname.replace('.log', '')
    #             data.append(tmp)
    #     return sorted(data, reverse=True)


    # def get_safe_logs(self, get):
    #     try:
    #         import html
    #         pythonV = sys.version_info[0]
    #         path = self.__logs_path + get.siteName + '/' + get.toDate + '.log'
    #         num = 10
    #         if not os.path.exists(path): return ["11"]
    #         p = 1
    #         if 'p' in get:
    #             p = int(get.p)
    #         start_line = (p - 1) * num
    #         count = start_line + num
    #         fp = open(path, 'rb')
    #         buf = ""
    #         try:
    #             fp.seek(-1, 2)
    #         except:
    #             return []
    #         if fp.read(1) == "\n": fp.seek(-1, 2)
    #         data = []
    #         b = True
    #         n = 0
    #         c = 0
    #         while c < count:
    #             while True:
    #                 newline_pos = str.rfind(buf, "\n")
    #                 pos = fp.tell()
    #                 if newline_pos != -1:
    #                     if n >= start_line:
    #                         line = buf[newline_pos + 1:]
    #                         if line:
    #                             try:
    #                                 tmp_data = json.loads(line)
    #                                 data.append(tmp_data)
    #                             except:
    #                                 c -= 1
    #                                 n -= 1
    #                                 pass
    #                         else:
    #                             c -= 1
    #                             n -= 1
    #                     buf = buf[:newline_pos]
    #                     n += 1
    #                     c += 1
    #                     break
    #                 else:
    #                     if pos == 0:
    #                         b = False
    #                         break
    #                     to_read = min(4096, pos)
    #                     fp.seek(-to_read, 1)
    #                     t_buf = fp.read(to_read)
    #                     if pythonV == 3: t_buf = t_buf.decode('utf-8', errors="ignore")
    #                     buf = t_buf + buf
    #                     fp.seek(-to_read, 1)
    #                     if pos - to_read == 0:
    #                         buf = "\n" + buf
    #             if not b: break
    #     except:
    #         data = []
    #         return public.get_error_info()
    #     return data

    def get_logs(self,args):
        #处理前端传过来的参数
        if not 'p' in args: args.p = 1
        if not 'rows' in args: args.rows = 15
        if not 'callback' in args: args.callback = ''
        args.p = int(args.p)
        args.rows = int(args.rows)
        #取日志总行数
        count = public.M('logs').where('type=?',(self.__log_name,)).count()
        #获取分页数据
        page_data = public.get_page(count,args.p,args.rows,args.callback)
        #获取当前页的数据列表
        log_list = public.M('logs').where('type=?',(self.__log_name,)).order('id desc').limit(page_data['shift'] + ',' + page_data['row']).field('id,type,log,addtime').select()
        #返回数据到前端
        return {'data': log_list,'page':page_data['page'] }

    # 名称输出过滤
    def xssencode(self, text):
        list = ['<', '>']
        ret = []
        for i in text:
            if i in list:
                i = ''
            ret.append(i)
        str_convert = ''.join(ret)
        if sys.version_info[0] == 3:
            import html
            text2 = html.escape(str_convert, quote=True)
        else:
            import cgi
            text2 = cgi.escape(str_convert, quote=True)

        reps = {'&amp;':'&'}
        for rep in reps.keys():
            if text2.find(rep) != -1: text2 = text2.replace(rep,reps[rep])
        return text2


    # 获取回收站信息
    def Get_Recycle_bin(self, get):
        data = []
        rPath  =self.__plugin_path+'Recycle_bin'
        if not os.path.exists(rPath): return data
        for file in os.listdir(rPath):
                try:
                    tmp = {}
                    fname = os.path.join(rPath , file)
                    # return fname
                    if sys.version_info[0] == 2:
                        fname = fname.encode('utf-8')
                    else:
                        fname.encode('utf-8')
                    tmp1 = file.split('_bt_')
                    tmp2 = tmp1[len(tmp1)-1].split('_t_')
                    file = self.xssencode(file)
                    tmp['rname'] = file
                    tmp['dname'] = file.replace('_bt_', '/').split('_t_')[0]
                    if tmp['dname'].find('@') != -1:
                        tmp['dname'] = "BTDB_" + tmp['dname'][5:].replace('@',"\\u").encode().decode("unicode_escape")
                    tmp['name'] = tmp2[0]
                    tmp['time'] = int(float(tmp2[1]))
                    if os.path.islink(fname):
                        filePath = os.readlink(fname)
                        if os.path.exists(filePath):
                            tmp['size'] = os.path.getsize(filePath)
                        else:
                            tmp['size'] = 0
                    else:
                        tmp['size'] = os.path.getsize(fname)
                    if os.path.isdir(fname):
                        if file[:5] == 'BTDB_':
                            tmp['size'] =  public.get_path_size(fname)
                        # data['dirs'].append(tmp)
                    else:
                        data.append(tmp)
                except:
                    continue
        data = sorted(data,key = lambda x: x['time'],reverse=True)
        return data

    # 从回收站恢复
    def Re_Recycle_bin(self,get):
        if sys.version_info[0] == 2:
            get.path = get.path.encode('utf-8')
        get.path = public.html_decode(get.path).replace(';','')
        dFile = get.path.replace('_bt_', '/').split('_t_')[0]
        if not os.path.exists(self.Recycle_bin+'/'+get.path):
            return public.returnMsg(False, 'FILE_RE_RECYCLE_BIN_ERR')
        try:
            import shutil
            shutil.move(self.Recycle_bin+'/'+get.path, dFile)
            return public.returnMsg(True, 'FILE_RE_RECYCLE_BIN')
        except:
            return public.returnMsg(False, 'FILE_RE_RECYCLE_BIN_ERR')


    def Del_Recycle_bin(self, get):
        if sys.version_info[0] == 2:
            get.path = get.path.encode('utf-8')
        tfile = public.html_decode(get.path).replace(';', '')
        filename=self.Recycle_bin+'/'+get.path
        public.ExecShell('chattr  -i ' + filename)
        try:
            os.remove(filename)
        except:
            public.ExecShell("rm -f " + filename)
        return public.returnMsg(True, '已经从木马隔离箱中永久删除当前文件'+tfile)


    def get_domain_logs(self,args):
        #处理前端传过来的参数
        if not 'p' in args: args.p = 1
        if not 'rows' in args: args.rows = 10
        if not 'callback' in args: args.callback = ''
        if not 'siteName' in args:
            args.p = int(args.p)
            args.rows = int(args.rows)
            #取日志总行数
            count = public.M('security_notice').dbfile("notice").where('status=?',(0,)).count()
            #获取分页数据
            page_data = public.get_page(count,args.p,args.rows,args.callback)
            #获取当前页的数据列表
            log_list = public.M('security_notice').dbfile("notice").where('status=?',(0,)).order('id desc').limit(page_data['shift'] + ',' + page_data['row']).select()
            #返回数据到前端
            for i in log_list:
                i['data_info']=json.loads(i['data_info'])
            return {'data': log_list,'page':page_data['page'] }
        else:
            args.p = int(args.p)
            args.rows = int(args.rows)
            #取日志总行数
            count = public.M('security_notice').dbfile("notice").where('status=? and domain=?',(0,args.siteName)).count()
            #获取分页数据
            page_data = public.get_page(count,args.p,args.rows,args.callback)
            #获取当前页的数据列表
            log_list = public.M('security_notice').dbfile("notice").where('status=? and domain=?',(0,args.siteName)).order('id desc').limit(page_data['shift'] + ',' + page_data['row']).select()
            #返回数据到前端
            for i in log_list:
                i['data_info']=json.loads(i['data_info'])
            return {'data': log_list,'page':page_data['page'] }

    def set_ignore(self,args):
        id =args.id
        operation=args.operation
        if public.M('security_notice').dbfile("notice").where('id=?', (id)).count()==0:
            return public.returnMsg(False,'不存在')
        public.M('security_notice').dbfile("notice").where('id=?', (id)).update({"status":operation})
        return public.returnMsg(True, '处理成功')

    def get_send_logs(self,args):
        #处理前端传过来的参数
        if not 'p' in args: args.p = 1
        if not 'rows' in args: args.rows = 15
        if not 'callback' in args: args.callback = ''
        args.p = int(args.p)
        args.rows = int(args.rows)
        #取日志总行数
        count = public.M('logs').where('type=?',('PHP安全告警通知',)).count()
        #获取分页数据
        page_data = public.get_page(count,args.p,args.rows,args.callback)
        #获取当前页的数据列表
        log_list = public.M('logs').where('type=?',('PHP安全告警通知',)).order('id desc').limit(page_data['shift'] + ',' + page_data['row']).field('id,type,log,addtime').select()
        #返回数据到前端
        return {'data': log_list,'page':page_data['page'] }


    def attack(self,get):
        '''
            @args.version

        '''
        php=self.get_php_versions(True)
        if len(php)==0:
            return public.returnMsg(False, '没有支持的php版本')
        flag=False
        for i in php:
            if i['v']==str(get.version):
                if i['state']!=1:
                    return public.returnMsg(False, '当前php未安装模块')
                flag=True
        if not flag:
            return public.returnMsg(False, '不支持该php版本或未安装模块')

        get_status=self.get_status(get)
        if not get_status['status']:return public.returnMsg(False, '未开启监控开关')
        if not get_status['send']:return public.returnMsg(False, '未开启告警设置')
        public.ExecShell("/etc/init.d/php-fpm-%s restart"%get.version)
        #time.sleep(1)
        php_info=''' <?php gethostbyname('test.www.dnslog.cn');sleep(60);?>'''
        import panelPHP
        php_obj=panelPHP.panelPHP()
        public.writeFile("/dev/shm/gethostbyname.php",php_info)
        #(version,uri,document_root,method='GET',pdata=b''):
        public.request_php(get.version,"gethostbyname.php","/dev/shm",method='GET',pdata=b'')
        if os.path.exists("/dev/shm/gethostbyname.php"):
            os.remove("/dev/shm/gethostbyname.php")




        #public.ExecShell("/www/server/php/%s/bin/php -d 'extension=security_notice.so' -r \"gethostbyname('test.www.dnslog.cn');sleep(60);\""%get.version)
        return public.returnMsg(True, '模拟测试成功')

    def get_fun(self,class_id, method_id):
        if class_id == 0 and method_id == 0: return "passthru"
        if class_id == 0 and method_id == 1: return "system"
        if class_id == 0 and method_id == 2: return "exec"
        if class_id == 0 and method_id == 3: return "shell_exec"
        if class_id == 0 and method_id == 4: return "proc_open"
        if class_id == 0 and method_id == 5: return "popen"
        if class_id == 0 and method_id == 6: return "pcntl_exec"
        if class_id == 1 and method_id == 0: return "file"
        if class_id == 1 and method_id == 1: return "readfile"
        if class_id == 1 and method_id == 2: return "file_get_contents"
        if class_id == 1 and method_id == 3: return "file_put_contents"
        if class_id == 1 and method_id == 4: return "copy"
        if class_id == 1 and method_id == 5: return "rename"
        if class_id == 1 and method_id == 6: return "unlink"
        if class_id == 1 and method_id == 7: return "dir"
        if class_id == 1 and method_id == 8: return "opendir"
        if class_id == 1 and method_id == 9: return "scandir"
        if class_id == 1 and method_id == 10: return "fopen"
        if class_id == 1 and method_id == 11: return "move_uploaded_file"
        if class_id == 1 and method_id == 12: return "__construct"
        if class_id == 2 and method_id == 0: return "socket_connect"
        if class_id == 3 and method_id == 0: return "gethostbyname"
        if class_id == 3 and method_id == 1: return "dns_get_record"
        if class_id == 4 and method_id == 0: return "assert"
        if class_id == 4 and method_id == 1: return "putenv"
        if class_id == 5 and method_id == 0: return "curl_exec"
        if class_id == 10 and method_id == 0: return "include"

    def write_log(self,log):
        __plugin_path = "/www/server/panel/plugin/security_notice/logs/logs.log"
        if os.path.exists(__plugin_path):
            if os.path.getsize(__plugin_path) > 124288000:
                public.WriteFile(__plugin_path, "")
        public.WriteFile(__plugin_path, log + "\n", 'a+')

    def write_total(self,fun_name, domain, address, url, intercept, solution, data_info, status, risk):

        sql = db.Sql().dbfile("notice")  # 初始化数据库
        if len(url) > 300:
            url = url[:300]
        data = {"fun_name": fun_name, "domain": domain, "address": address, "url": url, "intercept": intercept,
                "solution": solution, "data_info": json.dumps(data_info), "risk": risk, "status": status,
                "addtime": int(time.time())}
        sql.table("security_notice").insert(data)

    # def get_config(self):
    #     config_file = self.plugin_path + 'config.json'
    #     if not os.path.exists(config_file): return []
    #     f_body = public.ReadFile(config_file)
    #     if not f_body: return []
    #     config = json.loads(f_body)
    #     if type(config) == dict:
    #         return []
    #     return config
    #
    # def get_overall(self):
    #     if os.path.exists(self.overall_path):
    #         try:
    #             overall_config = json.loads(public.ReadFile(self.overall_path))
    #             return overall_config
    #         except:
    #             return {'ip_white': [], 'url_white': []}



    def ip_white(self,ip):
        ip_white = self.get_overall(None)['ip_white']
        if len(ip_white) <= 0: return False
        ipn = self.ip2long(ip)
        for i in ip_white:
            try:
                if ipn <= i[1] and ipn >= i[0]:
                    return True
            except:
                continue
        return False

    def url_white(self,url):
        url_white = self.get_overall(None)['url_white']
        if len(url_white) <= 0: return False
        for i in url_white:
            if re.search(i, url):
                return True
        return False

    # 移动到回收站
    def Mv_Recycle_bin(self,path):
        rPath = self.Recycle_bin
        if not os.path.exists(self.Recycle_bin):
            os.makedirs(self.Recycle_bin)
        rFile = os.path.join(rPath, path.replace('/', '_bt_') + '_t_' + str(time.time()))
        try:
            import shutil
            shutil.move(path, rFile)
            return True
        except:
            return False

    def is_open(self,domain):
        config = self.get_config()
        flag=False
        for i in config:
            if i['site_name'] == domain:
                flag=True
                if not i['open']:
                    return True,"/"
                return False,i['path']
        if not flag:
            self.sync_sites()
            return True,"/"
        return True,"/"




    def ReadFile(self,filename, mode='r'):
        import os
        if not os.path.exists(filename): return False
        try:
            fp = open(filename, mode)
            f_body = fp.read()
            fp.close()
        except Exception as ex:
            if sys.version_info[0] != 2:
                try:
                    fp = open(filename, mode, encoding="utf-8")
                    f_body = fp.read()
                    fp.close()
                except Exception as ex2:
                    return False
            else:
                return False
        return f_body

    def read_file_md5(self,filename):
        if os.path.exists(filename):
            with open(filename, 'rb') as fp:
                data = fp.read()
            import hashlib
            file_md5 = hashlib.md5(data).hexdigest()
            return file_md5
        else:
            return False

    def webshellchop(self,filename, url="http://w-check.bt.cn/check.php"):
        try:
            upload_url = url
            size = os.path.getsize(filename)
            if size > 1024000: return False
            user = json.loads(public.ReadFile('/www/server/panel/data/userInfo.json'))
            if len(user) == 0: return False
            upload_data = {'inputfile': self.ReadFile(filename), "md5": self.read_file_md5(filename), "path": filename,
                           "access_key": user['access_key'], "uid": user['uid'], "username": user["username"]}
            import requests
            upload_res = requests.post(upload_url, upload_data, timeout=20).json()
            if upload_res['msg'] == 'ok':
                if (upload_res['data']['data']['level'] == 5):
                    self.write_log('%s文件为木马  hash:%s' % (filename, upload_res['data']['data']['hash']))
                    return True
                return False
        except:
            return False
    # 登陆告警
    def send_news(self,intercept, ip, domain, url, risk, filename=None):
        login_send_type_conf = "/www/server/panel/data/security_notice_send.pl"
        if os.path.exists(login_send_type_conf):
            send_type = self.ReadFile(login_send_type_conf).strip()
        else:
            return False

        if not send_type:
            return False
        object = public.init_msg(send_type.strip())
        if not object: return False

        url = url.split('?')[0]
        if len(url) > 30:
            url = url[0:30]
        if risk == 3:
            risk = "高危"
            p_risk = '<span style="color:#f50606;">高危</span>'
        elif risk == 2:
            risk = "中危"
            p_risk = '<span style="color:#FF9900;">中危</span>'

        else:
            risk = "低危"
            p_risk = '<span style="color:#DDC400;">低危</span>'

        if intercept == '恶意文件上传' and filename:
            plist = [
                ">威胁行为：" + intercept,
                ">触发的IP：" + ip,
                ">风险等级：" + risk,
                ">受威胁的域名：" + domain,
                ">恶意文件上传的文件:" + filename,
                ">文件已经被隔离"
            ]
        elif filename:
            plist = [
                ">威胁行为：" + intercept,
                ">触发的IP：" + ip,
                ">风险等级：" + risk,
                ">受威胁的域名：" + domain,
                ">发现木马文件:" + filename,
                ">木马文件已经被隔离"
            ]
        else:
            plist = [
                ">威胁行为：" + intercept,
                ">触发的IP：" + ip,
                ">风险等级：" + risk,
                ">受威胁的域名：" + domain,
                ">威胁行为的URL：" + url
            ]

        p_log = '''
        威胁行为：【%s】触发的IP：【%s】 风险等级：【%s】  受威胁的域名：【%s】 威胁行为的URL：【%s】
        ''' % (intercept, ip, p_risk, domain, url)
        public.WriteLog("PHP安全告警通知", p_log)
        self.write_log("发送信息")
        info = public.get_push_info("PHP威胁告警", plist)
        reuslt = object.push_data(info)
        return reuslt

    def get_first_char(self,string):
        return string[0]

    def check_list(self,model_list, keyword_list, s_type=0):
        # s_type=0 的时候默认是 keyword_first_chars 大于 model_first_chars
        # s_type=1 的时候默认是 keyword_first_chars 等于 model_first_chars

        model_first_chars = list(map(self.get_first_char, model_list))
        keyword_first_chars = list(map(self.get_first_char, keyword_list))
        if s_type == 1:
            if len(keyword_first_chars) != len(model_first_chars): return False
        else:
            if len(keyword_first_chars) > len(model_first_chars): return False

        if all(x == y for x, y in zip(model_first_chars, keyword_first_chars)):
            return True
        else:
            return False

    def notice(self,payload_info,is_webshell=False):
        # 获取IP
        ip = payload_info['data']['request']['remoteAddress']
        url = payload_info['data']['request']['uri']
        domain = payload_info['data']['request']['serverName']
        if 'risk' not in payload_info:
            payload_info['risk'] = 1
        risk = payload_info['risk']

        # 木马查杀
        stack_trace = payload_info['data']['stack_trace']
        ret = []
        for i in stack_trace:
            if re.search("\w+\((.+\.php)", i):
                path = re.findall("\w+\((.+\.php)", i)[0]
                if path not in ret:
                    ret.append(path)


        if payload_info['intercept'] == "模拟测试":
            self.write_log(payload_info['fun_name'] + "   " + payload_info['intercept'] + " " + payload_info['solution'])
            self.write_total(payload_info['fun_name'], "localhost", "localhost", "localhost", payload_info['intercept'],
                        payload_info['solution'], payload_info, 0, risk)
            self.send_news(payload_info['intercept'], "localhost", "localhost", "localhost", risk)
            return




        # 判断该网站是否开启的状态
        if self.ip_white(ip): return False
        if self.url_white(url): return False
        is_status, domain_path = self.is_open(domain)
        if is_status: return False

        if is_webshell:
            self.write_log(
                payload_info['fun_name'] + "   " + payload_info['intercept'] + " " + payload_info['solution'])
            self.write_total(payload_info['fun_name'], domain, ip, url, payload_info['intercept'],
                             payload_info['solution'], payload_info, 0, risk)
            self.send_news('木马文件', ip, domain, url, 3, ret[0])

            if len(ret)>=1 and  self.Mv_Recycle_bin(ret[0]):
                try:
                    os.remove(ret[0])
                except:
                    pass
            return

        flag = False
        if len(ret) == 1:
            if os.path.exists(ret[0]):
                if self.webshellchop(ret[0]):
                    self.write_log(ret[0] + "当前文件为木马，将进入隔离文件")
                    # flag=True
                    self.write_total(payload_info['fun_name'], domain, ip, url, '木马文件', "已隔离该木马的文件,无需处理", payload_info, 0, 3)
                    self.send_news('木马文件', ip, domain, url, 3, ret[0])
                    if self.Mv_Recycle_bin(ret[0]):
                        try:
                            os.remove(ret[0])
                        except:
                            pass

        # if not flag:
        solution = payload_info['solution']
        self.write_log(payload_info['fun_name'] + "   " + payload_info['intercept'] + " " + payload_info['solution'])
        self.write_total(payload_info['fun_name'], domain, ip, url, payload_info['intercept'], solution, payload_info, 0,
                    risk)
        self.send_news(payload_info['intercept'], ip, domain, url, risk)
        if payload_info['intercept'] == '恶意文件上传':
            self.write_log("隔离上传的文件 " + payload_info['filename'] + " " + payload_info['solution'])
            payload_info['risk'] = 3
            self.write_total(payload_info['fun_name'], domain, ip, url, '隔离上传文件', "已隔离该木马的文件,无需处理", payload_info, 0, 3)
            self.send_news('隔离上传文件', ip, domain, url, 3, payload_info['filename'])
            if self.Mv_Recycle_bin(payload_info['filename']):
                try:
                    os.remove(payload_info['filename'])
                except:
                    pass
            return



    def set_cache(self,ip, payload_info):
        if not self.__cache.get(ip):
            self.__cache.set(ip, [payload_info], 60)
        else:
            cache_ip = self.__cache.get(ip)
            if len(cache_ip) > 10:
                self.__cache.set(ip, [payload_info], 60)
            else:
                cache_ip.append(payload_info)
                self.__cache.set(ip, cache_ip, 60)

    def GetFIles(self,path):
        if not os.path.exists(path): return False
        data = {}
        data['status'] = True
        data["only_read"] = False
        data["size"] = os.path.getsize(path)
        if os.path.getsize(path)> 1024 * 1024 * 2:return False
        fp = open(path, 'rb')
        if fp:
            srcBody = fp.read()
            fp.close()
            try:
                data['encoding'] = 'utf-8'
                data['data'] = srcBody.decode(data['encoding'])
            except:
                try:
                    data['encoding'] = 'GBK'
                    data['data'] = srcBody.decode(data['encoding'])
                except:
                    try:
                        data['encoding'] = 'BIG5'
                        data['data'] = srcBody.decode(data['encoding'])
                    except:
                        return False
        return True





    def start_payload_info(self,get):
        payload_info=get.payload_info
        domain = payload_info['data']['request']['serverName']
        domain_config=self.site_config_info(domain)
        domain_file=False
        domain_dir=False
        if domain_config and 'file_info' in domain_config:
            for i in domain_config['file_info']:
                if domain_config['file_info'][i]['type']=='file':
                    domain_file=True
                else:
                    domain_dir=True

        if 'data' in payload_info:
            if 'class_id' in payload_info['data']:
                # try:
                fun = self.get_fun(payload_info['data']['class_id'], payload_info['data']['method_id'])
                if not fun:
                    return
                if 'args' in payload_info['data']:
                    args = payload_info['data']['args']
                else:
                    return
                if 'ret' not in payload_info['data']:
                    if fun == "passthru" or fun == "system" or fun == "exec" or fun == "shell_exec" or fun == "proc_open" or fun == "popen" or fun == "pcntl_exec":
                        payload_info['data']['ret'] = 'true'
                    else:
                        return
                ret = payload_info['data']['ret']
                if ret == 'false':
                    return
                payload_info['fun_name'] = fun
                if 'args' not in payload_info['data']:
                    return
                if payload_info['data']['class_id'] == 10:
                    return

                # 判断是否是命令执行的函数
                # 判断是否是任意文件上传
                # -- 任意文件上传 漏洞检测
                try:
                    url = payload_info['data']['request']['uri']
                    url2 = url.split("?")[0]
                    stack_trace = payload_info['data']['stack_trace']
                    ip = payload_info['data']['request']['remoteAddress']


                    rets = []
                    for i in stack_trace:
                        if re.search("\w+\((.+\.php)", i):
                            paths = re.findall("\w+\((.+\.php)", i)[0]
                            if paths not in rets:
                                rets.append(paths)
                    is_webshell=0
                    if len(rets) == 1 and os.path.exists(rets[0]):
                        webshell_scan=self.__plugin_path+"webshell_scan"
                        scan_file=public.ExecShell(webshell_scan+" --file="+rets[0])
                        if scan_file[0]:
                            if re.search("Scan Path Is WebShell",scan_file[0]):
                                if re.search("Rule: (.+)",scan_file[0]):
                                    rule_list=re.findall("Rule: (.+)",scan_file[0])
                                    if rule_list[0] and self.GetFIles(rets[0]):
                                        print("发现webshell木马 "+rets[0]+" 规则为 "+rule_list[0])
                                        payload_info[
                                            'solution'] = "1.该文件经检测为WebShell木马规则为%s|split|2.默认拉入到隔离箱中|split|3.如认为是误报请发帖到宝塔论坛中"%rule_list[0]
                                        payload_info['risk'] = 3
                                        payload_info['intercept'] = 'webshell木马'
                                        self.notice(payload_info, True)
                                        return
                        is_webshell=1
                        self.set_cache(ip, payload_info)
                    get_cache = self.__cache.get(ip)

                except:

                    return
                if fun == "putenv" and is_webshell:
                        LD_PRELOAD = ["putenv(", "eval(", "eval(", "evalFunc(", "run("]
                        file_get = ["file_put_contents(", "eval(", "eval(", "evalFunc(", "run(", "evalFunc("]
                        if 'stack_trace' in payload_info['data']:
                            if self.check_list(payload_info['data']['stack_trace'], LD_PRELOAD):
                                if get_cache and len(get_cache) >= 2:
                                    if get_cache[-2]['data']['stack_trace'] and self.check_list(
                                            get_cache[-2]['data']['stack_trace'],
                                            file_get):
                                        print("哥斯拉 webshell 管理器V4 使用LD_PRELOAD 进行命令执行绕过")
                                        print("正在清理哥斯拉webshell木马")
                                        payload_info[
                                            'solution'] = "1.该文件为哥斯拉webshell工具使用LD_PRELOAD 执行命令|split|2.默认自动把木马文件拉入到隔离箱中|split|3.如认为是误报请发帖到宝塔论坛中"
                                        payload_info['risk'] = 3
                                        payload_info['intercept'] = '哥斯拉webshell工具执行命令'
                                        self.notice(payload_info, True)

                if fun == "move_uploaded_file":
                    if len(args) != 2: return
                    path = args[1]

                    # 如果上传的文件后缀名为php 并且返回值为true
                    if args[0].startswith("/tmp") and path.endswith(".php") and ret == 'true':
                        is_status, domain_path = self.is_open(domain)
                        if is_status: return False

                        #documentRoot = payload_info['data']['request']['documentRoot']
                        if path[0] != '/':
                            filename = os.path.abspath(domain_path + "/" + path)
                        else:
                            filename = os.path.abspath(path)
                        self.write_log("!!!!!!!!!!!任意文件上传" + path)
                        payload_info['intercept'] = '恶意文件上传'
                        payload_info['risk'] = 3
                        payload_info[
                            'solution'] = "1.该url 存在任意文件上传漏洞,上传的文件为[%s]|split|2.请合理的限制文件上传的类型|split|3.请检查文件上传目录中是否还存在木马文件" % path
                        # 判断是否/开头
                        payload_info['path'] = path
                        payload_info['filename'] = filename
                        payload_info['risk'] = 3
                        self.notice(payload_info)
                        # 判断文件是否存在
                elif fun == "copy":
                    if len(args) != 2: return
                    path = args[1]
                    # 如果上传的文件后缀名为php 并且返回值为true
                    if args[0].startswith("/tmp") and path.endswith(".php") and ret == 'true':
                        self.write_log("!!!!!!!!!!!任意文件上传" + path)
                        payload_info['intercept'] = '恶意文件上传'
                        documentRoot = payload_info['data']['request']['documentRoot']
                        # documentRoot = payload_info['data']['request']['documentRoot']
                        # 判断是否/开头
                        if path[0] != '/':
                            filename = os.path.abspath(documentRoot + "/" + path)
                        else:
                            filename = os.path.abspath(path)
                        payload_info['path'] = path
                        payload_info['filename'] = filename
                        payload_info['risk'] = 3
                        payload_info[
                            'solution'] = "1.该url 存在任意文件上传漏洞,上传的文件名为[%s]|split|2.请合理的限制文件上传的类型|split|3.请检查文件上传目录中是否还存在木马文件" % path
                        self.notice(payload_info)
                    elif path.endswith(".php") and ret == 'true':
                        if args[0].startswith("https://") or args[0].startswith("http://"):
                            documentRoot = payload_info['data']['request']['documentRoot']
                            if path[0] != '/':
                                filename = os.path.abspath(documentRoot + "/" + path)
                            else:
                                filename = os.path.abspath(path)
                            payload_info['intercept'] = '远程写入php'
                            payload_info['path'] = path
                            payload_info['filename'] = filename
                            payload_info['risk'] = 3
                            payload_info[
                                'solution'] = "1.该行为从远程下载文件并保存为php文件,写入的文件名为[%s]|split|2.请检查该下载函数是否对外参数|split|3.请检查报存文件中是否为木马文件" % path
                            self.notice(payload_info)
                        # 判断文件是否存在
                elif fun == "file_get_contents":
                    # 判断是否任意文件读取/etc/passwd
                    path = args[0]
                    # 读取本地/etc/passwd文件
                    # 判断args 中是否存在/etc/passwd
                    if not path: return
                    # print("is_webshell", is_webshell)
                    if is_webshell:
                        if path.endswith(".zip") or path.endswith(".rar") or path.endswith("tar") or path.endswith(
                                "gz") or path.endswith("bz2") or path.endswith("7z"):
                            if payload_info['data']['stack_trace']:
                                keyword_list = ["file_get_contents(", "readFileContent(", "evalFunc(", "run("]
                                if self.check_list(payload_info['data']['stack_trace'], keyword_list):
                                    if get_cache and len(get_cache) >= 2:
                                        print("进入到zip")
                                        if get_cache[-2]['data']['stack_trace'] and self.check_list(
                                                get_cache[-2]['data']['stack_trace'], ["scandir(", "bypass_open_basedir("]):
                                            print("哥斯拉 webshell 管理器V4.01 下载压缩包文件", path)
                                            print("正在清理哥斯拉webshell木马")
                                            payload_info[
                                                'solution'] = "1.该文件为哥斯拉webshell工具下载压缩包[%s]|split|2.默认自动把木马文件拉入到隔离箱中|split|3.如认为是误报请发帖到宝塔论坛中"%path
                                            payload_info['risk'] = 3
                                            payload_info['intercept'] = '哥斯拉webshell工具下载压缩包'
                                            self.notice(payload_info, True)

                        elif 'stack_trace' in payload_info['data']:
                            keyword_list = ["file_get_contents(", "readFileContent(", "evalFunc("]

                            getProcInfo = ["file_get_contents(", "getProcInfo(", "eval(", "evalFunc(", "run("]
                            webshell = ["file_get_contents(", "webShellScan(", "eval(", "evalFunc("]
                            disfunpoc = ["file_get_contents(", "read_proc_maps(", "selfpatch(", "eval(", "evalFunc("]
                            procfs_bypess = ["file_get_contents(", "parseelf(", "eval(", "eval(", "evalFunc("]
                            if self.check_list(payload_info['data']['stack_trace'], keyword_list):
                                if get_cache and len(get_cache) >= 2:
                                    if get_cache[-2]['data']['stack_trace'] and self.check_list(
                                            get_cache[-2]['data']['stack_trace'],
                                            ["scandir(", "bypass_open_basedir("]):
                                        if path == "/proc/net/tcp" or path == "/proc/net/udp":
                                            if not self.__cache.get(ip + "getProcInfo"):
                                                self.__cache.set(ip + "getProcInfo", '1', 2)
                                                print("哥斯拉 webshell 管理器V4.01 查看网络详情")
                                                print("正在清理哥斯拉webshell木马")
                                                payload_info[
                                                    'solution'] = "1.该文件为哥斯拉webshell工具查看网络详情|split|2.默认自动把木马文件拉入到隔离箱中|split|3.如认为是误报请发帖到宝塔论坛中"
                                                payload_info['risk'] = 3
                                                payload_info['intercept'] = '哥斯拉webshell工具查看网络详情'
                                                self.notice(payload_info, True)
                                        else:
                                            print("哥斯拉 webshell 管理器V4.01 打开文件%s" % path)
                                            print("正在清理哥斯拉webshell木马")
                                            payload_info[
                                                'solution'] = "1.该文件为哥斯拉webshell工具读取文件[%s]|split|2.默认自动把木马文件拉入到隔离箱中|split|3.如认为是误报请发帖到宝塔论坛中"%path
                                            payload_info['risk'] = 3
                                            payload_info['intercept'] = '哥斯拉webshell工具读取文件'
                                            self.notice(payload_info, True)

                            elif self.check_list(payload_info['data']['stack_trace'], getProcInfo):
                                if get_cache and len(get_cache) >= 2:
                                    if not self.__cache.get(ip + "getProcInfo") and get_cache[-2]['data'][
                                        'stack_trace'] and self.check_list(
                                            get_cache[-2]['data']['stack_trace'], getProcInfo):
                                        self.__cache.set(ip + "getProcInfo", '1', 180)
                                        print("哥斯拉 webshell 管理器V4.01 获取进程信息")
                                        print("正在清理哥斯拉webshell木马")
                                        payload_info[
                                            'solution'] = "1.该文件为哥斯拉webshell工具获取进程信息|split|2.默认自动把木马文件拉入到隔离箱中|split|3.如认为是误报请发帖到宝塔论坛中"
                                        payload_info['risk'] = 3
                                        payload_info['intercept'] = '哥斯拉webshell工具获取进程信息'
                                        self.notice(payload_info, True)
                            elif self.check_list(payload_info['data']['stack_trace'], webshell):
                                if get_cache and len(get_cache) >= 2:
                                    if not self.__cache.get(ip + "webshell") and get_cache[-2]['data'][
                                        'stack_trace'] and self.check_list(
                                            get_cache[-2]['data']['stack_trace'], webshell):
                                        self.__cache.set(ip + "webshell", '1', 180)
                                        print("哥斯拉 webshell 管理器V4.01 检查其他的webshell")
                                        print("正在清理哥斯拉webshell木马")
                                        payload_info[
                                            'solution'] = "1.该文件为哥斯拉webshell工具查杀其他文件|split|2.默认自动把木马文件拉入到隔离箱中|split|3.如认为是误报请发帖到宝塔论坛中"
                                        payload_info['risk'] = 3
                                        payload_info['intercept'] = '哥斯拉webshell工具查杀其他文件'
                                        self.notice(payload_info, True)
                            elif self.check_list(payload_info['data']['stack_trace'], disfunpoc):
                                if get_cache and len(get_cache) >= 2:
                                    if get_cache[-2]['data']['stack_trace'] and self.check_list(
                                            get_cache[-2]['data']['stack_trace'],
                                            ["scandir(", "bypass_open_basedir("]):
                                        if not self.__cache.get(ip + path):
                                            self.__cache.set(ip + path, '1', 180)
                                            print("哥斯拉 webshell 管理器V4.01 disfunpoc 执行命令")
                                            print("正在清理哥斯拉webshell木马")
                                            payload_info[
                                                'solution'] = "1.该文件为哥斯拉webshell工具使用disfunpoc进行命令执行绕过|split|2.默认自动把木马文件拉入到隔离箱中|split|3.如认为是误报请发帖到宝塔论坛中"
                                            payload_info['risk'] = 3
                                            payload_info['intercept'] = '哥斯拉webshell工具执行命令'
                                            self.notice(payload_info, True)
                            elif self.check_list(payload_info['data']['stack_trace'], procfs_bypess):
                                if get_cache and len(get_cache) >= 2:
                                    if get_cache[-2]['data']['stack_trace'] and self.check_list(
                                            get_cache[-2]['data']['stack_trace'],
                                            ["scandir(", "bypass_open_basedir("]):
                                        if not self.__cache.get(ip + path):
                                            self.__cache.set(ip + path, '1', 180)
                                            print("哥斯拉 webshell 管理器V4.01 procfs_bypess 执行命令")
                                            print("正在清理哥斯拉webshell木马")
                                            payload_info[
                                                'solution'] = "1.该文件为哥斯拉webshell工具使用procfs_bypess进行命令执行绕过|split|2.默认自动把木马文件拉入到隔离箱中|split|3.如认为是误报请发帖到宝塔论坛中"
                                            payload_info['risk'] = 3
                                            payload_info['intercept'] = '哥斯拉webshell工具执行命令'
                                            self.notice(payload_info, True)

                    flag = False
                    if path.find("/etc/passwd") != -1 and ret.find("/bin/bash"):
                        print(path,"path")
                        self.write_log("!!!!!!!!!!!任意文件读取" + path)
                        payload_info['risk'] = 2
                        payload_info['intercept'] = '任意文件读取'
                        payload_info['solution'] = "1.该url 任意文件读取漏洞,读取的文件为[%s]|split|2.请合理的限制读取文件的目录" % path
                        self.notice(payload_info)
                        flag = True
                    # file 协议
                    if path.find("file://") != -1:
                        self.write_log("file协议")
                        payload_info['intercept'] = '任意文件读取'
                        payload_info['risk'] = 1
                        payload_info['solution'] = "1.该url 任意文件读取漏洞,读取的文件为[%s]|split|2.请合理限制该参数的协议" % path
                        self.notice(payload_info)
                        flag = True
                    # file 协议
                    if path.find("php://filter/") != -1:
                        self.write_log("php://filter")
                        payload_info['risk'] = 1
                        payload_info['intercept'] = '任意文件读取'
                        payload_info['solution'] = "1.该url 任意文件读取漏洞,读取的文件为[%s]|split|2.请合理限制该参数的协议" % path
                        self.notice(payload_info)
                        flag = True
                    if not flag:
                        # 判断是否是读取其他目录的文件
                        # 1. 获取documentRoot
                        if 'request' in payload_info['data']:
                            if 'documentRoot' in payload_info['data']['request']:
                                documentRoot = payload_info['data']['request']['documentRoot']
                                if documentRoot=="/www/server/phpmyadmin":return False
                                # 判断是否是读取其他目录的文件
                                is_flag = False
                                # 如果documentRoot 最后面是public,则去掉public
                                if len(documentRoot) > 10 and documentRoot[-7:] == "/public":
                                    documentRoot2 = documentRoot
                                    documentRoot = documentRoot[:-7]
                                    if not path.startswith("/"):
                                        #首先啊通过/index.php 这种的获取
                                        path2 = os.path.abspath(documentRoot2 + "/" + path)
                                        if not os.path.exists(os.path.dirname(path2)):
                                           # self.write_log("目录不存在。应该是需要url的方式")
                                            #那么就是documentRoot2+url+path
                                            path_config = '/'.join(url2.split('/')[0:-1])
                                            if path_config:
                                                path = os.path.abspath(documentRoot2 + path_config + "/" + path)
                                            else:
                                                path = os.path.abspath(documentRoot + "/" + path)
                                        else:
                                            path=path2
                                    else:
                                        path = os.path.abspath(path)
                                    is_flag = True
                                # 判断是否/开头
                                if not is_flag:
                                    if not path.startswith("/"):
                                        path_config = '/'.join(url2.split('/')[0:-1])
                                        if path_config:
                                            path = os.path.abspath(documentRoot + path_config + "/" + path)
                                        else:
                                            path = os.path.abspath(documentRoot + "/" + path)
                                    else:
                                        path = os.path.abspath(path)
                                # self.write_log("path:[%s]"%path)
                                # 判断是否不是写入
                                if domain_file or domain_dir:
                                    if path in domain_config['file_info']:
                                        if not self.__cache.get(path + "read"):
                                            payload_info['risk'] = 2
                                            self.__cache.set(path + "read", 1, 60)
                                            payload_info['intercept'] = '文件监控告警'
                                            payload_info[
                                                'solution'] = "1.该URL读取了您设置的告警文件[%s]|split|2.请检查是否存在外部参数调用了此函数|split|3.应当检查当前这个函数是否需要调用其他目录下的文件" % path
                                            self.write_log("触发修改文件告警" + path)
                                            self.write_log("fun: " + fun)
                                            self.notice(payload_info)


                                #判断path 是否是他的子目录
                                is_status, domain_path = self.is_open(domain)
                                if is_status: return False
                                if  path.startswith(domain_path):
                                   return False

                                # 判断是否是读取其他目录的文件
                                if not path.startswith(documentRoot) and not path.startswith(
                                        "/tmp/") and not path.startswith("/proc/") and not path.startswith("/dev/"):
                                    self.write_log("读取了其他目录的文件" + path)
                                    flag = True
                                    payload_info['solution'] = "1.该行为为跨站读取其他目录的文件[%s]|split|2.请检查该函数是否存在对外参数" % path
                                    payload_info['intercept'] = '跨站读取文件'
                                    payload_info['risk'] = 2
                                    self.notice(payload_info)
                elif fun == "passthru" or fun == "system" or fun == "exec" or fun == "shell_exec" or fun == "proc_open" or fun == "popen" or fun == "pcntl_exec":
                    # 判断是否是ls命令
                    # 记录起来
                    path = args[0]
                    self.write_log("命令执行")
                    payload_info['risk'] = 3
                    payload_info['intercept'] = '命令执行'
                    payload_info[
                        'solution'] = "1.该行为为执行了系统命令,执行了命令为[%s]|split|2.请检查是否存在异常命令执行|split|3.应当合理的限制使用命令去执行某些操作|split|4.如存在误报请点击误报即可" % path
                    self.notice(payload_info)
                elif fun == 'fopen' or fun == 'file' or fun == 'readfile' or fun == 'file_put_contents' or fun == 'dir' or fun == 'opendir' or fun == 'scandir' or fun == 'unlink':
                    path = args[0]
                    #判断是否是读取文件



                    if fun=="unlink" and is_webshell:
                        unlink_list=["unlink(","eval(","eval(","evalFunc(","run("]
                        file_get=["file_put_contents(","eval(","eval(","evalFunc(","run("]
                        if 'stack_trace' in payload_info['data']:
                            if self.check_list(payload_info['data']['stack_trace'], unlink_list):
                                if get_cache and len(get_cache) >= 2:
                                    if get_cache[-2]['data']['stack_trace'] and self.check_list(
                                            get_cache[-2]['data']['stack_trace'],
                                            file_get):
                                        print("哥斯拉 webshell 管理器V4 使用FPM-bypass 进行命令执行绕过")
                                        print("正在清理哥斯拉webshell木马")
                                        payload_info[
                                            'solution'] = "1.该文件为哥斯拉webshell工具使用FPM-bypass 进行命令执行绕过|split|2.默认自动把木马文件拉入到隔离箱中|split|3.如认为是误报请发帖到宝塔论坛中"
                                        payload_info['risk'] = 3
                                        payload_info['intercept'] = '哥斯拉webshell工具执行命令'
                                        self.notice(payload_info, True)

                    if fun=="fopen" and is_webshell:
                        if path.endswith(".zip") or path.endswith(".rar") or path.endswith("tar") or path.endswith(
                            "gz") or path.endswith("bz2") or path.endswith("7z"):
                            if payload_info['data']['stack_trace']:
                                keyword_list=["fopen(","bigFileDownload(","evalFunc(","run("]
                                if self.check_list(payload_info['data']['stack_trace'],keyword_list):
                                    if self.check_list(payload_info['data']['stack_trace'], keyword_list):
                                        if get_cache and  len(get_cache) >= 2:
                                            if get_cache[-2]['data']['stack_trace'] and self.check_list(
                                                    get_cache[-2]['data']['stack_trace'],
                                                    ["scandir(", "bypass_open_basedir("]):
                                                if not self.__cache.get(ip+path):
                                                    self.__cache.set(ip+path,'1',180)
                                                    print("哥斯拉 webshell 管理器V4.01 大文件下载压缩包文件%s"%path)
                                                    print("正在清理哥斯拉webshell木马")
                                                    payload_info[
                                                        'solution'] = "1.该文件为哥斯拉webshell工具大文件下载文件[%s]|split|2.默认自动把木马文件拉入到隔离箱中|split|3.如认为是误报请发帖到宝塔论坛中"%path
                                                    payload_info['risk'] = 3
                                                    payload_info['intercept'] = '哥斯拉webshell工具大文件下载'
                                                    self.notice(payload_info, True)

                        elif path=="php://memory":
                            bypss_comm =["fopen(", "make_uaf_obj(", "go(", "fwrite(", "pwn(", "eval("]
                            if self.check_list(payload_info['data']['stack_trace'], bypss_comm):
                                if get_cache and len(get_cache) >= 2:
                                    if get_cache[-2]['data']['stack_trace'] and self.check_list(get_cache[-2]['data']['stack_trace'],["fopen(", "pwn(", "eval(", "eval(", "evalFunc("]):
                                            print("哥斯拉 webshell 管理器V4.01 php-fiter-bypass 命令执行")
                                            print("正在清理哥斯拉webshell木马")
                                            payload_info[
                                                'solution'] = "1.该文件为哥斯拉webshell工具的命令执行绕过行为|split|2.默认自动把木马文件拉入到隔离箱中|split|3.如认为是误报请发帖到宝塔论坛中"
                                            payload_info['risk'] = 3
                                            payload_info['intercept'] = '哥斯拉webshell工具执行命令'
                                            self.notice(payload_info, True)
                        elif path.endswith(".antproxy.php"):
                            bypss_comm = ["fopen(", "eval("]
                            if self.check_list(payload_info['data']['stack_trace'], bypss_comm,1):
                                bypss_comm = ["putenv(", "eval("]
                                bypss_comm2 = ["fopen(", "eval("]

                                if get_cache and len(get_cache) >= 2:
                                    if get_cache[-2]['data']['stack_trace'] and self.check_list(get_cache[-2]['data']['stack_trace'],bypss_comm,1):
                                            print("蚁剑 webshell 管理器  LD_PRELOAD 命令执行")
                                            print("正在清理蚁剑webshell木马")
                                            payload_info[
                                                'solution'] = "1.该文件为蚁剑webshell工具的 LD_PRELOAD 命令执行绕过行为|split|2.默认自动把木马文件拉入到隔离箱中|split|3.如认为是误报请发帖到宝塔论坛中"
                                            payload_info['risk'] = 3
                                            payload_info['intercept'] = '蚁剑webshell工具执行命令'
                                            self.notice(payload_info, True)
                                    if get_cache[-2]['data']['stack_trace'] and self.check_list(
                                        get_cache[-2]['data']['stack_trace'], bypss_comm2, 1):
                                            if get_cache[-2]['data']['args'][0].startswith("/tmp/."):
                                                print("蚁剑 webshell 管理器  FastCgi/Fpm 命令执行")
                                                print("正在清理蚁剑webshell木马")
                                                payload_info[
                                                    'solution'] = "1.该文件为蚁剑webshell工具的 FastCgi/Fpm 命令执行绕过行为|split|2.默认自动把木马文件拉入到隔离箱中|split|3.如认为是误报请发帖到宝塔论坛中"
                                                payload_info['risk'] = 3
                                                payload_info['intercept'] = '蚁剑webshell工具执行命令'
                                                self.notice(payload_info, True)

                    if fun=="file_put_contents" and is_webshell:
                        if 'stack_trace' in payload_info['data']:
                            new_file=["file_put_contents(", "newFile(", "evalFunc(", "run("]
                            upload_file=["file_put_contents(", "uploadFile(", "evalFunc(", "run("]
                            if self.check_list(payload_info['data']['stack_trace'],new_file):
                                if get_cache and len(get_cache) >= 2:
                                    if get_cache[-2]['data']['stack_trace'] and self.check_list(
                                            get_cache[-2]['data']['stack_trace'],
                                            ["scandir(", "bypass_open_basedir("]):
                                        if not self.__cache.get(ip+path):
                                            self.__cache.set(ip+path,'1',180)
                                            print("哥斯拉 webshell 管理器V4.01 新建文件%s"%path)
                                            print("正在清理哥斯拉webshell木马")
                                            payload_info[
                                                'solution'] = "1.该文件为哥斯拉webshell工具的新建文件行为[%s]|split|2.默认自动把木马文件拉入到隔离箱中|split|3.如认为是误报请发帖到宝塔论坛中"%path
                                            payload_info['risk'] = 3
                                            payload_info['intercept'] = '哥斯拉webshell工具文件上传'
                                            self.notice(payload_info, True)
                            elif self.check_list(payload_info['data']['stack_trace'],upload_file):
                                if get_cache and len(get_cache) >= 2:
                                    if get_cache[-2]['data']['stack_trace'] and self.check_list(
                                            get_cache[-2]['data']['stack_trace'],
                                            ["scandir(", "bypass_open_basedir("]):
                                        if not self.__cache.get(ip+path):
                                            self.__cache.set(ip+path,'1',180)
                                            print("哥斯拉 webshell 管理器V4.01 上传文件%s"%path)
                                            print("正在清理哥斯拉webshell木马")
                                            payload_info[
                                                'solution'] = "1.该文件为哥斯拉webshell工具的上传文件行为[%s]|split|2.默认自动把木马文件拉入到隔离箱中|split|3.如认为是误报请发帖到宝塔论坛中"%path
                                            payload_info['risk'] = 3
                                            payload_info['intercept'] = '哥斯拉webshell工具上传文件'
                                            self.notice(payload_info, True)

                    if 'request' in payload_info['data']:
                        if 'documentRoot' in payload_info['data']['request']:
                            documentRoot = payload_info['data']['request']['documentRoot']
                            if documentRoot == "/www/server/phpmyadmin": return False
                            # 判断是否是读取其他目录的文件
                            is_flag = False
                            # 如果documentRoot 最后面是public,则去掉public
                            if len(documentRoot) > 10 and documentRoot[-7:] == "/public":
                                documentRoot2 = documentRoot
                                documentRoot = documentRoot[:-7]
                                if not path.startswith("/"):
                                    # 首先啊通过/index.php 这种的获取
                                    path2 = os.path.abspath(documentRoot2 + "/" + path)
                                    if not os.path.exists(os.path.dirname(path2)):
                                        # self.write_log("目录不存在。应该是需要url的方式")
                                        # 那么就是documentRoot2+url+path
                                        path_config = '/'.join(url2.split('/')[0:-1])
                                        if path_config:
                                            path = os.path.abspath(documentRoot2 + path_config + "/" + path)
                                        else:
                                            path = os.path.abspath(documentRoot + "/" + path)
                                    else:
                                        path = path2
                                else:
                                    path = os.path.abspath(path)
                                is_flag = True
                            # 判断是否/开头
                            if not is_flag:
                                if not path.startswith("/"):
                                    path_config = '/'.join(url2.split('/')[0:-1])
                                    if path_config:
                                        path = os.path.abspath(documentRoot + path_config + "/" + path)
                                    else:
                                        path = os.path.abspath(documentRoot + "/" + path)
                                else:
                                    path = os.path.abspath(path)

                            #读取文件告警 读取文件的时候，如果是读取的是配置文件，那么就告警
                            if domain_file or domain_dir:
                                if path in domain_config['file_info']:
                                    #读取文件
                                    payload_info['risk'] = 2
                                    if domain_config['file_info'][path]['reit'] == "1" and fun == 'fopen' or fun == 'file' or fun == 'readfile':
                                        #判断是否不是写入
                                       if not self.__cache.get(path + "read"):
                                           self.__cache.set(path + "read", 1, 60)
                                           payload_info['intercept'] = '文件监控告警'
                                           payload_info[
                                               'solution'] = "1.该URL读取了您设置的告警文件[%s]|split|2.请检查是否存在外部参数调用了此函数|split|3.应当检查当前这个函数是否需要调用其他目录下的文件" % path
                                           self.write_log("触发修改文件告警" + path)
                                           self.write_log("fun: " + fun)
                                           self.notice(payload_info)

                                    #修改文件的告警
                                    if  domain_config['file_info'][path]['reit'] == "1" and fun == 'file_put_contents':
                                        if not self.__cache.get(path + "reit"):
                                            self.__cache.set(path + "reit", 1, 60)
                                            payload_info['intercept'] = '文件监控告警'
                                            payload_info[
                                                'solution'] = "1.该URL修改了您设置的告警文件[%s]|split|2.请检查是否存在外部参数调用了此函数|split|3.应当检查当前这个函数是否需要调用其他目录下的文件" % path
                                            self.write_log("触发修改文件告警" + path)
                                            self.write_log("fun: " + fun)
                                            self.notice(payload_info)
                                    #删除文件的告警
                                    if domain_config['file_info'][path]['del'] == "1" and fun == 'unlink':
                                        if not self.__cache.get(path + "del"):
                                            self.__cache.set(path + "del", 1, 60)
                                            payload_info['intercept'] = '文件监控告警'
                                            payload_info[
                                                'solution'] = "1.该URL删除了您设置的告警文件或目录[%s]|split|2.请检查是否存在外部参数调用了此函数|split|3.应当检查当前这个函数是否需要调用其他目录下的文件" % path
                                            self.write_log("触发修改文件告警" + path)
                                            self.write_log("fun: " + fun)
                                            self.notice(payload_info)
                                    #目录告警
                                    if domain_config['file_info'][path]['read'] == "1" and  fun == 'dir' or fun == 'opendir' or fun == 'scandir':
                                        if not self.__cache.get(path + "read"):
                                            self.__cache.set(path + "read", 1, 60)
                                            payload_info['intercept'] = '文件监控告警'
                                            payload_info[
                                                'solution'] = "1.该URL读取了您设置的告警目录[%s]|split|2.请检查是否存在外部参数调用了此函数|split|3.应当检查当前这个函数是否需要调用其他目录下的文件" % path
                                            self.write_log("触发修改文件告警" + path)
                                            self.write_log("fun: " + fun)
                                            self.notice(payload_info)
                            # 判断path 是否是他的子目录
                            is_status, domain_path = self.is_open(domain)
                            if is_status: return False
                            if path.startswith(domain_path):
                                return False
                            # 判断是否是读取其他目录的文件
                            if not path.startswith(documentRoot) and not path.startswith("/tmp/") and not path.startswith("/proc/") and not path.startswith("/dev/"):
                                payload_info['risk'] = 2
                                if fun == 'fopen' or fun == 'file' or fun == 'readfile':
                                    payload_info['intercept'] = '跨站读取文件'
                                    payload_info[
                                        'solution'] = "1.该URL读取了其他目录下的文件[%s]|split|2.请检查是否存在外部参数调用了此函数|split|3.应当检查当前这个函数是否需要调用其他目录下的文件" % path
                                if fun == 'file_put_contents':
                                    payload_info['intercept'] = '跨站写入文件'
                                    payload_info[
                                        'solution'] = "1.该行为为写入文件到其他目录中[%s]|split|2.请检查该行为是否是写入了木马文件|split|3.应当检查好该函数调用过程中是否存在外部调用" % path
                                if fun == 'dir' or fun == 'opendir' or fun == 'scandir':
                                    if path=="/proc" or path=="/dev" or path=="/tmp":
                                        return False
                                    payload_info['intercept'] = '跨站打开目录'
                                    payload_info[
                                        'solution'] = "1.该行为为列出了目录[%s]中的具体文件|split|2.请检查该操作是否符合程序规范|split|3.应当检查好该函数调用过程中是否存在外部调用" % path
                                if fun == 'unlink':
                                    payload_info['risk'] = 3
                                    payload_info['intercept'] = '跨站删除文件'
                                    payload_info[
                                        'solution'] = "1.该行为是删除非当前目录的文件[%s]|split|2.请检查该操作是否符合程序规范|split|3.应当检查好该函数调用过程中是否存在外部调用" % path
                                self.write_log("操作了其他目录的文件或者目录" + path)
                                self.write_log("fun: " + fun)
                                self.notice(payload_info)
                elif fun == 'gethostbyname':
                    doamin = args[0]
                    if doamin.endswith(".dnslog.cn"):
                        if doamin.endswith("test.www.dnslog.cn"):
                            payload_info['intercept'] = '模拟测试'
                            payload_info[
                                'solution'] = "1.模拟测试"
                            payload_info['risk'] = 1
                            self.notice(payload_info)
                        else:
                            self.write_log("存在dnslog 探测")
                            payload_info[
                                'solution'] = "1.该行为应为向外发送dns请求|split|2.如触发此行为大概为存在ssrf漏洞|split|3.应该查看程序调用栈的具体过程"
                            payload_info['risk'] = 1
                            payload_info['intercept'] = 'dnslog探测'
                            self.notice(payload_info)
                    beixie = ["gethostbyname(", "main(", "eval(", "eval(", "__invoke("]
                    file_get = ["file_put_contents("]
                    if is_webshell and 'stack_trace' in payload_info['data']:
                        if self.check_list(payload_info['data']['stack_trace'], beixie):
                            if get_cache and len(get_cache) >= 3:
                                if get_cache[-2]['data']['stack_trace'] and self.check_list(
                                        get_cache[-2]['data']['stack_trace'],
                                        file_get) and get_cache[-3]['data']['stack_trace'] and self.check_list(
                                    get_cache[-3]['data']['stack_trace'],
                                    file_get):
                                    print("冰蝎 Webshell连接行为")
                                    print("正在清理冰蝎webshell木马")
                                    payload_info[
                                        'solution'] = "1.该文件为冰蝎webshell管理工具的链接行为|split|2.默认自动把木马文件拉入到隔离箱中|split|3.如认为是误报请发帖到宝塔论坛中"
                                    payload_info['risk'] = 3
                                    payload_info['intercept'] = '冰蝎webshell连接'
                                    self.notice(payload_info, True)

                elif fun == 'curl_exec':
                    path = args[0]
                    if not path: return
                    flag = False

                    if path.find("/etc/passwd") != -1 and ret.find("/bin/bash"):
                        payload_info['intercept'] = '任意文件读取'
                        payload_info['risk'] = 2
                        payload_info[
                            'solution'] = "1.存在任意文件读取,读取的文件为[%s]|split|2.请限制好对外发送请求的格式|split|3.应当检查对外请求的头部是否为http或https" % path
                        self.notice(payload_info)
                        flag = True
                    # file 协议
                    if path.find("file://") != -1:
                        self.write_log("file协议")
                        payload_info['risk'] = 2
                        payload_info[
                            'solution'] = "1.存在任意文件读取,读取的文件为[%s]|split|2.请限制好对外发送请求的格式|split|3.应当检查对外请求的头部是否为http或https" % path
                        payload_info['intercept'] = '任意文件读取'
                        self.notice(payload_info)
                    # file 协议
                    if path.find("php://filter/") != -1:
                        self.write_log("php://filter")
                        payload_info['risk'] = 2
                        payload_info[
                            'solution'] = "1.存在任意文件读取,读取的文件为[%s]|split|2.请限制好对外发送请求的格式|split|3.应当检查对外请求的头部是否为http或https" % path
                        payload_info['intercept'] = '任意文件读取'
                        self.notice(payload_info)
                elif fun == 'rename':
                    oldname = args[0]
                    newname = args[1]
                    if  newname.endswith('.php'):
                        end = oldname.split('.')[-1]
                        end_list=['png','jpg','gif','jpge','css','js','html','xml']
                        if end in end_list:
                            self.write_log("fun" + fun)
                            payload_info['risk'] = 3
                            payload_info[
                                'solution'] = "1.非php文件重命名为php,源文件为[%s] 重命名后的文件为[%s]|split|2.检查该修改的文件是否为木马" % (
                            oldname, newname)
                            self.write_log("重命名为php文件")
                            payload_info['intercept'] = '恶意重命名'
                            self.notice(payload_info)
                else:
                    pass
