
#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <287962566@qq.com>
#-------------------------------------------------------------------

#------------------------------
# 堡塔网站加速
#------------------------------
import sys,os,re,json,time
os.chdir('/www/server/panel')
sys.path.insert(0,'class/')
import public
if __name__ != "__main__":
    from BTPanel import session

class site_speed_main:

    _plugin_path = 'plugin/site_speed'
    _config_file = _plugin_path + '/config.json'
    _rules_file = _plugin_path + '/rules.json'
    _sp_config = 'vhost/nginx/speed.conf'
    _init_path = '/www/server/speed'
    __server_path = '/www/server/'
    _init_config_file = _init_path + '/config.lua'
    _init_total_path = _init_path + '/total'
    _log_name = '站点加速'
    __session_name = 'site_speed_' + time.strftime('%Y-%m-%d')
    _config = {}
    _server_type = None

    def __init__(self):
        self._server_type = public.get_webserver()
        if not os.path.exists(self._init_total_path):
            os.makedirs(self._init_total_path)
            public.ExecShell("chown www:www {}".format(self._init_total_path))


    def get_site_speed_auth(self):
        import panelAuth
        if self.__session_name in session:
            if session[self.__session_name] != 0:
                return session[self.__session_name]


        cloudUrl = public.GetConfigValue('home')+'/api/panel/get_soft_list_test'
        pdata = panelAuth.panelAuth().create_serverid(None)
        ret = public.httpPost(cloudUrl, pdata)
        skey = public.md5(self.__session_name + '_sp_le')
        if not ret:
            if not self.__session_name in session:
                session[self.__session_name] = 1
                session[skey] = 3
            return 1
        try:
            ret = json.loads(ret)
            s_time = time.time()
            if ret['ltd'] > s_time:
                session[skey] = 0
            elif ret['pro'] > s_time or ret['pro'] == 0:
                session[skey] = 1
            else:
                session[skey] = 3
            session[self.__session_name] = 1
            return 1
        except:
            session[self.__session_name] = 1
            session[skey] = 3
            return 1

    def get_site_list(self,args):
        '''
            @name 获取网站列表
            @author hwliang<2020-06-02>
            @param today string(指定日期)
            @return list
        '''
        if not self._server_type in ['nginx','apache']:
            return public.returnMsg(False,'只支持Apache/Nginx')

        if self._server_type == 'apache':
            mem_res = self.check_memcached()
            if mem_res: return mem_res
        else:
            res = self.check_nginx()
            if res: return public.returnMsg(False,res)

        if self.get_site_speed_auth() == 0:
            return False

        self.sync_sites()
        if not 'today' in args:
            args.today = None
        data = []
        for k in self._config['sites'].keys():
            site_info = self._config['sites'][k].copy()
            site_info['total'] = self.get_site_total(k,args.today)
            site_info['site_name'] = k
            data.append(site_info)
        skey = public.md5(self.__session_name + '_sp_le')
        level_max = [ 0,800000,50000,50000]
        level_msg = [
            "<span style='color:green;'>当前为【企业版】，可无限制加速网站</span>",
            "<span style='color:cornflowerblue;'>当前为【专业版】，每天加速次数为[{}次]，升级到企业版可无限加速</span>".format(level_max[1]),
            "",
            "<span style='color:red;'>当前为【免费版】，每天加速次数为[{}次]，升级专业版提升至[{}次]，升级企业版可无限加速</span>".format(level_max[3],level_max[1])]

        level = session.get(skey,3)
        result = {
            "version": level_msg[level],
            "data": data,
            "max": level_max[level]
        }
        return result

    def check_conf(self):
        '''
            @name 检查配置文件
            @author hwliang<2020-07-31>
            @return None
        '''
        apache_conf_waf = 'vhost/apache/btwaf.conf'
        if not os.path.exists(apache_conf_waf):
            public.writeFile(apache_conf_waf,"LoadModule lua_module modules/mod_lua.so")
            public.ServiceReload()

    def check_apache(self):
        '''
            @name 检查apache是否能正常运行网站加速
            @author hwliang<2021-03-24>
            @return mixed
        '''



    def check_nginx(self):
        '''
            @name 检查nginx是否能正常运行网站加速
            @author hwliang<2021-03-24>
            @return mixed
        '''
        if not os.path.exists('/www/server/nginx/sbin/nginx'):
            return 'Nginx未安装，请到软件商店安装!'
        if not public.ExecShell('ps aux|grep /www/server/nginx/sbin/nginx|grep -v grep')[0]:
            return 'Nginx服务未启动，请到软件商店启动nginx服务!'
        if not public.ExecShell('/www/server/nginx/sbin/nginx -V 2>&1|grep lua_nginx_module|grep -v grep')[0]:
            return "当前Nginx版本不支持网站加速,请尝试重装新的nginx版本!"
        if not os.path.exists(self.__server_path + '/panel/vhost/nginx/speed.conf'):
            return "网站加速引用配置文件损坏，请尝试重新安装网站加速插件!"
        if not os.path.exists(self._init_path + '/speed.lua'):
            return "网站加速主程序文件损坏，请尝试重新安装网站加速插件!"
        return False



    def check_memcached(self):
        '''
            @name 检查memcached是否正常
            @author hwliang<2020-07-22>
            @return dict or None
        '''

        if not os.path.exists('/usr/local/memcached/bin/memcached'):
            return public.returnMsg(False,'没有找到memcached，请到[软件商店]安装memcached后再使用!')
        if not os.path.exists('/var/run/memcached.pid'):
            return public.returnMsg(False,'memcached未启动,请到[软件商店]启动memcached服务!')

    def write_log(self,log):
        '''
            @name 写操作日志
            @author hwliang<2020-06-02>
            @param log string(日志内容)
            @return void
        '''
        public.WriteLog(self._log_name,log)

    def get_site_find(self,args):
        '''
            @name 获取指定站点规则
            @author hwliang<2020-06-02>
            @param siteName string(网站名称)
            @return dict
        '''
        self.read_config()
        data = self._config['sites'][args.siteName]
        if data['white']['ip']:
            ips = []
            for i in data['white']['ip']:
                ips.append("{}-{}".format(self.long2ip(i[0]),self.long2ip(i[1])))
            data['white']['ip'] = ips
        return data

    def get_site_rule(self,args):
        '''
            @name 获取指定站点规则
            @author hwliang<2020-06-02>
            @param siteName string(网站名称)
            @param ruleRoot string(规则路径, force/white)
            @param ruleKey string(规则Key)
            @return list
        '''
        site_info = self.get_site_find(args)
        return site_info[args.ruleRoot][args.ruleKey]

    def set_site_config(self,args):
        '''
            @name 修改站点配置
            @author hwliang<2020-06-02>
            @param siteName string(网站名称)
            @param confKey string(规则Key)
            @param confValue mixed(规则内容)
            @return dict
        '''
        if  args.confKey in ['expire']:
            args.confValue = int(args.confValue)
        elif args.confKey in ['empty_cookie','open']:
            if args.confValue in ['0','false','False']:
                args.confValue = False
            else:
                args.confValue = True
        self.read_config()
        self._config['sites'][args.siteName][args.confKey] = args.confValue
        self.save_config()
        self.write_log('网站：{}，设置{} = {}'.format(args.siteName,args.confKey,args.confValue))
        return public.returnMsg(True,'设置成功!')

    def set_site_status(self,args):
        '''
            @name 修改站点状态
            @author hwliang<2020-06-02>
            @param siteName string(网站名称)
            @return dict
        '''
        self.read_config()
        self._config['sites'][args.siteName]['open'] = not self._config['sites'][args.siteName]['open']
        self.save_config()
        status = {True:"开启",False:"关闭"}
        self.write_log('网站：{}，设置加速状态为: {}'.format(args.siteName,status[self._config['sites'][args.siteName]['open']]))
        return public.returnMsg(True,'设置成功!')

    def long2ip(self,ips):
        '''
            @name 将整数转换为IP地址
            @author hwliang<2020-06-11>
            @param ips string(ip地址整数)
            @return ipv4
        '''
        i1 = int(ips / (2 ** 24))
        i2 = int((ips - i1 * ( 2 ** 24 )) / ( 2 ** 16 ))
        i3 = int(((ips - i1 * ( 2 ** 24 )) - i2 * ( 2 ** 16 )) / ( 2 ** 8))
        i4 = int(((ips - i1 * ( 2 ** 24 )) - i2 * ( 2 ** 16 )) - i3 * ( 2 ** 8))
        return "{}.{}.{}.{}".format(i1,i2,i3,i4)

    def ip2long(self,ip):
        '''
            @name 将IP地址转换为整数
            @author hwliang<2020-06-11>
            @param ip string(ipv4)
            @return long
        '''
        ips = ip.split('.')
        if len(ips) != 4: return 0
        iplong = 2 ** 24 * int(ips[0]) + 2 ** 16 * int(ips[1])  + 2 ** 8 * int(ips[2])  + int(ips[3])
        return iplong


    def create_rule(self,args):
        '''
            @name 缓存规则向导
            @author hwliang<2020-06-06>
            @param siteName string(网站名称)
            @param rules json(规则数组)
            @return dict
        '''

        rules = json.loads(args.rules)
        self.read_config()
        if not args.siteName in self._config['sites'].keys():
            return public.returnMsg(False,'指定网站不存在!')

        for k in rules.keys():
            if k in ['white','force']:
                for kv in rules[k].keys():
                    for v in rules[k][kv]:
                        if v in self._config['sites'][args.siteName][k][kv]: continue
                        self._config['sites'][args.siteName][k][kv].append(v)

            elif k == 'rule':
                self._config['sites'][args.siteName][k] = rules[k]
            elif k == 'login_success':
                self._config['sites'][args.siteName][k] = rules[k]
            elif k == 'login_out':
                self._config['sites'][args.siteName][k] = rules[k]
            elif k == 'expire':
                self._config['sites'][args.siteName][k] = rules[k]
            elif k == 'empty_cookie':
                self._config['sites'][args.siteName][k] = rules[k]
            else:
                self._config['sites'][args.siteName][k] = rules[k]


        self.save_config()
        self.write_log('网站：{}，通过缓存向导配置规则'.format(args.siteName))
        return public.returnMsg(True,'配置成功!')


    def create_login_rule(self,args):
        '''
            @name 创建登录规则
            @author hwliang<2020-06-06>
            @param siteName string(网站名称)
            @param rules json(规则数组)
            @return dict
        '''
        rules = json.loads(args.rules)
        self.read_config()
        if not args.siteName in self._config['sites'].keys():
            return public.returnMsg(False,'指定网站不存在!')

        self._config['sites'][args.siteName]['login_success'] = rules
        self.write_log('网站：{}，创建登录规则'.format(args.siteName))
        return public.returnMsg(True,'设置成功!')


    def create_loginout_rule(self,args):
        '''
            @name 创建登出规则
            @author hwliang<2020-06-06>
            @param siteName string(网站名称)
            @param rules json(规则数组)
            @return dict
        '''
        rules = json.loads(args.rules)
        self.read_config()
        if not args.siteName in self._config['sites'].keys():
            return public.returnMsg(False,'指定网站不存在!')

        self._config['sites'][args.siteName]['login_out'] = rules
        self.write_log('网站：{}，创建登出规则'.format(args.siteName))
        return public.returnMsg(True,'设置成功!')

    def clean_cache(self,args):
        '''
            @name 清空缓存
            @author hwliang<2020-06-06>
            @return dict
        '''
        if self._server_type == 'nginx':
            public.ExecShell("/etc/init.d/nginx restart")
        else:
            if not os.path.exists('/usr/bin/nc'):
                if os.path.exists('/usr/bin/apt'):
                    os.system("apt install ncat -y")
                else:
                    os.system("yum install nc -y")

            public.ExecShell("echo 'flush_all' | nc localhost 11211")
        self.write_log('已清空缓存')
        return public.returnMsg(True,'缓存已清除!')

    def add_site_rule(self,args):
        '''
            @name 添加规则
            @author hwliang<2020-06-02>
            @param siteName string(网站名称)
            @param ruleRoot string(规则路径, force/white)
            @param ruleKey string(规则Key)
            @param ruleValue mixed(规则内容)
            @return dict
        '''
        self.read_config()
        if args.ruleKey == 'ip':
            if args.ruleValue.find('[') == -1: return public.returnMsg(False,'错误的IP段格式')
            if args.ruleValue.find(':') != -1: return public.returnMsg(False,'不支持IPv6地址')
            ip_tmp = json.loads(args.ruleValue)
            ip_len = len(ip_tmp)
            if ip_len == 0 or ip_len > 2: return public.returnMsg(False,'错误的IP段格式')
            if ip_len == 1: ip_tmp.append(ip_tmp[0])
            args.ruleValue = [self.ip2long(ip_tmp[0]),self.ip2long(ip_tmp[1])]

        elif args.ruleKey == 'status':
            args.ruleValue = int(args.ruleValue)
        elif args.ruleKey == 'method':
            args.ruleValue = args.ruleValue.upper()
        elif args.ruleKey == 'ext':
            while args.ruleValue[0] in ['.','*']:
                args.ruleValue = args.ruleValue[1:]

        if args.ruleValue in self._config['sites'][args.siteName][args.ruleRoot][args.ruleKey]:
            return public.returnMsg(False,'指定规则已在存!')
        self._config['sites'][args.siteName][args.ruleRoot][args.ruleKey].insert(0,args.ruleValue)
        self.save_config()
        self.write_log('网站：{},添加规则到：{}，规则内容：{}'.format(args.siteName,args.ruleRoot + '/' + args.ruleKey,args.ruleValue))
        return public.returnMsg(True,'添加成功!')


    def remove_site_rule(self,args):
        '''
            @name 删除规则
            @author hwliang<2020-06-02>
            @param siteName string(网站名称)
            @param ruleRoot string(规则路径, force/white)
            @param ruleKey string(规则Key)
            @param ruleValue mixed(规则内容)
            @return dict
        '''
        self.read_config()

        if args.ruleKey == 'ip':
            if args.ruleValue.find('[') == -1: return public.returnMsg(False,'错误的IP段格式')
            if args.ruleValue.find(':') != -1: return public.returnMsg(False,'不支持IPv6地址')
            ip_tmp = json.loads(args.ruleValue)
            ip_len = len(ip_tmp)
            if ip_len == 0 or ip_len > 2: return public.returnMsg(False,'错误的IP段格式')
            if ip_len == 1: ip_tmp.append(ip_tmp[0])
            args.ruleValue = [self.ip2long(ip_tmp[0]),self.ip2long(ip_tmp[1])]
        elif args.ruleKey == 'status':
            args.ruleValue = int(args.ruleValue)
        elif args.ruleKey == 'method':
            args.ruleValue = args.ruleValue.upper()
        elif args.ruleKey == 'ext':
            while args.ruleValue[0] in ['.','*']:
                args.ruleValue = args.ruleValue[1:]

        if not args.ruleValue in self._config['sites'][args.siteName][args.ruleRoot][args.ruleKey]:
            return public.returnMsg(False,'指定规则不在存!')

        self._config['sites'][args.siteName][args.ruleRoot][args.ruleKey].remove(args.ruleValue)
        self.save_config()
        self.write_log('网站：{},从：{}，删除规则内容：{}'.format(args.siteName,args.ruleRoot + '/' + args.ruleKey,args.ruleValue))
        return public.returnMsg(True,'删除成功!')

    def get_site_total(self,siteName,today=None):
        '''
            @name 取指定站点统计
            @author hwliang<2020-06-02>
            @param siteName string(网站名称)
            @param today string(指定日期)
            @return 网站总请求，网站总命中，网站今日请求，网站今日命中
        '''
        site_total_path = self._init_total_path + '/' + siteName
        if not os.path.exists(site_total_path):
            return 0,0,0,0

        #总命中
        site_total_hit_file = site_total_path + '/hit.json'
        site_total_hit = 0
        total_tmp = public.readFile(site_total_hit_file)
        if total_tmp:
            site_total_hit = int(total_tmp)
        #总请求
        site_total_req_file = site_total_path + '/total.json'
        site_total_req = 0
        total_tmp = public.readFile(site_total_req_file)
        if total_tmp:
            site_total_req = int(total_tmp)
        #生成日期
        if not today:
            today = public.format_date("%Y-%m-%d")
        #当日命中
        site_total_hit_today_file = site_total_path + '/hit/'+today+'.json'
        site_total_today_hit = 0
        total_tmp = public.readFile(site_total_hit_today_file)
        if total_tmp:
            site_total_today_hit = int(total_tmp)
        #当日请求
        site_total_req_today_file = site_total_path + '/request/'+today+'.json'
        site_total_today_req = 0
        total_tmp = public.readFile(site_total_req_today_file)
        if total_tmp:
            site_total_today_req = int(total_tmp)

        return site_total_req+site_total_hit,site_total_hit,site_total_today_req+site_total_today_hit,site_total_today_hit


    def get_settings(self,args):
        '''
            @name 获取全局配置
            @author hwliang<2020-06-02>
            @return dict
        '''
        self.read_config()
        return self._config['settings']

    def set_settings(self,args):
        '''
            @name 设置全局配置
            @author hwliang<2020-06-02>
            @return dict
        '''
        self.read_config()
        status = [False,True]
        if 'open' in args:
            self._config['settings']['open'] = status[int(args.open)]
        if 'ip_for' in args:
            self._config['settings']['ip_for'] = json.loads(args.ip_for)
        if 'cache' in args:
            self._config['settings']['cache'] = json.loads(args.cache)
            sp_conf = public.readFile(self._sp_config)
            sp_conf = re.sub(r"lua_shared_dict\s+site_cache\s+\d+m;",'lua_shared_dict site_cache {}m;'.format(self._config['settings']['cache']['size']),sp_conf)
            public.writeFile(self._sp_config,sp_conf)
        self.save_config()
        self.write_log('设置全局配置为：{}'.format(self._config['settings']))
        return public.returnMsg(True,'配置已保存')

    def get_rules(self,args = None):
        '''
            @name 获取专属规则列表
            @author hwliang<2020-06-02>
            @return list
        '''
        force = None
        if args:
            if 'force' in args:
                force = args.force
        from BTPanel import cache
        rules = cache.get('site_speed_rule')
        if not rules or force:
            _url = public.get_url() + '/install/plugin/site_speed/rule.json'
            rules = public.httpGet(_url)
            try:
                json.loads(rules)
                if not rules:
                    if os.path.exists(self._rules_file):
                        rules = public.readFile(self._rules_file)
                    else:
                        rules = '[]'
                else:
                    cache.set('site_speed_rule',rules,3600)
                    public.writeFile(self._rules_file,rules)
            except:
                rules = public.readFile(self._rules_file)

        return json.loads(rules)

    def get_sites(self):
        self.read_config()
        return list(self._config['sites'].keys())

    def get_rule_list(self,args):
        '''
            @name 获取专属规则列表(前端)
            @author hwliang<2020-06-02>
            @return dict
        '''
        data = {
            "rule_list": self.get_rules(args),
            "site_list": self.get_sites()
        }

        return data


    def get_rule_find(self,ruleName):
        '''
            @name 获取指定专属规则
            @author hwliang<2020-06-02>
            @param ruleName string(规则名称)
            @return dict
        '''
        rules = self.get_rules()
        for rule in rules:
            if rule['name'] == ruleName:
                return rule
        return {}


    def set_site_rule(self,args):
        '''
            @name 指派专属规则
            @author hwliang<2020-06-02>
            @param siteName string(网站名称/多个请用,号分隔)
            @param ruleName string(规则名称)
            @return dict
        '''
        rule = self.get_rule_find(args.ruleName)
        if not rule: return public.returnMsg(False,'指定专属规则不存在:{}'.format(args.ruleName))
        self.read_config()
        site_names = args.siteName.split(',')
        c_names = self._config['sites'].keys()
        for site_name in site_names:
            if not site_name in c_names:
                return public.returnMsg(False,'指定站点不存在:{}'.format(site_name))
            self._config['sites'][site_name]['rule'] = args.ruleName
            self.write_log('网站：{}，指派专属规则为：{}'.format(site_name,args.ruleName))

        self.save_config()
        return public.returnMsg(True,'指定成功!')

    def add_site(self,siteName,domains):
        '''
            @name 同步网站列表
            @author hwliang<2020-06-02>
            @param siteName string(网站名称)
            @param domains list(域名列表)
            @return void
        '''
        siteInfo = {
    		"open" : False,
    		"expire" : 30,
    		"empty_cookie" : True,
            "rule":"Default",
    		"domains" : domains,
    		"force" : {
    			"uri" : [],
    			"ext" : [],
    			"type" : [],
    			"args" : [],
    			"host" : [],
    			"ip" : []
    		},

    		"white" : {
    		    "not_uri" : [],
    			"uri" : [],
    			"host" : [],
    			"ip" : [],
    			"ext" : [ "css" , "js" ],
    			"type" : [ "video" , "octet-stream" , "image" ],
    			"method" : [ "POST","PUT","DELETE","OPTION" ],
    			"args" : [],
    			"cookie" : []
    		},
            "login_success": {
                "sessionid_key": "",
                "uri": [],
                "method": "POST",
                "success": []
            },
            "login_out": {
                "uri": [],
                "method": 'GET',
                "success": []
            }
        }

        self._config['sites'][siteName] = siteInfo

    def get_domains(self,siteName = None,pid = None):
        '''
            @name 获取域名列表
            @author hwliang<2020-06-01>
            @param siteName string(网站名称)/可选
            @param pid int(网站标识)/可选
            @return list
        '''
        if not pid:
            pid = public.M('sites').where('name=?',(siteName,)).getField('id')
        ds = public.M('domain').where('pid=?',(pid,)).field('name').select()
        domains = []
        for d in ds:
            domains.append(d['name'])
        return domains

    def sync_sites(self):
        '''
            @name 同步网站列表
            @author hwliang<2020-06-01>
            @return void
        '''
        self.read_config()

        #同步新站点
        site_names = self._config['sites'].keys()
        new_site_names = []
        site_list = public.M('sites').field('id,name').select()
        is_save = False
        for site in site_list:
            new_site_names.append(site['name'])
            if site['name'] in site_names: continue
            domains = self.get_domains(pid=site['id'])
            self.add_site(site['name'],domains)
            is_save = True

        #清理多余站点
        site_names = list(self._config['sites'].keys())

        for sname in site_names:
            is_delete = True
            for new_name in new_site_names:
                if sname == new_name:
                    is_delete = False
            if is_delete:
                del(self._config['sites'][sname])
                is_save = True

        if is_save: self.save_config()

    def sync_config(self):
        '''
            @name 同步配置文件到Lua
            @author hwliang<2020-06-01>
            @return void
        '''
        self.read_config()
        skey = public.md5(self.__session_name + '_sp_le')
        to_config = {}
        to_config['settings'] = self._config['settings']
        if not skey in session: session[skey] = 3
        to_config['settings']['level'] = session[skey]
        to_config['sites'] = {}
        for site_name in self._config['sites'].keys():
            if not self._config['sites'][site_name]['open']: continue
            to_config['sites'][site_name] = self.format_rule(self._config['sites'][site_name])
            to_config['sites'][site_name]['domains'] = self.get_domains(siteName=site_name)

        lua_string = LuaMaker.makeLuaTable(to_config)
        lua_string = "return " + lua_string
        public.writeFile(self._init_config_file,lua_string)
        public.serviceReload()
        self.write_log('已将规则同步到加速器')

    def format_rule(self,siteInfo):
        '''
            @name 将专属规则格式化到网站规则中
            @author hwliang<2020-06-01>
            @param siteInfo dict(网站规则信息)
            @return dict
        '''
        rule_name = siteInfo['rule']
        del(siteInfo['rule'])
        rule = self.get_rule_find(rule_name)
        if not rule: return siteInfo
        root_rules = ['force','white']
        for rr in root_rules:
            for i in rule[rr].keys():
                for ru in rule[rr][i]:
                    if ru in siteInfo[rr][i]: continue
                    siteInfo[rr][i].append(ru)
        if 'login_success' in rule:
            siteInfo['login_success'] = rule['login_success']
        if 'login_out' in rule:
            siteInfo['login_out'] = rule['login_out']
        if 'is_no_cache' in rule:
            siteInfo['is_no_cache'] = rule['is_no_cache']
        return siteInfo


    def save_config(self):
        '''
            @name 保存配置文件
            @author hwliang<2020-06-01>
            @return bool
        '''
        public.writeFile(self._config_file,json.dumps(self._config))
        self.sync_config()
        return True

    def read_config(self):
        '''
            @name 读取配置文件
            @author hwliang<2020-06-01>
            @return dict
        '''
        if not os.path.exists(self._config_file):
            return self._config
        tmp = public.readFile(self._config_file)
        if not tmp: return self._config
        try:
            self._config = json.loads(tmp)
            return self._config
        except:
            return self._config

    #获取面板日志列表
    #传统方式访问get_logs方法：/plugin?action=a&name=demo&s=get_logs
    #使用动态路由模板输出： /demo/get_logs.html
    #使用动态路由输出JSON： /demo/get_logs.json
    def get_logs(self,args):
        #处理前端传过来的参数
        if not 'p' in args: args.p = 1
        if not 'rows' in args: args.rows = 15
        if not 'callback' in args: args.callback = ''
        args.p = int(args.p)
        args.rows = int(args.rows)

        #取日志总行数
        count = public.M('logs').where('type=?',(self._log_name,)).count()

        #获取分页数据
        page_data = public.get_page(count,args.p,args.rows,args.callback)

        #获取当前页的数据列表
        log_list = public.M('logs').where('type=?',(self._log_name,)).order('id desc').limit(page_data['shift'] + ',' + page_data['row']).field('id,type,log,addtime').select()

        #返回数据到前端
        return {'data': log_list,'page':page_data['page'] }




