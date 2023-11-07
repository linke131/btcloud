#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
pluginPath=/www/server/panel/plugin/pythonmamager
##online code

Install_PythonMamage()
{
#  if [ ! -f "/usr/bin/virtualenv" ];then
#    if [ -d "/www/server/panel/pyenv" ];then
#      /www/server/panel/pyenv/bin/pip install virtualenv
#      ln -s /www/server/panel/pyenv/bin/virtualenv /usr/bin/virtualenv
#    else
#      pip install virtualenv
#    fi
#
#  fi
	if [ -f "/etc/redhat-release" ];then
	  yum -y install git libffi-devel gcc zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel
	else
	  apt -y install git libffi-dev gcc zlib1g-dev libbz2-dev libssl-dev ncurses-dev libsqlite3-dev libreadline-dev tk-dev libgdbm-dev db4otool libpcap-dev xz-utils
	fi
	#curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
#	cp $pluginPath/pyenv.tar.gz /tmp/pyenv.tar.gz
#	tar -zxf /tmp/pyenv.tar.gz -C /root
#	ln -s /root/.pyenv /.pyenv
#	rm -f /tmp/pyenv.tar.gz
#    env=`grep "pyenv" /root/.bashrc |wc -l`
#    if [ "$env" -eq "0" ];then
#        echo 'export PATH=~/.pyenv/bin:$PATH' >> ~/.bashrc
#        echo 'export PYENV_ROOT=~/.pyenv' >> ~/.bashrc
#        echo 'eval "$(pyenv init -)"' >> ~/.bashrc
#        source ~/.bashrc
#    fi


	mkdir -p $pluginPath
	cp $pluginPath/bt_pym /etc/init.d/bt_pym
	chmod +x /etc/init.d/bt_pym
	systemctl enable bt_pym
	\cp -a -r /www/server/panel/plugin/pythonmamager/icon.png /www/server/panel/BTPanel/static/img/soft_ico/ico-pythonmamager.png
	echo 'Successify'
}

Uninstall_PythonMamage()
{
	rm -rf $pluginPath
	rm -rf /root/.pyenv
	rm -rf /.pyenv
	systemctl disable pythonmamager
	rm -f /etc/init.d/pythonmamager
	systemctl disable bt_pym
	rm -f /etc/init.d/bt_pym
	sed -i "/pyenv/d" /root/.bashrc
	echo 'Successify'
}




if [ "${1}" == 'install' ];then
	Install_PythonMamage
elif [ "${1}" == 'uninstall' ];then
	Uninstall_PythonMamage
fi

