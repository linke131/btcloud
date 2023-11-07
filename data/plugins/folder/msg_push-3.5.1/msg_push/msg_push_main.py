#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: zhw <zhw@bt.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   宝塔消息推送
#+--------------------------------------------------------------------
import sys
sys.path.append('/www/server/panel/class')
import json, os, time, public, re, datetime, base64
os.chdir("/www/server/panel")
class msg_push_main:
    access_defs = ['check_main']
    msg_push_cache = {}

    # 用户列表
    def __init__(self):
        self.panel_path = "/www/server/panel"
        self.plugin_path = "{}/plugin/msg_push".format(self.panel_path)
        self.warningUrl = "http://www.bt.cn/api/index/send_mail_msg"
        self.__mail_config = '{}/data/stmp_mail.json'.format(self.panel_path)
        self.__mail_list_data = '{}/data/mail_list.json'.format(self.panel_path)
        self.__dingding_config = '{}/data/dingding.json'.format(self.panel_path)
        self.msg_file = "{}/msg.json".format(self.plugin_path)
        self.pyv = self.check_pyv()[0]
        self.pip = self.check_pyv()[1]
        self.init_msg()

    def check_pyv(self):
        if os.path.exists('{}/pyenv'.format(self.panel_path)):
            pyv = '{}/pyenv/bin/python'.format(self.panel_path)
            pip = '{}/pyenv/bin/pip'.format(self.panel_path)
        else:
            pyv = '/usr/bin/python'
            pip = '/usr/bin/pip'
        return [pyv,pip]

    def init_msg(self):
        content = public.readFile(self.msg_file)
        try:
            content = json.loads(content)
        except:
            public.writeFile(self.msg_file,json.dumps([]))


    # 启动监控服务
    def StartServer(self, get):
        if self.check_monitor():
            a = self.CheckServer(get)
            if a["status"] == True:
                return public.returnMsg(True, '服务已经在运行了无需再启动')
            public.ExecShell("nohup %s %s/main &" % (self.pyv,self.plugin_path))
            a = self.CheckServer(get)
            if a["status"] == True:
                public.ExecShell("/usr/bin/echo '1' > %s/open.txt" % self.plugin_path)
                public.writeFile('',self.msg_file)
                return public.returnMsg(True, '服务启动成功')
            else:
                return public.returnMsg(False, '服务启动失败')
        else:
            return public.returnMsg(False, '请先打开 面板监控<br>开启方法: 菜单-->监控-->开启监控</br>')

    def StopServer(self, get):
        a = self.CheckServer(get)
        if a["status"] != True:
            return public.returnMsg(True, '服务没有启动')
        else:
            a = public.ExecShell("ps aux|grep msg_push|grep -v 'grep'|awk 'NR==1 {print $2}'")[0].strip("\n")
            public.ExecShell("kill -9 %s" % a)
            public.ExecShell("/usr/bin/echo '0' > %s/open.txt" % self.plugin_path)
            return public.returnMsg(True, '服务停止成功')

    def CheckServer(self, get):
        a = public.ExecShell("ps aux|grep 'msg_push'|grep -v 'grep'|wc -l")[0].strip()
        if a == "0":
            return public.returnMsg(False, '服务未启动')
        else:
            return public.returnMsg(True, '服务已启动')

    # 新建消息推送
    def create_msg_even(self, get):
        res = self.__check_msg_even(get)
        if res:
            return res
        if not self.check_monitor():
            return public.returnMsg(False, '请先开启面板监控')
        if get.check_type != "report":
            if int(get.push_time) < 10:
                return public.returnMsg(False, '邮件发送间隔时间不能小于10分钟')
        if get.check_type == "net" and get.push_type == "sms":
            return public.returnMsg(False, '短信无法发送网络类型短信，请选择其他推送方式！')
        getdata = get.__dict__
        data = {}
        for k in getdata.keys():
            if k == "args" or k == "data" or k == "s" or k == "action" or k == "name":
                continue
            if "value" in k:
                try:
                    n = int(getdata[k])
                    if n > 100 or n <= 0:
                        return public.returnMsg(False, '{}:{} 阈值不能小于等于0或大于100'.format(k,n))
                except:
                    return public.returnMsg(False, '{}:{} 请输入整数'.format(k,getdata[k]))
            if "time" in k:
                try:

                    n = int(getdata[k])
                    if n <= 0:
                        return public.returnMsg(False, '{}:{} 不能输入负数或0'.format(k,n))
                except:
                    return public.returnMsg(False, '{}:{} 请输入整数'.format(k,getdata[k]))
            if k =="mysql":
                if getdata[k] == "1":
                    if not os.path.exists("{}/masterslave".format(self.plugin_path)):
                        return public.returnMsg(False, '没有安装【Mysql主从】插件，无法启用监控')
            if k =="report" and getdata['check_type'] != 'check_ssl_expired':
                if not os.path.exists("{}/total".format(self.plugin_path)):
                    return public.returnMsg(False, '没有安装【网站监控报表】插件插件，无法启用报表发送')
            if k =="services":
                getdata[k] = json.loads(getdata[k])
            data[k] = getdata[k]
        if "url_list" in data.keys():
            site = {
                'url_list':data["url_list"],
                'key':data["key"],
                'site_name':data["site_name"],
                'adv':data["adv"]
            }
            data.pop("url_list")
            data.pop("key")
            data.pop("adv")
            data.pop("site_name")
            data["site"] = site
        conf_data = self.__read_config("{}/config.json".format(self.plugin_path))
        conf_data.append(data)
        self.__write_config("{}/config.json".format(self.plugin_path), conf_data)
        public.WriteLog('消息推送', ' 添加监控[' + data["push_name"] + ']')
        return public.returnMsg(True, '添加成功')

    # 检查事件是否存在
    def __check_msg_even(self,get):
        conf_data = self.__read_config("{}/config.json".format(self.plugin_path))
        for i in conf_data:
            if i["push_name"] == get.push_name:
                return public.returnMsg(False, '指定消息推送【{}】已存在'.format(get.push_name))
            if i['check_type'] == get.check_type:
                if get.check_type == 'cpu':
                    return public.returnMsg(False, '【CPU】监控只需要添加一个！')
                elif get.check_type == 'mem':
                    return public.returnMsg(False, '【内存】监控只需要添加一个！')
                elif get.check_type == 'disk':
                    return public.returnMsg(False, '【硬盘】监控只需要添加一个！')
                elif get.check_type == 'net':
                    return public.returnMsg(False, '【带宽】监控只需要添加一个！')
                elif get.check_type == 'check_ssl_expired':
                    return public.returnMsg(False, '【SSL到期】监控只需要添加一个！')

    # 获取事件列表
    def get_msgpush_list(self, get):
        conf = self.__read_config("{}/config.json".format(self.plugin_path))
        for i in conf:
            # if "push_time" in i.keys():
            #     i["push_time"] = "10"
            try:
                if "site" in i:
                    i["url_list"] = i["site"]["url_list"]
                    i["key"] = i["site"]["key"]
                    i["adv"] = i["site"]["adv"]
                    i["site_name"] = i["site"]["site_name"]
                    i.pop("site")
            # 兼容老配置
                for k in i.keys():
                    if '_alarm_value' in k:
                        tmp = i[k]
                        del (i[k])
                        i['alarm_value'] = tmp

                    if '_check_time' in k:
                        tmp = i[k]
                        del (i[k])
                        i['check_time'] = tmp
            except:
                return public.get_error_info()
                pass
        public.writeFile("{}/config.json".format(self.plugin_path),json.dumps(conf))
        return conf

    def get_local_site_list(self,get=None):
        site = {}
        site_list = public.M("sites").field("id,name").select()
        for i in site_list:
            domain_list = public.M("domain").where("pid=?", (i["id"],)).field("name").select()
            l = []
            for domain in domain_list:
                l.append(domain["name"])
            site[i["name"]] = l
        return site

    def check_value_time(self,value):
        try:
            a = int(value)
            if a <= 0:
                return public.returnMsg(False, '{} 不能输入负数或0'.format(a))
        except:
            return public.returnMsg(False, '{} 请输入整数'.format(a))

    def check_args(self,get):
        values = {}
        if hasattr(get, 'alarm_value'):
            try:
                a = int(get.alarm_value)
                if a <= 0 or a > 100:
                    return public.returnMsg(False, 'alarm_value:{} 阈值不能小于等于0或大于100'.format(get.alarm_value))
            except:
                return public.returnMsg(False, 'alarm_value:{} 请输入整数'.format(get.alarm_value))
            values['alarm_value'] = get.alarm_value
        if hasattr(get, 'open'):
            values['open'] = get.open
        if hasattr(get, 'report'):
            values['report'] = get.report
        if hasattr(get, 'ssl_check_time'):
            tmp = self.check_value_time(get.ssl_check_time)
            if tmp:
                return tmp
            values['ssl_check_time'] = get.ssl_check_time
        if hasattr(get, 'report_type'):
            values['report_type'] = get.report_type
        if hasattr(get, 'push_time'):
            tmp = self.check_value_time(get.push_time)
            if tmp:
                return tmp
            values['push_time'] = get.push_time
        if hasattr(get, 'check_time'):
            tmp = self.check_value_time(get.check_time)
            if tmp:
                return tmp
            values['check_time'] = get.check_time
        if hasattr(get, 'net_bandwidth'):
            values['net_bandwidth'] = get.net_bandwidth
        if hasattr(get, 'netcard'):
            values['netcard'] = get.netcard
        if hasattr(get, 'site_check_url'):
            values['site_check_url'] = get.site_check_url
        if hasattr(get, 'site_check_word'):
            values['site_check_word'] = get.site_check_word
        if hasattr(get, 'url_list'):
            values['url_list'] = get.url_list
        if hasattr(get, 'key'):
            values['key'] = get.key
        if hasattr(get, 'adv'):
            values['adv'] = get.adv
        if hasattr(get, 'site_name'):
            values['site_name'] = get.site_name
        if hasattr(get, 'push_name'):
            values['push_name'] = get.push_name
        if hasattr(get, 'check_type'):
            values['check_type'] = get.check_type
        if hasattr(get, 'push_type'):
            values['push_type'] = get.push_type
        if hasattr(get, 'services'):
            values['services'] = json.loads(get.services)
        if hasattr(get, 'act'):
            values['act'] = get.act
        if hasattr(get, 'ua_key'):
            values['ua_key'] = get.ua_key
        return public.returnMsg(True,values)

    def get_change_logs(self,desc_content,key,conf,v):
        """
        :param kargs:
        {\n
        "desc":[]                   # Key description list\n
        "desc_content" = ""         # The Key description
        "old_data":[]               # Old config\n
        "new_data":[]               # New config\n
        "key": "open"               # The args need to change\n
        "conf":{...}                # The config data\n
        "v":{...}                   # The fill in args\n
        }\n
        :return:
        """
        # 兼容ua_key，更新
        if key == "ua_key" and key not in conf:
            conf["ua_key"] = ""
        if conf[key] != v[key]:
            self.msg_push_cache['desc'].append(desc_content)
            self.msg_push_cache['old_data'].append(conf[key])
            self.msg_push_cache['new_data'].append(v[key])
            conf[key] = v[key]


        # return {"conf":kargs['conf'],"desc":kargs['desc'],"old_data":kargs['old_data'],"new_data":kargs['new_data']}
        # key = kargs['key']
        # if kargs['conf'][key] != kargs['v'][key]:
        #     kargs['desc'].append(kargs['desc_content'])
        #     kargs['old_data'].append(kargs['conf'][key])
        #     kargs['new_data'].append(kargs['v'][key])
        #     kargs['conf'][key] = kargs['v'][key]
        # return {"conf":kargs['conf'],"desc":kargs['desc'],"old_data":kargs['old_data'],"new_data":kargs['new_data']}

    def modify_msgpush(self,get):
        data = self.get_msgpush_list(get)
        v = self.check_args(get)
        if not v['status']:
            return v
        v = v['msg']
        self.msg_push_cache['desc'] = []
        self.msg_push_cache['old_data'] = []
        self.msg_push_cache['new_data'] = []
        alter_options = ""
        for conf in data:
            if conf['push_name'] != v['push_name']:
                continue
            if 'open' in v:
                self.get_change_logs(desc_content="开关",conf=conf,v=v,key='open')
            if 'report' in v:
                self.get_change_logs(desc_content="报告",conf=conf,v=v,key='report')
            if 'ssl_check_time' in v:
                self.get_change_logs(desc_content="SSL开启检查时间",conf=conf,v=v,key='ssl_check_time')
            if 'report_type' in v:
                self.get_change_logs(desc_content="报告类型",conf=conf,v=v,key='report_type')
            if 'push_time' in v:
                self.get_change_logs(desc_content="推送时间",conf=conf,v=v,key='push_time')
            if 'alarm_value' in v:
                self.get_change_logs(desc_content="告警阈值",conf=conf,v=v,key='alarm_value')
            if 'check_time' in v:
                self.get_change_logs(desc_content="检查时间",conf=conf,v=v,key='check_time')
            if 'net_bandwidth' in v:
                self.get_change_logs(desc_content="带宽",conf=conf,v=v,key='net_bandwidth')
            if 'netcard' in v:
                self.get_change_logs(desc_content="网卡",conf=conf,v=v,key='netcard')
            if 'site_check_url' in v:
                self.get_change_logs(desc_content="URL",conf=conf,v=v,key='site_check_url')
            if 'site_check_word' in v:
                self.get_change_logs(desc_content="关键词",conf=conf,v=v,key='site_check_word')
            if 'url_list' in v:
                self.get_change_logs(desc_content="URL列表",conf=conf,v=v,key='url_list')
            if 'key' in v:
                self.get_change_logs(desc_content="关键词",conf=conf,v=v,key='key')
            if 'adv' in v:
                self.get_change_logs(desc_content="高级开关", conf=conf, v=v, key='adv')
            if 'site_name' in v:
                self.get_change_logs(desc_content="网站名",conf=conf,v=v,key='site_name')
            if 'services' in v:
                self.get_change_logs(desc_content="服务名",conf=conf,v=v,key='services')
            if 'act' in v:
                self.get_change_logs(desc_content="自动重启", conf=conf,v=v,key='act')
            if 'ua_key' in v:
                self.get_change_logs(desc_content="自定义UA", conf=conf, v=v, key='ua_key')
            # return str(self.msg_push_cache['new_data'])
            if len(self.msg_push_cache['new_data']) > 1:
                tmp = "{},{}".format(','.join(self.msg_push_cache['new_data'][0]),','.join(self.msg_push_cache['new_data'][1]))
            elif len(self.msg_push_cache['new_data']) > 0:
                tmp1 = self.msg_push_cache['new_data'][0] if isinstance(self.msg_push_cache['new_data'][0],list) else self.msg_push_cache['new_data']
                tmp = ','.join(tmp1)
            else:
                tmp = None
            if tmp is not None:
                alter_options += '推送名称 "{}" 的 【{}】 修改为 【{}】\n'.format(conf['push_name'], ','.join(self.msg_push_cache['desc']), tmp)
        if bool(alter_options):
            public.WriteLog('消息推送', ' 修改配置,' + alter_options)
        public.writeFile("{}/config.json".format(self.plugin_path), json.dumps(data))
        return public.returnMsg(True,"修改成功")


    # 修改事件监控阈值
    def modify_msgpush_old(self,get):
        data = self.get_msgpush_list(get)
        push_name = get.push_name
        get_data = get.__dict__
        keys = {"push_type":"推送类型",
                "cpu_alarm_value":"CPU阈值",
                "cpu_check_time":"CPU检查周期",
                "mem_alarm_value":"内存阈值",
                "mem_check_time":"内存检查周期",
                "net_alarm_value":"带宽预警阈值",
                "net_check_time":"带宽监测时间",
                "net_bandwidth":"最大带宽",
                "site_check_url":"检查URL",
                "site_check_word":"检查关键字",
                "disk_alarm_value":"监控磁盘阈值",
                "url_list":"监控域名",
                "adv":"精确站点监控",
                "key":"监控站点关键字",
                "site_name":"监控站点",
                "push_time":"推送间隔时间",
                "report":"报表发送时间",
                "report_type":"报表类型",
                "netcard":"网卡",
                "open":"检测开关"}
        alter_options = ""
        try:
            push_time = get.push_time
        except:
            get.push_time = 10
        if int(get.push_time) < 10:
            return public.returnMsg(False, '邮件发送间隔时间不能小于10分钟')
        for i in data:
            if push_name == i["push_name"]:
                if not "push_time" in i.keys():
                    i["push_time"] = "10"
                for k in keys.keys():
                    try:
                        if get_data[k]:
                            if "value" in k:
                                try:
                                    a = int(get_data[k])
                                    if a <= 0 or a > 100:
                                        return public.returnMsg(False, '阈值不能小于等于0或大于100')
                                except:
                                    return public.returnMsg(False, '请输入整数')
                            if "time" in k:
                                try:
                                    a = int(get_data[k])
                                    if a <= 0:
                                        return public.returnMsg(False, '不能输入负数或0')
                                except:
                                    return public.returnMsg(False, '请输入整数')
                            if str(i[k]) != get_data[k]:
                                ldata = ""
                                udata = ""
                                if "value" in k:
                                    ldata += i[k] + "%"
                                    udata += get_data[k] + "%"
                                elif "time" in k:
                                    ldata += i[k] + "分钟"
                                    udata += get_data[k] + "分钟"
                                elif "open" in k or "adv" in k:
                                    if get_data[k] == "1":
                                        udata += "开启"
                                        ldata += "关闭"
                                    else:
                                        udata += "关闭"
                                        ldata += "开启"
                                elif "bandwidth" in k:
                                    udata += get_data[k] + "Mbps"
                                    ldata += i[k] + "Mbps"
                                elif "url" in k:
                                    udata += get_data[k]
                                    ldata += i[k]
                                else:
                                    udata += get_data[k]
                                    ldata += i[k]
                                alter_options += '推送名称 "%s" 的%s "%s" 修改为 "%s"' % (push_name, keys[k], ldata, udata)
                                i[k] = get_data[k]
                    except:
                        pass
                if alter_options:
                    public.WriteLog('消息推送', ' 修改配置[' + alter_options + ']')
        for i in data:
            try:
                if i["url_list"]:
                    site = {
                        "url_list":i["url_list"],
                        "key":i["key"],
                        "adv":i["adv"],
                        "site_name":i["site_name"]
                    }
                    i.pop("url_list")
                    i.pop("key")
                    i.pop("adv")
                    i.pop("site_name")
                    i["site"] = site
            except:
                pass

        self.__write_config("{}/config.json".format(self.plugin_path), data)
        return public.returnMsg(True, '修改成功')

    #删除推送事件
    def remove_msgpush(self,get):
        data = self.__read_config("{}/config.json".format(self.plugin_path))
        push_name = get.push_name
        for i in range(len(data)):
            if data[i]["push_name"] == push_name:
                del data[i]
                self.__write_config("{}/config.json".format(self.plugin_path), data)
                public.WriteLog('消息推送', ' 删除配置[' + push_name + ']')
                return public.returnMsg(True, '删除成功')

    # 第一次打开提醒设置邮件
    def CheckMailFirst(self, get):
        if not public.readFile("{}/firstcheck.json".format(self.plugin_path)):
            public.writeFile("{}/firstcheck.json".format(self.plugin_path),"1")
        a = public.readFile("{}/firstcheck.json".format(self.plugin_path))
        e = self.get_email_list(get)["emails"]
        if a == "1" and not e:
            b = a + "1"
            public.writeFile("{}/firstcheck.json".format(self.plugin_path),b)
            return a
        else:
            return 0

    # 获取邮箱列表
    def get_email_list(self, get):
        emails = public.readFile("{}/mail_list.json".format(self.plugin_path))
        if not emails:
            public.writeFile("{}/mail_list.json".format(self.plugin_path), '[]')
            emails = []
        else:
            emails = json.loads(emails)
        return {'emails':emails}

    # 添加邮箱地址
    def add_email(self, get):
        emails = self.get_email_list(get)['emails']
        if len(emails) > 2: return public.returnMsg(False, '最多添加3个收件地址!')
        if get.email in emails: return public.returnMsg(False, '指定收件地址已存在!')
        # rep = "^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$"
        rep = "\w[-\w.+]*@([A-Za-z0-9][-A-Za-z0-9]+\.)+[A-Za-z]{2,14}"
        if not re.search(rep,get.email):
            return public.returnMsg(False, '请输入正确的邮箱格式')
        emails.append(get.email)
        public.WriteLog('消息推送', '添加收件地址[' + get.email + ']')
        self.__write_config("{}/mail_list.json".format(self.plugin_path),emails)
        return public.returnMsg(True, '添加成功')

    # 删除邮箱地址
    def remove_email(self, get):
        emails = self.get_email_list(get)['emails']
        emails.remove(get.email)
        public.WriteLog('消息推送', '删除收件地址[' + get.email + ']')
        self.__write_config("{}/mail_list.json".format(self.plugin_path),emails)
        return public.returnMsg(True, '删除成功')


    # 读配置
    def __read_config(self, path):
        if not os.path.exists(path) or not public.readFile(path):
                public.writeFile(path, '[]')
        upBody = public.readFile(path)
        return json.loads(upBody)

    # 写配置
    def __write_config(self ,path, data):
        return public.writeFile(path, json.dumps(data))

    # 外部读配置
    def read_config(self):
        return self.__read_config("{}/config.json".format(self.plugin_path))

    # 发送邮件
    def __send_mail(self, url, data):
        return public.httpPost(url, data)

    # 检查监控是否开启
    def check_monitor(self):
        monitor_file = 'data/control.conf'
        if os.path.exists(monitor_file):
            return True

    # URL回调
    def callback_url(self):
        # 构造post请求
        pass
    # 获取日志
    def get_logs(self, get):
        import page
        page = page.Page()
        count = public.M('logs').where('type=?', (u'消息推送',)).count()
        limit = 12
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
        data['page'] = page.GetPage(info, '1,2,3,4,5,8')
        data['data'] = public.M('logs').where('type=?', (u'消息推送',)).order('id desc').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).field('log,addtime').select()
        return data

    def CheckPort(self,ip,port):
        import socket
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sk.settimeout(5)
        try:
            sk.connect((ip, int(port)))
            return True
        except:
            return False

    def __get_file_json(self, filename, defaultv={}):
        try:
            if not os.path.exists(filename): return defaultv;
            return json.loads(public.readFile(filename))
        except:
            os.remove(filename)
            return defaultv

    # 获取站点名称
    def get_all_name_of_sites(self):
        sites = []
        getsites = public.M('sites').field('name').select()
        for s in getsites:
            sites.append(s["name"])
        return sites

    def GetTime(self,time):
        year = datetime.datetime.now().year
        month = datetime.datetime.now().month
        hour = datetime.datetime.now().hour
        day = datetime.datetime.now().day
        lastHour = hour - 1
        yesterday = day - 1
        lastMonth = month - 1
        times = {"year": year, "month": month, "day": day, "hour": hour,"lastHour":lastHour,"yesterday":yesterday,"lastMonth":lastMonth}
        for i in times:
            if times[i] < 10:
                times[i] = "0"+str(times[i])
            else:
                times[i] = str(times[i])
        return times[time]

    # 获取24小时时间戳
    def GetTimeStamp(self):
        tsl = []
        for i in range(24):
            d = datetime.datetime.now().strftime("%Y-%m-%d") + " %2d:00:00" % i
            timelist = time.strptime(d, "%Y-%m-%d %H:%M:%S")
            tsl.append(int(time.mktime(timelist)))
        return tsl

    def is_domain(self,domain):
        reg = "^([\w\-\*]{1,100}\.){1,10}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$"
        if re.match(reg, domain): return True
        return False

    def push_argv(self,msg):
        if public.is_ipv4(msg):
            tmp1 = msg.split('.')
            msg = '{}.***.***.{}'.format(tmp1[0], tmp1[3])
        else:
            if self.is_domain(msg):
                msg = msg.replace('.', '_')
        return msg

    def send_sms(self,even):
        print("开始发送短信！！！")
        sms = sms_msg()
        data = dict()
        if even['status'] == "error":
            if even["resource_type"] == "CPU":
                data["sm_type"] = "cpu_err"
                data['sm_args'] = {
                    "name": self.push_argv(self.GetLocalIp()),
                    "usage": even['usage'],
                    "process": even['process'],
                    "usage_process": even['usage_process']
                }
            elif even["resource_type"] == "磁盘":
                data["sm_type"] = "disk_err"
                data['sm_args'] = {
                    "name": self.push_argv(self.GetLocalIp()),
                    "usage": even['usage'],
                    "partition": even['partition'],
                    "inode_usage": even['inode_usage']
                }
            elif even["resource_type"] == "内存":
                data["sm_type"] = "mem_err"
                data['sm_args'] = {
                    "name": self.push_argv(self.GetLocalIp()),
                    "usage": even['usage'],
                    "process": even['process'],
                    "usage_process": even['usage_process']
                }
            # elif even["resource_type"] == "带宽":
            #     data["sm_type"] = "net_err"
            #     data['sm_args'] = {
            #         "name": self.push_argv(self.GetLocalIp()),
            #         "tx": even['tx'],
            #         "rx": even['rx']
            #     }
            elif even["resource_type"] == "URL检测":
                data["sm_type"] = "url_err"
                data['sm_args'] = {
                    "name": self.push_argv(self.GetLocalIp()),
                    "resource_type": even['site_url'].replace("https://","").replace("http://","").replace(".","_") #将网站的域名. 改为 _
                }
            elif even["type"] == "service":
                data["sm_type"] = "service_err"
                data['sm_args'] = {
                    "name": self.push_argv(self.GetLocalIp()),
                    "service": even['service'],
                    "restart_success": even['restart_success']
                }
            else:
                data["sm_type"] = "site_err"
                data['sm_args'] = {
                    "name": self.push_argv(self.GetLocalIp()),
                    "usage": even['resource_type'].replace("https://","").replace("http://","").replace(".","_") #将网站的域名. 改为 _
                }
        else:
            data["sm_type"] = "back_to_normal"
            data['sm_args'] = {
                "name": self.push_argv(self.GetLocalIp()),
                "resource": even['resource_type'].replace(".", "_")  # 将网站的域名. 改为 _
            }
        send_result = sms.push_data(data)
        print(data)
        print(send_result)
        return send_result

    # 发送邮件
    # def SendMsg(self,email_data,content,push_type,even):
    def SendMsg(self,email_data,content,even):
        """
        发送消息通知
        @filename 文件名
        @s_body 欲写入的内容
        return bool 若文件不存在则尝试自动创建
        """
        msg_channel = self.get_channel_settings()
        print("开始发送消息")
        if even['push_type'] == 'msg_mail' and msg_channel['msg_mail']['msg_mail'] and msg_channel['msg_mail']['info']['status']:
            send_type = '消息通道【邮件】'
            print("开始使用 {} 发送".format(send_type))
            send_result = self.send_by_mail(content,even)
        elif even['push_type'] == 'dingding' and msg_channel['dingding']['dingding'] and msg_channel['dingding']['info']['status']:
            send_type = '消息通道【钉钉】'
            print("开始使用 {} 发送".format(send_type))
            send_result = self.send_by_dingding(content,even)
        elif even['push_type'] == 'telegram':
            send_type = '消息通道【Telegram】'
            print("开始使用 {} 发送".format(send_type))
            import telegram_bot
            tg = telegram_bot.telegram_bot()
            send_result = tg.send_by_tg_bot(content)
        elif even['push_type'] == 'sms':
            send_type = '短信'
            print("开始使用 {} 发送".format(send_type))
            send_result = self.send_sms(even)
        else:
            try:
                email_data["body"] = content
                email_data = base64.b64encode(json.dumps(email_data))
            except:
                email_data = base64.b64encode(json.dumps(email_data).encode()).decode()
            data = {"access_key": self.GetAccessKey(), "data": email_data,
                    "token": self.SetToken(email_data)}
            send_result = self.__send_mail(self.warningUrl, data)
            send_type = '堡塔API'
            print(send_result)
        if not send_result:
            public.WriteLog('消息推送', "使用[ {} ]发送消息[ {} ]失败:{}".format(send_type,even['resource_type'],send_result))
            # time.sleep(60)
        else:
            print("开始成功！")
            public.WriteLog('消息推送', "告警消息发送成功")
            # time.sleep(60)
            return True


    def GetLocalIp(self):
        # 取本地外网IP
        try:
            filename = '{}/data/iplist.txt'.format(self.panel_path)
            ipaddress = public.readFile(filename).strip()
            if not ipaddress:
                import urllib2
                url = 'http://pv.sohu.com/cityjson?ie=utf-8'
                opener = urllib2.urlopen(url)
                m_str = opener.read()
                ipaddress = re.search('\d+.\d+.\d+.\d+', m_str).group(0)
                public.WriteFile(filename, ipaddress)
            c_ip = public.check_ip(ipaddress)
            if not c_ip:
                a, e = public.ExecShell("curl ifconfig.me")
                return a
            return ipaddress
        except:
            # return public.get_error_info()
            try:
                url = public.GetConfigValue('home') + '/Api/getIpAddress';
                return public.HttpGet(url)
            except:
                return public.GetHost()

    def get_specify_conf(self,value):
        conf = self.__read_config("{}/config.json".format(self.plugin_path))
        if not conf:
            return {}
        try:
            for i in conf:
                if i['check_type'] == value and i['open'] == "1":
                    return i
                # for k in i:
                #     if value == k and i[value] and i['open'] == "1":
                #         return i

        except:
            return {}

    def GetNetCard(self,get):
        import psutil
        a = psutil.net_io_counters(pernic=True)
        l = []
        for i in a.keys():
            if i != "lo":
                l.append(i)
        return l

    def SetToken(self,email_data):
        ufile = "{}/data/userInfo.json".format(self.panel_path)
        uconf = public.readFile(ufile)
        if uconf:
            uconf = json.loads(uconf)
            sk = uconf["secret_key"]
        else:
            return False
        token = public.Md5(sk+email_data)
        return token

    def GetAccessKey(self):
        ufile = "{}/data/userInfo.json".format(self.panel_path)
        uconf = public.readFile(ufile)
        if uconf:
            uconf = json.loads(uconf)
            ak = uconf["access_key"]
        else:
            return False
        return ak

    def get_channel_settings(self,get=None):
        mail_info = json.loads(public.ReadFile(self.__mail_config))
        if len(mail_info) == 0:
            user_mail = False
        else:
            user_mail = True
        dingding_info = json.loads(public.ReadFile(self.__dingding_config))
        if len(dingding_info) == 0:
            dingding = False
        else:
            dingding = True
        ret = {}
        ret['msg_mail'] = {"msg_mail": user_mail, "mail_list": "{}/mail_list.json".format(self.plugin_path),"info":self.get_user_mail()}
        ret['dingding'] = {"dingding": dingding, "info": self.get_dingding()}
        return ret

    # 查看钉钉
    def get_dingding(self):
        qq_mail_info = json.loads(public.ReadFile(self.__dingding_config))
        if len(qq_mail_info) == 0:
            return public.returnMsg(False, '无信息')
        return public.returnMsg(True, qq_mail_info)

    # 查看自定义邮箱配置
    def get_user_mail(self):
        mail_info = json.loads(public.ReadFile(self.__mail_config))
        if len(mail_info) == 0:
            return public.returnMsg(False, '无信息')
        if not 'port' in mail_info:mail_info['port']=465
        return public.returnMsg(True, mail_info)

    def send_by_mail(self,content,even):
        return public.send_mail(title=even['title'],body=content,is_type=even['title'])

    def send_by_dingding(self,content,even):
        return public.send_dingding(content,is_type=even['title'])

    def load_module(self,module):
        # 加载需要的模块
        sys.path.insert(0,self.plugin_path+"/module/")
        module = __import__('{}'.format(module))
        return eval('module.check')

    def get_all_module(self):
        module_path = os.listdir("{}/module".format(self.plugin_path))
        module_obj = {}
        for m in module_path:
            if len(m) < 4: #a.py 最少长度4
                continue
            if m[-3:] != '.py':
                continue
            m = m[:-3]
            module_obj[m] = self.load_module(m)
        return module_obj

    def make_mail_format(self,data):
        file = "{}/msg_template/mail/{}/{}".format(self.plugin_path,data['status'],data['type'])
        template = public.readFile(file)

        if data['type'] == 'resource':
            content = template.format(title=data['title'],
                            ip=self.GetLocalIp(),
                            resource_type=data['resource_type'],
                            status='异常' if data['status'] == 'error' else "正常",
                            msg=data['msg'])
        # elif data['type'] == 'resource' and data['status'] == 'success':
        #     content = template.format(title=data['title'],
        #                     ip=self.GetLocalIp(),
        #                     resource_type=data['resource_type'],
        #                     status='异常' if data['status'] == 'error' else "正常")
        elif data['type'] == 'service' and data['status'] == 'error':
            content = template.format(title=data['title'],
                            ip=self.GetLocalIp(),
                            service=data['service'],
                            status='异常' if data['status'] == 'error' else "正常",
                            restart=data['restart'],
                            restart_success=data['restart_success'],
                            restart_fail=data['restart_fail'])
        elif data['type'] == 'service' and data['status'] == 'success':
            content = template.format(title=data['title'],
                            ip=self.GetLocalIp(),
                            service=data['service'],
                            status='异常' if data['status'] == 'error' else "正常",
                            msg = data["msg"])
        return content

    def make_dingding_format(self,data):
        file = "{}/msg_template/dingding/{}/{}".format(self.plugin_path,data['status'],data['type'])
        template = public.readFile(file)

        if data['type'] == 'resource':
            content = template.format(title=data['title'],
                            ip=self.GetLocalIp(),
                            resource_type=data['resource_type'],
                            status='异常' if data['status'] == 'error' else "正常",
                            msg=data['msg'])
        elif data['type'] == 'service' and data['status'] == 'error':
            content = template.format(title=data['title'],
                            ip=self.GetLocalIp(),
                            service=data['service'],
                            status='异常' if data['status'] == 'error' else "正常",
                            restart=data['restart'],
                            restart_success=data['restart_success'],
                            restart_fail=data['restart_fail'])
        elif data['type'] == 'service' and data['status'] == 'success':
            content = template.format(title=data['title'],
                            ip=self.GetLocalIp(),
                            service=data['service'],
                            status='异常' if data['status'] == 'error' else "正常",
                            msg = data["msg"])
        return content

    def make_telegram_format(self,data):
        file = "{}/msg_template/telegram/{}/{}".format(self.plugin_path,data['status'],data['type'])
        template = public.readFile(file)
        ip = self.GetLocalIp().replace('.','\.')
        character = ['.',',','!',':','%','[',']','\/','_','-']
        for d in data:
            for c in character:
                try:
                    data[d] = data[d].replace(c,'\\'+c)
                except:
                    data[d] = str(data[d])
                    data[d] = data[d].replace(c, '\\' + c)
        if data['type'] == 'resource':
            content = template.format(title=data['title'],
                            ip=ip,
                            resource_type=data['resource_type'],
                            status='异常' if data['status'] == 'error' else "正常",
                            msg=data['msg'])
        elif data['type'] == 'service' and data['status'] == 'error':
            content = template.format(title=data['title'],
                            ip=ip,
                            service=data['service'],
                            status='异常' if data['status'] == 'error' else "正常",
                            restart=data['restart'],
                            restart_success=data['restart_success'],
                            restart_fail=data['restart_fail'])
        elif data['type'] == 'service' and data['status'] == 'success':
            content = template.format(title=data['title'],
                            ip=ip,
                            service=data['service'],
                            status='异常' if data['status'] == 'error' else "正常",
                            msg = data["msg"])
        return content

    def push(self,email_data,msgs):
        "email_data 用于宝塔API发送"
        if not msgs:
            return
        try:
            msgs = json.loads(msgs)
            while msgs:
                msg = msgs.pop()
                if msg['push_type'] == "msg_mail":
                    content = self.make_mail_format(msg)
                elif msg['push_type'] == "dingding":
                    content = self.make_dingding_format(msg)
                elif msg['push_type'] == 'telegram':
                    content = self.make_telegram_format(msg)
                else:
                    content = self.make_mail_format(msg)
                self.SendMsg(email_data,content,msg)
                time.sleep(5)

            public.writeFile(self.msg_file,json.dumps(msgs))
        except:
            print(public.get_error_info(),str(msgs))

    def get_service_list(self,get):
        service_list = json.loads(public.readFile("{}/service.conf".format(self.plugin_path)))
        return service_list

    def init_tg_bot(self):
        sys.path.insert(0, self.plugin_path + "/")
        # 初始化机器人
        import tg_bot
        tg = tg_bot.tg_bot()
        tg.start_program()

    def check_main(self):
        import threading
        if not self.check_monitor():
            return public.returnMsg(False, '请先打开[面板监控]，开启方法菜单-->监控-->开启监控')

        t = threading.Thread(target=self.init_tg_bot)
        t.setDaemon(True)
        t.start()
        # 情况发送队列
        public.writeFile(self.msg_file,json.dumps(list()))
        while True:
            try:
                print('开始')
                check_list = self.get_all_module()
                mail_list = self.get_email_list(None)["emails"] #获取需要发送的邮箱列表
                mail_list = ",".join(mail_list) #格式化邮箱列表
                email_data = {"email": mail_list}
                push = self.push
                msgs = public.readFile(self.msg_file)
                if msgs:
                    t = threading.Thread(target=push,args=(email_data,msgs))
                    t.start()
                    time.sleep(10)
                for i in check_list:
                    t = threading.Thread(target=check_list[i],args=(email_data,self.msg_push_cache))
                    t.start()
                time.sleep(10)
            except:
                time.sleep(10)
                public.writeFile("{}/error.log".format(self.plugin_path),str(public.get_error_info()),'w+')


