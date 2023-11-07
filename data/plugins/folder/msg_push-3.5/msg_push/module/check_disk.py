#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: zhw <zhw@bt.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   硬盘监控
#+--------------------------------------------------------------------

import time
import public
import sys
import re
import os
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
    # 获取磁盘监控配置
    conf = get_specify_conf("disk")
    if not conf:
        return
    print("开始监控磁盘")
    msg_list = json.loads(public.readFile(msg_file))
    hd_data = get_hd_use()
    inode_data = get_inode_use()
    push_type = conf["push_type"]
    if "disk_t" not in msg_push_cache:
        msg_push_cache['disk_t'] = 0
        msg_push_cache['disk_msg'] = ""
        msg_push_cache['disk_err'] = 0
        msg_push_cache['disk_err_list'] = {}
    for keys in hd_data:
        use = int(hd_data[keys])
        inode_use = int(inode_data[keys])
        c_use = int(conf["alarm_value"])

        if use >= c_use or inode_use >= c_use:
            evenmd5 = "diskmsg" + public.Md5(str(use))
            now = time.time()
            t = now - float(msg_push_cache['disk_t'])
            push_time = int(conf["push_time"]) * 60
            if msg_push_cache['disk_msg'] != evenmd5 and t >= push_time:
                disk_data = '  %s  目录已经使用 %s%s 空间，inode 已经使用 %s%s' % (keys, use, "%", inode_use, "%")
                msg_push_cache['disk_msg'] = evenmd5
                msg_push_cache['disk_t'] = now
                even = "磁盘已经使用[  %s  ]超过设定阈值" % disk_data
                public.WriteLog('消息推送', even)
                email_data["title"] = "磁盘监控异常"
                data = {
                    "type":"resource",
                    "push_type":push_type,
                    "usage": use,
                    "inode_usage": inode_use,
                    "partition": keys,
                    "resource_type": "磁盘",
                    "status": "error",
                    "title": "磁盘异常通知!",
                    "msg": even # 重启结果
                }
                msg_list.append(data)
                public.writeFile(msg_file, json.dumps(msg_list))
                # mp.SendMsg(email_data, even, push_type)
                msg_push_cache['disk_err'] += 1
                msg_push_cache['disk_err_list'][keys] = msg_push_cache['disk_err']
                # 判断告警方式发送消息
        else:
            try:
                if msg_push_cache['disk_err_list'][keys] != 0:
                    msg_push_cache['disk_err_list'][keys] = 0
                    msg_push_cache['disk_msg'] = ""
                    even = "磁盘告警状态已经恢复正常"
                    data = {
                        "type": "resource",
                        "push_type": push_type,
                        "resource_type": "磁盘",
                        "status": "success",
                        "title": "磁盘占用恢复通知!",
                        "msg": even  # 重启结果
                    }
                    email_data["title"] = "磁盘告警状态已经恢复正常"
                    msg_list.append(data)
                    public.writeFile(msg_file, json.dumps(msg_list))
                    # mp.SendMsg(email_data, even, push_type)
                    # public.WriteLog('消息推送', even)
            except:
                msg_push_cache['disk_err_list'][keys] = 0

# 检测硬盘使用
def get_hd_use():
        cmd_get_hd_use = '/bin/df'
        try:
            fp = os.popen(cmd_get_hd_use)
        except:
            ErrorInfo = r'get_hd_use_error'
            return ErrorInfo
        re_obj = re.compile(r'^/dev/.+\s+(?P<used>\d+)%\s+(?P<mount>.+)')
        hd_use = {}
        for line in fp:
            match = re_obj.search(line)
            if match:
                hd_use[match.groupdict()['mount']] = match.groupdict()['used']
        fp.close()
        return hd_use
# 返回{'/www/wwwroot/www_youbadbad_cn/files': '6', '/boot': '14', '/': '61'}


def get_inode_use():
    cmd_get_hd_use = '/bin/df -i'
    try:
        fp = os.popen(cmd_get_hd_use)
    except:
        ErrorInfo = r'get_hd_use_error'
        return ErrorInfo
    re_obj = re.compile(r'^/dev/.+\s+(?P<used>\d+)%\s+(?P<mount>.+)')
    hd_use = {}
    for line in fp:
        match = re_obj.search(line)
        if match:
            hd_use[match.groupdict()['mount']] = match.groupdict()['used']
    fp.close()
    return hd_use