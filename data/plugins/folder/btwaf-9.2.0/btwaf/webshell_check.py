# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x6
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: lkqiang<lkq@bt.cn>
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   防火墙内部扫描webshell
# +--------------------------------------------------------------------
import sys

sys.path.append('/www/server/panel/class')
import json, os, time, public

os.chdir('/www/server/panel')
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class webshell_check:
    __user = {}
    __PATH = '/www/server/panel/plugin/btwaf/'
    Recycle_bin = __PATH + 'Recycle'
    Webshell_Alarm = __PATH + 'Webshell_Alarm.json'
    def __init__(self):
        if not os.path.exists(self.Recycle_bin):
            os.makedirs(self.Recycle_bin)
        try:
            self.__user = json.loads(public.ReadFile('/www/server/panel/data/userInfo.json'))
        except:
            pass


    # 移动到回收站
    def Mv_Recycle_bin(self,path):
        rPath = self.Recycle_bin
        if not os.path.exists(self.Recycle_bin):
            os.makedirs(self.Recycle_bin)
        rFile = os.path.join(rPath, path.replace('/', '_bt_') + '_t_' + str(time.time()))
        try:
            import shutil
            shutil.move(path, rFile)
            return True
        except:
            return False

    '''
    @name 获取目录下的所有php文件
    @param path 文件目录
    @return list
    '''

    def get_dir(self, path):
        return_data = []
        data2 = []
        [[return_data.append(os.path.join(root, file)) for file in files] for root, dirs, files in os.walk(path)]
        for i in return_data:
            if str(i.lower())[-4:] == '.php':
                data2.append(i)
        return data2

    '''
    @name 读取文件内容
    @param filename 文件路径
    @return 文件内容
    '''

    def ReadFile(self, filename, mode='rb'):
        import os
        if not os.path.exists(filename): return False
        try:
            fp = open(filename, mode)
            f_body = fp.read()
            fp.close()
        except Exception as ex:
            if sys.version_info[0] != 2:
                try:
                    fp = open(filename, mode, encoding="utf-8")
                    f_body = fp.read()
                    fp.close()
                except Exception as ex2:
                    return False
            else:
                return False
        return f_body

    def GetFIles(self,path):
        if not os.path.exists(path): return False
        data = {}
        data['status'] = True
        data["only_read"] = False
        data["size"] = os.path.getsize(path)
        if os.path.getsize(path)> 1024 * 1024 * 2:return False
        fp = open(path, 'rb')
        if fp:
            srcBody = fp.read()
            fp.close()
            try:
                data['encoding'] = 'utf-8'
                data['data'] = srcBody.decode(data['encoding'])
            except:
                try:
                    data['encoding'] = 'GBK'
                    data['data'] = srcBody.decode(data['encoding'])
                except:
                    try:
                        data['encoding'] = 'BIG5'
                        data['data'] = srcBody.decode(data['encoding'])
                    except:
                        return False
        return True

    '''
    @name 上传到云端判断是否是webshell
    @param filename 文件路径
    @param url 云端URL
    @return bool 
    '''

    def webshellchop(self, filename, url):
        try:
            upload_url = url
            size = os.path.getsize(filename)
            if size > 1024000: return False
            if len(self.__user) == 0: return False
            if not self.GetFIles(filename): return False
            md5s=public.Md5(filename)
            webshell_path = "/www/server/panel/data/btwaf_wubao/"
            if not os.path.exists(webshell_path):
                os.makedirs(webshell_path)
            if os.path.exists(webshell_path+md5s+".txt"):
                return False
            info=self.ReadFile(filename)
            upload_data = {'inputfile': info, "md5": md5s, "path": filename,
                           "access_key": self.__user['access_key'], "uid": self.__user['uid'],
                           "username": self.__user["username"]}
            print("正在上传文件:%s" % (filename))
            upload_res = requests.post(upload_url, upload_data, timeout=20).json()
            if upload_res['msg'] == 'ok':
                if (upload_res['data']['data']['level'] == 5):
                    self.Mv_Recycle_bin(filename)
                    if os.path.exists(self.Webshell_Alarm):
                        public.WriteFile(self.Webshell_Alarm, "[]")
                        Alarm = []
                    else:
                        try:
                            Alarm = json.loads(public.ReadFile(self.Webshell_Alarm))
                        except:
                            Alarm = []
                    if filename not in Alarm:
                        Alarm.append(filename)
                    public.WriteFile(self.Webshell_Alarm, json.dumps(Alarm))
                    print('%s 文件为木马 ' % (filename))
                    return True
                else:
                    return False
        except:
            return False

    '''
    @name 上传文件入口
    @param filename 文件路径
    @return bool 
    '''

    def upload_file_url2(self, filename, url):
        if os.path.exists(filename):
            ret = self.webshellchop(filename, url)
            if ret:
                return True
            return False
        else:
            return False

    '''
    @name 上传文件
    @param data 文件路径集合
    @return 返回webshell 路径
    '''

    def upload_shell(self, data):
        if len(data) == 0: return []
        return_data = []
        today = time.strftime("%Y-%m-%d-%H", time.localtime())
        if not os.path.exists("/www/server/btwaf/webshell_total/" + today + ".md5"):
            public.WriteFile("/www/server/btwaf/webshell_total/" + today + ".md5", "{}")
            md5_info={}
        else:
            try:
                md5_info = json.loads(public.ReadFile("/www/server/btwaf/webshell_total/" + today + ".md5"))
            except:
                md5_info = {}
        for i in data:
            if not os.path.exists(i):continue
            md5=public.FileMd5(i)
            if md5 in md5_info and md5_info[md5]==1:
                continue
            if self.upload_file_url2(i, "http://w-check.bt.cn/check.php"):
                return_data.append(i)
                md5_info[md5] = 0
            else:
                md5_info[md5]=1
        public.writeFile("/www/server/btwaf/webshell_total/" + today + ".md5", json.dumps(md5_info))
        return return_data

    def get_white(self):
        if not os.path.exists('/www/server/panel/data/white_webshell.json'): return []
        try:
            return json.loads(public.ReadFile('/www/server/panel/data/white_webshell.json'))
        except:
            return []

    '''
    @name 扫描webshell入口函数
    @param path 需要扫描的路径
    @return  webshell 路径集合
    '''

    def san_dir(self):
        import pwd
        stat = os.stat("/www/server/btwaf/webshell.json")
        accept = str(oct(stat.st_mode)[-3:])
        mtime = str(int(stat.st_mtime))
        user = ''
        try:
            user = pwd.getpwuid(stat.st_uid).pw_name
        except:
            user ="root"
        if user!="root":
            public.ExecShell("chown root:root /www/server/btwaf/webshell.json")

        today = time.strftime("%Y-%m-%d", time.localtime())
        #删除过期文件
        #列"/www/server/btwaf/webshell_total/" 目录
        if os.path.exists("/www/server/btwaf/webshell_total/"):
            for i in os.listdir("/www/server/btwaf/webshell_total/"):
                if i.startswith(today):continue
                os.remove("/www/server/btwaf/webshell_total/"+i)
        today = time.strftime("%Y-%m-%d-%H", time.localtime())
        if os.path.exists("/www/server/btwaf/webshell_total/" + today + ".json"):
            try:
                data = []
                webshell_info = json.loads(public.ReadFile("/www/server/btwaf/webshell_total/" + today + ".json"))
                for i in webshell_info:
                    if i not in data:
                        data.append(i)
                webshell_re = self.upload_shell(data)
                if len(webshell_re) >= 1:
                    print("扫描完成 发现存在%s个木马文件 时间:%s" % (
                    len(webshell_re), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
                else:
                    print("扫描完成未发现存在木马文件 时间:%s" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                return
            except:
                pass
        print("扫描完成未发现存在木马文件 时间:%s" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

    def return_python(self):
        if os.path.exists('/www/server/panel/pyenv/bin/python'): return '/www/server/panel/pyenv/bin/python'
        if os.path.exists('/usr/bin/python'): return '/usr/bin/python'
        if os.path.exists('/usr/bin/python3'): return '/usr/bin/python3'
        return 'python'

if __name__ == "__main__":
    webshell_check = webshell_check()
    webshell_check.san_dir()