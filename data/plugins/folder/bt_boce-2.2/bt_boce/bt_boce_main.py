# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   微架构 - 拔测监控
# +--------------------------------------------------------------------
import sys, os
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
sys.path.append("class/")
import public, time, crontab, panelAuth, json
import send_mail

class bt_boce_main:
    __mail_config = '/www/server/panel/data/stmp_mail.json'
    __mail_list_data = '/www/server/panel/data/mail_list.json'
    __dingding_config = '/www/server/panel/data/dingding.json'

    def __init__(self):
        try:
            self.mail = send_mail.send_mail()
            if not os.path.exists(self.__mail_list_data):
                ret = []
                public.writeFile(self.__mail_list_data, json.dumps(ret))
            else:
                try:
                    mail_data = json.loads(public.ReadFile(self.__mail_list_data))
                    self.__mail_list = mail_data
                except:
                    ret = []
                    public.writeFile(self.__mail_list_data, json.dumps(ret))
        except:pass
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'boce_task')).count():
            public.M('boce_task').execute('''CREATE TABLE IF NOT EXISTS boce_task (
    id      INTEGER      PRIMARY KEY AUTOINCREMENT,
    name    STRING (64),
    url     STRING (128),
    status  INTEGER,
    cycle   INTEGER,
    addtime INTEGER
)''', ())

            public.M('boce_list').execute('''CREATE TABLE IF NOT EXISTS boce_list (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    pid     INTEGER,
    data    TEXT,
    status  INTEGER,
    addtime INTEGER
)''', ())

            if not public.M('nodes').where("name=?", 'coll_boce').count():
                public.M('nodes').insert(
                    {"name": "coll_boce", "title": "拔测监控", "level": 1, "sort": 10.0, "state": 1, "p_nid": 0, "ps": ""})

    # 返回配置邮件地址
    def return_mail_list(self):
        return self.__mail_list

    # 查看自定义邮箱配置
    def get_user_mail(self):
        qq_mail_info = json.loads(public.ReadFile(self.__mail_config))
        if len(qq_mail_info) == 0:
            return False
        return qq_mail_info

    # 查看钉钉
    def get_dingding(self):
        qq_mail_info = json.loads(public.ReadFile(self.__dingding_config))
        if len(qq_mail_info) == 0:
            return False
        return qq_mail_info

    # 查看能使用的告警通道
    def get_settings(self):
        qq_mail_info = json.loads(public.ReadFile(self.__mail_config))
        if len(qq_mail_info) == 0:
            user_mail = False
        else:
            user_mail = True
        dingding_info = json.loads(public.ReadFile(self.__dingding_config))
        if len(dingding_info) == 0:
            dingding = False
        else:
            dingding = True
        ret = {}
        ret['user_mail'] = {"user_name": user_mail, "mail_list": self.__mail_list, "info": self.get_user_mail()}
        ret['dingding'] = {"dingding": dingding, "info": self.get_dingding()}
        return ret


    # 获取任务列表
    def get_list(self, args):
        if 'p' not in args: args.p = '1'
        args.p = int(args.p)
        data = {}
        where = ''
        if 'search' in args:
            where = "name='{0}' OR url='%{0}%'".format(args.search)
        count = public.M('boce_task').where(where, ()).order("id desc").count()
        data['page'] = public.get_page(count, args.p, 12)
        data['data'] = public.M('boce_task').where(where, ()).order("id desc").limit(
            '{},{}'.format(data['page']['shift'], data['page']['row'])).select()
        bock_list_sql = public.M('boce_list')
        for i in range(len(data['data'])):
            data['data'][i]['last_run_time'] = bock_list_sql.where('pid=?', (data['data'][i]['id'],)).order(
                'id desc').getField('addtime')
        return data

    # 取指定拔测任务
    def get_find(self, args):
        if 'id' not in args: return public.returnMsg(False, '错误的参数!')
        id = args.id
        return public.M('boce_task').where('id=?', id).find()

    # 创建拔测任务
    def create(self, args):
        pdata = {}
        pdata['name'] = args.name2
        pdata['url'] = args.url.strip()
        if pdata['url'].find('http://') == -1 and pdata['url'].find('https://') == -1:
            return public.returnMsg(False, 'URL地址必需包含http://或https://')
        pdata['cycle'] = int(args.cycle)
        #if public.is_free() and pdata['cycle'] < 10:
         #   return public.returnMsg(False, '免费版用户拔测周期最短不能少于10分钟')
        if pdata['cycle'] < 1: return public.returnMsg(False, '拔测周期最短不能少于1分钟')
        pdata['status'] = 1
        pdata['addtime'] = int(time.time())
        pdata['id'] = public.M('boce_task').insert(pdata)
        self.create_task(pdata)
        public.WriteLog('拔测监控', "创建拔测任务[{}]".format(pdata['name']))
        return public.returnMsg(True, '添加成功!')

    # 创建计划任务
    def create_task(self, pdata):
        p = crontab.crontab()
        args = {
            "name": "拔测任务[" + pdata['name'] + "]",
            "type": "minute-n",
            "where1": pdata['cycle'],
            "hour": "",
            "minute": "",
            "week": "",
            "sType": "toShell",
            "sName": "",
            "backupTo": "localhost",
            "save": "boce_id_{}".format(pdata['id']),
            "sBody": "python /www/server/panel/plugin/bt_boce/bt_boce_main.py {}".format(
                pdata['id']),
            "urladdress": "undefined"
        }

        p.AddCrontab(args)

    # 修改计划任务
    def modify_task(self, pdata):
        p = crontab.crontab()
        args = {
            "id": public.M('crontab').where("save=?", "boce_id_{}".format(pdata['id'])).getField('id'),
            "name": "拔测任务[" + str(pdata['name']) + "]",
            "type": "minute-n",
            "where1": pdata['cycle'],
            "hour": "",
            "minute": "",
            "week": "",
            "sType": "toShell",
            "sName": "",
            "backupTo": "localhost",
            "save": "boce_id_{}".format(pdata['id']),
            "sBody": "python /www/server/panel/plugin/bt_boce/bt_boce_main.py {}".format(
                pdata['id']),
            "urladdress": "undefined",
            "status": pdata['status']
        }
        p.modify_crond(args)

    # 删除计划任务
    def remove_task(self, pid):
        p = crontab.crontab()
        id = public.M('crontab').where("save=?", "boce_id_{}".format(pid)).getField('id')
        args = {"id": id}
        p.DelCrontab(args)

    # 编辑拔测任务
    def modify(self, args):
        if 'id' not in args: return public.returnMsg(False, '错误的参数!')
        id = args.id
        pdata = {}
        if 'name' in args: pdata['name'] = args.name2
        if 'url' in args:
            pdata['url'] = args.url.strip()
            if pdata['url'].find('http://') == -1 and pdata['url'].find('https://') == -1:
                return public.returnMsg(False, 'URL地址必需包含http://或https://')
        if 'cycle' in args:
            pdata['cycle'] = int(args.cycle)
            #if public.is_free() and pdata['cycle'] < 10: return public.returnMsg(False, '拔测周期最短不能少于10分钟')
            if pdata['cycle'] < 1: return public.returnMsg(False, '拔测周期最短不能少于1分钟')
        if 'status' in args: pdata['status'] = args.status
        public.M('boce_task').where('id=?', id).update(pdata)
        pdata = public.M('boce_task').where('id=?', id).find()
        self.modify_task(pdata)
        public.WriteLog('拔测监控', "修改拔测任务[{}]".format(pdata['name']))
        return public.returnMsg(True, '修改成功!')

    # 删除拔测任务
    def remove(self, args):
        if 'id' not in args: return public.returnMsg(False, '错误的参数!')
        id = args.id
        pdata = public.M('boce_task').where('id=?', id).find()
        public.M('boce_task').where('id=?', id).delete()
        public.M('boce_list').where('pid=?', id).delete()
        self.remove_task(id)
        public.WriteLog('拔测监控', "删除拔测任务[{}]".format(pdata['name']))
        return public.returnMsg(True, '删除成功!')

    # 执行指定拔测任务
    def start(self, args):
        if 'id' not in args: return public.returnMsg(False, '错误的参数!')
        id = args['id']
        result = self._send_task(id)
        if 'status' in result: return result
        pdata = {}
        pdata['status'] = self.get_state(result, id)
        pdata['data'] = json.dumps(result)
        pdata['pid'] = id
        pdata['addtime'] = int(time.time())
        public.M('boce_list').insert(pdata)
        result = sorted(result, key=lambda x: x['total_time'], reverse=True)
        return result

    # 获取测试状态
    def get_state(self, data, id):
        err = 0
        for n in data:
            if not n: continue
            if n['http_code'] not in [200, 301, 302, 403, 401]: err += 1
        if err > 2:
            self.send_mail(data, err, id)
            return 0
        return 1

    # 发送邮件通知
    def send_mail(self, data, num, id,send='mail'):
        # try:
        #     last_file = "/dev/shm/last_mail_send.pl"
        #     try:
        #         if os.path.exists(last_file):
        #             last_time = int(public.readFile(last_file))
        #             if time.time() - last_time < 3600: return False
        #     except:
        #         print(public.get_error_info())
        name = public.M('boce_task').where('id=?', id).getField('name')
        title = "【{}】堡塔拔测监控到[{}]个测试异常".format(name, num)
        mail_body = "<h2>堡塔云控平台拔测监控报表(" + public.format_date() + ")</h2><hr /><table  border='0' cellspacing='1' cellpadding='0' bgcolor='#888'><thead><tr bgcolor='#FFFFFF' style='background-color: darkgray;'><th>ISP</th><th>解析地址</th><th>响应状态</th><th>总耗时</th><th>解析耗时</th><th>处理耗时</th><th>响应大小</th><th>传输速度</th></tr></thead><tbody>"
        for i in data:
            if not i: continue
            is_red = ""
            if not i['primary_ip']:
                i['primary_ip'] = '解析失败'
                is_red = "style='color:red;'"
            if not i['http_code']:
                i['http_code'] = '无法访问'
                is_red = "style='color:red;'"
            mail_body += "<tr bgcolor='#FFFFFF' " + is_red + "><td>" + i['isp'] + "</td><td>" + i[
                'primary_ip'] + "</td><td>" + str(i['http_code'])
            mail_body += "</td><td>{:.2f}".format(i['total_time'] * 1000)
            mail_body += "ms</td><td>{:.2f}".format(i['namelookup_time'] * 1000)
            mail_body += "ms</td><td>{:.2f}".format(i['starttransfer_time'] * 1000)
            mail_body += "ms</td><td>" + public.to_size(i['size_download']) + "</td><td>" + public.to_size(
                i['speed_download']) + "/s</td></tr>"
        mail_body += "</tbody></table><hr><p>此为堡塔云控平台自动通知邮件，请勿回复</p>"
        tongdao = self.get_settings()
        if send == 'dingding':
            if tongdao['dingding']:
                msg = mail_body
                self.mail.dingding_send(msg)
        elif send == 'mail':
            if tongdao['user_mail']:
                if len(self.__mail_list) == 0:
                    if tongdao['user_mail']['user_name']:
                        self.mail.qq_smtp_send(str(tongdao['user_mail']['info']['qq_mail']), title=title, body=mail_body)
                else:
                    for i in self.__mail_list:
                        if tongdao['user_mail']['user_name']:
                            self.mail.qq_smtp_send(str(i), title=title, body=mail_body)
            #public.writeFile(last_file, str(int(time.time())))
        # except:
        #     pass

    # 获取任务执行记录
    def get_task_log(self, args):
        if 'pid' not in args: return public.returnMsg(False, '错误的参数!')
        pid = args.pid
        if 'p' not in args: args.p = '1'
        args.p = int(args.p)
        data = {}
        count = public.M('boce_list').where("pid=?", pid).order("id desc").count()
        data['page'] = public.get_page(count, args.p, 12)
        data['data'] = public.M('boce_list').where("pid=?", pid).order("id desc").limit(
            '{},{}'.format(data['page']['shift'], data['page']['row'])).select()
        for i in range(len(data['data'])):
            try:
                j_data = json.loads(data['data'][i]['data'])
                total_time = 0
                for d in j_data:
                    total_time += d['total_time']
                data['data'][i]['avgrage'] = float('{:.2f}'.format(total_time / len(j_data)))
                data['data'][i]['data'] = sorted(j_data, key=lambda x: x['total_time'], reverse=True)
                data['data'][i]['max'] = float('{:.2f}'.format(data['data'][i]['data'][0]['total_time']))
                data['data'][i]['max_isp'] = data['data'][i]['data'][0]['isp']
                data['data'][i]['min'] = float('{:.2f}'.format(data['data'][i]['data'][-1]['total_time']))
                data['data'][i]['min_isp'] = data['data'][i]['data'][-1]['isp']
            except:
                continue
        return data

    # 删除指定任务执行记录
    def remove_task_log(self, args):
        if 'id' not in args: return public.returnMsg(False, '错误的参数!')
        id = args.id
        public.M('boce_list').where('id=?', id).delete()
        public.WriteLog('拔测监控', "删除任务记录[{}]".format(id))
        return public.returnMsg(True, '删除成功!')

    # 发送任务到云端调度中心
    def _send_task(self, id):
        url = public.M('boce_task').where('id=?', id).getField('url')
        if not url: return public.returnMsg(False, '指定任务不存在!')
        pdata = panelAuth.panelAuth().create_serverid(None)
        pdata['url'] = url
        try:
            result = public.httpPost("http://www.bt.cn/api/local/boce", pdata, 60)
            result = json.loads(result)
            return result
        except:
            print(public.get_error_info())
            return public.returnMsg(False, '连接调度中心失败!')

	# 发送任务到云端调度中心
    def boce_task_byname(self,args):      

        pdata = panelAuth.panelAuth().create_serverid(None)
        pdata['url'] = args['url']
        try:
            result = public.httpPost("http://www.bt.cn/api/local/boce", pdata, 60)
            result = json.loads(result)    
            return result
        except:
            print(public.get_error_info())
            return public.returnMsg(False, '连接调度中心失败!')