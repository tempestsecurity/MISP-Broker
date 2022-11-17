#!/bin/bash

CURRENT=$(ls MISP-Broker/v* | grep -E "v[0-9\.]+" | awk -F\/ '{print $NF}' | grep -Eo "[0-9\.]+")

if [ "$(echo $CURRENT)" == "" ]
then
  CURRENT=$(ls v* | grep -E "v[0-9\.]+" | awk -F\/ '{print $NF}' | grep -Eo "[0-9\.]+")
fi

if [ "$(echo $CURRENT)" == "" ]
then
  CURRENT="Unknown"
fi

BROKER_PATH="$(pwd)/MISP-Broker"

VERSION=$(ls -l MISP-Broker*.* | grep -E '(.tar.gz|.zip)' 2> /dev/null | awk '{print $NF}' | grep -Eo "[0-9\.]+" | sed 's/.$//g' | grep -Eo "[0-9\.]+" | sort -u | tail -n 1)

if test -z "$VERSION"
then
    VERSION=$(ls -l MISP-Broker-main.zip 2> /dev/null | awk -F'-' '{print $NF}' | sed 's/.zip$//g' | sort -u | tail -n 1)
fi

LOCAL_PATH=$(ls | grep -E "^MISP-Broker$")
LOGO="
 __  __  _____   _____  _____    ____               _
|  \/  ||_   _| / ____||  __ \  |  _ \             | |
| \  / |  | |  | (___  | |__) | | |_) | _ __  ___  | | __ ___  _ __
| |\/| |  | |   \___ \ |  ___/  |  _ < | '__|/ _ \ | |/ // _ \| '__|
| |  | | _| |_  ____) || |      | |_) || |  | (_) ||   <|  __/| |
|_|  |_||_____||_____/ |_|      |____/ |_|   \___/ |_|\_\\___| |_|
Security Operations Center - Tempest Security Intelligence

Current version: $CURRENT
Version available for upgrade: $VERSION"

echo -e "$LOGO"

if test -z "$VERSION"
then
  echo -e "\nUpdate file not found!\nExample: MISP-Broker-5.1.tar.gz\n"
  exit 1
fi

user_name=$(ls -lh | awk '{print $3}' | tail -n 1)
group_name=$(ls -lh | awk '{print $4}' | tail -n 1)

if test -z "$LOCAL_PATH"
then
  echo -e "\nThe  MISP-Broker-${VERSION}.tar.gz  and the  $(echo $0 | sed 's/\.\///g')  need to be in the same directory that  MISP-Broker, not inside or above.\n\nExample:\n
\t$(whoami)@$(hostname):~$ ls -lh
\t$(ls -lh ../ | grep -E "^\total")
\tdrwxrwxr-x 11 $user_name $group_name 4,0K mai 19 10:58 BackUp_MISP-Broker
\tdrwxrwxr-x  6 $user_name $group_name 4,0K mai 19 19:07 MISP-Broker
\t-rwxrw-r--  1 $user_name $group_name   47 mai 19 18:52 misp-broker-updater.sh
\t-rw-rw-r--  1 $user_name $group_name  17M mai 13 18:44 MISP-Broker-${VERSION}.tar.gz
\n"
  exit 1
fi

COMPARE="$CURRENT
$VERSION"

COMPARE=$(echo "$COMPARE" | sort -u | tail -n 1 | grep "$VERSION")

if [ "$(echo $COMPARE)" == "" ]
then
  echo -e "\nDowngrade is not allowed!\n"
  exit 1
fi

echo -en "\nExecute upgrade? [y/N]: "
read do_upgrade

if [ "$(echo $do_upgrade | tr "A-Z" "a-z")" == "y" ]
then
  echo -en "\nAre you sure?! [y/N]: "
  read correct
  if [ "$(echo $correct | tr "A-Z" "a-z")" != "y" ]
  then
    echo -e "\nBye, bye.\n"
    exit 0
  fi
else
  echo -e "\nBye, bye.\n"
  exit 0
fi
cd MISP-Broker/

chmod u+x service.sh
./service.sh stopall

if [ -z "$(ps -e m | grep MISP_Broker | grep -v grep)" ]
then
  ./service.sh backup_make

  echo -e "\n\nRemoving old files...\n"

  rm -rfv $(ls files/setup/ | grep -Ev "(splunkapp-installe.*|\.dat)" | sed 's/^/files\/setup\//g' | tr "\n" " ") v[0-9]*

  cd ..

  echo -e "\n\nStarting update...\n"

  if [ "$(echo $VERSION)" == "main" ]
  then
    echo -en "From main branch "
    unzip MISP-Broker-main.zip
    cp -rv MISP-Broker-main/*  MISP-Broker/
    rm -rv MISP-Broker-main.zip MISP-Broker-main
  else
    echo -e "From release branch Archive:  MISP-Broker-${VERSION}.tar.gz"
    tar xzvf MISP-Broker-${VERSION}.tar.gz -C MISP-Broker/ --strip-components=1
    rm -rv MISP-Broker-${VERSION}.tar.gz
  fi

  echo -e "\n\nUpdate finished.\n\n\nDefining permissions...\n"

  cd -
  chmod u+x *.sh files/setup/*.sh
  cd -
  chown $(whoami) -R MISP-Broker


  echo -e "\n\nLooking for changes in settings.cfg...\n"

  diff BackUp_MISP-Broker/$(ls BackUp_MISP-Broker | tail -n 1)/settings.cfg MISP-Broker/settings.cfg

  if [ "$(echo $?)" != "0" ]
  then
    echo -e "\n\nThe settings.cfg files have divergences, analyze and make the necessary changes if necessary.\n"
  else
    echo -e "No divergence found."
  fi

  echo -e "\n\nAll done.\n\nNow MISP Broker is in the version: $(ls MISP-Broker/v[0-9]* | awk -F\/ '{print $NF}')\n\nPlease, start MISP-Broker again with:\n\n\tcd MISP-Broker\n\t./service.sh install_venv\n\t./service.sh startall\n"
  echo -e "You are in: $(pwd)"

else
  echo "MISP Broker need to be stopped before an update!"
fi
