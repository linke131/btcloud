# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyleft (c) 2015-2099 宝塔软件(http://bt.cn) All lefts reserved.
# +-------------------------------------------------------------------
# | Author: linxiao
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   宝塔网站监控报表工具函数
# +--------------------------------------------------------------------
from __future__ import absolute_import, print_function, division
import os
import sys
import time
import json

os.chdir("/www/server/panel")
sys.path.insert(0, "/www/server/panel/class")

import public
from pluginAuth import Plugin

__frontend_path = '/www/server/panel/plugin/total'
__backend_path = "/www/server/total"
PLUGIN_NAME = "total"


def getMsg(msg, args=[]):
    language_file = 'total.json'
    lang_file = os.path.join(__frontend_path, 'language', public.GetLanguage(), language_file)
    log_message = json.loads(public.readFile(lang_file))
    keys = log_message.keys()
    if type(msg) == str:
        if msg in keys:
            msg = log_message[msg]
            for i in range(len(args)):
                rep = '{' + str(i + 1) + '}'
                msg = msg.replace(rep, str(args[i]))
    return msg


def returnMsg(status, msg, args=[]):
    """
        @name 取通用dict返回
        @author hwliang<hwl@bt.cn>
        @param status  返回状态
        @param msg  返回消息
        @return dict  {"status":bool,"msg":string}
    """
    msg = getMsg(msg, args)
    return {'status': status, 'msg': msg}


def get_logs_db_name_by_timestamp(site, start_timestamp, end_timestamp):
    """根据查询时间查找对应的日志db文件

    Args:
        start_timestamp (timestamp): 起始时间戳
        end_timestamp (timestamp): 截止时间戳
    """
    base_dir = "/www/server/total/logs/{}/".format(site)
    normal_db_name = get_logs_db_name(time.localtime(start_timestamp))
    except_db_path = os.path.join(base_dir, normal_db_name)
    if os.path.exists(except_db_path):
        return except_db_path
    history_base_dir = get_history_data_dir()
    except_db_path = os.path.join(history_base_dir, site, normal_db_name)
    # print("except history db path: {}".format(except_db_path))
    if os.path.exists(except_db_path):
        return except_db_path

    info_file = base_dir + "logs.info"
    log_info_str = public.readFile(info_file)
    if log_info_str:
        log_info = json.loads(log_info_str)
        for fkey, info in log_info.items():
            if not type(info) == dict: continue
            start = info["start"]
            end = info["end"]
            match = False
            if start_timestamp >= start and end_timestamp <= end:
                match = True
            else:
                bokeh_start, _ = get_timestamp_interval(time.localtime(start))
                _, bokeh_end = get_timestamp_interval(time.localtime(end))
                if start_timestamp >= bokeh_start and end_timestamp <= bokeh_end:
                    match = True

            if match and fkey.endswith(".db"):
                db_name = os.path.join(history_base_dir, site, info["file_name"])
                if os.path.exists(db_name):
                    return db_name
    return ""


def get_logs_db_name(date=None):
    if date is None:
        date = time.localtime()
    time_format = "%Y%m%d"
    return time.strftime(time_format, date) + ".db"


def get_logs_txt_name(date=None):
    if date is None:
        date = time.localtime()
    time_format = "%Y%m%d"
    return time.strftime(time_format, date) + ".txt"


def get_time_key(date=None):
    if date is None:
        date = time.localtime()
    time_key = 0
    time_key_format = "%Y%m%d%H"
    if type(date) == time.struct_time:
        time_key = int(time.strftime(time_key_format, date))
    if type(date) == str:
        time_key = int(time.strptime(date, time_key_format))
    return time_key


def get_time_interval(local_time):
    start = None
    end = None
    time_key_format = "%Y%m%d00"
    start = int(time.strftime(time_key_format, local_time))
    time_key_format = "%Y%m%d23"
    end = int(time.strftime(time_key_format, local_time))
    return start, end


def get_timestamp_interval(local_time):
    start = None
    end = None
    start = time.mktime((local_time.tm_year, local_time.tm_mon,
                         local_time.tm_mday, 0, 0, 0, 0, 0, 0))
    end = time.mktime((local_time.tm_year, local_time.tm_mon,
                       local_time.tm_mday, 23, 59, 59, 0, 0, 0))
    return start, end


