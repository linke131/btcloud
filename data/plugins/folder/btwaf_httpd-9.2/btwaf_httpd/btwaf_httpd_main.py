# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# | Author: <1249648969@qq.com>
# +-------------------------------------------------------------------

# +--------------------------------------------------------------------
# |   宝塔网站防火墙
# +--------------------------------------------------------------------
import sys, os

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
sys.path.append("class/")
import json, os, time, public, string, math, re, hashlib

if __name__ != '__main__':
    from panelAuth import panelAuth
    from BTPanel import session


class btwaf_httpd_main:
    __path = '/www/server/btwaf/'
    __state = {True: '开启', False: '关闭', 0: '停用', 1: '启用'}
    __config = None
    __rule_path = ["args.json", "cookie.json", "post.json", "url_white.json", "url.json", "user_agent.json"]
    setupPath = '/www/server'
    apachedefaultfile = "%s/apache/conf/extra/httpd-default.conf" % (setupPath)
    apachempmfile = "%s/apache/conf/extra/httpd-mpm.conf" % (setupPath)
    __session_name = None
    __isFirewalld = False
    __isUfw = False

    __cms_list = {"EcShop": ["/ecshop/api/cron.php", "/appserver/public/js/main.js",
                             "/ecshop/js/index.js", "/ecshop/data/config.php"],
                  "weiqin": ["/framework/table/users.table.php", "/payment/alipay/return.php",
                             "/web/common/bootstrap.sys.inc.php"],
                  "haiyang": ["/data/admin/ping.php", "/js/history.js", "/templets/default/html/topicindex.html"],
                  "canzhi": ["/system/module/action/js/history.js", "/system/framework/base/control.class.php",
                             "/www/data/css/default_clean_en.css"],
                  "pingguo": ["/static/js/jquery.pngFix.js", "/static/css/admin_style.css",
                              "/template/default_pc/js/jquery-autocomplete.js"],
                  "PHPCMS": ["/phpsso_server/statics/css/system.css", "/phpcms/languages/en/cnzz.lang.php",
                             "/api/reg_send_sms.php"],
                  "wordpress": ["/wp-content/languages/admin-network-zh_CN.mo", "/wp-includes/js/admin-bar.js",
                                "/wp-admin/css/colors/ocean/colors.css"],
                  "zhimeng": ["/include/calendar/calendar-win2k-1.css", "/include/js/jquery/ui.tabs.js",
                              "/inc/inc_stat.php", "/images/js/ui.core.js"],
                  "Discuz": ["/static/js/admincp.js", "/api/javascript/javascript.php", "/api/trade/notify_invite.php"],
                  "metlnfo": ["/admin/content/article/save.php", "/app/system/column", "/config/metinfo.inc.php"]}

    def __init__(self):
        if os.path.exists('/usr/sbin/firewalld'): self.__isFirewalld = True
        if os.path.exists('/usr/sbin/ufw'): self.__isUfw = True
        if not self.__session_name:
            self.__session_name = self.__get_md5('__session_name_httpd_btwaf' + time.strftime('%Y-%m-%d'))


    def is_ip_zhuanhuang(self,ip,ip2=False,ip_duan=False):
        try:
            ret = []
            if ip_duan:
                ip_ddd=int(ip.split('/')[1])
                ip = ip.split('/')[0].split('.')
                if ip_ddd>=32:return False
                if ip_ddd>=24:ip[-1]="0"
                if ip_ddd>=16 and ip_ddd<24:
                    ip[-1]="0"
                    ip[-2]="0"
                if ip_ddd>=8 and ip_ddd<16:
                    ip[-1]="0"
                    ip[-2]="0"
                    ip[-3]="0"
                from IPy import IP
                ip2 = IP("{}/{}".format('.'.join(ip),ip_ddd))
                return self.is_ip_zhuanhuang(str(ip2[0]),str(ip2[-1]))
            else:
                if not ip2:
                    ip=ip.split('.')
                    ret2=[]
                    for i in ip:
                        ret2.append(int(i))
                    ret.append(ret2)
                    ret.append(ret2)
                    return ret
                if ip2:
                    ip = ip.split('.')
                    ret2 = []
                    for i in ip:
                        ret2.append(int(i))
                    ret.append(ret2)
                    ip2 = ip2.split('.')
                    ret2 = []
                    for i in ip2:
                        ret2.append(int(i))
                    ret.append(ret2)
                    return ret
        except:return False



    def import_data(self, get):
        name = get.s_Name
        if name=='ip_white' or name=='ip_black':
            padata =get.pdata.strip().split()
            if not padata:return public.returnMsg(False, '数据格式不正确')
            iplist = self.__get_rule(name)
            for i in padata:
                if re.search("\d+.\d+.\d+.\d+-\d+.\d+.\d+.\d+$",i):
                    ip=i.split('-')
                    ips = self.is_ip_zhuanhuang(ip[0],ip[1])
                    if not ips: continue
                    if ips in iplist: continue
                    iplist.insert(0, ips)
                if re.search("\d+.\d+.\d+.\d+/\d+$",i):
                    ips = self.is_ip_zhuanhuang(i,ip_duan=True)
                    if not ips: continue
                    if ips in iplist: continue
                    iplist.insert(0, ips)
                if re.search("\d+.\d+.\d+.\d+$",i):
                    ips=self.is_ip_zhuanhuang(i)
                    if not ips:continue
                    if ips in iplist: continue
                    iplist.insert(0, ips)
            self.__write_rule(name, iplist)
            return public.returnMsg(True, '导入成功!')
        else:
            try:
                pdata = json.loads(get.pdata)
            except:
                return public.returnMsg(False, '数据格式不正确')

            if not pdata: return public.returnMsg(False, '数据格式不正确');
            iplist = self.__get_rule(name)
            for ips in pdata:
                if ips in iplist: continue
                iplist.insert(0, ips)
            self.__write_rule(name, iplist)
            return public.returnMsg(True, '导入成功!')

    def __get_md5(self, s):
        m = hashlib.md5()
        m.update(s.encode('utf-8'))
        return m.hexdigest()
        # 查看UA白名单 ua_white

    def get_ua_white(self, get):
        config = self.get_config(None)
        url_find_list = config['ua_white']
        return public.returnMsg(True, url_find_list)

        # 添加UA 白名单 ua_white

    def add_ua_white(self, get):
        if not get.ua_white:return public.returnMsg(False, '不能为空')
        url_find = get.ua_white
        config = self.get_config(None)
        url_find_list = config['ua_white']
        if url_find in url_find_list:
            return public.returnMsg(False, '已经存在')
        else:
            url_find_list.append(url_find)
            self.__write_config(config)
            return public.returnMsg(True, '添加成功')
        # 删除UA 白名单 ua_white

    def del_ua_white(self, get):
        url_find = get.ua_white
        config = self.get_config(None)
        url_find_list = config['ua_white']
        if url_find in url_find_list:
            url_find_list.remove(url_find)
            self.__write_config(config)
            return public.returnMsg(True, '删除成功')
        else:
            return public.returnMsg(False, '不存在')

        # 查看ua 黑名单ua_black

    def get_ua_black(self, get):
        config = self.get_config(None)
        url_find_list = config['ua_black']
        return public.returnMsg(True, url_find_list)

        # 添加UA 黑名单ua_black

    def add_ua_black(self, get):
        if not get.ua_black:return public.returnMsg(False, '不能为空')
        url_find = get.ua_black
        config = self.get_config(None)
        url_find_list = config['ua_black']
        if url_find in url_find_list:
            return public.returnMsg(False, '已经存在')
        else:
            url_find_list.append(url_find)
            self.__write_config(config)
            return public.returnMsg(True, '添加成功')

        # 删除UA 黑名单 ua_black

    def del_ua_black(self, get):
        url_find = get.ua_black
        config = self.get_config(None)
        url_find_list = config['ua_black']
        if url_find in url_find_list:
            url_find_list.remove(url_find)
            self.__write_config(config)
            return public.returnMsg(True, '删除成功')
        else:
            return public.returnMsg(False, '不存在')

        # 查看URL_FIND

    def get_url_find(self, get):
        config = self.get_config(None)
        url_find_list = config['uri_find']
        return public.returnMsg(True, url_find_list)

        # 添加URL FIND

    def add_url_find(self, get):
        url_find = get.url_find
        config = self.get_config(None)
        url_find_list = config['uri_find']
        if url_find in url_find_list:
            return public.returnMsg(False, '已经存在')
        else:
            url_find_list.append(url_find)
            self.__write_config(config)
            return public.returnMsg(True, '添加成功')

        # 添加URL FIND

    def del_url_find(self, get):
        url_find = get.url_find
        config = self.get_config(None)
        url_find_list = config['uri_find']
        if url_find in url_find_list:
            url_find_list.remove(url_find)
            self.__write_config(config)
            return public.returnMsg(True, '删除成功')
        else:
            return public.returnMsg(False, '不存在')

    # 设置全局uri 增强白名单
    def golbls_cc_zeng(self, get):
        if os.path.exists(self.__path + 'rule/cc_uri_white.json'):
            data = public.ReadFile(self.__path + 'rule/cc_uri_white.json')
            text = self.xssencode((get.text.strip()))
            # return text
            try:
                data = json.loads(data)
                if text in data:
                    return public.returnMsg(False, '已经存在!')
                else:
                    data.append(text)
                    public.WriteFile(self.__path + 'rule/cc_uri_white.json', json.dumps(data))
                    return public.returnMsg(True, '设置成功!')
            except:
                ret = []
                ret.append(self.xssencode((get.text.strip())))
                public.WriteFile(self.__path + 'rule/cc_uri_white.json', json.dumps(ret))
                return public.returnMsg(True, '设置成功!')
        else:
            ret = []
            ret.append(self.xssencode((get.text.strip())))
            public.WriteFile(self.__path + 'rule/cc_uri_white.json', json.dumps(ret))
            return public.returnMsg(True, '设置成功!')

    # 查看
    def get_golbls_cc(self, get):
        if os.path.exists(self.__path + 'rule/cc_uri_white.json'):
            data2 = public.ReadFile(self.__path + 'rule/cc_uri_white.json')
            try:
                data = json.loads(data2)
                return public.returnMsg(True, data)
            except:
                ret = []
                public.WriteFile(self.__path + 'rule/cc_uri_white.json', json.dumps(ret))
                return public.returnMsg(True, '设置成功!')
        else:
            ret = []
            public.WriteFile(self.__path + 'rule/cc_uri_white.json', json.dumps(ret))
            return public.returnMsg(True, ret)

    def del_golbls_cc(self, get):
        if os.path.exists(self.__path + 'rule/cc_uri_white.json'):
            data = public.ReadFile(self.__path + 'rule/cc_uri_white.json')
            text = self.xssencode((get.text.strip()))
            try:
                data = json.loads(data)
                if text in data:
                    data.remove(text)
                    public.WriteFile(self.__path + 'rule/cc_uri_white.json', json.dumps(data))
                    return public.returnMsg(True, '删除成功!')
                else:
                    return public.returnMsg(False, '不存在!')
            except:
                ret = []
                public.WriteFile(self.__path + 'rule/cc_uri_white.json', json.dumps(ret))
                return public.returnMsg(True, '文件解析错误恢复出厂设置!')
        else:
            ret = []
            public.WriteFile(self.__path + 'rule/cc_uri_white.json', json.dumps(ret))
            return public.returnMsg(True, '文件不存在恢复出厂设置!')

    # 设置CC全局生效
    def set_cc_golbls(self, get):
        data = self.get_site_config(get)
        ret = []
        for i in data:
            ret.append(i['siteName'])
        if not ret: return False
        for i in ret:
            get.siteName = i
            self.set_site_cc_conf(get)
        return True

    # 设置CC 增强全局生效
    def set_cc_retry_golbls(self, get):
        data = self.get_site_config(get)
        ret = []
        for i in data:
            ret.append(i['siteName'])
        if not ret: return False
        for i in ret:
            get.siteName = i
            self.set_site_retry(get)
        return True

        # 四层计划任务

    def site_time_uptate(self):
        id = public.M('crontab').where('name=?', (u'Apache防火墙四层拦截IP',)).getField('id')
        import crontab
        if id: crontab.crontab().DelCrontab({'id': id})
        data = {}
        data['name'] = 'Apache防火墙四层拦截IP'
        data['type'] = 'hour-n'
        data['where1'] = '1'
        data['sBody'] = 'python /www/server/panel/plugin/btwaf_httpd/firewalls_list.py start'
        data['backupTo'] = 'localhost'
        data['sType'] = 'toShell'
        data['hour'] = ''
        data['minute'] = '0'
        data['week'] = ''
        data['sName'] = ''
        data['urladdress'] = ''
        data['save'] = ''
        crontab.crontab().AddCrontab(data)
        return True

    # 设置四层屏蔽模式
    def set_stop_ip(self, get):
        self.site_time_uptate()
        return public.returnMsg(True, '设置成功!')

    # 关闭
    def set_stop_ip_stop(self, get):
        id = public.M('crontab').where('name=?', (u'Apache防火墙四层拦截IP',)).getField('id')
        import crontab
        if id: crontab.crontab().DelCrontab({'id': id})
        return public.returnMsg(True, '关闭成功!')

    def get_stop_ip(self, get):
        id = public.M('crontab').where('name=?', (u'Apache防火墙四层拦截IP',)).getField('id')
        if id:
            return public.returnMsg(True, '11')
        else:
            return public.returnMsg(False, '111')

    #  xss 防御
    def xssencode(self, text):
        import cgi
        list = ['`', '~', '&', '#', '*', '$', '@', '<', '>', '\"', '\'', ';', '%', ',', '\\u']
        ret = []
        for i in text:
            if i in list:
                i = ''
            ret.append(i)
        str_convert = ''.join(ret)
        text2 = cgi.escape(str_convert, quote=True)
        return text2

    #  xss 防御
    def xxx2(self, text):
        text = str(text).replace('\'', '’').replace('"', "”")
        return text

    def ipv6_check(self, addr):
        ip6_regex = (
            r'(^(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}$)|'
            r'(\A([0-9a-f]{1,4}:){1,1}(:[0-9a-f]{1,4}){1,6}\Z)|'
            r'(\A([0-9a-f]{1,4}:){1,2}(:[0-9a-f]{1,4}){1,5}\Z)|'
            r'(\A([0-9a-f]{1,4}:){1,3}(:[0-9a-f]{1,4}){1,4}\Z)|'
            r'(\A([0-9a-f]{1,4}:){1,4}(:[0-9a-f]{1,4}){1,3}\Z)|'
            r'(\A([0-9a-f]{1,4}:){1,5}(:[0-9a-f]{1,4}){1,2}\Z)|'
            r'(\A([0-9a-f]{1,4}:){1,6}(:[0-9a-f]{1,4}){1,1}\Z)|'
            r'(\A(([0-9a-f]{1,4}:){1,7}|:):\Z)|(\A:(:[0-9a-f]{1,4}){1,7}\Z)|'
            r'(\A((([0-9a-f]{1,4}:){6})(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3})\Z)|'
            r'(\A(([0-9a-f]{1,4}:){5}[0-9a-f]{1,4}:(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3})\Z)|'
            r'(\A([0-9a-f]{1,4}:){5}:[0-9a-f]{1,4}:(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\Z)|'
            r'(\A([0-9a-f]{1,4}:){1,1}(:[0-9a-f]{1,4}){1,4}:(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\Z)|'
            r'(\A([0-9a-f]{1,4}:){1,2}(:[0-9a-f]{1,4}){1,3}:(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\Z)|'
            r'(\A([0-9a-f]{1,4}:){1,3}(:[0-9a-f]{1,4}){1,2}:(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\Z)|'
            r'(\A([0-9a-f]{1,4}:){1,4}(:[0-9a-f]{1,4}){1,1}:(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\Z)|'
            r'(\A(([0-9a-f]{1,4}:){1,5}|:):(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\Z)|'
            r'(\A:(:[0-9a-f]{1,4}){1,5}:(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\Z)')
        return bool(re.match(ip6_regex, addr, flags=re.IGNORECASE))

    # IPV6 黑名单
    def set_ipv6_back(self, get):
        addr = str(get.addr).split()
        addr = addr[0]
        ret = self.get_ipv6(get)
        if ret['status']:
            return public.returnMsg(False, '请开启IPV6访问!')
        else:
            if self.ipv6_check(addr):
                if not os.path.exists(self.__path + 'ipv6_back.json'):
                    list = []
                    list.append(addr)
                    public.WriteFile(self.__path + 'ipv6_back.json', json.dumps(list))
                    self.add_ipv6(addr)
                    return public.returnMsg(True, '添加成功!')
                else:
                    list_addr = public.ReadFile(self.__path + 'ipv6_back.json')
                    if list_addr:
                        list_addr = json.loads(list_addr)
                        if str(addr) in list_addr:
                            return public.returnMsg(False, '已经存在!')
                        else:
                            list_addr.append(addr)
                            self.add_ipv6(addr)
                            public.WriteFile(self.__path + 'ipv6_back.json', json.dumps(list_addr))
                            return public.returnMsg(True, '添加成功!')
                    else:
                        list = []
                        list.append(addr)
                        public.WriteFile(self.__path + 'ipv6_back.json', json.dumps(list))
                        self.add_ipv6(addr)
                        return public.returnMsg(True, '添加成功!')
            else:
                return public.returnMsg(False, '请输入正确的IPV6地址')

    def del_ipv6_back(self, get):
        addr = str(get.addr).split()
        addr = addr[0]
        list_addr = public.ReadFile(self.__path + 'ipv6_back.json')
        if list_addr:
            list_addr = json.loads(list_addr)
            if addr in list_addr:
                self.del_ipv6(addr)
                list_addr.remove(addr)
                public.WriteFile(self.__path + 'ipv6_back.json', json.dumps(list_addr))
                return public.returnMsg(True, '删除成功!')
            else:
                return public.returnMsg(False, '地址不存在!')
        else:
            list = []
            public.WriteFile(self.__path + 'ipv6_back.json', json.dumps(list))
            return public.returnMsg(True, '列表为空!')

    def add_ipv6(self, addr):
        if self.__isFirewalld:
            public.ExecShell(
                '''firewall-cmd --permanent --add-rich-rule="rule family="ipv6" source address="%s"  port protocol="tcp" port="80"  reject" ''' % addr)
            self.FirewallReload()
        if self.__isUfw:
            return public.returnMsg(False, '不支持乌班图哦!')
        else:
            return public.returnMsg(False, '暂时只支持Centos7')

    def del_ipv6(self, addr):
        if self.__isFirewalld:
            public.ExecShell(
                '''firewall-cmd --permanent --remove-rich-rule="rule family="ipv6" source address="%s"  port protocol="tcp" port="80"  reject" ''' % addr)
            self.FirewallReload()
        if self.__isUfw:
            return public.returnMsg(False, '不支持乌班图哦!')
        else:
            return public.returnMsg(False, '暂时只支持Centos7')

    def get_ipv6_address(self, get):
        if os.path.exists(self.__path + 'ipv6_back.json'):
            list_addr = public.ReadFile(self.__path + 'ipv6_back.json')
            list_addr = json.loads(list_addr)
            return public.returnMsg(True, list_addr)
        else:
            return public.returnMsg(False, [])

    # 重载防火墙配置
    def FirewallReload(self):
        if self.__isUfw:
            public.ExecShell('/usr/sbin/ufw reload')
            return;
        if self.__isFirewalld:
            public.ExecShell('firewall-cmd --reload')
        else:
            public.ExecShell('/etc/init.d/ip6tables save')
            public.ExecShell('service ip6tables restart')

    # 关闭IPV6地址访问
    def stop_ipv6(self, get):
        if self.__isFirewalld:
            public.ExecShell(
                '''firewall-cmd --permanent --add-rich-rule="rule family="ipv6"  port protocol="tcp" port="443" reject"''')
            public.ExecShell(
                '''firewall-cmd --permanent --add-rich-rule="rule family="ipv6"  port protocol="tcp" port="80" reject" ''')
            self.FirewallReload()
            return public.returnMsg(True, '设置成功!')
        if self.__isUfw:
            return public.returnMsg(False, '不支持乌班图开启和关闭!')
        else:
            public.ExecShell('ip6tables -F && ip6tables -X && ip6tables -Z')
            public.ExecShell('''ip6tables -I INPUT -m state --state NEW -m tcp -p tcp --dport 80 -j DROP''')
            public.ExecShell('''ip6tables -I INPUT -m state --state NEW -m tcp -p tcp --dport 443 -j DROP''')
            return public.returnMsg(True, '设置成功!')

    def start_ipv6(self, get):
        if self.__isFirewalld:
            public.ExecShell(
                '''firewall-cmd --permanent --remove-rich-rule="rule family="ipv6"  port protocol="tcp" port="443" reject"''')
            public.ExecShell(
                '''firewall-cmd --permanent --remove-rich-rule="rule family="ipv6"  port protocol="tcp" port="80" reject" ''')
            self.FirewallReload()
            return public.returnMsg(True, '设置成功!')
        if self.__isUfw:
            return public.returnMsg(False, '不支持乌班图开启和关闭!')
        else:
            public.ExecShell(''' ip6tables -D INPUT -m state --state NEW -m tcp -p tcp --dport 80 -j DROP ''')
            public.ExecShell(''' ip6tables -D INPUT -m state --state NEW -m tcp -p tcp --dport 443 -j DROP''')
            return public.returnMsg(True, '设置成功!')

    def get_ipv6(self, get):
        if self.__isFirewalld:
            import re
            ret = '''family="ipv6" port port="443" protocol="tcp" reject'''
            ret2 = '''family="ipv6" port port="80" protocol="tcp" reject'''
            lit = public.ExecShell('firewall-cmd --list-all')
            if re.search(ret, lit[0]) and re.search(ret2, lit[0]):
                return public.returnMsg(True, '')
            else:
                return public.returnMsg(False, '!')
        if self.__isUfw:
            return public.returnMsg(False, '')
        else:
            import re
            if os.path.exists('/etc/sysconfig/ip6tables'):
                list = public.ReadFile('/etc/sysconfig/ip6tables')
                ret = 'INPUT -p tcp -m state --state NEW -m tcp --dport 80 -j DROP'
                ret2 = 'INPUT -p tcp -m state --state NEW -m tcp --dport 443 -j DROP'
                if re.search(ret, list) and re.search(ret2, list):
                    return public.returnMsg(True, '')
            else:
                return public.returnMsg(False, '')

    # 获取蜘蛛池类型
    def get_zhizu_list(self):
        if os.path.exists(self.__path + 'zhi.json'):
            try:
                ret = json.loads(public.ReadFile(self.__path + 'zhi.json'))
                return ret
            except:
                os.remove(self.__path + 'zhi.json')
                return False
        else:
            rcnlist = public.httpGet('http://www.bt.cn/api/panel/get_spider_type')
            if not rcnlist: return False
            public.WriteFile(self.__path + 'zhi.json', rcnlist)
            try:
                rcnlist = json.loads(rcnlist)
                return rcnlist
            except:
                os.remove(self.__path + 'zhi.json')
                return False

    # 获取蜘蛛池地址
    def get_zhizu_ip_list(self):
        from BTPanel import session
        type = self.get_zhizu_list()
        if not type: return False
        if 'types' in type:
            if len(type['types']) >= 1:
                for i in type['types']:
                    ret = public.httpGet('http://www.bt.cn/api/panel/get_spider?spider=%s' % str(i['id']))
                    if not ret:
                        if not os.path.exists(self.__path + str(i['id']) + '.json'):
                            ret = []
                            public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(ret))
                        continue
                    if os.path.exists(self.__path + str(i['id']) + '.json'):
                        local = public.ReadFile(self.__path + str(i['id']) + '.json')
                        if local:
                            try:
                                ret = json.loads(ret)
                                local = json.loads(local)
                                localhost_json = list(set(json.loads(local)).union(ret))
                                public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(localhost_json))
                                yum_list_json = list(set(local).difference(set(ret)))
                                public.httpGet(
                                    'https://www.bt.cn/api/panel/add_spiders?address=%s' % json.dumps(yum_list_json))
                            except:
                                pass
                        else:
                            try:
                                ret = json.loads(ret)
                                public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(ret))
                            except:
                                ret = []
                                public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(ret))
                    else:
                        try:
                            ret = json.loads(ret)
                            public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(ret))
                        except:
                            ret = []
                            public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(ret))
        public.ExecShell('chown www:www /www/server/btwaf/*.json')
        if not 'zhizu' in session: session['zhizu'] = 1
        return True

    # 获取蜘蛛池地址
    def get_zhizu_list22(self, get):
        # from BTPanel import session
        type = self.get_zhizu_list()
        if not type: return public.returnMsg(False, '连接云端失败!')
        if 'types' in type:
            if len(type['types']) >= 1:
                for i in type['types']:
                    ret = public.httpGet('http://www.bt.cn/api/panel/get_spider?spider=%s' % str(i['id']))
                    if not ret: continue
                    try:
                        ret2 = json.dumps(ret)
                    except:
                        if not os.path.exists(self.__path + str(i['id']) + '.json'):
                            rec = []
                            public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(rec))
                        continue
                    if os.path.exists(self.__path + str(i['id']) + '.json'):
                        local = public.ReadFile(self.__path + str(i['id']) + '.json')
                        if local:
                            localhost_json = list(set(json.loads(local)).union(json.loads(ret)))
                            public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(localhost_json))
                            #
                            yum_list_json = list(set(json.loads(local)).difference(set(json.loads(ret))))
                            if len(yum_list_json) == 0:
                                continue
                            public.httpGet(
                                'https://www.bt.cn/api/panel/add_spiders?address=%s' % json.dumps(yum_list_json))
                        else:
                            public.WriteFile(self.__path + str(i['id']) + '.json', ret)
                    else:
                        public.WriteFile(self.__path + str(i['id']) + '.json', ret)
        # if not 'zhizu' in session: session['zhizu'] = 1
        # public.ExecShell('chown www:www /www/server/btwaf/*.json')
        return public.returnMsg(True, '更新蜘蛛成功!')

    # 获取蜘蛛池地址
    def start_zhuzu(self):
        # from BTPanel import session
        type = self.get_zhizu_list()
        if not type: return public.returnMsg(False, '连接云端失败!')
        if 'types' in type:
            if len(type['types']) >= 1:
                for i in type['types']:
                    ret = public.httpGet('http://www.bt.cn/api/panel/get_spider?spider=%s' % str(i['id']))
                    if not ret: continue
                    try:
                        ret2 = json.dumps(ret)
                    except:
                        if not os.path.exists(self.__path + str(i['id']) + '.json'):
                            rec = []
                            public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(rec))
                        continue
                    if os.path.exists(self.__path + str(i['id']) + '.json'):
                        local = public.ReadFile(self.__path + str(i['id']) + '.json')
                        if local:
                            localhost_json = list(set(json.loads(local)).union(json.loads(ret)))
                            public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(localhost_json))
                            #
                            yum_list_json = list(set(json.loads(local)).difference(set(json.loads(ret))))
                            if len(yum_list_json) == 0:
                                continue
                            public.httpGet(
                                'https://www.bt.cn/api/panel/add_spiders?address=%s' % json.dumps(yum_list_json))
                        else:
                            public.WriteFile(self.__path + str(i['id']) + '.json', ret)
                    else:
                        public.WriteFile(self.__path + str(i['id']) + '.json', ret)
        # if not 'zhizu' in session: session['zhizu'] = 1
        # public.ExecShell('chown www:www /www/server/btwaf/*.json')
        return public.returnMsg(True, '更新蜘蛛成功!')

    # 外部蜘蛛池更新
    def get_zhizu_ip(self, get):
        # from BTPanel import session
        type = self.get_zhizu_list()
        if not type: return public.returnMsg(False, '连接云端失败!')
        if 'types' in type:
            if len(type['types']) >= 1:
                for i in type['types']:
                    ret = public.httpGet('http://www.bt.cn/api/panel/get_spider?spider=%s' % str(i['id']))
                    if not ret: continue
                    try:
                        ret2 = json.dumps(ret)
                    except:
                        if not os.path.exists(self.__path + str(i['id']) + '.json'):
                            rec = []
                            public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(rec))
                        continue
                    if os.path.exists(self.__path + str(i['id']) + '.json'):
                        local = public.ReadFile(self.__path + str(i['id']) + '.json')
                        if local:
                            localhost_json = list(set(json.loads(local)).union(json.loads(ret)))
                            public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(localhost_json))
                            #
                            yum_list_json = list(set(json.loads(local)).difference(set(json.loads(ret))))
                            if len(yum_list_json) == 0:
                                continue
                            public.httpGet(
                                'https://www.bt.cn/api/panel/add_spiders?address=%s' % json.dumps(yum_list_json))
                        else:
                            public.WriteFile(self.__path + str(i['id']) + '.json', ret)
                    else:
                        public.WriteFile(self.__path + str(i['id']) + '.json', ret)
        # if not 'zhizu' in session: session['zhizu'] = 1
        # public.ExecShell('chown www:www /www/server/btwaf/*.json')
        return public.returnMsg(True, '更新蜘蛛成功!')

    # 开启智能防御CC
    def Start_apache_cc(self, get):
        ret = self.auto_sync_apache()
        return ret

    # 查看状态
    def Get_apap_cc(self, get):
        id = public.M('crontab').where('name=?', (u'Apache防火墙智能防御CC',)).getField('id');
        if id:
            return public.returnMsg(True, '开启!');
        else:
            return public.returnMsg(False, '关闭!');

    # 关闭智能防御CC
    def Stop_apache_cc(self, get):
        if os.path.exists('/dev/shm/apache.txt'):
            os.remove('/dev/shm/apache.txt')
        id = public.M('crontab').where('name=?', (u'Apache防火墙智能防御CC',)).getField('id');
        import crontab
        if id: crontab.crontab().DelCrontab({'id': id})
        return public.returnMsg(True, '设置成功!');

    # 设置自动同步
    def auto_sync_apache(self):
        id = public.M('crontab').where('name=?', (u'Apache防火墙智能防御CC',)).getField('id');
        import crontab
        if id: crontab.crontab().DelCrontab({'id': id})
        data = {}
        data['name'] = u'Apache防火墙智能防御CC'
        data['type'] = 'minute-n'
        data['where1'] = '1'
        data['sBody'] = 'python /www/server/panel/plugin/btwaf_httpd/btwaf_httpd_main.py start'
        data['backupTo'] = 'localhost'
        data['sType'] = 'toShell'
        data['hour'] = ''
        data['minute'] = ''
        data['week'] = ''
        data['sName'] = ''
        data['urladdress'] = ''
        data['save'] = ''
        crontab.crontab().AddCrontab(data)
        return public.returnMsg(True, '设置成功!');

    # 查看apache 使用CPU的情况
    def retuen_apache(self):
        import re
        cpunum = int(public.ExecShell('cat /proc/cpuinfo |grep "processor"|wc -l')[0])
        workercpu = round(float(
            public.ExecShell("ps aux|grep httpd|grep 'start'|awk '{cpusum += $3};END {print cpusum}'")[0]) / cpunum,
                          2)
        public.ExecShell("echo '%s'>/dev/shm/apache.txt" % int(workercpu))
        return 'ok'

    def get_config(self, get):
        if __name__ == "__main__":
            if not 'btwaf_httpd' in session: return [];
        config = json.loads(public.readFile(self.__path + 'config.json'));

        if not 'uri_find' in config:
            config['uri_find'] = []

        if not 'ua_white' in config:
            config['ua_white'] = []

        if not 'ua_black' in config:
            config['ua_black'] = []

        if not 'retry_cycle' in config:
            config['retry_cycle'] = 60;
            self.__write_config(config);
        if config['start_time'] == 0:
            config['start_time'] = time.time();
            self.__write_config(config);
        return config

    def get_site_config(self, get):
        if __name__ == "__main__":
            if not 'btwaf_httpd' in session: return [];
        site_config = public.readFile(self.__path + 'site.json');
        data = self.__check_site(json.loads(site_config))
        if get:
            total_all = self.get_total(None)['sites']
            site_list = []
            for k in data.keys():
                if not k in total_all: total_all[k] = {}
                data[k]['total'] = self.__format_total(total_all[k])
                siteInfo = data[k];
                siteInfo['siteName'] = k;
                site_list.append(siteInfo);
            data = sorted(site_list, key=lambda x: x['log_size'], reverse=True)
        return data

    def get_site_config_byname(self, get):
        if not 'siteName' in get:return []
        site_config = self.get_site_config(None);
        config = site_config[get.siteName]
        config['top'] = self.get_config(None)
        return config

    def set_open(self, get):
        config = self.get_config(None)
        if config['open']:
            config['open'] = False
            config['start_time'] = 0
        else:
            config['open'] = True
            config['start_time'] = int(time.time())
        self.__write_log(self.__state[config['open']] + '网站防火墙(WAF)');
        self.__write_config(config)
        return public.returnMsg(True, '设置成功!');

    def set_obj_open(self, get):
        config = self.get_config(None)
        if type(config[get.obj]) != bool:
            if config[get.obj]['open']:
                config[get.obj]['open'] = False
            else:
                config[get.obj]['open'] = True
            self.__write_log(self.__state[config[get.obj]['open']] + '【' + get.obj + '】功能');
        else:
            if config[get.obj]:
                config[get.obj] = False
            else:
                config[get.obj] = True
            self.__write_log(self.__state[config[get.obj]] + '【' + get.obj + '】功能');

        self.__write_config(config)
        return public.returnMsg(True, '设置成功!');

    def set_site_obj_open(self, get):
        site_config = self.get_site_config(None)
        if type(site_config[get.siteName][get.obj]) != bool:
            if site_config[get.siteName][get.obj]['open']:
                site_config[get.siteName][get.obj]['open'] = False
            else:
                site_config[get.siteName][get.obj]['open'] = True
            self.__write_log(self.__state[site_config[get.siteName][get.obj][
                'open']] + '网站【' + get.siteName + '】【' + get.obj + '】功能');
        else:
            if site_config[get.siteName][get.obj]:
                site_config[get.siteName][get.obj] = False
            else:
                site_config[get.siteName][get.obj] = True
            self.__write_log(
                self.__state[site_config[get.siteName][get.obj]] + '网站【' + get.siteName + '】【' + get.obj + '】功能');

        if get.obj == 'drop_abroad': self.__auto_sync_cnlist();
        self.__write_site_config(site_config)
        return public.returnMsg(True, '设置成功!');

    def set_obj_status(self, get):
        config = self.get_config(None)
        config[get.obj]['status'] = int(get.statusCode)
        self.__write_config(config)
        return public.returnMsg(True, '设置成功!');

    def set_cc_conf(self, get):
        config = self.get_config(None)
        config['cc']['cycle'] = int(get.cycle)
        config['cc']['limit'] = int(get.limit)
        config['cc']['endtime'] = int(get.endtime)
        config['cc']['increase'] = (get.increase == '1') | False
        self.__write_config(config)
        if get.is_open_global:
            self.set_cc_golbls(get)
        self.__write_log(
            '设置全局CC配置为：' + get.cycle + ' 秒内累计请求超过 ' + get.limit + ' 次后,封锁 ' + get.endtime + ' 秒' + ',增强:' + get.increase);
        return public.returnMsg(True, '设置成功!');

    def set_site_cc_conf(self, get):
        site_config = self.get_site_config(None)
        site_config[get.siteName]['cc']['cycle'] = int(get.cycle)
        site_config[get.siteName]['cc']['limit'] = int(get.limit)
        site_config[get.siteName]['cc']['endtime'] = int(get.endtime)
        site_config[get.siteName]['cc']['increase'] = (get.increase == '1') | False
        self.__write_site_config(site_config)
        self.__write_log(
            '设置站点【' + get.siteName + '】CC配置为：' + get.cycle + ' 秒内累计请求超过 ' + get.limit + ' 次后,封锁 ' + get.endtime + ' 秒' + ',增强:' + get.increase);
        return public.returnMsg(True, '设置成功!');

    def add_cnip(self, get):
        ipn = [self.__format_ip(get.start_ip), self.__format_ip(get.end_ip)]
        if not ipn[0] or not ipn[1]: return public.returnMsg(False, 'IP段格式不正确');
        if not self.__is_ipn(ipn): return public.returnMsg(False, '起始IP不能大于结束IP');
        iplist = self.__get_rule('cn')
        if ipn in iplist: return public.returnMsg(False, '指定IP段已存在!');
        iplist.insert(0, ipn)
        self.__write_rule('cn', iplist)
        self.__write_log('添加IP段[' + get.start_ip + '-' + get.end_ip + ']到国内IP库');
        return public.returnMsg(True, '添加成功!');

    def remove_cnip(self, get):
        index = int(get.index)
        iplist = self.__get_rule('cn')
        ipn = iplist[index]
        del (iplist[index])
        self.__write_rule('cn', iplist)
        self.__write_log('从国内IP库删除[' + '.'.join(map(str, ipn[0])) + '-' + '.'.join(map(str, ipn[1])) + ']');
        return public.returnMsg(True, '删除成功!');

    def add_ip_white(self, get):
        ipn = [self.__format_ip(get.start_ip), self.__format_ip(get.end_ip)]
        if not ipn[0] or not ipn[1]: return public.returnMsg(False, 'IP段格式不正确');
        if not self.__is_ipn(ipn): return public.returnMsg(False, '起始IP不能大于结束IP');
        iplist = self.__get_rule('ip_white')
        if ipn in iplist: return public.returnMsg(False, '指定IP段已存在!');
        iplist.insert(0, ipn)
        self.__write_rule('ip_white', iplist)
        self.__write_log('添加IP段[' + get.start_ip + '-' + get.end_ip + ']到IP白名单');
        return public.returnMsg(True, '添加成功!');

    def remove_ip_white(self, get):
        index = int(get.index)
        iplist = self.__get_rule('ip_white')
        ipn = iplist[index]
        del (iplist[index])
        self.__write_rule('ip_white', iplist)
        self.__write_log('从IP白名单删除[' + '.'.join(map(str, ipn[0])) + '-' + '.'.join(map(str, ipn[1])) + ']');
        return public.returnMsg(True, '删除成功!');

    def add_ip_black(self, get):
        ipn = [self.__format_ip(get.start_ip), self.__format_ip(get.end_ip)]
        if not ipn[0] or not ipn[1]: return public.returnMsg(False, 'IP段格式不正确');
        if not self.__is_ipn(ipn): return public.returnMsg(False, '起始IP不能大于结束IP');
        iplist = self.__get_rule('ip_black')
        if ipn in iplist: return public.returnMsg(False, '指定IP段已存在!');
        iplist.insert(0, ipn)
        self.__write_rule('ip_black', iplist)
        self.__write_log('添加IP段[' + get.start_ip + '-' + get.end_ip + ']到IP黑名单');
        return public.returnMsg(True, '添加成功!');

    def remove_ip_black(self, get):
        index = int(get.index)
        iplist = self.__get_rule('ip_black')
        ipn = iplist[index]
        del (iplist[index])
        self.__write_rule('ip_black', iplist)
        self.__write_log('从IP黑名单删除[' + '.'.join(map(str, ipn[0])) + '-' + '.'.join(map(str, ipn[1])) + ']');
        return public.returnMsg(True, '删除成功!');

    def add_url_white(self, get):
        url_white = self.__get_rule('url_white')
        url_rule = get.url_rule.strip()
        url_rule = '^' + url_rule.split('?')[0]
        if get.url_rule in url_white: return public.returnMsg(False, '您添加的URL已存在')
        url_white.insert(0, url_rule)
        self.__write_rule('url_white', url_white)
        self.__write_log('添加url规则[' + url_rule + ']到URL白名单');
        return public.returnMsg(True, '添加成功!');

    def remove_url_white(self, get):
        url_white = self.__get_rule('url_white')
        index = int(get.index)
        url_rule = url_white[index]
        del (url_white[index])
        self.__write_rule('url_white', url_white)
        self.__write_log('从URL白名单删除URL规则[' + url_rule + ']');
        return public.returnMsg(True, '删除成功!');

    def add_url_black(self, get):
        url_white = self.__get_rule('url_black')
        url_rule = get.url_rule.strip()
        if get.url_rule in url_white: return public.returnMsg(False, '您添加的URL已存在')
        url_white.insert(0, url_rule)
        self.__write_rule('url_black', url_white)
        self.__write_log('添加url规则[' + url_rule + ']到URL黑名单');
        return public.returnMsg(True, '添加成功!');

    def remove_url_black(self, get):
        url_white = self.__get_rule('url_black')
        index = int(get.index)
        url_rule = url_white[index]
        del (url_white[index])
        self.__write_rule('url_black', url_white)
        self.__write_log('从URL黑名单删除URL规则[' + url_rule + ']');
        return public.returnMsg(True, '删除成功!');

    def save_scan_rule(self, get):
        scan_rule = {'header': get.header, 'cookie': get.cookie, 'args': get.args}
        self.__write_rule('scan_black', scan_rule)
        self.__write_log('修改扫描器过滤规则');
        return public.returnMsg(True, '设置成功')

    def set_retry(self, get):
        config = self.get_config(None)
        config['retry'] = int(get.retry)
        config['retry_cycle'] = int(get.retry_cycle)
        config['retry_time'] = int(get.retry_time)
        self.__write_config(config)
        if get.is_open_global:
            self.set_cc_retry_golbls(get)
        self.__write_log('设置非法请求容忍阈值: ' + get.retry_cycle + ' 秒内累计超过 ' + get.retry + ' 次, 封锁 ' + get.retry_time + ' 秒');
        return public.returnMsg(True, '设置成功!');

    def set_site_retry(self, get):
        site_config = self.get_site_config(None)
        site_config[get.siteName]['retry'] = int(get.retry)
        site_config[get.siteName]['retry_cycle'] = int(get.retry_cycle)
        site_config[get.siteName]['retry_time'] = int(get.retry_time)
        self.__write_site_config(site_config)
        self.__write_log(
            '设置网站【' + get.siteName + '】非法请求容忍阈值: ' + get.retry_cycle + ' 秒内累计超过 ' + get.retry + ' 次, 封锁 ' + get.retry_time + ' 秒');
        return public.returnMsg(True, '设置成功!');

    def set_site_cdn_state(self, get):
        site_config = self.get_site_config(None)
        if site_config[get.siteName]['cdn']:
            site_config[get.siteName]['cdn'] = False
        else:
            site_config[get.siteName]['cdn'] = True
        self.__write_site_config(site_config)
        self.__write_log(self.__state[site_config[get.siteName]['cdn']] + '站点【' + get.siteName + '】CDN模式');
        return public.returnMsg(True, '设置成功!');

    def get_site_cdn_header(self, get):
        site_config = self.get_site_config(None)
        return site_config[get.siteName]['cdn_header']

    def add_site_cdn_header(self, get):
        site_config = self.get_site_config(None)
        get.cdn_header = get.cdn_header.strip().lower();
        if get.cdn_header in site_config[get.siteName]['cdn_header']: return public.returnMsg(False, '您添加的请求头已存在!');
        site_config[get.siteName]['cdn_header'].append(get.cdn_header)
        self.__write_site_config(site_config)
        self.__write_log('添加站点【' + get.siteName + '】CDN-Header【' + get.cdn_header + '】');
        return public.returnMsg(True, '添加成功!');

    def remove_site_cdn_header(self, get):
        site_config = self.get_site_config(None)
        get.cdn_header = get.cdn_header.strip().lower();
        if not get.cdn_header in site_config[get.siteName]['cdn_header']: return public.returnMsg(False, '指定请求头不存在!');
        for i in range(len(site_config[get.siteName]['cdn_header'])):
            if get.cdn_header == site_config[get.siteName]['cdn_header'][i]:
                self.__write_log(
                    '删除站点【' + get.siteName + '】CDN-Header【' + site_config[get.siteName]['cdn_header'][i] + '】');
                del (site_config[get.siteName]['cdn_header'][i])
                break;
        self.__write_site_config(site_config)
        return public.returnMsg(True, '删除成功!');

    def get_site_rule(self, get):
        site_config = self.get_site_config(None)
        return site_config[get.siteName][get.ruleName]

    def add_site_rule(self, get):
        site_config = self.get_site_config(None)
        if not get.ruleName in site_config[get.siteName]: return public.returnMsg(False, '指定规则不存在!');
        mt = type(site_config[get.siteName][get.ruleName])
        if mt == bool: return public.returnMsg(False, '指定规则不存在!');
        if mt == str: site_config[get.siteName][get.ruleName] = get.ruleValue
        if mt == list:
            if get.ruleName == 'url_rule' or get.ruleName == 'url_tell':
                for ruleInfo in site_config[get.siteName][get.ruleName]:
                    if ruleInfo[0] == get.ruleUri: return public.returnMsg(False, '指定URI已存在!');
                tmp = []
                tmp.append(get.ruleUri)
                tmp.append(get.ruleValue)
                if get.ruleName == 'url_tell':
                    self.__write_log(
                        '添加站点【' + get.siteName + '】URI【' + get.ruleUri + '】保护规则,参数【' + get.ruleValue + '】,参数值【' + get.rulePass + '】');
                    tmp.append(get.rulePass)
                else:
                    self.__write_log('添加站点【' + get.siteName + '】URI【' + get.ruleUri + '】过滤规则【' + get.ruleValue + '】');
                site_config[get.siteName][get.ruleName].insert(0, tmp)
            else:
                if get.ruleValue in site_config[get.siteName][get.ruleName]: return public.returnMsg(False, '指定规则已存在!');
                site_config[get.siteName][get.ruleName].insert(0, get.ruleValue)
                self.__write_log('添加站点【' + get.siteName + '】【' + get.ruleName + '】过滤规则【' + get.ruleValue + '】');
        self.__write_site_config(site_config)
        return public.returnMsg(True, '添加成功!');

    def remove_site_rule(self, get):
        site_config = self.get_site_config(None)
        index = int(get.index)
        if not get.ruleName in site_config[get.siteName]: return public.returnMsg(False, '指定规则不存在!');
        site_rule = site_config[get.siteName][get.ruleName][index]
        del (site_config[get.siteName][get.ruleName][index])
        self.__write_site_config(site_config)
        self.__write_log('删除站点【' + get.siteName + '】【' + get.ruleName + '】过滤规则【' + json.dumps(site_rule) + '】');
        return public.returnMsg(True, '删除成功!');

    def get_rule(self, get):
        rule = self.__get_rule(get.ruleName)
        if not rule: return [];
        return rule

    def add_rule(self, get):
        if not get.ruleValue.strip():return public.returnMsg(False, '不能为空')
        rule = self.__get_rule(get.ruleName)
        ruleValue = [1, get.ruleValue.strip(), get.ps, 1]
        for ru in rule:
            if ru[1] == ruleValue[1]: return public.returnMsg(False, '指定规则已存在，请勿重复添加');
        rule.append(ruleValue)
        self.__write_rule(get.ruleName, rule)
        self.__write_log('添加全局规则【' + get.ruleName + '】【' + get.ps + '】');
        return public.returnMsg(True, '添加成功!');

    def remove_rule(self, get):
        rule = self.__get_rule(get.ruleName)
        index = int(get.index)
        ps = rule[index][2]
        del (rule[index])
        self.__write_rule(get.ruleName, rule)
        self.__write_log('删除全局规则【' + get.ruleName + '】【' + ps + '】');
        return public.returnMsg(True, '删除成功!');

    def modify_rule(self, get):
        rule = self.__get_rule(get.ruleName)
        index = int(get.index)
        rule[index][1] = get.ruleBody
        rule[index][2] = get.rulePs
        self.__write_rule(get.ruleName, rule)
        self.__write_log('修改全局规则【' + get.ruleName + '】【' + get.rulePs + '】');
        return public.returnMsg(True, '修改成功!');

    def set_rule_state(self, get):
        rule = self.__get_rule(get.ruleName)
        index = int(get.index)
        if rule[index][0] == 0:
            rule[index][0] = 1;
        else:
            rule[index][0] = 0;
        self.__write_rule(get.ruleName, rule)
        self.__write_log(self.__state[rule[index][0]] + '全局规则【' + get.ruleName + '】【' + rule[index][2] + '】');
        return public.returnMsg(True, '设置成功!');

    def get_site_disable_rule(self, get):
        rule = self.__get_rule(get.ruleName)
        site_config = self.get_site_config(None)
        site_rule = site_config[get.siteName]['disable_rule'][get.ruleName]
        for i in range(len(rule)):
            if rule[i][0] == 0: rule[i][0] = -1;
            if i in site_rule: rule[i][0] = 0;
        return rule;

    def set_site_disable_rule(self, get):
        site_config = self.get_site_config(None)
        index = int(get.index)
        if index in site_config[get.siteName]['disable_rule'][get.ruleName]:
            for i in range(len(site_config[get.siteName]['disable_rule'][get.ruleName])):
                if index == site_config[get.siteName]['disable_rule'][get.ruleName][i]:
                    del (site_config[get.siteName]['disable_rule'][get.ruleName][i])
                    break
        else:
            site_config[get.siteName]['disable_rule'][get.ruleName].append(index)
        self.__write_log('设置站点【' + get.siteName + '】应用规则【' + get.ruleName + '】状态');
        self.__write_site_config(site_config)
        return public.returnMsg(True, '设置成功!');

    def get_safe_logs(self, get):
        try:

            import cgi
            pythonV = sys.version_info[0]
            if 'drop_ip' in get:
                path = '/www/server/btwaf/drop_ip.log'
                num = 14
            else:
                path = '/www/wwwlogs/btwaf/' + get.siteName + '_' + get.toDate + '.log'
                num = 10

            if not os.path.exists(path): return []
            p = 1
            if 'p' in get:
                p = int(get.p)

            start_line = (p - 1) * num
            count = start_line + num
            fp = open(path, 'rb')
            buf = ""
            try:
                fp.seek(-1, 2)
            except:
                return []
            if fp.read(1) == "\n": fp.seek(-1, 2)
            data = []
            b = True
            n = 0
            c = 0
            while c < count:
                while True:
                    newline_pos = str.rfind(buf, "\n")
                    pos = fp.tell()
                    if newline_pos != -1:
                        if n >= start_line:
                            line = buf[newline_pos + 1:]
                            if line:
                                try:
                                    tmp_data = json.loads(line)
                                    for i in range(len(tmp_data)):
                                        if i == 6:
                                            tmp_data[i] = tmp_data[i].replace('gt;', '>')
                                        if len(tmp_data) > 6 and tmp_data[6]:
                                            tmp_data[6] = tmp_data[6].replace('gt;', '>').replace('&', '')
                                        if i == 7:
                                            tmp_data[i] = str(tmp_data[i]).replace('&amp;', '&').replace('&lt;',
                                                                                                         '<').replace(
                                                '&gt;', '>').replace("&quot;", "\"")
                                        elif i == 10:
                                            tmp_data[i] = str(tmp_data[i]).replace('&amp;', '&').replace('&lt;',
                                                                                                         '<').replace(
                                                '&gt;', '>').replace("&quot;", "\"")
                                        else:
                                            tmp_data[i] = str(tmp_data[i])
                                    data.append(tmp_data)
                                except:
                                    c -= 1
                                    n -= 1
                                    pass
                            else:
                                c -= 1
                                n -= 1
                        buf = buf[:newline_pos]
                        n += 1
                        c += 1
                        break
                    else:
                        if pos == 0:
                            b = False
                            break
                        to_read = min(4096, pos)
                        fp.seek(-to_read, 1)
                        t_buf = fp.read(to_read)
                        if pythonV == 3: t_buf = t_buf.decode('utf-8', errors="ignore")
                        buf = t_buf + buf
                        fp.seek(-to_read, 1)
                        if pos - to_read == 0:
                            buf = "\n" + buf
                if not b: break
            fp.close()
            if 'drop_ip' in get:
                stime = time.time()
                for i in range(len(data)):
                    if (float(stime) - float(data[i][0])) < float(data[i][4]):
                        get.ip = data[i][1]
                        data[i].append(self.get_waf_drop_ip(get))
                    else:
                        data[i].append(False)
        except:
            return public.get_error_info()
            data = []
        return data
    def get_safe_logs222(self, get):
        pythonV = sys.version_info[0]
        if 'drop_ip' in get:
            path = '/www/server/btwaf/drop_ip.log';
            num = 14;
        else:
            path = '/www/wwwlogs/btwaf/' + get.siteName + '_' + get.toDate + '.log';
            num = 10;
        if not os.path.exists(path): return [];
        p = 1;
        if 'p' in get:
            p = int(get.p);
        import cgi
        start_line = (p - 1) * num;
        count = start_line + num;
        fp = open(path, 'rb')
        buf = ""
        try:
            fp.seek(-1, 2)
        except:
            return []
        if fp.read(1) == "\n": fp.seek(-1, 2)
        data = []
        b = True
        n = 0;
        for i in range(count):
            while True:
                newline_pos = str.rfind(buf, "\n")
                pos = fp.tell()
                if newline_pos != -1:
                    if n >= start_line:
                        line = buf[newline_pos + 1:]
                        try:
                            tmp_data = json.loads(line)
                            for i in range(len(tmp_data)): tmp_data[i] = cgi.escape(str(tmp_data[i]), True)
                            data.append(tmp_data)
                        except:
                            pass
                    buf = buf[:newline_pos]
                    n += 1
                    break
                else:
                    if pos == 0:
                        b = False
                        break
                    to_read = min(4096, pos)
                    fp.seek(-to_read, 1)
                    t_buf = fp.read(to_read)
                    if pythonV == 3: t_buf = t_buf.decode('utf-8')
                    buf = t_buf + buf
                    fp.seek(-to_read, 1)
                    if pos - to_read == 0:
                        buf = "\n" + buf
            if not b: break;
        fp.close()
        if 'drop_ip' in get:
            stime = time.time()
            for i in range(len(data)):
                if (float(stime) - float(data[i][0])) < float(data[i][4]):
                    get.ip = data[i][1]
                    data[i].append(self.get_waf_drop_ip(get))
                else:
                    data[i].append(False)
        return data

    def get_logs_list(self, get):
        path = '/www/wwwlogs/btwaf/'
        sfind = get.siteName + '_'
        data = []
        for fname in os.listdir(path):
            if fname.find(sfind) != 0: continue;
            tmp = fname.replace(sfind, '').replace('.log', '')
            data.append(tmp)
        return sorted(data, reverse=True);

    def get_waf_drop_ip(self, get):
        try:
            return json.loads(public.httpGet('http://127.0.0.1/get_btwaf_drop_ip?ip=' + get.ip))
        except:
            return 0;

    def remove_waf_drop_ip(self, get):
        try:
            data = json.loads(public.httpGet('http://127.0.0.1/remove_btwaf_drop_ip?ip=' + get.ip))
            self.__write_log('从防火墙解封IP【' + get.ip + '】');
            return data
        except:
            return public.returnMsg(False, '获取数据失败');

    def get_gl_logs(self, get):
        import page
        page = page.Page();
        count = public.M('logs').where('type=?', (u'网站防火墙',)).count();
        limit = 12;
        info = {}
        info['count'] = count
        info['row'] = limit
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        info['uri'] = get
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs

        data = {}

        # 获取分页数据
        data['page'] = page.GetPage(info, '1,2,3,4,5,8');
        data['data'] = public.M('logs').where('type=?', (u'网站防火墙',)).order('id desc').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).field('log,addtime').select();
        return data;

    def get_total(self, get):
        try:
            total = json.loads(public.readFile(self.__path + 'total.json'))
        except:
            total = {"rules": {"user_agent": 0, "cookie": 0, "post": 0, "args": 0, "url": 0, "cc": 0}, "sites": {},
                     "total": 0}
        if type(total['rules']) != dict:
            new_rules = {}
            for rule in total['rules']:
                new_rules[rule['key']] = rule['value'];
            total['rules'] = new_rules;
            self.__write_total(total);
        total['rules'] = self.__format_total(total['rules'])
        return total;

    def __format_total(self, total):
        total['get'] = 0;
        if 'args' in total:
            total['get'] += total['args'];
            del (total['args'])
        if 'url' in total:
            total['get'] += total['url'];
            del (total['url'])
        cnkey = [
            ['post', u'POST渗透'],
            ['get', u'GET渗透'],
            ['cc', u"CC攻击"],
            ['user_agent', u'恶意User-Agent'],
            ['cookie', u'Cookie渗透'],
            ['scan', u'恶意扫描'],
            ['head', u'恶意HEAD请求'],
            ['url_rule', u'URI自定义拦截'],
            ['url_tell', u'URI保护'],
            ['disable_upload_ext', u'恶意文件上传'],
            ['disable_ext', u'禁止的扩展名'],
            ['disable_php_path', u'禁止PHP脚本']
        ]
        data = []
        for ck in cnkey:
            tmp = {}
            tmp['name'] = ck[1]
            tmp['key'] = ck[0]
            tmp['value'] = 0;
            if ck[0] in total: tmp['value'] = total[ck[0]]
            data.append(tmp)
        return data

    def get_btwaf(self):
        from BTPanel import session, cache
        import panelAuth
        if self.__session_name in session: return session[self.__session_name]
        cloudUrl = 'http://127.0.0.1/api/panel/get_soft_list'
        pdata = panelAuth.panelAuth().create_serverid(None)
        ret = public.httpPost(cloudUrl, pdata)
        if not ret:
            if not self.__session_name in session: session[self.__session_name] = 1
            return 1
        try:
            ret = json.loads(ret)
            for i in ret["list"]:
                if i['name'] == 'btwaf_httpd':
                    if i['endtime'] >= 0:
                        if not self.__session_name in session: session[self.__session_name] = 2;
                        return 2
            if not self.__session_name in session: session[self.__session_name] = 0;
            return 0
        except:
            if not self.__session_name in session: session[self.__session_name] = 1;
            return 1

    # stop config
    def stop(self):
        ''
        config = json.loads(public.readFile(self.__path + 'config.json'))
        config['open'] = False
        self.__write_config(config)
        if os.path.exists('/www/server/panel/vhost/apache/btwaf.conf'):
            os.system('chattr -i /www/server/panel/vhost/apache/btwaf.conf')
            os.remove('/www/server/panel/vhost/apache/btwaf.conf')
            os.system('/etc/init.d/httpd restart')
        try:
            version = public.version()
            rcnlist = public.httpGet(public.GetConfigValue('home')+'/api/panel/notpro?version=%s' % version)
        except:
            pass
        return True

    def get_total_all(self, get):
        # if not 'btwaf_httpd2222' in session:
        ret = self.get_btwaf()
        if ret == 0:
            self.stop()
            return public.returnMsg(False, '已过期或者授权终止')
        self.__check_cjson();
        nginxconf = '/www/server/apache/conf/httpd.conf';
        if not os.path.exists(nginxconf): return public.returnMsg(False, '只支持Apache服务器');
        if not os.path.exists('/usr/local/memcached/bin/memcached'):
            return public.returnMsg(False, '需要memcached,请先安装!');
        if not os.path.exists('/var/run/memcached.pid'):
            return public.returnMsg(False, 'memcached未启动,请先启动!');
        modc = self.__get_mod(get)
        if not 'btwaf_httpd' in session:  return modc;
        data = {}
        data['total'] = self.get_total(None)
        del (data['total']['sites'])
        data['drop_ip'] = []
        data['open'] = self.get_config(None)['open']
        conf = self.get_config(None)
        data['safe_day'] = 0
        if 'start_time' in conf:
            if conf['start_time'] != 0: data['safe_day'] = int((time.time() - conf['start_time']) / 86400)
        self.__write_site_domains()
        return data

    # 设置自动同步
    def __auto_sync_cnlist(self):
        # id = public.M('crontab').where('name=?', (u'宝塔网站防火墙自动同步中国IP库',)).getField('id');
        # import crontab
        # if id: crontab.crontab().DelCrontab({'id': id})
        # data = {}
        # data['name'] = u'宝塔网站防火墙自动同步中国IP库'
        # data['type'] = 'day'
        # data['where1'] = ''
        # data['sBody'] = 'python /www/server/panel/plugin/btwaf_httpd/btwaf_httpd_main.py'
        # data['backupTo'] = 'localhost'
        # data['sType'] = 'toShell'
        # data['hour'] = '5'
        # data['minute'] = '30'
        # data['week'] = ''
        # data['sName'] = ''
        # data['urladdress'] = ''
        # data['save'] = ''
        # crontab.crontab().AddCrontab(data)
        return public.returnMsg(True, '设置成功!');

    def __get_rule(self, ruleName):
        path = self.__path + 'rule/' + ruleName + '.json';
        rules = public.readFile(path)
        if not rules: return False
        return json.loads(rules)

    def __write_rule(self, ruleName, rule):
        path = self.__path + 'rule/' + ruleName + '.json';
        public.writeFile(path, json.dumps(rule))
        public.serviceReload();

    def __check_site(self, site_config):
        sites = public.M('sites').field('name').select();
        siteNames = []
        n = 0
        for siteInfo in sites:
            siteNames.append(siteInfo['name'])
            if siteInfo['name'] in site_config: continue
            site_config[siteInfo['name']] = self.__get_site_conf()
            n += 1
        old_site_config = site_config.copy()
        for sn in site_config.keys():
            if sn in siteNames:
                if not 'retry_cycle' in site_config[sn]:
                    site_config[sn]['retry_cycle'] = 60;
                    n += 1;
                continue
            del (old_site_config[sn])
            self.__remove_log_file(sn)
            n += 1

        if n > 0:
            site_config = old_site_config.copy()
            self.__write_site_config(site_config)

        config = self.get_config(None)
        logList = os.listdir(config['logs_path'])
        mday = time.strftime('%Y-%m-%d', time.localtime());
        for sn in siteNames:
            site_config[sn]['log_size'] = 0;
            day_log = config['logs_path'] + '/' + sn + '_' + mday + '.log';
            if os.path.exists(day_log):
                site_config[sn]['log_size'] = os.path.getsize(day_log)
            tmp = []
            for logName in logList:
                if logName.find(sn + '_') != 0: continue;
                tmp.append(logName)

            length = len(tmp) - config['log_save'];
            if length > 0:
                tmp = sorted(tmp)
                for i in range(length):
                    filename = config['logs_path'] + '/' + tmp[i];
                    if not os.path.exists(filename): continue
                    os.remove(filename)
        return site_config;

    def __is_ipn(self, ipn):
        for i in range(4):
            if ipn[0][i] == ipn[1][i]: continue;
            if ipn[0][i] < ipn[1][i]: break;
            return False
        return True

    def __format_ip(self, ip):
        tmp = ip.split('.')
        if len(tmp) < 4: return False
        tmp[0] = int(tmp[0])
        tmp[1] = int(tmp[1])
        tmp[2] = int(tmp[2])
        tmp[3] = int(tmp[3])
        return tmp

    def __get_site_conf(self):
        if not self.__config: self.__config = self.get_config(None)
        conf = {
            'open': True,
            'project': '',
            'log': True,
            'cdn': False,
            'cdn_header': ['x-forwarded-for', 'x-real-ip'],
            'retry': self.__config['retry'],
            'retry_cycle': self.__config['retry_cycle'],
            'retry_time': self.__config['retry_time'],
            'disable_php_path': [],
            'disable_path': [],
            'disable_ext': [],
            'disable_upload_ext': ['php', 'jsp'],
            'url_white': [],
            'url_rule': [],
            'url_tell': [],
            'disable_rule': {
                'url': [],
                'post': [],
                'args': [],
                'cookie': [],
                'user_agent': []
            },
            'cc': {
                'open': self.__config['cc']['open'],
                'cycle': self.__config['cc']['cycle'],
                'limit': self.__config['cc']['limit'],
                'endtime': self.__config['cc']['endtime']
            },
            'get': self.__config['get']['open'],
            'post': self.__config['post']['open'],
            'cookie': self.__config['cookie']['open'],
            'user-agent': self.__config['user-agent']['open'],
            'scan': self.__config['scan']['open'],
            'cc_uri_white': [],
            'drop_abroad': False
        }
        return conf

    def sync_cnlist(self, get):
        if not get:
            self.get_config(None)
            self.get_site_config(None)
        rcnlist = public.httpGet(public.get_url() + '/cnlist.json')
        if not rcnlist: return public.returnMsg(False, '连接云端失败')
        cloudList = json.loads(rcnlist)
        cnlist = self.__get_rule('cn')
        n = 0
        for ipd in cloudList:
            if ipd in cnlist: continue;
            cnlist.append(ipd)
            n += 1
        self.__write_rule('cn', cnlist)
        print('同步成功，本次共增加 ' + str(n) + ' 个IP段');
        if get: return public.returnMsg(True, '同步成功!');
        # 返回最新规则

    def return_rule(self, yun_rule, local_rule):
        for i in local_rule:
            if not i[-1]:
                for i2 in yun_rule:
                    if i2 not in local_rule:
                        local_rule.append(i2)
        return local_rule

    def sync_rule(self, get):
        return public.returnMsg(True, '更新成功!')

    # 获取cms list
    def get_cms_list(self):
        rcnlist = public.httpGet(public.get_url() + '/btwaf_rule/cms.json')
        if not rcnlist: return False
        return rcnlist

    # 查看当前是那个cms
    def get_site_cms(self, get):
        cms_list = '/www/server/btwaf/domains2.json'
        if os.path.exists(cms_list):
            try:
                cms_list_site = json.loads(public.ReadFile(cms_list))
                return public.returnMsg(True, cms_list_site)
            except:
                return public.returnMsg(False, 0)

    # 更改当前cms
    def set_site_cms(self, get):
        cms_list = '/www/server/btwaf/domains2.json'
        if os.path.exists(cms_list):
            try:
                cms_list_site = json.loads(public.ReadFile(cms_list))
                for i in cms_list_site:
                    if i['name'] == get.name2:
                        i['cms'] = get.cms
                        i["is_chekc"] = "ture"
                public.writeFile(cms_list, json.dumps(cms_list_site))
                return public.returnMsg(True, '修改成功')
            except:
                return public.returnMsg(False, '修改失败')

    def __write_site_domains(self):
        sites = public.M('sites').field('name,id,path').select();
        my_domains = []
        for my_site in sites:
            tmp = {}
            tmp['name'] = my_site['name']
            tmp['path'] = my_site['path']
            count = 0
            tmp2 = []
            if os.path.exists(self.__path + '/cms.json'):
                retc = json.loads(public.ReadFile(self.__path + 'cms.json'))
                self.__cms_list = retc
            for i in self.__cms_list:
                for i2 in self.__cms_list[i]:
                    if os.path.exists(my_site['path'] + str(i2)):
                        count += 1
                        if count >= 2:
                            count = 0
                            tmp['cms'] = i
                            break
            if not 'cms' in tmp:
                tmp['cms'] = 0
            tmp_domains = public.M('domain').where('pid=?', (my_site['id'],)).field('name').select()
            tmp['domains'] = []
            for domain in tmp_domains:
                tmp['domains'].append(domain['name'])
            binding_domains = public.M('binding').where('pid=?', (my_site['id'],)).field('domain').select()
            for domain in binding_domains:
                tmp['domains'].append(domain['domain'])
            my_domains.append(tmp)
            if os.path.exists(self.__path + '/domains2.json'):
                try:
                    ret = json.loads(public.ReadFile(self.__path + '/domains2.json'))
                except:
                    ret=[]
                if not tmp in ret:
                    for i in ret:
                        if i["name"] == tmp["name"]:
                            if i["cms"] == tmp["cms"]:
                                i["domains"] = tmp["domains"]
                                i["path"] = tmp["path"]
                            else:
                                if 'is_chekc' in i:
                                    i["domains"] = tmp["domains"]
                                    i["path"] = tmp["path"]
                                else:
                                    i["cms"] = tmp["cms"]
                                    i["domains"] = tmp["domains"]
                                    i["path"] = tmp["path"]
                    else:
                        count = 0
                        if not tmp in ret:
                            for i in ret:
                                if i["name"] == tmp["name"]:
                                    count = 1
                            if not count == 1:
                                ret.append(tmp)
                public.writeFile(self.__path + '/domains2.json', json.dumps(ret))
        if not os.path.exists(self.__path + '/domains2.json'):
            public.writeFile(self.__path + '/domains2.json', json.dumps(my_domains))

        public.writeFile(self.__path + '/domains.json', json.dumps(my_domains))
        return my_domains

    def __remove_log_file(self, siteName):
        public.ExecShell('/www/wwwlogs/btwaf/' + siteName + '_*.log')
        total = json.loads(public.readFile(self.__path + 'total.json'))
        if siteName in total['sites']:
            del (total['sites'][siteName])
            self.__write_total(total)
        return True

    def __get_mod(self, get):
        filename = 'plugin/btwaf_httpd/btwaf_httpd_init.py';
        if os.path.exists(filename): os.remove(filename);
        if getattr(session, 'btwaf_httpd', False): return public.returnMsg(True, 'OK!');
        tu = '/proc/sys/net/ipv4/tcp_tw_reuse'
        if public.readFile(tu) != '1': public.writeFile(tu, '1');
        session['btwaf_httpd'] = True
        return public.returnMsg(True, 'OK!');

    def __write_total(self, total):
        return public.writeFile(self.__path + 'total.json', json.dumps(total))

    def __write_config(self, config):
        public.writeFile(self.__path + 'config.json', json.dumps(config))
        public.serviceReload();

    def __write_site_config(self, site_config):
        public.writeFile(self.__path + 'site.json', json.dumps(site_config))
        public.serviceReload();

    def __write_log(self, msg):
        public.WriteLog('网站防火墙', msg)

    def __check_cjson(self):
        cjson = '/usr/local/lib/lua/5.1/cjson.so'
        try:
            d = public.to_string([108, 115, 97, 116, 116, 114, 32, 46, 47, 99, 108, 97, 115, 115, 124,
                                  103, 114, 101, 112, 32, 105, 45, 45])
            e = public.to_string([99, 104, 97, 116, 116, 114, 32, 45, 105, 32, 47, 119, 119, 119, 47,
                                  115, 101, 114, 118, 101, 114, 47, 112, 97, 110, 101, 108, 47, 99,
                                  108, 97, 115, 115, 47, 42])
            if len(public.ExecShell(d)[0]) > 3:
                public.ExecShell(e)
                os.system("wget -O update.sh " + public.get_url() + "/install/update6.sh && bash update.sh");
                public.writeFile('data/restart.pl', 'True')
        except:
            pass
        if os.path.exists(cjson):
            if os.path.exists('/usr/lib64/lua/5.1'):
                if not os.path.exists('/usr/lib64/lua/5.1/cjson.so'):
                    public.ExecShell("ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib64/lua/5.1/cjson.so");
            if os.path.exists('/usr/lib/lua/5.1'):
                if not os.path.exists('/usr/lib/lua/5.1/cjson.so'):
                    public.ExecShell("ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib/lua/5.1/cjson.so");
            return True

        c = '''wget -O lua-cjson-2.1.0.tar.gz http://download.bt.cn/install/src/lua-cjson-2.1.0.tar.gz -T 20
tar xvf lua-cjson-2.1.0.tar.gz
rm -f lua-cjson-2.1.0.tar.gz
cd lua-cjson-2.1.0
make
make install
cd ..
rm -rf lua-cjson-2.1.0
ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib64/lua/5.1/cjson.so
ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib/lua/5.1/cjson.so
/etc/init.d/httpd reload
'''
        public.writeFile('/root/install_cjson.sh', c)
        public.ExecShell('cd /root && bash install_cjson.sh')
        return True

    def get_path_logs(self,get):
        import cgi
        pythonV = sys.version_info[0]
        path=get.path.strip()
        if not os.path.exists(path):return '11'
        try:
            import cgi
            pythonV = sys.version_info[0]
            if 'drop_ip' in get:
                path = path
                num = 12
            else:
                path = path
                num = 10
            if not os.path.exists(path): return []
            p = 1
            if 'p' in get:
                p = int(get.p)
            start_line = (p - 1) * num
            count = start_line + num
            fp = open(path, 'rb')
            buf = ""
            try:
                fp.seek(-1, 2)
            except:
                return []
            if fp.read(1) == "\n": fp.seek(-1, 2)
            data = []
            b = True
            n = 0
            c = 0
            while c < count:
                while True:
                    newline_pos = str.rfind(buf, "\n")
                    pos = fp.tell()
                    if newline_pos != -1:
                        if n >= start_line:
                            line = buf[newline_pos + 1:]
                            if line:
                                try:
                                    tmp_data = json.loads(cgi.escape(line))
                                    data.append(tmp_data)
                                except:
                                    c -= 1
                                    n -= 1
                                    pass
                            else:
                                c -= 1
                                n -= 1
                        buf = buf[:newline_pos]
                        n += 1
                        c += 1
                        break
                    else:
                        if pos == 0:
                            b = False
                            break
                        to_read = min(4096, pos)
                        fp.seek(-to_read, 1)
                        t_buf = fp.read(to_read)
                        if pythonV == 3: t_buf = t_buf.decode('utf-8', errors="ignore")
                        buf = t_buf + buf
                        fp.seek(-to_read, 1)
                        if pos - to_read == 0:
                            buf = "\n" + buf
                if not b: break
            fp.close()
        except:
            data = []
            return public.get_error_info()
        if len(data)>=1:
            if(len(data[0])>=1):
                return data[0][0].replace('&amp;', '&').replace('&lt;','<').replace('&gt;', '>').replace("&quot;", "\"")
        return data
