import os, sys

import json, requests

os.chdir('/www/server/panel')
if not 'class/' in sys.path:
    sys.path.insert(0, 'class/')
import public, db


class vuln_push_main:
    __plugin_path = '/www/server/panel/plugin/vuln_push'
    __load = __plugin_path + '/load_spy.py'
    __data_path = '/www/server/panel/data/vuln_push'
    __push_file = __data_path + '/push.pl'
    __result = __data_path + '/result.json'
    __sql = None

    def __init__(self):
        if not os.path.exists(self.__data_path):
            os.makedirs(self.__data_path, 384)
        if not os.path.exists(self.__result):
            public.WriteFile(self.__result, '[]')
        self.__sql = db.Sql().dbfile("vuln_push") # 初始化数据库
        if not self.__sql.table('sqlite_master').where('type=? AND name=?', ('table', 'vuln_push')).count():
            vuln_push_sql = '''
            CREATE TABLE IF NOT EXISTS `vuln_push` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `cve_id` VARCHAR(30),
            `name` TEXT,
            `info` TEXT,
            `msg` TEXT,
            `risk` VARCHAR(20),
            `time` VARCHAR(30),
            `msg1` TEXT
            )
            '''
            self.__sql.execute(vuln_push_sql)

    def vuln_spy(self, get):
        import re
        info = self.get_userInfo()
        response = requests.post(public.GetConfigValue('home')+'/api/bt_waf/getVulScanInfoList', info)
        data = json.loads(response.content)
        old_data = self.__sql.table("vuln_push").field('cve_id,name,info,msg,msg1,risk,time').select()
        for d in data["res"]:
            d.pop('id')
            d.pop('addtime')
            try:
                d['risk'] = d['msg'].split('危害定级: **')[1].split('**')[0]
                d['time'] = d['msg'].split('披露日期: **')[1].split('**')[0]
                tmp = [{'risk': d['msg'].split('危害定级: **')[1].split('**')[0],
                        'tag': re.findall(r'\*\*(.*?)\*\*', d['msg'].split('漏洞标签:')[1].split('\n- 披露日期:')[0]),
                        'time': d['msg'].split('披露日期: **')[1].split('**')[0],
                        'source': re.sub(r'\(.*?\)|\[|\]', '', d['msg'].split('信息来源: ')[1].split('\n- 推送原因:')[0]),
                        'reason': d['msg'].split('推送原因: ')[1].split('\n**参考链接**')[0],
                        'repair': '将相关组件升级至最新版本'
                        }]
                if not d['msg'].split('**参考链接**')[1]:
                    tmp[0]['link'] = ''
                else:
                    tmp[0]['link'] = re.findall(r'\[(.*?)\]', d['msg'].split('**参考链接**\n')[1])
                d['msg1'] = json.dumps(tmp)
            except:
                d['risk'] = ''
                d['time'] = ''
                d['msg'] = ''
            if d not in old_data:
                res = self.__sql.table("vuln_push").insert(d)
                self.send_news(d)

    def get_result(self, get):
        import page
        page = page.Page()
        count = self.__sql.table("vuln_push").count()
        public.print_log(count)
        limit = 10
        info = {}
        info['count'] = count
        info['row'] = limit
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        info['uri'] = get
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs
        data = {}
        data['page'] = page.GetPage(info, '1,2,3,4,5,8')
        if not count:
            data['data'] = []
            return data
        data['data'] = self.__sql.table("vuln_push").order('id desc').limit(str(page.SHIFT) + ',' + str(page.ROW)).select()
        return data

    def set_process(self, get):
        import crontab
        cmd = '{} {}'.format('/usr/bin/btpython', self.__load)
        args = {"name": "[勿删]堡塔漏洞情报任务", "type": 'day',
                "where1": '',
                "hour": '9',
                "minute": '0',
                "sName": "", "sType": 'toShell', "notice": '0', "notice_channel": '', "save": '', "save_local": '1',
                "backupTo": '', "sBody": cmd, "urladdress": '', "week": ''}
        cron_list = crontab.crontab().GetCrontab('')
        for cl in cron_list:
            if cl["name"] == "[勿删]堡塔漏洞情报任务":
                res = crontab.crontab().DelCrontab({"id":cl["id"]})
                if res["status"]:
                    return public.returnMsg(True, '关闭情报更新成功')
                else:
                    return public.returnMsg(False, '关闭情报更新失败')
        res = crontab.crontab().AddCrontab(args)
        if res["status"]:
            return public.returnMsg(True, '开启情报更新成功')
        else:
            return public.returnMsg(False, '开启情报更新失败')

    # def remove_process(self, get):
    #     import crontab
    #     cron_list = crontab.crontab().GetCrontab('')
    #     for cl in cron_list:
    #         if cl["name"] == "[勿删]堡塔漏洞情报任务":
    #             res = crontab.crontab().DelCrontab({"id":cl["id"]})
    #             public.print_log(res)
    #             if res["status"]:
    #                 return public.returnMsg(True, '关闭情报更新成功')
    #     return public.returnMsg(False, '关闭情报更新失败')

    # def get_status(self, get):
    #     import crontab
    #     cron_list = crontab.crontab().GetCrontab('')
    #     for cl in cron_list:
    #         if cl["name"] == "[勿删]堡塔漏洞情报任务":
    #             return {
    #                     "cycle": cl["cycle"],
    #                     "type": cl["type"],
    #                     "where1": cl["where1"],
    #                     "hour": cl["where_hour"],
    #                     "minute": cl["where_minute"]
    #                     }
    #     return {
    #         "cycle": "",
    #         "type": "",
    #         "where1": "",
    #         "hour": "",
    #         "minute": ""
    #     }

    # 是否开启
    def get_status(self, get):
        import crontab
        cron_list = crontab.crontab().GetCrontab('')
        for cl in cron_list:
            if cl["name"] == "[勿删]堡塔漏洞情报任务":
                return {"status": True}
        return {"status": False}


    def set_send(self, get):
        login_send_type_conf = self.__push_file
        set_type = get.type.strip()
        if set_type == "error":
            public.writeFile(login_send_type_conf, set_type)
            return public.returnMsg(True, '关闭成功')
        import config
        config = config.config()
        msg_configs = config.get_msg_configs(get)
        if set_type not in msg_configs.keys():
            return public.returnMsg(False, '不支持该发送类型')
        _conf = msg_configs[set_type]
        if "data" not in _conf or not _conf["data"]:
            return public.returnMsg(False, "该通道未配置, 请重新选择。")
        from panelMessage import panelMessage
        pm = panelMessage()
        obj = pm.init_msg_module(set_type)
        if not obj:
            return public.returnMsg(False, "消息通道未安装。")
        public.writeFile(login_send_type_conf, set_type)
        return public.returnMsg(True, '设置成功')

    def send_news(self, data):
        import re
        login_send_type_conf = self.__push_file
        if os.path.exists(login_send_type_conf):
            send_type = public.ReadFile(login_send_type_conf).strip()
        else:
            return False
        if not send_type:
            return False
        object = public.init_msg(send_type.strip())
        if not object: return False

        plist = [
            ">漏洞名称：" + data["name"],
            ">漏洞编号：" + data["cve_id"],
            ">漏洞介绍：" + data["info"],
            ">漏洞详情：" + re.sub(r'\(.*?\)', '', data["msg"].replace('*', ''))
        ]
        info = public.get_push_info("堡塔漏洞情报推送", plist)
        reuslt = object.push_data(info)
        return reuslt

    def get_send(self, get):
        send_type = "error"
        if os.path.exists(self.__push_file):
            send_type = public.ReadFile(self.__push_file)
        return public.returnMsg(True, send_type)

    def get_userInfo(self):
        info = json.loads(public.ReadFile("/www/server/panel/data/userInfo.json"))
        return {"uid": info["uid"], "access_key": info["access_key"], "serverid": info["serverid"]}


if __name__ == '__main__':
    vo = vuln_push_main()
    vo.vuln_spy('')
