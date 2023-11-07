# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 宝塔软件(https://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <baozi@bt.cn>
# | Author: baozi
# | Version: 4.0
# +-------------------------------------------------------------------
import os
import json
import re
import sys
import time
from datetime import datetime, timedelta
from typing import Iterator, Optional, List, Dict

class_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# /www/server/panel/class
sys.path.insert(0, class_path)

import public, panelPush


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


class rsync_push(base_push):
    __push_conf = "{}/class/push/push.json".format(public.get_panel_path())
    __task_template = "{}/class/push/scripts/rsync.json".format(public.get_panel_path())
    __bt_sync_conf = "{}/plugin/rsync/config4.json".format(public.get_panel_path())

    def __init__(self) -> None:
        self.__push = panelPush.panelPush()
        self._tip_counter = None
        self._push_counter = None

    # 版本信息 目前无作用
    def get_version_info(self, get=None):
        data = {}
        data['ps'] = '宝塔文件同步告警'
        data['version'] = '1.0'
        data['date'] = '2023-05-25'
        data['author'] = '宝塔'
        data['help'] = 'http://www.bt.cn/bbs'
        return data

    # 获取模块推送参数
    def get_module_config(self, get: public.dict_obj):
        data = []
        item = self.__push.format_push_data(push=["mail", 'dingding', 'weixin', "feishu", "wx_account"],
                                            project='rsync', type='')
        item['cycle'] = 30
        item['title'] = '文件同步'
        data.append(item)
        return data

    # 获取模块配置项
    def get_push_config(self, get: public.dict_obj):
        id = get.id
        # 其实就是配置信息，没有也会从全局配置文件push.json中读取
        push_list = self.__push._get_conf()

        if id not in push_list["rsync"]:
            res_data = public.returnMsg(False, '未找到指定配置.')
            res_data['code'] = 100
            return res_data
        result = push_list["rsync"][id]
        return result

    # 写入推送配置文件
    def set_push_config(self, get: public.dict_obj):
        push_id = get.id
        pdata = json.loads(get.data)
        try:
            lsyncd_conf = json.loads(public.readFile(self.__bt_sync_conf))
        except (json.JSONDecodeError, TypeError):
            return public.returnMsg(False, '没有文件同步配置，无法设置告警')
        if not ("senders" in lsyncd_conf and bool(lsyncd_conf['senders'])):
            return public.returnMsg(False, '没有文件同步配置，无法设置告警')

        conf_data = self.__push._get_conf()
        if "rsync_push" not in conf_data:
            conf_data["rsync_push"] = {}
            pdata["status"] = True
            pdata["project"] = "rsync_all"
            conf_data["rsync_push"][push_id] = pdata
        else:
            # 其实这里只可能有一个设置
            for k, conf in conf_data["rsync_push"].items():
                conf["interval"] = pdata["interval"]
                conf["module"] = pdata["module"]
                conf["push_count"] = pdata["push_count"]
                self._del_today_push_counter(k)

        return conf_data

    # 删除推送配置
    def del_push_config(self, get: public.dict_obj):
        # 从配置中删除信息，并做一些您想做的事，如记日志
        id = get.id
        data = self.__push._get_conf()
        if str(id).strip() in data["rsync_push"]:
            del data["rsync_push"][id]
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
        # 已改为触发类型，跳过判断
        return None
        # if self._get_today_push_counter(data["id"]) >= data["push_count"]:
        #     return None
        # has_err = self._check_func(data["interval"])
        # if not has_err:
        #     return None
        # result = {'index': time.time(), }
        # for m_module in data['module'].split(','):
        #     if m_module == 'sms':
        #         continue
        #     s_list = [
        #         ">通知类型：文件同步告警",
        #         ">告警内容：<font color=#ff0000>文件同步执行中出错了，请及时关注文件同步情况并处理。</font> ",
        #     ]
        #     sdata = public.get_push_info('文件同步告警', s_list)
        #     result[m_module] = sdata
        # self._set_today_push_counter(data["id"])
        # return result

    def get_push_data_by_event(self, data, task_name: str):
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
        result = {'index': time.time(), }
        for m_module in data['module'].split(','):
            if m_module == 'sms':
                continue
            s_list = [
                ">通知类型：文件同步告警",
                ">告警内容：<font color=#ff0000>文件同步任务{}在执行中出错了，请及时关注文件同步情况并处理。</font> ".format(
                    task_name),
            ]
            sdata = public.get_push_info('文件同步告警', s_list)
            result[m_module] = sdata
        self._set_today_push_counter(data["id"])
        return result

    def _check_func(self, interval: int) -> bool:
        if not isinstance(interval, int):
            return False
        start_time = datetime.now() - timedelta(seconds=interval * 1.2)
        log_file = "{}/plugin/rsync/lsyncd.log".format(public.get_panel_path())
        if not os.path.exists(log_file):
            return False
        return LogChecker(log_file=log_file, start_time=start_time)()

    @property
    def push_counter(self) -> dict:
        if self._push_counter is not None:
            return self._push_counter
        else:
            today_push_counter = '{}/data/push/tips/rsync_today.json'.format(public.get_panel_path())
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
        today_push_counter = '{}/data/push/tips/rsync_today.json'.format(public.get_panel_path())
        if self._push_counter is not None:
            public.writeFile(today_push_counter, json.dumps(self.push_counter))

    def _get_today_push_counter(self, task_id):
        if task_id in self.push_counter:
            res = self.push_counter[task_id]
        else:
            res = 0
        return res

    def _set_today_push_counter(self, task_id: str):
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
                    "attr": "interval",
                    "name": "检测间隔时间",
                    "type": "number",
                    "unit": "秒",
                    "default": 600
                },
                {
                    "attr": "push_count",
                    "name": "每日发送",
                    "type": "number",
                    "unit": "次后，不再发送，次日恢复",
                    "default": 2
                }
            ],
            "sorted": [
                [
                    "interval"
                ],
                [
                    "push_count"
                ]
            ],
            "type": "rsync_push",
            "module": [
                "wx_account",
                "dingding",
                "feishu",
                "mail",
                "weixin"
            ],
            "tid": "rsync_push@0",
            "title": "文件同步告警",
            "name": "rsync_push"
        }

    def get_task_template(self):
        res_data = public.readFile(self.__task_template)
        if res_data is False:
            res_data = self._get_bak_task_template()

        return "文件同步", [res_data, ]

    @staticmethod
    def get_view_msg(task_id, task_data):
        task_data["tid"] = "rsync_push@0"
        task_data["view_msg"] = "<span>文件同步出现异常时，推送告警信息(每日推送{}次后不在推送)<span>".format(task_data["push_count"])
        return task_data

    def main(self):
        if len(sys.argv) < 2:
            print("参数错误")
            return
        task_name = sys.argv[1]
        tip = RsyncPushTip()
        try:
            data = self.__push._get_conf()
            if "rsync_push" not in data:
                return
            rsync_push_conf: Dict[str, dict] = data["rsync_push"]
            for key, item in rsync_push_conf.items():
                item['id'] = key
                if item["status"] is False:
                    continue  # 跳过关闭的任务
                if not (item["project"] in ("rsync_push", "all") or item["project"] != task_name):
                    continue  # 跳过不匹配的任务
                if tip.have(task_name):
                    continue  # 推送时间频繁地跳过

                # 获取推送信息
                rdata = self.get_push_data_by_event(item, task_name)
                if not rdata:
                    continue
                print(rdata)
                for m_module in item['module'].split(','):
                    if m_module not in rdata:
                        continue
                    msg_obj = public.init_msg(m_module)
                    if not msg_obj:
                        continue
                    msg_obj.push_data(rdata[m_module])
            tip.save_tip_list()
        except:
            print(public.get_error_info())


