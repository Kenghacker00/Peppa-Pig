document.addEventListener("DOMContentLoaded", function() {
    // Manejo del formulario de registro
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const nickname = document.getElementById('nickname').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ nickname, email, password })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('message').innerText = data.message;
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    }

    // Manejo del formulario de inicio de sesión
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('message').innerText = data.message;
                if (data.success) {
                    window.location.href = '/profile'; // Redirigir al perfil
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
       