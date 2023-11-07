# coding: utf-8
import os
import sys
import re
os.chdir("/www/server/panel")
sys.path.append('class/')
import public


class crontab:

    # 删除计划任务
    def DelCrontab(self, get):
        try:
            id = get['id']
            find = public.M('crontab').where("id=?", (id,)).field('name,echo').find()
            if not self.remove_for_crond(find['echo']): return public.returnMsg(False, '无法写入文件，请检查是否开启了系统加固功能!')
            cronPath = public.GetConfigValue('setup_path') + '/cron'
            sfile = cronPath + '/' + find['echo']
            if os.path.exists(sfile): os.remove(sfile)
            sfile = cronPath + '/' + find['echo'] + '.log'
            if os.path.exists(sfile): os.remove(sfile)

            public.M('crontab').where("id=?", (id,)).delete()
            public.WriteLog('TYPE_CRON', 'CRONTAB_DEL', (find['name'],))
            return public.returnMsg(True, 'DEL_SUCCESS')
        except:
            return public.returnMsg(False, 'DEL_ERROR')

    # 从crond删除
    def remove_for_crond(self, echo):
        u_file = '/var/spool/cron/crontabs/root'
        file = self.get_cron_file()
        conf = public.readFile(file)
        rep = ".+" + str(echo) + ".+\n"
        conf = re.sub(rep, "", conf)
        if not public.writeFile(file, conf): return False
        self.CrondReload()
        return True

    # 重载配置
    def CrondReload(self):
        if os.path.exists('/etc/init.d/crond'):
            public.ExecShell('/etc/init.d/crond reload')
        elif os.path.exists('/etc/init.d/cron'):
            public.ExecShell('service cron restart')
        else:
            public.ExecShell("systemctl reload crond")

    # 获取计划任务文件位置
    def get_cron_file(self):
        u_path = '/var/spool/cron/crontabs'
        u_file = u_path + '/root'
        c_file = '/var/spool/cron/root'
        cron_path = c_file
        if not os.path.exists(u_path):
            cron_path = c_file
        if os.path.exists('/usr/bin/yum'):
            cron_path = c_file
        elif os.path.exists("/usr/bin/apt-get"):
            cron_path = u_file

        if cron_path == u_file:
            if not os.path.exists(u_path):
                os.makedirs(u_path, 472)
                public.ExecShell("chown root:crontab {}".format(u_path))
        return cron_path


if __name__ == '__main__':
    p = crontab()
    id = public.M('crontab').where("name=?", u'[勿删]资源管理器-获取进程流量').getField('id')
    print(id)
    args = {"id": id}
    p.DelCrontab(args)
