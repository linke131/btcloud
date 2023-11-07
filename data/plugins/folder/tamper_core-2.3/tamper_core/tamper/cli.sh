#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
LANG=en_US.UTF-8

set_path_config(){
    clear
    echo "正在配置 path_id=$path_id, path=$path_name 的防篡改配置"
    echo "----------------------------------------------------------------------"
    echo -e "  \033[33m1.\033[0m 关闭该路径的防篡改功能\c"
    echo -e "  \033[33m2.\033[0m 开启该路径的防篡改功能\n"
    echo -e "  \033[33m3.\033[0m 允许\033[33m[创建文件]\033[0m\c"
    echo -e "  \033[33m4.\033[0m 拒绝\033[33m[创建文件]\033[0m\n"
    echo -e "  \033[33m5.\033[0m 允许\033[33m[创建目录]\033[0m\c"
    echo -e "  \033[33m6.\033[0m 拒绝\033[33m[创建目录]\033[0m\n"
    echo -e "  \033[33m7.\033[0m 允许\033[33m[目录删除]\033[0m\c"
    echo -e "  \033[33m8.\033[0m 拒绝\033[33m[目录删除]\033[0m\n"
    echo -e "  \033[33m9.\033[0m 允许\033[33m[文件修改]\033[0m\c"
    echo -e "  \033[33m10.\033[0m 拒绝\033[33m[文件修改]\033[0m\n"
    echo -e "  \033[33m11.\033[0m 允许\033[33m[文件删除]\033[0m\c"
    echo -e "  \033[33m12.\033[0m 拒绝\033[33m[文件删除]\033[0m\n"
    echo -e "  \033[33m13.\033[0m 允许\033[33m[重命名]\033[0m\c"
    echo -e "  \033[33m14.\033[0m 拒绝\033[33m[重命名]\033[0m\n"
    echo -e "  \033[33m15.\033[0m 允许\033[33m[权限修改]\033[0m\c"
    echo -e "  \033[33m16.\033[0m 拒绝\033[33m[权限修改]\033[0m\n"
    echo -e "  \033[33m17.\033[0m 允许\033[33m[所有者修改]\033[0m\c"
    echo -e "  \033[33m18.\033[0m 拒绝\033[33m[所有者修改]\033[0m\n"
    echo -e "  \033[33m19.\033[0m 允许\033[33m[创建链接]\033[0m\c"
    echo -e "  \033[33m20.\033[0m 拒绝\033[33m[创建链接]\033[0m\n"
    echo -e "  \033[33m-1.\033[0m 返回上一层菜单\c"
    echo -e "  \033[33m0.\033[0m 返回主菜单\n"

    while((1))
    do
        echo -e "请选择菜单[\033[34m0-7\033[0m]: \c"
        read path_config_select

        if [ "$path_config_select" == "0" ];then
            main_menu
            return
        fi

        if [ "$path_config_select" == "-1" ];then
            show_list
            return
        fi

        if [ $path_config_num -lt 1 ] || [ $path_config_num -gt 20 ]; then
            echo -e "\033[31m错误: 输入错误,请重新输入\033[0m\n"
            continue
        fi

        if [ "$path_config_select" != "" ]; then
            break
        fi
    done

    case $path_config_select in
        1)
            ./tamper-cli set $path_id status=0
            ;;
        2)
            ./tamper-cli set $path_id status=1
            ;;
        3)
            ./tamper-cli set $path_id is_create=0
            ;;
        4)
            ./tamper-cli set $path_id is_create=1
            ;;
        5)
            ./tamper-cli set $path_id is_mkdir=0
            ;;
        6)
            ./tamper-cli set $path_id is_mkdir=1
            ;;
        7)
            ./tamper-cli set $path_id is_rmdir=0
            ;;
        8)
            ./tamper-cli set $path_id is_rmdir=1
            ;;
        9)
            ./tamper-cli set $path_id is_modify=0
            ;;
        10)
            ./tamper-cli set $path_id is_modify=1
            ;;
        11)
            ./tamper-cli set $path_id is_unlink=0
            ;;
        12)
            ./tamper-cli set $path_id is_unlink=1
            ;;
        13)
            ./tamper-cli set $path_id is_rename=0
            ;;
        14)
            ./tamper-cli set $path_id is_rename=1
            ;;
        15)
            ./tamper-cli set $path_id is_chmod=0
            ;;
        16)
            ./tamper-cli set $path_id is_chmod=1
            ;;
        17)
            ./tamper-cli set $path_id is_chown=0
            ;;
        18)
            ./tamper-cli set $path_id is_chown=1
            ;;
        19)
            ./tamper-cli set $path_id is_link=0
            ;;
        20)
            ./tamper-cli set $path_id is_link=1
            ;;
    esac



    while((1))
    do
        echo -e "输入 \033[33m-1\033[0m 返回上一层菜单,输入 \033[33m0\033[0m 返回主菜单,按 Ctrl + C 退出程序: \c"
        read back_num
        if [ "$back_num" = "-1" ]; then
            set_path_config
            return
        fi
        if [ "$back_num" = "0" ]; then
            main_menu
            return
        fi
        if [ "$back_num" = "" ]; then
            continue
        fi
    done


}

