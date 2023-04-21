from heapq import nlargest
import requests
import json
from data.token_list import access_token, user_id
import datetime


class VK:
    def __init__(self, version="5.131"):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.params = {"access_token": self.token, "v": self.version}
        self.data_point = self.id.isdigit()

    def users_info(self):  # получение информации о пользователе
        url = "https://api.vk.com/method/users.get"
        params = {"user_ids": self.id, "fields": "domain"}
        response = requests.get(url, params={**self.params, **params})

        return response.json()

    def get_photos_data(
        self, owner_id, token, offset=0
    ):  # получение информации о фото из ВК
        self.id = owner_id
        self.token = token
        url = "https://api.vk.com/method/photos.get"
        params = {
            "owner_id": self.id,
            "album_id": "profile",
            "access_token": self.token,
            "rev": 0,
            "extended": 1,
            "v": self.version,
            "photo_sizes": 1,
            "offset": offset,
        }
        response = requests.get(url, params=params)
        link = f"https://vk.com/{self.id}"
        # print(link)
        return json.loads(response.text)

    def data_for_db(self):
        data = self.users_info()
        # pprint(data)
        name = data["response"][0]["first_name"]
        second_name = data["response"][0]["last_name"]
        link = data["response"][0]["domain"]
        super_link = f"https://vk.com/{link}"
        data = self.get_photos_data(self.id, self.token)
        count_foto = data["response"]["count"]
        i = 0
        likes_counter = []  # находим самые популярные фото (по лайкам)
        while i < count_foto:
            likes = data["response"]["items"][i]["likes"]["count"]
            likes_counter.append(likes)
            i += 1
        likes_leaders = nlargest(3, likes_counter)
        # print(likes_leaders)

        j = 0
        new_data = []
        while j < count_foto:
            if data["response"]["items"][j]["likes"]["count"] in likes_leaders:
                new_data.append(data["response"]["items"][j])
            j += 1

        link_list = []
        k = 0
        while k < len(likes_leaders):  # отбираем версии фото лучшего качества
            max_height = 0
            for pics in new_data[k]["sizes"]:
                if max_height < pics["height"]:
                    max_height = pics["height"]
            # print(max_height)
            for pic in new_data[k]["sizes"]:
                # print(pic)
                if pic["height"] == max_height:
                    # print(max_height)
                    link_list.append(pic["url"])
            k += 1
        return link_list, name, second_name, super_link

# vk = VK()
# pprint(vk.data_for_db())

def take_user_info(user_id):
    url_id_info = "https://api.vk.com/method/users.get"
    params_id_info = {
        "access_token": access_token,
        "user_ids": user_id,
        "fields": "city, sex, bdate",
        "name_case": "nom",
        "v": "5.131",
    }
    response_id_info = requests.get(url_id_info, params=params_id_info)
    data_id_info = response_id_info.json()["response"][0]
    info = {
        "first_name": data_id_info["first_name"],
        "last_name": data_id_info["last_name"],
        "sex": data_id_info["sex"],
        "city": 1,
        "city_title": "Москва",
        "age": None
    }
    if "bdate" in data_id_info:
        try:
            delta = datetime.datetime.today() - datetime.datetime.strptime(
                data_id_info["bdate"], "%d.%m.%Y")
            info["age"] = delta.days // 365
        except:
            info["age"] = None
    if "city" in data_id_info:
        info["city"] = data_id_info["city"]["id"]
        info["city_title"] = data_id_info["city"]["title"]
    return info
