### О проекте
Телеграм бот, отслеживающий изменение статуса проверки домашней работы в Яндекс-практикуме.
Автор: Денис Хамцев, [GitHub](https://github.com/Khamtsev).
Реализовано с помощью Python Telegram Bot 13.7.

### Как запустить проект
Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/Khamtsev/homework_bot
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Получите токен Яндекс-практикума

```
https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a
```

Создайте и заполните .env файл по образцу .env.example

Активируйте бота, запустите:

```
howework.py
```

Если запуск прошел успешно - в телеграм придет сообщение "Начало работы".
Бот будет оповещать об изменении статуса проверки работа.
