import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import WrongStatus

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


def check_tokens() -> None:
    """Проверка наличия необходимых токенок."""
    TOKENS = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    missing_tokens = []
    for token in TOKENS:
        if not TOKENS[token]:
            logging.critical(f'Отсутствует токен {token}')
            missing_tokens.append(token)
    if missing_tokens != []:
        missing_tokens = ', '.join(missing_tokens)
        logging.critical(f'Отсутствуют токены {missing_tokens}')
        sys.exit()


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправка сообщения в телеграм."""
    logging.debug('Попытка отправить сообщение')
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.TelegramError as error:
        logging.error(f'Не удалось отправить сообщение: {error}')
    else:
        logging.debug('Сообщение успешно отправлено')


def get_api_answer(timestamp: int) -> dict:
    """Получение ответа от эндпоинта."""
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
        if response.status_code != HTTPStatus.OK:
            raise ConnectionError(
                f'Эндпоинт недоступен: {response.status_code}'
            )
        else:
            return response.json()
    except requests.RequestException as error:
        raise ConnectionError(f'Не удалось получить ответ: {error}')


def check_response(response: dict) -> list[dict]:
    """Проверка корректности ответа."""
    if not isinstance(response, dict):
        raise TypeError('Неверный формат response')
    if 'homeworks' not in response:
        raise KeyError('Отсуствует ключ homeworks')
    if not isinstance(response.get('homeworks'), list):
        raise TypeError('Неверный формат данных homeworks')
    logging.debug('Полученный ответ корректен')
    return response.get('homeworks')


def parse_status(homework: dict) -> str:
    """Проверка статуса домашней работы."""
    if 'homework_name' not in homework:
        raise KeyError('Отсуствует ключ homework_name')
    homework_name = homework['homework_name']
    if 'status' not in homework:
        raise KeyError('Отсуствует ключ status')
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise WrongStatus('Непредусмотренный статус домашней работы')
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main() -> None:
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
        except ConnectionError as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)
        except TypeError as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)
        except KeyError as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)
        except WrongStatus as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
