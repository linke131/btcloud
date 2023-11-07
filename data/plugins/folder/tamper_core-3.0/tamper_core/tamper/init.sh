#!/bin/bash
# chkconfig: 2345 55 25
# description: bt-tamper Service

### BEGIN INIT INFO
# Provides:          bt-tamper
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts bt-tamper
# Description:       starts the bt-tamper
### END INIT INFO

install_path=/www/server/tamper
tamperuser_bin=/www/server/tamper/tamperuser
tamper_cli_bin=/www/server/tamper/tamper-cli
tamper_config_file=/www/server/tamper/tamper.conf
kernel_version=$(uname -r|cut -f 1 -d "-")
cd $install_path

# 复制内核模块相关文件
copy_kernel_modules_files(){
    # 复制tampercore.ko
    chmod 700 $install_path/tamper-cli
    chmod 700 $install_path/tamperuser

    # 创建软链接
    if [ ! -f /usr/bin/tamper ];then
        ln -sf $install_path/tamper-cli /usr/bin/tamper
    fi

    if [ ! -f /usr/bin/tamper-cli ];then
        ln -sf $install_path/tamper-cli /usr/bin/tamper-cli
    fi
}


install_package_by_yum(){
    # 安装依赖包
    if [ ! -f /usr/bin/gcc ];then
        yum install -y gcc make automake autoconf libtool
    fi
    
    # centos需要安装elfutils-libelf-devel
    is_exists_libelf=$(rpm -q elfutils-libelf-devel)
    if [ $? -ne 0 ];then
        yum install -y elfutils-libelf-devel
    fi

    # 安装kernel-devel
    is_kenel_devel=$(rpm -q kernel-devel-$(uname -r))
    if [ $? -ne 0 ];then
        yum install -y kernel-devel
    fi

    # 检查内核版本是否一致
    kenel_devel_version_is=$(rpm -qa | grep -E "kernel(-devel-|-)$(uname -r)"| wc -l)
    if [ "$kenel_devel_version_is" = "2" ];then
        echo "内核版本不一致，请尝试手动安装内核版本为$(uname -r)的内核头文件"
        exit 1
    fi
}


install_package_by_apt(){
    # 安装依赖包
    if [ ! -f /usr/bin/gcc ];then
        apt-get install -y gcc make automake autoconf libtool
    fi

    # 安装kernel-devel
    is_kenel_devel=$(dpkg -l|grep linux-headers-$(uname -r))
    if [ "$is_kenel_devel" = "" ];then
        apt-get install -y linux-headers-$(uname -r)
    fi

    # 检查内核版本是否一致
    kenel_devel_version_is=$(dpkg -l | grep linux-headers-$(uname -r) | wc -l)
    if [ "$kenel_devel_version_is" = "1" ];then
        echo "内核版本不一致，请尝试手动安装内核版本为$(uname -r)的内核头文件"
        exit 1
    fi
}

install_package(){
    if [ -f /usr/bin/yum ];then
        install_package_by_yum
    elif [ -f /usr/bin/apt ];then
        install_package_by_apt
    fi
}

# 编译内核模块
compile_kernel_modules(){
    ko_file=/www/server/tamper/tampercore.ko
    if [ -f $ko_file ];then
        rm -f $ko_file
    fi

    bash /www/server/panel/plugin/tamper_core/tamper/down_ko.sh
    if [ -f $ko_file ];then
        echo "download tampercore.ko success"
        return
    fi

    install_package
    cpmpile_bin=/www/server/panel/plugin/tamper_core/tamper/jm
    if [ ! -f $cpmpile_bin ];then
        echo "compile_bin not found"
        exit 1
    fi

    chmod 700 $cpmpile_bin
    $cpmpile_bin compile
    if [ $? -ne 0 ];then
        echo "compile tampercore.ko failed"
        exit 1
    fi

    if [ ! -f $ko_file ];then
        echo "compile tampercore.ko failed"
        exit 1
    fi

    chmod 700 $ko_file
}

