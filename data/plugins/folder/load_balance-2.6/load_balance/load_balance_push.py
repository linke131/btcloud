# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 宝塔软件(https://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <baozi@bt.cn>
# | Author: baozi
# +-------------------------------------------------------------------
import os, json, sys
from datetime import datetime

import public, panelPush, time
# from push.base_push import base_push

try:
    sys.path.insert(0, "{}/plugin".format(public.get_panel_path()))
    from load_balance.load_balance_main import Server, UpStream, Node
except:
    Server, UpStream, Node = None, None, None


class base_push:

    # 版本信息 目前无作用
    def get_version_info(self, get=None):
        raise NotImplementedError

    # 格式化返回执行周期， 目前无作用
    def get_push_cycle(self, data: dict):
        return data

    # 获取模块推送参数
    def get_module_config(self, get: public.dict_obj):
        raise NotImplementedError

    # 获取模块配置项
    def get_push_config(self, get: public.dict_obj):
        # 其实就是配置信息，没有也会从全局配置文件push.json中读取
        raise NotImplementedError

    # 写入推送配置文件
    def set_push_config(self, get: public.dict_obj):
        raise NotImplementedError

    # 删除推送配置
    def del_push_config(self, get: public.dict_obj):
        # 从配置中删除信息，并做一些您想做的事，如记日志
        raise NotImplementedError

    # 无意义？？？
    def get_total(self):
        return True

    # 检查并获取推送消息，返回空时，不做推送, 传入的data是配置项
    def get_push_data(self, data, total):
        # data 内容
        # index :  时间戳 time.time()
        # 消息 以类型为key， 以内容为value， 内容中包含title 和msg
        # push_keys： 列表，发送了信息的推送任务的id，用来验证推送任务次数（） 意义不大
        raise NotImplementedError

