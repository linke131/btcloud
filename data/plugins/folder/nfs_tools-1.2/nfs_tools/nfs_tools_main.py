#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang<hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# NFS共享服务
#------------------------------
import os, sys, json,re
import time
import public


class nfs_tools_main:
    _log_type = 'NFS'
    _config_path = 'plugin/nfs_tools/config'
    _share_config_file = _config_path + '/share.json'
    _mount_config_file = _config_path + '/mount.json'
    _mount_script_file = _config_path + '/mount_script.sh'
    _mounts = []
    access_defs = ['auto_mount']
    
    def __init__(self):
        if not os.path.exists(self._config_path):
            os.makedirs(self._config_path)
        if not os.path.exists(self._share_config_file):
            public.writeFile(self._share_config_file, '[]')
        if not os.path.exists(self._mount_config_file):
            public.writeFile(self._mount_config_file, '[]')


    def exists_args(self,args,get):
        '''
            @name 检查参数是否存在
            @author hwliang<2021-06-08>
            @param args<list or str> 参数列表 允许是列表或字符串
            @param get<dict_obj> 参数对像
            @return bool 都存在返回True，否则抛出KeyError异常
        '''
        if type(args) == str:
            args = args.split(',')
        for arg in args:
            if not arg in get:
                raise KeyError('缺少必要参数: {}'.format(arg))
        return True

    def get_server_status(self, get):
        '''
            @name 获取服务状态
            @author hwliang<2021-06-08>
            @return dict
        '''

        data = {}
        exec_cmd1 = "systemctl status nfs-server.service|grep 'active (exited)'"
        data['nfs-server'] = not not public.ExecShell(exec_cmd1)[0]
        exec_cmd2 = "systemctl status rpcbind.service|grep 'active (running)'"
        data['rpcbind'] = not not public.ExecShell(exec_cmd2)[0]
        data['service_list'] = []
        if data['rpcbind']:
            rpcinfo_result = public.ExecShell('rpcinfo -p|grep -v program')[0]
            for _line in rpcinfo_result.split('\n'):
                if not _line: continue
                tmp = _line.split()
                t_len = len(tmp)
                if t_len == 4: tmp.append('')
                if t_len != 5: continue
                rpcinfo_line = {}
                rpcinfo_line['program'], rpcinfo_line['vers'], rpcinfo_line['proto'], rpcinfo_line['port'], rpcinfo_line['service'] = tmp
                data['service_list'].append(rpcinfo_line)

        return data


    def server_admin(self,get):
        '''
            @name 服务管理
            @author hwliang<2021-06-16>
            @param get<dict_obj>{
                server_name: string<服务名称> nfs-server/rpcbind
                status_args: string<操作参数> reload/stop/start/restart
            }
        '''
        try:
            self.exists_args('server_name,status_args',get)
        except Exception as ex:
            return public.returnMsg(False,str(ex))

        if not get.server_name in ['nfs-server','rpcbind']:
            return public.returnMsg(False,'服务名称错误')
        if not get.status_args in ['reload','stop','start','restart']:
            return public.returnMsg(False,'错误的操作参数')

        status = {
            'reload': '重载',
            'start': '启动',
            'stop': '停止',
            'restart': '重启'
        }
        public.ExecShell("systemctl {} {}.service".format(get.status_args,get.server_name))
        msg = '{}服务{}成功'.format(get.server_name,status[get.status_args])
        public.WriteLog(self._log_type,msg)
        return public.returnMsg(True,msg)


    def get_share_list(self, get):
        '''
            @name 获取共享目录列表
            @author hwliang<2021-06-08>
            @return list
        '''
        result = self.__get_mod()
        if result['status'] == False: return result

        share_list = self.get_share_config()
        
        if get:
            ports = self.get_accept_ports()
            data = {
                'list':share_list,
                'ports':ports
            }
            return data
        else:
            return share_list


    def get_accept_ports(self):
        '''
            @name 获取要放行的端口
            @author hwliang<2021-07-21>
            @return string
        '''
        rpcinfo_result = public.ExecShell('rpcinfo -p|grep -v program')[0]
        ports = []
        for _line in rpcinfo_result.split('\n'):
            if not _line: continue
            tmp = _line.split()
            t_len = len(tmp)
            if t_len == 4: tmp.append('')
            if t_len != 5: continue
            rpcinfo_line = {}
            rpcinfo_line['program'], rpcinfo_line['vers'], rpcinfo_line['proto'], rpcinfo_line['port'], rpcinfo_line['service'] = tmp
            port = int(rpcinfo_line['port'])
            if port >= 32874: continue
            if rpcinfo_line['port'] in ports: continue
            ports.append(str(rpcinfo_line['port']))
        ports.append('32874-65535')
        return '/'.join(ports)


    def __get_mod(self):
        from BTPanel import session
        from panelAuth import panelAuth
        skey = 'bt_nfs_tools_res'
        if skey in session: return public.returnMsg(True,'OK!')
        params = {}
        params['pid'] = '100000057'
        result = panelAuth().send_cloud('check_plugin_status',params)
        try:
            if not result['status']: 
                if skey in session: del(session[skey])
                return result
        except: pass
        session[skey] = True
        return result


    def get_share_find(self,get = None, share_name = None):
        '''
            @name 获取指定共享目录信息
            @author hwliang<2021-06-08>
            @param get<dict_obj>{
                share_name: string<共享名称>
            } [可选] 与share_name互斥
            @param share_name 共享名称[可选]
            @return dict
        '''
        if get:
            try:
                self.exists_args('share_name',get)
            except Exception as ex:
                return public.returnMsg(False,str(ex))
            
            share_name = get.share_name.strip()
        share_list = self.get_share_list(None)
        for share_info in share_list:
            if share_info['share_name'] == share_name:
                return share_info
        if not get: return False
        return public.returnMsg(False,'指定共享目录不存在')

    
    def create_share(self,get):
        '''
            @name 创建共享配置
            @author hwliang<2021-06-08>
            @param get<dict_obj>{
                share_name: string<共享名称>,
                path: string<共享路径>,
                limit_address: JSON_LIST<允许访问的IP列表> 示例：192.168.1.2 或 192.168.1.0/24,
                rw_mode: string<读写模式> 二选一 rw: 读写 ro: 只读,
                sync_mode: string<同步模式> 二选一 sync: 实时同步 - 数据更安全 async: 非实时同步 - 性能更好
                user: string<指定访问用户> 可选： www,root,mysql,redis 建议使用www
                squash: string<权限限制> 三选一 no_root_squash: root用户不受限, root_squash: root用户受限, all_squash: 所有用户受限(推荐)
                ps: string<备注>

            }
            @return dict
        '''
        try:
            self.exists_args('share_name,path,limit_address,rw_mode,sync_mode,user,squash,ps',get)
        except Exception as ex:
            return public.returnMsg(False,str(ex))

        pdata = {
            'share_name':get.share_name.strip(),
            'path': get.path.strip(),
            'limit_address': get.limit_address.strip(),
            'rw_mode': get.rw_mode.strip(),
            'sync_mode': get.sync_mode.strip(),
            'user': get.user.strip(),
            'squash': get.squash.strip(),
            'ps': get.ps,
            'addtime': int(time.time())
        }


        if not os.path.exists(pdata['path']):
            return public.returnMsg(False,'指定目录不存在!')

        limit_list = ['ro','rw']
        if not pdata['rw_mode'] in limit_list:
            return public.returnMsg(False,'rw_mode支持的值: {}'.format(limit_list))
        
        limit_list = ['sync','async']
        if not pdata['sync_mode'] in limit_list:
            return public.returnMsg('sync_mode支持的值: {}'.format(limit_list))

        limit_list = ['no_root_squash','root_squash','all_squash']
        if not pdata['squash'] in limit_list:
            return public.returnMsg('squash支持的值：{}'.format(limit_list))

        limit_list = ['www','root','mysql','redis']
        if not pdata['user'] in limit_list:
            return public.returnMsg('user支持的值：{}'.format(limit_list))

        if self.get_share_find(share_name=pdata['share_name']):
            return public.returnMsg(False,'指定共享名称已存在')
        
        share_list = self.get_share_list(None)
        share_list.insert(0,pdata)
        self.save_share_config(share_list)
        public.WriteLog(self._log_type,'创建NFS目录共享: {}'.format(pdata['share_name']))
        return public.returnMsg(True,'创建成功!')


    
    def modify_share(self,get):
        '''
            @name 获取指定共享目录信息
            @author hwliang<2021-06-08>
            @param get<dict_obj>{
                share_name: string<共享名称>,
                path: string<共享路径>,
                limit_address: JSON_LIST<允许访问的IP列表> 示例：192.168.1.2 或 192.168.1.0/24,
                rw_mode: string<读写模式> 二选一 rw: 读写 ro: 只读,
                sync_mode: string<同步模式> 二选一 sync: 实时同步 - 数据更安全 async: 非实时同步 - 性能更好
                user: string<指定访问用户> 可选： www,root,mysql,redis 建议使用www
                squash: string<权限限制> 三选一 no_root_squash: root用户不受限, root_squash: root用户受限, all_squash: 所有用户受限(推荐)
                ps: string<备注>
            }
            @return dict
        '''
        try:
            self.exists_args('share_name,path,limit_address,rw_mode,sync_mode,user,squash,ps',get)
        except Exception as ex:
            return public.returnMsg(False,str(ex))

        pdata = {
            'share_name':get.share_name.strip(),
            'path': get.path.strip(),
            'limit_address': get.limit_address.strip(),
            'rw_mode': get.rw_mode.strip(),
            'sync_mode': get.sync_mode.strip(),
            'user': get.user.strip(),
            'squash': get.squash.strip(),
            'ps': get.ps,
            'addtime': int(time.time())
        }


        if not os.path.exists(pdata['path']):
            return public.returnMsg(False,'指定目录不存在!')

        limit_list = ['ro','rw']
        if not pdata['rw_mode'] in limit_list:
            return public.returnMsg(False,'rw_mode支持的值: {}'.format(limit_list))
        
        limit_list = ['sync','async']
        if not pdata['sync_mode'] in limit_list:
            return public.returnMsg('sync_mode支持的值: {}'.format(limit_list))

        limit_list = ['no_root_squash','root_squash','all_squash']
        if not pdata['squash'] in limit_list:
            return public.returnMsg('squash支持的值：{}'.format(limit_list))

        limit_list = ['www','root','mysql','redis']
        if not pdata['user'] in limit_list:
            return public.returnMsg('user支持的值：{}'.format(limit_list))
        
        share_list = self.get_share_list(None)
        for i in range(len(share_list)):
            if share_list[i]['share_name'] == pdata['share_name']:
                share_list[i] = pdata
                self.save_share_config(share_list)
                public.WriteLog(self._log_type,'修改NFS目录共享: {}'.format(pdata['share_name']))
                return public.returnMsg(True,'修改成功!')

        return public.returnMsg(False,'指定共享名称不存在')


    def remove_share(self,get):
        '''
            @name 删除指定共享目录
            @author hwliang<2021-06-08>
            @param get<dict_obj>{
                share_name: string<共享名称>
            }
            @return dict
        '''
        try:
            self.exists_args('share_name',get)
        except Exception as ex:
            return public.returnMsg(False,str(ex))

        
        share_list = self.get_share_list(None)
        for i in range(len(share_list)):
            if share_list[i]['share_name'] == get['share_name']:
                del(share_list[i])
                self.save_share_config(share_list)
                public.WriteLog(self._log_type,'删除NFS目录共享: {}'.format(get['share_name']))
                return public.returnMsg(True,'删除成功!')
        
        return public.returnMsg(False,'指定共享名称不存在')


    def get_share_config(self):
        '''
            @name 获取共享目录配置
            @author hwliang<2021-06-08>
            @return list
        '''

        if not os.path.exists(self._share_config_file): return []
        try:
            config_data = json.loads(public.readFile(self._share_config_file))
            return config_data
        except:
            public.writeFile(self._share_config_file, '[]')
            return []

    def save_share_config(self,share_list):
        '''
            @name 保存共享目录配置
            @author hwliang<2021-06-08>
            @return list
        '''
        result = public.writeFile(self._share_config_file,json.dumps(share_list))
        self.write_export_conf()
        return result


    def get_user_id(self,user):
        '''
            @name 通过用户名获取uid/gid
            @author hwliang<2021-06-09>
            @return tuble uid,gid
        '''
        from pwd import getpwnam
        user_info = getpwnam(user)
        return user_info.pw_uid,user_info.pw_gid


    def write_export_conf(self):
        '''
            @name 将共享配置写入到配置文件
            @author hwliang<2021-06-09>
            @return void
        '''

        share_list = self.get_share_config()

        export_list = []
        for share in share_list:
            share['uid'],share['gid'] = self.get_user_id(share['user'])
            share_line = "{path} {ip}({rw_mode},{sync_mode},{squash},no_subtree_check,anonuid={uid},anongid={gid})".format(
                path=share['path'],
                ip=share['limit_address'],
                rw_mode=share['rw_mode'],
                sync_mode=share['sync_mode'],
                squash=share['squash'],
                uid=share['uid'],
                gid=share['gid']
            )

            export_list.append(share_line)

        export_body = "\n".join(export_list)
        export_file = '/etc/exports'
        public.writeFile(export_file,export_body)
        public.ExecShell('/usr/sbin/exportfs -avr')
        



    def get_mount_list(self,get):
        '''
            @name 获取挂载列表
            @author hwliang<2021-06-09>
            @return list
        '''

        mount_list = self.get_mount_config()
        
        iostat_list = self.get_nfsiostat()
        
        for i in range(len(mount_list)):
            mount_list[i]['mount_info'] = self.get_mount(mount_list[i]['mount_path'])
            if not mount_list[i]['mount_info']: mount_list[i]['mount_info'] = False
            mount_list[i]['iostat'] = False
            if mount_list[i]['mount_path'] in iostat_list:
                mount_list[i]['iostat'] = iostat_list[mount_list[i]['mount_path']]
        return mount_list


    def is_exists_mount_path(self,mount_name,mount_path):
        '''
            @name 检查指定挂载路径是否存在
            @author hwliang<2021-06-09>
            @param mount_name string<挂载名称>
            @param mount_path string<挂载路径>
            @return bool
        '''

        mount_list = self.get_mount_config()
        for mount in mount_list:
            if mount_name != mount['mount_name'] and mount_path == mount['mount_path']:
                return True
        return False


    def get_mount_find(self,get = None,mount_name = None):
        '''
            @name 获取指定挂载信息
            @author hwliang<2021-06-09>
            @param get<dict_obj>{
                mount_name: string<挂载名称>
            } [可选] 与mount_name互斥
            @param mount_name 挂载名称[可选]
            @return dict
        '''
        if get:
            try:
                self.exists_args('mount_name',get)
            except Exception as ex:
                return public.returnMsg(False,str(ex))
            
            mount_name = get.mount_name.strip()
        mount_list = self.get_mount_config()
        for mount_info in mount_list:
            if mount_info['mount_name'] == mount_name:
                return mount_info
        if not get: return False
        return public.returnMsg(False,'指定挂载信息不存在')


    def exec_shell(self,cmdstring, timeout=None, shell=True):
        '''
            @name 执行指定SHELL命令
            @author hwliang<2021-06-09>
            @param cmdstring<string> SHELL命令文本
            @param timeout<int> 返回超时时间（秒） 默认： None
            @param shell<bool> 是否为SHELL模式执行 默认：True
            @return tuple 通道1(正常输出信息),通道2(错误信息)
        '''
        a = ''
        e = ''
        import subprocess,tempfile
        
        try:
            rx = public.md5(cmdstring)
            succ_f = tempfile.SpooledTemporaryFile(max_size=4096,mode='wb+',suffix='_succ',prefix='btex_' + rx ,dir='/dev/shm')
            err_f = tempfile.SpooledTemporaryFile(max_size=4096,mode='wb+',suffix='_err',prefix='btex_' + rx ,dir='/dev/shm')
            sub = subprocess.Popen(cmdstring, close_fds=True, shell=shell,bufsize=128,stdout=succ_f,stderr=err_f)
            if timeout:
                s = 0
                d = 0.01
                while sub.poll() is None:
                    time.sleep(d)
                    s += d
                    if s >= timeout:
                        if not err_f.closed: err_f.close()
                        if not succ_f.closed: succ_f.close()
                        return '','Timed out'
            else:
                sub.wait()

            err_f.seek(0)
            succ_f.seek(0)
            a = succ_f.read()
            e = err_f.read()
            if not err_f.closed: err_f.close()
            if not succ_f.closed: succ_f.close()
        except:
            return '',public.get_error_info()
        try:
            #编码修正
            if type(a) == bytes: a = a.decode('utf-8')
            if type(e) == bytes: e = e.decode('utf-8')
        except:pass

        return a,e

    def show_ip_share_list(self,get = None,server_address = None):
        '''
            @name 获取指定服务器IP的共享目录列表
            @author hwliang<2021-06-10>
            @param get<dict_obj>{
                server_address: string<服务器IP>
            } [可选] 与server_address互斥
            @param server_address 服务器IP[可选]
            @return list
        '''
        try:
            self.exists_args('server_address',get)
        except Exception as ex:
            return public.returnMsg(False,str(ex))
        if get:
            server_address = get.server_address.strip()
        res = self.exec_shell("showmount -e {} --no-headers".format(server_address),timeout=10)
        res = '\n'.join(res)
        if res.find('Unable to receive') != -1 or res.find('Timed out') != -1:
            return public.returnMsg(False,'无法连接指定服务器的RPC服务,请检查该服务器的2049/111/32874-65535端口是否放行')
        if res.find('command not found') != -1:
            return public.returnMsg(False,'没有找到showmount命令，请检查nfs-server服务是否成功安装')
        result = []
        for s in res.split('\n'):
            try:
                s = s.strip()
                if not s: continue
                share_path = {}
                share_path['path'],share_path['limit_address'] = s.split()
                result.append(share_path)
            except: continue
        if not result: return public.returnMsg(False,'没有在指定服务器找到可用的NFS共享目录')
        return result

    def create_mount(self,get):
        '''
            @name 创建挂载配置
            @author hwliang<2021-06-08>
            @param get<dict_obj>{
                mount_name: string<挂载名称>,
                server_address: string<NFS服务器IP>,
                nfs_path: string<共享路径>,
                mount_path: string<挂载路径>,
                rsize: int<读取块大小>, 建议：1048576
                wsize: int<写入块大小>, 建议：1048576
                hard: int<自动等待恢复> , 0.不开启 1.开启 ， 建议开启
                retrans: int<请求重试次数>,
                noresvport: string<短时断网自动重连> 0.不开启  1.开启, 建议开启
                vers: int<NFS版本> 二选一： 3.NFS-3/4.NFS-4
                proto: string<协议> 二选一： tcp/udp
                timeo: int<重试时间> 单位秒/1-60之间
                auto_mount: int<是否开机自动挂载> 0.否 1.是
                ps: string<备注>
            }
            @return dict
        '''
        try:
            self.exists_args('mount_name,auto_mount,vers,proto,timeo,server_address,nfs_path,mount_path,rsize,wsize,hard,retrans,noresvport,ps',get)
        except Exception as ex:
            return public.returnMsg(False,str(ex))

        pdata = {
            'mount_name':get.mount_name.strip(),
            'server_address': get.server_address.strip(),
            'nfs_path': get.nfs_path,
            'mount_path': get.mount_path.strip(),
            'rsize': int(get.rsize),
            'wsize': int(get.wsize),
            'hard': int(get.hard),
            'retrans': int(get.retrans),
            'noresvport': int(get.noresvport),
            'vers': int(get.vers),
            'proto': get.proto.strip(),
            'timeo': int(get.timeo) * 10,
            'auto_mount': int(get.auto_mount),
            'ps': get.ps,
            'addtime': int(time.time())
        }


        if not os.path.exists(pdata['mount_path']):
            os.makedirs(pdata['mount_path'])
        if pdata['rsize'] < 1024 > pdata['wsize']:
            return public.returnMsg(False,'rsize/wsize不能小于1024')
        limit_list = [0,1]
        if not pdata['hard'] in limit_list:
            return public.returnMsg(False,'head支持的值: {}'.format(limit_list))
        if not pdata['noresvport'] in limit_list:
            return public.returnMsg(False,'noresvport支持的值: {}'.format(limit_list))
        if not pdata['auto_mount'] in limit_list:
            return public.returnMsg(False,'auto_mount支持的值: {}'.format(limit_list))
        if pdata['retrans'] < 1:
            return public.returnMsg('retrans参数值不能小于1')
        if not pdata['vers'] in [3,4]:
            return public.returnMsg(False,'vers只能传入3或4')
        if not pdata['proto'] in ['tcp','udp']:
            return public.returnMsg(False,'proto参数只能传入tcp或udp')
        if pdata['timeo'] < 10:
            return public.returnMsg(False,'timeo参数值不能小于1')
        
        if self.get_mount_find(mount_name=pdata['mount_name']):
            return public.returnMsg(False,'指定挂载名称已存在!')

        if self.is_exists_mount_path(pdata['mount_name'],pdata['mount_path']):
            return public.returnMsg(False,'指定挂载路径已经被占用了')
        
        mount_list = self.get_mount_config()
        mount_list.insert(0,pdata)
        self.save_mount_config(mount_list)
        public.WriteLog(self._log_type,'创建NFS挂载配置: {}'.format(pdata['mount_name']))
        return public.returnMsg(True,'创建成功!')


    def modify_mount(self,get):
        '''
            @name 修改挂载配置
            @author hwliang<2021-06-08>
            @param get<dict_obj>{
                mount_name: string<挂载名称>,
                server_address: string<NFS服务器IP>,
                nfs_path: string<共享路径>,
                mount_path: string<挂载路径>,
                rsize: int<读取块大小>, 建议：1048576
                wsize: int<写入块大小>, 建议：1048576
                hard: int<自动等待恢复> , 0.不开启 1.开启 ， 建议开启
                retrans: int<请求重试次数>,
                noresvport: string<短时断网自动重连> 0.不开启  1.开启, 建议开启
                vers: int<NFS版本> 二选一： 3.NFS-3/4.NFS-4
                proto: string<协议> 二选一： tcp/udp
                timeo: int<重试时间> 单位秒/1-60之间
                auto_mount: int<是否开机自动挂载> 0.否 1.是
                ps: string<备注>
            }
            @return dict
        '''
        try:
            self.exists_args('mount_name,auto_mount,vers,proto,timeo,server_address,nfs_path,mount_path,rsize,wsize,hard,retrans,noresvport,ps',get)
        except Exception as ex:
            return public.returnMsg(False,str(ex))

        pdata = {
            'mount_name':get.mount_name.strip(),
            'server_address': get.server_address.strip(),
            'nfs_path': get.nfs_path,
            'mount_path': get.mount_path.strip(),
            'rsize': int(get.rsize),
            'wsize': int(get.wsize),
            'hard': int(get.hard),
            'retrans': int(get.retrans),
            'noresvport': int(get.noresvport),
            'vers': int(get.vers),
            'proto': get.proto.strip(),
            'timeo': int(get.timeo) * 10,
            'auto_mount': int(get.auto_mount),
            'ps': get.ps,
            'addtime': int(time.time())
        }


        if not os.path.exists(pdata['mount_path']):
            os.makedirs(pdata['mount_path'])
        if pdata['rsize'] < 1024 > pdata['wsize']:
            return public.returnMsg(False,'rsize/wsize不能小于1024')
        limit_list = [0,1]
        if not pdata['hard'] in limit_list:
            return public.returnMsg(False,'head支持的值: {}'.format(limit_list))
        if not pdata['noresvport'] in limit_list:
            return public.returnMsg(False,'noresvport支持的值: {}'.format(limit_list))
        if not pdata['auto_mount'] in limit_list:
            return public.returnMsg(False,'auto_mount支持的值: {}'.format(limit_list))
        if pdata['retrans'] < 1:
            return public.returnMsg('retrans参数值不能小于1')
        if not pdata['vers'] in [3,4]:
            return public.returnMsg(False,'vers只能传入3或4')
        if not pdata['proto'] in ['tcp','udp']:
            return public.returnMsg(False,'proto参数只能传入tcp或udp')
        if pdata['timeo'] < 10:
            return public.returnMsg(False,'timeo参数值不能小于1')


        if self.is_exists_mount_path(pdata['mount_name'],pdata['mount_path']):
            return public.returnMsg(False,'指定挂载路径已经被占用了')

        mount_list = self.get_mount_config()
        for i in range(len(mount_list)):
            if mount_list[i]['mount_name'] == pdata['mount_name']:
                mount_list[i] = pdata
                self.save_mount_config(mount_list)
                public.WriteLog(self._log_type,'修改NFS挂载配置: {}'.format(pdata['mount_name']))
                return public.returnMsg(True,'修改成功!')

        return public.returnMsg(False,'指定挂载名称不存在')


    def remove_mount(self,get):
        '''
            @name 删除指定挂载配置
            @author hwliang<2021-06-08>
            @param get<dict_obj>{
                mount_name: string<挂载名称>
            }
            @return dict
        '''
        try:
            self.exists_args('mount_name',get)
        except Exception as ex:
            return public.returnMsg(False,str(ex))

        mount_list = self.get_mount_config()
        for i in range(len(mount_list)):
            if mount_list[i]['mount_name'] == get['mount_name']:
                self.set_umount(mount_list[i])
                del(mount_list[i])
                self.save_mount_config(mount_list)
                public.WriteLog(self._log_type,'删除NFS挂载配置: {}'.format(get['mount_name']))
                return public.returnMsg(True,'删除成功!')
        
        return public.returnMsg(False,'指定挂载名称不存在')
        


    def get_mount_config(self):
        '''
            @name 获取挂载配置
            @author hwliang<2021-06-09>
            @return list
        '''

        if not os.path.exists(self._mount_config_file): return []
        try:
            config_data = json.loads(public.readFile(self._mount_config_file))
            return config_data
        except:
            public.writeFile(self._mount_config_file, '[]')
            return []

    def save_mount_config(self,mount_list):
        '''
            @name 保存挂载配置
            @author hwliang<2021-06-08>
            @return list
        '''
        res =  public.writeFile(self._mount_config_file,json.dumps(mount_list))
        self.write_mount_conf()
        return res


    def get_mount_cmd(self,mount):
        '''
            @name 取挂载命令
            @author hwliang<2021-06-10>
            @return void
        '''

        hard = ''
        if mount['hard'] == 1: hard = 'hard,'
        mount_line = "mount -t nfs -o vers={vers},nolock,noacl,proto={proto},rsize={rsize},wsize={wsize},{hard}timeo={timeo},retrans={retrans} {server_address}:{nfs_path} {mount_path}".format(
            vers = mount['vers'],
            proto = mount['proto'],
            rsize = mount['rsize'], 
            wsize = mount['wsize'],
            hard = hard,
            timeo = mount['timeo'],
            retrans = mount['retrans'],
            server_address = mount['server_address'],
            nfs_path = mount['nfs_path'],
            mount_path = mount['mount_path']
        )

        return mount_line


    def get_disk_mounts(self,get = None):
        '''
            @name 获取当前磁盘挂载列表
            @author hwliang<2021-06-09>
            @return list
        '''

        df_result = self.exec_shell("df -B 1 -PT",timeout=3)[0]
        result = []
        if df_result:
            
            df_keys = ['filesystem','type','size','used_size','available_size','used_pre','mount_path']
            for df_line in df_result.split("\n"):
                if df_line.find('/') == -1: continue
                df_info = df_line.split()
                if len(df_info) != 7: continue
                ok_info = {}
                for i in range(len(df_keys)):
                    ok_info[df_keys[i]] = df_info[i]
                result.append(ok_info)
        else:
            df_result = self.exec_shell("mount -l|grep 'type nfs'",timeout=3)[0]
            if not df_result:
                return result
            
            for df_line in df_result.split("\n"):
                ikey = ' on '
                if df_line.find(ikey) == -1: continue
                df_info = df_line.split(ikey)
                ok_info = {
                    'filesystem': df_info[0],
                    'type': 'nfs',
                    'size': 0,
                    'used_size':0,
                    'available_size':0,
                    'used_pre': '0%',
                    'mount_path': df_info[1].split(' type nfs ')[0]
                }
                result.append(ok_info)
        return result


    def get_mount(self,mount_path,force=False):
        '''
            @name 取已挂载的指定目录
            @author hwliang<2021-06-10>
            @param mount_path<string> 挂载目录
            @param force<bool> 是否强制重新检测
            @return bool
        '''
        if not self._mounts or force:
            self._mounts = self.get_disk_mounts()
        
        for _mount in self._mounts:
            if _mount['mount_path'] == mount_path:
                return _mount
        return None

    def to_umount(self,get):
        '''
            @name 卸载NFS挂载
            @author hwliang<2021-06-09>
            @param get<dcit_obj>{
                mount_name: string<挂载名称>
            }
            @return dict
        '''
        try:
            self.exists_args('mount_name',get)
        except Exception as ex:
            return public.returnMsg(False,str(ex))

        _mount = self.get_mount_find(mount_name=get.mount_name)
        if not _mount: public.returnMsg('指定挂载名称不存在')
        return self.set_umount(_mount)

    def to_mount(self,get):
        '''
            @name 挂载指定NFS挂载配置
            @author hwliang<2021-06-09>
            @param get<dcit_obj>{
                mount_name: string<挂载名称>
            }
            @return dict
        '''
        try:
            self.exists_args('mount_name',get)
        except Exception as ex:
            return public.returnMsg(False,str(ex))

        _mount = self.get_mount_find(mount_name=get.mount_name)
        if not _mount: public.returnMsg(False,'指定挂载名称不存在')
        return self.set_mount(_mount)

    def set_umount(self,mount = {}):
        '''
            @name 卸载NFS挂载
            @author hwliang<2021-06-09>
            @return void
        '''
        _mount = self.get_mount(mount['mount_path'])
        if not _mount: return public.returnMsg(False,'指定配置当前未挂载')
        public.ExecShell("umount {}".format(mount['mount_path']))
        if self.get_mount(mount['mount_path'],True):
            return public.returnMsg(False,'卸载失败,当前有进程正在使用此挂载分区!')

        public.WriteLog(self._log_type,'卸载远程NFS目录: {} -> {}'.format(mount['mount_name'],mount['mount_path']))
        return public.returnMsg(True,'卸载成功!')

    def set_mount(self,mount = {}):
        '''
            @name 挂载指定NFS挂载配置
            @author hwliang<2021-06-09>
            @return void
        '''
        _mount = self.get_mount(mount['mount_path'])
        if _mount: return public.returnMsg(False,'指定挂载点当前已经被挂载')
        mount_cmd = self.get_mount_cmd(mount)
        result = public.ExecShell(mount_cmd)
        if not self.get_mount(mount['mount_path'],True):
            return public.returnMsg(False,'挂载失败: {}\n{}'.format(result[1],result[0]))

        public.WriteLog(self._log_type,'挂载远程NFS目录: {} -> {}'.format(mount['mount_name'],mount['mount_path']))
        return public.returnMsg(True,'挂载成功')


    def write_mount_conf(self):
        '''
            @name 将挂载配置写入到配置文件
            @author hwliang<2021-06-09>
            @return void
        '''

        mount_list = self.get_mount_config()
        _list = []
        for mount in mount_list:
            mount_line = self.get_mount_cmd(mount)
            _list.append(mount_line)
        mount_body = "\n".join(_list)
        public.writeFile(self._mount_script_file,mount_body)


    def auto_mount(self):
        '''
            @name 开机自动挂载
            @author hwliang<2021-06-10>
            @return void
        '''
        mount_list = self.get_mount_config()
        for mount in mount_list:
            if mount['auto_mount'] == 0: continue
            self.set_mount(mount)


    def get_nfsstat(self,get = None):
        '''
            @name 获取nfsstat
            @author hwliang<2021-06-11>
            @return dict {
                "nfs_v3_server": {              # NFS-3服务器状态
                    "total": 4264,              # 总op
                    "other": 36,                # 其它
                    "getattr": 895,             # 获取文件属性次数
                    "lookup": 717,              # 打开文件
                    "access": 683,              # 查询权限次数 
                    "readlink": 1,              # 读取连接次数
                    "read": 571,                # 读次数
                    "create": 3,                # 创建文件次数
                    "mkdir": 702,               # 创建文件夹次数
                    "rmdir": 5,                 # 删除文件夹次数
                    "readdirplus": 135,         # 读取目录次数
                    "fsstat": 501,              # 取文件stat次数
                    "fsinfo": 10,               # 取文件系统信息次数
                    "pathconf": 5               # 取目录配置次数
                },
                "nfs_v4_server": {
                    "total": 147,               # 总次数
                    "other": 5,                 # 其它
                    "compound": 142             # 综合
                },
                "nfs_v4_servop": {
                    "total": 429,
                    "access": 7,
                    "getattr": 127,
                    "getfh": 10,                # 获取次数
                    "lookup": 8,                
                    "putfh": 126,               # 获取文件句柄次数
                    "putrootfh": 4,             # 获取根句柄次数
                    "readdir": 1,               
                    "exchange_id": 4,           # 交换ID次数
                    "create_ses": 2,            # 创建
                    "destroy_ses": 2,           # 销毁
                    "secinfononam": 2,          
                    "sequence": 132,            # 排序次数
                    "destroy_clid": 2,          # 销毁clid
                    "reclaim_comp": 2           # 回收
                },
                "nfs_v3_client": {
                    "total": 4232,
                    "other": 4,
                    "getattr": 895,
                    "lookup": 717,
                    "access": 683,
                    "readlink": 1,
                    "read": 571,
                    "create": 3,
                    "mkdir": 702,
                    "rmdir": 5,
                    "readdirplus": 135,
                    "fsstat": 501,
                    "fsinfo": 10,
                    "pathconf": 5
                },
                "nfs_v4_client": {
                    "total": 153,
                    "other": 5,
                    "fsinfo": 6,
                    "access": 7,
                    "getattr": 15,
                    "lookup": 8,            # 查看
                    "lookup_root": 2,       # 查看根
                    "pathconf": 4,
                    "statfs": 75,
                    "readdir": 1,
                    "server_caps": 10,      
                    "exchange_id": 10,      # 交换ID
                    "create_session": 2,    # 创建会话
                    "destroy_session": 2,   # 销毁会话
                    "reclaim_comp": 2,      # 收回
                    "secinfo_no": 2,        # 
                    "destroy_clientid": 2   # 销毁客户端ID
                }
            }
        '''
        result = public.ExecShell('nfsstat -l')[0]
        r_list = re.findall("(nfs\s+v\d\s+\w+)\s+(\w+):\s+(\d+)",result)
        data = {}
        for rs in r_list:
            k = rs[0].replace(' ','_')
            if not k in data.keys():
                data[k] = {}
            k2 = rs[1] if rs[1] != 'null' else 'other'
            data[k][k2] = int(rs[2])
        return data

    def get_nfsiostat(self,get = None):
        '''
            @name 获取nfsiostat
            @author hwliang<2021-06-11>
            @return dict {
                'ops': float,             # 总IOPS/s
                'rpc_bklog': float,       # 队列长度
                'read_ops': float,        # 读IOPS/秒
                'read_kbs': float,        # 读速度/秒
                'read_kbop': float,       # 读速度/次
                'read_retrans': float,    # 读重传次数
                'read_avg_rtt_ms': float, # 读取时间 毫秒
                'read_avg_exe_ms': float, # 读取总耗时 毫秒
                'write_ops': float,       # 写IOPS
                'write_kbs': float,       # 写速度/秒 单位kB
                'write_kbop': float,     # 写速度/次 单位 kB
                'write_retrans': float,  # 写重试次数
                'write_avg_rtt_ms': float,  # 写入时间 毫秒
                'write_avg_exe_ms': float   # 写入总耗时 毫秒
            }
        '''

        result = public.ExecShell('nfsiostat -adp')[0]
        r_list = result.split(" mounted on ")
        data = {}
        for _s in r_list:
            if len(_s) < 100: continue
            mount_path = _s.split(':')[0]
            m = re.findall("(\s[\d\.]+\s)",_s)
            data[mount_path] = {
                'ops': float(m[0].strip()),             # 总IOPS/s
                'rpc_bklog': float(m[1].strip()),       # 队列长度
                'read_ops': float(m[2].strip()),        # 读IOPS/秒
                'read_kbs': float(m[3].strip()),        # 读速度/秒
                'read_kbop': float(m[4].strip()),       # 读速度/次
                'read_retrans': float(m[5].strip()),    # 读重传次数
                'read_avg_rtt_ms': float(m[6].strip()), # 读取时间 毫秒
                'read_avg_exe_ms': float(m[7].strip()), # 读取总耗时 毫秒
                'write_ops': float(m[8].strip()),       # 写IOPS
                'write_kbs': float(m[9].strip()),       # 写速度/秒 单位kB
                'write_kbop': float(m[10].strip()),     # 写速度/次 单位 kB
                'write_retrans': float(m[11].strip()),  # 写重试次数
                'write_avg_rtt_ms': float(m[12].strip()),  # 写入时间 毫秒
                'write_avg_exe_ms': float(m[13].strip())   # 写入总耗时 毫秒
            }
        return data


if __name__ == '__main__':
    p = nfs_tools_main()
    p.auto_mount()