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
# | 宝塔网站监控报表 - total_main
# +-------------------------------------------------------------------
from __future__ import absolute_import, division, print_function

import datetime
import json
import os
import sys
import time
import ipaddress
import contextlib
import requests
import zipfile

_ver = sys.version_info
is_py2 = (_ver[0] == 2)
is_py3 = (_ver[0] == 3)

os.chdir("/www/server/panel")
sys.path.insert(0, "class/")

import public
from BTPanel import cache

from lua_maker import LuaMaker
from tsqlite import tsqlite
import total_tools as tool

from total_base import totalBase


class total_main(totalBase):
    def __init__(self):
        super().__init__()
        self.__config = {}
        self.area_cache_file = self.frontend_path + "/area_cache.json"
        self.sites = self.get_sites()

    def get_site_lists(self, get):
        '''
        获取所有网站列表
        :param get:
        :return:
        '''
        if not self.sites:
            return {
                "status": False,
                "msg": tool.getMsg("PLEASE_CREATE_SITE")
            }

        tool.write_site_domains()
        if os.path.exists('/www/server/apache'):
            if not os.path.exists('/usr/local/memcached/bin/memcached'):
                return tool.returnMsg(False, 'MEMCACHE_CHECK')
            if not os.path.exists('/var/run/memcached.pid'):
                return public.returnMsg(False, 'MEMCACHE_CHECK2')

        res_site = []
        for site in self.sites:
            res_site.append(site["name"])

        default_site = self.get_default_site()
        res_data = {
            "status": True,
            "data": res_site,
            "default": default_site
        }
        return res_data

    def get_realtime_request(self, site=None):
        '''
        获取实时请求数
        @param site:
        @return:
        '''
        res_data = []
        if site is not None:
            log_file = self.plugin_path + "/logs/{}/req_sec.json".format(site)
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
        '''
        获取实时流量
        @param site:
        @return:
        '''
        res_data = []
        if site is not None:
            flow_file = self.plugin_path + "/logs/{}/flow_sec.json".format(
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
        '''
        获取指定站点概览页的统计数据
        @param site:
        @param start_date:
        @param end_date:
        @return:
        '''
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

    def get_site_overview(self, get):
        '''
        获取指定网站概览数据
        @param get:
        @return:
        '''
        if not self.sites:
            return {
                "status": False,
                "msg": tool.getMsg("PLEASE_CREATE_SITE")
            }
        try:
            # 根据传入的网站名称检查实际网站名
            site = self.get_siteName(get.site)
            # 查询日期
            query_date = get.query_date if 'query_date' in get else "today"
            # 需要查询什么数据
            target = get.target if 'target' in get else "pv"
            # 按时或按天
            time_scale = get.time_scale if 'time_scale' in get else 'hour'
            # 是否对比
            compare = get.compare.lower() == "true" if 'compare' in get else False
            # 对比前一天或上周同一天
            if compare:
                compare_date = get.compare_date if 'compare_date' in get else "yesterday"
            # 查询时间
            request_time = get.request_data_time if 'request_data_time' in get else None
            # 是否查看列表视图
            list_display = False
            if "list_display" in get:
                list_display = get.list_display.lower() == "true"

            self.set_module_total('get_site_overview')
            # print("display: {}".format(get.list_display))
            # if request_time is not None:
            #     print("请求时间{}以后的数据。".format(request_time))

            # 本机的/flush_data.html请求由插件前端发起，用于刷新缓存数据实时显示数据。
            self.flush_data("127.0.0.1", site)
            data = []
            sum_data = {}
            compare_data = []
            compare_sum_data = {}

            start_date, end_date = tool.get_query_date(query_date)
            compare_start_date, compare_end_date = 0, 0
            # print("查询时间周期: {} - {}".format(start_date, end_date))
            if not list_display:
                # 获取图表视图指定网站概览页列表数据
                if request_time is not None:
                    data, sum_data = self.get_overview_by_day(
                        site, request_time, end_date,
                        time_scale=time_scale, target=target)
                else:
                    data, sum_data = self.get_overview_by_day(
                        site, start_date, end_date,
                        time_scale=time_scale, target=target)

                # 是否对比前一天或上周同一天
                if compare:
                    compare_start_date, compare_end_date = tool.get_compare_date(
                        start_date, compare_date)
                    # print("对比时间周期: {} - {}".format(compare_start_date, compare_end_date))
                    compare_data, compare_sum_data = self.get_overview_by_day(
                        site, compare_start_date, compare_end_date,
                        time_scale=time_scale, target=target)
            else:
                # 获取列表视图指定网站概览页列表数据
                data = self.get_overview_list_data(site, start_date, end_date,
                                                   time_scale=time_scale)

            # 获取实时请求数
            realtime_req = self.get_realtime_request(site=site)
            # 获取实时流量
            realtime_traffic = self.get_realtime_traffic(site=site)

            # 按照指定时间或根据实时本地时间获取时间键，如2023051609
            request_time = tool.get_time_key()
            res_query_date = "{}-{}".format(start_date, end_date)
            res_compare_date = ""
            if compare:
                res_compare_date = "{}-{}".format(compare_start_date, compare_end_date)

            # 判断是否需要迁移旧监控报表数据
            migrate = self.get_migrate_status({})
            migrate_status = migrate["status"] == "completed"

            # 获取付费ip库信息
            online_data = self.get_online_ip_library()
            # 是否安装了系统防火墙插件
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
            # 检测如果是从面板请求的,就切换监控报表默认站点
            self.switch_site(get)
            return res_data
        except Exception as e:
            return tool.returnMsg(
                False,
                "REQUEST_INTERFACE_ERROR",
                args=(tool.getMsg("INTERFACE_SITE_OVERVIEW"), str(e),)
            )

    def get_ip_stat(self, get, flush=True):
        '''
        获取指定网站ip统计
        @param get:
        @param flush:
        @return:
        '''
        if not self.sites:
            return {
                "status": False,
                "msg": tool.getMsg("PLEASE_CREATE_SITE")
            }
        try:
            ts = None
            site = self.get_siteName(get.site) if "site" in get else "all"
            query_date = get.query_date if "query_date" in get else "today"
            top = int(get.top) if "top" in get else 0

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
                sites = self.sites
            else:
                sites = [{"name": site}]

            to_access_online_api = self.get_online_ip_library()
            drop_list = self.get_ip_rules()
            for site_info in sites:
                site_name = ""
                try:
                    site_name = site_info["name"]
                    # print("Get site:{} ip stat.".format(site_name))

                    if flush:
                        self.flush_data("127.0.0.1", site_name)

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
                                is_spider = self.find_ip_for_spiders(ip)
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
            return {
                "query_date": query_date,
                "top": top,
                "total_req": total_req,
                "total_flow": total_flow,
                "data": data,
                "ip_top_num": ip_top_num,
                "online_data": to_access_online_api is not None
                # "fields": fields
            }
        except Exception as e:
            return tool.returnMsg(
                False,
                "REQUEST_INTERFACE_ERROR",
                args=(tool.getMsg("INTERFACE_IP_STAT"), str(e),)
            )
        finally:
            if ts:
                ts.close()

    def get_uri_stat(self, get, flush=True):
        '''
        获取指定网站uri统计
        @param get:
        @param flush:
        @return:
        '''
        if not self.sites:
            return {
                "status": False,
                "msg": tool.getMsg("PLEASE_CREATE_SITE")
            }
        try:
            ts = None
            site = self.get_siteName(get.site) if "site" in get else "all"
            query_date = get.query_date if "query_date" in get else "today"
            top = int(get.top) if "top" in get else 0

            uri_top_num = 50
            settings = self.get_site_settings("global")
            if "uri_top_num" in settings.keys():
                uri_top_num = int(settings["uri_top_num"])
            if not top:
                top = uri_top_num
            if not top:
                top = 50
            get_spider_flow = True if "get_spider_flow" in get else False

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

            self.flush_data("127.0.0.1", site)
            if site == "all":
                sites = self.sites
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
                        self.flush_data("127.0.0.1", site_name)

                    time_start, time_end = tool.get_query_date(query_date)
                    total_sql = "select sum(req), sum(length) from request_stat where time>={} and time <={}".format(
                        time_start, time_end)
                    total_result = ts.query(total_sql)

                    total_req = 0
                    total_flow = 0
                    if len(total_result) > 0 and type(total_result[0]) != str:
                        total_req = total_result[0][0] or 0
                        total_flow = total_result[0][1] or 0

                    if not get_spider_flow:
                        select_sql = "select uri, ({}) as uri_count, ({}) as uri_flow, ({}) as spider_flow from uri_stat where uri_count > 0 order by uri_count desc limit {};".format(
                            fields, flow_fields, spider_fields, top)
                    else:
                        select_sql = "select uri, ({}) as uri_count, ({}) as uri_flow, ({}) as spider_flow from uri_stat where spider_flow > 0 order by uri_count,spider_flow desc limit {};".format(
                            fields, flow_fields, spider_fields, top)
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
                    print(tool.getMsg("REQUEST_SITE_INTERFACE_ERROR",
                                      (site_name, "get_uri_stat", str(e))))
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

    def get_top_spiders(self, site, start_date, end_date, target, top=None):
        '''
        获取指定网站指定时间top(10)的蜘蛛来访情况
        @param site:
        @param start_date:
        @param end_date:
        @param target:
        @param top:
        @return:
        '''
        if not self.sites:
            return {
                "status": False,
                "msg": tool.getMsg("PLEASE_CREATE_SITE")
            }
        ts = self.init_ts(site, self.total_db_name)
        sum_fields = ""
        top = top if top is not None else 10
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
        '''
        获取某一天的蜘蛛详细统计
        @param get:
        @return:
        '''
        if not self.sites:
            return {
                "status": False,
                "msg": tool.getMsg("PLEASE_CREATE_SITE")
            }
        try:
            site = self.get_siteName(get.site)
            query_date = get.query_date if "query_date" in get else "today"

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

    def get_overview_by_day(
            self, site, start_date, end_date, time_scale="hour", target=None
    ):
        '''
        获取某一段时间的概览数据
        @param site:
        @param start_date:
        @param end_date:
        @param time_scale:
        @param target:
        @return:
        '''
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

    def get_site_spider_stat_by_time_interval(
            self, site, start_date, end_date, time_scale="hour", target=None
    ):
        '''
        获取某一时间区间的蜘蛛统计数据
        @param site: 站点名
        @param start_date: 起始时间
        @param end_date: 终止时间
        @param time_scale: 时间刻度
        @param target: 绘图指标
        @return:
        '''
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

    def get_spider_stat(self, get):
        '''
        获取指定网站蜘蛛统计情况
        @param get:
        @return:
        '''
        if not self.sites:
            return {
                "status": False,
                "msg": tool.getMsg("PLEASE_CREATE_SITE")
            }
        try:
            site = self.get_siteName(get.site)
            query_date = get.query_date if 'query_date' in get else "today"
            time_scale = get.time_scale if 'time_scale' in get else 'hour'
            compare = get.compare.lower() == "true" if 'compare' in get else False
            if compare:
                compare_date = get.compare_date if 'compare_date' in get else "yesterday"
            target = get.target if "target" in get else "top"
            request_time = get.request_data_time if 'request_data_time' in get else None
            page = int(get.page) if "page" in get else 1
            page_size = int(get.page_size) if "page_size" in get else 20
            orderby = get.orderby if "orderby" in get else "time"
            desc = get.desc.lower() == "true" if "desc" in get else True

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

            # 获取指定网站日志存储路劲
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

            self.flush_data("127.0.0.1", site)
            top = 5
            # self.log("site:" + site)
            # 获取指定网站的蜘蛛top
            top_columns = self.get_top_spiders(site, start_date, end_date, target, top)
            if request_time is not None:
                # 默认top的情况下，每次重新请求
                if target and target != "top":
                    data, sum_data = self.get_site_spider_stat_by_time_interval(
                        site,
                        request_time,
                        end_date,
                        time_scale=time_scale,
                        target=top_columns
                    )
                else:
                    data, sum_data = self.get_site_spider_stat_by_time_interval(
                        site,
                        start_date,
                        end_date,
                        time_scale=time_scale,
                        target=top_columns
                    )
                list_data, total_row = self.get_spider_list(
                    site,
                    request_time,
                    end_date,
                    order=orderby,
                    desc=desc,
                    page_size=page_size,
                    page=page
                )
            else:
                data, sum_data = self.get_site_spider_stat_by_time_interval(
                    site,
                    start_date,
                    end_date,
                    time_scale=time_scale,
                    target=top_columns
                )
                list_data, total_row = self.get_spider_list(
                    site,
                    start_date,
                    end_date,
                    order=orderby,
                    desc=desc,
                    page_size=page_size,
                    page=page
                )

            if compare:
                compare_start_date, compare_end_date = tool.get_compare_date(start_date,
                                                                             compare_date)
                # print("对比时间周期: {} - {}".format(compare_start_date, compare_end_date))
                compare_data, compare_sum_data = self.get_site_spider_stat_by_time_interval(
                    site,
                    compare_start_date,
                    compare_end_date,
                    time_scale=time_scale,
                    target=top_columns
                )
                res_compare_date = "{}-{}".format(compare_start_date, compare_end_date)

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
        '''
        从云端更新蜘蛛IP库
        @param get:
        @return: bool
        '''
        if not self.sites:
            return {
                "status": False,
                "msg": tool.getMsg("PLEASE_CREATE_SITE")
            }

        try:
            # 下载zip文件
            zip_url = "http://io.bt.sy/install/zizhu/zizhu.zip"
            zip_path = "/www/server/total/xspiders/zizhu.zip"
            response = requests.get(zip_url, stream=True)
            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            # 解压文件
            extract_path = "/www/server/total/xspiders"
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            # 删除zip文件
            os.remove(zip_path)

            # 更新蜘蛛IP库
            userInfo = json.loads(public.ReadFile('/www/server/panel/data/userInfo.json'))
            data22 = {"access_key": userInfo['access_key'], "uid": userInfo['uid']}
            url = public.GetConfigValue('home')+'/api/bt_waf/getSpiders'
            data_list = json.loads(public.httpPost(url, data22, timeout=3))
            has_content = False

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

            return public.returnMsg(True, "更新成功！")

        except Exception as e:
            return public.returnMsg(False, "更新失败:" + str(e))

    def get_site_client_stat_by_time_interval(
            self, site, start_date, end_date, time_scale="hour", target=None
    ):
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

        pc_clients = ["firefox", "msie", "qh360", "theworld", "tt", "maxthon", "opera", "qq", "uc",
                      "safari", "chrome", "metasr", "pc2345", "edeg"]
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

    def get_client_list(
            self, ts, site, start_date, end_date, order="time", desc=False, page_size=20, page=1
    ):
        '''
        获取客户端统计列表数据
        @param ts:
        @param site:
        @param start_date:
        @param end_date:
        @param order:
        @param desc:
        @param page_size:
        @param page:
        @return:
        '''
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

    def get_spider_list(
            self, site, start_date, end_date, order="time", desc=True, page_size=20, page=1
    ):
        '''
        获取蜘蛛统计列表数据
        @param site:
        @param start_date:
        @param end_date:
        @param order:
        @param desc:
        @param page_size:
        @param page:
        @return:
        '''
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
            if client_name == "time": continue;
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

    def get_top_clients(self, db, start_date, end_date, top=3):
        '''
        获取前top的客户端
        @param db:
        @param start_date:
        @param end_date:
        @param top:
        @return:
        '''
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
        '''
        获取客户端统计
        @param get:
        @param flush:
        @return:
        '''
        if not self.sites:
            return {
                "status": False,
                "msg": tool.getMsg("PLEASE_CREATE_SITE")
            }
        try:
            ts = None
            site = self.get_siteName(get.site)
            query_date = get.query_date if 'query_date' in get else "today"
            time_scale = get.time_scale if 'time_scale' in get else 'day'
            compare = get.compare.lower() == "true" if 'compare' in get else False
            target = get.target if "target" in get else "top"
            request_time = get.request_data_time if 'request_data_time' in get else None
            page = int(get.page) if "page" in get else 1
            page_size = int(get.page_size) if "page_size" in get else 20
            orderby = get.orderby if "orderby" in get else "time"
            desc = get.desc.lower() == "true" if "desc" in get else True
            if compare:
                compare_date = get.compare_date if 'compare_date' in get else "yesterday"

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
                self.flush_data("127.0.0.1", site)
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
                        site,
                        request_time,
                        end_date,
                        time_scale=time_scale,
                        target=top_columns
                    )
                else:
                    data, sum_data = self.get_site_client_stat_by_time_interval(
                        site,
                        start_date,
                        end_date,
                        time_scale=time_scale,
                        target=top_columns
                    )
                list_data, total_row = self.get_client_list(
                    ts,
                    site,
                    request_time,
                    end_date,
                    order=orderby,
                    desc=desc,
                    page_size=page_size,
                    page=page
                )
            else:
                data, sum_data = self.get_site_client_stat_by_time_interval(
                    site,
                    start_date,
                    end_date,
                    time_scale=time_scale,
                    target=top_columns
                )
                list_data, total_row = self.get_client_list(
                    ts,
                    site,
                    start_date,
                    end_date,
                    order=orderby,
                    desc=desc,
                    page_size=page_size,
                    page=page
                )

            if compare:
                compare_start_date, compare_end_date = tool.get_compare_date(start_date,
                                                                             compare_date)
                # print("对比时间周期: {} - {}".format(compare_start_date, compare_end_date))
                compare_data, compare_sum_data = self.get_site_client_stat_by_time_interval(
                    site,
                    compare_start_date,
                    compare_end_date,
                    time_scale=time_scale,
                    target=top_columns
                )

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
        '''
        获取错误代码列表
        @param get:
        @return:
        '''
        return {
            "status_codes": ["all", "50x", "40x", "500", "501", "502", "503", "404"]
        }

    def get_site_error_sql(self, start_date, end_date, status_code, *args, **kwargs):
        '''
        获取错误日志的sql查询条件
        @param start_date:
        @param end_date:
        @param status_code:
        @param args:
        @param kwargs:
        @return:
        '''
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
        elif status_code == "all":
            status_codes = ",".join(
                [str(s) for s in (status_code_5xx + status_code_4xx)])
        else:
            status_codes = status_code
        # ts.table("site_logs").field(fields)
        where_sql = " where time >={} and time <={}".format(start_date, end_date)
        where_sql += " and status_code in ({})".format(status_codes)
        conditions = kwargs
        if "spider" in conditions.keys():
            spider = conditions["spider"].lower()
            if spider == "only_spider":
                where_sql += " and (trim(is_spider) <> '' and is_spider>=1 and is_spider<>77)"
            if spider == "no_spider":
                where_sql += " and (is_spider=0 or is_spider='')"

        select_sql = "select {} from site_logs" + where_sql
        # print(select_sql)
        return select_sql

    def get_site_error_logs_total(self, get):
        '''
        获取网站错误日志分页
        @param get:
        @return:
        '''
        try:
            site = get.site
            conditions = {}
            query_date = get.query_date if 'query_date' in get else "today"
            status_code = get.status_code if "status_code" in get else "all"
            ori_db_path = get.db_path if "db_path" in get else None

            if "spider" in get:
                spider = get.spider
                if spider:
                    conditions["spider"] = spider


            start_date, end_date = tool.get_query_timestamp(query_date)
            now_timestamp = time.time()

            query_dates = tool.split_query_date(start_date, end_date)

            total_rows = 0
            for query_date in query_dates:
                try:
                    ts = None
                    start_timestamp, end_timestamp = query_date

                    if not ori_db_path:
                        db_path = tool.get_logs_db_name_by_timestamp(
                            site, start_timestamp, end_timestamp)
                    else:
                        db_path = ori_db_path

                    if not os.path.exists(db_path):
                        continue

                    ts = tsqlite()
                    ts.dbfile(db_path)
                    select_sql = self.get_site_error_sql(start_timestamp, end_timestamp,
                                                         status_code, **conditions)
                    conditions_str = db_path + select_sql
                    conditions_key = public.md5(conditions_str)

                    not_today = now_timestamp < start_timestamp or now_timestamp > end_timestamp
                    cache_key = conditions_key
                    # 当天总数始终更新
                    if not_today:
                        cache_row = cache.get(cache_key)
                        if cache_row:
                            total_rows += cache_row
                            # print("获取缓存总数: ", cache_key, cache_row)
                            continue

                    total_sql = select_sql.format("count(*)")
                    total_res = ts.query(total_sql)
                    total_row = int(total_res[0][0])
                    total_rows += total_row

                    # print("set error total cache:", cache_key, total_row)
                    if not_today:
                        cache.set(cache_key, total_row, 31 * 86400)


                    else:
                        # 当天缓存截止到24点
                        s, e = tool.get_timestamp_interval(time.localtime())
                        day_of_end_time = e - now_timestamp
                        # print("day of end time:", day_of_end_time)
                        cache.set(cache_key, total_row, day_of_end_time)
                except Exception as e:
                    print(e)
                finally:
                    try:
                        ts and ts.close()
                    except:
                        pass
            return {"total_row": total_rows}
        except:
            return {"total_row": 0}

    def get_site_error_logs(self, get):
        '''
        获取指定网站错误日志
        @param get:
        @return:
        '''
        if not self.sites:
            return {
                "status": False,
                "msg": tool.getMsg("PLEASE_CREATE_SITE")
            }
        try:
            ts = None
            site = get.site
            conditions = {}
            query_date = get.query_date if 'query_date' in get else "today"
            status_code = get.status_code if "status_code" in get else "all"
            page = int(get.page) if "page" in get else 1
            page_size = int(get.page_size) if "page_size" in get else 20
            orderby = get.orderby if "orderby" in get else "time"
            desc = get.desc.lower() == "true" if "desc" in get else True
            no_total = get.no_total_rows.lower() == "true" if "no_total_rows" in get else False
            fields = get.fields if "fields" in get else "all"
            ori_db_path = get.db_path if "db_path" in get else None
            offset = int(get.offset) if "offset" in get else 0

            if "spider" in get:
                spider = get.spider
                if spider:
                    conditions["spider"] = spider

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

            self.flush_data("127.0.0.1", site)
            load_ip_info = self.get_online_ip_library() is not None

            selected_rows = 0  # 已查询行数
            target_rows = page_size  # 目标结果数
            page_start = (page - 1) * page_size
            select_offset = page_start + offset  # 预期偏移量
            # print("预期offset: ", select_offset)
            current_offset = 0
            data = []
            now_timestamp = time.time()
            # 循环累加查询次数，当大于该值表示缓存丢失。500次相当于500次分页查询。
            max_loop = 500
            loop_count = 0
            missing_cache_retry = 1  # 当缓存丢失，最大重试查询次数

            for date_tuple in query_dates:
                start_date, end_date = date_tuple
                sub_offset = 0
                if not ori_db_path:
                    db_path = tool.get_logs_db_name_by_timestamp(site, start_date, end_date)
                else:
                    db_path = ori_db_path
                if not db_path:
                    continue
                if not os.path.isfile(db_path):
                    continue

                try:
                    not_today = now_timestamp < start_date or now_timestamp > end_date
                    select_sql = self.get_site_error_sql(start_date, end_date, status_code,
                                                         **conditions)
                    # print("error logs sql:", select_sql)
                    conditions_str = db_path + select_sql
                    conditions_key = public.md5(conditions_str)

                    cache_result = cache.get(conditions_key)
                    if cache_result:
                        total_row = cache_result
                        if not_today:
                            if select_offset - current_offset >= total_row:
                                current_offset += total_row
                                continue
                            else:
                                sub_offset = select_offset - current_offset
                                current_offset = select_offset
                        else:
                            if select_offset - current_offset >= total_row:
                                # 当天的总条数不可信任，达到最大边界，继续往下查找
                                sub_offset = (total_row // page_size) * page_size
                                current_offset += sub_offset
                                # print("从缓存取整总条数:", total_row, sub_offset)
                            else:
                                sub_offset = select_offset - current_offset
                                current_offset = select_offset

                    ts = None
                    ts = tsqlite()
                    ts.dbfile(db_path)

                    total_row = 0
                    if not no_total:
                        total_fields = "count(*)"
                        total_sql = select_sql.format(total_fields)
                        total_res = ts.query(total_sql)
                        total_row = int(total_res[0][0])

                    if fields == "all":
                        fields = "time, ip, method, domain, status_code, protocol, uri, user_agent, body_length, referer, request_time, is_spider, request_headers, ip_list, client_port"
                    select_data_sql = select_sql.format(fields)
                    if orderby:
                        select_data_sql += " order by " + orderby
                    if desc:
                        select_data_sql += " desc"

                    while True:
                        sub_select_data_sql = select_data_sql + " limit " + str(page_size)
                        sub_select_data_sql += " offset " + str(sub_offset)

                        sub_select_data_sql += ";"
                        # print("select sql:")
                        # print(sub_select_data_sql)
                        sub_data = ts.query(sub_select_data_sql)
                        data_len = len(sub_data)
                        if data_len == 0:
                            break

                        # selected_rows += data_len
                        sub_offset += data_len
                        current_offset += data_len
                        if current_offset > select_offset:
                            current_offset = select_offset

                        # print("当前边界: ", current_offset, "预期边界：", select_offset)

                        # 找到分页的左边界
                        if current_offset == select_offset:
                            need_rows = target_rows - selected_rows
                            # print("已查询到数据行:", selected_rows)
                            # print("还需要数据行:", need_rows)
                            if data_len > need_rows:
                                data += sub_data[:need_rows]
                            else:
                                data += sub_data
                            selected_rows += data_len
                            if selected_rows >= target_rows:
                                break
                        loop_count += 1
                        if loop_count > max_loop:
                            break

                    if selected_rows >= target_rows:
                        break
                except Exception as e:
                    print(e)
                finally:
                    try:
                        ts and ts.close()
                    except:
                        pass

            if loop_count > max_loop and missing_cache_retry > 0:
                # print("重新尝试更新总数缓存查询...")
                missing_cache_retry -= 1
                self.get_site_logs_total(get)
                return self.get_site_logs(get)

            _columns = [column.strip() for column in fields.split(",")]
            error_count = {}
            for row in data:
                i = 0
                tmp1 = {}
                for column in _columns:
                    val = row[i]
                    if column == "body_length":
                        if not val: val = 0
                    if column == "status_code":
                        if val not in error_count:
                            error_count[val] = 1
                        else:
                            error_count[val] += 1
                    tmp1[column] = row[i]
                    i += 1
                list_data.append(tmp1)
                del (tmp1)

            res_data = {
                "status": True,
                "query_date": res_query_date,
                "page": page,
                "page_size": page_size,
                "total_row": total_row,
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
        '''
        获取网站日志查询sql条件
        @param conditions:
        @return:
        '''
        start_date = conditions["start_date"]
        end_date = conditions["end_date"]
        reverse_mode = conditions["reverse_mode"] if "reverse_mode" in conditions else ""
        time_reverse = conditions["time_reverse"] if "time_reverse" in conditions else False
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
        search_url = conditions["search_url"] if "search_url" in conditions_keys else ""
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
                        where_sql += " and (ip like \"%" + ip + "\" or ip_list like \"%" + ip + "\")"
                    else:
                        where_sql += " and ip not like \"%" + ip + "\" and ip_list not like \"%" + ip + "\""
                else:
                    if not reverse_mode:
                        where_sql += " and (ip=\"" + ip + "\" or ip_list like \"%" + ip + "%\")"
                    else:
                        where_sql += " and ip<>\"" + ip + "\" and ip_list not like \"%" + ip + "%\""

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

    def get_site_logs_total(self, get):
        '''
        获取网站日志
        @param get:
        @return:
        '''
        try:
            site = get.site
            conditions = {}
            query_date = get.query_date if 'query_date' in get else "today"
            status_code = "all"
            if "status_code" in get:
                status_code = get.status_code
                conditions["status_code"] = status_code
            if "method" in get:
                method = get.method
                conditions["method"] = method
            if "spider" in get:
                spider = get.spider
                if spider:
                    conditions["spider"] = spider
            filter_type = "ip"
            if "filter_type" in get:
                allow_filters = ["ip", "domain", "uri", "user_agent", "referer", "post_header"]
                _filter_type = get.filter_type
                if _filter_type in allow_filters:
                    filter_type = _filter_type
                    if "filter_value" in get:
                        conditions[filter_type] = get.filter_value.strip()
            if "ip" in get:
                conditions["ip"] = get.ip
            if "domain" in get:
                conditions["domain"] = get.domain
            if "search_url" in get:
                conditions["search_url"] = get.search_url
            if "user_agent" in get:
                conditions["user_agent"] = get.user_agent
            if "referer" in get:
                conditions["referer"] = get.referer
            if "post_header" in get:
                conditions["post_header"] = get.post_header
            if "exact_match" in get:
                conditions[
                    "search_mode"] = "exact" if get.exact_match.lower() == "true" else "fuzzy"
            if "reverse_match" in get:
                conditions["reverse_mode"] = True if get.reverse_match.lower() == "true" else False
            if "time_reverse" in get:
                conditions["time_reverse"] = True if get.time_reverse.lower() == "true" else False
            if "response_time" in get:
                conditions["response_time"] = float(get.response_time)
                if "response_time_comparator" in get:
                    conditions["response_time_comparator"] = get.response_time_comparator
            check_total = False
            if "check_total" in get or hasattr(get, "check_total"):
                check_total = get.check_total

            # 添加日志锚点
            if 'ip' in conditions and conditions["ip"]:
                self.set_module_total('get_site_logs_total_ip')
            elif 'search_url' in conditions and conditions["search_url"]:
                self.set_module_total('get_site_logs_total_search_url')
            elif 'user_agent' in conditions and conditions["user_agent"]:
                self.set_module_total('get_site_logs_total_user_agent')

            page = 1
            if "page" in get:
                page = int(get.page)
            page_size = 100
            if "page_size" in get:
                page_size = int(get.page_size)

            ori_db_path = None
            if "db_path" in get:
                ori_db_path = get.db_path

            start_date, end_date = tool.get_query_timestamp(query_date)
            now_timestamp = time.time()

            query_dates = tool.split_query_date(start_date, end_date)

            total_rows = 0
            for query_date in query_dates:
                try:
                    if not ori_db_path:
                        db_path = ""
                    else:
                        db_path = ori_db_path
                    ts = None
                    start_timestamp, end_timestamp = query_date
                    if not db_path:
                        db_path = tool.get_logs_db_name_by_timestamp(
                            site, start_timestamp, end_timestamp)

                    if not os.path.exists(db_path):
                        # print("未找到db文件。")
                        continue

                    ts = tsqlite()
                    ts.dbfile(db_path)

                    conditions.update({
                        "start_date": start_timestamp,
                        "end_date": end_timestamp
                    })

                    select_sql = self.get_site_logs_sql(conditions)

                    # print("select total sql:")
                    conditions_str = db_path + select_sql
                    conditions_key = public.md5(conditions_str)

                    total_sql = select_sql.format("count(*)")

                    not_today = now_timestamp < start_timestamp or now_timestamp > end_timestamp
                    cache_key = conditions_key
                    # 当天总数始终更新
                    if not_today:
                        cache_row = cache.get(cache_key)
                        if cache_row:
                            total_rows += cache_row
                            # print("获取缓存总数: ", cache_key, cache_row)
                            continue

                    total_res = ts.query(total_sql)
                    total_row = int(total_res[0][0])
                    total_rows += total_row
                    # print("+", total_row)

                    if not_today:
                        cache.set(cache_key, total_row, 31 * 86400)
                    else:
                        # 当天缓存截止到24点
                        s, e = tool.get_timestamp_interval(time.localtime())
                        day_of_end_time = e - now_timestamp
                        # print("day of end time:", day_of_end_time)
                        cache.set(cache_key, total_row, day_of_end_time)
                except Exception as e:
                    print(e)
                finally:
                    try:
                        ts and ts.close()
                    except:
                        pass
            return {"total_row": total_rows}
        except Exception as e:
            return {"total_row": 0}

    def get_site_logs(self, get):
        '''
        获取指定网站的网站日志
        @param get:
        @return:
        '''
        if not self.sites:
            return {
                "status": False,
                "msg": tool.getMsg("PLEASE_CREATE_SITE")
            }
        try:
            ts = None
            conditions = {}
            site = get.site
            query_date = "today"
            if 'query_date' in get:
                query_date = get.query_date
            method = "all"
            if "method" in get:
                method = get.method
                conditions["method"] = method
            status_code = "all"
            if "status_code" in get:
                status_code = get.status_code
                conditions["status_code"] = status_code
            if "spider" in get:
                spider = get.spider
                if spider:
                    conditions["spider"] = spider
            filter_type = "ip"
            if "filter_type" in get:
                allow_filters = ["ip", "domain", "uri", "user_agent", "referer", "post_header"]
                _filter_type = get.filter_type
                if _filter_type in allow_filters:
                    filter_type = _filter_type
                    if "filter_value" in get:
                        conditions[filter_type] = get.filter_value.strip()
            if "ip" in get:
                conditions["ip"] = get.ip
            if "domain" in get:
                conditions["domain"] = get.domain
            if "search_url" in get:
                conditions["search_url"] = get.search_url
            if "user_agent" in get:
                conditions["user_agent"] = get.user_agent
            if "referer" in get:
                conditions["referer"] = get.referer
            if "post_header" in get:
                conditions["post_header"] = get.post_header
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
            no_total = False
            if "no_total_rows" in get:
                no_total = True if get.no_total_rows.lower() == "true" else False
            fields = "all"
            if "fields" in get:
                fields = get.fields
            ori_db_path = ""
            if "db_path" in get:
                ori_db_path = get.db_path
            offset = 0
            if "offset" in get:
                offset = int(get.offset)
            # exact/fuzzy

            if "exact_match" in get:
                conditions[
                    "search_mode"] = "exact" if get.exact_match.lower() == "true" else "fuzzy"
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

            self.set_module_total('get_site_logs')
            list_data = []
            total_row = 0

            start_timestamp, end_timestamp = tool.get_query_timestamp(query_date)
            # print("start timestamp:")
            # print(start_timestamp, end_timestamp)
            query_dates = tool.split_query_date(start_timestamp, end_timestamp)
            print(query_dates)
            # print("query dates:")
            # print(query_dates)
            res_query_date = "{}-{}".format(start_timestamp, end_timestamp)

            if not query_dates:
                res_data = {
                    "status": True,
                    "query_date": res_query_date,
                    "page": page,
                    "page_size": page_size,
                    "total_row": total_row,
                    "list_data": list_data,
                    "filter_type": filter_type,
                    "ip_classify": {},
                    "load_ip_info": False
                }
                return res_data

            self.flush_data("127.0.0.1", site)
            load_ip_info = self.get_online_ip_library() is not None

            selected_rows = 0  # 已查询行数
            target_rows = page_size  # 目标结果数
            page_start = (page - 1) * page_size
            select_offset = page_start + offset  # 预期偏移量
            # print("预期offset: ", select_offset)
            current_offset = 0
            data = []
            now_timestamp = time.time()
            # 循环累加查询次数，当大于该值表示缓存丢失。500次相当于500次分页查询。
            max_loop = 500
            loop_count = 0
            missing_cache_retry = 1  # 当缓存丢失，最大重试查询次数

            for date_tuple in query_dates:
                start_date, end_date = date_tuple
                sub_offset = 0
                if not ori_db_path:
                    db_path = tool.get_logs_db_name_by_timestamp(site, start_date, end_date)
                else:
                    db_path = ori_db_path
                if not db_path:
                    continue

                if not os.path.isfile(db_path):
                    continue

                conditions.update({
                    "start_date": start_date,
                    "end_date": end_date,
                })

                try:
                    # 非严格意义上的today判断
                    not_today = now_timestamp < start_date or now_timestamp > end_date
                    select_sql = self.get_site_logs_sql(conditions)

                    conditions_str = db_path + select_sql
                    conditions_key = public.md5(conditions_str)
                    cache_result = cache.get(conditions_key)
                    if cache_result:
                        total_row = cache_result
                        if not_today:
                            if select_offset - current_offset >= total_row:
                                current_offset += total_row
                                continue
                            else:
                                sub_offset = select_offset - current_offset
                                current_offset = select_offset
                        else:
                            if select_offset - current_offset >= total_row:
                                # 当天的总条数不可信任，达到最大边界，继续往下查找
                                sub_offset = (total_row // page_size) * page_size
                                current_offset += sub_offset
                                # print("从缓存取整总条数:", total_row, sub_offset)
                            else:
                                sub_offset = select_offset - current_offset
                                current_offset = select_offset

                    ts = None
                    ts = tsqlite()
                    ts.dbfile(db_path)

                    total_row = 0
                    if not no_total:
                        total_fields = "count(*)"
                        total_sql = select_sql.format(total_fields)
                        total_res = ts.query(total_sql)
                        total_row = int(total_res[0][0])

                    if fields == "all":
                        fields = "time, ip, method, domain, status_code, protocol, uri, user_agent, body_length, referer, request_time, is_spider, request_headers, ip_list, client_port"
                    select_data_sql = select_sql.format(fields)
                    if orderby:
                        select_data_sql += " order by " + orderby
                    if desc:
                        select_data_sql += " desc"

                    while True:
                        sub_select_data_sql = select_data_sql + " limit " + str(page_size)
                        sub_select_data_sql += " offset " + str(sub_offset)

                        sub_select_data_sql += ";"
                        sub_data = ts.query(sub_select_data_sql)

                        data_len = len(sub_data)
                        if data_len == 0:
                            break

                        # selected_rows += data_len
                        sub_offset += data_len
                        current_offset += data_len
                        if current_offset > select_offset:
                            current_offset = select_offset

                        # print("当前边界: ", current_offset, "预期边界：", select_offset)

                        # 找到分页的左边界
                        if current_offset == select_offset:
                            need_rows = target_rows - selected_rows
                            # print("已查询到数据行:", selected_rows)
                            # print("还需要数据行:", need_rows)
                            if data_len > need_rows:
                                data += sub_data[:need_rows]
                            else:
                                data += sub_data
                            selected_rows += data_len
                            if selected_rows >= target_rows:
                                break
                        loop_count += 1
                        if loop_count > max_loop:
                            break

                    if selected_rows >= target_rows:
                        break
                except Exception as e:
                    print(e)
                finally:
                    try:
                        ts and ts.close()
                    except:
                        pass

            if loop_count > max_loop and missing_cache_retry > 0:
                # print("重新尝试更新总数缓存查询...")
                missing_cache_retry -= 1
                self.get_site_logs_total(get)
                return self.get_site_logs(get)

            _columns = [column.strip() for column in fields.split(",")]
            drop_list = self.get_ip_rules()
            error_count = 0
            fake_spider_count = 0
            spider_count = 0
            ip_list = []
            # print("select data:")
            # print(data)
            for row in data:
                i = 0
                tmp1 = {}
                for column in _columns:
                    val = row[i]
                    if column == "body_length":
                        if not val: val = 0
                    # print("check {}={}".format(column, val))
                    if column == "status_code":
                        val = int(val)
                        if val >= 400: error_count += 1
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
                    i += 1
                if "ip" in tmp1:
                    _ip = tmp1["ip"]
                    tmp1["droped"] = _ip in drop_list
                    ip_list.append(_ip)
                else:
                    tmp1["droped"] = False

                list_data.append(tmp1)
                del (tmp1)

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
                "page_size": page_size,
                "total_row": total_row,
                "list_data": list_data,
                "domains": domains,
                "filter_type": filter_type,
                "load_ip_info": load_ip_info,
                "total_data": total_data,
                "ip_classify": ip_classify_data
            }
            self.switch_site(get)
            return res_data
        except Exception as e:
            # import traceback
            # traceback.print_exc(e)
            return tool.returnMsg(
                False,
                "REQUEST_INTERFACE_ERROR",
                args=(
                    tool.getMsg("INTERFACE_LOGS"),
                    str(e),
                )
            )

    def get_all_site(self, get):
        '''
        所有站点信息概览
        @param get:
        @return:
        '''
        if not self.sites:
            return {
                "status": False,
                "msg": tool.getMsg("PLEASE_CREATE_SITE")
            }
        try:
            query_date = get.query_date if 'query_date' in get else "today"
            orderby = get.orderby if "orderby" in get else "pv"
            desc = get.desc == "true" if "desc" in get else True

            list_data = []

            # 获取查询日期，如2021033000-2021033023
            start_date, end_date = tool.get_query_date(query_date)
            sites = self.sites

            total_pv = 0
            total_uv = 0
            total_ip = 0
            total_req = 0
            total_length = 0
            total_spider = 0
            total_50x = 0
            total_40x = 0
            total_realtime_req = 0
            total_realtime_traffic = 0
            exception_sites = []
            for site_info in sites:
                try:
                    ori_site = site_info["name"]
                    # 根据传入的网站名称检查实际网站名
                    site = self.get_siteName(ori_site)
                    # 获取指定站点概览统计数据
                    site_overview_info = self.get_site_overview_sum_data(
                        site, start_date, end_date)
                    data = {
                        "name": ori_site, "pv": 0, "uv": 0, "ip": 0, "req": 0,
                        "length": 0, "spider": 0, "fake_spider": 0, "s50x": 0, "s40x": 0
                    }
                    data.update(site_overview_info)
                    # 获取实时请求数
                    realtime_req_list = self.get_realtime_request(site)
                    if len(realtime_req_list) > 0:
                        data["realtime_req"] = realtime_req_list[0]["req"]
                    else:
                        data["realtime_req"] = 0

                    # 获取实时流量
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
                    total_spider += data["spider"]
                    total_50x += data["s50x"]
                    total_40x += data["s40x"]

                    total_realtime_req += data["realtime_req"]
                    total_realtime_traffic += data["realtime_traffic"]
                    # 获取指定网站的监控报表开启状态
                    data["status"] = self.get_monitor_status(site)
                    list_data.append(data)
                except Exception as e:
                    msg = str(e)
                    if msg.find("object does not support item assignment") != -1:
                        msg = "数据文件/www/server/total/logs/{}/logs.db已损坏。".format(site)
                    exception_sites.append({"site": ori_site, "err": msg})

            def sort_key(d):
                return d[orderby]

            # 对list里面的每一个元素进行排序,desc为True则降序,否则忽略
            list_data.sort(key=sort_key, reverse=desc)

            res_data = {
                "sum_data": {
                    "pv": total_pv,
                    "uv": total_uv,
                    "ip": total_ip,
                    "req": total_req,
                    "length": total_length,
                    "spider": total_spider,
                    "s50x": total_50x,
                    "s40x": total_40x,
                    "realtime_req": total_realtime_req,
                    "realtime_traffic": total_realtime_traffic
                },
                "list_data": list_data,
                "orderby": orderby,
                "exception_sites": exception_sites,
                "desc": desc
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

    def get_settings_info(self, get):
        '''
        获取配置信息,适用插件前端调用
        @param get:
        @return:
        '''
        site = self.get_siteName(get.site) if "site" in get else None
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
        '''
        修改配置文件
        @param get:
        @return:
        '''
        site = None
        if "site" in get:
            site = self.get_siteName(get.site.strip())
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
            new_config[
                "statistics_machine_access"] = True if get.statistics_machine_access.lower() == "true" else False

        if "statistics_uri" in get:
            new_config["statistics_uri"] = True if get.statistics_uri.lower() == "true" else False

        if "statistics_ip" in get:
            new_config["statistics_ip"] = True if get.statistics_ip.lower() == "true" else False

        if "record_post_args" in get:
            new_config[
                "record_post_args"] = True if get.record_post_args.lower() == "true" else False

        if "record_get_403_args" in get:
            new_config[
                "record_get_403_args"] = True if get.record_get_403_args.lower() == "true" else False

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
        config_data = self.get_file_json(config_path)

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

                        reload_exclude_url_file = os.path.join(self.get_data_dir(), target_site,
                                                               "reload_exclude_ip.pl")
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
                    if "exclude_ip" in config_data["global"].keys():
                        config_data["global"]["old_exclude_ip"] = config_data["global"][
                            "exclude_ip"]
                    # 调整：仅标记全局排除规则变化
                    reload_exclude_url_file = os.path.join(self.get_data_dir(),
                                                           "reload_exclude_ip.pl")
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
                    reload_exclude_url_file = os.path.join(self.get_data_dir(), xsite,
                                                           "reload_exclude_ip.pl")
                else:
                    reload_exclude_url_file = os.path.join(self.get_data_dir(),
                                                           "reload_exclude_ip.pl")
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

    def sync_settings(self, get):
        '''
        同步站点配置
        @param get:
        @return:
        '''
        profile = None
        if "profile" in get:
            profile = self.get_siteName(get.profile.strip())
        tosites = None
        if "tosites" in get:
            tosites = get.tosites.strip()
        targets = []
        if tosites != "all":
            if tosites.find(",") < 0:
                targets.append(self.get_siteName(tosites))
            else:
                targets = [self.get_siteName(x) for x in tosites.split(",") if x.strip()]
        else:
            tosites = self.sites
            targets = [self.get_siteName(x["name"]) for x in tosites]

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
            new_config[
                "statistics_machine_access"] = True if get.statistics_machine_access.lower() == "true" else False

        if "record_post_args" in get:
            new_config[
                "record_post_args"] = True if get.record_post_args.lower() == "true" else False

        if "record_get_403_args" in get:
            new_config[
                "record_get_403_args"] = True if get.record_get_403_args.lower() == "true" else False

        save_day = 180
        if "save_day" in get:
            save_day = int(get.save_day)
            new_config["save_day"] = save_day

        if "compress_day" in get:
            new_config["compress_day"] = int(get.compress_day)

        config_path = "/www/server/total/config.json"
        config_data = self.get_file_json(config_path)
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
                reload_exclude_url_file = os.path.join(self.get_data_dir(), profile,
                                                       "reload_exclude_ip.pl")
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
                        reload_exclude_url_file = os.path.join(self.get_data_dir(), target_site,
                                                               "reload_exclude_ip.pl")
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
                reload_exclude_url_file = os.path.join(self.get_data_dir(), xsite,
                                                       "reload_exclude_ip.pl")
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

    def get_report_list(self, get):
        '''
        获取报表列表
        @param get:
        @return:
        '''
        if not self.sites:
            return {
                "status": False,
                "msg": tool.getMsg("PLEASE_CREATE_SITE")
            }
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
            report_db = os.path.join(self.frontend_path, "report.db")
            report_conn = sqlite3.connect(report_db)
            report_cur = report_conn.cursor()
            sql = "select report_id, sequence, report_cycle, report_type, generate_time, file_name, file_size from report where site='{}' and year='{}'".format(
                site, year)
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
                file_name = os.path.join(self.frontend_path, "reports", site, report[5])
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
        '''
        下载PDF格式报告
        @param get:
        @return:
        '''
        try:
            report_conn = None
            report_cur = None
            report_id = get.report_id

            import sqlite3
            report_db = os.path.join(self.frontend_path, "report.db")
            report_conn = sqlite3.connect(report_db)
            report_cur = report_conn.cursor()
            reportor = report_cur.execute(
                "select file_name from report where report_id={}".format(report_id))
            report = reportor.fetchone()
            if not report:
                return tool.returnMsg(False, "REPORT_NOT_EXISTS")
            report_file_name = report[0]

            pdf_path = os.path.join(self.frontend_path, "pdfs")
            file_name = os.path.join(pdf_path, report_file_name + ".pdf")
            if not os.path.isfile(file_name):
                if not file_name.endswith(".html"):
                    file_name = os.path.join(self.frontend_path, "reports",
                                             report_file_name + ".html")
                else:
                    file_name = os.path.join(self.frontend_path, "reports", report_file_name)
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
        '''
        预览报告
        @param get:
        @return:
        '''
        try:
            report_conn = None
            report_cur = None
            report_id = get.report_id
            site = self.get_siteName(get.site)
            # preview_type = "html"
            import sqlite3
            report_db = os.path.join(self.frontend_path, "report.db")
            report_conn = sqlite3.connect(report_db)
            report_cur = report_conn.cursor()
            reportor = report_cur.execute(
                "select file_name from report where report_id={}".format(report_id))
            report = reportor.fetchone()
            if not report:
                return tool.returnMsg(False, "REPORT_NOT_EXISTS")
            report_file_name = report[0]

            file_name = os.path.join(self.frontend_path, "reports", site,
                                     report_file_name + ".html")
            public.writeFile(os.path.join(self.frontend_path, "templates", "preview_report.html"),
                             public.readFile(file_name))

            if not os.path.isfile(file_name):
                return tool.returnMsg(False, "REPORT_NOT_EXISTS")
            return {
                "status": True,
                "data": file_name
            }
        except Exception as e:
            public.writeFile(
                os.path.join(self.frontend_path, "templates", "preview_report.html"),
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
        '''
        擦除ip统计数据
        @param get:
        @return:
        '''
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

            site = self.get_siteName(get.site)
            import sqlite3
            conn = sqlite3.connect(self.get_log_db_path(site, db_name=self.total_db_name))
            cur = conn.cursor()
            table_name = "ip_stat"
            selector = cur.execute("PRAGMA table_info([{}])".format(table_name))
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
        '''
        擦除URI统计数据
        @param get:
        @return:
        '''
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

            site = self.get_siteName(get.site)
            import sqlite3
            conn = sqlite3.connect(self.get_log_db_path(site, db_name=self.total_db_name))
            cur = conn.cursor()
            table_name = "uri_stat"
            selector = cur.execute("PRAGMA table_info([{}])".format(table_name))
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
        '''
        根据网站日志搜索结果导出日志数据
        @param get:
        @return:
        '''
        try:
            site = get.site
            allow_fields = ["time", "ip", "client_port", "method", "domain", "status_code",
                            "protocol", "uri", "user_agent", "body_length", "referer",
                            "request_time", "is_spider", "request_headers", "ip_list"]
            headers = ["时间", "真实IP", "客户端端口", "类型", "域名", "状态", "协议", "URL",
                       "User Agent", "响应大小(字节)", "来路", "耗时(毫秒)", "蜘蛛类型", "请求头",
                       "完整IP列表"]
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
                indexes = [allow_fields.index(f) for f in fields.split(",") if
                           f and f.strip() in allow_fields]
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

            if fields.find(",") < 0:
                fields = "distinct " + fields
            # print("fields:")
            # print(fields)

            get.fields = fields
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

            output_dir = os.path.join(self.frontend_path, "output")
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
            while page <= total_page:
                get.page = page
                get.page_size = page_size
                get.no_total_rows = "true"
                if not export_error:
                    logs = self.get_site_logs(get)
                else:
                    logs = self.get_site_error_logs(get)
                list_data = logs["list_data"]
                for log in list_data:
                    log_line = ""
                    # print("log keys:"+str(log.keys()))
                    df = [_key.replace("distinct ", "") for _key in log.keys()]
                    # print("df:"+str(df))
                    for data_field in allow_fields:
                        k = data_field
                        v = ""
                        if k in df:
                            if k in log.keys():
                                v = log[k]
                            else:
                                v = log["distinct " + k]
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

    def get_ip_info(self, get):
        '''
        获取ip相关信息
        @param get:
        @return:
        '''
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

    def change_history_data_dir(self, get):
        '''
        更改历史日志数据的存储目录，释放/www/目录下的存储空间
        @param get:
        @return:
        '''
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

        sites = self.sites
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
            return public.returnMsg(True,
                                    "数据目录更换成功，但部分文件拷贝可能失败，详情请看面板日志。")
        return public.returnMsg(True, "历史数据目录切换成功。")

    def get_referer_stat(self, get):
        '''
        获取站点来源统计排行
        @param get:
        @return:
        '''
        if not self.sites:
            return {
                "status": False,
                "msg": tool.getMsg("PLEASE_CREATE_SITE")
            }
        try:
            ts = None
            site = "all"
            if "site" in get:
                site = self.get_siteName(get.site)
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

            # self.flush_data("127.0.0.1", site)
            if site == "all":
                sites = self.sites
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
                        self.flush_data("127.0.0.1", site_name)

                    time_start, time_end = tool.get_query_date(query_date)
                    total_sql = "select sum(req), sum(length) from request_stat where time>={} and time <={}".format(
                        time_start, time_end)
                    total_result = ts.query(total_sql)

                    total_req = 0
                    total_flow = 0
                    if len(total_result) > 0 and type(total_result[0]) != str:
                        total_req = total_result[0][0] or 0
                        total_flow = total_result[0][1] or 0

                    select_sql = "select referer, ({}) as referer_count, ({}) as referer_flow from referer2_stat where referer_count > 0 order by referer_count desc limit {};".format(
                        fields, flow_fields, top)
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
                    print(tool.getMsg("REQUEST_SITE_INTERFACE_ERROR",
                                      (site_name, "get_referer_stat", str(e))))
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

    def find_ip_for_spiders(self, ip, cls_name=None):
        '''
        从IP蜘蛛库中查找IP
        @param ip:
        @param cls_name:
        @return:
        '''
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
            user_info = json.loads(
                public.ReadFile("{}/data/userInfo.json".format(public.get_panel_path())))
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
        if not self.sites:
            return {
                "status": False,
                "msg": tool.getMsg("PLEASE_CREATE_SITE")
            }
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
        user_info = json.loads(
            public.ReadFile("{}/data/userInfo.json".format(public.get_panel_path())))
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

## uri独立统计
    def add_uri_alone_stat(self, get):
        '''
        添加指定uri独立统计
        @param get:
            site: site_name,string
            uri: uri,string
        @return:
        '''
        self.set_module_total('add_uri_alone_stat')
        site = self.get_siteName(get.site) if "site" in get else None
        if not site: return public.returnMsg(False, "请选择站点")
        uri = get.uri if "uri" in get else ""
        if not uri: return public.returnMsg(False, "请输入或选择需要统计的uri")
        if not uri.startswith("/"): return public.returnMsg(False, "请以/开头，例：/bbs/thread-1.html")

        ts = self.init_ts(site, self.total_db_name)
        if not ts: return public.returnMsg(False, "数据库连接失败,请尝试重新添加URI!")

        have_uri = ts.table("uri_access").where("uri=?", (uri,)).find()
        if have_uri: return public.returnMsg(False, "URI已存在,请勿重复添加!")

        param = (uri, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        ts.table("uri_access").add("uri,date", param)

        have_uri = ts.table("uri_access").where("uri=?", (uri,)).find()
        ts.close()
        if have_uri:
            return public.returnMsg(True, "添加成功")
        return public.returnMsg(False, "添加失败,请尝试重新添加URI!")

    def del_uri_alone_stat(self, get):
        '''
        删除指定uri独立统计
        @param get:
            site: site_name,string
            uri: uri,string
        @return:
        '''
        site = self.get_siteName(get.site) if "site" in get else None
        if not site: return public.returnMsg(False, "请选择站点。")
        uri = get.uri if "uri" in get else None

        ts = self.init_ts(site, self.total_db_name)
        if not ts: return public.returnMsg(False, "数据库连接失败!")

        have_uri = ts.table("uri_access").where("uri=?", (uri,)).find()
        if have_uri:
            # 构造查询表名
            start_date, end_date = self.construct_query_date("l120")
            table_type_tup = ("uri_count_stat", "uri_client_stat", "uri_spider_stat", "uri_flow_stat", "uri_ip_stat")
            table_names_dict = self.construct_table_names(start_date, end_date, table_type_tup)
            with contextlib.suppress(Exception):
                ts.table("uri_access").delete(have_uri["id"])

            # 删除所有表中指定uri的数据
            for table_type in table_type_tup:
                if table_type not in table_names_dict.keys(): continue
                for table_name in table_names_dict[table_type]:
                    with contextlib.suppress(Exception):
                        ts.query("DELETE FROM {} WHERE uri_id=?".format(table_name), (have_uri["id"],))
            ts.close()
            return public.returnMsg(True, "删除成功")

        ts.close()
        return public.returnMsg(False, "删除失败,uri不存在或已删除")

    def construct_table_names(self, start_date, end_date, table_type_tup):
        '''
        构造表名
        @param start_date:
        @param end_date:
        @param table_type_tup:
        @return: {'uri_count_stat': ['uri_count_stat_202306'],...}
        '''
        tables = {}
        for table_type in table_type_tup:
            current_date = start_date
            construct_table_names = []
            while current_date <= end_date:
                table_name = table_type + '_' + current_date.strftime('%Y%m')
                if table_name not in construct_table_names: construct_table_names.append(table_name)
                current_date += datetime.timedelta(days=1)
            if construct_table_names: tables[table_type] = construct_table_names
        return tables

    def construct_query_date(self, query_date):
        '''
        构造查询时间
        @param query_date:
        @return: start_date:2023-06-26 end_date:2023-06-26
        '''
        today = datetime.date.today()
        date_ranges = {
            'h1': (today - datetime.timedelta(hours=1), today),
            'today': (today, today),
            'yesterday': (today - datetime.timedelta(days=1), today - datetime.timedelta(days=1)),
            'l7': (today - datetime.timedelta(days=7), today),
            'l30': (today - datetime.timedelta(days=30), today),
            'l120': (today - datetime.timedelta(days=120), today),
            'l180': (today - datetime.timedelta(days=180), today)
        }
        start_date, end_date = date_ranges.get(query_date, (None, None))
        return start_date, end_date

    def get_uri_sql_feilds(self, query_date, type):
        '''
        获取uri_stat表中的字段
        @param query_date:
        @type type:
        @return:
        '''
        if query_date == "h1":
            last_hour = "{:02d}".format(time.localtime().tm_hour - 1)
            now_hour = "{:02d}".format(time.localtime().tm_hour)
            ts_field = "SUM(h{} + h{}) AS total_count, {}".format(last_hour, now_hour, type)
        else:
            ts_field = '''SUM(h00 + h01 + h02 + h03 + h04 + h05 + h06 + h07 + h08 + h09 + h10 + h11 + h12 + h13 +
             h14 + h15 + h16 + h17 + h18 + h19 + h20 + h21 + h22 + h23) AS total_count, {}'''.format(type)
        return ts_field

    def get_uri_query_sql(self, tmp_table_names, get_sql_dict, field, type):
        '''
        获取uri查询sql
        @param tmp_table_names:
        @param get_sql_dict:
        @return:
        '''
        if len(tmp_table_names) > 1:
            query_sql = ""
            for index in range(len(tmp_table_names)):
                query_sql += "SELECT {} FROM {} WHERE uri_id={} AND date BETWEEN {} AND {} GROUP BY {}" \
                    .format(field, tmp_table_names[index], get_sql_dict["uri_result_id"],
                            get_sql_dict["start_date"], get_sql_dict["end_date"], type)
                query_sql += " UNION ALL " if index < len(tmp_table_names) - 1 else ""
            query_sql = "SELECT SUM(total_count), count_type FROM ({}) AS tmp GROUP BY count_type".format(query_sql)
        else:
            query_sql = "SELECT {} FROM {} WHERE uri_id={} AND date BETWEEN {} AND {} GROUP BY {}" \
                .format(field, tmp_table_names[0], get_sql_dict["uri_result_id"],
                        get_sql_dict["start_date"], get_sql_dict["end_date"], type)
        return query_sql

    def get_uri_alone_stat(self, get):
        '''
        获取指定网站所有uri独立统计列表
        @param get:
            site: site_name,string
            query_date: h1|today|yesterday|l7|l30,string
        @return:
        '''
        self.set_module_total('get_uri_alone_stat')
        site = self.get_siteName(get.site) if "site" in get else None
        if not site: return public.returnMsg(False, "请选择站点。")
        query_date = get.query_date if "query_date" in get else None

        ts = self.init_ts(site, self.total_db_name)
        if not ts: return public.returnMsg(False, "数据库连接失败,请尝试重新添加URI!")

        # 构造表名日期
        data = {"query_date": query_date, "data": []}

        access_result = ts.table("uri_access").field("id,uri,date").select()

        uri_client_stat_sort = {
            "count": ("android", "iphone", "mac", "windows", "linux"),
            "client": ("weixin", "edge", "firefox", "msie", "metasr", "tt", "maxthon", "theworld", "qh360",
                       "chrome", "safari", "opera", "qq", "uc", "pc2345", "machine", "other")
        }

        # 构造查询字段
        count_type_dict = {
            "uri_count_stat": ("pv", "uv", "ip", "spider"),
            "uri_client_stat": ("weixin", "android", "iphone", "mac", "windows", "linux", "edge", "firefox", "msie",
                                "metasr", "tt", "maxthon", "theworld", "qh360", "chrome", "safari", "opera", "qq",
                                "uc", "pc2345", "machine", "other"),
            "uri_spider_stat": ("bytes", "bing", "soso", "yahoo", "sogou", "google", "baidu", "qh360", "youdao",
                                "yandex", "dnspod", "yisou", "mpcrawler", "duckduckgo", "other"),
            "uri_flow_stat": ("flow", "spider_flow", "bytes_flow", "bing_flow", "soso_flow", "yahoo_flow",
                              "sogou_flow", "google_flow", "baidu_flow", "qh360_flow", "youdao_flow", "yandex_flow",
                              "dnspod_flow", "yisou_flow", "other_flow", "mpcrawler_flow", "duckduckgo_flow")
        }

        # 查询拼接返回的数据
        table_names = [row[0] for row in ts.query("SELECT name FROM sqlite_master WHERE type='table'")] or []

        # 构造表内查询日期
        start_date, end_date = self.construct_query_date(query_date)
        table_type_tup = ("uri_count_stat", "uri_client_stat", "uri_spider_stat", "uri_flow_stat")
        table_names_dict = self.construct_table_names(start_date, end_date, table_type_tup)
        ip_table_names_dict = self.construct_table_names(start_date, end_date, ("uri_ip_stat",))
        start_date = start_date.strftime('%Y%m%d')
        end_date = end_date.strftime('%Y%m%d')

        # 构造查询表名
        type_tup = ("count_type", "ip")
        ts_field = self.get_uri_sql_feilds(query_date, type_tup[0])
        ip_field = self.get_uri_sql_feilds(query_date, type_tup[1])
        get_sql_dict = {"start_date": start_date, "end_date": end_date}

        # 查询拼接需要返回的数据
        try:
            for i, uri_result in enumerate(access_result):
                uri_count_dict = {}
                get_sql_dict["uri_result_id"] = uri_result["id"]
                for table_type in table_type_tup:
                    tmp_count_dict = {}
                    if table_type not in table_names_dict.keys(): continue
                    # 解决如果连表查询某个表不存在而导致查询报错的问题
                    tmp_table_names = [value for value in table_names_dict[table_type] if value in table_names]
                    if not tmp_table_names:
                        uri_count_dict[table_type] = self.empty_dict()[table_type]
                        continue

                    # 按照count_type分组查询数据
                    query_sql = self.get_uri_query_sql(tmp_table_names, get_sql_dict, ts_field, type_tup[0])
                    count_result = ts.query(query_sql)

                    if len(count_result) == 0:
                        uri_count_dict[table_type] = self.empty_dict()[table_type]
                        continue

                    if table_type == "uri_client_stat": tmp_count_dict = {"count": {}, "client": {}}

                    # 整合client的结果
                    for re in count_result:
                        if table_type == "uri_client_stat":
                            if re[1] in uri_client_stat_sort["count"]: tmp_count_dict["count"][re[1]] = re[0]
                            if re[1] in uri_client_stat_sort["client"]: tmp_count_dict["client"][re[1]] = re[0]
                            continue
                        tmp_count_dict[re[1]] = re[0]

                    # 当有一些表中某种统计类型没有数据时，需要补充0
                    for value in count_type_dict[table_type]:
                        if table_type == "uri_client_stat":
                            for sort in uri_client_stat_sort["count"]:
                                if sort not in tmp_count_dict["count"]: tmp_count_dict["count"][sort] = 0
                            for sort in uri_client_stat_sort["client"]:
                                if sort not in tmp_count_dict["client"]: tmp_count_dict["client"][sort] = 0
                            continue
                        if value not in tmp_count_dict.keys():
                            tmp_count_dict[value] = 0

                    # 将总流量拼接到uri_count_stat中
                    if "flow" in tmp_count_dict.keys():
                        uri_count_dict["uri_count_stat"]["flow"] = tmp_count_dict["flow"]
                        tmp_count_dict.pop("flow")
                    if "spider_flow" in tmp_count_dict.keys():
                        uri_count_dict["uri_count_stat"]["spider_flow"] = tmp_count_dict["spider_flow"]
                        tmp_count_dict.pop("spider_flow")

                    uri_count_dict[table_type] = tmp_count_dict

                uri_count_dict["uri_ip_stat"] = self.get_uri_ip_stat(ip_table_names_dict, table_names, get_sql_dict,
                                                                     ip_field, ts, type_tup[1])

                # 如果没有数据则跳过
                uri_count_dict["no"] = i + 1
                uri_count_dict["uri"] = uri_result["uri"]
                uri_count_dict["uri_id"] = uri_result["id"]
                uri_count_dict["add_time"] = uri_result["date"]
                data["data"].append(uri_count_dict)

        except Exception:
            data["data"] = []

        ts.close()
        # 计算总数
        data["data_count"] = len(data["data"])
        return data

    def get_uri_ip_stat(self, ip_table_names_dict, table_names, get_sql_dict, ip_field, ts, type):
        '''
        获取ip统计的数据
        @param type:
        @param ip_table_names_dict:
        @param table_names:
        @param get_sql_dict:
        @param ip_field:
        @param ts:
        @return:
        '''
        tmp_count_dict = {}
        tmp_table_names = [value for value in ip_table_names_dict["uri_ip_stat"] if value in table_names]
        if not tmp_table_names: return {}

        query_sql = self.get_uri_query_sql(tmp_table_names, get_sql_dict, ip_field, type)
        count_result = ts.query(query_sql)
        if len(count_result) == 0: return {}
        for re in count_result:
            tmp_count_dict[re[1]] = re[0]

        return tmp_count_dict

    def get_uri_all_list(self, get):
        '''
        获取当日已经记录的uri列表
        @param get: site: site_name,string
        @return: list ["/","/wzznb",...]
        '''
        site = self.get_siteName(get.site) if "site" in get else None
        if not site: return public.returnMsg(False, "请选择站点")
        query_date = get.query_date if "query_date" in get else "l7"
        top = int(get.top) if "top" in get else 5

        fields, flow_fields, spider_fields = self.get_data_fields(query_date)
        db_path = self.get_log_db_path(site, db_name=self.total_db_name)
        ts = tsqlite()
        ts.dbfile(db_path)
        if not ts: return public.returnMsg(False, "数据库连接失败,请尝试重新添加URI!")
        select_sql = "select uri, ({}) as uri_count from uri_stat where uri_count > 0 order by uri_count desc limit {};".format(
            fields, top)
        uri_result = ts.query(select_sql)
        ts.close()

        if not uri_result: return []
        return [row[0] for row in uri_result]
