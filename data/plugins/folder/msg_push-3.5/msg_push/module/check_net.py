#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: zhw <zhw@bt.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   网络监控
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

def check(email_data, msg_push_cache):
    try:
        # 获取宽带监控配置
        conf = get_specify_conf("net")
        if not conf:
            return
        print("开始监控网卡流量...")
        msg_list = json.loads(public.readFile(msg_file))
        ct = int(conf["check_time"])
        nb = int(conf["net_bandwidth"])
        nv = int(conf["alarm_value"])
        push_time = int(conf["push_time"])
        if "network_t" not in msg_push_cache:
            print("开始初始化带宽缓存...")
            msg_push_cache['network_t'] = 0
            msg_push_cache['network_msg'] = ""
            msg_push_cache['network_err'] = 0
            msg_push_cache['r_tmp_list'] = []
            msg_push_cache['t_tmp_list'] = []
            msg_push_cache['r_list'] = []
            msg_push_cache['t_list'] = []
        cache_t = float(msg_push_cache['network_t'])
        if "netcard" not in conf.keys():
            conf["netcard"] = "lo"
        net_tmp = psutil.net_io_counters(pernic=True)
        print(net_tmp)
        r_tmp = net_tmp[conf["netcard"]].bytes_recv
        t_tmp = net_tmp[conf["netcard"]].bytes_sent
        push_type = conf["push_type"]
        # r_list = []
        # t_list = []
        # r_tmp_list = []
        # t_tmp_list = []
        if len(msg_push_cache['r_tmp_list']) < 2:
            msg_push_cache['r_tmp_list'].append(r_tmp)
        else:
            msg_push_cache['r_tmp_list'].pop(0)
            msg_push_cache['r_tmp_list'].append(r_tmp)
        if len(msg_push_cache['t_tmp_list']) < 2:
            msg_push_cache['t_tmp_list'].append(t_tmp)
        else:
            msg_push_cache['t_tmp_list'].pop(0)
            msg_push_cache['t_tmp_list'].append(t_tmp)
        r = int(msg_push_cache['r_tmp_list'][-1]) - int(msg_push_cache['r_tmp_list'][-2])
        t = int(msg_push_cache['t_tmp_list'][-1]) - int(msg_push_cache['t_tmp_list'][-2])
        if len(msg_push_cache['r_list']) > ct:
            msg_push_cache['r_list'].pop(0)
        if len(msg_push_cache['t_list']) > ct:
            msg_push_cache['t_list'].pop(0)
        msg_push_cache['r_list'].append(r)
        msg_push_cache['t_list'].append(t)
        rsum = 0
        tsum = 0

        for i in msg_push_cache['r_list']:
            rsum += i
        for i in msg_push_cache['t_list']:
            tsum += i
        rsum = rsum / 1024 / ct
        tsum = tsum / 1024 / ct
        net_bandwidth = nb * 1024 * nv / 100
        if rsum >= net_bandwidth and tsum >= net_bandwidth:
            d = "上行带宽 %.2fKB 下行带宽 %.2fKB" % (tsum, rsum)
            even = "带宽已经使用[ %s ]超过设定阈值" % d
            evenmd5 = "netmsg" + public.Md5(even)
            now = time.time()
            t = now - cache_t
            push_time = push_time * 60
            if msg_push_cache['network_msg'] != evenmd5 and t >= push_time:
                msg_push_cache['network_msg'] = evenmd5
                msg_push_cache['network_t'] = now
                data = {
                    "type": "resource",
                    "resource_type": "带宽",  # 停止的服务
                    "status": "error",
                    "tx": tsum,
                    "rx": rsum,
                    "title": "【带宽】异常通知！",
                    "push_type":push_type,
                    "msg": even
                    }
                # public.WriteLog('消息推送', even)
                # email_data["title"] = "带宽监控异常"
                # mp.SendMsg(email_data, even, push_type)
                msg_list.append(data)
                public.writeFile(msg_file,json.dumps(msg_list))
                msg_push_cache['network_err'] += 1
        else:
            if msg_push_cache['network_err'] != 0:
                msg_push_cache['network_err'] = 0
                msg_push_cache['network_msg'] = ""
                even = "带宽告警状态已经恢复正常"
                data = {
                    "type": "resource",
                    "resource_type": "带宽",  # 停止的服务
                    "status": "success",
                    "title": "【带宽】恢复通知！",
                    "push_type":push_type,
                    "msg": even
                    }
                msg_list.append(data)
                public.writeFile(msg_file,json.dumps(msg_list))
                # print(even)
                # email_data["title"] = "带宽告警状态已经恢复正常"
                # mp.SendMsg(email_data, even, push_type)
                # public.WriteLog('消息推送', "带宽告警状态已经恢复正常")
    except:
        print(public.get_error_info())

# 检测网络用量
def GetNetWorkIo(self, starttime):
    #取指定时间段的网络Io
    data =  public.M('network').dbfile('system').where("addtime>=? AND addtime<=?",(starttime,time.time())).field('id,up,down').order('id asc').select()
    return data