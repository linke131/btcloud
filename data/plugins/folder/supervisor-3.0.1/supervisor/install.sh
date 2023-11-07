#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
pluginPath=/www/server/panel/plugin/supervisor

wrong_actions=()
# Retry Download file
download_file()
{
    local_file=$1
    source=$2
    timeout=$3
    retry=$4
    if [ -n "$5" ]; then
        ori_retry=$5
    else
        ori_retry=$retry
    fi
    #echo "source:$source/local:$local_file/retry:$retry/ori_retry:$ori_retry"
    wget --no-check-certificate -O $local_file $source -T $timeout -t $ori_retry
    if [ -s $local_file ]; then
        echo $local_file" download successful."
    else
        if [ $retry -gt 1 ];then
            let retry=retry-1
            download_file $local_file $source $timeout $retry $ori_retry
        else
            echo "* "$local_file" download failed!"
            wrong_actions[${#wrong_actions[*]}]=$local_file
        fi
    fi
}

# 安装
Install_Supervisor()
{
    if [ -e '/www/server/panel/pyenv/' ]; then
        pipv='/www/server/panel/pyenv/bin/pip'
        path=/www/server/panel/pyenv/bin/supervisord
        py='/www/server/panel/pyenv/bin/python'
        echo_supervisord_conf='/www/server/panel/pyenv/bin/echo_supervisord_conf'
        supervisorctl='/www/server/panel/pyenv/bin/supervisorctl'
    else
        pipv='pip'
        py='python'
        path=supervisord
        echo_supervisord_conf='echo_supervisord_conf'
        supervisorctl='supervisorctl'
    fi
    if [ ! -d $pluginPath ]; then
        mkdir -p $pluginPath
    fi

    # 循环卸载已有的supervisor
    # for i in 1 2 3 4 5; do
    #     s_version=`btpip list | grep supervisor | awk '{print $2}'`
    #     if [ -z $s_version ]; then
    #         echo "Uninstalled all of supervisor."
    #         break
    #     fi
    #     echo Uninstalling supervisor $s_version
    #     btpip uninstall supervisor -y
    #     if [ $i -eq 5 ]; then
    #         # echo "exit."
    #         break
    #     fi
    # done

    cd $pluginPath
    btpip install supervisor==4.2.4 -I
    /bin/cp -f /www/server/panel/pyenv/lib/python3.7/site-packages/supervisor/options.py options.py.bak
    /bin/cp -f options.py /www/server/panel/pyenv/lib/python3.7/site-packages/supervisor/options.py
    /bin/cp -f /www/server/panel/pyenv/lib/python3.7/site-packages/supervisor/rpcinterface.py rpcinterface.py.bak
    /bin/cp -f  rpcinterface.py /www/server/panel/pyenv/lib/python3.7/site-packages/supervisor/rpcinterface.py
    echo bt > /www/server/panel/pyenv/lib/python3.7/site-packages/supervisor/bt.pl

    # download_file /tmp/supervisor-bt.zip http://download.bt.cn/install/plugin/supervisor/supervisor-4.2.4-bt.zip 10 3
    # if [ -f /tmp/supervisor-bt.zip ]; then
    #     cd /tmp
    #     if [ ! -d /tmp/supervisor ]; then
    #         mkdir /tmp/supervisor
    #     fi
    #     unzip -d /tmp/supervisor supervisor-bt.zip && cd /tmp/supervisor
    #     # btpip install setuptools==65.4.1
    #     btpython setup.py install --record $pluginPath/install_files.log
    #     rm -rf /tmp/supervisor
    #     rm -f /tmp/supervisor-bt.zip
    # fi
    # $pipv install supervisor -i http://pypi.douban.com/simple --trusted-host pypi.douban.com --ignore-installed meld3
    if [ ! -d $pluginPath/log ]; then
	    mkdir -p $pluginPath/log
    fi
    if [ ! -d $pluginPath/profile ]; then
	    mkdir -p $pluginPath/profile
    fi
    if [ ! -d /etc/supervisor ]; then
        mkdir -p /etc/supervisor
    fi

    # reg="^#\!$py\$"
    # is_sed=$(cat $echo_supervisord_conf|head -n 1|grep -E $reg)
    # if [ "${is_sed}" = "" ];then
    #     sed -i "s@^#!.*@#!$py@" $echo_supervisord_conf
    # fi
    # is_sed=$(cat $path|head -n 1|grep -E $reg)
    # if [ "${is_sed}" = "" ];then
    #     sed -i "s@^#!.*@#!$py@" $path
    # fi
    # is_sed=$(cat $supervisorctl|head -n 1|grep -E $reg)
    # if [ "${is_sed}" = "" ];then
    #     sed -i "s@^#!.*@#!$py@" $supervisorctl
    # fi

    if [ ! -s /etc/supervisor/supervisord.conf ]; then
        if [ ! -d /var/run ]; then
            mkdir /var/run
        fi
        if [ ! -d /var/log ]; then
            mkdir /var/log
        fi
        if [ ! -f /var/run/supervisor.sock ]; then
            touch /var/run/supervisor.sock
        fi
        if [ ! -f /var/run/supervisor.pid ]; then
            touch /var/run/supervisor.pid
        fi
        if [ ! -f /var/log/supervisor.log ]; then
            touch /var/log/supervisor.log
        fi
        cd $pluginPath
        cp sample.conf /etc/supervisor/supervisord.conf
        # $echo_supervisord_conf > /etc/supervisor/supervisord.conf
    fi


	echo '正在安装脚本文件...' > $install_tmp
	\cp -a -r $pluginPath/icon.png /www/server/panel/BTPanel/static/img/soft_ico/ico-supervisor.png
	# 防止系统加固误清理
	s_file=/www/server/panel/plugin/syssafe/config.json
	if [ -f $s_file ];then
	    is_exp=$(cat $s_file|grep supervisord)
	    if [ "$is_exp" = "" ];then
	        sed -i 's/"PM2"/"PM2","supervisord"/' $s_file
	        /etc/init.d/bt_syssafe restart
	    fi
	fi

    # $py /www/server/panel/plugin/supervisor/config.py
    # $path -c /etc/supervisor/supervisord.conf
    # $supervisorctl reload

    if [ -e '/usr/lib/systemd/system/' ]; then
        service_path=/usr/lib/systemd/system/supervisord.service
    else
        service_path=/lib/systemd/system/supervisord.service
    fi
    touch $service_path
    echo "[Unit]
Description=Process Monitoring and Control Daemon
After=rc-local.service nss-user-lookup.target

[Service]
Type=forking
ExecStart=$py $path -c /etc/supervisor/supervisord.conf
ExecStop=$py $path $OPTIONS shutdown
ExecReload=$py $path $OPTIONS reload
KillMode=process
Restart=on-failure
RestartSec=42s
[Install]
WantedBy=multi-user.target" > $service_path
    systemctl daemon-reload
    systemctl enable supervisord
    supervisor_pid=`ps -ef | grep supervisord | grep -v grep | awk '{print $2}'`
    if [ ! -z $supervisor_pid ]; then
        kill -9 $supervisor_pid
    fi

    pid=$(ps aux|grep /www/server/panel/pyenv/bin/supervisord|grep -v grep|awk '{print $2}')
    if [ ! -z $pid ]; then
        kill -9 $pid
    fi
    systemctl start supervisord
    echo '安装完成' > $install_tmp
}

# 卸载
Uninstall_Supervisor()
{
  if [ -e '/www/server/panel/pyenv/' ]; then
      pipv='/www/server/panel/pyenv/bin/pip'
      path=/www/server/panel/pyenv/bin/supervisord
      py='/www/server/panel/pyenv/bin/python'
      echo_supervisord_conf='/www/server/panel/pyenv/bin/echo_supervisord_conf'
      supervisorctl='/www/server/panel/pyenv/bin/supervisorctl'
  else
      pipv='pip'
      py='python'
      path=/usr/bin/supervisord
      echo_supervisord_conf='echo_supervisord_conf'
      supervisorctl='supervisorctl'
  fi
	$supervisorctl stop all
    if [ -f $pluginPath/install_files.log ]; then
        xargs rm -rf < $pluginPath/install_files.log
    else
        $pipv uninstall supervisor -y
    fi

    if [ -f /www/server/panel/pyenv/lib/python3.7/site-packages/supervisor/bt.pl ]; then
        cd $pluginPath
        if [ -f options.py.bak ]; then
            mv options.py.bak /www/server/panel/pyenv/lib/python3.7/site-packages/supervisor/options.py
        fi
        if [ -f rpcinterface.py.bak ]; then
            mv rpcinterface.py.bak /www/server/panel/pyenv/lib/python3.7/site-packages/supervisor/rpcinterface.py
        fi
        rm -f /www/server/panel/pyenv/lib/python3.7/site-packages/supervisor/bt.pl
    fi
	rm -rf $pluginPath
	rm -rf /etc/supervisor/supervisord.conf
    systemctl stop supervisord
	if [ -e '/usr/lib/systemd/system/' ]; then
        rm -f /usr/lib/systemd/system/supervisord.service
    else
        rm -f /lib/systemd/system/supervisord.service
    fi
	systemctl daemon-reload
}

if [ "${1}" == 'install' ];then
	Install_Supervisor
elif [ "${1}" == 'uninstall' ];then
	Uninstall_Supervisor
else
    echo 'Error'
fi