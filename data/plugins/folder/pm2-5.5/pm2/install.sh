#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
export HOME=/root
install_tmp='/tmp/bt_install.pl'
public_file=/www/server/panel/install/public.sh
if [ ! -f $public_file ];then
	wget -O $public_file http://download.bt.cn/install/public.sh -T 5;
fi
. $public_file

download_Url=$NODE_URL
export NVM_NODEJS_ORG_MIRROR=http://npm.taobao.org/mirrors/node

Install_nvm()
{ # this ensures the entire script is downloaded #

nvm_install_dir() {
  printf %s "/www/server/nvm"
}

nvm_latest_version() {
  echo "v0.33.4"
}


nvm_profile_is_bash_or_zsh() {
  local TEST_PROFILE
  TEST_PROFILE="${1-}"
  case "${TEST_PROFILE-}" in
    *"/.bashrc" | *"/.bash_profile" | *"/.zshrc")
      return
    ;;
    *)
      return 1
    ;;
  esac
}


#
# Node.js version to install
#
nvm_node_version() {
  echo "$NODE_VERSION"
}


#
# Automatically install Node.js
#
nvm_install_node() {
  local NODE_VERSION
  NODE_VERSION="$(nvm_node_version)"

  if [ -z "$NODE_VERSION" ]; then
    return 0
  fi

  echo "=> Installing Node.js version $NODE_VERSION"
  nvm install "$NODE_VERSION"
  local CURRENT_NVM_NODE

  CURRENT_NVM_NODE="$(nvm_version current)"
  if [ "$(nvm_version "$NODE_VERSION")" == "$CURRENT_NVM_NODE" ]; then
    echo "=> Node.js version $NODE_VERSION has been successfully installed"
  else
    echo >&2 "Failed to install Node.js $NODE_VERSION"
  fi
}

nvm_try_profile() {
  if [ -z "${1-}" ] || [ ! -f "${1}" ]; then
    return 1
  fi
  echo "${1}"
}

#
# Detect profile file if not specified as environment variable
# (eg: PROFILE=~/.myprofile)
# The echo'ed path is guaranteed to be an existing file
# Otherwise, an empty string is returned
#
nvm_detect_profile() {
  if [ -n "${PROFILE}" ] && [ -f "${PROFILE}" ]; then
    echo "${PROFILE}"
    return
  fi

  local DETECTED_PROFILE
  DETECTED_PROFILE=''
  local SHELLTYPE
  SHELLTYPE="$(basename "/$SHELL")"

  if [ "$SHELLTYPE" = "bash" ]; then
    if [ -f "$HOME/.bashrc" ]; then
      DETECTED_PROFILE="$HOME/.bashrc"
    elif [ -f "$HOME/.bash_profile" ]; then
      DETECTED_PROFILE="$HOME/.bash_profile"
    fi
  elif [ "$SHELLTYPE" = "zsh" ]; then
    DETECTED_PROFILE="$HOME/.zshrc"
  fi

  if [ -z "$DETECTED_PROFILE" ]; then
    for EACH_PROFILE in ".profile" ".bashrc" ".bash_profile" ".zshrc"
    do
      if DETECTED_PROFILE="$(nvm_try_profile "${HOME}/${EACH_PROFILE}")"; then
        break
      fi
    done
  fi

  if [ ! -z "$DETECTED_PROFILE" ]; then
    echo "$DETECTED_PROFILE"
  fi
}

#
# Check whether the user has any globally-installed npm modules in their system
# Node, and warn them if so.
#
nvm_check_global_modules() {
  command -v npm >/dev/null 2>&1 || return 0

  local NPM_VERSION
  NPM_VERSION="$(npm --version)"
  NPM_VERSION="${NPM_VERSION:--1}"
  [ "${NPM_VERSION%%[!-0-9]*}" -gt 0 ] || return 0

  local NPM_GLOBAL_MODULES
  NPM_GLOBAL_MODULES="$(
    npm list -g --depth=0 |
    command sed -e '/ npm@/d' -e '/ (empty)$/d'
  )"

  local MODULE_COUNT
  MODULE_COUNT="$(
    command printf %s\\n "$NPM_GLOBAL_MODULES" |
    command sed -ne '1!p' |                     # Remove the first line
    wc -l | tr -d ' '                           # Count entries
  )"

  if [ "${MODULE_COUNT}" != '0' ]; then
    # shellcheck disable=SC2016
    echo '=> You currently have modules installed globally with `npm`. These will no'
    # shellcheck disable=SC2016
    echo '=> longer be linked to the active version of Node when you install a new node'
    # shellcheck disable=SC2016
    echo '=> with `nvm`; and they may (depending on how you construct your `$PATH`)'
    # shellcheck disable=SC2016
    echo '=> override the binaries of modules installed with `nvm`:'
    echo

    command printf %s\\n "$NPM_GLOBAL_MODULES"
    echo '=> If you wish to uninstall them at a later point (or re-install them under your'
    # shellcheck disable=SC2016
    echo '=> `nvm` Nodes), you can remove them from the system Node as follows:'
    echo
    echo '     $ nvm use system'
    echo '     $ npm uninstall -g a_module'
    echo
  fi
}

