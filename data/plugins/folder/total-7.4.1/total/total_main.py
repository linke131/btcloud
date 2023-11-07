# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyleft (c) 2015-2099 宝塔软件(http://bt.cn) All lefts reserved.
# +-------------------------------------------------------------------
# | Author: linxiao
# | Author: lifu
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   宝塔网站监控报表
# +--------------------------------------------------------------------
from __future__ import absolute_import, division, print_function

import calendar
import datetime
import json
import os
import re
import sys
import time
import ipaddress
import psutil
import tarfile


_ver = sys.version_info
is_py2 = (_ver[0] == 2)
is_py3 = (_ver[0] == 3)

os.chdir("/www/server/panel")
sys.path.insert(0, "class/")

import public
from BTPanel import cache, get_input
from panelAuth import panelAuth

from lua_maker import LuaMaker
from total_migrate import total_migrate
from tsqlite import tsqlite
import total_tools as tool


class total_main:
    __plugin_path = '/www/server/total'
    __frontend_path = '/www/server/panel/plugin/total'
    __config = {}
    close_file = "/www/server/total/closing"
    data_dir = None
    history_data_dir = None
    global_region = {}
    total_db_name = "total.db"
    line_size = 400
    access_defs = [
        "get_site_overview_sum_data",
        "get_ip_stat",
        "get_uri_stat",
        "generate_area_stat",
        "get_area_stat",
        "init_ts",
        "get_referer_stat",
        "update_spiders_from_cloud",
        "get_online_ip_library"
    ]

    def __init__(self):
        self.area_cache_file = self.__frontend_path + "/area_cache.json"

    def log(self, msg):
        log_file = os.path.join(self.__frontend_path, "error.log")
        if is_py3:
            with open(log_file, "a", encoding="utf-8") as fp:
                fp.write(msg + "\n")
        else:
            with open(log_file, "a") as fp:
                fp.write(msg + "\n")

    def flush_data(self, site):
        try:
            import random
            no_flush_tag_file = os.path.join(self.__frontend_path, "no_flush.pl")
            if os.path.exists(no_flush_tag_file): return
            flush_url = "http://127.0.0.1:80/bt_total_flush_data?time=" + str(time.time()) + str(random.randint(0, 100)) + "\&server_name=" + site
            res = public.ExecShell("curl -m 5 " + flush_url)
            ares = "".join(res)
            if ares.find("Connection timed out") != -1:
                public.WriteFile(no_flush_tag_file, ares)
        except Exception as e:
            pass
            # public.WriteFile(no_flush_tag_file, str(e))

    def get_config(self, site=None):
        if self.__config and site in self.__config.keys(): return self.__config[site]
        data = public.readFile(self.__plugin_path + '/config.json')
        config = json.loads(data)
        if site in config.keys():
            global_config = config["global"]
            for k, v in global_config.items():
                if k not in config[site].keys():
                    config[site][k] = global_config[k]
            if not global_config["monitor"]:
                config[site]["monitor"] = False
            self.__config[site] = config[site]
        else:
            self.__config[site] = config["global"]
        return self.__config[site]

    def set_status(self, get):
        self.__read_config()
        self.__config['global']["monitor"] = not self.__config['global']['monitor']
        self.__write_config()
        self.__write_logs("设置网站监控插件状态为[%s]" % (self.__config['global']['monitor'],))
        return public.returnMsg(True, '设置成功!')

    def set_site_value(self, get):
        self.__read_config()
        site = ""
        if "siteName" in get:
            site = get.siteName
        if "site" in get:
            site = get.site

        if type(self.__config[site][get.s_key]) == bool:
            get.s_value = not self.__config[site][get.s_key]
        elif type(self.__config[get.siteName][get.s_key]) == int:
            get.s_value = int(get.s_value)
        self.__config[get.siteName][get.s_key] = get.s_value
        self.__write_logs(
            "设置网站[%s]的[%s]配置项为[%s]" % (site, get.s_key, get.s_value))
        self.__write_config()
        return public.returnMsg(True, '设置成功!')

    def get_total_ip(self, get):
        self.__read_config()
        data = {}
        data['total_ip'] = self.__config['sites'][get.siteName]['total_ip']
        data['total_uri'] = self.__config['sites'][get.siteName]['total_uri']
        return data

    def add_total_ip(self, get):
        self.__read_config()
        if get.ip in self.__config['sites'][get.siteName][
            'total_ip']: return public.returnMsg(False, '指定URI已存在!')
        self.__config['sites'][get.siteName]['total_uri'][get.uri_name] = 0
        self.__write_logs("向网站[%s]添加自定义统计IP[%s]" % (get.siteName, get.ip))
        self.__write_config()
        return public.returnMsg(False, '添加成功!')

    def remove_total_ip(self, get):
        self.__read_config()
        del (self.__config['sites'][get.siteName]['total_ip'][get.ip])
        self.__write_logs("从网站[%s]删除自定义统计IP[%s]" % (get.siteName, get.ip))
        self.__write_config()
        return public.returnMsg(False, '删除成功!')

    def get_total_uri(self, get):
        self.__read_config()
        return self.__config['sites'][get.siteName]['total_uri']

    def add_total_uri(self, get):
        self.__read_config()
        if get.uri_name in self.__config['sites'][get.siteName][
            'total_uri']: return public.returnMsg(False, '指定URI已存在!')
        self.__config['sites'][get.siteName]['total_uri'][get.uri_name] = 0
        self.__write_logs(
            "向网站[%s]添加自定义统计URI[%s]" % (get.siteName, get.uri_name))
        self.__write_config()
        return public.returnMsg(False, '添加成功!')

    def remove_total_uri(self, get):
        self.__read_config()
        del (self.__config['sites'][get.siteName]['total_uri'][get.uri_name])
        self.__write_logs(
            "从网站[%s]删除自定义统计URI[%s]" % (get.siteName, get.uri_name))
        self.__write_config()
        return public.returnMsg(False, '删除成功!')

    def get_log_exclude_status(self, get):
        site = ""
        if "siteName" in get:
            site = get.siteName
        if "site" in get:
            site = get.site
        self.__read_config()
        return self.__config[site]['exclude_status']

    def add_log_exclude_status(self, get):
        site = ""
        if "siteName" in get:
            site = get.siteName
        if "site" in get:
            site = get.site
        self.__read_config()
        if get.status in self.__config[site]['exclude_status']:
            return public.returnMsg(False, '指定响应状态已存在!')
        self.__config[site]['exclude_status'].insert(0, get.status)
        self.__write_logs("向网站[%s]添加响应状态排除[%s]" % (site, get.status))
        self.__write_config()
        return public.returnMsg(False, '添加成功!')

    def remove_log_exclude_status(self, get):
        site = ""
        if "siteName" in get:
            site = get.siteName
        if "site" in get:
            site = get.site
        self.__read_config()
        status = get.status
        self.__write_logs("从网站[%s]删除响应状态排除[%s]" % (site, status))
        self.__config[site]['exclude_status'].remove(status)
        self.__write_config()
        return public.returnMsg(False, '删除成功!')

    def get_log_exclude_extension(self, get):
        site = ""
        if "siteName" in get:
            site = get.siteName
        if "site" in get:
            site = get.site
        return self.__config[site]['exclude_extension']

    def add_log_exclude_extension(self, get):
        site = ""
        if "siteName" in get:
            site = get.siteName
        if "site" in get:
            site = get.site
        self.__read_config()
        if get.ext_name in self.__config[site]['exclude_extension']: return public.returnMsg(False, '指定扩展名已存在!')
        self.__config[site]['exclude_extension'].insert(0, get.ext_name)
        self.__write_logs("向网站[%s]添加扩展名排除[%s]" % (site, get.ext_name))
        self.__write_config()
        return public.returnMsg(False, '添加成功!')

    def get_global_total(self, get):
        self.__read_config()
        data = {}
        data['client'] = self.__get_file_json(
            self.__plugin_path + '/total/client.json')
        data['area'] = self.__get_file_json(
            self.__plugin_path + '/total/area.json')
        data['network'] = self.__get_file_json(
            self.__plugin_path + '/total/network.json')
        data['request'] = self.__get_file_json(
            self.__plugin_path + '/total/request.json')
        data['spider'] = self.__get_file_json(
            self.__plugin_path + '/total/spider.json')
        data['open'] = self.__config['open']
        return data

    def get_sites(self, get):
        # self._check_site()
        if os.path.exists('/www/server/apache'):
            if not os.path.exists('/usr/local/memcached/bin/memcached'):
                return public.returnMsg(False, '需要memcached,请先到【软件管理】页面安装!')
            if not os.path.exists('/var/run/memcached.pid'):
                return public.returnMsg(False, 'memcached未启动,请先启动!')
        # modc = self.__get_mod(get)
        # if not cache.get('bt_total'):  return modc
        result = {}
        data = []

        res = self.get_site_lists(get)
        if not res["status"]:
            return data
        site_lists = res["data"]
        for siteName in site_lists:
            tmp = {}
            tmp['total'] = self.__get_site_total(siteName)
            tmp['site_name'] = siteName
            data.append(tmp)
        data = sorted(data, key=lambda x: x['total']['request'], reverse=True)
        data = sorted(data, key=lambda x: x['total']['day_request'],
                      reverse=True)
        result['data'] = data
        result['open'] = self.get_config()['monitor']
        tool.write_site_domains()
        return result

    def __get_mod(self, get):
        if cache.get('bt_total'): return public.returnMsg(True, 'OK!')
        tu = '/proc/sys/net/ipv4/tcp_tw_reuse'
        if public.readFile(tu) != '1': public.writeFile(tu, '1')
        params = {}
        params['pid'] = '100000014'
        result = panelAuth().send_cloud('check_plugin_status', params)
        try:
            if not result['status']:
                if cache.get('bt_total'): cache.delete('bt_total')
                return result
        except:
            pass
        cache.set('bt_total', True)
        return result

    def get_history_data_dir(self):
        if self.history_data_dir is None:
            default_history_data_dir = os.path.join(self.__plugin_path, "logs")
            settings = self.get_site_settings("global")
            if "history_data_dir" in settings.keys():
                config_data_dir = settings["history_data_dir"]
            else:
                config_data_dir = default_history_data_dir
            self.history_data_dir = default_history_data_dir if not config_data_dir else config_data_dir
        return self.history_data_dir

    def get_data_dir(self):
        if self.data_dir is None:
            default_data_dir = os.path.join(self.__plugin_path, "logs")
            settings = self.get_site_settings("global")
            if "data_dir" in settings.keys():
                config_data_dir = settings["data_dir"]
            else:
                config_data_dir = default_data_dir
            self.data_dir = default_data_dir if not config_data_dir else config_data_dir
        return self.data_dir

    def get_log_db_path(self, site, db_name="logs.db", history=False):
        site = site.replace('_', '.')
        if not history:
            data_dir = self.get_data_dir()
            db_path = os.path.join(data_dir, site, db_name)
        else:
            data_dir = self.get_history_data_dir()
            db_name = "history_logs.db"
            db_path = os.path.join(data_dir, site, db_name)
        return db_path

    def get_realtime_request(self, site=None):
        """获取实时请求数"""
        res_data = []
        if site is not None:
            log_file = self.__plugin_path + "/logs/{}/req_sec.json".format(site)
            if not os.path.isfile(log_file):
                return res_data

            datetime_now = datetime.datetime.now()
            req_data = public.readFile(log_file)
            lines = req_data.split("\n")
            for line in lines:
                if not line: continue
                try:
                    _rt_req, _write_time = line.split(",")
                    datetime_log = datetime.datetime.fromtimestamp(
                        float(_write_time))
                    # print(datetime_log.strftime("%y%m%d %H:%M:%S"))
                    datetime_interval = datetime_now - datetime_log
                    # print("interval:", datetime_interval.seconds)
                    if datetime_interval.seconds < 3:
                        data = {"timestamp": _write_time, "req": int(_rt_req)}
                        res_data.append(data)

                except Exception as e:
                    print("Real-time data error:", str(e))
            if len(res_data) > 1:
                res_data.sort(key=lambda o: o["timestamp"], reverse=True)
        return res_data

    def get_realtime_traffic(self, site=None):
        """获取实时流量"""
        res_data = []
        if site is not None:
            flow_file = self.__plugin_path + "/logs/{}/flow_sec.json".format(
                site)
            if not os.path.isfile(flow_file):
                return res_data
            flow_data = public.readFile(flow_file)
            datetime_now = datetime.datetime.now()
            # print("Now:", datetime_now.strftime("%Y%m%d %H:%M:%S"))
            # print("Now:", datetime_now.timestamp())
            lines = flow_data.split("\n")
            for line in lines:
                if not line: continue
                try:
                    _flow, _write_time = line.split(",")
                    datetime_log = datetime.datetime.fromtimestamp(
                        float(_write_time))
                    datetime_interval = datetime_now - datetime_log
                    if datetime_interval.seconds < 3:
                        # print("flow interval by datetime:", datetime_interval.seconds)
                        # print(datetime_log.strftime("%Y%m%d %H:%M:%S"), _flow)
                        data = {"timestamp": _write_time, "flow": int(_flow)}
                        res_data.append(data)

                except Exception as e:
                    print("Real-time traffic error:", str(e))
            if len(res_data) > 1:
                res_data.sort(key=lambda o: o["timestamp"], reverse=True)
        return res_data

    def get_refresh_interval(self, site):
        global_config = self.get_site_settings("global")
        if not global_config:
            return 10
        return global_config["refresh_interval"]

    def get_refresh_status(self, site):
        global_config = self.get_site_settings("global")
        if not global_config:
            return False
        return global_config["autorefresh"]

    def get_monitor_status(self, site):
        global_config = self.get_site_settings("global")
        if not global_config["monitor"]:
            return True
        config = self.get_site_settings(site)
        return config["monitor"]

    def init_site_db(self, site):
        """初始化数据库"""
        tm = total_migrate()
        data_dir = self.get_data_dir()
        tm.init_site_db(site, target_data_dir=data_dir)

    def init_ts(self, site, db_name):
        self.init_site_db(site)
        db_path = self.get_log_db_path(site, db_name=db_name)
        ts = tsqlite()
        ts.dbfile(db_path)
        return ts

    def get_overview_list_data(self, site, start_date, end_date, time_scale="day"):
        """获取概览页列表数据

        Args:
            site (str): 网站名
            start_date (time): 起始时间
            end_date (time): 终止时间
            time_scale (str, optional): 时间颗粒度. Defaults to "day".
        """
        ts = self.init_ts(site, self.total_db_name)
        list_data = []
        if not ts:
            return list_data
        default_fields = "req,pv,uv,ip,length,spider,fake_spider"
        # 统计数据
        s50x_fields = ",status_500,status_501,status_502,status_503,status_504,status_505,status_506,status_507,status_509,status_510"
        s40x_fields = ",status_400,status_401,status_402,status_403,status_404,status_405,status_406,status_407,status_408,status_409,status_410,status_411,status_412,status_413,status_414,status_415,status_416,status_417,status_418,status_421,status_422,status_423,status_424,status_425,status_426,status_449,status_451"
        http_method_fields = ",http_get,http_put,http_post,http_patch,http_delete"
        if time_scale == "day":
            table_fieds = default_fields + s50x_fields + s40x_fields + http_method_fields
            sum_fields = ""
            for f in table_fieds.split(","):
                f = "sum(" + f + ") as " + f
                if sum_fields:
                    sum_fields += ","
                sum_fields += f
            total_fields = "time/100 as time1," + sum_fields
            ts.table("request_stat").field(total_fields).groupby("time1")
            ts.where("time >=? and time <=?", (start_date, end_date))
            ts.order("time1 desc")
        else:
            total_fields = "time," + default_fields + s50x_fields + s40x_fields + http_method_fields
            ts.table("request_stat").field(total_fields)
            ts.where("time >=? and time <=?", (start_date, end_date))
            ts.order("time desc")
        list_data = ts.select()

        import copy
        res_data = copy.deepcopy(list_data)
        for i in range(0, len(list_data)):
            item = list_data[i]
            x50 = {}
            x40 = {}
            for k, v in item.items():
                if k.startswith("status_5"):
                    x50[k.replace("status_", "")] = v
                    res_data[i].pop(k)
                if k.startswith("status_4"):
                    xk = k.replace("status_", "")
                    if int(xk) > 417:
                        res_data[i].pop(k)
                        continue
                    x40[xk] = v
                    res_data[i].pop(k)
            res_data[i]["50x"] = x50
            res_data[i]["40x"] = x40

        # print(list_data)
        return res_data

    def get_site_overview_sum_data(self, site, start_date, end_date):
        """获取站点概览页的统计数据"""
        ts = self.init_ts(site, self.total_db_name)
        sum_data = {}
        default_fields = "req,pv,uv,ip,length,spider,s50x,s40x"
        if not ts:
            for field in default_fields.split(","):
                sum_data[field] = 0
            return sum_data
        # 统计数据
        s50x_fields = ",sum(status_500+status_501+status_502+status_503+status_504+status_505+status_506+status_507+status_509+status_510) as s50x"
        s40x_fields = ",sum(status_400+status_401+status_402+status_403+status_404+status_405+status_406+status_407+status_408+status_409+status_410+status_411+status_412+status_413+status_414+status_415+status_416+status_417+status_418+status_421+status_422+status_423+status_424+status_425+status_426+status_449+status_451+status_499) as s40x"
        total_fields = "sum(req) as req, sum(pv) as pv, sum(uv) as uv, sum(ip) as ip, sum(length) as length, sum(spider) as spider, sum(fake_spider) as fake_spider"
        total_fields += s50x_fields + s40x_fields
        ts.table("request_stat").field(total_fields)
        ts.where("time between ? and ?", (start_date, end_date))
        sum_data = ts.find()
        # print("sum data:")
        # print(sum_data)

        if type(sum_data) != dict:
            for field in default_fields.split(","):
                sum_data[field] = 0
            return sum_data

        for key, value in sum_data.items():
            if not value:
                sum_data[key] = 0

        return sum_data

    def get_all_site_overview(self, site, start_date, end_date):
        """获取站点概览页的统计数据"""
        ts = self.init_ts(site, self.total_db_name)
        sum_data = {}
        default_fields = "req,pv,uv,ip,length"
        if not ts:
            for field in default_fields.split(","):
                sum_data[field] = 0
            return sum_data
        # 统计数据
        total_fields = "sum(req) as req, sum(pv) as pv, sum(uv) as uv, sum(ip) as ip, sum(length) as length"
        ts.table("request_stat").field(total_fields)
        ts.where("time between ? and ?", (start_date, end_date))
        sum_data = ts.find()

        if type(sum_data) != dict:
            for field in default_fields.split(","):
                sum_data[field] = 0
            return sum_data

        for key, value in sum_data.items():
            if not value:
                sum_data[key] = 0

        return sum_data

    def get_overview_by_day(self, site, start_date, end_date, time_scale="hour",
                            target=None):
        """获取某一段时间的概览数据"""
        data = []
        sum_data = {}

        ts = self.init_ts(site, self.total_db_name)
        if not ts:
            return data, self.get_site_overview_sum_data(site, start_date,
                                                         end_date)

        if target is None:
            target = "pv"

        allow_target = ["pv", "uv", "ip", "req", "length", "spider", "s50x", "s40x"]
        if target in allow_target:
            # 绘图数据
            if time_scale == "hour":
                ts.table("request_stat").field("time," + target)
                ts.where("time between ? and ?", (start_date, end_date))
                ts.order("time")
            elif time_scale == "day":
                sum_fields = "sum(" + target + ") as " + target
                sum_fields = "time/100 as time1," + sum_fields
                ts.table("request_stat").groupby("time1").field(sum_fields)
                ts.where("time between ? and ?", (start_date, end_date))
                ts.order("time1")

            data = ts.select()
            if type(data) != list:
                data = []
            if time_scale == "day":
                for d in data:
                    d["time"] = d["time1"]
                    del d["time1"]

        sum_data = self.get_site_overview_sum_data(site, start_date, end_date)
        return data, sum_data

    def get_site_overview(self, get):
        try:
            # 写入安装时间

            site = self.__get_siteName(get.site)
            query_date = "today"
            if 'query_date' in get:
                query_date = get.query_date
            target = "pv"
            if 'target' in get:
                target = get.target
            time_scale = 'hour'
            if 'time_scale' in get:
                time_scale = get.time_scale
            compare = False
            if 'compare' in get:
                compare = True if get.compare.lower() == "true" else False
            compare_date = "yesterday"
            if compare:
                if 'compare_date' in get:
                    compare_date = get.compare_date
            request_time = None
            if 'request_data_time' in get:
                request_time = get.request_data_time
            list_display = False
            if "list_display" in get:
                list_display = True if get.list_display.lower() == "true" else False

            self.set_module_total('get_site_overview')
            # print("display: {}".format(get.list_display))
            # if request_time is not None:
            #     print("请求时间{}以后的数据。".format(request_time))

            self.flush_data(site)
            data = []
            sum_data = {}
            compare_data = []
            compare_sum_data = {}

            start_date, end_date = tool.get_query_date(query_date)
            compare_start_date, compare_end_date = 0, 0
            # print("查询时间周期: {} - {}".format(start_date, end_date))
            if not list_display:
                if request_time is not None:
                    data, sum_data = self.get_overview_by_day(
                        site, request_time, end_date,
                        time_scale=time_scale, target=target)
                else:
                    data, sum_data = self.get_overview_by_day(
                        site, start_date, end_date,
                        time_scale=time_scale, target=target)

                if compare:
                    compare_start_date, compare_end_date = tool.get_compare_date(
                        start_date, compare_date)
                    # print("对比时间周期: {} - {}".format(compare_start_date, compare_end_date))
                    compare_data, compare_sum_data = self.get_overview_by_day(
                        site, compare_start_date, compare_end_date,
                        time_scale=time_scale, target=target)
            else:
                data = self.get_overview_list_data(site, start_date, end_date, time_scale=time_scale)

            realtime_req = self.get_realtime_request(site=site)
            realtime_traffic = self.get_realtime_traffic(site=site)

            request_time = tool.get_time_key()
            res_query_date = "{}-{}".format(start_date, end_date)
            res_compare_date = ""
            if compare:
                res_compare_date = "{}-{}".format(compare_start_date,
                                                  compare_end_date)

            migrate = self.get_migrate_status({})
            migrate_status = False
            if migrate["status"] == "completed":
                migrate_status = True

            online_data = self.get_online_ip_library()
            firewall_installed = os.path.exists("/www/server/panel/plugin/firewall")

            res_data = {
                "status": True,
                "query_date": res_query_date,
                "target": target,
                "time_scale": time_scale,
                "data": data,
                "sum_data": sum_data,
                "realtime_request": realtime_req,
                "realtime_traffic": realtime_traffic,
                "compare": compare,
                "compare_date": res_compare_date,
                "compare_data": compare_data,
                "compare_sum_data": compare_sum_data,
                "request_data_time": request_time,
                "migrated": migrate_status,
                "autorefesh": self.get_refresh_status(site),
                "refresh_interval": self.get_refresh_interval(site),
                "monitor": self.get_monitor_status(site),
                "online_data": online_data is not None,
                "sys_firewall": firewall_installed
            }
            self.switch_site(get)
            return res_data
        except Exception as e:
            return tool.returnMsg(
                False,
                "REQUEST_INTERFACE_ERROR",
                args=(tool.getMsg("INTERFACE_SITE_OVERVIEW"), str(e),)
            )

    def get_top_spiders(self, site, start_date, end_date, target, top):
        ts = self.init_ts(site, self.total_db_name)
        sum_fields = ""
        top = 10
        spiders = []
        if not ts:
            return []

        if not target or target == "top":
            table_name = "spider_stat"
            columns = ts.query("PRAGMA table_info([{}])".format(table_name))
            sum_fields = ""
            # 动态生成数据列
            for column in columns:
                client_name = column[1]
                if client_name == "time": continue
                if client_name.find("_flow") > 0: continue
                if sum_fields:
                    sum_fields += ","
                sum_fields += "sum(" + client_name + ") as " + client_name

            ts.table("spider_stat").field(sum_fields)
            ts.where("time between ? and ?", (start_date, end_date))
            sum_data = ts.find()
            # print("sum data:", sum_data)
            top_columns = []
            # print(sorted(sum_data, key=lambda kv:(kv[1], kv[0]), reverse=True))
            if len(sum_data) and type(sum_data) != str:
                _columns = sorted(sum_data.items(),
                                  key=lambda kv: (kv[1], kv[0]),
                                  reverse=True)
                for i in range(len(_columns)):
                    if i == top: break
                    top_columns.append(_columns[i][0])
        else:
            if target.find(",") >= 0:
                top_columns = target.split(",")
            else:
                top_columns = [target]
        return top_columns

    def get_spider_by_day(self, get):
        """获取某一天的蜘蛛详细统计 """
        try:
            site = self.__get_siteName(get.site)
            query_date = "today"
            if "query_date" in get:
                query_date = get.query_date

            start_date, end_date = tool.get_query_date(query_date)
            db_path = self.get_log_db_path(site, db_name=self.total_db_name)
            if not os.path.isfile(db_path):
                return public.returnMsg(False, "蜘蛛统计数据为空!")
            ts = tsqlite()
            ts.dbfile(db_path)
            ts.table("spider_stat")
            ts.where("time between ? and ?", (start_date, end_date))
            data = ts.select()
            return data
        except Exception as e:
            return public.returnMsg(False, "获取蜘蛛统计明细出现错误！")

    def get_site_spider_stat_by_time_interval(self, site, start_date, end_date,
                                              time_scale="hour", target=None):
        """获取某一时间区间的蜘蛛统计数据
        :site 站点名
        :start_date 起始时间
        :end_date 终止时间
        :time_scale 时间刻度
        :target 绘图指标
        """
        data = []
        sum_data = {}

        db_path = self.get_log_db_path(site, db_name=self.total_db_name)
        if not os.path.isfile(db_path):
            return data, sum_data

        ts = tsqlite()
        ts.dbfile(db_path)
        new_target = ""
        top_columns = target
        top = len(top_columns)

        # 2. 根据统计数据查询图表数据
        if time_scale == "hour":
            fields = ",".join(top_columns)
            fields = "time," + fields
            ts.table("spider_stat").field(fields)
            ts.where("time between ? and ?", (start_date, end_date))
            data = ts.select()
        elif time_scale == "day":
            fields = ""
            for i, col in enumerate(top_columns):
                if i == top: break
                if fields:
                    fields += ","
                fields += "sum(" + col + ") as " + col
            # print("fields :", fields)
            # print("start:{}/end:{}".format(start_date, end_date))
            ts.table("spider_stat").field(fields)
            ts.where("time between ? and ?", (start_date, end_date))
            _data = ts.find()
            for column in top_columns:
                data.append({column: _data[column]})

        total_data = {}
        table_name = "spider_stat"
        columns = ts.query("PRAGMA table_info([{}])".format(table_name))
        sum_fields = ""
        # 动态生成数据列
        for column in columns:
            client_name = column[1]
            if client_name == "time": continue
            if client_name.find("_flow") > 0: continue
            if sum_fields:
                sum_fields += "+"
            sum_fields += client_name
        total_field = "sum(" + sum_fields + ") as total"
        ts.table(table_name).field(total_field)
        ts.where("time between ? and ?", (start_date, end_date))
        total_res = ts.find()
        total_data["spider_total"] = total_res["total"]

        # 补充总请求数
        ts.table("request_stat").field("sum(req) as req, sum(fake_spider) as fake_spider")
        ts.where("time between ? and ?", (start_date, end_date))
        total_req = ts.find()
        if total_req:
            total_data["total_req"] = total_req["req"]
            total_data["fake_spider"] = total_req["fake_spider"]
        else:
            total_data["total_req"] = 0
            total_data["fake_spider"] = 0

        return data, total_data

    def get_spider_list(self, site, start_date, end_date, order="time",
                        desc=True, page_size=20, page=1):
        """获取蜘蛛统计列表数据"""

        list_data = []
        total_row = 0
        ts = self.init_ts(site, self.total_db_name)
        if not ts:
            return list_data, total_row

        sum_fields = ""
        table_name = "spider_stat"
        columns = ts.query("PRAGMA table_info([{}])".format(table_name))
        sum_fields = ""
        # 动态生成数据列
        for column in columns:
            client_name = column[1]
            if client_name == "time": continue
            if sum_fields:
                sum_fields += ","
            sum_fields += "sum(" + client_name + ") as " + client_name

        # 列表数据查询
        list_fields = "time/100 as time1, " + sum_fields
        list_fields += ",sum(other) as other"
        ts.table("spider_stat").field(list_fields).groupby("time1")
        # ts.where("time between ? and ?", (start_date, end_date))
        if "time" == order:
            order = "time1"
        if desc:
            order += " desc"
        page_start = (page - 1) * page_size
        ts.order(order)
        list_data = ts.select()
        total_row = len(list_data)
        list_data = list_data[page_start:page_start + page_size]
        for d in list_data:
            d["time"] = d["time1"]
            del d["time1"]
        return list_data, total_row

    def get_spider_stat(self, get):
        try:
            site = self.__get_siteName(get.site)
            query_date = "today"
            if 'query_date' in get:
                query_date = get.query_date
            time_scale = 'hour'
            if 'time_scale' in get:
                time_scale = get.time_scale
            compare = False
            if 'compare' in get:
                compare = True if get.compare.lower() == "true" else False
            compare_date = "yesterday"
            if compare:
                if 'compare_date' in get:
                    compare_date = get.compare_date
            target = "top"
            if "target" in get:
                target = get.target
            request_time = None
            if 'request_data_time' in get:
                request_time = get.request_data_time
            page = 1
            if "page" in get:
                page = int(get.page)
            page_size = 20
            if "page_size" in get:
                page_size = int(get.page_size)
            orderby = "time"
            if "orderby" in get:
                orderby = get.orderby
            desc = True
            if "desc" in get:
                desc = True if get.desc.lower() == "true" else False
            # if request_time is not None:
            #     print("请求时间{}以后的数据。".format(request_time))

            self.set_module_total('get_spider_stat')
            data = []
            sum_data = {}
            compare_data = []
            compare_sum_data = {}
            list_data = []
            total_row = 0

            start_date, end_date = tool.get_query_date(query_date)
            # print("查询时间周期: {} - {}".format(start_date, end_date))

            db_path = self.get_log_db_path(site, db_name=self.total_db_name)

            request_time = tool.get_time_key()
            res_query_date = "{}-{}".format(start_date, end_date)
            res_compare_date = ""
            if not os.path.isfile(db_path):
                # print("监控数据为空。")
                return {
                    "status": True,
                    "query_date": res_query_date,
                    "data": data,
                    "sum_data": sum_data,
                    "compare": compare,
                    "compare_date": res_compare_date,
                    "compare_data": compare_data,
                    "compare_sum_data": compare_sum_data,
                    "request_data_time": request_time,
                    "page": page,
                    "page_size": page_size,
                    "total_row": total_row,
                    "list_data": list_data,
                    "autorefesh": self.get_refresh_status(site),
                    "monitor": self.get_monitor_status(site)
                }

            self.flush_data(site)
            top = 5
            # self.log("site:" + site)
            top_columns = self.get_top_spiders(site, start_date, end_date,
                                               target, top)
            if request_time is not None:
                # 默认top的情况下，每次重新请求
                if target and target != "top":
                    data, sum_data = self.get_site_spider_stat_by_time_interval(
                        site, request_time, end_date, time_scale=time_scale,
                        target=top_columns)
                else:
                    data, sum_data = self.get_site_spider_stat_by_time_interval(
                        site, start_date, end_date, time_scale=time_scale,
                        target=top_columns)
                list_data, total_row = self.get_spider_list(site, request_time,
                                                            end_date,
                                                            order=orderby,
                                                            desc=desc,
                                                            page_size=page_size,
                                                            page=page)
            else:
                data, sum_data = self.get_site_spider_stat_by_time_interval(
                    site, start_date, end_date, time_scale=time_scale,
                    target=top_columns)
                list_data, total_row = self.get_spider_list(site, start_date,
                                                            end_date,
                                                            order=orderby,
                                                            desc=desc,
                                                            page_size=page_size,
                                                            page=page)

            if compare:
                compare_start_date, compare_end_date = tool.get_compare_date(
                    start_date, compare_date)
                # print("对比时间周期: {} - {}".format(compare_start_date, compare_end_date))
                compare_data, compare_sum_data = self.get_site_spider_stat_by_time_interval(
                    site, compare_start_date, compare_end_date,
                    time_scale=time_scale, target=top_columns)
                res_compare_date = "{}-{}".format(compare_start_date,
                                                  compare_end_date)

            res_data = {
                "status": True,
                "query_date": res_query_date,
                "data": data,
                "sum_data": sum_data,
                "compare": compare,
                "compare_date": res_compare_date,
                "compare_data": compare_data,
                "compare_sum_data": compare_sum_data,
                "request_data_time": request_time,
                "page": page,
                "page_size": page_size,
                "total_row": total_row,
                "list_data": list_data,
                "autorefesh": self.get_refresh_status(site),
                "monitor": self.get_monitor_status(site)
            }
            self.switch_site(get)
            return res_data
        except Exception as e:
            return tool.returnMsg(
                False,
                "REQUEST_INTERFACE_ERROR",
                args=(
                    tool.getMsg("INTERFACE_SPIDER_STAT"),
                    str(e),
                )
            )

    def update_spiders_from_cloud(self, get=None):
        """从云端更新蜘蛛IP库

        Returns:
            bool: true/false 是否更新成功
        """
        try:
            userInfo = json.loads(public.ReadFile('/www/server/panel/data/userInfo.json'))
            data22 = {"access_key": userInfo['access_key'], "uid": userInfo['uid']}
            url = public.GetConfigValue('home')+'/api/bt_waf/getSpiders'
            data_list = json.loads(public.httpPost(url, data22, timeout=3))
            has_content = False
            # print("蜘蛛种类: {}".format(len(data_list)))
            # print(data_list)
            if data_list:
                spiders_dir = "/www/server/total/xspiders"
                if not os.path.exists(spiders_dir):
                    os.mkdir(spiders_dir)
                for i22 in data_list:
                    try:
                        path = "%s/%s.json" % (spiders_dir, i22)
                        if os.path.exists(path):
                            ret = json.loads(public.ReadFile(path))
                            localhost_json = list(set(ret).union(data_list[i22]))
                        else:
                            localhost_json = data_list[i22]
                        print("开始写入{}蜘蛛库...".format(i22))
                        public.WriteFile(path, json.dumps(localhost_json))
                        has_content = True
                    except:
                        pass

                now = time.time()
                time_log = "%s/latest_update.log" % spiders_dir
                public.WriteFile(time_log, str(now))

                public.ExecShell("chown -R www:www {}".format(spiders_dir))
            if has_content:
                return public.returnMsg(True, "更新成功！")
            return public.returnMsg(True, "未更新数据。")
        except Exception as e:
            return public.returnMsg(False, "更新失败:" + str(e))

    def get_site_client_stat_by_time_interval(self, site, start_date, end_date,
                                              time_scale="hour", target=None):
        """获取某一时间区间的客户端统计数据
        :site 站点名
        :start_date 起始时间
        :end_date 终止时间
        :time_scale 时间刻度
        :target 绘图指标
        """
        data = []
        sum_data = {}

        db_path = self.get_log_db_path(site, db_name=self.total_db_name)
        if not os.path.isfile(db_path):
            return data, sum_data

        ts = tsqlite()
        ts.dbfile(db_path)
        new_target = ""
        top_columns = target
        top = len(top_columns)
        table_name = "client_stat"

        # 2. 根据统计数据查询图表数据
        if time_scale == "hour":
            fields = ",".join(top_columns)
            fields = "time," + fields
            ts.table(table_name).field(fields)
            ts.where("time between ? and ?", (start_date, end_date))
            data = ts.select()
        elif time_scale == "day":
            fields = ""
            for i, col in enumerate(top_columns):
                if i == top: break
                if fields:
                    fields += ","
                fields += "sum(" + col + ") as " + col
            ts.table(table_name).field(fields)
            ts.where("time between ? and ?", (start_date, end_date))
            _data = ts.find()
            for column in top_columns:
                data.append({column: _data[column]})

        columns = ts.query("PRAGMA table_info([{}])".format(table_name))
        total_data = {}

        pc_clients = ["firefox", "msie", "qh360", "theworld", "tt", "maxthon", "opera", "qq", "uc", "safari", "chrome",
                      "metasr", "pc2345", "edeg"]
        mobile_clients = ["android", "iphone"]

        total_field = ""
        pc_field = ""
        mobile_field = ""
        for column in columns:
            client_name = column[1]
            if client_name == "time": continue
            for pc in pc_clients:
                if client_name == pc:
                    if pc_field:
                        pc_field += "+"
                    pc_field += client_name
                    break

            # for mobile in mobile_clients:
            #     if client_name == mobile["column"]:
            #         if mobile_field:
            #             mobile_field += "+"
            #         mobile_field += client_name

        pc_field = "sum(" + pc_field + ") as pc"
        mobile_field = "sum(mobile) as mobile"
        ts.table(table_name).field(",".join([pc_field, mobile_field]))
        ts.where("time between ? and ?", (start_date, end_date))
        total_res = ts.find()
        total_data["total_pc"] = total_res["pc"]
        total_data["total_mobile"] = total_res["mobile"]

        # 补充总请求数
        ts.table("request_stat").field("sum(req) as req")
        ts.where("time between ? and ?", (start_date, end_date))
        total_req = ts.find()
        if total_req:
            total_data["total_req"] = total_req["req"]
        else:
            total_data["total_req"] = 0

        return data, total_data

    def get_client_list(self, ts, site, start_date, end_date, order="time",
                        desc=False, page_size=20, page=1):
        """获取客户端统计列表数据"""

        if not ts:
            ts = tsqlite()
            db_path = self.get_log_db_path(site, db_name=self.total_db_name)
            ts.dbfile(db_path)

        table_name = "client_stat"
        columns = ts.query("PRAGMA table_info([{}])".format(table_name))
        sum_fields = ""
        # 动态生成数据列
        for column in columns:
            client_name = column[1]
            if client_name == "time": continue
            if client_name == "mobile": continue
            if sum_fields:
                sum_fields += ","
            sum_fields += "sum(" + client_name + ") as " + client_name

        # 列表数据查询
        list_fields = "time/100 as time1, " + sum_fields
        ts.table(table_name).field(list_fields).groupby("time1")
        # ts.where("time between ? and ?", (start_date, end_date))
        if order == "time":
            order = "time1"
        if desc:
            order += " desc"
        ts.order(order)
        _data = ts.select()
        other_clients = ["metasr", "theworld", "tt", "maxthon", "opera", "qq",
                         "uc", "pc2345", "other", "linux"]
        list_data = []
        total_row = len(_data)
        page_start = (page - 1) * page_size
        _data = _data[page_start:page_start + page_size]
        for client_data in _data:
            tmp = {}
            other = {}
            for key, value in client_data.items():
                if key in other_clients:
                    other[key] = value
                else:
                    if key == "time1":
                        tmp["time"] = value
                    else:
                        tmp[key] = value
            tmp.update({"other": other})
            list_data.append(tmp)
        return list_data, total_row

    def get_top_clients(self, db, start_date, end_date, top=3):
        ts = db
        sum_fields = ""
        clients = []
        table_name = "client_stat"
        columns = ts.query("PRAGMA table_info([{}])".format(table_name))
        # print("columns:", str(columns))
        # 动态生成数据列
        for column in columns:
            client_name = column[1]
            if client_name == "time": continue
            if client_name == "mobile": continue
            if sum_fields:
                sum_fields += ","
            sum_fields += "sum(" + client_name + ") as " + client_name

        ts.table(table_name).field(sum_fields)
        ts.where("time>=? and time<=?", (start_date, end_date))
        sum_data = ts.find()
        top_columns = []
        # print(sorted(sum_data, key=lambda kv:(kv[1], kv[0]), reverse=True))
        if len(sum_data):
            _columns = sorted(sum_data.items(), key=lambda kv: (kv[1], kv[0]),
                              reverse=True)
            for i in range(len(_columns)):
                if i == top: break
                top_columns.append(_columns[i][0])
        return top_columns

    def get_client_stat(self, get, flush=True):
        try:
            ts = None
            site = self.__get_siteName(get.site)
            query_date = "today"
            if 'query_date' in get:
                query_date = get.query_date
            time_scale = 'day'
            if 'time_scale' in get:
                time_scale = get.time_scale
            compare = False
            if 'compare' in get:
                compare = True if get.compare.lower() == "true" else False
            compare_date = "yesterday"
            if compare:
                if 'compare_date' in get:
                    compare_date = get.compare_date
            target = "top"
            if "target" in get:
                target = get.target
            request_time = None
            if 'request_data_time' in get:
                request_time = get.request_data_time
            page = 1
            if "page" in get:
                page = int(get.page)
            page_size = 20
            if "page_size" in get:
                page_size = int(get.page_size)
            orderby = "time"
            if "orderby" in get:
                orderby = get.orderby
            desc = True
            if "desc" in get:
                desc = True if get.desc.lower() == "true" else False

            self.set_module_total('get_client_stat')
            data = []
            sum_data = {}
            compare_data = []
            compare_sum_data = {}
            list_data = []
            total_row = 0

            start_date, end_date = tool.get_query_date(query_date)
            # print("查询时间周期: {} - {}".format(start_date, end_date))

            res_query_date = "{}-{}".format(start_date, end_date)
            db_path = self.get_log_db_path(site, db_name=self.total_db_name)
            if not os.path.isfile(db_path):
                res_data = {
                    "status": True,
                    "query_date": res_query_date,
                    "data": data,
                    "sum_data": sum_data,
                    "compare": compare,
                    "compare_date": res_query_date,
                    "compare_data": compare_data,
                    "compare_sum_data": compare_sum_data,
                    "request_data_time": request_time,
                    "page": page,
                    "page_size": page_size,
                    "total_row": total_row,
                    "list_data": list_data,
                    "autorefesh": self.get_refresh_status(site),
                    "monitor": self.get_monitor_status(site)
                }
                return res_data

            if flush:
                self.flush_data(site)
            ts = tsqlite()
            ts.dbfile(db_path)

            top_columns = []
            top = 10
            if target == "top":
                top_columns = self.get_top_clients(ts, start_date, end_date,
                                                   top)
            else:
                if target.find(",") >= 0:
                    top_columns = target.split(",")
                else:
                    top_columns = [target]

            if request_time is not None:
                # 默认top的情况下，每次重新请求
                if target and target != "top":
                    data, sum_data = self.get_site_client_stat_by_time_interval(
                        site, request_time, end_date, time_scale=time_scale,
                        target=top_columns)
                else:
                    data, sum_data = self.get_site_client_stat_by_time_interval(
                        site, start_date, end_date, time_scale=time_scale,
                        target=top_columns)
                list_data, total_row = self.get_client_list(ts, site,
                                                            request_time,
                                                            end_date,
                                                            order=orderby,
                                                            desc=desc,
                                                            page_size=page_size,
                                                            page=page)
            else:
                data, sum_data = self.get_site_client_stat_by_time_interval(
                    site, start_date, end_date, time_scale=time_scale,
                    target=top_columns)
                list_data, total_row = self.get_client_list(ts, site,
                                                            start_date,
                                                            end_date,
                                                            order=orderby,
                                                            desc=desc,
                                                            page_size=page_size,
                                                            page=page)

            if compare:
                compare_start_date, compare_end_date = tool.get_compare_date(
                    start_date, compare_date)
                # print("对比时间周期: {} - {}".format(compare_start_date, compare_end_date))
                compare_data, compare_sum_data = self.get_site_client_stat_by_time_interval(
                    site, compare_start_date, compare_end_date,
                    time_scale=time_scale, target=top_columns)

            request_time = tool.get_time_key()
            res_query_date = "{}-{}".format(start_date, end_date)
            res_compare_date = ""
            if compare:
                res_compare_date = "{}-{}".format(compare_start_date, compare_end_date)

            res_data = {
                "status": True,
                "query_date": res_query_date,
                "data": data,
                "sum_data": sum_data,
                "target": target,
                "compare": compare,
                "compare_date": res_compare_date,
                "compare_data": compare_data,
                "compare_sum_data": compare_sum_data,
                "request_data_time": request_time,
                "page": page,
                "page_size": page_size,
                "total_row": total_row,
                "list_data": list_data,
                "autorefesh": self.get_refresh_status(site),
                "monitor": self.get_monitor_status(site)
            }
            self.switch_site(get)
            return res_data
        except Exception as e:
            return tool.returnMsg(
                False,
                "REQUEST_INTERFACE_ERROR",
                args=(
                    tool.getMsg("INTERFACE_CLIENT_STAT"),
                    str(e),
                )
            )

    def get_error_code(self, get):
        error_code = [
            "all", "50x", "40x", "500", "501", "502", "503", "404"
        ]
        return {"status_codes": error_code}

    def get_site_error_logs_total(self, get):
        try:
            site = get.site
            query_date = "today"
            if 'query_date' in get:
                query_date = get.query_date
            status_code = "all"
            if "status_code" in get:
                status_code = get.status_code

            flag = False
            start_date, end_date = tool.get_query_timestamp(query_date)
            now_timestamp = time.time()
            query_dates = tool.split_query_date(start_date, end_date)

            if query_date.startswith("h1"):
                flag = query_dates[0]
            total_rows = 0
            data_dir = self.get_data_dir()
            history_dir = self.get_history_data_dir()
            for query_date in query_dates:
                try:
                    start_timestamp, end_timestamp = query_date
                    day = time.strftime("%Y%m%d", time.localtime(start_timestamp))
                    not_today = now_timestamp < start_timestamp or now_timestamp > end_timestamp and not flag
                    file_path = os.path.join(data_dir, site, str(day) + '.txt')
                    if not_today:
                        if not os.path.exists(file_path):
                            file_path = os.path.join(history_dir, site, str(day) + '.tar.gz')

                    db_path = os.path.join(data_dir, site, 'cursor_log/', day + '.db')

                    if not os.path.exists(file_path) or not os.path.exists(db_path):
                        # print("未找到db文件。")
                        continue

                    ts = tsqlite()
                    ts.dbfile(db_path)
                    conditions_str = file_path + day + status_code
                    cache_key = public.md5(conditions_str)
                    # 当天总数始终更新
                    if not_today:
                        cache_row = cache.get(cache_key)
                        if cache_row:
                            total_rows += cache_row
                            # print("获取缓存总数: ", cache_key, cache_row)
                            continue

                    cursors = self._get_error_logs_total(ts, status_code)
                    if flag:
                        total_row = self._get_search_hour_rows(cursors, file_path, flag)
                    else:
                        total_row = len(cursors)
                    total_rows += total_row

                    if not_today:
                        cache.set(cache_key, total_row, 31 * 86400)
                    else:
                        cache.set(cache_key, total_row, 600)

                    ts and ts.close()

                except Exception as e:
                    print(e)
            return {"total_row": total_rows}
        except:
            return {"total_row": 0}

    def get_site_error_logs(self, get):
        try:
            site = get.site
            query_date = "today"
            if 'query_date' in get:
                query_date = get.query_date
            status_code = "all"
            if "status_code" in get:
                status_code = get.status_code
            page = 1
            if "page" in get:
                page = int(get.page)
            page_size = 20
            if "page_size" in get:
                page_size = int(get.page_size)
            desc = True
            if "desc" in get:
                desc = True if get.desc == "true" else False

            list_data = []
            total_row = 0

            self.set_module_total('get_site_error_logs')
            start_timestamp, end_timestamp = tool.get_query_timestamp(query_date)
            res_query_date = "{}-{}".format(start_timestamp, end_timestamp)
            query_dates = tool.split_query_date(start_timestamp, end_timestamp)

            if not query_dates:
                res_data = {
                    "status": True,
                    "query_date": res_query_date,
                    "page": page,
                    "page_size": page_size,
                    "total_row": total_row,
                    "list_data": list_data,
                    "load_ip_info": False
                }
                return res_data

            self.flush_data(site)
            flag = False
            if query_date.startswith("h1"):
                flag = query_dates[0]

            selected_rows = 0  # 已查询行数
            target_rows = page_size  # 目标结果数
            select_offset = (page - 1) * page_size  # 预期偏移量
            # print("预期offset: ", select_offset)
            current_offset = 0
            data = []
            total = self.get_site_error_logs_total(get)['total_row']
            data_dir = self.get_data_dir()
            history_dir = self.get_history_data_dir()
            now_timestamp = time.time()

            def sort_key(d):
                return d[0]

            if not desc:
                query_dates.sort(key=sort_key, reverse=False)

            for date_tuple in query_dates:
                start_date, end_date = date_tuple
                day = time.strftime("%Y%m%d", time.localtime(start_date))
                not_today = now_timestamp < start_date or now_timestamp > end_date and not flag
                file_path = os.path.join(data_dir, site, str(day) + '.txt')
                if not_today:
                    if not os.path.exists(file_path):
                        file_path = os.path.join(history_dir, site, str(day) + '.tar.gz')

                db_path = self.get_log_db_path(site, db_name='cursor_log/' + day + '.db')

                if not os.path.exists(file_path) or not os.path.exists(db_path):
                    # print("未找到db文件。")
                    continue

                conditions_str = file_path + day + status_code
                conditions_key = public.md5(conditions_str)
                cache_result = cache.get(conditions_key)
                if not cache_result:
                    continue

                total_row = cache_result

                if select_offset - current_offset >= total_row:
                    current_offset += total_row
                    continue
                else:
                    sub_offset = select_offset - current_offset
                    current_offset = select_offset

                ts = tsqlite()
                ts.dbfile(db_path)

                _, suffix = os.path.splitext(file_path)
                if suffix != '.txt':
                    cursors = self._get_error_logs_total(ts, status_code)
                    res = self._get_targz_site_data(ts, cursors, file_path, sub_offset, page_size, desc)

                else:
                    cursors = self._get_error_logs_total(ts, status_code)
                    res = self._get_site_data(ts, cursors, file_path, sub_offset, page_size, total_row, desc)

                data_len = len(res)
                data += res
                selected_rows += data_len
                page_size = page_size - data_len
                if selected_rows >= target_rows:
                    break

                if ts:
                    ts.close()

            fields = "time, ip, method, domain, status_code, protocol, uri, user_agent, body_length, referer, request_time, is_spider, request_headers, ip_list, client_port"
            _columns = [column.strip() for column in fields.split(",")]
            error_count = {}
            load_ip_info = self.get_online_ip_library() is not None
            for row in data:
                tmp1 = {}
                for column in _columns:
                    val = row[column]
                    if column == "status_code":
                        if val not in error_count:
                            error_count[val] = 1
                        else:
                            error_count[val] += 1
                    tmp1[column] = row[column]
                list_data.append(tmp1)
                del (tmp1)
            res_data = {
                "status": True,
                "query_date": res_query_date,
                "page": page,
                "page_size": target_rows,
                "total_row": total,
                "list_data": list_data,
                "total_data": error_count,
                "load_ip_info": load_ip_info
            }
            res_data.update(self.get_error_code(None))
            self.switch_site(get)
            return res_data
        except Exception as e:
            return tool.returnMsg(
                False,
                "REQUEST_INTERFACE_ERROR",
                args=(
                    tool.getMsg("INTERFACE_ERROR_LOGS"),
                    str(e),
                )
            )

    def get_site_logs_sql(self, conditions):
        start_date = conditions["start_date"]
        end_date = conditions["end_date"]
        reverse_mode = ""
        if "reverse_mode" in conditions:
            reverse_mode = conditions["reverse_mode"]
        time_reverse = False
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
        if "search_url" in conditions_keys:
            search_url = conditions["search_url"]
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
        if "spider" in conditions_keys:
            spider = conditions["spider"].lower()
            if spider == "only_spider":
                where_sql += " and (trim(is_spider) <> '' and is_spider>=1 and is_spider<>77)"
            elif spider == "no_spider":
                where_sql += " and (is_spider=0 or is_spider='')"
            elif spider == "fake_spider":
                where_sql += " and is_spider=77"
            elif type(spider) == str:
                is_num = False
                try:
                    int(spider)
                    is_num = True
                except:
                    pass
                if not is_num:
                    spider_table = {
                        "baidu": 1,
                        "bing": 2,
                        "qh360": 3,
                        "google": 4,
                        "bytes": 5,
                        "sogou": 6,
                        "youdao": 7,
                        "soso": 8,
                        "dnspod": 9,
                        "yandex": 10,
                        "yisou": 11,
                        "other": 12
                    }
                    if spider in spider_table.keys():
                        if not reverse_mode:
                            where_sql += " and is_spider=" + str(spider_table[spider])
                        else:
                            where_sql += " and is_spider<>" + str(spider_table[spider])
                else:
                    if not reverse_mode:
                        where_sql += " and is_spider=" + str(spider)
                    else:
                        where_sql += " and is_spider<>" + str(spider)

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
                        where_sql += " and ip_list like \"%" + ip + "\""
                    else:
                        where_sql += " and ip_list not like \"%" + ip + "\""
                else:
                    if not reverse_mode:
                        where_sql += " and ip_list like \"%" + ip + "%\""
                    else:
                        where_sql += " and ip_list not like \"%" + ip + "%\""

        if "domain" in conditions_keys:
            domain = conditions["domain"].strip()
            if domain:
                if search_mode == "fuzzy":
                    if not reverse_mode:
                        where_sql += " and domain like '%" + domain + "%'"
                    else:
                        where_sql += " and domain not like '%" + domain + "%'"
                else:
                    if not reverse_mode:
                        where_sql += " and domain='" + domain + "'"
                    else:
                        where_sql += " and domain<>'" + domain + "'"

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

        if "referer" in conditions_keys:
            referer = conditions["referer"].strip()
            if referer:
                if search_mode == "fuzzy":
                    if not reverse_mode:
                        if referer.lower() == "none":
                            where_sql += " and referer is null"
                        else:
                            where_sql += " and referer like '%" + referer + "%'"
                    else:
                        if referer.lower() == "none":
                            where_sql += " and referer is not null"
                        else:
                            where_sql += " and referer not like '%" + referer + "%'"
                else:
                    if not reverse_mode:
                        if referer.lower() == "none":
                            where_sql += " and referer is null"
                        else:
                            where_sql += " and referer='" + referer + "'"
                    else:
                        if referer.lower() == "none":
                            where_sql += " and referer is not null"
                        else:
                            where_sql += " and referer<>'" + referer + "'"

        if "post_header" in conditions_keys:
            header_str = conditions["post_header"].strip()
            if header_str:
                if search_mode == "fuzzy":
                    if not reverse_mode:
                        where_sql += " and request_headers like '%" + header_str + "%'"
                    else:
                        where_sql += " and request_headers not like '%" + header_str + "%'"
                else:
                    if not reverse_mode:
                        where_sql += " and request_headers='" + header_str + "'"
                    else:
                        where_sql += " and request_headers<>'" + header_str + "'"

        if "response_time" in conditions_keys and "response_time_comparator" in conditions_keys:
            comparator = conditions["response_time_comparator"]
            allow_comparator = [">=", "<=", "="]
            if comparator in allow_comparator:
                response_time = conditions["response_time"]
                if not reverse_mode:
                    where_sql += " and request_time {} {}".format(comparator, response_time)
                else:
                    if comparator == ">=":
                        where_sql += " and request_time < {}".format(response_time)
                    elif comparator == "<=":
                        where_sql += " and request_time > {}".format(response_time)
                    elif comparator == "=":
                        where_sql += " and request_time <> {}".format(response_time)

        select_sql = "select {} from site_logs" + where_sql
        return select_sql

    def set_module_total(self, module, name='total_plugin'):
        """
        @name 统计模块使用
        """
        try:
            public.set_module_logs(name, module, 1)
        except Exception as e:
            pass

    def get_site_logs_total(self, get):
        try:
            site = get.site
            query_date = "today"
            if 'query_date' in get:
                query_date = get.query_date
            ip_list = ''
            if "ip" in get:
                ip_list = get.ip
            uri = ''
            if "search_url" in get:
                uri = get.search_url
            flag = False
            # 添加日志锚点
            if ip_list:
                self.set_module_total('get_site_logs_total_ip')
            elif uri:
                self.set_module_total('get_site_logs_total_search_url')

            ip_list = ip_list.replace('*', '')
            start_date, end_date = tool.get_query_timestamp(query_date)
            now_timestamp = time.time()
            query_dates = tool.split_query_date(start_date, end_date)
            if query_date.startswith("h1"):
                flag = query_dates[0]
            total_rows = 0
            data_dir = self.get_data_dir()
            history_dir = self.get_history_data_dir()
            for query_date in query_dates:
                try:
                    start_timestamp, end_timestamp = query_date
                    day = time.strftime("%Y%m%d", time.localtime(start_timestamp))
                    start_str = time.strftime("%Y%m%d%H", time.localtime(start_timestamp))
                    end_str = time.strftime("%Y%m%d%H", time.localtime(end_timestamp))
                    not_today = now_timestamp < start_timestamp or now_timestamp > end_timestamp and not flag
                    file_path = os.path.join(data_dir, site, str(day) + '.txt')
                    if not_today:
                        if not os.path.exists(file_path):
                            file_path = os.path.join(history_dir, site, str(day) + '.tar.gz')

                    db_path = os.path.join(data_dir, site, 'cursor_log/', day + '.db')

                    if not os.path.exists(file_path) or not os.path.exists(db_path):
                        # print("未找到db文件。")
                        continue
                    ts = tsqlite()
                    ts.dbfile(db_path)
                    conditions_str = file_path + start_str + end_str + ip_list + uri
                    conditions_key = public.md5(conditions_str)

                    cache_key = conditions_key
                    # 当天总数始终更新
                    if not_today:
                        cache_row = cache.get(cache_key)
                        if cache_row:
                            total_rows += cache_row
                            continue

                    _, suffix = os.path.splitext(file_path)
                    if not uri and not ip_list:
                        if suffix != '.txt':
                            tar = tarfile.open(file_path, "r:gz")
                            for member in tar.getmembers():
                                total_row = member.size // self.line_size

                        elif flag:
                            stats = os.stat(file_path)
                            f = open(file_path, 'r')
                            total_row = self._get_hour_rows(f, flag, stats.st_size)
                            f.close()
                        else:
                            stats = os.stat(file_path)
                            # 文件每行数据(包含换行符)固定400字节
                            total_row = stats.st_size // self.line_size
                    else:
                        cursors = self._get_logs_cursor(ts, ip_list, uri)
                        if flag:
                            total_row = self._get_search_hour_rows(cursors, file_path, flag)
                        else:
                            total_row = len(cursors)
                    total_rows += total_row

                    if not_today:
                        cache.set(cache_key, total_row, 31 * 86400)
                    else:
                        cache.set(cache_key, total_row, 600)

                    ts and ts.close()

                except Exception as e:
                    print(e)
            return {"total_row": total_rows}
        except Exception as e:
            return {"total_row": 0}

    def get_all_site(self, get):
        """所有站点信息概览"""
        try:
            query_date = "today"
            if 'query_date' in get:
                query_date = get.query_date

            data = cache.get('ALL_SITE_OVERVIEW' + query_date)
            if data:
                return json.loads(data)

            start_date, end_date = tool.get_query_date(query_date)
            sites = public.M('sites').field('name').order("addtime").select()
            total_pv = 0
            total_uv = 0
            total_ip = 0
            total_req = 0
            total_length = 0
            total_realtime_req = 0
            total_realtime_traffic = 0
            exception_sites = []
            for site_info in sites:
                try:
                    ori_site = site_info["name"]
                    site = self.__get_siteName(ori_site)
                    site_overview_info = self.get_all_site_overview(site, start_date, end_date)
                    data = {"pv": 0, "uv": 0, "ip": 0, "req": 0, "length": 0}
                    data.update(site_overview_info)
                    realtime_req_list = self.get_realtime_request(site)
                    if len(realtime_req_list) > 0:
                        data["realtime_req"] = realtime_req_list[0]["req"]
                    else:
                        data["realtime_req"] = 0

                    realtime_traffic_list = self.get_realtime_traffic(site)
                    if len(realtime_traffic_list) > 0:
                        data["realtime_traffic"] = realtime_traffic_list[0]["flow"]
                    else:
                        data["realtime_traffic"] = 0

                    total_pv += data["pv"]
                    total_uv += data["uv"]
                    total_ip += data["ip"]
                    total_req += data["req"]
                    total_length += data["length"]
                    total_realtime_req += data["realtime_req"]
                    total_realtime_traffic += data["realtime_traffic"]

                except Exception as e:
                    msg = str(e)
                    if msg.find("object does not support item assignment") != -1:
                        msg = "数据文件/www/server/total/logs/{}/logs.db已损坏。".format(site)
                    exception_sites.append({"site": ori_site, "err": msg})

            res_data = {
                "pv": total_pv,
                "uv": total_uv,
                "ip": total_ip,
                "req": total_req,
                "length": total_length,
                "realtime_req": total_realtime_req,
                "realtime_traffic": total_realtime_traffic,
            }

            if query_date == 'today' or query_date == 'h1':
                timeout = 60
            else:
                s, e = tool.get_timestamp_interval(time.localtime())
                timeout = e - time.time()
            cache.set('ALL_SITE_OVERVIEW' + query_date, json.dumps(res_data), timeout)

            return res_data
        except Exception as e:
            return tool.returnMsg(
                False,
                "REQUEST_INTERFACE_ERROR",
                args=(
                    tool.getMsg("INTERFACE_SITE_LIST"),
                    str(e),
                )
            )

    def get_site_info(self, get):
        """获取站点信息"""
        try:
            query_date = "today"
            if 'query_date' in get:
                query_date = get.query_date

            orderby = "pv"
            if "orderby" in get:
                orderby = get.orderby

            page = 1
            if "page" in get:
                page = int(get.page)

            page_size = 20
            if "page_size" in get:
                page_size = int(get.page_size)

            site = 'all'
            if "site" in get:
                site = get.site

            desc = True
            if "desc" in get:
                desc = True if get.desc == "true" else False

            list_data = []
            sites = []
            offset = (page - 1) * page_size
            count = 0
            start_date, end_date = tool.get_query_date(query_date)

            if site == 'all':
                sites = public.M('sites').field('name').order("addtime").limit(page_size, offset).select()
                count = public.M('sites').query('select count(*) from sites;')
            else:
                res = public.M('sites').query('select name from sites where name like "%{}%" order by addtime limit {},{};'.format(site, offset, page_size))
                count = public.M('sites').query('select count(*) from sites where name like "%{}%";'.format(site))
                for i in res:
                    sites.append({"name": i[0]})

            count = count[0][0] if count else 0
            exception_sites = []
            for site_info in sites:
                try:
                    ori_site = site_info["name"]
                    site = self.__get_siteName(ori_site)
                    site_overview_info = self.get_site_overview_sum_data(
                        site, start_date, end_date)
                    data = {
                        "name": ori_site, "pv": 0, "uv": 0, "ip": 0, "req": 0,
                        "length": 0, "spider": 0, "fake_spider": 0, "s50x": 0, "s40x": 0
                    }
                    data.update(site_overview_info)
                    realtime_req_list = self.get_realtime_request(site)
                    if len(realtime_req_list) > 0:
                        data["realtime_req"] = realtime_req_list[0]["req"]
                    else:
                        data["realtime_req"] = 0

                    realtime_traffic_list = self.get_realtime_traffic(site)
                    if len(realtime_traffic_list) > 0:
                        data["realtime_traffic"] = realtime_traffic_list[0]["flow"]
                    else:
                        data["realtime_traffic"] = 0

                    data["status"] = self.get_monitor_status(site)
                    list_data.append(data)
                except Exception as e:
                    msg = str(e)
                    if msg.find("object does not support item assignment") != -1:
                        msg = "数据文件/www/server/total/logs/{}/logs.db已损坏。".format(site)
                    exception_sites.append({"site": ori_site, "err": msg})

            def sort_key(d):
                return d[orderby]

            list_data.sort(key=sort_key, reverse=desc)

            res_data = {
                "list_data": list_data,
                "orderby": orderby,
                "exception_sites": exception_sites,
                "desc": desc,
                "page": page,
                "page_size": page_size,
                "count": count,
            }
            return res_data
        except Exception as e:
            return tool.returnMsg(
                False,
                "REQUEST_INTERFACE_ERROR",
                args=(
                    tool.getMsg("INTERFACE_SITE_LIST"),
                    str(e),
                )
            )

    def __read_frontend_config(self):
        config_json = self.__frontend_path + "/config.json"
        data = {}
        if os.path.exists(config_json):
            data = json.loads(public.readFile(config_json))
        return data

    def set_default_site(self, site):
        config = self.__read_frontend_config()
        config["default_site"] = site
        config_json = self.__frontend_path + "/config.json"
        public.writeFile(config_json, json.dumps(config))
        return True

    def switch_site(self, post):
        if "request_in_panel" not in post: return
        # print("切换默认站点。")
        site = post.site
        if self.set_default_site(site):
            return public.returnMsg(True, "已切换默认站点为{}".format(site))
        return public.returnMsg(False, "切换默认站点失败。")

    def get_default_site(self):
        config = self.__read_frontend_config()
        default = None
        if "default_site" in config:
            default = config["default_site"]
        if not default:
            site = public.M('sites').field('name').order("addtime").find()
            default = site["name"]
        return default

    def get_site_lists(self, get):
        # self._check_site()
        tool.write_site_domains()
        if os.path.exists('/www/server/apache'):
            if not os.path.exists('/usr/local/memcached/bin/memcached'):
                return tool.returnMsg(False, 'MEMCACHE_CHECK')
            if not os.path.exists('/var/run/memcached.pid'):
                return public.returnMsg(False, 'MEMCACHE_CHECK2')
        # modc = self.__get_mod(get)
        # if not cache.get('bt_total'):  return modc

        sites = public.M('sites').field('name').order("addtime").select()
        if len(sites) == 0:
            res_data = {
                "status": False,
                "msg": tool.getMsg("PLEASE_CREATE_SITE")
            }
        else:
            res_site = []
            for site in sites:
                res_site.append(site["name"])

            # if os.path.exists("/www/server/total/logs/btunknownbt"):
            #     res_site.append("btunknownbt")
            default_site = self.get_default_site()
            res_data = {
                "status": True,
                "data": res_site,
                "default": default_site
            }
        return res_data

    def get_total_bysite(self, get):
        # self.__read_config()
        # tmp = self.__config['sites'][get.siteName]
        tmp = {}
        tmp['total'] = self.__get_site_total(get.siteName)
        tmp['site_name'] = get.siteName
        get.s_type = 'request'
        tmp['days'] = self.get_site_total_days(get)
        return tmp

    def get_site_total_days(self, get):
        site = self.__get_siteName(get.siteName)
        # s_type = get.s_type
        # types = {
        #     "request": "req",
        # }
        ts = self.init_ts(site, self.total_db_name)
        start, end = tool.get_last_days(30)
        days_sql = "select time/100 as time1 from request_stat " \
                   "where time between {} and {} group by time1 order by time1 desc".format(start, end)
        results = ts.query(days_sql)
        data = []
        if type(results) == str:
            return data
        for res in results:
            date = str(res[0])
            try:
                date = self.__timekey2date(date)
                data.append(date)
            except:
                pass
        return data

    def get_site_total_days_old(self, get):
        get.siteName = self.__get_siteName(get.siteName)

        path = self.__plugin_path + '/total/' + get.siteName + '/' + get.s_type
        data = []
        if not os.path.exists(path): return data
        for fname in os.listdir(path):
            if fname == 'total.json': continue
            data.append(fname.split('.')[0])

        return sorted(data, reverse=True)

    def get_site_network_all(self, get):
        get.siteName = self.__get_siteName(get.siteName)

        query_date = "l7"
        if "query_date" in get:
            query_date = get.query_date

        all_start, all_end = tool.get_query_date(query_date)
        get_total_sql = "select time/100 as time1, sum(length) as length, " \
                        "sum(req) as req, sum(uv) as uv, sum(pv) as pv, sum(ip) as ip, " \
                        "sum(spider) as spider, sum(status_500) as s500, sum(status_502) as s502, " \
                        "sum(status_503) as s503, sum(http_put) as put, sum(http_get) as get, sum(http_post) as post " \
                        "from request_stat " \
                        "where time >= {} and time <= {} " \
                        "group by time1 " \
                        "order by time1 desc;".format(all_start, all_end)
        ts = self.init_ts(get.siteName, self.total_db_name)
        results = ts.query(get_total_sql)
        data = {}
        # network_days = []
        request_days = []
        data['total_size'] = 0
        data['total_request'] = 0
        data['days'] = []
        if type(results) == list:
            for total_day in results:
                day_req = {}

                day_req["date"] = self.__timekey2date(total_day[0])
                day_size = self.get_num_value(total_day[1])
                day_req["size"] = day_size

                data['total_size'] += day_size

                day_req['request'] = self.get_num_value(total_day[2])
                day_req['uv'] = self.get_num_value(total_day[3])
                day_req['pv'] = self.get_num_value(total_day[4])
                day_req['ip'] = self.get_num_value(total_day[5])

                day_req['500'] = self.get_num_value(total_day[7])
                day_req['502'] = self.get_num_value(total_day[8])
                day_req['503'] = self.get_num_value(total_day[9])

                day_req['put'] = self.get_num_value(total_day[10])
                day_req['get'] = self.get_num_value(total_day[11])
                day_req['post'] = self.get_num_value(total_day[12])

                data['total_request'] += day_req["request"]
                data["days"].append(day_req)

        return data

    def get_site_total_byday(self, get):
        get.siteName = self.__get_siteName(get.siteName)
        time_key = self.__today2timekey(get.s_day)
        start_date, end_date = tool.get_query_date(time_key)
        types = {
            "request": "req",
            "network": "length",
        }
        fields = types[get.s_type]
        fields += ",http_get, http_post"
        select_sql = "select time, {} from request_stat where time >= {} and time <= {}" \
            .format(fields, start_date, end_date)
        # print("select sql byday:" + select_sql)
        ts = self.init_ts(get.siteName, self.total_db_name)
        results = ts.query(select_sql)
        data = []
        if type(results) == list:
            for result in results:
                time_key = str(result[0])
                hour = time_key[len(time_key) - 2:]
                value = result[1]
                data.append({"key": hour, "value": value, "GET": result[2], "POST": result[3]})

        # filename = self.__plugin_path + '/total/' + get.siteName + '/' + get.s_type + '/' + get.s_day + '.json'
        # if not os.path.exists(filename): return []
        # return self.__sort_json(self.__get_file_json(filename), False)
        return data

    def get_site_total_byspider(self, get):
        get.siteName = self.__get_siteName(get.siteName)
        ts = self.init_ts(get.siteName, self.total_db_name)
        columns = ts.query("PRAGMA table_info([{}])".format("spider_stat"))
        fields = []
        for column in columns:
            column_name = column[1]
            if column_name == "time": continue
            fields.append(column_name)

        config = self.get_config(get.siteName)
        save_day = config["save_day"]
        all_start, all_end = tool.get_query_date("l" + repr(save_day))
        select_all_sql = "select sum(spider) from request_stat where time between {} and {}".format(all_start, all_end)
        all_results = ts.query(select_all_sql)
        data = {}
        data['total_all'] = 0
        if type(all_results) == list:
            data["total_all"] = self.get_num_value(all_results[0][0])

        query_date = time.strftime('%Y%m%d', time.localtime())
        start_date, end_date = tool.get_query_date(query_date)
        get_spider_sql = "select time/100 as time1, " + ",".join(fields) + \
                         " from spider_stat where time between {} and {} group by time1".format(start_date, end_date)
        results = ts.query(get_spider_sql)
        data['total_day'] = 0
        data['days'] = []
        ts.close()

        fields_map = {
            "baidu": "BaiduSpider",
            "google": "Googlebot",
            "sogou": "Sogou web spider",
            "qh360": "360Spider"
        }
        if type(results) == list:
            for total_spider in results:
                tmp = {}
                time_key = total_spider[0]
                tmp['date'] = self.__timekey2date(time_key)
                for i, field in enumerate(fields):
                    if field in fields_map.keys():
                        tmp[fields_map[field]] = total_spider[i + 1]
                    else:
                        tmp[field] = total_spider[i + 1]
                data['days'].append(tmp)
            data['days'] = sorted(data['days'], key=lambda x: x['date'], reverse=True)
        return data

    def get_site_total_byclient(self, get):
        get.siteName = self.__get_siteName(get.siteName)
        path = self.__plugin_path + '/total/' + get.siteName + '/client'
        data = []
        if not os.path.exists(path): return data
        for fname in os.listdir(path):
            if fname == 'total.json': continue
            filename = path + '/' + fname
            day_data = self.__get_file_json(filename)
            tmp = {}
            tmp['date'] = fname.split('.')[0]
            for s_data in day_data.values():
                for s_key in s_data.keys():
                    if not s_key in tmp:
                        tmp[s_key] = s_data[s_key]
                    else:
                        tmp[s_key] += s_data[s_key]
            data.append(tmp)
        data = sorted(data, key=lambda x: x['date'], reverse=True)
        return data

    def get_site_total_byarea(self, get):
        get.siteName = self.__get_siteName(get.siteName)
        if not 's_day' in get: get.s_day = 'total'
        path = self.__plugin_path + '/total/' + get.siteName + '/area/' + get.s_day + '.json'
        data = {}
        data['date'] = get.s_day
        data['num'] = 0
        data['total'] = []
        if not os.path.exists(path): return data
        day_data = self.__get_file_json(path)
        data['num'] = self.__sum_dict(day_data)
        for s_key in day_data.keys():
            tmp1 = {}
            tmp1['area'] = s_key
            tmp1['num'] = day_data[s_key]
            tmp1['percentage'] = round(
                (float(tmp1['num']) / float(data['num'])) * 100.0, 2)
            data['total'].append(tmp1)
        data['total'] = sorted(data['total'], key=lambda x: x['num'],
                               reverse=True)
        return data

    def __sum_dict(self, data):
        num = 0
        for v in data.values():
            if type(v) == int:
                num += v
            else:
                for d in v.values(): num += d
        return num

    def __sort_json(self, data, dest=True):
        result = []
        for k in data.keys():
            if type(data[k]) == int:
                tmp = {}
                tmp['value'] = data[k]
            else:
                tmp = data[k]
            tmp['key'] = k
            result.append(tmp)
        return sorted(result, key=lambda x: x['key'], reverse=dest)

    def get_site_log_days(self, get):
        srcSiteName = get.siteName
        get.siteName = self.__get_siteName(get.siteName)
        self.__read_config()
        data = {}
        data['log_open'] = self.__config['sites'][srcSiteName]['log_open']
        data['save_day'] = self.__config['sites'][srcSiteName]['save_day']
        path = self.__plugin_path + '/logs/' + get.siteName
        data['days'] = []
        if not os.path.exists(path): return data
        for fname in os.listdir(path):
            if fname == 'error': continue
            data['days'].append(fname.split('.')[0])
        data['days'] = sorted(data['days'], key=lambda x: x, reverse=True)
        return data

    def remove_site_log_byday(self, get):
        get.siteName = self.__get_siteName(get.siteName)
        s_path = self.__plugin_path + '/logs/' + get.siteName
        if not 'error_log' in get:
            path = s_path + '/' + get.s_day + '.log'
        else:
            path = s_path + '/error/' + get.s_status + '.log'

        if os.path.exists(path): os.remove(path)
        return public.returnMsg(True, '日志清除成功!')

    def remove_site_log(self, get):
        get.siteName = self.__get_siteName(get.siteName)
        s_path = self.__plugin_path + '/logs/' + get.siteName
        public.ExecShell("rm -rf " + s_path)
        return public.returnMsg(True, '日志清除成功!')

    def get_site_log_byday(self, get):
        get.siteName = self.__get_siteName(get.siteName)
        s_path = self.__plugin_path + '/logs/' + get.siteName
        result = {}
        result['total_size'] = 0
        result['size'] = 0
        result['data'] = []
        get.site = get.siteName
        path = s_path + '/logs.db'
        if os.path.exists(path): result['total_size'] = os.path.getsize(path)
        page_size = 10
        get.page_size = page_size
        page = 1
        if 'p' in get:
            page = int(get.p)
            get.page = page
        # if not os.path.exists(s_path): return result
        if not 'error_log' in get:
            if not 's_day' in get: return public.returnMsg(False, '请指定日期!')
            query_date = self.__today2timekey(get.s_day)
            get.query_date = query_date

            results = self.get_site_logs(get)
            # for uname in os.listdir(s_path):
            #     filename = s_path + '/' + uname
            #     if os.path.isdir(filename): continue
            #     result['total_size'] += os.path.getsize(filename)
        else:
            if not 's_status' in get: return public.returnMsg(False, '请指定状态!')
            # s_path += '/error'
            # if not os.path.exists(s_path): return result
            path = s_path + '/' + get.s_status + '.log'
            get.status_code = get.s_status
            results = self.get_site_logs(get)
            # if os.path.exists(path): result['size'] = os.path.getsize(path)
            # for uname in os.listdir(s_path):
            #     filename = s_path + '/' + uname
            #     if os.path.isdir(filename): continue
            #     result['total_size'] += os.path.getsize(filename)

        data = []
        #           0     1   2                4           5         6    7           8            9        10
        # fields = "time, ip, method, domain, status_code, protocol, uri, user_agent, body_length, referer, request_time, is_spider, request_headers"
        if results["status"]:
            for line in results["list_data"]:
                # print("error log line:")
                # return public.returnMsg(False, str(line))
                # line = json.loads(line)
                data.append([
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(line["time"]))),
                    line["ip"],
                    get.siteName,
                    line["method"],
                    line["status_code"],
                    line["uri"],
                    line["body_length"],
                    line["referer"],
                    line["user_agent"],
                    line["protocol"]
                ])
        result['data'] = data
        return result

    def __timekey2date(self, timekey):
        date = str(timekey)
        date = date[0:4] + "-" + date[4:6] + "-" + date[6:]
        return date

    def __today2timekey(self, date):
        time_key = date.replace("-", "")
        return time_key

    def __get_site_total(self, siteName, get=None):
        data = {}
        is_red = False
        if not get: get = get_input()
        if hasattr(get, 'today'):
            today = get['today']
        else:
            today_time = time.localtime()
            today = time.strftime('%Y-%m-%d', today_time)
            is_red = True

        data['client'] = 0
        siteName = self.__get_siteName(siteName)
        # spdata = self.__get_file_json(
        #     self.__plugin_path + '/total/' + siteName + '/client/total.json')
        # for c in spdata.values(): data['client'] += c

        # 获取总流量
        config = self.get_config(siteName)
        save_day = config["save_day"]
        all_start, all_end = tool.get_query_date("l" + repr(save_day))
        get_total_sql = "select sum(length) as length, sum(req) as req, " \
                        "sum(spider) as spider from request_stat where time between {} and {}".format(all_start, all_end)

        ts = self.init_ts(siteName, self.total_db_name)
        results = ts.query(get_total_sql)
        if type(results) == str:
            data["newwork"] = 0
            data["request"] = 0
            data["spider"] = 0
        else:
            data["network"] = self.get_num_value(results[0][0])
            data["request"] = self.get_num_value(results[0][1])
            data["spider"] = self.get_num_value(results[0][2])

        # 获取实时的请求和流量
        data['req_sec'] = 0
        data['flow_sec'] = 0
        realtime_req_list = self.get_realtime_request(siteName)
        if len(realtime_req_list) > 0:
            data["req_sec"] = self.get_num_value(realtime_req_list[0]["req"])
        else:
            data["req_sec"] = 0

        realtime_traffic_list = self.get_realtime_traffic(siteName)
        if len(realtime_traffic_list) > 0:
            data["flow_rec"] = self.get_num_value(realtime_traffic_list[0]["flow"])
        else:
            data["flow_rec"] = 0

        #  获取今日总流量
        data['day_network'] = 0
        time_key = self.__today2timekey(today)
        start, end = tool.get_query_date(time_key)
        get_network_sql = "select sum(length) as length, sum(spider) as spider from request_stat where time between {} and {}".format(start, end)
        day_results = ts.query(get_network_sql)
        # print("site name:"+siteName)
        # print("今日总流量查询结果:"+str(day_results))
        if type(day_results) == list:
            day_network = self.get_num_value(day_results[0][0])
            data['day_network'] = day_network
            day_spider = self.get_num_value(day_results[0][1])
            data["day_spider"] = day_spider

        # path = self.__plugin_path + '/total/' + siteName + '/network/' + today + '.json'
        # if os.path.exists(path):
        #     spdata = self.__get_file_json(path)
        #     for c in spdata.values(): data['day_network'] += c
        # data['request'] = self.__total_request(
        #     self.__plugin_path + '/total/' + siteName + '/request/total.json')
        data['day_request'], data['day_ip'], data['day_pv'], data['day_uv'], \
            data['day_post'], data['day_get'], data['day_put'], data['day_500'], \
            data['day_502'], data['day_503'] = self.__total_request(siteName, time_key)

        # data['spider'] = 0

        # spdata = self.__get_file_json(
        #     self.__plugin_path + '/total/' + siteName + '/spider/total.json')
        # for c in spdata.values(): data['spider'] += c

        # data['day_spider'] = 0
        # path = self.__plugin_path + '/total/' + siteName + '/spider/' + today + '.json'
        data['day_spider_arr'] = {}

        table_info = ts.query("PRAGMA table_info([{}])".format("spider_stat"))
        columns = []
        for column in table_info:
            column_name = column[1]
            if column_name == "time": continue
            columns.append(column_name)

        get_spider_sql = "select time, " + ",".join(columns) + " from spider_stat where time between {} and {}".format(
            start, end)
        spider_results = ts.query(get_spider_sql)

        # fields_map = {
        #     "baidu": "BaiduSpider",
        #     "google": "Googlebot",
        #     "sogou": "Sogou web spider",
        #     "qh360": "360Spider"
        # }

        if type(spider_results) == list:
            for spider_line in spider_results:
                time_key = str(spider_line[0])
                hour = time_key[len(time_key) - 2:]
                spider_data = {}
                for i, column in enumerate(columns):
                    # if column in fields_map.keys():
                    #     column = fields_map[column]
                    spider_data[column] = spider_line[i + 1]
                data['day_spider_arr'][hour] = spider_data

        # if os.path.exists(path):
        #     spdata = self.__get_file_json(path)
        #     data['day_spider_arr'] = spdata
        #     for c in spdata.values():
        #         for d in c.values(): data['day_spider'] += d

        ts.close()

        if is_red:
            try:
                data['7day_total'] = []
                for i in range(6):
                    get.today = (datetime.date.today() + datetime.timedelta(
                        ~(i + 1) + 1)).strftime("%Y-%m-%d")
                    tmp = self.__get_site_total(siteName, get)
                    tmp['date'] = get.today
                    data['7day_total'].insert(0, tmp)
            except:
                pass
        return data

    def __get_site_total_old(self, siteName, get=None):
        data = {}
        is_red = False
        if not get: get = get_input()
        if hasattr(get, 'today'):
            today = get['today']
        else:
            today_time = time.localtime()
            today = time.strftime('%Y-%m-%d', today_time)
            is_red = True

        data['client'] = 0
        siteName = self.__get_siteName(siteName)
        spdata = self.__get_file_json(
            self.__plugin_path + '/total/' + siteName + '/client/total.json')
        for c in spdata.values(): data['client'] += c

        data['network'] = self.__get_file_json(
            self.__plugin_path + '/total/' + siteName + '/network/total.json',
            0)
        req_sec_file = self.__plugin_path + '/total/' + siteName + '/req_sec.json'
        data['req_sec'] = 0
        data['flow_sec'] = 0
        if os.path.exists(req_sec_file):
            if time.time() - os.stat(req_sec_file).st_mtime < 10:
                data['req_sec'] = self.__get_file_json(req_sec_file, 0)
                data['flow_sec'] = self.__get_file_json(
                    self.__plugin_path + '/total/' + siteName + '/flow_sec.json',
                    0)
        data['day_network'] = 0
        path = self.__plugin_path + '/total/' + siteName + '/network/' + today + '.json'
        if os.path.exists(path):
            spdata = self.__get_file_json(path)
            for c in spdata.values(): data['day_network'] += c
        data['request'] = self.__total_request(
            self.__plugin_path + '/total/' + siteName + '/request/total.json')
        data['day_request'], data['day_ip'], data['day_pv'], data['day_uv'], \
            data['day_post'], data['day_get'], data['day_put'], data['day_500'], \
            data['day_502'], data['day_503'] = self.__total_request(
            self.__plugin_path + '/total/' + siteName + '/request/' + today + '.json')
        data['spider'] = 0

        spdata = self.__get_file_json(
            self.__plugin_path + '/total/' + siteName + '/spider/total.json')
        for c in spdata.values(): data['spider'] += c

        data['day_spider'] = 0
        path = self.__plugin_path + '/total/' + siteName + '/spider/' + today + '.json'
        data['day_spider_arr'] = {}
        if os.path.exists(path):
            spdata = self.__get_file_json(path)
            data['day_spider_arr'] = spdata
            for c in spdata.values():
                for d in c.values(): data['day_spider'] += d
        if is_red:
            try:
                data['7day_total'] = []
                for i in range(6):
                    get.today = (datetime.date.today() + datetime.timedelta(
                        ~(i + 1) + 1)).strftime("%Y-%m-%d")
                    tmp = self.__get_site_total(siteName, get)
                    tmp['date'] = get.today
                    data['7day_total'].insert(0, tmp)
            except:
                pass
        return data

    def __get_site_total_bysite(self, siteName):
        data = {}
        siteName = self.__get_siteName(siteName)
        data['client'] = self.__get_file_json(
            self.__plugin_path + '/total/' + siteName + '/client/total.json')
        data['area'] = self.__get_file_json(
            self.__plugin_path + '/total/' + siteName + '/area/total.json')
        data['network'] = self.__get_file_json(
            self.__plugin_path + '/total/' + siteName + '/network/total.json',
            0)
        data['request'] = self.__get_file_json(
            self.__plugin_path + '/total/' + siteName + '/request/total.json')
        data['spider'] = self.__get_file_json(
            self.__plugin_path + '/total/' + siteName + '/spider/total.json')
        return data

    def __get_siteName(self, siteName):
        db_file = self.__plugin_path + '/total/logs/' + siteName + '/logs.db'
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
            db_file = self.__plugin_path + '/total/logs/' + domain["name"] + '/logs.db'
            if os.path.isfile(db_file):
                siteName = domain['name']
                break
        cache.set(cache_key, siteName.replace('_', '.'))
        return cache.get(cache_key)

    def write_lua_config(self, config=None):
        if not config:
            config = json.loads(public.readFile("/www/server/total/config.json"))
        lua_config = LuaMaker.makeLuaTable(config)
        lua_config = "return " + lua_config
        public.WriteFile("/www/server/total/total_config.lua", lua_config)

    def get_site_domains(self, get):
        """查找站点的绑定域名列表"""
        siteName = get.site
        domains = []
        pid = public.M('sites').where('name=?', (siteName,)).getField('id')
        if not pid:
            return domains

        objs = public.M('domain').where('pid=?', (pid,)).field(
            'name').select()
        for domain in objs:
            domains.append(domain["name"])
        return domains

    def get_num_value(self, value):
        if value is None:
            return 0
        return value

    def __total_request(self, site, query_date, get_total=False):
        start_time_key, end_time_key = tool.get_query_date(query_date)

        select_request_sql = "select " \
                             "sum(req) as req, sum(uv) as uv, sum(pv) as pv, sum(ip) as ip, " \
                             "sum(spider) as spider, sum(status_500) as s500, sum(status_502) as s502, " \
                             "sum(status_503) as s503, sum(http_put) as put, sum(http_get) as get, sum(http_post) as post " \
                             "from request_stat " \
                             "where time between {} and {}".format(start_time_key, end_time_key)

        ts = self.init_ts(site, self.total_db_name)
        results = ts.query(select_request_sql)
        # print("total request result:"+str(results))
        day_request = 0
        day_ip = 0
        day_pv = 0
        day_uv = 0
        day_post = 0
        day_get = 0
        day_put = 0
        day_500 = 0
        day_503 = 0
        day_502 = 0
        if type(results) == list:
            day_request = self.get_num_value(results[0][0])
            if get_total:
                ts.close()
                return day_request
            day_uv = self.get_num_value(results[0][1])
            day_pv = self.get_num_value(results[0][2])
            day_ip = self.get_num_value(results[0][3])

            day_500 = self.get_num_value(results[0][5])
            day_502 = self.get_num_value(results[0][6])
            day_503 = self.get_num_value(results[0][7])

            day_put = self.get_num_value(results[0][8])
            day_get = self.get_num_value(results[0][9])
            day_post = self.get_num_value(results[0][10])

        ts.close()
        return day_request, day_ip, day_pv, day_uv, day_post, day_get, day_put, day_500, day_502, day_503

    def __total_request_old(self, path):
        day_request = 0
        day_ip = 0
        day_pv = 0
        day_uv = 0
        day_post = 0
        day_get = 0
        day_put = 0
        day_500 = 0
        day_503 = 0
        day_502 = 0
        if os.path.exists(path):
            spdata = self.__get_file_json(path)
            if path.find('total.json') != -1:
                for c in spdata:
                    if re.match("^\d+$", c): day_request += spdata[c]
                return day_request

            for c in spdata.values():
                for d in c:
                    if re.match("^\d+$", d): day_request += c[d]
                    if 'ip' == d: day_ip += c['ip']
                    if 'pv' == d: day_pv += c['pv']
                    if 'uv' == d: day_uv += c['uv']
                    if 'POST' == d: day_post += c['POST']
                    if 'GET' == d: day_get += c['GET']
                    if 'PUT' == d: day_put += c['PUT']
                    if '500' == d: day_500 += c['500']
                    if '503' == d: day_503 += c['503']
                    if '502' == d: day_502 += c['502']

        if path.find('total.json') != -1: return day_request
        return day_request, day_ip, day_pv, day_uv, day_post, day_get, day_put, day_500, day_502, day_503

    def __remove_log_file(self, siteName):
        siteName = self.__get_siteName(siteName)
        path = self.__plugin_path + '/total/' + siteName
        if os.path.exists(path): public.ExecShell("rm -rf " + path)
        path = self.__plugin_path + '/logs/' + siteName
        if os.path.exists(path): public.ExecShell("rm -rf " + path)

    def __get_file_json(self, filename, defaultv={}):
        try:
            if not os.path.exists(filename): return defaultv
            return json.loads(public.readFile(filename))
        except:
            os.remove(filename)
            return defaultv

    def __write_config(self):
        public.writeFile(self.__plugin_path + '/config.json',
                         json.dumps(self.__config))
        public.serviceReload()

    def __read_config(self, site="global"):
        if self.__config: return True
        data = public.readFile(self.__plugin_path + '/config.json')
        self.__config = json.loads(data)

    def get_test(self, get):
        return self.__read_config()

    def __write_logs(self, logstr):
        public.WriteLog(tool.getMsg("PLUGIN_NAME"), logstr)

    def return_file(self, file):
        for root, dirs, files in os.walk(file):
            return files

    def get_ip_total(self, get):
        server_name = get.server_name.strip()
        day = get.day.strip()
        path = '/www/server/total/total/' + server_name + '/ip_total/' + day
        if not os.path.exists(path): return public.returnMsg(False, '无日志')
        file_data = self.return_file(path)
        result = []
        for i in file_data:
            try:
                tmp = {}
                tmp['ip'] = i.split('.json')[0]
                tmp['totla'] = json.loads(public.ReadFile(path + '/' + i))[
                    'totla']
                result.append(tmp)
            except:
                continue
        return result

    def migrate_total(self, get):
        import threading
        migrate_thread = threading.Thread(target=total_migrate().migrate_total)
        migrate_thread.setDaemon(True)
        migrate_thread.start()
        return public.returnMsg(True, "正在迁移中，请稍后。")

    def get_migrate_status(self, get):
        tm = total_migrate()
        res = tm.get_migrate_status()
        status = True if res["status"] == "completed" else False
        if not status:
            check_path = "/www/server/total/total"
            if not os.path.isdir(check_path) or public.get_path_size(
                    check_path) == 0:
                tm.set_migrate_status("completed")
                return tm.get_migrate_status()
        return res

    def get_site_settings(self, site):
        """获取站点配置"""

        config_path = "/www/server/total/config.json"
        config = self.__get_file_json(config_path)
        if not config:
            return {}
        # frontend_config = self.__read_frontend_config()

        res_config = {}
        if site not in config.keys():
            res_config = config["global"]
            res_config["push_report"] = False
        else:
            res_config = config[site]

        for k, v in config["global"].items():
            if k not in res_config.keys():
                if k == "push_report":
                    res_config[k] = False
                else:
                    res_config[k] = v
        res_config["default_site"] = self.get_default_site()
        return res_config

    def get_settings_info(self, get):
        """获取配置信息
        适用插件前端调用"""
        site = None
        if "site" in get:
            site = self.__get_siteName(get.site)
        if not site:
            return public.returnMsg(False, "请选择站点。")

        self.set_module_total('get_settings_info')
        settings_info = self.get_site_settings(site)
        for k, v in settings_info.items():
            if k == "exclude_url":
                # print("Exclude url:"+json.dumps(settings_info["exclude_url"]))
                settings_info["exclude_url"] = json.dumps(settings_info["exclude_url"])
                continue
            if type(v) == list:
                _v = [str(x) for x in v]
                settings_info[k] = ",".join(_v)
        if site == "global":
            try:
                spiders_update = public.readFile("/www/server/total/xspiders/latest_update.log")
                if spiders_update:
                    spiders_update = float(spiders_update)
                    settings_info["spiders_latest_update"] = spiders_update
                spiders_integrity = True
                spider_tags = [1, 2, 3, 4, 5, 6, 7]
                for x in spider_tags:
                    spider_path = "/www/server/total/xspiders/{}.json".format(x)
                    if not os.path.exists(spider_path):
                        spiders_integrity = False
                        break
                    spiders = json.loads(public.readFile(spider_path))
                    if len(spiders) == 0:
                        spiders_integrity = False
                        break
                settings_info["spiders_integrity"] = spiders_integrity
            except:
                pass
        return settings_info

    def set_settings(self, get):
        """修改配置文件"""
        site = None
        if "site" in get:
            site = self.__get_siteName(get.site.strip())
        if not site:
            return public.returnMsg(False, tool.getMsg("PLEASE_SELECT_SITE"))
        targets = []
        if site != "global":
            if site.find(",") < 0:
                targets.append(site)
            else:
                targets = [x for x in site.split(",") if x.strip()]

        new_config = {}
        monitor = None
        if "monitor" in get:
            monitor = True if get.monitor == "true" else False
            new_config["monitor"] = monitor
        default_site = None
        if "default_site" in get:
            default_site = get.default_site
            self.set_default_site(default_site)
        auto_refresh = None
        if "autorefresh" in get:
            auto_refresh = True if get.autorefresh == "true" else False
            new_config["autorefresh"] = auto_refresh
        refresh_interval = 3
        if "refresh_interval" in get:
            refresh_interval = int(get.refresh_interval)
            if refresh_interval < 3:
                refresh_interval = 3
            new_config["refresh_interval"] = refresh_interval
        cdn = True
        if "cdn" in get:
            cdn = True if get.cdn == "true" else False
            new_config["cdn"] = cdn
        cdn_headers = None
        if "cdn_headers" in get:
            cdn_headers = get.cdn_headers
            if cdn_headers == "null":
                cdn_headers = []
            else:
                cdn_headers = [x.strip() for x in cdn_headers.split(",")]
            new_config["cdn_headers"] = cdn_headers

        exclude_extension = None
        if "exclude_extension" in get:
            exclude_extension = get.exclude_extension
            if exclude_extension == "null":
                exclude_extension = []
            else:
                exclude_extension = [x.strip() for x in
                                     exclude_extension.split(",")]
            new_config["exclude_extension"] = exclude_extension
        exclude_status = []
        if "exclude_status" in get:
            exclude_status = get.exclude_status
            if exclude_status == "null":
                exclude_status = []
            else:
                exclude_status = [x.strip() for x in exclude_status.split(",")]
            new_config["exclude_status"] = exclude_status
        save_day = 180
        if "save_day" in get:
            save_day = int(get.save_day)
            new_config["save_day"] = save_day

        if "compress_day" in get:
            new_config["compress_day"] = int(get.compress_day)

        if "exclude_url" in get:
            try:
                _url_conf = json.loads(get.exclude_url)
                new_config["exclude_url"] = _url_conf
            except Exception as e:
                print(tool.getMsg("EXCLUDE_FORMAT_ERROR"))
                new_config["exclude_url"] = []

        if "exclude_ip" in get:
            exclude_ip = get.exclude_ip
            if exclude_ip != "null":
                new_config["exclude_ip"] = exclude_ip.split(",")
            else:
                new_config["exclude_ip"] = []

        if "statistics_machine_access" in get:
            new_config["statistics_machine_access"] = True if get.statistics_machine_access.lower() == "true" else False

        if "statistics_uri" in get:
            new_config["statistics_uri"] = True if get.statistics_uri.lower() == "true" else False

        if "statistics_ip" in get:
            new_config["statistics_ip"] = True if get.statistics_ip.lower() == "true" else False

        if "record_post_args" in get:
            new_config["record_post_args"] = True if get.record_post_args.lower() == "true" else False

        if "record_get_403_args" in get:
            new_config["record_get_403_args"] = True if get.record_get_403_args.lower() == "true" else False

        if "record_get_500_args" in get:
            new_config["record_get_500_args"] = True if get.record_get_500_args.lower() == "true" else False

        data_dir = "/www/server/total/logs"
        if "data_dir" in get:
            data_dir = get.data_dir.strip()
            new_config["data_dir"] = data_dir

        ip_top_num = None
        if "ip_top_num" in get:
            ip_top_num = int(get.ip_top_num)
            if ip_top_num <= 0 or ip_top_num > 2000:
                ip_top_num = 50
            new_config["ip_top_num"] = ip_top_num

        uri_top_num = None
        if "uri_top_num" in get:
            uri_top_num = int(get.uri_top_num)
            if uri_top_num <= 0 or uri_top_num > 2000:
                uri_top_num = 50
            new_config["uri_top_num"] = uri_top_num

        push_report = False
        if "push_report" in get:
            push_report = True if get.push_report.lower() == "true" else False
            new_config["push_report"] = push_report

        # 插件本身参数
        reload_service = True
        if "reload_service" in get:
            reload_service = True if get.push_report.lower() == "true" else False

        config_path = "/www/server/total/config.json"
        config_data = self.__get_file_json(config_path)

        if site != "global":
            for target_site in targets:
                site_config = {}
                if target_site in config_data.keys():
                    site_config = config_data[target_site]

                if new_config:
                    if "exclude_ip" in new_config.keys():
                        if "exclude_ip" in site_config.keys():
                            site_config["old_exclude_ip"] = site_config["exclude_ip"]
                        else:
                            if "exclude_ip" in config_data["global"].keys():
                                site_config["old_exclude_ip"] = config_data["global"]["exclude_ip"]

                        reload_exclude_url_file = os.path.join(self.get_data_dir(), target_site, "reload_exclude_ip.pl")
                        if os.path.exists(reload_exclude_url_file):
                            os.remove(reload_exclude_url_file)
                        # public.writeFile(reload_exclude_url_file, "reload")
                    site_config.update(new_config)
                    config_data[target_site] = site_config
            try:
                if new_config["push_report"] == True:
                    # 打开推送开关全局设置
                    global_config = config_data["global"]
                    if "push_report" in global_config.keys():
                        if not global_config["push_report"]:
                            global_config["push_report"] = True
                    else:
                        global_config["push_report"] = True

            except:
                pass
        else:
            if new_config:

                if "exclude_ip" in new_config.keys():
                    # 全局配置修改排除IP，所有未记录配置的站点都标记再次重载排除IP
                    # tosites = public.M('sites').field('name').order("addtime").select()
                    # targets = [self.__get_siteName(x["name"]) for x in tosites]
                    # for xsite in targets:
                    #     reload_exclude_ip = False
                    #     if xsite not in config_data.keys():
                    #         reload_exclude_ip = True
                    #         config_data[xsite] = {}
                    #     if xsite in config_data.keys() and "exclude_ip" not in config_data[xsite].keys():
                    #         reload_exclude_ip = True

                    #     if reload_exclude_ip:
                    #         config_data[xsite]["old_exclude_ip"] = config_data["global"]["exclude_ip"]

                    if "exclude_ip" in config_data["global"].keys():
                        config_data["global"]["old_exclude_ip"] = config_data["global"]["exclude_ip"]
                    # 调整：仅标记全局排除规则变化
                    reload_exclude_url_file = os.path.join(self.get_data_dir(), "reload_exclude_ip.pl")
                    if os.path.exists(reload_exclude_url_file):
                        os.remove(reload_exclude_url_file)
                    # public.writeFile(reload_exclude_url_file, "reload")

                config = config_data["global"]
                config.update(new_config)
                config_data["global"] = config
                self.set_monitor_status(config["monitor"])

        # print("New config:" + json.dumps(config_data))
        # json配置文件写入
        public.writeFile(config_path, json.dumps(config_data))

        # lua配置文件写入前置处理
        for xsite, conf in config_data.items():
            if "exclude_url" in conf.keys():
                url_conf = {}
                for i, _o in enumerate(conf["exclude_url"]):
                    if _o["mode"] == "regular":
                        _o["url"] = tool.parse_regular_url(_o["url"])
                    url_conf[str(i + 1)] = _o
                config_data[xsite]["exclude_url"] = url_conf

            if "exclude_ip" in conf.keys() and len(conf["exclude_ip"]) > 0:
                ips = []
                for ip in conf["exclude_ip"]:
                    if ip.find("-") > 0:
                        for xip in tool.parse_ips(ip):
                            ips.append(xip)
                    else:
                        ips.append(ip)
                config_data[xsite]["exclude_ip"] = ips

            if "old_exclude_ip" in conf.keys() and len(conf["old_exclude_ip"]) > 0:
                if xsite != "global":
                    reload_exclude_url_file = os.path.join(self.get_data_dir(), xsite, "reload_exclude_ip.pl")
                else:
                    reload_exclude_url_file = os.path.join(self.get_data_dir(), "reload_exclude_ip.pl")
                if not os.path.isfile(reload_exclude_url_file):
                    del config_data[xsite]["old_exclude_ip"]
                else:
                    ips = []
                    for ip in conf["old_exclude_ip"]:
                        if ip.find("-") > 0:
                            for xip in tool.parse_ips(ip):
                                ips.append(xip)
                        else:
                            ips.append(ip)
                    if ips:
                        config_data[xsite]["old_exclude_ip"] = ips

        self.write_lua_config(config_data)

        if reload_service:
            public.serviceReload()
        return tool.returnMsg(True, "CONFIGURATION_SUCCESSFULLY")

    def set_monitor_status(self, status):
        if status == True:
            print("开启监控.")
            if os.path.isfile(self.close_file):
                os.remove(self.close_file)
            if os.path.isfile("/www/server/nginx/sbin/nginx"):
                print(os.system("cp /www/server/panel/plugin/total/total_nginx.conf /www/server/panel/vhost/nginx/total.conf"))
            if os.path.isfile("/www/server/apache/bin/httpd"):
                os.system("cp /www/server/panel/plugin/total/total_httpd.conf /www/server/panel/vhost/apache/total.conf")
        else:
            public.WriteFile(self.close_file, "closing")
            os.system("rm -f /www/server/panel/vhost/nginx/total.conf")
            os.system("rm -f /www/server/panel/vhost/apache/total.conf")

    def sync_settings(self, get):
        """同步站点配置"""
        profile = None
        if "profile" in get:
            profile = self.__get_siteName(get.profile.strip())
        tosites = None
        if "tosites" in get:
            tosites = get.tosites.strip()
        targets = []
        if tosites != "all":
            if tosites.find(",") < 0:
                targets.append(self.__get_siteName(tosites))
            else:
                targets = [self.__get_siteName(x) for x in tosites.split(",") if x.strip()]
        else:
            tosites = public.M('sites').field('name').order("addtime").select()
            targets = [self.__get_siteName(x["name"]) for x in tosites]

        new_config = {}
        monitor = None
        if "monitor" in get:
            monitor = True if get.monitor == "true" else False
            new_config["monitor"] = monitor
        auto_refresh = None
        if "autorefresh" in get:
            auto_refresh = True if get.autorefresh == "true" else False
            new_config["autorefresh"] = auto_refresh
        refresh_interval = 3
        if "refresh_interval" in get:
            refresh_interval = int(get.refresh_interval)
            if refresh_interval < 3:
                refresh_interval = 3
            new_config["refresh_interval"] = refresh_interval
        # cdn = True
        # if "cdn" in get:
        #     cdn = True if get.cdn=="true" else False
        #     new_config["cdn"] = cdn
        cdn_headers = None
        if "cdn_headers" in get:
            cdn_headers = get.cdn_headers
            if cdn_headers == "null":
                cdn_headers = []
            else:
                cdn_headers = [x.strip() for x in cdn_headers.split(",")]
            new_config["cdn_headers"] = cdn_headers

        exclude_extension = None
        if "exclude_extension" in get:
            exclude_extension = get.exclude_extension
            if exclude_extension == "null":
                exclude_extension = []
            else:
                exclude_extension = [x.strip() for x in
                                     exclude_extension.split(",")]
            new_config["exclude_extension"] = exclude_extension
        exclude_status = []
        if "exclude_status" in get:
            exclude_status = get.exclude_status
            if exclude_status == "null":
                exclude_status = []
            else:
                exclude_status = [x.strip() for x in exclude_status.split(",")]
            new_config["exclude_status"] = exclude_status

        if "exclude_url" in get:
            try:
                _url_conf = json.loads(get.exclude_url)
                new_config["exclude_url"] = _url_conf
            except Exception as e:
                print(tool.getMsg("EXCLUDE_FORMAT_ERROR"))
                new_config["exclude_url"] = []

        if "exclude_ip" in get:
            exclude_ip = get.exclude_ip
            if exclude_ip != "null":
                new_config["exclude_ip"] = exclude_ip.split(",")
            else:
                new_config["exclude_ip"] = []

        if "statistics_machine_access" in get:
            new_config["statistics_machine_access"] = True if get.statistics_machine_access.lower() == "true" else False

        if "record_post_args" in get:
            new_config["record_post_args"] = True if get.record_post_args.lower() == "true" else False

        if "record_get_403_args" in get:
            new_config["record_get_403_args"] = True if get.record_get_403_args.lower() == "true" else False

        if "record_get_500_args" in get:
            new_config["record_get_500_args"] = True if get.record_get_500_args.lower() == "true" else False

        save_day = 180
        if "save_day" in get:
            save_day = int(get.save_day)
            new_config["save_day"] = save_day

        if "compress_day" in get:
            new_config["compress_day"] = int(get.compress_day)

        config_path = "/www/server/total/config.json"
        config_data = self.__get_file_json(config_path)
        # 保存站点配置
        current_config = {}
        if profile in config_data.keys():
            current_config = config_data[profile]

        if "exclude_ip" in new_config.keys():
            if profile != "global":
                if "exclude_ip" in current_config.keys():
                    current_config["old_exclude_ip"] = current_config["exclude_ip"]
                else:
                    if "exclude_ip" in config_data["global"].keys():
                        current_config["old_exclude_ip"] = config_data["global"]["exclude_ip"]
                reload_exclude_url_file = os.path.join(self.get_data_dir(), profile, "reload_exclude_ip.pl")
                public.writeFile(reload_exclude_url_file, "reload")

        current_config.update(new_config)
        config_data[profile] = current_config

        # 同步配置
        for target_site in targets:
            site_profile = {}
            if target_site in config_data.keys():
                site_profile = config_data[target_site]

            if new_config:

                if "exclude_ip" in new_config.keys():
                    if target_site != "global":
                        if "exclude_ip" in site_profile.keys():
                            site_profile["old_exclude_ip"] = site_profile["exclude_ip"]
                        else:
                            if "exclude_ip" in config_data["global"].keys():
                                site_profile["old_exclude_ip"] = config_data["global"]["exclude_ip"]
                        reload_exclude_url_file = os.path.join(self.get_data_dir(), target_site, "reload_exclude_ip.pl")
                        public.writeFile(reload_exclude_url_file, "reload")

                if profile == "global" and target_site != "global":
                    # 如果是从全局配置同步，删掉站点的自定义配置，从新恢复跟全局配置同步
                    for key, conf in new_config.items():
                        if key in site_profile.keys():
                            del site_profile[key]
                else:
                    site_profile.update(new_config)
                config_data[target_site] = site_profile

        public.writeFile(config_path, json.dumps(config_data))

        for xsite, conf in config_data.items():
            if "exclude_url" in conf.keys():
                url_conf = {}
                for i, _o in enumerate(conf["exclude_url"]):
                    if _o["mode"] == "regular":
                        _o["url"] = tool.parse_regular_url(_o["url"])
                    url_conf[str(i + 1)] = _o
                config_data[xsite]["exclude_url"] = url_conf

            if "exclude_ip" in conf.keys() and len(conf["exclude_ip"]) > 0:
                ips = []
                for ip in conf["exclude_ip"]:
                    if ip.find("-") > 0:
                        for xip in tool.parse_ips(ip):
                            ips.append(xip)
                    else:
                        ips.append(ip)
                config_data[xsite]["exclude_ip"] = ips

            if "old_exclude_ip" in conf.keys() and len(conf["old_exclude_ip"]) > 0:
                # 清理已经重载过的排除记录
                reload_exclude_url_file = os.path.join(self.get_data_dir(), xsite, "reload_exclude_ip.pl")
                if not os.path.isfile(reload_exclude_url_file):
                    del config_data[xsite]["old_exclude_ip"]
                else:
                    ips = []
                    for ip in conf["old_exclude_ip"]:
                        if ip.find("-") > 0:
                            for xip in tool.parse_ips(ip):
                                ips.append(xip)
                        else:
                            ips.append(ip)
                    if ips:
                        config_data[xsite]["old_exclude_ip"] = ips

        lua_config = LuaMaker.makeLuaTable(config_data)
        lua_config = "return " + lua_config
        public.WriteFile("/www/server/total/total_config.lua", lua_config)
        public.serviceReload()
        return tool.returnMsg(True, "CONFIGURATION_SYNC_SUCCESSFULLY")

    def get_uri_stat(self, get, flush=True):
        try:
            ts = None
            site = "all"
            if "site" in get:
                site = self.__get_siteName(get.site)
            query_date = "today"
            if "query_date" in get:
                query_date = get.query_date
            top = 0
            if "top" in get:
                top = int(get.top)

            uri_top_num = 50
            settings = self.get_site_settings("global")
            if "uri_top_num" in settings.keys():
                uri_top_num = int(settings["uri_top_num"])
            if not top:
                top = uri_top_num
            if not top:
                top = 50
            get_spider_flow = False
            if "get_spider_flow" in get:
                get_spider_flow = True

            self.set_module_total('get_uri_stat')
            fields, flow_fields, spider_fields = self.get_data_fields(query_date)
            if not fields:
                return {
                    "query_date": query_date,
                    "top": top,
                    "total_req": 0,
                    "total_flow": 0,
                    "data": [],
                    "uri_top_num": uri_top_num
                }

            self.flush_data(site)
            if site == "all":
                sites = public.M('sites').field('name').order("addtime").select()
            else:
                sites = [{"name": site}]

            data = []
            for site_info in sites:
                site_name = site_info["name"]
                try:
                    # print("Get {} uri statistics.".format(site_name))
                    db_path = self.get_log_db_path(site_name, db_name=self.total_db_name)
                    if not os.path.isfile(db_path):
                        continue

                    ts = tsqlite()
                    ts.dbfile(db_path)

                    if flush:
                        self.flush_data(site_name)

                    time_start, time_end = tool.get_query_date(query_date)
                    total_sql = "select sum(req), sum(length) from request_stat where time>={} and time <={}".format(time_start, time_end)
                    total_result = ts.query(total_sql)

                    total_req = 0
                    total_flow = 0
                    if len(total_result) > 0 and type(total_result[0]) != str:
                        total_req = total_result[0][0] or 0
                        total_flow = total_result[0][1] or 0

                    if not get_spider_flow:
                        select_sql = "select uri, ({}) as uri_count, ({}) as uri_flow, ({}) as spider_flow from uri_stat where uri_count > 0 order by uri_count desc limit {};".format(fields, flow_fields, spider_fields, top)
                    else:
                        select_sql = "select uri, ({}) as uri_count, ({}) as uri_flow, ({}) as spider_flow from uri_stat where spider_flow > 0 order by uri_count,spider_flow desc limit {};".format(fields, flow_fields, spider_fields, top)
                    api_result = ts.query(select_sql)
                    for i, line in enumerate(api_result):
                        sub_data = {}
                        _uri = line[0]
                        if not _uri: continue
                        sub_data["no"] = i + 1
                        sub_data["site"] = site_name
                        sub_data["uri"] = _uri

                        count = line[1]
                        count_rate = 0
                        if count > 0 and total_req > 0:
                            count_rate = round(count / total_req * 100, 2)
                        sub_data["count"] = count
                        sub_data["count_rate"] = count_rate

                        flow = line[2]
                        flow_rate = 0
                        if flow > 0 and total_flow > 0:
                            flow_rate = round(flow / total_flow * 100, 2)

                        sub_data["flow"] = flow
                        sub_data["flow_rate"] = flow_rate

                        spider_flow_val = line[3]
                        spider_rate = 0
                        if spider_flow_val > 0 and total_flow > 0:
                            spider_rate = round(spider_flow_val / total_flow * 100, 2)
                        sub_data["spider_flow"] = spider_flow_val
                        sub_data["spider_rate"] = spider_rate

                        data.append(sub_data)
                    if ts:
                        ts.close()
                except Exception as e:
                    print(tool.getMsg("REQUEST_SITE_INTERFACE_ERROR", (site_name, "get_uri_stat", str(e))))
                    # print("Get {} uri stat error: {}.".format(site_name, str(e)))
            self.switch_site(get)
            return {
                "query_date": query_date,
                "top": top,
                "data": data,
                "total_req": total_req,
                "total_flow": total_flow,
                "uri_top_num": uri_top_num,
                "get_spider_flow": get_spider_flow
            }
        except Exception as e:
            return tool.returnMsg(
                False,
                "REQUEST_INTERFACE_ERROR",
                args=(tool.getMsg("INTERFACE_URI_STAT"), str(e),)
            )
        finally:
            if ts:
                ts.close()

    def get_ip_segment_area(self, ips):
        """
        " search ip by ip2region
        """
        res = []
        dbFile = "/www/server/panel/plugin/total/library/ip.db"
        if (not os.path.isfile(dbFile)) or (not os.path.exists(dbFile)):
            # print("[Error]: Specified db file is not exists.")
            return res

        try:
            from ip2Region import Ip2Region
            searcher = Ip2Region(dbFile)
            tmp_areas = {}
            for ip_info in ips:
                _info = searcher.binarySearch(ip_info[0])
                if "city_id" in _info.keys():
                    city_id = _info["city_id"]
                    area = self.search_area(city_id)
                    if area not in tmp_areas.keys():
                        area_info = {}
                        area_info["area"] = area
                        area_info["count"] = ip_info[1]
                        area_info["flow"] = ip_info[2]

                        res.append(area_info)
                        tmp_areas[area] = len(res) - 1
                    else:
                        res[tmp_areas[area]]["count"] += ip_info[1]
                        res[tmp_areas[area]]["flow"] += ip_info[2]
        except:
            pass
        return res

    def get_ip_area_id(self, ip):
        """
        " search ip by ip2region
        """
        res = ""
        dbFile = "/www/server/panel/plugin/total/library/ip.db"
        if (not os.path.isfile(dbFile)) or (not os.path.exists(dbFile)):
            # print("[Error]: Specified db file is not exists.")
            return res

        try:
            from ip2Region import Ip2Region
            searcher = Ip2Region(dbFile)
            info = searcher.binarySearch(ip)
            city_id = res
            if "city_id" in info.keys():
                city_id = info["city_id"]
            return city_id
        except:
            pass
        return ""

    def search_area(self, area_id):
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

    def get_data_fields(self, query_date):
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

    def get_ip_stat(self, get, flush=True):
        try:
            ts = None
            site = "all"
            if "site" in get:
                site = self.__get_siteName(get.site)
            query_date = "today"
            if "query_date" in get:
                query_date = get.query_date
            top = 0
            if "top" in get:
                top = int(get.top)

            ip_top_num = 50
            settings = self.get_site_settings("global")
            if "ip_top_num" in settings.keys():
                ip_top_num = int(settings["ip_top_num"])
            if not top:
                top = ip_top_num
            if not top:
                top = 50

            self.set_module_total('get_ip_stat')

            fields, flow_fields, spider_fields = self.get_data_fields(query_date)
            if not fields:
                return {
                    "query_date": query_date,
                    "top": top,
                    "total_req": 0,
                    "total_flow": 0,
                    "data": [],
                    "ip_top_num": ip_top_num
                }

            data = []
            if site == "all":
                sites = public.M('sites').field('name').order("addtime").select()
            else:
                sites = [{"name": site}]
            to_access_online_api = self.get_online_ip_library()
            drop_list = self.get_ip_rules()
            for site_info in sites:

                site_name = ""
                try:
                    site_name = site_info["name"]

                    if query_date != 'today' or query_date != 'h1':
                        res = cache.get("GET_IP_STAT" + site_name + str(top))
                        if res:
                            self.switch_site(get)
                            return json.loads(res)

                    # print("Get site:{} ip stat.".format(site_name))

                    if flush:
                        self.flush_data(site_name)

                    db_path = self.get_log_db_path(site_name, db_name=self.total_db_name)
                    if not os.path.isfile(db_path):
                        continue

                    ts = tsqlite()
                    ts.dbfile(db_path)

                    time_start, time_end = tool.get_query_date(query_date)
                    total_sql = "select sum(req), sum(length) from request_stat where time>={} and time <={}".format(
                        time_start, time_end)
                    total_result = ts.query(total_sql)

                    total_req = 0
                    total_flow = 0
                    if len(total_result) > 0 and type(total_result[0]) != str:
                        total_req = total_result[0][0] or 0
                        total_flow = total_result[0][1] or 0

                    select_sql = "select ip, area, ({}) as ip_count, ({}) as ip_flow from ip_stat where ip_count> 0 order by ip_count desc limit {};".format(
                        fields, flow_fields, top)
                    # print("select sql:"+select_sql)
                    ips = []
                    ip_result = ts.query(select_sql)
                    # tmp_data = {}
                    ip_map = {}
                    for i, line in enumerate(ip_result):
                        append = False
                        sub_data = {}
                        sub_data["no"] = i + 1
                        sub_data["site"] = site_name
                        ip = line[0]
                        if not ip: continue
                        sub_data["ip"] = ip
                        sub_data["droped"] = ip in drop_list
                        area_id = line[1]
                        area = "-"
                        if to_access_online_api:
                            if ipaddress.ip_address(ip.strip()).is_private:
                                sub_data["area"] = "内网IP"
                                sub_data["carrier"] = "-"
                                # append = True
                            else:
                                online_cache_key = "ONLINE_AREA_" + ip
                                cache_info = cache.get(online_cache_key)
                                if cache_info:
                                    if ip in cache_info.keys():
                                        info = cache_info[ip]
                                        sub_data["area"] = self.get_online_area(info)
                                        sub_data["carrier"] = info.get("carrier", "-")
                                        # append = True
                                    else:
                                        # ips.append(ip)
                                        ip_map[ip] = i
                                else:
                                    # ips.append(ip)
                                    ip_map[ip] = i
                        else:
                            # append = True
                            if not area_id:
                                area_id = self.get_ip_area_id(ip)
                            area_cache_key = "XAREA_" + repr(area_id)
                            if cache.get(area_cache_key):
                                area = cache.get(area_cache_key)
                            else:
                                area = self.search_area(area_id)
                                cache.set(area_cache_key, area, 604800)
                            sub_data["area"] = area

                        count = line[2]
                        count_rate = 0
                        if count > 0 and total_req > 0:
                            count_rate = round(count / total_req * 100, 2)
                        sub_data["count"] = count
                        sub_data["count_rate"] = count_rate

                        flow = line[3]
                        flow_rate = 0
                        sub_data["flow"] = flow

                        if flow > 0 and total_flow > 0:
                            flow_rate = round(flow / total_flow * 100, 2)
                        sub_data["flow_rate"] = flow_rate
                        # tmp_data[ip] = sub_data

                        data.append(sub_data)

                    ips = list(ip_map.keys())
                    if ips:
                        ip_data = self.get_ip_data_from_server(ips)
                        if ip_data:
                            for _ip, info in ip_data.items():
                                area = self.get_online_area(info)
                                ip_inx = ip_map[_ip]
                                data[ip_inx]["area"] = area
                                carrier = info.get("carrier", "")
                                is_spider = self.find_zhizhu_ip(ip)
                                if is_spider:
                                    if carrier.find("蜘蛛") == -1:
                                        carrier += "/蜘蛛"
                                data[ip_inx]["carrier"] = carrier

                                online_cache_key = "ONLINE_AREA_" + _ip
                                cache_data = {
                                    _ip: info
                                }
                                cache.set(online_cache_key, cache_data, 604800)

                            # for _ip, _info in tmp_data.items():
                            #     data.append(_info)
                        else:
                            # 未查到信息
                            for _ip, inx in ip_map.items():
                                area = "-"
                                area_id = self.get_ip_area_id(ip)
                                area_cache_key = "XAREA_" + repr(area_id)
                                if cache.get(area_cache_key):
                                    area = cache.get(area_cache_key)
                                else:
                                    area = self.search_area(area_id)
                                    cache.set(area_cache_key, area)
                                data[inx]["area"] = area
                                data[inx]["carrier"] = ''
                    if ts:
                        ts.close()
                except Exception as e:
                    print("Get {} ip stat error: {}.".format(site_name, str(e)))

            self.switch_site(get)
            result = {
                "query_date": query_date,
                "top": top,
                "total_req": total_req,
                "total_flow": total_flow,
                "data": data,
                "ip_top_num": ip_top_num,
                "online_data": to_access_online_api is not None
                # "fields": fields
            }

            if query_date != 'today' or query_date != 'h1':
                cache.set("GET_IP_STAT" + site_name + str(top), json.dumps(result), 600)
            return result
        except Exception as e:
            return tool.returnMsg(
                False,
                "REQUEST_INTERFACE_ERROR",
                args=(tool.getMsg("INTERFACE_IP_STAT"), str(e),)
            )
        finally:
            if ts:
                ts.close()

    def refresh_area_cache(self, cache_data):
        public.writeFile(self.area_cache_file, json.dumps(cache_data, ensure_ascii=False))

    def get_area_cache(self):
        str_data = public.readFile(self.area_cache_file)
        if not str_data:
            return {}
        return json.loads(str_data)

    def generate_area_stat(self, site, query_date):
        try:
            ts = None
            get_online_data = self.get_online_ip_library()
            # 非精准数据包跳过区域请求
            if not get_online_data:
                return True

            db_path = self.get_log_db_path(site, db_name=self.total_db_name)

            refresh_cache = False
            area_cache_data = self.get_area_cache()

            # 清理大于两个月的缓存记录
            now = time.time()
            from copy import deepcopy
            area_cache_data_bak = deepcopy(area_cache_data)
            for ip_key, item in area_cache_data_bak.items():
                if "time" in item:
                    _write_time = item["time"]
                    if now - _write_time > 86400 * 60:
                        del area_cache_data[ip_key]
                        refresh_cache = True
            del area_cache_data_bak

            ts = tsqlite()
            ts.dbfile(db_path)

            select_sql = "select ip from ip_stat"
            ip_result = ts.query(select_sql)
            ips = ""
            count = 0
            max_number_ips = 30000
            request_wait = 10
            res = {}
            _keys = area_cache_data.keys()
            for line in ip_result:
                _ip = line[0]
                if _ip not in _keys:
                    if ips:
                        ips += ","
                    ips += _ip
                    count += 1

                if count >= max_number_ips:
                    # get data
                    retry = 2
                    while retry > 0:
                        # print("get data from server.")
                        _res = self.get_ip_data_from_server(ips)
                        if _res:
                            res.update(_res)
                            break
                        else:
                            # print("res is None.")
                            retry -= 1
                        time.sleep(request_wait)

                    # reset
                    count = 0
                    ips = ""

            if ips:
                _res = self.get_ip_data_from_server(ips)
                if _res:
                    res.update(_res)
            if res:
                try:
                    # c = 0
                    write_time = time.time()
                    for ip, info in res.items():
                        # area = self.get_online_area(info)
                        # c += 1
                        info["time"] = write_time
                        area_cache_data[ip] = info
                        refresh_cache = True
                        # print(ip, area)
                    # print(c, len(ip_result))
                except Exception as e:
                    print("更新area出错：", str(e))
                finally:
                    ts and ts.close()

            if refresh_cache:
                self.refresh_area_cache(area_cache_data)
        except Exception as e:
            print(str(e))
            print(tool.getMsg("GENERATE_AREA_INFO", args=(str(e),)))
        finally:
            ts and ts.close()

    def get_area_stat(self, get, flush=False, format_count=False):
        """获取地区访问统计

        :flush 是否及时刷新数据库
        :format_count 是否格式化数值输出，格式化之后数值将变成字符格式
        """
        try:
            # print("flush: {}, format: {}".format(flush, format_count))
            ts = None
            site = "all"
            if "site" in get:
                site = self.__get_siteName(get.site)
            query_date = "l30"
            if "query_date" in get:
                query_date = get.query_date

            top = 10
            if "top" in get:
                top = int(get.top)

            fields, flow_fields, spider_fields = self.get_data_fields(query_date)
            if not fields:
                return {
                    "query_date": query_date,
                    "top": top,
                    "total_req": 0,
                    "total_flow": 0,
                    "data": [],
                }

            data = {}
            if site == "all":
                sites = public.M('sites').field('name').order("addtime").select()
            else:
                sites = [{"name": site}]

            for site_info in sites:
                site_name = ""
                try:
                    site_name = site_info["name"]
                    area_list = []
                    # print("Get site:{} ip stat.".format(site_name))

                    if flush:
                        self.flush_data(site_name)

                    db_path = self.get_log_db_path(site_name, db_name=self.total_db_name)
                    if not os.path.isfile(db_path):
                        continue

                    ts = tsqlite()
                    ts.dbfile(db_path)

                    time_start, time_end = tool.get_query_date(query_date)
                    total_sql = "select sum(req), sum(length) from request_stat where time>={} and time <={}".format(time_start, time_end)
                    total_result = ts.query(total_sql)

                    total_req = 0
                    total_flow = 0
                    if len(total_result) > 0 and type(total_result[0]) != str:
                        # print("total result:"+str(total_result))
                        total_req = total_result[0][0] or 0
                        total_flow = total_result[0][1] or 0

                    # print("total req:" + repr(total_req))
                    # print("total flow:" + repr(total_flow))
                    select_sql = "select ip, ({}) as ip_count, ({}) as ip_flow from ip_stat where ip_count > 0".format(fields, flow_fields)
                    # print("Area select sql:"+select_sql)
                    area_result = ts.query(select_sql)
                    if ts:
                        ts.close()
                    # print(area_result)
                    get_online_data = self.get_online_ip_library()
                    area_cache_data = {}
                    if get_online_data:
                        area_cache_data = self.get_area_cache()
                        res = []
                        tmp_areas = {}
                        for ip_info in area_result:
                            ip = ip_info[0]
                            if ip in area_cache_data:
                                info = area_cache_data[ip]
                                _area = self.get_online_area(info)
                                if _area not in tmp_areas.keys():
                                    area_info = {}
                                    area_info["area"] = _area
                                    area_info["count"] = ip_info[1]
                                    area_info["flow"] = ip_info[2]

                                    res.append(area_info)
                                    tmp_areas[_area] = len(res) - 1
                                else:
                                    res[tmp_areas[_area]]["count"] += ip_info[1]
                                    res[tmp_areas[_area]]["flow"] += ip_info[2]
                        area_list = res
                    else:
                        area_list = self.get_ip_segment_area(area_result)

                    area_list = sorted(area_list, key=lambda o: o["count"], reverse=True)[:top]
                    data[site_name] = []
                    for i, line in enumerate(area_list):
                        sub_data = {}
                        sub_data["no"] = i + 1
                        # sub_data["site"] = site_name
                        sub_data["area"] = line["area"]
                        count = line["count"]
                        count_rate = 0
                        if count > 0 and total_req > 0:
                            count_rate = round(count / total_req * 100, 2)

                        sub_data["count_rate"] = count_rate
                        if count > 0 and format_count:
                            sub_data["count"] = "{:,}".format(count)

                        flow = line["flow"]
                        flow_rate = 0
                        sub_data["flow"] = flow

                        if flow > 0 and total_flow > 0:
                            flow_rate = round(flow / total_flow * 100, 2)
                        sub_data["flow_rate"] = flow_rate
                        if flow > 0 and format_count:
                            sub_data["flow"] = public.to_size(flow)
                            # print("Formated flow data:"+sub_data["flow"])
                        data[site_name].append(sub_data)
                except Exception as e:
                    print("Get {} area stat error: {}.".format(site_name, str(e)))
            return {
                "query_date": query_date,
                "top": top,
                "total_req": total_req,
                "total_flow": total_flow,
                "data": data,
                # "fields": fields
            }
        except Exception as e:
            return tool.returnMsg(
                False,
                "REQUEST_INTERFACE_ERROR",
                args=(tool.getMsg("INTERFACE_AREA_STAT"), str(e),)
            )
        finally:
            if ts:
                ts.close()

    def old_get_referer_stat(self, get, flush=True, format_count=False):
        """获取来源访问统计

        :flush 是否及时刷新数据库
        :format_count 是否格式化数值输出，格式化之后数值将变成字符格式
        """
        try:
            ts = None
            site = "all"
            if "site" in get:
                site = self.__get_siteName(get.site)
            query_date = "today"
            if "query_date" in get:
                query_date = get.query_date

            top = 10
            if "top" in get:
                top = int(get.top)

            data = []
            if site == "all":
                sites = public.M('sites').field('name').order("addtime").select()
            else:
                sites = [{"name": site}]

            for site_info in sites:
                site_name = ""
                try:
                    site_name = site_info["name"]
                    # print("Get site:{} ip stat.".format(site_name))

                    if flush:
                        self.flush_data(site_name)

                    db_path = self.get_log_db_path(site_name, db_name=self.total_db_name)
                    if not os.path.isfile(db_path):
                        continue

                    ts = tsqlite()
                    ts.dbfile(db_path)

                    time_start, time_end = tool.get_query_date(query_date)
                    total_sql = "select sum(req) from request_stat where time>={} and time <={}".format(time_start, time_end)
                    total_result = ts.query(total_sql)

                    total_req = 0
                    if len(total_result) > 0 and type(total_result[0]) != str:
                        total_req = total_result[0][0] or 0

                    # print("total req:" + repr(total_req))
                    # print("total flow:" + repr(total_flow))
                    select_sql = "select domain, sum(count) as t_count from referer_stat where time>={} and time<={} group by domain order by t_count desc limit {};".format(time_start // 100, time_end // 100, top)
                    referer_result = ts.query(select_sql)
                    # print("referer result:")
                    # print(referer_result)
                    for i, line in enumerate(referer_result):
                        sub_data = {}
                        sub_data["no"] = i + 1
                        sub_data["domain"] = line[0]

                        count = line[1]
                        if not count:
                            sub_data["count"] = 0
                            count = 0
                        count_rate = 0
                        if count > 0 and total_req > 0:
                            count_rate = round(count / total_req * 100, 2)
                        sub_data["count_rate"] = count_rate

                        if count > 0 and format_count:
                            sub_data["count"] = "{:,}".format(count)
                        else:
                            sub_data["count"] = count
                        data.append(sub_data)
                    if ts:
                        ts.close()
                except Exception as e:
                    print("Get {} referer stat error: {}.".format(site_name, str(e)))
            return {
                "query_date": query_date,
                "top": top,
                "total_req": total_req,
                "data": data,
                # "fields": fields
            }
        except Exception as e:
            return tool.returnMsg(
                False,
                "REQUEST_INTERFACE_ERROR",
                args=(
                    tool.getMsg("INTERFACE_REFERER_STAT"),
                    str(e)
                )
            )
        finally:
            if ts:
                ts.close()

    def get_path_space_info(self, get):
        """获取目录占用空间大小"""
        path = None
        if "path" in get:
            path = get.path

        if not path:
            return 0

        if not os.path.isdir(path):
            return public.returnMsg(False, "不是有效目录。")

        disk_info = psutil.disk_usage(path)
        disk_free = disk_info.free
        disk_total = disk_info.total
        # disk_free_percent = disk_free / disk_total

        path_size = public.get_path_size(path)
        return {
            "path": path,
            "disk_total": disk_total,
            "disk_free": disk_free,
            "path_size": path_size
        }

    def quick_change_data_dir(self, get):
        get.quick_mode = "true"
        return self.change_data_dir(get)

    def change_data_dir(self, get):
        """更换数据存储目录"""
        data_dir = None
        if "data_dir" in get:
            data_dir = get.data_dir.strip()
            if not os.path.isdir(data_dir):
                data_dir = None
        target_data_dir = None
        if "target_data_dir" in get:
            target_data_dir = get.target_data_dir.strip()
            if not os.path.isdir(target_data_dir):
                os.makedirs(target_data_dir)
        quick_mode = False
        if "quick_mode" in get:
            quick_mode = True if get.quick_mode == "true" else False

        if data_dir is None:
            return public.returnMsg(False, "现存储路径不是有效目录!")
        if target_data_dir is None:
            if quick_mode:
                target_data_dir = data_dir
            else:
                return public.returnMsg(False, "目标路径不是有效目录!")
        if not quick_mode:
            if target_data_dir == data_dir:
                return public.returnMsg(False, "目标路径相同，无需更换!")

        monitor_status = False
        get.site = "global"
        try:
            settings = self.get_site_settings("global")
            if settings and "monitor" in settings:
                monitor_status = settings["monitor"]
            if monitor_status:
                get.monitor = "false"
                self.set_settings(get)

            from total_logs import change_data_dir
            change_res = change_data_dir(data_dir, target_data_dir, quick_mode=quick_mode)
            if target_data_dir[-1] == "/":
                target_data_dir = target_data_dir[0:-1]
            args = public.dict_obj()
            args.data_dir = target_data_dir
            if monitor_status:
                args.monitor = monitor_status
            self.set_settings(args)
            if change_res:
                msg = "目录由 {} 更换为 {} 成功。".format(data_dir, target_data_dir)
                public.WriteLog("网站监控", msg)
                return public.returnMsg(True, msg)
            else:
                msg = "目录由 {} 更换为 {} 成功，但移动文件过程中出现错误！详细信息查看面板日志。".format(data_dir, target_data_dir)
                public.WriteLog("网站监控", msg)
                return public.returnMsg(True, msg)
        except Exception as e:
            if quick_mode:
                msg = "清除网站数据失败: {}".format(str(e))
                public.WriteLog("网站监控", msg)
                return public.returnMsg(False, msg)
            else:
                msg = "目录由 {} 更换为 {} 出现错误: {}".format(data_dir, target_data_dir, str(e))
                public.WriteLog("网站监控", msg)
                return public.returnMsg(False, msg)
        finally:
            if monitor_status:
                get.monitor = "true"
                self.set_settings(get)

    def get_report_list(self, get):
        """获取报表列表 """
        try:
            report_conn = None
            report_cur = None
            site = get.site
            year = time.strftime("%Y", time.localtime())
            if "year" in get:
                year = get.year
            report_type = "all"
            if "report_type" in get:
                report_type = get.report_type

            self.set_module_total('get_report_list')
            import sqlite3
            report_db = os.path.join(self.__frontend_path, "report.db")
            report_conn = sqlite3.connect(report_db)
            report_cur = report_conn.cursor()
            sql = "select report_id, sequence, report_cycle, report_type, generate_time, file_name, file_size from report where site='{}' and year='{}'".format(site, year)
            allow_types = {"month": "月报", "week": "周报"}
            if report_type not in allow_types.keys():
                report_type = "all"
            if report_type != "all":
                sql += " and report_type='{}'".format(allow_types[report_type])
            reportor = report_cur.execute(sql)
            report = reportor.fetchone()
            # print(report)
            data = []
            while report:
                file_name = os.path.join(self.__frontend_path, "reports", site, report[5])
                file_size = report[6]
                data.append({
                    "report_id": report[0],
                    "sequence": report[1],
                    "report_cycle": report[2],
                    "report_type": report[3],
                    "generate_time": report[4],
                    "file_size": file_size
                })
                report = reportor.fetchone()

            settings = self.get_site_settings(site)
            push_report = False
            if "push_report" in settings.keys():
                push_report = settings["push_report"]
            return {
                "status": True,
                "data": data,
                "push_report": push_report
            }
        except Exception as e:
            return tool.returnMsg(
                False,
                "REQUEST_INTERFACE_ERROR",
                args=(
                    tool.getMsg("INTERFACE_REPORT"),
                    str(e),
                )
            )
        finally:
            if report_cur:
                report_cur.close()
            if report_conn:
                report_conn.close()

    def download_report(self, get):
        """下载PDF格式报告"""
        try:
            report_conn = None
            report_cur = None
            report_id = get.report_id

            import sqlite3
            report_db = os.path.join(self.__frontend_path, "report.db")
            report_conn = sqlite3.connect(report_db)
            report_cur = report_conn.cursor()
            reportor = report_cur.execute("select file_name from report where report_id={}".format(report_id))
            report = reportor.fetchone()
            if not report:
                return tool.returnMsg(False, "REPORT_NOT_EXISTS")
            report_file_name = report[0]

            pdf_path = os.path.join(self.__frontend_path, "pdfs")
            file_name = os.path.join(pdf_path, report_file_name + ".pdf")
            if not os.path.isfile(file_name):
                if not file_name.endswith(".html"):
                    file_name = os.path.join(self.__frontend_path, "reports", report_file_name + ".html")
                else:
                    file_name = os.path.join(self.__frontend_path, "reports", report_file_name)
            return {
                "status": True,
                "data": file_name
            }
        except Exception as e:
            print("下载报表失败:" + str(e))
            return tool.returnMsg(
                False,
                "REPORT_DOWNLOAD_FAILED",
            )
        finally:
            if report_cur:
                report_cur.close()
            if report_conn:
                report_conn.close()

    def preview_report(self, get):
        """预览报告"""
        try:
            report_conn = None
            report_cur = None
            report_id = get.report_id
            site = self.__get_siteName(get.site)
            # preview_type = "html"
            import sqlite3
            report_db = os.path.join(self.__frontend_path, "report.db")
            report_conn = sqlite3.connect(report_db)
            report_cur = report_conn.cursor()
            reportor = report_cur.execute("select file_name from report where report_id={}".format(report_id))
            report = reportor.fetchone()
            if not report:
                return tool.returnMsg(False, "REPORT_NOT_EXISTS")
            report_file_name = report[0]

            file_name = os.path.join(self.__frontend_path, "reports", site, report_file_name + ".html")
            public.writeFile(os.path.join(self.__frontend_path, "templates", "preview_report.html"), public.readFile(file_name))

            if not os.path.isfile(file_name):
                return tool.returnMsg(False, "REPORT_NOT_EXISTS")
            return {
                "status": True,
                "data": file_name
            }
        except Exception as e:
            public.writeFile(
                os.path.join(self.__frontend_path, "templates", "preview_report.html"),
                tool.getMsg("REPORT_PREVIEW_ERROR", args=(str(e),))
            )
            return tool.returnMsg(
                False,
                "REPORT_PREVIEW_ERROR",
                args=(
                    str(e),
                )
            )
        finally:
            if report_cur:
                report_cur.close()
            if report_conn:
                report_conn.close()

    def erase_ip_stat(self, get):
        """擦除ip统计数据"""
        monitor_status = True
        config_path = "/www/server/total/config.json"
        try:
            conn = None
            cur = None

            settings = {}
            global_settings = {}
            if os.path.isfile(config_path):
                settings = json.loads(public.readFile(config_path))
                if "global" in settings:
                    global_settings = settings["global"]
                    monitor_status = global_settings["monitor"]

            # print("原监控状态:"+str(monitor_status))
            if monitor_status and global_settings:
                global_settings["monitor"] = False
                public.writeFile(config_path, json.dumps(settings))
                self.write_lua_config(settings)
                self.set_monitor_status(False)
                # print("监控报表已关闭。")

            site = self.__get_siteName(get.site)
            import sqlite3
            conn = sqlite3.connect(self.get_log_db_path(site, db_name=self.total_db_name))
            cur = conn.cursor()
            table_name = "ip_stat"
            selector = cur.execute("PRAGMA table_info([{}]);".format(table_name))
            update_fields = ""
            for c in selector.fetchall():
                column_name = c[1]
                if column_name == "ip": continue
                if update_fields:
                    update_fields += ","
                if column_name == "area":
                    update_fields += column_name + "=\"\""
                    continue
                update_fields += column_name + "=0"
            update_sql = "UPDATE {} SET {};".format(table_name, update_fields)
            cur.execute(update_sql)
            conn.commit()

            return tool.returnMsg(True, "ERASE_IP_STAT_SUCCESSFULLY")
        except Exception as e:
            return tool.returnMsg(
                False,
                "REQUEST_INTERFACE_ERROR",
                args=(
                    tool.getMsg("INTERFACE_ERASE_IP_STAT"),
                    str(e),
                )
            )
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

            if monitor_status and settings:
                settings = json.loads(public.readFile(config_path))
                global_settings = settings["global"]
                global_settings["monitor"] = True
                public.writeFile(config_path, json.dumps(settings))
                self.write_lua_config(settings)
                self.set_monitor_status(True)
                # print("监控报表已开启。")

    def erase_uri_stat(self, get):
        """擦除URI统计数据"""
        monitor_status = True
        config_path = "/www/server/total/config.json"
        try:
            conn = None
            cur = None

            settings = {}
            global_settings = {}
            if os.path.isfile(config_path):
                settings = json.loads(public.readFile(config_path))
                if "global" in settings:
                    global_settings = settings["global"]
                    monitor_status = global_settings["monitor"]

            # print("原监控状态:"+str(monitor_status))
            if monitor_status and global_settings:
                global_settings["monitor"] = False
                public.writeFile(config_path, json.dumps(settings))
                self.write_lua_config(settings)
                self.set_monitor_status(False)
                # print("监控报表已关闭。")

            site = self.__get_siteName(get.site)
            import sqlite3
            conn = sqlite3.connect(self.get_log_db_path(site, db_name=self.total_db_name))
            cur = conn.cursor()
            table_name = "uri_stat"
            selector = cur.execute("PRAGMA table_info([{}]);".format(table_name))
            update_fields = ""
            for c in selector.fetchall():
                column_name = c[1]
                if column_name == "uri": continue
                if column_name == "uri_md5": continue
                if update_fields:
                    update_fields += ","
                update_fields += column_name + "=0"
            update_sql = "UPDATE {} SET {};".format(table_name, update_fields)
            cur.execute(update_sql)
            conn.commit()

            return tool.returnMsg(True, "ERASE_IP_STAT_SUCCESSFULLY")
        except Exception as e:
            return tool.returnMsg(
                False,
                "REQUEST_INTERFACE_ERROR",
                args=(
                    tool.getMsg("INTERFACE_ERASE_URI_STAT"),
                    str(e),
                )
            )
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

            if monitor_status and settings:
                settings = json.loads(public.readFile(config_path))
                global_settings = settings["global"]
                global_settings["monitor"] = True
                public.writeFile(config_path, json.dumps(settings))
                self.write_lua_config(settings)
                self.set_monitor_status(True)
                # print("监控报表已开启。")

    def export_site_logs(self, get):
        """根据网站日志搜索结果导出日志数据"""
        try:
            site = get.site
            allow_fields = ["time","ip","client_port","method","domain","status_code","protocol","uri","user_agent","body_length","referer","request_time","is_spider","request_headers", "ip_list"]
            headers = ["时间","真实IP","客户端端口", "类型","域名","状态","协议","URL","User Agent","响应大小(字节)","来路","耗时(毫秒)","蜘蛛类型","请求头", "完整IP列表"]
            lang = public.GetLanguage()
            if lang.find("Chinese") < 0:
                headers = allow_fields
            headers_str = ""
            from flask import request
            ua = request.headers.get("User-Agent")
            encode = "utf-8"
            if ua.find("Windows") >= 0:
                encode = "gbk"
            export_error = False
            if "export_error" in get:
                export_error = True if get.export_error == "true" else False

            fields = "all"
            if "fields" in get:
                fields = get.fields
                indexes = [allow_fields.index(f) for f in fields.split(",") if f and f.strip() in allow_fields]
                fields = ""
                for inx in indexes:
                    _f = allow_fields[inx]
                    if fields:
                        fields += ","
                    fields += _f

                    _h = headers[inx]
                    if headers_str:
                        headers_str += ","
                    headers_str += _h

            if fields == "all":
                fields = ",".join(allow_fields)

            field_list = fields.split(',')

            total_row = -1
            if "total_row" in get:
                total_row = int(get.total_row)
            if total_row < 0:
                if not export_error:
                    total_row = self.get_site_logs_total(get)["total_row"]
                else:
                    total_row = self.get_site_error_logs_total(get)["total_row"]
            if total_row < 1:
                return tool.returnMsg(False, "EXPORT_DATA_IS_NULL")

            output_dir = os.path.join(self.__frontend_path, "output")
            if not os.path.isdir(output_dir):
                os.mkdir(output_dir)

            now = time.strftime("%Y%m%d%H%M", time.localtime())
            output_file = os.path.join(output_dir, "{}_{}_logs.csv".format(site, now))
            if export_error:
                output_file = os.path.join(output_dir, "{}_{}_errlogs.csv".format(site, now))

            if os.path.isfile(output_file):
                os.remove(output_file)
            page_size = 1000
            total_page = round(total_row // page_size)
            if total_page < 1:
                total_page = 1
            else:
                if total_row % page_size > 0:
                    total_page += 1
            page = 1
            # print("total_row:{}/total_page:{}".format(total_row, total_page))
            if is_py3:
                fp = open(output_file, "a", encoding=encode)
            else:
                fp = open(output_file, "a")
            fp.write(headers_str + "\n")
            if is_py3:
                fp.close()
                fp = open(output_file, "a", encoding="utf-8")

            spider_table = {
                "baidu": 1,
                "bing": 2,
                "qh360": 3,
                "google": 4,
                "bytes": 5,
                "sogou": 6,
                "youdao": 7,
                "soso": 8,
                "dnspod": 9,
                "yandex": 10,
                "yisou": 11,
                "other": 12
            }

            distinct_set = set()
            while page <= total_page:
                get.page = page
                get.page_size = page_size
                get.no_total_rows = "true"
                if not export_error:
                    logs = self.get_site_logs(get)
                else:
                    logs = self.get_site_error_logs(get)
                list_data = logs["list_data"]
                field_len = len(field_list)
                for log in list_data:
                    log_line = ""
                    df = [_key.replace("distinct ", "") for _key in log.keys()]
                    for k in field_list:
                        if k in df:
                            v = log[k]
                            if field_len == 1:
                                start_count = len(distinct_set)
                                distinct_set.add(log[k])
                                end_count = len(distinct_set)
                                if start_count == end_count:
                                    continue
                        else:
                            continue
                        if not v and v != 0:
                            v = ""
                        if k == "is_spider":
                            for sname, inx in spider_table.items():
                                if inx == v:
                                    v = sname
                                    break
                        if k == "time":
                            _time = time.localtime(v)
                            v = time.strftime("%Y/%m/%d %H:%M:%S", _time)
                        if k == "user_agent":
                            if v:
                                v = "\"" + v + "\""
                        if k == "request_headers":
                            if v:
                                try:
                                    obj = json.loads(v)
                                    tv = ""
                                    for sk, sv in obj.items():
                                        if tv:
                                            tv += ";"
                                        tv += sk + "=" + str(sv)
                                    v = tv
                                except:
                                    pass
                        if k == "client_port":
                            if not v or v == -1:
                                v = ""
                        if log_line:
                            log_line += ","
                        log_line += str(v)
                    fp.write(log_line + "\n")
                page += 1
            fp.close()
            # if os.path.isfile(output_file):
            #     print("文件存在")
            return {
                "status": True,
                "file_name": output_file
            }
        except Exception as e:
            return tool.returnMsg(
                False,
                "REQUEST_INTERFACE_ERROR",
                args=(
                    tool.getMsg("INTERFACE_EXPORT_LOGS"),
                    str(e),
                )
            )

    def get_online_ip_library(self):
        request_addr = None
        try:
            from pluginAuth import Plugin
            tm = Plugin("btiplibrary")
            res = tm.get_fun("get_request_address")()
            if res and "status" in res and res["status"]:
                request_addr = res["msg"]
        except Exception as e:
            pass
            # print("获取ip库地址出错。")
            # print(e)
        return request_addr

    def get_ip_info(self, get):
        ip = get.ip
        simplify = False
        if "simplify" in get:
            simplify = True if get.simplify == "true" else False

        request_addr = self.get_online_ip_library()
        res = self.get_ip_data_from_server(ip, request_addr=request_addr)
        if simplify:
            for ip, info in res.items():
                res[ip] = {
                    "area": self.get_online_area(info),
                    "carrier": info.get("carrier", "-")
                }
        return {
            "status": True,
            "data": res
        }

    def get_ip_data_from_server(self, ips, request_addr=None):
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
        """从在线IP库返回结果提取地区信息"""
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

    def change_history_data_dir(self, get):
        """更改历史日志数据的存储目录，释放/www/目录下的存储空间"""
        target_dir = ""
        if "target_dir" in get:
            target_dir = get.target_dir
        target_dir = os.path.abspath(target_dir)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        config_file = "/www/server/total/config.json"
        config = json.loads(public.readFile(config_file))
        global_config = config["global"]
        ori_history_data_dir = ""
        if "history_data_dir" in global_config:
            ori_history_data_dir = global_config["history_data_dir"]

        sites = public.M('sites').field('name').order("addtime").select()
        sites.append({'name': "btunknownbt"})
        error = False
        for site_info in sites:
            site_name = site_info["name"]
            if not os.path.exists(target_dir):
                os.mkdir(target_dir)
            from total_logs import change_site2
            res = change_site2(site_name, ori_history_data_dir, target_dir)
            if not res:
                error = True
        global_config["history_data_dir"] = target_dir
        public.writeFile(config_file, json.dumps(config))
        if error:
            return public.returnMsg(True, "数据目录更换成功，但部分文件拷贝可能失败，详情请看面板日志。")
        return public.returnMsg(True, "历史数据目录切换成功。")

    def get_ip_rules(self):
        """获取系统防火墙IP屏蔽规则列表"""
        drop_list = public.M('firewall_ip').field("address").where("types=?", ("drop",)).order("addtime desc").select()
        if drop_list:
            if type(drop_list) == list:
                address = []
                for obj in drop_list:
                    if type(obj) == dict and "address" in obj:
                        ad = obj["address"]
                        address.append(ad)
                return address
        return []

    def get_referer_stat(self, get):
        """获取站点来源统计排行

        Args:
            args (dict): 客户端客户端参数
        """
        try:
            ts = None
            site = "all"
            if "site" in get:
                site = self.__get_siteName(get.site)
            query_date = "today"
            if "query_date" in get:
                query_date = get.query_date
            top = 0
            if "top" in get:
                top = int(get.top)

            referer_top_num = 50
            settings = self.get_site_settings("global")
            if "referer_top_num" in settings.keys():
                referer_top_num = int(settings["referer_top_num"])
            if not top:
                top = referer_top_num
            if not top:
                top = 50

            fields, flow_fields, spider_fields = self.get_data_fields(query_date)
            # print("fields:")
            # print(fields)
            if not fields:
                return {
                    "query_date": query_date,
                    "top": top,
                    "total_req": 0,
                    "total_flow": 0,
                    "data": [],
                    "referer_top_num": referer_top_num
                }

            # self.flush_data(site)
            if site == "all":
                sites = public.M('sites').field('name').order("addtime").select()
            else:
                sites = [{"name": site}]

            format_count = True if "format_count" in get else False

            data = []
            for site_info in sites:
                site_name = site_info["name"]
                try:
                    # print("Get {} uri statistics.".format(site_name))
                    db_path = self.get_log_db_path(site_name, db_name=self.total_db_name)
                    if not os.path.isfile(db_path):
                        continue

                    ts = tsqlite()
                    ts.dbfile(db_path)

                    if "request_in_panel" in get:
                        self.flush_data(site_name)

                    time_start, time_end = tool.get_query_date(query_date)
                    total_sql = "select sum(req), sum(length) from request_stat where time>={} and time <={}".format(time_start, time_end)
                    total_result = ts.query(total_sql)

                    total_req = 0
                    total_flow = 0
                    if len(total_result) > 0 and type(total_result[0]) != str:
                        total_req = total_result[0][0] or 0
                        total_flow = total_result[0][1] or 0

                    select_sql = "select referer, ({}) as referer_count, ({}) as referer_flow from referer2_stat where referer_count > 0 order by referer_count desc limit {};".format(fields, flow_fields, top)
                    api_result = ts.query(select_sql)
                    for i, line in enumerate(api_result):
                        sub_data = {}
                        referer = line[0]
                        if not referer: continue
                        sub_data["no"] = i + 1
                        sub_data["site"] = site_name
                        sub_data["domain"] = referer

                        count = line[1]
                        count_rate = 0
                        if count > 0 and total_req > 0:
                            count_rate = round(count / total_req * 100, 2)
                        if count > 0 and format_count:
                            sub_data["count"] = "{:,}".format(count)
                        else:
                            sub_data["count"] = count
                        sub_data["count_rate"] = count_rate

                        flow = line[2]
                        flow_rate = 0
                        if flow > 0 and total_flow > 0:
                            flow_rate = round(flow / total_flow * 100, 2)

                        if flow > 0 and format_count:
                            sub_data["flow"] = public.to_size(flow)
                        else:
                            sub_data["flow"] = flow
                        sub_data["flow_rate"] = flow_rate
                        data.append(sub_data)
                    if ts:
                        ts.close()
                except Exception as e:
                    print(tool.getMsg("REQUEST_SITE_INTERFACE_ERROR", (site_name, "get_referer_stat", str(e))))
                    # print("Get {} uri stat error: {}.".format(site_name, str(e)))
            self.switch_site(get)
            return {
                "query_date": query_date,
                "top": top,
                "data": data,
                "total_req": total_req,
                "total_flow": total_flow,
                "referer_top_num": referer_top_num
            }
        except Exception as e:
            return tool.returnMsg(
                False,
                "REQUEST_INTERFACE_ERROR",
                args=(tool.getMsg("INTERFACE_REFERER_STAT"), str(e),)
            )
        finally:
            if ts:
                ts.close()

    def ip_classify(self, ip_list):
        '''为客户端请求IP进行归类，突出请求数量大的IP段

        统计数据结构:
        data = {
            "192.168.1": {  # IP段
                "count": 12,  # 该IP段的请求量
                "detail": {  # 具体每个IP请求次数
                    "192.168.1.1": 10,
                    "232.22.33.4": 2
                }
            }
        }
        '''
        res = {}
        for i in range(0, len(ip_list)):
            _ip = ip_list[i]
            pre_ip = _ip[:_ip.rfind(".")]
            if pre_ip in res.keys():
                res[pre_ip]["count"] = res[pre_ip]["count"] + 1
                if _ip not in res[pre_ip]["detail"]:
                    res[pre_ip]["detail"][_ip] = 1
                else:
                    res[pre_ip]["detail"][_ip] = res[pre_ip]["detail"][_ip] + 1
            else:
                res[pre_ip] = {}
                res[pre_ip]["detail"] = {}
                res[pre_ip]["count"] = 1
                res[pre_ip]["detail"][_ip] = 1

        new_res = sorted(res.items(), key=lambda x: x[1]["count"], reverse=True)
        # 单个IP只请求一次的忽略
        new_res = [obj for obj in new_res if obj[1]["count"] > 1]
        return new_res

    def find_zhizhu_ip(self, ip, cls_name=None):
        """从IP蜘蛛库中查找IP"""
        if not ip:
            return False
        zhizhu_cls = {
            "types": [{
                "id": 1,
                "name": "百度",
                "ua_key": "Baiduspider",
                "host_key": "baidu"
            }, {
                "id": 2,
                "name": "Google",
                "ua_key": "Googlebot",
                "host_key": "google"
            }, {
                "id": 3,
                "name": "360",
                "ua_key": "360Spider",
                "host_key": "0"
            }, {
                "id": 4,
                "name": "搜狗",
                "ua_key": "Sogou",
                "host_key": "sogou"
            }, {
                "id": 5,
                "name": "雅虎",
                "ua_key": "Yahoo!",
                "host_key": "yahoo"
            }, {
                "id": 6,
                "name": "必应",
                "ua_key": "bingbot",
                "host_key": "msn.com"
            }, {
                "id": 7,
                "name": "头条",
                "ua_key": "bytespider",
                "host_key": "bytedance.com"
            }],
        }
        # zhizhu_cls = json.loads(public.readFile("/www/server/panel/plugin/total/test/zhi.json"))["types"]
        for cls in zhizhu_cls["types"]:
            if cls_name:
                if cls != cls_name:
                    continue
            # print(cls)

            cache_key = "SPIDERS_" + str(cls["id"])
            cache_data = cache.get(cache_key)
            if cache_data:
                data = cache_data
            else:
                data_path = "/www/server/total/xspiders/{}.json".format(cls["id"])
                _d = public.readFile(data_path)
                if not _d: continue

                data = json.loads(_d)
                cache.set(cache_key, data, 60 * 2)

            if ip in data:
                # print("IP:{} 已在蜘蛛IP库中。".format(ip))
                return True
        return False

    def stop_nps(self, get):
        public.WriteFile("data/total_nps.pl", "")
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
                "product_type": 2
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

    def get_nps(self, get):
        data = {}
        data['safe_day'] = 0
        time_path = "/www/server/panel/plugin/total/install_time.pl"
        insta_time = 0
        if not os.path.exists(time_path):
            public.writeFile(time_path, str(int(time.time())))

        else:
            try:
                insta_time = int(public.ReadFile(time_path))
            except:
                public.writeFile(time_path, str(int(time.time())))
                insta_time = 0
        if insta_time != 0: data['safe_day'] = int((time.time() - insta_time) / 86400)
        if not os.path.exists("data/total_nps.pl"):
            # 如果安全运行天数大于5天 并且没有没有填写过nps的信息
            data['nps'] = False
            public.run_thread(self.get_nps_questions, ())
            if os.path.exists("data/total_nps_count.pl"):
                # 读取一下次数
                count = public.ReadFile("data/total_nps_count.pl")
                if count:
                    count = int(count)
                    public.WriteFile("data/total_nps_count.pl", str(count + 1))
                    data['nps_count'] = count + 1
            else:
                public.WriteFile("data/total_nps_count.pl", "1")
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
            "product_type": 2,
            "rate": get.rate,
            "feedback": get.feedback,
            "phone_back": get.phone_back,
            "questions": json.dumps(get.questions)
        }
        try:
            requests.post(api_url, data=data, timeout=10).json()
            public.WriteFile("data/total_nps.pl", "1")
        except:
            pass
        return public.returnMsg(True, "提交成功")

    def get_site_logs(self, get):
        try:
            query_date = "today"
            if 'query_date' in get:
                query_date = get.query_date
            site_name = ''
            if 'site' in get:
                site_name = get.site
            ip_list = ''
            if 'ip' in get:
                ip_list = get.ip
            uri = ''
            if 'search_url' in get:
                uri = get.search_url
            page = 1
            if 'page' in get:
                page = int(get.page)
            page_size = 10
            if 'page_size' in get:
                page_size = int(get.page_size)
            desc = True
            if "desc" in get:
                desc = True if get.desc == "true" else False

            ip_list = ip_list.replace('*', '')
            start_timestamp, end_timestamp = tool.get_query_timestamp(query_date)
            query_dates = tool.split_query_date(start_timestamp, end_timestamp)
            res_query_date = "{}-{}".format(start_timestamp, end_timestamp)

            if not query_dates:
                res_data = {
                    "status": True,
                    "query_date": res_query_date,
                    "page": page,
                    "page_size": page_size,
                    "total_row": 0,
                    "list_data": [],
                    "ip_classify": {},
                    "load_ip_info": False
                }
                return res_data

            self.flush_data(site_name)
            flag = False
            if query_date.startswith("h1"):
                flag = query_dates[0]
            selected_rows = 0  # 已查询行数
            target_rows = page_size  # 目标结果数
            select_offset = (page - 1) * page_size  # 预期偏移量
            data = []
            current_offset = 0
            data_dir = self.get_data_dir()
            history_dir = self.get_history_data_dir()
            total = self.get_site_logs_total(get)['total_row']
            now_timestamp = time.time()

            def sort_key(d):
                return d[0]

            if not desc:
                query_dates.sort(key=sort_key, reverse=False)

            for date_tuple in query_dates:
                start_date, end_date = date_tuple
                day = time.strftime("%Y%m%d", time.localtime(start_date))
                start_str = time.strftime("%Y%m%d%H", time.localtime(start_date))
                end_str = time.strftime("%Y%m%d%H", time.localtime(end_date))
                not_today = now_timestamp < start_date or now_timestamp > end_date and not flag
                file_path = os.path.join(data_dir, site_name, str(day) + '.txt')
                if not_today:
                    if not os.path.exists(file_path):
                        file_path = os.path.join(history_dir, site_name, str(day) + '.tar.gz')

                db_path = self.get_log_db_path(site_name, db_name='cursor_log/' + day + '.db')

                if not os.path.exists(file_path) or not os.path.exists(db_path):
                    # print("未找到db文件。")
                    continue
                ts = tsqlite()
                ts.dbfile(db_path)
                conditions_str = file_path + start_str + end_str + ip_list + uri
                conditions_key = public.md5(conditions_str)
                cache_result = cache.get(conditions_key)
                if not cache_result:
                    continue

                total_row = cache_result
                if select_offset - current_offset >= total_row:
                    current_offset += total_row
                    continue
                else:
                    sub_offset = select_offset - current_offset
                    current_offset = select_offset

                _, suffix = os.path.splitext(file_path)
                if suffix != '.txt':
                    if not ip_list and not uri:
                        res = self._get_targz_logs_info(ts, file_path, sub_offset, page_size, total_row, desc)
                    else:
                        cursors = self._get_logs_cursor(ts, ip_list, uri)
                        res = self._get_targz_site_data(ts, cursors, file_path, sub_offset, page_size, desc)

                else:
                    if not ip_list and not uri:
                        res = self._get_logs_info(ts, file_path, sub_offset, page_size, total_row, flag, desc)
                    else:
                        cursors = self._get_logs_cursor(ts, ip_list, uri)
                        res = self._get_site_data(ts, cursors, file_path, sub_offset, page_size, total_row, desc)

                data_len = len(res)
                data += res
                selected_rows += data_len
                page_size = page_size - data_len
                if selected_rows >= target_rows:
                    break

                if ts:
                    ts.close()
            fields = "time, ip, method, domain, status_code, protocol, uri, user_agent, body_length, referer, request_time, is_spider, request_headers, ip_list, client_port"
            _columns = [column.strip() for column in fields.split(",")]
            drop_list = self.get_ip_rules()
            load_ip_info = self.get_online_ip_library() is not None
            error_count = 0
            fake_spider_count = 0
            spider_count = 0
            ip_list = []
            list_data = []
            for row in data:
                tmp1 = {}
                for column in _columns:
                    val = row[column]
                    if column == "status_code":
                        val = int(val)
                        if val >= 400:
                            error_count += 1
                    if column == "is_spider":
                        if not val:
                            val = 0
                        else:
                            val = int(val)
                        if val == 77:
                            fake_spider_count += 1
                        elif val > 0:
                            spider_count += 1

                    tmp1[column] = val
                if "ip" in tmp1:
                    _ip = tmp1["ip"]
                    tmp1["droped"] = _ip in drop_list
                    ip_list.append(_ip)
                else:
                    tmp1["droped"] = False

                list_data.append(tmp1)
                del tmp1
            ip_classify_data = {}
            if ip_list:
                ip_classify_data = self.ip_classify(ip_list)
            total_data = {
                "error": error_count,
                "fake_spider": fake_spider_count,
                "spider": spider_count
            }
            domains = []
            res_data = {
                "status": True,
                "query_date": res_query_date,
                "page": page,
                "page_size": target_rows,
                "total_row": total,
                "list_data": list_data,
                "domains": domains,
                "load_ip_info": load_ip_info,
                "total_data": total_data,
                "ip_classify": ip_classify_data
            }
            self.switch_site(get)

            return res_data
        except Exception as e:
            return tool.returnMsg(
                False,
                "REQUEST_INTERFACE_ERROR",
                args=(
                    tool.getMsg("INTERFACE_LOGS"),
                    str(e),
                )
            )

    def _change_field_name(self, data):
        res = dict()
        res['domain'] = data.get('a')
        res['client_port'] = data.get('b')
        res['body_length'] = data.get('c')
        res['ip'] = data.get('d')
        res['uri'] = data.get('e')
        res['ip_list'] = data.get('f')
        res['request_time'] = data.get('g')
        res['user_agent'] = data.get('h')
        res['protocol'] = data.get('i')
        res['method'] = data.get('j')
        res['time'] = data.get('k')
        res['is_spider'] = data.get('l')
        res['status_code'] = data.get('m')
        res['server_name'] = data.get('n')
        res['referer'] = data.get('o')
        res['request_headers'] = data.get('p')
        return res

    def _get_cursor(self, result):
        cursor = []
        for cursors in result:
            cursors = cursors[0]
            if cursors.startswith("s;"):
                cursors = cursors[2:]
            cursor += cursors.split(';')
        cursor = [int(i) for i in cursor]
        return cursor

    def _get_site_data(self, ts, cursor, file_path, sub_offset, page_size, total_row, desc):
        headers_list = []
        referer_list = []
        ua_set = set()
        uri_set = set()
        data = list()
        cursor.sort()
        if desc:
            cursor.reverse()
        if sub_offset > total_row:
            return [], headers_list
        end = sub_offset + page_size
        if end > total_row:
            end = total_row
        cursor = cursor[sub_offset: end]
        with open(file_path, 'r+') as f:
            for i in cursor:
                f.seek(int(i))
                res = json.loads(f.readline().strip('\n').strip('0'))
                res = self._change_field_name(res)
                if res['user_agent']:
                    ua_set.add(str(res['user_agent']))
                if res['uri']:
                    uri_set.add(str(res['uri']))
                if res['request_headers']:
                    headers_list.append(res['request_headers'])
                if res['referer']:
                    referer_list.append(res['referer'])
                data.append(res)

        data = self._change_user_agent(data, ua_set, ts)
        data = self._change_request_uri(data, uri_set, ts)
        if headers_list:
            data = self._change_request_headers(data, headers_list, ts)
        if referer_list:
            data = self._change_referer(data, referer_list, ts)

        return data

    def _get_targz_site_data(self, ts, cursor, file_path, sub_offset, page_size, desc):
        headers_list = []
        referer_list = []
        ua_set = list()
        uri_set = list()
        data = list()
        cursor.sort()
        if desc:
            cursor.reverse()
        tf = tarfile.open(name=file_path, mode='r:gz')
        for member in tf.getmembers():
            f = tf.extractfile(member)
            cursor = cursor[sub_offset: sub_offset + page_size]
            for i in cursor:
                f.seek(int(i))
                content = f.readline().decode()
                if content:
                    res = json.loads(content.strip('\n').strip('0'))
                    res = self._change_field_name(res)
                    if res['user_agent']:
                        ua_set.add(str(res['user_agent']))
                    if res['uri']:
                        uri_set.add(str(res['uri']))
                    if res['request_headers']:
                        headers_list.append(res['request_headers'])
                    if res['referer']:
                        referer_list.append(res['referer'])
                    data.append(res)
                else:
                    break
            f.close()
        tf.close()
        data = self._change_user_agent(data, ua_set, ts)
        data = self._change_request_uri(data, uri_set, ts)
        if headers_list:
            data = self._change_request_headers(data, headers_list, ts)
        if referer_list:
            data = self._change_referer(data, referer_list, ts)
        return data

    # 转换user_agent
    def _change_user_agent(self, data, ua_set, ts):
        ua_dict = {}
        if ua_set:
            sql = 'SELECT id, user_agent FROM user_agent where id in ({});'.format(','.join(ua_set))
            user_agent = ts.query(sql)
            ua_dict = {i[0]: i[1] for i in user_agent}
        for i in data:
            i['user_agent'] = ua_dict.get(i['user_agent'])
        return data

    # 转换request_uri
    def _change_request_uri(self, data, uri_set, ts):
        ua_dict = {}
        if uri_set:
            sql = 'SELECT id, request_uri FROM request_uri where id in ({});'.format(','.join(uri_set))
            user_agent = ts.query(sql)
            ua_dict = {i[0]: i[1] for i in user_agent}
        for i in data:
            i['uri'] = ua_dict.get(i['uri'])
        return data

    # 转换request_headers
    def _change_request_headers(self, data, headers_list, ts):
        headers_dict = {}
        num = len(headers_list)
        value_str = "?," * num
        if headers_list:
            sql = 'SELECT id, request_headers FROM request_headers where id in ({});'.format(value_str[:-1])
            request_headers = ts.query(sql, headers_list)
            headers_dict = {i[0]: i[1] for i in request_headers}
        for i in data:
            i['request_headers'] = headers_dict.get(i['request_headers'])
        return data

    # 转换referer
    def _change_referer(self, data, referer_list, ts):
        referer_dict = {}
        num = len(referer_list)
        value_str = "?," * num
        if referer_list:
            sql = 'SELECT id, referer FROM referer where id in ({});'.format(value_str[:-1])
            request_referer = ts.query(sql, referer_list)
            referer_dict = {i[0]: i[1] for i in request_referer}
        for i in data:
            i['referer'] = referer_dict.get(i['referer'])
        return data

    # 获取日志数量
    def _get_logs_cursor(self, ts, ip_list, uri):
        cursors = []
        if ip_list and uri:
            ip_sql = "SELECT cursor FROM ip_cursor where ip_list like '%{}%';".format(ip_list)
            ip_result = ts.query(ip_sql)
            uri_sql = "SELECT cursor FROM uri_cursor where uri like '%{}%';".format(uri)
            uri_result = ts.query(uri_sql)

            if ip_result and uri_result:
                ip_cursors = self._get_cursor(ip_result)
                uri_cursors = self._get_cursor(uri_result)
                cursors = list(set(ip_cursors) & set(uri_cursors))

        elif ip_list:
            # 根据ip查询日志
            sql = "SELECT cursor FROM ip_cursor where ip_list like '%{}%';".format(ip_list)
            result = ts.query(sql)
            if result:
                cursors = self._get_cursor(result)

        elif uri:
            # 根据uri查询日志
            sql = "SELECT cursor FROM uri_cursor where uri like '%{}%';".format(uri)
            result = ts.query(sql)
            if result:
                cursors = self._get_cursor(result)

        return cursors

    def _get_logs_info(self, ts, file_path, sub_offset, page_size, total_row, flag, desc):
        headers_list = []
        referer_list = []
        data = []
        ua_set = set()
        uri_set = set()
        with open(file_path, 'r') as f:
            if desc:
                current = total_row - sub_offset
                offset = current - page_size
                if offset < 0:
                    page_size = page_size - abs(offset)
                    offset = 0
            else:
                offset = sub_offset
                if sub_offset + page_size > total_row:
                    page_size = total_row - sub_offset
            f.seek(offset * self.line_size)
            for i in range(page_size):
                res = f.readline().strip('\n').strip('0')
                res = json.loads(res)
                res = self._change_field_name(res)
                if flag:
                    if not self._verification_data(res['time'], flag):
                        break
                if res['user_agent']:
                    ua_set.add(str(res['user_agent']))
                if res['uri']:
                    uri_set.add(str(res['uri']))
                if res['request_headers']:
                    headers_list.append(res['request_headers'])
                if res['referer']:
                    referer_list.append(res['referer'])
                data.append(res)
        data = self._change_user_agent(data, ua_set, ts)
        data = self._change_request_uri(data, uri_set, ts)
        if headers_list:
            data = self._change_request_headers(data, headers_list, ts)
        if referer_list:
            data = self._change_referer(data, referer_list, ts)
        data.sort(key=lambda o: o["time"], reverse=desc)
        return data

    def _get_targz_logs_info(self, ts, file_path, sub_offset, page_size, total_row, desc):
        data = []
        ua_set = set()
        uri_set = set()
        headers_list = []
        referer_list = []
        tf = tarfile.open(name=file_path, mode='r:gz')
        for member in tf.getmembers():
            f = tf.extractfile(member)
            if desc:
                current = total_row - sub_offset
                offset = current - page_size
                if offset < 0:
                    page_size = page_size - abs(offset)
                    offset = 0
            else:
                offset = sub_offset
                if sub_offset + page_size > total_row:
                    page_size = total_row - sub_offset
            f.seek(offset * self.line_size)
            for i in range(page_size):
                content = f.readline().decode()
                if content:
                    res = json.loads(content.strip('\n').strip('0'))
                    res = self._change_field_name(res)
                    if res['user_agent']:
                        ua_set.add(str(res['user_agent']))
                    if res['uri']:
                        uri_set.add(str(res['uri']))
                    if res['request_headers']:
                        headers_list.append(res['request_headers'])
                    if res['referer']:
                        referer_list.append(res['referer'])
                    data.append(res)
                else:
                    break
            f.close()
        tf.close()
        data = self._change_user_agent(data, ua_set, ts)
        data = self._change_request_uri(data, uri_set, ts)
        if headers_list:
            data = self._change_request_headers(data, headers_list, ts)
        if referer_list:
            data = self._change_referer(data, referer_list, ts)
        data.sort(key=lambda o: o["time"], reverse=desc)
        return data

    # 递归查询近一小时日志数
    def _get_hour_rows(self, f, flag, stats, n=1000, row=0, offset=0):
        if n == 0:
            return row

        while True:
            offset += self.line_size * n
            if stats - offset < 0:
                break
            f.seek(stats - offset)
            res = json.loads(f.readline().strip('\n').strip('0'))
            log_time = int(res.get('k'))
            if log_time >= flag[0]:
                row += n
            else:
                break
        offset -= self.line_size * n
        return self._get_hour_rows(f, flag, stats, n // 10, row, offset)

    def _verification_data(self, log_time, flag):
        if log_time > flag[0]:
            return True
        return False

    def _get_search_hour_rows(self, cursor_list, file_path, flag):
        cursor_list.sort()
        cursor_list.reverse()
        f = open(file_path, 'r')
        num = len(cursor_list)

        # 递归查询近一小时日志数
        def get_hour_total(f, flag, num, n=1000, row=0):
            if n == 0:
                return row
            while True:
                offset = row + n
                if offset <= num:
                    f.seek(cursor_list[offset - 1])
                    res = json.loads(f.readline().strip('\n').strip('0'))
                    log_time = int(res.get('k'))
                    if log_time >= flag[0]:
                        row += n
                    else:
                        break
                else:
                    break
            return get_hour_total(f, flag, num, n // 10, row)

        return get_hour_total(f, flag, num)

    # 获取错误日志数量
    def _get_error_logs_total(self, ts, status_code):
        cursors = []
        status_code_50x = [500, 501, 502, 503, 504, 505, 506, 507, 509]
        status_code_40x = [400, 401, 402, 403, 404, 405, 406, 407, 408, 409]
        status_code_5xx = [500, 501, 502, 503, 504, 505, 506, 507, 509, 510]
        status_code_4xx = [400, 401, 402, 403, 404, 405, 406, 407, 408, 409,
                           410, 411, 412, 413, 414, 415, 416, 417, 418, 421,
                           422, 423, 424, 425, 426, 449, 451, 499]
        if status_code in ["5xx", "5**", "5XX"]:
            status_codes = ",".join([str(s) for s in status_code_5xx])
        elif status_code in ["50x", "50X", "50*"]:
            status_codes = ",".join([str(s) for s in status_code_50x])
        elif status_code in ["4xx", "4**", "4XX"]:
            status_codes = ",".join([str(s) for s in status_code_4xx])
        elif status_code in ["40x", "40X", "40*"]:
            status_codes = ",".join([str(s) for s in status_code_40x])
        elif status_code == "all":
            status_codes = ",".join(
                [str(s) for s in (status_code_5xx + status_code_4xx)])
        else:
            status_codes = status_code
        where_sql = " where status_code in ({})".format(status_codes)

        select_sql = 'SELECT cursor FROM error_logs' + where_sql
        result = ts.query(select_sql)
        if result:
            cursors = self._get_cursor(result)
        return cursors
