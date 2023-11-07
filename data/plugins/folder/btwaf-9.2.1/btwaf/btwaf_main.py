# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# | Author: 梁凯强 <1249648969@qq.com>
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   宝塔网站防火墙
# +--------------------------------------------------------------------
import sys, base64, binascii

sys.path.append('/www/server/panel/class')
import json, os, time, public, string, re, hashlib

os.chdir('/www/server/panel')
if __name__ != '__main__':
    from panelAuth import panelAuth
import totle_db
import totle_db2
# import db2
import time, datetime


class mobj:
    siteName = ''


class LuaMaker(set):
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
                        if type(k) not in [int, float, bool, list, dict, tuple]:
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
                        if type(v) not in [int, float, bool, list, dict, tuple]:
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
                return "{\n" + lineJoin.join(cell) + "\n" + _indent + "}"
            else:
                pass

        return analysisTable(table, "", "root")


class btwaf_main:
    __to_lua_table = LuaMaker()
    __path = '/www/server/btwaf/'
    __state = {True: '开启', False: '关闭', 0: '停用', 1: '启用'}
    __config = None
    __webshell = '/www/server/btwaf/webshell.json'
    __wubao = '/www/server/panel/plugin/btwaf/wubao.json'
    __rule_path = ["args.json", "cookie.json", "post.json", "url_white.json", "url.json", "user_agent.json"]
    __isFirewalld = False
    __isUfw = False
    __Obj = None
    __webshell_data = []
    __session_name = None
    __PATH = '/www/server/panel/plugin/btwaf/'
    Recycle_bin = __PATH + 'Recycle/'

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

        #判断/www/server/btwaf/totla_db/totla_db.db 的权限是否是root
        if os.path.exists('/www/server/btwaf/totla_db/totla_db.db'):
            #获取文件的用户权限
            user = os.stat('/www/server/btwaf/totla_db/totla_db.db').st_uid
            if user=="0" or user==0:
                public.ExecShell("chown www:www /www/server/btwaf/totla_db/totla_db.db")
        if not os.path.exists(self.Recycle_bin):
            os.makedirs(self.Recycle_bin)
        if not os.path.exists('/www/wwwlogs/btwaf'):
            os.system("mkdir /www/wwwlogs/btwaf -p && chmod 777 /www/wwwlogs/btwaf")
        if os.path.exists('/usr/sbin/firewalld'): self.__isFirewalld = True
        if os.path.exists('/usr/sbin/ufw'): self.__isUfw = True
        if not self.__session_name:
            self.__session_name = self.__get_md5('btwa1f_sesssion_time' + time.strftime('%Y-%m-%d'))
        if not os.path.exists(self.__webshell):
            os.system("echo '[]'>/www/server/btwaf/webshell.json && chown www:www /www/server/btwaf/webshell.json")
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'send_settings')).count():
            public.M('').execute('''CREATE TABLE "send_settings" (
                    "id" INTEGER PRIMARY KEY AUTOINCREMENT,"name" TEXT,"type" TEXT,"path" TEXT,"send_type" TEXT,"last_time" TEXT ,"time_frame" TEXT,"inser_time" TEXT DEFAULT'');''')
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'send_msg')).count():
            public.M('').execute(
                '''CREATE TABLE "send_msg" ("id" INTEGER PRIMARY KEY AUTOINCREMENT,"name" TEXT,"send_type" TEXT,"msg" TEXT,"is_send" TEXT,"type" TEXT,"inser_time" TEXT DEFAULT '');''')

    def to_str(self, bytes_or_str):
        try:
            if isinstance(bytes_or_str, bytes):
                value = bytes_or_str.decode('utf-8')
            else:
                value = bytes_or_str
            return value
        except:
            return str(bytes_or_str)

    def index(self, args):
        if 'export' in args:

            return self.export_info(args)
        if self.is_check_version():
            from BTPanel import render_template_string, g
            str_templste = public.ReadFile('{}/templates/index.html'.format(self.__PATH))
            try:
                g.btwaf_version = json.loads(public.ReadFile('{}/info.json'.format(self.__PATH)))['versions']
            except:
                g.btwaf_version = '8.8.5'
            return render_template_string(str_templste, data={})
        else:
            from BTPanel import render_template_string, g
            str_templste = public.ReadFile('{}/templates/error4.html'.format(self.__PATH))
            try:
                g.btwaf_version = json.loads(public.ReadFile('{}/info.json'.format(self.__PATH)))['versions']
            except:
                g.btwaf_version = '8.8.5'
            return render_template_string(str_templste, data={})

    def index2(self, args):
        if self.is_check_version():
            from BTPanel import render_template_string, g
            str_templste = public.ReadFile('{}/templates/index.html'.format(self.__PATH))
            try:
                g.btwaf_version = json.loads(public.ReadFile('{}/info.json'.format(self.__PATH)))['versions']
            except:
                g.btwaf_version = '8.8.5'
            return render_template_string(str_templste, data={})
        else:
            from BTPanel import render_template_string, g
            str_templste = public.ReadFile('{}/templates/error4.html'.format(self.__PATH))
            try:
                g.btwaf_version = json.loads(public.ReadFile('{}/info.json'.format(self.__PATH)))['versions']
            except:
                g.btwaf_version = '8.8.5'
            return render_template_string(str_templste, data={})

    def M3(self, table):
        with totle_db.Sql() as sql:
            return sql.table(table)

    def M2(self, table):
        with totle_db2.Sql() as sql:
            return sql.table(table)

    # def M3(self,table):
    #     with db2.Sql() as sql:
    #         return sql.table(table)

    def is_check_time(self, tie, count_time, is_time, type_chekc):
        if type_chekc == '>':
            if 'is_status' in tie:
                if tie['is_status'] == False:
                    return False
            if int(tie['time'] + count_time) > int(is_time):
                return True
            else:
                return False
        if type_chekc == '<':
            if 'is_status' in tie:
                if tie['is_status'] == False: return False
            if int(tie['time'] + count_time) < int(is_time):
                return True
            else:
                return False
        else:
            return False

    def get_blocking_ip_logs(self, get):
        return self.M2('blocking_ip').field(
            'time,time_localtime,server_name,ip,blocking_time,is_status').where(
            "time>=?", int(time.time()) - 86400).order('id desc').select()

    def test222(self, get):
        self.M2('blocking_ip').field(
            'time,time_localtime,server_name,ip,blocking_time,is_status').order('id desc').select()

    def get_total_all_overview(self, get):
        result = {}
        # 封锁IP24小时内封锁   正在封锁的数量
        result['day24_lan'] = {}
        ### 拦截状态
        result['day24_lan']['is_count_ip'] = 0
        result['day24_lan']['info'] = []
        result['day24_lan']['day_count'] = 0

        result['map'] = {}
        result['map']['info'] = {}
        result['map']['24_day_count'] = 0
        result['map']['1_day_count'] = 0
        result['map']['top10_ip'] = {}
        result['map']['24_day_count'] = 0

        if not 'start_time' in get:
            start_time = time.strftime("%Y-%m-%d", time.localtime(time.time()))
        else:
            start_time = get.start_time.strip()
        if not 'end_time' in get:
            # end_time = time.strftime("%Y-%m-%d", time.localtime(time.time()))
            end_time = start_time
        else:
            end_time = get.end_time.strip()
        start_time = start_time + ' 00:00:00'
        end_time2 = end_time + ' 23:59:59'
        start_timeStamp = int(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S')))
        end_timeStamp = int(time.mktime(time.strptime(end_time2, '%Y-%m-%d %H:%M:%S')))

        if os.path.exists("/www/server/btwaf/totla_db/totla_db.db"):
            day_24_data = self.M2('blocking_ip').field(
                'time,time_localtime,server_name,ip,ip_country,ip_country,ip_city,ip_subdivisions,blocking_time,is_status').where(
                "time>=? and time<=?", (start_timeStamp,end_timeStamp)).order('id desc').limit("10000").select()

            is_time = time.time()
            if type(day_24_data) == str: return result
            result['day24_lan']['day_count'] = len(day_24_data)
            if len(day_24_data) == 0:
                day_24_data = self.M2('blocking_ip').field(
                    'time,time_localtime,server_name,ip,ip_country,ip_country,ip_city,ip_subdivisions,blocking_time,is_status').limit("30").order('id desc').select()
                for i in day_24_data:
                    if not i['is_status']: continue
                    check = self.is_check_time(i, i['blocking_time'], is_time, '>')
                    i['is_status'] = check
                    if check: result['day24_lan']['is_count_ip'] += 1
            else:
                for i in day_24_data:
                    if not i['is_status']: continue
                    check = self.is_check_time(i, i['blocking_time'], is_time, '>')
                    i['is_status'] = check
                    if check: result['day24_lan']['is_count_ip'] += 1
            if len(day_24_data) > 100:
                day_24_data = day_24_data[0:100]
            result['day24_lan']['info'] = day_24_data
        #
        ##攻击地图+ top10 攻击IP
        result['map'] = {}
        result['map']['info'] = {}
        result['map']['24_day_count'] = 0
        result['map']['1_day_count'] = 0
        result['map']['top10_ip'] = {}
        result['map']['24_day_count'] = 0
        if os.path.exists("/www/server/btwaf/totla_db/totla_db.db"):
            map_24_data = self.M2('totla_log').field('time,ip,ip_country,ip_city,ip_subdivisions').where(
                "time>=? and time<=?", (start_timeStamp,end_timeStamp)).order(
                'id desc').limit("10000").select()

            # 获取今天的时间搓
            start_time = time.strftime("%Y-%m-%d", time.localtime(time.time()))
            start_time2 = start_time + ' 00:00:00'
            end_time2 = start_time + ' 23:59:59'
            start_timeStamp = int(time.mktime(time.strptime(start_time2, '%Y-%m-%d %H:%M:%S')))
            end_timeStamp = int(time.mktime(time.strptime(end_time2, '%Y-%m-%d %H:%M:%S')))
            result['map']['24_day_count'] = len(
                self.M2('totla_log').field('time').where("time>=? and time<?",(start_timeStamp,end_timeStamp)).order(
                    'id desc').limit("10000").select())
            is_time = time.time()
            for i in map_24_data:
                check = self.is_check_time(i, 3600, is_time, '>')
                if check: result['map']['1_day_count'] += 1
                if i['ip'] in result['map']['top10_ip']:
                    result['map']['top10_ip'][i['ip']] = result['map']['top10_ip'][i['ip']] + 1
                else:
                    result['map']['top10_ip'][i['ip']] = 1
                if i['ip_country'] == None: continue
                if i['ip_country'] in result['map']['info']:
                    result['map']['info'][i['ip_country']] = result['map']['info'][i['ip_country']] + 1
                else:
                    result['map']['info'][i['ip_country']] = 1
            if len(result['map']['info']):
                try:
                    result['map']['info'] = (sorted(result['map']['info'].items(), key=lambda kv: (kv[1], kv[0])))[::-1]

                except:
                    pass
            top10_ip = (sorted(result['map']['top10_ip'].items(), key=lambda kv: (kv[1], kv[0])))

            if len(top10_ip) > 30:
                result['map']['top10_ip'] = top10_ip[::-1][:30]
            else:
                result['map']['top10_ip'] = top10_ip[::-1]
            result_top_10=[]
            for i in result['map']['top10_ip']:
                i2=list(i)
                ret=self.M2('totla_log').field('ip_country').where("ip=?", i[0]).getField("ip_country")
                i2.append(ret)
                ret = self.M2('totla_log').field('ip_country').where("ip=?", i[0]).getField("ip_subdivisions")
                i2.append(ret)
                ret = self.M2('totla_log').field('ip_country').where("ip=?", i[0]).getField("ip_city")
                i2.append(ret)
                result_top_10.append(i2)
            result['map']['top10_ip']=result_top_10
                # result
        return result

    def gongji_check(self, tongji):
        for i in range(len(tongji['gongji'])):
            if i == len(tongji['gongji']) - 1:
                del tongji['gongji'][i]
                continue
            tongji['gongji'][i][1] = tongji['gongji'][i + 1][1]
        return tongji

    # 验证Ip是否被封锁
    def is_feng(self, data):
        drop_iplist = self.get_waf_drop_ip(None)
        if 'data' in data:
            for i in data['data']:
                if not i['is_status']:
                    i['is_feng'] = False
                else:
                    if int(i['time'] + i['blocking_time']) > int(time.time()):
                        check = self.is_check_time(i, i['blocking_time'], time.time(), '>')
                        i['is_feng'] = True if i['ip'] in drop_iplist or check else False
                    else:
                        i['is_feng'] = False

    def get_safe_logs_sql(self, get):
        result = {}
        result['page']="<div><span class='Pcurrent'>1</span><span class='Pcount'>共0条</span></div>"
        result['data']=[]
        if 'limit' in get:
            limit = int(get.limit.strip())
        else:
            limit = 12

        if os.path.exists("/www/server/btwaf/totla_db/totla_db.db"):
            try:
                if self.M2('blocking_ip').order('id desc').count() == 0: return public.returnMsg(True, result)
            except:
                return public.returnMsg(True, result)
            try:
                data = self.M2('blocking_ip').order('id desc').count()
            except:
                return public.returnMsg(True, result)
            import page
            page = page.Page()
            count = self.M2('blocking_ip').order('id desc').count()
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

            data222 = self.M3('blocking_ip').field(
                'time,time_localtime,server_name,ip,ip_city,ip_country,ip_subdivisions,ip_longitude,ip_latitude,type,uri,user_agent,filter_rule,incoming_value,value_risk,http_log,http_log_path,blockade,blocking_time,is_status').order(
                'id desc').limit(str(page.SHIFT) + ',' + str(page.ROW)).select()
            data['data'] = self.bytpes_to_string(data222)
            self.is_feng(data)
            return public.returnMsg(True, data)
        return public.returnMsg(True, result)

    def get_all_tu(self, get):

        result = {}
        time_xianzai = int(time.time())
        # 攻击趋势图
        result['gongji'] = []
        result['server_name_top5'] = {}
        result['dongtai'] = {}
        if not 'start_time' in get:
            start_time = time.strftime("%Y-%m-%d", time.localtime(time.time()))
        else:
            start_time = get.start_time.strip()
        if not 'end_time' in get:
            # end_time = time.strftime("%Y-%m-%d", time.localtime(time.time()))
            end_time = start_time
        else:
            end_time = get.end_time.strip()
        start_time = start_time + ' 00:00:00'
        end_time2 = end_time + ' 23:59:59'
        start_timeStamp = int(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S')))
        end_timeStamp = int(time.mktime(time.strptime(end_time2, '%Y-%m-%d %H:%M:%S')))

        if os.path.exists("/www/server/btwaf/totla_db/totla_db.db"):

            for i in range(0, 8):
                day = end_timeStamp - (i * 86400)
                day2 = end_timeStamp - ((i - 1) * 86400)
                jintian = self.M2('totla_log').field('time').where("time>? and time<?", (day, day2)).order(
                    'id desc').limit("10000").count()
                result['gongji'].append([self.dtchg(day), jintian])
            self.gongji_check(result)
            map_24_data = self.M2('totla_log').field('time,server_name').order(
                'id desc').where(
                "time>=? and time<=?", (start_timeStamp,end_timeStamp)).limit("10000").select()
            if type(map_24_data) == str: return result

            if len(map_24_data) >= 1:
                for i in map_24_data:
                    if i['server_name'] in result['server_name_top5']:
                        result['server_name_top5'][i['server_name']] = result['server_name_top5'][i['server_name']] + 1
                    else:
                        result['server_name_top5'][i['server_name']] = 1

            if len(result['server_name_top5']) >= 1:
                server_top5 = (sorted(result['server_name_top5'].items(), key=lambda kv: (kv[1], kv[0])))[::-1]
                if len(server_top5) > 5:
                    result['server_name_top5'] = server_top5[:5]
                else:
                    result['server_name_top5'] = server_top5
            dongtai = self.M2('totla_log').field('id,time,time_localtime,server_name,ip,ip_country,ip_subdivisions,ip_longitude,ip_latitude,type,filter_rule').where(
                "time>=?", int(time.time()) - 86400).order('id desc').limit("20").select()
            if len(dongtai) == 0:
                dongtai = self.M2('totla_log').field('id,time,time_localtime,server_name,ip,ip_country,ip_subdivisions,ip_longitude,ip_latitude,type,filter_rule').order(
                    'id desc').limit("20").select()
            if dongtai:
                result['dongtai'] = dongtai

        return result

    def remove_waf_drop_ip_data(self, get):
        pass

    '''设置表插入数据'''

    def insert_settings(self, name, type, path, send_type, time_frame=180):
        inser_time = self.dtchg(int(time.time()))
        last_time = int(time.time())
        if public.M('send_settings').where('name=?', (name,)).count(): return False
        data = {"name": name, "type": type, "path": path, "send_type": send_type, "time_frame": time_frame,
                "inser_time": inser_time, "last_time": last_time}
        return public.M('send_settings').insert(data)

    def dtchg(self, x):
        try:
            time_local = time.localtime(float(x))
            dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
            return dt
        except:
            return False

    # 返回站点
    def return_site(self, get):
        data = public.M('sites').field('name,path').select()
        ret = {}
        for i in data:
            ret[i['name']] = i['path']
        return public.returnMsg(True, ret)

    # 获取规则
    def shell_get_rule(self, get):
        ret = []
        if os.path.exists(self.__PATH + 'rule.json'):
            try:
                data = json.loads(public.ReadFile(self.__PATH + 'rule.json'))
                return data
            except:
                return False
        else:
            return False

    # 查询站点跟目录
    def getdir(self, dir, pc='', lis=[]):
        try:
            list = os.listdir(dir)
            for l in list:
                if os.path.isdir(dir + '/' + l):
                    lis = self.getdir(dir + '/' + l, pc, lis)
                elif str(l.lower())[-4:] == '.php' and str(dir + '/' + l).find(pc) == -1:
                    print(dir + '/' + l)
                    lis.append(dir + '/' + l)
            return lis
        except:
            return lis

    # 目录
    def getdir_list(self, get):
        path = get.path
        if os.path.exists(path):
            pc = 'hackcnm'
            rs = self.getdir(path, pc)
            return rs
        else:
            return False

    # 扫描
    def scan(self, path, filelist, rule):
        import time
        time_data = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        ret = []
        path_list = self.path_json(path)
        for file in filelist:
            try:
                data = open(file).read()
                for r in rule:
                    if re.compile(r).findall(data):
                        if file in path_list: continue
                        result = {}
                        result[file] = r
                        if result not in ret:
                            ret.append(result)
                        # ret.append(result)
                        data = ("%s [!] %s %s  \n" % (time_data, file, r))
                        self.insert_log(data)
            except:
                pass
        return ret

    def insert_log(self, data):
        public.writeFile(self.__PATH + 'webshell.log', data, 'a+')

    # Log 取100行操作
    def get_log(self, get):
        path = self.__PATH + 'webshell.log'
        if not os.path.exists(path): return False
        return public.GetNumLines(path, 3000)

    # 不是木马的过滤掉
    def path_json(self, path):
        path_file = str(path).replace('/', '')
        if os.path.exists(path):
            if os.path.exists(self.__PATH + path_file + '.json'):
                try:
                    path_data = json.loads(public.ReadFile(self.__PATH + path_file + '.json'))
                    return path_data
                except:
                    ret = []
                    public.WriteFile(self.__PATH + path_file + '.json', json.dumps(ret))
                    return []
            else:
                ret = []
                public.WriteFile(self.__PATH + path_file + '.json', json.dumps(ret))
                return []
        else:
            return []

    def san_dir(self, get):
        result2222 = []
        file = self.getdir_list(get)
        if not file: return public.returnMsg(False, "当前目录中没有php文件")
        rule = self.shell_get_rule(get)
        if not rule: return public.returnMsg(False, "规则为空或者规则文件错误")
        ret = self.scan(get.path, file, rule)
        return ret

    #  xss 防御
    def xssencode(self, text):
        import html
        list = ['`', '~', '&', '<', '>']
        ret = []
        for i in text:
            if i in list:
                i = ''
            ret.append(i)
        str_convert = ''.join(ret)
        text2 = html.escape(str_convert, quote=True)
        return text2

    # 添加规则
    def shell_add_rule(self, get):
        rule = self.xssencode(get.rule)
        ret = []
        if os.path.exists(self.__PATH + 'rule.json'):
            try:
                data = json.loads(public.ReadFile(self.__PATH + 'rule.json'))
                if rule in data:
                    return public.returnMsg(False, '已经存在此规则')
                else:
                    data.append(rule)
                    public.WriteFile(self.__PATH + 'rule.json', json.dumps(data))
                    return public.returnMsg(True, '添加成功')
            except:
                return public.returnMsg(False, '规则库解析错误')
        else:
            return public.returnMsg(False, '规则库文件不存在')

    # 删除规则库
    def shell_del_rule(self, get):
        rule = get.rule
        if os.path.exists(self.__PATH + 'rule.json'):
            try:
                data = json.loads(public.ReadFile(self.__PATH + 'rule.json'))
                if rule in data:
                    data.remove(rule)
                    public.WriteFile(self.__PATH + 'rule.json', json.dumps(data))
                    return public.returnMsg(True, '删除成功')
                else:
                    return public.returnMsg(False, '规则库不存在此规则')
            except:
                return public.returnMsg(False, '规则库解析错误')
        else:
            return public.returnMsg(False, '规则库文件不存在')

    # 标记不是木马
    def lock_not_webshell(self, get):
        path = get.path
        not_path = get.not_path
        if not os.path.exists(not_path): return public.returnMsg(False, '文件不存在')
        path_file = str(path).replace('/', '')
        if not os.path.exists(self.__PATH + path_file + '.json'):
            ret = []
            ret.append(not_path)
            public.WriteFile(self.__PATH + path_file + '.json', json.dumps(ret))
        else:
            try:
                path_data = json.loads(public.ReadFile(self.__PATH + path_file + '.json'))
                if not not_path in path_data:
                    path_data.append(not_path)
                    public.WriteFile(self.__PATH + path_file + '.json', json.dumps(path_data))
                    return public.returnMsg(True, '添加成功')
                else:
                    return public.returnMsg(False, '已经存在')
            except:
                ret = []
                ret.append(not_path)
                public.WriteFile(self.__PATH + path_file + '.json', json.dumps(ret))
                return public.returnMsg(True, '11111111')

    '''
    @name 上传到云端判断是否是webshell
    @param filename 文件路径
    @param url 云端URL
    @return bool 
    '''

    def webshellchop(self, filename, url):
        try:
            import requests
            upload_url = url
            size = os.path.getsize(filename)
            if size > 1024000: return public.returnMsg(True, '未查出风险,需等待一段时间后查询')
            try:
                self.__user = json.loads(public.ReadFile('/www/server/panel/data/userInfo.json'))
            except:
                self.__user = []
                pass
            if len(self.__user) == 0: return public.returnMsg(True, '未查出风险,需等待一段时间后查询')
            upload_data = {'inputfile': public.ReadFile(filename), "md5": self.read_file_md5(filename),
                           "path": filename, "access_key": self.__user['access_key'], "uid": self.__user['uid'],
                           "username": self.__user["username"]}
            upload_res = requests.post(upload_url, upload_data, timeout=20).json()
            if upload_res['msg'] == 'ok':
                if (upload_res['data']['data']['level'] == 5):
                    shell_insert = {'filename': filename, "hash": upload_res['data']['data']['hash']}
                    self.send_baota2(filename)
                    return public.returnMsg(True, '此文件为webshell')
                elif upload_res['data']['level'] >= 3:
                    self.send_baota2(filename)
                    return public.returnMsg(True, '未查出风险,需等待一段时间后查询')
                return public.returnMsg(True, '未查出风险,需等待一段时间后查询')
        except:
            return public.returnMsg(True, '未查出风险,需等待一段时间后查询')

    def upload_file_url(self, get):
        return self.webshellchop(get.filename, "http://w-check.bt.cn/check.php")

    # webshell 流量查杀
    def get_webshell(self, get):
        try:
            data = json.loads(public.ReadFile(self.__webshell))
            return public.returnMsg(True, data)
        except:
            os.system("echo '[]'>/www/server/btwaf/webshell.json && chown www:www /www/server/btwaf/webshell.json")
            return public.returnMsg(True, [])

    # 打开二进制文件并计算md5
    def read_file_md5(self, filename):
        if os.path.exists(filename):
            with open(filename, 'rb') as fp:
                data = fp.read()
            file_md5 = hashlib.md5(data).hexdigest()
            return file_md5
        else:
            return False

    def send_baota2(self, filename):
        cloudUrl = 'http://www.bt.cn/api/panel/btwaf_submit'
        pdata = {'codetxt': public.ReadFile(filename), 'md5': self.read_file_md5(filename), 'type': '0',
                 'host_ip': public.GetLocalIp(), 'size': os.path.getsize(filename)}
        ret = public.httpPost(cloudUrl, pdata)
        return True

    # get_url
    def get_check_url(self, filename):
        try:
            import requests
            ret = requests.get('http://www.bt.cn/checkWebShell.php').json()
            if ret['status']:
                upload_url = ret['url']
                size = os.path.getsize(filename)
                if size > 1024000: return False
                upload_data = {'inputfile': public.ReadFile(filename)}
                upload_res = requests.post(upload_url, upload_data, timeout=20).json()
                if upload_res['msg'] == 'ok':
                    if (upload_res['data']['data']['level'] == 5):
                        self.send_baota2(filename)
                        return public.returnMsg(False, '当前文件为webshell')
                    elif upload_res['data']['level'] >= 3:
                        self.send_baota2(filename)
                        return public.returnMsg(False, '可疑文件,建议手工检查')
                    return public.returnMsg(True, '无风险')
            return public.returnMsg(True, '无风险')
        except:
            return public.returnMsg(True, '无风险')

    # 上传云端
    def send_baota(self, get):
        '''
        filename  文件
        '''
        try:
            if os.path.exists(get.filename):
                return self.get_check_url(get.filename)
            else:
                return public.returnMsg(True, '无风险')
        except:
            return public.returnMsg(True, '无风险')

    # 检测是否是木马
    def check_webshell(self, get):
        if 'filename' not in get: return public.returnMsg(False, '请选择你需要上传的文件')
        if not os.path.exists(get.filename): return public.returnMsg(False, '文件不存在')
        cloudUrl = 'http://www.bt.cn/api/panel/btwaf_check_file'
        pdata = {'md5': self.read_file_md5(get.filename), 'size': os.path.getsize(get.filename)}
        ret = public.httpPost(cloudUrl, pdata)
        if ret == '0':
            return public.returnMsg(True, '未查出风险,需等待一段时间后查询')
        elif ret == '1':
            return public.returnMsg(True, '该文件经过系统检测为webshell！！！！')
        elif ret == '-1':
            return public.returnMsg(True, '未查询到该文件,请上传检测')
        else:
            return public.returnMsg(False, '系统错误')

    # 删除列表中的一条数据
    def del_webshell_list(self, get):
        if 'path' not in get: return public.returnMsg(False, '请填写你需要删除的路径')
        if not os.path.exists(self.__wubao):

            public.WriteFile(self.__wubao, json.dumps([get.path.strip()]))
            list_data = json.loads(public.ReadFile(self.__webshell))
            if get.path in list_data:
                list_data.remove(get.path)
                public.writeFile(self.__webshell, json.dumps(list_data))
                return public.returnMsg(True, '添加成功')
            else:
                return public.returnMsg(False, '添加失败')
        else:
            try:
                result = json.loads(public.ReadFile(self.__wubao))
                if not get.path.strip() in result:
                    result.append(get.path.strip())
                    public.WriteFile(self.__wubao, json.dumps(result))
                list_data = json.loads(public.ReadFile(self.__webshell))
                if get.path in list_data:
                    list_data.remove(get.path)
                    public.writeFile(self.__webshell, json.dumps(list_data))
                    return public.returnMsg(True, '添加成功')
                else:
                    return public.returnMsg(False, '添加失败')
            except:
                public.WriteFile(self.__wubao, json.dumps([get.path.strip()]))
                list_data = json.loads(public.ReadFile(self.__webshell))
                if get.path in list_data:
                    list_data.remove(get.path)
                    public.writeFile(self.__webshell, json.dumps(list_data))
                    return public.returnMsg(True, '添加成功')
                else:
                    return public.returnMsg(False, '添加失败')

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
        url_find = get.ua_white
        config = self.get_config(None)
        url_find_list = config['ua_white']
        if url_find in url_find_list:
            return public.returnMsg(False, '已经存在')
        else:
            url_find_list.append(url_find)
            self.__write_config(config)
            return public.returnMsg(True, '添加成功')

    # 导入UA白名单
    def add_ua_list(self, get):
        if 'json' not in get:
            get.json = True
        else:
            get.json = False
        if get.json:
            pdata = json.loads(get.pdata)
        else:
            pdata = get.pdata.strip().split('\n')
        if not pdata: return public.returnMsg(False, '不能为空')
        for i in pdata:
            get.ua_white = i
            self.add_ua_white(get)
        return public.returnMsg(True, '导入成功')

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

    # 导入UA黑名单
    def add_black_list(self, get):
        if 'json' not in get:
            get.json = True
        else:
            get.json = False
        if get.json:
            pdata = json.loads(get.pdata)
        else:
            pdata = get.pdata.strip().split('\n')
        if not pdata: return public.returnMsg(False, '不能为空')
        for i in pdata:
            get.ua_black = i
            self.add_ua_black(get)
        return public.returnMsg(True, '导入成功')

    # 添加UA 黑名单ua_black
    def add_ua_black(self, get):
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

    # 导入URL拦截
    def add_url_list(self, get):
        if 'json' not in get:
            get.json = True
        else:
            get.json = False
        if get.json:
            pdata = json.loads(get.pdata)
        else:
            pdata = get.pdata.strip().split()
        if not pdata: return public.returnMsg(False, '不能为空')
        for i in pdata:
            get.url_find = i
            self.add_url_find(get)
        return public.returnMsg(True, '导入成功')

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

    def check_herader2(self, data, method_type):
        for i in data:
            if method_type == i[0]:
                return True
        return False

    # 删除请求类型
    def add_method_type(self, get):
        config = self.get_config(None)
        check = get.check.strip()
        if not check in ['0', '1']: return public.returnMsg(False, '类型错误')
        if int(check) == 0:
            check = False
        else:
            check = True
        url_find_list = config['method_type']
        if not self.check_herader2(url_find_list, get.method_type.strip()):
            return public.returnMsg(False, '不存在')
        else:
            for i in url_find_list:
                if get.method_type.strip() == i[0]:
                    i[1] = check
            self.__write_config(config)
            return public.returnMsg(True, '修改成功')

    # 删除请求类型
    def del_header_len(self, get):
        header_type = get.header_type.strip()
        header_len = get.header_type_len.strip()
        config = self.get_config(None)
        url_find_list = config['header_len']
        if not self.check_herader(url_find_list, header_type):
            return public.returnMsg(False, '不存在')
        else:
            url_find_list.remove([header_type, header_len])
            self.__write_config(config)
            return public.returnMsg(True, '删除成功')

    # 修改
    def edit_header_len(self, get):
        header_type = get.header_type.strip()
        header_len = get.header_type_len.strip()
        config = self.get_config(None)
        url_find_list = config['header_len']
        if self.check_herader(url_find_list, header_type):
            for i in url_find_list:
                if header_type == i[0]:
                    i[1] = header_len
            self.__write_config(config)
            return public.returnMsg(True, '修改成功')
        else:
            return public.returnMsg(False, '不存在')

    def check_herader(self, data, header):
        for i in data:
            if header == i[0]:
                return True
        return False

    # 添加
    def add_header_len(self, get):
        header_type = get.header_type.strip()
        header_len = get.header_type_len.strip()
        config = self.get_config(None)
        url_find_list = config['header_len']
        if self.check_herader(url_find_list, header_type):
            return public.returnMsg(False, '已经存在')
        else:
            url_find_list.append([header_type, header_len])
            self.__write_config(config)
            return public.returnMsg(True, '添加成功')

    # 查看URL_FIND
    def get_url_white_chekc(self, get):
        config = self.get_config(None)
        url_find_list = config['url_white_chekc']
        return public.returnMsg(True, url_find_list)

    # 添加URL FIND
    def add_url_white_chekc(self, get):
        url_find = get.url_find
        config = self.get_config(None)
        url_find_list = config['url_white_chekc']
        if url_find in url_find_list:
            return public.returnMsg(False, '已经存在')
        else:
            url_find_list.append(url_find)
            self.__write_config(config)
            return public.returnMsg(True, '添加成功')

    # 添加URL FIND
    def del_url_white_chekc(self, get):
        url_find = get.url_find
        config = self.get_config(None)
        url_find_list = config['url_white_chekc']
        if url_find in url_find_list:
            url_find_list.remove(url_find)
            self.__write_config(config)
            return public.returnMsg(True, '删除成功')
        else:
            return public.returnMsg(False, '不存在')

    def get_cc_status(self, get):
        config = self.get_config(None)
        if config['cc_automatic']:
            return public.returnMsg(True, '')
        else:
            return public.returnMsg(False, '')

    def stop_cc_status(self, get):
        # config = self.get_config(None)
        # config['cc_automatic'] = False
        # self.__write_config(config)
        # site_conf = self.get_site_config(None)
        # for i in site_conf:
        #     site_conf[i]['cc_automatic'] = False
        # self.__write_site_config(site_conf)
        # time.sleep(0.2)
        return public.returnMsg(True, '关闭成功')

    def start_cc_status(self, get):
        # config = self.get_config(None)
        # config['cc_automatic'] = True
        # site_conf=self.get_site_config(None)
        # for i in site_conf:
        #     site_conf[i]['cc_automatic'] = True
        # self.__write_site_config(site_conf)
        # self.__write_config(config)
        # time.sleep(0.2)
        return public.returnMsg(True, '开启成功')

    def isDigit(self, x):
        try:
            x = int(x)
            return isinstance(x, int)
        except ValueError:
            return False

    def set_cc_automatic(self, get):
        cc_time = get.cc_time
        cc_retry_cycle = get.cc_retry_cycle
        config = self.get_config(None)
        if not self.isDigit(cc_time) and not self.isDigit(cc_retry_cycle): return public.returnMsg(False, '需要设置数字!')
        config['cc_time'] = int(cc_time)
        config['cc_retry_cycle'] = int(cc_retry_cycle)
        site_conf = self.get_site_config(None)
        for i in site_conf:
            site_conf[i]['cc_time'] = int(cc_time)
            site_conf[i]['cc_retry_cycle'] = int(cc_retry_cycle)
        self.__write_site_config(site_conf)
        self.__write_config(config)
        return public.returnMsg(True, '设置成功!')

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
                    # public.WriteFile(self.__path + 'rule/cc_uri_white.lua', self.__to_lua_table.makeLuaTable(data))
                    return public.returnMsg(True, '设置成功!')
            except:
                ret = []
                ret.append(self.xssencode((get.text.strip())))
                public.WriteFile(self.__path + 'rule/cc_uri_white.json', json.dumps(ret))
                # public.WriteFile(self.__path + 'rule/cc_uri_white.lua', self.__to_lua_table.makeLuaTable(ret))
                return public.returnMsg(True, '设置成功!')
        else:
            ret = []
            ret.append(self.xssencode((get.text.strip())))
            public.WriteFile(self.__path + 'rule/cc_uri_white.json', json.dumps(ret))
            # public.WriteFile(self.__path + 'rule/cc_uri_white.lua', self.__to_lua_table.makeLuaTable(ret))
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

    def site_golbls_cc(self, get):
        text = self.xssencode((get.text.strip()))
        data = self.get_site_config(get)
        for i in data:
            if get.siteName == i['siteName']:
                if 'cc_uri_white' not in i:
                    i['cc_uri_white'] = []
                    i['cc_uri_white'].append(text)

                else:
                    if text not in i['cc_uri_white']:
                        i['cc_uri_white'].append(text)
                        self.__write_site_config(data)
                        return public.returnMsg(True, '添加成功')
                    else:
                        return public.returnMsg(False, '已经存在!')
        return public.returnMsg(False, '未知错误!')

    def del_site_golbls_cc(self, get):
        text = self.xssencode((get.text.strip()))
        data = self.get_site_config(get)
        for i in data:
            if get.siteName == i['siteName']:
                if 'cc_uri_white' not in i:
                    i['cc_uri_white'] = []
                else:
                    if text not in i['cc_uri_white']:
                        return public.returnMsg(False, '不存在!')
                    else:
                        if text in i['cc_uri_white']:
                            i['cc_uri_white'].remove(text)
                            self.__write_site_config(data)
                            return public.returnMsg(True, '删除成功')
                        else:
                            return public.returnMsg(False, '不存在!')
        return public.returnMsg(False, '未知错误!')

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
        id = public.M('crontab').where('name=?', (u'Nginx防火墙四层拦截IP',)).getField('id')
        import crontab
        if id: crontab.crontab().DelCrontab({'id': id})
        data = {}
        data['name'] = 'Nginx防火墙四层拦截IP'
        data['type'] = 'hour-n'
        data['where1'] = '1'
        data['sBody'] = 'python /www/server/panel/plugin/btwaf/firewalls_list.py start'
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
        id = public.M('crontab').where('name=?', (u'Nginx防火墙四层拦截IP',)).getField('id')
        import crontab
        if id: crontab.crontab().DelCrontab({'id': id})
        return public.returnMsg(True, '关闭成功!')

    def get_stop_ip(self, get):
        id = public.M('crontab').where('name=?', (u'Nginx防火墙四层拦截IP',)).getField('id')
        if id:
            return public.returnMsg(True, '11')
        else:
            return public.returnMsg(False, '111')

    def get_site_config2(self):
        site_config = public.readFile(self.__path + 'site.json')
        try:
            data = json.loads(site_config)
        except:
            return False
        return data

    def add_body_site_rule(self, get):
        if not get.text.strip(): return public.returnMsg(False, '需要替换的数据不能为空')
        config = self.get_site_config2()
        if not config: public.returnMsg(False, '未知错误')
        config2 = config[get.siteName]
        if not 'body_character_string' in config2:
            config2['body_character_string'] = []
        if not get.text2.strip():
            ret = {get.text: ''}
        else:
            ret = {get.text: get.text2}
        body = config2['body_character_string']
        if len(body) == 0:
            config2['body_character_string'].append(ret)
            self.__write_site_config(config)
            return public.returnMsg(True, '添加成功重启Nginx生效')
        else:
            if body in config2['body_character_string']:
                return public.returnMsg(False, '已经存在')
            else:
                config2['body_character_string'].append(ret)
                self.__write_site_config(config)
                return public.returnMsg(True, '添加成功重启Nginx生效')

    def add_body_body_intercept(self, get):
        if not get.text.strip(): return public.returnMsg(False, '需要拦截数据不能为空')
        config = self.get_site_config2()
        if not config: public.returnMsg(False, '未知错误')
        config2 = config[get.siteName]
        if not 'body_intercept' in config2:
            config2['body_intercept'] = []
        if get.text.strip() in config2['body_intercept']:
            return public.returnMsg(False, '已经存在')
        else:
            config2['body_intercept'].append(get.text.strip())
            self.__write_site_config(config)
            return public.returnMsg(True, '添加成功')

    def del_body_body_intercept(self, get):
        if not get.text.strip(): return public.returnMsg(False, '需要拦截数据不能为空')
        config = self.get_site_config2()
        if not config: public.returnMsg(False, '未知错误')
        config2 = config[get.siteName]
        if not 'body_intercept' in config2:
            config2['body_intercept'] = []
        if get.text.strip() in config2['body_intercept']:
            config2['body_intercept'].pop(get.text.strip())
            self.__write_site_config(config)
            return public.returnMsg(True, '删除成功')
        else:
            return public.returnMsg(False, '不存在')

    def del_body_site_rule(self, get):
        body = json.loads(get.body)
        config = self.get_site_config2()
        if not config: public.returnMsg(False, '未知错误')
        config2 = config[get.siteName]
        if not 'body_character_string' in config2:
            config2['body_character_string'] = []
            self.__write_site_config(config)
            return public.returnMsg(False, '替换文件为空,请添加数据')
        else:
            data = config2['body_character_string']

            if body in data:
                ret = data.index(body)
                data.pop(ret)
                self.__write_site_config(config)
                return public.returnMsg(True, '删除成功,重启nginx生效')
            else:
                return public.returnMsg(False, '删除失败/不存在')

    #  xss 防御
    def xssencode(self, text):
        import html
        list = ['`', '~', '&', '#', '*', '$', '@', '<', '>', '\"', '\'', ';', '%', ',', '\\u']
        ret = []
        for i in text:
            if i in list:
                i = ''
            ret.append(i)
        str_convert = ''.join(ret)
        text2 = html.escape(str_convert, quote=True)
        return text2

    def del_body_rule(self, get):

        body = json.loads(get.body)

        config = self.get_config(get)
        if not 'body_character_string' in config:
            config['body_character_string'] = []
            self.__write_config(config)
            return public.returnMsg(False, '替换文件为空,请添加数据')
        else:
            data = config['body_character_string']
            if body in data:
                ret = data.index(body)
                data.pop(ret)
                self.__write_config(config)
                return public.returnMsg(True, '删除成功,重启nginx生效')
            else:
                return public.returnMsg(False, '删除失败/不存在')

    def add_body_rule(self, get):
        if not get.text.strip(): return public.returnMsg(False, '需要替换的数据不能为空')
        config = self.get_config(get)

        if not 'uri_find' in config:
            config['uri_find'] = []

        if not 'body_character_string' in config:
            config['body_character_string'] = []
        if not get.text2.strip():
            ret = {self.xssencode(get.text): ''}
        else:
            ret = {self.xssencode(get.text): self.xssencode(get.text2)}
        body = config['body_character_string']
        if len(body) == 0:
            config['body_character_string'].append(ret)
            self.__write_config(config)
            return public.returnMsg(True, '添加成功重启Nginx生效')
        else:
            if body in config['body_character_string']:
                return public.returnMsg(False, '已经存在')
            else:
                config['body_character_string'].append(ret)
                self.__write_config(config)
                return public.returnMsg(True, '添加成功重启Nginx生效')

    # 导入违禁词
    def import_body_intercept(self, get):
        if not get.text.strip(): return public.returnMsg(False, '需要拦截数据不能为空')
        data = get.text.strip().split()
        if len(data) == 0: return public.returnMsg(False, '需要拦截数据不能为空')
        config = self.get_config(get)
        if not 'body_intercept' in config:
            config['body_intercept'] = []
        if len(config['body_intercept']) == 0:
            config['body_intercept'] = data
            self.__write_config(config)
            return public.returnMsg(True, '导入成功')
        else:
            config['body_intercept'] = list(set(data) | set(config['body_intercept']))
            self.__write_config(config)
            return public.returnMsg(True, '导入成功')

    # 导出违禁词
    def export_body_intercept(self, get):
        config = self.get_config(get)
        if not 'body_intercept' in config:
            config['body_intercept'] = []
            return ''
        else:
            return '\n'.join(config['body_intercept'])

    # 清空
    def empty_body_intercept(self, get):
        config = self.get_config(get)
        config['body_intercept'] = []
        self.__write_config(config)
        return public.returnMsg(True, '清空成功')

    def add_body_intercept(self, get):
        if not get.text.strip(): return public.returnMsg(False, '你需要的拦截内容不能为空')
        config = self.get_config(get)
        if not 'body_intercept' in config:
            config['body_intercept'] = []
        if not 'body_intercept' in config:
            config['body_intercept'] = []
        if get.text.strip() in config['body_intercept']:
            return public.returnMsg(False, '拦截的内容已经存在')
        else:
            config['body_intercept'].append(get.text.strip())
            self.__write_config(config)
            return public.returnMsg(True, '添加成功')

    def del_body_intercept(self, get):
        if not get.text.strip(): return public.returnMsg(False, '你需要的拦截内容不能为空')
        config = self.get_config(get)
        if not 'body_intercept' in config:
            config['body_intercept'] = []
        if not 'body_intercept' in config:
            config['body_intercept'] = []
        if get.text.strip() in config['body_intercept']:
            config['body_intercept'].remove(get.text.strip())
            self.__write_config(config)
            return public.returnMsg(True, '删除成功')
        else:
            return public.returnMsg(False, '拦截的内容不存在')

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
        # from BTPanel import session
        # type = self.get_zhizu_list()
        # if not type: return False
        # if 'types' in type:
        #     if len(type['types']) >= 1:
        #         for i in type['types']:
        #             ret = public.httpGet('http://www.bt.cn/api/panel/get_spider?spider=%s' % str(i['id']))
        #             if not ret:
        #                 if not os.path.exists(self.__path + str(i['id']) + '.json'):
        #                     ret = []
        #                     public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(ret))
        #                 continue
        #             if os.path.exists(self.__path + str(i['id']) + '.json'):
        #                 local = public.ReadFile(self.__path + str(i['id']) + '.json')
        #                 if local:
        #                     try:
        #                         ret = json.loads(ret)
        #                         local = json.loads(local)
        #                         localhost_json = list(set(json.loads(local)).union(ret))
        #                         public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(localhost_json))
        #                         yum_list_json = list(set(local).difference(set(ret)))
        #                         public.httpGet(
        #                             'https://www.bt.cn/api/panel/add_spiders?address=%s' % json.dumps(yum_list_json))
        #                     except:
        #                         pass
        #                 else:
        #                     try:
        #                         ret = json.loads(ret)
        #                         public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(ret))
        #                     except:
        #                         ret = []
        #                         public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(ret))
        #             else:
        #                 try:
        #                     ret = json.loads(ret)
        #                     public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(ret))
        #                 except:
        #                     ret = []
        #                     public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(ret))
        # public.ExecShell('chown www:www /www/server/btwaf/*.json')
        # if not 'zhizu' in session: session['zhizu'] = 1
        return public.returnMsg(True, '更新蜘蛛成功!')

    # 获取蜘蛛池地址
    def get_zhizu_list22(self, get):
        # type = self.get_zhizu_list()
        # if not type: return public.returnMsg(False, '云端连接错误!')
        # if 'types' in type:
        #     if len(type['types']) >= 1:
        #         for i in type['types']:
        #             ret = public.httpGet('http://www.bt.cn/api/panel/get_spider?spider=%s' % str(i['id']))
        #             if not ret:
        #                 if not os.path.exists(self.__path + str(i['id']) + '.json'):
        #                     ret = []
        #                     public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(ret))
        #                 continue
        #
        #             if os.path.exists(self.__path + str(i['id']) + '.json'):
        #                 local = public.ReadFile(self.__path + str(i['id']) + '.json')
        #                 if local:
        #                     try:
        #                         ret = json.loads(ret)
        #                         local = json.loads(local)
        #                         localhost_json = list(set(json.loads(local)).union(ret))
        #                         public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(localhost_json))
        #                         yum_list_json = list(set(local).difference(set(ret)))
        #                         public.httpGet(
        #                             'https://www.bt.cn/api/panel/add_spiders?address=%s' % json.dumps(yum_list_json))
        #                     except:
        #                         pass
        #                 else:
        #                     try:
        #                         ret = json.loads(ret)
        #                         public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(ret))
        #                     except:
        #                         ret = []
        #                         public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(ret))
        #             else:
        #                 try:
        #                     ret = json.loads(ret)
        #                     public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(ret))
        #                 except:
        #                     ret = []
        #                     public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(ret))
        # public.ExecShell('chown www:www /www/server/btwaf/*.json')
        return public.returnMsg(True, '更新蜘蛛成功!')

    # 获取蜘蛛池地址
    def get_zhizu_list2233(self, get):
        self.test_check_zhilist(None)
        return public.returnMsg(True, '更新蜘蛛成功!')

    # 获取蜘蛛池地址
    def start_zhuzu(self):
        type = self.get_zhizu_list()
        if not type: return public.returnMsg(False, '云端连接错误!')
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
        return public.returnMsg(True, '更新蜘蛛成功!')

    # 外部蜘蛛池更新
    def get_zhizu_ip(self, get):
        type = self.get_zhizu_list()
        if not type: return False
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
                            yum_list_json = list(set(local).difference(set(ret)))
                            public.httpGet(
                                'https://www.bt.cn/api/panel/add_spiders?address=%s' % json.dumps(yum_list_json))
                        else:
                            public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(ret))
                    else:
                        public.WriteFile(self.__path + str(i['id']) + '.json', json.dumps(ret))

        return public.returnMsg(True, '更新蜘蛛成功!')

    def get_process_list(self):
        import psutil
        count = 0
        cpunum = int(public.ExecShell('cat /proc/cpuinfo |grep "processor"|wc -l')[0])
        Pids = psutil.pids();
        for pid in Pids:
            tmp = {}
            try:
                p = psutil.Process(pid);
            except:
                continue
            if str(p.name()) == 'php-fpm':
                count += int(p.cpu_percent(0.1))
        public.ExecShell("echo '%s' >/dev/shm/nginx.txt" % count / cpunum)
        return count / cpunum

    # 开启智能防御CC
    def Start_apache_cc(self, get):
        ret = self.auto_sync_apache()
        return ret

    # 查看状态
    def Get_apap_cc(self, get):
        id = public.M('crontab').where('name=?', (u'Nginx防火墙智能防御CC',)).getField('id');
        if id:
            return public.returnMsg(True, '开启!');
        else:
            return public.returnMsg(False, '关闭!');

    # 关闭智能防御CC
    def Stop_apache_cc(self, get):
        if os.path.exists('/dev/shm/nginx.txt'):
            os.remove('/dev/shm/nginx.txt')
        id = public.M('crontab').where('name=?', (u'Nginx防火墙智能防御CC',)).getField('id');
        import crontab
        if id: crontab.crontab().DelCrontab({'id': id})
        return public.returnMsg(True, '设置成功!');

    # 设置自动同步
    def auto_sync_apache(self):
        id = public.M('crontab').where('name=?', (u'Nginx防火墙智能防御CC',)).getField('id');
        import crontab
        if id: crontab.crontab().DelCrontab({'id': id})
        data = {}
        data['name'] = u'Nginx防火墙智能防御CC'
        data['type'] = 'minute-n'
        data['where1'] = '1'
        data['sBody'] = 'python /www/server/panel/plugin/btwaf/btwaf_main.py start'
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
    def retuen_nginx(self):
        import psutil
        count = 0
        cpunum = int(public.ExecShell('cat /proc/cpuinfo |grep "processor"|wc -l')[0])
        Pids = psutil.pids();
        for pid in Pids:
            tmp = {}
            try:
                p = psutil.Process(pid);
            except:
                continue
            if str(p.name()) == 'php-fpm':
                count += int(p.cpu_percent(0.1))

        public.ExecShell("echo '%s' >/dev/shm/nginx.txt" % str(count / cpunum))
        return count / cpunum

    def set_scan_conf(self, get):
        '''
        三个参数  通过404 的访问次数来拦截扫描器。最低不能低于60秒120次。
        open
        limit
        cycle
        '''
        config = self.get_config(None)
        if not 'limit' in get:
            if 'limit' in config['scan_conf']:
                get.limit = config['scan_conf']['limit']
            else:
                get.limit = 120
        if not 'cycle' in get:
            if 'cycle' in config['scan_conf']:
                get.cycle = config['scan_conf']['cycle']
            else:
                get.cycle = 60
        if not 'open' in get:
            if 'open' in config['scan_conf']:
                if config['scan_conf']['open']:
                    get.open = 0
                else:
                    get.open = 1
            else:
                get.open = 1
        if int(get.limit) < 20:
            return public.returnMsg(False, '次数不能小于20次')
        if int(get.cycle) < 20:
            return public.returnMsg(False, '周期不能小于20秒')
        if get.open == 1 or get.open == '1':
            open = True
        else:
            open = False
        # config = self.get_config(None)
        config['scan_conf'] = {"open": open, "limit": int(get.limit), "cycle": int(get.cycle)}
        self.__write_config(config)
        return public.returnMsg(True, '设置成功')

    def get_config(self, get):
        try:
            config = json.loads(public.readFile(self.__path + 'config.json'))
        except:
            config = {
                "scan": {
                    "status": 444,
                    "ps": "过滤常见扫描测试工具的渗透测试",
                    "open": True,
                    "reqfile": ""
                },
                "cc": {
                    "status": 444,
                    "ps": "过虑CC攻击",
                    "increase": False,
                    "limit": 120,
                    "endtime": 300,
                    "open": True,
                    "reqfile": "",
                    "cycle": 60
                },
                "logs_path": "/www/wwwlogs/btwaf",
                "open": True,
                "reqfile_path": "/www/server/btwaf/html",
                "retry": 10,
                "log": True,
                "cc_automatic": False,
                "user-agent": {
                    "status": 403,
                    "ps": "通常用于过滤浏览器、蜘蛛及一些自动扫描器",
                    "open": True,
                    "reqfile": "user_agent.html"
                },
                "other": {
                    "status": 403,
                    "ps": "其它非通用过滤",
                    "reqfile": "other.html"
                },
                "uri_find": [],
                "cc_retry_cycle": "600",
                "cc_time": "60",
                "ua_black": [],
                "drop_abroad": {
                    "status": 444,
                    "ps": "禁止中国大陆以外的地区访问站点",
                    "open": True,
                    "reqfile": ""
                },
                "drop_china": {
                    "status": 444,
                    "ps": "禁止大陆地区访问",
                    "open": False,
                    "reqfile": ""
                },
                "retry_cycle": 120,
                "get": {
                    "status": 403,
                    "ps": "过滤uri、uri参数中常见sql注入、xss等攻击",
                    "open": True,
                    "reqfile": "get.html"
                },
                "body_character_string": [],
                "body_intercept": [],
                "start_time": 0,
                "cookie": {
                    "status": 403,
                    "ps": "过滤利用Cookie发起的渗透攻击",
                    "open": True,
                    "reqfile": "cookie.html"
                },
                "retry_time": 1800,
                "post": {
                    "status": 403,
                    "ps": "过滤POST参数中常见sql注入、xss等攻击",
                    "open": True,
                    "reqfile": "post.html"
                },
                "ua_white": [],
                "body_regular": [],
                "log_save": 30,
                "sql_injection":{"status":403,"reqfile":"get.html","open":True,"post_sql":True,"get_sql":True,"mode":"high"},
                "xss_injection": {"status":403,"reqfile":"get.html","open": True, "post_xss": True, "get_xss": True, "mode": "high"},
                "file_upload": {"status":444,"reqfile":"get.html","open": True, "mode": "high","from-data":True},

            }
        config['drop_abroad_count']=0

        inf = public.cache_get("get_drop_abroad_count")
        if inf:
            config['drop_abroad_count']=inf
        count = 0
        try:
            site_config = json.loads(public.readFile(self.__path + 'site.json'))
        except:
            site_config=[]
            pass

        for i in site_config:
            if site_config[i]['drop_abroad']:
                count += 1
        public.cache_set("get_drop_abroad_count", count, 360)
        config['drop_abroad_count']=count


        is_flag = False
        if not 'sql_injection' in config:
            config['sql_injection'] = {"status":403,"reqfile":"get.html","open": True, "post_sql": True, "get_sql": True, "mode": "high"}
            is_flag = True
        if not 'xss_injection'in config:
            config['xss_injection']={"status":403,"reqfile":"get.html","open": True, "post_xss": True, "get_xss": True, "mode": "high"}
            is_flag = True
        if not 'file_upload' in config:
            config['file_upload']={"status":444,"reqfile":"get.html","open": True, "mode": "high","from-data":True}
            is_flag = True
        if not 'other_rule' in config:
            config['other_rule']={"status":444,"reqfile":"get.html","open": True, "mode": "high"}
            is_flag = True
        if not 'nday' in config:
            config['nday']=True
            is_flag = True
        # if not 'php_execution' in config:
        #     config['php_execution'] = {"status": 403, "reqfile": "get.html", "open": True, "mode": "high","get":True,"post":True}
        #     is_flag = True
        else:
            if 'from-data' not in config['file_upload']:
                config['file_upload'] = {"open": True, "mode": "high", "from-data": True}
                is_flag = True
        if not 'scan_conf' in config:
            config['scan_conf'] = {"open": True, "limit": 240, "cycle": 60}
        if not 'cc_type_status' in config:
            config['cc_type_status'] = 2
            is_flag = True
        if not 'body_intercept' in config:
            config['body_intercept'] = []
            is_flag = True
        if not 'cc_mode' in config:
            config['cc_mode'] = 1
            is_flag = True
        if not 'retry_cycle' in config:
            config['retry_cycle'] = 60
            is_flag = True
            self.__write_config(config)

        if config['cc'] and not 'countrys' in config['cc']:
            config['cc']['countrys'] = {}
            is_flag = True

        if not 'cc_uri_frequency' in config:
            # {"/index.php":{"frequency":10,"cycle":60}}
            config['cc_uri_frequency'] = {}

        if not 'uri_find' in config:
            config['uri_find'] = []
            is_flag = True
        if not 'increase_wu_heng' in config:
            config['increase_wu_heng'] = False
            is_flag = True
        if not 'ua_white' in config:
            config['ua_white'] = []
            is_flag = True
        if not 'ua_black' in config:
            config['ua_black'] = []
            is_flag = True
        if not 'body_character_string' in config:
            config['body_character_string'] = []
            is_flag = True
        if not 'body_regular' in config:
            config['body_regular'] = []
            is_flag = True

        if not 'get_is_sql' in config:
            config['get_is_sql'] = True
            is_flag = True
        if not 'get_is_xss' in config:
            config['get_is_xss'] = True
        if not 'post_is_sql' in config:
            config['post_is_sql'] = True
        if not 'post_is_xss' in config:
            config['post_is_xss'] = True
        if not 'post_is_xss_count' in config:
            config['post_is_xss_count'] = 1
        else:
            if config['post_is_xss_count'] == 6:
                if not os.path.exists("/www/server/panel/data/post_is_xss_count.pl"):
                    config['post_is_xss_count'] = 1
                    is_flag = True
                    public.WriteFile("/www/server/panel/data/post_is_xss_count.pl", "")

        if not 'url_cc_param' in config:
            config['url_cc_param'] = {}
        if not 'send_to' in config:
            config['send_to'] = 'ERROR'
        if not 'drop_china' in config:
            config['drop_china'] = {
                "status": 444,
                "ps": "禁止大陆地区访问",
                "open": False,
                "reqfile": ""
            }
            is_flag = True
        # method_type_check开关
        if not 'method_type' in config:
            config['method_type'] = [['POST', True], ['GET', True], ['PUT', True], ['OPTIONS', True], ['HEAD', True],
                                     ['DELETE', True], ['TRACE', True], ['PATCH', True], ['MOVE', True], ['COPY', True],
                                     ['LINK', True], ['UNLINK', True], ['WRAPPED', True], ['PROPFIND', True],
                                     ['PROPPATCH', True], ['MKCOL', True], ['CONNECT', True], ['SRARCH', True]]

        if not 'header_len' in config:
            config['header_len'] = [['host', 500], ['connection', 100], ['content-length', 100], ['cache-control', 100],
                                    ['upgrade-insecure-requests', 100], ['origin', 500], ['content-type', 300],
                                    ['user-agent', 500], ['accept', 500], ['referer', 10000], ['accept-encoding', 500],
                                    ['accept-language', 500], ['cookie', 10000]]

        for i in range(len(config['header_len'])):
            if config['header_len'][i][0] == 'referer':
                if config['header_len'][i][1] == 500 or config['header_len'][i][1] == 3000:
                    config['header_len'][i][1] = 10000
        if not 'from_data' in config:
            config['from_data'] = True
            is_flag = True

            # webshell开关
        if not 'webshell_opens' in config:
            config['webshell_opens'] = True
        if not config['webshell_opens'] and public.M('crontab').where('name=?', (u'Nginx防火墙木马查杀进程请勿删除',)).count()==0:
            id = public.M('crontab').where('name=?', (u'Nginx防火墙木马查杀进程请勿删除',)).getField('id')
            import crontab
            if id: crontab.crontab().DelCrontab({'id': id})


        if config['webshell_opens']:
            if get and  'open_btwaf_webshell' in get and get.open_btwaf_webshell:
                #判断这个是否是5分钟的计划任务。只执行一次
                if not os.path.exists("/www/server/panel/plugin/btwaf/webshell_opens.pl"):
                    if public.M('crontab').where('name=?', (u'Nginx防火墙木马查杀进程请勿删除',)).count()==1:
                        if public.M('crontab').where('name=?', (u'Nginx防火墙木马查杀进程请勿删除',)).getField("where1")=="5":
                            id = public.M('crontab').where('name=?', (u'Nginx防火墙木马查杀进程请勿删除',)).getField('id')
                            import crontab
                            if id: crontab.crontab().DelCrontab({'id': id})
                            public.WriteFile("/www/server/panel/plugin/btwaf/webshell_opens.pl", "True")
                self.webshell_check()

        if not 'http_open' in config:
            config['http_open'] = False
            is_flag = True
        # cc 自动开关
        if not 'cc_automatic' in config:
            config['cc_automatic'] = False
        if not 'is_browser' in config:
            config['is_browser'] = False
        if not 'url_white_chekc' in config:
            config['url_white_chekc'] = []
        if not 'cc_time' in config:
            config['cc_time'] = 60
        if not 'cc_retry_cycle' in config:
            config['cc_retry_cycle'] = 6000
        if config['start_time'] == 0:
            config['start_time'] = time.time()
            is_flag = True
        if not 'static_code_config' in config:
            config['static_code_config'] = {}
            is_flag = True
        if is_flag:
            self.__write_config(config)

        return config

    def find_site(self, data, site):
        for i in data:
            for i2 in i['domains']:
                if i2 == site:
                    return i
        return False

    def find_site_config(self, config, site):
        data = [{"name": "POST渗透", "key": "post", "value": 0}, {"name": "GET渗透", "key": "get", "value": 0},
                {"name": "CC攻击", "key": "cc", "value": 0}, {"name": "恶意User-Agent", "key": "user_agent", "value": 0},
                {"name": "Cookie渗透", "key": "cookie", "value": 0}, {"name": "恶意扫描", "key": "scan", "value": 0},
                {"name": "恶意HEAD请求", "key": "head", "value": 0}, {"name": "URI自定义拦截", "key": "url_rule", "value": 0},
                {"name": "URI保护", "key": "url_tell", "value": 0},
                {"name": "恶意文件上传", "key": "disable_upload_ext", "value": 0},
                {"name": "禁止的扩展名", "key": "disable_ext", "value": 0},
                {"name": "禁止PHP脚本", "key": "disable_php_path", "value": 0}]
        total_all = self.get_total(None)['sites']
        config['total'] = data if site in total_all else self.__format_total(total_all[site])
        config['siteName'] = site
        return config

    def find_websites(self, get):
        try:
            site_config = json.loads(public.readFile(self.__path + 'site.json'))
            site_name = get.siteName.strip()
            site_config2 = json.loads(public.readFile(self.__path + 'domains.json'))
            site = self.find_site(site_config2, site_name)
            if not site: return public.returnMsg(False, '未找到')
            if not site['name'] in site_config: return public.returnMsg(False, '未找到')
            return public.returnMsg(True, self.find_site_config(site_config[site['name']], site['name']))
        except:
            self.__write_site_domains()
            return public.returnMsg(False, '未找到')

    def get_site_config(self, get):
        try:
            site_config = json.loads(public.readFile(self.__path + 'site.json'))
        except:
            public.WriteFile(self.__path + 'site.json', json.dumps({}))
            self.__write_site_domains()
            site_config = json.loads(public.readFile(self.__path + 'site.json'))
        if not os.path.exists(self.__path + '/domains.lua'):
            self.__write_site_domains()
        data = self.__check_site(site_config)
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
        from BTPanel import session, cache
        if not self.__session_name in session:
            ret = self.get_btwaf()
            if ret == 0:
                self.stop()
                return public.returnMsg(False, '')
        site_config = self.get_site_config(None);
        config = site_config[get.siteName]
        config['top'] = self.get_config(None)
        return config

    def set_open(self, get):
        from BTPanel import session, cache
        if not self.__session_name in session:
            ret = self.get_btwaf()
            if ret == 0:
                self.stop()
                return public.returnMsg(False, '')

        config = self.get_config(None)
        if config['open']:
            config['open'] = False
            config['start_time'] = 0
        else:
            config['open'] = True
            config['start_time'] = int(time.time())
        self.__write_log(self.__state[config['open']] + '网站防火墙(WAF)');
        self.__write_config(config)
        public.ExecShell("/etc/init.d/bt_ipfilter restart")
        return public.returnMsg(True, '设置成功!');

    def set_obj_open(self, get):
        if get.obj == 'set_scan_conf':
            return self.set_scan_conf(get)
        config = self.get_config(None)
        if get.obj == 'webshell_opens':
            if config['webshell_opens']:
                # 这里是关闭
                try:
                    id = public.M('crontab').where('name=?', (u'Nginx防火墙木马查杀进程请勿删除',)).getField('id')
                    if id:
                        import crontab
                        data = {'id': id}
                        crontab.crontab().DelCrontab(data)
                except:
                    pass
            else:
                # 这里是开启
                self.webshell_check()
        if get.obj=="sql_injection":
            msg="SQL注入防御"
        elif get.obj=="xss_injection":
            msg="XSS防御"
        elif get.obj=="user-agent":
            msg="恶意爬虫防御"
        elif get.obj=="cookie":
            msg="恶意Cookie防御"
        elif get.obj=="drop_abroad":
            public.cache_remove('get_drop_abroad_count')
            msg="禁止国外访问"
        elif get.obj=="drop_china":
            msg="禁止国内访问"
        elif get.obj=="is_browser":
            msg="非浏览器访问"
        elif get.obj=="file_upload":
            msg="恶意文件上传"
        elif get.obj=="get":
            msg="恶意下载防御"
        elif get.obj=="get":
            msg="自定义规则拦截"
        elif get.obj=="scan":
            msg="恶意扫描器"
        elif get.obj == "webshell_opens":
            msg = "木马查杀"
        elif get.obj == "http_open":
            msg = "日志记录"
        else:
            msg=get.obj

        if type(config[get.obj]) != bool:
            if config[get.obj]['open']:
                config[get.obj]['open'] = False
            else:
                config[get.obj]['open'] = True

            self.__write_log(self.__state[config[get.obj]['open']] + '【' + msg + '】功能');
        else:
            if config[get.obj]:
                config[get.obj] = False
            else:
                config[get.obj] = True
            self.__write_log(self.__state[config[get.obj]] + '【' + msg + '】功能');

        self.__write_config(config)
        return public.returnMsg(True, '设置成功!');

    def set_spider(self, get):
        try:
            id = int(get.id.strip())
            site_config = self.get_site_config(None)
            if site_config[get.siteName]['spider'][id - 1]:
                if 'status' in site_config[get.siteName]['spider'][id - 1]:
                    if site_config[get.siteName]['spider'][id - 1]['status']:
                        site_config[get.siteName]['spider'][id - 1]['status'] = False
                    else:
                        site_config[get.siteName]['spider'][id - 1]['status'] = True
                    self.__write_site_config(site_config)
                    return public.returnMsg(True, '设置成功!')
            return public.returnMsg(False, '错误的参数!')
        except:
            return public.returnMsg(False, '错误的参数!')

    def set_site_obj_open(self, get):
        site_config = self.get_site_config(None)

        if get.obj=="drop_abroad":
            public.cache_remove('get_drop_abroad_count')
            #判断全局是否开启。如果全局是关闭的状态、那么此刻就不能开启
            if not self.get_config(None)['drop_abroad']['open']:
                return public.returnMsg(False, '全局设置中未开启禁止国外访问!')
        # if get.obj=="sql_injection":
        #     #判断全局是否开启。如果全局是关闭的状态、那么此刻就不能开启
        #     if not self.get_config(None)['sql_injection']['open']:
        #         return public.returnMsg(False, '全局设置中未开启SQL注入防御!')
        #
        # if get.obj=="xss_injection":
        #     #判断全局是否开启。如果全局是关闭的状态、那么此刻就不能开启
        #     if not self.get_config(None)['xss_injection']['open']:
        #         return public.returnMsg(False, '全局设置中未开启XSS防御!')
        #
        # if get.obj=="user-agent":
        #     #判断全局是否开启。如果全局是关闭的状态、那么此刻就不能开启
        #     if not self.get_config(None)['user-agent']['open']:
        #         return public.returnMsg(False, '全局设置中未开启恶意爬虫防御!')
        #
        # if get.obj=="cookie":
        #     #判断全局是否开启。如果全局是关闭的状态、那么此刻就不能开启
        #     if not self.get_config(None)['cookie']['open']:
        #         return public.returnMsg(False, '全局设置中未开启恶意Cookie防御!')
        # if get.obj=="cc":
        #     #判断全局是否开启。如果全局是关闭的状态、那么此刻就不能开启
        #     if not self.get_config(None)['cc']['open']:
        #         return public.returnMsg(False, '全局设置中未开启CC防御!')
        if get.obj=="sql_injection":
            msg="SQL注入防御"
        elif get.obj=="xss_injection":
            msg="XSS防御"
        elif get.obj=="user-agent":
            msg="恶意爬虫防御"
        elif get.obj=="cookie":
            msg="恶意Cookie防御"
        elif get.obj=="drop_abroad":
            msg="禁止国外访问"
        elif get.obj=="drop_china":
            msg="禁止国内访问"
        elif get.obj=="is_browser":
            msg="非浏览器访问"
        elif get.obj=="file_upload":
            msg="恶意文件上传"
        elif get.obj=="get":
            msg="恶意下载防御"
        elif get.obj=="get":
            msg="自定义规则拦截"
        elif get.obj=="scan":
            msg="恶意扫描器"
        elif get.obj == "webshell_opens":
            msg = "木马查杀"
        elif get.obj == "http_open":
            msg = "日志记录"
        else:
            msg=get.obj
        if get.obj == 'spider':
            # 关闭就是关闭所有蜘蛛
            if site_config[get.siteName]['spider_status']:
                site_config[get.siteName]['spider_status'] = False
            else:
                site_config[get.siteName]['spider_status'] = True
            self.__write_site_config(site_config)
            return public.returnMsg(True, '设置成功!如需立即生效需重启Nginx')
        if type(site_config[get.siteName][get.obj]) != bool:
            if site_config[get.siteName][get.obj]['open']:
                site_config[get.siteName][get.obj]['open'] = False
            else:
                site_config[get.siteName][get.obj]['open'] = True

            self.__write_log(self.__state[site_config[get.siteName][get.obj][
                'open']] + '网站【' + get.siteName + '】【' + msg + '】功能');
        else:
            if site_config[get.siteName][get.obj]:
                site_config[get.siteName][get.obj] = False
            else:
                site_config[get.siteName][get.obj] = True
            self.__write_log(
                self.__state[site_config[get.siteName][get.obj]] + '网站【' + get.siteName + '】【' + msg + '】功能');
        if get.obj == 'drop_abroad': self.__auto_sync_cnlist();
        self.__write_site_config(site_config)
        return public.returnMsg(True, '设置成功!');

    def __auto_sync_cnlist(self):
        return True

    def set_obj_status(self, get):
        config = self.get_config(None)
        if get.obj == 'post_is_xss_count':
            config[get.obj] = int(get.statusCode)
        else:
            config[get.obj]['status'] = int(get.statusCode)
        self.__write_config(config)
        return public.returnMsg(True, '设置成功!');

    def set_cc_conf(self, get):
        config = self.get_config(None)
        if not 'cc_increase_type' in get: return public.returnMsg(False, '需要cc_increase_type参数');
        if not get.cc_increase_type in ['js', 'code', 'renji', 'huadong', 'browser']: return public.returnMsg(False,
                                                                                                              '需要cc_increase_type参数');
        end_time = int(get.endtime)
        if end_time > 86400:
            return public.returnMsg(False, '封锁时间不能超过86400秒')
        if not 'cc_mode' in get: get.cc_mode = '1'
        if 'country' in get:
            try:
                countrysss = get.country.split(",")
                country = {}
                for i in countrysss:
                    i = i.strip()
                    if i:
                        country[i] = i
            except:
                country = {}
        else:
            country = {}
        config['cc_mode'] = int(get.cc_mode)
        config['cc']['cycle'] = int(get.cycle)
        config['cc']['limit'] = int(get.limit)
        config['cc']['endtime'] = int(get.endtime)
        config['cc']['countrys'] = country
        config['cc']['increase'] = (get.increase == '1') | False
        config['increase_wu_heng'] = (get.increase_wu_heng == '1') | False
        config['cc']['cc_increase_type'] = get.cc_increase_type
        config['cc_type_status'] = int(get.cc_type_status)
        if int(get.cc_mode) == 3:
            config['cc_automatic'] = True
        else:
            config['cc_automatic'] = False
        self.__write_config(config)
        public.writeFile('/www/server/btwaf/config.json', json.dumps(config))
        self.__write_log(
            '设置全局CC配置为：' + get.cycle + ' 秒内累计请求超过 ' + get.limit + ' 次后,封锁 ' + get.endtime + ' 秒' + ',增强:' + get.increase);
        if get.is_open_global:
            self.set_cc_golbls(get)
        public.serviceReload()
        return public.returnMsg(True, '设置成功!');

    def set_site_cc_conf(self, get):
        if not 'cc_increase_type' in get: return public.returnMsg(False, '需要cc_increase_type参数');
        if not get.cc_increase_type in ['js', 'code', 'renji', 'huadong', 'browser']: return public.returnMsg(False,
                                                                                                              '需要cc_increase_type参数');
        site_config = self.get_site_config(None)
        if not 'cc_mode' in get: get.cc_mode = 1
        if not 'cc_time' in get: get.cc_time = False
        if not 'cc_retry_cycle' in get: get.cc_retry_cycle = False
        if 'country' in get:
            try:
                countrysss = get.country.split(",")
                country = {}
                for i in countrysss:
                    i = i.strip()
                    if i:
                        country[i] = i
            except:
                country = {}
        else:
            country = {}
        if get.cc_mode and get.cc_retry_cycle:
            if not self.isDigit(get.cc_mode) and not self.isDigit(get.cc_retry_cycle): return public.returnMsg(False,
                                                                                                               '需要设置数字!')
            site_config[get.siteName]['cc_time'] = int(get.cc_time)
            site_config[get.siteName]['cc_mode'] = int(get.cc_mode)
            site_config[get.siteName]['cc']['cc_mode'] = int(get.cc_mode)
            site_config[get.siteName]['cc_retry_cycle'] = int(get.cc_retry_cycle)
            site_config[get.siteName]['cc_automatic'] = True
            site_config[get.siteName]['cc']['countrys'] = country
        else:
            site_config[get.siteName]['cc']['countrys'] = country
            site_config[get.siteName]['cc_automatic'] = False
            site_config[get.siteName]['cc_mode'] = int(get.cc_mode)
            site_config[get.siteName]['cc']['cc_mode'] = int(get.cc_mode)
            site_config[get.siteName]['cc']['cycle'] = int(get.cycle)
            site_config[get.siteName]['cc']['limit'] = int(get.limit)
            site_config[get.siteName]['cc']['endtime'] = int(get.endtime)
            site_config[get.siteName]['cc']['cc_increase_type'] = get.cc_increase_type
            site_config[get.siteName]['cc']['increase'] = (get.increase == '1') | False
            site_config[get.siteName]['increase_wu_heng'] = (get.increase_wu_heng == '1') | False
        site_config[get.siteName]['cc_type_status'] = int(get.cc_type_status)
        self.__write_site_config(site_config)
        public.WriteFile('/www/server/btwaf/site.json', json.dumps(site_config, ensure_ascii=False))
        self.__write_log(
            '设置站点【' + get.siteName + '】CC配置为：' + get.cycle + ' 秒内累计请求超过 ' + get.limit + ' 次后,封锁 ' + get.endtime + ' 秒' + ',增强:' + get.increase);
        return public.returnMsg(True, '设置成功!')

    def cn_to_ip(self, aaa):
        for i in aaa:
            for i2 in range(len(i)):
                if i2>=2:break
                i[i2] = self.ip2long(i[i2])
        return aaa

    def binary_search(self,data, value):
        low = 0
        high = len(data) - 1

        while low <= high:
            mid = (low + high) // 2
            start, end = data[mid]

            if start <= value <= end:
                return {"start":start,"end":end,"result":True}
            elif value < start:
                high = mid - 1
            else:
                low = mid + 1
        return {"start":0,"end":0,"result":False}

    def add_cnip(self, get):
        ipn = [self.__format_ip(get.start_ip), self.__format_ip(get.end_ip)]
        if not ipn[0] or not ipn[1]: return public.returnMsg(False, 'IP段格式不正确');
        if not self.__is_ipn(ipn): return public.returnMsg(False, '起始IP不能大于结束IP');
        iplist = self.get_cn_list('cn')
        ipn = [get.start_ip, get.end_ip]
        if ipn in iplist: return public.returnMsg(False, '指定IP段已存在!');

        rule = self.__get_rule("cn")
        start_info=self.binary_search(rule, self.ip2long(ipn[0]))
        end_info = self.binary_search(rule, self.ip2long(ipn[1]))
        if start_info["result"]:
            return public.returnMsg(False, "该IP已经存在在:"+self.long2ip(start_info["start"]) +"-"+self.long2ip(start_info["end"])+"这个IP段中,无需添加")
        if end_info["result"]:
            return public.returnMsg(False, "该IP已经存在在:"+self.long2ip(end_info["start"]) +"-"+self.long2ip(end_info["end"])+"这个IP段中,无需添加")

        iplist.insert(0, ipn)
        iplist2=self.cn_to_ip(iplist)
        iplist2 = sorted(iplist2, key=lambda x: x[0])
        self.__write_rule('cn', iplist2)
        self.__write_log('添加IP段[' + get.start_ip + '-' + get.end_ip + ']到国内IP库');
        return public.returnMsg(True, '添加成功!')

    def remove_cnip(self, get):
        index = int(get.index)
        iplist = self.get_cn_list('cn')
        del (iplist[index])
        iplist2=self.cn_to_ip(iplist)
        iplist2 = sorted(iplist2, key=lambda x: x[0])
        self.__write_rule('cn', iplist2)
        return public.returnMsg(True, '删除成功!')


    def add_ip_white(self, get):
        ipn = [self.__format_ip(get.start_ip), self.__format_ip(get.end_ip)]
        ips = "-,{}-{}".format(get.start_ip, get.end_ip)
        public.WriteFile("/dev/shm/.bt_ip_filter", ips)
        if not ipn[0] or not ipn[1]: return public.returnMsg(False, 'IP段格式不正确');
        if not self.__is_ipn(ipn): return public.returnMsg(False, '起始IP不能大于结束IP');
        ipn = [get.start_ip, get.end_ip]
        if 'ps' in get and get.ps:
            ipn.append(get.ps)
        iplist = self.get_cn_list('ip_white')
        if ipn in iplist: return public.returnMsg(False, '指定IP段已存在!');
        iplist.insert(0, ipn)
        self.__write_rule('ip_white', self.cn_to_ip(iplist))
        self.__write_log('添加IP段[' + get.start_ip + '-' + get.end_ip + ']到IP白名单')
        return public.returnMsg(True, '添加成功!')

    def edit_ip_white_ps(self,get):
        if 'id'  not in  get:return public.returnMsg(False, '参数错误!')
        iplist = self.get_cn_list('ip_white')
        if len(iplist) < int(get.id): return public.returnMsg(False, '参数错误!')
        if len(iplist[int(get.id)])==2:
            iplist[int(get.id)].append(get.ps)
        else:
            iplist[int(get.id)][2] = get.ps
        self.__write_rule('ip_white', self.cn_to_ip(iplist))
        return public.returnMsg(True, '修改成功!')

    def edit_ip_black_ps(self,get):
        if 'id'  not in  get:return public.returnMsg(False, '参数错误!')
        iplist = self.get_cn_list('ip_black')
        if len(iplist) < int(get.id): return public.returnMsg(False, '参数错误!')
        if len(iplist[int(get.id)])==2:
            iplist[int(get.id)].append(get.ps)
        else:
            iplist[int(get.id)][2] = get.ps
        self.__write_rule('ip_black', self.cn_to_ip(iplist))
        return public.returnMsg(True, '修改成功!')

    def remove_ip_white(self, get):
        index = int(get.index)
        iplist = self.get_cn_list('ip_white')
        ipn = iplist[index]
        del (iplist[index])
        self.__write_rule('ip_white', self.cn_to_ip(iplist))
        return public.returnMsg(True, '删除成功!')

    def import_data2(self, type, pdata):
        if not pdata: return public.returnMsg(False, '数据格式不正确')
        # iplist = self.get_cn_list(type)
        for i in pdata:
            ipn = [self.__format_ip(i[0]), self.__format_ip(i[1])]
            if not ipn[0] or not ipn[1]: continue
            if not self.__is_ipn(ipn): continue
            ipn = [i[0], i[1]]
            iplist = self.get_cn_list(type)
            if ipn in iplist: continue
            iplist.insert(0, ipn)
            self.__write_rule(type, self.cn_to_ip(iplist))
        return public.returnMsg(True, '导入成功!')

    def is_ip_zhuanhuang(self, ip, ip2=False, ip_duan=False):
        try:
            ret = []
            if ip_duan:
                ip_ddd = int(ip.split('/')[1])
                ip = ip.split('/')[0].split('.')
                if ip_ddd >= 32: return False
                if ip_ddd >= 24: pass
                if ip_ddd >= 16 and ip_ddd < 24:
                    ip[-1] = "0"
                    ip[-2] = "0"
                if ip_ddd >= 8 and ip_ddd < 16:
                    ip[-1] = "0"
                    ip[-2] = "0"
                    ip[-3] = "0"
                from IPy import IP
                ip2 = IP("{}/{}".format('.'.join(ip), ip_ddd))
                return self.is_ip_zhuanhuang(str(ip2[0]), str(ip2[-1]))
            else:
                if ip2 and ip:
                    ret.append(ip)
                    ret.append(ip2)
                    return ret
                else:
                    ret.append(ip)
                    ret.append(ip)
                    return ret
        except:
            return False

    def bt_ip_filter(self, datas):
        # 检查状态
        status = public.ExecShell("/etc/init.d/bt_ipfilter status")
        if 'service not running' in status[0]:
            public.ExecShell("/etc/init.d/bt_ipfilter restart")
        path = "/dev/shm/.bt_ip_filter"
        if os.path.exists(path):
            data = public.ReadFile(path)
            data += "\n" + datas
            public.WriteFile(path, data)
        else:
            public.WriteFile(path, datas)

    def import_data(self, get):
        name = get.s_Name
        if name == 'ip_white' or name == 'ip_black' or name=="cn":
            padata = get.pdata.strip().split()
            if not padata: return public.returnMsg(False, '数据格式不正确')
            iplist = self.get_cn_list(name)
            for i in padata:
                if re.search("\d+.\d+.\d+.\d+-\d+.\d+.\d+.\d+$", i):
                    ip = i.split('-')
                    ips = self.is_ip_zhuanhuang(ip[0], ip[1])
                    if not ips: continue
                    if ips in iplist: continue
                    iplist.insert(0, ips)

                elif re.search("\d+.\d+.\d+.\d+/\d+$", i):
                    ips = self.is_ip_zhuanhuang(i, ip_duan=True)
                    if not ips: continue
                    if ips in iplist: continue
                    iplist.insert(0, ips)

                elif re.search("\d+.\d+.\d+.\d+$", i):
                    ips = self.is_ip_zhuanhuang(i)
                    if not ips: continue
                    if ips in iplist: continue
                    iplist.insert(0, ips)
                if name == 'ip_black':
                    # 如果他在白名单中则不添加
                    ipn = [ips[0], ips[1]]
                    ip_white_rule = self.get_cn_list('ip_white')
                    if ipn in ip_white_rule: continue
                    self.bt_ip_filter("+,%s-%s,86400" % (ips[0], ips[1]))
                if name == "ip_white":
                    ips = self.is_ip_zhuanhuang(i)
                    self.bt_ip_filter("-,%s-%s" % (ips[0], ips[1]))
                # public.ExecShell('echo "+,%s-%s,86400" >/dev/shm/.bt_ip_filter'%(ips[0],ips[1]))
            self.__write_rule(name, self.cn_to_ip(iplist))
            return public.returnMsg(True, '导入成功!')
        else:
            if 'json' not in get:
                get.json = True
            else:
                get.json = False
            if get.json:
                pdata = json.loads(get.pdata)
            else:
                pdata = get.pdata.strip().split()
            if not pdata: return public.returnMsg(False, '数据格式不正确');
            if name == 'ip_white': return self.import_data2('ip_white', pdata)
            if name == 'ip_black': return self.import_data2('ip_black', pdata)
            if name == 'cn': return self.import_data2('cn', pdata)
            iplist = self.__get_rule(name)
            for ips in pdata:
                if ips in iplist: continue;
                iplist.insert(0, ips)
            self.__write_rule(name, iplist)
            return public.returnMsg(True, '导入成功!')

    def output_data(self, get):
        iplist = self.__get_rule(get.s_Name)
        return iplist;

    def add_ip_black(self, get):
        ipn = [self.__format_ip(get.start_ip), self.__format_ip(get.end_ip)]
        if not ipn[0] or not ipn[1]: return public.returnMsg(False, 'IP段格式不正确');
        if not self.__is_ipn(ipn): return public.returnMsg(False, '起始IP不能大于结束IP');

        ipn = [get.start_ip, get.end_ip]

        iplist = self.get_cn_list('ip_white')
        if not ipn in iplist:
            ipn = [get.start_ip, get.end_ip]
            self.bt_ip_filter("+,%s-%s,86400" % (get.start_ip, get.end_ip))
        if 'ps' in get and get.ps:
            ipn.append(get.ps)
        iplist = self.get_cn_list('ip_black')
        if ipn in iplist: return public.returnMsg(False, '指定IP段已存在!');
        iplist.insert(0, ipn)
        self.__write_rule('ip_black', self.cn_to_ip(iplist))
        self.__write_log('添加IP段[' + get.start_ip + '-' + get.end_ip + ']到IP黑名单')
        return public.returnMsg(True, '添加成功!')

    def remove_ip_black(self, get):
        index = int(get.index)
        iplist = self.get_cn_list('ip_black')
        ipn = iplist[index]
        del (iplist[index])
        # return ipn
        self.bt_ip_filter("-,%s-%s,86400" % (ipn[0], ipn[1]))
        self.__write_rule('ip_black', self.cn_to_ip(iplist))
        return public.returnMsg(True, '删除成功!')

    def add_url_white(self, get):
        url_white = self.__get_rule('url_white')
        url_rule = get.url_rule.strip()
        if url_rule == '^/' or url_rule == '/': return public.returnMsg(False, '不允许添加根目录')
        if get.url_rule in url_white: return public.returnMsg(False, '您添加的URL已存在')
        url_white.insert(0, url_rule)
        self.__write_rule('url_white', url_white)
        self.__write_log('添加url规则[' + url_rule + ']到URL白名单');
        return public.returnMsg(True, '添加成功!')

    def add_url_white_senior(self, get):
        if not 'url' in get: return public.returnMsg(False, '请输入url!')
        if not 'param' in get: return public.returnMsg(False, '请输入参数!')
        url_white = self.__get_rule('url_white_senior')
        try:
            param = json.loads(get.param)
        except:
            return public.returnMsg(False, '参数传递错误!')
        params = []
        for i in param:
            if i == "": continue
            if not i: continue
            params.append(i)
        data = {get.url: params}
        if data in url_white: return public.returnMsg(False, '已存在!')
        url_white.insert(0, data)
        self.__write_rule('url_white_senior', url_white)
        return public.returnMsg(True, '添加成功')

    def del_url_white_senior(self, get):
        if not 'url' in get: return public.returnMsg(False, '请输入url!')
        if not 'param' in get: get.param=""
        url_white = self.__get_rule('url_white_senior')
        param = get.param.strip()
        param = param.split(",")
        if len(param)==1 and param[0]=="":
            data = {get.url: []}
        else:
            data = {get.url: param}
        if not data in url_white: return public.returnMsg(False, '不存在!')
        url_white.remove(data)
        self.__write_rule('url_white_senior', url_white)
        return public.returnMsg(True, '删除成功')

    def get_url_white_senior(self, get):
        url_white = self.__get_rule('url_white_senior')
        return url_white

    def get_url_request_mode(self, get):
        url_white = self.__get_rule('url_request_mode')
        return url_white

    def get_reg_tions(self, get):
        url_white = self.__get_rule('reg_tions')
        return url_white

    def city(self, get):

        data = ['中国大陆以外的地区(包括[中国特别行政区:港,澳,台])', '中国大陆(不包括[中国特别行政区:港,澳,台])', '中国香港', '中国澳门', '中国台湾',
                '美国', '日本', '英国', '德国', '韩国', '法国', '巴西', '加拿大', '意大利', '澳大利亚', '荷兰', '俄罗斯', '印度', '瑞典', '西班牙', '墨西哥',
                '比利时', '南非', '波兰', '瑞士', '阿根廷', '印度尼西亚', '埃及', '哥伦比亚', '土耳其', '越南', '挪威', '芬兰', '丹麦', '乌克兰', '奥地利',
                '伊朗', '智利', '罗马尼亚', '捷克', '泰国', '沙特阿拉伯', '以色列', '新西兰', '委内瑞拉', '摩洛哥', '马来西亚', '葡萄牙', '爱尔兰', '新加坡',
                '欧洲联盟', '匈牙利', '希腊', '菲律宾', '巴基斯坦', '保加利亚', '肯尼亚', '阿拉伯联合酋长国', '阿尔及利亚', '塞舌尔', '突尼斯', '秘鲁', '哈萨克斯坦',
                '斯洛伐克', '斯洛文尼亚', '厄瓜多尔', '哥斯达黎加', '乌拉圭', '立陶宛', '塞尔维亚', '尼日利亚', '克罗地亚', '科威特', '巴拿马', '毛里求斯', '白俄罗斯',
                '拉脱维亚', '多米尼加', '卢森堡', '爱沙尼亚', '苏丹', '格鲁吉亚', '安哥拉', '玻利维亚', '赞比亚', '孟加拉国', '巴拉圭', '波多黎各', '坦桑尼亚',
                '塞浦路斯', '摩尔多瓦', '阿曼', '冰岛', '叙利亚', '卡塔尔', '波黑', '加纳', '阿塞拜疆', '马其顿', '约旦', '萨尔瓦多', '伊拉克', '亚美尼亚', '马耳他',
                '危地马拉', '巴勒斯坦', '斯里兰卡', '特立尼达和多巴哥', '黎巴嫩', '尼泊尔', '纳米比亚', '巴林', '洪都拉斯', '莫桑比克', '尼加拉瓜', '卢旺达', '加蓬',
                '阿尔巴尼亚', '利比亚', '吉尔吉斯坦', '柬埔寨', '古巴', '喀麦隆', '乌干达', '塞内加尔', '乌兹别克斯坦', '黑山', '关岛', '牙买加', '蒙古', '文莱',
                '英属维尔京群岛', '留尼旺', '库拉索岛', '科特迪瓦', '开曼群岛', '巴巴多斯', '马达加斯加', '伯利兹', '新喀里多尼亚', '海地', '马拉维', '斐济', '巴哈马',
                '博茨瓦纳', '扎伊尔', '阿富汗', '莱索托', '百慕大', '埃塞俄比亚', '美属维尔京群岛', '列支敦士登', '津巴布韦', '直布罗陀', '苏里南', '马里', '也门',
                '老挝', '塔吉克斯坦', '安提瓜和巴布达', '贝宁', '法属玻利尼西亚', '圣基茨和尼维斯', '圭亚那', '布基纳法索', '马尔代夫', '泽西岛', '摩纳哥', '巴布亚新几内亚',
                '刚果', '塞拉利昂', '吉布提', '斯威士兰', '缅甸', '毛里塔尼亚', '法罗群岛', '尼日尔', '安道尔', '阿鲁巴', '布隆迪', '圣马力诺', '利比里亚',
                '冈比亚', '不丹', '几内亚', '圣文森特岛', '荷兰加勒比区', '圣马丁', '多哥', '格陵兰', '佛得角', '马恩岛', '索马里', '法属圭亚那', '西萨摩亚',
                '土库曼斯坦', '瓜德罗普', '马里亚那群岛', '瓦努阿图', '马提尼克', '赤道几内亚', '南苏丹', '梵蒂冈', '格林纳达', '所罗门群岛', '特克斯和凯科斯群岛', '多米尼克',
                '乍得', '汤加', '瑙鲁', '圣多美和普林西比', '安圭拉岛', '法属圣马丁', '图瓦卢', '库克群岛', '密克罗尼西亚联邦', '根西岛', '东帝汶', '中非',
                '几内亚比绍', '帕劳', '美属萨摩亚', '厄立特里亚', '科摩罗', '圣皮埃尔和密克隆', '瓦利斯和富图纳', '英属印度洋领地', '托克劳', '马绍尔群岛', '基里巴斯',
                '纽埃', '诺福克岛', '蒙特塞拉特岛', '朝鲜', '马约特', '圣卢西亚', '圣巴泰勒米岛']

        return data

    def reg_domains(self, get):
        site_config2 = json.loads(public.readFile(self.__path + 'domains.json'))
        return site_config2

    def add_reg_tions(self, get):
        if not 'site' in get: return public.returnMsg(False, '请输入需要设置的站点!')
        if not 'types' in get: return public.returnMsg(False, '请输入类型!')
        if not 'region' in get: return public.returnMsg(False, '请输入地区!')
        url_white = self.__get_rule('reg_tions')
        param = get.region.split(",")

        sitessss = get.site.split(",")
        type_list = ["refuse", "accept"]
        if not get.types in type_list: return public.returnMsg(False, '输入的类型错误!')

        paramMode = {}
        for i in param:
            if not i: continue
            i = i.strip()
            if not i in paramMode:
                paramMode[i] = "1"
        sitesMode = {}

        if '海外' in paramMode and '中国' in paramMode:
            return public.returnMsg(False, '不允许设置【中国大陆】和【中国大陆以外地区】一同开启地区限制!')
        for i in sitessss:
            i = i.strip()
            if not i: continue

            if not i in sitesMode:
                sitesMode[i] = "1"
        if len(paramMode) == 0: return public.returnMsg(False, '输入的请求类型错误!')
        if len(sitesMode) == 0: return public.returnMsg(False, '输入的站点错误!')

        data = {"site": sitesMode, "types": get.types, "region": paramMode}
        if data in url_white: return public.returnMsg(False, '已存在!')
        url_white.insert(0, data)
        self.__write_rule('reg_tions', url_white)
        return public.returnMsg(True, '添加成功!')

    def del_reg_tions(self, get):
        if not 'site' in get: return public.returnMsg(False, '请输入需要设置的站点!')
        if not 'types' in get: return public.returnMsg(False, '请输入类型!')
        if not 'region' in get: return public.returnMsg(False, '请输入地区!')
        url_white = self.__get_rule('reg_tions')
        param = get.region.split(",")
        sitessss = get.site.split(",")
        type_list = ["refuse", "accept"]
        if not get.types in type_list: return public.returnMsg(False, '输入的类型错误!')
        paramMode = {}
        for i in param:
            if not i: continue
            if not i in paramMode:
                paramMode[i] = "1"
        sitesMode = {}
        for i in sitessss:
            if not i: continue
            if not i in sitesMode:
                sitesMode[i] = "1"
        if len(paramMode) == 0: return public.returnMsg(False, '输入的请求类型错误!')
        if len(sitesMode) == 0: return public.returnMsg(False, '输入的站点错误!')

        data = {"site": sitesMode, "types": get.types, "region": paramMode}
        if not data in url_white: return public.returnMsg(False, '不存在!')
        url_white.remove(data)
        self.__write_rule('reg_tions', url_white)
        return public.returnMsg(True, '删除成功!')

    def add_url_request_mode(self, get):
        if not 'url' in get: return public.returnMsg(False, '请输入url!')
        if not 'param' in get: return public.returnMsg(False, '请输入参数!')
        if not 'type' in get: return public.returnMsg(False, '请输入类型!')
        url_white = self.__get_rule('url_request_mode')
        param = get.param.split(",")
        paramlist = ["POST", "GET", "PUT", "OPTIONS", "HEAD", "DELETE", "TRACE", "PATCH", "MOVE", "COPY", "LINK",
                     "UNLINK", "WRAPPED", "PROPFIND", "PROPPATCH"
                                                      "MKCOL", "CONNECT", "SRARCH"]
        type_list = ["refuse", "accept"]
        if not get.type in type_list: return public.returnMsg(False, '输入的类型错误!')
        paramMode = {}
        for i in param:
            if i in paramlist:
                if not i in paramMode:
                    paramMode[i] = i
        if len(paramMode) == 0: return public.returnMsg(False, '输入的请求类型错误!')
        data = {"url": get.url, "type": get.type, "mode": paramMode}
        if data in url_white: return public.returnMsg(False, '已存在!')
        url_white.insert(0, data)
        self.__write_rule('url_request_mode', url_white)
        return public.returnMsg(True, '添加成功!')

    def del_url_request_mode(self, get):
        if not 'url' in get: return public.returnMsg(False, '请输入url!')
        if not 'param' in get: return public.returnMsg(False, '请输入参数!')
        if not 'type' in get: return public.returnMsg(False, '请输入类型!')
        url_white = self.__get_rule('url_request_mode')
        param = get.param.split(",")
        paramlist = ["POST", "GET", "PUT", "OPTIONS", "HEAD", "DELETE", "TRACE", "PATCH", "MOVE", "COPY", "LINK",
                     "UNLINK", "WRAPPED", "PROPFIND", "PROPPATCH"
                                                      "MKCOL", "CONNECT", "SRARCH"]
        type_list = ["refuse", "accept"]
        if not get.type in type_list: return public.returnMsg(False, '输入的类型错误!')
        paramMode = {}
        for i in param:
            if i in paramlist:
                if not i in paramMode:
                    paramMode[i] = i
        if len(paramMode) == 0: return public.returnMsg(False, '输入的请求类型错误!')
        data = {"url": get.url, "type": get.type, "mode": paramMode}
        if not data in url_white: return public.returnMsg(False, '已存在!')
        url_white.remove(data)
        self.__write_rule('url_request_mode', url_white)
        return public.returnMsg(True, '删除成功!')

    def url_white_add_param(self,get):
        url = get.url_rule.strip()
        #获取到url 然后再获取参数
        uri = url.split('?')[0]
        url2 = url.replace(uri, "")
        ret = []
        if not url2.startswith("?"):
            return public.returnMsg(False, '未发现该URL存在参数!')
        else:
            # 去掉第一个字符串
            url2 = url2[1:]
            # 使用&分割字符串
            url2 = url2.split('&')
            # 遍历字符串
            for i in url2:
                i = i.split("=")
                if len(i) == 2:
                    ret.append(i[0])
        if not ret:
            return public.returnMsg(False, '未发现该URL存在参数!')
        if uri=="/":
            return public.returnMsg(False, '不允许添加URL为 [/] 的URL为白名单')
        get.url=uri
        get.param=json.dumps(ret)
        return self.add_url_white_senior(get)


    def wubao_url_white(self, get):
        if not 'http_log' in get:
            get.http_log = ''
        if not 'error_log' in get:
            get.error_log = ''
        if not 'param' in get:
            get.param=0
        url_rule=""


        if get.param==0:
            url_white = self.__get_rule('url_white')
            url_rule = get.url_rule.strip()
            url_rule = '^' + url_rule.split('?')[0]
            if url_rule in url_white: return public.returnMsg(False, '您添加的URL已存在')
            if url_rule == '^/': return public.returnMsg(False, '不允许添加URL为 [/] 的URL为白名单')
            url_white.insert(0, url_rule)
            self.__write_rule('url_white', url_white)
            self.__write_log('添加url规则[' + url_rule + ']到URL白名单')
        else:
            if os.path.exists('/www/server/panel/data/userInfo.json'):
                try:
                    userInfo = json.loads(public.ReadFile('/www/server/panel/data/userInfo.json'))
                    url = "https://www.bt.cn/api/bt_waf/reportInterceptFail"
                    data = {"url": url_rule, "error_log": get.error_log, "http_log": get.http_log,
                            "access_key": userInfo['access_key'], "uid": userInfo['uid']}
                    public.httpPost(url, data)
                except:
                    pass

            return self.url_white_add_param(get)
        if os.path.exists('/www/server/panel/data/userInfo.json'):
            try:
                userInfo = json.loads(public.ReadFile('/www/server/panel/data/userInfo.json'))
                url = "https://www.bt.cn/api/bt_waf/reportInterceptFail"
                data = {"url": url_rule, "error_log": get.error_log, "http_log": get.http_log,
                        "access_key": userInfo['access_key'], "uid": userInfo['uid']}
                public.httpPost(url, data)
            except:
                pass
        return public.returnMsg(True, '添加成功!')

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
        # return self.set_scan_conf(get)
        scan_rule = {'header': get.header, 'cookie': get.cookie, 'args': get.args}
        self.__write_rule('scan_black', scan_rule)
        self.__write_log('修改扫描器过滤规则');
        return public.returnMsg(True, '设置成功')

    def set_retry(self, get):
        config = self.get_config(None)
        end_time = int(get.retry_time)
        if end_time > 86400: return public.returnMsg(False, '封锁时间不能超过86400!');

        config['retry'] = int(get.retry)
        config['retry_cycle'] = int(get.retry_cycle)
        config['retry_time'] = int(get.retry_time)
        self.__write_config(config)
        self.__write_log('设置非法请求容忍阈值: ' + get.retry_cycle + ' 秒内累计超过 ' + get.retry + ' 次, 封锁 ' + get.retry_time + ' 秒');
        if get.is_open_global:
            self.set_cc_retry_golbls(get)
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
        site_config[get.siteName]['cdn_header'].insert(0, get.cdn_header)
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
                get.ruleUri = get.ruleUri.split('?')[0]

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

    def get_cn_list(self, type):
        if type == 'ip_white' or type == 'ip_black' or type == 'cn':
            try:
                rule = self.__get_rule(type)
                for i in rule:
                    for i2 in range(len(i)):
                        if i2>=2:continue
                        i[i2] = self.long2ip(i[i2])
                return rule
            except:
                self.__write_rule(type, [])
                os.system('/etc/init.d/nginx restart')
                return []
        else:
            rule = self.__get_rule(type)
            for i in rule:
                for i2 in range(len(i)):
                    i[i2] = self.long2ip(i[i2])
            return rule

    def get_rule(self, get):
        if get.ruleName == 'cn':
            return self.get_cn_list('cn')
        if get.ruleName == 'ip_white':
            return self.get_cn_list('ip_white')
        if get.ruleName == 'ip_black':
            return self.get_cn_list('ip_black')
        if get.ruleName == 'spider':
            return self.spider(get)
        rule = self.__get_rule(get.ruleName)
        if not rule: return [];
        return rule

    def spider(self, get):
        if not 'spider' in get:
            get.spider = 'baidu'
        list_sp = ["baidu", "google", "360", "sogou", "yahoo", "bingbot", "bytespider"]
        if not str(get.spider) in list_sp: return []
        list_index = list_sp.index(str(get.spider))
        try:
            path = "/www/server/btwaf/" + str(list_index + 1) + '.json'
            rules = public.readFile(path)
            if not rules: return []
            return json.loads(rules)
        except:
            return []

    # spider添加删除
    def add_spider(self, get):
        if not 'ip' in get: return public.returnMsg(False, '请输入IP地址')
        if not 'spider' in get:
            get.spider = 'baidu'
        list_sp = ["baidu", "google", "360", "sogou", "yahoo", "bingbot", "bytespider"]
        if not str(get.spider) in list_sp: return public.returnMsg(False, '蜘蛛类型错误!')
        list_index = list_sp.index(str(get.spider))
        path = "/www/server/btwaf/" + str(list_index + 1) + '.json'
        try:
            rules = json.loads(public.readFile(path))
            if not rules:
                public.WriteFile(path, json.dumps([get.ip.strip()]))
                return public.returnMsg(True, '添加成功!')
            else:
                if get.ip.strip() in rules:
                    return public.returnMsg(False, '添加失败!')
                else:
                    rules.insert(0, get.ip.strip())
                    public.WriteFile(path, json.dumps(rules))
                    return public.returnMsg(True, '添加成功!')
        except:
            public.WriteFile(path, json.dumps([get.ip.strip()]))
            return public.returnMsg(True, '添加成功!')

    # spider删除
    def del_spider(self, get):
        if not 'ip' in get: return public.returnMsg(False, '请输入IP地址')
        if not 'spider' in get:
            get.spider = 'baidu'
        list_sp = ["baidu", "google", "360", "sogou", "yahoo", "bingbot", "bytespider"]
        if not str(get.spider) in list_sp: return public.returnMsg(False, '蜘蛛类型错误!')
        list_index = list_sp.index(str(get.spider))
        path = "/www/server/btwaf/" + str(list_index + 1) + '.json'
        try:
            rules = json.loads(public.readFile(path))
            if not rules:
                return public.returnMsg(True, '当前IP不存在!')
            else:
                if get.ip.strip() in rules:
                    rules.remove(get.ip.strip())
                    public.WriteFile(path, json.dumps(rules))
                    return public.returnMsg(True, '删除成功!')
                else:
                    return public.returnMsg(False, '当前IP不存在!')
        except:
            public.WriteFile(path, json.dumps([get.ip.strip()]))
            return public.returnMsg(True, '添加成功!')

    # spider导入
    def import_spider(self, get):
        if not 'ip_list' in get: return public.returnMsg(False, '请输入IP地址')
        if not 'spider' in get:
            get.spider = 'baidu'
        list_sp = ["baidu", "google", "360", "sogou", "yahoo", "bingbot", "bytespider"]
        ip_list = json.loads(get.ip_list)
        if not str(get.spider) in list_sp: return public.returnMsg(False, '蜘蛛类型错误!')
        list_index = list_sp.index(str(get.spider))
        path = "/www/server/btwaf/" + str(list_index + 1) + '.json'
        try:
            if len(ip_list) > 1:
                for i in ip_list:
                    get.ip = i
                    self.add_spider(get)
                return public.returnMsg(True, '导入成功!')
        except:
            pass

    def add_rule(self, get):
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
            import html
            pythonV = sys.version_info[0]
            if 'drop_ip' in get:
                path = '/www/server/btwaf/drop_ip.log'
                num = 12
                if os.path.getsize(path) > 209715200:
                    return {"status": False, "msg": "日志文件过大!", "clear": True}
            else:
                path = '/www/wwwlogs/btwaf/' + get.siteName + '_' + get.toDate + '.log'
                num = 10
            if not os.path.exists(path): return ["11"]
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
                                    host = ""
                                    for i in range(len(tmp_data)):
                                        if i == 6:
                                            tmp_data[i] = tmp_data[i].replace('gt;', '>')
                                        if len(tmp_data) > 6 and tmp_data[6]:
                                            tmp_data[6] = tmp_data[6].replace('gt;', '>').replace('&', '')
                                        if i == 7:
                                            tmp_data[i] = str(tmp_data[i]).replace('&amp;', '&').replace('&lt;',
                                                                                                         '<').replace(
                                                '&gt;', '>').replace("&quot;", "\"")
                                            if re.search('host:(.*?)\n', tmp_data[7]):
                                                host = re.search('host:(.*?)\n', tmp_data[7]).groups()[0]


                                        elif i == 10:
                                            tmp_data[i] = str(tmp_data[i]).replace('&amp;', '&').replace('&lt;',
                                                                                                         '<').replace(
                                                '&gt;', '>').replace("&quot;", "\"")
                                        else:
                                            tmp_data[i] = str(tmp_data[i])
                                    if host:
                                        tmp_data.append('http://' + host + tmp_data[3])
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
                drop_iplist = self.get_waf_drop_ip(None)
                stime = time.time()
                setss = []
                for i in range(len(data)):
                    if (float(stime) - float(data[i][0])) < float(data[i][4]):
                        setss.append(data[i][1])
                        data[i].append(data[i][1] in drop_iplist)
                    else:
                        data[i].append(False)
        except:
            data = []
            return public.get_error_info()
        return data

    def get_waf_drop_ip(self, get):
        try:
            data = json.loads(public.httpGet('http://127.0.0.1/get_btwaf_drop_ip'))
            return data
        except:
            return []

    def get_logs_list(self, get):
        path = '/www/wwwlogs/btwaf/'
        sfind = get.siteName + '_'
        data = []
        for fname in os.listdir(path):
            if fname.find(sfind) != 0: continue;
            tmp = fname.replace(sfind, '').replace('.log', '')
            data.append(tmp)
        return sorted(data, reverse=True)

    def remove_waf_drop_ip(self, get):
        public.WriteFile('/dev/shm/.bt_ip_filter', '-,' + get.ip.strip())
        try:
            self.M2('blocking_ip').field('time,ip,is_status').where("ip=? and time>=?",
                                                                    (get.ip.strip(), int(time.time()) - 86400)).update(
                {"is_status": "0"})
        except:
            pass
        try:
            data = json.loads(public.httpGet('http://127.0.0.1/remove_btwaf_drop_ip?ip=' + get.ip))
            self.__write_log('从防火墙解封IP【' + get.ip + '】')
            return data
        except:
            public.WriteFile('/dev/shm/.bt_ip_filter', '-,' + get.ip.strip())
            return public.returnMsg(False, '获取数据失败');

    def clean_waf_drop_ip(self, get):
        public.WriteFile("/dev/shm/.bt_ip_filter", "-,0.0.0.0")
        try:
            self.M2('blocking_ip').field('time,ip,is_status').where("time>=?", (int(time.time()) - 86400)).update(
                {"is_status": "0"})
        except:
            pass
        try:
            public.WriteFile("/dev/shm/.bt_ip_filter", "-,0.0.0.0")
            try:
                datas = public.ExecShell("ipset list |grep timeout")[0].split("\n")
                if len(datas) != 3:
                    public.WriteFile("/dev/shm/.bt_ip_filter", "-,0.0.0.0")
                    public.ExecShell("/etc/init.d/bt_ipfilter restart")
            except:
                pass
            self.__write_log('从防火墙解封所有IP')
            data = json.loads(public.httpGet('http://127.0.0.1/clean_btwaf_drop_ip'))
            for i in self.get_cn_list('ip_black'):
                ipn = [i[0], i[1]]
                iplist = self.get_cn_list('ip_white')
                if ipn in iplist: continue
                self.bt_ip_filter("+,%s-%s,86400" % (i[0], i[1]))
            return data
        except:
            public.WriteFile("/dev/shm/.bt_ip_filter", "-,0.0.0.0")
            return public.returnMsg(False, '获取数据失败')

    def get_gl_logs(self, get):
        import page
        page = page.Page()
        if 'search' in get and get.search:
            count=public.M('logs').where("type=? and log LIKE ?", (u'网站防火墙',"%{}%".format(get.search),)).count()
        else:
            count = public.M('logs').where('type=?', (u'网站防火墙',)).count()
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
        if 'search' in get and get.search:
            data['data'] = public.M('logs').where("type=? and log LIKE ?", (u'网站防火墙',"%{}%".format(get.search),)).order('id desc').limit(
                str(page.SHIFT) + ',' + str(page.ROW)).field('log,addtime').select()
        else:
            data['data'] = public.M('logs').where('type=?', (u'网站防火墙',)).order('id desc').limit(str(page.SHIFT) + ',' + str(page.ROW)).field('log,addtime').select()
        return data

    def get_total(self, get):
        # total = json.loads(public.readFile(self.__path + 'total.json'))
        try:
            total = json.loads(public.readFile(self.__path + 'total.json'))
        except:
            total = {"rules": {"user_agent": 0, "cookie": 0, "post": 0, "args": 0, "url": 0, "cc": 0}, "sites": {},
                     "total": 0}
            self.__write_total(total);
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
            ['sql', u'sql注入拦截'],
            ['xss', u'xss拦截'],
            ['cc', u"CC拦截"],
            ['user_agent', u'恶意爬虫拦截'],
            ['cookie', u'Cookie渗透'],
            ['scan', u'恶意扫描拦截'],
            ['upload', u'文件上传拦截'],
            ['path_php', u'禁止PHP脚本拦截'],
            ['download', u'恶意下载拦截'],
            ['file', u'目录拦截'],
            ['php', u'php代码拦截'],
            ['other', u'自定义拦截']
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
        #cloudUrl = public.GetConfigValue('home')+'/api/panel/get_soft_list'
        cloudUrl = 'http://127.0.0.1/api/panel/get_soft_list'
        pdata = panelAuth.panelAuth().create_serverid(None)
        ret = public.httpPost(cloudUrl, pdata)
        if not ret:
            if not self.__session_name in session: session[self.__session_name] = 1
            return 1
        try:
            ret = json.loads(ret)
            for i in ret["list"]:
                if i['name'] == 'btwaf':
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
        return True

    def test_check_zhilist(self, get):
        try:
            flag = False
            # 如果文件存在
            Itime_path = '/www/server/panel/data/btwaf_getSpiders.ini'
            startime = int(time.time())
            if os.path.exists(Itime_path):
                Itime = int(public.ReadFile(Itime_path))
                if startime - Itime > 36000:
                    flag = True
            else:
                flag = True
            if flag:
                public.WriteFile(Itime_path, str(startime))
                userInfo = json.loads(public.ReadFile('/www/server/panel/data/userInfo.json'))
                data22 = {"access_key": userInfo['access_key'], "uid": userInfo['uid']}
                url = public.GetConfigValue('home')+'/api/bt_waf/getSpiders'
                data_list = json.loads(public.httpPost(url, data22, timeout=3))
                if data_list:
                    for i22 in data_list:
                        try:
                            path = "/www/server/btwaf/%s.json" % i22
                            if os.path.exists(path):
                                ret = json.loads(public.ReadFile(path))
                                localhost_json = list(set(ret).union(data_list[i22]))
                                public.WriteFile(path, json.dumps(localhost_json))
                        except:
                            continue
        except:
            return []

    def return_python(self):
        if os.path.exists('/www/server/panel/pyenv/bin/python'): return '/www/server/panel/pyenv/bin/python'
        if os.path.exists('/usr/bin/python'): return '/usr/bin/python'
        if os.path.exists('/usr/bin/python3'): return '/usr/bin/python3'
        return 'python'

    # 四层计划任务
    def add_webshell_check(self):
        id = public.M('crontab').where('name=?', (u'【官方】Nginx防火墙木马扫描进程',)).getField('id')
        import crontab
        if not id:
            data = {}
            data['name'] = '【官方】Nginx防火墙木马扫描进程'
            data['type'] = 'minute-n'
            data['where1'] = '5'
            data['sBody'] = '%s /www/server/panel/plugin/btwaf/webshell_check.py' % self.return_python()
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

    def get_webshell_size(self):
        rPath = self.Recycle_bin
        if not os.path.exists(rPath):return 0
        #循环这个目录下的所有文件
        count=0
        for root, dirs, files in os.walk(rPath):
            if files:
                for name in files:
                    count+=1
        return count


    def get_webshell_info(self, get):
        ret = []
        try:
            webshell_info = json.loads(public.ReadFile("/www/server/btwaf/webshell.json"))

            for i in webshell_info:
                result = {}
                result['path'] = i
                result['is_path'] = webshell_info[i]
                ret.append(result)
            return ret
        except:
            return []
    #
    # def get_total_all(self,get):
    #     if public.cache_get("get_total_all"):
    #         public.run_thread(self.get_total_all_info,get)
    #         return public.cache_get("get_total_all")
    #     else:
    #         return self.get_total_all_info(get)

    def check_zhiz(self,get):
        zhizhu_list = ['1', '2', '4', '5', '6']
        for i in zhizhu_list:
            try:
                if os.path.getsize('/www/server/btwaf/zhizhu' + i + '.json') > 10:
                    f = open('/www/server/btwaf/zhizhu' + i + '.json', 'r')
                    tt = []
                    for i2 in f:
                        i2 = i2.strip()
                        tt.append(i2)
                    f.close()
                    userInfo = json.loads(public.ReadFile('/www/server/panel/data/userInfo.json'))
                    data22 = {"type": i, "ip_list": json.dumps(tt), "access_key": userInfo['access_key'],
                              "uid": userInfo['uid']}
                    url = public.GetConfigValue('home')+'/api/bt_waf/addSpider'
                    if len(tt) >= 1:
                        public.httpPost(url, data22)
                    public.WriteFile('/www/server/btwaf/zhizhu' + i + '.json', "")
            except:
                continue

    def db_5000(self,get):
        if os.path.exists("/www/server/btwaf/totla_db/totla_db.db") and os.path.getsize(
                "/www/server/btwaf/totla_db/totla_db.db") > 506897664:
            # 大于500M的时候压缩文件
            # 获取一下配置文件
            data_path = '/www/server/panel/data/btwaf_db_file.json'
            datas = []
            if os.path.exists(data_path):
                try:
                    datas = json.loads(public.ReadFile(data_path))
                except:
                    pass
            path = "/www/server/btwaf/totla_db/db.{}.tar.gz".format(time.strftime("%Y-%m-%d"))
            if not datas:
                datas.append({"path": path, "time": time.strftime("%Y-%m-%d")})
            else:
                # 备份最多报错7份
                tmp = []
                if len(datas) >= 3:
                    for i in datas:
                        tmp.append(i['time'])
                    tmp.sort()
                    datas.remove({"path": "/www/server/btwaf/totla_db/db.{}.tar.gz".format(tmp[0]), "time": tmp[0]})
                    public.ExecShell("rm -rf  /www/server/btwaf/totla_db/db.{}.tar.gz".format(tmp[0]))
                if {"path": path, "time": time.strftime("%Y-%m-%d")} in datas:
                    # 如果存在在配置文件中 再判断一下文件是否存在。 如果文件存在 就可以删除源文件了。如果文件不存在那么就不删除源文件
                    if os.path.exists(path):
                        public.ExecShell("rm -rf /www/server/btwaf/totla_db/totla_db.*")
            public.WriteFile(data_path, json.dumps(datas))
            import files
            file = files.files()
            args_obj = public.dict_obj()
            args_obj.sfile = "totla_db.db"
            args_obj.dfile = path
            args_obj.z_type = "tar.gz"
            args_obj.path = "/www/server/btwaf/totla_db/"
            file.Zip(args_obj)

    def get_total_all(self, get):
        self.__check_cjson()
        # self.add_webshell_check()

        nginxconf = '/www/server/nginx/conf/nginx.conf'
        if not os.path.exists(nginxconf): return public.returnMsg(False, '只支持nginx服务器');
        # if public.readFile(nginxconf).find('luawaf.conf') == -1: return public.returnMsg(False,
        # '当前nginx不支持防火墙,请重装nginx');
        data = {}
        data['total'] = self.get_total(None)
        data['webshell'] = self.get_webshell_size()
        del (data['total']['sites'])
        data['drop_ip'] = []
        get.open_btwaf_webshell=1
        data['open'] = self.get_config(get)['open']
        conf = self.get_config(None)
        data['safe_day'] = 0
        if 'start_time' in conf:
            if conf['start_time'] != 0: data['safe_day'] = int((time.time() - conf['start_time']) / 86400)
            session_id = self.__get_md5(time.strftime('%Y-%m-%d'))
            if not os.path.exists('/www/server/btwaf/config.json') or not os.path.exists(
                    '/www/server/btwaf/config.lua'):
                self.__write_config(conf)
            os.chdir('/www/server/panel')
            try:
                from BTPanel import session
                if not session_id in session:
                    self.__write_config(conf)
                    self.__write_site_domains()
                    session[session_id] = 111
            except:

                self.__write_config(conf)
                self.__write_site_domains()

        public.run_thread(self.test_check_zhilist(None))
        # 判断是否存在其他的蜘蛛
        public.run_thread(self.check_zhiz(None))
        public.run_thread(self.db_5000(None))
        return data

    def stop_nps(self, get):
        public.WriteFile("data/btwaf_nps.pl", "")
        return public.returnMsg(True, '关闭成功')

    def get_nps_questions(self):
        try:
            import requests
            api_url = public.GetConfigValue('home')+'/panel/notpro'
            user_info = json.loads(public.ReadFile("{}/data/userInfo.json".format(public.get_panel_path())))
            data = {
                "uid": user_info['uid'],
                "access_key": user_info['access_key'],
                "serverid": user_info['serverid'],
                "product_type": 1
            }

            result = requests.post(api_url, data=data, timeout=10).json()
            if result['res']:
                public.WriteFile('data/get_nps_questions.json', json.dumps(result['res']))
        except:
            public.WriteFile('data/get_nps_questions.json', json.dumps([{
                "id": "NKORxSVqUMjc0YjczNTUyMDFioPLiIoT",
                "question": "当初购买防火墙是解决什么问题？什么事件触发的？",
                "hint": "如：购买时是想预防网站以后被攻击。",
                "required": 1
            }, {
                "id": "dFMoTKffBMmM0YjczNTUyMDM0HugtbUY",
                "question": "您在使用防火墙过程中出现最多的问题是什么？",
                "hint": "如：开启后还是被入侵，然后后续怎么去处理？",
                "required": 1
            }, {
                "id": "dnWeQbiHJMmI4YjczNTUyMDJhurmpsfs",
                "question": "谈谈您对防火墙的建议。",
                "hint": "如：我希望防火墙能防御多台服务器。天马行空，说说您的想法。",
                "required": 1
            }]))

    def get_questions(self, get):
        if os.path.exists('data/get_nps_questions.json'):
            try:
                result = json.loads(public.ReadFile('data/get_nps_questions.json'))
            except:
                result = [{
                    "id": "NKORxSVqUMjc0YjczNTUyMDFioPLiIoT",
                    "question": "当初购买防火墙是解决什么问题？什么事件触发的？",
                    "hint": "如：购买时是想预防网站以后被攻击。",
                    "required": 1
                }, {
                    "id": "dFMoTKffBMmM0YjczNTUyMDM0HugtbUY",
                    "question": "您在使用防火墙过程中出现最多的问题是什么？",
                    "hint": "如：开启后还是被入侵，然后后续怎么去处理？",
                    "required": 1
                }, {
                    "id": "dnWeQbiHJMmI4YjczNTUyMDJhurmpsfs",
                    "question": "谈谈您对防火墙的建议。",
                    "hint": "如：我希望防火墙能防御多台服务器。天马行空，说说您的想法。",
                    "required": 1
                }]

        return public.returnMsg(True, result)

    def get_nps(self, get):
        data = {}
        conf = self.get_config(None)
        data['safe_day'] = 0
        if conf['start_time'] != 0: data['safe_day'] = int((time.time() - conf['start_time']) / 86400)
        if not os.path.exists("data/btwaf_nps.pl"):
            # 如果安全运行天数大于5天 并且没有没有填写过nps的信息
            data['nps'] = False
            public.run_thread(self.get_nps_questions, ())
            if os.path.exists("data/btwaf_nps_count.pl"):
                # 读取一下次数
                count = public.ReadFile("data/btwaf_nps_count.pl")
                if count:
                    count = int(count)
                    public.WriteFile("data/btwaf_nps_count.pl", str(count + 1))
                    data['nps_count'] = count + 1
            else:
                public.WriteFile("data/btwaf_nps_count.pl", "1")
                data['nps_count'] = 1
        else:
            data['nps'] = True
        return data

    def write_nps(self, get):
        '''
            @name nps 提交
            @param rate 评分
            @param feedback 反馈内容

        '''
        import json, requests
        api_url = public.GetConfigValue('home')+'/panel/notpro'
        user_info = json.loads(public.ReadFile("{}/data/userInfo.json".format(public.get_panel_path())))
        if 'rate' not in get:
            return public.returnMsg(False, "参数错误")
        if 'feedback' not in get:
            get.feedback = ""
        if 'phone_back' not in get:
            get.phone_back = 0
        else:
            if get.phone_back == 1:
                get.phone_back = 1
            else:
                get.phone_back = 0

        if 'questions' not in get:
            return public.returnMsg(False, "参数错误")

        try:
            get.questions = json.loads(get.questions)
        except:
            return public.returnMsg(False, "参数错误")

        data = {
            "uid": user_info['uid'],
            "access_key": user_info['access_key'],
            "serverid": user_info['serverid'],
            "product_type": 1,
            "rate": get.rate,
            "feedback": get.feedback,
            "phone_back": get.phone_back,
            "questions": json.dumps(get.questions)
        }
        try:
            requests.post(api_url, data=data, timeout=10).json()
            public.WriteFile("data/btwaf_nps.pl", "1")
        except:
            pass
        return public.returnMsg(True, "提交成功")

    # 取当站点前运行目录
    def GetSiteRunPath(self, id):
        siteName = public.M('sites').where('id=?', (id,)).getField('name');
        sitePath = public.M('sites').where('id=?', (id,)).getField('path');
        path = sitePath;
        if public.get_webserver() == 'nginx':
            filename = '/www/server/panel/vhost/nginx/' + siteName + '.conf'
            if os.path.exists(filename):
                conf = public.readFile(filename)
                rep = '\s*root\s*(.+);'
                tmp1 = re.search(rep, conf)
                if tmp1: path = tmp1.groups()[0];
        runPath = ''
        if sitePath == path:
            pass
        else:
            runPath = path.replace(sitePath, '');
        if runPath == '/':
            return ''
        return runPath

    def __write_site_domains(self):
        sites = public.M('sites').field('name,id,path').select();
        my_domains = []
        for my_site in sites:
            tmp = {}
            tmp['name'] = my_site['name']
            tmp['path'] = my_site['path'] + self.GetSiteRunPath(my_site['id'])
            count = 0
            # tmp2 = []
            # if os.path.exists(self.__path + '/cms.json'):
            #     retc = json.loads(public.ReadFile(self.__path + 'cms.json'))
            #     self.__cms_list = retc
            # for i in self.__cms_list:
            #     for i2 in self.__cms_list[i]:
            #         if os.path.exists(my_site['path'] + str(i2)):
            #             count += 1
            #             if count >= 2:
            #                 count = 0
            #                 tmp['cms'] = 0
            #                 break
            # if not 'cms' in tmp:
            #     tmp['cms'] = 0
            tmp_domains = public.M('domain').where('pid=?', (my_site['id'],)).field('name').select()
            tmp['domains'] = []
            for domain in tmp_domains:
                tmp['domains'].append(domain['name'])
            binding_domains = public.M('binding').where('pid=?', (my_site['id'],)).field('domain').select()
            for domain in binding_domains:
                tmp['domains'].append(domain['domain'])
            my_domains.append(tmp)
            # if os.path.exists(self.__path + '/domains2.json'):
            #     try:
            #         ret = json.loads(public.ReadFile(self.__path + '/domains2.json'))
            #     except:
            #         ret = []
            #     if not tmp in ret:
            #         for i in ret:
            #             if i["name"] == tmp["name"]:
            #                 # if i["cms"] == tmp["cms"]:
            #                 #     i["domains"] = tmp["domains"]
            #                 #     i["path"] = tmp["path"]
            #                 # else:
            #                     if 'is_chekc' in i:
            #                         i["domains"] = tmp["domains"]
            #                         i["path"] = tmp["path"]
            #                     else:
            #                         #i["cms"] = tmp["cms"]
            #                         i["domains"] = tmp["domains"]
            #                         i["path"] = tmp["path"]
            #         else:
            #             count = 0
            #             if not tmp in ret:
            #                 for i in ret:
            #                     if i["name"] == tmp["name"]:
            #                         count = 1
            #                 if not count == 1:
            #                     ret.append(tmp)
            # public.writeFile(self.__path + '/domains2.json', json.dumps(ret))
        # if not os.path.exists(self.__path + '/domains2.json'):
        #     public.writeFile(self.__path + '/domains2.json', json.dumps(my_domains))
        public.writeFile(self.__path + '/domains.json', json.dumps(my_domains))
        # public.writeFile(self.__path + '/domains.lua', 'return '+self.__to_lua_table.makeLuaTable(my_domains))
        return my_domains

    def sync_cnlist(self, get):
        # if not get:
        #     self.get_config(None)
        #     self.get_site_config(None)
        # rcnlist = public.httpGet(public.get_url() + '/cnlist2.json')
        # if not rcnlist: return public.returnMsg(False, '连接云端失败')
        # cloudList = json.loads(rcnlist)
        # cnlist = self.__get_rule('cn')
        # n = 0
        # for ipd in cloudList:
        #     if ipd in cnlist: continue;
        #     cnlist.append(ipd)
        #     n += 1
        # self.__write_rule('cn', cnlist)
        # print('同步成功，本次共增加 ' + str(n) + ' 个IP段')
        if get: return public.returnMsg(True, '同步成功!')

    def get_python_dir(self):
        if os.path.exists('/www/server/panel/pyenv/bin/python'):
            return '/www/server/panel/pyenv/bin/python'
        if os.path.exists('/usr/bin/python'):
            return '/usr/bin/python'
        else:
            return 'python'

    # # 设置自动同步
    def webshell_check(self):

        id = public.M('crontab').where('name=?', (u'Nginx防火墙木马查杀进程请勿删除',)).count()
        if id>0:return False
        import crontab
        data = {}
        data['name'] = u'Nginx防火墙木马查杀进程请勿删除'
        data['type'] = 'minute-n'
        data['where1'] = '1'
        data['sBody'] = self.get_python_dir() + ' /www/server/panel/plugin/btwaf/webshell_check.py'
        data['backupTo'] = ''
        data['sType'] = 'toShell'
        data['hour'] = ''
        data['minute'] = ''
        data['week'] = ''
        data['sName'] = ''
        data['urladdress'] = ''
        data['save'] = ''
        crontab.crontab().AddCrontab(data)
        return True

    def __get_rule(self, ruleName):
        path = self.__path + 'rule/' + ruleName + '.json';
        rules = public.readFile(path)
        if not rules: return False
        return json.loads(rules)

    def __write_rule(self, ruleName, rule):
        path = self.__path + 'rule/' + ruleName + '.json';
        public.writeFile(path, json.dumps(rule))
        # public.writeFile(self.__path + 'rule/' + ruleName + '.lua','return '+self.__to_lua_table.makeLuaTable((rule)))
        public.serviceReload();

    def __check_site(self, site_config):
        sites = public.M('sites').field('name').select();
        if type(sites) != list: return;
        siteNames = []
        n = 0
        for siteInfo in sites:
            siteNames.append(siteInfo['name'])
            if siteInfo['name'] in site_config: continue
            site_config[siteInfo['name']] = self.__get_site_conf()
            n += 1
        old_site_config = site_config.copy()
        spider = [{
            "id": 1,
            "name": "百度",
            "return": 444,
            "status": True
        }, {
            "id": 2,
            "name": "Google",
            "return": 444,
            "status": True
        }, {
            "id": 3,
            "name": "360",
            "return": 444,
            "status": True
        }, {
            "id": 4,
            "name": "搜狗",
            "return": 444,
            "status": True
        }, {
            "id": 5,
            "name": "雅虎",
            "return": 444,
            "status": True
        }, {
            "id": 6,
            "name": "必应",
            "return": 444,
            "status": True
        }, {
            "id": 7,
            "name": "头条",
            "return": 444,
            "status": True
        }]
        for sn in site_config.keys():
            if sn in siteNames:
                if not 'cdn_baidu' in site_config[sn]:
                    site_config[sn]['cdn_baidu'] = False
                    n += 1
                site_config[sn]['site_id'] = public.M('sites').where('name=?', (sn,)).field('id').getField('id')
                # 'disable_upload_ext': ['php', 'jsp', 'user.ini', 'htaccess'],
                if not 'sql_injection' in site_config[sn]:
                    site_config[sn]['sql_injection'] = {"status":403,"reqfile":"get.html","open": True, "post_sql": True, "get_sql": True, "mode": "high"}
                    n += 1
                if not 'xss_injection' in site_config[sn]:
                    site_config[sn]['xss_injection'] = {"status":403,"reqfile":"get.html","open": True, "post_xss": True, "get_xss": True, "mode": "high"}
                    n += 1
                if not 'file_upload' in site_config[sn]:
                    site_config[sn]['file_upload'] = {"status":444,"reqfile":"get.html","open": True, "mode": "high", "from-data": True}
                    n += 1

                if not 'nday' in site_config[sn]:
                    site_config[sn]['nday'] = True
                    n += 1
                if not 'other_rule' in site_config[sn]:
                    site_config[sn]['other_rule'] = {"status": 444, "reqfile": "get.html", "open": True, "mode": "high"}
                    n += 1
                if not 'cc_type_status' in site_config[sn]:
                    site_config[sn]['cc_type_status'] = 2
                    n += 1
                if not 'spider' in site_config[sn]:
                    site_config[sn]['spider'] = spider
                    n += 1
                if not 'spider_status' in site_config[sn]:
                    site_config[sn]['spider_status'] = True
                    n += 1
                if 'php_version' in site_config[sn] or not 'php_version' in site_config[sn]:
                    try:
                        import panelSite
                        panelSite = panelSite.panelSite()
                        get = mobj()
                        get.siteName = sn
                        data = panelSite.GetSitePHPVersion(get)
                        if data["phpversion"] == "00":
                            site_config[sn]['php_version'] = "php"
                        else:
                            site_config[sn]['php_version'] = "/www/server/php/{}/bin/php".format(data["phpversion"])
                    except:
                        site_config[sn]['php_version'] = "php"
                if 'php' in site_config[sn] or not 'php' in site_config[sn]:
                    try:
                        import panelSite
                        panelSite = panelSite.panelSite()
                        get = mobj()
                        get.siteName = sn
                        data = panelSite.GetSitePHPVersion(get)
                        if data["phpversion"] == "00":
                            site_config[sn]['php_version'] = 7
                        else:
                            if data["phpversion"][0]=="5":
                                site_config[sn]['php']=5
                            elif data["phpversion"][0]=="7":
                                site_config[sn]['php']=7
                            else:
                                site_config[sn]['php']=8
                    except:
                        site_config[sn]['php'] = 5

                if site_config[sn]['cc'] and not 'countrys' in site_config[sn]['cc']:
                    site_config[sn]['cc']['countrys'] = {}
                    n += 1
                if not 'cc_automatic' in site_config[sn]:
                    site_config[sn]['cc_automatic'] = False
                    n += 1
                if not 'cc_time' in site_config[sn]:
                    site_config[sn]['cc_time'] = 60
                    n += 1

                if not 'cc_retry_cycle' in site_config[sn]:
                    site_config[sn]['cc_retry_cycle'] = 600
                    n += 1

                if not 'drop_china' in site_config[sn]:
                    site_config[sn]['drop_china'] = False
                    n += 1
                if not 'post_is_sql' in site_config[sn]:
                    site_config[sn]['post_is_sql'] = True
                    n += 1
                if not 'post_is_xss' in site_config[sn]:
                    site_config[sn]['post_is_xss'] = True
                    n += 1
                if not 'post_is_xss_count' in site_config[sn]:
                    site_config[sn]['post_is_xss_count'] = 1
                    n += 1
                if not 'get_is_xss' in site_config[sn]:
                    site_config[sn]['get_is_xss'] = True
                    n += 1
                if not 'get_is_sql' in site_config[sn]:
                    site_config[sn]['get_is_sql'] = True
                    n += 1
                if not 'retry_cycle' in site_config[sn]:
                    site_config[sn]['retry_cycle'] = 60
                    n += 1
                if not 'disable_php_path' in site_config[sn]:
                    site_config[sn]['disable_php_path'] = ['^/cache/', '^/config/', '^/runtime/', '^/application/',
                                                           '^/temp/', '^/logs/', '^/log/']
                    n += 1
                else:
                    n += 1
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
        return tmp;

    def __get_site_conf(self):
        if not self.__config: self.__config = self.get_config(None)
        conf = {
            'open': True,
            'project': '',
            'log': True,
            'cdn': False,
            'cdn_header': ['x-forwarded-for', 'x-real-ip', 'x-forwarded', 'forwarded-for', 'forwarded',
                           'true-client-ip', 'client-ip', 'ali-cdn-real-ip', 'cdn-src-ip', 'cdn-real-ip',
                           'cf-connecting-ip', 'x-cluster-client-ip', 'wl-proxy-client-ip', 'proxy-client-ip',
                           'true-client-ip'],
            'retry': self.__config['retry'],
            'retry_cycle': self.__config['retry_cycle'],
            'retry_time': self.__config['retry_time'],
            'disable_php_path': ['^/cache/', '^/config/', '^/runtime/', '^/application/', '^/temp/', '^/logs/',
                                 '^/log/'],
            'disable_path': [],
            'disable_ext': ['sql', 'bak', 'swp'],
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
                'cc_increase_type': 'js',
                'endtime': self.__config['cc']['endtime']
            },
            'get': self.__config['get']['open'],
            'cc_mode': self.__config['cc_mode'],
            'post': self.__config['post']['open'],
            'cookie': self.__config['cookie']['open'],
            'user-agent': self.__config['user-agent']['open'],
            'scan': self.__config['scan']['open'],
            'body_character_string': [],
            'body_intercept': [],
            'increase_wu_heng': self.__config['increase_wu_heng'],
            'cc_uri_white': [],
            'get_is_sql': True,
            'get_is_xss': True,
            'post_is_sql': True,
            'post_is_xss': True,
            'uri_find': [],
            'drop_abroad': False,
            'drop_china': False
        }
        return conf

    def return_rule(self, yun_rule, local_rule):
        for i in local_rule:
            if not i[-1]:
                for i2 in yun_rule:
                    if i2 not in local_rule:
                        local_rule.append(i2)
        return local_rule

    def sync_rule(self, get):
        ret = self.get_cms_list()
        if not ret: return public.returnMsg(False, '连接云端失败')
        public.writeFile(self.__path + '/cms.json', ret)
        for i in self.__rule_path:
            arg = i.split('.')[0]
            rcnlist = public.httpGet(public.get_url() + '/btwaf_rule/httpd/rule/' + i)
            if not rcnlist: return public.returnMsg(False, '连接云端失败')
            yun_args_rule = json.loads(rcnlist)
            args_rule = self.__get_rule(arg)
            ret = self.return_rule(yun_args_rule, args_rule)
            self.__write_rule(arg, ret)

        public.ExecShell("wget -O /tmp/cms.zip %s/btwaf_rule/httpd/cms.zip" % public.get_url())
        if os.path.exists('/tmp/cms.zip'):
            public.ExecShell("mv /www/server/btwaf/cms/ /home && unzip cms.zip -d /www/server/btwaf")
            if not os.path.exists("/www/server/btwaf/cms/weiqin_post.json"):
                public.ExecShell("rm -rf /www/server/btwaf/cms/ &&  mv /home/cms/ /www/server/btwaf")
            os.remove("/tmp/cms.zip")
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

    def __remove_log_file(self, siteName):
        public.ExecShell('/www/wwwlogs/btwaf/' + siteName + '_*.log')
        total = json.loads(public.readFile(self.__path + 'total.json'))
        if siteName in total['sites']:
            del (total['sites'][siteName])
            self.__write_total(total)
        return True

    def __write_total(self, total):
        return public.writeFile(self.__path + 'total.json', json.dumps(total))

    def __write_config(self, config):
        # public.writeFile(self.__path + 'config.lua', 'return '+self.__to_lua_table.makeLuaTable(config))
        public.writeFile(self.__path + 'config.json', json.dumps(config))
        public.serviceReload()

    def __write_site_config(self, site_config):
        # public.writeFile(self.__path + 'site.lua', 'return '+self.__to_lua_table.makeLuaTable(site_config))
        public.writeFile(self.__path + 'site.json', json.dumps(site_config))
        public.serviceReload()

    def __write_log(self, msg):
        public.WriteLog('网站防火墙', msg)

    def __check_cjson(self):
        cjson = '/usr/local/lib/lua/5.1/cjson.so'
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
/etc/init.d/nginx reload
'''
        public.writeFile('/root/install_cjson.sh', c)
        public.ExecShell('cd /root && bash install_cjson.sh')
        return True

    # 报警日志
    def get_log_send(self, get):
        import page
        page = page.Page()
        count = public.M('logs').where('type=?', (u'WAF防火墙消息通知',)).count()
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
        data['data'] = public.M('logs').where('type=?', (u'WAF防火墙消息通知',)).order('id desc').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).field('log,addtime').select()
        return data

    '''报警开关'''

    def get_send_status(self, get):
        config = self.get_config(None)
        if not public.M('send_settings').where('name=?', ('Nginx防火墙',)).count():
            if config['send_to'] != 'ERROR':
                config['send_to'] = 'ERROR'
                self.__write_config(config)
            return public.returnMsg(False, {"open": False, 'to_mail': False})
        data = public.M('send_settings').where('name=?', ('Nginx防火墙',)).field(
            'id,name,type,path,send_type,inser_time,last_time,time_frame').select()
        data = data[0]
        if data['send_type'] == 'mail':
            if config['send_to'] != 'mail':
                config['send_to'] = 'mail'
                self.__write_config(config)
            return public.returnMsg(True, {"open": True, "to_mail": "mail"})
        elif data['send_type'] == 'dingding':
            if config['send_to'] != 'dingding':
                config['send_to'] = 'dingding'
                self.__write_config(config)
            return public.returnMsg(True, {"open": True, "to_mail": "dingding"})
        else:
            if config['send_to'] != 'ERROR':
                config['send_to'] = 'ERROR'
                self.__write_config(config)
            return public.returnMsg(False, {"open": False, 'to_mail': False})

    '''报警设置'''

    def set_mail_to(self, get):
        config = self.get_config(None)
        config['send_to'] = 'mail'
        self.__write_config(config)
        if not public.M('send_settings').where('name=?', ('btwaf',)).count():
            self.insert_settings('btwaf', 'python_script', '/www/server/panel/plugin/btwaf/send.py', 'weixin', 60)
            self.__write_log('开启成功邮件告警成功')
            return 2
        return public.M('send_settings').where('name=?', ('btwaf',)).select()
        #
        #     return public.returnMsg(True, '开启成功')
        # else:
        #     data = public.M('send_settings').where('name=?', ('Nginx防火墙',)).field(
        #         'id,name,type,path,send_type,inser_time,last_time,time_frame').select()
        #     data = data[0]
        #     public.M('send_settings').where("id=?", (data['id'])).update({"send_type": "mail"})
        #     self.__write_log('开启成功邮件告警成功')
        #     return public.returnMsg(True, '开启成功')

    def stop_mail_send(self, get):
        config = self.get_config(None)
        config['send_to'] = 'ERROR'
        self.__write_config(config)
        public.M('send_settings').where('name=?', ('btwaf',)).delete()
        return public.returnMsg(True, '关闭成功')

    '''钉钉'''

    def set_dingding(self, get):
        config = self.get_config(None)
        config['send_to'] = 'dingding'
        self.__write_config(config)
        if not public.M('send_settings').where('name=?', ('Nginx防火墙',)).count():
            self.insert_settings('Nginx防火墙', 'json', '/dev/shm/btwaf.json', 'dingding', 60)
            self.__write_log('开启成功dingding告警成功')
            return public.returnMsg(True, '开启成功')
        else:
            data = public.M('send_settings').where('name=?', ('Nginx防火墙',)).field(
                'id,name,type,path,send_type,inser_time,last_time,time_frame').select()
            data = data[0]
            public.M('send_settings').where("id=?", (data['id'])).update({"send_type": "dingding"})
            self.__write_log('开启成功dingding告警成功')
            return public.returnMsg(True, '开启成功')

    def ip2long(self, ip):
        ips = ip.split('.')
        if len(ips) != 4: return 0
        iplong = 2 ** 24 * int(ips[0]) + 2 ** 16 * int(ips[1]) + 2 ** 8 * int(ips[2]) + int(ips[3])
        return iplong

    def long2ip(self, long):
        floor_list = []
        yushu = long
        for i in reversed(range(4)):  # 3,2,1,0
            res = divmod(yushu, 256 ** i)
            floor_list.append(str(res[0]))
            yushu = res[1]
        return '.'.join(floor_list)

    def get_safe_logs2(self, get):
        try:
            import cgi
            pythonV = sys.version_info[0]
            if 'drop_ip' in get:
                path = '/www/server/btwaf/drop_ip.log'
                num = 10000
            else:
                path = '/www/wwwlogs/btwaf/' + get.siteName + '_' + get.toDate + '.log'
                num = 1000000
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
                                        if i == 7:
                                            tmp_data[i] = str(tmp_data[i]).replace('&amp;', '&').replace('&lt;',
                                                                                                         '<').replace(
                                                '&gt;', '>')
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
                drop_iplist = self.get_waf_drop_ip(None)
                stime = time.time()
                setss = []
                for i in range(len(data)):
                    if (float(stime) - float(data[i][0])) < float(data[i][4]):
                        setss.append(data[i][1])
                        data[i].append(data[i][1] in drop_iplist)
                    else:
                        data[i].append(False)
        except:
            data = []
            return public.get_error_info()
        return data

    def import_ip_data(self, get):
        ret = []
        try:

            get.drop_ip = 1
            iplist = self.get_safe_logs2(get)
            for i in iplist:
                if i[-1]:
                    ret.append(i[1])

            return ret
        except:
            return ret

    # add_ip_black
    def import_ip_black(self, get):
        try:
            get.drop_ip = 1
            iplist = self.get_safe_logs2(get)
            for i in iplist:
                if i[-1]:
                    get.start_ip = i[1]
                    get.end_ip = i[1]
                    self.add_ip_black(get)
            return public.returnMsg(True, '导入成功')
        except:
            return public.returnMsg(False, '导入失败')

    def down_site_log(self, get):
        try:
            rows = []
            if get.siteName == 'all':
                site_list = []
                [site_list.append(x['siteName']) for x in self.get_site_config(get)]
                for i3 in site_list:
                    get.siteName = i3
                    list = self.get_logs_list(get)
                    for i in list:
                        get.toDate = i
                        data = self.get_safe_logs2(get)
                        if not data: continue
                        for i2 in data:
                            try:
                                rule = i2[6].split('&amp;gt;&amp;gt;')[0]
                                user_post = i2[6].split('&amp;gt;&amp;gt;')[1]
                                rows.append([get.siteName, i2[0], i2[1], i2[2], i2[3], i2[4], rule, user_post, i2[7]])
                            except:
                                continue
                with open('/www/server/btwaf/test.json', 'w')as f:
                    f.write('格式:网站名称,时间，攻击者IP,请求类型,请求的URL,攻击者UA,触发的规则,传入值,具体的HTTP包详情\n')
                    f.write(json.dumps(rows))
                return public.returnMsg(True, '导出成功')
            else:
                if get.toDate == 'all':
                    list = self.get_logs_list(get)
                    for i in list:
                        get.toDate = i
                        data = self.get_safe_logs2(get)
                        if not data: continue
                        for i2 in data:
                            try:
                                rule = i2[6].split('&amp;gt;&amp;gt;')[0]
                                user_post = i2[6].split('&amp;gt;&amp;gt;')[1]
                                rows.append([get.siteName, i2[0], i2[1], i2[2], i2[3], i2[4], rule, user_post, i2[7]])
                            except:
                                continue
                    with open('/www/server/btwaf/test.json', 'w')as f:
                        f.write('格式:网站名称,时间，攻击者IP,请求类型,请求的URL,攻击者UA,触发的规则,传入值,具体的HTTP包详情\n')
                        f.write(json.dumps(rows))
                    return public.returnMsg(True, '导出成功')
                else:
                    path = '/www/wwwlogs/btwaf/' + get.siteName + '_' + get.toDate + '.log'
                    if not os.path.exists(path): return public.returnMsg(False, '导出失败,日志文件不存在')
                    data = self.get_safe_logs2(get)
                    if not data: return public.returnMsg(False, '导出失败,日志文件不存在')
                    for i2 in data:
                        try:
                            rule = i2[6].split('&amp;gt;&amp;gt;')[0]
                            user_post = i2[6].split('&amp;gt;&amp;gt;')[1]
                            rows.append([get.siteName, i2[0], i2[1], i2[2], i2[3], i2[4], rule, user_post, i2[7]])
                        except:
                            continue
                    with open('/www/server/btwaf/test.json', 'w')as f:
                        f.write('格式:网站名称,时间，攻击者IP,请求类型,请求的URL,攻击者UA,触发的规则,传入值,具体的HTTP包详情\n')
                        f.write(json.dumps(rows))
                    return public.returnMsg(True, '导出成功')
        except:
            return public.returnMsg(False, '导出失败')

    def empty_data(self, get):
        type_list = ['ua_white', 'ua_black', 'ip_white', 'ip_black', 'url_white', 'url_black', 'uri_find']
        stype = get.type
        if not stype in type_list: return public.returnMsg(False, '清空失败,错误的选项')
        if stype == 'ua_white':
            config = self.get_config(None)
            config['ua_white'] = []
            self.__write_config(config)
        elif stype == 'ua_black':
            config = self.get_config(None)
            config['ua_black'] = []
            self.__write_config(config)
        elif stype == 'ip_white':
            datas = self.get_cn_list('ip_white')
            if ['127.0.0.1', '127.0.0.255'] in datas:
                self.__write_rule('ip_white', [[2130706433, 2130706687]])
            else:
                self.__write_rule('ip_white', [])
        elif stype == 'ip_black':
            for i in self.get_cn_list('ip_black'):
                self.bt_ip_filter("-,%s-%s,86400" % (i[0], i[1]))

            self.__write_rule('ip_black', [])
        elif stype == 'url_white':
            self.__write_rule('url_white', [])
        elif stype == 'url_black':
            self.__write_rule('url_black', [])
        elif stype == 'uri_find':
            config = self.get_config(None)
            config['uri_find'] = []
            self.__write_config(config)
        return public.returnMsg(True, '清空成功')

    # 查询站点跟目录
    def getdir2(self, file_dir):
        for root, dirs, files in os.walk(file_dir):
            return files

    def remove_log(self, get):
        '''
        get.safe_logs  #封锁历史日志   例如:safe_logs=1
        get.site_logs  # 站点的日志文件 site_logs=["192.168.1.72","www.bt.cn"]
        get.site_all  # 清理所有站点日志
        :param get:
        :return:
        '''
        if not 'safe_logs' in get: return public.returnMsg(False, '没有safe_logs参数')
        if not 'site_logs' in get: return public.returnMsg(False, '没有site_logs参数')
        if not 'site_all' in get: return public.returnMsg(False, '没有site_all参数')
        try:
            site_list = json.loads(get.site_logs)
        except:
            return public.returnMsg(True, '请输入正确的网站列表')
        if get.safe_logs == '1':
            public.ExecShell("echo ''>/www/server/btwaf/drop_ip.log")
            if os.path.exists("/www/server/btwaf/totla_db/totla_db.db"):
                path_list = self.M2('blocking_ip').where("type=?", ("POST")).field('http_log').select()
                for i in path_list:
                    if os.path.exists(i['http_log']):
                        os.remove(i['http_log'])
                self.M2('blocking_ip').delete()

        if get.site_all == '1':
            if os.path.exists("/www/server/btwaf/totla_db/totla_db.db"):

                path_list = self.M2('totla_log').where("type=?", ("POST")).field('http_log').select()
                if type(path_list) != "str":
                    for i in path_list:
                        if os.path.exists(i['http_log']):
                            os.remove(i['http_log'])
                    self.M2('totla_log').delete()
            public.ExecShell("rm -rf /www/wwwlogs/btwaf/*.log")
            # 清理所有网站统计
            public.WriteFile("/www/server/btwaf/total.json",
                             {"rules": {"user_agent": 0, "cookie": 0, "post": 0, "args": 0, "url": 0, "cc": 0},
                              "sites": {}, "total": 0})
        # public.WriteFile("/www/server/btwaf/site.json",{})

        else:
            ret = []
            try:
                site_info = json.loads(public.ReadFile("/www/server/btwaf/total.json"))
            except:
                site_info = {}
            if len(site_list) >= 1:
                log_data = self.getdir2('/www/wwwlogs/btwaf/')
                for i in site_list:
                    if not i in site_info["sites"]: continue
                    if site_info["sites"][i]:
                        for i2 in site_info["sites"][i]:
                            # return site_info["sites"][i]
                            site_info["total"] -= site_info["sites"][i][i2]
                            site_info["rules"][i2] -= site_info["sites"][i][i2]
                            site_info["sites"][i][i2] = 0

                    if os.path.exists("/www/server/btwaf/totla_db/totla_db.db"):
                        path_list = self.M2('totla_log').where("type=? and server_name=?", ("POST", i)).field(
                            'http_log').select()
                        for i3 in path_list:
                            if os.path.exists(i3['http_log']):
                                os.remove(i3['http_log'])
                        self.M2('totla_log').where("server_name=?", (i)).delete()
                    for i2 in log_data:
                        if re.search('^' + i, i2):
                            ret.append(i2)
                if len(ret) >= 1:
                    for i3 in ret:
                        os.remove('/www/wwwlogs/btwaf/' + i3)
            public.WriteFile("/www/server/btwaf/total.json", json.dumps(site_info))
        return public.returnMsg(True, '清理完成')

    # 站点分页
    def get_site_config3(self, get):
        try:
            site_config = json.loads(public.readFile(self.__path + 'site.json'))
        except:
            public.WriteFile(self.__path + 'site.json', json.dumps({}))
            self.__write_site_domains()
            site_config = json.loads(public.readFile(self.__path + 'site.json'))
        if not os.path.exists(self.__path + '/domains.lua'):
            self.__write_site_domains()
        data = self.__check_site(site_config)
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

        if not 'limit' in get:
            get.limit = 12
        limit = int(get.limit)
        if not 'p' in get:
            get.p = 1
        p = int(get.p)
        count = len(data)
        result = []
        if count < limit:
            result = data
        if count < (p * limit):
            result = data[(p - 1) * limit:count]
        else:
            result = data[(p - 1) * limit:(p * limit)]
        import page
        page = page.Page()
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
        data['data'] = result
        return data

    # 批量设置站点
    def batch_site_all(self, get):
        '''
        siteNames
        is_all=1 | 0
        obj
        is_status
        '''
        siteNames = get.siteNames.strip()
        is_all = True if get.is_all.strip() == '1' else False
        obj = get.obj.strip()
        obj_list = ['cc', 'get', 'post', 'cookie', 'user-agent', 'drop_abroad', 'cdn', 'open', 'drop_china']
        is_status = get.is_status.strip()
        is_status_list = ['true', 'false']
        if not is_status in is_status_list: return public.returnMsg(False, '状态值不对')
        is_status = True if is_status == 'true' else False

        if not obj in obj_list: return public.returnMsg(False, '不支持该操作')
        if is_all:
            site_config = self.get_site_config(None)
            for i in site_config:
                if type(site_config[i][obj]) != bool:
                    if site_config[i][obj]['open']:
                        site_config[i][obj]['open'] = is_status
                    else:
                        site_config[i][obj]['open'] = is_status
                else:
                    if site_config[i][obj]:
                        site_config[i][obj] = is_status
                    else:
                        site_config[i][obj] = is_status
            self.__write_site_config(site_config)
            return public.returnMsg(True, '设置成功!')
        else:
            try:
                siteName = json.loads(siteNames)
            except:
                return public.returnMsg(True, '解析错误网站列表')
            site_config = self.get_site_config(None)
            for i in site_config:
                for i2 in siteName:
                    if i2 == i:
                        if type(site_config[i][obj]) != bool:
                            if site_config[i][obj]['open']:
                                site_config[i][obj]['open'] = is_status
                            else:
                                site_config[i][obj]['open'] = is_status
                        else:
                            if site_config[i][obj]:
                                site_config[i][obj] = is_status
                            else:
                                site_config[i][obj] = is_status
                self.__write_site_config(site_config)

            # return public.returnMsg(True, '设置成功!')
            return {"success": siteName, "status": True, "msg": "设置成功"}

    # 测试按钮
    def test_waf(self, get):
        '''
        无参数。增加一条攻击
        '''
        try:
            import requests
            ret = requests.get(get.url, timeout=3)
            html = ret.content
            html_doc = str(html, 'utf-8')
            return public.returnMsg(True, html_doc)
        except:
            return public.returnMsg(False, '访问失败!')

    def return_is_site(self, get):
        data = self.get_site_config(get)
        result = []
        if len(data) >= 1:
            for i in data:
                if len(result) >= 6: break
                result.append('http://' + i['siteName'] + '/?id=1\'union select user(),1,3--')
        return result

    def __write_rule_dddd(self, rule, data):
        return public.writeFile('/www/server/btwaf/rule/' + rule, json.dumps(data))

    # 恢复默认配置
    def set_default_settings(self, get):
        '''
        无参数,恢复默认配置
        '''
        return self.restore_default_configuration(get)

    # 备份防火墙配置
    def bckup_sesings(self, get):
        key = 'bt_waf__2021_yes_day'
        backup_data = {}
        config = self.get_config(None)
        # 备份ua黑白名单
        backup_data['ua_white'] = config['ua_white']
        backup_data['ua_black'] = config['ua_black']
        # 备份IP黑白名单
        backup_data['ip_white'] = self.get_cn_list('ip_white')
        backup_data['ip_black'] = self.get_cn_list('ip_black')
        # 备份URL黑白名单
        backup_data['url_white'] = self.__get_rule('url_white')
        backup_data['url_black'] = self.__get_rule('url_black')
        # 备份全局配置其他
        backup_data['sql_injection'] = config['sql_injection']
        backup_data['xss_injection'] = config['xss_injection']
        backup_data['file_upload'] = config['file_upload']
        backup_data['other_rule'] = config['other_rule']

        backup_data['cc_mode'] = config['cc_mode']
        backup_data['cc'] = config['cc']
        backup_data['cc_mode'] = config['cc_mode']
        backup_data['cc_automatic'] = config['cc_automatic']
        backup_data['cc_retry_cycle'] = config['cc_retry_cycle']
        backup_data['cc_time'] = config['cc_time']
        backup_data['cc_mode'] = config['cc_mode']
        backup_data['cookie'] = config['cookie']
        backup_data['drop_abroad'] = config['drop_abroad']
        backup_data['drop_china'] = config['drop_china']
        backup_data['get'] = config['get']
        backup_data['header_len'] = config['header_len']
        backup_data['http_open'] = config['http_open']
        backup_data['method_type'] = config['method_type']
        backup_data['post'] = config['post']
        backup_data['retry_cycle'] = config['retry_cycle']
        backup_data['retry_time'] = config['retry_time']
        backup_data['scan'] = config['scan']
        backup_data['uri_find'] = config['uri_find']
        backup_data['user-agent'] = config['user-agent']
        # backup_data['webshell_open'] = config['webshell_open']
        return public.returnMsg(True, public.aes_encrypt(json.dumps(backup_data), key))

    # 导入防火墙配置
    def import_sesings(self, get):
        key = 'bt_waf__2021_yes_day'
        backup_d = get.backup_data.strip()
        try:
            backup_data = public.aes_decrypt(backup_d, key)
            backup_data = json.loads(backup_data)
        except:
            return public.returnMsg(False, '请输入正确的备份数据')
        config = self.get_config(None)
        # 备份全局配置其他
        config['sql_injection'] = backup_data['sql_injection']
        config['xss_injection'] = backup_data['xss_injection']
        config['file_upload'] = backup_data['file_upload']
        config['other_rule'] = backup_data['other_rule']
        config['cc_mode'] = backup_data['cc_mode']
        config['cc'] = backup_data['cc']
        config['cc_mode'] = backup_data['cc_mode']
        config['cc_automatic'] = backup_data['cc_automatic']
        config['cc_retry_cycle'] = backup_data['cc_retry_cycle']
        config['cc_time'] = backup_data['cc_time']
        config['cc_mode'] = backup_data['cc_mode']
        config['cookie'] = backup_data['cookie']
        config['drop_abroad'] = backup_data['drop_abroad']
        config['drop_china'] = backup_data['drop_china']
        config['get'] = backup_data['get']
        config['header_len'] = backup_data['header_len']
        config['http_open'] = backup_data['http_open']
        config['method_type'] = backup_data['method_type']
        config['post'] = backup_data['post']
        config['retry_cycle'] = backup_data['retry_cycle']
        config['retry_time'] = backup_data['retry_time']
        config['scan'] = backup_data['scan']
        config['uri_find'] = backup_data['uri_find']
        config['user-agent'] = backup_data['user-agent']
        # config['webshell_open'] = backup_data['webshell_open']
        config['ua_white'] = backup_data['ua_white']
        config['ua_black'] = backup_data['ua_black']
        self.__write_config(config)

        # ip黑白名单
        if len(backup_data['ip_white']) > 0:
            get.s_Name = 'ip_white'
            get.pdata = json.dumps(backup_data['ip_white'])
            self.import_data(get)
        if len(backup_data['ip_black']) > 0:
            get.s_Name = 'ip_black'
            get.pdata = json.dumps(backup_data['ip_black'])
            self.import_data(get)

        # url黑白名单
        if len(backup_data['url_white']) > 0:
            get.s_Name = 'url_white'
            get.pdata = json.dumps(backup_data['url_white'])
            self.import_data(get)

        if len(backup_data['url_black']) > 0:
            get.s_Name = 'url_black'
            get.pdata = json.dumps(backup_data['url_black'])
            self.import_data(get)
        public.serviceReload()
        return public.returnMsg(True, '设置成功!')

    # 添加状态码拦截
    def add_static_code_config(self, get):
        code_list = ["201", "202", "203", "300", "301", "303", "304", "308", "400", "401", "402", "403", "404", "406",
                     "408", "413", "415", "416", "500", "501", "502", "503", "505"]
        code_from = get.code_from.strip()
        code_to = get.code_to.strip()
        code_to_list = ["500", "501", "502", "503", "400", "401", "404", "444"]
        if code_from == '200': return public.returnMsg(False, '不允许设置200的返回状态码拦截!')
        if not code_from in code_list: return public.returnMsg(False, '不允许的状态码!')
        if not code_to in code_to_list: return public.returnMsg(False, '不允许的返回状态码!')
        config = self.get_config(get)
        static_code_config = config['static_code_config']
        if code_from in static_code_config:
            return public.returnMsg(False, '已经存在!')
        else:
            config['static_code_config'][code_from] = code_to
            self.__write_config(config)
            return public.returnMsg(True, '添加成功')

    # 修改状态码拦截
    def edit_static_code_config(self, get):
        code_list = ["201", "202", "203", "300", "301", "303", "304", "308", "400", "401", "402", "403", "404", "406",
                     "408", "413", "415", "416", "500", "501", "502", "503", "505"]
        code_from = get.code_from.strip()
        code_to = get.code_to.strip()
        code_to_list = ["500", "501", "502", "503", "400", "401", "404", "444"]
        if code_from == '200': return public.returnMsg(False, '不允许设置200的返回状态码拦截!')
        if not code_from in code_list: return public.returnMsg(False, '不允许的状态码!')
        if not code_to in code_to_list: return public.returnMsg(False, '不允许的返回状态码!')
        config = self.get_config(get)
        static_code_config = config['static_code_config']
        if not code_from in static_code_config:
            return public.returnMsg(False, '不存在!')
        else:
            config['static_code_config'][code_from] = code_to
            self.__write_config(config)
            return public.returnMsg(True, '修改成功')

    # 删除状态码拦截
    def del_static_code_config(self, get):
        code_list = ["201", "202", "203", "300", "301", "303", "304", "308", "400", "401", "402", "403", "404", "406",
                     "408", "413", "415", "416", "500", "501", "502", "503", "505"]
        code_from = get.code_from.strip()
        code_to = get.code_to.strip()
        code_to_list = ["500", "501", "502", "503", "400", "401", "404", "444"]
        if code_from == '200': return public.returnMsg(False, '不允许设置200的返回状态码拦截!')
        if not code_from in code_list: return public.returnMsg(False, '不允许的状态码!')
        if not code_to in code_to_list: return public.returnMsg(False, '不允许的返回状态码!')
        config = self.get_config(get)
        static_code_config = config['static_code_config']
        if code_from in static_code_config:
            del config['static_code_config'][code_from]
            self.__write_config(config)
            return public.returnMsg(True, '删除成功')
        else:
            return public.returnMsg(True, '不存在')

    def is_check_version(self):
        if not os.path.exists('/www/server/btwaf/init.lua'): return False
        init_lua = public.ReadFile('/www/server/btwaf/init.lua')
        if type(init_lua) == bool: return False

        if "require 'maxminddb'" in init_lua:
            return True
        else:
            return False

    def get_safe22(self, get):
        result = {}
        # if self.M3('site_logs').order('id desc').count()==0:return public.returnMsg(False, result)

        import page
        page = page.Page()
        count = self.M3('site_logs').order('id desc').count()
        limit = 1000
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
        data['data'] = self.M3('site_logs').field(
            'time,ip,method,domain,status_code,protocol,uri,user_agent,body_length,referer,request_time').order(
            'id desc').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).select()
        return public.returnMsg(True, data)

    def get_logs(self, get):
        import cgi
        pythonV = sys.version_info[0]
        path = get.path.strip()
        if not os.path.exists(path): return ''
        try:
            import html
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
                                    tmp_data = json.loads(line)
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
                drop_iplist = self.get_waf_drop_ip(None)
                stime = time.time()
                setss = []
                for i in range(len(data)):
                    if (float(stime) - float(data[i][0])) < float(data[i][4]) and not data[i][1] in setss:
                        setss.append(data[i][1])
                        data[i].append(data[i][1] in drop_iplist)
                    else:
                        data[i].append(False)
        except:
            data = []
            return public.get_error_info()
        if len(data) >= 1:
            if (len(data[0]) >= 1):
                return data[0][0].replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace("&quot;",
                                                                                                          "\"")
        return data

    def get_timestamp(self, str):
        timeArray = time.strptime('2021-06-06', "%Y-%m-%d")
        timeStamp = int(time.mktime(timeArray))
        return (timeStamp, timeStamp + 86400)


    def bytpes_to_string(self, data):
        for i in data:
            for key in i.keys():
                i[key] = self.to_str(i[key])

        return data

    def get_safe_logs_sql2(self, get):
        '''
        siteName:网站名称
        start_time:2021-05-06
        end_time:2021-05-07
        p:1  页数
        limit:10
        '''
        if not 'siteName' in get:
            return public.returnMsg(True, "请传递网站名称")
        if not 'limit' in get:
            limit = 10
        else:
            limit = int(get.limit.strip())
        if not 'p' in get:
            p = 10
        else:
            p = int(get.p.strip())
        if not 'start_time' in get:
            start_time = time.strftime("%Y-%m-%d", time.localtime(time.time()))
        else:
            start_time = get.start_time.strip()
        if not 'end_time' in get:
            # end_time = time.strftime("%Y-%m-%d", time.localtime(time.time()))
            end_time = start_time
        else:
            end_time = get.end_time.strip()
        start_time = start_time + ' 00:00:00'
        end_time2 = end_time + ' 23:59:59'
        start_timeStamp = int(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S')))
        end_timeStamp = int(time.mktime(time.strptime(end_time2, '%Y-%m-%d %H:%M:%S')))

        if os.path.exists("/www/server/btwaf/totla_db/totla_db.db"):
            import page
            page = page.Page()
            count = self.M2('totla_log').field('time').where("time>? and time<? and server_name=?", (
                start_timeStamp, end_timeStamp, get.siteName.strip())).order('id desc').count()
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
            data['data'] = []
            data22 = self.M3('totla_log').field(
                'time,time_localtime,server_name,ip,ip_city,ip_country,ip_subdivisions,ip_longitude,ip_latitude,type,uri,user_agent,filter_rule,incoming_value,value_risk,http_log,http_log_path').order(
                'id desc').where("time>? and time<? and server_name=?",
                                 (start_timeStamp, end_timeStamp, get.siteName.strip())).limit(
                str(page.SHIFT) + ',' + str(page.ROW)).select()
            if type(data22) == str: public.returnMsg(True, data)
            try:
                data['data'] = self.bytpes_to_string(data22)
            except:
                pass
            return public.returnMsg(True, data)
        else:
            data = {}
            data['page'] = "<div><span class='Pcurrent'>1</span><span class='Pcount'>共0条</span></div>"
            data['data'] = []
            return public.returnMsg(False, data)

    # 设置经纬度
    def set_server_longitude(self, get):
        latitude = get.latitude.strip()
        longitude = get.longitude.strip()
        is_check_longitude = [latitude, longitude]
        if len(re.findall(r'-?[0-9]*\.*[0-9]+$', longitude)) == 0: return public.returnMsg(False, '经纬度错误')
        if len(re.findall(r'-?[0-9]*\.*[0-9]+$', latitude)) == 0: return public.returnMsg(False, '经纬度错误')
        if os.path.exists('/www/server/panel/data/get_geo2ip.json'):
            data = json.loads(public.ReadFile('/www/server/panel/data/get_geo2ip.json'))
            data['latitude'] = latitude
            data['longitude'] = longitude
            public.WriteFile('/www/server/panel/data/get_geo2ip.json', json.dumps(data))
            return public.returnMsg(True, '设置成功')
        else:
            return public.returnMsg(False, '设置失败')

    # 从外部刷新经纬度
    def get_wai_longitude(self, get):
        import requests
        result = {}
        jsonda = requests.get("http://www.bt.cn/api/panel/get_geo2ip", timeout=3).json()
        result['ip_address'] = jsonda['traits']['ip_address']
        result['latitude'] = jsonda['location']['latitude']
        result['longitude'] = jsonda['location']['longitude']
        public.WriteFile('/www/server/panel/data/get_geo2ip.json', json.dumps(result))
        return public.returnMsg(True, result)

    def get_server_longitude(self, get):
        try:
            if os.path.exists('/www/server/panel/data/get_geo2ip.json'):
                data = json.loads(public.ReadFile('/www/server/panel/data/get_geo2ip.json'))
                return public.returnMsg(True, data)
            else:
                #
                import requests
                result = {}
                user_info = public.get_user_info()
                data={}
                data['ip'] = user_info['address']
                data['uid'] = user_info['uid']
                data["serverid"] = user_info["serverid"]
                jsonda = requests.get("https://www.bt.cn/api/panel/get_ip_info", timeout=3).json()
                result['ip_address'] = data['ip']
                result['latitude'] = jsonda[data['ip']]['latitude']
                result['longitude'] = jsonda[data['ip']]['longitude']
                public.WriteFile('/www/server/panel/data/get_geo2ip.json', json.dumps(result))
                return public.returnMsg(True, result)
        except:
            try:
                import requests
                result = {}
                jsonda = requests.get("http://www.bt.cn/api/panel/get_geo2ip", timeout=3).json()
                result['ip_address'] = jsonda['traits']['ip_address']
                result['latitude'] = jsonda['location']['latitude']
                result['longitude'] = jsonda['location']['longitude']
                public.WriteFile('/www/server/panel/data/get_geo2ip.json', json.dumps(result))
                return public.returnMsg(True, result)
            except:
                return public.returnMsg(False, '')

    def gongji_map(self, get):
        '''
        返回攻击地图
        '''
        if os.path.exists("/www/server/btwaf/totla_db/totla_db.db"):
            map_24_data = self.M2('totla_log').field(
                'ip,ip_country,ip_subdivisions,ip_longitude,ip_latitude').where("time>=?",
                                                                                             int(time.time()) - 86400 * 7).order(
                'id desc').limit("500").select()
            if type(map_24_data) == str: return public.returnMsg(True, [])
            ret = []
            for i in map_24_data:
                if i['ip_country'] == '内网地址': continue
                ret.append(i)

            return public.returnMsg(True, ret)
        return public.returnMsg(True, [])

    '''攻击搜索'''
    '''
        所有网站[前10W条数据分析]
            根据IP搜索
            根据URI进行搜索
            根据UA搜索
            根据时间搜索攻击
        单个网站[5W条数据分析]
            根据IP搜索
            根据URI进行搜索
            根据UA搜索
            根据时间搜索攻击
    '''

    def get_search(self, get):
        '''
        :param get:
            参数is_all 是否查询所有
            参数server_name 当查询所有的时候不需要传递
            参数type  查询的类型 1->ip  2->uri  3->url 4->时间搜索
            参数start_time  end_time --> 类型为4 的时候才传递的时间参数  默认不传递是今天的
            参数serach 类型为1-2-3 的时候需要传递的查询语句
        '''
        if not 'is_all' in get:
            is_all = 0
        else:
            is_all = get.is_all.strip()
        if not os.path.exists("/www/server/btwaf/totla_db/totla_db.db"): return public.returnMsg(False, "无数据库文件")
        if int(is_all) == 1:
            if not 'type' in get: return public.returnMsg(False, "必须传递type参数")
            type = get.type.strip()
            if int(type) == 4:
                if not 'start_time' in get:
                    start_time = time.strftime("%Y-%m-%d", time.localtime(time.time()))
                else:
                    start_time = get.start_time.strip()
                if not 'end_time' in get:
                    end_time = time.strftime("%Y-%m-%d", time.localtime(time.time()))
                else:
                    end_time = get.end_time.strip()
                start_time = start_time + ' 00:00:00'
                end_time2 = end_time + ' 23:59:59'
                start_timeStamp = int(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S')))
                end_timeStamp = int(time.mktime(time.strptime(end_time2, '%Y-%m-%d %H:%M:%S')))
                import page
                page = page.Page()
                count = self.M2('totla_log').field('time').where("time>? and time<?", (
                    start_timeStamp, end_timeStamp)).order('id desc').count()
                info = {}
                info['count'] = count
                info['row'] = 10
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
                data22 = self.M3('totla_log').field(
                    'id,time,time_localtime,server_name,ip,uri,filter_rule').order('id desc').where("time>? and time<?",
                                                                                                    (start_timeStamp,
                                                                                                     end_timeStamp)).limit(
                    str(page.SHIFT) + ',' + str(page.ROW)).select()
                data['data'] = self.bytpes_to_string(data22)
                return public.returnMsg(True, data)
            else:
                if not 'serach' in get: return public.returnMsg(False, "必须传递serach参数")
                serach = get.serach.strip()
                if int(type) == 1:
                    import page
                    page = page.Page()
                    count = self.M2('totla_log').field('time').where("ip=?", serach).order('id desc').count()
                    info = {}
                    info['count'] = count
                    info['row'] = 10
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
                    data22 = self.M3('totla_log').field(
                        'id,time,time_localtime,server_name,ip,uri,filter_rule').order('id desc').where("ip=?",
                                                                                                        serach).limit(
                        str(page.SHIFT) + ',' + str(page.ROW)).select()
                    data['data'] = self.bytpes_to_string(data22)
                    return public.returnMsg(True, data)
                if int(type) == 2:
                    try:
                        result = []
                        '''uri==> /?id=/etc/passwd  代表的是/  为uri'''

                        data_count = self.M2('totla_log').query(
                            "select COUNT(*) from totla_log WHERE uri like '{}?%';".format(serach))
                        if data_count[0]:
                            if data_count[0][0]:
                                count = data_count[0][0]
                            else:
                                count = 0
                        else:
                            count = 0
                        import page
                        page = page.Page()
                        count = count
                        info = {}
                        info['count'] = count
                        info['row'] = 12
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
                        data222 = self.M2('totla_log').query(
                            "select id,time,time_localtime,server_name,ip,uri,filter_rule from totla_log WHERE uri like '{0}?%' limit {1},{2}".format(
                                serach, str(page.SHIFT), str(page.ROW)))
                        if len(data222) > 0:
                            ret = []
                            for i in data222:
                                ret.append(
                                    {"id": i[0], "time": i[1], "time_localtime": i[2], "server_name": i[3], "ip": i[4],
                                     "uri": i[5], "filter_rule": i[6]})
                            data['data'] = ret
                        else:
                            data['data'] = []
                        return public.returnMsg(True, data)
                    except:
                        return {"status": True, "msg": {
                            "page": "<div><span class='Pcurrent'>1</span><span class='Pcount'>共0条</span></div>",
                            "data": []}}
                if int(type) == 3:
                    '''url ==> /?id=/etc/passwd 代表为 /?id=/etc/passwd'''
                    import page
                    page = page.Page()
                    count = self.M2('totla_log').field('time').where("uri=?", serach).order('id desc').count()
                    info = {}
                    info['count'] = count
                    info['row'] = 10
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
                    data22 = self.M3('totla_log').field(
                        'id,time,time_localtime,server_name,ip,uri,filter_rule').order('id desc').where("uri=?",
                                                                                                        serach).limit(
                        str(page.SHIFT) + ',' + str(page.ROW)).select()
                    data['data'] = self.bytpes_to_string(data22)
                    return public.returnMsg(True, data)
                else:
                    return public.returnMsg(False, "参数传递错误")
        else:
            if not 'server_name' in get:
                return public.returnMsg(False, "请选择需要查询的网站名称")
            else:
                server_name = get.server_name.strip()
                if not 'type' in get: return public.returnMsg(False, "必须传递type参数")
                type = get.type.strip()
                if int(type) == 4:
                    if not 'start_time' in get:
                        start_time = time.strftime("%Y-%m-%d", time.localtime(time.time()))
                    else:
                        start_time = get.start_time.strip()
                    if not 'end_time' in get:
                        end_time = time.strftime("%Y-%m-%d", time.localtime(time.time()))
                    else:
                        end_time = get.end_time.strip()
                    start_time = start_time + ' 00:00:00'
                    end_time2 = end_time + ' 23:59:59'
                    start_timeStamp = int(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S')))
                    end_timeStamp = int(time.mktime(time.strptime(end_time2, '%Y-%m-%d %H:%M:%S')))
                    import page
                    page = page.Page()
                    count = self.M2('totla_log').field('time').where("time>? and time<? and server_name=?", (
                        start_timeStamp, end_timeStamp, server_name)).order('id desc').count()
                    info = {}
                    info['count'] = count
                    info['row'] = 10
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
                    data22 = self.M2('totla_log').field(
                        'id,time,time_localtime,server_name,ip,uri,filter_rule').order('id desc').where(
                        "time>? and time<? and server_name=?",
                        (start_timeStamp, end_timeStamp, server_name)).limit(
                        str(page.SHIFT) + ',' + str(page.ROW)).select()
                    data['data'] = data22
                    return public.returnMsg(True, data)
                else:
                    if not 'serach' in get: return public.returnMsg(False, "必须传递serach参数")
                    serach = get.serach.strip()
                    if int(type) == 1:
                        import page
                        page = page.Page()
                        count = self.M2('totla_log').field('time').where("ip=? and server_name=?",
                                                                         (serach, server_name)).order('id desc').count()
                        info = {}
                        info['count'] = count
                        info['row'] = 10
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
                        data22 = self.M3('totla_log').field(
                            'id,time,time_localtime,server_name,ip,uri,filter_rule').order('id desc').where(
                            "ip=? and server_name=?", (serach, server_name)).limit(
                            str(page.SHIFT) + ',' + str(page.ROW)).select()
                        data['data'] = self.bytpes_to_string(data22)
                        return public.returnMsg(True, data)
                    if int(type) == 2:
                        try:
                            data_count = self.M2('totla_log').query(
                                "select COUNT(*) from totla_log WHERE server_name='{0}' and uri like '{1}?%';".format(
                                    server_name, serach))
                            if data_count[0]:
                                if data_count[0][0]:
                                    count = data_count[0][0]
                                else:
                                    count = 0
                            else:
                                count = 0
                            import page
                            page = page.Page()
                            count = count
                            info = {}
                            info['count'] = count
                            info['row'] = 10
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
                            data222 = self.M2('totla_log').query(
                                "select id,time,time_localtime,server_name,ip,uri,filter_rule from totla_log WHERE server_name='{3}' and  uri like '{0}?%' limit {1},{2}".format(
                                    serach, str(page.SHIFT), str(page.ROW), server_name))
                            if len(data222) > 0:
                                ret = []
                                for i in data222:
                                    ret.append(
                                        {"id": i[0], "time": i[1], "time_localtime": i[2], "server_name": i[3],
                                         "ip": i[4],
                                         "uri": i[5], "filter_rule": i[6]})
                                data['data'] = ret
                            else:
                                data['data'] = []
                            return public.returnMsg(True, data)
                        except:
                            return {"status": True, "msg": {
                                "page": "<div><span class='Pcurrent'>1</span><span class='Pcount'>共0条</span></div>",
                                "data": []}}
                    if int(type) == 3:
                        '''url ==> /?id=/etc/passwd 代表为 /?id=/etc/passwd'''
                        import page
                        page = page.Page()
                        count = self.M2('totla_log').field('time').where("uri=? and server_name=?",
                                                                         (serach, server_name)).order('id desc').count()
                        info = {}
                        info['count'] = count
                        info['row'] = 10
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
                        data22 = self.M3('totla_log').field(
                            'id,time,time_localtime,server_name,ip,uri,filter_rule').order('id desc').where(
                            "uri=? and server_name=?", (serach, server_name)).limit(
                            str(page.SHIFT) + ',' + str(page.ROW)).select()
                        data['data'] = self.bytpes_to_string(data22)
                        return public.returnMsg(True, data)
                    else:
                        return public.returnMsg(False, "参数传递错误")

    def get_id_log(self, get):
        '''
        返回当前ID的数据
        '''
        id = get.id.strip()
        if self.M2('totla_log').where("id=?", id).count() == 0: return public.returnMsg(False, "当前ID不存在")
        data22 = self.M3('totla_log').field(
            'id,time,time_localtime,server_name,ip,ip_city,ip_country,ip_subdivisions,ip_longitude,ip_latitude,type,uri,user_agent,filter_rule,incoming_value,value_risk,http_log,http_log_path').order(
            'id desc').where("id=?", id).select()
        data = self.bytpes_to_string(data22)
        return public.returnMsg(True, data)

    def takeSecond(self, elem):
        return elem[1]

    def report_data(self, data):
        '''
        返回报表数据
        '''
        result = {}
        result["type"] = {}
        result["ip"] = {}
        result["uri"] = {}
        result["ip_list"] = {}
        result['uri_list'] = {}
        tmp={}
        for i in data:
            if i['ip'] in result["ip"]:
                result["ip"][i['ip']] = result["ip"][i['ip']] + 1
            else:
                result["ip_list"][i['ip']] = {"uri": {}, "list": [], "type": {},"ip_country":""}
                result["ip"][i['ip']] = 1
            tmp[i['ip']]=i['ip_country']
            if not result["ip_list"][i['ip']]["ip_country"]:
               result["ip_list"][i['ip']]["ip_country"]=i["ip_country"]
            tmp[i['ip']+"ip_subdivisions"]=i['ip_subdivisions']
            if  not "ip_subdivisions" in result["ip_list"][i['ip']]:
               result["ip_list"][i['ip']]["ip_subdivisions"]=i["ip_subdivisions"]
            tmp[i['ip'] + "ip_city"] = i['ip_city']
            if not "ip_city" in result["ip_list"][i['ip']]:
                result["ip_list"][i['ip']]["ip_city"] = i["ip_city"]
            #
            # if not result["ip_list"][i['ip']]["ip_subdivisions"]:
            #    result["ip_list"][i['ip']]["ip_subdivisions"]=i["ip_subdivisions"]

            # if not result["ip_list"][i['ip']]["ip_city"]:
            #    result["ip_list"][i['ip']]["ip_city"]=i["ip_city"]

            url = i['uri'].split("?")[0]
            if url in result["ip_list"][i['ip']]["uri"]:
                result["ip_list"][i['ip']]["uri"][url] += 1
            else:
                result["ip_list"][i['ip']]["uri"][url] = 1
            if url in result["uri"]:
                result["uri"][url] = result["uri"][url] + 1
            else:
                result["uri"][url] = 1
            if i['filter_rule'] in result["ip_list"][i['ip']]["type"]:
                result["ip_list"][i['ip']]["type"][i['filter_rule']] += 1
            else:
                result["ip_list"][i['ip']]["type"][i['filter_rule']] = 1
            if i['filter_rule'] in result["type"]:
                if i['filter_rule']:
                    result["type"][i['filter_rule']] += 1
            else:
                if i['filter_rule']:
                    result["type"][i['filter_rule']] = 1
            if not url in result['uri_list']:
                result['uri_list'][url] = {"ip_list": []}
            if len(result['uri_list'][url]['ip_list']) < 100:
                result['uri_list'][url]['ip_list'].append(
                    {"id": i["id"], "uri": i['uri'], "ip": i["ip"], "filter_rule": i["filter_rule"],
                     "server_name": i['server_name'], "time_localtime": i["time_localtime"],"ip_country":i["ip_country"],"ip_subdivisions":i["ip_subdivisions"],"ip_city":i["ip_city"]})
            if len(result["ip_list"][i['ip']]["list"]) < 100:
                result["ip_list"][i['ip']]["list"].append(
                    {"id": i["id"], "uri": i['uri'], "filter_rule": i["filter_rule"], "server_name": i['server_name'],
                     "time_localtime": i["time_localtime"],"ip_country":i["ip_country"],"ip_subdivisions":i["ip_subdivisions"],"ip_city":i["ip_city"]})

        result["ip"] = (sorted(result["ip"].items(), key=lambda kv: (kv[1], kv[0]), reverse=True))
        if len(result["ip"]) > 100:
            result["ip"] = result["ip"][0:100]
        ip_country=[]
        for i in result["ip"]:
            #查看ip归属地
            ret=[]
            ret.append(i[0])
            ret.append(i[1])
            ip_c=tmp[i[0]]
            ip_p=tmp[i[0]+"ip_subdivisions"]
            ip_d=tmp[i[0] + "ip_city"]
            ret.append(ip_c)
            ret.append(ip_p)
            ret.append(ip_d)
            ip_country.append(ret)
        result["ip"]=ip_country

        top_uri = (sorted(result["uri"].items(), key=lambda kv: ((kv[1]), kv[0]), reverse=True))
        result["uri"] = top_uri
        top_type = (sorted(result["type"].items(), key=lambda kv: (kv[1], kv[0]), reverse=True))
        result["type"] = top_type
        ip_list = {}
        for i in result["ip"]:
            if i[0] in result['ip_list']:
                result['ip_list'][i[0]]['uri'] = (
                    sorted(result['ip_list'][i[0]]['uri'].items(), key=lambda kv: (kv[1], kv[0]), reverse=True))
                ip_list[i[0]] = result['ip_list'][i[0]]
        result["ip_list"] = ip_list
        return result


    def get_report(self,get):
        # 默认是获取当天的数据
        if not 'start_time' in get:
            start_time = time.strftime("%Y-%m-%d", time.localtime(time.time()))
        else:
            start_time = get.start_time.strip()
        if not 'end_time' in get:
            end_time = start_time
        else:
            end_time = get.end_time.strip()
        start_time = start_time + ' 00:00:00'
        end_time2 = end_time + ' 23:59:59'
        start_timeStamp = int(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S')))
        end_timeStamp = int(time.mktime(time.strptime(end_time2, '%Y-%m-%d %H:%M:%S')))
        key ="get_report"+str(start_timeStamp)+str(end_timeStamp)

        if public.cache_get(key):
            public.run_thread(self.get_report_info,get)
            inf=public.cache_get(key)
            return public.returnMsg(True, inf)
        else:
            return self.get_report_info(get)

    '''
    所有网站[前30W条数据分析]
        漏洞攻击类型分布图
        攻击IP流量分析（top200）
        攻击页面分析(top 200)

    单个网站[前10W条数据分析]
        漏洞攻击类型分布图
        攻击IP流量分析（top200）
        攻击页面分析(top 200)
    '''
    def get_report_info(self, get):
        tmp={"type": [], "ip": [], "uri": [], "ip_list": {}, "uri_list": {}}
        # 默认是获取当天的数据
        if not 'start_time' in get:
            start_time = time.strftime("%Y-%m-%d", time.localtime(time.time()))
        else:
            start_time = get.start_time.strip()
        if not 'end_time' in get:
            end_time = start_time
        else:
            end_time = get.end_time.strip()
        start_time = start_time + ' 00:00:00'
        end_time2 = end_time + ' 23:59:59'
        start_timeStamp = int(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S')))
        end_timeStamp = int(time.mktime(time.strptime(end_time2, '%Y-%m-%d %H:%M:%S')))
        key ="get_report"+str(start_timeStamp)+str(end_timeStamp)

        if 'server_name' in get:
            if os.path.exists("/www/server/btwaf/totla_db/totla_db.db"):
                map_24_data = self.M3('totla_log').field('id,time_localtime,ip,uri,server_name,type,filter_rule,ip_city,ip_country,ip_subdivisions').where(
                    "time>? and time<? and server_name=?",
                    (start_timeStamp, end_timeStamp, get.server_name.strip())).limit("10000").order('id desc').select()
                if type(map_24_data) == str: return public.returnMsg(True, tmp)
                map_24_data = self.bytpes_to_string(map_24_data)
                public.cache_set(key,self.report_data(map_24_data),30)
                return public.returnMsg(True, self.report_data(map_24_data))
            return public.returnMsg(True, tmp)
        else:
            if os.path.exists("/www/server/btwaf/totla_db/totla_db.db"):
                map_24_data = self.M3('totla_log').field('id,time_localtime,ip,uri,server_name,type,filter_rule,ip_city,ip_country,ip_subdivisions').where(
                    "time>? and time<?", (start_timeStamp, end_timeStamp), ).limit("10000").order('id desc').select()
                if type(map_24_data) == str: return public.returnMsg(True, tmp)
                map_24_data = self.bytpes_to_string(map_24_data)
                public.cache_set(key,self.report_data(map_24_data),30)
                return public.returnMsg(True, self.report_data(map_24_data))
            return public.returnMsg(True,  tmp)

    def get_server_name(self, get):
        try:
            site_config = public.readFile(self.__path + 'site.json')
            resutl = []
            data = json.loads(site_config)
            for i in data.items():
                resutl.append(i[0])
            return resutl
        except:
            return []
        return []

    def test222(self, get):
        return self.M2('totla_log').field('id,time_localtime,ip,uri,server_name,type,filter_rule').limit(
            "100000").order(
            'id desc').count()

    def get_cc_uri_frequency(self, get):
        get_config = self.get_config(None)
        return get_config['cc_uri_frequency']

    def add_cc_uri_frequency(self, get):
        if 'url' not in get: return public.ReturnMsg(False, '参数url不能为空')
        if 'frequency' not in get: return public.ReturnMsg(False, '参数frequency不能为空')
        if 'cycle' not in get: return public.ReturnMsg(False, '参数cycle不能为空')

        get_config = self.get_config(None)
        cc_uri_frequency = get_config['cc_uri_frequency']
        if get.url.strip() in cc_uri_frequency:
            return public.ReturnMsg(False, '已经存在')

        cc_uri_frequency[get.url.strip()] = {'frequency': get.frequency.strip(), 'cycle': get.cycle.strip()}
        get_config['cc_uri_frequency'] = cc_uri_frequency
        self.__write_config(get_config)
        return public.ReturnMsg(True, '添加成功')

    def del_cc_uri_frequency(self, get):
        if 'url' not in get: return public.ReturnMsg(False, '参数url不能为空')
        get_config = self.get_config(None)
        cc_uri_frequency = get_config['cc_uri_frequency']
        if get.url.strip() in cc_uri_frequency:
            del cc_uri_frequency[get.url.strip()]
            get_config['cc_uri_frequency'] = cc_uri_frequency
            self.__write_config(get_config)
            return public.ReturnMsg(True, '删除成功')
        return public.ReturnMsg(False, '不存在')

    def edit_cc_uri_frequency(self, get):
        if 'url' not in get: return public.ReturnMsg(False, '参数url不能为空')
        if 'frequency' not in get: return public.ReturnMsg(False, '参数frequency不能为空')
        if 'cycle' not in get: return public.ReturnMsg(False, '参数cycle不能为空')
        get_config = self.get_config(None)
        cc_uri_frequency = get_config['cc_uri_frequency']
        if get.url.strip() in cc_uri_frequency:
            cc_uri_frequency[get.url.strip()] = {'frequency': get.frequency.strip(), 'cycle': get.cycle.strip()}
            get_config['cc_uri_frequency'] = cc_uri_frequency
            self.__write_config(get_config)
            return public.ReturnMsg(True, '修改成功')
        return public.ReturnMsg(False, '不存在')

    # 验证是否存在人机验证
    def check_renji(self, get):
        if os.path.exists('/www/server/btwaf/init.lua'):
            lua_data = public.ReadFile('/www/server/btwaf/init.lua')
            if 'a20be899_96a6_40b2_88ba_32f1f75f1552_yanzheng_huadong' in lua_data:
                return True
            else:
                return False

    # 添加url_cc_param 参数
    def add_url_cc_param(self, get):
        '''
        @name 添加url_cc_param 参数
        @param get.uri 请求的uri
        @param get.param 参数列表
        @param get.type 参数值
        @param get.stype  类型值  一个是url  一个是regular
        '''
        # {"index.php":{"param":[],"type":1,"stype":"url"}}
        if not 'uri' in get: return public.returnMsg(False, "必须传递uri参数")
        if not 'param' in get: return public.returnMsg(False, "必须传递param参数")
        if not 'type' in get: return public.returnMsg(False, "必须传递type参数")
        if not 'stype' in get: return public.returnMsg(False, "必须传递stype参数")
        config = self.get_config(None)
        if get.uri.strip() in config['url_cc_param']: return public.returnMsg(False, "当前URI已经存在")
        try:
            param = json.loads(get.param)
            type = (int(get.type))
        except:
            return public.returnMsg(False, "param类型不对,需要json格式")

        if 'url_cc_param' not in config:
            config['url_cc_param'] = {}
        config['url_cc_param'][get.uri.strip()] = {"param": param, 'type': type, 'stype': get.stype.strip()}
        self.__write_config(config)
        return public.returnMsg(True, "添加成功")

    # 删除url_cc_param 参数
    def del_url_cc_param(self, get):
        if not 'uri' in get: return public.returnMsg(False, "必须传递uri参数")
        config = self.get_config(None)
        if 'url_cc_param' not in config:
            config['url_cc_param'] = {}
        if not get.uri.strip() in config['url_cc_param']: return public.returnMsg(False, "当前URI不存在")
        del config['url_cc_param'][get.uri.strip()]
        self.__write_config(config)
        return public.returnMsg(True, "删除成功")

    def wubao_webshell(self, get):
        if 'path' not in get:
            return public.returnMsg(False, '必须传递path参数')
        path =self.Recycle_bin+get.path
        if not os.path.exists(path):
            return public.returnMsg(False, '文件不存在')
        dFile = get.path.replace('_bt_', '/').split('_t_')[0]
        file_md5=public.Md5(dFile)
        # 删除webshell那个内容以及文件
        webshell_path = "/www/server/panel/data/btwaf_wubao/"
        if not os.path.exists(webshell_path):
            os.makedirs(webshell_path)
        wubao_file = webshell_path+file_md5+".txt"
        public.WriteFile(wubao_file, '')
        #恢复文件
        return  self.Re_Recycle_bin(get)

    def del_yangben(self, get):

        if not 'path' in get:
            return public.returnMsg(False, '必须传递path参数')
        if not 'is_path' in get:
            is_path = 1
        webshell_path = "/www/server/panel/data/btwaf_webshell/"

        if os.path.exists(webshell_path + get.is_path):
            try:
                os.remove(webshell_path + get.is_path)
            except:
                pass
        if 'delete' in get:
            if os.path.exists(get.path):
                try:
                    os.remove(get.path)
                except:
                    pass
        try:
            webshell_info = json.loads(public.ReadFile("/www/server/btwaf/webshell.json"))
            if get.path in webshell_info:
                webshell_path = "/www/server/panel/data/btwaf_webshell/"
                if os.path.exists(webshell_path + webshell_info[get.path]):
                    os.remove(webshell_path + webshell_info[get.path])
                del webshell_info[get.path]
                public.writeFile('/www/server/btwaf/webshell.json', json.dumps(webshell_info))
        except:
            pass

        return public.returnMsg(True, '删除成功')

    def restore_default_configuration(self, get):
        config_path = '/www/server/btwaf/config.json'
        config = '''{
	"scan": {
		"status": 444,
		"ps": "过滤常见扫描测试工具的渗透测试",
		"open": true,
		"reqfile": ""
	},
	"cc": {
		"status": 444,
		"ps": "过虑CC攻击",
		"increase": false,
		"limit": 120,
		"endtime": 300,
		"open": true,
		"reqfile": "",
		"cycle": 60
	},
	"logs_path": "/www/wwwlogs/btwaf",
	"open": true,
	"reqfile_path": "/www/server/btwaf/html",
	"retry": 10,
	"log": true,
	"cc_automatic": false,
	"user-agent": {
		"status": 403,
		"ps": "通常用于过滤浏览器、蜘蛛及一些自动扫描器",
		"open": true,
		"reqfile": "user_agent.html"
	},
	"other": {
		"status": 403,
		"ps": "其它非通用过滤",
		"reqfile": "other.html"
	},
	"uri_find": [],
	"cc_retry_cycle": "600",
	"cc_time": "60",
	"ua_black": [],
	"drop_abroad": {
		"status": 444,
		"ps": "禁止中国大陆以外的地区访问站点",
		"open": true,
		"reqfile": ""
	},
	"retry_cycle": 120,
	"get": {
		"status": 403,
		"ps": "过滤uri、uri参数中常见sql注入、xss等攻击",
		"open": true,
		"reqfile": "get.html"
	},
	"body_character_string": [],
	"start_time": 0,
	"cookie": {
		"status": 403,
		"ps": "过滤利用Cookie发起的渗透攻击",
		"open": true,
		"reqfile": "cookie.html"
	},
	"retry_time": 1800,
	"post": {
		"status": 403,
		"ps": "过滤POST参数中常见sql注入、xss等攻击",
		"open": true,
		"reqfile": "post.html"
	},
	"scan_conf":{"open": true, "limit": 240, "cycle": 60},
	"ua_white": [],
	"body_regular": [],
	"log_save": 30
}'''

        public.WriteFile(config_path, config)

        # 网站配置
        site_config_path = '/www/server/btwaf/site.json'
        public.WriteFile(site_config_path, '{}')

        # ip白名单
        ip_white_path = '/www/server/btwaf/rule/ip_white.json'
        public.WriteFile(ip_white_path, '[[2130706433, 2130706687]]')

        # ip黑名单
        ip_black_path = '/www/server/btwaf/rule/ip_black.json'
        public.WriteFile(ip_black_path, '[]')

        # url白名单
        url_white_path = '/www/server/btwaf/rule/url_white.json'
        public.WriteFile(url_white_path, '[]')

        # url黑名单
        url_black_path = '/www/server/btwaf/rule/url_black.json'
        public.WriteFile(url_black_path, '[]')

        # 统计文件
        statistics_path = '/www/server/btwaf/total.json'
        public.WriteFile(statistics_path,
                         '{"rules":{"user_agent":0,"cookie":0,"post":0,"args":0,"url":0,"cc":0},"sites":{},"total":0}')

        # domains.json
        domains_path = '/www/server/btwaf/domains.json'
        public.WriteFile(domains_path, '[]')

        # 地区限制
        area_limit_path = '/www/server/btwaf/rule/reg_tions.json'

        public.WriteFile(area_limit_path, '[]')

        # 初始化默认配置

        self.get_config(get)
        self.get_site_config(get)
        public.ExecShell("/etc/init.d/nginx restar")
        return public.returnMsg(True, '恢复成功')

    def get_site_logs_sql(self, tables, conditions):
        start_date = conditions["start_time"]
        end_date = conditions["end_time"]
        reverse_mode = ""
        if "reverse_mode" in conditions:
            reverse_mode = conditions["reverse_mode"]

        time_reverse = False
        if 'server_name' in conditions:
            where_sql = " where server_name=\"{}\" ".format(conditions['server_name'])
            if "time_reverse" in conditions:
                time_reverse = conditions["time_reverse"]
            if not time_reverse:
                where_sql += " and time >= {} and time <= {}".format(start_date, end_date)
            else:
                where_sql += " and time < {} or time > {}".format(start_date, end_date)
        else:
            if "time_reverse" in conditions:
                time_reverse = conditions["time_reverse"]
            if not time_reverse:
                where_sql = " where time >= {} and time <= {}".format(start_date, end_date)
            else:
                where_sql = " where time < {} or time > {}".format(start_date, end_date)

        conditions_keys = conditions.keys()
        if "status_code" in conditions_keys:
            status_code = conditions["status_code"]
            status_code_50x = [500, 501, 502, 503, 504, 505, 506, 507, 509]
            status_code_40x = [400, 401, 402, 403, 404, 405, 406, 407, 408, 409]
            status_code_5xx = [500, 501, 502, 503, 504, 505, 506, 507, 509, 510]
            status_code_4xx = [400, 401, 402, 403, 404, 405, 406, 407, 408, 409,
                               410, 411, 412, 413, 414, 415, 416, 417, 418, 421,
                               422, 423, 424, 425, 426, 449, 451, 499]
            if status_code in ["5xx", "5**", "5XX"]:
                status_code = ",".join([str(s) for s in status_code_5xx])
            elif status_code in ["50x", "50X", "50*"]:
                status_code = ",".join([str(s) for s in status_code_50x])
            elif status_code in ["4xx", "4**", "4XX"]:
                status_code = ",".join([str(s) for s in status_code_4xx])
            elif status_code in ["40x", "40X", "40*"]:
                status_code = ",".join([str(s) for s in status_code_40x])
            else:
                status_code = status_code
            if status_code != "all":
                if not reverse_mode:
                    where_sql += " and status_code in ({})".format(status_code)
                else:
                    where_sql += " and status_code not in ({})".format(status_code)
        if "method" in conditions_keys:
            method = conditions["method"]
            if method != "all":
                if not reverse_mode:
                    where_sql += " and method='{}'".format(method)
                else:
                    where_sql += " and method<>'{}'".format(method)
        search_url = ""
        if "serach_url" in conditions_keys:
            search_url = conditions["serach_url"]
        if "uri" in conditions_keys:
            search_url = conditions["uri"]
        search_mode = "fuzzy"
        if "search_mode" in conditions_keys:
            search_mode = conditions["search_mode"]
        if search_url:
            if search_url.find(",") < 0:
                if search_mode == "fuzzy":
                    if not reverse_mode:
                        where_sql += " and uri like '%{}%'".format(search_url)
                    else:
                        where_sql += " and uri not like '%{}%'".format(search_url)
                else:
                    if not reverse_mode:
                        where_sql += " and uri='{}'".format(search_url)
                    else:
                        where_sql += " and uri<>'{}'".format(search_url)
            else:
                _sql = ""
                for url in search_url.split(","):
                    url = url.strip()
                    if _sql:
                        _sql += " or "
                    if search_mode == "fuzzy":
                        if not reverse_mode:
                            _sql += "uri like '%{}%'".format(url)
                        else:
                            _sql += "uri not like '%{}%'".format(url)
                    else:
                        if not reverse_mode:
                            _sql += "uri='{}'".format(url)
                        else:
                            _sql += "uri<>'{}'".format(url)
                where_sql += " and " + _sql
        # ip
        if "ip" in conditions_keys:
            ip = conditions["ip"].strip()
            if ip:
                ip = ip.replace("，", ",")
                if ip.find(",") > 0:
                    ip = ",".join(["'" + ip.strip() + "'" for ip in ip.split(",")])
                    if not reverse_mode:
                        where_sql += " and ip in (" + ip + ")"
                    else:
                        where_sql += " and ip not in (" + ip + ")"
                elif ip.find("*") >= 0:
                    ip = ip.replace("*", "%")
                    if not reverse_mode:
                        where_sql += " and (ip like \"" + ip + "\" or ip like \"" + ip + "\")"
                    else:
                        where_sql += " and ip not like \"" + ip + "\" and ip not like \"" + ip + "\""
                else:
                    if not reverse_mode:
                        where_sql += " and (ip=\"" + ip + "\" or ip like \"%" + ip + "%\")"
                    else:
                        where_sql += " and ip<>\"" + ip + "\" and ip not like \"%" + ip + "%\""
        # 域名过滤
        if "domain" in conditions_keys:
            domain = conditions["domain"].strip()
            if domain:
                if search_mode == "fuzzy":
                    if not reverse_mode:
                        where_sql += " and server_name like '%" + domain + "%'"
                    else:
                        where_sql += " and server_name not like '%" + domain + "%'"
                else:
                    if not reverse_mode:
                        where_sql += " and server_name='" + domain + "'"
                    else:
                        where_sql += " and server_name<>'" + domain + "'"
        # ua过滤
        if "user_agent" in conditions_keys:
            user_agent = conditions["user_agent"].strip()
            if user_agent:
                if search_mode == "fuzzy":
                    if not reverse_mode:
                        where_sql += " and user_agent like '%" + user_agent + "%'"
                    else:
                        where_sql += " and user_agent not like '%" + user_agent + "%'"
                else:
                    if not reverse_mode:
                        where_sql += " and user_agent='" + user_agent + "'"
                    else:
                        where_sql += " and user_agent<>'" + user_agent + "'"

        select_sql = "select {} from %s" % (tables) + where_sql
        return select_sql

    def __format_field(self, field):
        import re
        fields = []
        for key in field:
            s_as = re.search(r'\s+as\s+', key, flags=re.IGNORECASE)
            if s_as:
                as_tip = s_as.group()
                key = key.split(as_tip)[1]
            fields.append(key)
        return fields

    '''
        @搜索拦截日志
        @param {"ip":"192.168.10.1,192.168.10.1,192.168.10.*"}   ip搜索 
        @param {"url":"/ali.php"}     url搜索
        @param {"site":"www.bt.cn"}   按照网站搜索 
        @param {"start_time":"time"}  开始时间  
        @param {"end_time":"time"}    结束时间
        @param {"ua":"Mozilla/5.0"}   按照ua搜索 
    '''

    def get_search_logs(self, get):
        result = {}
        if 'limit' in get:
            limit = int(get.limit.strip())
        else:
            limit = 12

        if os.path.exists("/www/server/btwaf/totla_db/totla_db.db"):
            try:
                if self.M2('blocking_ip').order('id desc').count() == 0: return public.returnMsg(False, result)
            except:
                return {"status": True, "msg": {
                    "page": "<div><span class='Pcurrent'>1</span><span class='Pcount'>\u51710\u6761</span></div>",
                    "data": []}}
        try:
            conditions = {}
            if "ip" in get:
                conditions["ip"] = get.ip
            if "domain" in get:
                conditions["domain"] = get.domain
            if "serach_url" in get:
                conditions["serach_url"] = get.serach_url
            if "user_agent" in get:
                conditions["user_agent"] = get.user_agent

            if 'time_reverse' in get:
                conditions["time_reverse"] = get.time_reverse

            if 'start_time' in get:
                conditions["start_time"] = int(get.start_time)
            else:
                conditions["start_time"] = 0

            if 'end_time' in get:
                conditions["end_time"] = int(get.end_time)
            else:
                conditions["end_time"] = int(time.time())

            orderby = "time"
            if "orderby" in get:
                orderby = get.orderby

            desc = True
            if "desc" in get:
                desc = True if get.desc.lower() == "true" else False

            page_size = 10
            get.page_size = page_size

            if "exact_match" in get:
                conditions["search_mode"] = "exact" if get.exact_match.lower() == "true" else "fuzzy"
            else:
                conditions["search_mode"] = "fuzzy"
            if "reverse_match" in get:
                conditions["reverse_mode"] = True if get.reverse_match.lower() == "true" else False
            if "time_reverse" in get:
                conditions["time_reverse"] = True if get.time_reverse.lower() == "true" else False
            if "response_time" in get:
                conditions["response_time"] = float(get.response_time)
                if "response_time_comparator" in get:
                    conditions["response_time_comparator"] = get.response_time_comparator

            offset = 0
            if "offset" in get:
                offset = int(get.offset)

            select_sql = self.get_site_logs_sql('blocking_ip', conditions)

            self.__OPT_FIELD = 'time,time_localtime,server_name,ip,ip_city,ip_country,ip_subdivisions,ip_longitude,ip_latitude,type,uri,user_agent,filter_rule,incoming_value,value_risk,http_log,http_log_path,blockade,blocking_time,is_status'
            count = "count(*)"
            select_data_sql = select_sql.format(count)
            result = self.M2('blocking_ip').query(select_data_sql)

            import page
            page = page.Page()
            count = result[0][0]
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

            select_data_sql = select_sql.format(self.__OPT_FIELD)

            if orderby:
                select_data_sql += " order by " + orderby
            if desc:
                select_data_sql += " desc"

            sub_select_data_sql = select_data_sql + " limit " + (str(page.SHIFT) + ',' + str(page.ROW))
            # sub_select_data_sql += " offset " + str(sub_offset)

            sub_select_data_sql += ";"

            # return sub_select_data_sql
            result = self.M2('blocking_ip').query(sub_select_data_sql)

            if self.__OPT_FIELD != "*":
                fields = self.__format_field(self.__OPT_FIELD.split(','))
                tmp = []
                for row in result:
                    i = 0
                    tmp1 = {}
                    for key in fields:
                        tmp1[key.strip('`')] = row[i]
                        i += 1
                    tmp.append(tmp1)
                    del (tmp1)
                result = tmp
                del (tmp)
            data['data'] = self.bytpes_to_string(result)
            self.is_feng(data)
            return public.returnMsg(True, data)

        except:
            return {"status": True, "msg": {
                "page": "<div><span class='Pcurrent'>1</span><span class='Pcount'>\u51710\u6761</span></div>",
                "data": []}}

    # 导出所有的封锁日志
    def export_info(self, get):
        from BTPanel import send_file
        cvs_path = "/www/server/panel/data/1.csv"
        try:
            data222 = self.M3('blocking_ip').field(
                'time,time_localtime,server_name,ip,uri,user_agent').order(
                'id desc').select()
            data = self.bytpes_to_string(data222)
            import csv
            with open(cvs_path, 'w') as file:
                writer = csv.writer(file)
                writer.writerow(['time', 'server_name', 'ip', 'uri', 'user_agent'])
                for row in data222:
                    writer.writerow(
                        [row['time_localtime'], row['server_name'], row['ip'], row['uri'], row['user_agent']])
            return send_file(cvs_path, conditional=True, etag=True)
        except:
            public.writeFile(cvs_path, '')
            return send_file(cvs_path, conditional=True, etag=True)

    # 搜索网站
    def get_search_sites(self, get):
        # 所有所有的网站信息
        try:
            site_config = json.loads(public.readFile(self.__path + 'site.json'))
        except:
            public.WriteFile(self.__path + 'site.json', json.dumps({}))
            self.__write_site_domains()
            site_config = json.loads(public.readFile(self.__path + 'site.json'))
        if not os.path.exists(self.__path + '/domains.lua'):
            self.__write_site_domains()
        data_site = self.__check_site(site_config)
        if get:
            total_all = self.get_total(None)['sites']
            site_list = []
            for k in data_site.keys():
                if not k in total_all: total_all[k] = {}
                data_site[k]['total'] = self.__format_total(total_all[k])
                siteInfo = data_site[k]
                siteInfo['siteName'] = k
                site_list.append(siteInfo)
            data_site = sorted(site_list, key=lambda x: x['log_size'], reverse=True)
        #return data_site
        import data as data2
        data2 = data2.data()
        get.table = 'sites'
        get.limit = 10
        if 'p' not in get:
            get.p = 1
        get.type = '-1'
        datas = data2.getData(get)

        ret = []
        if datas['data']:
            for site in datas['data']:
                for i in data_site:
                    if i['siteName'] == site['name']:
                        ret.append(i)
        data_site = ret
        if not 'limit' in get:
            get.limit = 12
        limit = int(get.limit)
        if not 'p' in get:
            get.p = 1
        p = int(get.p)
        count = len(data_site)
        result = []
        if count < limit:
            result = data_site
        if count < (p * limit):
            result = data_site[(p - 1) * limit:count]
        else:
            result = data_site[(p - 1) * limit:(p * limit)]
        import page
        page = page.Page()
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
        data['data'] = result
        return data

    def get_site_safe_logs(self, get):
        '''
        siteName:按照网站进行高级搜索
        start_time:2022--06
        end_time:2021-05-07
        p:1  页数
        limit:10
        @param {"ip":"192.168.10.1,192.168.10.1,192.168.10.*"}   ip搜索
        @param {"url":"/ali.php"}     url搜索
        @param {"site":"www.bt.cn"}   按照网站搜索
        @param {"start_time":"time"}  开始时间
        @param {"end_time":"time"}    结束时间
        @param {"ua":"Mozilla/5.0"}   按照ua搜索

        '''
        if not 'siteName' in get:
            return public.returnMsg(False, "请传递网站名称")
        if not 'limit' in get:
            limit = 10
        else:
            limit = int(get.limit.strip())
        if not 'p' in get:
            p = 10
        else:
            p = int(get.p.strip())
        if not 'start_time' in get:
            start_time = time.strftime("%Y-%m-%d", time.localtime(time.time()))
        else:
            start_time = get.start_time.strip()
        if not 'end_time' in get:
            # end_time = time.strftime("%Y-%m-%d", time.localtime(time.time()))
            end_time = start_time
        else:
            end_time = get.end_time.strip()
        start_time = start_time + ' 00:00:00'
        end_time2 = end_time + ' 23:59:59'
        start_timeStamp = int(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S')))
        end_timeStamp = int(time.mktime(time.strptime(end_time2, '%Y-%m-%d %H:%M:%S')))

        conditions = {}
        if "ip" in get:
            conditions["ip"] = get.ip
        conditions["server_name"] = get.siteName
        if "serach_url" in get:
            conditions["serach_url"] = get.serach_url
        if "user_agent" in get:
            conditions["user_agent"] = get.user_agent

        # conditions["time_reverse"] = 1

        conditions["start_time"] = start_timeStamp

        conditions["end_time"] = end_timeStamp

        orderby = "time"
        if "orderby" in get:
            orderby = get.orderby

        desc = True
        if "desc" in get:
            desc = True if get.desc.lower() == "true" else False

        page_size = 10
        get.page_size = page_size

        if "exact_match" in get:
            conditions["search_mode"] = "exact" if get.exact_match.lower() == "true" else "fuzzy"
        else:
            conditions["search_mode"] = "fuzzy"
        if "reverse_match" in get:
            conditions["reverse_mode"] = True if get.reverse_match.lower() == "true" else False
        if "time_reverse" in get:
            conditions["time_reverse"] = True if get.time_reverse.lower() == "true" else False
        if "response_time" in get:
            conditions["response_time"] = float(get.response_time)
            if "response_time_comparator" in get:
                conditions["response_time_comparator"] = get.response_time_comparator
        offset = 0
        if "offset" in get:
            offset = int(get.offset)
        select_sql = self.get_site_logs_sql('totla_log', conditions)

        # 获取所有的网站信息
        if os.path.exists("/www/server/btwaf/totla_db/totla_db.db"):
            import page
            page = page.Page()
            self.__OPT_FIELD = 'time,time_localtime,server_name,ip,ip_city,ip_country,ip_subdivisions,ip_longitude,ip_latitude,type,uri,user_agent,filter_rule,incoming_value,value_risk,http_log,http_log_path'
            count = "count(*)"
            select_data_sql = select_sql.format(count)
            result = self.M2('totla_log').query(select_data_sql)
            info = {}
            info['count'] = result[0][0]
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
            data['data'] = []
            select_data_sql = select_sql.format(self.__OPT_FIELD)

            if orderby:
                select_data_sql += " order by " + orderby
            if desc:
                select_data_sql += " desc"

            sub_select_data_sql = select_data_sql + " limit " + (str(page.SHIFT) + ',' + str(page.ROW))
            sub_select_data_sql += ";"
            result = self.M2('blocking_ip').query(sub_select_data_sql)
            if self.__OPT_FIELD != "*":
                fields = self.__format_field(self.__OPT_FIELD.split(','))
                tmp = []
                for row in result:
                    i = 0
                    tmp1 = {}
                    for key in fields:
                        tmp1[key.strip('`')] = row[i]
                        i += 1
                    tmp.append(tmp1)
                    del (tmp1)
                result = tmp
                del (tmp)

            try:
                data['data'] = self.bytpes_to_string(result)
            except:
                data = {}
                data['page'] = "<div><span class='Pcurrent'>1</span><span class='Pcount'>共0条</span></div>"
                data['data'] = []
                return public.returnMsg(False, data)
            return public.returnMsg(True, data)
        else:
            data = {}
            data['page'] = "<div><span class='Pcurrent'>1</span><span class='Pcount'>共0条</span></div>"
            data['data'] = []
            return public.returnMsg(False, data)


    # 获取回收站信息
    def Get_Recycle_bin(self, get):
        data = []
        rPath  =self.__PATH+'Recycle'
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

    def html_decode(self,text):
        '''
            @name HTML解码
            @author hwliang
            @param text 要解码的HTML
            @return string 返回解码后的HTML
        '''
        try:
            from cgi import html
            text2 = html.unescape(text)
            return text2
        except:
            return text

    # 从回收站恢复
    def Re_Recycle_bin(self,get):
        if sys.version_info[0] == 2:
            get.path = get.path.encode('utf-8')
        get.path = self.html_decode(get.path).replace(';','')
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
        tfile = self.html_decode(get.path).replace(';', '')
        filename=self.Recycle_bin+'/'+get.path
        public.ExecShell('chattr  -i ' + filename)
        try:
            os.remove(filename)
        except:
            public.ExecShell("rm -f " + filename)
        return public.returnMsg(True, '已经从木马隔离箱中永久删除当前文件'+tfile)


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

    #设置告警
    def Set_Alarm(self,get):
        '''
            @name 设置告警
            @param get
            @param CC攻击告警   120秒内有30个IP触发CC拦截。就告警
            @param 封锁IP总数   如果120秒内有60 IP触发封锁。就告警
            @param 版本更新     如果有新版本。就告警
            @param 发现木马     如果有木马。就告警
            @param 安全漏洞通知   如果有新的安全漏洞。就告警
        '''
        pdata={}
        if 'cc' not in get:
            pdata['cc']={"cycle":120,"limit":30,"status":False}
        else:
            pdata['cc'] = json.loads(get.cc)
        if 'file' not in get:
            pdata['file']={"cycle":120,"limit":60,"status":False}
        else:
            pdata['file'] = json.loads(get.file)
        #新版本
        if 'version' not in get:
            pdata['version']={"status":False}
        else:
            pdata['version'] = json.loads(get.version)

        if 'webshell' not in get:
            pdata['webshell']={"status":False}
        else:
            pdata['webshell'] = json.loads(get.vul)

        if 'vul' not in get:
            pdata['vul']={"status":False}
        else:
            pdata['vul'] = json.loads(get.vul)

        if 'send' not in get:
            pdata['send']={"status":False,"send_type":"error"}
        else:
            pdata['send'] = json.loads(get.send)
        #设置告警
        send_type=pdata['send']['send_type']
        if not public.M('send_settings').where('name=?', ('btwaf',)).count():
            self.insert_settings('btwaf', 'python_script', '/www/server/panel/plugin/btwaf/send.py', send_type, 60)
            self.__write_log('开启告警成功')
            # self.get_Alarm_info()
        public.WriteFile("data/btwaf_alarm.json",json.dumps(pdata))
        return public.returnMsg(True, '设置成功')

    def Get_Alarm(self,get):
        '''
            @name 获取告警设置
        '''
        # self.get_Alarm_info()
        try:
            if not os.path.exists("data/btwaf_alarm.json"):
                self.Set_Alarm(get)
            info=json.loads(public.readFile("data/btwaf_alarm.json"))
            if info['send']['status'] and info['send']['send_type']!="error":
                if not public.M('send_settings').where('name=?', ('btwaf',)).count():
                    self.insert_settings('btwaf', 'python_script', '/www/server/panel/plugin/btwaf/send.py', info['send']['send_type'],60)
            return info
        except:
            self.Set_Alarm(get)
            return json.loads(public.readFile("data/btwaf_alarm.json"))

    def start_main(self,path):
        if not os.path.exists(path): return False
        module = os.path.basename(path).split('.')[0]
        module_dir = os.path.dirname(path)
        sys.path.insert(0, "{}".format(module_dir))
        send_to_user_info = __import__('{}'.format(module))
        try:
            public.mod_reload(send_to_user_info)
        except:
            pass
        return eval('send_to_user_info.{}()'.format(module))

    def get_Alarm_info(self):
        obj=self.start_main("/www/server/panel/class/send_to_user.py")
        if obj:
            #判断是否存在send_mail_data这个方法名
            if hasattr(obj, 'send_mail_data'):
                return True
        return False



    def get_drop_abroad_count(self,get):
        inf = public.cache_get("get_drop_abroad_count")
        if inf:
            return public.returnMsg(True, inf)
        count = 0
        try:
            site_config = json.loads(public.readFile(self.__path + 'site.json'))
        except:
            return public.returnMsg(True, count)

        for i in site_config:
            if site_config[i]['drop_abroad']:
                count+=1
        public.cache_set("get_drop_abroad_count",count,360)
        return public.returnMsg(True, count)

    # 攻击报表导出
    def attack_export(self, get):
        from BTPanel import send_file
        cvs_path = "/www/server/panel/data/2.csv"
        try:
            # data222 = self.M3('blocking_ip').field(
            #     'time,time_localtime,server_name,ip,uri,user_agent').order(
            #     'id desc').select()
            # data = self.bytpes_to_string(data222)
            import csv
            info = self.get_report(get)


            with open(cvs_path, 'w') as file:
                writer = csv.writer(file)
                writer.writerow(['IP报表', '时间', '网站域名', '攻击IP', '攻击的URL', '攻击的User-Agent'])
                if info['ip_list']:
                    for i in info['ip_list']:
                        writer.writerow([info['ip_list'][i], i['server_name'], i['ip'], i['uri'], i['user_agent']])

            return send_file(cvs_path, conditional=True, etag=True)
        except:
            public.writeFile(cvs_path, '')
            return send_file(cvs_path, conditional=True, etag=True)

    def nday_get(self,get):
        pass


# if __name__ == '__main__':
# b_obj = btwaf_main()
# type = sys.argv[1]
# if type == 'start':
#     b_obj.retuen_nginx()
# elif type == 'zhuzu':
#     b_obj.start_zhuzu()
# else:
#     b_obj.sync_