#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: 邹浩文 <627622230@qq.com>
# Maintainer:hezhihong<272267659@qq.com>
#-------------------------------------------------------------------
"""
author: haowen
date: 2020/5/13 15:56
"""
from __future__ import print_function, absolute_import
import sys

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
import os

from boto3 import client

from s3lib.osclient.osclient import OSClient
import public


class COSClient(OSClient, object):
    _name = "aws_s3"
    _title = "AWS S3对象存储"
    __error_count = 0
    __secret_id = None
    __secret_key =None

    __bucket_name = None
    __oss_path = None
    __backup_path = 'bt_backup/'
    __error_msg = "ERROR: 无法连接AWS S3对象存储 !"
    reload = False

    def __init__(self, config_file=None):
        super(COSClient, self).__init__(config_file)
        self.init_config()

    def init_config(self):
        _auth = self.auth
        try:
            self.auth = None
            keys = self.get_config()
            self.__secret_id = keys[0].strip()
            self.__secret_key = keys[1].strip()
            # self.__region = keys[2]
            self.__bucket_name = keys[2].strip()

            self.authorize()

            # 设置存储路径和兼容旧版本
            if len(keys) == 4:
                bp = keys[3].strip()
                if bp != "/":
                    bp = self.get_path(bp)
                if bp:
                    self.__backup_path = bp
                else:
                    self.__backup_path = self.default_backup_path
            else:
                self.__backup_path = self.default_backup_path

        except:
            print(self.__error_msg)
            self.auth = _auth

    def set_config(self, conf):
        path = self.get_config_file()
        public.writeFile(path, conf)
        self.reload = True
        self.init_config()
        return True

    def get_config(self):
        path = self.get_config_file()
        default_config = ['', '', '', '', self.default_backup_path]
        if not os.path.exists(path): return default_config;

        conf = public.readFile(path)
        if not conf: return default_config
        result = conf.split(self.CONFIG_SEPARATOR)
        if len(result) < 3: result.append(self.default_backup_path);
        if not result[3]: result[3] = self.default_backup_path;
        return result

    def re_auth(self):
        if self.auth is None or self.reload:
            self.reload = False
            return True

    def build_auth(self):
        config = client(
            's3',
            aws_access_key_id=self.__secret_id,
            aws_secret_access_key=self.__secret_key,
        )
        return config

    def get_list(self, path="/"):
        try:
            data = []
            path = self.get_path(path)
            client = self.authorize()
            max_keys = 1000
            objects = client.list_objects_v2(
                Bucket=self.__bucket_name,
                MaxKeys=max_keys,
                Delimiter=self.delimiter,
                Prefix=path)
            if 'Contents' in objects:
                for b in objects['Contents']:
                    tmp = {}
                    b['Key'] = b['Key'].replace(path, '')
                    if not b['Key']: continue
                    tmp['name'] = b['Key']
                    tmp['size'] = b['Size']
                    tmp['type'] = b['StorageClass']
                    tmp['download'] = ""
                    tmp['time'] = b['LastModified'].timestamp()
                    # tmp['time'] = ""
                    data.append(tmp)

            if 'CommonPrefixes' in objects:
                for i in objects['CommonPrefixes']:
                    if not i['Prefix']: continue
                    dir_dir = i['Prefix'].split('/')[-2] + '/'
                    tmp = {}
                    tmp["name"] = dir_dir
                    tmp["type"] = None
                    data.append(tmp)

            mlist = {}
            mlist['path'] = path
            mlist['list'] = data
            return mlist
        except Exception as e:
            return public.returnMsg(False, '密钥验证失败！')

    def multipart_upload(self,local_file_name,object_name=None):
        """
        分段上传
        :param local_file_name:
        :param object_name:
        :return:
        """
        if int(os.path.getsize(local_file_name)) <= 102400000:
            return self.upload_file1(local_file_name,object_name)
        if object_name is None:
            temp_file_name = os.path.split(local_file_name)[1]
            object_name = self.backup_dir + temp_file_name

        client = self.authorize()
        part_size = 10 * 1024 * 1024
        result = client.create_multipart_upload(Bucket=self.__bucket_name, Key=object_name)
        upload_id = result["UploadId"]
        index = 0
        with open(local_file_name, "rb") as fp:
            while True:
                index += 1
                part = fp.read(part_size)
                if not part:
                    break
                print("上传分段 {}\n大小 {}".format(index, part_size))
                client.upload_part(Bucket=self.__bucket_name, Key=object_name, PartNumber=index, UploadId=upload_id, Body=part)
                # print("上传成功")
        rParts = client.list_parts(Bucket=self.__bucket_name, Key=object_name, UploadId=upload_id)["Parts"]

        partETags = []
        for part in rParts:
            partETags.append({"PartNumber": part['PartNumber'], "ETag": part['ETag']})
        print(partETags)
        client.complete_multipart_upload(Bucket=self.__bucket_name, Key=object_name, UploadId=upload_id,
                                         MultipartUpload={'Parts': partETags})
        # print("上传成功")
        return True

    def upload_file1(self,local_file_name,object_name=None):
        if object_name is None:
            temp_file_name = os.path.split(local_file_name)[1]
            object_name = self.backup_dir + temp_file_name
        client = self.authorize()
        client.upload_file(
            Bucket=self.__bucket_name,
            Filename=local_file_name,
            Key=object_name
        )
        # print("上传成功")
        return True

    def delete_object_by_os(self, object_name):
        """删除对象"""

        # TODO(Linxiao) 支持目录删除
        client = self.authorize()
        response = client.delete_object(
            Bucket=self.__bucket_name,
            Key=object_name,
        )
        return response is not None

    def download_file(self, object_name,local_file):
        # 连接OSS服务器
        client = self.authorize()
        try:
            with open(local_file,'wb') as f:
                client.download_fileobj(
                    self.__bucket_name,
                    object_name,
                    f
                )
        except:
            print(self.__error_msg, public.get_error_info())
            
    # def get_lib(self):
    #     import json
    #     list = {
    #         "name": "AWS S3",
    #         "type": "Cron job",
    #         "ps": "Package and backup website or database to AWS S3, <a class='link' "
    #               "href='https://portal.qiniu.com/signup?code=3liz7nbopjd5e' "
    #               "target='_blank'>点击申请</a>",
    #         "status": 'false',
    #         "opt": "aws_s3",
    #         "module": "boto3",
    #         "script": "aws_s3",
    #         "help": "https://www.bt.cn/bbs/thread-17442-1-1.html",
    #         "SecretId": "SecretId|请输入SecretId|AWS S3的SecretId",
    #         "SecretKey": "SecretKey|请输入SecretKey|AWS S3 的SecretKey",
    #         "region": "存储地区|请输入对象存储地区|例如 ap-chengdu",
    #         "Bucket": "存储名称|请输入绑定的存储名称",
    #         "check": ["/usr/lib/python2.6/site-packages/boto3/__init__.py",
    #                   "/usr/lib/python2.7/site-packages/boto3/__init__.py",
    #                   "/www/server/panel/pyenv/lib/python3.7/site-packages/boto3/__init__.py"]
    #     }
    #     lib = '/www/server/panel/data/libList.conf'
    #     lib_dic = json.loads(public.readFile(lib))
    #     for i in lib_dic:
    #         if list['name'] in i['name']:
    #             return True
    #         else:
    #             pass
    #     lib_dic.append(list)
    #     public.writeFile(lib, json.dumps(lib_dic))
    #     return lib_dic
