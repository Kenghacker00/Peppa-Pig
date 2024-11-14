from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from controllers.auth import AuthController
from controllers.movie import MovieController
from controllers.review import ReviewController
from utils.imdb import search_movies, get_movie_details
from utils.email import send_verification_email, send_movie_request_email
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import SubmitField
from config import Config
import os
import random
import sqlite3
from database import db
from datetime import timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tu_clave_secreta')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Inicializar controladores
db_path = 'database/cinevibes.db'
auth_controller = AuthController(db_path)
movie_controller = MovieController(db_path)
review_controller = ReviewController(db_path)

class ProfileForm(FlaskForm):
    profile_pic = FileField('Foto de Perfil', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Solo se permiten imágenes.')
    ])
    submit = SubmitField('Actualizar')

def get_user():
    """Función para obtener el perfil del usuario si está autenticado."""
    return auth_controller.get_user_profile(session.get('user_id'))

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    user = get_user()
    recent_movies = []
    with db.get_db() as conn:
        cursor = conn.cursor()
        try:
            recent_movies = cursor.execute(
                'SELECT * FROM movies ORDER BY release_date DESC LIMIT 10'
            ).fetchall()
        except sqlite3.OperationalError:
            pass  # Si la tabla no existe, simplemente se devuelve una lista vacía
    return render_template('index.html', movies=recent_movies, user=user)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user = get_user()
    if user is None:
        flash('Debes iniciar sesión para ver tu perfil', 'error')
        return redirect(url_for('login'))

    form = ProfileForm()
    if form.validate_on_submit() and form.profile_pic.data:
        file = form.profile_pic.data
        filename = secure_filename(f"user_{session['user_id']}_{file.filename}")
        upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'profile_pics')
        os.makedirs(upload_folder, exist_ok=True)

        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        relative_path = os.path.join('uploads', 'profile_pics', filename)
        auth_controller.update_profile_pic(session['user_id'], relative_path)

        flash('Foto de perfil actualizada con éxito', 'success')
        return redirect(url_for('profile'))

    reviews = review_controller.get_user_reviews(session['user_id'])
    return render_template('profile.html', user=user, reviews=reviews, form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        nickname = data.get('nickname')
        email = data.get('email')
        password = data.get('password')

        error = validate_registration(nickname, email, password)
        if error:
            return handle_registration_error(error, request.is_json)

        auth_controller.register(nickname, email, password)

        if request.is_json:
            return jsonify({'success': True, 'message': 'Registro exitoso. Se ha enviado un código de verificación a tu email.'})
        flash('Registro exitoso. Se ha enviado un código de verificación a tu email.', 'success')
        return redirect(url_for('verify', email=email))

    return render_template('register.html', user=get_user())

def validate_registration(nickname, email, password):
    if not nickname:
        return 'Se requiere un nickname.'
    if not email:
        return 'Se requiere un email.'
    if not password:
        return 'Se requiere una contraseña.'
    if db.get_db().execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
        return f'El email {email} ya está registrado.'
    return None

def handle_registration_error(error, is_json):
    if is_json:
        return jsonify({'success': False, 'message': error})
    flash(error, 'error')
    return redirect(url_for('register'))

@app.route('/verify/<email>', methods=['GET', 'POST'])
def verify(email):
    user = get_user()
    if request.method == 'POST':
        code = request.form.get('code')
        if auth_controller.verify_code(email, code):
            flash('Cuenta verificada exitosamente. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        flash('Código de verificación incorrecto.', 'error')

    return render_template('verify.html', email=email, user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    user = get_user()
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        password = data.get('password')

        error, user_data = validate_login(email, password)  # Modificado para recibir user_data
        if error:
            return handle_login_error(error, request.is_json)

        session.clear()
        session['user_id'] = user_data['id']  # Ahora user_data está definido
        if request.is_json:
            return jsonify({'success': True, 'message': 'Inicio de sesión exitoso'})
        return redirect(url_for('index'))

    return render_template('login.html', user=user)

def validate_login(email, password):
    db_instance = db.get_db()  # Obtén la conexión a la base de datos
    user_data = db_instance.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if user_data is None:
        return 'Email incorrecto.', None
    if not check_password_hash(user_data['password'], password):
        return 'Contraseña incorrecta.', None
    if not user_data['is_verified']:
        return 'Por favor verifica tu email antes de iniciar sesión.', None
    return None, user_data  # Devuelve el user_data si no hay error

def handle_login_error(error, is_json):
    if is_json:
        return jsonify({'success': False, 'message': error})
    flash(error, 'error')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('index'))

@app.route('/movie/player/<string:movie_id>')
def movie_player(movie_id):
    user = get_user()
    movie = movie_controller.get_movie_details(movie_id)
    if movie is None:
        return "Película no encontrada", 404

    reviews = review_controller.get_movie_reviews(movie_id)
    return render_template('movie_player.html', movie=movie, reviews=reviews, user=user)

@app.route('/ver_peliculas', methods=['GET'])
def ver_peliculas():
    user = get_user()  # Obtener el perfil del usuario si está autenticado
    available_movies = movie_controller.get_available_movies()
    return render_template('ver_peliculas.html', movies=available_movies, user=user)

@app.route('/search', methods=['GET'])
def search():
    user = get_user()
    query = request.args.get('q', '')
    if query:
        movies = movie_controller.search_movies(query)
        available_movies = movie_controller.get_available_movies()
        return render_template('search_results.html', movies=movies.get('Search', []), available_movies=available_movies, query=query, user=user)
    return render_template('search.html', user=user)

@app.route('/movie/<string:movie_id>')
def movie_detail(movie_id):
    user = get_user()
    movie = movie_controller.get_movie_details(movie_id)
    if movie is None:
        return "Película no encontrada", 404
    return render_template('movie_detail.html', movie=movie, user=user)

@app.route('/movie/<string:movie_id>/review', methods=['POST'])
def add_review(movie_id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión para dejar un comentario.', 'error')
        return redirect(url_for('login'))

    content = request.form['content']
    rating = request.form['rating']
    review_controller.add_review(session['user_id'], movie_id, content, rating)
    flash('Tu comentario ha sido añadido.', 'success')
    return redirect(url_for('movie_player', movie_id=movie_id))

@app.route('/request-movie', methods=['GET', 'POST'])
def request_movie():
    user = get_user()
    movie_title = request.args.get('title', '').strip()
    movie_year = request.args.get('year', '')

    if request.method == 'POST':
        if user is None:
            flash('Debes iniciar sesión para enviar una solicitud de película.', 'error')
            return redirect(url_for('login'))

        user_email = request.form['user_email']
        movie_title = request.form['movie_title']
        additional_info = request.form.get('additional_info', '')

        if not movie_title:
            flash('El título de la película es obligatorio.', 'error')
            return redirect(url_for('request_movie', title=movie_title, year=movie_year))

        if not user_email:
            flash('El correo electrónico es obligatorio.', 'error')
            return redirect(url_for('request_movie', title=movie_title, year=movie_year))

        send_movie_request_email('vibescine10@gmail.com', movie_title, user_email, additional_info)
        flash('Tu solicitud de película ha sido enviada.', 'success')
        return redirect(url_for('index'))

    user_email = user['email'] if user else ''
    return render_template('request_movie.html', title=movie_title, year=movie_year, user_email=user_email, user=user)

@app.route('/favorites', methods=['GET', 'POST'])
def favorites():
    user = get_user()
    if user is None:
        return redirect(url_for('login'))

    if request.method == 'POST':
        movie_id = request.form.get('movie_id')
        movie_controller.toggle_favorite(session['user_id'], movie_id)
        return jsonify({'success': True})

    favorites = movie_controller.get_user_favorites(session['user_id'])
    return render_template('favorites.html', movies=favorites, user=user)

@app.route('/resend-verification-code/<email>', methods=['POST'])
def resend_verification_code(email):
    verification_code = ''.join(random.choices('0123456789', k=6))
    send_verification_email(email, verification_code)
    flash('Se ha reenviado el código de verificación a tu correo.', 'success')
    return redirect(url_for('verify', email=email))

@app.route('/recommend')
def recommend():
    user = get_user()
    if user is None:
        return redirect(url_for('login'))

    recommendations = movie_controller.get_recommendations(session['user_id'])
    return render_template('recommend.html', movies=recommendations, user=user)

@app.route('/genres/<genre>')
def genre_movies(genre):
    user = get_user()
    movies = movie_controller.get_movies_by_genre(genre)
    return render_template('genre_movies.html', genre=genre, movies=movies, user=user)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    user = get_user()
    return render_template('500.html', user=user), 500

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.permanent_session_lifetime = timedelta(days=30)
    app.run(debug=True)
