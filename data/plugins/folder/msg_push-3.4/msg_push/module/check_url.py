#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: zhw <zhw@bt.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   URL监控
#+--------------------------------------------------------------------

import time
import public
import sys
import requests
import json
panel_path = "/www/server/panel"
plugin_path = "{}/plugin/msg_push".format(panel_path)
msg_file = '{}/msg.json'.format(plugin_path)
sys.path.append(plugin_path)
# import msg_push_main as mp
# mp = mp.msg_push_main()

def get_specify_conf(value):
    conf = json.loads(public.readFile("{}/config.json".format(plugin_path)))
    conf_list = []
    if not conf:
        return {}
    try:
        for i in conf:
            if i['check_type'] == value and i['open'] == "1":
                conf_list.append(i)
        return conf_list
    except:
        return {}

def check(email_data, msg_push_cache):
    # 获取URL监控配置
    conf_list = get_specify_conf("url")
    if not conf_list:
        return
    print("开始监控URL")
    for conf in conf_list:
        msg_list = json.loads(public.readFile(msg_file))
        site_url = conf["site_check_url"]
        if conf['push_name'] not in msg_push_cache:
            print("初始化缓存...")
            msg_push_cache['{}_t'.format(conf['push_name'])] = 0
            msg_push_cache['url_msg'] = ""
            msg_push_cache['{}_err'.format(conf['push_name'])] = 0
            msg_push_cache['url_dict'] = {}
        check_site_health(conf,msg_push_cache)
        push_type = conf["push_type"]
        for u in msg_push_cache['url_dict']:
            url_err_n = 'url_err_times{}'.format(u)
            if not url_err_n in msg_push_cache:
                msg_push_cache[url_err_n] = 0
            if not msg_push_cache['url_dict'][u]:
                if msg_push_cache[url_err_n] < 5:
                    msg_push_cache[url_err_n] += 1
                    print(msg_push_cache[url_err_n])
                    continue
                even = "URL [  %s  ] 监控到访问异常" % site_url
                # print(even)
                evenmd5 = "sitemsg" + public.Md5(even)
                now = time.time()
                t = now - float(msg_push_cache['{}_t'.format(conf['push_name'])])
                push_time = int(conf["push_time"]) * 60
                if msg_push_cache['url_msg'] != evenmd5 and t >= push_time:
                    msg_push_cache['url_msg'] = evenmd5
                    msg_push_cache['{}_t'.format(conf['push_name'])] = now
                    # public.WriteLog('消息推送', even)
                    email_data["title"] = "URL监控异常"
                    data = {
                        "type":"resource",
                        "push_type":push_type,
                        "resource_type": "URL检测",
                        "status": "error",
                        "title": "URL访问异常通知!",
                        "site_url":site_url,
                        "msg": even  # 重启结果
                    }
                    # print("开始发送URL异常通知")
                    # mp.SendMsg(email_data, even, push_type)
                    msg_list.append(data)
                    public.writeFile(msg_file,json.dumps(msg_list))
                    msg_push_cache[url_err_n] = 0
                    msg_push_cache['{}_err'.format(conf['push_name'])] += 1
                    # print(msg_push_cache['url_err)
            else:
                print("error: {}".format(msg_push_cache['{}_err'.format(conf['push_name'])]))
                msg_push_cache[url_err_n] = 0
                if msg_push_cache['{}_err'.format(conf['push_name'])] != 0:
                    msg_push_cache['{}_err'.format(conf['push_name'])] = 0
                    msg_push_cache['url_msg'] = ""
                    even = "URL告警状态已经恢复正常 [ %s ]" % site_url
                    data = {
                        "type": "resource",
                        "resource_type": "CPU",  # 停止的服务
                        "status": "success",
                        "title": "URL访问恢复通知",
                        "push_type":push_type,
                        "msg": even
                        }
                    msg_list.append(data)
                    # email_data["title"] = "CPU异常恢复正常"
                    public.writeFile(msg_file, json.dumps(msg_list))
                    # print(even)
                    # email_data["title"] = even
                    # public.WriteLog('消息推送', even)
                    # mp.SendMsg(email_data, even, push_type)

# 检查站点健康
def check_site_health(i,msg_push_cache):
    site_check_word = i["site_check_word"]
    site_check_url = i["site_check_url"]
    try:
        site_data = requests.get(site_check_url,timeout=5)
        site_data.encoding = 'utf-8'
        msg_push_cache['url_dict'][site_check_url] = site_check_word in site_data.text
    except:
        msg_push_cache['url_dict'][site_check_url] = False