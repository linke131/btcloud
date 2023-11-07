#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

#配置插件安装目录
install_path=/www/server/panel/plugin/vuln_push
#存放数据
data_path=/www/server/panel/data/vuln_push


#安装
Install()
{
    mkdir -p $data_path
    chmod 600 $data_path
	#==================================================================
	#依赖安装开始
	#依赖安装结束
	#==================================================================
	echo '================================================'
	echo '安装完成'
}

#卸载
Uninstall()
{
	rm -rf $install_path
	rm -rf $data_path
}

#操作判断
action=$1
if [ "${1}" == 'install' ];then
    Install
else
    Uninstall
fi
