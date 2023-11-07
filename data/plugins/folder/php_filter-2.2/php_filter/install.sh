#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
os_bit=$(getconf LONG_BIT)
is_arm=$(uname -a|grep -E 'aarch64|arm|ARM')

if [ "$os_bit" = "32" ] || [ "$is_arm" != "" ];then
	echo "========================================="
	echo "错误: 不支持32位和ARM/AARCH64平台的系统!"
	echo "========================================="
	exit 0;
fi

pluginPath=/www/server/panel/plugin/php_filter
extFile=""
version=""

upload_php_ext()
{
	for phpV in $(ls /www/server/php)
	do
		ext_dir=/www/server/php/$phpV/lib/php/extensions
		if [ ! -d $ext_dir ];then
			continue;
		fi
		ext_dirname=$(ls $ext_dir)
		so_file=$ext_dir/$ext_dirname/bt_filter.so
		if [ ! -f $so_file ];then
			continue;
		fi
		old_md5=$(md5sum $so_file|awk '{print $1}')
		new_file=$pluginPath/modules/bt_filter_${phpV}.so
		if [ ! -f $new_file ];then
			continue;
		fi

		new_md5=$(md5sum $new_file|awk '{print $1}')
		if [ "$old_md5" = "$new_md5" ];then
			continue;
		fi

		\cp -f $new_file $so_file
		/etc/init.d/php-fpm-$phpV reload
	done
}


Install_php_filter()
{
	mkdir -p $pluginPath
	mkdir -p $pluginPath/config
	mkdir -p $pluginPath/total
	upload_php_ext
	echo > /www/server/panel/data/reload.pl
	echo 'Successify'
}


Uninstall_php_filter()
{
	rm -rf $pluginPath
}


action=$1
if [ "${1}" == 'install' ];then
	Install_php_filter
else
	Uninstall_php_filter
fi
