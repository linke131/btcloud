# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------
import sys
import os
import json
import time
import re

os.chdir('/www/server/panel')
sys.path.insert(0, 'class/')
sys.path.insert(0, 'data/')
sys.path.insert(0, 'plugin/oos')
import public
import oos_server
import threading

try:
    if __name__ != '__main__':
        from BTPanel import my_terms
    else:
        my_terms = {}
except:
    my_terms = {}


class oos_main:
    plugin_path = 'plugin/oos/'
    server_path = plugin_path + 'server/'
    trigger_path = plugin_path + 'triggers/'
    script_path = plugin_path + 'scripts/'
    arrange_path = plugin_path + 'arranges/'
    script_arr = {}
    arrange_last_time = None
    arrange_list = None
    is_read_file = '/dev/shm/arrange_read.pl'
    log_name = '运维中心'

    def __init__(self):
        pass

    def service_status(self, args=None):
        pid_file = 'logs/oos.pid'
        init_file = '/etc/init.d/BT-OOS'
        if not os.path.exists(pid_file):
            if os.path.exists(init_file):
                public.ExecShell(init_file + '　start')
            else:
                public.ExecShell("chmod 700 /www/server/panel/plugin/oos/BT-OOS")
                public.ExecShell("/www/server/panel/plugin/oos/BT-OOS > /dev/null")
            return os.path.exists(pid_file)
        else:
            return True

    # 获取分页数据
    # args 前端参数
    # s_key 被搜索的字段
    def get_page_data(self, args, s_key=['title', 'ps'], order='addtime', reverse=True):
        # 是否搜索
        s_search = None
        if 'search' in args:
            s_search = args.search.strip()

        # 指定目录是否存在
        _list = []
        if os.path.exists(args.path):
            f_names = os.listdir(args.path)
        else:
            f_names = []

        # 遍历配置文件
        for name in f_names:
            s_file = args.path + name + '/info.json'
            if not os.path.exists(s_file): continue
            j_tmp = public.readFile(s_file)
            if not j_tmp: continue
            s_info = json.loads(j_tmp)
            # 搜索
            if s_search:
                is_return = False
                for key in s_key:
                    if name.find(key) != -1:
                        is_return = True
            else:
                is_return = True

            # s_info['addtime'] = os.stat(s_file).st_ctime
            if is_return: _list.append(s_info)
        _list = sorted(_list, key=lambda x: x[order], reverse=reverse)
        # 获取分页数据
        if 'p' not in args:
            args.p = 1
        else:
            args.p = int(args.p)
        if 'callback' not in args:
            args.callback = ''
        rows = 20
        if 'rows' in args:
            rows = int(args.rows)

        s_len = len(_list)
        data = public.get_page(s_len, args.p, rows=rows, callback=args.callback)
        # shift = int(data['shift']) - 1
        # row = shift + int(data['row'])
        # data['list'] = []
        #
        # for i in range(s_len):
        #     if i > row: break
        #     if i <= shift: continue
        #     data['list'].append(_list[i])
        return self.data_arrays(_list, data, s_len)

    # 检查参数
    def _check_args(self, args, s_key=[]):
        for key in s_key:
            if not key in args:
                return public.returnMsg(False, '缺少参数: {}'.format(key))
            args[key] = args[key].strip()
        return args

    # 获取服务器列表
    def get_server_list(self, args):
        args.path = self.server_path
        return self.get_page_data(args)

    # 获取简易服务器列表
    def get_servers(self, args):
        server_list = []
        for name in os.listdir(self.server_path):
            info_file = self.server_path + name + '/info.json'
            if not os.path.exists(info_file): continue
            info = json.loads(public.readFile(info_file))
            server_list.append({"title": info['title'], "address": info['address'], 'addtime': info['addtime']})
        server_list = sorted(server_list, key=lambda x: x['address'])
        return server_list

    # 获取指定服务器信息
    def get_server_find(self, args):
        if not 'address' in args:
            return public.returnMsg(False, '请指定address')
        f_path = self.server_path + args.address
        if not os.path.exists(f_path):
            return False
        f_path += '/info.json'
        info = public.readFile(f_path)
        if not info: return False
        return json.loads(info)

    # 添加服务器
    def add_server(self, args):
        args = self._check_args(args, ['address', 'title', 'type', 'connect_info'])
        if type(args) == dict: return args
        f_path = self.server_path + args.address
        info = {"address": args.address, "title": args.title, "type": args.type,
                "connect_info": json.loads(args.connect_info), "addtime": int(time.time())}

        result = self.check_connect(info)
        if result: return result

        if not os.path.exists(f_path):
            os.makedirs(f_path, 384)
        u_file = f_path + '/users.json'
        if os.path.exists(u_file):
            os.remove(u_file)
        f_path += '/info.json'

        public.writeFile(f_path, json.dumps(info))
        public.WriteLog('运维中心', '添加服务器: {}:{}'.format(info['title'], info['address']))
        return public.returnMsg(True, '添加成功!')


    # 批量添加服务器
    def add_server_all(self,args):
        servers = args.servers.split('\n')
        results = []
        for s in servers:
            s_info = s.strip().split('|')
            if len(s_info) < 4:
                continue
            f_path = self.server_path + s_info[0]
            connect_info = {"host":s_info[0], "port": s_info[1], "username": s_info[2], "password": s_info[3], "pkey": ""}
            info = {"address":s_info[0],"title":s_info[0],"type":'ssh',"connect_info":connect_info,"addtime":int(time.time())}
            result = self.check_connect(info)
            if result: 
                results.append({"address":s_info[0],"status":0,"msg":result['msg']})
                return result
            results.append({"address":s_info[0],"status":1,"msg":"添加成功"})

            if not os.path.exists(f_path):
                os.makedirs(f_path,384)
            u_file = f_path + '/users.json'
            if os.path.exists(u_file):
                os.remove(u_file)
            f_path += '/info.json'
            public.writeFile(f_path,json.dumps(info))
            public.WriteLog('运维中心','添加服务器: {}:{}'.format(info['title'],info['address']))
        return results

    # 检查连接
    def check_connect(self, info):
        try:
            sp = oos_server.server_admin(None)
            sp._address = info['connect_info']['host']
            sp._s_info = info
            sp.connect_ssh()
            return False
        except Exception as ex:
            ex = str(ex)
            msg = ex
            if ex.find('Authentication failed') != -1:
                msg = '用户名或密码错误!'
            elif ex.find('Unable to connect to port') != -1:
                msg = '服务器连接失败,请检查服务器IP与SSH端口是否正确!'
            elif ex.find('Error reading SSH protocol banner') != -1:
                msg = '连接SSH协议时发生错误，请检查端口是否正确!'
            elif ex.find('not a valid RSA private key file') != -1:
                msg = '不是有效的RSA私钥,请检查私钥是否粘贴正确!'
            elif ex.find('Name or service not known') != -1:
                msg = '无法解析的IP/域名，请检查IP址是否正确!'
            return public.returnMsg(False, msg)

    def connect_server(self, address):
        skey = 'oos_server_' + address
        if not skey in my_terms:
            my_terms[skey] = oos_server.server_admin(address)

        if my_terms[skey]._term:
            if my_terms[skey]._term._transport.is_active():
                my_terms[skey].last_time = time.time()
                return skey
            else:
                del (my_terms[skey])
                return self.connect_server(address)
        return skey

    # 编辑服务器
    def modify_server(self, args):
        s_info = self.get_server_find(args)
        if 'title' in args:
            s_info['title'] = args.title.strip()
        if 'type' in args:
            s_info['type'] = args.type.strip()
        if 'connect_info' in args:
            s_info['connect_info'] = json.loads(args.connect_info)

        result = self.check_connect(s_info)
        if result: return result

        f_path = self.server_path + args.address + '/info.json'
        public.writeFile(f_path, json.dumps(s_info))
        public.WriteLog('运维中心', '编辑服务器: {}:{}'.format(s_info['title'], s_info['address']))
        return public.returnMsg(True, '编辑成功!')

    # 删除服务器
    def remove_server(self, args):
        if not 'address' in args:
            return public.returnMsg(False, '请指定address')
        f_path = self.server_path + args.address
        if not os.path.exists(f_path):
            return public.returnMsg(False, '指定服务器不存在')

        public.ExecShell("rm -rf {}".format(f_path))
        public.WriteLog('运维中心', '删除服务器: {}'.format(args.address))
        return public.returnMsg(True, '删除成功!')

    # 执行脚本
    def exec_shell(self, args):
        sp = oos_server.server_admin(args.address)
        result = sp.exec_shell(args.shell_str)
        return result

    # 获取文件列表
    def get_files(self, args):
        skey = self.connect_server(args.address)
        result = my_terms[skey].get_files(args.path)
        return result

    # 上传文件
    def upload_file(self, args):
        skey = self.connect_server(args.address)
        my_terms[skey].upload_file(args.sfile, args.dfile)
        return public.returnMsg(True, '上传成功!')

    # 删除文件
    def remove_file(self, args):
        skey = self.connect_server(args.address)
        my_terms[skey].remove_file(args.path)
        return public.returnMsg(True, '删除成功!')

    # 文件重命名
    def rename_file(self, args):
        skey = self.connect_server(args.address)
        my_terms[skey].rename(args.sfile, args.dfile)
        return public.returnMsg(True, '重命名成功!')

    # 压缩文件
    def zip_file(self, args):
        pass

    # 解压文件
    def unzip_file(self, args):
        pass

    # 打开终端
    def term(self, args):
        pass

    # 获取监控事件列表
    def get_control_event(self, args):
        pass

    # 获取监控脚本列表
    def get_control_scripts(self, args):
        pass

    # 增加监控脚本
    def add_control_script(self, args):
        pass

    # 删除监控脚本
    def remove_control_script(self, args):
        pass

    # 编辑监控脚本
    def modify_control(self, args):
        pass

    # 添加监控事件
    def add_control_event(self, args):
        pass

    # 编辑监控事件
    def modify_control_event(self, args):
        pass

    # 删除监控事件
    def remove_control_event(self, args):
        pass

    # 获取触发器列表
    def get_trigger_list(self, args):
        args.path = self.trigger_path
        return self.get_page_data(args, order='sort')

    # 获取指定触发器
    def get_trigger_find(self, args):
        name = args.sname.strip()
        info_file = self.trigger_path + name + '/info.json'
        script_file = self.trigger_path + name + '/script'
        if not os.path.exists(info_file) or not os.path.exists(script_file):
            return public.returnMsg(False, '指定触发器不存在!')
        info = json.loads(public.readFile(info_file))
        info['script'] = public.readFile(script_file)
        return info

    # 删除指定触发器
    def remove_trigger(self, args):
        name = args.sname.strip()
        _path = self.trigger_path + name
        if os.path.exists(_path):
            public.ExecShell("rm -rf {}".format(_path))
        public.WriteLog(self.log_name, '删除触发器: {}'.format(name))
        return public.returnMsg(True, '删除成功!')

    # 因为要多次调用，所以从添加脚本库里面分离出来了
    def write_script_file(self, _path: str, info: dict, script: str) -> None:
        # _path = self.script_path + info['name']
        if not os.path.exists(_path):
            os.makedirs(_path, 384)
        public.writeFile(_path + '/info.json', json.dumps(info))
        public.writeFile(_path + '/script', script)

    # 添加触发器
    def add_trigger(self, args):
        info = json.loads(args.info)
        script = args.script
        _path = self.trigger_path + info['name']
        self.write_script_file(_path, info, script)
        public.WriteLog(self.log_name, '添加触发器: {}'.format(info['name']))
        return public.returnMsg(True, '添加成功!')

    # 修改改定触发器
    def modify_trigger(self, args):
        info = json.loads(args.info)
        script = args.script
        _path = self.trigger_path + info['name']
        if not os.path.exists(_path):
            return public.returnMsg(False, '指定触发器不存在!')
        public.writeFile(_path + '/info.json', json.dumps(info))
        public.writeFile(_path + '/script', script)
        public.WriteLog(self.log_name, '修改触发器: {}'.format(info['name']))
        return public.returnMsg(True, '修改成功!')

    # 执行指定脚本
    def exec_trigger(self, args):
        server_list = json.loads(args.server_list)
        info_file = self.trigger_path + args.sname + '/info.json'
        s_info = json.loads(public.readFile(info_file))
        thead_list = {}
        self.script_arr[s_info['name']] = []
        for address in server_list:
            thead_list[address] = threading.Thread(target=self.exec_server_trigger, args=[address, s_info])
            thead_list[address].start()

        for address in server_list:
            thead_list[address].join()
        public.WriteLog(self.log_name, '执行触发器脚本: {}'.format(args.sname))
        return self.script_arr[args.sname]

    # 在指定服务器执行脚本
    def exec_server_trigger(self, address, s_info):
        s_time = time.time()
        addr = address.split(',')
        skey = self.connect_server(addr[0])
        script_file = self.trigger_path + s_info['name'] + '/script'
        to_script_file = '/home/.bt_trigger/{}'.format(s_info['name'])
        my_terms[skey].upload_file(script_file, to_script_file)
        result = my_terms[skey].exec_shell(s_info['type'] + ' ' + to_script_file)
        self.script_arr[s_info['name']].append(
            {"server": addr[1] + '({})'.format(addr[0]), "result": result[1] + result[0], 'starttime': s_time,
             'endtime': time.time()})
        return True

    # 钢刀
    @staticmethod
    def zip_dir(dirname, zip_filename=None):
        import zipfile
        if dirname and zip_filename:
            filelist = []
            if os.path.isfile(dirname):
                filelist.append(dirname)
            else:
                for root, dirs, files in os.walk(dirname):
                    for name in files:
                        filelist.append(os.path.join(root, name))
            zf = zipfile.ZipFile(zip_filename, "w", zipfile.zlib.DEFLATED)
            for tar in filelist:
                arcname = tar[len(dirname):]
                zf.write(tar, arcname)
            zf.close()

    # 钢刀
    @staticmethod
    def un_zip(self, zip_path, target_path=None):
        import zipfile
        zip_file = zipfile.ZipFile(zip_path)
        for names in zip_file.namelist():
            zip_file.extract(names, target_path)
        zip_file.close()



    # 导入触发器   -> 钢刀
    def import_trigger(self, args):
        self.un_zip(args["path"], self.trigger_path)
        return public.returnMsg(True, "导入成功")

    # 导出触发器   -> 钢刀
    def export_trigger(self, args):
        try:
            self.zip_dir(self.trigger_path, self.plugin_path + "triggers.zip")
        except Exception as e:
            return public.returnMsg(False, f"触发器导出失败！{str(e)}")
        else:
            return public.returnMsg(True, f"触发器导出成功！{self.plugin_path+'triggers.zip'}")

    # 从云端同步触发器列表 -> 钢刀
    def cloud_sync_trigger(self, args):
        self.cloud_sync_script_or_triggers("triggers")
        public.WriteLog(self.log_name, '云端同步官方触发器')
        return public.returnMsg(True, '已同步官方触发器')

    # 获取脚本库列表
    def get_scripts(self, args):
        args.path = self.script_path
        return self.get_page_data(args, order='sort')

    # 取指定脚本
    def get_script_find(self, args):
        info_file = self.script_path + args.sname + '/info.json'
        script_file = self.script_path + args.sname + '/script'
        if not os.path.exists(info_file) or not os.path.exists(script_file):
            return public.returnMsg(False, '指定脚本不存在!')
        s_info = json.loads(public.readFile(info_file))
        s_info['script'] = public.readFile(script_file)
        return s_info

    # 执行指定脚本
    def exec_script(self, args):
        server_list = json.loads(args.server_list)
        info_file = self.script_path + args.sname + '/info.json'
        s_info = json.loads(public.readFile(info_file))
        thead_list = {}
        for address in server_list:
            thead_list[address] = threading.Thread(target=self.exec_server_script, args=[address, s_info])
            thead_list[address].start()

        for address in server_list:
            thead_list[address].join()
        public.WriteLog(self.log_name, '执行脚本库脚本: {}'.format(args.sname))
        return self.script_arr[args.sname]

    # 在指定服务器执行脚本
    def exec_server_script(self, address, s_info):
        s_time = time.time()
        addr = address.split(',')
        skey = self.connect_server(addr[0])
        script_file = self.script_path + s_info['name'] + '/script'
        to_script_file = '/home/.bt_scripts/{}'.format(s_info['name'])
        my_terms[skey].upload_file(script_file, to_script_file)
        result = my_terms[skey].exec_shell(s_info['type'] + ' ' + to_script_file)
        if not s_info['name'] in self.script_arr:
            self.script_arr[s_info['name']] = []
        self.script_arr[s_info['name']].append(
            {"server": addr[1] + '({})'.format(addr[0]), "result": result[1] + result[0], 'starttime': s_time,
             'endtime': time.time()})
        return True

    # 添加脚本库
    def add_script(self, args):
        info = json.loads(args.info)
        script = args.script
        _path = self.script_path + info['name']
        self.write_script_file(_path, info, script)
        # _path = self.script_path + info['name']
        # if not os.path.exists(_path):
        #     os.makedirs(_path,384)
        # public.writeFile(_path + '/info.json',json.dumps(info))
        # public.writeFile(_path + '/script',script)
        public.WriteLog(self.log_name, '添加脚本: {}'.format(info['title']))
        return public.returnMsg(True, '添加成功!')

    # 判断所安装的php版本并生成相应脚本 -> 钢刀
    def generate_script(self, args):
        word = "php-fpm-"
        try:
            for application_name in os.listdir("/etc/init.d"):
                if word in application_name:
                    php_version = ".".join(application_name.split(word)[-1])
                    info = {
                        "title": "重启PHP-{}".format(php_version),
                        "ps": "重启通过宝塔面板安装的PHP{}".format(php_version),
                        "name": "bt_script_restart_php{}".format(php_version.replace(".", "_")),
                        "type": "bash",
                        "sort": 0,
                        "author": "宝塔"
                    }
                    script = "/etc/init.d/{} restart".format(application_name)
                    _path = self.script_path + info['name']
                    self.write_script_file(_path, info, script)
        except:
            return False
        else:
            return True

    # 脚本或触发器官方同步共用函数 -> 钢刀
    def cloud_sync_script_or_triggers(self, key_type: str) -> bool:
        """
        :param key_type: "scripts" or "triggers";
        :return: bool
        """
        current_path = "/".join(os.path.abspath(__file__).split("/")[:-1]) + "/"
        if os.path.exists(current_path + key_type):
            cmd = """
                mv {} {}_tmp
                """.format(current_path+key_type, current_path+key_type)
            public.ExecShell(cmd)

        cmd_lines = """
                    mv {} {}_tmp\n
                    wget -O {}.zip {}/install/plugin/oos/{}.zip -T 5\n
                    unzip -o {}.zip -d {}\n
                    rm -f {}.zip
                    """.format(current_path+key_type, current_path+key_type, current_path+key_type, public.get_url(),
                               key_type, current_path+key_type, current_path, current_path+key_type)
        public.ExecShell(cmd_lines)

        if os.path.exists("{}_tmp".format(key_type)):
            public.ExecShell("""
                \cp -rf {}{}_tmp/* {}/
                """.format(current_path, key_type, current_path + key_type))
        return True

    # 编辑脚本库
    def modify_script(self, args):
        info = json.loads(args.info)
        script = args.script
        _path = self.script_path + info['name']
        if not os.path.exists(_path):
            return public.returnMsg(False, '指定脚本不存在!')
        public.writeFile(_path + '/info.json', json.dumps(info))
        public.writeFile(_path + '/script', script)
        public.WriteLog(self.log_name, '编辑脚本: {}'.format(info['title']))
        return public.returnMsg(True, '修改成功!')

    # 删除脚本库
    def remove_script(self, args):
        name = args.sname.strip()
        _path = self.script_path + name
        if os.path.exists(_path):
            public.ExecShell("rm -rf {}".format(_path))
        public.WriteLog(self.log_name, '删除脚本: {}'.format(name))
        return public.returnMsg(True, '删除成功!')

    # 取脚本执行日志
    def get_script_log(self, args):
        pass

    # 导入脚本库 -> 钢刀
    def import_script(self, args):
        if os.path.exists(args["path"]):
            self.un_zip(args["path"], self.script_path)
            return public.returnMsg(True, "导入成功")
        else:
            return public.returnMsg(False, "导入失败")

    # 导出脚本库 -> 钢刀
    def export_script(self, args):
        try:
            self.zip_dir(self.script_path, self.plugin_path + "scripts.zip")
        except Exception as e:
            return public.returnMsg(False, f"脚本导出失败！{str(e)}")
        else:
            return public.returnMsg(True, f"脚本导出成功！{self.plugin_path + 'scripts.zip'}")

    # 从云端同步脚本库 -> 钢刀
    def cloud_sync_script(self, args):
        self.cloud_sync_script_or_triggers("scripts")
        bl = self.generate_script(None)
        public.WriteLog(self.log_name, '云端同步官方脚本')
        return public.returnMsg(bl, "已同步官方脚本")

    # 获取任务编排分类列表
    def get_arrange_types(self, args):
        type_file = self.arrange_path + 'type.json'
        if not os.path.exists(type_file):
            public.writeFile(type_file, '[{"id":1,"name":"默认分类"}]')
        type_list = json.loads(public.readFile(type_file))
        type_list = sorted(type_list, key=lambda x: x['id'])
        return type_list

    # 保存分类
    def save_arrange_types(self, type_list):
        type_file = self.arrange_path + 'type.json'
        public.writeFile(type_file, json.dumps(type_list))

    # 取分类ID
    def get_type_id(self, type_list):
        return type_list[-1]['id'] + 1

    # 添加任务编排分类
    def add_arrange_type(self, args):
        type_list = self.get_arrange_types(None)
        type_info = {"id": self.get_type_id(type_list), "name": args.sname}
        type_list.append(type_info)
        self.save_arrange_types(type_list)
        return public.returnMsg(True, '添加成功!')

    # 编辑任务编排分类
    def modify_arrange_type(self, args):
        id = int(args.id)
        type_list = self.get_arrange_types(None)
        for i in range(len(type_list)):
            if type_list[i]['id'] == id:
                type_list[i]['name'] = args.sname.strip()
                break
        self.save_arrange_types(type_list)
        return public.returnMsg(True, '编辑成功!')

    # 删除任务编排分类
    def remove_arrange_type(self, args):
        id = int(args.id)
        type_list = self.get_arrange_types(None)
        for i in range(len(type_list)):
            if type_list[i]['id'] == id:
                del (type_list[i]['name'])
                break
        self.save_arrange_types(type_list)
        return public.returnMsg(True, '删除成功!')

    # 保存任务编排列表
    def save_arrange_list(self, a_list):
        a_file = self.arrange_path + 'list.json'
        public.writeFile(a_file, json.dumps(a_list))
        public.writeFile(self.is_read_file, '')

    # 获取任务编排列表
    def get_arrange_list(self, args, local=False):
        self.service_status()
        a_file = self.arrange_path + 'list.json'
        if not os.path.exists(a_file):
            public.writeFile(a_file, '[]')
        a_list = json.loads(public.readFile(a_file))
        result = []
        type_id = None
        if 'type_id' in args:
            type_id = int(args.type_id)
        search = None
        if 'search' in args:
            search = args.search.strip()
        for arrange_info in a_list:
            if type_id:
                if arrange_info['type_id'] != type_id:
                    continue
            if search:
                if arrange_info['title'].find(search) == -1 and arrange_info['name'].find(search) == -1 and \
                        arrange_info['ps'].find(search) == -1:
                    continue
            # if not local:
            #     info_file = self.trigger_path + arrange_info['trigger'] + '/info.json'
            #     if os.path.exists(info_file):
            #         arrange_info['trigger'] = json.loads(public.readFile(info_file))['title']
            #     info_file = self.script_path + arrange_info['script'] + '/info.json'
            #     if os.path.exists(info_file):
            #         arrange_info['script'] = json.loads(public.readFile(info_file))['title']
            result.append(arrange_info)
        result = sorted(result, key=lambda x: x['addtime'], reverse=True)
        if local:
            return result

        s_len = len(result)
        rows = 20
        if 'rows' in args:
            rows = int(args.rows)
        if 'p' not in args:
            args.p = 1
        if 'callback' not in args:
            args.callback = ''

        data = public.get_page(s_len, int(args.p), rows=rows, callback=args.callback)
        # shift = int(data['shift']) - 1
        # row = shift + int(data['row'])
        # data['list'] = []
        #
        # for i in range(s_len):
        #     if i > row: break
        #     if i <= shift: continue
        #     data['list'].append(result[i])
        return self.data_arrays(result, data, s_len)

    # 分页数据判断,集中在这个函数处理, 之前的第二页会多一条  ->  钢刀
    def data_arrays(self, result, data, s_len):
        shift = int(data['shift']) - 1
        row = shift + int(data['row'])
        data['list'] = []

        for i in range(s_len):
            if i > row: break
            if i <= shift: continue
            data['list'].append(result[i])

        return data

    # 获取触发器、脚本库、服务器列表
    def get_all_list(self, args):
        args.rows = 1000
        result = {}
        result['servers'] = self.get_server_list(args)['list']
        result['scripts'] = self.get_scripts(args)['list']
        result['triggers'] = self.get_trigger_list(args)['list']
        return result

    # 添加任务编排
    def add_arrange(self, args):
        arrange_info = json.loads(args.arrange_info)
        if not re.search('^[a-zA-Z0-9_-]+$', arrange_info['name']):
            return public.returnMsg(False, '任务名称不正确，只支持字每、数字、下划线的组合!')
        arrange_info['addtime'] = int(time.time())
        arrange_list = self.get_arrange_list(args, True)
        for arrange_data in arrange_list:
            if arrange_data['name'] == arrange_info['name']:
                return public.returnMsg(False, '指定任务名称已存在!')
        arrange_info['last_exec_time'] = 0
        arrange_info['last_avcive_time'] = 0
        arrange_info['avcive_total'] = 0
        arrange_info['exec_total'] = 0
        arrange_list.append(arrange_info)
        self.save_arrange_list(arrange_list)
        public.WriteLog(self.log_name, '添加编排任务: {}'.format(arrange_info['title']))
        return public.returnMsg(True, '添加成功!')

    # 取一条任务编排
    def get_arrange_find(self, args):
        name = args.sname.strip()
        arrange_list = self.get_arrange_list(args, True)
        for arrange_data in arrange_list:
            if arrange_data['name'] == name:
                data = self.get_all_list(args)
                data['arrange'] = arrange_data
                return data
        return public.returnMsg(False, '指定任务编排不存在!')

    # 修改任务编排
    def modify_arrange(self, args):
        arrange_info = json.loads(args.arrange_info)
        arrange_list = self.get_arrange_list(args, True)
        for i in range(len(arrange_list)):
            if arrange_list[i]['name'] == arrange_info['name']:
                arrange_info['addtime'] = arrange_list[i]['addtime']
                try:
                    arrange_info['last_exec_time'] = arrange_list[i]['last_exec_time']
                    arrange_info['last_avcive_time'] = arrange_list[i]['last_avcive_time']
                    arrange_info['avcive_total'] = arrange_list[i]['avcive_total']
                    arrange_info['exec_total'] = arrange_list[i]['exec_total']
                except:
                    arrange_info['last_exec_time'] = 0
                    arrange_info['last_avcive_time'] = 0
                    arrange_info['avcive_total'] = 0
                    arrange_info['exec_total'] = 0
                arrange_list[i] = arrange_info
        self.save_arrange_list(arrange_list)
        public.WriteLog(self.log_name, '修改编排任务: {}'.format(arrange_info['title']))
        return public.returnMsg(True, '编辑成功!')

    # 设置任务编排状态
    def set_arrange_status(self, args):
        name = args.sname
        status = int(args.status)
        arrange_list = self.get_arrange_list(args, True)
        for i in range(len(arrange_list)):
            if arrange_list[i]['name'] == name:
                arrange_list[i]['status'] = status
        self.save_arrange_list(arrange_list)
        public.WriteLog(self.log_name, '设置编排任务{} 状态为: {}'.format(name, status))
        return public.returnMsg(True, '设置成功!')

    # 删除任务编排
    def remove_arrange(self, args):
        name = args.sname.strip()
        arrange_list = self.get_arrange_list(args, True)
        for i in range(len(arrange_list)):
            if arrange_list[i]['name'] == name:
                del (arrange_list[i])
        self.save_arrange_list(arrange_list)
        public.WriteLog(self.log_name, '删除编排任务: {}'.format(name))
        return public.returnMsg(True, '删除成功!')

    # 执行任务编排
    def exec_arrange(self, args):
        arrange_info = self.get_arrange_find(args)['arrange']
        trigger_file = self.trigger_path + arrange_info['trigger'] + '/script'
        script_file = self.script_path + arrange_info['script'] + '/script'
        if not os.path.exists(trigger_file):
            return public.returnMsg(False, '指定触发器不存在!')
        if not os.path.exists(script_file):
            return public.returnMsg(False, '指定脚本库不存在!')
        self.script_arr[arrange_info['name']] = []
        thead_list = {}
        for address in arrange_info['servers']:
            thead_list[address] = threading.Thread(target=self.exec_arrange_script, args=[address, arrange_info])
            thead_list[address].start()

        for address in arrange_info['servers']:
            thead_list[address].join()

        public.WriteLog(self.log_name, '手动执行编排任务: {}'.format(arrange_info['title']))
        return self.script_arr[arrange_info['name']]

    def exec_arrange_script(self, address, arrange_info):
        try:
            # 准备信息
            trigger_file = self.trigger_path + arrange_info['trigger'] + '/script'
            trigger_info = json.loads(public.readFile(self.trigger_path + arrange_info['trigger'] + '/info.json'))
            script_file = self.script_path + arrange_info['script'] + '/script'
            script_info = json.loads(public.readFile(self.script_path + arrange_info['script'] + '/info.json'))
            result = {"server": address, "starttime": time.time()}

            # 执行触发器
            skey = self.connect_server(address)
            to_script_file = '/home/.bt_trriggers/{}'.format(arrange_info['trigger'])
            my_terms[skey].upload_file(trigger_file, to_script_file)
            trigger_result = my_terms[skey].exec_shell(trigger_info['type'] + ' ' + to_script_file)
            result['trigger_result'] = trigger_result[1] + trigger_result[0]

            # 执行脚本
            if self.check_arrange_value(trigger_result[0], trigger_info['value_type'], arrange_info):
                to_script_file = '/home/.bt_scripts/{}'.format(arrange_info['script'])
                my_terms[skey].upload_file(script_file, to_script_file)
                script_result = my_terms[skey].exec_shell(script_info['type'] + ' ' + to_script_file)
                result['script_result'] = script_result[1] + script_result[0]
                result['result'] = True
            else:
                result['script_result'] = ''
                result['result'] = False
            result['endtime'] = time.time()
            self.save_exec_info(arrange_info['name'], address, result['result'], result['script_result'])
            if arrange_info['name'] in self.script_arr:
                self.script_arr[arrange_info['name']].append(result)
            return True
        except:
            self.script_arr[arrange_info['name']].append(public.get_error_info())
            return False

    # 检查触发值
    def check_arrange_value(self, res_value, value_type, arrange_info):
        if value_type == 'int':
            c_value = [float(res_value)]
            d_value = float(arrange_info['where'])
        elif value_type == 'float':
            c_value = [float(res_value)]
            d_value = float(arrange_info['where'])
        elif value_type == 'string':
            c_value = [str(res_value).strip()]
            d_value = str(arrange_info['where'])
        elif value_type == 'list':
            c_value = json.loads(res_value)
            d_value = float(arrange_info['where'])

        for c in c_value:
            if arrange_info['operator'] == '=':
                if c == d_value:
                    return True
            elif arrange_info['operator'] == '>':
                if c > d_value:
                    return True
            elif arrange_info['operator'] == '<':
                if c < d_value:
                    return True
            elif arrange_info['operator'] == '!=':
                if c != d_value:
                    return True
            elif arrange_info['operator'] == '~':
                if c.find(d_value) != -1:
                    return True
            elif arrange_info['operator'] == '~':
                if c.find(d_value) == -1:
                    return True
        return False

    def run_arrange(self):
        self.get_arranges()
        for arrange_info in self.arrange_list:
            if arrange_info['status'] in [0, '0']:
                continue
            if not 'last_exec_time' in arrange_info:
                arrange_info['last_exec_time'] = 0

            if time.time() - arrange_info['last_exec_time'] > arrange_info['cycle']:
                for address in arrange_info['servers']:
                    tp = threading.Thread(target=self.exec_arrange_script, args=[address, arrange_info])
                    tp.setDaemon(True)
                    tp.start()

    def save_exec_info(self, name, address, is_avcive, result):
        public.writeFile(self.is_read_file, '')
        arrange_list = self.get_arranges(True)
        s_time = int(time.time())
        is_save = False

        # 写实时
        for i in range(len(arrange_list)):
            if arrange_list[i]['name'] != name:
                continue
            if not 'exec_total' in arrange_list[i]:
                arrange_list[i]['exec_total'] = 0
                arrange_list[i]['avcive_total'] = 0

            arrange_list[i]['last_exec_time'] = s_time
            arrange_list[i]['exec_total'] += 1
            if is_avcive:
                arrange_list[i]['last_avcive_time'] = s_time
                arrange_list[i]['avcive_total'] += 1
            is_save = True
            break

        # 写缓存
        for i in range(len(self.arrange_list)):
            if arrange_list[i]['name'] != name:
                continue
            self.arrange_list[i]['last_exec_time'] = s_time
            if is_avcive:
                self.arrange_list[i]['last_avcive_time'] = s_time
            break

        # 保存
        if is_save:
            self.save_arrange_list(arrange_list)
            s_file = self.arrange_path + 'logs/'
            if not os.path.exists(s_file):
                os.makedirs(s_file, 384)
            _head = "\n【{}】, 服务器: {},  触发: {}\n".format(public.format_date(times=s_time), address, is_avcive) + (
                        '=' * 50) + "\n"
            public.writeFile(s_file + name + '.log', _head + result, 'a+')

    def get_arranges(self, is_return=False):
        is_read = False
        if not self.arrange_list:
            is_read = True
        if not self.arrange_last_time and not is_read:
            is_read = True
        if not is_read:
            if time.time() - self.arrange_last_time > 60:
                is_read = True
        if not is_read:
            if os.path.exists(self.is_read_file):
                is_read = True
        if is_read:
            a_file = self.arrange_path + 'list.json'
            if not os.path.exists(a_file):
                public.writeFile(a_file, '[]')
            arrange_list = json.loads(public.readFile(a_file))
            if not is_return:
                self.arrange_last_time = time.time()
            if os.path.exists(self.is_read_file): os.remove(self.is_read_file)
        else:
            arrange_list = self.arrange_list
        if is_return:
            if not self.arrange_list:
                self.arrange_list = arrange_list
            return arrange_list
        else:
            self.arrange_list = arrange_list
            return []

    # 获取任务编排进度
    def get_arrange_progress(self, args):
        pass

    # 获取任务编排日志
    def get_arrange_log(self, args):
        s_file = self.arrange_path + 'logs/' + args.sname + '.log'
        if not s_file:
            return ""
        return public.GetNumLines(s_file, 200)

    # 清除运维平台日志   -> 钢刀
    def rm_all_log(self, args):
        import sqlite3
        try:
            conn = sqlite3.connect('data/default.db')
            cur = conn.cursor()
            cur.execute("DELETE from logs WHERE type=?", (self.log_name,))
        except Exception as e:
            try:
                conn.close()
            except:
                pass
            return public.returnMsg(False, str(e))
        else:
            conn.commit()
            cur.close()
            conn.close()
        return public.returnMsg(True, "运维平台日志清除成功")

    # 获取操作日志
    def get_logs(self, get):
        import page
        page = page.Page()
        count = public.M('logs').where('type=?', (self.log_name,)).count()
        limit = 12
        info = {}
        info['count'] = count
        info['row'] = limit
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        info['uri'] = get
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs

        data = {}

        # 获取分页数据
        data['page'] = page.GetPage(info, '1,2,3,4,5,8')
        data['data'] = public.M('logs').where('type=?', (self.log_name,)).order('id desc').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).field('log,addtime').select()
        return data

    def run_task(self):
        while True:
            self.run_arrange()
            time.sleep(1)


if __name__ == '__main__':
    p = oos_main()
    p.run_task()
