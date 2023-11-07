#!/www/server/panel/pyenv/bin/python3
# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +------------------------------------------------------------------
# | Author: wzz
# | email : help@bt.cn
# +------------------------------------------------------------------
# -------------------------------------------------------------------
# 网站监控报表安装脚本
# -------------------------------------------------------------------

import os, sys, platform, shutil, re, subprocess
import time
from typing import Optional, Dict, Union

os.chdir("/www/server/panel")
sys.path.insert(0, "class")
import public

panel_path = public.get_panel_path()


def get_pack_manager() -> Optional[Union[bool, str]]:
    '''
    获取系统软件包管理器
    @return:
    '''
    if shutil.which("yum") and os.path.isdir("/etc/yum.repos.d"):
        return "yum"
    elif shutil.which("apt") or shutil.which("apt-get") and os.path.isdir("/usr/bin/dpkg"):
        return "apt-get"
    else:
        return False


def get_env() -> Optional[Dict]:
    env = os.environ.copy()
    env["PATH"] = "/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin"
    return env


def get_webserver():
    '''
    获取web服务器类型
    @return:
    '''
    webserver = ''
    if os.path.exists('/www/server/nginx/sbin/nginx'):
        webserver = 'nginx'
    elif os.path.exists('/www/server/apache/bin/httpd'):
        webserver = 'apache'
    elif os.path.exists('/usr/local/lsws/bin/lswsctrl'):
        webserver = 'lswsctrl'
    return webserver


