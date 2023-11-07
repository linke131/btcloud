# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyleft (c) 2015-2099 宝塔软件(http://bt.cn) All lefts reserved.
# +-------------------------------------------------------------------
# | Author: linxiao
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   宝塔网站监控报表报告
# +-------------------------------------------------------------------
from __future__ import absolute_import, print_function, division

import enum
import os
import sys
import time
from jinja2 import Environment, FileSystemLoader
import sqlite3
import json

try:
    from urllib.parse import urlparse
except:
    from urlparse import urlparse

os.chdir("/www/server/panel")
sys.path.insert(0, "/www/server/panel")
sys.path.insert(0, "/www/server/panel/class/")

import public
import total_tools as tool

plugin_dir = "/www/server/panel/plugin/total"
report_db_path = os.path.join(plugin_dir, "report.db")
TOTAL_DB_NAME = "total.db"
REPORT_TOP_NUM = 50


def init_db():
    import sqlite3
    try:
        conn = None
        cur = None
        conn = sqlite3.connect(report_db_path)
        cur = conn.cursor()

        results = cur.execute("SELECT name FROM sqlite_master where type='table'").fetchall()
        tables = [r[0] for r in results]
        if "report" in tables:
            return True

        """
        send_log 表说明:
        推送记录
        @report_id 报表ID
        @send_time 推送时间
        @send_status 推送状态
        """
        cur.execute("""
        CREATE TABLE send_log(
            report_id INTEGER,
            send_time timestamp default CURRENT_TIMESTAMP,
            receiver TEXT DEFAULT "",
            send_status INTEGER,
            remark TEXT DEFAULT ""
        )
        """)
        """
        parse_log 表说明：
        提取日志记录，防止重复读取日志
        """
        cur.execute("""
        create table parse_log(
            site text,
            log_time integer,
            parse_time timestamp default CURRENT_TIMESTAMP
        )
        """)
        """
        report 表说明：
        报表生成记录
        @site 站点名
        @year 年度
        @sequence 顺序号，周报是第几周，月份是哪个月
        @report_type 报表类型
        @report_cycle 报告时间周期
        @file_name 本地文件名
        @file_size 文件大小
        @generate_time 生成时间
        """
        cur.execute("""
        create table report(
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            site text,
            year INTEGER,
            sequence INTEGER,
            report_type CHAR(10),
            report_cycle TEXT,
            file_name TEXT,
            file_size INTEGER,
            generate_time timestamp default CURRENT_TIMESTAMP
        )
        """)
        """send_list 表说明
        记录将要推送的报告ID
        @report_id 报告ID
        @add_time 时间
        """
        cur.execute("""
        create table send_list(
            report_id INTEGER PRIMARY KEY,
            add_time timestamp default CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
    except Exception as e:
        print(tool.getMsg("TIPS_INIT_REPORT_DB_ERROR", args=(str(e),)))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_overview_data(site, query_date):
    """获取报告概览数据
    
    :site 站点
    :cycle 报告时间周期
    
    概览包括总访问量、PV、UV等数据，经过格式化处理后在报表显示。
    """
    # 当下周期
    start_date, end_date = tool.get_query_date(query_date)
    cycle_data = tool.request_plugin("get_site_overview_sum_data", (site, start_date, end_date,))
    report_data = {}
    if not cycle_data:
        return report_data

    for k, v in cycle_data.items():
        if not v: v = 0
        if k == "length":
            format_val = public.to_size(v)
        else:
            format_val = "{:,}".format(v)
        report_data[k] = {
            "count": v,
            "f_count": format_val
        }
    report_data["error"] = {
        "count": cycle_data["s40x"] + cycle_data["s50x"],
        "f_count": "{:,}".format(cycle_data["s40x"] + cycle_data["s50x"])
    }
    # report_data.update(cycle_data)
    # cycle_data["log_size"] = 0
    # cycle_data["new_uv"] = 0
    return report_data


def get_ip_data(site, query_date):
    get = public.dict_obj()
    get.site = site
    get.query_date = query_date
    get.top = REPORT_TOP_NUM
    select_data = tool.request_plugin("get_ip_stat", (get,), {"flush": False})
    data = select_data["data"]
    ip_data = []
    for data_line in data:
        count = data_line["count"]
        if count > 0:
            data_line["f_count"] = format_count(count)
        flow = data_line["flow"]
        # print("flow: {}, res:{}".format(flow, public.to_size(flow)))
        if flow > 0:
            data_line["f_flow"] = format_flow(flow)
        ip_data.append(data_line)
    # print("ip data:")
    # print(ip_data)
    return ip_data


def get_uri_data(site, query_date):
    """获取URI统计数据"""
    get = public.dict_obj()
    get.site = site
    get.query_date = query_date
    get.top = REPORT_TOP_NUM
    select_data = tool.request_plugin("get_uri_stat", (get,), {"flush": False})
    data = select_data["data"]
    uri_data = []
    for data_line in data:
        count = data_line["count"]
        if count > 0:
            data_line["count"] = "{:,}".format(count)
        flow = data_line["flow"]
        if flow > 0:
            data_line["flow"] = public.to_size(flow)
        uri_data.append(data_line)
    return uri_data


def get_area_data(site, query_date):
    """获取地区统计数据"""
    try:
        get = public.dict_obj()
        get.site = site
        get.query_date = query_date
        get.top = REPORT_TOP_NUM
        tool.request_plugin("generate_area_stat", (site, query_date,))
        select_data = tool.request_plugin("get_area_stat", (get,), {"flush": False, "format_count": True})
        area_data = select_data["data"][site]
        return area_data
    except:
        return []


def get_client_data(site, query_date):
    """获取客户端统计数据"""
    try:
        ts = None
        start_date, end_date = tool.get_query_date(query_date)

        ts = tool.request_plugin("init_ts", (site, TOTAL_DB_NAME))
        table_name = "client_stat"
        columns = ts.query("PRAGMA table_info([{}])".format(table_name))
        sum_fields = ""
        clients_json = "/www/server/total/config/clients.json"
        config_data = json.loads(public.readFile(clients_json))
        pc_client_name = [c["column"] for c in config_data["pc"]]
        # pc_client_name = ["firefox", "msie", "qh360", "theworld", "tt", "maxthon", "opera", "qq", "uc", "safari", "chrome", "metasr", "pc2345", "edeg"]
        pc_fields = ""
        # 动态生成数据列
        for column in columns:
            client_name = column[1]
            if client_name == "time": continue
            if sum_fields:
                sum_fields += ","
            sum_fields += "sum(" + client_name + ") as " + client_name

            if client_name in pc_client_name:
                if pc_fields:
                    pc_fields += "+"
                pc_fields += "sum(" + client_name + ")"

        sum_fields += ",(" + pc_fields + ") as pc"
        ts.table("client_stat").field(sum_fields)
        ts.where("time>=? and time<=?", (start_date, end_date,))
        total_data = ts.select()
        # print("total data:"+str(total_data))
        if type(total_data) == list and len(total_data) > 0:
            client_data = total_data[0]
            client_title = {
                "weixin": "微信",
                "android": "安卓",
                "iphone": "iPhone",
                "mac": "Macintosh苹果操作系统",
                "windows": "Windows操作系统",
                "linux": "Linux操作系统",
                "edeg": "Edge浏览器",
                "firefox": "火狐浏览器",
                "msie": "IE浏览器",
                "metasr": "搜狗浏览器",
                "qh360": "360浏览器",
                "theworld": "世界之窗浏览器",
                "qq": "QQ浏览器",
                "uc": "UC浏览器",
                "pc2345": "2345浏览器",
                "safari": "Safari浏览器",
                "chrome": "Google Chrome浏览器",
                "other": "其他",
                "machine": "机器访问",
                "mobile": "移动端"
            }

            other_clients = ["theworld", "tt", "maxthon", "opera", "uc", "pc2345", "other"]
            res_data = {}
            other = 0
            for k, v in client_data.items():
                title = k
                if not v: v = 0
                if k in client_title.keys():
                    title = client_title[k]
                if k in other_clients:
                    other = other + v
                else:
                    res_data[k] = {
                        "f_count": format_count(v),
                        "title": title,
                        "count": v
                    }

            pc = res_data["pc"]["count"]
            mobile = res_data["mobile"]["count"]
            pc_ratio = 0
            mobile_ratio = 0
            _vs = 0
            if pc > 0 and mobile > 0:
                _vs = mobile / pc
                if _vs < 1:
                    pc_ratio = int(1 / _vs)
                    mobile_ratio = 1
                else:
                    pc_ratio = 1
                    mobile_ratio = int(_vs)
            else:
                if pc == 0:
                    mobile_ratio = mobile
                if mobile == 0:
                    pc_ratio = pc

            res_data["mobilevspc"] = "{}:{}".format(mobile_ratio, pc_ratio)
            # print("占比:{}:{}/PC:{}/Mobile:{}".format(mobile_ratio, pc_ratio, pc, mobile))
            # res_data["other"] = {
            # 	"count": "{:,}".format(other),
            # 	"title": "其他"
            # }
            return res_data
    except Exception as e:
        # print("获取客户端统计数据出现错误:"+str(e))
        print(tool.getMsg("TIPS_REPORT_GET_CLIENT_ERROR", args=(str(e),)))
    finally:
        if ts:
            ts.close()


def get_spider_data(site, query_date):
    """获取蜘蛛统计数据"""
    try:
        ts = None
        start_date, end_date = tool.get_query_date(query_date)

        ts = tool.request_plugin("init_ts", (site, TOTAL_DB_NAME))
        table_name = "spider_stat"
        columns = ts.query("PRAGMA table_info([{}])".format(table_name))
        sum_fields = ""
        flow_fields = ""

        # 动态生成数据列
        for column in columns:
            client_name = column[1]
            if client_name == "time": continue
            if sum_fields:
                sum_fields += ","
            sum_fields += "sum(" + client_name + ") as " + client_name

            if flow_fields:
                flow_fields += ","
            flow_fields += "sum(" + client_name + "_flow) as " + client_name + "_flow"

        ts.table(table_name).field(sum_fields)
        ts.where("time>=? and time<=?", (start_date, end_date,))
        total_data = ts.select()
        res_data = {}
        if type(total_data) == list and len(total_data) > 0:
            client_data = total_data[0]
            for k, v in client_data.items():
                if not v: v = 0
                if k.find("_flow") > 0: continue
                title = k
                format_val = 0
                if v > 0:
                    format_val = "{:,}".format(v)
                res_data[k] = {
                    "f_count": format_val,
                    "title": title,
                    "flow": client_data[k + "_flow"],
                    "f_flow": public.to_size(client_data[k + "_flow"]),
                    "count": v
                }
            # print("占比:{}:{}/PC:{}/Mobile:{}".format(mobile_ratio, pc_ratio, pc, mobile))
            # res_data["other"] = {
            # 	"count": "{:,}".format(other),
            # 	"title": "其他"
            # }
        return res_data
    except Exception as e:
        # print("获取蜘蛛统计数据出现错误:"+str(e))
        print(tool.getMsg("TIPS_REPORT_GET_SPIDER_ERROR", args=(str(e),)))
    finally:
        if ts:
            ts.close()


def get_referer_data(site, query_date):
    """获取来源统计数据"""
    get = public.dict_obj()
    get.site = site
    # query_date = "20221010-20221019"
    get.query_date = query_date
    get.top = REPORT_TOP_NUM
    get.format_count = True
    select_data = tool.request_plugin("get_referer_stat", (get,))
    referer_data = select_data["data"]
    return referer_data


def parse_logs_data_old(site, query_date, db_path, total_db_path=None):
    """分析日志，提取离线数据"""
    conn = None
    cur = None
    total_cur = None
    total_conn = None
    try:

        start_timestamp, end_timestamp = tool.get_query_timestamp(query_date)
        start_parse_date = time.localtime(start_timestamp)

        today = time.strftime("%Y%m%d", time.localtime())
        _end = time.localtime(end_timestamp)
        _end_time = time.localtime(time.mktime((_end.tm_year, _end.tm_mon, _end.tm_mday + 1, 0, 0, 0, 0, 0, 0)))
        end_gen = time.strftime("%Y%m%d", _end_time)
        # ts = tm.init_ts(site)
        import sqlite3
        conn = sqlite3.connect(db_path)
        total_conn = None
        if total_db_path is not None:
            total_conn = sqlite3.connect(total_db_path)

        if sys.version_info[0] == 3:
            conn.text_factory = lambda x: str(x, encoding="utf-8", errors='ignore')
        else:
            conn.text_factory = lambda x: unicode(x, "utf-8", "ignore")
        cur = conn.cursor()

        report_conn = sqlite3.connect(report_db_path)
        report_cur = report_conn.cursor()

        fields = "time, ip, domain, server_name, method, status_code, uri, body_length, referer, user_agent, protocol, request_time, is_spider"
        fields = "referer, is_spider, body_length"
        while True:
            time_key = time.strftime("%Y%m%d", start_parse_date)
            if time_key == end_gen or time_key == today:
                break
            log_res = report_cur.execute("select count(*) from parse_log where site=\"{}\" and log_time={}".format(site, time_key)).fetchone()
            if log_res[0] > 0: 
                # print("{} 已解析,跳过。".format(time.strftime("%Y-%m-%d", start_parse_date)))
                start_parse_date = time.localtime(time.mktime((start_parse_date.tm_year, start_parse_date.tm_mon, start_parse_date.tm_mday+1, 0, 0, 0, 0, 0, 0)))
                continue
            # if log_res[0]
            # print("开始解析 {} 的日志...".format(time.strftime("%Y-%m-%d", start_parse_date)))
            print(tool.getMsg("TIPS_REPORT_START_PARSE_LOGS", args=(time.strftime("%Y-%m-%d", start_parse_date))))
            total_referer = {}

            day_start, day_end = tool.get_timestamp_interval(start_parse_date)
            select_logs_sql = "select {} from site_logs where time>={} and time<={};".format(fields, day_start, day_end)
            selector = cur.execute(select_logs_sql)
            count = 1
            log_line = selector.fetchone()
            while log_line:
                # print("正在处理第{}行".format(count), end='\r')
                _referer = log_line[0]
                if _referer and _referer != "None":
                    ref_url = urlparse(_referer)
                    referer = ref_url.netloc
                    sep_index = referer.find(":")
                    if sep_index >= 0:
                        referer = referer[0:sep_index]
                    if referer not in total_referer.keys():
                        total_referer[referer] = 1
                    else:
                        total_referer[referer] = total_referer[referer] + 1

                is_spider = log_line[1]
                body_length = log_line[2]

                log_line = selector.fetchone()
                count += 1
                # if count>10:
                # 	break
            del selector
            del log_line
            print()
            # print("{}行日志数据处理完毕。".format(count))
            print(tool.getMsg("TIPS_REPORT_PARSED_LOGS", args=(count,)))

            total_cur = None
            if total_conn:
                total_cur = total_conn.cursor()
            else:
                total_cur = cur

            total_cur.execute("BEGIN TRANSACTION;")
            for domain, num in total_referer.items():
                insert_sql = "insert into referer_stat(time, domain, count) select {time}, \"{domain}\", 0 where not exists (select time,domain from referer_stat where time={time} and domain=\"{domain}\")"
                total_cur.execute(insert_sql.format(time=time_key, domain=domain))
                update_sql = "update referer_stat set count=count+{count} where time={time} and domain=\"{domain}\""
                total_cur.execute(update_sql.format(count=num, time=time_key, domain=domain))

            if total_conn:
                total_conn.commit()
            else:
                conn.commit()

            print("save parse log: {}".format(time_key))
            report_cur.execute("INSERT INTO parse_log(site, log_time, parse_time) VALUES('{}',{}, '{}')".format(
                site, time_key, time.time()
            ))
            report_conn.commit()

            if time_key == end_gen or time_key == today:
                break
            start_parse_date = time.localtime(time.mktime((start_parse_date.tm_year, start_parse_date.tm_mon, start_parse_date.tm_mday+1, 0, 0, 0, 0, 0, 0)))

        if report_cur:
            report_cur.close()
        if report_conn:
            report_conn.close()
    except Exception as e:
        print(tool.getMsg("TIPS_REPORT_PARSED_ERROR", args=(str(e),)))
    finally:
        if total_db_path is not None:
            total_cur and total_cur.close()
            total_conn and total_conn.close()
        if cur:
            cur.close()
        if conn:
            conn.close()


def parse_logs_data(site, query_date):
    if query_date.find("-") > 0:
        s, e = query_date.split("-")
        try:
            time.strptime(s, "%Y%m%d%H%M%S")
        except:
            s = s + "000000"
            e = e + "000000"
            query_date = s + "-" + e

    # print("parse query date:")
    # print(query_date)
    query_array = tool.split_query_date(query_date)
    for qdate in query_array:
        if qdate == "today":
            db_path = tool.get_log_db_path(site)
            total_db_path = None
        else:
            db_path = tool.get_log_db_path(site, history=True)
            total_db_path = tool.get_log_db_path(site)
        parse_logs_data_old(site, qdate, db_path, total_db_path=total_db_path)


def get_last_week(base_time=None):
    if base_time is None:
        base_time = time.localtime()
    now = base_time
    this_week = int(time.strftime("%W", now))
    last_week = this_week
    # print("This week:"+repr(this_week))
    this_year = now.tm_year
    _now = now
    while last_week == this_week:
        t1 = time.mktime((_now.tm_year, _now.tm_mon, _now.tm_mday - 1, 0, 0, 0, 0, 0, 0))
        t1 = time.localtime(t1)
        # print(t1.tm_year, this_year)
        # if t1.tm_year < this_year:
        #     t1 = _now
        #     break
        last_week = int(time.strftime("%W", t1))
        _now = t1
        # print(last_week)
    last_week_end = t1
    last_week_start = time.localtime(time.mktime((t1.tm_year, t1.tm_mon, t1.tm_mday - 7 + 1, 0, 0, 0, 0, 0, 0)))
    start_week = time.strftime("%W", last_week_start)
    end_week = time.strftime("%W", last_week_end)
    while start_week != end_week:
        last_week_start = time.localtime(time.mktime((last_week_start.tm_year, last_week_start.tm_mon, last_week_start.tm_mday+1, 0, 0, 0, 0, 0, 0)))
        start_week = time.strftime("%W", last_week_start)
    # print(time.strftime("%Y%m%d", last_week_start))
    # print(time.strftime("%Y%m%d", last_week_end))
    return last_week_start, last_week_end


def get_last_month(base_time=None):
    if base_time is None:
        base_time = time.localtime()
    now = base_time
    t1 = time.mktime((now.tm_year, now.tm_mon - 1, 1, 0, 0, 0, 0, 0, 0))
    start_day = time.localtime(t1)

    import calendar
    _, last_month_days = calendar.monthrange(start_day.tm_year, start_day.tm_mon)
    end_day = time.localtime(time.mktime((start_day.tm_year, start_day.tm_mon, last_month_days, 0, 0, 0, 0, 0, 0)))
    # print("Day Interval:{}-{}".format(time.strftime("%Y%m%d", start_day), time.strftime("%Y%m%d", end_day)))
    return start_day, end_day


def format_count(count):
    return "{:,}".format(count)


def format_flow(flow):
    return public.to_size(flow)


def get_diff_value(val1, val2, format=format_count):
    diff = val1 - val2
    tag = ""
    color = "black"
    if diff < 0:
        tag = "↓"
        color = "red"
        diff = format(abs(diff))
    elif diff > 0:
        tag = "↑"
        color = "green"
        diff = format(abs(diff))
    else:
        diff = ""

    return tag, diff, color


def generate_pdf_report(source_file):
    pdf_file_name = None
    try:
        pdf_path = os.path.join("/www/server/panel/plugin/total/", "pdfs")
        if not os.path.isdir(pdf_path):
            os.mkdir(pdf_path)
        pdf_file_name = os.path.join(pdf_path, os.path.splitext(os.path.split(source_file)[1])[0] + ".pdf")
        import pdfkit
        options = {
            "page-size": "A4",
            "encoding": "UTF-8",
            "quiet": ""
        }
        pdfkit.from_file(source_file, pdf_file_name, options=options)
        return pdf_file_name
    except Exception as e:
        # print("HTML转PDF发生错误:"+str(e))
        print(tool.getMsg("TIPS_REPORT_HTML2PDF_ERROR", args=(str(e),)))
        if pdf_file_name:
            if os.path.isfile(pdf_file_name):
                return pdf_file_name
    return None


def generate_week_report(site, cycle_start=None, cycle_end=None, force=False):
    try:
        report_conn = None
        report_cur = None
        init_db()
        env = Environment(loader=FileSystemLoader(os.path.join(plugin_dir, "templates")))
        reports_dir = os.path.join(plugin_dir, "reports")
        template = env.get_template("baogao.html")

        if not cycle_start or not cycle_end:
            cycle_start, cycle_end = get_last_week()
        cycle = time.strftime("%Y%m%d", cycle_start) + "-" + time.strftime("%Y%m%d", cycle_end)
        # print("cycle:"+cycle)

        report_path = os.path.join(reports_dir, site)
        if not os.path.exists(report_path):
            os.makedirs(report_path)

        report_conn = sqlite3.connect(report_db_path)
        report_cur = report_conn.cursor()
        if not force:
            reportor = report_cur.execute("select report_id, site, report_cycle, report_type, file_name, generate_time from report where site='{}' and report_cycle='{}'".format(site, cycle))
            for report in reportor.fetchall():
                report_id = report[0]
                report_file_name = report[4]
                file_name = os.path.join(report_path, report_file_name + ".html")
                if os.path.isfile(file_name):
                    print("报表已生成在：{}".format(file_name))
                    return {
                        "report_id": report_id,
                        "report_file_name": report_file_name
                    }

        # last_cycle_start = time.localtime(time.mktime((cycle_start.tm_year, cycle_start.tm_mon, cycle_start.tm_mday -7, 0,0,0,0,0,0)))
        # last_cycle_end = time.localtime(time.mktime((cycle_start.tm_year, cycle_start.tm_mon, cycle_start.tm_mday -1, 0,0,0,0,0,0)))
        last_cycle_start, last_cycle_end = get_last_week(base_time=cycle_start)
        last_cycle = time.strftime("%Y%m%d", last_cycle_start) + "-" + time.strftime("%Y%m%d", last_cycle_end)
        # print("last_cycle:"+last_cycle)

        report_type = tool.getMsg("REPORT_WEEK")
        last_cycle_title = tool.getMsg("REPORT_LAST_WEEK")
        sequence = int(time.strftime("%W", cycle_start))
        year = time.strftime("%Y", cycle_start)
        lang = public.GetLanguage()
        if lang.find("Chinese") >= 0:
            week_desc = "第{}周数据".format(sequence)
            report_title = "{year}年网站{site}{week}{type}".format(
                year=year, site=site, week=week_desc, type=report_type
            )
        else:
            week_desc = "Week {} weekly".format(sequence)
            report_title = "{year} Website {site} {week} {type}".format(
                year=year, site=site, week=week_desc, type=report_type
            )
        # 概览数据
        overview = get_overview_data(site, query_date=cycle)
        if overview["req"]["count"] == 0:
            # print("统计数据为空无须生成报告。")
            return None

        # print("正在生成站点: {} 数据周报...".format(site))
        print(tool.getMsg("REPORT_WEEK_GENERATING", args=(site,)))
        panel_config = {}
        alias = ""
        server_ip = public.GetLocalIp()
        try:
            panel_config = json.loads(public.readFile("/www/server/panel/config/config.json"))
            if "title" in panel_config.keys():
                alias = panel_config["title"]
        except:
            pass
        server_name = ""
        if alias and alias != server_ip:
            server_name = "{}({})".format(server_ip, alias)
        else:
            server_name = server_ip
        last_overview = get_overview_data(site, query_date=last_cycle)

        for k, v in overview.items():
            last_val = last_overview[k]
            format_func = format_count
            if k == "length":
                format_func = format_flow
            tag, diff, color = get_diff_value(v["count"], last_val["count"], format=format_func)
            overview[k].update({
                "diff_tag": tag,
                "diff": diff,
                "color": color
            })

        # IP 统计数据
        ip_data = get_ip_data(site, query_date=cycle)
        # URI 统计数据
        uri_data = get_uri_data(site, query_date=cycle)
        # 地区统计数据
        area_data = get_area_data(site, query_date=cycle)

        # 分析日志，提取数据
        # parse_logs_data(site, query_date=cycle)
        # parse_logs_data(site, query_date=last_cycle)

        referer_data = get_referer_data(site, query_date=cycle)
        # print("referer data:")
        # print(referer_data)

        client_data = get_client_data(site, query_date=cycle)
        last_client_data = get_client_data(site, query_date=last_cycle)

        if client_data:
            for k, v in client_data.items():
                last_val = last_client_data[k]
                if type(last_val) == str: continue
                tag, diff, color = get_diff_value(v["count"], last_val["count"])
                client_data[k].update({
                    "diff_tag": tag,
                    "diff": diff,
                    "color": color
                })
        else:
            client_data = {}

        spider_data = get_spider_data(site, query_date=cycle)
        last_spider_data = get_spider_data(site, query_date=last_cycle)

        if spider_data:
            for k, v in spider_data.items():
                last_value = last_spider_data[k]
                tag, diff, color = get_diff_value(v["count"], last_value["count"])
                spider_data[k].update({
                    "diff_tag": tag,
                    "diff": diff,
                    "color": color
                })
        else:
            spider_data = {}

        report_cycle = "{} - {}".format(time.strftime("%Y-%m-%d", cycle_start), time.strftime("%Y-%m-%d", cycle_end))
        report_file_name = report_title.replace(" ", "_")
        file_name = os.path.join(report_path, report_file_name + ".html")
        online_ip_library = tool.request_plugin("get_online_ip_library", args={})
        public.writeFile(file_name,
                         template.render(
                             server_name=server_name,
                             title=report_title,
                             site_name=site,
                             report_type=report_type,
                             last_cycle_title=last_cycle_title,
                             report_cycle=report_cycle,
                             generate_time=time.strftime("%Y-%m-%d %H:%M", time.localtime()),
                             overview=overview,
                             last_overview=last_overview,
                             ip_data=ip_data,
                             uri_data=uri_data,
                             area_data=area_data,
                             referer_data=referer_data,
                             client_data=client_data,
                             last_client_data=last_client_data,
                             spider_data=spider_data,
                             last_spider_data=last_spider_data,
                             online_ip_library=online_ip_library is not None
                         )
                         )

        pdf_file_name = generate_pdf_report(file_name)
        if not pdf_file_name:
            pdf_file_name = file_name
        # print("报告已生成到: {}".format(pdf_file_name))
        print(tool.getMsg("REPORT_WEEK_GENERATED", args=(pdf_file_name,)))
        record_selector = report_cur.execute("select report_id from report where site=? and year=? and report_type=? and sequence=? order by generate_time desc", (site, year, report_type,sequence,))
        records = record_selector.fetchall()
        if len(records) == 0:
            report_cur.execute("insert into report(site, year, report_type, sequence, report_cycle, file_name, file_size, generate_time) values('{}', {}, '{}', {}, '{}', '{}', {}, '{}')".format(
                site, year, report_type, sequence, cycle, report_file_name, public.get_path_size(pdf_file_name), time.time()
            ))
            report_id = report_cur.lastrowid
            report_conn.commit()
        else:
            report_id = records[0][0]
            # print("更新已存在报告ID: {}".format(report_id))
            report_cur.execute("update report set year=?,report_type=?,sequence=?,report_cycle=?,file_name=?,file_size=?,generate_time=? where report_id=?",
                (year, report_type, sequence, cycle, report_file_name, public.get_path_size(pdf_file_name), time.time(), report_id,))
            report_conn.commit()
        return {
            "report_id": report_id,
            "report_file_name": report_file_name
        }
    except Exception as e:
        # print("站点: {} 生成数据周报错误: {}。".format(site, str(e)))
        print(tool.getMsg("REPORT_WEEK_GENERATE_ERROR", args=(site, str(e),)))
    finally:
        if report_cur:
            report_cur.close()
        if report_conn:
            report_conn.close()


def generate_month_report(site, base_time=None, test=False, force=False):
    try:
        report_conn = None
        report_cur = None

        init_db()
        report_type = tool.getMsg("REPORT_MONTH")
        last_cycle_title = tool.getMsg("REPORT_LAST_MONTH")
        env = Environment(loader=FileSystemLoader(os.path.join(plugin_dir, "templates")))
        reports_dir = os.path.join(plugin_dir, "reports")
        template = env.get_template("baogao.html")

        report_path = os.path.join(reports_dir, site)
        if not os.path.exists(report_path):
            os.makedirs(report_path)
        cycle_start, cycle_end = get_last_month()
        cycle = time.strftime("%Y%m%d", cycle_start) + "-" + time.strftime("%Y%m%d", cycle_end)
        # print("Month cycle:"+cycle)

        report_conn = sqlite3.connect(report_db_path)
        report_cur = report_conn.cursor()
        if not force:
            reportor = report_cur.execute("select report_id, site, report_cycle, report_type, file_name, generate_time from report where site='{}' and report_cycle='{}'".format(site, cycle))
            for report in reportor.fetchall():
                file_name = os.path.join(report_path, report[4] + ".html")
                report_id = report[0]
                if os.path.isfile(file_name):
                    print("报表已生成在：{}".format(file_name))
                    return {
                        "report_id": report_id,
                        "report_file_name": report[4]
                    }

        last_cycle_start, last_cycle_end = get_last_month(cycle_start)
        last_cycle = time.strftime("%Y%m%d", last_cycle_start) + "-" + time.strftime("%Y%m%d", last_cycle_end)
        # print("Month last_cycle:"+last_cycle)

        sequence = int(time.strftime("%m", cycle_start))
        year = time.strftime("%Y", cycle_start)
        cn_num = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"]
        month_desc = "{}月份数据报告".format(cn_num[sequence - 1])
        report_file_name = "{year}年网站{site}{month_desc}".format(
            year=year, site=site, month_desc=month_desc
        )

        # 概览数据
        overview = get_overview_data(site, query_date=cycle)
        if overview["req"]["count"] == 0:
            # print("统计数据为空无须生成报告。")
            return None

        # print("正在生成站点: {} 数据月报...".format(site))
        print(tool.getMsg("REPORT_MONTH_GENERATING", args=(site,)))
        panel_config = {}
        alias = ""
        server_ip = public.GetLocalIp()
        try:
            panel_config = json.loads(public.readFile("/www/server/panel/config/config.json"))
            if "title" in panel_config.keys():
                alias = panel_config["title"]
        except:
            pass
        server_name = ""
        if alias and alias != server_ip:
            server_name = "{}({})".format(server_ip, alias)
        else:
            server_name = server_ip

        last_overview = get_overview_data(site, query_date=last_cycle)
        for k, v in overview.items():
            last_val = last_overview[k]
            format_func = format_count
            if k == "length":
                format_func = format_flow
            tag, diff, color = get_diff_value(v["count"], last_val["count"], format=format_func)
            overview[k].update({
                "diff_tag": tag,
                "diff": diff,
                "color": color
            })

        # IP 统计数据
        ip_data = get_ip_data(site, query_date=cycle)
        # URI 统计数据
        uri_data = get_uri_data(site, query_date=cycle)
        # 地区统计数据
        area_data = get_area_data(site, query_date=cycle)

        # 分析日志，提取数据
        # parse_logs_data(site, query_date=cycle)

        referer_data = get_referer_data(site, query_date=cycle)

        client_data = get_client_data(site, query_date=cycle)
        last_client_data = get_client_data(site, query_date=last_cycle)

        for k, v in client_data.items():
            last_val = last_client_data[k]
            if type(last_val) == str: continue
            tag, diff, color = get_diff_value(v["count"], last_val["count"])
            client_data[k].update({
                "diff_tag": tag,
                "diff": diff,
                "color": color
            })

        spider_data = get_spider_data(site, query_date=cycle)
        last_spider_data = get_spider_data(site, query_date=last_cycle)

        for k, v in spider_data.items():
            last_value = last_spider_data[k]
            tag, diff, color = get_diff_value(v["count"], last_value["count"])
            spider_data[k].update({
                "diff_tag": tag,
                "diff": diff,
                "color": color
            })

        report_cycle = "{} - {}".format(time.strftime("%Y-%m-%d", cycle_start), time.strftime("%Y-%m-%d", cycle_end))
        source_file_name = os.path.join(report_path, report_file_name + ".html")
        public.writeFile(source_file_name,
                         template.render(
                             server_name=server_name,
                             title=report_file_name,
                             site_name=site,
                             report_type=report_type,
                             last_cycle_title=last_cycle_title,
                             report_cycle=report_cycle,
                             generate_time=time.strftime("%Y-%m-%d %H:%M", time.localtime()),
                             overview=overview,
                             last_overview=last_overview,
                             ip_data=ip_data,
                             uri_data=uri_data,
                             area_data=area_data,
                             referer_data=referer_data,
                             client_data=client_data,
                             last_client_data=last_client_data,
                             spider_data=spider_data,
                             last_spider_data=last_spider_data
                         )
                         )

        pdf_file_name = generate_pdf_report(source_file_name)
        # print("报告已生成到: {}".format(pdf_file_name))
        print(tool.getMsg("REPORT_WEEK_GENERATED", args=(pdf_file_name,)))
        record_selector = report_cur.execute("select report_id from report where site=? and year=? and report_type=? and sequence=? order by generate_time desc", (site, year, report_type,sequence,))
        records = record_selector.fetchall()
        if len(records) == 0:
            report_cur.execute("insert into report(site, year, report_type, sequence, report_cycle, file_name, file_size, generate_time) values('{}', {}, '{}', {}, '{}', '{}', {}, '{}')".format(
                site, year, report_type, sequence, cycle, report_file_name, public.get_path_size(pdf_file_name), time.time()
            ))
            report_id = report_cur.lastrowid
            report_conn.commit()
        else:
            report_id = records[0][0]
            # print("更新已存在报告ID: {}".format(report_id))
            report_cur.execute("update report set year=?,report_type=?,sequence=?,report_cycle=?,file_name=?,file_size=?,generate_time=? where report_id=?",
                (year, report_type, sequence, cycle, report_file_name, public.get_path_size(pdf_file_name), time.time(), report_id,))
            report_conn.commit()
        if test:
            os.system("cp -f {} {}".format(source_file_name, "/www/wwwroot/192.168.1.60/"))
            os.system("cp -f {} {}".format(pdf_file_name, "/www/wwwroot/192.168.1.60/"))
        return {
            "report_id": report_id,
            "report_file_name": report_file_name
        }
    except Exception as e:
        # print("站点: {} 生成数据月报错误: {}。".format(site, str(e)))
        print(tool.getMsg("REPORT_MONTH_GENERATE_ERROR", args=(site, str(e),)))
    finally:
        if report_cur:
            report_cur.close()
        if report_conn:
            report_conn.close()
    return None


def generate_year_report(site, base_time=None, test=False):
    try:
        report_conn = None
        report_cur = None

        init_db()
        report_type = "年报"
        last_cycle_title = "上年度"
        env = Environment(loader=FileSystemLoader(os.path.join(plugin_dir, "templates")))
        reports_dir = os.path.join(plugin_dir, "reports")
        template = env.get_template("baogao.html")

        report_path = os.path.join(reports_dir, site)
        if not os.path.exists(report_path):
            os.makedirs(report_path)

        last_year = time.localtime().tm_year - 1
        cycle_start = time.localtime(time.mktime((last_year, 1, 1, 0, 0, 0, 0, 0, 0)))
        import calendar
        _, last_month_days = calendar.monthrange(last_year, 12)
        cycle_end = time.localtime(time.mktime((last_year, 12, last_month_days, 12, 59, 59, 0, 0, 0)))
        cycle = time.strftime("%Y%m%d", cycle_start) + "-" + time.strftime("%Y%m%d", cycle_end)
        # print("Month cycle:"+cycle)

        report_conn = sqlite3.connect(report_db_path)
        report_cur = report_conn.cursor()
        reportor = report_cur.execute("select report_id, site, report_cycle, report_type, file_name, generate_time from report where site='{}' and report_cycle='{}'".format(site, cycle))
        for report in reportor.fetchall():
            file_name = os.path.join(report_path, report[4] + ".html")
            report_id = report[0]
            if os.path.isfile(file_name):
                # print("报表已生成在：{}".format(file_name))
                return {
                    "report_id": report_id,
                    "report_file_name": report[4]
                }

        last_last_year = time.localtime().tm_year - 2
        last_cycle_start = time.localtime(time.mktime((last_last_year, 1, 1, 0, 0, 0, 0, 0, 0)))
        _, last_month_days = calendar.monthrange(last_last_year, 12)
        last_cycle_end = time.localtime(time.mktime((last_year, 12, last_month_days, 12, 59, 59, 0, 0, 0)))
        last_cycle = time.strftime("%Y%m%d", last_cycle_start) + "-" + time.strftime("%Y%m%d", last_cycle_end)
        # print("Month last_cycle:"+last_cycle)

        sequence = int(time.strftime("%m", cycle_start))
        year = time.strftime("%Y", cycle_start)
        year_desc = "年度数据报告"
        report_file_name = "{year}年网站{site}{year_desc}".format(
            year=year, site=site, year_desc=year_desc
        )

        # 概览数据
        overview = get_overview_data(site, query_date=cycle)
        if overview["req"]["count"] == 0:
            # print("统计数据为空无须生成报告。")
            return None

        # print("正在生成站点: {} 数据月报...".format(site))
        print("正在生成站点: {} 数据年报...".format(site))
        panel_config = {}
        alias = ""
        server_ip = public.GetLocalIp()
        try:
            panel_config = json.loads(public.readFile("/www/server/panel/config/config.json"))
            if "title" in panel_config.keys():
                alias = panel_config["title"]
        except:
            pass
        server_name = ""
        if alias and alias != server_ip:
            server_name = "{}({})".format(server_ip, alias)
        else:
            server_name = server_ip

        last_overview = get_overview_data(site, query_date=last_cycle)
        for k, v in overview.items():
            last_val = last_overview[k]
            format_func = format_count
            if k == "length":
                format_func = format_flow
            tag, diff, color = get_diff_value(v["count"], last_val["count"], format=format_func)
            overview[k].update({
                "diff_tag": tag,
                "diff": diff,
                "color": color
            })

        # IP 统计数据
        ip_data = get_ip_data(site, query_date=cycle)
        # URI 统计数据
        uri_data = get_uri_data(site, query_date=cycle)
        # 地区统计数据
        area_data = get_area_data(site, query_date=cycle)

        # 分析日志，提取数据
        # parse_logs_data(site, query_date=cycle)

        referer_data = get_referer_data(site, query_date=cycle)

        client_data = get_client_data(site, query_date=cycle)
        last_client_data = get_client_data(site, query_date=last_cycle)

        for k, v in client_data.items():
            last_val = last_client_data[k]
            if type(last_val) == str: continue
            tag, diff, color = get_diff_value(v["count"], last_val["count"])
            client_data[k].update({
                "diff_tag": tag,
                "diff": diff,
                "color": color
            })

        spider_data = get_spider_data(site, query_date=cycle)
        last_spider_data = get_spider_data(site, query_date=last_cycle)

        for k, v in spider_data.items():
            last_value = last_spider_data[k]
            tag, diff, color = get_diff_value(v["count"], last_value["count"])
            spider_data[k].update({
                "diff_tag": tag,
                "diff": diff,
                "color": color
            })

        report_cycle = "{} - {}".format(time.strftime("%Y-%m-%d", cycle_start), time.strftime("%Y-%m-%d", cycle_end))
        source_file_name = os.path.join(report_path, report_file_name + ".html")
        public.writeFile(source_file_name,
                         template.render(
                             server_name=server_name,
                             title=report_file_name,
                             site_name=site,
                             report_type=report_type,
                             last_cycle_title=last_cycle_title,
                             report_cycle=report_cycle,
                             generate_time=time.strftime("%Y-%m-%d %H:%M", time.localtime()),
                             overview=overview,
                             last_overview=last_overview,
                             ip_data=ip_data,
                             uri_data=uri_data,
                             area_data=area_data,
                             referer_data=referer_data,
                             client_data=client_data,
                             last_client_data=last_client_data,
                             spider_data=spider_data,
                             last_spider_data=last_spider_data
                         )
                         )

        pdf_file_name = generate_pdf_report(source_file_name)
        # print("报告已生成到: {}".format(pdf_file_name))
        print(tool.getMsg("REPORT_WEEK_GENERATED", args=(pdf_file_name,)))
        report_cur.execute("insert into report(site, year, report_type, sequence, report_cycle, file_name, file_size, generate_time) values('{}', {}, '{}', {}, '{}', '{}', {}, '{}')".format(
            site, year, report_type, sequence, cycle, report_file_name, public.get_path_size(pdf_file_name), time.time()
        ))
        report_id = report_cur.lastrowid
        # print("Last report id:"+repr())
        report_conn.commit()
        if test:
            os.system("cp -f {} {}".format(source_file_name, "/www/wwwroot/192.168.1.60/"))
            os.system("cp -f {} {}".format(pdf_file_name, "/www/wwwroot/192.168.1.60/"))
        return {
            "report_id": report_id,
            "report_file_name": report_file_name
        }
    except Exception as e:
        print("站点: {} 生成数据年报错误: {}。".format(site, str(e)))
        # print(tool.getMsg("REPORT_MONTH_GENERATE_ERROR", args=(site, str(e),)))
    finally:
        if report_cur:
            report_cur.close()
        if report_conn:
            report_conn.close()
    return None


def send_report():
    """推送报告"""
    try:
        send_interval = 60 * 2
        report_conn = sqlite3.connect(report_db_path)
        report_cur = report_conn.cursor()
        selector = report_cur.execute("select report_id from send_list;")
        log = selector.fetchone()
        while log:
            send_status = 0
            report_id = log[0]
            report = report_cur.execute("select site, file_name from report where report_id={};".format(report_id)).fetchone()
            if report:
                site = report[0]
                # print("准备发送报告: {}".format(report[1]))
                print(tool.getMsg("REPORT_SENDING", args=(report[1],)))
                report_file_name = report[1]
                file_name = os.path.join("/www/server/panel/plugin/total", "reports", site, report_file_name + ".html")
                if os.path.isfile(file_name):
                    # to send mail
                    from send_mail import send_mail
                    sm = send_mail()
                    settings = sm.get_settings()

                    mail_list = []
                    if "user_mail" in settings.keys():
                        if "mail_list" in settings["user_mail"].keys():
                            mail_list = settings["user_mail"]["mail_list"]
                    content = public.readFile(file_name)
                    for i, receiver in enumerate(mail_list):
                        # print("Receiver:"+receiver)
                        res = sm.qq_smtp_send(receiver, title=report_file_name, body=content)
                        if res:
                            # print("报告:{} 发送成功({})。".format(report_file_name, time.strftime("%Y%m%d %H:%M:%S", time.localtime())))
                            print(tool.getMsg("REPORT_SEND_SUCCESSFULLY", args=(report_file_name, time.strftime("%Y%m%d %H:%M:%S", time.localtime()),)))
                            send_status = 1
                        else:
                            send_status = 2
                    
                        report_cur.execute("insert into send_log(report_id, receiver, send_time, send_status) values({}, '{}', {}, {});".format(report_id, receiver, time.time(), send_status))

                        if i < len(mail_list) - 1:
                            print("Waiting...")
                            time.sleep(send_interval)

            else:
                # failture
                receiver = ""
                send_status = 2
                remark = "Not found report."
                report_cur.execute("insert into send_log(report_id, receiver, send_time, send_status, remark) values({}, '{}', {}, {}, '{}');".format(
                    report_id, receiver, time.time(), send_status, remark)
                )

            report_cur.execute("delete from send_list where report_id={}".format(report_id))
            log = selector.fetchone()
            if log:
                print("Waiting2...")
                time.sleep(send_interval)

        try:
            report_conn.commit()
        except:
            pass
        report_cur.close()
        report_conn.close()
    except Exception as e:
        # print("推送报告出现错误:" + str(e))
        print(tool.getMsg("REPORT_SEND_ERROR", args=(str(e),)))


def automatic_generate_report_old():
    """自动生成数据报告
    
    每月1号生成上月的月报
    每周一生成上周的周报
    
    生成完之后逐一进行推送
    """
    now = time.localtime()
    generator = []
    frist_report_tag_file = "/www/server/panel/plugin/total/frist_report.pl"
    frist_generate_report = True
    if os.path.isfile(frist_report_tag_file):
        frist_generate_report = False
    if frist_generate_report or now.tm_mday == 1:
        # 每月1号生成上月的月报
        generator.append(generate_month_report)

    if frist_generate_report or now.tm_wday == 0:
        # 每周一生成上周的周报	
        generator.append(generate_week_report)

    sites = public.M('sites').field('name').order("addtime").select()
    # for site_info in sites:
    #     parse_logs_data(site_info["name"], "today")

    if len(generator) == 0:
        return True

    config = json.loads(public.readFile("/www/server/total/config.json"))
    for site_info in sites:
        site = site_info["name"].replace("_", ".")
        for gen in generator:
            try:
                report_info = gen(site)
                if report_info:
                    new_report_id = report_info["report_id"]
                    report_file_name = report_info["report_file_name"]
                    # print("新报表ID：{}".format(new_report_id))
                    # print("新报表文件名：{}".format(report_file_name))

                    global_push_m = False
                    push_m = False
                    if "push_report" in config["global"].keys():
                        global_push_m = config["global"]["push_report"]
                    if global_push_m and site in config.keys():
                        site_config = config[site]
                        if "push_report" in site_config.keys():
                            push_m = site_config["push_report"]

                    if push_m:
                        report_conn = sqlite3.connect(report_db_path)
                        report_cur = report_conn.cursor()
                        report_send_log_selector = report_cur.execute("select count(*) from send_log where report_id={}".format(new_report_id)) 
                        report_send_log = report_send_log_selector.fetchone()
                        if report_send_log[0] <= 0:
                            report_cur.execute("insert into send_list(report_id, add_time) values({}, {});".format(new_report_id, time.time()))
                            report_conn.commit()
                        else:
                            print(tool.getMsg("REPORT_SEND"))
                        report_cur.close()
                        report_conn.close()
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(tool.getMsg("AUTOMATIC_GENERATE_REPORT_ERROR", args=(str(e),)))

    send_report()
    if frist_generate_report:
        public.writeFile(frist_report_tag_file, "yes")


def automatic_generate_week_report(site):
    """"""
    now = time.localtime()
    base_time = now
    reports = []
    start, end = get_last_week(base_time=base_time)
    report_info = generate_week_report(site, cycle_start=start, cycle_end=end)
    if report_info:
        reports.append(report_info)

    return reports


def automatic_generate_report(week_time, month_time):
    sites = public.M('sites').field('name').order("addtime").select()
    config = json.loads(public.readFile("/www/server/total/config.json"))
    reports = []
    global_push_m = False
    if "push_report" in config["global"].keys():
        global_push_m = config["global"]["push_report"]

    for site_info in sites:
        # generate
        if week_time == 0:
            site = site_info["name"].replace("_", ".")
            week_reports = automatic_generate_week_report(site)
            reports += week_reports

        if month_time == 1:
            month_report = generate_month_report(site)
            if month_report:
                reports.append(month_report)

        push_m = False
        if global_push_m and site in config.keys():
            site_config = config[site]
            if "push_report" in site_config.keys():
                push_m = site_config["push_report"]

        # send 
        # print("{} 推送开关: {}".format(site, push_m))
        if push_m:
            # print('待发送报告数量: {}'.format(len(reports)))
            for report_info in reports:
                if report_info:
                    new_report_id = report_info["report_id"]
                    # report_file_name = report_info["report_file_name"]
                    # print("新报表ID：{}".format(new_report_id))
                    # print("新报表文件名：{}".format(report_file_name))

                    report_conn = sqlite3.connect(report_db_path)
                    report_cur = report_conn.cursor()
                    report_send_log_selector = report_cur.execute("select count(*) from send_log where report_id={}".format(new_report_id)) 
                    report_send_log = report_send_log_selector.fetchone()
                    if report_send_log[0] <= 0:
                        try:
                            report_cur.execute("insert into send_list(report_id, add_time) values({}, {});".format(new_report_id, time.time()))
                            report_conn.commit()
                        except:
                            pass
                    else:
                        print(tool.getMsg("REPORT_SEND"))
                    report_cur.close()
                    report_conn.close()

            send_report()


def clear_report():
    import sqlite3
    conn = sqlite3.connect(report_db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM report")
    conn.commit()


def test_send_report():
    import sqlite3
    conn = sqlite3.connect(report_db_path)
    cur = conn.cursor()
    selector = cur.execute("select report_id from report order by report_id desc limit 1;")
    report_id = selector.fetchone()[0]

    cur.execute("insert into send_list(report_id) values({});".format(report_id))
    conn.commit()

    send_report()


def test_get_data(site):
    # tm = Plugin(PLUGIN_NAME)
    start_date, end_date = tool.get_query_date("l30")
    # cycle_data = tm.get_fun()()
    get = public.dict_obj()
    get.site = site
    get.query_date = "l30"
    get.top = 20
    print(tool.request_plugin("get_site_overview_sum_data", (site, start_date, end_date)))
    print(tool.request_plugin("get_area_stat", (get,), {"flush": False, "format_count": True}))


def test_get_fun():
    """测试付费插件授权"""
    sites = public.M('sites').field('name').order("addtime").select()
    for i in range(0, 1):
        for site in sites:
            test_get_data(site["name"])
    print("测试完成!")


if __name__ == "__main__":
    # repair_report()
    # test_get_fun()
    # site = ""
    # if len(sys.argv) > 1:
    #     site = sys.argv[1]
    # if site == "all":
    #     sites = public.M('sites').field('name').order("addtime").select()
    #     sites = [x["name"] for x in sites]
    # else:
    #     sites = [site]
    # for s in sites:
    #     if s:
    #         generate_year_report(s)
    # automatic_generate_report()
    # sites = public.M('sites').field('name').order("addtime").select()
    # for site_info in sites:
    #     site = site_info["name"].replace("_", ".")
    #     # generate_month_report(site)
    # generate_week_report("www.zhiyun-tech.com", force=True)
    # generate_month_report("192.168.1.65", force=True)
    # print(get_client_data("www.bt.cn", "20210701-20210702"))
    # get_last_month(base_time=time.strptime("20210607", "%Y%m%d"))
    # generate_month_report(site, test=True)

    # test_send_report()
    # test_get_data("www.zhiyun-tech.com")
    pass
    # print(now, month, week)
