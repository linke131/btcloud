#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyleft (c) 2015-2099 宝塔软件(http://bt.cn) All lefts reserved.
# +-------------------------------------------------------------------
# | Author: linxiao
# | Date: 2021/11/5
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   宝塔网站监控报表日志自助清理工具
# +--------------------------------------------------------------------
from __future__ import absolute_import, print_function, division

import sqlite3
import sys
import time
import os
import json

if sys.version_info[0] == 2:
    input = raw_input

def get_before_days(before_days):
    if before_days < 0:
        raise RuntimeError("Error.")

    now = time.localtime()
    count = 1
    days = []
    for i in range(now.tm_mday-1, 0, -1):
        # print("i:{}, count: {}".format(i, count))
        if count > before_days:
            days.append(i)
        if count >= 30:
            break
        count += 1

    import calendar
    _, last_month_days = calendar.monthrange(now.tm_year, now.tm_mon-1)
    if count < (max(last_month_days, 30)):
        for j in range(last_month_days, 0, -1):
            # print("j: {}, count: {}".format(j, count))
            if count > before_days:
                days.append(j)
            if count >= 30:
                break
            count += 1
    return days


def ReadFile(filename,mode = 'r'):
    """
    读取文件内容
    @filename 文件名
    return string(bin) 若文件不存在，则返回None
    """
    import os
    if not os.path.exists(filename): return False
    try:
        fp = open(filename, mode)
        f_body = fp.read()
        fp.close()
    except Exception as ex:
        if sys.version_info[0] != 2:
            try:
                fp = open(filename, mode,encoding="utf-8")
                f_body = fp.read()
                fp.close()
            except:
                fp = open(filename, mode,encoding="GBK")
                f_body = fp.read()
                fp.close()
        else:
            return False
    return f_body

def clear_logs(target_sites="all", before_days=30, clear_statistics=True):

    config_path = "/www/server/total/config.json"
    settings = json.loads((ReadFile(config_path)))
    monitor_status = False
    if "global" in settings:
        global_settings = settings["global"]
        monitor_status = global_settings["monitor"]
    if monitor_status:
        print("请先关闭监控报表。")
        return False

    site_conn = sqlite3.connect("/www/server/panel/data/default.db")
    site_cur = site_conn.cursor()
    sites = site_cur.execute("select name from sites;").fetchall()
    site_cur.close()
    site_conn.close()
    site_tips = ""

    now = time.localtime()
    before_timestamp = time.mktime((now.tm_year, now.tm_mon, now.tm_mday-before_days-1, 0, 0, 0, 0, 0, 0))
    before_date = time.localtime(before_timestamp)
    time_key = int(time.strftime("%Y%m%d", before_date))
    time_desc = time.strftime("%Y-%m-%d", before_date)   

    if before_days > 0:
        if clear_statistics:
            print("以下网站{}天(包括{})以前的日志和统计数据将被删除:".format(before_days, time_desc))
        else:
            print("以下网站{}天(包括{})以前的日志将被删除:".format(before_days, time_desc))
    else:
        print("以下网站所有日志和统计数据将被删除:")
    for s in sites:
        if target_sites == "all":
            print(s[0])
        else:
            if s[0] == target_sites:
                print(target_sites)

    answer = input("确认清除操作?(Y/N):")

    if answer not in ["Y", "y", "yes"]:
        print("操作取消。")
        return False

    print("数据越多，清理时间越长，请耐心等待。")
    print("开始清理数据...")
    for site_info in sites:
        site_name = site_info[0]
        if target_sites != "all":
            if site_name != target_sites:
                # print("CONTINUE: {}".format(site_name))
                continue

        db_path = "/www/server/total/logs/{}/history_logs.db".format(site_name)
        if not os.path.exists(db_path):
            continue

        if before_days == 0:
            os.remove(db_path)
            continue

        try:
            time_start = time.time()
        
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()

            if clear_statistics:
                cur.execute("DELETE FROM {} where time/100 <= {}".format("client_stat", time_key))
                cur.execute("DELETE FROM {} where time/100 <= {}".format("request_stat", time_key))
                cur.execute("DELETE FROM {} where time/100 <= {}".format("spider_stat", time_key))

                cur.execute("DELETE FROM {} where time <= {}".format("referer_stat", time_key/100))
        
                for day in get_before_days(before_days):
                    # print("清理day{} stat...".format(day))
                    cur.execute("UPDATE {table} set day{day}=0, flow{day}=0, spider_flow{day}=0".format(table="uri_stat", day=day))
                    cur.execute("UPDATE {table} set day{day}=0, flow{day}=0".format(table="ip_stat", day=day))
        
            cur.execute("DELETE FROM {} where time <= {}".format("site_logs", before_timestamp))
            time_end1 = time.time()
            conn.commit()
            print("删除数据耗时: {}秒.".format(round(time_end1-time_start, 2)))

            print("正在整理数据空间...")
            time_start2 = time.time()
            conn.execute("VACUUM;")
            time_end2 = time.time()
            cur.close()
            conn.close()
            print("整理空间耗时: {}秒.".format(round(time_end2-time_start2, 2)))
            current_size = os.path.getsize(db_path)
            print("{} 清理完后日志文件大小:{}GB.".format(site_name, round(current_size/1024/1024/1024, 2)))
        except Exception as e:
            print("站点:{} 清理日志出错: {}.".format(site_name, str(e)))

    print("数据清理完毕。")

if __name__ == "__main__":
    site_conn = sqlite3.connect("/www/server/panel/data/default.db")
    site_cur = site_conn.cursor()
    sites = site_cur.execute("select name from sites;").fetchall()
    site_cur.close()
    site_conn.close()
    
    if len(sites) == 0:
        print("站点为空。")
        sys.exit(0)

    print("请选择需要清理的站点:")
    for inx, s in enumerate(sites):

        db_path = "/www/server/total/logs/{}/history_logs.db".format(s[0])
        db_size = 0
        if os.path.exists(db_path):
            db_size = round(os.path.getsize(db_path) /1024/1024/1024, 2)
        print("[{}] {} {}GB".format(inx+1, s[0], db_size))

    print("[{}] 所有站点".format(inx+1+1))
    print("[0] 取消")
    
    try:
        answer = int(input("请选择:"))
    except:
        answer = 0

    site_name = ""
    if answer == 0:
        print("取消操作。")
        sys.exit(0)
    
    if answer == inx+1+1:
        site_name = "all"
        print("选择了清理所有站点。")
    else:
        site_name = sites[answer-1][0]
        print("站点: {} 将被清理。".format(site_name))
    
    try:
        before_days = input("请输入保留日志的天数(0 删除所有数据, N/n 取消)：")
        try:
            before_days = int(before_days)
        except:
            print("操作取消。")
            sys.exit(0)

    except Exception as e:
        print("操作有误。")
        sys.exit(0)

    clear_statistics = False
    # if before_days > 0:
    #     try:
    #         clear_answer = input("是否保留统计数据? (Y/N)：")
    #         if clear_answer in ["Y", "y", "yes"]:
    #             print("保留统计数据，只清理网站日志。")
    #             clear_statistics = False
    #         else:
    #             print("统计数据也将被删除。")
    #             clear_statistics = True
    #     except:
    #         print("操作有误。")
    #         sys.exit(0)

    # site = sys.argv[1]
    # days = int(sys.argv[2])
    clear_logs(site_name, before_days, clear_statistics=clear_statistics)
    # print(get_before_days(0))