# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x7
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: lkqiang<lkq@bt.cn>
# +-------------------------------------------------------------------
# |   webshell 扫描插件
# +--------------------------------------------------------------------
import sys
if not '/www/server/panel/class/' in sys.path:
    sys.path.insert(0, '/www/server/panel/class/')
import json, os, time, public, string, re, hashlib,requests
class webshell_check_main:
    __count=0
    __size="/www/server/panel/plugin/webshell_check/size.txt"
    __shell="/www/server/panel/plugin/webshell_check/shell.txt"
    __user={}

    def __init__(self):
        try:
            self.__user = json.loads(public.ReadFile('/www/server/panel/data/userInfo.json'))
        except:
            pass



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
    def ReadFile(self,filename, mode='rb'):
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

    '''
    @name 获取文件的md5值
    @param filename 文件路径
    @return MD5
    '''
    def read_file_md5(self, filename):
        if os.path.exists(filename):
            with open(filename, 'rb') as fp:
                data = fp.read()
            file_md5 = hashlib.md5(data).hexdigest()
            return file_md5
        else:
            return False

    '''
    @name 上传到云端判断是否是webshell
    @param filename 文件路径
    @param url 云端URL
    @return bool 
    '''
    def webshellchop(self,filename,url):
        try:
            upload_url =url
            size = os.path.getsize(filename)
            if size > 1024000: return False
            if len(self.__user)==0:return  False
            upload_data = {'inputfile': self.ReadFile(filename), "md5": self.read_file_md5(filename),"path":filename,"access_key": self.__user['access_key'], "uid": self.__user['uid'],"username":self.__user["username"]}
            upload_res = requests.post(upload_url, upload_data, timeout=20).json()
            if upload_res['msg']=='ok':
                if (upload_res['data']['data']['level']==5):
                    print('%s文件为木马  hash:%s' % (filename,upload_res['data']['data']['hash']))
                    shell_insert={'filename':filename,"hash":upload_res['data']['data']['hash']}
                    if os.path.exists(self.__shell):
                        public.WriteFile(self.__shell,json.dumps(shell_insert)+"\n","a+")
                    else:
                        public.WriteFile(self.__shell,json.dumps(shell_insert)+"\n")
                    self.send_baota2(filename)
                    return True
                elif upload_res['data']['level'] >= 3:
                    print('%s可疑文件,建议手工检查' % filename)
                    self.send_baota2(filename)
                    return False
                return False
        except:
            return False
    '''
    @name 上传到宝塔云端
    @param filename 文件路径
    @return bool 
    '''
    def send_baota2(self, filename):
        cloudUrl = 'http://www.bt.cn/api/panel/btwaf_submit'
        pdata = {'codetxt': self.ReadFile(filename), 'md5': self.read_file_md5(filename), 'type': '0',
                 'host_ip': public.GetLocalIp(), 'size': os.path.getsize(filename)}
        ret = public.httpPost(cloudUrl, pdata)
        return True

    '''
    @name 上传文件入口
    @param filename 文件路径
    @return bool 
    '''
    def upload_file_url2(self, filename,url):
        try:
            if os.path.exists(filename):
                ret=self.webshellchop(filename,url)
                if  ret:
                    return True
                return False
            else:
                return False
        except:
            return False

    '''
    @name 获取云端URL地址
    @return URL 
    '''
    def get_check_url(self):
        try:
            ret=requests.get('http://www.bt.cn/checkWebShell.php').json()
            if ret['status']:
                return ret['url']
            return False
        except:
            return False

    '''
    @name 上传文件
    @param data 文件路径集合
    @return 返回webshell 路径
    '''
    def upload_shell(self, data):
        if len(data) == 0: return []
        return_data = []
        url=self.get_check_url()
        if not url: return []
        count=0
        for i in data:
            count+=1
            if self.upload_file_url2(i,url):
                return_data.append(i)
            schedule=("%.2f" % (float(count)/float(self.__count)*100))
            public.WriteFile(self.__size,str(schedule))
        return return_data

    '''
    @name 获取当前目录下所有PHP文件
    '''
    def getdir_list(self, path_data):
        if os.path.exists(str(path_data)):
            return self.get_dir(path_data)
        else:
            return False

    '''
    @name 扫描webshell入口函数
    @param path 需要扫描的路径
    @return  webshell 路径集合
    '''
    def san_dir(self, path):
        self.__count=0
        file = self.getdir_list(path)
        if not file:
            return []
        ##进度条
        print(file)
        self.__count=len(file)
        return_data = self.upload_shell(file)
        #写结果

        return return_data

    # 返回站点
    def return_site(self, get):
        data = public.M('sites').field('name,path').select()
        ret = {}
        for i in data:
            ret[i['name']] = i['path']
        return public.returnMsg(True, ret)

    def return_python(self):
        if os.path.exists('/www/server/panel/pyenv/bin/python'):return '/www/server/panel/pyenv/bin/python'
        if os.path.exists('/usr/bin/python'):return '/usr/bin/python'
        if os.path.exists('/usr/bin/python3'):return '/usr/bin/python3'
        return 'python'

    def san_path(self,get):
        if os.path.exists(self.__size):
            os.remove(self.__size)
        if os.path.exists(self.__shell):
            os.remove(self.__shell)
        if not  'path' in get:return public.returnMsg(False, "目录不存在")
        if  not os.path.exists(get.path):return public.returnMsg(False, "目录不存在")
        file_count = self.getdir_list(get.path)
        print(file_count)
        if not  file_count or len(file_count)==0:return public.returnMsg(False, "当前目录下没有PHP文件")
        #检查当前是否存在有运行的查杀进程
        webshell_count=public.ExecShell("ps -aux |grep webshell_check_main.py |wc -l")
        try:
            count=int(webshell_count[0].strip())
            if count>2:
                pid = public.ExecShell("ps -aux | grep webshell_check_main.py | grep -v grep | awk '{print $2}'")
                public.ExecShell("kill -9 {}".format(pid[0].strip()))
                # return public.returnMsg(False, "当前存在木马查杀进程。不支持同时运行多个查杀进程")
        except:
            return public.returnMsg(False, "启动扫描进程失败,请检查是否存在查杀进程")
        shell="%s /www/server/panel/plugin/webshell_check/webshell_check_main.py %s &"%(self.return_python(),get.path.strip())
        public.ExecShell(shell)
        return public.returnMsg(True, "已经启动扫描进程")

    #获取进度
    def get_san(self,get):
        if not os.path.exists(self.__size):return 0
        data3=public.ReadFile(self.__size)
        if isinstance(data3,str):
            data3=data3.strip()
            try:
                data=int(float(data3))
            except:
                data=0
            return data
        return 0

    #读取扫描后的文件
    def get_shell(self,get):
        time.sleep(1)
        ret=[]
        count=1
        ret.append(["序号", "hash", "路径"])
        if not os.path.exists("/www/server/panel/plugin/webshell_check/shell.txt"):return []
        f = open("/www/server/panel/plugin/webshell_check/shell.txt",'r')
        for i in f:
            try:
                i=i.strip()
                i=json.loads(i)
                ret.append(["%s"%count,"%s"%i['hash'],i['filename']])
                count+=1
            except:
                continue
        return ret


    #提交误报
    def send_baota(self,get):
        userInfo = json.loads(public.ReadFile('/www/server/panel/data/userInfo.json'))
        cloudUrl = 'http://www.bt.cn/api/bt_waf/reportTrojanError'
        pdata = {'name':get.filename,'inputfile': self.ReadFile(get.filename), "md5": self.read_file_md5(get.filename),"access_key": userInfo['access_key'], "uid": userInfo['uid'],"username":self.__user["username"]}
        ret = public.httpPost(cloudUrl, pdata)
        return public.returnMsg(True, "提交误报完成")

    def remove_file(self,get):
        import files
        data=files.files()
        get.path=get.filename
        return data.DeleteFile(get)


if __name__ == "__main__":
    data=webshell_check_main()
    path = sys.argv[1]
    file = data.getdir_list(path)
    print(file)
    data.san_dir(path)
