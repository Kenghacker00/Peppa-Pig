import requests
from config import Config

def get_movie_details(movie_id):
    url = f"https://imdb-api.com/en/API/Title/{Config.IMDB_API_KEY}/{movie_id}"
    response = requests.get(url)
    return response.json()

def search_movies(query):
    url = f"https://imdb-api.com/en/API/SearchMovie/{Config.IMDB_API_KEY}/{query}"
    response = requests.get(url)
    return response.json()