class LuaMaker:
    """
    lua 处理器
    """
    @staticmethod
    def makeLuaTable(table):
        """
        table 转换为 lua table 字符串
        """
        _tableMask = {}
        _keyMask = {}
        def analysisTable(_table, _indent, _parent):
            if isinstance(_table, tuple):
                _table = list(_table)
            if isinstance(_table, list):
                _table = dict(zip(range(1, len(_table) + 1), _table))
            if isinstance(_table, dict):
                _tableMask[id(_table)] = _parent
                cell = []
                thisIndent = _indent + "    "
                for k in _table:
                    if sys.version_info[0] == 2:
                        if type(k) not in [int,float,bool,list,dict,tuple]:
                            k = k.encode()

                    if not (isinstance(k, str) or isinstance(k, int) or isinstance(k, float)):
                        return
                    key = isinstance(k, int) and "[" + str(k) + "]" or "[\"" + str(k) + "\"]"
                    if _parent + key in _keyMask.keys():
                        return
                    _keyMask[_parent + key] = True
                    var = None
                    v = _table[k]
                    if sys.version_info[0] == 2:
                        if type(v) not in [int,float,bool,list,dict,tuple]:
                            v = v.encode()
                    if isinstance(v, str):
                        var = "\"" + v + "\""
                    elif isinstance(v, bool):
                        var = v and "true" or "false"
                    elif isinstance(v, int) or isinstance(v, float):
                        var = str(v)
                    else:
                        var = analysisTable(v, thisIndent, _parent + key)
                    cell.append(thisIndent + key + " = " + str(var))
                lineJoin = ",\n"
                return "{\n" + lineJoin.join(cell) + "\n" + _indent +"}"
            else:
                pass
        return analysisTable(table, "", "root")


if __name__ == '__main__':
    p = site_speed_main()
    p.sync_config()
