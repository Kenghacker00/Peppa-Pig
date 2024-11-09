import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tu_clave_secreta'
    DATABASE = 'database/cinevibes.db'
    EMAIL_SENDER = 'vibescine10@gmail.com'
    EMAIL_PASSWORD = 'adoi iehs jvmm itme'
    IMDB_API_KEY = 'http://www.omdbapi.com/?i=tt3896198&apikey=3e192711'
