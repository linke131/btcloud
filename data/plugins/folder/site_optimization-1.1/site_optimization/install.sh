#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

pluginPath=/www/server/panel/plugin/site_optimization
pyVersion=$(python -c 'import sys;print(sys.version_info[0]);')
py_zi=$(python -c 'import sys;print(sys.version_info[1]);')
mkdir -p $pluginPath/check_site_type_script
mkdir -p $pluginPath/opt_site_script
Install_Site_OPT()
{

  cp -a -r $pluginPath/icon.png /www/server/panel/BTPanel/static/img/soft_ico/ico-site_optimization.png

  echo 'Successify'
}

Uninstall_Site_OPT()
{
	rm -rf /www/server/panel/plugin/site_optimization
	echo 'Successify'
}


action=$1
if [ "${1}" == 'install' ];then
	Install_Site_OPT
	echo > /www/server/panel/data/reload.pl
else
	Uninstall_Site_OPT
fi
