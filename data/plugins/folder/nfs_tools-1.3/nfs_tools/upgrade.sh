#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
pluginPath=/www/server/panel/plugin/nfs_tools
initSh=/etc/init.d/bt_nfs_mount

# 升级nfs服务到最新
if [ -f /usr/bin/apt ];then
    apt install nfs-kernel-server -y
else
    yum install nfs-utils -y
fi

# 替换自动挂载服务脚本
\cp -f $pluginPath/init.sh $initSh
chmod +x $initSh

$initSh stop
$initSh start

# 输出成功标记
echo 'Successify'