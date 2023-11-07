#!/bin/bash
OS_BIT=$(uname -m)
if [ $OS_BIT != "x86_64" ]; then
    echo "Only support x86_64"
    exit 1
fi

KRNL_VERSION=$(uname -r)
IS_UBUNTU=$(cat /etc/*release | grep -v ID_LIKE | grep -iE "ubuntu")
IS_DEBIAN=$(cat /etc/*release | grep -v ID_LIKE | grep -iE "debian")
IS_CENTOS=$(cat /etc/*release | grep -v ID_LIKE | grep -iE "centos")
IS_ROCKY=$(cat /etc/*release | grep -v ID_LIKE | grep -iE "rocky")
IS_TENCENTOS=$(cat /etc/*release | grep -v ID_LIKE | grep -iE "TencentOS")
IS_ALIYUN=$(cat /etc/*release | grep -v ID_LIKE | grep -iE "Alibaba Cloud Linux")
IS_ANOLIS=$(cat /etc/*release | grep -v ID_LIKE | grep -iE "Anolis OS")
IS_ALMA=$(cat /etc/*release | grep -v ID_LIKE | grep -iE "AlmaLinux")
IS_OPENCLOUD=$(cat /etc/*release | grep -v ID_LIKE | grep -iE "OpenCloudOS")
IS_OPENEULER=$(cat /etc/*release | grep -v ID_LIKE | grep -iE "openEuler")
IS_EULER=$(cat /etc/*release | grep -v ID_LIKE | grep -iE "EulerOS")
IS_Amazon=$(cat /etc/*release | grep -v ID_LIKE | grep -iE "Amazon Linux")
IS_UnionTech=$(cat /etc/*release | grep -v ID_LIKE | grep -iE "UnionTech OS")
IS_DEEPIN=$(cat /etc/*release | grep -v ID_LIKE | grep -iE "Deepin")
IS_KYLIN=$(cat /etc/*release | grep -v ID_LIKE | grep -iE "Kylin Linux")

OS_MAJOR_VERSION=0
OS_NAME=""
LAST_NAME="tampercore"
END_NAME="amd64.ko"
END_SIGN="amd64.sign"
URL="https://download.bt.cn/tampercore"

get_opencloudos_version() {
    if [ -f /etc/opencloudos-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/opencloudos-release | grep -Eow '[0-9]' | head -n 1)
    elif [ -f /etc/os-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/os-release | grep VERSION_ID | cut -f 2 -d '=' | sed 's/"//g' | cut -f 1 -d '.')
    fi
    OS_NAME="opencloudos${OS_MAJOR_VERSION}"
}

get_almlinux_version() {
    if [ -f /etc/almalinux-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/almalinux-release | awk '{print $3}' | cut -d '.' -f 1)
    elif [ -f /etc/os-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/os-release | grep VERSION_ID | cut -f 2 -d '=' | sed 's/"//g' | cut -f 1 -d '.')
    fi
    OS_NAME="almlinux${OS_MAJOR_VERSION}"
}

get_openeuler_version() {
    if [ -f /etc/openEuler-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/openEuler-release | awk '{print $3}' | cut -d '.' -f 1)
    elif [ -f /etc/os-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/os-release | grep VERSION_ID | cut -f 2 -d '=' | sed 's/"//g' | cut -f 1 -d '.')
    fi
    OS_NAME="openeuler${OS_MAJOR_VERSION}"
}

get_euler_version() {
    if [ -f /etc/uos-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/uos-release | awk '{print $3}' | sed 's/\.//g')
    elif [ -f /etc/os-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/os-release | grep VERSION_ID | cut -f 2 -d '=' | sed -e's/"//g' -e 's/\.//g')
    fi
    OS_NAME="euler${OS_MAJOR_VERSION}"
}

get_uniontech_version() {
    if [ -f /etc/uos-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/uos-release | awk '{print $5}')
    elif [ -f /etc/os-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/os-release | grep VERSION_ID | cut -f 2 -d '=' | sed 's/"//g')
    fi
    OS_NAME="uniontech${OS_MAJOR_VERSION}"
}

get_deepin_version() {
    if [ -f /etc/deepin-version ]; then
        OS_MAJOR_VERSION=$(cat /etc/deepin-version | grep Version | cut -f 2 -d '=' | sed 's/\.//g')
    elif [ -f /etc/os-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/os-release | grep VERSION_ID | cut -f 2 -d '=' | sed -e's/"//g' -e 's/\.//g')
    fi
    OS_NAME="deepin${OS_MAJOR_VERSION}"
}

get_kylin_version() {
    if [ -f /etc/kylin-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/kylin-release | awk '{print $6}')
    elif [ -f /etc/os-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/os-release | grep VERSION_ID | cut -f 2 -d '=' | sed 's/"//g')
    fi
    OS_NAME="kylin${OS_MAJOR_VERSION}"
}

get_amazon_version() {
    if [ -f /etc/system-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/system-release | awk '{print $4}')
    elif [ -f /etc/os-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/os-release | grep VERSION_ID | cut -f 2 -d '=' | sed 's/"//g')
    fi
    OS_NAME="amazonlinux${OS_MAJOR_VERSION}"
}

get_ubuntu_version() {
    if [ -f /etc/lsb-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/lsb-release | grep DISTRIB_RELEASE | cut -f 2 -d '=' | sed 's/\.//g')
    elif [ -f /etc/os-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/os-release | grep VERSION_ID | cut -f 2 -d '=' | sed 's/"\.//g' | sed 's/\.//g')
    fi

    OS_NAME="ubuntu${OS_MAJOR_VERSION}"
}

get_debian_version() {
    if [ -f /etc/debian_version ]; then
        OS_MAJOR_VERSION=$(cat /etc/debian_version | cut -f 1 -d '.')
    elif [ -f /etc/os-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/os-release | grep VERSION_ID | cut -f 2 -d '=' | sed 's/"//g')
    fi

    OS_NAME="debian${OS_MAJOR_VERSION}"
}

get_centos_version() {
    if [ -f /etc/centos-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/centos-release | cut -f 4 -d ' ' | cut -f 1 -d '.')
    elif [ -f /etc/os-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/os-release | grep VERSION_ID | cut -f 2 -d '=' | sed 's/"//g')
    fi

    if [ $OS_MAJOR_VERSION -eq 8 ]; then
        IS_Stream=$(cat /etc/centos-release | grep Stream)
        if [ "${IS_Stream}" != "" ]; then
            OS_MAJOR_VERSION="${OS_MAJOR_VERSION}s"
        fi
    fi

    OS_NAME="centos${OS_MAJOR_VERSION}"
}

get_tencentos_version() {
    if [ -f /etc/tencentos-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/tencentos-release | awk '{print $4}' | sed 's/\.//g')
        if [ $(echo $OS_MAJOR_VERSION | grep "(") != "" ]; then
            OS_MAJOR_VERSION=$(cat /etc/tencentos-release | awk '{print $3}' | sed 's/\.//g')
        fi
    elif [ -f /etc/os-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/os-release | grep VERSION_ID | cut -f 2 -d '=' | sed 's/"//g' | sed 's/\.//g')
    fi

    OS_NAME="tencentos${OS_MAJOR_VERSION}"
}

get_rocky_version() {
    if [ -f /etc/os-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/os-release | grep VERSION_ID | cut -f 2 -d '=' | sed 's/"//g' | cut -f 1 -d '.')
    elif [ -f /etc/rocky-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/rocky-release | awk '{print $4}' | cut -f 1 -d '.')
    fi

    OS_NAME="rocky_linux${OS_MAJOR_VERSION}"
}

get_aliyun_version() {
    if [ -f /etc/os-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/os-release | grep VERSION_ID | cut -f 2 -d '=' | sed 's/"//g' | cut -f 1 -d '.')
    elif [ -f /etc/alinux-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/alinux-release | awk '{print $7}' | cut -f 1 -d '.')
    fi

    OS_NAME="aliyun${OS_MAJOR_VERSION}"
}

get_anolis_version() {
    if [ -f /etc/os-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/os-release | grep VERSION_ID | cut -f 2 -d '=' | sed 's/"//g' | cut -f 1 -d '.')
    elif [ -f /etc/anolis-release ]; then
        OS_MAJOR_VERSION=$(cat /etc/anolis-release | awk '{print $4}' | cut -f 1 -d '.')
    fi

    if [ $OS_MAJOR_VERSION -eq 8 ]; then
        OS_MAJOR_VERSION=""
    fi
    OS_NAME="anolisos${OS_MAJOR_VERSION}"
}

if [ "$IS_UBUNTU" != "" ]; then
    get_ubuntu_version
elif [ "$IS_DEBIAN" != "" ]; then
    get_debian_version
elif [ "$IS_CENTOS" != "" ]; then
    get_centos_version
elif [ "$IS_ROCKY" != "" ]; then
    get_rocky_version
elif [ "$IS_TENCENTOS" != "" ]; then
    get_tencentos_version
elif [ "$IS_ALIYUN" != "" ]; then
    get_aliyun_version
elif [ "$IS_ANOLIS" != "" ]; then
    get_anolis_version
elif [ "$IS_OPENEULER" != "" ]; then
    get_openeuler_version
elif [ "$IS_EULER" != "" ]; then
    get_euler_version
elif [ "$IS_Amazon" != "" ]; then
    get_amazon_version
elif [ "$IS_UnionTech" != "" ]; then
    get_uniontech_version
elif [ "$IS_DEEPIN" != "" ]; then
    get_deepin_version
elif [ "$IS_KYLIN" != "" ]; then
    get_kylin_version
elif [ "$IS_ALMA" != "" ]; then
    get_almlinux_version
elif [ "$IS_OPENCLOUD" != "" ]; then
    get_opencloudos_version
else
    echo "Not support this OS"
    exit 1
fi

ko_save_path=/www/server/tamper
download_url="${URL}/$OS_BIT/${OS_NAME}/${LAST_NAME}_${KRNL_VERSION}_${END_NAME}"
sign_url="${URL}/$OS_BIT/${OS_NAME}/${LAST_NAME}_${KRNL_VERSION}_${END_SIGN}"
ko_file_tmp=$ko_save_path/tampercore_tmp.ko
ko_file=$ko_save_path/tampercore.ko
if [ ! -d $ko_save_path ];then
    mkdir -p $ko_save_path
fi

wget -O $ko_file_tmp $download_url -T 5
if [ ! -f $ko_file_tmp ];then
    echo "Download $ko_file failed"
    exit 1
fi

# 检查下载的文件是否正常
ko_size=$(ls -l $ko_file_tmp | awk '{print $5}')
if [ $ko_size -lt 10240 ];then
    echo "Download $ko_file failed, file size is too small"
    rm -f $ko_file_tmp
    exit 1
fi

# 检查下载的文件sha256是否正确
which sha256sum > /dev/null 2>&1
if [ $? ];then
    sign=$(curl -sS --connect-timeout 30 -m 5 $sign_url)
    ko_file_sign=$(sha256sum $ko_file_tmp | awk '{print $1}')
    echo "cloud_sign: ${sign}"
    echo "local_sign: ${ko_file_sign}"
    if [ "${ko_file_sign}" != "${sign}" ];then
        echo "Download $ko_file failed, sha256sum error"
        rm -f $ko_file_tmp
        exit 1
    fi
fi

mv -f $ko_file_tmp $ko_file
echo "Download $ko_file success"
echo '======================================================================='
exit 0