class sms_msg:
    panelPath = "/www/server/panel"
    _APIURL = 'http://www.bt.cn/api/wmsg'
    __UPATH = panelPath + '/data/userInfo.json'
    conf_path = panelPath + '/data/sms_main.json'

    # 构造方法
    def __init__(self):
        self.setupPath = public.GetConfigValue('setup_path')
        pdata = {}
        data = {}
        if os.path.exists(self.__UPATH):
            try:
                self.__userInfo = json.loads(public.readFile(self.__UPATH))

                if self.__userInfo:
                    pdata['access_key'] = self.__userInfo['access_key']
                    data['secret_key'] = self.__userInfo['secret_key']
            except:
                self.__userInfo = None
        else:
            pdata['access_key'] = 'test'
            data['secret_key'] = '123456'

        pdata['data'] = data
        self.__PDATA = pdata

    def get_version_info(self, get):
        """
        获取版本信息
        """
        data = {}
        data['ps'] = '宝塔短信消息通道，用于接收面板消息推送'
        data['version'] = '1.0'
        data['date'] = '2021-05-14'
        data['author'] = '宝塔'
        data['help'] = 'http://www.bt.cn'
        return data

    def get_config(self, get):
        result = self.request('get_user_sms')
        data = {}
        try:
            data = json.loads(public.readFile(self.conf_path))
        except:
            pass

        for key in data.keys():
            result[key] = data[key]
        return result

    def is_strong_password(self, password):
        """判断密码复杂度是否安全
        非弱口令标准：长度大于等于9，分别包含数字、小写。
        @return: True/False
        @author: linxiao<2020-9-19>
        """
        if len(password) < 6: return False

        import re
        digit_reg = "[0-9]"  # 匹配数字 +1
        lower_case_letters_reg = "[a-z]"  # 匹配小写字母 +1
        special_characters_reg = r"((?=[\x21-\x7e]+)[^A-Za-z0-9])"  # 匹配特殊字符 +1

        regs = [digit_reg, lower_case_letters_reg, special_characters_reg]
        grade = 0
        for reg in regs:
            if re.search(reg, password):
                grade += 1

        if grade >= 2 or (grade == 1 and len(password) >= 9):
            return True
        return False

    def __check_auth_path(self):

        auth = public.readFile('data/admin_path.pl')
        if not auth: return False

        slist = ['/', '/123456', '/admin123', '/111111', '/bt', '/login', '/cloudtencent', '/tencentcloud', '/admin',
                 '/admin888', '/test']
        if auth in slist: return False

        if not self.is_strong_password(auth.strip('/')):
            return False
        return True

    def set_config(self, get):

        data = {}
        try:
            data = json.loads(public.readFile(self.conf_path))
        except:
            pass

        if 'login' in get:
            is_login = int(get['login'])
            if is_login and not self.__check_auth_path(): return public.returnMsg(False,
                                                                                  '安全入口过于简单，存在安全隐患. <br>1、长度不得少于9位<br>2、英文+数字组合.')
            data['login'] = is_login

        public.writeFile(self.conf_path, json.dumps(data))
        return public.returnMsg(True, '操作成功!')

    """
    @发送短信
    @sm_type 预警类型
    @sm_args 预警参数
    """

    def send_msg(self, sm_type=None, sm_args=None):
        self.__PDATA['data']['sm_type'] = sm_type
        self.__PDATA['data']['sm_args'] = sm_args
        result = self.request('send_msg')

        return result

    def push_data(self, data):
        return self.send_msg(data['sm_type'], data['sm_args'])

    # 发送请求
    def request(self, dname):

        pdata = {}
        pdata['access_key'] = self.__PDATA['access_key']
        pdata['data'] = json.dumps(self.__PDATA['data'])
        try:
            result = public.httpPost(self._APIURL + '/' + dname, pdata)
            result = json.loads(result)
            return result
        except:
            return public.returnMsg(False, public.get_error_info())

# class msg_push_cache:
#     pass

# if __name__ == '__main__':
#     msg_push = msg_push_main()
#     msg_push.check_main()
    # msg_push.get_all_module()
