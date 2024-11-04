from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from controllers.auth import AuthController
from controllers.movie import MovieController
from controllers.review import ReviewController

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta'  # Cambia esto por una clave secreta real
db_path = 'database/cinevibes.db'

auth_controller = AuthController(db_path)
movie_controller = MovieController(db_path)
review_controller = ReviewController(db_path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    movie = movie_controller.get_movie_details(movie_id)
    return render_template('movie_detail.html', movie=movie)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Llama al controlador de autenticación
        result = auth_controller.login(email, password)

        if result.get('success'):  # Suponiendo que tu controlador devuelve un diccionario con una clave 'success'
            session['user_id'] = result['user_id']  # Guarda el ID del usuario en la sesión
            return redirect(url_for('profile'))  # Redirige a la página de perfil
        else:
            # Maneja el error (por ejemplo, mostrar un mensaje de error)
            return render_template('login.html', error=result.get('message'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Obtener datos del formulario
        nickname = request.form.get('nickname')
        email = request.form.get('email')
        password = request.form.get('password')

        # Llama al controlador de autenticación
        result = auth_controller.register(nickname, email, password)

        if result.get('success'):
            # Redirige a la página de verificación
            return redirect(url_for('verify', email=email))  # Pasa el email a la página de verificación
        else:
            # Maneja el error (por ejemplo, mostrar un mensaje de error)
            return render_template('register.html', error=result.get('message'))

    return render_template('register.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = auth_controller.get_user_profile(session['user_id'])
    return render_template('profile.html', nickname=user['nickname'], email=user['email'])

@app.route('/review', methods=['POST'])
def review():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Debes iniciar sesión para dejar una reseña.'})

    movie_id = request.json.get('movie_id')
    review_text = request.json.get('review_text')
    result = review_controller.add_review(session['user_id'], movie_id, review_text)
    return jsonify(result)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/movies')
def movie_list():
    # Aquí puedes obtener la lista de películas de la base de datos o de la API de IMDb
    return render_template('movie_list.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    email = request.args.get('email')  # Obtiene el email de la URL
    if request.method == 'POST':
        code = request.form.get('code')  # Obtiene el código ingresado por el usuario

        # Llama al controlador de autenticación para verificar el código
        result = auth_controller.verify_code(email, code)

        if result.get('success'):
            return redirect(url_for('login'))  # Redirige a la página de inicio de sesión
        else:
            return render_template('verify.html', error=result.get('message'), email=email)

    return render_template('verify.html', email=email)  # Muestra el formulario de verificación# Create this template

if __name__ == '__main__':
    # Crear la base de datos y las tablas si no existen
    conn = sqlite3.connect(db_path)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            release_date TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            movie_id INTEGER,
            review_text TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (movie_id) REFERENCES movies (id)
        )
    ''')
    conn.close()

    app.run(debug=True)
