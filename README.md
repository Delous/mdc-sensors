# Настройка OrangePi под этот код 
Скачать по ссылке образ (нужен именно server): [Orangepizero3_1.0.0_debian_bullseye_server_linux5.4.125.7z](https://drive.google.com/drive/folders/1cZajR3hlankwvoM--EwY_jdbsfLipPAm)

Установить образ на microSD с помощью Rufus (если установка происходит на Windows). В процессе установки никаких настроек, предложенных от Rufus, не менять.

Вставить microSD в Orange PI, подключить по LAN кабелю. Дождаться зеленого светодиода, после найти IP адрес устройства, заглянув в настройках роутера в раздел [Cтатистика - DHCP](https://192.168.1.1)

Как только был получен IP, надо подключиться по SSH, введя следующие данные:
`ssh orangepi@IP`
`password: orangepi`

или
`ssh root@IP`
`password: orangepi`

ssh orangepi@192.168.1.158

***

В системе уже должен быть python, вызывается командой `python3`
Для установки docker, следуй этой [инструкции](https://docs.docker.com/engine/install/debian/).

***

После установки, напиши команду `sudo systemctl enable docker`.

***

Добавить `docker-compose.yml` и переменную `.env` в каталог пользователя `/home/orangepi`.

В `.env` переменной надо указать host сайта по умолчанию и id, который будет передаваться на сервер для настроек.

***

Для автообновления кода через docker-compose.yml нужно настроить скрипт:
```
sudo nano /usr/local/bin/update-orangepi-app.sh
```

```
#!/bin/bash

COMPOSE_FILE="/home/orangepi/docker-compose.yml"

echo "========================================"
echo "Docker update started: $(date)"
echo "========================================"

echo "Trying to pull new images..."

if /usr/bin/timeout 120 /usr/bin/docker compose \
    -f "$COMPOSE_FILE" \
    pull
then
    echo "Images pulled successfully."
else
    echo "WARNING: Could not pull images."
    echo "Registry, Internet or DNS may be unavailable."
    echo "Starting application using local images."
fi

echo "Starting/updating containers..."

if /usr/bin/docker compose \
    -f "$COMPOSE_FILE" \
    up -d --pull never
then
    echo "Application started successfully."
else
    echo "ERROR: Application failed to start."
    exit 1
fi

echo "Docker update finished: $(date)"
```

```
sudo chmod +x /usr/local/bin/update-orangepi-app.sh
```

Создать systemd сервис:
```
sudo nano /etc/systemd/system/orangepi-app-update.service
```

```
[Unit]
Description=Update and start Orange Pi Docker application
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/update-orangepi-app.sh
```

И таймер:
```
sudo nano /etc/systemd/system/orangepi-app-update.timer
```

```
[Unit]
Description=Check Docker images every hour

[Timer]
OnBootSec=30s
OnUnitActiveSec=1h

[Install]
WantedBy=timers.target
```

После чего всё нужно активировать:
```
sudo systemctl daemon-reload
```

```
sudo systemctl enable --now orangepi-app-update.timer
```

И проверить, что работает:
```
systemctl status orangepi-app-update.timer
```

***

Чтобы подключиться к wi-fi на заводе, напиши `nmcli device wifi connect "Имя_сети" password "пароль"`

***

Опционально, но возможно пригодится:
[[Настройка программы для смены DNS]]
