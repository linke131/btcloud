# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang<hwliang@bt.cn>
# +-------------------------------------------------------------------

# +--------------------------------------------------------------------
# |   宝塔事件型防篡改
# +--------------------------------------------------------------------
import sys
sys.path.insert(0, '/www/server/panel/class')
import os, pyinotify, public, json, shutil, time, psutil, re
import threading
import datetime

class MyEventHandler(pyinotify.ProcessEvent):
    _PLUGIN_PATH = "/www/server/panel/plugin/tamper_proof"
    __CONFIG = '/config.json'
    _SITES = '/sites.json'
    _SITES_DATA = None
    __CONFIG_DATA = None
    _DONE_FILE = None
    bakcupChirdPath = []

    def rmdir(self, filename):
        try:
            shutil.rmtree(filename)
        except:
            pass

    def check_site_logs(self, Stiename, datetime_time):
        ret = []
        cur_month = datetime_time.month
        cur_day = datetime_time.day
        cur_year = datetime_time.year
        cur_hour = datetime_time.hour
        cur_minute = datetime_time.minute
        cur_second = int(datetime_time.second)
        months = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07',
                  'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
        logs_data = self.get_site_logs(Stiename)
        if not logs_data: return False
        for i2 in logs_data:
            try:
                i = i2.split()
                # 判断状态码是否为200
                if int(i[8]) not in [200, 500]: continue
                # 判断是否为POST
                day_time = i[3].split('/')[0].split('[')[1]
                if int(cur_day) != int(day_time): continue
                month_time = i[3].split('/')[1]
                if int(months[month_time]) != int(cur_month): continue
                year_time = i[3].split('/')[2].split(':')[0]
                if int(year_time) != int(cur_year): continue
                hour_time = i[3].split('/')[2].split(':')[1]
                if int(hour_time) != int(cur_hour): continue
                minute_time = i[3].split('/')[2].split(':')[2]
                if int(minute_time) != int(cur_minute): continue
                second_time = int(i[3].split('/')[2].split(':')[3])
                if cur_second - second_time > 10: continue
                ret.append(i2)
            except:
                continue
        ret2 = []
        if len(ret) > 20:
            for i2 in logs_data:
                try:
                    i = i2.split()
                    if i[6] != 'POST': continue
                    if int(i[8]) not in [200, 500]: continue
                    # 判断是否为POST
                    day_time = i[3].split('/')[0].split('[')[1]
                    if int(cur_day) != int(day_time): continue
                    month_time = i[3].split('/')[1]
                    if int(months[month_time]) != int(cur_month): continue
                    year_time = i[3].split('/')[2].split(':')[0]
                    if int(year_time) != int(cur_year): continue
                    hour_time = i[3].split('/')[2].split(':')[1]
                    if int(hour_time) != int(cur_hour): continue
                    minute_time = i[3].split('/')[2].split(':')[2]
                    if int(minute_time) != int(cur_minute): continue
                    ret2.append(i2)
                except:
                    continue
        if ret2:
            ret = ret2
        if len(ret) > 20:
            return ret[0:20]
        return ret

    def get_site_logs(self, Stiename):
        try:
            pythonV = sys.version_info[0]
            path = '/www/wwwlogs/' + Stiename + '.log'
            num = 500
            if not os.path.exists(path): return []
            p = 1
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
            c = 0
            while c < count:
                while True:
                    newline_pos = str.rfind(buf, "\n")
                    pos = fp.tell()
                    if newline_pos != -1:
                        if n >= start_line:
                            line = buf[newline_pos + 1:]
                            if line:
                                try:
                                    data.append(line)
                                except:
                                    c -= 1
                                    n -= 1
                                    pass
                            else:
                                c -= 1
                                n -= 1
                        buf = buf[:newline_pos]
                        n += 1
                        c += 1
                        break
                    else:
                        if pos == 0:
                            b = False
                            break
                        to_read = min(4096, pos)
                        fp.seek(-to_read, 1)
                        t_buf = fp.read(to_read)
                        if pythonV == 3: t_buf = t_buf.decode('utf-8', errors="ignore")
                        buf = t_buf + buf
                        fp.seek(-to_read, 1)
                        if pos - to_read == 0:
                            buf = "\n" + buf
                if not b: break
            fp.close()
        except:
            data = []
        return data

    def process_IN_CREATE(self, event):
        siteInfo = self.get_SITE_CONFIG(event.pathname)
        if not self.check_FILE(event, siteInfo, True): return False
        self._DONE_FILE = event.pathname
        try:
            src_path = os.path.dirname(event.pathname).replace(" ", "\ ")
            os.system("chattr -a {}".format(src_path))
            os.rmdir(event.pathname) if os.path.isdir(event.pathname) else os.remove(event.pathname)
            os.system("chattr +a {}".format(src_path))
            self.write_LOG('create', siteInfo['siteName'], event.pathname, datetime.datetime.now())
        except:
            print("create 报错了")

    def process_IN_MOVED_FROM(self, event):
        print("process_IN_MOVED_FROM  ", event)

    def process_IN_MOVED_TO(self, event):
        # 检查是否受保护
        try:
            siteInfo = self.get_SITE_CONFIG(event.pathname)
            if not self.check_FILE(event, siteInfo): return False
            if not getattr(event, 'src_pathname', None):
                if os.path.isdir(event.pathname):
                    self.rmdir(event.pathname)
                else:
                    os.remove(event.pathname)
                self.write_LOG('move', siteInfo['siteName'], '未知 -> ' + event.pathname, datetime.datetime.now())
                return True

            if event.src_pathname == self._DONE_FILE: return False
            if not os.path.exists(event.src_pathname):
                self._DONE_FILE = event.pathname
                os.renames(event.pathname, event.src_pathname)
            self.write_LOG('move', siteInfo['siteName'], event.src_pathname + ' -> ' + event.pathname, datetime.datetime.now())
        except:
            pass

    def check_FILE(self, event, siteInfo, create=False):
        if not siteInfo: return False
        if self.exclude_PATH(event.pathname):
            return False
        if event.dir and create: return True
        if not event.dir:
            if not self.protect_EXT(event.pathname):
                return False
        return True

    def protect_EXT(self, pathname):
        if pathname.find('.') == -1: return False
        extName = pathname.split('.')[-1].lower()
        siteData = self.get_SITE_CONFIG(pathname)
        if siteData:
            if pathname in siteData['protectExt']:
                return True
            if extName in siteData['protectExt']:
                return True
        return False

    def exclude_PATH(self, pathname):
        if pathname.find('/') == -1: return False
        siteData = self.get_SITE_CONFIG(pathname)
        return self.exclude_PATH_OF_SITE(pathname, siteData['excludePath'])

    def exclude_PATH_OF_SITE(self, pathname, excludePath):
        pathname = pathname.lower()
        dirNames = pathname.split('/')
        if excludePath:
            if pathname in excludePath:
                return True
            if pathname + '/' in excludePath:
                return True
            for ePath in excludePath:
                if ePath in dirNames: return True
                if pathname.find(ePath) == 0: return True
        return False

    def get_SITE_CONFIG(self, pathname):
        if not self._SITES_DATA: self._SITES_DATA = json.loads(public.readFile(self._PLUGIN_PATH + self._SITES))
        for site in self._SITES_DATA:
            re_str = "({}/)".format(site['path'])
            result = re.findall(re_str, pathname)
            if not result: continue
            return site
        return None

    def get_CONFIG(self):
        if self.__CONFIG_DATA: return self.__CONFIG_DATA
        self.__CONFIG_DATA = json.loads(public.readFile(self._PLUGIN_PATH + self.__CONFIG))

    def list_DIR(self, path, siteInfo):  # path 站点路径
        if not os.path.exists(path): return
        lock_files = []
        lock_dirs = []
        explode_a = ['log', 'logs', 'cache', 'templates', 'template', 'upload', 'img', 'image', 'images', 'public', 'static', 'js', 'css', 'tmp', 'temp', 'update', 'data']
        for name in os.listdir(path):
            try:
                filename = "{}/{}".format(path, name).replace('//', '/')
                lower_name = name.lower()
                lower_filename = filename.lower().replace(' ', '\ ')
                if " " in filename:
                    filename = filename.replace(" ", "\ ")
                if os.path.isdir(filename.replace("\ ", " ")):  # 是否为目录
                    if lower_name in siteInfo['excludePath']: continue  # 是否为排除的文件名
                    if not self.exclude_PATH_OF_SITE(filename, siteInfo['excludePath']):  # 是否为排除目录
                        if not lower_name in explode_a:  # 是否为固定不锁定目录
                            lock_dirs.append('"' + name + '"')
                        self.list_DIR(filename.replace('\ ', ' '), siteInfo)
                    continue
                if not lower_name in siteInfo['protectExt'] and not lower_filename.replace('\ ', ' ') in siteInfo['protectExt']:  # 是否为受保护的文件名或文件全路径
                    if not self.get_EXT_NAME(lower_name) in siteInfo['protectExt']: continue  # 是否为受保护文件类型
                if lower_filename in siteInfo['excludePath']: continue  # 是否为排除文件
                if lower_name in siteInfo['excludePath']: continue  # 是否为排除的文件名
                lock_files.append('"' + name + '"')
            except:
                print(public.get_error_info())
        if lock_files:
            self.thread_exec(lock_files, path, 'i')
        if lock_dirs:
            self.thread_exec(lock_dirs, path, 'a')

    _thread_count = 0
    _thread_max = 2 * psutil.cpu_count()

    def thread_exec(self, file_list, cwd, i='i'):
        while self._thread_count > self._thread_max:
            time.sleep(0.1)

        self._thread_count += 1
        cmd = "cd {} && chattr +{} {} > /dev/null".format(cwd.replace(' ', '\ '), i, ' '.join(file_list))
        if len(file_list) > 10000: cmd = "cd {} && chattr +{} * > /dev/null".format(cwd, i)
        p = threading.Thread(target=self.run_thread, args=(cmd,))
        p.start()

    def run_thread(self, cmd):
        os.system(cmd)
        self._thread_count -= 1

    def get_EXT_NAME(self, fileName):
        return fileName.split('.')[-1]

    def write_LOG(self, eventType, siteName, pathname, datetime):
        # 获取网站时间的top100 记录
        site_log = '/www/wwwlogs/%s.log' % siteName
        logs_data = []
        if os.path.exists(site_log):
            logs_data = self.check_site_logs(siteName, datetime)
        dateDay = time.strftime("%Y-%m-%d", time.localtime())
        logPath = self._PLUGIN_PATH + '/sites/' + siteName + '/bt_tamper_proof_total/' + dateDay
        if not os.path.exists(logPath): os.makedirs(logPath)
        logFile = os.path.join(logPath, 'logs.json')
        logVar = [int(time.time()), eventType, pathname, logs_data]
        fp = open(logFile, 'a+')
        fp.write(json.dumps(logVar) + "\n")
        fp.close()
        logFiles = [
            logPath + '/total.json',
            self._PLUGIN_PATH + '/sites/' + siteName + '/bt_tamper_proof_total/total.json',
            self._PLUGIN_PATH + '/sites/total.json'
        ]

        for totalLogFile in logFiles:
            if not os.path.exists(totalLogFile):
                totalData = {"total": 0, "delete": 0, "create": 0, "modify": 0, "move": 0}
            else:
                dataTmp = public.readFile(totalLogFile)
                if dataTmp:
                    totalData = json.loads(dataTmp)
                else:
                    totalData = {"total": 0, "delete": 0, "create": 0, "modify": 0, "move": 0}

            totalData['total'] += 1
            totalData[eventType] += 1
            public.writeFile(totalLogFile, json.dumps(totalData))

    # 设置.user.ini
    def set_user_ini(self, path, up=0):
        os.chdir(path)
        useriniPath = path.replace(' ', '\ ') + '/.user.ini'
        if os.path.exists(useriniPath):
            os.system('chattr +i ' + useriniPath)
        for p1 in os.listdir(path):
            try:
                npath = path + '/' + p1
                if not os.path.isdir(npath): continue
                useriniPath = npath + '/.user.ini'
                if os.path.exists(useriniPath):
                    os.system('chattr +i ' + useriniPath)
                if up < 3: self.set_user_ini(npath, up + 1)
            except:
                continue
        return True

    def unlock(self, path):
        a_path = path.replace(' ', '\ ')
        os.system('chattr -R -i {} &> /dev/null'.format(a_path))
        os.system('chattr -R -a {} &> /dev/null'.format(a_path))
        self.set_user_ini(path)

    def close(self, reload=False):
        # 解除锁定
        sites = self.get_sites()
        print("")
        print("=" * 60)
        print("【{}】正在关闭防篡改，请稍候...".format(public.format_date()))
        print("-" * 60)
        for siteInfo in sites:
            tip = self._PLUGIN_PATH + '/tips/' + siteInfo['siteName'] + '.pl'
            if not siteInfo['open'] and not os.path.exists(tip): continue
            if reload and siteInfo['open']: continue
            if sys.version_info[0] == 2:
                print("【{}】|-解锁网站[{}]".format(public.format_date(), siteInfo['siteName'])),
            else:
                os.system("echo -e '【{}】|-解锁网站[{}]\c'".format(public.format_date(), siteInfo['siteName']))
                # print("【{}】|-解锁网站[{}]".format(public.format_date(),siteInfo['siteName']),end=" ")
            if not os.path.exists(siteInfo['path']):
                print("\t=> {}目录不存在，关闭失败！".format(siteInfo['path']))
                continue
            self.unlock(siteInfo['path'])
            if os.path.exists(tip): os.remove(tip)
            print("\t=> 完成")
        print("-" * 60)
        print('|-防篡改已关闭')
        print("=" * 60)
        # print(">>>>>>>>>>BT-END<<<<<<<<<<")

    # 获取网站配置列表
    def get_sites(self):
        site_data = {}
        site_data['site'] = public.M('sites').field('id,name,path,status,ps,addtime,project_type,project_config').select()
        site_data['domain'] = public.M('domain').field('pid,name,port,addtime').select()
        siteconf = self._PLUGIN_PATH + '/sites.json'
        d = public.readFile(siteconf)
        if not os.path.exists(siteconf) or not d:
            public.writeFile(siteconf, "[]")
        data = json.loads(public.readFile(siteconf))

        # 处理多余字段开始 >>>>>>>>>>
        is_write = False
        rm_keys = ['lock', 'bak_open']
        for i in data:
            i_keys = i.keys()
            if not 'open' in i_keys: i['open'] = False
            for o in rm_keys:
                if o in i_keys:
                    if i[o]: i['open'] = True
                    i.pop(o)
                    is_write = True
        if is_write: public.writeFile(siteconf, json.dumps(data))
        # 处理多余字段结束 <<<<<<<<<<<<<

        # 处理后期修改网站目录后防篡改同步配置
        k_list = []
        for i in site_data['domain']:
            k_data = {}
            for j in site_data['site']:
                if i['pid'] == j['id']:
                    k_data['domain'] = i['name']
                    k_data['path'] = j['path']
                    k_list.append(k_data)
        del site_data
        del k_data
        j_list = []
        for i in k_list:
            for j in data:
                if i['domain'] == j['siteName']:
                    j['path'] = i['path']
                    j_list.append(j)
        data = j_list

        del k_list
        del j_list
        # 后期修改网站目录后防篡改配置异常处理结束
        return data

    def __enter__(self):
        self.close()

    def __exit__(self, a, b, c):
        self.close()


