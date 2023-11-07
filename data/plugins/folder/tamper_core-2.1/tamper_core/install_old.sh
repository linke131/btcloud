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


# 检查是否为Centos7
check_centos7(){
    is_centos7="no"
    if [ -f /etc/redhat-release ];then
        os_version=$(cat /etc/redhat-release | grep 'release 7' | grep -i centos | wc -l)
        if [ $os_version -eq 1 ];then
            is_centos7="yes"
        fi
    fi
}


# 下载软件包
download_pack(){
    curl_bin=$(which curl)
    wget_bin=$(which wget)
    if [ -f $curl_bin ];then
        curl -k -# -o $1 $2
    elif [ -f $wget_bin ];then
        wget --no-check-certificate -O $1 $2 -T 5
    else
        echo "错误：未安装curl或wget！"
        exit 1
    fi

    if [ ! -f $1 ];then
        echo "错误：下载失败！"
        exit 1
    fi
}


# 下载centos7的内核模块
download_centos7_kernel_module(){
    kernel_path="$plugin_path/tamper/kernel/${kernel_version}"
    ko_file="$kernel_path/tampercore.ko"
    cli_file="$kernel_path/tamper-cli"
    user_file="$kernel_path/tamperuser"
    if [ -f $ko_file ];then
        echo "内核模块已存在！"
        return
    fi
    down_url="https://download.bt.cn/install/plugin/tamper/kernel/${kernel_version}"
    ko_url="$down_url/tampercore.ko"
    cli_url="$down_url/tamper-cli"
    user_url="$down_url/tamperuser"

    if [ ! -d $kernel_path ];then
        mkdir -p $kernel_path
    fi


    if [ ! -f $ko_file ];then
        download_pack $ko_file $ko_url
    fi
    # 检查是否下载成功？
    ko_size=$(du -b $ko_file | awk '{print $1}')
    if [ $ko_size -lt 8192 ];then
        echo "错误：下载Centos7的专用内核模块失败，内核版本：$kernel_version"
        rm -f $ko_file
        exit 1
    fi

    if [ ! -f $cli_file ];then
        download_pack $cli_file $cli_url
    fi
    if [ ! -f $user_file ];then
        download_pack $user_file $user_url
    fi
}



# 检查内核条件
kernel_check(){
    ko_file=$plugin_path/tamper/kernel/$kernel_version/tampercore.ko
    if [ ! -f $ko_file ];then
        check_centos7
        if [ $is_centos7 == "yes" ];then
            download_centos7_kernel_module
            if [ -f $ko_file ];then
                return
            fi
        fi

        echo "错误：不支持的内核版本!"
        echo "当前内核版本为：$kernel_version"
        echo '------------------------------------------------------------------'
        echo "支持的内核版本:"
        ls $plugin_path/tamper/kernel
        rm -rf $plugin_path
        exit 1
    fi

    # 卸载当前同名内核模块
    is_ins=$(lsmod|grep tampercore)
    if [ "$is_ins" != "" ]; then
        rmmod tampercore.ko
    fi

    # 结束同名控制台进程
    pid=$(pidof tamperuser)
    if [ "$pid" != "" ]; then
        kill -9 $pid
    fi
}

# 解压软件包
unpack_pack(){
    mkdir -p $install_path
    if [ ! -d $install_path ];then
        mkdir -p $install_path
    fi

    if [ -d $install_path/kernel ];then
        rm -rf $install_path/kernel
    fi

    \cp -arf $plugin_path/tamper/kernel $install_path/kernel
    \cp -arf $plugin_path/tamper/init.sh $install_path/init.sh
    \cp -arf $plugin_path/tamper/cli.sh $install_path/cli.sh
    if [ ! -f $install_path/tamper.conf ];then
        \cp -f $plugin_path/tamper/tamper.conf $install_path/tamper.conf
    fi
    # rm -rf $plugin_path/tamper
}


# 复制内核模块相关文件
copy_kernel_modules_files(){
    # 复制tampercore.ko
    if [ -f $install_path/kernel/$kernel_version/tampercore.ko ];then
        \cp -f $install_path/kernel/$kernel_version/tampercore.ko $install_path/tampercore.ko
        if [ $? -ne 0 ];then
            echo "错误：复制文件tampercore.ko失败！"
            exit 1
        fi
    fi

    # 复制tamperuser
    if [ -f $install_path/kernel/$kernel_version/tamperuser ];then
        \cp -f $install_path/kernel/$kernel_version/tamperuser $install_path/tamperuser
        if [ $? -ne 0 ];then
            echo "错误：复制文件tamperuser失败！"
            exit 1
        fi
    fi

    # 复制tamper_cli
    if [ -f $install_path/kernel/$kernel_version/tamper-cli ];then
        \cp -f $install_path/kernel/$kernel_version/tamper-cli $install_path/tamper-cli
        if [ $? -ne 0 ];then
            echo "错误：复制文件tamper-cli失败！"
            exit 1
        fi
    fi

    # 创建软链接
    if [ ! -f /usr/bin/tamper ];then
        ln -sf $install_path/tamper-cli /usr/bin/tamper
    fi

    if [ ! -f /usr/bin/tamper-cli ];then
        ln -sf $install_path/tamper-cli /usr/bin/tamper-cli
    fi

    \cp -f $install_path/init.sh /etc/init.d/bt-tamper
    chmod 700 /etc/init.d/bt-tamper

    chown -R root:root $install_path
    chmod -R 600 $install_path
    chmod 700 $install_path/tamper-cli
    chmod 700 $install_path/tamperuser
    chmod 700 $install_path/tampercore.ko
    chmod 700 $install_path/cli.sh
}

# 安装服务
install_service(){
    if [ -f /usr/bin/yum ];then
        chkconfig --add bt-tamper
        chkconfig --level 2345 bt-tamper on
    elif [ -f /usr/bin/apt ];then
        update-rc.d bt-tamper defaults
    fi

    bash /etc/init.d/bt-tamper stop
    bash /etc/init.d/bt-tamper start
}

# 安装
Install_tamper_core(){
    os_check
    kernel_check
    unpack_pack
    copy_kernel_modules_files
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
