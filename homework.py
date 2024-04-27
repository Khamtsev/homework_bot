from http import HTTPStatus
import logging
import os
import requests
import sys

from dotenv import load_dotenv
import telegram
import time

from exceptions import HomeworkKeyError, TokenError, WrongStatus


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter('%(asctime)s, %(levelname)s, %(message)s')
handler.setFormatter(formatter)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка наличия необходимых токенок."""
    TOKENS = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    for token in TOKENS.keys():
        if not TOKENS[token]:
            message = f'Отсутствует токен {token}'
            logging.critical(message)
            raise TokenError(message)


def send_message(bot, message):
    """Отправка сообщения в телеграм."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.TelegramError as error:
        logging.error(f'Не удалось отправить сообщение: {error}')
    else:
        logging.debug('Сообщение успешно отправлено')


def get_api_answer(timestamp):
    """Получение ответа от эндпоинта."""
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
        if response.status_code == HTTPStatus.OK:
            return response.json()
        else:
            message = f'Эндпоинт недоступен: {response.status_code}'
            logging.error(message)
            raise RuntimeError(message)
    except requests.RequestException as error:
        logging.error(f'Не удалось получить ответ: {error}')
        raise RuntimeError(error)


def check_response(response):
    """Проверка корректности ответа."""
    if not isinstance(response, dict):
        message = 'Неверный формат response'
        logging.error(message)
        raise TypeError(message)
    if 'homeworks' not in response:
        message = 'Отсуствует ключ homeworks'
        logging.error(message)
        raise HomeworkKeyError(message)
    if not isinstance(response.get('homeworks'), list):
        message = 'Неверный формат данных homeworks'
        logging.error(message)
        raise TypeError(message)
    logging.debug('Полученный ответ корректен')
    return response.get('homeworks')


def parse_status(homework):
    """Проверка статуса домашней работы."""
    if 'homework_name' not in homework:
        raise HomeworkKeyError('Отсуствует ключ homework_name')
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if status not in HOMEWORK_VERDICTS:
        raise WrongStatus('Непредусмотренный статус домашней работы')
    verdict = HOMEWORK_VERDICTS.get(status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    send_message(bot, 'Начало работы')
    timestamp = int(time.time())
    last_status = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            timestamp = int(time.time())
            homeworks = check_response(response)
            if homeworks:
                new_status = parse_status(homeworks[0])
                if new_status != last_status:
                    send_message(bot, new_status)
                    last_status = new_status
                else:
                    logging.debug('Обновлений статуса не было')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
