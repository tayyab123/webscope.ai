import os
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-development-secret")
    DATABASE = os.environ.get("WEBSCOPE_DB", "webscope.sqlite3")
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
