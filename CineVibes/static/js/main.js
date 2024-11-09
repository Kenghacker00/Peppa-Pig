// static/js/main.js

document.addEventListener('DOMContentLoaded', function() {
    // Cerrar alertas
    const alertDismissible = document.querySelectorAll('.alert-dismissible');
    alertDismissible.forEach(alert => {
        alert.querySelector('.close').addEventListener('click', function() {
            alert.style.display = 'none';
        });
    });

    // Manejo de favoritos
    const favoriteButtons ```javascript
    = document.querySelectorAll('.favorite-button');
    favoriteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const movieId = this.dataset.movieId;
            fetch('/favorites', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                },
                body: JSON.stringify({ movie_id: movieId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Película añadida a favoritos.');
                } else {
                    alert('Error al añadir a favoritos.');
                }
            });
        });
    });
});
