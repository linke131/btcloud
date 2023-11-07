# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyleft (c) 2015-2099 宝塔软件(http://bt.cn) All lefts reserved.
# +-------------------------------------------------------------------
# | Author: wzz
# | email : help@bt.cn
# +-------------------------------------------------------------------
# +-------------------------------------------------------------------
# | 宝塔网站监控报表 - total_migrate_6x
# +-------------------------------------------------------------------
import os
import sys
import time
import datetime
import sqlite3


class site_logs_migrate:
    def __init__(self):
        self.data_dir = "/www/server/total/logs/"
        self.db_path = ""
        self.db_name = ""
        self.logs_sql = None
        self.logs_cursor = None

    def sql(self, site_name):
        self.db_path = self.data_dir + "{}/".format(site_name) + self.db_name
        # print(self.db_path)
        return sqlite3.connect(self.db_path)

    def cursor(self, sql):
        return sql.cursor()

    def get_current_day_timestamp(self, day):
        '''
        获取某一天的开始和结束时间戳
        @return:
        '''
        # 获取当前时间戳
        current_timestamp = time.time()

        # 计算180天前的时间戳
        one_day = 24 * 60 * 60  # 一天的秒数
        # 计算当前日期
        current_day = datetime.datetime.fromtimestamp(current_timestamp - (day * one_day))

        # 获取当前日期的0点时间戳
        current_day_start = current_day.replace(hour=0, minute=0, second=0, microsecond=0)
        current_day_start_timestamp = int(current_day_start.timestamp())

        # 获取当前日期的23点时间戳
        current_day_end = current_day.replace(hour=23, minute=59, second=59, microsecond=999999)
        current_day_end_timestamp = int(current_day_end.timestamp())
        return [current_day_start_timestamp, current_day_end_timestamp, current_day]

    def site_logs_migrate_fun(self, site_name):
        '''
        旧logs.db迁出site_logs表
        @return:
        '''
        none_list = []
        sum = 0
        # 遍历180天内的每一天
        for i in range(180):
            current_day_start_timestamp, current_day_end_timestamp, \
                current_day = self.get_current_day_timestamp(i)
            # 打印当前日期和时间戳范围
            print("正在迁移日期:{}的数据,请稍后...".format(current_day.strftime("%Y-%m-%d")))
            date = datetime.datetime.fromtimestamp(current_day_start_timestamp)

            today = date.strftime('%Y%m%d')
            new_db_file = "{}.db".format(today)

            create_table_sql = """
            CREATE TABLE IF NOT EXISTS site_logs (
                time INTEGER,
                ip TEXT,
                domain TEXT,
                server_name TEXT,
                method TEXT,
                status_code INTEGER,
                uri TEXT,
                body_length INTEGER,
                referer TEXT DEFAULT "",
                user_agent TEXT,
                is_spider INTEGER DEFAULT 0,
                protocol TEXT,
                request_time INTEGER,
                request_headers TEXT DEFAULT "",
                ip_list TEXT DEFAULT "",
                client_port INTEGER DEFAULT -1
            );
            """

            try:
                site_logs = self.logs_cursor.execute(
                    "SELECT * FROM site_logs WHERE time >= ? AND time < ?", (
                        current_day_start_timestamp,
                        current_day_end_timestamp
                    )
                ).fetchall()
            except Exception:
                return False

            if i == 0:
                self.db_name = new_db_file
                new_sql = self.sql(site_name)
                new_cursor = self.cursor(new_sql)
                new_cursor.execute(create_table_sql)
                if len(site_logs) > 0:
                    for site_log in site_logs:
                        new_cursor.execute(
                            "INSERT INTO site_logs (time, ip, domain, server_name, method, status_code, uri, body_length, referer, user_agent, is_spider, protocol, request_time, request_headers, ip_list, client_port) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            site_log
                        )
            else:
                if os.path.isfile(new_db_file):
                    print(
                        "当前日期:{}日志文件已存在,已跳过".format(
                            current_day.strftime("%Y-%m-%d")
                        )
                    )
                    continue
                if len(site_logs) <= 0:
                    none_list.append(current_day.strftime("%Y-%m-%d"))
                    sum += 1
                    if sum >= 3:
                        print("已检测超过3天无日志")
                        print("当前日期:{}及以前的日期可能无数据,即将完成迁移...".format(none_list))
                        for n_list in none_list:
                            os.system(
                                "rm -rf {}/{}/{}.db"
                                .format(self.data_dir, site_name, n_list)
                            )
                        break
                    continue
                sum = 0
                self.db_name = new_db_file
                new_sql = self.sql(site_name)
                new_cursor = self.cursor(new_sql)
                new_cursor.execute(create_table_sql)
                for site_log in site_logs:
                    new_cursor.execute(
                        "INSERT INTO site_logs (time, ip, domain, server_name, method, status_code, uri, body_length, referer, user_agent, is_spider, protocol, request_time, request_headers, ip_list, client_port) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        site_log
                    )

            new_sql.commit()
            new_sql.close()
        return True

    def ip_stat_alter(self):
        '''
        旧logs.db表新增ip_stat列
        @param cursor:
        @return:
        '''
        self.logs_cursor.execute('''PRAGMA table_info(ip_stat)''')
        columns = [column[1] for column in self.logs_cursor.fetchall()]

        if 'day_hour1' not in columns:
            self.logs_cursor.execute(
                '''ALTER TABLE ip_stat ADD COLUMN day_hour1 INTEGER DEFAULT 0''')

        if 'flow_hour1' not in columns:
            self.logs_cursor.execute(
                '''ALTER TABLE ip_stat ADD COLUMN flow_hour1 INTEGER DEFAULT 0''')

    def create_referer2_stat(self):
        '''
        创建referer2_stat表
        @return:
        '''
        self.logs_cursor.execute('''
            CREATE TABLE IF NOT EXISTS referer2_stat (
                referer_md5 CHAR (32) PRIMARY KEY,
                referer     TEXT,
                day1        INTEGER   DEFAULT 0,
                day2        INTEGER   DEFAULT 0,
                day3        INTEGER   DEFAULT 0,
                day4        INTEGER   DEFAULT 0,
                day5        INTEGER   DEFAULT 0,
                day6        INTEGER   DEFAULT 0,
                day7        INTEGER   DEFAULT 0,
                day8        INTEGER   DEFAULT 0,
                day9        INTEGER   DEFAULT 0,
                day10       INTEGER   DEFAULT 0,
                day11       INTEGER   DEFAULT 0,
                day12       INTEGER   DEFAULT 0,
                day13       INTEGER   DEFAULT 0,
                day14       INTEGER   DEFAULT 0,
                day15       INTEGER   DEFAULT 0,
                day16       INTEGER   DEFAULT 0,
                day17       INTEGER   DEFAULT 0,
                day18       INTEGER   DEFAULT 0,
                day19       INTEGER   DEFAULT 0,
                day20       INTEGER   DEFAULT 0,
                day21       INTEGER   DEFAULT 0,
                day22       INTEGER   DEFAULT 0,
                day23       INTEGER   DEFAULT 0,
                day24       INTEGER   DEFAULT 0,
                day25       INTEGER   DEFAULT 0,
                day26       INTEGER   DEFAULT 0,
                day27       INTEGER   DEFAULT 0,
                day28       INTEGER   DEFAULT 0,
                day29       INTEGER   DEFAULT 0,
                day30       INTEGER   DEFAULT 0,
                day31       INTEGER   DEFAULT 0,
                day32       INTEGER   DEFAULT 0,
                flow1       INTEGER   DEFAULT 0,
                flow2       INTEGER   DEFAULT 0,
                flow3       INTEGER   DEFAULT 0,
                flow4       INTEGER   DEFAULT 0,
                flow5       INTEGER   DEFAULT 0,
                flow6       INTEGER   DEFAULT 0,
                flow7       INTEGER   DEFAULT 0,
                flow8       INTEGER   DEFAULT 0,
                flow9       INTEGER   DEFAULT 0,
                flow10      INTEGER   DEFAULT 0,
                flow11      INTEGER   DEFAULT 0,
                flow12      INTEGER   DEFAULT 0,
                flow13      INTEGER   DEFAULT 0,
                flow14      INTEGER   DEFAULT 0,
                flow15      INTEGER   DEFAULT 0,
                flow16      INTEGER   DEFAULT 0,
                flow17      INTEGER   DEFAULT 0,
                flow18      INTEGER   DEFAULT 0,
                flow19      INTEGER   DEFAULT 0,
                flow20      INTEGER   DEFAULT 0,
                flow21      INTEGER   DEFAULT 0,
                flow22      INTEGER   DEFAULT 0,
                flow23      INTEGER   DEFAULT 0,
                flow24      INTEGER   DEFAULT 0,
                flow25      INTEGER   DEFAULT 0,
                flow26      INTEGER   DEFAULT 0,
                flow27      INTEGER   DEFAULT 0,
                flow28      INTEGER   DEFAULT 0,
                flow29      INTEGER   DEFAULT 0,
                flow30      INTEGER   DEFAULT 0,
                flow31      INTEGER   DEFAULT 0,
                day_hour1   INTEGER   DEFAULT 0,
                flow_hour1  INTEGER   DEFAULT 0
            );
        ''')

    def request_stat_alter(self):
        '''
        旧logs.db表新增request_stat列
        @param cursor:
        @return:
        '''
        self.logs_cursor.execute('''PRAGMA table_info(request_stat)''')
        columns = [column[1] for column in self.logs_cursor.fetchall()]

        if 'status_499' not in columns:
            self.logs_cursor.execute(
                '''ALTER TABLE request_stat ADD COLUMN status_499 INTEGER DEFAULT 0'''
            )

    def uri_stat_alter(self):
        '''
        旧logs.db表新增uri_stat列
        @param cursor:
        @return:
        '''
        self.logs_cursor.execute('''PRAGMA table_info(uri_stat)''')
        columns = [column[1] for column in self.logs_cursor.fetchall()]

        spider_flow = [
            "spider_flow1", "spider_flow2", "spider_flow3", "spider_flow4",
            "spider_flow5", "spider_flow6", "spider_flow7", "spider_flow8",
            "spider_flow9", "spider_flow10", "spider_flow11", "spider_flow12",
            "spider_flow13", "spider_flow14", "spider_flow15", "spider_flow16",
            "spider_flow17", "spider_flow18", "spider_flow19", "spider_flow20",
            "spider_flow21", "spider_flow22", "spider_flow23", "spider_flow24",
            "spider_flow25", "spider_flow26", "spider_flow27", "spider_flow28",
            "spider_flow29", "spider_flow30", "spider_flow31", "day_hour1",
            "flow_hour1", "spider_flow_hour1"
        ]
        for flow in spider_flow:
            if flow not in columns:
                self.logs_cursor.execute(
                    '''ALTER TABLE uri_stat ADD COLUMN {} INTEGER DEFAULT 0'''.format(flow)
                )

    def move_logs_to_total(self, site_name):
        os.system(
            "mv -f {0}/{1}/logs.db {0}/{1}/total.db".format(self.data_dir, site_name)
        )
        # os.system(
        #     "\cp -r -a {0}/{1}/logs.db {0}/{1}/total.db".format(self.data_dir, site_name)
        # )

    def migrate_run(self, site_name):
        try:
            print("正在迁移6.x版本的: {} 网站".format(site_name))
            self.db_name = "logs.db"
            self.logs_sql = self.sql(site_name)
            self.logs_cursor = self.logs_sql.cursor()
            if not self.site_logs_migrate_fun(site_name):
                return False
            self.ip_stat_alter()
            self.create_referer2_stat()
            self.request_stat_alter()
            self.uri_stat_alter()
            self.logs_sql.close()
            self.move_logs_to_total(site_name)
            # print("6.x版本监控报表旧数据库迁移完毕!")
            return True
        except Exception:
            pass


if __name__ == '__main__':
    site_logs_migrate = site_logs_migrate()
    site_logs_migrate.migrate_run(site_name="")
