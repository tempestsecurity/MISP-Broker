#!/bin/bash

# DO YOU NOT EDIT THIS FILE

# CONSTANTS
SETTINGS_FILE="settings.cfg"
PYTHON_VERSION="3"
PROXY="$(cat $SETTINGS_FILE | grep -E "PROXY =.*#" | tr "#" "=" | awk -F= '{print $2}' | grep -Eo "[^ ]+")"
TOKEN="$(cat $SETTINGS_FILE | grep -E "TELEGRAM_BOT_TOKEN =.*#" | tr "#" "=" | awk -F= '{print $2}' | grep -Eo "[^ ]+")"
CHAT_ID="$(cat $SETTINGS_FILE | grep -E "TELEGRAM_CHAT_ID =.*#" | tr "#" "=" | awk -F= '{print $2}' | grep -Eo "[^ ]+")"
OPTION=$1
SETUP_PATH="files/setup"
ENV_PATH="$(pwd)"
ENV_PATH_FOLDER=$(echo "$ENV_PATH" | awk -F\/ '{print $NF}')
DATE=$(date +"%Y-%m-%d_%H-%M-%S")
AGENT_FOLDER=$(pwd | awk -F\/ '{print $NF}')
CONFIG_FILE=$(echo $2 | awk -F. '{print $1}')
INSTALLED_SPLUNKAPP_FILE=$ENV_PATH/$SETUP_PATH/splunkapp-installed-$CONFIG_FILE
VENV_PATH=$ENV_PATH/$SETUP_PATH/venv
INTERPRETER="python${PYTHON_VERSION}"
INTERPRETER_FULL="$VENV_PATH/bin/${INTERPRETER}"
INSTALLED_FILE=$ENV_PATH/$SETUP_PATH/venv-installed
STATUS=$(ps -e m | grep "python3" | grep "MISP_Broker.py" | grep -v grep)
CRON_LIST="$(crontab -l)"
CRON_STATUS_BACKUP="$(echo "$CRON_LIST" | grep "$ENV_PATH" | grep "backup_make")"
CRON_BKP_FILE="$ENV_PATH/$SETUP_PATH/cron_bkp.dat"
REQ_INSTALL="$ENV_PATH/$SETUP_PATH/install_requirement_in_venv.sh"
CURL="$(which curl)"
URL="https://api.telegram.org/bot$TOKEN/sendMessage"
HELP="Choose:\n$(cat $0 | grep -Eo "[a-zA-Z_-]+\) +# .*$" | grep -Eo "[a-zA-Z_-]+.*" | sed 's/) \+#/ /g' | sed 's/^/\t/g')

Example:
\t$0 status

Some options need to give a cfg file, example:
\t$0 start alpha

And others is optional, example:
\t$0 logs         \t->\tWill show all cfg logs in real time
\t$0 logs alpha   \t->\tWill show only alpha.cfg log in real time
"
SCRIPT_FILE=$(echo $0)
PROCESS=$(ps -e m | grep MISP_Broker.py | grep -v grep | grep -E "^[ 0-9]+")
VERSION=$(ls v* | grep -E "^v[0-9\.]+")
LOGO="
 __  __  _____   _____  _____    ____               _
|  \/  ||_   _| / ____||  __ \  |  _ \             | |
| \  / |  | |  | (___  | |__) | | |_) | _ __  ___  | | __ ___  _ __
| |\/| |  | |   \___ \ |  ___/  |  _ < | '__|/ _ \ | |/ // _ \| '__|
| |  | | _| |_  ____) || |      | |_) || |  | (_) ||   <|  __/| |
|_|  |_||_____||_____/ |_|      |____/ |_|   \___/ |_|\_\\___| |_|
Security Operations Center - Tempest Security Intelligence
version: $VERSION

"

