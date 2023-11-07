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

Install_Ncdu(){
  yum remove ncdu -y
  name=$1
  ncdu_url=https://dev.yorhel.nl/download/$name
  if [ ! -f $name ];then
    wget $ncdu_url -T 5
    echo "下载完成: $ncdu_url"
  else
    echo "已下载完成: $ncdu_url"
  fi

  if [ ! -f $name ];then
    echo "下载失败: $name"
    echo "请重新下载"
    return
  fi

  echo "正在解压: $name"
  if tar -xzvf $name ;then
    echo "解压完成"
    rm $name
    if [ -L "/usr/bin/ncdu" ];then rm /usr/bin/ncdu; fi
    ln -s /www/server/panel/plugin/disk_analysis/ncdu /usr/bin/ncdu
    chmod +x /usr/bin/ncdu
  fi
  echo `ncdu -v`
}
Install_disk_analysis()
{
  if [ ! -f "/www/server/panel/plugin/disk_analysis/ncdu" ];then
    Install_Ncdu ncdu-2.2.1-linux-x86_64.tar.gz
	fi

	# 授权
	if [ -L "/usr/bin/ncdu" ];then
	  chmod +x /usr/bin/ncdu
	else
	  ln -s /www/server/panel/plugin/disk_analysis/ncdu /usr/bin/ncdu
    chmod +x /usr/bin/ncdu
	fi

	echo '正在安装脚本文件...' > $install_tmp
    # wget -O /www/server/panel/plugin/obs/obs_main.py $download_Url/install/plugin/obs/obs_main.py -T 5
    # wget -O /www/server/panel/plugin/obs/index.html $download_Url/install/plugin/obs/index.html -T 5
    # wget -O /www/server/panel/plugin/obs/info.json $download_Url/install/plugin/obs/info.json -T 5
    # wget -O /www/server/panel/plugin/obs/icon.png $download_Url/install/plugin/obs/icon.png -T 5
    # wget -O /www/server/panel/static/img/soft_ico/ico-obs.png $download_Url/install/plugin/obs/icon.png -T 5

	echo '安装完成' > $install_tmp
	echo success
}

Uninstall_disk_analysis()
{
 	rm -rf /www/server/panel/plugin/disk_analysis
}


action=$1
if [ "${1}" == 'install' ];then
	Install_disk_analysis
else
	Uninstall_disk_analysis
fi
