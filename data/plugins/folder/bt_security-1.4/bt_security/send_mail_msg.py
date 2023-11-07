# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 梁凯强 <1249648969@qq.com>
# +-------------------------------------------------------------------
import sys, os
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
sys.path.append("class/")
import public, json,time
import send_mail

class webshell_check:
    __PATH = '/www/server/panel/data/'
    __mail_config = '/www/server/panel/data/stmp_mail.json'
    __mail_list_data = '/www/server/panel/data/mail_list.json'
    __dingding_config = '/www/server/panel/data/dingding.json'
    __to_msg = '/www/server/panel/plugin/bt_security/msg.conf'
    __mail_list = []
    __weixin_user = []

    def __init__(self):
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

    def send(self,title,body):
        tongdao = self.get_settings()
        self.mail.qq_smtp_send(str(tongdao['user_mail']['info']['qq_mail']), title=title, body=body)

    def send_dingding(self,count):
        self.mail.dingding_send(count)

    def return_data(self):
        if not os.path.exists('/www/server/panel/plugin/bt_security'):return False
        try:
            msg_conf=json.loads(public.ReadFile(self.__to_msg))
            return msg_conf
        except:
            public.writeFile(self.__to_msg,json.dumps({"open":False,'to_mail':False}))
            return False

    '''获取用户的日志'''
    def get_safe_logs(self, path,p=1,num=11):
        try:
            import cgi
            pythonV = sys.version_info[0]
            if not os.path.exists(path): return '111';
            start_line = (p - 1) * num
            count = start_line + num
            fp = open(path, 'rb')
            buf = ""
            try:
                fp.seek(-1, 2)
            except:
                return []
            if fp.read(1) == "\n": fp.seek(-1, 2)
            data = []
            b = True
            n = 0
            for i in range(count):
                while True:
                    newline_pos = str.rfind(buf, "\n")
                    pos = fp.tell()
                    if newline_pos != -1:
                        if n >= start_line:
                            line = buf[newline_pos + 1:]
                            try:
                                tmp_data = json.loads(cgi.escape(line))
                                data.append(tmp_data)
                            except:
                                pass
                        buf = buf[:newline_pos]
                        n += 1
                        break
                    else:
                        if pos == 0:
                            b = False
                            break
                        to_read = min(4096, pos)
                        fp.seek(-to_read, 1)
                        t_buf = fp.read(to_read)
                        if pythonV == 3: t_buf = t_buf.decode('utf-8')
                        buf = t_buf + buf
                        fp.seek(-to_read, 1)
                        if pos - to_read == 0:
                            buf = "\n" + buf
                if not b: break;
            fp.close()
        except:
            data = []
        return data

    def get_ip(self):
        if os.path.exists('/www/server/panel/data/iplist.txt'):
            data=public.ReadFile('/www/server/panel/data/iplist.txt')
            return data.strip()
        else:return '127.0.0.1'

    def main_send(self,title,count):
        data=self.return_data()
        if not data['open']:return False
        if data['to_mail']=='mail':
            self.send(title,count)
        if data['to_mail']=='dingding':
            self.send_dingding(count)

    def read_file(self):
        if not os.path.exists('/www/server/panel/data/send_mail_to_time.json'):
            public.writeFile('/www/server/panel/data/send_mail_to_time.json',json.dumps([]))
            return []
        else:
            try:
                return json.loads(public.ReadFile('/www/server/panel/data/send_mail_to_time.json'))
            except:
                public.writeFile('/www/server/panel/data/send_mail_to_time.json', json.dumps([]))
                return []

    def timestamp_to_str(self,timestamp=None, format='%Y-%m-%d %H:%M:%S'):
        if timestamp:
            return time.strftime(format, time.localtime(timestamp))
        else:
            return time.strftime(format, time.localtime())


    def __write_log(self, msg):
        public.WriteLog('防提权告警', msg)


    def main(self):
        if not  os.path.exists('/usr/local/usranalyse/logs/send/bt_security.json'):return False
        data=self.get_safe_logs('/usr/local/usranalyse/logs/send/bt_security.json')
        read_file=self.read_file()
        count=1
        data222=self.return_data()
        print(data)
        start_time=int(time.time())
        for i in data:
            if i[0] in read_file:continue
            time_data=(int(time.time())-int(i[0]))
            if time_data>86400:continue
            if len(i)>2:continue
            if count>=4:
                if int(int(time.time())-start_time)<60:
                    continue
            if not data222['open']:continue
            self.main_send(self.get_ip()+'服务器可能遭到入侵',i[1]+'---时间:'+self.timestamp_to_str(int(i[0])))
            self.__write_log(self.get_ip()+'服务器可能遭到入侵'+i[1]+'---时间:'+self.timestamp_to_str(int(i[0])))
            read_file.append(i[0])
            count+=1
        public.writeFile('/www/server/panel/data/send_mail_to_time.json', json.dumps(read_file))

if __name__ == '__main__':
    data=webshell_check()
    data.main()