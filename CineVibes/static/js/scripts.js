document.addEventListener("DOMContentLoaded", function() {
    // Funciones de utilidad
    function handleFetchError(error) {
        console.error('Error:', error);
    }

    function updateMessage(message) {
        document.getElementById('message').innerText = message;
    }

    // Manejo del formulario de registro
    function handleRegisterForm() {
        const registerForm = document.getElementById('register-form');
        if (registerForm) {
            registerForm.addEventListener('submit', function(event) {
                event.preventDefault();
                const nickname = document.getElementById('nickname').value;
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;

                fetch('/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nickname, email, password })
                })
                .then(response => response.json())
                .then(data => updateMessage(data.message))
                .catch(handleFetchError);
            });
        }
    }

    // Manejo del formulario de inicio de sesión
    function handleLoginForm() {
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', function(event) {
                event.preventDefault();
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;

                fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                })
                .then(response => response.json())
                .then(data => {
                    updateMessage(data.message);
                    if (data.success) {
                        window.location.href = '/profile';
                    }
                })
                .catch(handleFetchError);
            });
        }
    }

    // Detección de bloqueador de anuncios
    function setupAdBlockDetection() {
        function adBlockDetected() {
            console.log("Bloqueador de anuncios detectado");
            // Lógica adicional si se detecta un bloqueador de anuncios
        }

        function adBlockNotDetected() {
            console.log("No se detectó bloqueador de anuncios");
            // Lógica adicional si no se detecta un bloqueador de anuncios
        }

        if (typeof fuckAdBlock === 'undefined') {
            adBlockDetected();
        } else {
            fuckAdBlock.onDetected(adBlockDetected);
            fuckAdBlock.onNotDetected(adBlockNotDetected);
        }
    }

    // Manejo de la carga de imagen de perfil
    function handleProfileImageUpload() {
        const profilePicInput = document.getElementById('profile_pic');
        if (profilePicInput) {
            profilePicInput.onchange = function() {
                if (this.files && this.files[0]) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        document.querySelector('.profile-image').src = e.target.result;
                    };
                    reader.readAsDataURL(this.files[0]);

                    // Mostrar indicador de carga
                    document.querySelector('.profile-image').style.opacity = '0.5';
                    document.querySelector('.profile-card').insertAdjacentHTML('beforeend', '<div id="loading">Subiendo...</div>');

                    // Enviar el formulario
                    this.form.submit();
                }
            };
        }
    }

    // Validación de formularios
    function setupFormValidation() {
        'use strict';
        var forms = document.querySelectorAll('.needs-validation');
        Array.prototype.slice.call(forms).forEach(function(form) {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
    }

    // Inicialización
    handleRegisterForm();
    handleLoginForm();
    setupAdBlockDetection();
    handleProfileImageUpload();
    setupFormValidation();
});

(function () {
    'use strict'
    const forms = document.querySelectorAll('.needs-validation')
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault()
                event.stopPropagation()
            }
            form.classList.add('was-validated')
        }, false)
    })
})()
