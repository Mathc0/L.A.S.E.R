from flask import Flask, send_from_directory
import os

app = Flask(__name__, static_folder="interface_test", template_folder="interface_test")

@app.route('/')
def index():
    """Sert la page principale de l'interface (index.html)."""
    return send_from_directory(app.template_folder, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """Sert les fichiers statiques (JS, CSS, images, etc.) depuis le dossier interface_test.

    :param filename: chemin relatif du fichier demandé (str), ex. "style.css" ou "img/logo.png"
    """
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    app.run(debug=True)