set_path_black_exts(){
    clear
    echo "正在配置 path_id=$path_id, path=$path_name 的 [受保护的文件后缀]"
    echo -e "  \033[33m1.\033[0m 添加后缀\n"
    echo -e "  \033[33m2.\033[0m 删除后缀\n"
    echo -e "  \033[33m-1.\033[0m 返回上一层菜单\c"
    echo -e "  \033[33m0.\033[0m 返回主菜单\n"
    black_exts=$(./tamper-cli show-path-black_exts $path_id)
    echo  "--------------------------------------------------------------------------------"
    echo -e "当前受保护的文件后缀: $black_exts"
    echo  "--------------------------------------------------------------------------------"
    while((1))
    do
        echo -e "请选择菜单[\033[34m0-2\033[0m]: \c"
        read path_black_exts_select

        if [ "$path_black_exts_select" == "0" ];then
            main_menu
            return
        fi

        if [ "$path_black_exts_select" == "-1" ];then
            show_list
            return
        fi

        if [ $path_black_exts_select -lt 1 ] || [ $path_black_exts_select -gt 2 ]; then
            echo -e "\033[31m错误: 输入错误,请重新输入\033[0m\n"
            continue
        fi

        if [ "$path_black_exts_select" != "" ]; then
            break
        fi
    done
    echo  "--------------------------------------------------------------------------------"
    echo -e "提示：输入 -1 返回上一层菜单,输入 0 返回主菜单,按 Ctrl + C 退出程序\n"
    case $path_black_exts_select in
        1)
            while((1))
            do
                black_exts=$(./tamper-cli show-path-black_exts $path_id)
                echo  "--------------------------------------------------------------------------------"
                echo -e "当前受保护的文件后缀: $black_exts"
                echo  "--------------------------------------------------------------------------------"
                echo -e "请输入要添加的文件后缀,如.php: \c"
                read path_black_exts_add
                if [ "$path_black_exts_add" = "-1" ]; then
                    set_path_black_exts
                    return
                fi
                if [ "$path_black_exts_add" = "0" ]; then
                    main_menu
                    return
                fi
                if [ "$path_black_exts_add" = "" ]; then
                    continue
                fi
                ./tamper-cli set $path_id black_exts add $path_black_exts_add
            done

            ;;
        2)

            while((1))
            do
                black_exts=$(./tamper-cli show-path-black_exts $path_id)
                echo  "--------------------------------------------------------------------------------"
                echo -e "当前受保护的文件后缀: $black_exts"
                echo  "--------------------------------------------------------------------------------"
                echo -e "请输入要删除的文件后缀,如.php: \c"
                read path_black_exts_del
                if [ "$path_black_exts_del" = "-1" ]; then
                    set_path_black_exts
                    return
                fi
                if [ "$path_black_exts_del" = "0" ]; then
                    main_menu
                    return
                fi
                if [ "$path_black_exts_del" = "" ]; then
                    continue
                fi
                ./tamper-cli set $path_id black_exts del $path_black_exts_del
            done
            ;;
    esac
}