BY="

                                  -:+*######**###=
                   -:=+**######*+:-.+##=        *#+
    .:=+**#######**+++====**.     .#*-           =##.
 .*#*.      .#*===========#+     :#*           -:+*##:
 :##        +#+===========#*.   :#+     =*##++======##=
 =##        +#+===========+#=  .*+  -*#++============*#*
 -*#=       -#*============+#= :#-+#*=================+*#+                         ..--:=+*################***###*###**********########=.
  =##-       :#+============+*#+##*============*##*+:.  :##:          .:+########**=:-                         =#*                     *##-
   :#*:       -**=============+###+=======+**:.           =##++*###*+:-.                                        +#*.          ..        =##.
     *#+        =##+===+++**####*##+===*#*-         -=*###*=:.                                  :+***+:.         *#=      -#########+.  .+##
      :*#+     .=######*:.        =####+     .+####*:                                        .*###########+      .##-    *#############: :##:
        .+*#*=-.                    +#*+*###=-.*#=                                          .###############+     ##-   :*##############+=*#+
                                 -=##+:.       =#+.                                         -################*.   ##-   :###################*
                            .*#*+.              ##:                                         .*################+   ##-     .+*###############*.
                           *#=                  .##:                                            .=*############: +#+           +############*.
                          .##.                   .*#+                                            :*############:-##:         =##############*
                        .=###+                     +#*:                                        *###############**#**#*++====+*##############+
                     .*##*--*#-                      *##.                                      *##################============*#############-
                   :*#*-    :*#-                       =##+.                                    :################*===========*#############*
                  *#*.       =#*-                        .+##+.                                   :*########+    -=*#####**=:.-=====:   *##.
                .##+          ##*-                           -*###.                                  -*##+                             *##-
                +#*-         +####=                              .-*##**=-                    -++*##*-                                *##:
               .*#*.        :##+.*#*-                    .::====:-.      .::=+**#########**+=:-                                     .*##:
                *#*-        :##+  .##+                :*###############+-.                                                         -##*
                :##=         =##+.  -*#*.            :####*+++++++++*################****################+.                      .*##:
                 =##:          -+########*:          -##================+###################################=                  .*##:
                  -##*                  :+##*-        :##+=================+#*====+*#########################:              .+##*-
                    +##*.                   :##*:        *#*==================#*=======+*###################*            .####-
                      -*##+-                   -*##+:      .+##*+=========================*###############+          .+###*-
                         .+####=-               -:*#####:.      :+##*++====================*#########*=.        .:*###=-
                               +*###############*+.     +#####-         :+***############*##*+:            :####*+
                                                           -*#######*+=-                         -++*#############*=.
                                                         .*############################################################+.
                                                         *#################################################################:
                                                        .#####################################################################.
                                                        +##########################################################################+-
                                                        ####################################################################*+=====*###.
                                                       :###################################################################+=========+##+.
                                                       +################################################################*+=============##*.
                                                      -*############-  :*###########################################*+==================##+
                                                      =############*.     *#####################################+=======================+##.
                                                      +############=    :*#+=====+++*###################*++=============================+##:
                                                     -############*:   +#*==============================================================+##-
                                                     :############+   ##*===============================================================*#*
                                                     *#############*-*#*+==============================================================+#*.
                                                     +#################*==============================================================*#*-
                                                     .*################*=============================================================*##+.
                                                       .###############*+===========================================================++==+*#=
                                                           .:+##########+===============================================================*#+
                                                                       +#*============================================================+##:
                                                                       =###+========================================================+*#*
                             -=++++++=-                             :*#+==========================================================+##+
                      .=*##***+++===+++***##*=.                    +#*+===++***##*++==============================+**===========*##=
                   :*##+=====================+*##+                 :##=========+#*. -+##*+==================+*###*===========*##+.
                 +*############**+===============*##:                .##*====+#*-         +##*+=====+######++#*=========+*#####
            .+##*+==============++*##*+============*#*-                 -*###*.         .+#+==+*##*==#+.     -#*+++*###*:.  :*+
          :##*==++**##**+++==========+*#*+===========##-                 =#*-          +#*+========*##:        -=#+         =#.
        .##**#*+==========+*##*=========+##+=========+##               :##           =###*+========*#=         -*#.        -*+
       -###*+==================+*#*=======*#*+========*#+            +#*-          -#*.    .-::==:-            +#-         =#-
       +##*=======================+*#+======*#+=======+##+####*+:-.=##-          :#*-                         :#:         .#=
       +##+==========================*#*=====*#+======+##+=======+*####=.      :##.                          .#=          **-
       :##+============================##+====*#=====+*##*+===========+*##*. +#*-                      :*#####+.         +#####*+.
        =#*+============================+#+====#*====++====+*#+==========+###+                       +##+==+#*-         :*#=====+##+
         -##+============================*#*===+#+=========================##-                      ##*+====*#+.      .+#*=======+##=
           =##+===========================*#*===#*========================+##.                    .+###+==========+++===========*##=
             =#*+==========================#*+==*#+===================+**##+.                   +#*+===+**+================+*#*+++*#+.    .:=+*########*+=:-
               :*#+========================+#+===+#+====================*#-                  .+#*===================================+###*+=================+*###+.
                  *#*=======================#*=====*#*+=+===============+**                 :#*+=================================+##+===========================+##*-
                    -*#*===============+**#####*+=====+*#+===============#*                +#*+================================+++================================+*##-
                       -*###****##***+==========+*#+=====+*#+============#*                ##+======================================================================+#*:
                         .###+======================*#*====+##*=========*#*                #*+=======================================================================*#+.
                           *#*=======================+*#+====*#+=======*#+                 *#*=======================================================================+#*.
                           .+#*========================*#*===+#*+====*#*-                   *#+======================================================================+#+.
                             -##*======================+#*===+#+==+##*                       :##+===================================================================+#*-
                               .+##*==================+*#+=+##*=:.                            +#**###*++===========================================================*#+
                                   :*###**++++===+++*####+-                                  :#*==========+++++++++++++++****###**+++++=================+++***##**+*#:
                                         .:=++++==-.                                          .=*##**++++++===============================++++++++++++++==========+*#*
                                                                                                         ..-:::====:::==+*#####**++======================+**####*:
                                                                                                                                   ..--::=========::--..

