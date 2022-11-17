# MISP Broker
&nbsp;

Use **README.pt-BR.md** for Portuguese Brazilian Documentation.

&nbsp;

**MISP Broker** is a tool developed by the platform team of the Security Operations Center (SOC) of [**Tempest Security Intelligence**](https://www.tempest.com.br/). Its purpose is to perform a manageable and reliable integration of the MISP Indicators of Compromise (IoC) in Splunk, QRadar and other platforms that can use CSV type table files like *block list*.
\
\
The actions taken in the MISP are reflected in the SIEMs and platforms quickly, depending on the hardware and network conditions. In an environment where there are SIEM, firewall, antivirus, EDR, SOAR and other platforms that can use CSVs, the data will always be updated uniformly, consistently and without the need to keep updating the platforms manually, MISP Broker does everything automatically.
\
\
A simple *thumbs up* click on an attribute in MISP (via the web interface) and in a matter of seconds it will be included in SIEMs and platforms with renewed TTL (means its lived days have been reset) and a click on the *thumbs down* will remove it.
\
\
Using MISP Broker there will be significant performance improvements in the execution of use cases in SIEMs and platforms as the raw data stays in the application itself, avoiding excessive requests for data (hashs, IPs, domains, etc) to the MISP at each execution/test/validation, also avoiding the possibility of not detecting a possible threat due to failure of communication with the MISP during the action of the application.
\
\
In case of lack of communication with the SIEM or inaccessible CSV directory, the MISP Broker continues working, collecting information from the MISP, storing it in its database and at the opportune moment when the communication or directory is available, the synchronizations with SIEMs and/or platforms will be performed at intervals so that the large amount of information accumulated in the queue does not burden the SIEMs and platforms.
\
\
MISP Broker also sends alerts via Telegram if it is having problems running, so you can be sure that everything is running smoothly.
\
&nbsp;
### Its features include:
- Intuitive user interface with comments and descriptions;
- Synchronization of MISP IoCs with one or more SIEMs and platforms simultaneously with the possibility of configuring IoC and TTL types globally or independently;
- Selection of the types of IoCs that will be synchronized; ¹
- Lifetime management (validity) of each type of IoC; ¹
- Removal of old volatile IoCs such as IPs, Domains, URLs, URIs, etc, avoiding false positive alerts; ¹
- Accumulation of filename IoCs and hashs such as md5, sha256, sha512, imphash, etc, increasing the detection intelligence of platforms that work with hashs as an antivirus; ¹
- Using the *thumbs up*, *thumbs down* and *last seen* features of MISP to re-include or remove IoC from SIEMs and platforms;
- Broker failure alert via Telegram;
- Possibility of adding IoC and removing false positives manually in SIEMs and platforms quickly.
  - To include:
    - Create an event in MISP;
    - Add attributes with the *to_ids* flag checked; and
    - Publish the event.
  - To remove:
    - Create an event in MISP;
    - Add attributes with the *to_ids* flag unchecked;
    - Mark *thumbs down* on all attributes;
    - Or add a comment/tag defined in the settings as Exception; and
    - Publish the event.
\
&nbsp;

¹ See the **type_list.txt** file for more details.


&nbsp;

------------
&nbsp;
### USED TECHNOLOGIES
* ShellScript -> As User Management Interface
* Python 3 -> MISP Broker Core
* SQLite -> Single database for each configuration
\
&nbsp;

------------
&nbsp;
### REQUIREMENTS FOR MISP BROKER
* MISP API token with *read only* and *Sighting Creator* permissions;
* Debian 9/Ubuntu 20.04 or higher;
* python3.5 or higher;
* Internet connection to install dependent packages;
* System dependent packages: curl python3 python3-venv unzip tar; and
* Table **cron** started on MISP Broker running user.
\
&nbsp;
------------
&nbsp;
### REQUIREMENTS FOR SIEM / CSV
* SIEM
  * SIEM API token with permission to manipulate KV Store (Splunk) or Reference Sets (QRadar).
* CSV
  * Create the destination directory before running MISP Broker; and
  * Set read and write permissions of the MISP Broker execution user in the destination directory defined in the configuration file.
\
&nbsp;
------------
&nbsp;
### INSTALLATION
&nbsp;
#### ATTENTION
Do not use directories with spaces, this can interfere with the correct functioning of the tool.
 
Wrong path example:
```shell
/opt/new folder/MISP-Broker
```
Right path example:
```shell
/opt/new-folder/MISP-Broker
or
/opt/new_folder/MISP-Broker
```
&nbsp;

#### ALL VALUES USED IN THIS DOCUMENTATION ARE EXAMPLE.

&nbsp;
#### 1. Install dependencies:
```shell
sudo apt update
sudo apt install curl python3 python3-venv unzip tar
```
&nbsp;
#### 2. Run the command below as a regular user to start cron:
```shell
crontab -e
```
- Choose the editor.
- Insert a blank line at the end of the file.
- Save and close.
\
&nbsp;
#### 3. Unzip and rename the folder from MISP-Broker-vX or MISP-Broker-main to MISP-Broker:
Command for MISP-Broker-X.X tar.gz or zip:
```shell
BROKER_VERSION=$(ls -l MISP-Broker*.* | grep -E '(.tar.gz|.zip)' 2> /dev/null | awk '{print $NF}' | grep -Eo "[0-9\.]+" | sed 's/.$//g' | grep -Eo "[0-9\.]+" | sort -u | tail -n 1)
EXTENSION=$(ls -l MISP-Broker-$BROKER_VERSION.* | grep -Eo '(.tar.gz|.zip)')

tar -xzvf MISP-Broker-${BROKER_VERSION}${EXTENSION}
OR
unzip MISP-Broker-${VERSION}${EXTENSION}

mv MISP-Broker-${BROKER_VERSION} MISP-Broker
cd MISP-Broker
```
Command for MISP-Broker-main:
```shell
unzip MISP-Broker-main.zip
mv MISP-Broker-main MISP-Broker
cd MISP-Broker
```
\
&nbsp;
File structure:
```
.
├── a1_splunk_misp_v1.1.4.tar.gz
├── configs
│   └── default.cfg
├── files
│   ├── databases
│   ├── python
│   │   ├── agent.py
│   │   ├── constants.py
│   │   ├── csv.py
│   │   ├── error_register.py
│   │   ├── global_functions.py
│   │   ├── qradar.py
│   │   ├── reflect_db_to_siem.py
│   │   ├── reflect_siem_to_db.py
│   │   ├── splunk.py
│   │   ├── sqlite_functions.py
│   │   └── update_lived_days.py
│   └── setup
│       ├── install_requirement_in_venv.sh
│       ├── requirements.txt
│       ├── venv-pip-whl-bullseye
│       │   ├── certifi-2022.5.18.1-py3-none-any.whl
│       │   ├── charset_normalizer-2.0.12-py3-none-any.whl
│       │   ├── idna-3.3-py3-none-any.whl
│       │   ├── numpy-1.22.4-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
│       │   ├── pandas-1.4.2-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
│       │   ├── PyMySQL-1.0.2-py3-none-any.whl
│       │   ├── python_dateutil-2.8.2-py2.py3-none-any.whl
│       │   ├── pytz-2022.1-py2.py3-none-any.whl
│       │   ├── requests-2.27.1-py2.py3-none-any.whl
│       │   ├── six-1.16.0-py2.py3-none-any.whl
│       │   └── urllib3-1.26.9-py2.py3-none-any.whl
│       ├── venv-pip-whl-buster
│       │   ├── certifi-2022.5.18.1-py3-none-any.whl
│       │   ├── charset_normalizer-2.0.12-py3-none-any.whl
│       │   ├── idna-3.3-py3-none-any.whl
│       │   ├── numpy-1.21.6.zip
│       │   ├── pandas-1.3.5.tar.gz
│       │   ├── PyMySQL-1.0.2-py3-none-any.whl
│       │   ├── python_dateutil-2.8.2-py2.py3-none-any.whl
│       │   ├── pytz-2022.1-py2.py3-none-any.whl
│       │   ├── requests-2.27.1-py2.py3-none-any.whl
│       │   ├── six-1.16.0-py2.py3-none-any.whl
│       │   └── urllib3-1.26.9-py2.py3-none-any.whl
│       ├── venv-pip-whl-focal
│       │   ├── certifi-2022.5.18.1-py3-none-any.whl
│       │   ├── charset_normalizer-2.0.12-py3-none-any.whl
│       │   ├── idna-3.3-py3-none-any.whl
│       │   ├── numpy-1.22.4-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
│       │   ├── pandas-1.4.2-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
│       │   ├── PyMySQL-1.0.2-py3-none-any.whl
│       │   ├── python_dateutil-2.8.2-py2.py3-none-any.whl
│       │   ├── pytz-2022.1-py2.py3-none-any.whl
│       │   ├── requests-2.27.1-py2.py3-none-any.whl
│       │   ├── six-1.16.0-py2.py3-none-any.whl
│       │   └── urllib3-1.26.9-py2.py3-none-any.whl
│       ├── venv-pip-whl-jammy
│       │   ├── certifi-2022.5.18.1-py3-none-any.whl
│       │   ├── charset_normalizer-2.0.12-py3-none-any.whl
│       │   ├── idna-3.3-py3-none-any.whl
│       │   ├── numpy-1.22.4-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
│       │   ├── pandas-1.4.2-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
│       │   ├── PyMySQL-1.0.2-py3-none-any.whl
│       │   ├── python_dateutil-2.8.2-py2.py3-none-any.whl
│       │   ├── pytz-2022.1-py2.py3-none-any.whl
│       │   ├── requests-2.27.1-py2.py3-none-any.whl
│       │   ├── six-1.16.0-py2.py3-none-any.whl
│       │   └── urllib3-1.26.9-py2.py3-none-any.whl
│       └── venv-pip-whl-stretch
│           ├── certifi-2022.5.18-py3-none-any.whl
│           ├── chardet-4.0.0-py2.py3-none-any.whl
│           ├── idna-2.10-py2.py3-none-any.whl
│           ├── numpy-1.18.5-cp35-cp35m-manylinux1_x86_64.whl
│           ├── pandas-0.25.3-cp35-cp35m-manylinux1_x86_64.whl
│           ├── PyMySQL-1.0.0-py3-none-any.whl
│           ├── python_dateutil-2.8.2-py2.py3-none-any.whl
│           ├── pytz-2022.1-py2.py3-none-any.whl
│           ├── requests-2.25.1-py2.py3-none-any.whl
│           ├── six-1.16.0-py2.py3-none-any.whl
│           └── urllib3-1.26.9-py2.py3-none-any.whl
├── logs
├── MISP_Broker.py
├── misp-broker-updater.sh
├── README.md
├── README.pt-BR.md
├── runnings
├── service.sh
├── settings.cfg
├── type_list.txt
└── v5.1

12 directories, 78 files
```
&nbsp;
#### 4. Create one or more configuration files:
Access configurations directory:
```shell
cd configs
```
  
Copy the template file (default.cfg) to, example, lhebes:
  
```shell
cp -v default.cfg lhebes.cfg
```
&nbsp;
#### 5. Edit, fill in cfg file settings parameters, save and close, example:
  
```shell
nano lhebes.cfg
```
Example for SIEM:
```shell  
[SIEM_SETTINGS]
SIEM = SPLUNK  # QRADAR or SPLUNK or CSV
SIEM_PROTOCOL = https  # http or https (ignore if use CSV)
SIEM_ADDRESS = 192.168.153.41  # URL or IP or Full PATH if use CSV
SIEM_PORT = 8089  # Example 443, 8089, etc (ignore if use CSV)
SIEM_API_TOKEN = XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX  # API token with permissions to manager KVs (Splunk) or Reference Sets (QRadar) (ignore if use CSV)
SIEM_API_VERSION = 13.1  # 13.1 or above. Only if use the QRadar (ignore if use CSV)
SIEM_APP_VERSION = 1.1.4  # Always above the previous version installed in the Splunk. Only if use the Splunk (ignore if use CSV)
BATCH_LIST_SIZE =   # Max recommended: 1000 to Splunk and 10000 to QRadar (leave blank to use these default values) (ignore if use CSV)


[MISP_SETTINGS]
MISP_ADDRESS = 192.168.153.11  # URL or IP
MISP_PROTOCOL = https  # http or https
MISP_API_TOKEN = XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  # API token with USER role
```
Example for CSV:
```shell  
[SIEM_SETTINGS]
SIEM = CSV  # QRADAR or SPLUNK or CSV
SIEM_PROTOCOL = https  # http or https (ignore if use CSV)
SIEM_ADDRESS = /home/user/MISP/CSVs  # URL or IP or Full PATH if use CSV
SIEM_PORT =   # Example 443, 8089, etc (ignore if use CSV)
SIEM_API_TOKEN =   # API token with permissions to manager KVs (Splunk) or Reference Sets (QRadar) (ignore if use CSV)
SIEM_API_VERSION = 13.1  # 13.1 or above. Only if use the QRadar (ignore if use CSV)
SIEM_APP_VERSION = 1.1.4  # Always above the previous version installed in the Splunk. Only if use the Splunk (ignore if use CSV)
BATCH_LIST_SIZE =   # Max recommended: 1000 to Splunk and 10000 to QRadar (leave blank to use these default values) (ignore if use CSV)


[MISP_SETTINGS]
MISP_ADDRESS = 192.168.153.11  # URL or IP
MISP_PROTOCOL = https  # http or https
MISP_API_TOKEN = XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  # API token with USER role
```
If using CSV, you need to run these commands to prepare the directory specified in SIEM_ADDRESS:
```shell  
mkdir -p /home/user/MISP/CSVs
chown user. -R /home/user/MISP/CSVs
```

&nbsp;
#### 6. Return to the previous directory:
  
```shell
cd ..
```
&nbsp;
#### 7. Set permissions on scripts:
```shell
chmod u+x service.sh
chmod u+x misp-broker-updater.sh
```
&nbsp;
#### 8. Configure proxy (if necessary) and Telegram in settings.cfg file, example:
```shell
nano settings.cfg
```
Edit the fields:
```shell
[SYSTEM_SETTINGS]
PROXY = 10.10.1.254:3128 # Proxy if it is necessary to use telegram and install virtual environment packages
TELEGRAM_BOT_TOKEN = 000000000:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX # Telegram bot token to send alerts
TELEGRAM_CHAT_ID = -1009999999999 # Telegram chat id that will receive the alerts
```
&nbsp;
#### 9. Install the virtual environment:
```shell
./service.sh install_venv
```
\
&nbsp;
#### 10. Run MISP Broker as a regular user using the following command, passing a cfg file as a parameter, example lhebes:
```shell
./service.sh start lhebes
```
\
**<span style="color: red;">If the SIEM is QRADAR or is using CSV, skip to the next step (11), if the SIEM is Splunk continue with the following procedures.</span>**
\
\
 MISP Broker will start, create the KVs in Splunk and an App in the format **a1_splunk_misp_1.1.4.tar.gz** in the directory and then finish generating a log with the App installation procedure in Splunk.
\
\
Run the command below to analyze the logs, for example lhebes:
```shell
./service.sh logs lhebes
```
Wait for the Broker to finish creating the KVs in Splunk, you will see the last two lines like this:
  
```
 __  __  _____   _____  _____    ____               _
|  \/  ||_   _| / ____||  __ \  |  _ \             | |
| \  / |  | |  | (___  | |__) | | |_) | _ __  ___  | | __ ___  _ __
| |\/| |  | |   \___ \ |  ___/  |  _ < | '__|/ _ \ | |/ // _ \| '__|
| |  | | _| |_  ____) || |      | |_) || |  | (_) ||   <|  __/| |
|_|  |_||_____||_____/ |_|      |____/ |_|   \___/ |_|\_\___| |_|
Security Operations Center - Tempest Security Intelligence
version: v5.1



CONFIG FILE: lhebes.cfg


timestamp="2022-05-13 17:42:31,045" severity="WARNING" func="create_store_in_siem" mode="AGENT" details="App created, please, now go to the SPLUNK and install the app." value="a1_splunk_misp_v1.1.4.tar.gz"
timestamp="2022-05-13 17:42:31,056" severity="INFO" func="execution_stop_register" details="Process finished" value="(True, [(1, 'AGENT', '2022-05-13 17:42:00', '2022-05-13 17:42:31', '0:00:31.049755', 'App created, please, now go to the SPLUNK and install the app a1_splunk_misp_v1.1.4.tar.gz ')])"
```
\
**Note**: if no changes are made to the **type_list.txt** file, the App already compiled included in the package can be used.

\
Install the App **app a1_splunk_misp_1.1.4.tar.gz** in Splunk.
\
Having the **sure** that the App was installed on Splunk, run MISP Broker again with the command below:
  
```shell
./service.sh start lhebes
```
&nbsp;
#### 11. Check if the MISP Broker is running with the command, example lhebes:
```shell
./service.sh status
```

The output should look like this:
    
```
 __  __  _____   _____  _____    ____               _
|  \/  ||_   _| / ____||  __ \  |  _ \             | |
| \  / |  | |  | (___  | |__) | | |_) | _ __  ___  | | __ ___  _ __
| |\/| |  | |   \___ \ |  ___/  |  _ < | '__|/ _ \ | |/ // _ \| '__|
| |  | | _| |_  ____) || |      | |_) || |  | (_) ||   <|  __/| |
|_|  |_||_____||_____/ |_|      |____/ |_|   \___/ |_|\_\___| |_|
Security Operations Center - Tempest Security Intelligence
version: v5.1



CONFIG FILE: All cfg files

Total enabled in cron: 1

Total running:
1682727 ?        -    0:23 /home/user/MISP-Broker/files/setup/venv/bin/python3 MISP_Broker.py lhebes
```
&nbsp;
#### 12. Check if the MISP Broker was added to the cron with the command, example lhebes:
```shell
crontab -l | grep MISP-Broker | grep lhebes
```

The output should contain two lines similar to these:
    
```shell
@reboot cd /home/user/MISP-Broker; /home/user/MISP-Broker/files/setup/venv/bin/python3 MISP_Broker.py lhebes &> /dev/null &
  
*/10 * * * * cd /home/user/MISP-Broker; bash service.sh check lhebes
```
&nbsp;
#### 13. Follow the logs to verify that everything is ok:
```shell
./service.sh logs
```
or
```shell
./service.sh logs lhebes
```

------------
&nbsp;
### MANAGEMENT
&nbsp;
To view all options navigate to the MISP Broker directory and run:
```shell
./service.sh help
```
The output will be this:
```
 __  __  _____   _____  _____    ____               _
|  \/  ||_   _| / ____||  __ \  |  _ \             | |
| \  / |  | |  | (___  | |__) | | |_) | _ __  ___  | | __ ___  _ __
| |\/| |  | |   \___ \ |  ___/  |  _ < | '__|/ _ \ | |/ // _ \| '__|
| |  | | _| |_  ____) || |      | |_) || |  | (_) ||   <|  __/| |
|_|  |_||_____||_____/ |_|      |____/ |_|   \___/ |_|\_\___| |_|
Security Operations Center - Tempest Security Intelligence
version: v5.1



Choose:
        status               ->         Show status of all Broker config files processes
        logs                 ->         Show logs of all Broker config file running process or justo one
        start                ->         Start one Broker config file running process
        stop                 ->         Stop one Broker config file running process
        restart              ->         Restart one Broker config file service
        startall             ->         Start all Broker config files listed in cron
        stopall              ->         Stop all Broker config files with running process
        restartall           ->         Restart all Broker config files listed in cron
        kill                 ->         Force kill all Broker config files running process or just one config file running process
        enable               ->         Add Broker config file service from cron
        disable              ->         Remove Broker config file service from cron
        check                ->         Verify if Broker config file service is running with activity
        backup_make          ->         Make a backup of important Broker files
        backup_restore       ->         Restore existing backups of important Broker files
        install_venv         ->         Install python 3 virtual environment for Broker
        reinstall_venv       ->         Reinstall python 3 virtual environment for Broker
        lookthis             ->         Wait! What is it?! O_o
        help                 ->         Show this help message

Example:
        ./service.sh status

Some options need to give a cfg file, example:
        ./service.sh start alpha

And others is optional, example:
        ./service.sh logs               ->      Will show all cfg logs in real time
        ./service.sh logs alpha         ->      Will show only alpha.cfg log in real time

```
\
**Note**: It is not necessary to stop or restart services whenever you change **settings.cfg** files and files inside **configs/*.cfg**. At each loop these settings are reloaded.
\
&nbsp;

------------
&nbsp;
### UPDATE
&nbsp;  
Download the new version and place it in the same directory level as **MISP-Broker**.

\
Put the **misp-broker-updater.sh** next to the new version file:
```shell
cp MISP-Broker/misp-broker-updater.sh .
```
\
The files and directories should look like this:
```shell
user@ubuntu:~$ls -lh
total 34M
drwxrwxr-x 11 user user 4.0K May 19 00:01 BackUp_MISP-Broker
drwxrwxr-x  6 user user 4.0K May 19 19:07 MISP-Broker
-rwxrw-r--  1 user user   47 May 19 18:52 misp-broker-updater.sh
-rw-rw-r--  1 user user  17M May 13 18:44 MISP-Broker-7.6.tar.gz
```

\
To start the update use the commands:
```shell
chmod u+x misp-broker-updater.sh
./misp-broker-updater.sh
```
\
Note¹: no matter if other .tar.gz or .zip files from earlier versions are in the directory, **misp-broker-updater.sh** will use the latest one.
\
\
Note²: safely stopping processes is usually quite time consuming.
\
\
**<span style="color: red;">ATTENTION: the update replaces the settings.cfg file, if you have made any changes to this file it will display the diff to compare the new version's file with the previous version's file that was saved in the backup, make the adjustments in the settings.cfg of the new version IF NECESSARY.</span>**
\
\
To review the differences use the command below:
```shell
diff BackUp_MISP-Broker/$(ls BackUp_MISP-Broker | tail -n 1)/settings.cfg MISP-Broker/settings.cfg
```
\
Reinstall the virtual environment:
```shell
cd MISP-Broker
./service.sh install_venv
```
\
Start the processes again with the command (only these that are enabled in cron):
```shell
./service.sh startall
```
\
Check the logs to see if everything is ok:
```shell
./service.sh logs
```
\
**Tip**: it is possible to display the logs of only one cfg file passing its name as a parameter, for example:
```shell
 ./service.sh logs lhebes
 ```
&nbsp;

------------
&nbsp;
### CLEAR SIEM/CSV DATA TO START FROM ZERO
&nbsp;  
Go to the **MISP-Broker** directory and stop the service of the cfg file that you want to clean the data in SIEM or CSV, example:
```shell
 ./service.sh stop lhebes
 ```
&nbsp;  
Remove the database of the cfg file in question, example:
```shell
 rm -v files/database/lhebes.db
 ```
&nbsp;  
Perform the procedures in **INSTALLATION** from step **10**.
&nbsp;  
&nbsp;  
\
**Tip**: if you wanna keep SIEM/CSV clean look the logs and stop the **MISP-Broker** of the cfg file when it finalize the *create_store_in_siem* funcion and start the *mark_as_false_positive* function, for example:
```
timestamp="2022-05-13 18:09:41,005" severity="INFO" func="create_store_in_siem" mode="AGENT" type="vulnerability" details="Creating storage name in QRADAR" value="tsi_misp_vulnerability"
timestamp="2022-05-13 18:09:43,517" severity="INFO" func="create_store_in_siem" mode="AGENT" type="vulnerability" details="Created reference set in QRADAR" value="tsi_misp_vulnerability - 409 - {"http_response":{"code":409,"message":"The request could not be completed due to a conflict with the current state of the resource"},"code":1004,"description":"The reference set could not be created, the name provided is already in use. Please change the name and try again.","details":{},"message":"The name tsi_misp_vulnerability is already in use"}"
timestamp="2022-05-13 18:09:43,554" severity="INFO" func="mark_as_false_positive" mode="AGENT" details="Checking ip-src IOCs status" value="1/24"
timestamp="2022-05-13 18:09:43,858" severity="INFO" func="mark_as_false_positive" mode="AGENT" details="Checking ip-dst IOCs status" value="2/24"
```
&nbsp;  
&nbsp;  
