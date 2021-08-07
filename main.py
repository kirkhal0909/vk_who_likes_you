import requests
import re

class VK:
    __session__ = None
    __headers__ = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36"}

    def __init__(self, login, password):
        self.__session__ = requests.Session()
        authed = self.auth(login, password)
        if authed:
            print("Authed successfully")
        else:
            print("Some problem with authorization")

    def do_get(self, link, writeToFile=False):
        r = self.__session__.get(link, headers=self.__headers__)
        if writeToFile:
            file = open("tmp.html", "wb")
            file.write(r.content)
            file.close()
        return r

    def do_post(self, link, data, writeToFile=False):
        r = self.__session__.post(link, data=data, headers=self.__headers__)
        if writeToFile:
            file = open("tmp.html", "wb")
            file.write(r.content)
            file.close()
        return r

    def parse(self, text, leftText, rightText, fromPos=0):
        parsed = [founded[len(leftText): founded.rfind(rightText)] for founded in re.findall(leftText + r".*?" + rightText, text[fromPos:]) ]
        return parsed

    def auth(self, login, password):
        authed = False
        r = self.do_get("https://vk.com")
        ip_h = self.parse(r.text, '''<input type="hidden" name="ip_h" value="''', '''" />''')[0]
        lg_h = self.parse(r.text, '''<input type="hidden" name="lg_h" value="''', '''" />''')[0]

        auth_link = "https://login.vk.com/?act=login"
        data = {
            "act": "login", "role": "al_frame",
            "_origin": "https://vk.com",
            "ip_h": ip_h, "lg_h": lg_h,
            "email": login, "pass": password
        }
        r = self.do_post(auth_link, data)
        if "onLoginDone" in r.text:
            authed = True
        return authed

    def photo_likes(self, photo_id="59837601_457263143"):
        link = "https://vk.com/like.php?act=a_get_stats"
        data = {
            "act": "a_get_stats",
            "al": "1",
            "has_share": "1",
            "object": "photo" + photo_id
        }
        r = self.do_post(link, data)
        who_likes = self.parse(r.text.replace("\\",""), '''href="/''', '''">''')[1:]
        return who_likes

    def photos_ids(self, human_id="59837601", max_pages = 2):
        link = "https://vk.com/photos"+str(human_id)
        pages = max_pages
        offset = 0
        data = {
            "al": "1", "al_ad": "0",
            "from": "albums", "from_block": "1",
            "offset": str(offset), "part": "1"
        }
        r = self.do_post(link, data)

        photo_ids = set()
        photo_ids_last = self.parse(r.text.replace("\\",""), 'data-id="', '"')
        photo_ids |= set(photo_ids_last)
        pages -= 1
        while len(photo_ids_last) != 0 and pages > 0:
            pages -= 1
            offset += 85
            data["offset"] = str(offset)
            r = self.do_post(link, data)
            photo_ids_last = self.parse(r.text.replace("\\", ""), 'data-id="', '"')
            photo_ids |= set(photo_ids_last)


        return photo_ids

    def photos_who_likes_often(self, human_id="59837601", pages_photos_max = 2):
        print("Try get photos from album - {}".format(human_id))
        photos_ids = self.photos_ids(human_id=human_id, max_pages=pages_photos_max)
        print("Links photos loaded - {}".format(len(photos_ids)))
        who_likes = {}
        count = 0
        for photo_id in photos_ids:
            who = self.photo_likes(photo_id)
            for human_href in who:
                try:
                    who_likes[human_href] += 1
                except:
                    who_likes[human_href] = 1
            if count % 20 == 0:
                print("Progress {}/{}".format(count+1, len(photos_ids)))
            count += 1

        who_likes = {k: v for k, v in sorted(who_likes.items(), key=lambda item: item[1], reverse=True)}
        fileName = "Who_like_{}.txt".format(human_id)
        file = open(fileName,"w")
        for who in who_likes:
            file.write("{}\thttps://vk.com/{}\n".format(who_likes[who], who))
        file.close()
        print()
        print("who likes often stats writed to:\n{}".format(fileName))


login, password = open("auth_data.txt", "r").read().split("\n")

vk = VK(login, password)
vk.photos_who_likes_often("59837601")