set_path_white_files(){
    clear
    echo "正在配置 path_id=$path_id, path=$path_name 的 [文件白名单]"
    echo -e "  \033[33m1.\033[0m 添加文件路径\n"
    echo -e "  \033[33m2.\033[0m 删除文件路径\n"
    echo -e "  \033[33m-1.\033[0m 返回上一层菜单\c"
    echo -e "  \033[33m0.\033[0m 返回主菜单\n"

    while((1))
    do
        echo -e "请选择菜单[\033[34m0-2\033[0m]: \c"
        read path_white_files_select

        if [ "$path_white_files_select" == "0" ];then
            main_menu
            return
        fi

        if [ "$path_white_files_select" == "-1" ];then
            show_list
            return
        fi

        if [ $path_white_files_select -lt 1 ] || [ $path_white_files_select -gt 2 ]; then
            echo -e "\033[31m错误: 输入错误,请重新输入\033[0m\n"
            continue
        fi

        if [ "$path_white_files_select" != "" ]; then
            break
        fi
    done

    echo  "--------------------------------------------------------------------------------"
    echo -e "提示：输入 -1 返回上一层菜单,输入 0 返回主菜单,按 Ctrl + C 退出程序\n"

    case $path_white_files_select in
        1)
            while((1))
            do
                echo -e "当前文件白名单: "
                echo '--------------------------------------------------------------------------------'
                ./tamper-cli show-path-white_files $path_id
                echo '--------------------------------------------------------------------------------'
                echo -e "请输入文件名或文件绝对路径: \c"
                read path_white_files_add
                if [ "$path_white_files_add" = "-1" ]; then
                    set_path_white_files
                    return
                fi
                if [ "$path_white_files_add" = "0" ]; then
                    main_menu
                    return
                fi
                if [ "$path_white_files_add" = "" ]; then
                    continue
                fi
                ./tamper-cli set $path_id white_files add $path_white_files_add
            done

            ;;
        2)
            while((1))
            do
                echo -e "当前文件白名单: "
                echo '--------------------------------------------------------------------------------'
                ./tamper-cli show-path-white_files $path_id
                echo '--------------------------------------------------------------------------------'
                echo -e "请输入文件名或文件绝对路径: \c"
                read path_white_files_del
                if [ "$path_white_files_del" = "-1" ]; then
                    set_path_white_files
                    return
                fi
                if [ "$path_white_files_del" = "0" ]; then
                    main_menu
                    return
                fi
                if [ "$path_white_files_del" = "" ]; then
                    continue
                fi
                ./tamper-cli set $path_id white_files del $path_white_files_del
            done
            ;;
    esac

}

set_path_white_dirs(){
    clear
    echo "正在配置 path_id=$path_id, path=$path_name 的 [文件夹白名单]"
    echo -e "  \033[33m1.\033[0m 添加文件夹路径\n"
    echo -e "  \033[33m2.\033[0m 删除文件夹路径\n"
    echo -e "  \033[33m-1.\033[0m 返回上一层菜单\c"
    echo -e "  \033[33m0.\033[0m 返回主菜单\n"

    echo -e "当前文件夹白名单: "
    echo '--------------------------------------------------------------------------------'
    ./tamper-cli show-path-white_dirs $path_id
    echo '--------------------------------------------------------------------------------'

    while((1))
    do
        echo -e "请选择菜单[\033[34m0-2\033[0m]: \c"
        read path_white_dirs_select

        if [ "$path_white_dirs_select" == "0" ];then
            main_menu
            return
        fi

        if [ "$path_white_dirs_select" == "-1" ];then
            show_list
            return
        fi

        if [ $path_white_dirs_select -lt 1 ] || [ $path_white_dirs_select -gt 2 ]; then
            echo -e "\033[31m错误: 输入错误,请重新输入\033[0m\n"
            continue
        fi

        if [ "$path_white_dirs_select" != "" ]; then
            break
        fi
    done

    echo  "--------------------------------------------------------------------------------"
    echo -e "提示：输入 -1 返回上一层菜单,输入 0 返回主菜单,按 Ctrl + C 退出程序\n"

    case $path_white_dirs_select in
        1)
            while((1))
            do
                echo -e "当前文件夹白名单: "
                echo '--------------------------------------------------------------------------------'
                ./tamper-cli show-path-white_dirs $path_id
                echo '--------------------------------------------------------------------------------'
                echo -e "请输入文件夹名或文件夹绝对路径: \c"
                read path_white_dirs_add
                if [ "$path_white_dirs_add" = "-1" ]; then
                    set_path_white_dirs
                    return
                fi
                if [ "$path_white_dirs_add" = "0" ]; then
                    main_menu
                    return
                fi
                if [ "$path_white_dirs_add" = "" ]; then
                    continue
                fi
                ./tamper-cli set $path_id white_dirs add $path_white_dirs_add
            done

            ;;
        2)
            while((1))
            do
                echo -e "当前文件夹白名单: "
                echo '--------------------------------------------------------------------------------'
                ./tamper-cli show-path-white_dirs $path_id
                echo '--------------------------------------------------------------------------------'
                echo -e "请输入文件夹名或文件夹绝对路径: \c"
                read path_white_dirs_del
                if [ "$path_white_dirs_del" = "-1" ]; then
                    set_path_white_dirs
                    return
                fi
                if [ "$path_white_dirs_del" = "0" ]; then
                    main_menu
                    return
                fi
                if [ "$path_white_dirs_del" = "" ]; then
                    continue
                fi
                ./tamper-cli set $path_id white_dirs del $path_white_dirs_del
            done
            ;;
    esac
}

