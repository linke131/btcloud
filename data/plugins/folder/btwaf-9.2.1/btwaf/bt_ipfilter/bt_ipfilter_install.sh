#!/bin/bash
if [ ! -f /usr/sbin/ipset ] && [ ! -f /sbin/ipset ];then
    if [ -f /usr/bin/apt ];then
        apt install ipset -y
		apt install gcc -y 
    else
        yum install ipset -y
		yum install gcc -y
    fi
fi

if [ ! -f /usr/sbin/iptables ] && [ ! -f /sbin/iptables ];then
    if [ -f /usr/bin/apt ];then
        apt install iptables -y
    else
        yum install iptables -y
    fi
fi

init_file=/etc/init.d/bt_ipfilter
if [ -f $init_file ];then
    $init_file stop
fi
run_file=/www/server/panel/script/bt-ipfilter
gcc ./bt_ipfilter.c -o $run_file
chmod 700 $run_file
chown root:root $run_file

\cp -f ./bt_ipfilter.sh $init_file
chmod 700 $init_file
chown root:root $init_file
$init_file start
$init_file status

if [ -f "/usr/bin/apt-get" ];then
    sudo update-rc.d bt_ipfilter defaults
else
    chkconfig --add bt_ipfilter
    chkconfig --level 2345 bt_ipfilter on
fi

