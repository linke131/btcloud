#!/usr/bin/python
# coding: utf-8
# Date 2023/7/19
import os,time,sys
os.chdir('/www/server/panel')
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import public,re

__plugin_path = "/www/server/panel/plugin/security_notice/"
__php_path = "/www/server/php/"
__disable_php = ['52','00',None]
vfs = {
    '52': '/www/server/php/52/lib/php/extensions/no-debug-non-zts-20060613',
    '53': '/www/server/php/53/lib/php/extensions/no-debug-non-zts-20090626',
    '54': '/www/server/php/54/lib/php/extensions/no-debug-non-zts-20100525',
    '55': '/www/server/php/55/lib/php/extensions/no-debug-non-zts-20121212',
    '56': '/www/server/php/56/lib/php/extensions/no-debug-non-zts-20131226',
    '70': '/www/server/php/70/lib/php/extensions/no-debug-non-zts-20151012',
    '71': '/www/server/php/71/lib/php/extensions/no-debug-non-zts-20160303',
    '72': '/www/server/php/72/lib/php/extensions/no-debug-non-zts-20170718',
    '73': '/www/server/php/73/lib/php/extensions/no-debug-non-zts-20180731',
    '74': '/www/server/php/74/lib/php/extensions/no-debug-non-zts-20190902',
    '80': '/www/server/php/80/lib/php/extensions/no-debug-non-zts-20200930',
    '81': '/www/server/php/81/lib/php/extensions/no-debug-non-zts-20210902'
}


def get_filter_so(v):

    if v in vfs.keys():
        if not os.path.exists(vfs[v]):
            os.makedirs(vfs[v])
        return vfs[v] + '/security_notice.so'
    return None


def get_php_versions():
    data = []
    for php_version in os.listdir(__php_path):
        if php_version in __disable_php: continue
        php_path = os.path.join(__php_path, php_version)
        php_ini = os.path.join(php_path, 'etc/php.ini')
        if not os.path.exists(php_ini): continue
        filter_so = get_filter_so(php_version)
        if not filter_so: continue
        php_v = public.readFile(os.path.join(php_path, 'version_check.pl'))
        if not php_v:
            php_v = php_version
        php_info = {
            "version": php_v,
            "v": php_version,
        }
        # 判断是否安装
        if not os.path.exists(filter_so):
            php_info['state'] = -1
        else:
            # 是否加载
            php_ini_conf = public.readFile(php_ini)
            php_info['state'] = 1
            if php_ini_conf.find('security_notice.so') == -1:
                php_info['state'] = 0
            if re.search(r";\s*extension\s*=\s*security_notice.so", php_ini_conf):
                php_info['state'] = 0
        php_info['site_count'] = 0
        data.append(php_info)
    return sorted(data, key=lambda x: x['version'], reverse=True)

for i in get_php_versions():
    if i['state']:
        path=vfs[i['v']]+"/security_notice.so"
        if os.path.exists(path):
            #获取文件的md5
            md5=public.FileMd5(path)
            #获取当前目录下的文件的md5
            md5_1=public.FileMd5(__plugin_path+"modules/security_notice_%s.so"%i['v'])
            if md5!=md5_1:
                public.ExecShell("\cp -arf {} {} && chmod +x {}".format(__plugin_path+"modules/security_notice_%s.so"%i['v'], path, path))
                #重启php
                public.phpReload(i['v'])
                print("%s版本的security_notice.so已更新"%i['version'])
        else:
            public.ExecShell(
                "\cp -arf {} {} && chmod +x {}".format(__plugin_path + "modules/security_notice_%s.so" % i['v'], path,
                                                       path))
            # 重启php
            public.phpReload(i['v'])
            print("%s版本的security_notice.so已更新" % i['version'])