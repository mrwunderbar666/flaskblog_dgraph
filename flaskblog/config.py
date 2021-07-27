import os

class Config:
    SECRET_KEY = os.environ.get('FLASKBLOG_SECRETKEY', '123456789')
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('EMAIL_USER')
    MAIL_PASSWORD = os.environ.get('EMAIL_PW')
    DGRAPH_ENDPOINT = "localhost:9080"
    DGRAPH_CREDENTIALS = None
    DGRAPH_OPTIONS = None