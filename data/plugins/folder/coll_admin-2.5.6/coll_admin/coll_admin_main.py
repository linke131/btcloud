#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

# +--------------------------------------------------------------------
# |   堡塔云控管理器
# +--------------------------------------------------------------------
import public, os


class coll_admin_main:
    _init = "/etc/init.d/baota"
    _path = '/www/server/coll'

    def M(self, table_name):
        import db
        sql = db.Sql()
        sql._Sql__DB_FILE = '/www/server/coll/data/data.db'
        return sql.table(table_name)

    # 获取状态
    def get_stat(self, args):
        if not os.path.exists(self._init): return public.returnMsg(False, '未安装!')
        data = {}
        data['state'] = public.process_exists('baota_coll')
        data['port'] = int(public.readFile(self._path + '/data/port.pl'))
        data['host'] = public.GetHost()
        data['admin_path'] = self.get_admin_path()
        data['username'] = self.M('users').where('uid=?', 1).getField('username')
        data['password'] = public.readFile(self._path + '/default.pl')
        if data['password']: data['password'] = data['password'].strip()
        return data

    # 获取安全入口
    def get_admin_path(self, get=None):
        admin_path_file = self._path + '/data/admin_path.pl'
        admin_path = '/'
        if os.path.exists(admin_path_file): admin_path = public.readFile(admin_path_file).strip()
        return admin_path

    # 安装
    def install(self, args):
        version = public.version()
        if version < "6.9.9": 
            if len(version) > 5:
                if version < "6.9.37":
                    return public.returnMsg(False, '请将面板升级到最新版11!')
            else:
                return public.returnMsg(False, '请将面板升级到最新版22!')
        if os.path.exists(self._init): return public.returnMsg(False, '已经安装过了!')
        if public.M('task_list').where('name=? AND (status=? OR status=?)', ('安装堡塔云控', 0, -1)).count():
            return public.returnMsg(False, '安装任务已存在!')
        import panelTask
        t = panelTask.bt_task()
        t.create_task("安装堡塔云控", 0, "curl http://download.bt.cn/coll_free/install.sh|bash")
        return public.returnMsg(True, '已将安装任务添加到队列!')

    # 停止
    def stop(self, args):
        public.ExecShell("/etc/init.d/baota stop")
        return public.returnMsg(True, '操作成功!')

    # 启动
    def start(self, args):
        public.ExecShell("/etc/init.d/baota start")
        return public.returnMsg(True, '操作成功!')

    # 重启
    def restart(self, args):
        public.ExecShell("/etc/init.d/baota restart")
        return public.returnMsg(True, '操作成功!')
