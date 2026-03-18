from dotenv import load_dotenv
import os
load_dotenv()


class ENVDATA:
    EMAIL = os.getenv("EMAIL")
    PASSWORD = os.getenv("PASSWORD")
    ONELOGIN_SUBDOMAIN = os.getenv("ONELOGIN_SUBDOMAIN")
    ONELOGIN_USERNAME = os.getenv("ONELOGIN_USERNAME")
    ONELOGIN_PASSWORD = os.getenv("ONELOGIN_PASSWORD")
    ONELOGIN_CLIENT_ID = os.getenv("ONELOGIN_CLIENT_ID")
    ONELOGIN_CLIENT_SECRET = os.getenv("ONELOGIN_CLIENT_SECRET")
    TYPE = os.getenv("TYPE")
    PROJECT_ID = os.getenv("PROJECT_ID")
    PRIVATE_KEY_ID = os.getenv("PRIVATE_KEY_ID")
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")
    CLIENT_EMAIL = os.getenv("CLIENT_EMAIL")
    CLIENT_ID = os.getenv("CLIENT_ID")
    AUTH_URI = os.getenv("AUTH_URI")
    TOKEN_URI = os.getenv("TOKEN_URI")
    AUTH_PROVIDER_X509_CERT_URL = os.getenv("AUTH_PROVIDER_URL")
    CLIENT_X509_CERT_URL = os.getenv("CLIENT_CERT_URL")
    UNIVERSAL_DOMAIN = os.getenv("UNIVERSAL_DOMAIN")
    HEADLESS = os.getenv("HEADLESS", "false")
    SPREADSHEET_NAME=os.getenv("SPREADSHEET_NAME")
    WORKSHEET_NAME=os.getenv("WORKSHEET_NAME")