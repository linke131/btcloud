#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
pluginPath=/www/server/panel/plugin/nfs_tools
initSh=/etc/init.d/bt_nfs_mount

if [ ! -f $initSh ];then
    \cp -f $pluginPath/init.sh $initSh
    chmod +x $initSh
fi

$initSh stop
$initSh start

echo 'Successify'