class RsyncPushTip(object):
    _FILE = '{}/data/push/tips/rsync_push.tip'.format(public.get_panel_path())

    def __init__(self):
        self._tip_map = None

    @property
    def tip_list(self) -> dict:
        if self._tip_map is not None:
            return self._tip_map

        if os.path.exists(self._FILE):
            try:
                tip = json.loads(public.readFile(self._FILE))
            except:
                tip = {}
        else:
            tip = {}

        self._tip_map = tip
        return self._tip_map

    def save_tip_list(self):
        if self._tip_map is not None:
            public.writeFile(self._FILE, json.dumps(self._tip_map))

    def have(self, name):
        now = time.time()
        if name in self._tip_map:
            if now > self._tip_map[name]:
                self._tip_map[name] = now + 60 * 3
                return False
            else:
                return True
        else:
            self._tip_map[name] = now + 60 * 3
            return False


class LogChecker:
    """
    排序查询并获取日志内容
    """
    rep_time = re.compile(r'(?P<target>(\w{3}\s+){2}(\d{1,2})\s+(\d{2}:?){3}\s+\d{4})')
    format_str = '%a %b %d %H:%M:%S %Y'
    err_datetime = datetime.fromtimestamp(0)
    err_list = ("error", "Error", "ERROR", "exitcode = 10", "failed")

    def __init__(self, log_file: str, start_time: datetime):
        self.log_file = log_file
        self.start_time = start_time
        self.is_over_time = None  # None:还没查到时间，未知， False: 可以继续网上查询， True:比较早的数据了，不再向上查询
        self.has_err = False  # 目前已查询的内容中是否有报错信息

    def _format_time(self, log_line) -> Optional[datetime]:
        try:
            date_str_res = self.rep_time.search(log_line)
            if date_str_res:
                time_str = date_str_res.group("target")
                return datetime.strptime(time_str, self.format_str)
        except Exception:
            return self.err_datetime
        return None

    # 返回日志内容
    def __call__(self):
        _buf = b""
        file_size, fp = os.stat(self.log_file).st_size - 1, open(self.log_file, mode="rb")
        fp.seek(-1, 2)
        while file_size:
            read_size = min(1024, file_size)
            fp.seek(-read_size, 1)
            buf: bytes = fp.read(read_size) + _buf
            fp.seek(-read_size, 1)
            if file_size > 1024:
                idx = buf.find(ord("\n"))
                _buf, buf = buf[:idx], buf[idx + 1:]
            for i in self._get_log_line_from_buf(buf):
                self._check(i)
                if self.is_over_time:
                    fp.close()
                    return self.has_err
            file_size -= read_size
        fp.close()
        return False

    # 从缓冲中读取日志
    @staticmethod
    def _get_log_line_from_buf(buf: bytes) -> Iterator[str]:
        n, m = 0, 0
        buf_len = len(buf) - 1
        for i in range(buf_len, -1, -1):
            if buf[i] == ord("\n"):
                log_line = buf[buf_len + 1 - m: buf_len - n + 1].decode("utf-8")
                yield log_line
                n = m = m + 1
            else:
                m += 1
        yield buf[0: buf_len - n + 1].decode("utf-8")

    # 格式化并筛选查询条件
    def _check(self, log_line: str) -> None:
        # 筛选日期
        for err in self.err_list:
            if err in log_line:
                self.has_err = True

        ck_time = self._format_time(log_line)
        if ck_time:
            self.is_over_time = self.start_time > ck_time


if __name__ == "__main__":
    rsync_push().main()
