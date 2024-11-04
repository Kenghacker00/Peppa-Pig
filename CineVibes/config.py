import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tu_clave_secreta'
    DATABASE = 'database/cinevibes.db'
    EMAIL_SENDER = 'vibescine10@gmail.com'  # Cambia esto por tu email
    EMAIL_PASSWORD = 'adoi iehs jvmm itme'  # Cambia esto por tu contraseña
    IMDB_API_KEY = '3e192711'  # Cambia esto por tu API Key de IMDb
