#!/www/server/panel/pyenv/bin/python3.7
#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi<baozi@bt.cn>
# +-------------------------------------------------------------------

# +--------------------------------------------------------------------
# |   宝塔防篡改测试攻击
# +--------------------------------------------------------------------

import os, shutil, re


def dict2str(dict_obj):
    res = "{"
    for k, v in dict_obj.items():
        if isinstance(k, str):
            res += f'"{k}":'
        else:
            continue
        if isinstance(v, dict):
            res += dict2str(v)
        elif isinstance(v, str):
            res += f'"{v}",'
        elif isinstance(v, (int, float)):
            res += f'{v},'
        else:
            idx = res.rfind(",") + 1
            res = res[:idx]
    res += "}"
    return res


class Attack:
    def __init__(self, attack_config) -> None:
        self.atk_type = attack_config["type"]
        self.atk_dir = attack_config["dir"]
        self.base_path = attack_config["base_path"][:-1]
        self.attack_process = attack_config["attack_process"]
        self.atk_file = attack_config.get("file", None)
        self.tmp = None

    def do_attack(self):
        func = getattr(self, "atk_" + self.atk_type)
        try:
            func()
        except PermissionError:
            print("ok")
        except Exception as e:
            print(str(e))
        else:
            func(clean=True)
            print("danger")

    @staticmethod
    def do_attack_sh(attack_config, file_path):
        attack_process = attack_config["attack_process"]
        tmp_file = "/tmp/{}".format(attack_process)
        os.system("\cp -f {} /tmp/{}".format(file_path, attack_process))
        os.chmod(tmp_file, mode=0o777)
        rep = r' {1}"do_attack_config:REPLACE"'
        with open(tmp_file, mode="r+", encoding="utf-8") as fp:
            fp.seek(0, 0)
            content = fp.read()
            content = re.sub(rep, dict2str(attack_config), content)
            fp.seek(0, 0)
            fp.truncate()
            fp.write(content)

        return "{} &> /tmp/{}.log".format(tmp_file, attack_process)

    def atk_is_mkdir(self, clean=False):
        if not clean:
            os.mkdir(self.atk_dir)
        else:
            os.rmdir(self.atk_dir)

    def atk_is_create(self, clean=False):
        if not clean:
            _dir = os.path.dirname(self.atk_file)
            if not os.path.exists(_dir):
                os.makedirs(_dir)
            with open(self.atk_file, mode="w", encoding="utf-8") as fp:
                fp.write("tamper attack")
        else:
            _dir = os.path.dirname(self.atk_file)
            if os.path.exists(self.atk_file) and os.path.isfile(self.atk_file):
                os.remove(self.atk_file)
            if _dir != self.atk_file:
                target_dirname = [
                    i for i in _dir.split("/")[1:]
                    if self.atk_file.find(i) == -1
                ][0]
                shutil.rmtree("{}/{}".format(self.base_path, target_dirname))

    def atk_is_link(self, clean=False):
        _link_path = "/tmp/tamper_attact_link"
        if not clean:
            os.symlink(self.atk_file, _link_path)
        else:
            os.remove(_link_path)

    def atk_is_chmod(self, clean=False):
        self.tmp = os.stat(self.atk_file).st_mode & 0o777
        if not clean:
            os.chmod(self.atk_file, mode=0o000)
        else:
            os.chmod(self.atk_file, mode=self.tmp)

    def atk_is_chown(self, clean=False):
        self.tmp = os.stat(self.atk_file).st_uid, os.stat(self.atk_file).st_gid
        if not clean:
            os.chown(self.atk_file, 0, 0)
        else:
            os.chown(self.atk_file, self.tmp, *self.tmp)

    def atk_is_rename(self, clean=False):
        _dir = self.atk_file.rsplit("/", 1)[0]
        if not clean:
            os.rename(self.atk_file, _dir + "/tamper_attact_rename")
        else:
            os.rename(_dir + "/tamper_attact_rename", self.atk_file)

    def atk_is_modify(self, clean=False):
        if not clean:
            with open(self.atk_file, mode="a", encoding="utf-8") as fp:
                fp.write("tamper-attack")
        else:
            with open(self.atk_file, mode="r+", encoding="utf-8") as fp:
                fp.seek(0, 0)
                content = fp.read()
                content = content.strip("tamper-attack")
                fp.seek(0, 0)
                fp.truncate()
                fp.write(content)

    def atk_is_unlink(self, clean=False):
        if not clean:
            os.remove(self.atk_file)

    def atk_is_rmdir(self, clean=False):
        if not clean:
            shutil.rmtree(self.atk_dir)


