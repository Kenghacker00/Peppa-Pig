from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from controllers.auth import AuthController
from controllers.movie import MovieController
from controllers.review import ReviewController
from utils.imdb import search_movies, get_movie_details
from utils.email import send_verification_email
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
from database import db
import random
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import SubmitField

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'tu_clave_secreta'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
db_path = 'database/cinevibes.db'

# Inicializar controladores
auth_controller = AuthController(db_path)
movie_controller = MovieController(db_path)
review_controller = ReviewController(db_path)

class ProfileForm(FlaskForm):
    profile_pic = FileField('Foto de Perfil', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Solo se permiten imágenes.')
    ])
    submit = SubmitField('Actualizar')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para ver tu perfil', 'error')
        return redirect(url_for('login'))

    form = ProfileForm()

    if form.validate_on_submit():
        if form.profile_pic.data:
            file = form.profile_pic.data
            filename = secure_filename(f"user_{session['user_id']}_{file.filename}")

            # Asegurarse de que existe el directorio de uploads
            upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'profile_pics')
            os.makedirs(upload_folder, exist_ok=True)

            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)

            # Actualizar la base de datos con la nueva ruta
            relative_path = os.path.join('uploads', 'profile_pics', filename)
            auth_controller.update_profile_pic(session['user_id'], relative_path)

            flash('Foto de perfil actualizada con éxito', 'success')
            return redirect(url_for('profile'))

    user = auth_controller.get_user_profile(session['user_id'])
    reviews = review_controller.get_user_reviews(session['user_id'])
    return render_template('profile.html', user=user, reviews=reviews, form=form)

def get_db():
    return db.get_db()

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
        if auth_controller.verify_code(email, code):
            flash('Cuenta verificada exitosamente. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Código de verificación incorrecto.', 'error')

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
        },
        'tt10872600': {
            'title': 'Spider-Man: No Way Home',
            'year': '2021',
            'director': 'Jon Watts',
            'plot': 'Peter Parker es desenmascarado y por tanto no es capaz de separar su vida normal de los enormes riesgos que conlleva ser un súper héroe. Cuando pide ayuda a Doctor Strange, los riesgos pasan a ser aún más peligrosos, obligándole a descubrir lo que realmente significa ser Spider-Man.',
            'imdb_id': 'tt10872600'
        }
    }

    movie = movies.get(movie_id)
    if movie is None:
        return "Película no encontrada", 404

    return render_template('movie_player.html', movie=movie)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    if query:
        movies = movie_controller.search_movies(query)
        return render_template('search_results.html', movies=movies, query=query)
    return render_template('search.html')

@app.route('/movie/<string:movie_id>', methods=['GET', 'POST'])
def movie_detail(movie_id):
    movie = movie_controller.get_movie_details(movie_id)
    if movie:
        return render_template('movie_detail.html', movie=movie)
    else:
        flash('Película no encontrada', 'error')
        return redirect(url_for('index'))

def search_movies(query):
    url = f"http://www.omdbapi.com/?apikey={Config.OMDB_API_KEY}&s={query}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(data)  # Imprimir la respuesta para depuración
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con la API de OMDb: {e}")
        return {"errorMessage": "No se pudo conectar con la API de OMDb"}

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
        additional_info = request.form.get('additional_info', '')

        # Enviar email sin el additional_info si la función solo acepta 3 argumentos
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

@app.route('/movie/<string:imdb_id>', methods=['GET', 'POST'])
def movie(imdb_id):
    movie = movie_controller.get_movie_details(imdb_id)
    form = ReviewForm()
    reviews = review_controller.get_movie_reviews(imdb_id)
    return render_template('movie.html', movie=movie, form=form, reviews=reviews)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Elimina todo el código de creación de tablas al final del archivo
if __name__ == '__main__':
    # Configuración adicional de la aplicación
    UPLOAD_FOLDER = 'static/images'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    # Asegurarse de que existe el directorio de uploads
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Configurar el manejo de sesiones
    app.permanent_session_lifetime = timedelta(days=30)

    # Ejecutar la aplicación
    app.run(debug=True)