def get_last_days_by_timestamp(day):
    now = time.localtime()
    if day == 30:
        last_month = now.tm_mon - 1
        if last_month <= 0:
            last_month = 12
        import calendar
        _, last_month_days = calendar.monthrange(now.tm_year, last_month)
        day = last_month_days
    else:
        day += 1

    t1 = time.mktime(
        (now.tm_year, now.tm_mon, now.tm_mday - day, 0, 0, 0, 0, 0, 0))
    t2 = time.localtime(t1)
    start, _ = get_timestamp_interval(t2)
    _, end = get_timestamp_interval(now)
    return start, end


def get_last_days(day):
    now = time.localtime()
    if day == 30:
        last_month = now.tm_mon - 1
        if last_month <= 0:
            last_month = 12
        import calendar
        _, last_month_days = calendar.monthrange(now.tm_year, last_month)
        day = last_month_days
    else:
        day += 1

    t1 = time.mktime(
        (now.tm_year, now.tm_mon, now.tm_mday - day, 0, 0, 0, 0, 0, 0))
    t2 = time.localtime(t1)
    start, _ = get_time_interval(t2)
    _, end = get_time_interval(now)
    return start, end


def get_query_timestamp(query_date):
    """获取查询日期的时间戳 """
    try:
        start_date = None
        end_date = None
        if query_date == "today":
            start_date, end_date = get_timestamp_interval(
                time.localtime())
        elif query_date == "yesterday":
            # day - 1
            now = time.localtime()
            yes_i = time.mktime((now.tm_year, now.tm_mon, now.tm_mday - 1, 0, 0, 0, 0, 0, 0))
            yes = time.localtime(yes_i)
            start_date, end_date = get_timestamp_interval(yes)
        elif query_date.startswith("l"):
            days = int(query_date[1:])
            start_date, end_date = get_last_days_by_timestamp(days)
        elif query_date.startswith("h1"):
            # 近1小时查询
            # hours = int(query_date[1:])
            # 如果当前小时未超过30分钟，把上一小时数据计算进来，否则只算当前一小时的
            # 数据。
            now = time.localtime()
            start_date = time.mktime((now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min - 60, 0, 0, 0, 0))
            end_date = time.mktime(now)
        else:
            if query_date.find("-") < 0:
                if query_date.isdigit():
                    s_time = time.strptime(query_date, "%Y%m%d")
                    start_date, end_date = get_timestamp_interval(
                        s_time)
            else:
                s, e = query_date.split("-")
                if s[-6:] == "000000" and e[-6:] == "000000":
                    s = s[:-6]
                    e = e[:-6]
                    start_time = time.strptime(s.strip(), "%Y%m%d")
                    end_time = time.strptime(e.strip(), "%Y%m%d")
                    start_date, _ = get_timestamp_interval(start_time)
                    _, end_date = get_timestamp_interval(end_time)
                else:
                    start_time = time.strptime(s.strip(), "%Y%m%d%H%M%S")
                    end_time = time.strptime(e.strip(), "%Y%m%d%H%M%S")
                    start_date = time.mktime(start_time)
                    end_date = time.mktime(end_time)

    except Exception as e:
        print("query timestamp exception:", str(e))
    return start_date, end_date


