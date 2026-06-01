from flask import Flask, send_from_directory
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
interface_dir = os.path.join(BASE_DIR, "interface_test")
app = Flask(__name__, static_folder=interface_dir, template_folder=interface_dir)

@app.route('/')
def index():
    """Sert la page principale de l'interface (index.html)."""
    return send_from_directory(interface_dir, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """Sert les fichiers statiques (JS, CSS, images, etc.) depuis le dossier interface_test.

    :param filename: chemin relatif du fichier demandé (str), ex. "style.css" ou "img/logo.png"
    """
    return send_from_directory(interface_dir, filename)

if __name__ == '__main__':
    app.run(debug=True)