"
# FUNCTIONS

backup_make() {
  echo -e "\nMaking BackUp for $AGENT_FOLDER\n"

  mkdir -p ../BackUp_${AGENT_FOLDER}/${DATE} -v
  mkdir -p ../BackUp_${AGENT_FOLDER}/${DATE}/files/databases
  mkdir -p ../BackUp_${AGENT_FOLDER}/${DATE}/files/setup
  mkdir -p ../BackUp_${AGENT_FOLDER}/${DATE}/configs
  mkdir -p ../BackUp_${AGENT_FOLDER}/${DATE}/logs
  mkdir -p ../BackUp_${AGENT_FOLDER}/${DATE}/runnings

  cp -v files/databases/*.db ../BackUp_${AGENT_FOLDER}/${DATE}/files/databases/
  cp -v files/setup/splunkapp-installed* ../BackUp_${AGENT_FOLDER}/${DATE}/files/setup/
  cp -v settings.cfg ../BackUp_${AGENT_FOLDER}/${DATE}/
  cp -v type_list.txt ../BackUp_${AGENT_FOLDER}/${DATE}/
  cp -v v* ../BackUp_${AGENT_FOLDER}/${DATE}/
  cp -v configs/*.cfg ../BackUp_${AGENT_FOLDER}/${DATE}/configs/
  cp -v logs/*.log ../BackUp_${AGENT_FOLDER}/${DATE}/logs/
  cp -v runnings/*.std ../BackUp_${AGENT_FOLDER}/${DATE}/runnings/
  cp -v telegram.log ../BackUp_${AGENT_FOLDER}/${DATE}/

  cd ../BackUp_${AGENT_FOLDER}/
  BKP_PATH=$(pwd)

  if [ $(ls -lh | grep -E "^d" | wc -l) -gt 10 ]; then
    echo -e "\nClearing old backups..."
    find $BKP_PATH -type d -mtime +10 -exec rm -rf {} \;
  fi

  cd -

  echo -e '\nFINISHED!!! \n'
}


backup_restore() {
  echo -e "\nRestoring BackUp for $AGENT_FOLDER\n"

  if ! test -e ../BackUp_${AGENT_FOLDER}/
  then
    echo -e 'No back ups found!!! \n'
    exit 1
  else
    COUNT=0
    BACKUPS=$(ls ../BackUp_${AGENT_FOLDER}/)
    BACKUPS_TEXT=""
    for b in $BACKUPS
    do
        BACKUPS_LIST[$COUNT]=$b
        BACKUPS_TEXT="${BACKUPS_TEXT}${COUNT} - ${b}\n"
        ((COUNT++))
    done

    BACKUPS_LOOP="N"
    while [[ "$(echo $BACKUPS_LOOP | tr "A-Z" "a-z")" != "y" ]]
    do
      echo -en "\nSelect the BACKUP:\n$BACKUPS_TEXT\nChoose a number: "
      read selected_backup

      echo -en "\nYou was selected the BACKUP: ${BACKUPS_LIST[$selected_backup]}, is correct? [y/N] "
      read correct_backup
      if [ "$(echo $correct_backup | tr "A-Z" "a-z")" == "y" ]
      then

        echo -e "\nFinding for difference in type_list.txt..."
        diff ../BackUp_${AGENT_FOLDER}/${BACKUPS_LIST[$selected_backup]}/type_list.txt type_list.txt

        if [ "$(echo $?)" != "0" ]
        then
          echo -en "\nThe type_list.txt file is different, do you wanna restore the old type_list.txt? [y/N] "
          read replace_typelist
          if [ "$(echo $replace_typelist | tr "A-Z" "a-z")" == "y" ]
          then
              cp -v type_list.txt type_list.txt_new
              cp -v ../BackUp_${AGENT_FOLDER}/${BACKUPS_LIST[$selected_backup]}/type_list.txt .
          fi
        else
          cp -v ../BackUp_${AGENT_FOLDER}/${BACKUPS_LIST[$selected_backup]}/type_list.txt .
        fi

        echo
        cp -v ../BackUp_${AGENT_FOLDER}/${BACKUPS_LIST[$selected_backup]}/files/databases/*.db files/databases/
        cp -v ../BackUp_${AGENT_FOLDER}/${BACKUPS_LIST[$selected_backup]}/files/setup/splunkapp-installed* files/setup/
        cp -v ../BackUp_${AGENT_FOLDER}/${BACKUPS_LIST[$selected_backup]}/configs/*.cfg configs/
        cp -v ../BackUp_${AGENT_FOLDER}/${BACKUPS_LIST[$selected_backup]}/logs/*.log logs/
#        cp -v ../BackUp_${AGENT_FOLDER}/${BACKUPS_LIST[$selected_backup]}/runnings/*.std runnings/
        cp -v ../BackUp_${AGENT_FOLDER}/${BACKUPS_LIST[$selected_backup]}/telegram.log .

        mv settings.cfg settings_new.cfg

        cp -v ../BackUp_${AGENT_FOLDER}/${BACKUPS_LIST[$selected_backup]}/settings.cfg .

        if [ "$(cat settings.cfg | wc -l)" != "$(cat settings_new.cfg | wc -l)" ]
        then
          echo -e "\nNew settings are added:"
        fi

        for var in $(cat settings_new.cfg | grep -Eo '^[A-Z_]+')
        do
          if [ "$(cat settings.cfg | grep -E "^$var = ")" == "" ]
          then
              cat settings_new.cfg | grep -E "^$var = " | tee -a settings.cfg
          fi
        done

        rm -rf settings_new.cfg

        BACKUPS_LOOP="y"
      fi
    done
  fi

  echo -e '\nFINISHED!!! \n'
}

check_dir() {

  if ! test -z "$CONFIG_FILE"; then
    echo -e "CONFIG FILE: $CONFIG_FILE.cfg\n"
  else
    echo -e "CONFIG FILE: All cfg files\n"
  fi

  if [ "$(echo "$ENV_PATH_FOLDER" | grep -Eo "v([0-9]+\.?)+")" != "" ]; then
    echo -e "ATTENTION! YOU NO REMOVED THE VERSION NAME!\nPlease, rename the  $ENV_PATH_FOLDER  directory to  MISP-Broker\n"
    echo -e "\nThe path name must be like: MISP-Broker\n"
    exit 1
  fi
}


install_venv() {
    chmod u+x $REQ_INSTALL
    bash $REQ_INSTALL
    if [ "$(echo $?)" != "0" ]; then
      exit 1
    fi
}


forcekill() {

  if test -z "$CONFIG_FILE"; then
    PID=$(echo "$STATUS" | awk '{print $1}')
  else
    PID=$(echo "$STATUS" | grep "$CONFIG_FILE" | awk '{print $1}')
  fi
  if ! test -z "$PID"; then
    kill $PID
  else
    echo -e "\nNo process found!\n"
  fi
}

internet_test() {
  if [ "$PROXY" != "" ]
  then
      PROXY_SYSTEM="
\texport http_proxy=http://$PROXY
\texport https_proxy=http://$PROXY"
  PX="-x $PROXY"
  fi
  if test -z "$CURL" ; then
    echo -e "
Run as root or with sudo:
$PROXY_SYSTEM
\tapt update && apt install python3-venv ${CURL_ERROR}-y

and try again.\n"
    exit 1
  else
    MY_IP="$(curl -s $PX --connect-timeout 3 --max-time 3 ifconfig.me)"
    if [ "$MY_IP" == "" ]
    then
      echo -e "\nNot internet connection!\nTelegram alerts and virtual environment installation may be not work!\nPlease, check your proxy definition in $SETTINGS_FILE\n"
    fi
  fi
}


start() {

  if test -z "$CONFIG_FILE"; then
    echo -e "$HELP\n\n------------------------ERROR----------------------------\n\nPlease, give a cfg filename located in the path: configs/\nExample:\n\t$0 $OPTION alpha\n\nAvailable options:\n$(ls configs/*.cfg | grep -v default.cfg | awk -F\/ '{print $NF}' | awk -F. '{print $1}' | sed 's/^/\t/g')\n"
    exit 1
  fi

  SIEM=$(cat configs/$CONFIG_FILE.cfg | grep "SIEM = " | awk -F= '{print $NF}' | grep -Eo "[A-Z]+" | sed "s/'//g")
  STATUS=$(ps -e m | grep "python3" | grep "MISP_Broker.py" | grep -E "\b$CONFIG_FILE\b" | grep -v grep)

  if [ "$STATUS" != "" ]; then
    echo -e "Already running: $STATUS"
    exit 1
  fi

  if ! test -d $VENV_PATH || ! test -e $INSTALLED_FILE || test -z "$CURL" ; then
    install_venv
    sleep 3
  fi

  if [ "$(whoami)" == "root" ]; then
    echo -e "\n\nNOT RUN AS ROOT!\n"
    exit 1
  fi

  if [ "$PYTHON_VERSION" == "3.X" ]; then
    echo -e "Please, edit the service.sh file and set the PYTHON_VERSION variable."
    exit 1
  fi

  if [ "$(which $INTERPRETER)" == "" ]; then
    echo -e "$INTERPRETER not found!"
    exit 1
  fi

  . $VENV_PATH/bin/activate

  if [ "$(echo $?)" != "0" ]; then
    echo -e "\nFailed to load virtual environment, try to reinstall venv with:\n\n\t$0 reinstall_venv\n\nand try again.\n"
    exit 1
  fi

  if [ "$SIEM" == "SPLUNK" ]; then
    if ! test -e $INSTALLED_SPLUNKAPP_FILE; then
      $INTERPRETER_FULL MISP_Broker.py $CONFIG_FILE &>/dev/null &

      echo -en "Starting... please, wait."
      while true; do
        APP_STATUS1="$(tail -1 logs/$CONFIG_FILE.log | grep -E "(Process finished|App created)")"
        if test -e logs/$CONFIG_FILE.log; then
          APP_STATUS2="$(tail -1 logs/$CONFIG_FILE.log | grep -E "(Process finished|App created)")"
        else
          APP_STATUS2=""
        fi
        if [ "$APP_STATUS1" == "" ] && [ "$APP_STATUS2" == "" ]; then
          echo -n "."
          sleep 0.5
        else
          echo -e "\n\n$APP_STATUS1\n$APP_STATUS2\n"
          break
        fi
      done

      APP_STATUS="$(tail -1 logs/$CONFIG_FILE.log | grep -E "(App created)")"
      if [ "$APP_STATUS" == "" ]; then
        echo -e "Error while trying to create app,\nplease, fix the errors and run '$0 start $CONFIG_FILE' again as common user.\n"
        bash service.sh stop
        exit 1
      else
        touch $INSTALLED_SPLUNKAPP_FILE
        echo -e "After install the app run '$0 start $CONFIG_FILE' again as common user.\n"
        bash service.sh stop
        exit 0
      fi
    fi
  elif [ "$SIEM" == "" ]; then
    echo -e "Please, config the configs/$CONFIG_FILE.cfg file!"
    exit 1
  fi

  $INTERPRETER_FULL MISP_Broker.py $CONFIG_FILE &> /dev/null &

  addcron

  echo -e "Started!\n\nPlease, run: $SCRIPT_FILE status  and  $SCRIPT_FILE logs  to see if is everything ok.\n"
  #tail -f misp_*
}

startall() {
    DATE=$(date)
    echo -e "\n\n---------------------------\n\nBegin: $DATE\n\nStarting all cfg files...\n"

    SCRIPT=.script.sh

    echo -e '#!/bin/bash\n' > $SCRIPT
    crontab -l | grep -E "@reboot cd $ENV_PATH; $VENV_PATH/bin/python3 MISP_Broker.py " | sed 's/@reboot //g' >> $SCRIPT

    chmod +x $SCRIPT
    bash $SCRIPT
    rm $SCRIPT

    echo

    bash $0 status

    echo -e "\nEnd: $(date)"
    sleep 3
    exit 0
}


stop() {

  if test -z "$CONFIG_FILE"; then
    echo -e ""
    echo -e "$HELP\n\n------------------------ERROR----------------------------\n\nPlease, give a cfg filename located in the path: configs/\nExample:\n\t$0 $OPTION alpha\n\nAvailable options:\n$(ls configs/*.cfg | grep -v default.cfg | awk -F\/ '{print $NF}' | awk -F. '{print $1}' | sed 's/^/\t/g')\n"
    exit 1
  fi

  if test -e runnings/$CONFIG_FILE.std; then
    rm runnings/$CONFIG_FILE.std
  fi

  status
  echo -en "Finishing... please, wait."

  count=0

  while true; do
    FINISH="$(tail -10 logs/$CONFIG_FILE.log | grep "run_start_date")"
    STATUS=$(ps -e m | grep "python3" | grep "MISP_Broker.py" | grep -E "\b$CONFIG_FILE\b" | grep -v grep)
    if [ "$FINISH" == "" ] && [ "$STATUS" != "" ]; then
      echo -n "."
      sleep 0.2
      ((count++))
    else
      echo -e "\n\n$FINISH\n"
      echo -e 'FINISHED!!! \n'
      exit 0
    fi

    if [ $count -eq 3000 ] && [ "$STATUS" != "" ]; then
      forcekill
      echo -e "\n\nStop timeout, forced kill!\n\n$(tail -2 logs/$CONFIG_FILE.log)\n"
      exit 1
    fi

  done
}

stopall() {
    DATE=$(date)
    echo -e "\n\n---------------------------\n\nBegin: $DATE\n\nStoping all process...\n"

    #PROCESS=$(ps -e m | grep MISP_Broker.py | grep -v grep | awk '{print $NF}')
    PROCESS=$(ps -e m | grep MISP_Broker.py | grep -v grep | awk '{print $NF,"\t\t PID:",$1}' | sort -n | awk '{print "PID: "$NF"\t"$1}')
    TOTAL=$(echo "$PROCESS" | wc -l)


    while [ $TOTAL -gt 0 ]
    do
            rm $ENV_PATH/runnings/*.std &> /dev/null &

            clear
            echo -e "$LOGO\n\nBegin: $DATE\n\nStoping all process...\n"

            PROCESS=$(ps -e m | grep MISP_Broker.py | grep -v grep | awk '{print $NF,"\t\t PID:",$1}' | sort -n | awk '{print "PID: "$NF"\t"$1}')
            TOTAL=$(echo "$PROCESS" | wc -l)

            if [ "$TOTAL" == "1" ] && [ "$(echo "$PROCESS" | wc -w)" == "0"  ]
            then
                    TOTAL=0
            fi
            echo
            echo -e "Stoping: $TOTAL\n\n$PROCESS\n"
            L=$(tail -n 1 $ENV_PATH/logs/*.log)
            echo -e "\n$L\n"
            date
            sleep 1
    done

    echo -e "\nEnd: $(date)\n\nATTENTION: All enabled cfg files will autostart in 20 minutes!!!\nEnabled cfg: $(crontab -l | grep -E "@reboot cd .*MISP-Broker; .*python3 MISP_Broker.py " | sed 's/@reboot //g' | wc -l)\n"
    sleep 3
    exit 0
}

status() {
  echo -e "Total enabled in cron: $(crontab -l | grep -E "@reboot cd .*MISP-Broker; .*python3 MISP_Broker.py " | sed 's/@reboot //g' | wc -l)"
  crontab -l | grep -E "@reboot cd .*MISP-Broker; .*python3 MISP_Broker.py " | sed 's/@reboot //g' | grep -Eo "MISP_Broker.py [^&]+" | sed 's/MISP_Broker.py /  /g'

  if [ "$STATUS" == "" ]; then
    echo -e '\nNot running! \n'
    exit 1
  else
    echo -e "\nTotal running:\n$STATUS \n"
  fi
}

logs() {

  if test -z "$CONFIG_FILE"; then
    tail -f logs/*.log
  else
    tail -f logs/$CONFIG_FILE.log
  fi

}

addcron() {

  if test -z "$CONFIG_FILE"; then
    echo -e "$HELP\n\n------------------------ERROR----------------------------\n\nPlease, give a cfg filename located in the path: configs/\nExample:\n\t$0 $OPTION alpha\n\nAvailable options:\n$(ls configs/*.cfg | grep -v default.cfg | awk -F\/ '{print $NF}' | awk -F. '{print $1}' | sed 's/^/\t/g')\n"
    exit 1
  fi

  if [ "$CRON_STATUS_BACKUP" == "" ]; then
    crontab -l >$CRON_BKP_FILE
    echo "0 0 * * * cd $ENV_PATH; bash service.sh backup_make" >>$CRON_BKP_FILE
    crontab $CRON_BKP_FILE
    if [ "$?" == "0"  ]; then
      echo -e "Broker BACKUP added to cron!"
    else
      echo -e "FAIL when try to add Broker BACKUP to cron!"
    fi
  fi

  CRON_STATUS_BOOTSTART="$(echo "$CRON_LIST" | grep "$ENV_PATH" | grep "MISP_Broker.py $CONFIG_FILE")"

  if [ "$CRON_STATUS_BOOTSTART" == "" ]; then
    crontab -l >$CRON_BKP_FILE
    echo "@reboot cd $ENV_PATH; $INTERPRETER_FULL MISP_Broker.py $CONFIG_FILE &> /dev/null &" >>$CRON_BKP_FILE
    crontab $CRON_BKP_FILE
    if [ "$?" == "0"  ]; then
      echo -e "BOOTSTART $CONFIG_FILE added to cron!"
    else
      echo -e "FAIL when try to add BOOTSTART $CONFIG_FILE to cron!"
    fi
  fi

  CRON_STATUS_CHECK="$(echo "$CRON_LIST" | grep "$ENV_PATH" | grep "check" | grep "$CONFIG_FILE")"

  if [ "$CRON_STATUS_CHECK" == "" ]; then
    crontab -l >$CRON_BKP_FILE
    echo "*/10 * * * * cd $ENV_PATH; bash service.sh check $CONFIG_FILE" >>$CRON_BKP_FILE
    crontab $CRON_BKP_FILE
    if [ "$?" == "0"  ]; then
      echo -e "CHECK $CONFIG_FILE added to cron!"
    else
      echo -e "FAIL when try to add CHECK $CONFIG_FILE to cron!"
    fi
  fi

  echo ""

  if [ "$CRON_STATUS_BOOTSTART" != "" ] && [ "$CRON_STATUS_CHECK" != "" ] && [ "$CRON_STATUS_BACKUP" != "" ]; then
    echo -e "No cron to add\n"
  fi
}


