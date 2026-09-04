import os
import re
import time

import pandas as pd
import vk_api
from dotenv import load_dotenv
from vk_api.exceptions import Captcha
import logging

format=('[{asctime}] #{levelname:8} {filename} - {lineno} - {message}')
stderr_handler = logging.StreamHandler()
file_handler = logging.FileHandler('logs.log')


logging.basicConfig(level=logging.INFO, format=format, datefmt='%Y-%m-%d %H:%M:%S', style='{')

logger=logging.getLogger(__name__)

logger.addHandler(file_handler)
logger.addHandler(stderr_handler)

excel_day=int(input('Введи день экселя\n'))
if 1 <= excel_day <= 9:
    file_path = fr"group_target/День_{excel_day}.xlsx"
elif 10 <= excel_day < 50:
    file_path = fr"group_target/GruppySLR.xlsx"
elif excel_day >= 50:
    file_path = fr"group_target/GruppySLR2.xlsx"
else:
    raise ValueError(f"Некорректный день: {excel_day}")

print(file_path)

urls = pd.read_excel(file_path, sheet_name = 'Предложка')
urls = urls[urls["Commit"].isna()]
urls["Commit"] = urls["Commit"].astype(str).str.strip()
load_dotenv("req.env")

TOKEN = input("Введи токен \n").split('=')[1].split('&')[0]
print(f"TOKEN={TOKEN}")  # <- проверим, что токен загружен
# GROUP_URL = "https://vk.com/club230032166"
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
upload = vk_api.VkUpload(vk_session)
urls = pd.read_excel(file_path)
subscription_log = []  # список для хранения информации о подписке


#Автор - Название книги
#Жанр
#Завершена в процессе
#Отрывок
#Короткая ссылка
#Обложка
POST_TEXT = f"""

Как я стала многодетной мамой
Ирис Вельс

Бытовое фэнтези 16+

Уснула в шелковой пижаме, а проснулась в вонючей избе на соломенном матрасе. 
Бонус: четверо голодных, немытых детей и муж-торговец, который появляется дома раз в полгода, чтобы сделать нового ребенка и снова уехать. Я всегда ненавидела бытовуху и яжематерей. 
Но теперь мне придется стать главной из них, чтобы выжить. А когда вернется благоверный, его ждет большой сюрприз.

https://vk.cc/d1iBJW
"""


def ensure_membership(group_id: int) -> str:
    try:
        response = vk.groups.isMember(group_id=abs(group_id))
        is_member = response.get("member") if isinstance(response, dict) else int(response)
        if not is_member:
            try:
                vk.groups.join(group_id=abs(group_id))
                time.sleep(1)
                return "✅ Подписались"
            except vk_api.exceptions.ApiError as join_error:
                return f"❌ Не удалось подписаться: {join_error}"
        return "🔁 Уже подписаны"
    except Exception as e:
        return f"❌ Ошибка при проверке подписки: {e}"

# Функция обработки одной ссылки

def process_group(url: str) -> str:
    subscription_status = "❌ Группа не обработана"  # значение по умолчанию
    try:
        match = re.search(r"vk.com/(?:club|public)?([^?/]+)", str(url))
        if match:
            screen_name = match.group(1).strip()
            if screen_name.isdigit():
                group_id = -int(screen_name)
            else:
                response = vk.utils.resolveScreenName(screen_name=screen_name)
                if response and response['type'] == 'group':
                    group_id = -response['object_id']
                else:
                    subscription_log.append(subscription_status)
                    return "❌ Группа не найдена или указано неверное имя"
        else:
            subscription_log.append(subscription_status)
            return "❌ Некорректный формат ссылки на группу"

        # Проверка подписки и попытка подписаться
        subscription_status = ensure_membership(group_id)

        # Используем уже загруженное изображение
        attachment = "photo-235291631_457239121" #  МЕНЯТЬ ССЫЛКУ ТУТ
        try:
            resp = vk.wall.post(
                owner_id=group_id,
                message=POST_TEXT,
                attachments=attachment,
                from_group=0,
                signed=1,
            )
            time.sleep(7)
            subscription_log.append(subscription_status)
            return f"✅ Пост ID: {resp['post_id']}"
        except Captcha as cap:
            captcha_url = cap.get_url()
            print(f"🔐 Капча: {captcha_url}")
            code = input("Введите капчу VK: ")
            try:
                # Повторяем запрос с ключом капчи
                resp = cap.try_again(key=code)
                time.sleep(7)
                subscription_log.append(subscription_status)
                return f"✅ Пост после капчи ID: {resp['post_id']}"
            except Exception as e:
                subscription_log.append("❌ Капча не пройдена")
                return f"❌ Ошибка капчи: {e}"



    except vk_api.exceptions.ApiError as e:
        subscription_log.append(subscription_status)
        return f"❌ Пост не отправлен! ошибка: {e}"
    except Exception as e:
        subscription_log.append(subscription_status)
        return f"❌ Ошибка: {e}"


# Применяем ко всем строкам
urls['status'] = urls[' Ссылка'].apply(process_group)
urls['subscription'] = subscription_log[:len(urls)]  # гарантируем соответствие длины
output_path=r"group_target/группы.xlsx"
# Сохраняем результат
urls.to_excel(output_path, index=False)
print("Готово! Смотри файл группы.xlsx")