show_list(){
    clear
    echo "----------------------------------------------------------------------"
    ./tamper-cli list
    echo "----------------------------------------------------------------------"
    while((1))
    do
        echo -e "请输入指定 \033[33mpath_id\033[0m 进行配置,输入 \033[33m0\033[0m 返回主菜单: \c"
        read path_id
        if [ "$path_id" = "0" ]; then
            main_menu
            return
        fi
        if [ "$path_id" = "" ]; then
            continue
        fi
        path_name=$(./tamper-cli list|grep -E "^${path_id}\s+"|awk '{print $2}')
        if [ "$path_name" = "" ]; then
            echo -e "\033[31m错误: 路径不存在,请重新输入\033[0m\n"
            continue
        fi
        if [ "$path_name" != "" ]; then
            break
        fi
    done



    clear
    echo "正在配置 path_id=$path_id, path=$path_name 的防篡改配置"
    echo "----------------------------------------------------------------------"
    echo -e "  \033[33m1.\033[0m 关闭该路径的防篡改功能\n"
    echo -e "  \033[33m2.\033[0m 开启该路径的防篡改功能\n"
    echo -e "  \033[33m3.\033[0m 修改配置\n"
    echo -e "  \033[33m4.\033[0m 管理受保护的文件后缀名列表\n"
    echo -e "  \033[33m5.\033[0m 管理文件白名单\n"
    echo -e "  \033[33m6.\033[0m 管理文件夹白名单\n"
    echo -e "  \033[33m7.\033[0m 删除此配置\n"
    echo -e "  \033[33m-1.\033[0m 返回上一层菜单\n"
    echo -e "  \033[33m0.\033[0m 返回主菜单\n"

    while((1))
    do
        echo -e "请选择菜单[\033[34m-1-7\033[0m]: \c"
        read path_config_num
        if [ "$path_config_num" = "0" ]; then
            main_menu
            return
        fi

        if [ "$path_config_num" = "-1" ]; then
            clear
            show_list
            return
        fi

        if [ $path_config_num -lt -1 ] || [ $path_config_num -gt 7 ]; then
            echo -e "\033[31m错误: 输入错误,请重新输入\033[0m\n"
            continue
        fi

        if [ "$path_config_num" != "" ]; then
            break
        fi

    done

    case $path_config_num in
        1)
            ./tamper-cli set $path_id status=0
            ;;
        2)
            ./tamper-cli set $path_id status=1
            ;;
        3)
            set_path_config $path_id
            ;;
        4)
            set_path_black_exts $path_id
            ;;
        5)
            set_path_white_files $path_id
            ;;
        6)
            set_path_white_dirs $path_id
            ;;
        7)
            ./tamper-cli del $path_id
            ;;
    esac

    while((1))
    do
        echo -e "输入 \033[33m-1\033[0m 返回上一层菜单,输入 \033[33m0\033[0m 返回主菜单,按 Ctrl + C 退出程序: \c"
        read back_num
        if [ "$back_num" = "-1" ]; then
            clear
            show_list
            return
        fi
        if [ "$back_num" = "0" ]; then
            main_menu
            return
        fi
        if [ "$back_num" = "" ]; then
            continue
        fi
    done
}

