import os
import re
import wget
import json
import random
import logging
import sqlite3
import asyncio
import requests
from pytube import YouTube
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, executor, types


API_TOKEN = '' # Токен
time_out = 900 # 15 мин
group_id = "-100000" # id группы 

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


def check_url_exists_in_database(url: str) -> bool:
    # Установление соединения с базой данных
    conn = sqlite3.connect('example.db')

    # Создание таблицы, если ее нет
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS urls (id INTEGER PRIMARY KEY, url TEXT)')

    # Формирование и выполнение SQL-запроса для поиска URL в базе данных
    sql = "SELECT * FROM urls WHERE url=?"
    cursor.execute(sql, (url,))

    # Получение результатов запроса
    result = cursor.fetchone()

    # Если URL найден в базе данных, возвращаем True
    if result:
        cursor.close()
        conn.close()
        return True
    else:
        # Добавление URL в базу данных
        sql = "INSERT INTO urls (url) VALUES (?)"
        cursor.execute(sql, (url,))
        conn.commit()

        cursor.close()
        conn.close()

        # Возвращаем False, т.к. URL не был найден в базе данных
        return False


def pars_vk():
    with open('list_vk.txt', 'r') as file:
        for line in file:

            line = line.replace(" ", "")
            line = line.replace("\n", "")

            try:
                html = requests.get(line)
                soup = BeautifulSoup(html.text, 'lxml')

                lenta = soup.find('div', {'id': 'posts_container'})
                test = lenta.find_all('div', class_="wall_item post--withRedesign")
                for i in test:
                    img = i.find('img', class_="MediaGrid__imageSingle")

                    status = check_url_exists_in_database(img['src'])
                    if status == False:
                        wget.download(img['src'], out="save_img")
                    else:
                        pass

                    print('good')
            except Exception as e:
                print('err')


def pars_youtube():
    with open('list_yt.txt', 'r') as file:
        for line in file:

            line = line.replace(" ", "")
            line = line.replace("\n", "")

            html = requests.get(line)
            soup = BeautifulSoup(html.text, 'lxml')

            pattern = re.compile(r"ytInitialData = (\{.*?\});$", re.MULTILINE | re.DOTALL)
            script = soup.find("script", string=pattern)

            if script:
                obj = pattern.search(script.text).group(1)
                obj = json.loads(obj)

            for i in obj['contents']['twoColumnBrowseResultsRenderer']['tabs']:
                try:
                    # print("Заголовок:" + i['tabRenderer']['content']['richGridRenderer']['contents'][0]['richItemRenderer']['content']['reelItemRenderer']['headline']['simpleText'])
                    #print("https://www.youtube.com/shorts/" + i['tabRenderer']['content']['richGridRenderer']['contents'][0]['richItemRenderer']['content']['reelItemRenderer']['videoId'])
                    #print('\n')

                    for y in i['tabRenderer']['content']['richGridRenderer']['contents']:
                        # print('Заголовок: ' + y['richItemRenderer']['content']['reelItemRenderer']['headline']['simpleText'])
                        # print("https://www.youtube.com/shorts/" + y['richItemRenderer']['content']['reelItemRenderer']['videoId'])

                        link = "https://www.youtube.com/watch?v=" + y['richItemRenderer']['content']['reelItemRenderer']['videoId'] # уник

                        status = check_url_exists_in_database(link)
                        if status == False:
                            yt = YouTube(link)
                            yt = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

                            chars = 'abcdefghijklnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
                            yt_name = ''

                            for i in range(8):
                                yt_name += random.choice(chars)

                            yt.download(output_path='save_video', filename=f"{yt_name}.mp4")
                        else:
                            pass

                except:
                    pass


async def main_video():
    content = os.listdir('save_video')

    for video in content:
        await asyncio.sleep(10.0)

        await bot.send_video(
            group_id,
            open(f'save_video\\{video}', 'rb'))

        os.remove(f'save_video\\{video}')

        await bot.close()

    # for video in content:
    #     os.remove(f'save_video\\{video}')


async def main_image():
    content = os.listdir('save_img')

    for img in content:
        await asyncio.sleep(10.0)

        await bot.send_photo(
              group_id,
              open(f'save_img\\{img}', 'rb'))

        os.remove(f'save_img\\{img}')

        await bot.close()

    # for img in content:
    #     os.remove(f'save_img\\{img}')


async def T_time():
    while True:
        await asyncio.sleep(float(time_out))

        print('start')

        # # Качаем картинки Ошибку выдало
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, pars_vk)
        #
        # # Качаем видео Норм сработало
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, pars_youtube)


        print('Ждем')
        await asyncio.sleep(300.0) # 5 мин

        # Работает
        await main_image()

        # Отправляем в группу порой баги, а так робит
        await main_video()


loop = asyncio.new_event_loop()
loop.run_until_complete(T_time())



