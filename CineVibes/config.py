import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tu_clave_secreta'
    DATABASE = 'database/cinevibes.db'
    EMAIL_SENDER = 'vibescine10@gmail.com'
    EMAIL_PASSWORD = 'adoi iehs jvmm itme'
    OMDB_API_KEY = '15fb7f01'