delcron() {

  if test -z "$CONFIG_FILE"; then
    echo -e "$HELP\n\n------------------------ERROR----------------------------\n\nPlease, give a cfg filename located in the path: configs/\nExample:\n\t$0 $OPTION alpha\n\nAvailable options:\n$(ls configs/*.cfg | grep -v default.cfg | awk -F\/ '{print $NF}' | awk -F. '{print $1}' | sed 's/^/\t/g')\n"
    exit 1
  fi

  CRON_STATUS_BOOTSTART="$(echo "$CRON_LIST" | grep "$ENV_PATH" | grep "MISP_Broker.py $CONFIG_FILE")"

  if [ "$CRON_STATUS_BOOTSTART" != "" ]; then
    crontab -l | grep -v "@reboot cd $ENV_PATH; $INTERPRETER_FULL MISP_Broker.py $CONFIG_FILE &> /dev/null &" >$CRON_BKP_FILE
    crontab $CRON_BKP_FILE
    if [ "$?" == "0"  ]; then
      echo -e "BOOTSTART $CONFIG_FILE removed from cron!"
    else
      echo -e "FAIL when try to remove BOOTSTART $CONFIG_FILE from cron!"
    fi
  fi

  CRON_STATUS_CHECK="$(echo "$CRON_LIST" | grep "$ENV_PATH" | grep "check" | grep "$CONFIG_FILE")"

  if [ "$CRON_STATUS_CHECK" != "" ]; then
    crontab -l | grep -v "cd $ENV_PATH; bash service.sh check $CONFIG_FILE" >$CRON_BKP_FILE
    crontab $CRON_BKP_FILE
    if [ "$?" == "0"  ]; then
      echo -e "CHECK $CONFIG_FILE removed from cron!"
    else
      echo -e "FAIL when try to remove CHECK $CONFIG_FILE from cron!"
    fi
  fi

  echo ""

  if [ "$CRON_STATUS_BOOTSTART" == "" ] && [ "$CRON_STATUS_CHECK" == "" ]; then
    echo -e "No cron to remove\n"
  fi
}