add_path(){
    clear
    echo "----------------------------------------------------------------------"
    ./tamper-cli list
    echo "----------------------------------------------------------------------"
    while((1))
    do
        echo -e "请输入要保护的文件夹路径: \c"
        read path_name
        if [ "$path_name" = "0" ]; then
            main_menu
            return
        fi
        if [ "$path_name" = "" ]; then
            continue
        fi
        if [ ! -d "$path_name" ]; then
            echo -e "\033[31m错误: 指定文件夹路径不存在,请先创建!\033[0m\n"
            continue
        fi
        is_exists=$(./tamper-cli list|grep -E "${path_name}\s+")
        if [ "$is_exists" != "" ]; then
            echo -e "\033[31m错误: 指定路径配置已经添加过了,请重新输入\033[0m\n"
            continue
        fi
        if [ "$path_name" != "" ]; then
            break
        fi
    done

    ./tamper-cli add $path_name
    echo -e "\033[32m添加成功!\033[0m\n"
    sleep 3
    add_path
}

set_process_names(){
    clear
    echo "正在配置 [进程白名单]"
    echo -e "  \033[33m1.\033[0m 添加进程名\n"
    echo -e "  \033[33m2.\033[0m 删除进程名\n"
    echo -e "  \033[33m-1.\033[0m 返回上一层菜单\c"
    echo -e "  \033[33m0.\033[0m 返回主菜单\n"
    process_names=$(./tamper-cli show-global-process_names)
    echo  "--------------------------------------------------------------------------------"
    echo -e "当前进程白名单: $process_names"
    echo  "--------------------------------------------------------------------------------"
    while((1))
    do
        echo -e "请选择菜单[\033[34m0-2\033[0m]: \c"
        read process_names_select

        if [ "$process_names_select" == "0" ];then
            main_menu
            return
        fi

        if [ "$process_names_select" == "-1" ];then
            modify_config
            return
        fi

        if [ $process_names_select -lt 1 ] || [ $process_names_select -gt 2 ]; then
            echo -e "\033[31m错误: 输入错误,请重新输入\033[0m\n"
            continue
        fi

        if [ "$process_names_select" != "" ]; then
            break
        fi
    done
    echo  "--------------------------------------------------------------------------------"
    echo -e "提示：输入 -1 返回上一层菜单,输入 0 返回主菜单,按 Ctrl + C 退出程序\n"
    case $process_names_select in
        1)
            while((1))
            do
                process_names=$(./tamper-cli show-global-process_names)
                echo  "--------------------------------------------------------------------------------"
                echo -e "当前进程白名单: $process_names"
                echo  "--------------------------------------------------------------------------------"
                echo -e "请输入要添加的进程名称,如sshd: \c"
                read process_names_add
                if [ "$process_names_add" = "-1" ]; then
                    set_process_names
                    return
                fi
                if [ "$process_names_add" = "0" ]; then
                    main_menu
                    return
                fi
                if [ "$process_names_add" = "" ]; then
                    continue
                fi
                ./tamper-cli set global process_names add $process_names_add
            done

            ;;
        2)

            while((1))
            do
                process_names=$(./tamper-cli show-global-process_names)
                echo  "--------------------------------------------------------------------------------"
                echo -e "当前进程白名单: $process_names"
                echo  "--------------------------------------------------------------------------------"
                echo -e "请输入要删除的进程名称,如sshd: \c"
                read process_names_del
                if [ "$process_names_del" = "-1" ]; then
                    set_process_names
                    return
                fi
                if [ "$process_names_del" = "0" ]; then
                    main_menu
                    return
                fi
                if [ "$process_names_del" = "" ]; then
                    continue
                fi
                ./tamper-cli set global process_names del $process_names_del
            done
            ;;
    esac
}

