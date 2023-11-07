# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyleft (c) 2015-2099 宝塔软件(http://bt.cn) All lefts reserved.
# +-------------------------------------------------------------------
# | Author: wzz
# | email : help@bt.cn
# +-------------------------------------------------------------------
# +-------------------------------------------------------------------
# | 宝塔网站监控报表 - total_base
# +-------------------------------------------------------------------
from __future__ import absolute_import, division, print_function

import calendar
import json
import os
import sys
import time
import contextlib
import subprocess

_ver = sys.version_info
is_py2 = (_ver[0] == 2)
is_py3 = (_ver[0] == 3)

panelPath = '/www/server/panel'
sys.path.insert(0, panelPath)
os.chdir(panelPath)
if not panelPath + "/class/" in sys.path:
    sys.path.insert(0, panelPath + "/class/")
import public
from BTPanel import cache
from lua_maker import LuaMaker
from total_migrate import total_migrate
from tsqlite import tsqlite
import total_tools as tool


class totalBase:
    def __init__(self):
        self.plugin_path = '/www/server/total'
        self.frontend_path = '/www/server/panel/plugin/total'
        self.close_file = "/www/server/total/closing"
        self.data_dir = None
        self.history_data_dir = None
        self.global_region = {}
        self.total_db_name = "total.db"
        self.__config = {}

    def get_sites(self):
        '''
        获取网站信息
        @return:
        '''
        try:
            return public.M('sites').field('name').order("addtime").select()
        except Exception:
            return None

    def debug_log(self, msg):
        '''
        自己写的debug日志调试方法，用于区分面板的debug
        @param msg:
        @return:
        '''
        log_file = os.path.join(self.frontend_path, "error.log")
        if is_py3:
            with open(log_file, "a", encoding="utf-8") as fp:
                fp.write(msg + "\n")
        else:
            with open(log_file, "a") as fp:
                fp.write(msg + "\n")

    def set_module_total(self, module, name='total_plugin'):
        '''
        统计模块使用
        @param module:
        @param name:
        @return:
        '''
        with contextlib.suppress(Exception):
            public.set_module_logs(name, module, 1)

    def flush_data(self, host, site):
        '''
        刷新lua数据
        @param host:
        @param site:
        @return:
        '''
        with contextlib.suppress(Exception):
            import random
            no_flush_tag_file = os.path.join(self.frontend_path, "no_flush.pl")
            if os.path.exists(no_flush_tag_file): return
            flush_url = "http://{}:80/bt_total_flush_data?time={}{}\&server_name={}" \
                .format(host, time.time(), random.randint(0, 100), site)
            res = public.ExecShell("curl -m 5 {}".format(flush_url))
            ares = "".join(res)
            if "Connection timed out" in ares:
                public.WriteFile(no_flush_tag_file, ares)

    def get_siteName(self, siteName):
        '''
        获取网站名
        @param siteName:
        @return:
        '''
        try:
            db_file = self.plugin_path + '/total/logs/' + siteName + '/logs.db'
            if os.path.isfile(db_file): return siteName

            cache_key = "SITE_NAME" + "_" + siteName
            if cache.get(cache_key):
                return cache.get(cache_key)

            pid = public.M('sites').where('name=?', (siteName,)).getField('id')
            if not pid:
                cache.set(cache_key, siteName)
                return siteName

            domains = public.M('domain').where('pid=?', (pid,)).field(
                'name').select()
            for domain in domains:
                db_file = self.plugin_path + '/total/logs/' + domain["name"] + '/logs.db'
                if os.path.isfile(db_file):
                    siteName = domain['name']
                    break
            cache.set(cache_key, siteName.replace('_', '.'))
            return cache.get(cache_key)
        except Exception:
            return ""
    def get_migrate_status(self, get):
        '''
        获取监控报表迁移状态,是否需要迁移
        @param get:
        @return:
        '''
        tm = total_migrate()
        res = tm.get_migrate_status()
        status = res["status"] == "completed"
        if not status:
            check_path = "/www/server/total/total"
            if not os.path.isdir(check_path) or public.get_path_size(
                    check_path) == 0:
                tm.set_migrate_status("completed")
                return tm.get_migrate_status()
        return res

    def __read_frontend_config(self):
        '''
        读取监控报表配置文件
        @return:
        '''
        config_json = self.frontend_path + "/config.json"
        return (
            json.loads(public.readFile(config_json))
            if os.path.exists(config_json)
            else {}
        )

    def set_default_site(self, site):
        '''
        设置监控报表默认站点
        @param site:
        @return:
        '''
        config = self.__read_frontend_config()
        config["default_site"] = site
        config_json = self.frontend_path + "/config.json"
        public.writeFile(config_json, json.dumps(config))
        return True

    def get_default_site(self):
        '''
        获取监控报表默认站点
        @return:
        '''
        try:
            config = self.__read_frontend_config()
            default = config["default_site"] if "default_site" in config else None
            if not default:
                site = public.M('sites').field('name').order("addtime").find()
                default = site["name"]
            return default
        except Exception:
            return ""

    def switch_site(self, post):
        '''
        设置监控报表默认站点
        @param post:
        @return:
        '''
        if "request_in_panel" not in post: return
        site = post.site
        return (
            public.returnMsg(True, "已切换默认站点为{}".format(site))
            if self.set_default_site(site)
            else public.returnMsg(False, "切换默认站点失败。")
        )

    def get_file_json(self, filename, defaultv=None):
        '''
        封装取json格式的文件
        @param filename:
        @param defaultv:
        @return:
        '''
        if defaultv is None:
            defaultv = {}
        try:
            if not os.path.exists(filename): return defaultv
            return json.loads(public.readFile(filename))
        except Exception:
            os.remove(filename)
            return defaultv

    def get_site_settings(self, site):
        '''
        获取指定站点/全局配置文件
        @param site:
        @return:
        '''
        config_path = "/www/server/total/config.json"
        config = self.get_file_json(config_path)
        if not config:
            return {}

        res_config = {}
        if site not in config.keys():
            res_config = config["global"]
            res_config["push_report"] = False
        else:
            res_config = config[site]

        for k, v in config["global"].items():
            if k not in res_config.keys():
                res_config[k] = False if k == "push_report" else v
        res_config["default_site"] = self.get_default_site()
        return res_config

    def get_refresh_interval(self, site):
        '''
        获取自动刷新间隔,全局设置--刷新间隔
        @param site:
        @return:
        '''
        global_config = self.get_site_settings("global")
        return 10 if not global_config else global_config["refresh_interval"]

    def get_refresh_status(self, site):
        '''
        获取刷新状态,全局设置--是否自动刷新
        @param site:
        @return:
        '''
        global_config = self.get_site_settings("global")
        return False if not global_config else global_config["autorefresh"]

    def get_data_dir(self):
        '''
        获取监控报表日志存储目录
        @return:
        '''
        if self.data_dir is None:
            default_data_dir = os.path.join(self.plugin_path, "logs")
            settings = self.get_site_settings("global")
            if "data_dir" in settings.keys():
                config_data_dir = settings["data_dir"]
            else:
                config_data_dir = default_data_dir
            self.data_dir = default_data_dir if not config_data_dir else config_data_dir
        return self.data_dir

    def get_history_data_dir(self):
        '''
        获取监控报表历史日志存储目录
        @return:
        '''
        if self.history_data_dir is None:
            default_history_data_dir = os.path.join(self.plugin_path, "logs")
            settings = self.get_site_settings("global")
            if "history_data_dir" in settings.keys():
                config_data_dir = settings["history_data_dir"]
            else:
                config_data_dir = default_history_data_dir
            self.history_data_dir = (
                default_history_data_dir if not config_data_dir else config_data_dir
            )
        return self.history_data_dir

    def get_log_db_path(self, site, db_name="logs.db", history=False):
        '''
        获取指定网站日志存储路劲
        @param site:
        @param db_name:
        @param history:
        @return:
        '''
        site = site.replace('_', '.')
        if not history:
            data_dir = self.get_data_dir()
        else:
            data_dir = self.get_history_data_dir()
            db_name = "history_logs.db"
        return os.path.join(data_dir, site, db_name)

    def get_monitor_status(self, site):
        '''
        获取监控状态
        @param site:
        @return:
        '''
        # 获取全局配置文件
        global_config = self.get_site_settings("global")
        if not global_config["monitor"]:
            return True
        # 获取指定网站配置文件
        config = self.get_site_settings(site)
        return config["monitor"]

    def set_monitor_status(self, status):
        '''
        设置监控报表的总开关
        @param status:
        @return:
        '''
        if status == True:
            print("开启监控.")
            if os.path.isfile(self.close_file):
                os.remove(self.close_file)
            if os.path.isfile("/www/server/nginx/sbin/nginx"):
                command = [
                    "cp",
                    "-a",
                    "-r",
                    "/www/server/panel/plugin/total/total_nginx.conf",
                    "/www/server/panel/vhost/nginx/total.conf"
                ]
                subprocess.run(command, check=True)
            if os.path.isfile("/www/server/apache/bin/httpd"):
                command = [
                    "cp",
                    "-a",
                    "-r",
                    "/www/server/panel/plugin/total/total_httpd.conf",
                    "/www/server/panel/vhost/apache/total.conf"
                ]
                subprocess.run(command, check=True)
        else:
            public.WriteFile(self.close_file, "closing")
            subprocess.run(["rm", "-f", "/www/server/panel/vhost/nginx/total.conf"], check=True)
            subprocess.run(["rm", "-f", "/www/server/panel/vhost/apache/total.conf"], check=True)

    def write_lua_config(self, config=None):
        '''
        将配置文件转lua可用格式后写入
        @param config:
        @return:
        '''
        if not config:
            config = json.loads(public.readFile("/www/server/total/config.json"))
        lua_config = LuaMaker.makeLuaTable(config)
        lua_config = "return " + lua_config
        public.WriteFile("/www/server/total/total_config.lua", lua_config)

    def get_ip_rules(self):
        '''
        获取系统防火墙IP屏蔽规则列表
        @return:
        '''
        drop_list = public.M('firewall_ip').field("address").where("types=?", ("drop",)) \
            .order("addtime desc").select()
        if drop_list:
            if type(drop_list) == list:
                return [
                    obj["address"]
                    for obj in drop_list
                    if type(obj) == dict and "address" in obj
                ]
        return []

    # 数据库相关 -- 开始
    def init_ts(self, site, db_name):
        '''

        @param site:
        @param db_name:
        @return:
        '''
        self.init_site_db(site)
        db_path = self.get_log_db_path(site, db_name=db_name)
        ts = tsqlite()
        ts.dbfile(db_path)
        return ts

    def init_site_db(self, site):
        '''
        初始化数据库
        @param site:
        @return:
        '''
        tm = total_migrate()
        data_dir = self.get_data_dir()
        tm.init_site_db(site, target_data_dir=data_dir)

    def get_data_fields(self, query_date):
        '''
        获取数据查询字段
        @param query_date:
        @return:
        '''
        fields = ""
        flow_fields = ""
        spider_fields = ""

        # return "day_hour1", "flow_hour1", "spider_flow_hour1"
        now = time.localtime()
        last_month = now.tm_mon - 1
        if last_month <= 0:
            last_month = 12
        if query_date.startswith("l"):
            year = now.tm_year
            month = now.tm_mon
            day = now.tm_mday

            _, last_month_days = calendar.monthrange(year, last_month)
            days = int(query_date[1:])
            if days == 30:
                if last_month_days == 31:
                    days = 31

            for i in range(day, 0, -1):
                if fields:
                    fields += "+"
                fields += "day" + repr(i)

                if flow_fields:
                    flow_fields += "+"
                flow_fields += "flow" + repr(i)

                if spider_fields:
                    spider_fields += "+"
                spider_fields += "spider_flow" + repr(i)

                days -= 1
                if days <= 0:
                    break

            days = min(last_month_days, days)
            if days > 0:
                for i in range(last_month_days, 0, -1):
                    if fields:
                        fields += "+"
                    fields += "day" + repr(i)

                    if flow_fields:
                        flow_fields += "+"
                    flow_fields += "flow" + repr(i)

                    if spider_fields:
                        spider_fields += "+"
                    spider_fields += "spider_flow" + repr(i)

                    days -= 1
                    if days <= 0:
                        break

        elif query_date == "today":
            day = now.tm_mday
            fields = "day" + repr(day)
            flow_fields = "flow" + repr(day)
            spider_fields = "spider_flow" + repr(day)
        elif query_date == "yesterday":
            day = now.tm_mday
            if day > 1:
                yesterday = day - 1
                fields = "day" + repr(yesterday)
                flow_fields = "flow" + repr(yesterday)
                spider_fields = "spider_flow" + repr(yesterday)
            if day == 1:
                _, last_month_days = calendar.monthrange(now.tm_year, last_month)
                fields = "day" + repr(last_month_days)
                flow_fields = "flow" + repr(last_month_days)
                spider_fields = "spider_flow" + repr(last_month_days)
        elif query_date.find("-") > 0:
            _start, _end = query_date.split("-")
            start = time.strptime(_start, "%Y%m%d")
            day_start = int(time.strftime("%d", start))
            end = time.strptime(_end, "%Y%m%d")
            day_end = int(time.strftime("%d", end))
            if now.tm_mon == start.tm_mon:
                for i in range(day_end, 0, -1):
                    if fields:
                        fields += "+"
                    fields += "day" + repr(i)

                    if flow_fields:
                        flow_fields += "+"
                    flow_fields += "flow" + repr(i)

                    if spider_fields:
                        spider_fields += "+"
                    spider_fields += "spider_flow" + repr(i)

                    if i == day_start:
                        break
            else:
                for i in range(day_end, 0, -1):
                    if fields:
                        fields += "+"
                    fields += "day" + repr(i)

                    if flow_fields:
                        flow_fields += "+"
                    flow_fields += "flow" + repr(i)

                    if spider_fields:
                        spider_fields += "+"
                    spider_fields += "spider_flow" + repr(i)

                _, last_month_days = calendar.monthrange(now.tm_year, last_month)
                for j in range(last_month_days, day_start - 1, -1):
                    if fields:
                        fields += "+"
                    fields += "day" + repr(j)

                    if flow_fields:
                        flow_fields += "+"
                    flow_fields += "flow" + repr(j)

                    if spider_fields:
                        spider_fields += "+"
                    spider_fields += "spider_flow" + repr(i)
        elif query_date == "h1":
            return "day_hour1", "flow_hour1", "spider_flow_hour1"

        return fields, flow_fields, spider_fields

    # 数据库相关 -- 结束

    # ip相关 -- 开始
    def get_online_ip_library(self):
        '''
        获取ip精准包
        @return:
        '''
        request_addr = None
        with contextlib.suppress(Exception):
            from pluginAuth import Plugin
            tm = Plugin("btiplibrary")
            res = tm.get_fun("get_request_address")()
            if res and "status" in res and res["status"]:
                request_addr = res["msg"]
        return request_addr

    def get_ip_area_id(self, ip):
        '''
        获取ip区域id,按照ip2region区域搜索ip
        @param ip:
        @return:
        '''
        res = ""
        dbFile = "/www/server/panel/plugin/total/library/ip.db"
        if (not os.path.isfile(dbFile)) or (not os.path.exists(dbFile)):
            return res

        with contextlib.suppress(Exception):
            from ip2Region import Ip2Region
            searcher = Ip2Region(dbFile)
            info = searcher.binarySearch(ip)
            return info["city_id"] if "city_id" in info.keys() else res
        return ""

    def search_area(self, area_id):
        '''
        搜索ip区域,ip运营商
        @param area_id:
        @return:
        '''
        try:
            if not area_id:
                return "-"
            area_id = str(area_id)

            services = {
                "9999": "内网IP",
                "9998": "阿里云",
                "9997": "腾讯云",
                "9996": "华为云",
                "9995": "电信",
                "9994": "移动",
                "9993": "教育网",
                "9992": "联通"
            }
            if area_id in services.keys():
                return services[area_id]

            if not self.global_region:
                region_file = os.path.join("/www/server/panel/plugin/total", "global_region.csv")
                region_data = public.readFile(region_file)
                for region in region_data.split("\n"):
                    line = region.split(",")
                    if len(line) != 5: continue
                    self.global_region[line[0]] = line

            region = self.global_region.get(area_id, [])
            if len(region) == 5:
                city = region[2]
                _p = self.global_region.get(region[1], None)
                province = ""
                if _p:
                    province = _p[2]
                if province and province != city:
                    return province + "," + city
                else:
                    return city
        except Exception as e:
            print("Search area error: %s" % e)
        return "-"

    def get_ip_data_from_server(self, ips, request_addr=None):
        '''
        从服务器获取ip归属地等信息
        @param ips:
        @param request_addr:
        @return:
        '''
        try:
            # ip_record_json = self.__plugin_path()
            if not request_addr:
                request_addr = "https://www.bt.cn/api/panel/get_ip_info"
            if not ips:
                return None
            ips_text = ips
            if type(ips) == list:
                ips_text = ",".join(ips)
            elif type(ips) != str:
                ips_text = str(ips)
            data = {
                "ip": ips_text
            }
            if ips_text.find(",") == -1:
                online_cache_key = "ONLINE_AREA_" + ips_text
                cache_data = cache.get(online_cache_key)
                if cache_data:
                    return cache_data

            raw_res = public.httpPost(request_addr, data)
            if raw_res:
                try:
                    res = json.loads(raw_res)
                    if res and ips_text.find(",") == -1:
                        online_cache_key = "ONLINE_AREA_" + ips_text
                        cache.set(online_cache_key, res, 604800)
                    return res
                except:
                    pass
        except Exception as e:
            print("查询在线IPAPI出错: {}".format(e))
        return None

    def get_online_area(self, info):
        '''
        从在线IP库返回结果提取地区信息
        @param info:
        @return:
        '''
        area = ""
        country = info.get("country", "")
        if country == "保留":
            return "内网IP"
        province = info.get("province", "")
        city = info.get("city", "")
        region = info.get("region", "")

        if not region:
            if province and city:
                if province != city:
                    area = "{},{}".format(province, city)
                else:
                    area = province
        else:
            if city and province:
                if city != province:
                    area = "{},{},{}".format(province, city, region)
                else:
                    area = "{},{}".format(province, region)
            elif city:
                area = "{},{}".format(city, region)
            elif province:
                area = "{},{}".format(province, region)

        if not area:
            if country:
                if country == "中国":
                    if province:
                        area = province
                    else:
                        area = country
                else:
                    if province:
                        area = "{},{}".format(country, province)
                    else:
                        area = country
        return area

    # ip相关 -- 结束

    def empty_dict(self):
        '''
        @summary: 返回空的数据
        @return:
        '''
        return {
            "uri_count_stat": {
                "ip": 0,
                "pv": 0,
                "spider": 0,
                "uv": 0,
                "flow": 0,
                "spider_flow": 0
            },
            "uri_client_stat": {
                "count": {
                    "android": 0,
                    "iphone": 0,
                    "linux": 0,
                    "mac": 0,
                    "windows": 0
                },
                "client": {
                    "chrome": 0,
                    "edge": 0,
                    "firefox": 0,
                    "machine": 0,
                    "maxthon": 0,
                    "metasr": 0,
                    "msie": 0,
                    "opera": 0,
                    "other": 0,
                    "pc2345": 0,
                    "qh360": 0,
                    "qq": 0,
                    "safari": 0,
                    "theworld": 0,
                    "tt": 0,
                    "uc": 0,
                    "weixin": 0
                }
            },
            "uri_spider_stat": {
                "baidu": 0,
                "bing": 0,
                "bytes": 0,
                "dnspod": 0,
                "duckduckgo": 0,
                "google": 0,
                "mpcrawler": 0,
                "other": 0,
                "qh360": 0,
                "sogou": 0,
                "soso": 0,
                "yahoo": 0,
                "yandex": 0,
                "yisou": 0,
                "youdao": 0
            },
            "uri_flow_stat": {
                "baidu_flow": 0,
                "bing_flow": 0,
                "bytes_flow": 0,
                "dnspod_flow": 0,
                "duckduckgo_flow": 0,
                "google_flow": 0,
                "mpcrawler_flow": 0,
                "other_flow": 0,
                "qh360_flow": 0,
                "sogou_flow": 0,
                "soso_flow": 0,
                "yahoo_flow": 0,
                "yandex_flow": 0,
                "yisou_flow": 0,
                "youdao_flow": 0
            }
        }