check() {

  if test -z "$CONFIG_FILE"; then
    echo -e "$HELP\n\n------------------------ERROR----------------------------\n\nPlease, give a cfg filename located in the path: configs/\nExample:\n\t$0 $OPTION alpha\n\nAvailable options:\n$(ls configs/*.cfg | grep -v default.cfg | awk -F\/ '{print $NF}' | awk -F. '{print $1}' | sed 's/^/\t/g')\n"
    exit 1
  fi

  CRON_PATH=$(crontab -l | grep "MISP-Broker"| grep -Eo "cd.*" | grep "$CONFIG_FILE" | tail -1  | tr " " ";" | awk -F\; '{print $2}')

  if [ "$CRON_PATH" == "" ]; then

    MESSAGE="Cron for MISP Broker does not exists in:\nConfig: $CONFIG_FILE\nServer: $(cat /etc/hostname)\nUser: $(whoami)\n\nPlease, run: $0 enable $CONFIG_FILE"
    MESSAGE="$(echo -e $MESSAGE)"
    if [ "$PROXY" == "" ]; then
      curl -s -X POST $URL -d chat_id=$CHAT_ID -d text="$MESSAGE"
    else
      curl -s -x $PROXY -X POST $URL -d chat_id=$CHAT_ID -d text="$MESSAGE"
    fi
  elif [ "$(find "$CRON_PATH/logs/" -name "$CONFIG_FILE.log" -type f -mmin +20)" != "" ]; then
    process=$(ps -e m | grep "python3" | grep "MISP_Broker.py" | grep -E "\b$CONFIG_FILE\b" | grep -v grep)
    forcekill

    if [ $? -eq 0 ] && [ "$process" != "" ]; then
      a="The process has been killed: $process"
    else
      a="No process has been found."
    fi

    cd $ENV_PATH
    $INTERPRETER_FULL MISP_Broker.py $CONFIG_FILE &> /dev/null &

    MESSAGE="$(date)\n\nThe MISP Broker service for \nConfig: $CONFIG_FILE\nServer: $(cat /etc/hostname)\nUser: $(whoami)\nhas been down over 20 minutes! \n\n$a\n\n$b"
    MESSAGE="$(echo -e $MESSAGE)"

    echo -e "$MESSAGE\n\n-------------\n" >>telegram.log
    if [ "$PROXY" == "" ]; then
      curl -s -X POST $URL -d chat_id=$CHAT_ID -d text="$MESSAGE"
    else
      curl -s -x $PROXY -X POST $URL -d chat_id=$CHAT_ID -d text="$MESSAGE"
    fi

    MESSAGE="$(echo -e "MISP Broker: $CONFIG_FILE.log\n\n$(tail -4 logs/$CONFIG_FILE.log)")"
    if [ "$PROXY" == "" ]; then
      curl -s -X POST $URL -d chat_id=$CHAT_ID -d text="$MESSAGE"
    else
      curl -s -x $PROXY -X POST $URL -d chat_id=$CHAT_ID -d text="$MESSAGE"
    fi

  fi
}