class load_balance_push(base_push):
    __push_conf = "{}/class/push/push.json".format(public.get_panel_path())
    __task_template = "{}/class/push/scripts/load_balance_push.json".format(public.get_panel_path())

    def __init__(self) -> None:
        self.__push = panelPush.panelPush()
        self._tip_counter = None
        self._push_counter = None

    # 版本信息 目前无作用
    def get_version_info(self, get=None):
        data = {}
        data['ps'] = '宝塔负载均衡告警'
        data['version'] = '1.0'
        data['date'] = '2023-05-25'
        data['author'] = '宝塔'
        data['help'] = 'http://www.bt.cn/bbs'
        return data

    # 获取模块推送参数
    def get_module_config(self, get: public.dict_obj):
        data = []
        item = self.__push.format_push_data(push=["mail", 'dingding', 'weixin', "feishu", "wx_account"],
                                            project='load_balance', type='')
        item['cycle'] = 30
        item['title'] = '负载均衡'
        data.append(item)
        return data

    # 获取模块配置项
    def get_push_config(self, get: public.dict_obj):
        id = get.id
        # 其实就是配置信息，没有也会从全局配置文件push.json中读取
        push_list = self.__push._get_conf()

        if id not in push_list["load_balance_push"]:
            res_data = public.returnMsg(False, '未找到指定配置.')
            res_data['code'] = 100
            return res_data
        result = push_list["load_balance_push"][id]
        return result

    # 写入推送配置文件
    def set_push_config(self, get: public.dict_obj):
        load_push_id = get.id
        pdata = json.loads(get.data)
        all_upstream_name = UpStream.SQL().field("name").select()
        all_upstream_name = [i["name"] for i in all_upstream_name]
        if not bool(all_upstream_name):
            return public.returnMsg(False, '没有负载均衡配置，无法设置告警')
        if pdata["project"] not in all_upstream_name and pdata["project"] != "all":
            return public.returnMsg(False, '没有该负载均衡配置，无法设置告警')
        conf_data = self.__push._get_conf()
        if "load_balance_push" not in conf_data:
            conf_data["load_balance_push"] = {}
        cycle = []
        for i in pdata["cycle"].split("|"):
            if bool(i) and i.isdecimal():
                code = int(i)
                if 100 <= code < 600:
                    cycle.append(str(code))
        if not bool(cycle):
            return public.returnMsg(False, '没有指定任何错误码，无法设置告警')
        cycle = "|".join(cycle)
        create = True
        for k, conf in conf_data["load_balance_push"].items():
            if conf["project"] == pdata["project"]:
                conf["cycle"] = cycle
                conf["interval"] = 60
                conf["module"] = pdata["module"]
                conf["push_count"] = pdata["push_count"]
                self._del_today_push_counter(k)
                create = False
        if create:
            pdata["status"] = True
            pdata["title"] = "所有已配置的负载" if pdata["project"] == "all" else pdata["project"]
            conf_data["load_balance_push"][load_push_id] = pdata
        return conf_data

    # 删除推送配置
    def del_push_config(self, get: public.dict_obj):
        # 从配置中删除信息，并做一些您想做的事，如记日志
        data = self.__push._get_conf()
        if "load_balance_push" not in data:
            data["load_balance_push"] = {}
        if "upstream_name" in get:
            u_name = get.upstream_name
            public.print_log(u_name)
            ids = []
            for k_id, conf in data["load_balance_push"].items():
                if conf["project"] == u_name:
                    ids.append(k_id)
            for i in ids:
                del data["load_balance_push"][i]
            public.print_log(ids)
            public.print_log(data)
        else:
            id = get.id
            if str(id).strip() in data["load_balance_push"]:
                del data["load_balance_push"][id]
        public.writeFile(self.__push_conf, json.dumps(data))

        return public.returnMsg(True, '删除成功.')

    # 无意义？？？
    def get_total(self):
        return True

    # 检查并获取推送消息，返回空时，不做推送, 传入的data是配置项
    def get_push_data(self, data, total):
        # 返回内容
        # index :  时间戳 time.time()
        # 消息 以类型为key， 以内容为value， 内容中包含title 和msg
        # push_keys： 列表，发送了信息的推送任务的id，用来验证推送任务次数（） 意义不大
        """
        @检测推送数据
        @data dict 推送数据
            title:标题
            count:触发次数
            cycle:周期 天、小时
            keys:检测键值
        """
        if self._get_today_push_counter(data["id"]) >= data["push_count"]:
            return None
        err_nodes = self._check_func(data["project"], data["cycle"])
        if not err_nodes:
            return None
        result = {'index': time.time(), }
        pj = "负载均衡:【{}】".format(data["project"]) if data["project"] != "all" else "所有负载均衡"
        nodes = '、'.join(err_nodes)
        for m_module in data['module'].split(','):
            if m_module == 'sms':
                continue
            s_list = [
                ">通知类型：企业版负载均衡告警",
                ">告警内容：<font color=#ff0000>{}配置下的节点【{}】出现访问错误，请及时关注节点情况并处理。</font> ".format(pj, nodes),
            ]
            sdata = public.get_push_info('企业版负载均衡告警', s_list)
            result[m_module] = sdata
        self._set_today_push_counter(data["id"])
        return result

    def _check_func(self, upstream_name: str, codes: str) -> list:
        if upstream_name == "all":
            upstreams = UpStream.SQL().all()
        else:
            upstream = UpStream.SQL().get_by_name(upstream_name)
            upstreams = []
            if upstream is not None:
                upstreams.append(upstream)
        if not upstreams:
            return []
        access_codes = [int(i) for i in codes.split("|") if bool(i.strip())]
        res_list = []
        for upstream in upstreams:
            res = upstream.check_nodes(access_codes, return_nodes=True)
            for ping_url in res:
                if ping_url in self.tip_counter:
                    self.tip_counter[ping_url].append(int(time.time()))
                    idx = 0
                    for i in self.tip_counter[ping_url]:
                        if time.time() - i > 60 * 4:
                            idx += 1
                    self.tip_counter[ping_url] = self.tip_counter[ping_url][idx:]
                    if len(self.tip_counter[ping_url]) >= 3:
                        res_list.append(ping_url)
                        self.tip_counter[ping_url] = []
                else:
                    self.tip_counter[ping_url] = [int(time.time()), ]
        self.save_tip_counter()
        return res_list

    @property
    def tip_counter(self) -> dict:
        if self._tip_counter is not None:
            return self._tip_counter
        tip_counter = '{}/data/push/tips/load_balance_push.json'.format(public.get_panel_path())
        if os.path.exists(tip_counter):
            try:
                self._tip_counter = json.loads(public.readFile(tip_counter))
            except json.JSONDecodeError:
                self._tip_counter = {}
        else:
            self._tip_counter = {}
        return self._tip_counter

    def save_tip_counter(self):
        tip_counter = '{}/data/push/tips/load_balance_push.json'.format(public.get_panel_path())
        public.writeFile(tip_counter, json.dumps(self.tip_counter))

    @property
    def push_counter(self):
        if self._push_counter is not None:
            return self._push_counter
        else:
            today_push_counter = '{}/data/push/tips/load_balance_today.json'.format(public.get_panel_path())
            t_day = datetime.now().strftime('%Y-%m-%d')
            if os.path.exists(today_push_counter):
                tip = json.loads(public.readFile(today_push_counter))
                if tip["t_day"] != t_day:
                    tip = {"t_day": t_day}
            else:
                tip = {"t_day": t_day}
        self._push_counter = tip
        return self._push_counter

    def save_push_counter(self):
        today_push_counter = '{}/data/push/tips/load_balance_today.json'.format(public.get_panel_path())
        if self._push_counter is not None:
            public.writeFile(today_push_counter, json.dumps(self._push_counter))

    def _get_today_push_counter(self, task_id):
        if task_id in self.push_counter:
            res = self.push_counter[task_id]
        else:
            res = 0
        return res

    def _set_today_push_counter(self, task_id):
        if task_id in self.push_counter:
            self.push_counter[task_id] += 1
        else:
            self.push_counter[task_id] = 1
        self.save_push_counter()

    def _del_today_push_counter(self, task_id):
        if task_id in self.push_counter:
            del self.push_counter[task_id]
        self.save_push_counter()

    @staticmethod
    def _get_bak_task_template():
        return {
            "field": [
                {
                    "attr": "project",
                    "name": "负载名称",
                    "type": "select",
                    "default": "all",
                    "unit": "中的节点访问失败时，触发告警",
                    "items": [
                        {
                            "title": "所有已配置的负载",
                            "value": "all"
                        }
                    ]
                },
                {
                    "attr": "cycle",
                    "name": "访问成功的状态码包含:",
                    "type": "text",
                    "unit": "",
                    "default": "200|301|302|403|404"
                },
                {
                    "attr": "push_count",
                    "name": "每个负载均衡配置发送",
                    "type": "number",
                    "unit": "次后，当日不再发送，次日恢复",
                    "default": 2
                }
            ],
            "sorted": [
                [
                    "project"
                ],
                [
                    "cycle"
                ],
                [
                    "push_count"
                ]
            ],
            "type": "load_balance_push",
            "module": [
                "wx_account",
                "dingding",
                "feishu",
                "mail",
                "weixin"
            ],
            "title": "企业级负载均衡告警",
            "name": "load_balance_push"
        }

    def get_task_template(self):
        res_data = public.readFile(self.__task_template)
        all_upstream = UpStream.SQL().all()
        if not all_upstream:
            return "", None
        for upstream in all_upstream:
            res_data["field"][0]["items"].append({
                "title": upstream.name,
                "value": upstream.name
            })

        return "企业级负载均衡", [res_data, ]