class PrepareAttack:

    def __init__(self, attack_config) -> None:
        self.atk_type = attack_config["type"]
        self.base_path = attack_config["base_path"][:-1]
        self.prep_process = attack_config["prep_process"]
        self.prep_dir = attack_config["dir"]
        self.prep_file = attack_config.get("file", None)

    def _add_dir(self):
        os.makedirs(self.prep_dir)

    def _del_dir(self):
        if not os.path.exists(self.prep_dir): return True
        tmp = os.listdir(self.prep_dir)
        for i in tmp:
            _tmp_file = "{}/{}".format(self.prep_dir, i)
            if os.path.isfile(_tmp_file):
                os.remove(_tmp_file)
        os.rmdir(self.prep_dir)

    def _add_file(self):
        if not self.prep_file: return
        _dir = os.path.dirname(self.prep_file)
        if not os.path.exists(_dir):
            os.makedirs(_dir)
        with open(self.prep_file, mode="w", encoding="utf-8") as fp:
            fp.write("tamper attack")

    def _del_file(self):
        if not self.prep_file: return
        _dir = os.path.dirname(self.prep_file)
        if os.path.exists(self.prep_file) and os.path.isfile(self.prep_file):
            os.remove(self.prep_file)
        if _dir != self.base_path:
            target_dirname = [i for i in _dir.split("/")[1:] if self.base_path.find(i) == -1][0]
            shutil.rmtree("{}/{}".format(self.base_path, target_dirname))

    def do_prep(self):
        if self.atk_type not in ("is_mkdir", "is_create"):
            self._add_dir()
            self._add_file()
        print("ok")

    def remove_prep(self):
        if self.atk_type not in ("is_mkdir"):
            self._del_file()
            self._del_dir()
        print("ok")

    @staticmethod
    def set_prep_sh(attack_config, file_path):
        prep_process = attack_config["prep_process"]
        tmp_file = "/tmp/{}".format(prep_process)
        os.system("cp {} /tmp/{}".format(file_path, prep_process))
        os.chmod(tmp_file, mode=0o777)
        rep = r' {1}"do_prep_config:REPLACE"'
        with open(tmp_file, mode="r+", encoding="utf-8") as fp:
            fp.seek(0, 0)
            content = fp.read()
            content = re.sub(rep, dict2str(attack_config), content)
            fp.seek(0, 0)
            fp.truncate()
            fp.write(content)

        return "{} &> /tmp/{}.log".format(tmp_file, prep_process)

    @staticmethod
    def remove_prep_sh(attack_config, file_path):
        prep_process = attack_config["prep_process"]
        tmp_file = "/tmp/{}".format(prep_process)
        os.system("\cp -f {} /tmp/{}".format(file_path, prep_process))
        os.chmod(tmp_file, mode=0o777)
        rep = r' {1}"remove_prep_config:REPLACE"'
        with open(tmp_file, mode="r+", encoding="utf-8") as fp:
            fp.seek(0, 0)
            content = fp.read()
            content = re.sub(rep, dict2str(attack_config), content)
            fp.seek(0, 0)
            fp.truncate()
            fp.write(content)
            
        return "{} &>> /tmp/{}.log".format(tmp_file, prep_process)


def clean(attack_config):
    prep_process = attack_config["prep_process"]
    tmp_file1 = "/tmp/{}".format(prep_process)
    attack_process = attack_config["attack_process"]
    tmp_file2 = "/tmp/{}".format(attack_process)
    tmp_file_3 = "/tmp/{}.log".format(prep_process)
    tmp_file_4 = "/tmp/{}.log".format(attack_process)
    for i in [tmp_file1, tmp_file2, tmp_file_3, tmp_file_4]:
        if os.path.exists(i):
            os.remove(i)


if __name__ == "__main__":
    do_prep_config = "do_prep_config:REPLACE"
    remove_prep_config = "remove_prep_config:REPLACE"
    do_attack_config = "do_attack_config:REPLACE"

    if isinstance(do_prep_config, dict):
        prep = PrepareAttack(do_prep_config)
        prep.do_prep()
    elif isinstance(remove_prep_config, dict):
        prep = PrepareAttack(remove_prep_config)
        prep.remove_prep()
    elif isinstance(do_attack_config, dict):
        prep = Attack(do_attack_config)
        prep.do_attack()
    else:
        print("ERROR: No config!")