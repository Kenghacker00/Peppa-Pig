from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, g
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash  # Añade esta línea
import sqlite3
from controllers.auth import AuthController
from controllers.movie import MovieController
from controllers.review import ReviewController
from utils.imdb import search_movies, get_movie_details
from utils.email import send_verification_email
import os
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'tu_clave_secreta'
db_path = 'database/cinevibes.db'

# Inicializar controladores
auth_controller = AuthController(db_path)
movie_controller = MovieController(db_path)
review_controller = ReviewController(db_path)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            recent_movies = cursor.execute(
                'SELECT * FROM movies ORDER BY release_date DESC LIMIT 10'
            ).fetchall()
        except sqlite3.OperationalError:
            # Si la tabla no existe, devuelve una lista vacía
            recent_movies = []
    return render_template('index.html', movies=recent_movies)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Obtener datos del formulario o JSON
        data = request.get_json() if request.is_json else request.form
        nickname = data.get('nickname')
        email = data.get('email')
        password = data.get('password')

        db = get_db()
        error = None

        if not nickname:
            error = 'Se requiere un nickname.'
        elif not email:
            error = 'Se requiere un email.'
        elif not password:
            error = 'Se requiere una contraseña.'
        elif db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
            error = f'El email {email} ya está registrado.'

        if error is None:
            verification_code = ''.join(random.choices('0123456789', k=6))
            db.execute(
                'INSERT INTO users (nickname, email, password, verification_code) VALUES (?, ?, ?, ?)',
                (nickname, email, generate_password_hash(password), verification_code)
            )
            db.commit()
            send_verification_email(email, verification_code)

            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Registro exitoso. Se ha enviado un código de verificación a tu email.'
                })
            flash('Registro exitoso. Se ha enviado un código de verificación a tu email.', 'success')
            return redirect(url_for('verify', email=email))

        if request.is_json:
            return jsonify({'success': False, 'message': error})
        flash(error, 'error')

    return render_template('register.html')

