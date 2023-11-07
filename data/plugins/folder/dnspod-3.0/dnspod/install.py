import sys,os,shutil
panelPath = os.getenv('BT_PANEL')
os.chdir(panelPath);
sys.path.insert(0,panelPath + "/class/")
import public,imp,json

__name = 'dnspod'
__path = panelPath + '/plugin/' + __name

def install():
    if not os.path.exists(__path): os.makedirs(__path)

    downUrl = public.get_url()
    pluginUrl = downUrl + '/win/install/plugin/' + __name

    
    os.system(public.get_run_pip('[PIP] install tencentcloud-sdk-python'))

    fileList = ['dnspod_main.py','index.html','info.json','icon.png']
    for f in fileList:
        public.bt_print(pluginUrl + '/' + f)
        public.downloadFile(pluginUrl + '/' + f,__path + '/' + f)
        if not os.path.exists(__path + '/' + f):
            public.bt_print("ERROR:文件下载失败!")
            exit()
    public.bt_print("安装成功!")


def update():
    install()

def uninstall():

    shutil.rmtree(__path)

if __name__ == "__main__":
    opt = sys.argv[1]
    if opt == 'update':
        update()
    elif opt == 'uninstall':
        uninstall()
    else:
        install()
