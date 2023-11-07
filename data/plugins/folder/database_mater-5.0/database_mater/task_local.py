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
import os,public,re

class backup:
    __mysql_bin_log='/www/backup/mysql_bin_backup'

    ### 二进制日志管理
    def file_name(self,file_dir):
        data=None
        for root, dirs, files in os.walk(file_dir):
            return {"root":root,"files":files}
        return {"root":False, "files": []}

    # 获取数据库配置信息
    def GetMySQLInfo(self):
        data = {}
        try:
            public.CheckMyCnf()
            myfile = '/etc/my.cnf'
            mycnf = public.readFile(myfile)
            rep = "datadir\s*=\s*(.+)\n"
            data['datadir'] = re.search(rep, mycnf).groups()[0]
            rep = "port\s*=\s*([0-9]+)\s*\n"
            data['port'] = re.search(rep, mycnf).groups()[0]
            rep = "log-bin\s*=\s*(.+)\n"
            data['log-bin'] = re.search(rep, mycnf).groups()[0]
        except:
            data['datadir'] = '/www/server/data'
            data['port'] = '3306'
            data['log-bin'] = 'mysql-bin'
        return data

    #查看当前的二进制文件
    def get_mysql_bin(self):
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

    #备份函数
    def backup(self,back_path,local_path):
        #备份目录没有这个文件
        if not os.path.exists(local_path):
            public.ExecShell('cp -p %s %s' % (back_path, self.__mysql_bin_log))
            if os.path.exists(local_path):
                print('正在备份二进制文件%s  |  文件备份成功' % back_path)
                return True
        else:
            if os.path.getsize(back_path) == os.path.getsize(local_path):
                print('正在备份二进制文件%s   |  文件未发生变化跳过' % back_path)
                return True
            if os.path.getsize(back_path) > os.path.getsize(local_path):
                public.ExecShell('rm -rf %s && cp -p %s %s' % (local_path,back_path, self.__mysql_bin_log))
                print('正在备份二进制文件%s  |  文件发生变化已成功备份' % back_path)
                return True

    def backup_mysql_bin(self):
        mysql_bin_data=self.get_mysql_bin()
        if len(mysql_bin_data)==0:exit('未发现存在有mysql二进制文件')

        for i in mysql_bin_data:
            path=i['root']+'/'+i['files']
            if os.path.exists(path):

                self.backup(path,self.__mysql_bin_log+'/'+i['files'])

        print('所有二进制文件备份完成,备份文件存放在[%s]目录中' %self.__mysql_bin_log)
        print('------------EOF -----------')
if __name__ == "__main__":
    backup=backup()
    backup.backup_mysql_bin()