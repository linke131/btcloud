#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: zhw <zhw@bt.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   本地网站监控
#+--------------------------------------------------------------------

import time
import public
import sys
import requests
import threading
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
    # 获取本地网站监控配置
    conf_list = get_specify_conf("site")
    if not conf_list:
        return
    print('开始监控本地网站')
    for conf in conf_list:
        msg_list = json.loads(public.readFile(msg_file))
        if "site_t" not in msg_push_cache:
            msg_push_cache['{}_t'.format(conf['push_name'])] = 0
            msg_push_cache['site_msg'] = ""
            msg_push_cache['{}_err'.format(conf['push_name'])] = 0
            # msg_push_cache['site_url_dict = {}
            msg_push_cache['site_dict'] = {}
        threading_check(conf,msg_push_cache)
        l = []
        l.append(conf["url_list"])
        push_type = conf["push_type"]
        # if conf["adv"] == "1":
        #     while len(msg_push_cache['site_url_dict) != len(l):
        #         time.sleep(0.5)
        # else:
        while len(msg_push_cache['site_dict']) != 3:
            time.sleep(0.5)

        # if msg_push_cache['site_dict:
        a = msg_push_cache['site_dict']
        # else:
        #     a = msg_push_cache['site_url_dict
        for s in a.keys():
            if a['status_code'] != 200 or not a['key']:
                even = "站点 [  %s  ] 监控到访问异常" % a['site']
                evenmd5 = "localsitemsg" + public.Md5(even)
                now = time.time()
                t = now - float(msg_push_cache['{}_t'.format(conf['push_name'])])
                push_time = int(conf["push_time"]) * 60
                if msg_push_cache['site_msg'] != evenmd5 and t >= push_time:
                    msg_push_cache['site_msg'] = evenmd5
                    msg_push_cache['{}_t'.format(conf['push_name'])] = now
                    data = {
                        "type":"resource",
                        "push_type":push_type,
                        "resource_type": a['site'],
                        "status": "error",
                        "title": "网站异常通知!",
                        "msg": even  # 重启结果
                    }
                    # public.WriteLog('消息推送', even)
                    # email_data["title"] = even
                    # mp.SendMsg(email_data, even, push_type)
                    msg_list.append(data)
                    public.writeFile(msg_file,json.dumps(msg_list))
                    msg_push_cache['site_err'] += 1
            else:
                if msg_push_cache['{}_err'.format(conf['push_name'])] != 0:
                    msg_push_cache['{}_err'.format(conf['push_name'])] = 0
                    msg_push_cache['site_msg'] = ""
                    msg_push_cache['site_dict'] = {}
                    even = "站点告警状态已经恢复正常 [ %s ]" % a['site']
                    data = {
                        "type":"resource",
                        "push_type":push_type,
                        "resource_type": a['site'],
                        "status": "success",
                        "title": "网站恢复通知!",
                        "msg": even  # 重启结果
                    }
                    msg_list.append(data)
                    public.writeFile(msg_file,json.dumps(msg_list))
                    # email_data["title"] = even
                    # public.WriteLog('消息推送', even)
                    # mp.SendMsg(email_data, even, push_type)

def threading_check(conf,msg_push_cache):
    if conf["adv"] == "1":
        t = threading.Thread(target=check_site_health, args=(conf,msg_push_cache))
        t.start()
    else:
        u = conf['url_list']
        t = threading.Thread(target=check_local_site_health, args=(u,msg_push_cache))
        t.start()

# 检查站点健康
def check_site_health(conf,msg_push_cache):
    site_check_word = conf["key"]
    site_check_url = "http://" + conf["url_list"]
    try:
        site_data = requests.get(site_check_url,timeout=5)
        site_data.encoding = 'utf-8'
        msg_push_cache['site_dict']['key'] = site_check_word in site_data.text
        msg_push_cache['site_dict']['status_code'] = site_data.status_code
        msg_push_cache['site_dict']['site'] = site_check_url
    except:
        msg_push_cache['site_dict']['site'] = site_check_url
        msg_push_cache['site_dict']['key'] = False
        msg_push_cache['site_dict']['status_code'] = 'error'

def check_local_site_health(url,msg_push_cache):
    url = "http://"+url
    try:
        a = requests.get(url, timeout=5)
        msg_push_cache['site_dict']['site'] = url
        msg_push_cache['site_dict']['status_code'] = a.status_code
        msg_push_cache['site_dict']['key'] = True
    except:
        msg_push_cache['site_dict']['site'] = url
        msg_push_cache['site_dict']['status_code'] = "error"
        msg_push_cache['site_dict']['key'] = False