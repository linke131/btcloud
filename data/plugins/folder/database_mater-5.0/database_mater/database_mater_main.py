# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: 1249648969@qq.com
# -------------------------------------------------------------------
# 数据库管理运维工具
# ------------------------------
import sys
sys.path.append('/www/server/panel/class')
import json,os,time,public,string,panelMysql,re,psutil,string,data,crontab
os.chdir('/www/server/panel')
from datetime import datetime

class database_mater_main():
    DB_MySQL = None
    data = None
    __text=None
    Pids = None
    __cpu_time = None
    new_info = {}
    old_info = {}
    old_path = '/tmp/bt_task_old2.json'
    __my_cnf='/etc/my.cnf'
    __mysql_log='/www/server/data/mysql-slow.log'
    log=public.WriteLog
    __mysql_bin_log='/www/backup/mysql_bin_backup'

    def __init__(self):
        if not self.DB_MySQL: self.DB_MySQL = panelMysql.panelMysql()
        if not self.data: self.database = data.data()
        if not public.M('sqlite_master').where('type=? AND name=?', ('table','database_mater',)).count():
            public.M('').execute('''CREATE TABLE "database_mater" (
                          "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                          "hosts" TEXT,
                          "tables" TEXT,
                          "field" TEXT,
                          "type" TEXT,
                          "sql" TEXT,
                          "revoke" TEXT,
                          "status" TEXT,
                          "time" TEXT,
                          "ps" TEXT
                        );''')

    #写入数据库
    def insert(self,hosts,tables,field,sql,revoke,ps,stype):
        if public.M('database_mater').where("ps=?", (ps,)).count():return True
        inser_data={"ps":ps,"hosts":hosts,"tables":tables,"field":field,"sql":sql,"revoke":revoke,"status":1,"time":datetime.now().strftime("%Y-%m-%d:%H:%M:%S"),"type":stype}
        public.M('database_mater').insert(inser_data)
        return True

    def update(self,id,data):
        public.M('database_mater').where("id=? and type=?", (id,'sql',)).update(data)
        return True

    def delete(self,id):
        public.M('database_mater').where("id=? and type=?", (id,'sql',)).delete()
        return True

    def select(self,id=None):
        if id:return public.M('database_mater').where("id=? and type=?", (id,'sql',)).field(
            'id,hosts,tables,field,sql,revoke,ps,time,status').select()
        return public.M('database_mater').where("type=?", ('sql',)).field('id,hosts,tables,field,sql,revoke,ps,time,status').select()

    def prece_data(self,data):
        for i in data:
            if type(i)==list:
                self.prece_data(i)
            else:
                self.__text+=i
        return self.__text

    def check_data(self,data,check):
        if type(data)==str:
            if re.search(check,data):
                return True
        elif type(data)==list:
            self.__text=''
            if re.search(check,self.prece_data(data)):
                return True
        else:
            return False

    def GetRunStatus(self,get):
        import time
        result = {}
        data =self.DB_MySQL.query('show global status')
        gets = ['Innodb_log_writes','Innodb_data_reads','Innodb_data_writes','Innodb_dblwr_writes','Innodb_buffer_pool_write_requests','Max_used_connections','Com_commit','Com_rollback','Questions','Innodb_buffer_pool_reads','Innodb_buffer_pool_read_requests','Key_reads','Key_read_requests','Key_writes','Key_write_requests','Qcache_hits','Qcache_inserts','Bytes_received','Bytes_sent','Aborted_clients','Aborted_connects','Created_tmp_disk_tables','Created_tmp_tables','Innodb_buffer_pool_pages_dirty','Opened_files','Open_tables','Opened_tables','Select_full_join','Select_range_check','Sort_merge_passes','Table_locks_waited','Threads_cached','Threads_connected','Threads_created','Threads_running','Connections','Uptime']
        try:
            if data[0] == 1045:
                return public.returnMsg(False,'MySQL密码错误!')
        except:pass
        for d in data:
            for g in gets:
                try:
                    if d[0] == g: result[g] = d[1]
                except:
                    pass
        if not 'Run' in result and result:
            result['Run'] = int(time.time()) - int(result['Uptime'])
        tmp = panelMysql.panelMysql().query('show master status')
        try:
            result['qps'] = int(result['Questions']) / int(result['Uptime'])
            result['InnoDB_IO'] = int(result['Innodb_data_reads']) + int(result['Innodb_data_writes']) + int(
                result['Innodb_dblwr_writes']) + int(result['Innodb_log_writes'])
            result['MyISAM_IO'] = int(result['Key_reads']) * 2 + int(result['Key_writes']) * 2 + int(
                result['Key_read_requests']) * 2
            mysql_system = self.get_process_list()
            if mysql_system:
                result['mysql_memory'] = mysql_system['memory_used']
                result['mysql_io_write_speed'] = mysql_system['io_write_speed']
                result['mysql_io_read_speed'] = mysql_system['io_read_speed']
                result['mysql_create_time'] = mysql_system['create_time']
                result['mysql_system_cpu'] = mysql_system['cpu_percent']
            else:
                result['mysql_memory'] = 0
                result['mysql_io_write_speed'] = 0
                result['mysql_io_read_speed'] = 0
                result['mysql_create_time'] = int(time.time())
                result['mysql_system_cpu'] = 0
            result['mysql_count_size']=self.get_mysql_size()
            result['slow_query_log']=self.slow_query_log()
            result['File'] = tmp[0][0]
            result['Position'] = tmp[0][1]

        except:
            result['File'] = 'OFF'
            result['Position'] = 'OFF'
        return result

    def get_old(self):
        if self.old_info: return True;
        if not os.path.exists(self.old_path): return False
        data = public.readFile(self.old_path)
        if not data: return False
        data = json.loads(data);
        if not data: return False
        self.old_info = data
        del(data)
        return True

    def get_cpu_time(self):
        if self.__cpu_time: return self.__cpu_time
        self.__cpu_time = 0.00
        s = psutil.cpu_times()
        self.__cpu_time = s.user + s.system + s.nice + s.idle
        return self.__cpu_time

    def get_process_cpu_time(self, cpu_times):
        cpu_time = 0.00
        for s in cpu_times: cpu_time += s
        return cpu_time

    def get_cpu_percent(self,pid,cpu_times,cpu_time):
        self.get_old()
        percent = 0.00
        process_cpu_time = self.get_process_cpu_time(cpu_times)
        if not self.old_info: self.old_info = {}
        if not pid in self.old_info:
            self.new_info[pid] = {}
            self.new_info[pid]['cpu_time'] = process_cpu_time
            return percent
        percent = round(100.00 * (process_cpu_time - self.old_info[pid]['cpu_time']) / (cpu_time - self.old_info['cpu_time']),2)
        self.new_info[pid] = {}
        self.new_info[pid]['cpu_time'] = process_cpu_time
        if percent > 0: return percent
        return 0.00

    def get_io_write(self,pid,io_write):
        self.get_old()
        disk_io_write = 0
        if not self.old_info: self.old_info = {}
        if not pid in self.old_info:
            self.new_info[pid]['io_write'] = io_write
            return disk_io_write
        if not 'time' in self.old_info: self.old_info['time'] = self.new_info['time']
        io_end = (io_write - self.old_info[pid]['io_write'])
        if io_end > 0:
            disk_io_write = io_end / (time.time() - self.old_info['time'])
        self.new_info[pid]['io_write'] = io_write
        if disk_io_write > 0: return int(disk_io_write)
        return 0

    def get_io_read(self,pid,io_read):
        self.get_old()
        disk_io_read = 0
        if not self.old_info: self.old_info = {}
        if not pid in self.old_info:
            self.new_info[pid]['io_read'] = io_read
            return disk_io_read
        if not 'time' in self.old_info: self.old_info['time'] = self.new_info['time']
        io_end = (io_read - self.old_info[pid]['io_read'])
        if io_end > 0:
            disk_io_read = io_end / (time.time() - self.old_info['time'])
        self.new_info[pid]['io_read'] = io_read
        if disk_io_read > 0: return int(disk_io_read)
        return 0

    def get_connects(self,pid):
        connects = 0
        try:
            if pid == 1: return connects
            tp = '/proc/' + str(pid) + '/fd/'
            if not os.path.exists(tp): return connects;
            for d in os.listdir(tp):
                fname = tp + d
                if os.path.islink(fname):
                    l = os.readlink(fname)
                    if l.find('socket:') != -1: connects += 1
        except:pass
        return connects

    def get_load_average(self):
        b = public.ExecShell("uptime")[0].replace(',', '')
        c = b.split()
        data = {}
        data['1'] = float(c[-3])
        data['5'] = float(c[-2])
        data['15'] = float(c[-1])
        return data

    def get_mem_info(self,get=None):
        mem = psutil.virtual_memory()
        memInfo = {'memTotal':mem.total,'memFree':mem.free,'memBuffers':mem.buffers,'memCached':mem.cached}
        memInfo['memRealUsed'] = memInfo['memTotal'] - memInfo['memFree'] - memInfo['memBuffers'] - memInfo['memCached']
        return memInfo['memRealUsed']

    def get_process_list(self):
        self.Pids = psutil.pids()
        processList = []
        if type(self.new_info) != dict: self.new_info = {}
        self.new_info['cpu_time'] = self.get_cpu_time()
        self.new_info['time'] = time.time()
        info = {}
        info['activity'] = 0
        info['cpu'] = 0.00
        info['mem'] = 0
        info['disk'] = 0
        status_ps = {'sleeping': '睡眠', 'running': '活动'}
        for pid in self.Pids:
            tmp = {}
            try:
                p = psutil.Process(pid)
            except:
                continue
            with p.oneshot():
                p_mem = p.memory_full_info()
                if p_mem.uss + p_mem.rss + p_mem.pss + p_mem.data == 0: continue;
                pio = p.io_counters()
                p_cpus = p.cpu_times()
                p_state = p.status()
                if p.name() !='mysqld':continue
                if p_state == 'running': info['activity'] += 1;
                if p_state in status_ps: p_state = status_ps[p_state];
                tmp['exe'] = p.exe()
                tmp['name'] = p.name()
                tmp['pid'] = pid
                tmp['ppid'] = p.ppid()
                tmp['create_time'] = int(p.create_time())
                tmp['status'] = p_state
                tmp['user'] = p.username()
                tmp['memory_used'] = p_mem.uss
                tmp['cpu_percent'] = self.get_cpu_percent(str(pid), p_cpus, self.new_info['cpu_time'])
                tmp['io_write_bytes'] = pio.write_bytes
                tmp['io_read_bytes'] = pio.read_bytes
                tmp['io_write_speed'] = self.get_io_write(str(pid), pio.write_bytes)
                tmp['io_read_speed'] = self.get_io_read(str(pid), pio.read_bytes)
                tmp['connects'] = self.get_connects(pid)
                tmp['threads'] = p.num_threads()
                if tmp['cpu_percent'] > 100: tmp['cpu_percent'] = 0.1;
                info['cpu'] += tmp['cpu_percent']
                info['disk'] += tmp['io_write_speed'] + tmp['io_read_speed']
            processList.append(tmp)
            del (p)
            del (tmp)
        if len(processList)==0:return False
        return processList[0]

    #数据库大小
    def get_mysql_size(self):
        data_size = self.DB_MySQL.query("select concat(round(sum((data_length+index_length)/1024/1024),2),'MB') as data from information_schema.TABLES;")
        if len(data_size)==0:
            return '0M'
        else:
            return data_size[0][0]

    #慢查询检查
    def slow_query_log(self):
        result = {}
        data = self.DB_MySQL.query("show variables like 'slow_query%'")
        gets = ['slow_query_log','slow_query_log_file']
        try:
            if data[0] == 1045:
                return public.returnMsg(False, 'MySQL密码错误!')
        except:
            pass
        for d in data:
            for g in gets:
                try:
                    if d[0] == g: result[g] = d[1]
                except:
                    pass
        if result['slow_query_log']!='ON':
            self.DB_MySQL.query("set global slow_query_log='ON';")
            self.DB_MySQL.query("set global slow_query_log_file='/www/server/data/mysql-slow.log';")
            self.DB_MySQL.query("set global long_query_time=3;")
        return result

    #永久性开启慢查询
    def set_slow_query_log(self,get):
        mysql_cnf=public.ReadFile(self.__my_cnf)
        #判断是否存在
        if re.search('slow_query_log',mysql_cnf) and re.search('slow-query-log-file',mysql_cnf) and re.search('long_query_time',mysql_cnf):
            mysql_cnf=re.sub('slow_query_log\s?=\s?.+','slow_query_log=1',mysql_cnf)
            mysql_cnf=re.sub('slow-query-log-file\s?=\s?.+', 'slow-query-log-file=/www/server/data/mysql-slow.log', mysql_cnf)
            mysql_cnf=re.sub('long_query_time\s?=\s?.+', 'long_query_time=3', mysql_cnf)
            public.writeFile(self.__my_cnf,mysql_cnf)
            return public.returnMsg(200,'开启成功请重启mysql才能永久生效')
        else:
            txt='\nslow_query_log=1\nslow-query-log-file=/www/server/data/mysql-slow.log\nlong_query_time=3\n\ninnodb_data_home_dir'
            mysql_cnf=re.sub('innodb_data_home_dir', txt, mysql_cnf)
            public.writeFile(self.__my_cnf, mysql_cnf)
            return public.returnMsg(200, '开启成功请重启mysql才能永久生效')

    def get_file_log(self,logfile, n):
        blk_size_max = 4096
        n_lines = []
        with open(logfile, 'r') as fp:
            fp.seek(0, os.SEEK_END)
            cur_pos = fp.tell()
            while cur_pos > 0 and len(n_lines) < n:
                blk_size = min(blk_size_max, cur_pos)
                fp.seek(cur_pos - blk_size, os.SEEK_SET)
                blk_data = fp.read(blk_size)
                len(blk_data) == blk_size
                lines = blk_data.split('\n')
                if len(lines) > 1 and len(lines[0]) > 0:
                    n_lines[0:0] = lines[1:]
                    cur_pos -= (blk_size - len(lines[0]))
                else:
                    n_lines[0:0] = lines
                    cur_pos -= blk_size
                fp.seek(cur_pos, os.SEEK_SET)
        if len(n_lines) > 0 and len(n_lines[-1]) == 0:
            del n_lines[-1]
        return n_lines[-n:]

    def return_user(self,data):
        if re.search('\[(.+)\]\s+@', data):
            data=re.findall('\[(.+)\]\s+@', data)
            if len(data)==1:
                return data[0]
            else:
                return 'mysql'
        else:return 'mysql'

    def return_time(self, data):
        if re.search('# Query_time:\s(.+)\sLock_time:\s(.+)\sRows_sent', data):
            data = re.findall('# Query_time:\s(.+)\sLock_time:\s(.+)\sRows_sent', data)
            if len(data)==0:
                return {'Query_time':0,'Lock_time':0}
            else:
                if len(data[0])==2:
                    return {'Query_time':data[0][0].strip().split('.')[0],'Lock_time':data[0][1].strip().split('.')[0]}
                else:
                    return {'Query_time': 0, 'Lock_time': 0}
    ## 慢查询
    def get_log(self,get):
        result=[]
        data=self.get_file_log(self.__mysql_log,1000)
        for i in range(len(data)):
            if i<4:continue
            if type(data[i])!=str:continue
            if 'SELECT' in data[i].upper():
                t={}
                t['time']=data[i-1].replace('SET timestamp=','').replace(';','')
                if 'use' in data[i-2]:
                    t['host']=data[i-2].replace('use ','')
                    t['query_time'] =self.return_time(data[i - 3])
                else:
                    t['query_time']=self.return_time(data[i - 2])
                    t['host'] = self.return_user(data[i - 3])
                t['select']=data[i]
                result.append(t)
        return result

    def str_sub(self, data):
        data = re.sub('=\s+', '=', data)
        data = re.sub('\s+=', '=', data)
        data = re.sub('\s+=\s+', '=', data)
        data = re.sub('\s=\s+', '=', data)
        data = re.sub('`', '=', data)
        return data

    def sql_parse(self, sql):
        parse_func = {
            'select': self.select_parse,
        }
        sql = self.str_sub(sql)
        sql_l = sql.split(' ')
        func = sql_l[0].lower()
        res = ''
        if func in parse_func:
            res = parse_func[func](sql_l)
        if res=='':return False
        return res

    def select_parse(self, sql_l):
        sql_dic = {
            'select': [],
            'from': [],
            'where': [],
            'limit': [],
        }
        return self.handle_parse(sql_l, sql_dic)

    def handle_parse(self, sql_l, sql_dic):
        tag = False
        for item in sql_l:
            item2 = item
            item = item.lower()
            if tag and item in sql_dic:
                tag = False
            if not tag and item in sql_dic:
                tag = True
                key = item
                continue
            if tag:
                sql_dic[key].append(item2)
        if sql_dic.get('where'):
            sql_dic['where'] = self.where_parse(sql_dic.get('where'))
        return sql_dic

    def where_parse(self, where_l):
        res = []
        key = ['>', '<', '=', '!=', '>=', '<=']
        try:
            for i in where_l:
                for i2 in key:
                    if i2 in i:
                        res.append(i.split(i2)[0])
                        break
            if len(res) >= 1:
                for i3 in range(len(res)):
                    if not res[i3]:
                        del res[i3]
            if 'like' or 'LIKE' in where_l:
                for i3 in range(len(where_l)):
                    if i3==0:continue
                    if where_l[i3].lower() == 'like':
                        res.append(where_l[i3 - 1])
                res = list(set(res))
        except:return res
        return res


    #查看优化记录
    def get_optimization_log(self,get):
        if 'p' not in get: get.p = '1'
        get.p = int(get.p)
        data = {}
        count = public.M('database_mater').where("type=?", ('sql',)).order("id desc").count()
        data['page'] = public.get_page(count, get.p, 12)
        data['data'] = public.M('database_mater').where("type=?", ('sql',)).order("id desc").limit(
            '{},{}'.format(data['page']['shift'], data['page']['row'])).field('id,hosts,tables,field,sql,revoke,ps,time,status').select()
        return data

    #优化表
    def OptimizeTable(self,table_name,db_name=None):
        if db_name:
            self.DB_MySQL.execute('OPTIMIZE table `%s`.`%s`;' % (db_name, table_name))
        else:
            self.DB_MySQL.execute('OPTIMIZE table `%s`;' % (table_name))
        return True

    #判断该字段类型是否是int/string/chr
    def chekc_types(self,sql,chekc_list):
        result = {}
        data = self.DB_MySQL.query(sql)
        gets = chekc_list
        try:
            if data[0] == 1045:
                return '1045'
            if data[0] == 1146:
                return '1146'
        except:
            pass
        try:
            for d in data:
                for g in gets:
                        if d[0] == g: result[g] = d[1]
        except:
            return result
        return result

    #查看数据库
    def get_local_database(self,get):
        if 'p' not in get: get.p = '1'
        get.p = int(get.p)
        data = {}
        count = public.M('databases').order("id desc").count()
        data['page'] = public.get_page(count, get.p, 12)
        data['data'] = public.M('databases').order("id desc").limit(
            '{},{}'.format(data['page']['shift'], data['page']['row'])).field('name').select()
        return data

    def get_local_database2(self,get):
       return public.M('databases').field('name').select()

    #撤销、并删除此条记录
    def set_revoke(self,get):
        if not 'id' in get:return public.returnMsg(False, '缺少id参数!')
        if not public.M('database_mater').where("id=? and type=?", (get.id,'sql',)).count():return public.returnMsg(False, 'ID填写错误!')
        revoke=self.select(id=get.id)
        if type(revoke)==list:
            if not 'revoke' in revoke[0]:return public.returnMsg(False, 'ID填写错误!')
            self.DB_MySQL.query(revoke[0]['revoke'])
            public.M('database_mater').where("id=? and type=?", (get.id,'sql',)).delete()
            public.WriteLog('堡塔数据库运维工具', '撤销成功:%s' %revoke[0]['ps'])
            return public.returnMsg(True, '撤销成功!')
        elif type(revoke)==dict:
            if not 'revoke' in revoke:return public.returnMsg(False, 'ID填写错误!')
            self.DB_MySQL.query(revoke[0]['revoke'])
            public.M('database_mater').where("id=? and type=?", (get.id,'sql',)).delete()
            public.WriteLog('堡塔数据库运维工具', '撤销成功:%s' % revoke['ps'])
            return public.returnMsg(True, '撤销成功!')
        else:return public.returnMsg(False, 'ID填写错误!')

    #重试
    def set_retry(self,get):
        if not 'id' in get:return public.returnMsg(False, '缺少id参数!')
        if not public.M('database_mater').where("id=? and type=?", (get.id,'sql',)).count():return public.returnMsg(False, 'ID填写错误!')
        revoke=self.select(id=get.id)
        if type(revoke)==list:
            if not 'sql' in revoke[0]:return public.returnMsg(False, 'ID填写错误!')
            self.DB_MySQL.query(revoke[0]['sql'])
            return public.returnMsg(True, '重试成功!')
        elif type(revoke)==dict:
            if not 'sql' in revoke:return public.returnMsg(False, 'ID填写错误!')
            self.DB_MySQL.query(revoke[0]['sql'])
            return public.returnMsg(True, '重试成功!')
        else:return public.returnMsg(False, 'ID填写错误!')

    #设置索引
    def check_index(self,host_table,field,mode=None):
        sql="ALTER TABLE %s ADD INDEX( `%s`);"%(host_table,field)
        data_chekc = self.DB_MySQL.query(sql)
        revoke="ALTER TABLE %s DROP INDEX %s;"%(host_table,field)
        ps='%s:%s数据库中%s表优化了%s字段'%(mode,host_table.split('.')[0],host_table.split('.')[1],field)
        self.insert(host_table.split('.')[0],host_table.split('.')[1],field,sql,revoke,ps,'sql')
        return data_chekc

    '''
     * 取数据列表
     * @param String _GET['tab'] 数据库表名
     * @param Int _GET['count'] 每页的数据行数
     * @param Int _GET['p'] 分页号  要取第几页数据
     * @return Json  page.分页数 , count.总行数   data.取回的数据
    '''
    def get_mysql_database(self,get):
        return self.database.getData(get)

    # 自定义sql语句 进行优化
    # 选择慢查询进行优化
    def optimization(self,get):
        host=get.host
        select=get.select
        mysql_data=self.sql_parse(select)
        if not mysql_data:return public.returnMsg(False, '请提供正确的sql语句')
        if len(mysql_data['from'])==0:return public.returnMsg(False, '请提供正确的sql语句')
        if len(mysql_data['select']) == 0: return public.returnMsg(False, '请提供正确的sql语句')
        if len(mysql_data['where']) == 0:
            if '.' in mysql_data['from'][0]:self.OptimizeTable(mysql_data['from'][0])
            self.OptimizeTable(mysql_data['from'][0],host)
            return public.returnMsg(True, '优化完成')
        else:
            host_tables = mysql_data['from'][0] if '.' in mysql_data['from'][0] else host+'.'+mysql_data['from'][0]
            sql="show columns from %s;" % host_tables
            data=self.chekc_types(sql,mysql_data['where'])
            if data=='1045':public.returnMsg(False, 'mysql密码错误')
            if data == '1146': public.returnMsg(False, '数据库执行错误,可能表或者字段不存在')
            if len(data)==0:return public.returnMsg(False, '数据库中未查询到此字段,可能输入的sql语句有误')
            for i in data:
                if 'int' in data[i]  or 'string'  in data[i] or 'char':data[i]='YES'
            sql="SHOW INDEX FROM %s" %host_tables
            data_chekc=self.DB_MySQL.query(sql)
            if type(data_chekc)!=list:
                 return data_chekc
            else:
                for i in data_chekc:
                    for i2 in data:
                        if i[2] == 'PRIMARY':
                            if i2 == i[4]:
                                data[i2] = 'NO'
                        if data[i2] == 'YES':
                            if i2 == i[2]:
                                data[i2] = 'NO'
        count=0
        for i in data:
            if data[i]=='YES':
                count+=1
                 #return host_tables.split('.')
                self.check_index(host_tables,i,'手动优化数据库')
        public.WriteLog('堡塔数据库运维工具','手动优化数据库:本次优化数据库【%s】中【%s】表 %s个字段' % (host_tables.split('.')[0], host_tables.split('.')[1],count))
        return public.returnMsg(True, '本次优化数据库【%s】中【%s】表 %s个字段' % (host_tables.split('.')[0], host_tables.split('.')[1],count))

    #自动优化（语句大于20s的自动优化）
    def automatic_optimization(self,get):
        optimization_data=self.get_log(get)
        count = 0
        host_list=[]
        table_list=[]
        try:
            for i in optimization_data:
                if int(i['query_time']['Query_time'])>20:
                    host=i['host']
                    select=i['select']
                    mysql_data = self.sql_parse(select)
                    if not mysql_data: continue
                    if len(mysql_data['from']) == 0: continue
                    if len(mysql_data['select']) == 0: continue
                    if len(mysql_data['where']) == 0:
                        if '.' in mysql_data['from'][0]: self.OptimizeTable(mysql_data['from'][0])
                        self.OptimizeTable(mysql_data['from'][0], host)
                        continue
                    else:
                        host_tables = mysql_data['from'][0] if '.' in mysql_data['from'][0] else host + '.' + mysql_data['from'][0]
                        sql = "show columns from %s;" % host_tables
                        data = self.chekc_types(sql, mysql_data['where'])
                        if data == '1045': continue
                        if data == '1146': continue
                        if len(data) == 0:continue
                        for i in data:
                            if 'int' in data[i] or 'string' in data[i] or 'char': data[i] = 'YES'
                            sql = "SHOW INDEX FROM %s" % host_tables
                            data_chekc = self.DB_MySQL.query(sql)
                            if type(data_chekc) != list:
                                    continue
                        else:
                            for i in data_chekc:
                                for i2 in data:
                                    if i[2] == 'PRIMARY':
                                        if i2 == i[4]:
                                            data[i2] = 'NO'
                                    if data[i2] == 'YES':
                                        if i2 == i[2]:
                                            data[i2] = 'NO'
                    for i in data:
                        if data[i] == 'YES':
                            count += 1
                            host_list.append(host_tables.split('.')[0])
                            table_list.append(host_tables.split('.')[1])
                            self.check_index(host_tables, i,'自动优化数据库')
        except:pass
        public.WriteLog('堡塔数据库运维工具', '自动优化数据库:本次优化了【%s】个数据库、【%s】张表 【%s】个表字段' % (len(list(set(host_list))),len(list(set(table_list))),count))
        return public.returnMsg(True, '本次优化了【%s】个数据库、【%s】张表 【%s】个表字段' % (len(list(set(host_list))),len(list(set(table_list))),count))

    # sql 语句性能测试（select）
    def select_testing(self,get):
        host = get.host
        select = get.select
        mysql_data = self.sql_parse(select)
        if not mysql_data: return public.returnMsg(False, '请提供正确的sql语句')
        if len(mysql_data['from']) == 0: return public.returnMsg(False, '请提供正确的sql语句')
        if len(mysql_data['select']) == 0: return public.returnMsg(False, '请提供正确的sql语句')
        start_time = time.time()
        if '.' in mysql_data['from'][0]:
            self.DB_MySQL.query(select)
            return public.returnMsg(True, '此sql语句执行耗时%s秒'%str(int(time.time()) - int(start_time)))
        else:
            select=select.replace(mysql_data['from'][0],host+'.'+mysql_data['from'][0])
            self.DB_MySQL.query(select)
            return public.returnMsg(True, '此sql语句执行耗时%s秒' %str(int(time.time()) - int(start_time)))

    # 获取文件/目录 权限信息
    def GetFileAccess(self, filename):
        if sys.version_info[0] == 2:
            filename = filename.encode('utf-8')
        data = {}
        try:
            import pwd
            stat = os.stat(filename)
            data['chmod'] = str(oct(stat.st_mode)[-3:])
            data['chown'] = pwd.getpwuid(stat.st_uid).pw_name
        except:
            data['chmod'] = 755
            data['chown'] = 'www'
        return data

    #获取mysql 的用户和登陆
    def get_mysql_user(self,get):
        result = {}
        data = self.DB_MySQL.query("select Host,User from mysql.user where Host='%'")
        return data

    #风险
    '''
    端口  (对外开放3306端口)
    文件权限 
    运行用户
    mysql用户有没高权限 
    root用户是否空密码是否允许%连接
    查询缓存是否启用
    二进制是否开启
    '''
    def risk(self,file):
        result={}
        result['file']=file
        port_open=public.M('firewall').where('port=?',('3306',)).count()
        my_cnf_chmoe=self.GetFileAccess('/etc/my.cnf')
        GetDbStatus=self.GetDbStatus(get=None)
        if len(GetDbStatus)==0:
            result['query_cache_size']=0
        else:result['query_cache_size'] = GetDbStatus['query_cache_size']
        result['mysql_open_port']=True if port_open else False
        result['my_cnf_chown']='root' if my_cnf_chmoe['chown']=='root' else my_cnf_chmoe['chown']
        result['mysql_user']=self.get_mysql_user(get=None)

        #查一个二进制日志的
        return result

    #综合评分
    '''
    1.是否开启对外开放 10 
    2.查询缓存是否启用
    3.查询缓存命中率 10 	
    4.没有使用索引的量 10 
    5.Innodb索引命中率 10 
    6.线程缓存命中率  10 
    7.cpu 开销  10 
    8.内存开销   10 
    9.IO    10 
    10.慢查询  10
    线程缓存命中率	  = ((1 - rdata.Threads_created / rdata.Connections) * 100).toFixed(2);
    索引命中率	= ((1 - rdata.Key_reads / rdata.Key_read_requests) * 100).toFixed(2);
    Innodb索引命中率	= ((1 - rdata.Innodb_buffer_pool_reads / rdata.Innodb_buffer_pool_read_requests) * 100).toFixed(2);
    查询缓存命中率	   =((parseInt(rdata.Qcache_hits) / (parseInt(rdata.Qcache_hits) + parseInt(rdata.Qcache_inserts))) * 100).toFixed(2) + '%';
    创建临时表到磁盘=((rdata.Created_tmp_disk_tables / rdata.Created_tmp_tables) * 100).toFixed(2);
    锁表次数  Table_locks_waited
    '''
    def comprehensive_score(self,get):
        result={}
        result['data']=[]
        result['fraction']=100
        #1、3306端口
        mysql_status=self.GetRunStatus(get)
        if mysql_status['File']=='OFF':public.returnMsg(False,'数据库未启动')
        port_open = public.M('firewall').where('port=?', ('3306',)).count()
        if port_open:
            result['fraction'] = result['fraction']-10
            result['data'].append('风险提醒：3306端口开启了对外连接')
        mysql_user_data = self.get_mysql_user(get=None)
        #2、 对开开放的用户
        if len(mysql_user_data)>=1:
            result['fraction'] = result['fraction'] - 10
            ret=''
            for i in mysql_user_data:
                ret += i[1] + '   '
            result['data'].append('风险提醒：mysql 存在%s个对外开放的用户 用户如下:%s'%(str(len(mysql_user_data)),ret))
        #3、查询缓存是否启用
        GetDbStatus = self.GetDbStatus(get=None)
        if len(GetDbStatus) == 0:
            result['fraction'] = result['fraction'] - 10
            result['data'].append('风险提醒:查询缓存未启用。请在配置中配置query_cache_size该项')
        else:
            if  'query_cache_size' in  GetDbStatus:
                if GetDbStatus['query_cache_size']==0:
                    result['fraction'] = result['fraction'] - 10
                    result['data'].append('风险提醒:查询缓存未启用。建议修改query_cache_size')
        try:
           # 4、线程缓存命中率
           # ((1 - rdata.Threads_created / rdata.Connections) * 100)
           thread_cache_size = int((1 - int(mysql_status['Threads_created']) / int(mysql_status['Connections'])) * 100)
           if thread_cache_size <= 50:
               result['fraction'] = result['fraction'] - 5
               result['data'].append('风险提醒:线程缓存命中率小于百分之50,建议增加thread_cache_size')
        except:pass
        try:
            # 5、索引命中率
            key_buffer_size=int((1 - int(mysql_status['Key_reads']) / int(mysql_status['Key_read_requests'])) * 100)
            if key_buffer_size <= 30:
                result['fraction'] = result['fraction'] - 5
                result['data'].append('风险提醒:索引命中率小于百分之30,建议增加key_buffer_size')
        except:pass
        try:
            #6、Innodb索引命中率
            innodb_buffer_pool_size=int((1 - int(mysql_status['Innodb_buffer_pool_reads']) / int( mysql_status['Innodb_buffer_pool_read_requests'])) * 100)
            if innodb_buffer_pool_size<=50:
                result['fraction'] = result['fraction'] - 5
                result['data'].append('风险提醒:Innodb索引命中率小于百分之50,建议增加innodb_buffer_pool_size')
            pass
        except:pass
        try:
            #7\查询缓存命中率
            query_cache_size=int(float(mysql_status['Qcache_hits']) / (float(mysql_status['Qcache_hits']) + float(mysql_status['Qcache_inserts'])) * 100)
            if query_cache_size<=20:
                result['fraction'] = result['fraction'] - 5
                result['data'].append('风险提醒:查询缓存命中率小于百分之20,建议增加query_cache_size')
        except:pass
        try:
            #8、创建临时表到磁盘
            tmp_table_size=int((int(mysql_status['Created_tmp_disk_tables']) / int(mysql_status['Created_tmp_tables'])) * 100)
            if tmp_table_size>=50:
                result['fraction'] = result['fraction'] - 5
                result['data'].append('风险提醒:创建临时表到磁盘大于百分之50,建议增加tmp_table_size')
        except:pass
        return result

    ########### 配置优化
    #获取MySQL配置状态
    def GetDbStatus(self,get):
        result = {}
        data =  self.DB_MySQL.query('show variables')
        gets = ['table_open_cache','thread_cache_size','query_cache_type','key_buffer_size','query_cache_size','tmp_table_size','max_heap_table_size','innodb_buffer_pool_size','innodb_additional_mem_pool_size','innodb_log_buffer_size','max_connections','sort_buffer_size','read_buffer_size','read_rnd_buffer_size','join_buffer_size','thread_stack','binlog_cache_size']
        result = {}
        for d in data:
            try:
                for g in gets:
                    if d[0] == g: result[g] = d[1]
            except:
                continue
        if 'query_cache_type' in result:
            if result['query_cache_type'] != 'ON': result['query_cache_size'] = '0'
        return result

    #设置MySQL配置参数
    def SetDbConf(self,get):
        gets = ['key_buffer_size','query_cache_size','tmp_table_size','max_heap_table_size','innodb_buffer_pool_size','innodb_log_buffer_size','max_connections','query_cache_type','table_open_cache','thread_cache_size','sort_buffer_size','read_buffer_size','read_rnd_buffer_size','join_buffer_size','thread_stack','binlog_cache_size']
        emptys = ['max_connections','query_cache_type','thread_cache_size','table_open_cache']
        mycnf = public.readFile('/etc/my.cnf')
        n = 0
        m_version = public.readFile('/www/server/mysql/version.pl')
        if not m_version: m_version = ''
        for g in gets:
            if m_version.find('8.') == 0 and g in ['query_cache_type','query_cache_size']: continue
            s = 'M'
            if n > 5: s = 'K'
            if g in emptys: s = ''
            rep = '\s*'+g+'\s*=\s*\d+(M|K|k|m|G)?\n'
            c = g+' = ' + get[g] + s +'\n'
            if mycnf.find(g) != -1:
                mycnf = re.sub(rep,'\n'+c,mycnf,1)
            else:
                mycnf = mycnf.replace('[mysqld]\n','[mysqld]\n' +c)
            n+=1
        public.writeFile('/etc/my.cnf',mycnf)
        return public.returnMsg(True,'SET_SUCCESS')

    ##根据mysql 近期运行情况自适应调整（每48小时调整一次）
    def mysql_adjustment(self,get):
        pass

    ### 二进制日志管理
    def file_name(self,file_dir):
        data=None
        for root, dirs, files in os.walk(file_dir):
            return {"root":root,"files":files}
        return {"root":False, "files": []}
    #获取数据库配置信息
    def GetMySQLInfo(self):
        data = {}
        try:
            public.CheckMyCnf()
            myfile = '/etc/my.cnf'
            mycnf = public.readFile(myfile)
            rep = "datadir\s*=\s*(.+)\n"
            data['datadir'] = re.search(rep,mycnf).groups()[0]
            rep = "port\s*=\s*([0-9]+)\s*\n"
            data['port'] = re.search(rep,mycnf).groups()[0]
            rep = "log-bin\s*=\s*(.+)\n"
            data['log-bin'] = re.search(rep, mycnf).groups()[0]
        except:
            data['datadir'] = '/www/server/data'
            data['port'] = '3306'
            data['log-bin']='mysql-bin'
        return data

    #查看当前的二进制文件
    def get_mysql_bin(self,get):
        result=[]
        get_mysql_path=self.GetMySQLInfo()
        if not os.path.exists(get_mysql_path['datadir']):return []
        file_data=self.file_name(get_mysql_path['datadir'])
        if len(file_data['files'])==0:return []
        for i in  file_data['files']:
            if get_mysql_path['log-bin'] in i:
                if re.search('^%s.+\d$'%get_mysql_path['log-bin'], i):
                    result.append({"root": file_data['root'], "files": i})
        return result

    #查看备份二进制文件
    def get_backup_mysql_bin(self,get):
        result = []
        get_mysql_path = self.GetMySQLInfo()
        if not os.path.exists(self.__mysql_bin_log): return []
        file_data = self.file_name(self.__mysql_bin_log)
        if len(file_data['files']) == 0: return []
        for i in file_data['files']:
            if get_mysql_path['log-bin'] in i:
                if re.search('^%s.+\d$' % get_mysql_path['log-bin'], i):
                    result.append({"root": file_data['root'], "files": i})
        return result

    #备份函数
    def backup(self,back_path,local_path):
        #备份目录没有这个文件
        if not os.path.exists(local_path):
            public.ExecShell('cp -p %s %s' % (back_path, self.__mysql_bin_log))
            if os.path.exists(local_path):
                ps='备份二进制文件成功:文件%s备份文件存放在[%s]目录中'%(local_path,self.__mysql_bin_log)
                self.insert('1', '1', '1', '1', '1',ps, 'file')
                return True
        else:
            if os.path.getsize(back_path) == os.path.getsize(local_path):
                return True
            if os.path.getsize(back_path) > os.path.getsize(local_path):
                public.ExecShell('rm -rf %s && cp -p %s %s' % (local_path,back_path, self.__mysql_bin_log))
                ps='备份二进制文件成功:文件%s备份文件存放在[%s]目录中'%(local_path,self.__mysql_bin_log)
                self.insert('1', '1', '1', '1', '1', ps, 'file')
                return True

    '''
     * 备份二进制文件
     * $_GET['all']   默认为None (代表备份全部)
     * $_['path']    代表备份的目录文件(绝对目录) 
    '''
    ###备份
    def backup_mysql_bin(self,get):
        if not 'all' in get:
            get.all=False
        if get.all:
            mysql_bin_data=self.get_mysql_bin(get)
            if len(mysql_bin_data)==0:return public.returnMsg(False, '未发现存在有mysql二进制文件')
            for i in mysql_bin_data:
                path=i['root']+'/'+i['files']
                if os.path.exists(path):
                    self.backup(path,self.__mysql_bin_log+'/'+i['files'])
            return public.returnMsg(True, '所有二进制文件备份完成,备份文件存放在[%s]目录中' % self.__mysql_bin_log)
        else:
            if not 'path' in get: return public.returnMsg(False, '缺少path参数')
            if not os.path.exists(get.path): return public.returnMsg(False, '文件路径不存在')
            if not re.search('^%s.+\d$'%self.GetMySQLInfo()['log-bin'],get.path.strip().split('/')[-1]):return public.returnMsg(False, '请选择mysql二进制文件')
            if not os.path.exists(self.__mysql_bin_log):
                os.system('mkdir -p %s'%self.__mysql_bin_log)
            #备份
            self.backup(get.path.strip(), self.__mysql_bin_log + '/' + get.path.strip().split('/')[-1])
            if os.path.exists(self.__mysql_bin_log+'/'+get.path.strip().split('/')[-1]):
                public.WriteLog('堡塔数据库运维工具','备份%s二进制文件成功:备份文件存放在[%s]目录中'%(self.__mysql_bin_log+'/'+get.path.strip().split('/')[-1],self.__mysql_bin_log))
                return public.returnMsg(True, '备份完成,备份文件存放在[%s]目录中'%self.__mysql_bin_log)
            else:return public.returnMsg(False, '备份失败,可能文件系统满了,或者受某些安全软件导致的备份失败')

    ## 删除
    def delete_file(self,get):
        if os.path.exists(get.path.strip()):
            if not re.search('^%s.+\d$' % self.GetMySQLInfo()['log-bin'],get.path.strip().split('/')[-1]): return public.returnMsg(False, '只能删除数据库二进制文件,不允许删除其他文件')
            public.ExecShell('rm -rf %s'%get.path)
            if not os.path.exists(get.path.strip()):
                public.WriteLog('堡塔数据库运维工具', '删除二进制文件成功:%s'%get.path.strip())
                return public.returnMsg(True,'删除成功')
            else:
                return public.returnMsg(False,'删除失败.可能受到某些安全软件导致的删除文件失败')
        return public.returnMsg(False, '文件不存在')

    # 创建计划任务
    def create_task(self):
        p = crontab.crontab()
        args = {
            "name": "堡塔数据库运维工具二进制文件备份",
            "type": "day",
            "where1": "",
            "hour": "1",
            "minute": "30",
            "week": "",
            "sType": "toShell",
            "sName": "",
            "backupTo": "localhost",
            "save": "",
            "sBody": "python /www/server/panel/plugin/database_mater/task_local.py",
            "urladdress": "undefined"
        }
        return p.AddCrontab(args)

    # 查看自动备份转态
    def get_automatic_status(self,get):
        if public.M('crontab').where('name=?',('堡塔数据库运维工具二进制文件备份',)).count():
            return public.returnMsg(True, '')
        else:
            return public.returnMsg(False, '')
    #删除
    def del_automatic_status(self,get):
        if public.M('crontab').where('name=?', ('堡塔数据库运维工具二进制文件备份',)).count():
            data=public.M('crontab').where('name=?', ('堡塔数据库运维工具二进制文件备份',)).getField('id')
            if type(data)==list:return public.returnMsg(False, '你没有启用该计划任务')
            p = crontab.crontab()
            return p.DelCrontab(get={'id':data})

    #自动备份防止被误删
    def automatic_backup(self,get):
        if not public.M('crontab').where('name=?', ('堡塔数据库运维工具二进制文件备份',)).count():
            return self.create_task()
        else:
            return public.returnMsg(False, '已经开启')

    # 读文件指定倒数行数
    def GetLastLine(self, inputfile, lineNum):
        result = public.GetNumLines(inputfile, lineNum)
        if len(result) < 1:
            return public.getMsg('TASK_SLEEP')
        return result

    ##分析
    def analysis_mysql(self,get):
        path=get.path.strip()
        if os.path.exists(path):
            if not re.search('^%s.+\d$' % self.GetMySQLInfo()['log-bin'],
                             get.path.strip().split('/')[-1]): return public.returnMsg(False, '只能删除数据库二进制文件,不允许删除其他文件')
            public.ExecShell('rm -rf /var/tmp/689.log && /www/server/mysql/bin/mysqlbinlog -v --base64-output=decode-rows %s> /var/tmp/689.log'%path)
            if os.path.exists('/var/tmp/689.log'):
                data = self.GetLastLine('/var/tmp/689.log', 2000)
                return public.returnMsg(True, data)
        else:
            return public.returnMsg(False, '文件不存在')

    '''
    必选参数
    path =[]
    参数可选: 
    --database=db  
    --start_datetime='2019-04-11 00:00:00'
    --stop_datetime='2019-04-11 15:00:00' 
    '''
    ##导出sql
    def export_sql(self,get):
        if not 'path' in get:
            return public.returnMsg(False, '缺少path参数')
        try:
            path=json.loads(get.path)
        except:
            return public.returnMsg(False, '请正确填写path的值')
        if len(path)==0:return public.returnMsg(False, '请正确填写path的值')
        if not 'database' in get:get.database=False
        if not 'start_datetime' in get: get.start_datetime = False
        if not 'stop_datetime' in get: get.stop_datetime = False
        ret=''
        for i in path:
            ret +=' '+str(i) +' '
        file_name='mysql_bin_'+str(int(time.time()))+'.sql'
        if not  get.database and  not get.start_datetime  and  not get.stop_datetime:
            public.ExecShell('/www/server/mysql/bin/mysqlbinlog -v --base64-output=decode-rows %s> %s' %(path,self.__mysql_bin_log+'/'+file_name))
        elif  get.database and not get.start_datetime  and  not get.stop_datetime:
            public.ExecShell('/www/server/mysql/bin/mysqlbinlog --database=%s   -v --base64-output=decode-rows %s> %s' % (
            get.database.strip(),path, self.__mysql_bin_log + '/' + file_name))
        elif  get.database  and  get.stop_datetime:
            public.ExecShell(
                '/www/server/mysql/bin/mysqlbinlog --database=%s  --stop-datetime=%s  -v --base64-output=decode-rows %s> %s' % (
                    get.database.strip(),get.stop_datetime.strip(), path, self.__mysql_bin_log + '/' + file_name))
        elif get.database and get.start_datetime and  get.stop_datetime:
            public.ExecShell('/www/server/mysql/bin/mysqlbinlog --database=%s --start-datetime=%s  --stop-datetime=%s  -v --base64-output=decode-rows %s> %s' % (
                    get.database.strip(), get.start_datetime.strip(), get.stop_datetime.strip(), path, self.__mysql_bin_log + '/' + file_name))
        elif not get.database  and get.start_datetime and  get.stop_datetime:
            public.ExecShell(
                '/www/server/mysql/bin/mysqlbinlog  --start-datetime=%s  --stop-datetime=%s  -v --base64-output=decode-rows %s> %s' % (get.start_datetime.strip(), get.stop_datetime.strip(), path,
                    self.__mysql_bin_log + '/' + file_name))
        elif not get.database and not get.start_datetime and get.stop_datetime:
            public.ExecShell(
                '/www/server/mysql/bin/mysqlbinlog    --stop-datetime=%s  -v --base64-output=decode-rows %s> %s' % (
                 get.stop_datetime.strip(), path,
                self.__mysql_bin_log + '/' + file_name))
        else:
            return public.returnMsg(False, '不允许这种导出方式')
        if os.path.exists(self.__mysql_bin_log + '/' + file_name):
            ps='%s到处sql保存于%s'%(get.path[0],self.__mysql_bin_log + '/' + file_name)
            self.insert('', '', '', '', '',ps, 'file')
            public.WriteLog('堡塔数据库运维工具', '导出sql文件成功:%s' % self.__mysql_bin_log + '/' + file_name)
            return public.returnMsg(True, self.__mysql_bin_log + '/' + file_name)
        else:
            return public.returnMsg(False, '导出失败可能%s目录无权访问或者系统文件已满' % self.__mysql_bin_log)

    #查看备份日志
    def get_backup_log(self,get):
        if 'p' not in get: get.p = '1'
        get.p = int(get.p)
        data = {}
        count = public.M('database_mater').where("type=?", ('file',)).order("id desc").count()
        data['page'] = public.get_page(count, get.p, 10)
        data['data'] = public.M('database_mater').where("type=?", ('file',)).order("id desc").limit(
            '{},{}'.format(data['page']['shift'], data['page']['row'])).field('id,ps').select()
        return data

    #查看操作日志
    def get_local_log(self,get):
        if 'p' not in get: get.p = '1'
        get.p = int(get.p)
        data = {}
        count = public.M('logs').where("type=?", ('堡塔数据库运维工具',)).order("id desc").count()
        data['page'] = public.get_page(count, get.p, 10)
        data['data'] = public.M('logs').where("type=?", ('堡塔数据库运维工具',)).order("id desc").limit(
            '{},{}'.format(data['page']['shift'], data['page']['row'])).select()
        return data