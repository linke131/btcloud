#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: zhw <zhw@bt.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   内存监控
#+--------------------------------------------------------------------

import time
import public
import sys
import psutil
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
    if not conf:
        return {}
    try:
        for i in conf:
            if i['check_type'] == value and i['open'] == "1":
                return i
    except:
        return {}

def check(email_data, msg_push_cache):
    # 获取内存监控配置
    conf = get_specify_conf("mem")
    if not conf:
        return
    print("开始监控内存...")
    msg_list = json.loads(public.readFile(msg_file))
    starttime = time.time() - int(conf["check_time"]) * 60
    mem_data = get_mem_io(starttime)
    memsum = 0
    for mem in mem_data:
        memsum += int(mem["mem"])
    mem_avg = memsum / len(mem_data)
    push_type = conf["push_type"]
    if "mem_t" not in msg_push_cache:
        print("开始初始化内存监控缓存...")
        msg_push_cache['mem_t'] = 0
        msg_push_cache['mem_msg'] = ""
        msg_push_cache['mem_err'] = 0
        msg_push_cache['mem_process'] = {}
    if int(conf["alarm_value"]) <= mem_avg:
        evenmd5 = "memmsg" + public.Md5(str(mem_avg))
        now = time.time()
        t = now - float(msg_push_cache['mem_t'])
        push_time = int(conf["push_time"]) * 60
        if msg_push_cache['mem_msg'] != evenmd5 and t >= push_time:
            mxp = get_process_mem_percent(msg_push_cache)
            even = "内存已经使用[  %d%s  ]超过设定阈值，其中【%s】进程占用内存最高，占用率为 %sMB" % (mem_avg, "%", mxp[0], mxp[1])
            data = {
                "type": "resource",
                "push_type": push_type,
                "resource_type": "内存",
                "usage": round(mem_avg,2),
                "process": mxp[0].split("/")[-1],
                "usage_process": round(mxp[1],2),
                "status": "error",
                "title": "【内存】异常通知!",
                "msg": even  # 重启结果
            }
            msg_push_cache['mem_msg'] = evenmd5
            msg_push_cache['mem_t'] = now
            # public.WriteLog('消息推送', even)
            # email_data["title"] = "内存监控异常"
            # mp.SendMsg(email_data, even, push_type)
            msg_list.append(data)
            public.writeFile(msg_file, json.dumps(msg_list))
            msg_push_cache['mem_err'] += 1
            # 判断告警方式发送消息
    else:
        if msg_push_cache['mem_err'] != 0:
            msg_push_cache['mem_err'] = 0
            msg_push_cache['mem_msg'] = ""
            even = "内存告警状态已经恢复正常"
            data = {
                "type": "resource",
                "push_type": push_type,
                "resource_type": "内存",
                "status": "success",
                "title": "【内存】恢复通知!",
                "msg": even  # 重启结果
            }
            msg_list.append(data)
            public.writeFile(msg_file, json.dumps(msg_list))
            # email_data["title"] = "内存告警状态已经恢复正常"
            # mp.SendMsg(email_data, even, push_type)
            # public.WriteLog('消息推送', even)

# 监控MEMIO
def get_mem_io(starttime):
    # 取指定时间段的CpuIo
    data = public.M('cpuio').dbfile('system').where("addtime>=? AND addtime<=?",(starttime, time.time())).field('id,pro,mem').order('id asc').select()
    return data

# 取占用内存最高的进程
def get_process_mem_percent(msg_push_cache):
    msg_push_cache['mem_process'] = {}
    for i in psutil.pids():
        # time.sleep(0.2)
        threading.Thread(target=get_process_mem,args=(i,msg_push_cache)).start()
    # time.sleep(10)
    maxk = max(msg_push_cache['mem_process'],key=msg_push_cache['mem_process'].get)
    if maxk == "gunicorn":
        del(msg_push_cache['mem_process'][maxk])
    maxk = max(msg_push_cache['mem_process'], key=msg_push_cache['mem_process'].get)
    return [maxk,msg_push_cache['mem_process'][maxk]]

# 取进程占用的CPU
def get_process_mem(i,msg_push_cache):
    try:
        pp = psutil.Process(i)
        if pp.name() not in msg_push_cache['mem_process'].keys():
            msg_push_cache['mem_process'][pp.name()] = float(pp.memory_info().rss / 1024 / 1024)
            return
        msg_push_cache['mem_process'][pp.name()]+=float(pp.memory_info().rss / 1024 / 1024)
    except:
        pass