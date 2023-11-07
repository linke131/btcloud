#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2019 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 邹浩文 <627622230@qq.com>
# +-------------------------------------------------------------------

#--------------------------------
# Mysql主从复制
#--------------------------------
import sys
sys.path.append("class/")
import os,public,re,base64,time,json,threading,psutil,socket
os.chdir("/www/server/panel")
import panelMysql as pm

class masterslave_main:
    __mfile = "/etc/my.cnf"
    setpath = "/www/server/panel"
    logfile = "%s/plugin/masterslave/setslave.log" % setpath
    totalspeedfile = "%s/plugin/masterslave/speed.log" % setpath
    datafile = "%s/plugin/masterslave/data.json" % setpath
    def GetMasterInfo(self,get):
        """
            @name 获取主库信息
            @author zhwen<zhw@bt.cn>
            @return masterinfo dict
        """
        master_version = self.GetVersion()
        master_id = re.search("server-id\s+=\s+(\d+)", public.readFile("/etc/my.cnf")).group(1)
        masterinfo = {
            "slave_user": self.GetRandomString(9),
            "slave_pass": self.GetRandomString(9),
            "btmysql": self.GetRandomString(9),
            "master_port": str(self.GetMysqlPort()),
            "master_version": str(master_version),
            "master_dbs": self.GetDbs(get),
            "master_id": master_id,
            "slave_id": [(int(master_id)+1)]
        }
        return masterinfo

    def GetVersion(self):
        """
            @name 获取数据库版本号
            @author zhwen<zhw@bt.cn>
            @return master_version str
        """
        master_version = pm.panelMysql().query("select version()")[0][0].split(".")
        master_version = master_version[0] + "." + master_version[1]
        return master_version

    def GetMysqlPort(self):
        """
            @name  获取数据库端口号
            @author zhwen<zhw@bt.cn>
            @return port int
        """
        try:
            port = pm.panelMysql().query("show global variables like 'port'")[0][1]
        except:
            return False
        if not port:
            return False
        else:
            return int(port)

    def GetDbs(self,get=None):
        """
            @name  获取数据库所有数据库
            @author zhwen<zhw@bt.cn>
            @return dbs list
        """
        # 判断mysql是否启动
        if not self.GetMysqlPort():
            print('请确定数据库已经开启或尝试重置数据库ROOT密码')
            return public.returnMsg(False, '请确定数据库已经开启或尝试重置数据库ROOT密码')
        master_version = pm.panelMysql().query("select version()")[0][0].split("-")[0]
        if "5.1." in master_version:
            return public.returnMsg(False, '本插件不支持5.1版本MYSQL，请安装5.5或以上版本')
        ms = pm.panelMysql().query("show databases")
        dbs = []
        for i in ms:
            if i[0] != "information_schema" and i[0] != "performance_schema" and i[0] != "sys":
                dbs.append(i[0])
        return dbs

    def GetLocalIP(self):
        """
            @name  获取本机ip
            @author zhwen<zhw@bt.cn>
            @return ip str
        """
        #获取本机ip
        ip = []
        result = psutil.net_if_addrs()
        for k, v in result.items():
            for item in v:
                if item[0] == 2 and not item[1] == '127.0.0.1':
                    ip.append((item[1]))
        return ip

    def CheckPort(self,ip,port):
        """
            @name  检查mysql端口是否能连接
            @author zhwen<zhw@bt.cn>
        """
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sk.settimeout(5)
        try:
            sk.connect((ip, int(port)))
            return True
        except Exception as e:
            return False

    def CreateSalveUser(self,masterinfo,slave_ip):
        """
            @name  创建同步用的用户
            @author zhwen<zhw@bt.cn>
        """
        pm.panelMysql().execute("delete from mysql.user where host='%s'" % slave_ip)
        flush_sql = "flush privileges"
        if re.match("8",masterinfo["master_version"]):
            create_btmysql_sql = "create user btmysql@'%s' identified by '%s'" % (slave_ip, masterinfo["btmysql"])
            grant_btmysql_sql = "grant all on *.* to btmysql@'%s'" % slave_ip
            create_slave_sql = "create user %s@'%s' identified by '%s'" % (masterinfo["slave_user"], slave_ip, masterinfo["slave_pass"])
            grant_slave_sql = "grant replication slave on *.* to %s@'%s'" % (masterinfo["slave_user"], slave_ip)
        else:
            grant_btmysql_sql = ""
            grant_slave_sql = ""
            create_btmysql_sql = "grant all on *.* to btmysql@'%s' identified by '%s'" % (slave_ip,masterinfo["btmysql"])
            create_slave_sql = "grant replication slave on *.* to %s@'%s' identified by '%s'" % (masterinfo["slave_user"],slave_ip, masterinfo["slave_pass"])
        for i in [flush_sql,create_btmysql_sql,create_slave_sql,grant_btmysql_sql,grant_slave_sql,flush_sql]:
            pm.panelMysql().execute(i)

    def CheckBinLog(self):
        """
            @name  检查数据库二进制日志是否已经开启
            @author zhwen<zhw@bt.cn>
        """
        mconf = public.readFile(self.__mfile)
        sidrep = "\nlog-bin=mysql-bin"
        if not re.search(sidrep,mconf):
            return False
        else:
            return True

    def _check_parameter(self,get):
        if not self.GetPort(get):
            return public.returnMsg(False, '请确定数据库已经开启或尝试重置数据库ROOT密码')
        iprep = "(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})\.(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})\.(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})\.(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})"
        if re.search(iprep, get.slave_ip):
            slave_ip = re.search(iprep, get.slave_ip).group()
        else:
            return public.returnMsg(False, '请输入正确的IP地址')
        ip = self.GetLocalIP()
        for i in ip:
            if i == slave_ip:
                return public.returnMsg(False, '不能输入本机的IP')
        try:
            slave_port = int(get.slave_port)
            if slave_port >= 65535 or slave_port < 1:
                return public.returnMsg(False, '请输入正确的端口号')
        except:
            return public.returnMsg(False, '请输入正确的端口号')
        if not self.CheckBinLog():
            return public.returnMsg(False, '请先开启Mysql二进制日志')
        if not self.CheckPort(slave_ip,slave_port):
            return public.returnMsg(False, '无法访问从服务器<br>请确认安全组是否已经放行<br>Mysql端口：%s' % slave_port)
        return {'slave_ip':slave_ip,'slave_port':slave_port}

    def _build_replicate_dbs(self,get,masterinfo):
        """
            @name  构造需要同步的数据库列表
            @author zhwen<zhw@bt.cn>
        """
        dbmsg = []
        if masterinfo["replicate_dbs"][0] == "alldatabases":
            for i in self.GetDbs(get):
                if i != "mysql":
                    d = public.M('databases').where('name=?', ('%s' % i,)).find()
                    dbmsg.append(d)
        else:
            for i in masterinfo["replicate_dbs"]:
                d = public.M('databases').where('name=?', (i,)).find()
                dbmsg.append(d)
        return dbmsg

    def _restart_mysql(self):
        """
            @name  重启数据库，最多尝试重启10次
            @author zhwen<zhw@bt.cn>
        """
        self.WriteLog("重启mysql")
        pid_old = public.ExecShell("ps aux|grep 'mysql.sock'|awk 'NR==1 {print $2}'")[0].split("\n")[0]
        self.WriteLog("旧PID %s" % pid_old)
        pid_new = pid_old
        public.writeFile("/tmp/mysqlpid", "")
        n=0
        # 重启数据库，最多尝试10次
        for i in range(10):
            if i == 0:
                public.ExecShell("/etc/init.d/mysqld restart &")
                time.sleep(60)
                pid_new = public.ExecShell("ps aux|grep 'mysql.sock'|awk 'NR==1 {print $2}'")[0].split("\n")[0]
                self.WriteLog("新PID %s" % pid_new)
            if pid_old == pid_new:
                time.sleep(60)
                pid_new = public.ExecShell("ps aux|grep 'mysql.sock'|awk 'NR==1 {print $2}'")[0].split("\n")[0]
            else:
                public.writeFile("/tmp/mysqlpid", "ok")
                n+=1
                break
        return n

    def _set_mysql_gtid_conf(self,masterinfo,mconf):
        """
            @name  设置mysql5.6-8.0 以gtid模式同步
            @author zhwen<zhw@bt.cn>
        """
        addconf = """
        log-slave-updates=true
        enforce-gtid-consistency=true
        gtid-mode=on"""
        if "5.5" not in masterinfo["master_version"] and not re.match("10", masterinfo["master_version"]):
            if re.search("gtid-mode=on", mconf):
                return True
            mconf = re.sub("\[mysqld\]", "[mysqld]" + addconf, mconf)
            public.writeFile(self.__mfile, mconf)
            if self._restart_mysql() == 0:
                return False


    def SetMaster(self,get):
        """
            @name  设置主服务器配置
            @author zhwen<zhw@bt.cn>
        """
        check_result = self._check_parameter(get)
        if isinstance(check_result,dict) and check_result.get('msg'):
            return check_result
        slave_ip = check_result['slave_ip']
        slave_port = check_result['slave_port']
        mconf = public.readFile(self.__mfile)
        masterinfo = self.GetMasterInfo(get)
        masterinfo["replicate_dbs"] = json.loads(get.replicate_dbs)
        dbmsg = self._build_replicate_dbs(get,masterinfo)
        masterinfo["slave_ip"] = [slave_ip]
        masterinfo["slave_port"] = [str(slave_port)]
        masterinfo["replicate_dbs_info"] = dbmsg

        if masterinfo["replicate_dbs"][0] == "alldatabases":
            masterinfo["slave_ips"] = public.M('config').where('id=?', (1,)).getField('mysql_root')
        self._set_mysql_gtid_conf(masterinfo,mconf)
        time.sleep(1)
        self.CreateSalveUser(masterinfo,slave_ip)

        masterinfo = json.dumps(masterinfo)
        try:
            keys = base64.b64encode(masterinfo)
        except:
            keys = str(base64.b64encode(masterinfo.encode('utf-8')), 'utf-8')
        public.writeFile(self.datafile, masterinfo)
        return keys

    def GetKeys(self,get):
        """
            @name  获取主服务器同步插件需要要的KEY
            @author zhwen<zhw@bt.cn>
        """
        masterinfo = public.readFile(self.datafile)
        if not masterinfo:
            return False
        if "master_ip" in json.loads(masterinfo).keys():
            return public.returnMsg(False, "该服务器为从服务器，无法获取key")
        try:
            return base64.b64encode(masterinfo)
        except:
            b = base64.b64encode(bytes(masterinfo,encoding = "utf8"))
            return bytes.decode(b)

    def GetRandomString(self,length):
        """
            @name  构造随机字符串
            @author zhwen<zhw@bt.cn>
            @param length 字符串长度
        """
        from random import Random
        strings = ''
        chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
        chrlen = len(chars) - 1
        random = Random()
        for i in range(length):
            strings += chars[random.randint(0, chrlen)]
        return strings

    def __ExceSql(self,*args, **kwargs):
        """
            @name  使用ssh命令执行sql
            @author zhwen<zhw@bt.cn>
            @param
        """
        try:
            if kwargs:
                ip = kwargs["masterinfo"]["master_ip"]
                port = kwargs["masterinfo"]["master_port"]
                user = "btmysql"
                passwd = kwargs["masterinfo"]["btmysql"]
            else:
                ip = args[0]
                port = args[1]
                user = args[2]
                passwd = args[3]
            sql = args[-1]
            result = public.ExecShell("/usr/bin/mysql -h%s -P%s --connect_timeout=3 -u%s -p%s  -e '%s'" % (ip, port, user, passwd, sql))
        except:
            result = False
        return result

    def WriteLog(self, msg):
        """
            @name  写入mysql同步创建时的日志
            @author zhwen<zhw@bt.cn>
            @param
        """
        localtime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
        if not os.path.exists(self.logfile):
                public.ExecShell("touch %s" % self.logfile)
        public.writeFile(self.logfile,localtime+"\n"+msg+"\n","a+")

    def SetTotalSpeed(self,msg):
        """
            @name  设置同步总进度
            @author zhwen<zhw@bt.cn>
            @param
        """
        if not os.path.exists(self.totalspeedfile):
                public.ExecShell("touch %s" % self.totalspeedfile)
        public.writeFile(self.totalspeedfile,json.dumps(msg))

    def GetTotalSpeed(self,get):
        """
            @name  获取设置同步总进度
            @author zhwen<zhw@bt.cn>
            @param
        """
        if not os.path.exists(self.totalspeedfile):
            public.ExecShell("touch %s" % self.totalspeedfile)
            public.writeFile(self.totalspeedfile,json.dumps({"total":"1"}))
        s = public.readFile(self.totalspeedfile)
        return json.loads(s)

    def CheckMasterOrSlave(self,get):
        """
            @name  检查本服务器是主服务器还是从服务器
            @author zhwen<zhw@bt.cn>
            @param
        """
        conf = public.readFile(self.datafile)
        if os.path.exists(self.datafile) and conf:
            if "master_ip" in json.loads(conf).keys():
                return public.returnMsg(True, "该服务器为从服务器，无法添加从服务器")
            else:
                return public.returnMsg(True, "该服务器为主服务器")
        else:
            return public.returnMsg(False, "该服务器为还没配置主从")

    def AddSalve(self,get):
        """
            @name  添加一个从服务器
            @author zhwen<zhw@bt.cn>
            @param
        """
        if not self.GetPort(get):
            print(self.GetPort(get))
            return public.returnMsg(False, '请确定数据库已经开启或尝试重置数据库ROOT密码')
        conf = public.readFile(self.datafile)
        slave_ip=get.slave_ip
        if os.path.exists(self.datafile) and conf:
            try:
                master_conf = json.loads(conf)
                if "slave_id" not in master_conf.keys():
                    master_conf["slave_id"] = [2]
                slave_id_new = int(master_conf["slave_id"][-1])+1
                master_conf["slave_id"].append(slave_id_new)
                if slave_ip in master_conf["slave_ip"]:
                    return public.returnMsg(False, '该从库已经存在')
                master_conf["slave_ip"].append(slave_ip)
                master_conf["slave_port"].append(get.slave_port)
                master_conf["slave_pass"] = master_conf["slave_pass"]
                master_conf["slave_user"] = master_conf["slave_user"]
                master_conf["btmysql"] = master_conf["btmysql"]

                self.CreateSalveUser(master_conf,slave_ip)
                public.writeFile(self.datafile,json.dumps(master_conf))
                # keys = base64.b64encode(json.dumps(master_conf))
                master_conf = json.dumps(master_conf)
                try:
                    keys = base64.b64encode(master_conf)
                except:
                    keys = str(base64.b64encode(master_conf.encode('utf-8')), 'utf-8')
                return keys
            except:
                return public.returnMsg(False, "添加从服务器出错：{}".format(public.get_error_info()))
        else:
            return public.returnMsg(False, "没有配置主从服务，无法添加从服务器")

    # 获取备份路径
    def get_backup_path(self):

        database_backup_path = public.M('config').where("id=?",('1',)).field('backup_path').find();
        return database_backup_path["backup_path"]

    def get_mysql_datas(self):
        data = None

        if os.path.exists(self.datafile):
            data = json.loads(public.readFile(self.datafile))
        return data

    # 设置任务进度
    def __set_speed(self, data, init_data=False):
        sp_path = self.setpath + '/plugin/masterslave/speed.pl'
        print(data)
        public.writeFile(sp_path, json.dumps(data));
        return True

    # 取任务进度
    def GetSpeed(self, get):
        sp_path = self.setpath + '/plugin/masterslave/speed.pl'
        if not os.path.exists(sp_path): return {'title': "等待备份...", 'progress': 0, 'total': 0, 'used': 0, 'speed': 0}
        data = json.loads(public.readFile(sp_path))

        if 'type' in data:
            if data['type'] == 'backup_database':
                path = self.get_backup_path() + '/masterslave.sql'
                if os.path.exists(path):  data['title'] = data['title'] + ' 备份大小：%s' % (
                    public.to_size(public.get_path_size(path)))
            elif data['type'] == 'import_database':
                masterinfo = self.get_mysql_datas()

                used = 0
                if masterinfo["replicate_dbs"][0] == "alldatabases":
                    try:
                        used = \
                        pm.panelMysql().query("select sum(data_length) as data_length from information_schema.tables")[
                            0][0]
                    except:
                        used = 0
                else:
                    for i in masterinfo["replicate_dbs"]:
                        try:
                            data_len = pm.panelMysql().query(
                                "select sum(data_length) as data_length from information_schema.tables where table_schema='%s'" % i)[
                                0][0]
                            used += data_len
                        except:
                            used += 0
                data['title'] = data['title'] + ' 已完成大小：%s ' % (public.to_size(used))
        return data

                #放行Mysql端口
    def GetPort(self,get):
        """
            @name  为从服务器放行3306端口
            @author zhwen<zhw@bt.cn>
            @param
        """
        try:
            import firewalls
            port = self.GetMysqlPort()

            if port:
                get.port = str(port)
            else:
                return False
            get.ps = 'MySQL'
            firewalls.firewalls().AddAcceptPort(get)
            return port
        except:
            return False

    def _check_slave_parma(self,get):
        # 是否为ip
        iprep = "(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})\.(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})\.(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})\.(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})"
        if re.search(iprep, get.master_ip):
            master_ip = re.search(iprep, get.master_ip).group()
        else:
            return public.returnMsg(False, '请输入正确的IP地址')
        ip = self.GetLocalIP()
        for i in ip:
            if i == master_ip:
                return public.returnMsg(False, '不能输入本机的IP')
        return master_ip

    def _decode_master_key(self,get,master_ip):
        # 解码
        masterinfo = json.loads(base64.b64decode(get.keys))
        masterinfo["master_ip"] = master_ip
        slave_version = self.GetVersion()
        masterinfo["slave_version"] = slave_version
        # 写入data.json供设置速度使用
        self.WriteLog(json.dumps(masterinfo))
        public.writeFile(self.datafile, json.dumps(masterinfo))
        return {'masterinfo':masterinfo,'slave_version':slave_version}

    def _build_master_con_object(self,masterinfo):
        """
            @name  创建主库连接
            @author zhwen<zhw@bt.cn>
            @param
        """
        try:
            import MySQLdb as pym
        except:
            import pymysql as pym
        try:
            master_port = int(masterinfo["master_port"])
        except Exception as e:
            return public.returnMsg(False, e)
        try:
            db = pym.connect(host=masterinfo["master_ip"], port=master_port, user="btmysql",
                             passwd=masterinfo["btmysql"],
                             charset="utf8")
            cur = db.cursor()
        except:
            return public.returnMsg(False, '无法连接主服务器，请确定主服务器 IP端口是否正确，安全组是否已经放行Mysql端口')
        return {'cur':cur,'db':db}

    def _backup_all_db(self,cur,backsh,backsqlpath,masterinfo):
        """
            @name  备份所有数据库
            @author zhwen<zhw@bt.cn>
            @param
        """
        self.WriteLog("开始备份数据库")
        # 开始备份数据库
        try:
            self.WriteLog("备份数据库 %s" % "alldatabases")
            error = public.ExecShell(backsh % (
            masterinfo["master_ip"], masterinfo["master_port"], "btmysql", masterinfo["btmysql"], "--all-databases", "",
            backsqlpath))[1]
            mysqldump_process = public.ExecShell('ps aux|grep mysqldump|grep -v "grep"')[0]
            while mysqldump_process:
                time.sleep(1)
                mysqldump_process = public.ExecShell('ps aux|grep mysqldump|grep -v "grep"')[0]
            if "error" in error or "not exist" in error:
                return public.returnMsg(False, '数据库备份失败 %s\n错误信息：%s\n ,请检测主库是否有问题' % ("alldatabases", error))
        except:
            self.WriteLog("备份失败 %s" % "alldatabases")
            return public.returnMsg(False, '数据库备份失败 %s' % "alldatabases")
        # threading.Thread(target=self.SetSpeed()).start()

    def _backup_specify_db(self,cur,backsh,backsqlpath,masterinfo):
        """
            @name  备份指定数据库
            @author zhwen<zhw@bt.cn>
            @param
        """
        # total_db = 1
        replicate_dbs = ""
        cur.execute("use information_schema")
        for d in masterinfo["replicate_dbs"]:
            replicate_dbs += " %s " % d
        # 开始备份数据库
        try:
            self.WriteLog("备份数据库 %s" % replicate_dbs)
            error = public.ExecShell(backsh % (
                masterinfo["master_ip"], masterinfo["master_port"], "btmysql", masterinfo["btmysql"], "--databases",
                replicate_dbs, backsqlpath))[1]
            mysqldump_process = public.ExecShell('ps aux|grep mysqldump|grep -v "grep"')[0]
            while mysqldump_process:
                time.sleep(1)
                mysqldump_process = public.ExecShell('ps aux|grep mysqldump|grep -v "grep"')[0]
            if "error" in error or "not exist" in error:
                return public.returnMsg(False, '数据库备份失败 %s\n错误信息：%s\n ,请检测主库是否有问题' % ("replicate_dbs", error))
        except:
            self.WriteLog("备份失败 %s" % replicate_dbs)
            return public.returnMsg(False, '数据库备份失败 %s' % replicate_dbs)
        self.WriteLog("备份成功")

    def _get_mysql_replicate_log_info(self,backsqlpath,db,masterinfo,bakpath):
        """
            @name  获取数据库复制的日志信息
            @author zhwen<zhw@bt.cn>
            @param
        """
        masterlogdata = public.ExecShell("head -n 50 %s" % backsqlpath)
        try:
            masterlogdata = masterlogdata[0]
            rep = "CHANGE MASTER TO MASTER_LOG_FILE='([\w\-\.]+)',\s*MASTER_LOG_POS=(\d+);"
            logfile = re.search(rep, masterlogdata).group(1)
            logpos = re.search(rep, masterlogdata).group(2)
        except:
            return public.returnMsg(False, '获取Master信息失败')
        try:
            gtid = \
            self.__ExceSql('SELECT BINLOG_GTID_POS("%s", %s)' % (logfile, logpos), masterinfo=masterinfo)[0].split(
                "\n")[1]
        except:
            gtid = ""
        db.close()
        public.writeFile("%s/log.txt" % bakpath, str([logfile, logpos]))
        masterinfo["logfile"] = logfile
        masterinfo["logpos"] = logpos
        masterinfo["gtid"] = gtid
        masterinfo["backsqlpath"] = backsqlpath
        public.writeFile("%s/plugin/masterslave/data.json" % self.setpath, json.dumps(masterinfo))
        public.writeFile("/tmp/mysql.log", masterinfo, "a+")
        return masterinfo

    def BackUpMasterDbs(self,get):
        """
            @name  备份数据库并导入
            @author zhwen<zhw@bt.cn>
            @param
        """
        bakpath = "/www/backup/database"
        check_result = self._check_slave_parma(get)
        if isinstance(check_result,dict) and check_result.get('msg'):
            return check_result
        master_ip = check_result
        decode_master_key = self._decode_master_key(get,master_ip)
        masterinfo = decode_master_key['masterinfo']
        slave_version = decode_master_key['slave_version']
        self.__set_speed({'title': '正在检测主服务器 %s 端口是否开放。' % masterinfo["master_port"], 'progress': 0})
        if not self.CheckPort(master_ip, masterinfo["master_port"]):
            return public.returnMsg(False, '无法访问从服务器<br>请确认安全组是否已经放行<br>Mysql端口：%s' % masterinfo["master_port"])
        if slave_version in masterinfo["master_version"]:
            self.__set_speed({'title': '正在尝试连接主服务器。', 'progress': 5})
            master_con = self._build_master_con_object(masterinfo)
            if isinstance(master_con,dict) and master_con.get('msg'):
                return master_con
            db = master_con['db']
            cur = master_con['cur']
            self.__set_speed({'title': '正在准备备份数据库。', 'progress': 10})
            # 开始备份
            backsqlpath = "%s/masterslave.sql" % (bakpath)
            backsh = "nohup mysqldump -h%s -P%s -u%s -p%s --master-data=2 --skip-lock-tables --single-transaction %s%s 1> %s 2>/dev/null&"
            if masterinfo["replicate_dbs"][0] == "alldatabases":
                replicate_dbs = "All"
                self.__set_speed({'title': '开始备份所有数据库。', 'progress': 15})
                result = self._backup_all_db(cur,backsh,backsqlpath,masterinfo)
            else:
                replicate_dbs = ""
                cur.execute("use information_schema")
                for d in masterinfo["replicate_dbs"]: replicate_dbs += " %s " % d
                self.__set_speed({'title': '正在备份数据库 %s。' % replicate_dbs, 'progress': 15, 'type': 'backup_database'})
                result = self._backup_specify_db(cur,backsh,backsqlpath,masterinfo)
            if result:
                return result
            time.sleep(1)
            masterinfo = self._get_mysql_replicate_log_info(backsqlpath,db,masterinfo,bakpath)
            self.__set_speed({'title': '备份 %s 数据库成功。' % replicate_dbs, 'progress': 30})
            return masterinfo
        else:
            self.WriteLog("mysql版本不一致 主版本%s 从版本%s" % (masterinfo["master_version"],slave_version))
            return public.returnMsg(False, 'mysql版本不一致 主版本%s 从版本%s' % (masterinfo["master_version"],slave_version))

    def _reset_replicate(self,pm):
        pm.panelMysql().execute("stop slave")
        pm.panelMysql().execute("reset master")
        pm.panelMysql().execute("reset slave all")

    def _write_panel_db(self,masterinfo):
        """
            @name  将数据库信息写入面板数据库
            @author zhwen<zhw@bt.cn>
            @param
        """

        for i in masterinfo["replicate_dbs_info"]:
            if not i:
                continue
            if isinstance(i,dict):
                localdb = public.M('databases').where('name=?', (i["name"],)).select()
                if not localdb:
                    public.M('databases').add(("name,username,password,accept,ps"), (i["name"], i["username"], i["password"], i["accept"], i["ps"]))
                    continue
            else:
                localdb = public.M('databases').where('name=?', (i[2],)).select()
                if not localdb:
                    public.M('databases').add(("name,username,password,accept,ps"), (i[2], i[3], i[4], i[5], i[6]))

    def _skip_error(self,skip_error,sconf):
        if not skip_error:
            return True
        skip_error = ','.join(skip_error)
        skip_error = '\nslave-skip-errors={}'.format(skip_error)
        if 'slave-skip-errors' in sconf:
            return True
        sconf = re.sub("\[mysqld\]", "[mysqld]" + skip_error, sconf)
        return sconf

    def SetSlave(self,get):
        self.__set_speed({'title': '正在检测环境。', 'progress': 0}, True)
        if not self.GetPort(get):
            return public.returnMsg(False, '请确定数据库已经开启或尝试重置数据库ROOT密码')
        if not self.CheckBinLog():
            return public.returnMsg(False, '请先开启Mysql二进制日志')
        if get.skip_error:
            try:
                skip_error = json.loads(get.skip_error)
            except:
                return public.returnMsg(False, 'skip_error 参数需要传入列表')
        sconf = public.readFile(self.__mfile)
        # 备份需要同步的数据库
        masterinfo = self.BackUpMasterDbs(get)
        if isinstance(masterinfo,dict) and masterinfo.get('msg'):
            return masterinfo
        __dbpass = public.M('config').where('id=?', (1,)).getField('mysql_root')

        slave_version = masterinfo["slave_version"]
        create_replicate_sql = ""
        # Mysql5.5版本
        if "5.5" in slave_version:
            create_replicate_sql += "CHANGE MASTER TO MASTER_HOST='%s',MASTER_PORT=%s,MASTER_USER='%s',MASTER_PASSWORD='%s',MASTER_LOG_FILE='%s',MASTER_LOG_POS=%s" % (
                masterinfo["master_ip"], masterinfo["master_port"], masterinfo["slave_user"],
                masterinfo["slave_pass"],
                masterinfo["logfile"], masterinfo["logpos"])
        # Mysql5.6+版本
        addconf = """
log-slave-updates=true
enforce-gtid-consistency=true
gtid-mode=on"""
        if "5.5" not in slave_version and not re.match("10", slave_version):
            if not re.search("gtid-mode=on",sconf):
                sconf = re.sub("\[mysqld\]", "[mysqld]" + addconf, sconf)
            create_replicate_sql += "CHANGE MASTER TO MASTER_HOST='%s',MASTER_PORT=%s,MASTER_USER='%s',MASTER_PASSWORD='%s',MASTER_AUTO_POSITION = 1" % (
                masterinfo["master_ip"], masterinfo["master_port"], masterinfo["slave_user"],
                masterinfo["slave_pass"])
        # 构造要同步的数据库配置
        replicate_dbs = ""
        if masterinfo["replicate_dbs"][0] != "alldatabases":
            for d in masterinfo["replicate_dbs"]:
                replicate_dbs += "\nreplicate-wild-do-table = %s.%s" % (d, "%")
        else:
            sconf = re.sub("replicate-wild-do-table\s*=\s*[\w\%\.\_\-]+","",sconf)
        try:
            serverid = masterinfo["slave_id"]
        except:
            serverid = [int(masterinfo["master_id"]) +1]
        localip = public.ExecShell("ip a")[0]
        netip = public.readFile("%s/data/iplist.txt")
        index = 0
        try:
            for i in masterinfo["slave_ip"]:
                if i in localip or i in netip:
                    index += masterinfo["slave_ip"].index("i")
                    break
            if not index:
                return public.returnMsg(False, '主库没有设置该主机为从服务器，请先设置主服务器后再配置从库')
        except:
            pass
        serverid = serverid[index]
        self.__set_speed({'title': '正在导入数据库 ', 'progress': 35, 'type': 'import_database'})
        if not re.search("replicate-wild-do-table",sconf):
            sconf = re.sub("server-id\s*=\s*\d+", "server-id = %s%s" % (serverid,replicate_dbs), sconf)
        # 添加跳过主键冲突的错误
        sconf = self._skip_error(skip_error,sconf)
        public.writeFile(self.__mfile, sconf)
        # 导入主库数据库
        try:
            if self._restart_mysql() == 0:
                return public.returnMsg(False,'数据重启失败！')
            self._reset_replicate(pm)
            self.WriteLog("开始导入数据库")
            # speed = public.getSpeed()
            # public.writeSpeed("导入数据库", 1, speed["total"])
            error = public.ExecShell("nohup /usr/bin/mysql -uroot -p%s < %s &" % (__dbpass, masterinfo["backsqlpath"]))
            import_pid = public.ExecShell('ps aux|grep "/usr/bin/mysql -uroot -p"|grep -v "grep"')[0]
            while import_pid:
                time.sleep(2)
                import_pid = public.ExecShell('ps aux|grep "/usr/bin/mysql -uroot -p"|grep -v "grep"')[0]
            self.WriteLog(str(error))
        except Exception as e:
            self.WriteLog("导入数据库失败  %s" % e)
            return public.ReturnMsg(False, "导入失败")
        self.__set_speed({'title': '数据库导入成功 。', 'progress': 60})
        # threading.Thread(target=self.SetSpeed()).start()
        self.WriteLog("导入数据库完成")

        self.WriteLog("删除备份的数据库文件")
        public.ExecShell("rm -f %s" % masterinfo["backsqlpath"])
        public.ExecShell("rm -f /tmp/mysqlpid")
        self.WriteLog("重启mysql")
        pid_old = public.ExecShell("ps aux|grep 'mysql.sock'|awk 'NR==1 {print $2}'")[0].split("\n")[0]
        self.WriteLog("旧PID %s" % pid_old)
        self.__set_speed({'title': '正在重启数据库 ', 'progress': 65, 'type': 'restart_database'})
        if self._restart_mysql() == 0:
            return public.ReturnMsg(False, "导入数据后重启失败")
        self.WriteLog("mysql重启完成")
        self.__set_speed({'title': '同步面板数据库文件 ', 'progress': 75})
        # 写入同步的数据库到面板数据库
        self._write_panel_db(masterinfo)
        # 完整复制将主root密码写入到从的面板
        if masterinfo["replicate_dbs"][0] ==  "alldatabases":
            self.WriteLog("因为是完整同步，修改从库面板密码为主库")
            public.M('config').where('id=?', (1,)).setField('mysql_root', masterinfo["slave_ips"])
            result = str(pm.panelMysql().query("select version()")[0])
            self.WriteLog(result)
            if result == "1045":
                public.M('config').where('id=?', (1,)).setField('mysql_root', __dbpass)
        # Mairadb10.*版本
        if re.match("10",slave_version):
            set_slave_pos_sql = "SET GLOBAL gtid_slave_pos='%s'" % masterinfo["gtid"]
            # 需要在数据重启后配置
            pm.panelMysql().query(set_slave_pos_sql)
            create_replicate_sql += "CHANGE MASTER TO MASTER_HOST='%s',MASTER_PORT=%s,MASTER_USER='%s',MASTER_PASSWORD='%s',master_use_gtid=slave_pos" % (
                masterinfo["master_ip"], masterinfo["master_port"], masterinfo["slave_user"], masterinfo["slave_pass"])
        self.__set_speed({'title': '配置从服务状态 ', 'progress': 85})
        self.WriteLog("停止从服务")
        pm.panelMysql().query("stop slave")
        self.WriteLog("修改从服务器的主服务器信息")
        pm.panelMysql().query(create_replicate_sql)
        self.WriteLog("启动从服务")
        pm.panelMysql().query("start slave")

        time.sleep(2)
        self.WriteLog("获取从状态")
        slavestatus = pm.panelMysql().query("show slave status")[0]
        self.WriteLog(str(slavestatus))
        self.__set_speed({'title': '创建Slave监控用户 ', 'progress': 90})
        self.WriteLog("创建Slave监控用户")
        create_status_user = "create user %s@%s identified by '%s'" % ("user"+masterinfo["slave_user"], masterinfo["master_ip"], "pass"+masterinfo["slave_pass"])
        grant_status_user = "grant super,select,delete on *.* to %s@'%s'" % ("user"+masterinfo["slave_user"], masterinfo["master_ip"])
        pm.panelMysql().execute(create_status_user)
        pm.panelMysql().execute(grant_status_user)

        # 检查主从是否已经设置成功
        n = 0
        try:
            for i in slavestatus:
                if i == "Yes":
                    n += 1
        except:
            return public.returnMsg(False, '获取主从状态失败')
        if n == 2:
            self.__set_speed({'title':'配置成功，请手动检查是否配置成功。。 ','progress':100})
            self.WriteLog("删除btmysql用户")
            self.__ExceSql('delete from mysql.user where user="btmysql"', masterinfo=masterinfo)
            if masterinfo["replicate_dbs"][0] != "alldatabases":
                self.WriteLog("删除从btmysql用户")
                pm.panelMysql().execute("delete from mysql.user where user='btmysql'")
            self.WriteLog("设置成功")
            public.ExecShell("rm -f %s" % self.totalspeedfile)
            return public.returnMsg(True, '设置成功')
        else:
            self.__set_speed({'title': '配置失败。 ', 'progress': 100})
            self.WriteLog("设置失败")
            public.ExecShell("rm -f %s" % self.totalspeedfile)
            return public.returnMsg(True, '设置失败')

    def RemoveMysqlRepConf(self,sconf):
        sconf = re.sub("replicate-wild-do-table\s*=\s*.+\n","",sconf)
        return sconf

    def _remove_skip_error(self,sconf):
        sconf = re.sub('\nslave-skip-errors.*','',sconf)
        public.writeFile(self.__mfile,sconf)


    def RemoveReplicate(self,get):
        slave_ip = get.slave_ip
        conf = public.readFile(self.datafile)
        sconf = public.readFile(self.__mfile)
        if os.path.exists(self.datafile) and conf != "":
            conf = json.loads(conf)
            try:
                # 判断是否在从服务器操作，有值表示是
                master_ip = conf["master_ip"]
            except:
                master_ip = ""
            if master_ip:
                pm.panelMysql().execute("stop slave")
                pm.panelMysql().execute("reset slave all")
                pm.panelMysql().execute("reset master")
                public.ExecShell("rm -f %s" % self.datafile)
                sconf = self.RemoveMysqlRepConf(sconf)
                self._remove_skip_error(sconf)
            else:
                try:
                    pm.panelMysql().execute("delete from mysql.user where host='%s'" % slave_ip)
                    pm.panelMysql().execute("flush privileges")
                    index = conf["slave_ip"].index(slave_ip)
                    conf["slave_ip"].pop(index)
                    conf["slave_port"].pop(index)
                    conf["slave_id"].pop(index)
                except:
                    public.ExecShell("rm -f %s" % self.datafile)
                if not conf["slave_ip"]:
                    public.ExecShell("rm -f %s" % self.datafile)
                else:
                    public.writeFile(self.datafile, json.dumps(conf))

            self.WriteLog("删除成功")
            return public.returnMsg(True, "删除成功")

    # 获取主从状态
    def GetReplicateStatus(self,get):
        conf = public.readFile(self.datafile)
        status_list = []
        if not conf:
            return public.returnMsg(True, "获取成功")
        conf = json.loads(conf)
        # 兼容旧版本设置
        if not isinstance(conf["slave_ip"],list):
            conf["slave_ip"] = [conf["slave_ip"]]
            conf["slave_port"] = [str(conf["slave_port"])]
            conf["slave_id"] = [int(conf["master_id"])+1]
            public.writeFile(self.datafile,json.dumps(conf))
        try:
            slaveip =  conf["slave_ip"]
            slaveport = conf["slave_port"]
            if "master_ip" in conf.keys():
                slavestatus = pm.panelMysql().query("show slave status")[0]
                Slave_IO_Running = slavestatus[10]
                Slave_SQL_Running = slavestatus[11]
                master_ip = conf["master_ip"]
                slave_ip = "local"
            else:
                for i in slaveip:
                    master_ip = "local"
                    slave_ip = i
                    if not self.CheckPort(slave_ip, slaveport[slaveip.index(i)]):
                        status = {
                            "Slave_IO_Running": "no",
                            "Slave_SQL_Running": "no",
                            "master_ip": master_ip,
                            "slave_ip": slave_ip,
                            "slavestatus": False,
                            "replicate_dbs": conf["replicate_dbs"],
                            "slave_port": slaveport[slaveip.index(i)]
                        }
                        status_list.append(status)
                        continue
                    slavestatus = public.ExecShell(
                        "mysql -h%s -P%s --connect_timeout=3 -u%s -p%s -e 'show slave status\G'" % (i,slaveport[slaveip.index(i)],"user"+conf["slave_user"],"pass"+conf["slave_pass"]))[0]
                    Slave_IO_Running = "Slave_IO_Running:\s+(\w+)"
                    Slave_SQL_Running = "Slave_SQL_Running:\s+(\w+)"
                    if not slavestatus:
                        Slave_IO_Running = "no"
                        Slave_SQL_Running = "no"
                    else:
                        Slave_IO_Running = re.search(Slave_IO_Running, slavestatus).group(1)
                        Slave_SQL_Running = re.search(Slave_SQL_Running, slavestatus).group(1)
                    status = {
                        "Slave_IO_Running": Slave_IO_Running,
                        "Slave_SQL_Running": Slave_SQL_Running,
                        "master_ip": master_ip,
                        "slave_ip": slave_ip,
                        "slavestatus": slavestatus,
                        "replicate_dbs": conf["replicate_dbs"],
                        "slave_port": slaveport[slaveip.index(i)]
                    }
                    status_list.append(status)

        except:
            slavestatus = ""
            Slave_IO_Running = "no"
            Slave_SQL_Running = "no"
            master_ip = ""
            slave_ip = ""
        if not status_list:
            status_list = [{
                "Slave_IO_Running": Slave_IO_Running,
                "Slave_SQL_Running": Slave_SQL_Running,
                "master_ip": master_ip,
                "slave_ip": slave_ip,
                "slavestatus": slavestatus,
                "replicate_dbs": conf["replicate_dbs"]
            }]
        return public.returnMsg(True, status_list)

    def CheckTables(self):
        try:
            __dbpass = public.M('config').where('id=?', (1,)).getField('mysql_root')
            file = "%s/plugin/masterslave/data.json" % self.setpath
            conf = json.loads(public.readFile(file))
            host = "localhost"
            user = "root"
            passwd = __dbpass
            a = public.ExecShell("/www/server/mysql/bin/mysqlcheck -h%s aaa_com -u%s -p%s" % (host, user, passwd))[
                0].split("OK")
            host = conf["slave_ip"]
            user = "user"+conf["slave_user"]
            passwd = "pass"+conf["slave_pass"]
            b = public.ExecShell("/www/server/mysql/bin/mysqlcheck -h%s aaa_com -u%s -p%s" % (host, user, passwd))[
                0].split("OK")
            errortable = []
            for l in [a, b]:
                for i in l:
                    if "error" in i:
                        errortable.append(i)
            print(errortable)
            if errortable:
                return public.returnMsg(False, "以下表 %s 已损坏，请修复后再重新做同步" % errortable)
        except:
            return public.returnMsg(False,'检查数据表时发生错误！')

    # 检测主从错误
    def GetReplicateError(self,get):
        try:
            status_list = self.GetReplicateStatus(get)["msg"]
            for status in status_list:
                if status["slave_ip"] != get.slave_ip:
                    continue
                # if status["master_ip"] != "local" or status["slave_ip"] != get.slave_ip:
                if status["master_ip"] != "local":
                    return public.returnMsg(False, "请到主服务器执行")
                if status["Slave_IO_Running"] == "Yes" and status["Slave_SQL_Running"] == "Yes":
                    print("同步正常无需修复")
                    return public.returnMsg(False, "同步正常无需修复")
                if status["Slave_IO_Running"] == "Connecting":
                    return public.returnMsg(False, "从服务器同步用户无法连接主服务器，请联系官方人员检查")
                errortable = self.CheckTables()
                if errortable:
                    return errortable
                if not self.CheckPort(status["slave_ip"], status["slave_port"]):
                    return public.returnMsg(False, "无法连接到从服务器")
                last_io_errno = re.search("Last_IO_Errno:\s+(\d+)", status["slavestatus"]).group(1)
                if last_io_errno == "1236":
                    errormsg = re.search("Last_IO_Error:\s+(.+)", status["slavestatus"]).group(1)
                    if "Could not find first log file name in binary log index file" in errormsg:
                        print('<br><a style="color:red;">主服务器二进制文件丢失，请重做主从，请先备份数据以免丢失数据</a>')
                        return public.returnMsg(False, "主服务器异常重启导致主库有数据回滚，若有数据丢失请到从库查找，若要重做主从请先备份好主库和从库以免丢失数据")
                    if "Slave has more GTIDs than the master has" in errormsg:
                        print("主服务器二进制文件丢失，请重做主从，以免丢失数据")
                        return public.returnMsg(False, "主服务器异常重启导致主库有数据回滚，若有数据丢失请到从库查找，若要重做主从请先备份好主库和从库以免丢失数据")
                    if "Error: connecting slave requested to start from GTID" in errormsg:
                        return public.returnMsg(False, "主服务器异常重启导致主库有数据回滚，若有数据丢失请到从库查找，若要重做主从请先备份好主库和从库以免丢失数据")
                    return public.returnMsg(True, "读取二进制日志时报错，主要出现在服务器有异常重启的情况，是否尝试修复")
                # 主键冲突处理
                last_sql_errno = re.search("Last_SQL_Errno:\s+(\d+)", status["slavestatus"]).group(1)
                if last_sql_errno == "1062":
                    return public.returnMsg(True, "从库已经存在插入的数据，修复时会先删除从库冲突数据，再尝试插入主库的数据到从库，是否尝试修复"+'<br><a style="color:red;">！！！如果需要修复请先备份好从库以免使数据丢失！！！</a>')
            return public.returnMsg(False, "该错误无法修复，需要重做主从，请先备份数据以免丢失数据")
        except:
            return public.returnMsg(False, "获取从库信息失败，一般情况是因为无法连接从库导致的，请尝试删除同步后再创建")

    # 修复主从
    def FixReplicate(self,get):
        file = "%s/plugin/masterslave/data.json" % self.setpath
        conf = json.loads(public.readFile(file))
        status = self.GetReplicateStatus(get)
        slave_ip = get.slave_ip
        if not status:
            return public.returnMsg(False, "获取主从状态失败")
        status_list = status["msg"]
        for status in status_list:
            if status["slave_ip"] != slave_ip:
                continue
            if status["Slave_IO_Running"] == "Yes" and status["Slave_SQL_Running"] == "Yes":
                print("同步正常无需修复")
                return public.returnMsg(True, "同步正常无需修复")
            mversion = pm.panelMysql().query("select version()")[0][0].split("-")[0]
            Last_IO_Errno = re.search("Last_IO_Errno:\s+(\d+)", status["slavestatus"]).group(1)
            if Last_IO_Errno == "1236":
                if "5.5" in mversion:
                    errormsg = re.search("Last_IO_Error:\s+(.+)",status["slavestatus"]).group(1)
                    rep = "(mysql-bin\.\d+)\'\s\w{2}\s(\d+)"
                    errormsg = re.search(rep, errormsg)
                    errmysqlbin = errormsg.group(1)
                    errlogpos = errormsg.group(2)
                    public.ExecShell(
                        "/www/server/mysql/bin/mysqlbinlog /www/server/data/%s|grep 'end_log_pos' > /www/server/data/btfix.log" % errmysqlbin)
                    mpos = public.ExecShell("tail -n 1 /www/server/data/btfix.log|awk '{print $7}'")[0].split("\n")[0]
                    print(mpos)
                    if int(mpos) < int(errlogpos):
                        change_sql='stop slave;change master to  MASTER_LOG_FILE="%s",MASTER_LOG_POS=%s;start slave' % (errmysqlbin,mpos)
                        print(change_sql)
                        print(self.__ExceSql(status["slave_ip"], status["slave_port"], "user" + conf["slave_user"],
                                       "pass" + conf["slave_pass"], change_sql))
                        status = self.GetReplicateStatus(get)
                        status = status["msg"]
                        if status["Slave_IO_Running"] == "Yes" and status["Slave_SQL_Running"] == "Yes":
                            public.ExecShell("rm -f /www/server/data/btfix.log")
                            print("修复成功")
                            return public.returnMsg(True, "修复成功")
                        else:
                            print("修复失败")
                            return public.returnMsg(True, "修复失败")

            # 主键冲突处理
            last_sql_errno = re.search("Last_SQL_Errno:\s+(\d+)", status["slavestatus"]).group(1)
            if last_sql_errno == "1062":
                while True:
                    errormsg = re.search("Last_SQL_Error:\s+(.*)", status["slavestatus"]).group(1)
                    primary = "entry\s'(\w+)'"
                    defdb = "database:\s'(\w*)'"
                    db_tb = "(insert|INSERT)\s+(into|INTO)\s+(`|)([\w\_\-\.]+)(`|)"
                    primary = re.search(primary, errormsg).group(1)
                    try:
                        defdb = re.search(defdb, errormsg).group(1)
                    except:
                        defdb = ""
                    db_tb = re.search(db_tb, errormsg)
                    if db_tb:
                        db_tb = db_tb.group(4)
                    if "`" in db_tb:
                        db_tb = db_tb.split('`')[-2]

                    if "." in db_tb and '`' not in db_tb:
                        db_tb = db_tb.split('.')[-1]
                    print(primary, defdb, db_tb)
                    if defdb:
                        db_tb=defdb+"."+db_tb.split(".")[-1]
                    sql = "desc %s" % db_tb
                    result = pm.panelMysql().query(sql)
                    for i in result:
                        if "PRI" in i:
                            prikey = i[0]

                    sql = 'delete from %s where %s=%s;stop slave;start slave;' % (db_tb, prikey, primary)
                    print(sql)
                    a = self.__ExceSql(status["slave_ip"], status["slave_port"], "user" + conf["slave_user"],
                                   "pass" + conf["slave_pass"], sql)
                    time.sleep(0.3)
                    status_list = self.GetReplicateStatus(get)["msg"]
                    for status in status_list:
                        if status["slave_ip"] == slave_ip:
                            last_sql_errno = re.search("Last_SQL_Errno:\s+(\d+)", status["slavestatus"]).group(1)
                            if last_sql_errno != "1062":
                                return public.returnMsg(True, "修复成功")
        return public.returnMsg(False, "无法修复")

