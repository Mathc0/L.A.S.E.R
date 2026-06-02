from flask import Flask, send_from_directory
import os

app = Flask(__name__, static_folder="interface_test", template_folder="interface_test")

@app.route('/')
def index():
    """
    Sert la page d'accueil de l'interface.
    Retourne le fichier index.html.
    """
    return send_from_directory(app.template_folder, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """
    Sert les fichiers statiques du projet.
    Gère les fichiers CSS, JavaScript et images.
    
    :param filename: chemin du fichier à servir
    """
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    app.run(debug=True)
