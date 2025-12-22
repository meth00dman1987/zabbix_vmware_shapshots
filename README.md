# zabbix_vmware_shapshots
Мониторинг снапшотов VMWare

Установка.

sudo apt-get update

sudo apt-get install -y python3 python3-pip

sudo pip3 install pyvmomi

sudo cp vmware_old_snapshot.py /usr/lib/zabbix/externalscripts/vmware_old_snapshot.py

sudo chmod +x /usr/lib/zabbix/externalscripts/vmware_old_snapshots.py

sudo chown zabbix:zabbix /usr/lib/zabbix/externalscripts/vmware_old_snapshots.py


Макросы.

{$SNAP_AGE_HOURS} - возраст снапшота в часах

{$SNAP_VM_EXCLUDE_REGEX} - регулярка для исключения снапшотов на которые не надо реагировать

{$VCENTER_HOST} - адрес vcentr

{$VCENTER_USER} - логин (достаточно ro пользователя)

{$VCENTER_PASS} - пароль


Обратите внимание!
Если вы получаете оповещения через Telegram и снапшотов много, может возникнуть ошибка отправки из-за ограничения тела сообщения самим Telegram.
