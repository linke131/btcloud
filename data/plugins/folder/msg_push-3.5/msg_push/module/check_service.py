#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: zhw <zhw@bt.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|  服务状态
#+--------------------------------------------------------------------
import time
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
    # 监控常用服务的状态
    conf_list = get_specify_conf("service") #{"open": "1", "push_name": "fdsa", "push_type": "mail", "check_type": "service", "push_time": "10","check_time": "4","service":["nginx","redis"],"act":"1"}
    if not conf_list:
        return
    print("开始监控services")
    print(conf_list)
    for conf in conf_list:
        msg_list = json.loads(public.readFile(msg_file))
        service_list = json.loads(public.readFile("{}/service.conf".format(plugin_path)))
        service_list_exist = []
        for i in conf['services']:
            if i not in [i['check_name'] for i in service_list]:
                print("此服务还未适配 {}".format(i))
                public.WriteLog("消息推送", "此服务还未适配 {}".format(i))
            else:
                service_list_exist.append(i)
        if not service_list_exist:
            print("没有找到能够监控的服务！")
            return
        if conf['push_name'] not in msg_push_cache:
            print("开始初始化services缓存...")
            msg_push_cache[conf['push_name']] = 0
            msg_push_cache['service_up'] = []
        service_down = []
        service_status_list = {}
        push_type = conf["push_type"]
        for i in service_list_exist:
            path = [s['path'] for s in service_list if i == s['check_name']][0]
            service = [s['service'] for s in service_list if i == s['check_name']][0]
            if service in ['redis']:
                service_status_list[i] = public.process_exists(i, path)
            elif "php-" in service:
                service_status_list[i] = get_php_status(i[-2:])
            else:
                print(service,path)
                service_status_list[i] = public.process_exists(service,path)
        print(service_status_list)
        for service_status in service_status_list:
            if not service_status_list[service_status]:
                service_down.append(service_status)
        print(service_down)
        if service_down:
            now = time.time()
            t = now - float(msg_push_cache[conf['push_name']])
            push_time = int(conf["push_time"]) * 60
            if t >= push_time:
                even = {
                    "type": "service",
                    "push_type": push_type,
                    "service":",".join(service_down),  #停止的服务
                    "status":"error",
                    "resource_type":"",
                    "title":"服务异常通知！",
                    "restart":"是" if conf['act'] == '1' else "否",  #是否需要重启
                    "restart_success":[],  #重启结果
                    "restart_fail": []  # 重启结果
                }
                if conf['act'] == '1':
                    even = restart_service(service_down,msg_push_cache,service_list,even)
                msg_push_cache[conf['push_name']] = now
                title = "{} 服务监控异常".format(','.join(service_down))
                even['title'] = title
                even['restart_success'] = ",".join(even['restart_success'])
                msg_list.append(even)
                public.writeFile(msg_file, json.dumps(msg_list))
                print(msg_push_cache['service_up'])
                # content = get_msg_format(even,push_type)
                # mp.SendMsg(email_data, content, push_type, even)
                # msg_push_cache['service_err += 1
                # self.ed[service] = self.service_error_code
                # 判断告警方式发送消息
        else:
            print(msg_push_cache['service_up'])
            if msg_push_cache['service_up']:
                service_up = ",".join(msg_push_cache['service_up'])
                even = "\n【{}】服务告警状态已经恢复正常".format(service_up)
                even = {
                    "type": "service",
                    "push_type": push_type,
                    "service":service_up,  #停止的服务
                    "resource_type":service_up,
                    "status":"success",
                    "title": even,
                    "msg":even
                }
                # content = get_msg_format(even,push_type,status='success')
                # email_data["title"] = "服务【{}】告警状态已经恢复正常".format(",".join(msg_push_cache['service_up))
                msg_push_cache['service_up'] = []
                msg_push_cache[conf['push_name']] = 0
                # mp.SendMsg(email_data, content, push_type, even)
                msg_list.append(even)
                print(msg_list)
                public.writeFile(msg_file, json.dumps(msg_list))
                # public.WriteLog('消息推送', even)

def restart_service(service_down,msg_push_cache,service_list,even):
    for i in service_down:
        service = [s['service'] for s in service_list if i == s['check_name']][0]
        path = [s['path'] for s in service_list if i == s['check_name']][0]
        if "php-" in service:
            public.ExecShell('/etc/init.d/{} restart'.format(i))
        else:
            print('systemctl restart {}'.format(service))
            public.ExecShell('systemctl restart {}'.format(service))

        time.sleep(3)

        if service in ["redis"]:
            process = public.process_exists(i,path)
        elif "php-" in service:
            process = get_php_status(i[-2:])
        else:
            process = public.process_exists(service, path)

        if process:
            even['restart_success'].append(i)
            msg_push_cache['service_up'].append(i)
        else:
            # even += "\n\n服务【{}】重新启动失败，请手动检查！".format(i)
            even['restart_fail'].append(i)
    return even

def get_php_status(phpversion):
    import os
    '''
        @name 获取指定PHP版本的服务状态
        @author hwliang<2020-10-23>
        @param phpversion string PHP版本
        @return bool
    '''
    try:
        php_status = os.path.exists('/tmp/php-cgi-'+phpversion+'.sock')
        if php_status: return php_status
        pid_file = '/www/server/php/{}/var/run/php-fpm.pid'.format(phpversion)
        if not os.path.exists(pid_file): return False
        pid = int(public.readFile(pid_file))
        return os.path.exists('/proc/{}/comm'.format(pid))
    except:
        return False