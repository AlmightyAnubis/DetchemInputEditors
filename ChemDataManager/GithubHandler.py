from tkinter import messagebox

import github
#import gitlab
#import github3
from github import Github
from github import Auth
from github.ContentFile import ContentFile
from requests import session

from bs4 import BeautifulSoup as bs

# Authentication is defined via github.Auth

import GeneralUtil.TextModifiers
from ChemDataManager import global_vars

# Needs good authentication system, what is not easy to do...
def send_pull_request(target_branch, title, body) -> int:
    # using an access token

    # Public Web Github
    name = ""
    pw = ""
    #gh = github3.login(username=name, password=pw)
    #gh.login(username=name, password=pw)
    #user = gh.me()
    #repos = user.repositories()

    USER = name
    PASSWORD = pw

    URL1 = 'https://github.com/session'

    with session() as s:

        req = s.get(URL1).text
        html = bs(req)
        token = html.find("input", {"name": "authenticity_token"}).attrs['value']
        com_val = html.find("input", {"name": "commit"}).attrs['value']

        login_data = {'login': USER,
                      'password': PASSWORD,
                      'commit': com_val,
                      'authenticity_token': token}

        r1 = s.post(URL1, data=login_data)
        response_url = r1.url
        cookies = r1.cookies
        print(len(cookies))
        session_key = ""
        for cookie in cookies:
            if cookie.name == "_gh_sess":
                session_key = cookie.value
        if session_key != "":
            login_data.update({'session_key': session_key})
            gh = github.Github(session_key)
            print(gh.get_user())

        r2 = s.get(response_url)


    # Not working !!

    return 0

if __name__ == "__main__":
    send_pull_request("a","b","c")