#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: zhw <zhw@bt.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   CPU监控
#+--------------------------------------------------------------------

import time
import public
import sys
import psutil
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

# CPU监控代码
def check(email_data, msg_push_cache):
    # 获取CPU监控配置
    conf = get_specify_conf("cpu")
    if not conf:
        return
    # 检查cpu负载
    print("开始监控CPU")
    msg_list = json.loads(public.readFile(msg_file))
    try:
        starttime = time.time() - int(conf["check_time"]) * 60
        cpu_data = get_cpu_io(starttime)
        cpusum = 0
        for cpuio in cpu_data:
            cpusum += int(cpuio["pro"])
        cpu_avg = cpusum / len(cpu_data)
        push_type = conf["push_type"]
        if "cpu_t" not in msg_push_cache:
            msg_push_cache['cpu_t'] = 0
            msg_push_cache['cpu_msg'] = ""
            msg_push_cache['cpu_err'] = 0
        if int(conf["alarm_value"]) <= cpu_avg:
            evenmd5 = "cpu_msg" + public.Md5(str(cpu_avg))
            now = time.time()
            t = now - float(msg_push_cache['cpu_t'])
            push_time = int(conf["push_time"]) * 60
            if msg_push_cache['cpu_msg'] != evenmd5 and t >= push_time:
                mxp = get_max_cpu_program()
                msg_push_cache['cpu_t'] = now
                msg_push_cache['cpu_msg'] = evenmd5
                log_even = "CPU当前使用已超过[  %.2f%s  ]，其中【%s】进程占用cpu最高，占用率为 %.2f%s 请及时排查。" % (
                cpu_avg, "%", mxp[0], float(mxp[1]) / int(psutil.cpu_count()), "%")
                even = {
                    "type":"resource",
                    "push_type":push_type,
                    "resource_type": "CPU",
                    "status": "error",
                    "usage": cpu_avg,
                    "usage_process": float(mxp[1]) / int(psutil.cpu_count()),
                    "process": mxp[0].split('/')[-1],
                    "title": "CPU占用异常通知!",
                    "msg": log_even  # 重启结果
                }
                # content = get_msg_format(even,push_type)
                public.WriteLog('消息推送', log_even)
                # 判断告警方式发送消息
                # email_data["title"] = "CPU异常通知!"
                msg_list.append(even)
                public.writeFile(msg_file,json.dumps(msg_list))
                # mp.SendMsg(email_data, content, push_type, even)

                msg_push_cache['cpu_err'] += 1

        else:
            if msg_push_cache['cpu_err'] != 0:
                msg_push_cache['cpu_err'] = 0
                msg_push_cache['cpu_msg'] = ""
                # even_log = "cpu 告警状态已经恢复正常"
                even = {
                    "type": "resource",
                    "resource_type": "CPU",  # 停止的服务
                    "status": "success",
                    "title": "CPU占用恢复正常",
                    "push_type":push_type,
                    "msg": "cpu 告警状态已经恢复正常"
                    }
                # content = get_msg_format(even,push_type,status='success')
                msg_list.append(even)
                email_data["title"] = "CPU异常恢复正常"
                public.writeFile(msg_file, json.dumps(msg_list))
                # public.WriteLog('消息推送', even_log)
                # mp.SendMsg(email_data, content, push_type, even)
    except:
        print("出错了！！！{}".format(public.get_error_info()))
        public.WriteLog("消息推送", "".format(public.get_error_info()))

# 监控CPUIO
def get_cpu_io(starttime):
    # 取指定时间段的CpuIo
    data = public.M('cpuio').dbfile('system').where("addtime>=? AND addtime<=?",(starttime, time.time())).field('id,pro,mem').order('id asc').select()
    return data

def get_max_cpu_program():
    result = public.ExecShell("ps -aux | sort -k3nr | head -1")
    cpu_percend = result[0].split()[2]
    try:
        program_name = result[0].split(':')[2][3:-1]
    except:
        program_name = result[0].split(':')[1][3:-1]
    return [program_name,cpu_percend]