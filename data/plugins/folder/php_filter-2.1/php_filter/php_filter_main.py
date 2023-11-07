#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   宝塔PHP安全防护模块
#+--------------------------------------------------------------------
import sys,os,json,re,time

#设置运行目录
os.chdir("/www/server/panel")

#添加包引用位置并引用公共包
sys.path.append("class/")
import public

class php_filter_main:
    __plugin_path = "plugin/php_filter/"
    __rule_file = __plugin_path + 'rule.json'
    __php_path = "/www/server/php/"
    __log_path = '/www/wwwlogs/php_filter/'
    __vhost_path = 'vhost/nginx/'
    __install_day = __plugin_path + 'install_date.pl'
    __session_name = 'php_filter_' + time.strftime('%Y-%m-%d')
    __config = []
    __sites = []
    __log_name = 'PHP防护'
    __disable_php = ['52','00',None]
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
        if not os.path.exists(self.__install_day):
            public.writeFile(self.__install_day,str(int(time.time())))

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

    def get_server_names(self):
        '''
            @name 获取$_SERVER条件索引
            @author 黄文良<2020-05-09>
            @ps 可用的$_SRTVER字段列表
            @return list
        '''
        return [
            {"name":"HTTP_HOST","title":"访问域名","id":0},
            {"name":"HTTP_COOKIE","title":"Cookie内容","id":1},
            {"name":"HTTP_USER_AGENT","title":"客户端User-Agent","id":2},
            {"name":"REMOTE_ADDR","title":"客户端IP","id":3},
            {"name":"SERVER_NAME","title":"网站名称","id":4},
            {"name":"SERVER_ADDR","title":"服务器IP","id":5},
            {"name":"SERVER_PORT","title":"服务器端口","id":6},
            {"name":"SERVER_PROTOCOL","title":"协议版本","id":7},
            {"name":"DOCUMENT_ROOT","title":"网站根目录","id":8},
            {"name":"DOCUMENT_URI","title":"文档URI","id":9},
            {"name":"REQUEST_METHOD","title":"请求类型","id":12},
            {"name":"REQUEST_SCHEME","title":"请求协议","id":11},
            {"name":"REQUEST_URI","title":"请求URI地址","id":12},
            {"name":"SCRIPT_FILENAME","title":"文件路径","id":13},
            {"name":"SCRIPT_NAME","title":"文件名称","id":14},
            {"name":"QUERY_STRING","title":"查询参数","id":15},
            {"name":"GATEWAY_INTERFACE","title":"网关接口","id":16},
            {"name":"PATH_INFO","title":"PATH_INFO值","id":17}
        ]

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
        data['server_names'] = self.get_server_names()
        return data

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
                "v": php_version
            }

            #判断是否安装
            if not os.path.exists(filter_so):
                php_info['state'] = -1
                php_info['enable'] = 0
                php_info['cli_enable'] = 0
            else:
                #是否加载
                php_ini_conf = public.readFile(php_ini)
                php_info['state'] = 1
                if php_ini_conf.find('bt_filter.so') == -1:
                    php_info['state'] = 0
                if re.search(r";\s*extension\s*=\s*bt_filter.so",php_ini_conf):
                    php_info['state'] = 0
                if php_info['state'] > 0:
                    #是否启用
                    tmp = re.findall(r"bt_filter.enable\s*=\s*(\d+)",php_ini_conf)
                    if not tmp:
                        tmp[0] = '0'
                    php_info['enable'] = int(tmp[0])
                    tmp = re.findall(r"bt_filter.cli_enable\s*=\s*(\d+)",php_ini_conf)
                    if not tmp:
                        tmp[0] = '0'
                    php_info['cli_enable'] = int(tmp[0])
                else:
                    php_info['enable'] = 0
                    php_info['cli_enable'] = 0
            php_info['site_count'] = 0
            if args:
                for s_info in sites:
                    if s_info['version'] == php_version:
                        php_info['site_count'] += 1
            data.append(php_info)

        return sorted(data,key=lambda x: x['version'],reverse=True)


    def set_php_status(self,args):
        '''
            @name 设置PHP版本状态
            @author 黄文良<2020-04-28>
            @param args {
                php_version: PHP版本,如：53
                cli_enable: CLI模式下的防护状态 0.关闭 1.开启
                enable: 防护状态 0.关闭 1.开启
            }
            @return dict
        '''
        php_v = args.php_version.strip()
        php_ini_file = os.path.join(self.__php_path,php_v,'etc/php.ini')
        if not os.path.exists(php_ini_file):
            return public.returnMsg(False,'指定PHP版本未正确安装')

        php_ext_so = self.get_filter_so(php_v)
        if not os.path.exists(php_ext_so):
            src_ext_so = "{}/modules/bt_filter_{}.so".format(self.__plugin_path,php_v)
            # ext_so_url = public.get_url() + '/install/plugin/php_filter/modules/bt_filter_{}.so'.format(php_v)
            # public.ExecShell("wget -O {} {} -T 5".format(php_ext_so,ext_so_url))
            if not os.path.exists(src_ext_so):
                return public.returnMsg(False,'暂不支持PHP-{}版本'.format(php_v))
            public.ExecShell("\cp -arf {} {}".format(src_ext_so,php_ext_so))
            if os.path.getsize(php_ext_so) < 100000:
                return public.returnMsg(False,'文件下载失败!')


        phpini = public.readFile(php_ini_file)
        if phpini.find('bt_filter.filter_list') == -1:
            phpini = re.sub(r".*bt_filter.+","",phpini)
            phpini += '''

[bt_filter]
extension=bt_filter.so
bt_filter.enable = 1
bt_filter.cli_enable= 0
bt_filter.filter_list = ''

'''
            public.writeFile(php_ini_file,phpini)

        status_msg = {'0':'关闭','1':'开启'}

        if 'cli_enable' in args:
            phpini = re.sub(r"bt_filter.cli_enable\s*=\s*.+","bt_filter.cli_enable = {}".format(args.cli_enable),phpini)
        else:
            tmp = re.findall(r"bt_filter.cli_enable\s*=\s*(\d+)",phpini)
            if not tmp: tmp[0] = '0'
            args.cli_enable = tmp[0]

        if 'enable' in args:
            phpini = re.sub(r"bt_filter.enable\s*=\s*.+","bt_filter.enable = {}".format(args.enable),phpini)
        else:
            tmp = re.findall(r"bt_filter.enable\s*=\s*(\d+)",phpini)
            if not tmp: tmp[0] = '0'
            args.enable = tmp[0]

        rep = r".*;\s*extension\s*=\s*bt_filter.so"
        if re.search(rep,phpini):
            phpini = re.sub(rep,"extension = bt_filter.so",phpini)
        public.writeFile(php_ini_file,phpini.replace("\n"*3,"\n"))
        self.sync_phpini()
        public.ExecShell("/etc/init.d/php-fpm-{} start".format(php_v))
        public.ExecShell("/etc/init.d/php-fpm-{} restart".format(php_v))
        public.WriteLog(self.__log_name,'设置PHP-{}的FastCGI防护状态为：{}，CLI防护状态为：{}'.format(php_v,status_msg[args.enable],status_msg[args.cli_enable]))
        return public.returnMsg(True,'设置成功!')


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
            return vfs[v] + '/bt_filter.so'
        return None

    def get_rule_list(self,args = None):
        '''
            @name 获取专属规则列表
            @author 黄文良<2020-04-30>
            @param args dict_obj or None
            @return list
        '''
        from BTPanel import cache
        data = {}
        rules = cache.get('php_filter_rule')
        if not rules:
            _url = public.get_url() + '/install/plugin/php_filter/rule.json'
            rules = public.httpGet(_url)
            if not rules:
                if os.path.exists(self.__rule_file):
                    rules = public.readFile(self.__rule_file)
                else:
                    rules = '[]'
            else:
                try:
                    json.loads(rules)
                    cache.set('php_filter_rule',rules,3600)
                    public.writeFile(self.__rule_file,rules)
                except:
                    if os.path.exists(self.__rule_file):
                        rules = public.readFile(self.__rule_file)
                    else:
                        rules = '[]'
        try:
            data['rule_list'] = json.loads(rules)
        except:
            data['rule_list'] = []
        data['site_list'] = []
        if args:
            self.__get_config()
            for s in self.__config:
                data['site_list'].append(s['site_name'])

        return data


    def get_rule_find(self,args = None, ruleName = None):
        '''
            @name 获取指定专属规则
            @author 黄文良<2020-04-30>
            @param args dict_obj{
                ruleName: string(rule名称)
            }
            @return list
        '''
        if not ruleName:
            ruleName = args.ruleName.strip()
        rules = self.get_rule_list()['rule_list']
        for rule in rules:
            if rule['name'] == ruleName:
                return rule

        return public.returnMsg(False,'找不到指定规则')

    def set_rule_site(self,args):
        '''
            @name 指派专属规则到指定站点
            @author 黄文良<2020-05-08>
            @param args dict_obj{
                siteName: string(网站名称，多个使用逗号隔开)
                ruleName: string(rule名称)
            }
            @return dict
        '''
        args.siteName = args.siteName.split(',')
        for siteName in args.siteName:
            self.set_site_key(siteName,'rule_name',args.ruleName)
            public.WriteLog(self.__log_name,'为站点：{}，指派专属规则为：{}'.format(siteName,args.ruleName))
        return public.returnMsg(True,'规则指派成功!')



    def get_sites(self,args = None):
        '''
            @name 获取网站列表
            @author 黄文良<2020-04-28>
            @param args dict_obj or None
            @return list [
                {
                    site_name: 网站名称
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
        self.sync_sites()
        sites = self.__get_config(force=True)
        is_state = type(args)
        php_versions = None
        if is_state != bool:
            php_versions = self.get_php_versions()
        if args:
            #处理PHP模块未加载或未开启的情况
            tmp_data = []
            for i in range(len(sites)):
                try:
                    sites[i]['version'] = self.get_site_php_version(sites[i]['site_name'])
                    #放弃指定PHP版本
                    if sites[i]['version'] in self.__disable_php: continue
                    # if sites[i]['rule_name'] != '默认规则':
                    #     rule = self.get_rule_find(ruleName=sites[i]['rule_name'])
                    #     sites[i]['filter_dir'] = sites[i]['filter_dir'] + rule['filter_dir']
                    #     sites[i]['filter_disable_funs'] =  sites[i]['filter_disable_funs'] + rule['filter_disable_funs']
                    #     sites[i]['filter_funs'] = sites[i]['filter_funs'] + rule['filter_funs']
                    #     sites[i]['input'] = {"black": rule['input']['black'] + sites[i]['input']['black'],"white": rule['input']['white'] + sites[i]['input']['white']}
                    #     sites[i]['server'] = {"black": rule['server']['black'] + sites[i]['server']['black'],"white": rule['server']['white'] + sites[i]['server']['white']}

                    sites[i]['total'] = self.get_site_total(sites[i]['site_name'])
                    tmp_data.append(sites[i])
                    if php_versions:
                        try:
                            if not tmp_data[-1]['open']: continue
                        except:
                            return tmp_data
                        for php_v in php_versions:
                            if php_v['v'] != tmp_data[-1]['version']: continue
                            if php_v['state'] != 1 or php_v['enable'] != 1:
                                    tmp_data[-1]['open'] = False

                    if tmp_data[-1]['open']:
                        php_ini = self.get_php_ini_data(tmp_data[-1]['version'])
                        if php_ini.find(tmp_data[-1]['path']) == -1:
                            self.sync_phpini()



                except:continue

            sites = tmp_data


        if is_state == bool:
            return sites

        data = {}
        data['total'] = self.get_all_total()
        data['safe_time'] = int((time.time() - int(public.readFile(self.__install_day))) / 86400)
        data['sites'] = sites
        data['server_names'] = self.get_server_names()
        return data



    def get_all_total(self):
        '''
            @name 获取所有网站的总防护次数
            @author 黄文良<2020-04-29>
            @return int
        '''
        total = 0
        t_path = self.__log_path
        if not os.path.exists(t_path):
            os.makedirs(t_path)
        for d in os.listdir(t_path):
            t_file = os.path.join(t_path,d,'total/total.json')
            if not os.path.exists(t_file): continue
            total += os.path.getsize(t_file)
        return total


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

        if not day:
            day = public.format_date("%Y-%m-%d")

        data = {"total":0,"server_black":0,"input_black":0,"filter_funs":0}

        total_path = self.__log_path + '/' + siteName + '/total/'

        total_file = total_path + 'total.json'
        if os.path.exists(total_file):
            data['total'] = os.path.getsize(total_file)

        server_black_file = total_path + day + '_server_black.json'
        if os.path.exists(server_black_file):
            data['server_black'] = os.path.getsize(server_black_file)

        input_black_file = total_path + day + '_input_black.json'
        if os.path.exists(input_black_file):
            data['input_black'] = os.path.getsize(input_black_file)

        filter_funs_file = total_path + day + '_filter_funs.json'
        if os.path.exists(filter_funs_file):
            data['filter_funs'] = os.path.getsize(filter_funs_file)

        return data


    def get_site_logs(self,args = None,siteName = None,day = None):
        '''
            @name 获取网站防护日志数据
            @author 黄文良<2020-04-28>
            @param args dict_obj{
                siteName: string(网站名称)
                day: string(指定日期)
            }
            @param siteName string(网站名称)
            @param day string(指定日期)
            @return list
        '''

        if args:
            siteName = args.siteName.strip()
            if 'day' in args:
                day = args.day
        if not day:
            day = public.format_date("%Y-%m-%d")
        data = {}
        data['days'] = []
        s_path = self.__log_path + '/' + siteName + '/logs/'
        if os.path.exists(s_path):
            for d in os.listdir(s_path):
                data['days'].insert(0,d[:-4])
        log_list = []
        log_file = s_path + day + '.log'
        if os.path.exists(log_file):
            tmp_logs = public.GetNumLines(log_file,500)
            tmp_list = tmp_logs.split("\n")
            for tmp in tmp_list:
                try:
                    log_list.append(json.loads("{}".format(tmp),strict=False))
                except:
                    continue

        data['logs'] =  sorted(log_list,key= lambda x:x[0],reverse=True)
        data['days'] = sorted(data['days'],reverse=True)
        return data

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

        self.__get_config()
        for site in self.__config:
            if site['site_name'] == siteName:
                return site

        return None

    def set_site_status(self,args):
        '''
            @name 设置指定站点的防御状态
            @author 黄文良<2020-04-28>
            @param siteName string(网站名称)
            @return dict
        '''

        s_find = self.get_site_find(args)
        if not s_find:
            return public.returnMsg(False,'指定站点不存在!')

        #处理PHP模块未开启或未安装的情况
        s_find['version'] = self.get_site_php_version(s_find['site_name'])
        php_versions = self.get_php_versions()
        for php_v in php_versions:
            if php_v['v'] != s_find['version']: continue
            if php_v['state'] != 1 or php_v['enable'] != 1:
                return public.returnMsg(False,'指定站点使用的PHP版本未在【PHP设置】中开启防护模块，无法设置该站点的防护状态!')
        state = False
        if s_find['open'] == False:
            state = True
        status_msg = {False:'关闭',True:'开启'}
        self.set_site_key(args.siteName,'open',state)
        public.WriteLog(self.__log_name,'设置网站：{}的PHP防护状态为：{}'.format(args.siteName,status_msg[state]))
        return public.returnMsg(True,'设置成功!')

    def create_request_filter(self,args):
        '''
            @name 创建请求过滤规则
            @author 黄文良<2020-04-28>
            @param siteName string(网站名称)
            @param filter_name string(过滤名称,server.$_SERVER input.输入过滤)
            @param filter_type string(过滤类型,white.白名单 black.黑名单)
            @param where_index1 int(字段索引,*.匹配所有)
            @param where_type1 int(匹配类型 1.模糊 0.完整))
            @param where_val1 string(匹配内容)
            @param where_index2 int(字段索引)
            @param where_type2 int(匹配类型 1.模糊 0.完整))
            @param where_val2 string(匹配内容)
            @return dict
        '''

        if re.match(r"^\d+$",args.where_index1):
            args.where_index1 = int(args.where_index1)

        if re.match(r"^\d+$",args.where_index2):
            args.where_index2 = int(args.where_index2)

        self.__get_config()
        for i in range(len(self.__config)):
            if self.__config[i]['site_name'] != args.siteName:
                continue
            filter_rule = [
                args.where_index1,
                int(args.where_type1),
                args.where_val1.strip(),
                args.where_index2,
                int(args.where_type2),
                args.where_val2.strip()
                ]
            self.__config[i][args.filter_name][args.filter_type].insert(0,filter_rule)
            self.__set_config()
            public.WriteLog(self.__log_name,'为网站：{}创建请求过滤规则：{}'.format(args.siteName,filter_rule))
            return public.returnMsg(True,'添加成功!')

        return public.returnMsg(False,'添加失败!')

    def modify_request_filter(self,args):
        '''
            @name 编辑请求过滤规则
            @author 黄文良<2020-04-28>
            @param siteName string(网站名称)
            @param filter_name string(过滤名称,server.$_SERVER input.输入过滤)
            @param filter_type string(过滤类型,white.白名单 black.黑名单)
            @param filter_index int(过滤规则索引)
            @param where_index1 int(字段索引,*.匹配所有)
            @param where_type1 int(匹配类型 1.模糊 0.完整))
            @param where_val1 string(匹配内容)
            @param where_index2 int(字段索引)
            @param where_type2 int(匹配类型 1.模糊 0.完整))
            @param where_val2 string(匹配内容)
            @return dict
        '''

        if re.match(r"^\d+$",args.where_index1):
            args.where_index1 = int(args.where_index1)

        if re.match(r"^\d+$",args.where_index2):
            args.where_index2 = int(args.where_index2)
        args.filter_index = int(args.filter_index)

        self.__get_config()
        for i in range(len(self.__config)):
            if self.__config[i]['site_name'] != args.siteName:
                continue
            filter_rule = [
                args.where_index1,
                int(args.where_type1),
                args.where_val1.strip(),
                args.where_index2,
                int(args.where_type2),
                args.where_val2.strip()
                ]
            self.__config[i][args.filter_name][args.filter_type][args.filter_index] = filter_rule
            self.__set_config()
            public.WriteLog(self.__log_name,'修改网站：{}请求过滤规则内容：{}'.format(args.siteName,filter_rule))
            return public.returnMsg(True,'编辑成功!')

        return public.returnMsg(False,'编辑失败!')

    def remove_request_filter(self,args):
        '''
            @name 删除请求过滤规则
            @author 黄文良<2020-04-28>
            @param siteName string(网站名称)
            @param filter_name string(过滤名称,server.$_SERVER input.输入过滤)
            @param filter_type string(过滤类型,white.白名单 black.黑名单)
            @param filter_index int(过滤规则索引)
            @return dict
        '''

        args.filter_index = int(args.filter_index)

        self.__get_config()
        for i in range(len(self.__config)):
            if self.__config[i]['site_name'] != args.siteName:
                continue
            del(self.__config[i][args.filter_name][args.filter_type][args.filter_index])
            self.__set_config()
            public.WriteLog(self.__log_name,'删除网站：{}请求过滤规则内容：{}.{}'.format(args.siteName,args.filter_type,args.filter_name))
            return public.returnMsg(True,'删除成功!')

        return public.returnMsg(False,'删除失败!')


    def create_disable_funs(self,args):
        '''
            @name 创建函数禁用规则
            @author 黄文良<2020-04-28>
            @param siteName string(网站名称)
            @param functionName string(函数名称)
            @return dict
        '''
        args.functionName = args.functionName.strip()
        self.__get_config()
        for i in range(len(self.__config)):
            if self.__config[i]['site_name'] != args.siteName:
                continue

            if args.functionName in self.__config[i]['filter_disable_funs']:
                return public.returnMsg(False,'指定函数已禁用!')

            self.__config[i]['filter_disable_funs'].insert(0,args.functionName)
            self.__set_config()
            public.WriteLog(self.__log_name,'为网站：{}创建函数禁用规则：{}'.format(args.siteName,args.functionName))
            return public.returnMsg(True,'添加成功!')

        return public.returnMsg(False,'添加失败!')


    def remove_disable_funs(self,args):
        '''
            @name 删除函数禁用规则
            @author 黄文良<2020-04-28>
            @param siteName string(网站名称)
            @param functionName string(函数名称)
            @return dict
        '''
        args.functionName = args.functionName.strip()
        self.__get_config()
        for i in range(len(self.__config)):
            if self.__config[i]['site_name'] != args.siteName:
                continue

            if not args.functionName in self.__config[i]['filter_disable_funs']:
                return public.returnMsg(False,'指定函数不在禁用列表中!')

            self.__config[i]['filter_disable_funs'].remove(args.functionName)
            self.__set_config()
            public.WriteLog(self.__log_name,'删除网站：{}函数禁用规则：{}'.format(args.siteName,args.functionName))
            return public.returnMsg(True,'删除成功!')

        return public.returnMsg(False,'删除失败!')


    def create_filter_dir(self,args):
        '''
            @name 创建目录禁用规则
            @author 黄文良<2020-04-28>
            @param siteName string(网站名称)
            @param path string(目录全路径)
            @return dict
        '''
        args.path = args.path.strip()
        #if args.path[-1] == '/':
            #args.path = args.path[:-1]

        self.__get_config()
        for i in range(len(self.__config)):
            if self.__config[i]['site_name'] != args.siteName:
                continue

            if args.path in self.__config[i]['filter_dir']:
                return public.returnMsg(False,'指定目录已在禁用列表中!')

            self.__config[i]['filter_dir'].insert(0,args.path)
            self.__set_config()
            public.WriteLog(self.__log_name,'为网站：{}创建目录禁用规则：{}'.format(args.siteName,args.path))
            return public.returnMsg(True,'添加成功!')

        return public.returnMsg(False,'添加失败!')


    def remove_filter_dir(self,args):
        '''
            @name 删除目录禁用规则
            @author 黄文良<2020-04-28>
            @param siteName string(网站名称)
            @param path string(目录全路径)
            @return dict
        '''
        args.path = args.path.strip()
        #if args.path[-1] == '/':
            #args.path = args.path[:-1]

        self.__get_config()
        for i in range(len(self.__config)):
            if self.__config[i]['site_name'] != args.siteName:
                continue

            if not args.path in self.__config[i]['filter_dir']:
                return public.returnMsg(False,'指定目录不在禁用列表中!')

            self.__config[i]['filter_dir'].remove(args.path)
            self.__set_config()
            public.WriteLog(self.__log_name,'删除网站：{}目录禁用规则：{}'.format(args.siteName,args.path))
            return public.returnMsg(True,'删除成功!')

        return public.returnMsg(False,'删除失败!')


    def create_filter_funs(self,args):
        '''
            @name 创建函数过滤规则
            @author 黄文良<2020-04-28>
            @param siteName string(网站名称)
            @param functionName string(函数名称)
            @param args list(过滤的参数)
            @return dict
        '''

        args.functionName = args.functionName.strip()
        fun_args = json.loads(args.args)
        fun_args.insert(0,args.functionName)

        self.__get_config()
        for i in range(len(self.__config)):
            if self.__config[i]['site_name'] != args.siteName:
                continue

            self.__config[i]['filter_funs'].insert(0,fun_args)
            self.__set_config()
            public.WriteLog(self.__log_name,'为网站：{}创建函数过滤规则：{}:{}'.format(args.siteName,args.functionName,fun_args))
            return public.returnMsg(True,'添加成功!')

        return public.returnMsg(False,'添加失败!')


    def remove_filter_funs(self,args):
        '''
            @name 删除函数过滤规则
            @author 黄文良<2020-04-28>
            @param siteName string(网站名称)
            @param functionIndex int(规则索引)
            @return dict
        '''
        args.functionIndex = int(args.functionIndex)
        self.__get_config()
        for i in range(len(self.__config)):
            if self.__config[i]['site_name'] != args.siteName:
                continue
            rule_info = self.__config[i]['filter_funs'][args.functionIndex]
            del(self.__config[i]['filter_funs'][args.functionIndex])
            self.__set_config()
            public.WriteLog(self.__log_name,'删除网站：{}函数过滤规则：{}'.format(args.siteName,rule_info))
            return public.returnMsg(True,'删除成功!')
        return public.returnMsg(False,'删除失败!')


    def set_site_key(self,siteName,sKey,sValue):
        '''
            @name 设置指定站点的指定值
            @author 黄文良<2020-04-28>
            @param siteName string(网站名称)
            @param sKey string(字段名)
            @param sValue mixed(字段值)
            @return bool
        '''
        self.__get_config()
        for i in range(len(self.__config)):
            if self.__config[i]['site_name'] == siteName:
                self.__config[i][sKey] = sValue

        self.__set_config()
        return True


    def add_site(self,siteInfo):
        '''
            @name 添加网站到配置文件
            @author 黄文良<2020-04-28>
            @param siteInfo{
                name: string(网站名称)
                path: string(根目录)

            }
            @return void
        '''

        self.__get_config()
        siteInfo['open'] = False
        siteInfo['site_name'] = siteInfo['name']
        siteInfo['log_file'] = os.path.join(self.__log_path,siteInfo['site_name'])
        siteInfo['filter_disable_funs'] = []
        siteInfo['filter_dir'] = []
        siteInfo['filter_funs'] = []
        siteInfo['server'] = {"white":[],"black":[]}
        siteInfo['input'] = {"white":[],"black":[]}
        siteInfo['rule_name'] = '默认规则'
        del(siteInfo['name'])
        self.__config.append(siteInfo)
        self.__set_config()
        return True


    def get_php_filter_auth(self):
        import panelAuth
        from BTPanel import session
        if self.__session_name in session:
            if session[self.__session_name] != 0:
                return session[self.__session_name]

        cloudUrl = public.GetConfigValue('home')+'/api/panel/get_soft_list_test'
        pdata = panelAuth.panelAuth().create_serverid(None)
        ret = public.httpPost(cloudUrl, pdata)
        if not ret:
            if not self.__session_name in session:
                session[self.__session_name] = 1
            return 1
        try:
            ret = json.loads(ret)
            for i in ret["list"]:
                if i['name'] == 'php_filter':
                    if i['endtime'] >= 0:
                        session[self.__session_name] = 2
                        return 2
            return 0
        except:
            session[self.__session_name] = 1
            return 1



    def sync_sites(self):
        '''
            @name 同步网站列表
            @author 黄文良<2020-04-28>
            @return void
        '''
        site_list = public.M('sites').field('name,path').select()

        sites = []
        for site in site_list:
            sites.append(site['name'])
            s_find = self.get_site_find(None,site['name'])
            if s_find:
                if s_find['path'] != site['path']:
                    self.set_site_key(site['name'],'path',site['path'])
                continue
            self.add_site(site)

        self.__get_config(force=True)
        site_list = self.__config[:]
        is_write = False
        for site in site_list:
            if not site['site_name'] in sites:
                self.__config.remove(site)
                is_write = True

        if is_write:
            self.__set_config()




    def sync_phpini(self):
        '''
            @name 同步配置到PHP
            @author 黄文良<2020-04-28>
            @return void
        '''
        self.__get_config(force=True)
        php_versions = {
            "52":[],
            "53":[],
            "54":[],
            "55":[],
            "56":[],
            "70":[],
            "71":[],
            "72":[],
            "73":[],
            "74":[],
            "80":[],
            "81":[]
        }



        for siteInfo in self.__config:
            if not siteInfo['open']: continue
            php_v = siteInfo['version']
            if php_v not in php_versions:continue
            php_ini_file = os.path.join(self.__php_path,php_v,'etc/php.ini')
            if not os.path.exists(php_ini_file): continue
            del(siteInfo['version'])
            del(siteInfo['open'])


            #创建日志和统计目录
            p_logs = siteInfo['log_file'] + '/logs'
            p_total = siteInfo['log_file'] + '/total'
            if not os.path.exists(p_logs):
                os.makedirs(p_logs)
                public.ExecShell("chmod -R 755 {}".format(siteInfo['log_file']))
                public.ExecShell("chown -R www:www {}".format(siteInfo['log_file']))
            if not os.path.exists(p_total):
                os.makedirs(p_total)
                public.ExecShell("chmod -R 755 {}".format(siteInfo['log_file']))
                public.ExecShell("chown -R www:www {}".format(siteInfo['log_file']))


            if 'rule_name' in siteInfo:
                if siteInfo['rule_name']:
                    siteInfo = self.sync_rule_site(siteInfo)
                del(siteInfo['rule_name'])

            php_versions[php_v].append(siteInfo)

        self.__config = []

        for v in php_versions.keys():
            if v in self.__disable_php: continue
            php_ini_file = os.path.join(self.__php_path,v,'etc/php.ini')
            if not os.path.exists(php_ini_file): continue
            phpini = public.readFile(php_ini_file)
            if phpini.find('bt_filter.filter_list') == -1:
                continue
            if not php_versions[v]:
                config_json = ''
            else:
                config_json = json.dumps(php_versions[v])
            phpini = re.sub(r"bt_filter.filter_list\s*=\s*.*","bt_filter.filter_list = '{}'".format(config_json),phpini)
            public.writeFile(php_ini_file,phpini)
            public.phpReload(v)


    def sync_rule_site(self,siteInfo):
        '''
            @name 同步专属规则到配置
            @author 黄文良<2020-05-08>
            @param siteInfo dict 网站配置
            @return siteInfo
        '''
        rule = self.get_rule_find(ruleName = siteInfo['rule_name'])
        if 'status' in rule: return siteInfo

        for df in rule['filter_disable_funs']:
            if df in siteInfo['filter_disable_funs']: continue
            siteInfo['filter_disable_funs'].append(df)

        for df in rule['filter_dir']:
            if df in siteInfo['filter_dir']: continue
            siteInfo['filter_dir'].append(df)

        for df in rule['filter_funs']:
            if df in siteInfo['filter_funs']: continue
            siteInfo['filter_funs'].append(df)

        for df in rule['server']['white']:
            if df in siteInfo['server']['white']: continue
            siteInfo['server']['white'].append(df)

        for df in rule['server']['black']:
            if df in siteInfo['server']['black']: continue
            siteInfo['server']['black'].append(df)

        for df in rule['input']['white']:
            if df in siteInfo['input']['white']: continue
            siteInfo['input']['white'].append(df)

        for df in rule['input']['black']:
            if df in siteInfo['input']['black']: continue
            siteInfo['input']['black'].append(df)

        return siteInfo

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
        count = public.M('logs').where('type=?',(self.__log_name,)).count()

        #获取分页数据
        page_data = public.get_page(count,args.p,args.rows,args.callback)

        #获取当前页的数据列表
        log_list = public.M('logs').where('type=?',(self.__log_name,)).order('id desc').limit(page_data['shift'] + ',' + page_data['row']).field('id,type,log,addtime').select()

        #返回数据到前端
        return {'data': log_list,'page':page_data['page'] }

    #读取配置项(插件自身的配置文件)
    #@param key 取指定配置项，若不传则取所有配置[可选]
    #@param force 强制从文件重新读取配置项[可选]
    def __get_config(self,force=False):
        #判断是否从文件读取配置
        if not self.__config or force:
            config_file = self.__plugin_path + 'config.json'
            if not os.path.exists(config_file): return None
            f_body = public.ReadFile(config_file)
            if not f_body: return None
            self.__config = json.loads(f_body)
            if type(self.__config) == dict:
                self.__config = []

        return self.__config

    #设置配置项(插件自身的配置文件)
    #@param key 要被修改或添加的配置项[可选]
    #@param value 配置值[可选]
    def __set_config(self):
        #是否需要初始化配置项
        if not self.__config: self.__config = []

        #写入到配置文件
        config_file = self.__plugin_path + 'config.json'
        public.WriteFile(config_file,json.dumps(self.__config))
        self.sync_phpini()
        return True

