import pythonmamager_main
def auto_start(name):
    return pythonmamager_main.pythonmamager_main().exec_crontab(name)
     

if __name__ == '__main__':
    import argparse
    args_obj = argparse.ArgumentParser(usage="必要的参数：--cron_name 任务名称!")
    args_obj.add_argument("--cron_name", help="任务名称!")
    args = args_obj.parse_args()
    if args.cron_name:
        auto_start(args.cron_name)