echo -e "$LOGO\n"

mkdir -p logs
mkdir -p runnings
mkdir -p files/databases

if test -z "$1"; then
  echo -e "$HELP"
  exit 1
fi

if test -z "$CRON_LIST"; then
  echo -e '\nRemember to initializer your cron!\n'
fi

#chmod +x backup_*.sh
check_dir $2

if [ "$CONFIG_FILE" != "" ]; then
  if [ "$(ls configs/*.cfg | grep -v default.cfg | awk -F\/ '{print $NF}' | awk -F. '{print $1}' | grep "$CONFIG_FILE")" == "" ]; then
    echo -e "\nInvalid CONFIG FILE: $CONFIG_FILE\n\nAvailable options:"
    ls configs/*.cfg | grep -v default.cfg | awk -F\/ '{print $NF}' | awk -F. '{print $1}' | sed 's/^/\t/g'
    echo
    exit 1
  fi
fi

internet_test

# CONDITIONS

case $OPTION in
status) #              ->\t\tShow status of all Broker config files processes
  status
  ;;
logs) #                ->\t\tShow logs of all Broker config file running process or justo one
  logs
  ;;
start) #               ->\t\tStart one Broker config file running process
  start
  ;;
stop) #                ->\t\tStop one Broker config file running process
  stop
  ;;
restart) #             ->\t\tRestart one Broker config file service
  stop
  sleep 5
  start
  ;;
startall) #            ->\t\tStart all Broker config files listed in cron
  startall
  ;;
stopall) #             ->\t\tStop all Broker config files with running process
  stopall
  ;;
restartall) #          ->\t\tRestart all Broker config files listed in cron
  stopall
  sleep 5
  startall
  ;;
kill) #                ->\t\tForce kill all Broker config files running process or just one config file running process
  forcekill
  ;;
enable) #              ->\t\tAdd Broker config file service from cron
  addcron
  ;;
disable) #             ->\t\tRemove Broker config file service from cron
  delcron
  ;;
check) #               ->\t\tVerify if Broker config file service is running with activity
  check
  ;;
backup_make) #         ->\t\tMake a backup of important Broker files
  backup_make
  ;;
backup_restore) #      ->\t\tRestore existing backups of important Broker files
  backup_restore
  ;;
install_venv) #        ->\t\tInstall python 3 virtual environment for Broker
  install_venv
  ;;
reinstall_venv) #      ->\t\tReinstall python 3 virtual environment for Broker
  install_venv
  ;;
lookthis) #            ->\t\tWait! What is it?! O_o
  echo -e "${LOGO}\n(use arrow UP and DOWN to scroll)\n\nDeveloped by:${BY}\n\nPress q to quit:" | less
  echo -e "If you understand me... ;)\n"
  ;;
help) #                ->\t\tShow this help message
  echo -e "$HELP"
  ;;
*)
  echo -e "$HELP"
  ;;
esac
