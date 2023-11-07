# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import sys, os, time, json, re, requests

panel_path = '/www/server/panel'
os.chdir(panel_path)
sys.path.insert(0, 'class/')

import public, db


class node_admin_main:
    _sql = None
    _path = panel_path + '/plugin/node_admin'
    _db_file = _path + '/data.db'
    _log_file = _path + '/sync_task.log'
    _task_log = _path + '/task_log'
    _task_id = None
    __BT_PANEL = None
    _site_list = None
    _error = None
    __session_name = 'php_filter_' + time.strftime('%Y-%m-%d')
    _request = None
    access_defs = ['run']

    def __init__(self):
        self.init_db()

        pass

    def init_db(self):
        if not self._sql:
            self._sql = db.Sql()
            self._sql._Sql__DB_FILE = self._db_file

    def write_log(self, log_type, log_msg):
        '''
            @name 写操作日志
            @author hwliang<2020-09-17>
            @param log_type<string> 日志类型
            @param log_msg<string> 日志详情
            @return bool
        '''
        pdata = {
            'log_type': log_type,
            'log_msg': log_msg,
            'log_addtime': int(time.time())
        }
        self._sql.table('node_logs').insert(pdata)
        return True

    def get_logs_list(self, args):
        '''
            @name 获取日志列表
            @author hwliang<2020-09-17>
            @param args<dict_obj>{
                p: int<分页> 默认第1页
                rows: int<每页行数> 默认每页15行
                search: string<搜索条件> 若不提供或为空，则不进行搜索
            }
            @return bool
        '''
        if not 'p' in args:
            args.p = 1
        if not 'rows' in args:
            args.rows = 15
        if not 'callback' in args:
            args.callback = ''

        if not 'search' in args:
            args.search = ''

        if args.search:
            count = self._sql.table('node_logs').where("log_type LIKE '%{search}%' OR log_msg LIKE '%{search}%'".format(search=args.search.strip()),()).count()
        else:
            count = self._sql.table('node_logs').count()
        data = public.get_page(count,int(args.p),int(args.rows),args.callback)
        
        if args.search:
            data['data'] = self._sql.table('node_logs').where("log_type LIKE '%{search}%' OR log_msg LIKE '%{search}%'".format(search=args.search.strip()),()).limit(data['shift'] + ',' + data['row']).order('log_id desc').field('log_type,log_msg,log_addtime').select()
        else:
            data['data'] = self._sql.table('node_logs').limit(data['shift'] + ',' + data['row']).order('log_id desc').field('log_type,log_msg,log_addtime').select()
        return data

    def get_group_list(self, args):
        '''
            @name 获取分组列表
            @author hwliang<2020-09-16>
            @param args<dict_obj>
            @return list
        '''

        data = self._sql.table('node_group').select()
        return data

    def get_auth(self):
        import panelAuth
        from BTPanel import session
        if self.__session_name in session:
            if session[self.__session_name] != 0:
                return session[self.__session_name]

        cloudUrl = public.GetConfigValue('home')+'/api/panel/get_soft_list_test'
        pdata = panelAuth.panelAuth().create_serverid(None)
        ret = public.httpPost(cloudUrl, pdata)
        if not ret:
            if not self.__session_name in session:
                session[self.__session_name] = 1
            return 1
        try:
            ret = json.loads(ret)
            for i in ret["list"]:
                if i['name'] == 'node_admin':
                    if i['endtime'] >= 0:
                        session[self.__session_name] = 2
                        return 2
            return 0
        except:
            session[self.__session_name] = 1
            return 1

    def get_group_find(self, args):
        '''
            @name 获取指定分组信息
            @author hwliang<2020-09-16>
            @param args<dict_obj>{
                group_id: int<分组标识>
            }
            @return dict
        '''
        if not 'group_id' in args:
            return public.returnMsg(False, '没有分组标识参数')
        group_info = self._sql.table('node_group').where('group_id=?', args.group_id).find()
        if not group_info: return public.returnMsg(False, '指定分组不存在')
        return group_info

    def create_group(self, args):
        '''
            @name 创建分组
            @author hwliang<2020-09-16>
            @param args<dict_obj>{
                title: string<分组名称>
            }
            @return dict
        '''
        if not 'title' in args:
            return public.returnMsg(False, '没有分组名称参数')
        pdata = {
            'title': args.title.strip(),
            'state': 1
        }
        if(self._sql.table('node_group').where('title=?', pdata['title']).count()):
            return public.returnMsg(False, '指定分组名称已存在')
        self._sql.table('node_group').insert(pdata)
        self.write_log('分组管理', '创建分组[{}]'.format(pdata['title']))
        return public.returnMsg(True, '分组创建成功')

    def modify_group(self, args):
        '''
            @name 修改分组
            @author hwliang<2020-09-16>
            @param args<dict_obj>{
                group_id: int<分组标识>
                title: string<分组名称>
                state: int<分组状态> 0. 停用  1.启用
            }
            @return dict
        '''
        if not 'group_id' in args:
            return public.returnMsg(False, '没有分组标识参数')
        if not 'state' in args:
            return public.returnMsg(False, '没有分组状态参数')
        if not 'title' in args:
            return public.returnMsg(False, '没有分组名称参数')

        if (not self._sql.table('node_group').where('group_id=?', args['group_id']).count()):
            return public.returnMsg(False, '指定分组不存在')

        pdata = {
            'group_id': int(args.group_id),
            'title': args.title.strip(),
            'state': int(args.state)
        }

        self._sql.table('node_group').where('group_id=?',args['group_id']).update(pdata)
        self.write_log('分组管理','修改分组[{}], title={} , state={}'.format(pdata['group_id'],pdata['title'],pdata['state']))
        return public.returnMsg(True,'修改分组成功')

    def remove_group(self, args):
        '''
            @name 删除分组
            @author hwliang<2020-09-16>
            @param args<dict_obj>{
                group_id: int<分组标识>
            }
            @return dict
        '''
        if not 'group_id' in args:
            return public.returnMsg(False, '没有分组标识参数')
        group_info = self._sql.table('node_group').where('group_id=?', args['group_id']).find()
        if (not group_info):
            return public.returnMsg(False, '指定分组不存在')
        is_node = self._sql.table('node_list').where('group_id=?', args.group_id).find()
        if is_node:
            return public.returnMsg(False, '当前有服务器正在使用此分组，不能删除')

        self._sql.table('node_group').where('group_id=?', args['group_id']).delete()
        self.write_log('分组管理', '删除分组[{}]'.format(group_info['title']))
        return public.returnMsg(True, '删除分组成功')

    def get_node_list(self, args):
        '''
            @name 获取节点列表
            @author hwliang<2020-09-16>
            @param args<dict_obj>{
                p: int<分页> 默认第1页
                rows: int<每页行数> 默认每页15行
                search: string<搜索条件> 若不提供或为空，则不进行搜索
                group_id: int<分组标识> 若不提供则返回所有分组
            }
            @return dict
        '''
        if time.time() > 1611072000:
            ret = self.get_auth()
            if ret == 0:
                return False

        if not 'p' in args:
            args.p = 1
        if not 'rows' in args:
            args.rows = 15
        if not 'callback' in args:
            args.callback = ''

        if not 'search' in args:
            args.search = ''

        if not 'group_id' in args:
            args.group_id = ''

        if not 'state' in args:
            args.state = ''
        search_where = None
        if args.search:
            search_where = "title LIKE '%{search}%' OR address LIKE '%{search}%' OR ps LIKE '%{search}%'".format(search=args.search.strip())
            count = self._sql.table('node_list').where(search_where,()).count()
        else:
            if args.group_id == '' and args.state == '':
                count = self._sql.table('node_list').count()
            elif args.state != '':
                count = self._sql.table('node_list').where('state=?', int(args.state)).count()
            else:
                count = self._sql.table('node_list').where('group_id=?', int(args.group_id)).count()

        data = public.get_page(count, int(args.p), int(args.rows), args.callback)
        field = 'sid,title,address,connect_type,group_id,state,ps,addtime'
        if search_where:
            data['data'] = self._sql.table('node_list').where(search_where,()).limit(data['shift'] + ',' + data['row']).order('addtime desc').field(field).select()
        else:
            if args.group_id == '' and args.state == '':
                data['data'] = self._sql.table('node_list').limit(data['shift'] + ',' + data['row']).order('addtime desc').field(field).select()
            elif args.state != '':
                data['data'] = self._sql.table('node_list').where('state=?',int(args.state)).limit(data['shift'] + ',' + data['row']).order('addtime desc').field(field).select()
            else:
                data['data'] = self._sql.table('node_list').where('group_id=?',int(args.group_id)).limit(data['shift'] + ',' + data['row']).order('addtime desc').field(field).select()
        return data

    def get_node_find(self, args):
        '''
            @name 获取指定节点
            @author hwliang<2020-09-16>
            @param args<dict_obj>{
                sid: int<节点标识> 必传
            }
            @return dict
        '''
        if not 'sid' in args:
            return public.returnMsg(False, '没有节点标识参数')
        data = self._sql.table('node_list').where('sid=?', int(args.sid)).find()
        if not data: return public.returnMsg(False, '指定节点不存在')
        return data

    def create_node(self, args):
        '''
            @name 创建节点
            @author hwliang<2020-09-16>
            @param args<dict_obj>{
                title: string<节点名称>
                address: string<节点IP>
                group_id: int<分组标识>
                connect_type: int<连接类型>  0.ssh 1.面板API
                connect_info: string<连接信息> json字符串
                state: int<节点状态> 0.停用 1.启用
                ps: string<节点描述>
            }
            @return dict
        '''
        args_names = ['title', 'address', 'group_id', 'connect_type', 'connect_info']
        pdata = {}
        for name in args_names:
            if not name in args:
                return public.returnMsg(False, '没有找到参数: {}'.format(name))
            pdata[name] = args[name].strip()

        pdata['ps'] = args.get('ps').strip() if args.get('ps') else '无'

        pdata['state'] = 1
        pdata['addtime'] = int(time.time())

        if self._sql.table('node_list').where('address=?', pdata['address']).count():
            return public.returnMsg(False, '指定IP地址已存在，请不要重复添加!')
        test_result = self.test_connect(pdata)
        if test_result:
            return test_result

        self._sql.table('node_list').insert(pdata)
        self.write_log('节点管理', '添加节点: {}'.format(pdata['address']))
        return public.returnMsg(True, '添加成功')

    def test_connect(self, pdata):
        '''
            @name 测试节点连接
            @author hwliang<2020-09-16>
            @param pdata<dict>
            @return dict or bool
        '''
        if pdata['connect_type'] in ['1', 1]:
            try:
                result = self.send_panel(sid=1,connect_info=json.loads(pdata['connect_info']),pdata={},p_uri='/ajax?action=GetTaskCount')
                if not isinstance(result,int):
                    return result
            except:
                return public.returnMsg(False, '连接失败!')
        return False

    def modify_node(self, args):
        '''
            @name 修改节点
            @author hwliang<2020-09-16>
            @param args<dict_obj>{
                sid: int<节点标识>
                title: string<节点名称>
                address: string<节点IP>
                group_id: int<分组标识>
                connect_type: int<连接类型>  0.ssh 1.面板API
                connect_info: string<连接信息> json字符串
                state: int<节点状态> 0.停用 1.启用
                ps: string<节点描述>
            }
            @return dict
        '''

        args_names = ['sid', 'title', 'address', 'group_id', 'connect_type', 'connect_info', 'state']
        pdata = {}
        for name in args_names:
            if not name in args:
                return public.returnMsg(False, '没有找到参数: {}'.format(name))
            pdata[name] = args[name].strip()

        pdata['ps'] = args.get('ps').strip() if args.get('ps') else '无'

        if not self._sql.table('node_list').where('sid=?', pdata['sid']).count():
            return public.returnMsg(False, '指定节点不存在!')

        test_result = self.test_connect(pdata)
        if test_result:
            return test_result

        self._sql.table('node_list').where('sid=?', pdata['sid']).update(pdata)
        self.write_log('节点管理', '修改节点: {}'.format(pdata['address']))
        return public.returnMsg(True, '修改成功')

    def batch_modify_node(self, args):
        '''
            @name 批量修改节点
            @param args<dict_obj>{
                sid: int<节点标识>
                title: string<节点名称>
                address: string<节点IP>
                group_id: int<分组标识>
                connect_type: int<连接类型>  0.ssh 1.面板API
                connect_info: string<连接信息> json字符串
                state: int<节点状态> 0.停用 1.启用
                ps: string<节点描述>
            }
            @return dict
        '''
        if not args.data:
            return public.returnMsg(False, '缺少参数data!')

        data = json.loads(args.data)
        error_info = []
        error_count = 0
        success_count = 0

        for i in data:
            args_names = ['sid', 'title', 'address', 'group_id', 'connect_type', 'connect_info', 'state', 'ps']
            pdata = {}
            for name in args_names:
                if not name in i:
                    return public.returnMsg(False, '没有找到参数: {}'.format(name))
                pdata[name] = i[name].strip() if isinstance(i[name], str) else i[name]

            # 调用test_connect时会调用json.loads
            # public.print_log(pdata['connect_info'])
            # public.print_log(type(pdata['connect_info']))
            # pdata['connect_info'] = json.dumps(pdata['connect_info'])

            if not self._sql.table('node_list').where('sid=?', pdata['sid']).count():
                error_info.append('指定节点({})不存在!'.format(i['title']))
                error_count += 1
                continue

            test_result = self.test_connect(pdata)
            if test_result:
                error_info.append('{}连接失败!'.format(i['title']))
                error_count += 1
                continue

            self._sql.table('node_list').where('sid=?', pdata['sid']).update(pdata)
            self.write_log('节点管理', '修改节点: {}'.format(pdata['address']))
            success_count += 1

        msg = '修改成功'

        if error_info:
            msg = '修改成功{}个，失败{}个。 失败信息如下：{}'.format(success_count, error_count, '; '.join(error_info))

        return public.returnMsg(True, msg)

    def remove_node(self, args):
        '''
            @name 删除节点
            @author hwliang<2020-09-16>
            @param args<dict_obj>{
                sid: int<节点标识>
            }
            @return dict
        '''
        if not 'sid' in args:
            return public.returnMsg(False, '没有找到参数：sid')
        node_info = self._sql.table('node_list').where('sid=?', args['sid']).find()
        if not node_info:
            return public.returnMsg(False, '指定节点不存在!')
        self._sql.table('node_list').where('sid=?', args['sid']).delete()
        self.write_log('节点管理', '删除节点: {}'.format(node_info['address']))
        return public.returnMsg(True, '删除成功')

    def batch_remove_node(self, args):
        '''
            @name 批量删除节点
            @author chenquanji<2023-02-08>
            @param args<dict_obj>{
                sid: list<int><节点标识>
            }
            @return dict
        '''
        if not 'sid' in args:
            return public.returnMsg(False, '没有找到参数：sid')
        sid_list = json.loads(args['sid'])

        for sid in sid_list:
            node_info = self._sql.table('node_list').where('sid=?', sid).find()
            if not node_info:
                continue
            self._sql.table('node_list').where('sid=?', sid).delete()
            self.write_log('节点管理', '删除节点: {}'.format(node_info['address']))
        return public.returnMsg(True, '删除成功')

    def get_sync_task_list(self, args):
        '''
            @name 获取同步任务列表
            @author hwliang<2020-09-16>
            @param args<dict_obj>{
                p: int<分页> 默认第1页
                rows: int<每页行数> 默认每页15行
            }
            @return dict
        '''

        if not 'p' in args:
            args.p = 1
        if not 'rows' in args:
            args.rows = 15
        if not 'callback' in args:
            args.callback = ''
        if not 'order' in args:
            args.order = 'state asc'

        count = self._sql.table('node_task').count()
        data = public.get_page(count, int(args.p), int(args.rows), args.callback)
        data['data'] = self._sql.table('node_task').limit(data['shift'] + ',' + data['row']).order(args.order).select()
        for i in range(len(data['data'])):
            if not data['data'][i]['speed']: data['data'][i]['speed'] = ''
            data['data'][i]['msg'] = ''
            if data['data'][i]['state'] in ['-1', -1]:
                self._task_log_file = '{}/{}.log'.format(self._task_log, data['data'][i]['task_id'])
                data['data'][i]['msg'] = public.GetNumLines(self._task_log_file, 100)
        return data

    def get_sync_task_find(self, args):
        '''
            @name 获取指定同步任务
            @author hwliang<2020-09-16>
            @param args<dict_obj>{
                task_id: int<任务标识>
            }
            @return dict
        '''

        if not 'task_id' in args:
            return public.returnMsg(False, '指定任务不存在!')

        data = self._sql.table('node_task').where('task_id=?', int(args.task_id)).find()
        if not data['speed']: data['speed'] = ''
        data['msg'] = ''
        if data['state'] in ['-1', -1, 1, '1']:
            self._task_log_file = '{}/{}.log'.format(self._task_log, data['task_id'])
            data['msg'] = public.GetNumLines(self._task_log_file, 100)
        return data

    def get_sync_task_detail(self, args):
        '''
            @name 获取同步任务详细信息
            @author chenquanji<2023-02-09>
            @return void
        '''
        task_id = args.task_id
        node_info = self._sql.table('node_task').where('task_id=?', int(task_id)).find()
        task_info = json.loads(node_info['task_info'])
        content = set()
        target_website = set()
        for i in task_info:
            content.add(i.get('type'))
            target_website.add(i.get('name'))

        rsp = {
            "task_id": node_info['task_id'],
            "task_name": node_info['task_name'],
            "address": node_info['address'],
            "content": list(content),
            "target_website": list(target_website)
        }

        return rsp

    def get_sync_log(self, args):
        '''
            @name 取指定同步日志
            @author hwliang<2020-10-23>
            @return void
        '''
        task_id = args.task_id
        self._task_log_file = '{}/{}.log'.format(self._task_log, task_id)
        return public.GetNumLines(self._task_log_file, 2000)

    def resync_task(self, args):
        '''
            @name 重新执行指定同步任务
            @author hwliang<2020-10-23>
            @return void
        '''
        task_id = args.task_id
        self._sql.table('node_task').where('task_id=?', task_id).update({'state': 0, 'speed': '', 'endtime': 0, 'addtime': int(time.time())})
        self.start_task('single', task_id)
        return public.returnMsg(True, '正在重新同步')

    def batch_resync_task(self, args):
        '''
            @name 批量重新执行指定同步任务
            @author chenquanji<2023-02-08>
            @return void
        '''
        task_ids = json.loads(args.task_id)
        for task_id in task_ids:
            self._sql.table('node_task').where('task_id=?', task_id).update(
                {'state': 0, 'speed': '', 'endtime': 0, 'addtime': int(time.time())})
        self.start_task('batch', task_ids)
        return public.returnMsg(True, '正在重新同步')

    def create_sync_task(self, args):
        '''
            @name 创建同步任务
            @author hwliang<2020-09-19>
            @param args<dict_obj>{
                task_name: string<任务名称>
                sid: json<服务器标识列表>
                task_info: json<同步内容>
            }
            @return dict
        '''
        if not 'task_name' in args: return public.returnMsg(False, '请输入任务名称')
        if not 'sid' in args: return public.returnMsg(False, '请指定目标服务器')
        if not 'task_info' in args: return public.returnMsg(False, '请选择要同步的内容')

        sid_list = json.loads(args.sid)
        task_info = json.loads(args.task_info)
        if not task_info: return public.returnMsg(False, '请选择要同步的内容')
        if not sid_list: return public.returnMsg(False, '请指定目标服务器')
        for sid in sid_list:
            node_info = self._sql.table('node_list').where('sid=?', sid).find()
            if not node_info: continue
            # 添加site_cert和site_files同步任务的远程校验
            for i in task_info:
                if i.get('type') == 'site_cert' or i.get('type') == 'site_files':
                    self.get_site_list(json.loads(node_info['connect_info']))
                    if not i.get('name') in self._site_list:
                        return public.returnMsg(False, '远程站点不存在')

            pdata = {}
            pdata['task_name'] = '{}[{}]'.format(args.task_name, node_info['title'])
            pdata['sid'] = sid
            pdata['address'] = node_info['address']
            pdata['state'] = 0
            pdata['addtime'] = int(time.time())
            pdata['endtime'] = 0
            pdata['task_info'] = args.task_info
            result = self._sql.table('node_task').insert(pdata)

        self.write_log('同步任务', '添加同步任务[{}]'.format(args.task_name))
        return public.returnMsg(True, '同步任务[{}]添加成功!'.format(args.task_name))

    def batch_create_sync_task(self, args):
        '''
            @name 批量创建同步任务
            @author quanjichen<2023-02-08>
            @param args<dict_obj>{
                task_name: string<任务名称>
                sid: json<服务器标识列表>
                task_info: json<同步内容>
                target_info: 目标网站
            }
            @return dict
        '''
        if not 'task_name' in args: return public.returnMsg(False, '请输入任务名称')
        if not 'sid' in args: return public.returnMsg(False, '请指定目标服务器')
        if not 'task_info' in args: return public.returnMsg(False, '请选择要同步的内容')
        if not 'target_info' in args: return public.returnMsg(False, '请选择目标网站')

        sid_list = json.loads(args.sid)
        task_info = json.loads(args.task_info)
        target_info = json.loads(args.target_info)
        if not task_info: return public.returnMsg(False, '请选择要同步的内容')
        if not sid_list: return public.returnMsg(False, '请指定目标服务器')
        for sid in sid_list:
            node_info = self._sql.table('node_list').where('sid=?', sid).find()
            if not node_info: continue
            # 添加site_cert和site_files同步任务的远程校验
            for i in task_info:
                if i == 'site_cert' or i == 'site_files':
                    self.get_site_list(json.loads(node_info['connect_info']))
                    if not set(target_info).issubset(set(self._site_list.keys())):
                        return public.returnMsg(False, '远程站点不存在')

            pdata = {}
            pdata['task_name'] = '{}[{}]'.format(args.task_name, node_info['title'])
            pdata['sid'] = sid
            pdata['address'] = node_info['address']
            pdata['state'] = 0
            pdata['addtime'] = int(time.time())
            pdata['endtime'] = 0
            data = [{'type': task, 'name': target} for target in target_info for task in task_info]
            pdata['task_info'] = json.dumps(data)
            result = self._sql.table('node_task').insert(pdata)

        self.write_log('同步任务', '添加同步任务[{}]'.format(args.task_name))
        return public.returnMsg(True, '同步任务[{}]添加成功!'.format(args.task_name))

    def remove_sync_task(self, args):
        '''
            @name 删除同步任务
            @author hwliang<2020-09-19>
            @param args<dict_obj>{
                task_id: int<任务标识>
            }
            @return dict
        '''
        task_id = int(args.task_id)
        task_info = self._sql.table('node_task').where('task_id=?', task_id).find()
        if not task_info: return public.returnMsg(False, '指定任务不存在')
        self._sql.table('node_task').where('task_id=?', task_id).delete()
        self.write_log('同步任务', '删除同步任务[{}]'.format(task_info['task_name']))
        return public.returnMsg(True, '任务删除成功')

    def batch_remove_sync_task(self, args):
        '''
            @name 批量删除同步任务
            @author chenquanji<2023-02-08>
            @param args<dict_obj>{
                task_id: list<int><任务标识>
            }
            @return dict
        '''
        task_ids = json.loads(args.task_id)
        for task_id in task_ids:
            task_id = int(task_id)
            task_info = self._sql.table('node_task').where('task_id=?', task_id).find()
            if not task_info: return public.returnMsg(False, '指定任务不存在')
            self._sql.table('node_task').where('task_id=?', task_id).delete()
            self.write_log('同步任务', '删除同步任务[{}]'.format(task_info['task_name']))
        return public.returnMsg(True, '任务删除成功')

    def start_task(self, mode='all', task_id=None):
        task_list = self._sql.table('node_task').where('state=? or state=?', (0, -1)).select()
        if not task_list: return public.returnMsg(False, '当前没有等待执行的任务')

        if len(public.ExecShell('ps aux|grep START_TASK|grep -v grep')[0]) > 10:
            return public.returnMsg(False, '请等待所有任务执行完成再重试!')

        if mode == 'single':
            self.single_run(task_id)
            return public.returnMsg(True, '正在执行')

        if mode == 'batch':
            self.batch_run(task_id)
            return public.returnMsg(True, '正在执行')

        python_bin = public.get_python_bin()
        public.ExecShell("nohup {} {}/START_TASK 2>&1 > {}/error.log &".format(python_bin, self._path, self._path))
        return public.returnMsg(True, '正在执行')

    def echo_log(self, msg):
        '''
            @name 写输出日志
            @author hwliang<2020-09-24>
            @param msg<string> 内容
            @return void
        '''
        public.writeFile(self._log_file, str(msg) + "\n", 'a+')

    def write_speed(self, msg):
        '''
            @name 写当前进度
            @author hwliang<2020-09-24>
            @param msg<string> 内容
            @return void
        '''
        self._sql.where('task_id=?', self._task_id).setField('speed', msg)

    def get_local_site_list(self, args):
        data = public.M('sites').field('name').order('id desc').select()
        result = [x['name'] for x in data]
        return result

    def get_site_list(self, connect_info):
        '''
            @name 获取指定服务器的网站列表
            @author hwliang<2020-10-12>
            @param connect_info<dict> 服务器信息
            @return void
        '''
        if self._site_list: return self._site_list
        pdata = {
            'table': 'sites',
            'limit': '10000'
        }
        result = self.send_panel(connect_info=connect_info, pdata=pdata, p_uri='/data?action=getData')
        if not 'data' in result:
            return False
        self._site_list = {}
        for s in result['data']:
            self._site_list[s['name']] = s

        return self._site_list

    def get_php_version(self, siteName):
        '''
            @name 获取指定站点的PHP版本
            @author hwliang<2020-10-12>
            @param siteName<string> 网站名称
            @return string
        '''

        conf_file = '/www/server/panel/vhost/nginx/{}.conf'.format(siteName)
        if not os.path.exists(conf_file): return '00'
        conf_body = public.readFile(conf_file)
        tmp = re.findall(r"enable-(\d+).conf", conf_body)
        if not tmp: return '00'
        return tmp[0]

    def create_site(self, connect_info, siteInfo):
        '''
            @name 创建网站
            @author hwliang<2020-10-12>
            @param connect_info<dict> 服务器信息
            @param siteInfo<dict> 网站信息
            @return dict
        '''
        domainList = []
        s_port = '80'
        for d in siteInfo['domain']:
            if siteInfo['name'] == d['name']:
                s_port = d['port']
                continue
            domainList.append('{}:{}'.format(d['name'], d['port']))

        webname = {
            'domain': siteInfo['name'],
            'domainlist': domainList,
            'count': len(domainList)
        }

        pdata = {
            'webname': json.dumps(webname),
            'ps': siteInfo['ps'],
            'path': siteInfo['path'],
            'ftp': 'false',
            'sql': 'false',
            'codeing': 'utf8',
            'type': 'PHP',
            'version': self.get_php_version(siteInfo['name']),
            'type_id': '0',
            'port': s_port
        }

        result = self.send_panel(connect_info=connect_info, pdata=pdata, p_uri='/site?action=AddSite')
        return result

    def add_domain(self, connect_info, siteInfo, domains):
        '''
            @name 添加域名
            @author hwliang<2020-10-12>
            @param connect_info<dict> 服务器信息
            @param siteInfo<dict> 网站信息
            @param domains<list> 域名列表信息
            @return dict
        '''
        domain = ','.join(domains)
        pdata = {
            'id': self._site_list[siteInfo['name']]['id'],
            'webname': siteInfo['name'],
            'domain': domain
        }
        result = self.send_panel(connect_info=connect_info, pdata=pdata, p_uri='/site?action=AddDomain')
        return result

    def remove_domain(self, connect_info, siteInfo, domains):
        '''
            @name 删除域名
            @author hwliang<2020-10-12>
            @param connect_info<dict> 服务器信息
            @param siteInfo<dict> 网站信息
            @param domain<string> 域名信息
            @return dict
        '''
        for domain in domains:
            port = '80'
            if domain.find(':') != -1:
                domain, port = domain.split(':')

            pdata = {
                'id': self._site_list[siteInfo['name']]['id'],
                'webname': siteInfo['name'],
                'domain': domain,
                'port': port
            }
            result = self.send_panel(connect_info=connect_info, pdata=pdata, p_uri='/site?action=DelDomain')
        return result

    def sync_site_config(self, siteName, connect_info):
        '''
            @name 同步网站配置
            @author hwliang<2020-10-12>
            @param siteName<dict> 网站名称
            @param connect_info<dict> 服务器信息
            @return bool
        '''
        self.write_speed('正在同步网站配置')
        self.write_task_log('校验同步信息')
        siteInfo = public.M('sites').where('name=?', siteName).field('id,name,path,ps').find()
        if not siteInfo: return False
        siteInfo['domain'] = public.M('domain').where('pid=?', siteInfo['id']).field('name,port').select()

        self.get_site_list(connect_info)
        # 同步网站记录
        if not siteName in self._site_list:
            self.write_task_log('正在创建远程站点')
            result = self.create_site(connect_info, siteInfo)

            if not 'siteId' in result:
                self.write_task_log('远程站点创建失败,退出同步进程')
                return False

            self._site_list[siteName] = siteInfo
            self._site_list[siteName]['id'] = result['siteId']

        # 同步域名列表
        self.write_task_log('正在同步域名列表')
        pdata = {
            'table': 'domain',
            'list': 'True',
            'search': self._site_list[siteName]['id']
        }
        to_domains = self.send_panel(connect_info=connect_info, pdata=pdata, p_uri='/data?action=getData')
        so_domains = siteInfo['domain']
        to_domain_list = [x['name'] + ':' + str(x['port']) for x in to_domains]
        so_domain_list = [x['name'] + ':' + str(x['port']) for x in so_domains]

        # 删除多余域名
        x_domain = []
        for td in to_domains:
            tmp_domain = "{}:{}".format(td['name'], td['port'])
            if tmp_domain in so_domain_list:
                continue
            x_domain.append(tmp_domain)

        if x_domain:
            self.remove_domain(connect_info, siteInfo, x_domain)

        # 添加域名
        x_domain = []
        for sd in so_domains:
            tmp_domain = "{}:{}".format(sd['name'], sd['port'])
            if tmp_domain in to_domain_list:
                continue
            x_domain.append(tmp_domain)

        if x_domain:
            self.add_domain(connect_info, siteInfo, x_domain)

        # 同步配置文件
        self.write_task_log('正在同步网站配置文件')
        sync_files = [
            '/www/server/nginx/conf',
            '/www/server/apache/conf',
            '{}/vhost/nginx/{}.conf'.format(panel_path, siteName),
            '{}/vhost/nginx/redirect/{}'.format(panel_path, siteName),
            '{}/vhost/nginx/proxy/{}'.format(panel_path, siteName),
            '{}/vhost/nginx/dir_auth/{}'.format(panel_path, siteName),
            '{}/vhost/apache/{}.conf'.format(panel_path, siteName),
            '{}/vhost/apache/redirect/{}'.format(panel_path, siteName),
            '{}/vhost/apache/proxy/{}'.format(panel_path, siteName),
            '{}/vhost/apache/dir_auth/{}'.format(panel_path, siteName),
            '{}/vhost/openlitespeed/{}.conf'.format(panel_path, siteName),
            '{}/vhost/openlitespeed/listen'.format(panel_path),
            '{}/vhost/openlitespeed/redirect/{}.conf'.format(panel_path, siteName),
            '{}/vhost/openlitespeed/proxy/{}.conf'.format(panel_path, siteName),
            '{}/vhost/openlitespeed/detail/{}.conf'.format(panel_path, siteName),
            '{}/vhost/openlitespeed/detail/ssl/{}.conf'.format(panel_path, siteName),
            '/www/server/pass/{}.pass'.format(siteName),
            '/www/server/pass/{}'.format(siteName),
            '{}/vhost/rewrite/{}.conf'.format(panel_path, siteName),
            '{}/vhost/open_basedir/nginx/{}.conf'.format(panel_path, siteName),
            '{}/vhost/cert/{}'.format(panel_path, siteName)
        ]

        # 获取子目录绑定rewrite文件
        rewrite_path = '{}/vhost/rewrite'.format(panel_path)
        rewrite_name = '{}_'.format(siteName)
        for re_name in os.listdir(rewrite_path):
            if re_name.find(rewrite_name) == 0:
                sync_files.append(rewrite_path + '/' + re_name)

        for sf in sync_files:  # 上传文件列表
            if os.path.isfile(sf):
                self.upload_file(sf, os.path.dirname(sf), connect_info)
            else:
                self.upload_file(sf, sf, connect_info)
        self.write_task_log('同步完成')

    def sync_site_files(self, siteName, connect_info):
        '''
            @name 同步网站文件
            @author hwliang<2020-10-20>
            @param siteName<dict> 网站名称
            @param connect_info<dict> 服务器信息
            @return bool
        '''
        self.write_task_log('正在准备同步信息')
        siteInfo = public.M('sites').where('name=?', siteName).field('id,name,path').find()
        if not siteInfo:
            self.write_task_log('指定网站不存在')
            self._error = '指定网站不存在'
            return False
        self.get_site_list(connect_info)
        if not siteName in self._site_list:
            self.write_task_log('远程站点不存在')
            self._error = '指定网站不存在'
            return False
        site_path = siteInfo['path']
        self.write_task_log('开始同步网站文件')
        self.upload_file(site_path, self._site_list[siteName]['path'], connect_info)
        return True

    def sync_site_cert(self, siteName, connect_info):
        '''
            @name 同步网站SSL
            @author hwliang<2020-10-20>
            @param siteName<dict> 网站名称
            @param connect_info<dict> 服务器信息
            @return bool
        '''
        self.write_task_log('正在准备同步信息')
        siteInfo = public.M('sites').where('name=?', siteName).field('id,name,path').find()
        if not siteInfo:
            self.write_task_log('指定网站不存在')
            self._error = '指定网站不存在'
            return False
        self.get_site_list(connect_info)
        if not siteName in self._site_list:
            self.write_task_log('远程站点不存在')
            self._error = '远程站点不存在'
            return False
        self.write_task_log('开始同步SSL证书文件')
        cert_path = '{}/vhost/cert/{}'.format(panel_path, siteName)
        self.upload_file(cert_path, os.path.dirname(cert_path), connect_info)
        return True

    def sync_site_rewrite(self, siteName, connect_info):
        '''
            @name 同步网站伪静态
            @author hwliang<2020-10-20>
            @param siteName<dict> 网站名称
            @param connect_info<dict> 服务器信息
            @return bool
        '''
        self.write_task_log('正在准备同步信息')
        siteInfo = public.M('sites').where('name=?', siteName).field('id,name,path').find()
        if not siteInfo:
            self.write_task_log('指定网站不存在')
            self._error = '指定网站不存在'
            return False
        self.get_site_list(connect_info)
        if not siteName in self._site_list:
            self.write_task_log('远程站点不存在')
            self._error = '远程站点不存在'
            return False
        self.write_task_log('开始同步rewrite文件')
        ngx_rewrite_path = '{}/vhost/rewrite/{}.conf'.format(panel_path, siteName)
        self.upload_file(ngx_rewrite_path, os.path.dirname(ngx_rewrite_path), connect_info)
        return True

    def sync_php_config(self, php_version, connect_info):
        pass

    def sync_mysql_config(self, connect_info):
        pass

    def sync_nginx_config(self, connect_info):
        pass

    def sync_apache_config(self, connect_info):
        pass

    def sync_database_data(self, dataName, connect_info):
        pass

    def sync_waf_config(self, siteName, connect_info):
        pass

    def write_task_log(self, msg):
        if not os.path.exists(self._task_log):
            os.makedirs(self._task_log)
        public.writeFile(self._task_log_file, str(msg) + "\n", 'a+')

    def run_task(self, task_info):
        if not task_info['connect_info']:
            self._sql.table('node_task').where('task_id=?', task_info['task_id']).update({'state': 2, 'speed': '未找到节点服务器信息，请查看节点是否已删除！'})
            return
        connect_info = json.loads(task_info['connect_info'])
        task_info_list = json.loads(task_info['task_info'])
        self._task_id = task_info['task_id']
        self._task_log_file = '{}/{}.log'.format(self._task_log, self._task_id)
        self._sql.table('node_task').where('task_id=?', task_info['task_id']).setField('state', -1)
        self.write_speed('开始同步任务')
        self._error = None
        for t_info in task_info_list:

            if t_info['type'] == 'site_config':
                if not 'name' in t_info:
                    self._sql.table('node_task').where('task_id=?', task_info['task_id']).setField('state', 1)
                    continue
                self.sync_site_config(t_info['name'], connect_info)
            elif t_info['type'] == 'site_files':
                self.sync_site_files(t_info['name'], connect_info)
            elif t_info['type'] == 'site_cert':
                self.sync_site_cert(t_info['name'], connect_info)
            elif t_info['type'] == 'site_rewrite':
                self.sync_site_rewrite(t_info['name'], connect_info)
            elif t_info['type'] == 'php_config':
                self.sync_php_config(t_info['name'], connect_info)
            elif t_info['type'] == 'mysql_config':
                self.sync_mysql_config(connect_info)
            elif t_info['type'] == 'nginx_config':
                self.sync_nginx_config(connect_info)
            elif t_info['type'] == 'apache_config':
                self.sync_apache_config(connect_info)
            elif t_info['type'] == 'database_data':
                self.sync_database_data(t_info['name'], connect_info)
            elif t_info['type'] == 'waf_config':
                self.sync_waf_config(t_info['name'], connect_info)

        if not self._error:
            self._sql.table('node_task').where('task_id=?', task_info['task_id']).update({'state': 1, 'endtime': int(time.time())})
            self.reload_webservice(connect_info)
        else:
            self._sql.table('node_task').where('task_id=?', task_info['task_id']).update({'state': 2, 'speed': self._error})

    def reload_webservice(self, connect_info):
        '''
            @name 重载web服务器
            @author hwliang<2020-09-24>
            @return void
        '''
        pdata = {
            'name': 'nginx',
            'type': 'reload'
        }
        self.send_panel(connect_info=connect_info, pdata=pdata, p_uri='/system?action=ServiceAdmin')
        pdata['name'] = 'httpd'
        self.send_panel(connect_info=connect_info, pdata=pdata, p_uri='/system?action=ServiceAdmin')

    def run(self):
        '''
            @name 开始同步任务
            @author hwliang<2020-09-24>
            @return void
        '''
        task_list = self._sql.table('node_task').where('state=? or state=?', (0, -1)).select()
        if not task_list:
            self.echo_log("没有需要执行的任务!")

        for task_info in task_list:
            task_info['connect_info'] = self._sql.table('node_list').where('sid=?', task_info['sid']).getField(
                'connect_info')
            self.run_task(task_info)

    def single_run(self, task_id):
        '''
            @name 开始同步任务
            @author hwliang<2020-09-24>
            @return void
        '''
        task_list = self._sql.table('node_task').where('task_id=?', task_id).select()
        if not task_list:
            self.echo_log("没有需要执行的任务!")
        for task_info in task_list:
            task_info['connect_info'] = self._sql.table('node_list').where('sid=?', task_info['sid']).getField(
                'connect_info')
            self.run_task(task_info)

    def batch_run(self, task_id):
        '''
            @name 开始同步任务
            @author hwliang<2020-09-24>
            @return void
        '''
        field = '?,' * len(task_id)

        task_list = self._sql.table('node_task').where('task_id in ({})'.format(field[:-1]), task_id).select()
        if not task_list:
            self.echo_log("没有需要执行的任务!")
        for task_info in task_list:
            task_info['connect_info'] = self._sql.table('node_list').where('sid=?', task_info['sid']).getField('connect_info')
            self.run_task(task_info)

    def get_history_list(self, args):
        '''
            @name 获取历史副本列表
            @author hwliang<2020-09-19>
            @param args<dict_obj>{
                p: int<分页>
                sid: int<服务器标识>
                rows: int<每页行数>
            }
            @return dict
        '''

    def get_history_find(self, args):
        '''
            @name 获取历史副本列表
            @author hwliang<2020-09-19>
            @param args<dict_obj>{
                p: int<分页>
                sid: int<服务器标识>
                rows: int<每页行数>
            }
            @return dict
        '''

    def add_history(self, args):
        '''
            @name 添加历史副本
            @author hwliang<2020-09-19>
            @param args<dict_obj>{
                task_id: int<任务标识>
            }
            @return dict
        '''

    def rec_history(self, args):
        '''
            @name 恢复历史副本
            @author hwliang<2020-09-19>
            @param args<dict_obj>{
                history_id: int<历史副本标识>
            }
            @return dict
        '''

    def remove_history(self, args):
        '''
            @name 删除历史副本
            @author hwliang<2020-09-19>
            @param args<dict_obj>{
                history_id: int<历史副本标识>
            }
            @return dict
        '''
        pass

    def upload_file(self, file_path, upload_path, connect_info):
        file_path = file_path.replace('//', '/')
        upload_path = upload_path.replace('//', '/')
        if not os.path.exists(file_path): return
        self.__BT_PANEL = connect_info['panel']
        pdata = self.__get_key_data(token=connect_info['token'])
        pdata['f_path'] = upload_path
        if not self._request: self._request = requests.session()
        if not os.path.isdir(file_path): return self.start_upload(pdata, file_path)
        n = 0
        size = 0
        for d_info in os.walk(file_path):
            pdata['f_path'] = (upload_path + '/' + d_info[0].replace(file_path, '')).replace('//', '/')
            mode_user = public.get_mode_and_user(d_info[0])
            pdata['dir_mode'] = "{},{}".format(mode_user['mode'], mode_user['user'])
            for name in d_info[2]:
                filename = os.path.join(d_info[0], name)
                mode_user_file = public.get_mode_and_user(filename)
                pdata['file_mode'] = "{},{}".format(mode_user_file['mode'], mode_user_file['user'])
                pdata['f_size'] = os.path.getsize(filename)
                self.write_task_log("SYNC {}".format(filename))
                self.start_upload(pdata, filename)
                n += 1
                size += pdata['f_size']

        self.write_task_log('同步完成，文件数量: {}, 总大小: {}'.format(n, public.to_size(size)))

    def get_filename(self, filename):
        return filename.split('/')[-1]

    def start_upload(self, pdata, filename):
        pdata['f_start'] = 0
        pdata['f_name'] = self.get_filename(filename)
        pdata['action'] = 'upload'
        if not 'f_size' in pdata: pdata['f_size'] = os.path.getsize(filename)
        f = open(filename, 'rb')
        ret = self.send_file_to(pdata, f)
        f.close()
        return ret

    def send_file_to(self, data, f):

        max_size = 1024 * 1024 * 2

        f.seek(data['f_start'])
        f_end = max_size
        t_end = data['f_size'] - data['f_start']
        if t_end < max_size: f_end = t_end

        files = {'blob': f.read(f_end)}
        try:
            ret = self._request.post(self.__BT_PANEL + '/files', data=data, files=files, verify=False)
        except:
            return
        if re.search(r'^\d+$', ret.text):
            data['f_start'] = int(ret.text)
            return self.send_file_to(data, f)
        else:
            self.write_task_log(os.path.join(data['f_path'], data['f_name']) + " {} => OK".format(data['f_size']))
            return ret.text

    # 发送指令到面板
    def send_panel(self, args=None, sid=None, connect_info=None, pdata=None, p_uri=None):
        if not connect_info:
            if not sid:
                sid = int(args.sid)
            connect_info = json.loads(self._sql('node_list').where('sid=?', (sid,)).getField('connect_info'))
        if pdata == None:
            pdata = json.loads(args.pdata)
        if not p_uri:
            p_uri = args.p_uri
        pdata = self.__get_key_data(pdata, connect_info['token'])
        if not self._request: self._request = requests.session()
        result = self._request.post(connect_info['panel'] + '/' + p_uri, pdata, timeout=60, verify=False).text
        try:
            result = json.loads(result)
        except:
            return result
        return result

    # 构造带有签名的关联数组
    def __get_key_data(self, pdata={}, token=""):
        if not pdata: pdata = {}
        pdata['request_time'] = int(time.time())
        pdata['request_token'] = public.md5(str(pdata['request_time']) + '' + public.md5(str(token)))
        return pdata


if __name__ == '__main__':
    p = node_admin_main()
    p.run()