def run():
    # 初始化inotify对像
    event = MyEventHandler()
    watchManager = pyinotify.WatchManager()
    starttime = time.time()
    mode = pyinotify.IN_CREATE | pyinotify.IN_MOVED_TO

    # 处理网站属性
    sites = event.get_sites()
    print("=" * 60)
    print("【{}】正在启动防篡改，请稍候...".format(public.format_date()))
    print("-" * 60)
    tip_path = event._PLUGIN_PATH + '/tips/'
    if not os.path.exists(tip_path): os.makedirs(tip_path)
    speed_file = event._PLUGIN_PATH + '/speed.pl'
    for siteInfo in sites:
        s = time.time()
        tip = tip_path + siteInfo['siteName'] + '.pl'
        if not siteInfo['open']: continue
        if sys.version_info[0] == 2:
            print("【{}】|-网站[{}]".format(public.format_date(), siteInfo['siteName'])),
        else:
            os.system("echo -e '【{}】|-网站[{}]\c'".format(public.format_date(), siteInfo['siteName']))
            # print("【{}】|-网站[{}]".format(public.format_date(),siteInfo['siteName']),end=" ")
        if not os.path.exists(siteInfo['path']):
            print("\t\t=> {}目录不存在，开启防篡改失败！".format(siteInfo['path']))
            continue
        public.writeFile(speed_file, "正在处理网站[{}]，请稍候...".format(siteInfo['siteName']))
        if not os.path.exists(tip):
            event.list_DIR(siteInfo['path'], siteInfo)
        try:
            watchManager.add_watch(siteInfo['path'], mode, auto_add=True, rec=True)
        except:
            print(public.get_error_info())
        tout = round(time.time() - s, 2)
        public.writeFile(tip, '1')
        print("\t\t=> 完成，耗时 {} 秒".format(tout))

    # 启动服务
    endtime = round(time.time() - starttime, 2)
    public.WriteLog(u'防篡改程序', u"网站防篡改服务已成功启动,耗时[%s]秒" % endtime)
    notifier = pyinotify.Notifier(watchManager, event)
    print("-" * 60)
    print('|-防篡改服务已启动')
    print("=" * 60)
    end_tips = ">>>>>>>>>>BT-END<<<<<<<<<<"
    print(end_tips)
    public.writeFile(speed_file, end_tips)
    notifier.loop()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if 'stop' in sys.argv:
            event = MyEventHandler()
            event.close()
        elif 'start' in sys.argv:
            run()
        elif 'unlock' in sys.argv:
            event = MyEventHandler()
            event.unlock(sys.argv[2])
        elif 'reload' in sys.argv:
            event = MyEventHandler()
            event.close(True)
        else:
            print('args error')

    else:
        run()