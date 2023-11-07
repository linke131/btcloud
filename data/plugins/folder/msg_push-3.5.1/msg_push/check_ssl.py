#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: zhw <zhw@bt.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   监控SSL到期时间
#+--------------------------------------------------------------------


import public
import sys
import json
panel_path = "/www/server/panel"
plugin_path = "{}/plugin/msg_push".format(panel_path)
msg_file = '{}/msg.json'.format(plugin_path)
sys.path.append(plugin_path)
# import msg_push_main as mp
# mp = mp.msg_push_main()

def get_specify_conf(value):
    conf = json.loads(public.readFile("{}/config.json".format(plugin_path)))
    if not conf:
        return {}
    try:
        for i in conf:
            if i['check_type'] == value and i['open'] == "1":
                return i
    except:
        return {}

def check(email_data, msg_push_cache):
    # 获取SSL到期时间监控配置
    conf = get_specify_conf("check_ssl_expired")
    if not conf:
        return
    print("开始监控 SSL 到期时间...")
    msg_list = json.loads(public.readFile(msg_file))
    if "ssl_t" not in msg_push_cache:
        print("开始初始化SSL缓存...")
        msg_push_cache['ssl_t'] = 0
        msg_push_cache['ssl_msg'] = False
    if get_check_time(conf):
        msg_push_cache['ssl_t'] = ''
        msg = "还未到检测时间！"
        print(msg)
        return msg
    if msg_push_cache['ssl_msg'] == False:
        sites = get_all_name_of_sites()
        push_type = conf["push_type"]
        import data
        d = data.data()
        even = '<br>'
        for site_info in sites:
            site_name = site_info['site_name']
            if str(site_info['status']) == "0":
                print("网站已经被暂停跳过：{}".format(site_name))
                continue
            ssl_info = d.get_site_ssl_info(site_name)
            if str(ssl_info) == '-1':
                continue
            if not int(ssl_info['endtime']) <= int(conf['check_time']):
                continue
            tmp = "监控到网站 [ {} ] 的SSL就要过期了，过期时间是：{}天后".format(site_name, int(ssl_info['endtime']))
            public.WriteLog('消息推送', tmp)
            even += tmp + '<br>'
        if even == '<br>':
            return '没有检查到即将过期的证书'
        even = {
            "type": "resource",
            "push_type": push_type,
            "resource_type": "SSL证书",
            "status": "error",
            "title": "【SSL证书】到期通知",
            "msg": even  # 重启结果
        }
        msg_list.append(even)
        public.writeFile(msg_file, json.dumps(msg_list))
        # email_data["title"] = "监控到有网站SSL即将到期！"
        #
        # mp.SendMsg(email_data, even, push_type)
        msg_push_cache['ssl_msg'] = True

def get_check_time(i):
    try:
        if int(i['report']) < 10:
            i['report'] = "0" + str(i['report'])
    except:
        i['report'] = "09"
    if not GetTime("hour") == i['report']:
        return True

def GetTime(time):
    import datetime
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

# 获取站点名称
def get_all_name_of_sites():
    sites = []
    getsites = public.M('sites').select()
    for s in getsites:
        sites.append({"site_name":s["name"],"status":s["status"]})
    return sites