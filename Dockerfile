# Используем официальный минимальный образ python 3.12
FROM python:3.13-slim-bullseye

# Создаём рабочую директорию
WORKDIR /app

# Устанавливаем библиотеки
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем файлы проекта в контейнер
COPY . .

# Запускаем скрипт
CMD ["python3", "main.py"]

# Команда для сборки: docker build -t delous/mdc-sensors .
# Команда для пуша: docker push delous/mdc-sensors
# Команда для запуска: docker run -e PYTHONUNBUFFERED=1 --device=/dev/ttyUSB0 --restart=always delous/mdc-sensors

# docker run -d \
#   --name watchtower \
#   --restart=always \
#   -v /var/run/docker.sock:/var/run/docker.sock \
#   nickfedor/watchtower:latest \
#   --interval 60 \
#   --cleanup