download_nvm(){
  wget -O /tmp/nvm-$(nvm_latest_version).zip $download_Url/install/src/nvm-$(nvm_latest_version).zip -T 20
  cd /tmp && unzip -o /tmp/nvm-$(nvm_latest_version).zip
  cd -
  if [ -f "$(nvm_install_dir)" ]; then
    rm -rf "$(nvm_install_dir)"
  fi

  \mv /tmp/nvm-$(nvm_latest_version) "$(nvm_install_dir)"
}

nvm_do_install() {
  download_nvm
  echo

  local NVM_PROFILE
  NVM_PROFILE="$(nvm_detect_profile)"
  local PROFILE_INSTALL_DIR
  PROFILE_INSTALL_DIR="$(nvm_install_dir| sed "s:^$HOME:\$HOME:")"

  SOURCE_STR="\nexport NVM_DIR=\"${PROFILE_INSTALL_DIR}\"\n[ -s \"\$NVM_DIR/nvm.sh\" ] && \\. \"\$NVM_DIR/nvm.sh\"  # This loads nvm\n"
  COMPLETION_STR="[ -s \"\$NVM_DIR/bash_completion\" ] && \\. \"\$NVM_DIR/bash_completion\"  # This loads nvm bash_completion\n"
  BASH_OR_ZSH=false

  if [ -z "${NVM_PROFILE-}" ] ; then
    echo "=> Profile not found. Tried ${NVM_PROFILE} (as defined in \$PROFILE), ~/.bashrc, ~/.bash_profile, ~/.zshrc, and ~/.profile."
    echo "=> Create one of them and run this script again"
    echo "=> Create it (touch ${NVM_PROFILE}) and run this script again"
    echo "   OR"
    echo "=> Append the following lines to the correct file yourself:"
    command printf "${SOURCE_STR}"
  else
    if nvm_profile_is_bash_or_zsh "${NVM_PROFILE-}"; then
      BASH_OR_ZSH=true
    fi
    if ! command grep -qc '/nvm.sh' "$NVM_PROFILE"; then
      echo "=> Appending nvm source string to $NVM_PROFILE"
      command printf "${SOURCE_STR}" >> "$NVM_PROFILE"
    else
      echo "=> nvm source string already in ${NVM_PROFILE}"
    fi
    # shellcheck disable=SC2016
    if ${BASH_OR_ZSH} && ! command grep -qc '$NVM_DIR/bash_completion' "$NVM_PROFILE"; then
      echo "=> Appending bash_completion source string to $NVM_PROFILE"
      command printf "$COMPLETION_STR" >> "$NVM_PROFILE"
    else
      echo "=> bash_completion source string already in ${NVM_PROFILE}"
    fi
  fi
  if ${BASH_OR_ZSH} && [ -z "${NVM_PROFILE-}" ] ; then
    echo "=> Please also append the following lines to the if you are using bash/zsh shell:"
    command printf "${COMPLETION_STR}"
  fi

  # Source nvm
  # shellcheck source=/dev/null
  \. "$(nvm_install_dir)/nvm.sh"

  nvm_check_global_modules

  nvm_install_node

  nvm_reset

  echo "=> Close and reopen your terminal to start using nvm or run the following to use it now:"
  command printf "${SOURCE_STR}"
  if ${BASH_OR_ZSH} ; then
    command printf "${COMPLETION_STR}"
  fi
}

#
# Unsets the various functions defined
# during the execution of the install script
#
nvm_reset() {
  unset -f nvm_has nvm_install_dir nvm_latest_version nvm_profile_is_bash_or_zsh \
    nvm_source nvm_node_version nvm_download install_nvm_from_git nvm_install_node \
    install_nvm_as_script nvm_try_profile nvm_detect_profile nvm_check_global_modules \
    nvm_do_install nvm_reset
}

[ "_$NVM_ENV" = "_testing" ] || nvm_do_install

} # this ensures the entire script is downloaded #

Uninstall_nvm(){
	source /www/server/nvm/nvm.sh
	pm2 stop all
	rm -rf /www/server/nvm
	sed -i "/NVM/d" /root/.bash_profile
	sed -i "/NVM/d" /root/.bashrc
	rm -rf /www/server/panel/plugin/pm2
	rm -rf /root/.pm2
	rm -rf /root/.npm
	rm -rf /root/.npmrc
}

backup_folder(){
  # 备份文件
  pm2_dir=/root/.pm2/dump.pm2
  # 判断文件是否存在
  if [ -f "$pm2_dir" ]; then
    # 备份文件
    \cp -p "$pm2_dir" "/tmp/bak_pm2"
  fi
}

restore_folder(){
  # 还原备份文件
  pm2_dir=/root/.pm2/dump.pm2
  # 判断文件是否存在
  if [ -f "/tmp/bak_pm2" ]; then
    # 备份文件
    \cp -p "/tmp/bak_pm2" "$pm2_dir"
    rm -rf "/tmp/bak_pm2" 
  fi
}

action=$1
if [ "${1}" == 'install' ];then
  backup_folder
	Install_nvm
	. ~/.bash_profile
	. ~/.bashrc

	source /www/server/nvm/nvm.sh
	nvm install --lts
	oldreg=`npm get registry`
	npm config set registry http://registry.npm.taobao.org/
	npm install -g pm2
	npm config set registry $oldreg
	mkdir -p /www/server/panel/plugin/pm2
	echo '安装完成' > $install_tmp
  restore_folder
else
	Uninstall_nvm
fi