def get_query_date(query_date, begin=True):
    """获取查询日期

    查询日期的表示形式是以区间的格式表示，这里也考虑到了数据库里面实际存储的方式。
    在数据库里面是以小时为单位统计日志数据，所以这里的区间也是也小时来表示。
    比如表示今天，假设今天是2021/3/30，查询日期的格式是2021033000-2021033023。
    """
    try:
        start_date = None
        end_date = None
        if query_date == "today":
            start_date, end_date = get_time_interval(time.localtime())
        elif query_date == "yesterday":
            # day - 1
            now = time.localtime()
            yes_i = time.mktime((now.tm_year, now.tm_mon, now.tm_mday - 1, 0, 0, 0, 0, 0, 0))
            yes = time.localtime(yes_i)
            start_date, end_date = get_time_interval(yes)
        elif query_date.startswith("l"):
            days = int(query_date[1:])
            start_date, end_date = get_last_days(days)
        elif query_date.startswith("h1"):
            # 近1小时查询
            # hours = int(query_date[1:])
            # 如果当前小时未超过30分钟，把上一小时数据计算进来，否则只算当前一小时的
            # 数据。
            now = time.localtime()
            if now.tm_min >= 30:
                start_date = time.mktime((now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, 0, 0, 0, 0, 0))
                start_date = get_time_key(start_date)
                end_date = start_date
            else:
                s = time.localtime(time.mktime((now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour - 1, 0, 0, 0, 0, 0)))
                start_date = get_time_key(s)
                e = time.localtime(time.mktime((now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, 0, 0, 0, 0, 0)))
                end_date = get_time_key(e)
        else:
            if query_date.find("-") < 0:
                if query_date.isdigit():
                    s_time = time.strptime(query_date, "%Y%m%d")
                    start_date, end_date = get_time_interval(s_time)
            else:
                s, e = query_date.split("-")
                start_time = time.strptime(s.strip(), "%Y%m%d")
                start_date, _ = get_time_interval(start_time)
                end_time = time.strptime(e.strip(), "%Y%m%d")
                _, end_date = get_time_interval(end_time)

    except Exception as e:
        print("query date exception:", str(e))
    # print("start, end:", start_date, end_date)
    return start_date, end_date


def get_compare_date(query_start_date, compare_date):
    """获取对比日期"""
    try:
        start_date = time.strptime(str(query_start_date), "%Y%m%d%H")
        end_date = None
        if compare_date == "yesterday":
            yes_i = time.mktime((start_date.tm_year, start_date.tm_mon,
                                 start_date.tm_mday - 1, 0, 0, 0, 0, 0, 0))
            yes = time.localtime(yes_i)
            start_date, end_date = get_time_interval(yes)
        elif compare_date == "lw":
            week_i = time.mktime((start_date.tm_year, start_date.tm_mon,
                                  start_date.tm_mday - 7, 0, 0, 0, 0, 0, 0))
            week = time.localtime(week_i)
            start_date, end_date = get_time_interval(week)
        elif compare_date == "h1":
            now = time.localtime()
            if now.tm_min >= 30:
                start_date = time.mktime((now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour - 1, 0, 0, 0, 0, 0))
                start_date = get_time_key(start_date)
                end_date = start_date
            else:
                s = time.localtime(time.mktime((now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour - 2, 0, 0, 0, 0, 0)))
                start_date = get_time_key(s)
                end_date = start_date
        else:
            if compare_date.find("-") < 0:
                if compare_date.isdigit():
                    s_time = time.strptime(compare_date, "%Y%m%d")
                    start_date, end_date = get_time_interval(s_time)
            else:
                # print("区间时间：", compare_date)
                s, e = compare_date.split("-")
                start_time = time.strptime(s.strip(), "%Y%m%d")
                start_date, _ = get_time_interval(start_time)
                end_time = time.strptime(e.strip(), "%Y%m%d")
                _, end_date = get_time_interval(end_time)

        return start_date, end_date
    except Exception as e:
        print("compare date exception:", str(e))
    return None, None


#############sqlite####################


def export_sqlite_sql(db, tables="all", output_file=None):
    import sqlite3
    if os.path.exists(db):
        db = sqlite3.connect(db)
    else:
        return False

    cur = db.cursor()
    tables_str = ""
    if type(tables) == str:
        if tables == "all":
            pass
        elif tables.find(",") >= 0:
            tables_str = ["'" + t + "'" for t in tables.split(",") if t.strip()]
        else:
            tables_str = "'{}'".format(tables)
    else:
        tables_str = ["'" + t + "'" for t in tables]
    if tables == "all":
        results = cur.execute("select sql from sqlite_master").fetchall()
    else:
        select_sql = "select sql from sqlite_master where name in ({})".format(tables_str)
        results = cur.execute(select_sql).fetchall()
    sql_text = ""
    for res in results:
        if res[0]:
            if sql_text and sql_text != "None":
                sql_text += "\n"
            sql_text += res[0] + ";"

    if output_file and sql_text:
        with open(output_file, "w", encoding="utf-8") as fp:
            fp.write(sql_text)
    return sql_text


