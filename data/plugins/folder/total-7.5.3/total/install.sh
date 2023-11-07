#!/bin/bash
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 网站监控报表安装脚本
# -------------------------------------------------------------------
# 求助地址：https://www.bt.cn/bbs
# -------------------------------------------------------------------

PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

pluginPath=/www/server/panel/plugin/total
total_path=/www/server/total

Install_total() {
    public_file=/www/server/panel/install/public.sh
    grep "English" /www/server/panel/config/config.json
    if [ "$?" -ne 0 ]; then
        public_file=/www/server/panel/install/public.sh
        if [ ! -f $public_file ]; then
            wget -O $public_file https://download.bt.cn/install/public.sh -T 5
        fi
        . $public_file
        download_Url=$NODE_URL
    else
        download_Url="https://node.aapanel.com"
    fi
    echo $download_Url

    /www/server/panel/pyenv/bin/python3 ${pluginPath}/total_install.py ${download_Url}
}

Uninstall_total() {
    if [ -f /etc/init.d/httpd ]; then
        if [ -f $total_path/uninstall.lua ]; then
            lua $total_path/uninstall.lua
        fi
    fi

    if hash btpython 2>/dev/null; then
        btpython $pluginPath/total_task.py remove
    else
        python $pluginPath/total_task.py remove
    fi

    chkconfig --level 2345 bt_total_init off

    cd /tmp
    rm -rf $total_path
    rm -f /www/server/panel/vhost/apache/total.conf
    rm -f /www/server/panel/vhost/nginx/total.conf
    rm -rf $pluginPath

    rm -f /etc/init.d/bt_total_init
    rm -f /usr/bin/bt_total_init

    if [ -f /etc/init.d/httpd ]; then
        if [ ! -d /www/server/panel/plugin/btwaf_httpd ]; then
            rm -f /www/server/panel/vhost/apache/btwaf.conf
        fi
        /etc/init.d/httpd reload
    else
        /etc/init.d/nginx reload
    fi
}

if [ "${1}" == 'install' ]; then
    Install_total
elif [ "${1}" == 'update' ]; then
    Install_total
elif [ "${1}" == 'uninstall' ]; then
    Uninstall_total
fi
