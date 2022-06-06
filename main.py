import json
import os
import requests
from datetime import datetime

BASE_PATH = os.getcwd()
LOGS_DIR_NAME = 'logs'
LOGS_FILE_NAME = 'logs.txt'
TOKEN_VK_NAME = 'token.txt'


class VkUser:
    def __init__(self, token, version, count=5):
        self.params = {
            'access_token': token,
            'v': version
        }
        self.dict_photos = {}
        self.count = count
        self.file_name = ''
        self.url = 'https://api.vk.com/method/'

    # функция, которая возвращает новый словарь с фотографиями максимального разрешения, кол-во лайков и дату публикации
    def _get_photos_json(self, owner_id):
        get_photos_url = self.url + 'photos.get'
        get_photos_params = {
            'owner_id': owner_id,
            'album_id': 'profile',
            'rev': 1,
            'extended': 1,
            'photo_sizes': 1,
            'count': self.count
        }
        # получаем json в качестве результата к запросу по фотографиям из профиля
        return requests.get(get_photos_url, params={**self.params, **get_photos_params}).json()

    def get_photos(self, owner_id):
        res = self._get_photos_json(owner_id)
        if 'error' in res.keys():
            print(res['error']['error_msg'])
        elif res['response']:
            for idx, value in enumerate(res['response']['items']):
                # проебразование даты формата Unixtime в YYYYmmdd
                timestamp = (res['response']['items'][idx]['date'])
                date_of_photo = datetime.utcfromtimestamp(timestamp).strftime('%Y%m%d')

                # создаем словарь учитывая одинаковое кол-во лайков, если есть повторы, мы добавляем дату
                # загрузки фото
                key = str(res['response']['items'][idx]['likes']['count'])
                if key in self.dict_photos.keys():
                    self.dict_photos[key + date_of_photo] = {'file_name': (key + date_of_photo + '.jpg'),
                                                             'size': res['response']['items'][idx]['sizes'][-1][
                                                                 'type']}
                    self.file_name = key + date_of_photo + '.jpg'

                else:
                    self.dict_photos[key] = {'file_name': (key + '.jpg'),
                                             'size': res['response']['items'][idx]['sizes'][-1]['type']}
                    self.file_name = key + '.jpg'

                # скачиваем фото в папку
                get_path_photos = os.path.join(BASE_PATH, owner_id, self.file_name)

                api = requests.get(res['response']['items'][idx]['sizes'][-1]['url'])
                with open(get_path_photos, 'wb') as file_obj_photos:
                    file_obj_photos.write(api.content)
                    file_obj_photos.close()

        # json-файл с информацией по файлам
        with open('data.json', 'w') as file_json:
            return json.dump(list(self.dict_photos.values()), file_json)


class YaUploader:
    def __init__(self, token_ya: str):
        self.token_ya = token_ya

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.token_ya)
        }

    # создаем папку на янедкс диски по ID пользователя
    def _make_folder_yadisk(self, file_path: str):
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.get_headers()
        params = {'path': file_path, 'overwrite': 'true'}
        requests.put(url, headers=headers, params=params)

    # получаем ссылку для файлов для загрузки на диск яндекса
    def _get_upload(self, file_path: str):
        upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        headers = self.get_headers()
        params = {'path': file_path, 'overwrite': 'true'}
        response = requests.get(upload_url, headers=headers, params=params)
        return response.json()

    def _log_func(self):
        full_path_logs = os.path.join(BASE_PATH, LOGS_DIR_NAME, LOGS_FILE_NAME)
        log_directory = os.path.join(BASE_PATH, LOGS_DIR_NAME)
        if not os.path.exists(log_directory):
            os.mkdir(log_directory)
        with open(full_path_logs, 'a') as file_log:
            file_log.write(f'{datetime.now()} \n')

    # загрузка файлов на диск
    def upload(self, directory: str, path_to_yandexdisk: str):
        self._make_folder_yadisk(path_to_yandexdisk)
        file_list = os.listdir(directory)
        for file in file_list:
            href = self._get_upload(file_path=(path_to_yandexdisk + '/' + file)).get('href', "")
            response = requests.put(href, data=open(os.path.join(directory, file), 'rb'))
            response.raise_for_status()
            if response.status_code == 201:
                print('Success')
        self._log_func()


if __name__ == '__main__':

    # считываем токен из файла для VK
    full_path_token_vk = os.path.join(BASE_PATH, TOKEN_VK_NAME)
    with open(full_path_token_vk, 'r') as file_obj:
        token = file_obj.read().strip()

    owner_id = input('Введите user id: ').strip()
    directory = os.path.join(BASE_PATH, owner_id)
    if not os.path.exists(directory):
        os.mkdir(directory)
    count_of_photos = input('Введите какое кол-во фото загрузить (по умолчанию 5): ').strip()
    ver_vk = '5.131'

    vk_user = VkUser(token, ver_vk, count_of_photos)
    photos = vk_user.get_photos(owner_id)

    path_to_yandexdisk = owner_id
    token_ya = 'AQAAAABWyoCJAADLWyRSnIXtBkVooENr291MNjs'

    uploader = YaUploader(token_ya)
    uploader.upload(directory, path_to_yandexdisk)