def init_db_from(ori_db, new_db, tables="all"):
    try:
        sql_text = export_sqlite_sql(ori_db, tables=tables)
        if sql_text:
            import sqlite3
            print(new_db)
            conn = sqlite3.connect(new_db)
            cur = conn.cursor()
            res = cur.executescript(sql_text)
            cur.close()
            conn.close()
        if os.path.exists(new_db):
            return True
    except Exception as e:
        print("初始化异常：{}".format(e))
    return False


def get_file_json(filename, defaultv={}):
    try:
        if not os.path.exists(filename): return defaultv;
        return json.loads(public.readFile(filename))
    except:
        os.remove(filename)
        return defaultv


def get_site_settings(site):
    """获取站点配置"""

    config_path = "/www/server/total/config.json"
    config = get_file_json(config_path)

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
    return res_config


def get_site_name(siteName):
    db_file = '/www/server/total/logs/' + siteName + '/logs.db'
    if os.path.isfile(db_file): return siteName

    pid = public.M('sites').where('name=?', (siteName,)).getField('id');
    if not pid:
        return siteName

    domains = public.M('domain').where('pid=?', (pid,)).field('name').select()
    for domain in domains:
        db_file = '/www/server/total/logs/' + domain["name"] + '/logs.db'
        if os.path.isfile(db_file):
            siteName = domain['name']
            break
    return siteName.replace('_', '.')


# def split_query_date(query_date):
#     query_start, query_end = get_query_timestamp(query_date)
#     today = time.strftime("%Y%m%d", time.localtime())
#     _e = time.localtime(query_end)
#     end = time.strftime("%Y%m%d", _e)
#     query_array = []
#     if today == end:
#         query_array.append("today")

#         _e = time.localtime(time.mktime((_e.tm_year, _e.tm_mon, _e.tm_mday-1, 0,0,0,0,0,0)))
#         end_time = time.strftime("%Y%m%d", _e)
#         _start, _end = get_query_timestamp(end_time)
#         # print(query_start, _start)
#         if query_start < _start:
#             s = time.strftime("%Y%m%d000000", time.localtime(query_start))
#             e = time.strftime("%Y%m%d000000", _e)
#             query_str = "{}-{}".format(s, e)
#             query_array.append(query_str)
#     else:
#         query_array.append(query_date)
#     return query_array

def get_history_data_dir():
    default_history_data_dir = os.path.join(__backend_path, "logs")
    settings = get_site_settings("global")
    if "history_data_dir" in settings.keys():
        config_data_dir = settings["history_data_dir"]
    else:
        config_data_dir = default_history_data_dir
    history_data_dir = default_history_data_dir if not config_data_dir else config_data_dir
    return history_data_dir


def get_data_dir():
    default_data_dir = os.path.join(__backend_path, "logs")
    settings = get_site_settings("global")
    if "data_dir" in settings.keys():
        config_data_dir = settings["data_dir"]
    else:
        config_data_dir = default_data_dir
    data_dir = default_data_dir if not config_data_dir else config_data_dir
    return data_dir


def get_log_db_path(site, db_name="logs.db", history=False):
    site = site.replace('_', '.')
    if not history:
        data_dir = get_data_dir()
        db_path = os.path.join(data_dir, site, db_name)
    else:
        # 已废弃
        data_dir = get_history_data_dir()
        db_name = "history_logs.db"
        db_path = os.path.join(data_dir, site, db_name)
    return db_path


def request_plugin(fun_name, args, kwargs={}, retry=2):
    plu = Plugin(PLUGIN_NAME)
    msg = ""
    try:
        result = plu.get_fun(fun_name)(*args, **kwargs)
        if result:
            from collections.abc import Iterable
            if isinstance(result, Iterable) and "status" in result:
                msg = result["msg"]
    except Exception as e:
        msg = str(e)
        result = public.returnMsg(False, msg)

    if msg.find("授权验证失败") != -1:
        if retry > 0:
            return request_plugin(fun_name, args, kwargs, retry=retry - 1)
        raise RuntimeError(msg)
    return result


def get_compress_types():
    return ["tar.gz"]


def get_default_compress_type():
    """选择压缩类型

    Returns:
        (ctype, suffix): 压缩类型和文件后缀
    """
    return "tar.gz", "tar.gz"


