import mechanicalsoup
import pandas as pd
import getpass
import login
import pathlib
import httpx
# DO NOT EDIT ABOVE THIS LINE



# User agent of your choice
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
# File to save session to.
session_file = "session.j4f"
# Directory to create just for fans tree.
save_dir = "./just4fans"

# DO NOT EDIT BELOW THIS LINE
save_location = pathlib.Path(save_dir)

urls = {
    "login":"https://justfor.fans/login.php",
    "home_url":"https://justfor.fans/home",
    "get_more_posts":"https://justfor.fans/ajax/getPosts.php?Type=One&UserID={}&PosterID={}&StartAt={}&Page=Profile&UserHash4={}&SplitTest=0"
# GET MORE POSTS ORDER USERID POSTERID STARTAT USERHASH4
}
# Create a browser object
class Browser:
    def __init__(self,name):
        self.media = {}
        self.name = name
        self.poster_id=""
        self.hash4=""
        self.start_at = 0
        self.sub_name = ""
        if not self.load_session():
            self.browser = mechanicalsoup.StatefulBrowser(user_agent=user_agent)
            self.browser.open(urls["login"])
            self.url = self.browser.get_url()
            self.page = self.browser.get_current_page()
            self.session = self.browser.session
            self.cookies = self.session.cookies.get_dict()
            self.headers = self.session.headers
            self.user_agent = user_agent


    def login(self):
        try:
            # _u = input("Email: ")
            # _p = input("Password: ")
            _u = login._u
            _p = login._p
            self.browser.select_form()
            self.browser["Email"] = _u
            self.browser["Password"] = _p
            self.browser.submit_selected()
            self.page = self.browser.get_current_page()
            self.session = self.browser.session
            self.cookies = self.session.cookies.get_dict()
            self.headers = self.session.headers
            self.url = self.browser.get_url()
        except:
            print("Login Failed")
    def go(self,url):
        try:
            self.browser.open(url)
            self.page = self.browser.get_current_page()
            self.session = self.browser.session
            self.cookies = self.session.cookies.get_dict()
            self.headers = self.session.headers
            self.url = self.browser.get_url()
            if not self.url == url:
                raise Exception("Failed to go to url")
        except Exception as e:
            print(e)
    def save_session(self):
        session = pd.DataFrame([self.name,self.cookies,self.headers,self.user_agent])
        session.to_csv(session_file)
    def load_session(self):
        try:
            session_info = pd.read_csv(session_file)
            if not self.name == session_info[0][0]:
                return False
            self.cookies = session_info[1][0]
            self.headers = session_info[2][0]
            self.user_agent = session_info[3][0]
            self.browser = mechanicalsoup.StatefulBrowser(user_agent=self.user_agent)
            self.browser.set_cookiejar(self.cookies)
            self.browser.session.headers = self.headers
            self.go(urls["home_url"])
            if self.browser.get_url() == urls["home_url"]:
                return True
            else:
                return False
        except:
            return False
    def get_subs(self):
        performers_div = self.browser.get_current_page().find_all("div", {"id": "homeMyPerformers"})
        performers_data = []
        for performer in performers_div:
            data = {"profile_url": "https://justfor.fans{}".format(performer.find("a")["href"]),
                    "name": performer.find("a").text.strip(), "image": performer.find("img")["src"]}
            performers_data.append(data)
        self.performers_data = performers_data

    def parse_subs(self):
        for sub in self.performers_data:
            self.go(sub["profile_url"])
            sub_post_data = self.page.find_all("div" , {"id":"postAreaAutoScroll"})
            sub_post_data = [x.find("a")["href"] for x in sub_post_data]
            if len(sub_post_data) == 1:
                sub_post_data = sub_post_data[0]
            else:
                sub_post_data = sub_post_data[1]
            sub_photo_data_split = sub_post_data.split("&")
            for x in sub_photo_data_split:
                if "PosterID" in x:
                    self.poster_id = x.split("=")[1]
                if "Hash4" in x:
                    self.hash4 = x.split("=")[1]
                if "UserID" in x:
                    self.user_id = x.split("=")[1]
            self.get_more_posts_url = urls["get_more_posts"].format(self.user_id,self.poster_id,self.start_at,self.hash4)
            sub_name = sub["name"]
            self.sub_name = sub_name
            sub_data = {"name": [], "photos": [], "videos": [], "audios": []}
            self.media.update({sub_name:sub_data})
    def get_posts(self):
        self.go(self.get_more_posts_url)
        self.page = self.browser.get_current_page()
        self.session = self.browser.session
        self.cookies = self.session.cookies.get_dict()
        self.headers = self.session.headers
        self.url = self.browser.get_url()
        self.start_at += 10
        self.get_more_posts_url = urls["get_more_posts"].format(self.user_id,self.poster_id,self.start_at,self.hash4)
    def find_media(self):
        # This function will need work to support filtering out old posts.
        images = self.page.find_all("img")
        sorted_images = []
        for image in images:
            if "src" in image.attrs:
                if "https://media.justfor.fans" in image["src"] and self.poster_id in image["src"]:
                    sorted_images.append(image["src"])
            elif "data-src" in image.attrs:
                if "https://media.justfor.fans" in image["data-src"] and self.poster_id in image["data-src"]:
                    sorted_images.append(image["data-src"])
            elif "data-original" in image.attrs:
                if "https://media.justfor.fans" in image["data-original"] and self.poster_id in image["data-original"]:
                    sorted_images.append(image["data-original"])
            elif "data-lazy" in image.attrs:
                if "https://media.justfor.fans" in image["data-lazy"] and self.poster_id in image["data-lazy"]:
                    sorted_images.append(image["data-lazy"])

        self.media[self.sub_name]['photos'].extend(sorted_images)
    def find_posts(self):
        pass
    def download_media(self):
        for sub in self.media:
            top_directory = pathlib.Path("{}/{}".format(save_dir,sub))
            top_directory.mkdir(parents=True, exist_ok=True)
            for media_type in self.media[sub]:
                sub_directory = pathlib.Path(top_directory / media_type)
                sub_directory.mkdir(parents=True, exist_ok=True)
                for media in self.media[sub][media_type]:
                    file_name = media.split("/")[-1]
                    file_path = pathlib.Path(sub_directory / file_name)
                    if not file_path.exists():
                        print("Downloading {}".format(file_name))


                    else:
                        print("Skipping {}".format(file_name))
    def print(self):
        print(self.url)
        print(self.media)








def process():
    j4f = Browser("j4f")
    j4f.login()
    j4f.save_session()
    j4f.go(urls["home_url"])
    j4f.get_subs()
    j4f.parse_subs()
    j4f.get_posts()
    j4f.find_media()
    j4f.print()
    j4f.download_media()


if __name__ == "__main__":
    process()