import requests
from os import environ
from dotenv import load_dotenv


def login():
    profile_url = "https://railspaapi.shohoz.com/v1.0/web/auth/profile"
    login_url = "https://railspaapi.shohoz.com/v1.0/web/auth/sign-in"
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    }
    login_payload = {
        "mobile_number": environ.get("MOBILE_NUMBER"),
        "password": environ.get("PASSWORD"),
    }
    login_response = session.post(login_url, data=login_payload, headers=headers)
    login_dict = login_response.json()
    auth_token = ""
    if "data" in login_dict:
        print("Login successful!")
        print("Session Started")
        auth_token = login_dict["data"]["token"]
        # auth_hash = login_dict["extra"]["hash"]
        headers["Authorization"] = f"Bearer {auth_token}"
    else:
        print(login_dict["error"]["messages"])
        exit()
    profile_response = session.get(profile_url, headers=headers)
    profile_dict = profile_response.json()
    print(profile_dict["data"]["email"], profile_dict["data"]["display_name"], end="\n")


load_dotenv(dotenv_path=".env", override=True)
login()
