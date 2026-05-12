from flask import Flask, send_from_directory
import os

app = Flask(__name__, static_folder="interface_test", template_folder="interface_test")

@app.route('/')
def index():
    # Sert le fichier index.html
    return send_from_directory(app.template_folder, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    # Sert les fichiers statiques (JS, CSS, images)
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    app.run(debug=True)