set_uids(){
    clear
    echo "正在配置 [UID白名单]"
    echo -e "  \033[33m1.\033[0m 添加UID\n"
    echo -e "  \033[33m2.\033[0m 删除UID\n"
    echo -e "  \033[33m-1.\033[0m 返回上一层菜单\c"
    echo -e "  \033[33m0.\033[0m 返回主菜单\n"
    uids=$(./tamper-cli show-global-uids)
    echo  "--------------------------------------------------------------------------------"
    echo -e "当前UID白名单: $uids"
    echo  "--------------------------------------------------------------------------------"
    while((1))
    do
        echo -e "请选择菜单[\033[34m0-2\033[0m]: \c"
        read uids_select

        if [ "$uids_select" == "0" ];then
            main_menu
            return
        fi

        if [ "$uids_select" == "-1" ];then
            modify_config
            return
        fi

        if [ $uids_select -lt 1 ] || [ $uids_select -gt 2 ]; then
            echo -e "\033[31m错误: 输入错误,请重新输入\033[0m\n"
            continue
        fi

        if [ "$uids_select" != "" ]; then
            break
        fi
    done
    echo  "--------------------------------------------------------------------------------"
    echo -e "提示：输入 -1 返回上一层菜单,输入 0 返回主菜单,按 Ctrl + C 退出程序\n"
    case $uids_select in
        1)
            while((1))
            do
                uids=$(./tamper-cli show-global-uids)
                echo  "--------------------------------------------------------------------------------"
                echo -e "当前UID白名单: $uids"
                echo  "--------------------------------------------------------------------------------"
                echo -e "请输入要添加的UID,如1000: \c"
                read uids_add
                if [ "$uids_add" = "-1" ]; then
                    set_uids
                    return
                fi
                if [ "$uids_add" = "0" ]; then
                    main_menu
                    return
                fi
                if [ "$uids_add" = "" ]; then
                    continue
                fi
                ./tamper-cli set global uids add $uids_add
            done

            ;;
        2)

            while((1))
            do
                uids=$(./tamper-cli show-global-uids)
                echo  "--------------------------------------------------------------------------------"
                echo -e "当前UID白名单: $uids"
                echo  "--------------------------------------------------------------------------------"
                echo -e "请输入要删除的UID,如1000: \c"
                read uids_del
                if [ "$uids_del" = "-1" ]; then
                    set_uids
                    return
                fi
                if [ "$uids_del" = "0" ]; then
                    main_menu
                    return
                fi
                if [ "$uids_del" = "" ]; then
                    continue
                fi
                ./tamper-cli set global uids del $uids_del
            done
            ;;
    esac
}

show_config(){
    clear
    ./tamper-cli show-global-config
    while((1))
    do
        echo -e "输入 \033[33m0\033[0m 返回主菜单,按 Ctrl + C 退出程序: \c"
        read back_num
        if [ "$back_num" = "0" ]; then
            main_menu
            return
        fi
        if [ "$back_num" = "" ]; then
            continue
        fi
    done
}

