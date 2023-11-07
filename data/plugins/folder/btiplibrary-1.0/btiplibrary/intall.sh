#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

Install_iplibrary
{
	cp\ icon.png /www/server/panel/static/img/soft_ico/ico-btiplibrary.png
	echo "Successify"
}

if [ "${1}" == 'install' ];then
    Install_total
elif  [ "${1}" == 'update' ];then
    Install_total
elif [ "${1}" == 'uninstall' ];then
    Uninstall_total
fi