def compress_file(source, new_file, ctype="tar.gz"):
    """对source压缩，输出为new_file

    Args:
        source (str): 源文件名
        new_file (str): 新文件名称
        ctype: 压缩类型
    """

    if ctype == "tar.gz":
        public.ExecShell("tar -czf {} {}".format(new_file, source))
        if os.path.exists(new_file):
            return True
        return False


def get_db_time_interval(db_name):
    """给定一个db文件，返回db记录的网站日志时间区间

    Args:
        db_name (str): db文件路径

    Returns:
        tuple: 正常返回日志起始时间(start, end)，没有记录或异常返回(0,0)
    """
    conn = None
    cur = None
    try:
        import sqlite3
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()

        select_start_sql = "select time from site_logs order by time asc limit 1"
        cur.execute(select_start_sql)
        _res = cur.fetchone()
        if not _res:
            print("not start info。")
            return 0, 0
        start = _res[0]

        select_end_sql = "select time from site_logs order by time desc limit 1"
        cur.execute(select_end_sql)
        _res = cur.fetchone()
        end = _res[0]

        print("start from: {}/ end with: {}".format(start, end))
        return start, end
    except Exception as e:
        print("获取db日志时间间隔异常:")
        print(e)
    finally:
        cur and cur.close()
        conn and conn.close()
    return 0, 0


def write_site_domains():
    """写入lua端调用的域名配置

    Returns:
        str: 可供lua直接require的格式数据
    """
    sites = public.M('sites').field('name,id').select()
    my_domains = {}
    for my_site in sites:
        tmp_domains = public.M('domain').where('pid=?',
                                               (my_site['id'],)).field(
            'name').select()
        site_name = my_site['name']
        generic_domains = []
        normal_domains = []
        for domain in tmp_domains:
            domain_name = domain['name']
            if domain_name.find("*") != -1:
                simple_name = domain_name.replace("*.", '')
                normal_domains.append(simple_name)
                generic_domains.append(domain_name)
            else:
                if domain_name != site_name:
                    normal_domains.append(domain_name)
        binding_domains = public.M('binding').where('pid=?',
                                                    (my_site['id'],)).field(
            'domain').select()
        for domain in binding_domains:
            domain_name = domain['domain']
            if domain_name.find("*") != -1:
                simple_name = domain_name.replace("*.", '')
                normal_domains.append(simple_name)
                generic_domains.append(domain_name)
            else:
                if domain_name != site_name:
                    normal_domains.append(domain_name)
        tmp = {}
        if normal_domains:
            tmp["normal"] = normal_domains
        if generic_domains:
            tmp["generic"] = generic_domains
        my_domains[site_name] = tmp
    from lua_maker import LuaMaker
    config_domains = LuaMaker.makeLuaTable(my_domains)
    domains_str = "return " + config_domains
    public.WriteFile("/www/server/total/domains.lua", domains_str)
    return True


def parse_regular_url(url):
    """处理url中的特殊字符，以符合lua配置文件语法"""
    v = url
    if v.find("\?") >= 0:
        v = v.replace("\?", "\\\?")
    return v


def parse_ips(ips):
    """生成区间IP列表"""
    sip, eip = ips.split("-")
    ip_prefix = sip[:sip.rfind(".") + 1]
    snum = int(sip[sip.rfind(".") + 1:])
    enum = int(eip[eip.rfind(".") + 1:])
    ip_list = []
    for x in range(snum, enum + 1):
        if x > 255:
            break
        ip_list.append(ip_prefix + str(x))
    return ip_list


def split_query_date(start_timestamp, end_timestamp=None):
    """倒着写"""
    start = time.localtime(end_timestamp)
    # end = time.localtime(start_timestamp)
    query_list = []
    # format = "%Y%m%d%H%M%S"
    while True:
        s, e = get_timestamp_interval(start)
        if e > end_timestamp:
            e = end_timestamp
        if s < start_timestamp:
            s = start_timestamp
        # query_start = time.strftime(format, time.localtime(s))
        # query_end = time.strftime(format, time.localtime(e))
        # query_interval = query_start + "-" + query_end
        query_list.append((s, e,))

        start = time.localtime(time.mktime((start.tm_year, start.tm_mon, start.tm_mday - 1, 0, 0, 0, 0, 0, 0)))
        if s <= start_timestamp:
            break

    return query_list