modify_config(){
    clear
    ./tamper-cli show-global-config
    echo "----------------------------------------------------------------------"

    echo -e "  \033[33m1.\033[0m 关闭防篡改\c"
    echo -e "  \033[33m2.\033[0m 开启防篡改\n"
    echo -e "  \033[33m3.\033[0m 允许\033[33m[创建文件]\033[0m\c"
    echo -e "  \033[33m4.\033[0m 拒绝\033[33m[创建文件]\033[0m\n"
    echo -e "  \033[33m5.\033[0m 允许\033[33m[创建目录]\033[0m\c"
    echo -e "  \033[33m6.\033[0m 拒绝\033[33m[创建目录]\033[0m\n"
    echo -e "  \033[33m7.\033[0m 允许\033[33m[目录删除]\033[0m\c"
    echo -e "  \033[33m8.\033[0m 拒绝\033[33m[目录删除]\033[0m\n"
    echo -e "  \033[33m9.\033[0m 允许\033[33m[文件修改]\033[0m\c"
    echo -e "  \033[33m10.\033[0m 拒绝\033[33m[文件修改]\033[0m\n"
    echo -e "  \033[33m11.\033[0m 允许\033[33m[文件删除]\033[0m\c"
    echo -e "  \033[33m12.\033[0m 拒绝\033[33m[文件删除]\033[0m\n"
    echo -e "  \033[33m13.\033[0m 允许\033[33m[重命名]\033[0m\c"
    echo -e "  \033[33m14.\033[0m 拒绝\033[33m[重命名]\033[0m\n"
    echo -e "  \033[33m15.\033[0m 允许\033[33m[权限修改]\033[0m\c"
    echo -e "  \033[33m16.\033[0m 拒绝\033[33m[权限修改]\033[0m\n"
    echo -e "  \033[33m17.\033[0m 允许\033[33m[所有者修改]\033[0m\c"
    echo -e "  \033[33m18.\033[0m 拒绝\033[33m[所有者修改]\033[0m\n"
    echo -e "  \033[33m19.\033[0m 允许\033[33m[创建链接]\033[0m\c"
    echo -e "  \033[33m20.\033[0m 拒绝\033[33m[创建链接]\033[0m\n"
    echo -e "  \033[33m21.\033[0m 管理\033[33m[进程白名单]\033[0m\c"
    echo -e "  \033[33m22.\033[0m 管理\033[33m[UID白名单]\033[0m\n"
    echo -e "  \033[33m23.\033[0m 设置不受保护的最小PID\c"
    echo -e "  \033[33m0.\033[0m 返回主菜单\n"

    while((1))
    do
        echo -e "请输入选项: \c"
        read modify_num
        if [ "$modify_num" = "0" ]; then
            main_menu
            return
        fi
        if [ "$modify_num" = "" ]; then
            continue
        fi
        if [ "$modify_num" -lt "1" ] || [ "$modify_num" -gt "23" ]; then
            echo -e "\033[31m错误: 输入的选项不存在,请重新输入!\033[0m\n"
            continue
        fi
        break
    done

    case $modify_num in
        1)
            ./tamper-cli set global status=0
            ;;
        2)
            ./tamper-cli set global status=1
            ;;
        3)
            ./tamper-cli set global is_create=0
            ;;
        4)
            ./tamper-cli set global is_create=1
            ;;
        5)
            ./tamper-cli set global is_mkdir=0
            ;;
        6)
            ./tamper-cli set global is_mkdir=1
            ;;
        7)
            ./tamper-cli set global is_rmdir=0
            ;;
        8)
            ./tamper-cli set global is_rmdir=1
            ;;
        9)
            ./tamper-cli set global is_modify=0
            ;;
        10)
            ./tamper-cli set global is_modify=1
            ;;
        11)
            ./tamper-cli set global is_delete=0
            ;;
        12)
            ./tamper-cli set global is_delete=1
            ;;
        13)
            ./tamper-cli set global is_rename=0
            ;;
        14)
            ./tamper-cli set global is_rename=1
            ;;
        15)
            ./tamper-cli set global is_chmod=0
            ;;
        16)
            ./tamper-cli set global is_chmod=1
            ;;
        17)
            ./tamper-cli set global is_chown=0
            ;;
        18) 
            ./tamper-cli set global is_chown=1
            ;;
        19)
            ./tamper-cli set global is_symlink=0
            ;;
        20)
            ./tamper-cli set global is_symlink=1
            ;;
        21)
            set_process_names
            ;;
        22)
            set_uids
            ;;
        23)
            while((1))
            do
                echo -e "请输入不受保护的最小PID[10-1000]: \c"
                read min_pid
                if [ "$min_pid" = "" ]; then
                    continue
                fi

                if [ "$min_pid" -lt "10" ] || [ "$min_pid" -gt "1000" ]; then
                    echo -e "\033[31m错误: 输入的不受保护的最小PID应当在10-1000之间,请重新输入!\033[0m\n"
                    continue
                fi

                ./tamper-cli set global min_pid=$min_pid
                break
            done
            ;;
    esac

    modify_config

}

show_total(){
    clear
    ./tamper-cli total

    while((1))
    do
        echo -e "输入 \033[33m0\033[0m 返回主菜单,按 Ctrl + C 退出程序: \c"
        read back_num
        if [ "$back_num" = "0" ]; then
            main_menu
            return
        fi
        if [ "$back_num" = "" ]; then
            continue
        fi
    done
}

