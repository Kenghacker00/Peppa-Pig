import requests
from config import Config

def search_movies(query):
    url = f"https://imdb-api.com/en/API/SearchMovie/{Config.IMDB_API_KEY}/{query}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Esto lanzará una excepción para códigos de estado HTTP no exitosos
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con la API de IMDb: {e}")
        return {"errorMessage": "No se pudo conectar con la API de IMDb"}

def get_movie_details(movie_id):
    url = f"https://imdb-api.com/en/API/Title/{Config.IMDB_API_KEY}/{movie_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener detalles de la película: {e}")
        return {"errorMessage": "No se pudieron obtener los detalles de la película"}
