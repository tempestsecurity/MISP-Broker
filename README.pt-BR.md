
# MISP Broker  
&nbsp;

O **MISP Broker** é uma ferramenta desenvolvida pelo time de plataforma do Security Operations Center (SOC) da [**Tempest Security Intelligence**](https://www.tempest.com.br/). Seu propósito é realizar uma integração gerenciável e com confiabilidade dos Indicadores de Comprometimento (IoC) do MISP em Splunk, QRadar e outras plataformas que possam utilizar arquivos de tabelas do tipo CSV como *block list*.
\
\
As ações realizadas no MISP refletem nos SIEMs e plataformas de forma rápida, a depender do hardware e condições de rede. Um ambiente onde existem SIEM, firewall, antivírus, EDR, SOAR e outras plataformas que possam utilizar CSVs terão os dados sempre atualizados de modo uniforme, consistente e sem a necessidade de ficar atualizando as plataformas manualmente, o MISP Broker faz tudo de forma automática.
\
\
Um simples clicar no *polegar para cima* em um atributo no MISP (via interface web) e em questão de segundos ele será incluído nos SIEMs e plataformas com o tempo de vida (TTL) renovado (significa que seus dias vividos foram zerados) e um clicar no *polegar para baixo* fará com que seja removido.
\
\
Utilizando o MISP Broker haverá melhorias significativas de performance na execução de casos de uso em SIEMs e plataformas pois os dados brutos ficam na própria aplicação, evitando solicitações excessivas de dados (hashs, IPs, domínios, etc) ao MISP a cada execução/teste/validação, também evitando a possibilidade da não detecção de uma possível ameaça por falha de comunicação com o MISP durante a ação da aplicação. 
\
\
Em caso de falta de comunicação com o SIEM ou diretório de CSVs inacessível o MISP Broker continua trabalhando, coletando informações do MISP, armazenando em seu banco de dados e no momento oportuno em que a comunicação ou diretório estiverem disponíveis as sincronizações com SIEMs e/ou plataformas serão realizadas de forma intervalada para que a grande quantidade de informações acumuladas na fila não onerem os SIEMs e plataformas.
\
\
O MISP Broker também envia alertas pelo Telegram caso esteja tendo problemas de execução, assim é possível ter a certeza de que tudo está executando perfeitamente.
\
&nbsp;
### Seus recursos incluem:
- Interface de utilização intuitiva com comentários e descrições;
- Sincronização de IoCs do MISP com um ou mais SIEMs e plataformas simultaneamente com a possibilidade de configuração dos tipos de IoC e TTL de forma global ou independente;
- Seleção dos tipos de IoCs que serão sincronizados; ¹
- Gerenciamento de tempo de vida (validade) de cada tipo de IoC; ¹
- Remoção de IoCs voláteis antigos como IPs, Domínios, URLs, URIs, etc, evitando criação alertas falsos positivos; ¹
- Acúmulo de IoCs do tipo filename e hashs como md5, sha256, sha512, imphash, etc, aumentando cada vez mais a inteligência de detecção de plataformas que trabalham com hashs como antivírus; ¹
- Utilização do recursos de *polegar para cima*, *polegar para baixo* e *last seen* do MISP para reincluir ou remover IoC dos SIEMs e plataformas;
- Alertar de falha no Broker via Telegram; 
- Possibilidade de inclusão de IoC e remoção falsos positivos manualmente nos SIEMs e plataformas de forma rápida.
  - Para incluir:
    - Criar um evento no MISP;
    - Adicionar os atributos com a flag *to_ids* marcada; e
    - Publicar o evento.
  - Para remover:
    - Criar um evento no MISP;
    - Adicionar os atributos com a flag *to_ids* desmarcada;
    - Marcar *polegar para baixo* em todos os atributos;
    - Ou adicionar um comentário/tag definidos nas configurações como Exceção; e
    - Publicar o evento.
\
&nbsp;

¹ Consultar o arquivo **type_list.txt** para mais detalhes.


&nbsp;

------------  
&nbsp;
### TECNOLOGIAS UTILIZADAS
* ShellScript -> Como interface de gerenciamento do usuário
* Python 3 -> Núcleo do MISP Broker
* SQLite -> Banco de dados único para cada configuração
\
&nbsp;

------------  
&nbsp;
### REQUISITOS PARA O MISP BROKER
* Debian 9/Ubuntu 20.04 ou superior;
* python3.5 ou superior;
* Conexão com a internet para para instalação dos pacotes dependentes;
* Pacotes dependentes no sistema: curl python3 python3-venv unzip tar;
* Token de API do MISP com permissão *read only*; e
* Tabela **cron** iniciada no usuário de execução do MISP Broker.
\
&nbsp;
------------  
&nbsp;
### REQUISITOS PARA O SIEM / CSV
* SIEM
  * Token de API do SIEM com permissão de manipulação de KV Store (Splunk) ou Reference Sets (QRadar).
* CSV
  * Criar o diretório destino antes de executar o MISP Broker; e
  * Definir permissões de leitura e escrita do usuário de execução do MISP Broker no diretório destino definido no arquivo de configuração.
\
&nbsp;
------------  
&nbsp;
### INSTALAÇÃO  
&nbsp;
#### ATENÇÃO
Não use diretórios com espaços, isso pode interferir no correto funcionamento da ferramenta.


Exemplo de diretório errado:
```shell
/opt/new folder/MISP-Broker
```
Exemplo de diretório certo:
```shell
/opt/new-folder/MISP-Broker
ou
/opt/new_folder/MISP-Broker
```
&nbsp;
#### 1. Instalar dependências:  
```shell  
sudo apt update
sudo apt install curl python3 python3-venv unzip tar
```  
&nbsp;
#### 2. Executar o comando abaixo como usuário comum para inicializar a cron:  
```shell  
crontab -e
```  
- Escolher o editor.  
- Inserir uma linha em branco no final do arquivo.  
- Salvar e fechar.
\
&nbsp;
#### 3. Descompactar e renomear a pasta de MISP-Broker-vX para MISP-Broker: 
Comando para MISP-Broker-vX: 
```shell  
BROKER_VERSION=$(ls -l MISP-Broker_v*.tar.gz 2> /dev/null | awk '{print $NF}' | grep -Eo "[0-9\.]+" | sed 's/.$//g' | grep -Eo "[0-9\.]+" | sort -u | tail -n 1)  

tar -xzvf MISP-Broker_v${BROKER_VERSION}.tar.gz 
mv MISP-Broker_v${BROKER_VERSION} MISP-Broker  
cd MISP-Broker  
```  
Comando para MISP-Broker-main:
```shell
unzip MISP-Broker-main.zip
mv MISP-Broker-main MISP-Broker
cd MISP-Broker
```
\
&nbsp;
Estrutura de arquivos:  
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
#### 4. Criar um ou mais arquivos de configuração:  
Acessar diretório de configurações:  
```shell  
cd configs
```  
  
Copiar o arquivo modelo (default.cfg) para, exemplo, lhebes:  
  
```shell  
cp -v default.cfg lhebes.cfg
```  
&nbsp;
#### 5. Editar, preencher os parâmetros de configurações do arquivo cfg, salvar e fechar, exemplo:  
  
```shell  
nano lhebes.cfg
```  
Exemplo para SIEM:
```shell  
[SIEM_SETTINGS]
SIEM = SPLUNK  # QRADAR or SPLUNK or CSV
SIEM_PROTOCOL = https  # http or https (ignore if use CSV)
SIEM_ADDRESS = 192.168.153.41  # URL or IP or Full PATH if use CSV
SIEM_PORT = 8089  # Example 443, 8089, etc (ignore if use CSV)
SIEM_API_TOKEN = 13a2f79e-d7fe-a142-4d9c-313c41a163b7  # API token with permissions to manager KVs (Splunk) or Reference Sets (QRadar) (ignore if use CSV)
SIEM_API_VERSION = 13.1  # 13.1 or above. Only if use the QRadar (ignore if use CSV)
SIEM_APP_VERSION = 1.1.4  # Always above the previous version installed in the Splunk. Only if use the Splunk (ignore if use CSV)
BATCH_LIST_SIZE =   # Max recommended: 1000 to Splunk and 10000 to QRadar (leave blank to use these default values) (ignore if use CSV)


[MISP_SETTINGS]
MISP_ADDRESS = 192.168.153.11  # URL or IP
MISP_PROTOCOL = https  # http or https
MISP_API_TOKEN = 75fRj0e77uNUqAQmpKiLpLVw5ZXQYIwsxnJujl3w  # API token with USER role
```
Exemplo para CSV:
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
MISP_API_TOKEN = 75fRj0e77uNUqAQmpKiLpLVw5ZXQYIwsxnJujl3w  # API token with USER role
```
Se usar CSV, você precisa executar estes comandos para preparar o diretório informado em SIEM_ADDRESS:

```shell  
mkdir -p /home/user/MISP/CSVs
chown user. -R /home/user/MISP/CSVs
```

&nbsp;
#### 6. Retornar ao diretório anterior:  
  
```shell  
cd ..
```  
&nbsp;
#### 7. Definir permissões nos scripts:  
```shell  
chmod u+x service.sh
chmod u+x misp-broker-updater.sh
```  
&nbsp;
#### 8. Configurar o proxy (se necessário) e o Telegram no arquivo settings.cfg, exemplo:  
```shell  
nano settings.cfg
```  
Edite os campos:
```shell  
[SYSTEM_SETTINGS]
PROXY = 10.10.1.254:3128  # Proxy if is necessary to use telegram and install virtual environment packages  
TELEGRAM_BOT_TOKEN = 780193837:AAEqlAKfRYwwkWJG1u3OWTef28AIPWU9zdo  # Telegram bot token to send alerts  
TELEGRAM_CHAT_ID = -1001667174374  # Telegram chat id that will receive the alerts  
```
&nbsp;
#### 9. Instale o virtual environment:  
```shell  
./service.sh install_venv
```
\
&nbsp;
#### 10. Executar o MISP Broker como usuário comum utilizando o comando a seguir passando um arquivo cfg como parâmetro, exemplo lhebes:  
```shell  
./service.sh start lhebes
```
\
**<span style="color: red;">Se o SIEM for QRADAR ou está utilizando CSV, pule para o próximo passo (11), caso o SIEM seja Splunk continue com os procedimentos a seguir.</span>**
\
\
 O MISP Broker vai iniciar, criar as KVs no Splunk e um App no formato **a1_splunk_misp_v1.1.4.tar.gz** no diretório e então encerrar gerando um log com o procedimento de instalação do App no Splunk.
\
\
Execute o comando abaixo para ficar analisando os logs, exemplo lhebes:  
```shell  
./service.sh logs lhebes
```  
Espere o Broker finalizar a criação das KVs no Splunk, você verá as duas últimas linhas desta forma:  
  
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
**Observação**: se nenhuma alteração for realizada no arquivo **type_list.txt** pode-se utilizar o App já compilado incluído no pacote.  

\
Realizar a instalação do App **app a1_splunk_misp_v1.1.4.tar.gz** no Splunk.  
\
Tendo a **certeza** de que o App foi instalado no Splunk, execute o MISP Broker novamente com o comando abaixo:  
  
```shell  
./service.sh start lhebes
```  
&nbsp;
#### 11. Verifique se o MISP Broker está rodando com o comando, exemplo lhebes:
```shell
./service.sh status
```

A saída deve ser semelhante a esta:
    
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
#### 12. Verificar se o MISP Broker foi adicionado na cron com o comando, exemplo lhebes:
```shell
crontab -l | grep MISP-Broker | grep lhebes
```

A saída deve contar duas linhas similares a estas:
    
```shell
@reboot cd /home/user/MISP-Broker; /home/user/MISP-Broker/files/setup/venv/bin/python3 MISP_Broker.py lhebes &> /dev/null &
  
*/10 * * * * cd /home/user/MISP-Broker; bash service.sh check lhebes
```
&nbsp;
#### 13. Acompanhe os logs para verificar se está tudo certo:
```shell
./service.sh logs
```
ou
```shell
./service.sh logs lhebes
```

------------  
&nbsp;
### GERENCIAMENTO
&nbsp;  
Para visualizar todas as opções navegue até dentro do diretório do MISP Broker e execute:  
```shell  
./service.sh help
```
A saída será esta:
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
**Observação**: não é necessário para ou reiniciar os serviços sempre que alterar os arquivos **settings.cfg** e arquivos dentro de **configs/*.cfg**. A cada loop estas configurações são recarregadas.
\
&nbsp;

------------  
&nbsp;
### ATUALIZAÇÃO
&nbsp;  
Baixe a nova versão e coloque no mesmo diretório nível de **MISP-Broker**.

\
Coloque o **misp-broker-updater.sh** junto ao arquivo de nova versão:
```shell
cp MISP-Broker/misp-broker-updater.sh .
```
\
Os arquivos e diretórios devem estar desta forma:  
```shell  
user@ubuntu:~$ ls -lh
total 34M
drwxrwxr-x 11 user user 4,0K mai 19 00:01 BackUp_MISP-Broker
drwxrwxr-x  6 user user 4,0K mai 19 19:07 MISP-Broker
-rwxrw-r--  1 user user   47 mai 19 18:52 misp-broker-updater.sh
-rw-rw-r--  1 user user  17M mai 13 18:44 MISP-Broker_v7.6.tar.gz
```

\
Para iniciar a atualização utilize os comandos:
```shell
chmod u+x misp-broker-updater.sh
./misp-broker-updater.sh
```
\
Observação¹: não importa se outros arquivos .tar.gz de versões anteriores estejam no diretório, o **misp-broker-updater.sh** irá utilizar o mais recente.
\
\
Observação²: parar os processos de forma segura geralmente é bastante demorado.
\
\
**<span style="color: red;">ATENÇÃO: a atualização substitui o arquivo settings.cfg, caso você tenha feito alguma alteração neste arquivo ele exibirá o diff para comparar o arquivo da nova versão com o arquivo da versão anterior que foi salvo no backup, faça os ajustes no settings.cfg da nova versão SE NECESSÁRIO.</span>**\
\
\
Para rever as diferenças use o comando abaixo:
```shell
diff BackUp_MISP-Broker/$(ls BackUp_MISP-Broker | tail -n 1)/settings.cfg MISP-Broker/settings.cfg
```
\
Reinstale o virtual environment:
```shell
cd MISP-Broker
./service.sh install_venv
```
\
Inicie os processos novamente com o comando (apenas aqueles que estão habilitados na cron):
```shell
./service.sh startall
```
\
Acompanhe os logs para ver se está tudo certo:
```shell
./service.sh logs
```
\
**Dica**: é possível exibir os logs de apenas um arquivo cfg passando seu nome como parâmetro, exemplo:
```shell
 ./service.sh logs lhebes
 ```
&nbsp;  

------------  
&nbsp;
### LIMPAR DADOS DO SIEM/CSV PARA RECOMEÇAR DO ZERO
&nbsp;  
Acesse o diretório do **MISP-Broker** e pare o serviço do arquivo cfg que deseja limpar os dados no SIEM ou CSV, exemplo:
```shell
 ./service.sh stop lhebes
 ```
&nbsp;  
Remova o banco de dados do arquivo cfg em questão, exemplo:
```shell
 rm -v files/database/lhebes.db
 ```
&nbsp;  
Execute os procedimentos em **INSTALAÇÃO** a partir do passo **10**.
&nbsp;  
&nbsp;  
\
**Dica**: se você deseja manter o SIEM/CSV limpo olhe os logs e pare o **MISP-Broker** do arquivo cfg quando finalizar a função *create_store_in_siem* e iniciar a função *mark_as_false_positive*, por exemplo:
```
timestamp="2022-05-13 18:09:41,005" severity="INFO" func="create_store_in_siem" mode="AGENT" type="vulnerability" details="Creating storage name in QRADAR" value="tsi_misp_vulnerability"
timestamp="2022-05-13 18:09:43,517" severity="INFO" func="create_store_in_siem" mode="AGENT" type="vulnerability" details="Created reference set in QRADAR" value="tsi_misp_vulnerability - 409 - {"http_response":{"code":409,"message":"The request could not be completed due to a conflict with the current state of the resource"},"code":1004,"description":"The reference set could not be created, the name provided is already in use. Please change the name and try again.","details":{},"message":"The name tsi_misp_vulnerability is already in use"}"
timestamp="2022-05-13 18:09:43,554" severity="INFO" func="mark_as_false_positive" mode="AGENT" details="Checking ip-src IOCs status" value="1/24"
timestamp="2022-05-13 18:09:43,858" severity="INFO" func="mark_as_false_positive" mode="AGENT" details="Checking ip-dst IOCs status" value="2/24"
```
&nbsp;  
&nbsp;  
