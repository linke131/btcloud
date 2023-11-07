#!/usr/bin/python
# coding: utf-8
# +------------------------------------------------------------------
# | 阿里云对象存储自动挂载平台客户端
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hezhihong <272267659@qq.com>
# +-------------------------------------------------------------------
import json
import os
import sys
import time

import requests
from cmath import inf
from gevent import config
from operator import contains

panelPath = os.getenv('BT_PANEL')
if not panelPath: panelPath = '/www/server/panel'
import oss2
from oss2.exceptions import NoSuchKey, OssError, NotFound

sys.path.append("class/")
import public


class ossfs_main:
    _secret_id = None
    _secret_key = None
    _aes_key = None
    _ossfs_path = '/www/server/panel/plugin/ossfs/data'
    _set_path = '/www/ossfs'
    _access_key_id = ''
    _access_key_secret = ''
    _bucket_name = ''
    _app_id = ''
    _endpoint = ''
    _oss_path = os.path.join(_ossfs_path, 'ossfs.conf')
    _mount_file = os.path.join(_ossfs_path, 'oss_mount.conf')

    def __init__(self):
        if not os.path.isdir(os.path.join(self._set_path, 'alioss')): os.makedirs(
            os.path.join(self._set_path, 'alioss'))
        if not os.path.isdir(os.path.join(self._set_path, 'bos')): os.makedirs(os.path.join(self._set_path, 'bos'))

        if not os.path.exists(self._ossfs_path):
            os.makedirs(self._ossfs_path)
        # 用户反馈有密钥泄露风险, 将配置放到插件目录,卸载时就会被清理
        # 删除旧配置文件
        if os.path.exists('/www/server/panel/data/ossfs.conf'):
            os.replace('/www/server/panel/data/ossfs.conf', self._oss_path)
        if os.path.exists('/www/server/panel/data/oss_mount.conf'):
            os.replace('/www/server/panel/data/oss_mount.conf', self._mount_file)

    def uninstall_check(self, get=None):

        conf = []
        has_mount = False
        try:
            with open(self._mount_file) as fp:
                conf = json.load(fp)
        except:
            pass
        for item in conf:
            mlist = item.get('mount_list', [])
            if len(mlist) > 0:
                has_mount = True
                break
        if has_mount:
            return {'status': True, 'code': -1,
                    'msg': '检测到有云存储未卸载，为保证数据安全,请在保证没有读写的情况下卸载所有云存储后再卸载插件！'}
        return {'status': False}

    def get_mount_default_path(self, oss_type):
        """
        @name
        """
        add_path = os.path.join(self._set_path, oss_type)
        path = os.path.join(add_path, self._bucket_name)
        return path

    def get_bucket(self, get):
        ks3 = ks3_main()
        return ks3.get_bucket()

    def get_oss_path(self, path_one, path_two):
        """
        @name 拼接对象存储挂载路径
        """
        return os.path.join(path_one, path_two)

    def get_oss_info(self, get):
        """
        @name 取oss密钥信息
        """
        if get.type == 'txcos':
            oss_info = {"type": get.type, "key_info": {"access_key_id": "", "access_key_secret": "", "app_id": ""}}
        else:
            oss_info = {"type": get.type, "key_info": {"access_key_id": "", "access_key_secret": ""}}
        conf = []
        try:
            conf = json.loads(public.readFile(self._oss_path))
        except:
            conf = []
        if conf:
            for ali_info in conf:
                if 'type' not in ali_info or 'key_info' not in ali_info or 'access_key_id' not in ali_info[
                    'key_info'] or 'access_key_secret' not in ali_info['key_info']: continue
                if ali_info['type'] == get.type:
                    if get.type == 'txcos' and 'app_id' not in ali_info['key_info']:
                        ali_info['key_info']['app_id'] == ''
                    oss_info = ali_info
                    break
        ak = oss_info["key_info"]["access_key_id"]
        sk = oss_info["key_info"]["access_key_secret"]
        if ak: ak = ak[:4] + " ***** " + ak[-4:]
        if sk: sk = sk[:4] + " ***** " + sk[-4:]
        oss_info["key_info"]["access_key_id"] = ak
        oss_info["key_info"]["access_key_secret"] = sk
        return oss_info

    def remove_blank_lines(self, conf_file):
        """
        去除文本的空行
        """
        file_one = open(conf_file, 'r', encoding='utf-8')
        lines = file_one.readlines()
        file_two = open(conf_file, 'w', encoding='utf-8')
        for line in lines:
            if line.split():
                file_two.writelines(line)
            else:
                file_two.writelines("")
        file_one.close()
        file_two.close()
        return True

    def get_path(self, path):
        """
        @name 取路径
        """
        if path[-1] != '/': path = path + '/'
        if path[:1] != '/': path = '/' + path
        path = path.replace('//', '/')
        return path

    def check_path(self, path):
        """
        @name 检测挂载目录 是否有数据、是否为系统关键目录
        """
        # 检测是否为系统关键目录
        sys_path_one, sys_path_two = public.get_sys_path()
        path = self.get_path(path)
        for check_one in sys_path_one:
            if path in self.get_path(check_one): return False
        for check_two in sys_path_two:
            if path in self.get_path(check_two): return False
        return True

    def check_bucket_mount(self, bucket_name):
        """
        @name 检测bucket是否挂载
        @params bucket_name 存储空间名
        """
        add_path = os.path.join(self._set_path, 'alioss')
        path = os.path.join(add_path, self._bucket_name)
        if self.check_path_mount(path):
            return True
        else:
            return False

    def check_path_mount(self, path):
        """
        @name 检测目录是否挂载
        @path 挂载目录
        """
        mount_result = public.ExecShell("df -h -P|grep '/'|grep -v tmpfs")[0]
        mount_list = mount_result.split('\n')
        for check_mount in mount_list:
            if not check_mount: continue
            mount_info = check_mount.split()
            if len(mount_info) < 6: continue
            if mount_info[5] == path: return True
        return False

    def get_mount_list(self, get):
        """
        @name 取挂载信息列表
        return [{'bucket_name':bucket_name,'mount_path':mount_path,'mount_date':mount_date,'auto':True}]
        """
        return self.get_oss_mount_list(get, True)

    def get_oss_obj(self, oss_type):
        """
        @name 取oss对象
        """
        oss_obj = None
        if oss_type == 'alioss':
            oss_obj = alioss_main()
        elif oss_type == 'bos':
            oss_obj = bos_main()
        elif oss_type == 'jdoss':
            oss_obj = jdoss_main()
        elif oss_type == 'txcos':
            oss_obj = txcos_main()
        elif oss_type == 'obs':
            oss_obj = obs_main()
        elif oss_type == 'ks3':
            oss_obj = ks3_main()
        elif oss_type == 'qiniu':
            oss_obj = qiniu_main()
        return oss_obj

    def get_oss_mount_list(self, args=None, is_get=False):
        """
        @name 取挂载信息列表
        """
        get = args
        data = []
        mount_info = []
        try:
            mount_info = json.loads(public.readFile(self._mount_file))
            print(mount_info)
        except:
            pass
        # if not mount_info:return data
        oss_obj = self.get_oss_obj(get.type)
        bucket_list = oss_obj.get_bucket()
        if not bucket_list: return data
        print(bucket_list)
        for bucket in bucket_list:
            tmp_dict = {}
            if not bucket: continue
            tmp_dict['bucket_name'] = bucket['bucket_name']
            tmp_dict['bucket_location'] = bucket['bucket_location']
            tmp_dict['bucket_location'] = self.format_region(bucket['bucket_location'], get.type)
            tmp_dict['mount_path'] = ''
            self._bucket_name = bucket['bucket_name']
            tmp_dict['default_path'] = self.get_mount_default_path(get.type)
            is_mount = False
            tmp_dict['mount'] = False
            for info in mount_info:
                if not mount_info: continue
                # print('11111111111222222222222')
                # print(mount_info)
                if 'type' not in info or info['type'] != get.type or 'mount_list' not in info: continue
                for mount_i in info['mount_list']:
                    if 'bucket_name' not in mount_i: continue
                    # print(info['mount_list'])
                    # print('3333333')
                    # print(mount_i)
                    # print(mount_i['bucket_name'])
                    # print(type(mount_i['bucket_name']))
                    if mount_i['bucket_name'] == bucket['bucket_name']:
                        tmp_dict['mount_path'] = mount_i['mount_path']
                        is_mount = True
            if is_mount: tmp_dict['mount'] = True
            print(tmp_dict)
            data.append(tmp_dict)
        # data = sorted(data,key=lambda keys:keys['mount'],reverse=True)
        if is_get:
            return self.get_page(data, args)
        else:
            return data

    def check_ossfs_install(self, check_str):
        """
        @name 检测ossfs是否安装
        """
        exec_cmd = 'which {} |grep {}|wc -l'.format(check_str, check_str)
        check_result = 0
        try:
            check_result = int(public.ExecShell(exec_cmd)[0])
        except:
            pass
        if check_result == 0: return False
        return True

    def install_ossfs(self):
        """
        @name 安装ossfs
        """
        public.ExecShell('wget http://gosspublic.alicdn.com/ossfs/ossfs_1.80.6_centos7.0_x86_64.rpm')
        try:
            public.ExecShell('sudo yum install ossfs_1.80.6_centos7.0_x86_64.rpm')
        except:
            public.ExecShell('yum install ossfs_1.80.6_centos7.0_x86_64.rpm')

    def format_region(self, region, oss_type):
        """
        @name bucket地区转换
        """
        args_value = public.dict_obj()
        args_value.type = oss_type
        region_list = self.get_region(args_value)
        result = ''
        for region_info in region_list:
            if region == region_info['value']:
                result = region_info['title']
                break
        return result

    def get_region(self, get=None):
        """
        @name 地区可选值列表
        """
        args_value = get
        return self.get_oss_region(args_value.type)

    def get_oss_region(self, oss_type):
        region_list = []
        if oss_type == 'alioss':
            region_list = [{'value': 'oss-ap-south-1', 'title': '印度（孟买）'},
                           {'value': 'oss-ap-southeast-7', 'title': '泰国（曼谷）'},
                           {'value': 'oss-ap-southeast-6', 'title': '菲律宾（马尼拉）'},
                           {'value': 'oss-me-east-1', 'title': '阿联酋（迪拜）'},
                           {'value': 'oss-us-east-1', 'title': '美国（弗吉尼亚）'},
                           {'value': 'oss-us-west-1', 'title': '美国（硅谷）'},
                           {'value': 'oss-eu-west-1', 'title': '英国（伦敦）'},
                           {'value': 'oss-eu-central-1', 'title': '德国（法兰克福）'},
                           {'value': 'oss-ap-northeast-1', 'title': '日本（东京）'},
                           {'value': 'oss-ap-southeast-5', 'title': '印度尼西亚（雅加达）'},
                           {'value': 'oss-ap-southeast-3', 'title': '马来西亚（吉隆坡）'},
                           {'value': 'oss-ap-northeast-2', 'title': '韩国（首尔）'},
                           {'value': 'oss-ap-southeast-1', 'title': '新加坡'},
                           {'value': 'oss-ap-southeast-2', 'title': '澳大利亚（悉尼）'},
                           {'value': 'oss-cn-hongkong', 'title': '中国香港'},
                           {'value': 'oss-cn-chengdu', 'title': '西南1（成都）'},
                           {'value': 'oss-cn-guangzhou', 'title': '华南3（广州）'},
                           {'value': 'oss-cn-heyuan', 'title': '华南（2）（河源）'},
                           {'value': 'oss-cn-shenzhen', 'title': '华南1（深圳）'},
                           {'value': 'oss-cn-wulanchabu', 'title': '华北6（乌兰察布）'},
                           {'value': 'oss-cn-huhehaote', 'title': '华北5（呼和浩特）'},
                           {'value': 'oss-cn-zhangjiakou', 'title': '华北3（张家口）'},
                           {'value': 'oss-cn-beijing', 'title': '华北2（北京）'},
                           {'value': 'oss-cn-qingdao', 'title': '华北1（青岛）'},
                           {'value': 'oss-cn-nanjing', 'title': '华东5（南京）'},
                           {'value': 'oss-cn-shanghai', 'title': '华东2（上海）'},
                           {'value': 'oss-cn-hangzhou', 'title': '华东1（杭州）'}]
        elif oss_type == 'bos':
            region_list = [{'value': 'bj', 'title': '华北-北京'}, {'value': 'bd', 'title': '华北-保定'},
                           {'value': 'su', 'title': '华东-苏州'}, {'value': 'gz', 'title': '华南-广州'},
                           {'value': 'fsh', 'title': '华东-上海 '}, {'value': 'fwh', 'title': '金融华中-武汉'},
                           {'value': 'hkg', 'title': '中国香港'}, {'value': 'sin', 'title': '新加坡'}]
        elif oss_type == 'jdoss':
            region_list = [{'value': 'cn-north-1', 'title': '华北-北京'}, {'value': 'cn-south-1', 'title': '华南-广州'},
                           {'value': 'cn-east-1', 'title': '华东-宿迁'}, {'value': 'cn-east-2', 'title': '华东-上海'}]
        elif oss_type == 'obs':
            region_list = [{'value': 'af-south-1', 'title': '非洲-约翰内斯堡'},
                           {'value': 'cn-north-4', 'title': '华北-北京四'},
                           {'value': 'cn-north-1', 'title': '华北-北京一'},
                           {'value': 'cn-north-9', 'title': '华北-乌兰察布一'},
                           {'value': 'cn-east-2', 'title': '华东-上海二'},
                           {'value': 'cn-east-3', 'title': '华东-上海一'},
                           {'value': 'cn-south-1', 'title': '华南-广州'},
                           {'value': 'la-north-2', 'title': '拉美-墨西哥城二'},
                           {'value': 'na-mexico-1', 'title': '拉美-墨西哥城一'},
                           {'value': 'sa-brazil-1', 'title': '拉美-圣保罗一'},
                           {'value': 'la-south-2', 'title': '拉美-圣地亚哥'},
                           {'value': 'cn-southwest-2', 'title': '西南-贵阳一'},
                           {'value': 'ap-southeast-2', 'title': '亚太-曼谷'},
                           {'value': 'ap-southeast-3', 'title': '亚太-新加坡'},
                           {'value': 'ap-southeast-1', 'title': '中国-香港'}]
        elif oss_type == 'txcos':
            region_list = [{'value': 'ap-chengdu', 'title': '成都（中国）'},
                           {'value': 'ap-shanghai', 'title': '上海（中国）'},
                           {'value': 'ap-nanjing', 'title': '南京（中国）'},
                           {'value': 'ap-beijing', 'title': '北京（中国）'},
                           {'value': 'ap-guangzhou', 'title': '广州（中国）'},
                           {'value': 'ap-chongqing', 'title': '重庆（中国）'},
                           {'value': 'ap-shenzhen-fsi', 'title': '深圳金融（中国）'},
                           {'value': 'ap-shanghai-fsi', 'title': '上海金融（中国）'},
                           {'value': 'ap-beijing-fsi', 'title': '北京金融（中国）'},
                           {'value': 'ap-hongkong', 'title': '中国香港（中国）'},
                           {'value': 'ap-singapore', 'title': '新加坡'}, {'value': 'ap-mumbai', 'title': '孟买'},
                           {'value': 'ap-jakarta', 'title': '雅加达'}, {'value': 'ap-seoul', 'title': '首尔'},
                           {'value': 'ap-bangkok', 'title': '曼谷'}, {'value': 'ap-tokyo', 'title': '东京'},
                           {'value': 'na-siliconvalley', 'title': '硅谷（美西）'},
                           {'value': 'na-ashburn', 'title': '弗吉尼亚（美东）'},
                           {'value': 'na-toronto', 'title': '多伦多'}, {'value': 'sa-saopaulo', 'title': '圣保罗'},
                           {'value': 'eu-frankfurt', 'title': '法兰克福'}, {'value': 'eu-moscow', 'title': '莫斯科'}]
        elif oss_type == 'ks3':
            region_list = [{'value': 'beijing', 'title': '中国（北京）'}, {'value': 'shanghai', 'title': '中国（上海）'},
                           {'value': 'guangzhou', 'title': '中国（广州）'}, {'value': 'hk-1', 'title': '中国（香港）'},
                           {'value': 'rus', 'title': '俄罗斯'}, {'value': 'sgp', 'title': '新加坡'}]
        elif oss_type == 'qiniu':
            region_list = [{'value': 'cn-east-1', 'title': '华东-浙江'}, {'value': 'cn-east-2', 'title': '华东-浙江2'},
                           {'value': 'cn-north-1', 'title': '华北-河北'}, {'value': 'cn-south-1', 'title': '华南-广东'},
                           {'value': 'us-north-1', 'title': '北美-洛杉矶'},
                           {'value': 'ap-southeast-1', 'title': '亚太-新加坡（原东南亚）'}]
        return region_list

    def oss_mount(self, get):
        """
        @name 挂载存储空间
        """
        # echo chus:LTAI9wOiuFfGCCtR:72RTcX0JwChaE6J2ATyULThuPzBtQL > /etc/passwd-ossfs
        # chmod 640 /etc/passwd-ossfs
        # mkdir /www/ossfs
        # ossfs chus /www/ossfs -o url=https://oss-cn-hangzhou.aliyuncs.com
        #
        if get:
            if 'bucket_name' not in get or 'path' not in get or 'type' not in get or not get.bucket_name or not get.path or not get.type: return public.returnMsg(
                False, '错误的参数')
        # if not get or 'type' not in get or 'bucket_name' not in get:return public.returnMsg(False, '错误的参数')
        return self.oss_exec_mount(get)
        return public.returnMsg(True, '挂载成功！')

    def get_key_id_secret(self, oss_type):
        """
        @name 取密钥信息
        """
        if not self._access_key_id or not self._access_key_secret:
            try:
                conf = json.loads(public.readFile(self._oss_path))
                print(conf)
                for info in conf:
                    if 'type' not in info or oss_type != info['type'] or 'key_info' not in info: continue
                    if 'access_key_id' not in info['key_info'] or 'access_key_secret' not in info['key_info']: continue
                    self._access_key_id = info['key_info']['access_key_id']
                    self._access_key_secret = info['key_info']['access_key_secret']
                    print(self._access_key_id)
                    print(self._access_key_secret)
            except:
                pass
        if not self._access_key_id or not self._access_key_secret: return False
        return True

    def oss_exec_mount(self, args):
        get = args
        if get: self._bucket_name = get.bucket_name.strip()
        path = get.path.strip()
        # print(self._bucket_name)
        # print(path)
        check_str = ''
        if get.type == 'bos':
            check_str = 'bosfs'
        elif get.type == 'txcos':
            check_str = 'cosfs'
        else:
            check_str = 's3fs'
        if not self.check_ossfs_install(check_str):
            self.install_ossfs()
        if not self.check_ossfs_install(check_str): return public.returnMsg(False,
                                                                            '{}未成功安装，无法挂载！'.format(check_str))
        if self.check_path_mount(path): return public.returnMsg(False, '挂载失败！挂载目录被占用，请重新设置挂载目录！')
        if not self.check_path(path): return public.returnMsg(False,
                                                              '不能设置系统关键目录为挂载目录，请重新设置挂载目录！')
        if not os.path.isdir(path): os.makedirs(path)
        if os.listdir(path): return public.returnMsg(False, '挂载目录不为空，请移除挂载目录内的文件后再尝试挂载！')
        # print('222222')
        oss_obj = self.get_oss_obj(get.type)
        bucket_list = oss_obj.get_bucket()
        # print(bucket_list)
        is_bucket = False
        region_name = ''
        for bucket in bucket_list:
            if bucket['bucket_name'] == self._bucket_name:
                is_bucket = True
                # if get.type == 'ks3':continue
                region_name = bucket['bucket_location']
                break
        if not is_bucket: return public.returnMsg(False, '挂载的存储桶不存在，请创建后再重新挂载！')
        if not self.get_key_id_secret(get.type): return public.returnMsg(False, '对象客户端密钥信息获取失败！')
        conf_file = '/etc/passwd-{}_ossfs'.format(get.type)

        # 兼容多种对象存储
        self._endpoint = self.get_url(get.type, region_name)

        if hasattr(get, "intranet_endpoint"):
            if get.intranet_endpoint == '1':
                self._endpoint = oss_obj.get_endpoint(self._endpoint, self._bucket_name)
                if get.type != 'ks3':
                    try:
                        requests.get(self._endpoint, timeout=1)
                    except:
                        return public.returnMsg(False, '内网地址不通，请勿选择内网挂载')
        if get.type == 'jdoss':
            exec_cmd = 'echo {}:{} > {}'.format(self._access_key_id, self._access_key_secret, conf_file)
            public.ExecShell(exec_cmd)
            public.ExecShell('chmod 600 {}'.format(conf_file))
            exec_cmd = 's3fs {} {} -o passwd_file={} -o url={}'.format(self._bucket_name, path,
                                                                       conf_file,
                                                                       self._endpoint)
            print('exec_cmd')
            print(exec_cmd)
            print(self._endpoint)
            public.ExecShell(exec_cmd)
        elif get.type == 'qiniu':
            exec_cmd = 'echo {}:{} > {}'.format(self._access_key_id, self._access_key_secret, conf_file)
            public.ExecShell(exec_cmd)
            public.ExecShell('chmod 600 {}'.format(conf_file))
            exec_cmd = 's3fs {} {} -o passwd_file={} -o url={}'.format(self._bucket_name, path, conf_file,
                                                                       self._endpoint)
            public.ExecShell(exec_cmd)
        elif get.type == 'bos':
            exec_cmd = 'bosfs {} {} -o endpoint={} -o ak={} -o sk={} -o allow_other -o mount_umask=0000'.format(
                self._bucket_name, path, self._endpoint, self._access_key_id, self._access_key_secret)
            print(exec_cmd)
            public.ExecShell(exec_cmd)
        elif get.type == 'alioss':
            exec_cmd = 'echo {}:{}:{}> {}'.format(self._bucket_name, self._access_key_id, self._access_key_secret,
                                                  conf_file)
            public.ExecShell(exec_cmd)
            public.ExecShell('chmod 600 {}'.format(conf_file))
            exec_cmd = 'ossfs {} {} -o passwd_file={} -o url={}'.format(self._bucket_name, path, conf_file,
                                                                        self._endpoint)
            public.ExecShell(exec_cmd)
        elif get.type == 'obs':
            exec_cmd = 'echo {}:{} > {}'.format(self._access_key_id, self._access_key_secret, conf_file)
            public.ExecShell(exec_cmd)
            public.ExecShell('chmod 600 {}'.format(conf_file))
            exec_cmd = 'obsfs {} {} -o passwd_file={} -o url={}'.format(self._bucket_name, path, conf_file,
                                                                        self._endpoint)
            public.ExecShell(exec_cmd)
        elif get.type == 'txcos':
            exec_cmd = 'echo {}:{}:{} > {}'.format(self._bucket_name, self._access_key_id, self._access_key_secret,
                                                   conf_file)
            public.ExecShell(exec_cmd)
            public.ExecShell('chmod 600 {}'.format(conf_file))
            exec_cmd = 'cosfs {} {} -opasswd_file={} -ourl={} -odbglevel=info -onoxattr -oallow_other'.format(
                self._bucket_name, path, conf_file, self._endpoint)
            public.ExecShell(exec_cmd)
        elif get.type == 'ks3':
            exec_cmd = 'echo {}:{}> {}'.format(self._access_key_id, self._access_key_secret, conf_file)
            public.ExecShell(exec_cmd)
            public.ExecShell('chmod 600 {}'.format(conf_file))
            region_list = self.get_oss_region('ks3')
            for region in region_list:
                if region['value'] in ['rus', 'sgp']:
                    self._endpoint = 'https://ks3-{}.ksyuncs.com'.format(region['value'])
                else:
                    self._endpoint = 'https://ks3-cn-{}.ksyuncs.com'.format(region['value'])
                if hasattr(get, "intranet_endpoint"):
                    if get.intranet_endpoint == '1':
                        self._endpoint = oss_obj.get_endpoint(self._endpoint, self._bucket_name)
                print(self._endpoint)
                exec_cmd = 's3fs {} {} -o passwd_file={} -o url={}'.format(self._bucket_name,
                                                                           path, conf_file,
                                                                           self._endpoint)
                print(exec_cmd)
                result = public.ExecShell(exec_cmd)

                if result[1].find('Operation not permitted\n') == -1: break
        if not self.check_path_mount(path): return public.returnMsg(False, '挂载失败！')
        # 设置开机自动挂载
        # self.set_auto_mount(exec_cmd)
        self.set_auto_mount_new(exec_cmd)
        # 记录挂载配置
        data = []
        add_mount = {}
        add_mount['bucket_name'] = get.bucket_name
        add_mount['mount_path'] = path
        alioss_int_info = {}
        alioss_int_info['type'] = get.type
        alioss_int_info['key_info'] = {'access_key_id': self._access_key_id,
                                       'access_key_secret': self._access_key_secret}
        mount_list = []
        mount_list.append(add_mount)
        alioss_int_info['mount_list'] = mount_list
        mount_info = []
        found = False
        try:
            mount_info = json.loads(public.readFile(self._mount_file))
        except:
            pass

        m_item = {
            "type": get.type,
            "key_info": {'access_key_id': self._access_key_id, 'access_key_secret': self._access_key_secret},
            "mount_list": [add_mount]
        }
        for item in mount_info:
            if item['type'] == get.type:
                m_list = item.get('mount_list', [])
                m_list.append(add_mount)
                item['mount_list'] = m_list
                found = True
                break
        if not found:
            mount_info.append(m_item)
        public.writeFile(self._mount_file, json.dumps(mount_info))
        # if os.path.isfile(self._mount_file):
        #     mount_info=[]
        #     try:
        #         mount_info=json.loads(public.readFile(self._mount_file))
        #     except:
        #         pass
        #     for mount_i in mount_info:
        #         if not mount_info:
        #             data.append(alioss_int_info)
        #             is_True=False
        #             break
        #         if not mount_i or 'type' not in mount_i:continue
        #         if mount_i==mount_info[-1] and mount_i['type']!=get.type:
        #             data =mount_info
        #             break
        #         if mount_i['type']!=get.type or 'mount_list' not in mount_i or not mount_i['mount_list']:continue
        #         mount_i['mount_list'].append(add_mount)
        #         data =mount_info
        #         is_True=False
        #         break

        # if is_True:data.append(alioss_int_info)
        # public.writeFile(self._mount_file,json.dumps(data))
        self.remove_blank_lines(self._mount_file)
        return public.returnMsg(True, '挂载成功！')

    def get_url(self, storage_type, region_name):
        """
        获取挂载url
        :param region_name:
        :param type:
        :return:
        """
        if storage_type == 'obs':
            _endpoint = 'https://obs.{}.myhuaweicloud.com'.format(region_name)
        elif storage_type == 'jdoss':
            _endpoint = "https://s3.{}.jdcloud-oss.com".format(region_name)
        elif storage_type == 'alioss':
            _endpoint = 'https://{}.aliyuncs.com'.format(region_name)
        elif storage_type == 'obs':
            _endpoint = 'https://obs.{}.myhuaweicloud.com'.format(region_name)
        elif storage_type == 'txcos':
            _endpoint = 'http://cos.{}.myqcloud.com'.format(region_name)
        elif storage_type == 'bos':
            _endpoint = 'http://{}.bcebos.com'.format(region_name)
        elif storage_type == 'qiniu':
            _endpoint = 'https://s3-{}.qiniucs.com'.format(region_name)
        return _endpoint

    def clear_mount(self, file_name, check_str, is_passwd=False, is_umount=False, oss_type=None, mount_str=None):
        """
        @name 清除/etc/passwd-ossfs文件记录
        """
        if not os.path.isfile(file_name): return True
        with open(file_name, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(file_name, "w", encoding="utf-8") as f_w:
            check_bucket = '/' + check_str
            for line in lines:
                if len(line.split()) < 5: continue
                replace_one = line.split()[2].replace(check_bucket, '')
                replace_two = replace_one.replace('/www/ossfs/', '')
                if is_passwd and line.split(':')[0] == check_str: continue
                if is_umount and line[0] != '#' and len(line.split()) > 4 and line.split()[
                    1] == check_str and replace_two == oss_type and line.split()[0] == mount_str: continue
                f_w.write(line)
        self.remove_blank_lines(self._mount_file)

    def oss_unmount(self, get=None):
        """
        @name 卸载oss挂载
        """
        return self.oss_exec_unmount(get)

    def oss_exec_unmount(self, args):
        get = args
        exec_cmd = ''
        if get: path = get.path
        # if get.type =='txcos' or get.type =='ks3' or get.type =='jdoss' or get.type =='obs':
        unmount_str = 'umount'
        exec_cmd_one = '{} {}'.format(unmount_str, path)
        # else:
        unmount_str = 'fusermount'
        exec_cmd_two = '{} -zu {}'.format(unmount_str, path)
        # print(exec_cmd)
        try:
            result = os.system(exec_cmd_one)
        except:
            try:
                result = os.system(exec_cmd_two)
            except:
                pass
        print(exec_cmd_one)
        print(exec_cmd_two)
        # return public.returnMsg(False, '卸载失败！')
        # if self.check_path_mount(path):return public.returnMsg(False, '挂载目录已挂载，请重新设置挂载目录！')
        if result != 0 and self.check_path_mount(path): return public.returnMsg(False, '卸载失败！')
        # 清理挂载记录信息
        mount_info = []
        if os.path.isfile(self._mount_file):
            try:
                mount_info = json.loads(public.readFile(self._mount_file))
            except:
                pass
        tmp_mount_list = []
        if mount_info:
            print(self._mount_file)
            print(mount_info)
            for info in mount_info:
                modify_index = mount_info.index(info)
                if 'type' not in info or 'mount_list' not in info: continue
                if info['type'] == get.type:
                    print('211111111111')
                    tmp_mount_list = info['mount_list']
                    for bucket in info['mount_list']:
                        if 'bucket_name' not in bucket: continue
                        if bucket['bucket_name'] == get.bucket_name:
                            tmp_mount_list.remove(bucket)
                            info['mount_list'] = tmp_mount_list
                            mount_info[modify_index] = info
                            public.writeFile(self._mount_file, json.dumps(mount_info))
                            self.remove_blank_lines(self._mount_file)
                            print('211111111111')
                            break
        file_name = '/etc/init.d/ossfs'
        mount_str = ''
        if get.type == 'bos':
            mount_str = 'bosfs'
        elif get.type == 'txcos':
            mount_str = 'cosfs'
        else:
            mount_str = 's3fs'

        self.clear_mount_new(file_name, mount_str, mount_path=path)

        # self.clear_mount(file_name,get.bucket_name,False,True,get.type,mount_str)
        return public.returnMsg(True, '卸载成功！')

    def module_file(self, add_value):
        """
        @name 模板文件
        """
        add_endpoint = 'https://' + self._endpoint
        module_content = '''
#!/bin/bash
#
# ossfs      Automount Aliyun OSS Bucket in the specified direcotry.
#
# chkconfig: 2345 90 10
# description: Activates/Deactivates ossfs configured to start at boot time.

%s 
''' % (add_value)
        return module_content

    def set_auto_mount(self, add_value):
        """
        @name 设置开机自动挂载
        """
        file_name = '/etc/init.d/ossfs'
        if not os.path.isfile(file_name):
            public.writeFile(file_name, self.module_file(add_value))
        else:
            add_endpoint = 'https://' + self._endpoint
            add_str = '\n'
            # add_str+='ossfs {} {} -o url={}'.format(self._bucket_name,path,add_endpoint)
            add_str += add_value
            conf = public.readFile(file_name)
            conf += add_str
            public.writeFile(file_name, conf)
        exec_cmd_one = 'chmod a+x /etc/init.d/ossfs'
        exec_cmd_two = 'chkconfig ossfs on'
        self.remove_blank_lines(file_name)
        public.ExecShell(exec_cmd_one)
        public.ExecShell(exec_cmd_two)

    def _parse_init_script(self, text):
        s0 = False
        cmds = []
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line: continue
            # 兼容旧配置
            if line.split(' ')[0] in ['bosfs', 'cosfs', 's3fs']:
                cmds.append(line)
                continue
            if line == '#MOUNT#': s0 = True
            if line[0] == '#' or not s0: continue
            cmds.append(line)
        return cmds

    def _gen_init_script(self, cmds):
        init_script_header = '''#!/bin/bash
# chkconfig: 2345 90 10
# description: Activates/Deactivates ossfs configured to start at boot time.

### BEGIN INIT INFO
# Provides:          Ossfs
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts ossfs
# Description:       starts ossfs
### END INIT INFO

case "$1" in
        start)
            echo "start Ossfs Service"
            ;;
        *)
            echo "ignore."
            exit 0
            ;;
esac
##
#MOUNT#

'''
        return init_script_header + '\n'.join(cmds)

    def set_auto_mount_new(self, new_val):

        file_name = '/etc/init.d/ossfs'
        if not os.path.isfile(file_name):
            cmds = [new_val]
        else:
            old_conf = public.readFile(file_name)
            cmds = self._parse_init_script(old_conf)
            cmds.append(new_val)

        new_conf = self._gen_init_script(cmds)
        public.writeFile(file_name, new_conf)

        public.ExecShell('chmod a+x /etc/init.d/ossfs')
        public.ExecShell('chkconfig ossfs on')  # centos
        public.ExecShell('update-rc.d ossfs defaults')  # debian

    def clear_mount_new(self, init_file, cmd, mount_path=None):
        old_conf = public.readFile(init_file)
        cmds = self._parse_init_script(old_conf)
        n_cmds = []
        for item in cmds:
            if item.startswith(cmd) and item.find(mount_path + ' ') > -1:
                continue
            n_cmds.append(item)

        new_conf = self._gen_init_script(n_cmds)
        public.writeFile(init_file, new_conf)

    # def _get_mount_list_from_config(self, get):
    #     mounts = []
    #     conf=[]
    #     try:
    #         with open(self._mount_file) as fp:
    #             conf=json.load(fp)

    #     except Exception as e:
    #         public.print_log(e)
    #         pass
    #     for item in conf:
    #         mlist = item.get('mount_list', [])
    #         public.print_log(mlist)
    #         for mi in mlist:
    #             mounts.append({
    #                 'type': item['type'],
    #                 'bucket_name': mi['bucket_name'],
    #                 'mount_path':  mi['mount_path']
    #             })
    #     return mounts

    def create_bucket(self, get=None):
        """
        @name 创建bucket
        """
        oss_info = self.get_oss_info(get)
        if get:
            if 'bucket_name' not in get or 'region_url' not in get or 'type' not in get or not get.bucket_name or not get.region_url or not get.type: return public.returnMsg(
                False, '错误的参数')
        if 'type' not in oss_info or 'key_info' not in oss_info or 'access_key_id' not in oss_info[
            'key_info'] or 'access_key_secret' not in oss_info['key_info'] or not oss_info['key_info'][
            'access_key_id'] or not oss_info['key_info']['access_key_secret']: return public.returnMsg(False,
                                                                                                       '请配置密钥信息后再尝试创建!')
        import re
        test_str = re.search(r"\W", get.bucket_name)
        if test_str != None:
            return public.returnMsg(False, 'bucket名称包含特殊字符，请重新设置')
        if get.type == 'alioss':
            alioss = alioss_main()
            return alioss.create_bucket(get)
        elif get.type == 'bos':
            bos = bos_main()
            return bos.create_bucket(get)
        elif get.type == 'jdoss':
            jdoss = jdoss_main()
            return jdoss.create_bucket(get)
        elif get.type == 'txcos':
            txcos = txcos_main()
            return txcos.create_bucket(get)
        elif get.type == 'obs':
            obs = obs_main()
            return obs.create_bucket(get)
        elif get.type == 'ks3':
            ks3 = ks3_main()
            return ks3.create_bucket(get)
        elif get.type == 'qiniu':
            qn = qiniu_main()
            return qn.create_bucket(get)

    def get_oss_error(self, oss_type, e):
        """
        @name 取oss错误
        """
        res = '创建失败！{}'.format(e)
        if oss_type == 'alioss':
            if e.args[0] == 409 and 'Code' in e.args[-1] and e.args[-1]['Code'] == 'BucketAlreadyExists':
                res = 'bucket名称已经存在！'
            elif e.args[0] == 400 and 'Code' in e.args[-1] and e.args[-1]['Code'] == 'InvalidBucketName':
                res = 'bucket名称不合法！'
            else:
                return e
        elif oss_type == 'bos':
            if e.args[0].find('baidubce.exception.BceServerError') != -1: res = 'bucket名称不合法！'
        return res

    def get_page(self, data, get):
        """
        @name 取分页
        @return 指定分页数据
        """
        # 包含分页类
        import page
        # 实例化分页类
        page = page.Page()

        info = {}
        info['count'] = len(data)
        info['row'] = 10
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        info['uri'] = {}
        info['return_js'] = ''
        # 获取分页数据
        result = {}
        result['page'] = page.GetPage(info, limit='1,2,3,4,5,8')
        n = 0
        result['data'] = []
        for i in range(info['count']):
            if n >= page.ROW: break
            if i < page.SHIFT: continue
            n += 1
            result['data'].append(data[i])
        return result

    def set_oss_config(self, get):
        """
        @name 设置oss密钥信息
        """
        if not os.path.isdir(os.path.split(self._oss_path)[0]): os.makedirs(self._oss_path)
        if not get.get('access_key_id/str', '') or not get.get('access_key_secret/str', '') or not get.get('type/str',
                                                                                                           ''): return public.returnMsg(
            False, 'access_key_id/access_key_secret/bucket_name/endpoint_url参数不能为空或者不合法！')
        self._access_key_id = get.access_key_id.strip()
        self._access_key_secret = get.access_key_secret.strip()
        oss_obj = self.get_oss_obj(get.type)
        bucket_list = oss_obj.check_connect(self._access_key_id, self._access_key_secret)
        if bucket_list == 0: return public.returnMsg(False, '设置失败！请检查密钥是否正确！')
        add_list = []
        add_dict = {}
        add_dict['type'] = get.type
        add_key_info = {}
        add_key_info['access_key_id'] = self._access_key_id
        add_key_info['access_key_secret'] = self._access_key_secret
        if 'app_id' in get and get.app_id:
            add_key_info['app_id'] = get.app_id
        add_dict['key_info'] = add_key_info
        if os.path.isfile(self._oss_path):
            # conf = []
            try:
                add_list = json.loads(public.readFile(self._oss_path))
            except:
                pass
        is_add = True
        if add_list:
            for i in add_list:
                if 'key_info' not in i: continue
                if 'type' in i and i['type'] == get.type:
                    modify_index = add_list.index(i)
                    is_add = False
                    add_list[modify_index] = add_dict
                    break
        if is_add:
            add_list.append(add_dict)
        public.writeFile(self._oss_path, json.dumps(add_list))
        return public.returnMsg(True, '设置成功!')


class alioss_main(ossfs_main):
    """
    @name 阿里云对象的类
    """

    def __init__(self):
        try:
            conf = json.loads(public.readFile(self._oss_path))
        except:
            conf = []
        if conf:
            for ali_info in conf:
                if 'type' not in ali_info or 'key_info' not in ali_info or 'access_key_id' not in ali_info[
                    'key_info'] or 'access_key_secret' not in ali_info['key_info']: continue
                if ali_info['type'] == 'alioss':
                    self._access_key_id = ali_info['key_info']['access_key_id']
                    self._access_key_secret = ali_info['key_info']['access_key_secret']
                    # self._bucket_name='thisyearbase'

    def authorize(self):
        try:
            client = oss2.Auth(
                self._access_key_id,
                self._access_key_secret
            )
            return client
        except Exception as e:
            print(e)
            raise ("阿里云OSS客户端连接异常, 请检查配置参数是否正确。")

    def create_bucket(self, args):
        get = args
        import oss2
        a = 'https://{}.aliyuncs.com'.format(get.region_url)
        bucket_name = None
        if get: bucket_name = get.bucket_name
        bucket_list = self.get_bucket()
        is_exist = False
        for bucket_i in bucket_list:
            if 'bucket_name' not in bucket_i: continue
            if bucket_name == bucket_i['bucket_name']:
                is_exist = True
                break
        if is_exist: return public.returnMsg(False, '需要创建的存储桶名与现有存储桶名重复，请重新设置存储桶名！')
        try:
            auth = self.authorize()
            bucket = oss2.Bucket(auth, a, bucket_name)
            bucket.create_bucket()
        except Exception as e:
            res = self.get_oss_error('alioss', e)
            return public.returnMsg(False, res)
        return public.returnMsg(True, '创建成功！')

    def check_connect(self, access_key_id, access_key_secret):
        """
        @name 密钥信息能否正常连接
        """
        self._access_key_id = access_key_id
        self._access_key_secret = access_key_secret
        bucket_list = []
        try:
            auth = self.authorize()
            service = oss2.Service(auth, 'oss-cn-beijing.aliyuncs.com')
            buckets = oss2.BucketIterator(service)
            # print('buckets')
            # print(buckets)
            for bucket in buckets:
                if not buckets: continue
                add_value = {}
                if not bucket: continue
                # print(bucket.name)
                # print(bucket.location)
                add_value['bucket_name'] = bucket.name
                add_value['bucket_location'] = bucket.location
                if add_value in bucket_list: continue
                # add_value['bucket_time']==public.format_date(times=bucket.creationDate)
                # add_value['bucket_time']==bucket.time
                bucket_list.append(add_value)
        except:
            bucket_list = 0
        return bucket_list

    def get_bucket(self):
        """
        @name 取存储空间
        """
        bucket_list = []
        # print('1111111')
        try:
            auth = self.authorize()
            service = oss2.Service(auth, 'oss-cn-beijing.aliyuncs.com')
            buckets = oss2.BucketIterator(service)
            print('buckets')
            print(buckets)
            for bucket in buckets:
                if not buckets: continue
                add_value = {}
                if not bucket: continue
                # print(bucket.name)
                # print(bucket.location)
                add_value['bucket_name'] = bucket.name
                add_value['bucket_location'] = bucket.location
                if add_value in bucket_list: continue
                # add_value['bucket_time']==public.format_date(times=bucket.creationDate)
                # add_value['bucket_time']==bucket.time
                bucket_list.append(add_value)
        except:
            pass
        return bucket_list

    def get_endpoint(self, endpoint, bucket):
        auth = self.authorize()
        bucket = oss2.Bucket(auth, endpoint, bucket)
        bucket_info = bucket.get_bucket_info()
        return 'https://' + bucket_info.intranet_endpoint


class bos_main(ossfs_main):
    """
    @name 百度云存储的类
    """

    def __init__(self):
        print(self._access_key_id)
        print(self._access_key_secret)
        try:
            conf = json.loads(public.readFile(self._oss_path))
        except:
            conf = []
        if conf:
            for ali_info in conf:
                if 'type' not in ali_info or 'key_info' not in ali_info or 'access_key_id' not in ali_info[
                    'key_info'] or 'access_key_secret' not in ali_info['key_info']: continue
                if ali_info['type'] == 'bos':
                    print(ali_info)
                    if not self._access_key_id: self._access_key_id = ali_info['key_info']['access_key_id']
                    if not self._access_key_secret: self._access_key_secret = ali_info['key_info']['access_key_secret']
                    # print(self._access_key_id)
                    # print(self._access_key_secret)
                    # self._bucket_name='thisyearbase'

    def authorize(self):
        from baidubce.bce_client_configuration import BceClientConfiguration
        from baidubce.auth.bce_credentials import BceCredentials
        from baidubce.services.bos.bos_client import BosClient
        from baidubce import exception
        from baidubce.services import bos
        from baidubce.services.bos import canned_acl
        if not self._endpoint: self._endpoint = 'http://bj.bcebos.com'
        try:
            config = BceClientConfiguration(
                credentials=BceCredentials(self._access_key_id, self._access_key_secret),
                endpoint=self._endpoint)
            return BosClient(config)
        except Exception as e:
            print(e)
            raise ("百度云BOS客户端连接异常, 请检查配置参数是否正确。")

    def create_bucket(self, args):
        get = args
        import oss2
        self._endpoint = 'http://{}.bcebos.com'.format(get.region_url)
        bucket_name = None
        if get: bucket_name = get.bucket_name
        bucket_list = self.get_bucket()
        is_exist = False
        for bucket_i in bucket_list:
            if 'bucket_name' not in bucket_i: continue
            if bucket_name == bucket_i['bucket_name']:
                is_exist = True
                break
        if is_exist: return public.returnMsg(False, '需要创建的存储桶名与现有存储桶名重复，请重新设置存储桶名！')
        try:
            auth = self.authorize()
            if not auth.does_bucket_exist(bucket_name):
                auth.create_bucket(bucket_name)
            # return True
        except Exception as e:
            res = self.get_oss_error('bos', e)
            return public.returnMsg(False, res)
        return public.returnMsg(True, '创建成功！')

    def check_connect(self, access_key_id, access_key_secret):
        """
        @name 密钥信息能否正常连接
        """
        self._access_key_id = access_key_id
        self._access_key_secret = access_key_secret
        bucket_list = []
        try:
            auth = self.authorize()
            response = auth.list_buckets()
            for bucket in response.buckets:
                if not response.buckets: continue
                add_value = {}
                if not bucket: continue
                print(bucket.name)
                print(bucket.location)
                add_value['bucket_name'] = bucket.name
                add_value['bucket_location'] = bucket.location
                if add_value in bucket_list: continue
                bucket_list.append(add_value)
        except:
            bucket_list = 0
        return bucket_list

    def get_bucket(self):
        """
        @name 取存储空间
        """
        bucket_list = []
        try:
            auth = self.authorize()
            response = auth.list_buckets()
            for bucket in response.buckets:
                if not response.buckets: continue
                add_value = {}
                if not bucket: continue
                # print(bucket.name)
                # print(bucket.location)
                add_value['bucket_name'] = bucket.name
                add_value['bucket_location'] = bucket.location
                if add_value in bucket_list: continue
                # add_value['bucket_time']==public.format_date(times=bucket.creationDate)
                # add_value['bucket_time']==bucket.time
                bucket_list.append(add_value)
        except:
            pass
        return bucket_list


class jdoss_main(ossfs_main):
    """
    @name jdoss的类
    """

    def __init__(self):
        print(self._access_key_id)
        print(self._access_key_secret)
        try:
            conf = json.loads(public.readFile(self._oss_path))
        except:
            conf = []
        if conf:
            for ali_info in conf:
                if 'type' not in ali_info or 'key_info' not in ali_info or 'access_key_id' not in ali_info[
                    'key_info'] or 'access_key_secret' not in ali_info['key_info']: continue
                if ali_info['type'] == 'jdoss':
                    print(ali_info)
                    if not self._access_key_id: self._access_key_id = ali_info['key_info']['access_key_id']
                    if not self._access_key_secret: self._access_key_secret = ali_info['key_info']['access_key_secret']
                    # print(self._access_key_id)
                    # print(self._access_key_secret)
                    # self._bucket_name='thisyearbase'

    def authorize(self):
        import boto3
        if not self._access_key_id or not self._access_key_secret:
            raise (
                "无法连接到京东云存储服务器，请检查["
                "AccessKeyId/AccessKeySecret/Endpoint]设置是否正确!")
        print(self._endpoint)
        if not self._endpoint: self._endpoint = 'https://s3.cn-north-1.jdcloud-oss.com'
        if self._endpoint.find('http') == -1: 'https://' + self._endpoint
        # self._endpoint='https://s3.cn-north-1.jdcloud-oss.com'
        print(self._access_key_id)
        print(self._access_key_secret)
        print(self._endpoint)
        try:
            # 初始化
            return boto3.client(
                's3',
                aws_access_key_id=self._access_key_id,
                aws_secret_access_key=self._access_key_secret,
                # 下面给出一个endpoint_url的例子
                endpoint_url=self._endpoint
            )
        except Exception as e:
            print('11111111')
            print(e)
            raise ("京东云存储客户端连接异常, 请检查配置参数是否正确。")

    def create_bucket(self, args):
        import boto3
        get = args
        # s3 = boto3.resource('s3')
        # bucket = s3.Bucket(get.bucket_name)

        get = args
        import oss2
        # self._endpoint='https://s3.{}.jdcloud-oss.com'.format(get.region_url)
        bucket_name = None
        if get: bucket_name = get.bucket_name
        bucket_list = self.get_bucket()
        is_exist = False
        for bucket_i in bucket_list:
            if 'bucket_name' not in bucket_i: continue
            if bucket_name == bucket_i['bucket_name']:
                is_exist = True
                break
        if is_exist: return public.returnMsg(False, '需要创建的存储桶名与现有存储桶名重复，请重新设置存储桶名！')
        try:
            auth = self.authorize()
            response = auth.create_bucket(

                # ACL='private'|'public-read'|'public-read-write', 分别是私有读写，公有读私有写，公有读写
                ACL='private',
                Bucket=get.bucket_name,  # 这里写新建bucket名称
                CreateBucketConfiguration={
                    'LocationConstraint': get.region_url,
                },  # 地域 如华北-北京 对应 cn-north-1  其他参考“https://docs.jdcloud.com/cn/object-storage-service/oss-endpont-list”
            )

            print(response)
            # return True
        except Exception as e:
            print(e)
            print(type(e))
            e = str(e)
            if e.find('The specified bucket is not valid.') != -1 or e.find('BucketAlreadyExists') != -1 or e.find(
                    'The requested bucket name is not available.') != -1:
                # res=self.get_oss_error(e)
                return public.returnMsg(False, 'bucket名称不合法！')
            # return  public.returnMsg(False, 'bucket名称不合法！')
        return public.returnMsg(True, '创建成功！')

    def check_connect(self, access_key_id, access_key_secret):
        """
        @name 密钥信息能否正常连接
        """
        self._access_key_id = access_key_id
        self._access_key_secret = access_key_secret
        bucket_list = []
        region_list = ['cn-north-1', 'cn-south-1', 'cn-east-1', 'cn-east-2']
        for region in region_list:
            self._endpoint = 'https://s3.{}.jdcloud-oss.com'.format(region)
            try:
                import datetime
                auth = self.authorize()
                response = auth.list_buckets()
                print(response)
                print(type(response))
                print(response['Buckets'])
                # bucket_list = response
                # return public.returnMsg(True, response)
                for bucket in response['Buckets']:
                    if not response['Buckets']: continue
                    add_value = {}
                    if not bucket: continue
                    add_value['bucket_name'] = bucket['Name']
                    add_value['bucket_location'] = region
                    if add_value in bucket_list: continue
                    # add_value['bucket_time']==public.format_date(times=bucket.creationDate)
                    # add_value['bucket_time']==bucket.time
                    bucket_list.append(add_value)
            except:
                bucket_list = 0
                break
        return bucket_list

    def get_bucket(self):
        """
        @name 取存储空间
        """
        bucket_list = []
        region_list = ['cn-north-1', 'cn-south-1', 'cn-east-1', 'cn-east-2']
        for region in region_list:
            self._endpoint = 'https://s3.{}.jdcloud-oss.com'.format(region)
            try:
                import datetime
                auth = self.authorize()
                response = auth.list_buckets()
                # print(response)
                # print(type(response))
                # print(response['Buckets'])
                # bucket_list = response
                # return public.returnMsg(True, response)
                for bucket in response['Buckets']:
                    if not response['Buckets']: continue
                    add_value = {}
                    if not bucket: continue
                    add_value['bucket_name'] = bucket['Name']
                    add_value['bucket_location'] = region
                    if add_value in bucket_list: continue
                    # add_value['bucket_time']==public.format_date(times=bucket.creationDate)
                    # add_value['bucket_time']==bucket.time
                    bucket_list.append(add_value)
            except:
                pass
        return bucket_list

    def get_endpoint(self, endpoint: str, bucket):
        intranet_endpoint = endpoint.replace('.cn', '-internal.cn')
        return intranet_endpoint


class txcos_main(ossfs_main):
    """
    @name 腾讯云对象的类
    """

    def __init__(self):
        try:
            conf = json.loads(public.readFile(self._oss_path))
        except:
            conf = []
        if conf:
            for ali_info in conf:
                if 'type' not in ali_info or 'key_info' not in ali_info or 'access_key_id' not in ali_info[
                    'key_info'] or 'access_key_secret' not in ali_info['key_info']: continue
                if ali_info['type'] == 'txcos':
                    self._access_key_id = ali_info['key_info']['access_key_id']
                    self._access_key_secret = ali_info['key_info']['access_key_secret']
                if 'app_id' in ali_info['key_info']:
                    self._app_id = ali_info['key_info']['app_id']

    def authorize(self, endpoint=None):
        if not self._endpoint: self._endpoint = 'ap-nanjing'
        if endpoint: self._endpoint = endpoint
        try:
            from qcloud_cos import CosConfig, CosS3Client
            config = CosConfig(
                Region=self._endpoint,
                Secret_id=self._access_key_id,
                Secret_key=self._access_key_secret,
                Token=None,
                Scheme='https')
            part_retry = 10
            return CosS3Client(config, retry=part_retry)
        except Exception as e:
            raise ("腾讯COS客户端连接异常, 请检查配置参数是否正确。")

    def create_bucket(self, args):
        get = args
        self._endpoint = get.region_url
        if not self._app_id: self._app_id = '1259325357'
        if get: bucket_name = '{}-{}'.format(get.bucket_name, self._app_id)
        bucket_list = self.get_bucket()
        is_exist = False
        for bucket_i in bucket_list:
            if 'bucket_name' not in bucket_i: continue
            if bucket_name == bucket_i['bucket_name']:
                is_exist = True
                break
        if is_exist: return public.returnMsg(False, '需要创建的存储桶名与现有存储桶名重复，请重新设置存储桶名！')
        try:
            auth = self.authorize(get.region_url)
            response = auth.create_bucket(
                Bucket=bucket_name,
                ACL='private'
            )
        except Exception as e:
            # res=self.get_oss_error(e)
            return public.returnMsg(False, e)
        return public.returnMsg(True, '创建成功！')

    def check_connect(self, access_key_id, access_key_secret):
        """
        @name 密钥信息能否正常连接
        """
        self._access_key_id = access_key_id
        self._access_key_secret = access_key_secret
        bucket_list = []
        try:
            auth = self.authorize()
            buckets = auth.list_buckets()
            print(buckets)
            for bucket in buckets['Buckets']['Bucket']:
                if not buckets['Buckets']: continue
                add_value = {}
                if 'Name' not in bucket or 'Location' not in bucket: continue
                add_value['bucket_name'] = bucket['Name']
                add_value['bucket_location'] = bucket['Location']
                if add_value in bucket_list: continue
                # add_value['bucket_time']==public.format_date(times=bucket.creationDate)
                # add_value['bucket_time']==bucket.time
                bucket_list.append(add_value)
        except:
            bucket_list = 0
        return bucket_list

    def get_bucket(self):
        """
        @name 取存储空间
        """
        bucket_list = []
        try:
            auth = self.authorize()
            buckets = auth.list_buckets()
            # print(buckets)
            for bucket in buckets['Buckets']['Bucket']:
                if not buckets['Buckets']: continue
                add_value = {}
                if 'Name' not in bucket or 'Location' not in bucket: continue
                add_value['bucket_name'] = bucket['Name']
                add_value['bucket_location'] = bucket['Location']
                if add_value in bucket_list: continue
                # add_value['bucket_time']==public.format_date(times=bucket.creationDate)
                # add_value['bucket_time']==bucket.time
                bucket_list.append(add_value)
        except:
            pass
        return bucket_list

    def clear_mount(self, file_name, check_str, is_passwd=False, is_umount=False):
        """
        @name 清除/etc/passwd-ossfs文件记录
        """
        with open(file_name, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(file_name, "w", encoding="utf-8") as f_w:
            for line in lines:
                if is_passwd and line.split(':')[0] == check_str: continue
                if is_umount and line[0] != '#' and len(line.split()) > 4 and line.split()[1] == check_str: continue
                f_w.write(line)
        self.remove_blank_lines(self._mount_file)

    def get_endpoint(self, endpoint, bucket):
        return endpoint


class obs_main(ossfs_main):
    """
    @name 华为云对象的类
    """

    def __init__(self):
        try:
            conf = json.loads(public.readFile(self._oss_path))
        except:
            conf = []
        if conf:
            for ali_info in conf:
                if 'type' not in ali_info or 'key_info' not in ali_info or 'access_key_id' not in ali_info[
                    'key_info'] or 'access_key_secret' not in ali_info['key_info']: continue
                if ali_info['type'] == 'obs':
                    self._access_key_id = ali_info['key_info']['access_key_id']
                    self._access_key_secret = ali_info['key_info']['access_key_secret']
                    # self._bucket_name='thisyearbase'

    def authorize(self):
        if not self._endpoint: self._endpoint = 'https://obs.cn-north-1.myhuaweicloud.com'
        from obs import ObsClient
        from obs import CreateBucketHeader
        if not self._access_key_id or not self._access_key_secret or not self._endpoint:
            raise (
                "无法连接到华为云OBS服务器，请检查["
                "AccessKeyId/AccessKeySecret/Endpoint]设置是否正确!")
        try:
            # 初始化
            # print(self._access_key_id)
            # print(self._access_key_secret)
            # print(self._endpoint)
            return ObsClient(
                access_key_id=self._access_key_id,
                secret_access_key=self._access_key_secret,
                server=self._endpoint,
            )
        except Exception as e:
            print(e)
            raise ("华为云OBS客户端连接异常, 请检查配置参数是否正确。")

    def create_bucket(self, args):
        get = args
        import oss2
        a = 'https://{}.aliyuncs.com'.format(get.region_url)
        bucket_name = None
        if get: bucket_name = get.bucket_name
        bucket_list = self.get_bucket()
        is_exist = False
        for bucket_i in bucket_list:
            if 'bucket_name' not in bucket_i: continue
            if bucket_name == bucket_i['bucket_name']:
                is_exist = True
                break
        if is_exist: return public.returnMsg(False, '需要创建的存储桶名与现有存储桶名重复，请重新设置存储桶名！')
        try:
            auth = self.authorize()
            resp = auth.createBucket(bucketName=bucket_name, location=get.region_url)
            if resp.status < 300:
                print('requestId:', resp.requestId)
            else:
                print('errorCode:', resp.errorCode)
                print('errorMessage:', resp.errorMessage)
                print(resp.status)
                print(resp)
                # return public.returnMsg(False, resp.errorMessage)
                print(type(resp.errorMessage))
            # if resp.errorMessage=='The specified bucket is not valid.':return public.returnMsg(False, 'bucket名称不合法！')
            if resp.status == 409 and resp.reason == 'Conflict': return public.returnMsg(False, 'bucket名称不合法！')
            # bucket = oss2.Bucket(autpublic.returnMsg(False, '需要创建的存储桶名与现有存储桶名重复，请重新设置存储桶名！')h,a,bucket_name)
            # bucket.create_bucket()
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return public.returnMsg(False, e)
        return public.returnMsg(True, '创建成功！')

    def check_connect(self, access_key_id, access_key_secret):
        """
        @name 密钥信息能否正常连接
        """
        self._access_key_id = access_key_id
        self._access_key_secret = access_key_secret
        bucket_list = []
        try:
            auth = self.authorize()
            resp = auth.listBuckets(True)
            for bucket in resp.body.buckets:
                if not resp.body.buckets: continue
                add_value = {}
                if not bucket: continue
                # print(bucket.name)
                # print(bucket.location)
                add_value['bucket_name'] = bucket.name
                add_value['bucket_location'] = bucket.location
                if add_value in bucket_list: continue
                # add_value['bucket_time']==public.format_date(times=bucket.creationDate)
                # add_value['bucket_time']==bucket.time
                # print(add_value)
                bucket_list.append(add_value)
        except:
            bucket_list = 0
        return bucket_list

    def get_bucket(self):
        """
        @name 取存储空间
        """
        bucket_list = []
        try:
            auth = self.authorize()
            resp = auth.listBuckets(True)
            for bucket in resp.body.buckets:
                if not resp.body.buckets: continue
                add_value = {}
                if not bucket: continue
                # print(bucket.name)
                # print(bucket.location)
                add_value['bucket_name'] = bucket.name
                add_value['bucket_location'] = bucket.location
                if add_value in bucket_list: continue
                # add_value['bucket_time']==public.format_date(times=bucket.creationDate)
                # add_value['bucket_time']==bucket.time
                # print(add_value)
                bucket_list.append(add_value)
        except:
            pass
        return bucket_list

    def get_endpoint(self, endpoint, bucket):
        return endpoint


class ks3_main(ossfs_main):
    """
    @name 金山云对象的类
    """

    def __init__(self):
        try:
            conf = json.loads(public.readFile(self._oss_path))
        except:
            conf = []
        if conf:
            for ali_info in conf:
                if 'type' not in ali_info or 'key_info' not in ali_info or 'access_key_id' not in ali_info[
                    'key_info'] or 'access_key_secret' not in ali_info['key_info']: continue
                if ali_info['type'] == 'ks3':
                    self._access_key_id = ali_info['key_info']['access_key_id']
                    self._access_key_secret = ali_info['key_info']['access_key_secret']
                    # self._bucket_name='thisyearbase'

    def authorize(self):
        if not self._endpoint: self._endpoint = 'ks3-cn-beijing.ksyuncs.com'
        if self._endpoint.find('http://') != -1: self._endpoint.replace('http://', '')
        if self._endpoint.find('https://') != -1: self._endpoint.replace('https://', '')

        from ks3.connection import Connection
        if not self._access_key_id or not self._access_key_secret or not self._endpoint:
            print('33333333')
            raise (
                "无法连接到金山云服务器，请检查["
                "AccessKeyId/AccessKeySecret/Endpoint]设置是否正确!")
        try:
            # 初始化
            # print(self._access_key_id)
            # print(self._access_key_secret)
            # print(self._endpoint)
            return Connection(
                self._access_key_id,
                self._access_key_secret,
                host=self._endpoint,
                # is_secure=True,
                # domain_mode=True
            )
        except Exception as e:
            # return None
            print(e)
            raise ("金山云客户端连接异常, 请检查配置参数是否正确。")

    def create_bucket(self, args):
        get = args
        self._endpoint = 'ks3-cn-{}.ksyuncs.com'.format(get.region_url)
        bucket_list = self.get_bucket()
        is_exist = False
        for bucket_i in bucket_list:
            if 'bucket_name' not in bucket_i: continue
            if get.bucket_name == bucket_i['bucket_name']:
                is_exist = True
                break
        if is_exist: return public.returnMsg(False, '需要创建的存储桶名与现有存储桶名重复，请重新设置存储桶名！')
        try:
            auth = self.authorize()
            auth.create_bucket(get.bucket_name, policy='private')
            # if resp.status == 409:
            #     return  public.returnMsg(False, '存储桶名有冲突')
        except Exception as e:
            print(e)
            e = str(e)
            print(type(e))
            if e.find('BucketAlreadyExists') != -1:
                return public.returnMsg(False, "bucket名称不合法！")
        return public.returnMsg(True, '创建成功！')

    def check_connect(self, access_key_id, access_key_secret):
        """
        @name 密钥信息能否正常连接
        """
        self._access_key_id = access_key_id
        self._access_key_secret = access_key_secret
        bucket_list = []
        try:
            auth = self.authorize()
            buckets = auth.get_all_buckets()
            for bucket in buckets:
                if not buckets: break
                add_value = {}
                if not bucket: continue
                add_value['bucket_name'] = bucket.name
                add_value['bucket_location'] = auth.get_bucket_location(bucket.name).lower()
                if add_value in bucket_list: continue
                # add_value['bucket_time']==public.format_date(times=bucket.creationDate)
                # add_value['bucket_time']==bucket.time
                # print(add_value)
                bucket_list.append(add_value)
        except:
            bucket_list = 0
        return bucket_list

    def get_bucket(self):
        """
        @name 取存储空间
        """
        bucket_list = []
        try:
            auth = self.authorize()
            buckets = auth.get_all_buckets()
            for bucket in buckets:
                if not buckets: break
                add_value = {}
                if not bucket: continue
                add_value['bucket_name'] = bucket.name
                add_value['bucket_location'] = auth.get_bucket_location(bucket.name).lower()
                if add_value in bucket_list: continue
                # add_value['bucket_time']==public.format_date(times=bucket.creationDate)
                # add_value['bucket_time']==bucket.time
                # print(add_value)
                bucket_list.append(add_value)
        except:
            pass
        return bucket_list

    def get_endpoint(self, endpoint: str, bucket):
        return endpoint.replace('.ksyuncs.com', '-internal.ksyuncs.com')


class qiniu_main(ossfs_main):
    name = 'qiniu'

    # https://developer.qiniu.com/kodo/4088/s3-access-domainname
    def __init__(self):
        print(self._access_key_id)
        print(self._access_key_secret)
        try:
            conf = json.loads(public.readFile(self._oss_path))
        except:
            conf = []
        if conf:
            for item in conf:
                if 'type' not in item or 'key_info' not in item or 'access_key_id' not in item[
                    'key_info'] or 'access_key_secret' not in item['key_info']: continue
                if item['type'] == self.name:
                    if not self._access_key_id: self._access_key_id = item['key_info']['access_key_id']
                    if not self._access_key_secret: self._access_key_secret = item['key_info']['access_key_secret']

    def authorize(self):
        import boto3
        if not self._access_key_id or not self._access_key_secret:
            raise (
                "无法连接到七牛云存储服务器，请检查["
                "AccessKeyId/AccessKeySecret/Endpoint]设置是否正确!")

        if not self._endpoint: self._endpoint = 'https://s3-cn-east-1.qiniucs.com'
        if self._endpoint.find('http') == -1: 'https://' + self._endpoint

        try:
            # 初始化
            return boto3.client(
                's3',
                aws_access_key_id=self._access_key_id,
                aws_secret_access_key=self._access_key_secret,
                endpoint_url=self._endpoint
            )
        except Exception as e:
            print(e)
            raise ("七牛云存储客户端连接异常, 请检查配置参数是否正确。")

    def create_bucket(self, args):
        import boto3
        get = args

        bucket_name = None
        if get: bucket_name = get.bucket_name
        bucket_list = self.get_bucket()
        is_exist = False
        for bucket_i in bucket_list:
            if 'bucket_name' not in bucket_i: continue
            if bucket_name == bucket_i['bucket_name']:
                is_exist = True
                break
        if is_exist: return public.returnMsg(False, '需要创建的存储桶名与现有存储桶名重复，请重新设置存储桶名！')
        try:
            auth = self.authorize()
            response = auth.create_bucket(
                # ACL='private'|'public-read'|'public-read-write', 分别是私有读写，公有读私有写，公有读写
                ACL='private',
                Bucket=get.bucket_name,  # 这里写新建bucket名称
                CreateBucketConfiguration={
                    'LocationConstraint': get.region_url,
                },  # 地域 如华北-北京
            )
        except Exception as e:
            print(e)
            e = str(e)
            if e.find('The specified bucket is not valid.') != -1 or e.find('BucketAlreadyExists') != -1 or e.find(
                    'The requested bucket name is not available.') != -1:
                # res=self.get_oss_error(e)
                return public.returnMsg(False, 'bucket名称不合法！')
            return public.returnMsg(False, 'bucket创建失败,请稍后重试!')

        return public.returnMsg(True, '创建成功！')

    def check_connect(self, access_key_id, access_key_secret):
        """
        @name 密钥信息能否正常连接
        """
        self._access_key_id = access_key_id
        self._access_key_secret = access_key_secret
        try:
            auth = self.authorize()
            buckets = auth.list_buckets()
        except:
            return 0
        return buckets

    def get_bucket(self):
        bucket_list = []

        self._endpoint = "https://s3-cn-east-1.qiniucs.com"
        try:
            auth = self.authorize()
            response = auth.list_buckets()

            for bucket in response['Buckets']:
                bucket_name = bucket['Name']
                region = auth.get_bucket_location(Bucket=bucket_name)['LocationConstraint']

                bucket_list.append({
                    'bucket_name': bucket_name,
                    'bucket_location': region
                })
        except:
            pass
        return bucket_list

    def get_endpoint(self, endpoint, bucket):
        return endpoint
