#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: zhwen <zhw@bt.cn>
# Maintainer:hezhihong<272267659@qq.com>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# AWSS3存储
# -------------------------------------------------------------------
import sys

from s3lib.osclient.itools import switch_environment

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')

switch_environment()

from s3lib.client.aws_s3 import COSClient
import public

# 腾讯云oss 的类
class aws_s3_main:
    __client = None

    def __init__(self):
        self.get_lib()

    @property
    def client(self):
        if self.__client:
            return self.__client
        self.__client = COSClient()
        return self.__client

    def get_config(self, get):
        return self.client.get_config()

    def set_config(self, get):
        try:
            secret_id = get.secret_id.strip()
            secret_key = get.secret_key.strip()
            bucket_name = get.Bucket.strip()
            # region = get.region.strip()
            backup_path = get.backup_path.strip()
            if not backup_path:
                backup_path = 'bt_backup/'
            # 验证前端输入
            values = [secret_id,
                      secret_key,
                      bucket_name,
                      backup_path]
            for v in values:
                if not v:
                    return public.returnMsg(False, 'API资料校验失败，请核实!')

            conf = secret_id + '|' + \
                   secret_key + '|' + \
                   bucket_name + '|' + \
                   backup_path

            if self.client.set_config(conf):
                if self.client.get_list():
                    return public.returnMsg(True, '设置成功!')
            return public.returnMsg(False, 'API资料校验失败，请核实!')
        except Exception as e:
            return public.returnMsg(False, 'API资料校验失败，请核实!')

    # 上传文件
    def upload_file(self, filename):
        return self.client.resumable_upload(filename)

    # 创建目录
    # def create_dir(self, get):
    #     path = get.path + get.dirname;
    #     if self.client.create_dir(path):
    #         return public.returnMsg(True, '目录{}创建成功!'.format(path));
    #     else:
    #         return public.returnMsg(False, "创建失败！")

    # 取回文件列表
    def get_list(self, get):
        return self.client.get_list(get.path)

    # 删除文件
    def delete_file(self, get):
        try:
            filename = get.filename
            path = get.path
            if path != "/":
                if path[0] == "/":
                    path = path[1:]

            if path[-1] != "/":
                file_name = path + "/" + filename
            else:
                file_name = path + filename

            if file_name[-1] == "/":
                return public.returnMsg(False, "暂时不支持目录删除！")

            if file_name[:1] == "/":
                file_name = file_name[1:]
            if self.client.delete_object(file_name):
                return public.returnMsg(True, '删除成功')
            return public.returnMsg(False, '文件{}删除失败, path:{}'.format(file_name,
                                                                      get.path))
        except:
            return public.get_error_info()

    def download_file(self, get):
        # 连接OSS服务器
        print('开始下载文件')
        self.client.download_file(get.object_name,get.local_file)
        print('下载成功')

    def get_lib(self):
        import json
        info = {
            "name": "AWS S3对象存储",
            "type": "计划任务",
            "ps": "将网站或数据库打包备份到腾讯云COS对象存储空间,, <a class='link' "
                  "href='https://portal.qiniu.com/signup?code=3liz7nbopjd5e' "
                  "target='_blank'>点击申请</a>",
            "status": 'false',
            "opt": "aws_s3",
            "module": "boto3",
            "script": "aws_s3",
            "help": "https://www.bt.cn/bbs/thread-17442-1-1.html",
            "SecretId": "SecretId|请输入SecretId|AWS S3的SecretId",
            "SecretKey": "SecretKey|请输入SecretKey|AWS S3 的SecretKey",
            "region": "存储地区|请输入对象存储地区|例如 ap-chengdu",
            "Bucket": "存储名称|请输入绑定的存储名称",
            "check": ["/usr/lib/python2.6/site-packages/boto3/__init__.py",
                      "/usr/lib/python2.7/site-packages/boto3/__init__.py",
                      "/www/server/panel/pyenv/lib/python3.7/site-packages/boto3/__init__.py"]
        }
        lib = '/www/server/panel/data/libList.conf'
        lib_dic = json.loads(public.readFile(lib))
        for i in lib_dic:
            if info['name'] in i['name']:
                return True
            else:
                pass
        lib_dic.append(info)
        public.writeFile(lib, json.dumps(lib_dic))
        return lib_dic


if __name__ == "__main__":
    import json

    import panelBackup

    new_version = True if panelBackup._VERSION >= 1.2 else False
    if not new_version:
        data = None
        client = COSClient()
        type = sys.argv[1]
        if type == 'site':
            if sys.argv[2] == 'ALL':
                client.backupSiteAll(sys.argv[3])
            else:
                client.backupSite(sys.argv[2], sys.argv[3])
            exit()
        elif type == 'database':
            if sys.argv[2] == 'ALL':
                client.backupDatabaseAll(sys.argv[3])
            else:
                client.backupDatabase(sys.argv[2], sys.argv[3])
            exit()
        elif type == 'path':
            client.backupPath(sys.argv[2], sys.argv[3])
        elif type == 'upload':
            data = client.upload_file(sys.argv[2])
        elif type == 'download':
            data = client.generate_download_url(sys.argv[2])
        elif type == 'get':
            data = client.get_object_info(sys.argv[2])
        elif type == 'list':
            data = client.get_list("/")
        elif type == 'delete_file':
            data = client.delete_file(sys.argv[2])
        elif type == 'lib':
            data = client.get_lib()
        else:
            data = 'ERROR: 参数不正确!'
    else:
        client = COSClient()
        client.execute_by_comandline(sys.argv)