@app.route('/verify/<email>', methods=['GET', 'POST'])
def verify(email):
    if request.method == 'POST':
        code = request.form.get('code')
        result = auth_controller.verify_code(email, code)

        if result.get('success'):
            flash('Cuenta verificada exitosamente. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        else:
            flash(result.get('message'), 'error')

    return render_template('verify.html', email=email)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Obtener datos del formulario o JSON
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        password = data.get('password')

        db = get_db()
        error = None
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user is None:
            error = 'Email incorrecto.'
        elif not check_password_hash(user['password'], password):
            error = 'Contraseña incorrecta.'
        elif not user['is_verified']:
            error = 'Por favor verifica tu email antes de iniciar sesión.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']

            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Inicio de sesión exitoso'
                })
            return redirect(url_for('index'))

        if request.is_json:
            return jsonify({'success': False, 'message': error})
        flash(error, 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = auth_controller.get_user_profile(session['user_id'])
    reviews = review_controller.get_user_reviews(session['user_id'])
    return render_template('profile.html', user=user, reviews=reviews)

@app.route('/movie/<int:movie_id>', methods=['GET', 'POST'])
def movie_detail(movie_id):
    movie = movie_controller.get_movie_details(imdb_id)
    if movie:
        return render_template('movie_detail.html', movie=movie)
    else:
        flash('Película no encontrada', 'error')
        return redirect(url_for('index'))

@app.route('/movie/player/<string:movie_id>')
def movie_player(movie_id):
    # Diccionario con la información de las películas
    movies = {
        'tt1431045': {
            'title': 'Deadpool',
            'year': '2016',
            'director': 'Tim Miller',
            'plot': 'Un mercenario con una lengua afilada y un sentido del humor mórbido es sometido a un experimento clandestino que le deja con poderes de curación acelerados y una misión de venganza.',
            'imdb_id': 'tt1431045'
        },
        'tt1537481': {
            'title': 'Deadpool And Wolverine',
            'year': '2024',
            'director': 'Shawn Levy',
            'plot': 'La nueva entrega de la saga donde Wade Wilson, conocido por todos como Deadpool, intenta llevar una vida normal lejos de su pasado como mercenario. Pero cuando su mundo se encuentra al borde de una catástrofe, se ve obligado a regresar a la acción.',
            'imdb_id': 'tt1537481'
        }
    }

    movie = movies.get(movie_id)
    if movie is None:
        return "Película no encontrada", 404

    return render_template('movie_player.html', movie=movie)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    if query:
        movies = movie_controller.search_movies(query)
        return render_template('search_results.html', movies=movies, query=query)
    return render_template('search.html')

@app.route('/movie/<string:movie_id>/review', methods=['POST'])
def add_review(movie_id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión para dejar una reseña.', 'error')
        return redirect(url_for('login'))

    content = request.form['content']
    rating = request.form['rating']

    review_controller.add_review(session['user_id'], movie_id, content, rating)
    flash('Tu reseña ha sido añadida.', 'success')
    return redirect(url_for('movie_detail', movie_id=movie_id))

from utils.email import send_movie_request_email

@app.route('/request-movie', methods=['GET', 'POST'])
def request_movie():
    if request.method == 'POST':
        movie_title = request.form['movie_title']
        user_email = request.form['user_email']

        send_movie_request_email('vibescine10@gmail.com', movie_title, user_email)
        flash('Tu solicitud de película ha sido enviada.', 'success')
        return redirect(url_for('index'))

    return render_template('request_movie.html')

@app.route('/favorites', methods=['GET', 'POST'])
def favorites():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        movie_id = request.form.get('movie_id')
        movie_controller.toggle_favorite(session['user_id'], movie_id)
        return jsonify({'success': True})

    favorites = movie_controller.get_user_favorites(session['user_id'])
    return render_template('favorites.html', movies=favorites)

@app.route('/recommend')
def recommend():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    recommendations = movie_controller.get_recommendations(session['user_id'])
    return render_template('recommend.html', movies=recommendations)

@app.route('/genres/<genre>')
def genre_movies(genre):
    movies = movie_controller.get_movies_by_genre(genre)
    return render_template('genre_movies.html', genre=genre, movies=movies)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Crear la base de datos y las tablas si no existen
    with sqlite3.connect(db_path) as conn:
        # Crear tabla de usuarios
        conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            is_verified BOOLEAN DEFAULT 0,
            verification_code TEXT,
            profile_pic TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

        # Crear tabla de películas
        conn.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                imdb_id TEXT UNIQUE,
                title TEXT NOT NULL,
                year INTEGER,
                poster TEXT,
                plot TEXT,
                director TEXT,
                actors TEXT,
                genres TEXT,
                imdb_rating REAL,
                release_date TIMESTAMP
            )
        ''')

        # Crear tabla de reseñas
        conn.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                movie_id INTEGER,
                review_text TEXT,
                rating INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (movie_id) REFERENCES movies (id)
            )
        ''')

        # Crear tabla de favoritos
        conn.execute('''
            CREATE TABLE IF NOT ```python
            EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                movie_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (movie_id) REFERENCES movies (id),
                UNIQUE(user_id, movie_id)
            )
        ''')

        # Crear tabla de códigos de verificación
        conn.execute('''
            CREATE TABLE IF NOT EXISTS verification_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                code TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_used BOOLEAN DEFAULT 0
            )
        ''')

        # Crear tabla de preferencias de usuario
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                preferred_genres TEXT,
                preferred_actors TEXT,
                preferred_directors TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Crear tabla de historial de visualización
        conn.execute('''
            CREATE TABLE IF NOT EXISTS watch_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                movie_id INTEGER,
                watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (movie_id) REFERENCES movies (id)
            )
        ''')

        # Crear índices para mejorar el rendimiento
        conn.execute('CREATE INDEX IF NOT EXISTS idx_movies_title ON movies(title)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_movies_imdb_id ON movies(imdb_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_reviews_movie_id ON reviews(movie_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews(user_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_favorites_movie_id ON favorites(movie_id)')

        # Crear vistas para consultas comunes
        conn.execute('''
            CREATE VIEW IF NOT EXISTS movie_ratings AS
            SELECT
                movie_id,
                COUNT(*) as review_count,
                AVG(rating) as average_rating
            FROM reviews
            GROUP BY movie_id
        ''')

        conn.execute('''
            CREATE VIEW IF NOT EXISTS user_activity AS
            SELECT
                users.id as user_id,
                users.nickname,
                COUNT(DISTINCT reviews.id) as review_count,
                COUNT(DISTINCT favorites.id) as favorite_count,
                COUNT(DISTINCT watch_history.id) as watched_count
            FROM users
            LEFT JOIN reviews ON users.id = reviews.user_id
            LEFT JOIN favorites ON users.id = favorites.user_id
            LEFT JOIN watch_history ON users.id = watch_history.user_id
            GROUP BY users.id
        ''')

        conn.commit()

    # Configuración adicional de la aplicación
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

    # Asegurarse de que existe el directorio de uploads
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Configurar el manejo de sesiones
    app.permanent_session_lifetime = timedelta(days=30)

    # Ejecutar la aplicación
    app.run(debug=True)
