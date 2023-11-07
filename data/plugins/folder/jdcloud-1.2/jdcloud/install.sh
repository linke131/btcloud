#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'

public_file=/www/server/panel/install/public.sh
if [ ! -f $public_file ];then
	wget -O $public_file http://download.bt.cn/install/public.sh -T 5;
fi
. $public_file

download_Url=$NODE_URL

Install_jdcloud()
{
    mkdir -p /www/server/panel/plugin/jdcloud
    mkdir -p /www/server/panel/static/img/soft_ico
    echo '正在安装脚本文件...' > $install_tmp
	btpip install boto3==1.20.27
	pip install boto3==1.20.27
	btpip install httplib2==0.20.4
	pip install httplib2==0.20.4
    # wget -O /www/server/panel/plugin/jdcloud/jdcloud_main.py $download_Url/install/plugin/jdcloud/jdcloud_main.py -T 5
    # wget -O /www/server/panel/plugin/jdcloud/index.html $download_Url/install/plugin/jdcloud/index.html -T 5
    # wget -O /www/server/panel/plugin/jdcloud/info.json $download_Url/install/plugin/jdcloud/info.json -T 5
    # wget -O /www/server/panel/plugin/jdcloud/icon.png $download_Url/install/plugin/jdcloud/icon.png -T 5
    # wget -O /www/server/panel/BTPanel/static/img/soft_ico/ico-jdcloud.png $download_Url/install/plugin/jdcloud/icon.png -T 5
    \cp -rf /www/server/panel/plugin/jdcloud/icon.png /www/server/panel/BTPanel/static/img/soft_ico/ico-jdcloud.png
	echo '安装完成' > $install_tmp
	echo success
}

Uninstall_jdcloud()
{
 	rm -rf /www/server/panel/data/jdcloudAS.conf
	echo '备份文件已删除'
	rm -rf /www/server/panel/plugin/jdcloud
}


action=$1
if [ "${1}" == 'install' ];then
	Install_jdcloud
else
	Uninstall_jdcloud
fi