tamper_start()
{
    if [ ! -f tampercore.ko ];then
        compile_kernel_modules
        if [ ! -f tampercore.ko ];then
            echo "tampercore.ko not found"
            exit 1
        fi
    fi

    is_ins=$(lsmod | grep tampercore)
    if [ "$is_ins" == "" ]; then
        echo -e "Loading Bt-Tampercore...\c"
        copy_kernel_modules_files
        sys_call_table_addr_str=$(cat /proc/kallsyms|grep ' sys_call_table'|head -n 1|awk '{printf $1}')
        insmod tampercore.ko sys_call_table_addr=$sys_call_table_addr_str >/dev/null 2>&1
        if [ $? -ne 0 ];then
            insmod -f tampercore.ko sys_call_table_addr=$sys_call_table_addr_str
            if [ $? -ne 0 ];then
                compile_kernel_modules
                insmod tampercore.ko sys_call_table_addr=$sys_call_table_addr_str
                if [ $? -ne 0 ];then
                    echo -e "	\033[31mfailed\033[0m"
                    exit 1
                fi
            fi
        fi

        tamperuser_pid=$(pidof tamperuser)
        if [ "$tamperuser_pid" != "" ]; then
            kill -9 $tamperuser_pid
            pkill -9 tamperuser
        fi

        echo -e "	\033[32mdone\033[0m"
    else
        echo "Loading Bt-Tampercore... Bt-Tampercore Kernel module loaded"
    fi

    tamperuser_pid=$(pidof tamperuser)
    if [ "$tamperuser_pid" != "" ]; then
        echo -e "Starting Bt-Tamperuser... Bt-Tamperuser (pid $tamperuser_pid) already running"
    else
        echo -e "Starting Bt-Tamper...\c"
        nohup $tamperuser_bin  &> $install_path/tamperuser.log &
        sleep 1
        tamperuser_pid=$(pidof tamperuser)
        if [ "$tamperuser_pid" == "" ]; then
            echo -e "   \033[31mfailed\033[0m"
            exit 1
        else
            echo -e "	\033[32mdone\033[0m"
        fi
    fi
    tamper_day_start
}



tamper_stop()
{
        echo -e "Stopping Bt-Tamperuser...\c";
        tamperuser_pid=$(pidof tamperuser)
        if [ "$tamperuser_pid" != "" ]; then
            kill -9 $tamperuser_pid
            pkill -9 tamperuser
        fi
        echo -e "	\033[32mdone\033[0m"

        echo -e "Uninstall Bt-Tampercore...\c";
        is_ins=$(lsmod | grep tampercore)
        if [ "$is_ins" != "" ]; then
            rmmod tampercore
        fi
        echo -e "	\033[32mdone\033[0m"
        tamper_day_stop
}

tamper_status()
{
    tamperuser_pid=$(pidof tamperuser)
    is_ins=$(lsmod | grep tampercore)
    if [ "$tamperuser_pid" != "" ]; then
        echo -e "\033[32mBt-Tamperuser (pid $tamperuser_pid) is running\033[0m"
    else
        echo -e "\033[31mBt-Tamperuser is not running\033[0m"
    fi

    if [ "$is_ins" != "" ]; then
        echo -e "\033[32mBt-Tampercore Kernel module loaded\033[0m"
    else
        echo -e "\033[31mBt-Tampercore Kernel module not loaded\033[0m"
    fi
}

tamper_reload()
{
    tamper_stop
    tamper_start
}

tamper_day_start() {
    # 记录使用时间
    if [ ! -f $install_path/date.pl ]; then
        cat >$install_path/date.pl <<EOF
$(date +%s)
0
EOF
    else
        last=$(sed -n 1p $install_path/date.pl)
        if [ "${last}" == "null" ]; then
            sed -i "1c $(date +%s)" $install_path/date.pl
        fi
    fi
}

tamper_day_stop() {
    # 记录使用时间
    if [ ! -f $install_path/date.pl ]; then
        cat >$install_path/date.pl <<EOF
null
0
EOF
    else
        last=$(sed -n 1p $install_path/date.pl)
        seconds=$(sed -n 2p $install_path/date.pl)
        if [ "${last}" == "null" ]; then
            last=$(date +%s)
        fi
        if [ $last -lt 2147483647 ]; then
            now=$(date +%s)
            theseconds=$((${now} - ${last}))
            cat >$install_path/date.pl <<EOF
null
$((${seconds} + ${theseconds}))
EOF
        fi
    fi
}



case "$1" in
    start)
        tamper_start
        ;;
    stop)
        tamper_stop
        ;;
    restart)
        tamper_stop
        tamper_start
        ;;
    status)
        tamper_status
        ;;
    reload)
        tamper_reload
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|reload}"
        exit 1
        ;;
esac