class total_install():
    def __init__(self, download_url: str, pack_manager: str, local_env: Dict, webserver: str):
        self.download_url = download_url
        self.pluginPath = "/www/server/panel/plugin/total"
        self.libraryPath = "/www/server/panel/plugin/total/library"
        self.total_path = "/www/server/total"
        self.remote_dir = "total2"
        self.lua515_install_path = self.total_path + "/lua515"
        self.pack_manager = pack_manager
        self.install_log = ""
        self.local_env = local_env
        self.webserver = webserver

    def download_file(self, local_file: str, source: str, timeout: int = 3, retry: int = 4) -> \
            Optional[bool]:
        os.system("wget -O {} {} --no-check-certificate -T {} -t {}"
                  .format(local_file, source, timeout, retry))
        if not os.path.exists(local_file):
            if retry > 1:
                retry -= 1
                self.download_file(local_file, source, timeout, retry)
            else:
                return False
        else:
            return True

    def shutil_rmtree(self, filename: str) -> None:
        '''
        删除指定文件或文件夹
        @param filename:
        @return:
        '''
        shutil.rmtree(filename, ignore_errors=True)

    def set_ownership(self, directory, user):
        '''
        设置指定目录及目录下所有文件、子目录所属为user
        @param directory:
        @param user:
        @return:
        '''
        import pwd
        uid = pwd.getpwnam(user).pw_uid
        gid = pwd.getpwnam(user).pw_gid

        os.chown(directory, uid, gid)

        for root, dirs, files in os.walk(directory):
            for d in dirs:
                dir_path = os.path.join(root, d)
                os.chown(dir_path, uid, gid)
            for f in files:
                file_path = os.path.join(root, f)
                os.chown(file_path, uid, gid)

    def set_permissions(self, directory, permissions):
        '''
        设置指定目录及目录下所有文件、子目录权限为permissions
        @param directory:
        @param permissions: 传八进制，如0o755
        @return:
        '''
        os.chmod(directory, permissions)

        for root, dirs, files in os.walk(directory):
            for d in dirs:
                dir_path = os.path.join(root, d)
                os.chmod(dir_path, permissions)
            for f in files:
                file_path = os.path.join(root, f)
                os.chmod(file_path, permissions)

    def get_platform(self) -> str:
        '''
        获取系统的平台
        @return:
        '''
        system = platform.system()
        if system == "Linux":
            return "linux"
        elif system == "FreeBSD":
            return "freebsd"
        elif system.startswith("BSD"):
            return "bsd"
        elif system == "Darwin":
            return "macosx"
        elif system.startswith("CYGWIN") or system.startswith("MINGW") or system.startswith("MSYS"):
            return "mingw"
        elif system == "AIX":
            return "aix"
        elif system == "SunOS":
            return "solaris"
        else:
            return "unknown"

    def get_lua_version(self) -> str:
        '''
        获取系统lua版本
        @return:
        '''
        return public.ExecShell("lua -e 'print(_VERSION:sub(5))'")[0].strip()

    def install_lua(self) -> Optional[bool]:
        '''
        安装lua
        @return:
        '''
        # 安装lua515
        install_path = self.lua515_install_path
        if os.path.isfile("{}/bin/lua".format(install_path)):
            os.system("rm -rf /usr/bin/lua")
            os.system("ln -sf {}/bin/lua /usr/bin/lua".format(install_path))
            return True

        lua_version = "lua-5.1.5"
        package_name = "{}.tar.gz".format(lua_version)
        url = "{}/install/plugin/{}/library/{}".format(self.download_url, self.remote_dir, package_name)
        os.makedirs(install_path, exist_ok=True)

        tmp_dir = "/tmp/{}".format(lua_version)
        os.makedirs(tmp_dir, exist_ok=True)
        os.chdir(tmp_dir)

        if not os.path.isfile("{}/{}".format(self.libraryPath, package_name)):
            self.download_file("{}/{}".format(self.libraryPath, package_name), url, 10, 3)
        os.system("tar xvf {}/{}".format(self.libraryPath, package_name))
        os.chdir(lua_version)

        os_platform = self.get_platform()
        if os_platform == "unknown":
            os_platform = "linux"
        subprocess.run(["make", os_platform, "install", "INSTALL_TOP={}".format(install_path)], env=self.local_env, check=True)
        os.chdir(self.total_path)
        self.shutil_rmtree(tmp_dir)

        if not os.path.isfile("{}/bin/lua".format(install_path)): return False
        os.system("rm -rf /usr/bin/lua")
        os.system("ln -sf {}/bin/lua /usr/bin/lua".format(install_path))

        lua_version = self.get_lua_version()
        if lua_version != "5.1": return False

        # 安装apache的lua
        if self.webserver == "apache":
            lua_so = "/www/server/apache/modules/mod_lua.so"
            apache_path = "/www/server/apache"
            if os.path.isfile(lua_so): return True

            os.chdir(apache_path)
            apache_dir = "httpd-2.4.56"
            apr_dir = "apr-1.6.3"
            apr_util_dir = "apr-util-1.6.1"
            if not os.path.isdir("{}/src".format(apache_path)):
                if not os.path.isfile("{}/{}.tar.gz".format(self.libraryPath, apache_dir)):
                    apache_url = "{}/src/{}.tar.gz".format(self.download_url, apache_dir)
                    self.download_file("{}/{}.tar.gz".format(self.libraryPath, apache_dir), apache_url, 10, 3)
                    os.system("tar xvf {}/{}.tar.gz".format(self.libraryPath, apache_dir))
                    os.system("mv -f {} src".format(apache_dir))
            os.chdir("{}/src/srclib".format(apache_path))

            if not os.path.isfile("{}/{}.tar.gz".format(self.libraryPath, apr_dir)):
                apr_url = "{}/src/{}.tar.gz".format(self.download_url, apr_dir)
                self.download_file("{}/{}.tar.gz".format(self.libraryPath, apr_dir), apr_url, 10, 3)
                os.system("tar xvf {}/{}.tar.gz".format(self.libraryPath, apr_dir))
                os.system("mv -f {} apr".format(apr_dir))

            if not os.path.isfile("{}/{}.tar.gz".format(self.libraryPath, apr_util_dir)):
                apr_url = "{}/src/{}.tar.gz".format(self.download_url, apr_util_dir)
                self.download_file("{}/{}.tar.gz".format(self.libraryPath, apr_util_dir), apr_url, 10, 3)
                os.system("tar xvf {}/{}.tar.gz".format(self.libraryPath, apr_util_dir))
                os.system("mv -f {} apr-util".format(apr_util_dir))
            os.chdir("{}/src".format(apache_path))
            command = ["./configure", "--prefix=/www/server/apache", "--enable-lua"]
            subprocess.run(command, cwd="/www/server/apache/src", env=self.local_env, check=True)
            subprocess.run("make", cwd="/www/server/apache/src/modules/lua", check=True)
            subprocess.run(["make", "install"], cwd="/www/server/apache/src/modules/lua", check=True)
            if not os.path.isfile(lua_so):
                return False
        return True

    def install_sqlite3(self) -> Optional[bool]:
        '''
        安装luarocks\lsqlite3\csjon
        @return:
        '''
        # 安装luarocks包管理器
        if not shutil.which("luarocks") or str(os.system("luarocks --version")) != "0":
            luarocks_version = "luarocks-3.9.2"
            luarocks_dir = "/tmp/{}".format(luarocks_version)
            os.chdir(self.total_path)
            if os.path.isdir(luarocks_dir): self.shutil_rmtree(luarocks_dir)

            luarocks_url = "{}/install/plugin/{}/library/{}.tar.gz".format(self.download_url, self.remote_dir, luarocks_version)
            if not os.path.isfile("{}/{}.tar.gz".format(self.libraryPath, luarocks_version)):
                self.download_file("{}/{}.tar.gz".format(self.libraryPath, luarocks_version), luarocks_url, 10, 3)

            os.chdir("/tmp")
            os.system("tar xvf {}/{}.tar.gz".format(self.libraryPath, luarocks_version))
            os.chdir(luarocks_dir)

            command = [
                "./configure",
                "--with-lua-include={}/include".format(self.lua515_install_path),
                "--with-lua-bin={}/bin".format(self.lua515_install_path)
            ]
            subprocess.run(command, env=self.local_env, check=True)
            subprocess.run(["make", "-I", "{}/bin".format(self.lua515_install_path)], env=self.local_env, check=True)
            subprocess.run(["make", "install"], env=self.local_env, check=True)

            os.chdir(self.total_path)
            self.shutil_rmtree(luarocks_dir)
            self.shutil_rmtree("/tmp/{}.tar.gz".format(luarocks_version))

        # 将lua的包管理器的lua路劲重新指向lua515
        if shutil.which("luarocks") and str(os.system("luarocks --version")) == "0":
            luarocks_lua_dir = public.ExecShell("luarocks config variables.LUA_DIR")[0]
            if os.path.isdir(self.lua515_install_path):
                if luarocks_lua_dir != self.lua515_install_path:
                    if not os.path.isdir("/root/.luarocks/"): os.makedirs("/root/.luarocks/")
                    os.system("luarocks config variables.LUA {}/bin/lua".format(self.lua515_install_path))
                    os.system("luarocks config variables.LUA_DIR {}".format(self.lua515_install_path))
                    os.system("luarocks config variables.LUA_BINDIR {}/bin".format(self.lua515_install_path))
                    os.system("luarocks config variables.LUA_INCDIR {}/include".format(self.lua515_install_path))

        # 安装sqlite3，并配置nginx的SQLite3插件
        if shutil.which("luarocks") and str(os.system("luarocks --version")) == "0":
            if self.pack_manager == "yum":
                is_install = public.ExecShell("rpm -qa |grep sqlite-devel")[0]
                if not is_install: os.system("{} install -y sqlite-devel".format(self.pack_manager))
            elif self.pack_manager == "apt-get":
                is_install = public.ExecShell("dpkg -l|grep libsqlite3-dev")[0]
                if not is_install: os.system("{} install -y libsqlite3-dev".format(self.pack_manager))

            luasocket_check = public.ExecShell("luarocks list")[0]
            if "lsqlite3" not in luasocket_check:
                os.system("luarocks install lsqlite3 --server https://luarocks.cn")
                luasocket_check = public.ExecShell("luarocks list")[0]

            total_lsqlite3 = os.path.exists("{}/lsqlite3.so".format(self.total_path))
            if "lsqlite3" not in luasocket_check or not total_lsqlite3:
                lsqlite3_url = "{}/install/plugin/{}/library/lsqlite3_fsl09y.zip".format(self.download_url, self.remote_dir)
                if not os.path.isfile("{}/lsqlite3_fsl09y.zip".format(self.libraryPath)):
                    self.download_file("{}/lsqlite3_fsl09y.zip".format(self.libraryPath), lsqlite3_url, 10, 3)

                subprocess.run(["unzip", "lsqlite3_fsl09y.zip"], cwd=self.libraryPath, check=True)
                lsqlite3_dir = "{}/lsqlite3_fsl09y".format(self.libraryPath)
                subprocess.run(["make"], cwd=lsqlite3_dir, env=self.local_env, check=True)
                os.system("\cp -r {}/lsqlite3.so {}/lsqlite3.so".format(lsqlite3_dir, self.total_path))

                if not os.path.isfile("{}/lsqlite3.so".format(self.total_path)):
                    lsqlite3so_url = "{}/install/plugin/{}/library/lsqlite3.so".format(self.download_url, self.remote_dir)
                    self.download_file("{}/lsqlite3.so".format(self.libraryPath), lsqlite3so_url, 10, 3)
                    os.system("\cp -a -r {}/lsqlite3.so {}/lsqlite3.so".format(self.libraryPath, self.total_path))
                else:
                    os.system("\cp -a -r {}/lsqlite3.so {}/lsqlite3.so".format(lsqlite3_dir, self.total_path))
                os.chdir(self.total_path)
                self.shutil_rmtree(lsqlite3_dir)
                self.shutil_rmtree("/tmp/lsqlite3_fsl09y.zip")
        else:
            print("luarocks 包管理器异常，请重新安装监控报表!")
            return False
        return True

    def get_system_lua_info(self) -> Optional[Dict]:
        '''
        获取系统自带lua相关信息
        @return:
        '''
        include_path = ''
        if os.path.exists('/usr/include/lua.h'):
            include_path = '/usr/include/'
        elif os.path.exists('/usr/include/lua5.1/lua.h'):
            include_path = '/usr/include/lua5.1'
        elif os.path.exists('/usr/include/lua5.3/lua.h'):
            include_path = '/usr/include/lua5.3'
        elif os.path.exists('/usr/local/include/luajit-2.0/lua.h'):
            include_path = '/usr/local/include/luajit-2.0/'
        elif os.path.exists('/usr/include/lua5.1/'):
            include_path = '/usr/include/lua5.1/'
        elif os.path.exists('/usr/local/include/luajit-2.1/'):
            include_path = '/usr/local/include/luajit-2.1/'

        is_lua53 = ""
        version = self.get_lua_version()
        if version == "5.3" and os.path.isdir("/usr/lib64/lua"):
            lua_bin = "/usr/bin/"
            is_lua53 = "yes"
        elif version == "5.3" and os.path.isfile("/usr/lib64/lua"):
            lua_bin = "/usr/lib64"
            is_lua53 = "yes"
        elif os.path.isfile("/usr/bin/lua"):
            lua_bin = "/usr/bin/"
        elif os.path.isfile("/usr/lib/lua"):
            lua_bin = "/usr/lib/"
        else:
            lua_bin = os.path.dirname(os.popen("which lua").read().strip())

        return {"include_path": include_path, "lua_bin": lua_bin, "is_lua53": is_lua53}

    def install_socket(self) -> Optional[bool]:
        '''
        安装lua socket
        @return:
        '''
        if not os.path.isfile("/usr/local/lib/lua/5.1/socket/core.so"):
            luasocket_check = public.ExecShell("luarocks list")[0]
            if "luasocket" not in luasocket_check:
                os.system("luarocks install luasocket --server https://luarocks.cn")
            luasocket_check = public.ExecShell("luarocks list")[0]
            if "luasocket" in luasocket_check:
                return True
            lua_socket_dir = "luasocket-master"
            if not os.path.isfile("{}/luasocket-master.zip".format(self.libraryPath)):
                lua_socket_url = "{}/install/src/{}.zip".format(self.download_url, lua_socket_dir)
                self.download_file("{}/luasocket-master.zip".format(self.libraryPath),
                                   lua_socket_url, 10, 3)
            os.chdir("/tmp")
            os.system("unzip {}/{}.zip".format(self.libraryPath, lua_socket_dir))
            os.chdir(lua_socket_dir)
            # os.system("make && make install")
            subprocess.run(["make"], env=self.local_env, check=True)
            subprocess.run(["make", "install"], env=self.local_env, check=True)
            os.chdir(self.total_path)
            self.shutil_rmtree("/tmp/{}".format(lua_socket_dir))
            self.shutil_rmtree("/tmp/{}.zip".format(lua_socket_dir))

        if not os.path.isdir("/usr/share/lua/5.1/socket"):
            if os.path.isdir("/usr/lib64/lua/5.1"):
                dirs_to_remove = ("/usr/lib64/lua/5.1/socket", "/usr/lib64/lua/5.1/mime")
                for dir_path in dirs_to_remove:
                    self.shutil_rmtree(dir_path)
                os.makedirs("/usr/lib64/lua/5.1", exist_ok=True)
                os.symlink("/usr/local/lib/lua/5.1/socket", "/usr/lib64/lua/5.1/socket")
                os.symlink("/usr/local/lib/lua/5.1/mime", "/usr/lib64/lua/5.1/mime")
            else:
                dirs_to_remove = ("/usr/lib/lua/5.1/socket", "/usr/lib/lua/5.1/mime")
                for dir_path in dirs_to_remove:
                    self.shutil_rmtree(dir_path)
                os.makedirs("/usr/lib/lua/5.1", exist_ok=True)
                if not os.path.exists("/usr/lib/lua/5.1/socket"):
                    os.symlink("/usr/local/lib/lua/5.1/socket", "/usr/lib/lua/5.1/socket")
                if not os.path.exists("/usr/lib/lua/5.1/mime"):
                    os.symlink("/usr/local/lib/lua/5.1/mime", "/usr/lib/lua/5.1/mime")

            dirs_to_remove = (
                '/usr/share/lua/5.1/mime.lua',
                '/usr/share/lua/5.1/socket.lua',
                '/usr/share/lua/5.1/socket'
            )
            for dir_path in dirs_to_remove:
                self.shutil_rmtree(dir_path)
            os.makedirs("/usr/share/lua/5.1", exist_ok=True)
            if not os.path.exists("/usr/share/lua/5.1/mime.lua"):
                os.symlink("/usr/local/share/lua/5.1/mime.lua", "/usr/share/lua/5.1/mime.lua")
            if not os.path.exists("/usr/share/lua/5.1/socket.lua"):
                os.symlink("/usr/local/share/lua/5.1/socket.lua", "/usr/share/lua/5.1/socket.lua")
            if not os.path.exists("/usr/share/lua/5.1/socket"):
                os.symlink("/usr/local/share/lua/5.1/socket", "/usr/share/lua/5.1/socket")
        return True

    def install_cjson_2(self):
        '''
        安装luajit cjson
        @return:
        '''
        lua_cjson_210_dir = "lua-cjson-2.1.0"
        if not os.path.isfile("{}/{}.tar.gz".format(self.libraryPath, lua_cjson_210_dir)):
            lua_cjson_210_url = "{}/install/src/{}.tar.gz".format(self.download_url, lua_cjson_210_dir)
            self.download_file("{}/{}.tar.gz".format(self.libraryPath, lua_cjson_210_dir), lua_cjson_210_url, 10, 3)

        os.chdir("/tmp")
        os.system("tar xvf {}/{}.tar.gz".format(self.libraryPath, lua_cjson_210_dir))
        os.chdir(lua_cjson_210_dir)
        subprocess.run(["make", "clean"], env=self.local_env, check=True)
        os.system("sed -i 's#^PREFIX =            /usr/local$#PREFIX =            /www/server/total/lua515#' Makefile")
        os.system("sed -i 's#^LUA_INCLUDE_DIR =   $(PREFIX)/include/luajit-2.0$#LUA_INCLUDE_DIR =   $(PREFIX)/include#' Makefile")
        subprocess.run(["make"], env=self.local_env, check=True)
        subprocess.run(["make", "install"], env=self.local_env, check=True)
        os.system("\cp -r /usr/local/lib/lua/5.1/cjson.so /usr/local/lib/lua/5.1/cjson.so~")
        os.system("\cp -r {}/lib/lua/5.1/cjson.so /usr/local/lib/lua/5.1/cjson.so".format(self.lua515_install_path))
        os.system("\cp -r {}/lib/lua/5.1/cjson.so {}/".format(self.lua515_install_path, self.total_path))
        os.system("ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib64/lua/5.1/cjson.so")
        os.system("ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib/lua/5.1/cjson.so")
        os.chmod("{}/cjson.so".format(self.total_path), 0o755)
        os.chown("{}/cjson.so".format(self.total_path), 0, 0)
        os.chmod("/usr/local/lib/lua/5.1/cjson.so", 0o755)
        os.chown("/usr/local/lib/lua/5.1/cjson.so", 0, 0)
        os.chdir(self.total_path)
        self.shutil_rmtree("/tmp/{}".format(lua_cjson_210_dir))
        self.shutil_rmtree("/tmp/{}.tar.gz".format(lua_cjson_210_dir))

    def install_luajit2(self):
        '''
        安装luajit-2.1
        @return:
        '''
        lua_jit_ver = "2.1.0-beta3"
        lua_jit_inc_path = "luajit-2.1"
        lua_jit_21_exe = "/usr/local/bin/luajit-2.1.0-beta3"
        is_lua_jit_21 = public.ExecShell("luajit -v | grep -E '2.1.0-beta3|2.1.0-beta2|2.1.0-beta1'")[0]
        if (not os.path.isfile("/usr/local/lib/libluajit-5.1.so") or
            not os.path.isfile("/usr/local/include/{}/luajit.h".format(lua_jit_inc_path)) or
            not os.path.isfile(lua_jit_21_exe)):
            if not os.path.isfile("{}/LuaJIT-{}.tar.gz".format(self.libraryPath, lua_jit_ver)):
                lua_jit_url = "{}/install/src/LuaJIT-{}.tar.gz".format(self.download_url, lua_jit_ver)
                self.download_file("{}/LuaJIT-{}.tar.gz".format(self.libraryPath, lua_jit_ver), lua_jit_url, 10, 3)

            os.chdir("/tmp")
            os.system("tar xvf {}/LuaJIT-{}.tar.gz".format(self.libraryPath, lua_jit_ver))
            os.chdir("/tmp/LuaJIT-{}".format(lua_jit_ver))

            subprocess.run(["make"], env=self.local_env, check=True)
            subprocess.run(["make", "install"], env=self.local_env, check=True)
            os.system("export LUAJIT_LIB=/usr/local/lib")
            os.system("export LUAJIT_INC=/usr/local/include/{}".format(lua_jit_inc_path))
            os.system("ln -sf /usr/local/lib/libluajit-5.1.so.2 /usr/local/lib64/libluajit-5.1.so.2")
            os.system("echo \"/usr/local/lib\" >> /etc/ld.so.conf")
            os.system("ldconfig")
            os.chdir(self.total_path)
            self.shutil_rmtree("/tmp/LuaJIT-{}".format(lua_jit_ver))
            self.shutil_rmtree("{}/LuaJIT-{}.tar.gz".format(self.libraryPath, lua_jit_ver))

        if public.ExecShell("{} -v".format(lua_jit_21_exe))[0] and not is_lua_jit_21:
            os.system("rm -rf /usr/local/bin/luajit")
            os.system("ln -sf {} /usr/local/bin/luajit".format(lua_jit_21_exe))
        is_lua_jit_21 = public.ExecShell("luajit -v | grep -E '2.1.0-beta3|2.1.0-beta2|2.1.0-beta1'")[0]
        if not is_lua_jit_21:
            return False
        return True


    def install_cjson(self) -> Optional[bool]:
        '''
        如无cjson，则再次尝试安装
        @return:
        '''
        if self.pack_manager == "yum":
            is_install = public.ExecShell("rpm -qa |grep lua-devel")[0]
            if not is_install: os.system("yum install -y lua-devel lua lua-socket")
        elif self.pack_manager == "apt-get":
            is_install = public.ExecShell("dpkg -l|grep liblua5.1-0-dev")[0]
            if not is_install:
                os.system("apt-get install lua5.1 lua5.1-dev lua5.1-cjson lua5.1-socket -y")

        lua51_cjson_file = "/usr/local/lib/lua/5.1/cjson.so"

        is_lua_jit_21 = public.ExecShell("luajit -v | grep -E '2.1.0-beta3|2.1.0-beta2|2.1.0-beta1'")[0]
        if os.path.isfile(lua51_cjson_file) and is_lua_jit_21:
            is_jit_cjson = public.ExecShell("luajit -e \"require 'cjson'\" 2>&1|grep 'undefined symbol: luaL_setfuncs'")[0]
            if not is_jit_cjson:
                os.system("\cp -r /usr/local/lib/lua/5.1/cjson.so {}/cjson.so".format(self.total_path))
                if os.path.isdir("/usr/lib64/lua/5.1"):
                    os.system("ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib64/lua/5.1/cjson.so")
                if os.path.isdir("/usr/lib/lua/5.1"):
                    os.system("ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib/lua/5.1/cjson.so")
                os.chmod("{}/cjson.so".format(self.total_path), 0o755)
                os.chown("{}/cjson.so".format(self.total_path), 0, 0)
                os.chmod("/usr/local/lib/lua/5.1/cjson.so", 0o755)
                os.chown("/usr/local/lib/lua/5.1/cjson.so", 0, 0)
                return True
        else:
            self.install_luajit2()

        if not os.path.isfile(lua51_cjson_file):
            self.install_cjson_2()
            return True

        is_lua_jit_21 = public.ExecShell("luajit -v | grep -E '2.1.0-beta3|2.1.0-beta2|2.1.0-beta1'")[0]
        if os.path.isfile(lua51_cjson_file) and is_lua_jit_21:
            is_jit_cjson = public.ExecShell("luajit -e \"require 'cjson'\" 2>&1|grep 'undefined symbol: luaL_setfuncs'")[0]
            if not is_jit_cjson:
                os.system("\cp -r /usr/local/lib/lua/5.1/cjson.so {}/cjson.so".format(self.total_path))
                if os.path.isdir("/usr/lib64/lua/5.1"):
                    os.system("ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib64/lua/5.1/cjson.so")
                if os.path.isdir("/usr/lib/lua/5.1"):
                    os.system("ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib/lua/5.1/cjson.so")
                os.chmod("{}/cjson.so".format(self.total_path), 0o755)
                os.chown("{}/cjson.so".format(self.total_path), 0, 0)
                os.chmod("/usr/local/lib/lua/5.1/cjson.so", 0o755)
                os.chown("/usr/local/lib/lua/5.1/cjson.so", 0, 0)
                return True
            else:
                self.install_cjson_2()
                return True
        else:
            os.system("\cp -r /usr/local/lib/lua/5.1/cjson.so {}/cjson.so".format(self.total_path))
            if os.path.isdir("/usr/lib64/lua/5.1"):
                os.system("ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib64/lua/5.1/cjson.so")
            if os.path.isdir("/usr/lib/lua/5.1"):
                os.system("ln -sf /usr/local/lib/lua/5.1/cjson.so /usr/lib/lua/5.1/cjson.so")

            os.chmod("{}/cjson.so".format(self.total_path), 0o755)
            os.chown("{}/cjson.so".format(self.total_path), 0, 0)
            os.chmod("/usr/local/lib/lua/5.1/cjson.so", 0o755)
            os.chown("/usr/local/lib/lua/5.1/cjson.so", 0, 0)

            if not os.path.isfile(lua51_cjson_file):
                luasocket_check = public.ExecShell("luarocks list")[0]
                if "lua-cjson" not in luasocket_check:
                    os.system("luarocks install lua-cjson --server https://luarocks.cn")
                luasocket_check = public.ExecShell("luarocks list")[0]
                if "lua-cjson" in luasocket_check:
                    return True
                return False

    def install_pdf_library(self) -> Optional[bool]:
        '''
        安装pdf扩展、命令
        @return:
        '''
        msyh_path = "/usr/share/fonts/msyh.ttf"
        if not os.path.isfile(msyh_path):
            msyh_url = "{}/install/plugin/{}/library/msyh.ttf".format(self.download_url, self.remote_dir)
            self.download_file("{}/msyh.ttf".format(self.libraryPath), msyh_url, 10, 3)
            os.system("\cp -a -r {}/msyh.ttf {}".format(self.libraryPath, msyh_path))
            self.shutil_rmtree("{}/msyh.ttf".format(self.libraryPath))

        # 安装python pdf库
        if shutil.which("btpip"):
            pdfkit_check = public.ExecShell("btpip list|grep pdfkit")[0]
            if "pdfkit" not in pdfkit_check: os.system("btpip install pdfkit")
        else:
            pdfkit_check = public.ExecShell("pip list|grep pdfkit")[0]
            if "pdfkit" not in pdfkit_check: os.system("pip install pdfkit")

        if shutil.which("wkhtmltopdf"):
            return True

        is_aarch = public.is_aarch()
        if is_aarch:
            # 安装wkhtmltopdf命令，redhat
            is_8 = False
            redhat_file = "/etc/redhat-release"
            os_file = "/etc/os-release"
            os_release = public.ReadFile(os_file).split("\n")
            if any("centos" in o.lower() or "Anolis" in o.lower() for o in os_release): is_8 = True
            if any("Huawei Cloud EulerOS" in o.lower() or "hce" in o.lower() for o in os_release): is_8 = True
            if os.path.isfile(redhat_file) or is_8:
                os_list = ("6", "7", "8")
                os_version = None
                redhat_release = public.ReadFile(redhat_file) if os.path.isfile(redhat_file) else ""
                match = re.search(r'.* ([0-9]+)\..*', redhat_release)
                if match and match.group(1) in os_list: os_version = match.group(1)

                wkhtmltox_path = None
                wkhtmltox_url = None
                is_8check = False
                if os_version:
                    wkhtmltox_path = "{}/wkhtmltox-0.12.6-1{}{}.aarch64.rpm".format(self.libraryPath, ".centos", os_version)
                    wkhtmltox_url = "{}/install/plugin/{}/library/wkhtmltox-0.12.6-1{}{}.aarch64.rpm" \
                        .format(self.download_url, self.remote_dir, ".centos", os_version)
                if redhat_release == "CentOS Stream release 9":
                    wkhtmltox_path = "{}/wkhtmltox-0.12.6.1{}.aarch64.rpm".format(self.libraryPath, "-2.almalinux9")
                    wkhtmltox_url = "{}/install/plugin/{}/library/wkhtmltox-0.12.6.1{}.aarch64.rpm" \
                        .format(self.download_url, self.remote_dir, "-2.almalinux9")
                if redhat_release == "CentOS Stream release 8": is_8check = True
                if not wkhtmltox_path:
                    if any("8." in o.lower() or "Huawei Cloud EulerOS" in o.lower() or "hce" in o.lower() for o in os_release):
                        is_8check = True
                    if any("platform:oc8" in o.lower() or
                           "platform:al8" in o.lower() or
                           "platform:el8" in o.lower() or
                           "platform:an8" in o.lower() for o in os_release):
                        is_8check = True
                if is_8check:
                    wkhtmltox_path = "{}/wkhtmltox-0.12.6.1{}.x86_64.rpm".format(self.libraryPath, "-2.almalinux8")
                    wkhtmltox_url = "{}/install/plugin/{}/library/wkhtmltox-0.12.6.1{}.aarch64.rpm"\
                        .format(self.download_url, self.remote_dir, "-2.almalinux8")

                if wkhtmltox_path and wkhtmltox_url:
                    self.download_file(wkhtmltox_path, wkhtmltox_url, 10, 3)
                    os.system("yum install -y {}".format(wkhtmltox_path))
                    if not shutil.which("wkhtmltopdf"):
                        return False
                return True

            # ubuntu/debian系列系统安装wkhtmltox
            deb_version_file = "/etc/issue"
            redhat_release = public.ReadFile(deb_version_file).strip("\n")
            try:
                ub_version = re.search(r"Ubuntu\s+(\d+)\.\d+", redhat_release).group(1)
            except:
                ub_version = None
            if not ub_version:
                db_version = re.search(r"(\d+)", redhat_release).group(1)
                deb_install_file = ""
                if db_version == "9":
                    deb_install_file = 'wkhtmltox_0.12.6-1.stretch_arm64.deb'
                elif db_version == "10":
                    deb_install_file = 'wkhtmltox_0.12.6-1.buster_arm64.deb'
                elif db_version == "11":
                    deb_install_file = 'wkhtmltox_0.12.6.1-2.bullseye_arm64.deb'
                elif db_version == "12":
                    deb_install_file = 'wkhtmltox_0.12.6.1-3.bookworm_arm64.deb'
                deb_install_url = "{}/install/plugin/{}/library/{}" \
                    .format(self.download_url, self.remote_dir, deb_install_file)
            else:
                deb_install_file = ""
                if ub_version == "22":
                    deb_install_file = "wkhtmltox_0.12.6.1-2.jammy_arm64.deb"
                elif ub_version == "20":
                    deb_install_file = "wkhtmltox_0.12.6-1.focal_arm64.deb"
                elif ub_version == "18":
                    deb_install_file = "wkhtmltox_0.12.6-1.bionic_arm64.deb"
                elif ub_version == "16":
                    deb_install_file = "wkhtmltox_0.12.6-1.xenial_arm64.deb"
                deb_install_url = "{}/install/plugin/{}/library/{}"\
                    .format(self.download_url, self.remote_dir, deb_install_file)

            self.download_file("{}/{}".format(self.libraryPath, deb_install_file), deb_install_url, 10, 3)
            os.system("apt install -y {}/{}".format(self.libraryPath, deb_install_file))
            if shutil.which("wkhtmltopdf"):
                return True
            return False

        # 安装wkhtmltopdf命令，redhat
        is_8 = False
        redhat_file = "/etc/redhat-release"
        os_file = "/etc/os-release"
        os_release = public.ReadFile(os_file).split("\n")
        if any("centos" in o.lower() or "Anolis" in o.lower() for o in os_release): is_8 = True
        if any("Huawei Cloud EulerOS" in o.lower() or "hce" in o.lower() for o in os_release): is_8 = True
        if os.path.isfile(redhat_file) or is_8:
            os_list = ("6", "7", "8")
            os_version = None
            redhat_release = public.ReadFile(redhat_file) if os.path.isfile(redhat_file) else ""
            match = re.search(r'.* ([0-9]+)\..*', redhat_release)
            if match and match.group(1) in os_list: os_version = match.group(1)

            wkhtmltox_path = None
            wkhtmltox_url = None
            is_8check = False
            if os_version:
                wkhtmltox_path = "{}/wkhtmltox-0.12.6-1{}{}.x86_64.rpm".format(self.libraryPath, ".centos", os_version)
                wkhtmltox_url = "{}/install/plugin/{}/library/wkhtmltox-0.12.6-1{}{}.x86_64.rpm" \
                    .format(self.download_url, self.remote_dir, ".centos", os_version)
            if redhat_release == "CentOS Stream release 9":
                wkhtmltox_path = "{}/wkhtmltox-0.12.6.1{}.x86_64.rpm".format(self.libraryPath, "-2.almalinux9")
                wkhtmltox_url = "{}/install/plugin/{}/library/wkhtmltox-0.12.6.1{}.x86_64.rpm" \
                    .format(self.download_url, self.remote_dir, "-2.almalinux9")
            if redhat_release == "CentOS Stream release 8": is_8check = True
            if not wkhtmltox_path:
                if any("8." in o.lower() or "Huawei Cloud EulerOS" in o.lower() or "hce" in o.lower() for o in os_release):
                    is_8check = True
                if any("platform:oc8" in o.lower() or
                       "platform:al8" in o.lower() or
                       "platform:el8" in o.lower() or
                       "platform:an8" in o.lower() for o in os_release):
                    is_8check = True
            if is_8check:
                wkhtmltox_path = "{}/wkhtmltox-0.12.6.1{}.x86_64.rpm".format(self.libraryPath, "-2.almalinux8")
                wkhtmltox_url = "{}/install/plugin/{}/library/wkhtmltox-0.12.6.1{}.x86_64.rpm"\
                    .format(self.download_url, self.remote_dir, "-2.almalinux8")

            if wkhtmltox_path and wkhtmltox_url:
                self.download_file(wkhtmltox_path, wkhtmltox_url, 10, 3)
                os.system("yum install -y {}".format(wkhtmltox_path))
                if not shutil.which("wkhtmltopdf"):
                    return False
            return True

        # ubuntu/debian系列系统安装wkhtmltox
        deb_version_file = "/etc/issue"
        redhat_release = public.ReadFile(deb_version_file).strip("\n")
        try:
            ub_version = re.search(r"Ubuntu\s+(\d+)\.\d+", redhat_release).group(1)
        except:
            ub_version = None
        if not ub_version:
            db_version = re.search(r"(\d+)", redhat_release).group(1)
            deb_install_file = ""
            if db_version == "9":
                deb_install_file = 'wkhtmltox_0.12.6-1.stretch_amd64.deb'
            elif db_version == "10":
                deb_install_file = 'wkhtmltox_0.12.6-1.buster_amd64.deb'
            elif db_version == "11":
                deb_install_file = 'wkhtmltox_0.12.6.1-2.bullseye_amd64.deb'
            elif db_version == "12":
                deb_install_file = 'wkhtmltox_0.12.6.1-3.bookworm_amd64.deb'
            deb_install_url = "{}/install/plugin/{}/library/{}" \
                .format(self.download_url, self.remote_dir, deb_install_file)
        else:
            deb_install_file = ""
            if ub_version == "22":
                deb_install_file = "wkhtmltox_0.12.6.1-2.jammy_amd64.deb"
            elif ub_version == "20":
                deb_install_file = "wkhtmltox_0.12.6-1.focal_amd64.deb"
            elif ub_version == "18":
                deb_install_file = "wkhtmltox_0.12.6-1.bionic_amd64.deb"
            elif ub_version == "16":
                deb_install_file = "wkhtmltox_0.12.6-1.xenial_amd64.deb"
            deb_install_url = "{}/install/plugin/{}/library/{}" \
                .format(self.download_url, self.remote_dir, deb_install_file)

        self.download_file("{}/{}".format(self.libraryPath, deb_install_file), deb_install_url, 10, 3)
        os.system("apt install -y {}/{}".format(self.libraryPath, deb_install_file))
        if shutil.which("wkhtmltopdf"):
            return True
        return False

    def install_ip_library(self) -> Optional[bool]:
        '''
        安装ip库
        @return:
        '''
        if not os.path.isfile("{}/ip.db".format(self.libraryPath)):
            ip_url = "{}/install/plugin/{}/library/ip.db".format(self.download_url, self.remote_dir)
            self.download_file("{}/ip.db".format(self.libraryPath), ip_url, 10, 3)
            if not os.path.isfile("{}/ip.db".format(self.libraryPath)):
                return False
        return True

    def install_environment(self) -> Optional[bool]:
        '''
        环境安装总方法
        @return:
        '''
        if self.webserver not in ['nginx', 'apache']:
            print("仅支持nginx或apache!")
            return False

        if not os.path.isfile("/usr/include/linux/limits.h"):
            if self.pack_manager == "yum":
                os.system("{} install kernel-headers -y".format(self.pack_manager))
            elif self.pack_manager == "apt-get":
                os.system("{} install linux-headers-$(uname -r)".format(self.pack_manager))

        print("正在检测lua相关环境,请勿终止操作...")
        msg = "执行到{}报错了,请联系堡塔运维!"
        print("正在检查lua_jit环境")
        self.install_luajit2()
        print("正在检查lua环境")
        if not self.install_lua():
            self.install_log = msg.format("self.install_lua()")
            return False
        print("正在检查lua_cjson环境")
        if not self.install_cjson():
            self.install_log = msg.format("self.install_cjson()")
            return False
        print("正在检查数据库环境")
        if not self.install_sqlite3():
            self.install_log = msg.format("self.install_sqlite3()")
            return False
        print("正在检查python pdf环境")
        if not self.install_pdf_library():
            self.install_log = msg.format("self.install_pdf_library()")
            return False
        print("正在检查ip库")
        if not self.install_ip_library():
            self.install_log = msg.format("self.install_ip_library()")
            return False
        if self.webserver == "apache":
            if not self.install_socket():
                self.install_log = msg.format("self.get_webserver()")
                return False
        print("lua相关环境检测完成!")
        return True

    def install_total(self) -> Optional[bool]:
        os.makedirs(self.total_path, exist_ok=True)
        os.makedirs(self.libraryPath, exist_ok=True)

        if not shutil.which("gcc") or not shutil.which("g++"):
            if self.pack_manager == "yum":
                os.system("{} install -y gcc gcc-c++".format(self.pack_manager))
            elif self.pack_manager == "apt-get":
                os.system("{} install -y gcc g++".format(self.pack_manager))

        # 安装lua环境
        if not self.install_environment(): return False

        # 安装监控报表相关代码文件
        os.chdir("/tmp")
        import pwd
        www_uid = pwd.getpwnam('www').pw_uid
        www_gid = pwd.getpwnam('www').pw_gid

        debug_file = os.path.join(self.total_path, "debug.log")
        if not os.path.exists(debug_file): open(debug_file, 'a').close()
        os.chown(debug_file, www_uid, www_gid)

        if os.path.isfile("mv -f {}/panelMonitor.py".format(self.pluginPath)):
            os.system("mv -f {}/panelMonitor.py {}/class/monitor.py".format(self.pluginPath, panel_path))
        if not os.path.exists("{}/server.log".format(self.pluginPath)):
            open("{}/server.log".format(self.pluginPath), 'a').close()
        if not os.path.isfile("{}/server_port.pl".format(self.pluginPath)):
            public.WriteFile("{}/server_port.pl".format(self.pluginPath), "9876")
        if not os.path.isfile("{}/BTPanel/static/js/tools.min.js".format(panel_path)):
            os.system("\cp -a -r {}/tools.min.js {}/BTPanel/static/js/tools.min.js".format(self.pluginPath, panel_path))
        if not os.path.isfile("{}/BTPanel/static/js/china.js".format(panel_path)):
            os.system("\cp -a -r {}/china.js {}/BTPanel/static/js/china.js".format(self.pluginPath, panel_path))
        if not os.path.isfile("{}/config.json".format(self.total_path)):
            os.system("\cp -a -r {}/total_config.json {}/config.json".format(self.pluginPath, self.total_path))
        if not os.path.exists("{}/closing".format(self.total_path)):
            if not os.path.isfile("{}/vhost/apache/total.conf".format(panel_path)):
                os.system("\cp -a -r {}/total_httpd.conf {}/vhost/apache/total.conf".format(self.pluginPath, panel_path))
                os.system("\cp -a -r {}/total_nginx.conf {}/vhost/nginx/total.conf".format(self.pluginPath, panel_path))
        waf_conf = "/www/server/panel/vhost/apache/btwaf.conf"
        if not os.path.isfile(waf_conf):
            public.WriteFile(waf_conf, "LoadModule lua_module modules/mod_lua.so")

        if os.path.isdir("{}/total2".format(self.pluginPath)):
            os.system("\cp -a -rf {}/total2/* {}/".format(self.pluginPath, self.total_path))

        # 打补丁/安装python user-agents==2.2.0库
        if shutil.which("btpip"):
            user_agents = public.ExecShell("btpip list|grep user-agents")[0]
            user_agents_v = public.ExecShell("btpip show user-agents | grep \"Version: 2.2.0\"")[0]
            if "user-agents" not in user_agents or user_agents_v == "":
                os.system("btpip install -I -U user-agents==2.2.0")

            os.system("btpython {}/total_migrate.py".format(self.pluginPath))
            os.system("btpython {}/total_patch.py".format(self.pluginPath))
        else:
            user_agents = public.ExecShell("pip list|grep user-agents")[0]
            user_agents_v = public.ExecShell("pip show user-agents | grep \"Version: 2.2.0\"")[
                0]
            if "user-agents" not in user_agents or user_agents_v == "":
                os.system("pip install -I -U user-agents==2.2.0")
            os.system("python {}/total_migrate.py".format(self.pluginPath))
            os.system("python {}/total_patch.py".format(self.pluginPath))

        self.set_ownership(self.total_path, "www")
        self.set_permissions(self.total_path, 0o755)
        os.chmod("{}/httpd_log.lua".format(self.total_path), 0o755)
        os.chown("{}/httpd_log.lua".format(self.total_path), 0, 0)
        os.chmod("{}/nginx_log.lua".format(self.total_path), 0o755)
        os.chown("{}/nginx_log.lua".format(self.total_path), 0, 0)
        os.chmod("{}/memcached.lua".format(self.total_path), 0o755)
        os.chown("{}/memcached.lua".format(self.total_path), 0, 0)
        if os.path.isfile("{}/lsqlite3.so".format(self.total_path)):
            os.chmod("{}/lsqlite3.so".format(self.total_path), 0o755)
            os.chown("{}/lsqlite3.so".format(self.total_path), 0, 0)
        os.chmod("{}/CRC32.lua".format(self.total_path), 0o755)
        os.chown("{}/CRC32.lua".format(self.total_path), 0, 0)

        # 兼容负载均衡插件,lua引用路劲
        os.chmod("{}/load_total.lua".format(self.total_path), 0o755)
        os.chown("{}/load_total.lua".format(self.total_path), 0, 0)
        if os.path.isdir('{}/vhost/nginx/proxy'.format(panel_path)):
            dir_list = os.listdir('{}/vhost/nginx/proxy/'.format(panel_path))
            for dir in dir_list:
                conf_file = os.path.join(dir, 'load_balance.conf')
                if os.path.isfile(conf_file):
                    if os.path.isdir('{}/plugin/load_balance'.format(panel_path)):
                        shutil.copy2('{}/load_total.lua'.format(self.total_path),
                                     '{}/plugin/load_balance/load_total.lua'.format(panel_path))
                        shutil.copy2('{}/load_total.lua'.format(self.total_path),
                                     os.path.join(dir, 'load_total.lua'))

        self.shutil_rmtree("{}/total_main.cpython-37m-x86_64-linux-gnu.so".format(self.pluginPath))
        self.shutil_rmtree("{}/total_main.so".format(self.pluginPath))
        self.shutil_rmtree("{}/tools.min.js".format(self.pluginPath))
        self.shutil_rmtree("{}/china.js".format(self.pluginPath))
        self.shutil_rmtree("{}/config.json".format(self.total_path))
        self.shutil_rmtree("{}/total2".format(self.pluginPath))

        restart_result = public.ExecShell("/etc/init.d/nginx restart")
        if restart_result[1].find('nginx.pid') != -1:
            public.ExecShell('pkill -9 nginx && sleep 1')
            public.ExecShell('/etc/init.d/nginx start')

        open("{}/data/reload.pl".format(panel_path), 'a').close()
        print("Successify")
        return True

    def run(self) -> Optional[bool]:
        '''
        脚本从这里开始
        @return:
        '''
        if not self.install_total():
            print("监控报表安装异常，详情如下：\n{}".format(self.install_log))
            return False
        return True


if __name__ == '__main__':
    webserver = get_webserver()
    if webserver not in ['nginx', 'apache']:
        print("暂时只支持nginx或apache,请安装支持的web服务后再安装网站监控报表!")
        sys.exit(1)
    param = sys.argv
    download_url = param[1] if len(param) > 1 else "http://download.bt.cn"
    pack_manager = get_pack_manager()
    if not pack_manager:
        print("系统包管理器异常,请及时处理")
        sys.exit(1)
    local_env = get_env()
    total_install = total_install(download_url, pack_manager, local_env, webserver)
    total_install.run()
    # total_install.install_luajit2()
    # total_install.install_cjson()
    # total_install.install_pdf_library()
    # total_install.install_lua()
    # total_install.install_sqlite3()