bind_auth(){
    clear

    while((1))
    do
        echo -e "请粘贴授权码: \c"
        read auth_code
        if [ "$auth_code" = "0" ]; then
            main_menu
            return
        fi
        if [ "$auth_code" = "" ]; then
            continue
        fi
        break
    done

    ./tamper-cli set_auth $auth_code

    while((1))
    do
        echo -e "输入 \033[33m0\033[0m 返回主菜单,按 Ctrl + C 退出程序: \c"
        read back_num
        if [ "$back_num" = "0" ]; then
            main_menu
            return
        fi
        if [ "$back_num" = "" ]; then
            continue
        fi
    done
}

show_log(){
    clear
    echo "----------------------------------------------------------------------"
    ./tamper-cli list
    echo "----------------------------------------------------------------------"
    while((1))
    do
        echo -e "请输入指定 \033[33mpath_id\033[0m 查看日志,输入 \033[33m0\033[0m 返回主菜单: \c"
        read path_id
        if [ "$path_id" = "0" ]; then
            main_menu
            return
        fi
        if [ "$path_id" = "" ]; then
            continue
        fi
        path_name=$(./tamper-cli list|grep -E "^${path_id}\s+"|awk '{print $2}')
        if [ "$path_name" = "" ]; then
            echo -e "\033[31m错误: 路径不存在,请重新输入\033[0m\n"
            continue
        fi
        if [ "$path_name" != "" ]; then
            break
        fi
    done

    ./tamper-cli log $path_id

    echo "----------------------------------------------------------------------"
    echo -e "提示：查看实时日志，请使用: ./tamper-cli log $path_id -f\n"
    echo "----------------------------------------------------------------------"

    while((1))
    do
        echo -e "输入 \033[33m-1\033[0m 返回上一层菜单, 输入 \033[33m0\033[0m 返回主菜单,按 Ctrl + C 退出程序: \c"
        read back_num
        if [ "$back_num" = "0" ]; then
            main_menu
            return
        fi
        if [ "$back_num" = "-1" ]; then
            show_log
        fi
        if [ "$back_num" = "" ]; then
            continue
        fi
    done
}

main_menu(){
clear
echo "=========================================================================="
echo "堡塔防篡改程序 - 命令行版"
echo "=========================================================================="

status="\033[42m正在运行\033[0m"
if [ "$(lsmod|grep tampercore)" = "" ]; then
    status="\033[34m已停止\033[0m"
fi

echo "帮助说明: https://www.bt.cn/bbs/"
echo "反馈问题：https://www.bt.cn/bbs/forum-40-1.html"
echo "=========================================================================="
echo -e "版本：v1.0.0 / 内核版本：$(uname -r) / 状态: $status"
echo "=========================================================================="
auth=$(./tamper-cli show_auth|grep -E '(未激活|错误|无效)')
if [ "$auth" != "" ]; then
    echo -e "授权信息: \033[31m$auth\033[0m"
else
    ./tamper-cli show_auth
fi
echo "=========================================================================="

echo -e "  \033[33m1.\033[0m 管理受保护的文件夹列表\n"
echo -e "  \033[33m2.\033[0m 添加受保护的文件夹\n"
echo -e "  \033[33m3.\033[0m 查看全局配置\n"
echo -e "  \033[33m4.\033[0m 修改全局配置\n"
echo -e "  \033[33m5.\033[0m 查看统计信息\n"
echo -e "  \033[33m6.\033[0m 查看日志\n"
echo -e "  \033[33m7.\033[0m 绑定授权码\n"
echo -e "  \033[33m0.\033[0m 退出\n"

echo -e "提示: 如果你不想执行选项, 按 Ctrl + C 即可退出"
echo "=========================================================================="
while((1))
do
    echo -e "请选择菜单[\033[34m0-7\033[0m]: \c"
    read num
    if [ "$num" = "" ]; then
        continue
    fi

    if [ "$num" -lt "0" ] || [ "$num" -gt "7" ]; then
        echo -e "\033[31m错误: 输入的菜单选项应当在0-7之间,请重新输入!\033[0m\n"
        continue
    fi

    break
done

case $num in
    1)
        show_list
        ;;
    2)
        add_path
        ;;
    3)
        show_config
        ;;
    4)
        modify_config
        ;;
    5)
        show_total
        ;;
    6)
        show_log
        ;;
    7)
        bind_auth
        ;;

    0)
        exit
        ;;
esac


}


cd /www/server/tamper
main_menu
