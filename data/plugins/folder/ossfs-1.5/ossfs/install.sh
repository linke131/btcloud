#!/bin/bash
PATH=/www/server/panel/pyenv/bin:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'

public_file=/www/server/panel/install/public.sh
if [ ! -f $public_file ]; then
  wget -O $public_file http://download.bt.cn/install/public.sh -T 5
fi
. $public_file
download_Url=$NODE_URL
System_Lib() {
  if [ "${PM}" == "yum" ] || [ "${PM}" == "dnf" ]; then
    Pack="fuse-devel gcc-c++ autoconf automake libuuid-devel openssl-devel libcurl-devel fuse ossfs_1.80.6_centos7.0_x86_64.rpm libxml2-devel automake git make"
  elif [ "${PM}" == "apt-get" ]; then
    Pack="libfuse-dev fuse autoconf uuid-dev libssl-dev libcurl4-openssl-dev automake autotools-dev fuse g++ git libcurl4-openssl-dev libfuse-dev libssl-dev libxml2-dev make pkg-config"
  fi
  ${PM} install ${Pack} -y
}
install_ossfs() {

  if ! command -v ossfs &>/dev/null; then

    if [ ! -d /www/ossfs ]; then
      mkdir /www/ossfs
    fi
    cd /www/ossfs/ || exit
    wget ossfs-master.zip ${download_Url}/src/ossfs-master.zip
    unzip ossfs-master.zip
    cd /www/ossfs/ossfs-master || exit
    ./autogen.sh
    ./configure
    make
    make install
    cd ..
    rm -rf ossfs-master*
  fi
}

install_obsfs() {

  if ! command -v obsfs &>/dev/null; then

    if [ ! -d /www/ossfs ]; then
      mkdir /www/ossfs
    fi
    cd /www/ossfs/ || exit
    wget huaweicloud-obs-obsfs-master.zip ${download_Url}/src/huaweicloud-obs-obsfs-master.zip
    unzip huaweicloud-obs-obsfs-master.zip
    cd huaweicloud-obs-obsfs-master || exit
    sh build.sh
    cd ..
    rm -rf huaweicloud-obs-obsfs*
  fi
}

Install_Ossfs() {
  #安装ossfs
  # wget http://gosspublic.alicdn.com/ossfs/ossfs_1.80.6_centos7.0_x86_64.rpm
  # yum install ossfs_1.80.6_centos7.0_x86_64.rpm

  # btpip install oss2==2.5.0
  # pip install oss2==2.5.0
  #安装cosfs
  mkdir -p /www/ossfs
  if ! command -v cosfs &>/dev/null; then
    wget -O cosfs-master.zip ${download_Url}/src/cosfs-master.zip
    unzip cosfs-master.zip
    cd cosfs-master || exit
    ./autogen.sh
    ./configure
    make
    make install
    cd ..
    rm -rf cosfs-master*
  fi
  mkdir -p /www/server/panel/plugin/ossfs
  #安装ossfs服务
  install_ossfs
  #安装obsfs
  install_obsfs
  #安装s3fs
  if ! command -v s3fs &>/dev/null; then
    wget -O s3fs-fuse-master.zip ${download_Url}/src/s3fs-fuse-master.zip
    unzip s3fs-fuse-master.zip
    cd s3fs-fuse-master || exit
    ./autogen.sh
    ./configure
    make
    make install
  fi
  #安装金山云
  btpip install ks3sdk
  # wget -O /www/server/panel/plugin/ossfs/ossfs_main.py $download_Url/install/plugin/ossfs/ossfs_main.py -T 5
  # wget -O /www/server/panel/plugin/ossfs/index.html $download_Url/install/plugin/ossfs/index.html -T 5
  # wget -O /www/server/panel/plugin/ossfs/info.json $download_Url/install/plugin/ossfs/info.json -T 5
  # wget -O /www/server/panel/plugin/ossfs/icon.png $download_Url/install/plugin/ossfs/icon.png -T 5
  # wget -O /www/server/panel/BTPanel/static/img/soft_ico/ico-ossfs.png $download_Url/install/plugin/ossfs/icon.png -T 5
  \cp -rf /www/server/panel/plugin/ossfs/icon.png /www/server/panel/BTPanel/static/img/soft_ico/ico-ossfs.png
  #安装百度云
  # 	cd $plugin_path/fuse-2.9.4
  #     ./configure
  #     make && make install
  if ! command -v bosfs &>/dev/null; then
    cd /www/server/panel/plugin/ossfs || exit
    tar -xzvf /www/server/panel/plugin/ossfs/bosfs-1.0.0.12.tar.gz
    cd /www/server/panel/plugin/ossfs/bosfs-1.0.0.12 || exit
    sh build.sh
    rm -f /www/server/panel/plugin/ossfs/bosfs-1.0.0.12.tar.gz
  fi
  btpip install oss2==2.5.0
  echo '安装完成' >$install_tmp
}

Uninstall_Ossfs() {
  rm -rf /www/server/panel/plugin/ossfs
}

actionType=$1
if [ "${actionType}" == "install" ]; then
  System_Lib
  Install_Ossfs
else
  Uninstall_Ossfs
fi
