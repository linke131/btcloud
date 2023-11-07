#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
LANG=en_US.UTF-8
plugin_path=/www/server/panel/plugin/tamper_core
install_path=/www/server/tamper
tamperuser_bin=/www/server/tamper/tamperuser
tamper_cli_bin=/www/server/tamper/tamper-cli
tamper_config_file=/www/server/tamper/tamper.conf
kernel_version=$(uname -r|cut -f 1 -d "-")

# 检查操作系统条件
os_check(){
    os_bit=$(getconf LONG_BIT)
    if [ $os_bit == 32 ];then
        echo "错误：不支持32位系统！"
        exit 1
    fi
    os_machine=$(uname -m)
    if [ $os_machine != "x86_64" ];then
        echo "错误：只支持x64_64平台！"
        exit 1
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
    build_path=/lib/modules/$(uname -r)/build
    src_path=/usr/src/kernels/$(uname -r)
    if [[ ! -d $build_path ]] || [[ ! -d $src_path ]];then
        yum install -y kernel-devel
    fi
    
    # 检查内核版本是否一致
    if [[ ! -d $build_path ]] || [[ ! -d $src_path ]];then
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
    kenel_devel_version_is=$(dpkg -l|grep linux-headers|grep $(uname -r)|wc -l)
    if [ "$kenel_devel_version_is" = "0" ];then
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


# 解压软件包
unpack_pack(){
    mkdir -p $install_path
    if [ ! -d $install_path ];then
        mkdir -p $install_path
    fi

    if [ ! -d /etc/init.d ];then
        ln -sf /etc/rc.d/init.d /etc/init.d
    fi

    \cp -f $plugin_path/tamper/tamperuser $install_path/tamperuser
    \cp -f $plugin_path/tamper/tamper-cli $install_path/tamper-cli
    \cp -f $plugin_path/tamper/init.sh $install_path/init.sh
    \cp -f $plugin_path/tamper/cli.sh $install_path/cli.sh
    if [ ! -f $install_path/tamper.conf ];then
        \cp -f $plugin_path/tamper/tamper.conf $install_path/tamper.conf
    fi
}


# 复制内核模块相关文件
copy_kernel_modules_files(){
    # 创建软链接
    if [ ! -f /usr/bin/tamper ];then
        ln -sf $install_path/tamper-cli /usr/bin/tamper
    fi

    if [ ! -f /usr/bin/tamper-cli ];then
        ln -sf $install_path/tamper-cli /usr/bin/tamper-cli
    fi

    \cp -arf $install_path/init.sh /etc/init.d/bt-tamper
    chmod 700 /etc/init.d/bt-tamper
    chown -R root:root $install_path
    chmod -R 600 $install_path
    chmod 700 $install_path/tamper-cli
    chmod 700 $install_path/tamperuser
    chmod 700 $install_path/cli.sh
}


# 编译内核模块
compile_kernel_modules(){
    ko_file=/www/server/tamper/tampercore.ko
    if [ -f $ko_file ];then
        rm -f $ko_file
    fi
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


# 安装服务
install_service(){
    if [ -f /usr/bin/yum ];then
        is_chkconfig=$(which chkconfig)
        if [ "$is_chkconfig" = "" ];then
            yum install -y chkconfig
        fi

        if [ ! -d /etc/init.d ];then
            ln -sf /etc/rc.d/init.d /etc/init.d
        fi

        chkconfig --add bt-tamper &> /dev/null
        chkconfig --level 2345 bt-tamper on &> /dev/null
    elif [ -f /usr/bin/apt ];then
        update-rc.d bt-tamper defaults &> /dev/null
    fi

    bash /etc/init.d/bt-tamper stop
    bash /etc/init.d/bt-tamper start
}

# 安装
Install_tamper_core(){
    os_check
    unpack_pack
    install_package
    copy_kernel_modules_files
    compile_kernel_modules
    install_service
    echo 'Successify'
}


# 卸载
Uninstall_tamper_core(){
    init_file=/etc/init.d/bt-tamper
    $init_file stop
    if [ -f /usr/bin/yum ];then
        chkconfig --del bt-tamper
    elif [ -f /usr/bin/apt ];then
        update-rc.d -f bt-tamper remove
    fi

    rm -f $init_file
    rm -rf $install_path
    rm -rf $plugin_path
    echo 'Successify'
}


action=$1
if [ "${1}" == 'install' ];then
	Install_tamper_core
elif [ "${1}" == 'uninstall' ];then
	Uninstall_tamper_core
else
    echo 'Usage:'
    echo '  bash tamper.sh install'
    echo '  bash tamper.sh uninstall'
fi
