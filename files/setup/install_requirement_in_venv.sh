#!/bin/bash

SETUP_PATH="files/setup"
SETTINGS_FILE="settings.cfg"
PROXY="$(cat $SETTINGS_FILE | grep -E "PROXY =.*#" | tr "#" "=" | awk -F= '{print $2}' | grep -Eo "[^ ]+")"
OS_VERSION=$(cat /etc/os-release | grep CODENAME | head -n 1 | awk -F= '{print $NF}')

echo -e "\n\nVenv installation STARTED!\n"

if [ "$(whoami)" == "root" ]
then
    echo -e "\n\nNOT RUN AS ROOT!\n"
    exit 1
fi

if [ "$PROXY" != "" ]
then
    PROXY_PIP="--proxy http://$PROXY"
    PROXY_SYSTEM="
\texport http_proxy=http://$PROXY
\texport https_proxy=http://$PROXY"
fi

ENV_PATH=$(pwd)
INSTALLED_FILE=$ENV_PATH/$SETUP_PATH/venv-installed
VENV_PATH=$ENV_PATH/$SETUP_PATH/venv

if test -e $INSTALLED_FILE
then
    rm $INSTALLED_FILE
fi


if test -d $VENV_PATH
then
    rm -rf $VENV_PATH
fi

if test -z "$(which curl)"
then
  CURL_ERROR="curl "
fi

python3 -m venv $VENV_PATH

if [ "$(echo $?)" != "0" ]
then
    echo -e "
Run as root or with sudo:
$PROXY_SYSTEM
\tapt update && apt install python3-venv ${CURL_ERROR}-y

and try again.\n"
    exit 1
else
    . $VENV_PATH/bin/activate
    if [ "$(echo $?)" == "0" ]
    then
        echo -e "\nTrying online installation...\n"
        pip install $PROXY_PIP -r $SETUP_PATH/requirements.txt
        if [ "$(echo $?)" != "0" ]
        then
            echo -e "\nNot connected with internet. Trying offline installation...\n"

            if [ ! -d $ENV_PATH/$SETUP_PATH/venv-pip-whl-${OS_VERSION} ]
            then
                cd $ENV_PATH
                echo -e "\nOffline installation is not compatible with your system: ${OS_VERSION} $(cat /etc/os-release | grep PRETTY_NAME | head -n 1 | awk -F= '{print $NF}')\n"
                exit 1
            fi

            cd $ENV_PATH/$SETUP_PATH/venv-pip-whl-${OS_VERSION}/
            pip install *.whl

            if [ "$(echo $?)" != "0" ]
            then
                cd $ENV_PATH
                echo -e "\nNot all dependencies were successfully installed\n\nSee above messages and try again.\n"
                exit 1
            fi
            cd $ENV_PATH
        fi
    fi
fi

touch $INSTALLED_FILE
echo -e "\nAll dependencies were successfully installed"
echo -e "\n\nVenv installation DONE!\n"
exit 0
