import requests
from config import Config

def search_movies(query):
    url = f"http://www.omdbapi.com/?apikey={Config.OMDB_API_KEY}&s={query}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Esto lanzará una excepción para códigos de estado HTTP no exitosos
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con la API de OMDb: {e}")
        return {"errorMessage": "No se pudo conectar con la API de OMDb"}

def get_movie_details(movie_id):
    url = f"http://www.omdbapi.com/?apikey={Config.OMDB_API_KEY}&i={movie_id}&language=es"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(data)  # Imprimir la respuesta para depuración
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener detalles de la película: {e}")
        return {"errorMessage": "No se pudieron obtener los detalles de la película"}
