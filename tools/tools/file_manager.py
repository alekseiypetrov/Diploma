import os
import json
import datetime
import pytz

moscow_tz = pytz.timezone("Europe/Moscow")


def get_status(file_path):
    if not os.path.exists(file_path):
        save_status(file_path, is_first=True)
    with open(file_path, encoding='utf-8') as json_file:
        status = json.load(json_file)
    return status


def save_status(file_path, status='', is_first=False):
    if is_first:
        status = {
            'message': 'Ожидание первого выполнения',
            'last_update': datetime.datetime.now(tz=moscow_tz).strftime(format="%Y-%m-%d %H:%M:%S")
        }
    with open(file_path, mode='w', encoding='utf-8') as json_file:
        json.dump(status, json_file, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    print(BASE_DIR)
    print(os.path.split(os.path.split(BASE_DIR)[0]))
