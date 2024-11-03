from flask import render_template, redirect, url_for, flash, request, g, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, mail, get_db
from flask_mail import Message
import random
import string
import requests
import os
from datetime import datetime

@app.route('/')
def index():
    db = get_db()
    movies = db.execute('SELECT * FROM movies ORDER BY id DESC LIMIT 10').fetchall()
    return render_template('index.html', movies=movies)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone() is not None:
            error = 'User {} is already registered.'.format(username)
        elif db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone() is not None:
            error = 'Email {} is already registered.'.format(email)

        if error is None:
            confirmation_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            db.execute(
                'INSERT INTO users (username, email, password_hash, confirmation_code) VALUES (?, ?, ?, ?)',
                (username, email, generate_password_hash(password), confirmation_code)
            )
            db.commit()
            send_confirmation_email(email, confirmation_code)
            flash('A confirmation code has been sent to your email.', 'info')
            return redirect(url_for('confirm_email', email=email))

        flash(error, 'error')

    return render_template('register.html')

@app.route('/confirm_email/<email>', methods=['GET', 'POST'])
def confirm_email(email):
    if request.method == 'POST':
        code = request.form['confirmation_code']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user and code == user['confirmation_code']:
            db.execute('UPDATE users SET is_confirmed = 1, confirmation_code = NULL WHERE id = ?', (user['id'],))
            db.commit()
            flash('Your email has been confirmed. You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid confirmation code.', 'error')

    return render_template('confirm_email.html', email=email)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user is None:
            error = 'Incorrect email.'
        elif not check_password_hash(user['password_hash'], password):
            error = 'Incorrect password.'
        elif not user['is_confirmed']:
            error = 'Please confirm your email before logging in.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error, 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    if request.method == 'POST':
        nickname = request.form['nickname']
        profile_pic = request.form['profile_pic']

        db.execute('UPDATE users SET nickname = ?, profile_pic = ? WHERE id = ?',
                   (nickname, profile_pic, session['user_id']))
        db.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)

@app.route('/movie/<imdb_id>', methods=['GET', 'POST'])
def movie(imdb_id):
    db = get_db()
    movie = db.execute('SELECT * FROM movies WHERE imdb_id = ?', (imdb_id,)).fetchone()

    if not movie:
        # Fetch movie data from IMDb API
        api_key = os.getenv('IMDB_API_KEY')
        response = requests.get(f'http://www.omdbapi.com/?i={imdb_id}&apikey={api_key}')
        data = response.json()
        if data['Response'] == 'True':
            db.execute('INSERT INTO movies (imdb_id, title, year, poster) VALUES (?, ?, ?, ?)',
                       (imdb_id, data['Title'], int(data['Year']), data['Poster']))
            db.commit()
            movie = db.execute('SELECT * FROM movies WHERE imdb_id = ?', (imdb_id,)).fetchone()
        else:
            flash('Movie not found.', 'error')
            return redirect(url_for('index'))

    if request.method == 'POST' and 'user_id' in session:
        content = request.form['content']
        rating = request.form['rating']
        db.execute('INSERT INTO reviews (content, rating, user_id, movie_id) VALUES (?, ?, ?, ?)',
                   (content, rating, session['user_id'], movie['id']))
        db.commit()
        flash('Your review has been posted.', 'success')
        return redirect(url_for('movie', imdb_id=imdb_id))

    reviews = db.execute('SELECT r.*, u.username FROM reviews r JOIN users u ON r.user_id = u.id WHERE r.movie_id = ? ORDER BY r.timestamp DESC', (movie['id'],)).fetchall()
    return render_template('movie.html', movie=movie, reviews=reviews)

@app.route('/search')
def search():
    query = request.args.get('query')
    if query:
        api_key = os.getenv('IMDB_API_KEY')
        response = requests.get(f'http://www.omdbapi.com/?s={query}&apikey={api_key}')
        data = response.json()
        if data['Response'] == 'True':
            movies = data['Search']
            return render_template('search_results.html', movies=movies)
    return render_template('search_results.html', movies=[])

@app.route('/recommendations')
def recommendations():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    # Implementar lógica de recomendaciones basada en las reseñas del usuario
    # Por ahora, simplemente mostraremos algunas películas aleatorias
    recommended_movies = db.execute('SELECT * FROM movies ORDER BY RANDOM() LIMIT 5').fetchall()
    return render_template('recommendations.html', movies=recommended_movies)

def send_confirmation_email(email, code):
    msg = Message('Confirm Your Email', sender='noreply@cinevibes.com', recipients=[email])
    msg.body = f'Your confirmation code is: {code}'
    mail.send(msg)
