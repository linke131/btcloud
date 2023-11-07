#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

if [ -d "/www/server/panel/pyenv" ];then
  btpip install boto3
else
  pip install boto3
fi
Install_AWS()
{
	mkdir -p /www/server/panel/plugin/aws_s3
	cd /www/server/panel/plugin/aws_s3
	echo 'Successify'
}

Uninstall_AWS()
{
	rm -rf /www/server/panel/plugin/aws_s3
	echo 'Successify'
}


action=$1
if [ "${1}" == 'install' ];then
	Install_AWS
else
	Uninstall_AWS
fi
