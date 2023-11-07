# 宝塔面板第三方云端
这是一个用php开发的宝塔面板第三方云端站点程序。

# 不要不带眼睛注意看箭头所示 不带眼镜不要找我 近视就不要研究了
# ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
# 本仓库源代码可能不完整 未能完整推送请勿get源代码有需要可前往源仓获取 上传至Releases的可正常使用 源仓: https://github.com/flucont/btcloud
# ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑

你可以使用此程序搭建属于自己的宝塔面板第三方云端，实现最新版宝塔面板私有化部署，不与宝塔官方接口通信，满足隐私安全合规需求。同时还可以去除面板强制绑定账号，DIY面板功能等。

网站后台管理可一键同步宝塔官方的插件列表与增量更新插件包，还有云端使用记录、IP黑白名单、操作日志、定时任务等功能。

本项目自带的宝塔安装包和更新包是8.0.x最新版，已修改适配此第三方云端，并且全开源，无so等加密文件。

觉得该项目不错的可以给个Star~

## 声明

1.此项目只能以自用为目的，不得侵犯堡塔公司及其他第三方的知识产权和其他合法权利。

2.搭建使用此项目必须有一定的编程和Linux运维基础，纯小白不建议使用。

## 环境要求

* `PHP` >= 7.4
* `MySQL` >= 5.6
* `fileinfo`扩展
* `ZipArchive`扩展

## 部署方法

- [下载最新版的Release包](https://github.com/flucont/btcloud/releases)
- 如果是下载的源码包，需要执行 `composer install --no-dev` 安装依赖，如果是下载的Release包，则不需要
- 设置网站运行目录为`public`
- 设置伪静态为`ThinkPHP`
- 访问网站，会自动跳转到安装页面，根据提示安装完成

## 使用方法

- 在`批量替换工具`，执行页面显示的命令，可将bt安装包、更新包和脚本文件里面的`http://www.example.com`批量替换成当前网站的网址。
- 在`系统基本设置`修改宝塔面板接口设置。你需要准备一个使用官方最新脚本安装并绑定账号的宝塔面板，用于获取最新插件列表及插件包。并根据界面提示安装好专用插件。
- 在`定时任务设置`执行所显示的命令从宝塔官方获取最新的插件列表并批量下载插件包（增量更新）。当然你也可以去插件列表，一个一个点击下载。
- 访问网站`/download`查看使用此第三方云端的一键安装脚本。

## 更新方法

- [下载最新版的Release包](https://github.com/flucont/btcloud/releases)
- 上传覆盖除data文件夹以外的全部文件
- 后台使用批量替换工具->获取最新插件列表->修改Linux面板等版本号

## 其他

- [Linux面板官方更新包修改记录](./wiki/update.md)

- [Windows面板官方更新包修改记录](./wiki/updatewin.md)

- [宝塔云监控安装包修改记录](./wiki/btmonitor.md)

- 宝塔面板官方版与此第三方云端版对比：

  |            | 官方版                                                       | 此第三方云端版                                     |
  | ---------- | ------------------------------------------------------------ | -------------------------------------------------- |
  | 版本更新   | 支持                                                         | 支持                                               |
  | 面板广告   | 有广告                                                       | 无广告                                             |
  | 是否全开源 | 没有全开源                                                   | 全开源                                             |
  | 资源占用   | 各种统计上报等任务，资源占用略高                             | 去除了很多无用的定时任务，资源占较少               |
  | 兼容性     | 由于编译的so文件有系统架构限制，兼容的系统仅限已编译的so对应的系统架构 | 由于全开源，没有已编译的so文件，因此无系统架构限制 |
  
  
