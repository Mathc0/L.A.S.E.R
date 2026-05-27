from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from client_yt_music import YouTubeMusicClient

app = Flask(__name__)
CORS(app)

# On crée le client YouTube une seule fois
youtube_client = YouTubeMusicClient()


@app.route("/")
def home():
    """Sert la page principale de l'interface (index.html)."""
    return send_from_directory("interface_test", "index.html")


@app.route("/style.css")
def style():
    """Sert le fichier de style CSS de l'interface."""
    return send_from_directory("interface_test", "style.css")


@app.route("/script.js")
def script():
    """Sert le fichier JavaScript de l'interface."""
    return send_from_directory("interface_test", "script.js")


@app.route("/api/test")
def test():
    """Vérifie que la connexion entre l'interface et le serveur Python fonctionne.

    Retourne un JSON :
        success (bool) : toujours True
        message (str)  : message de confirmation
    """
    return jsonify({
        "success": True,
        "message": "Connexion Python ↔ Interface OK"
    })


@app.route("/api/youtube", methods=["POST"])
def search_youtube():
    """Recherche une musique sur YouTube et lance sa lecture immédiatement.

    Corps JSON attendu :
        query (str) : terme de recherche (ex. "daft punk around the world")

    Retourne un JSON :
        success (bool) : True si la recherche a réussi
        track   (str)  : titre de la piste trouvée
        message (str)  : message d'erreur si success est False
    """
    data = request.get_json()
    query = data.get("query", "").strip()

    if not query:
        return jsonify({
            "success": False,
            "message": "Recherche vide"
        }), 400

    try:
        track = youtube_client.search_and_play(query)

        return jsonify({
            "success": True,
            "track": track
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


@app.route("/api/play", methods=["POST"])
def api_play():
    """Démarre ou reprend la lecture. Peut démarrer une piste spécifique par index.

    Corps JSON (optionnel) :
        index (int) : index de la piste dans la playlist à jouer (0-based).
                      Si absent, reprend la piste en cours.

    Retourne un JSON :
        success (bool) : True si l'opération a réussi
        status  (dict) : état complet du lecteur (voir get_status())
        message (str)  : message d'erreur si success est False
    """
    try:
        data = request.get_json(silent=True) or {}
        index = data.get("index")

        if index is not None:
            youtube_client.play(int(index))
        else:
            youtube_client.play()

        return jsonify({
            "success": True,
            "status": youtube_client.get_status()
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

@app.route("/api/pause", methods=["POST"])
def api_pause():
    """Met en pause la lecture en cours, ou la reprend si déjà en pause (toggle).

    Retourne un JSON :
        success (bool) : True si l'opération a réussi
        status  (dict) : état complet du lecteur (voir get_status())
        message (str)  : message d'erreur si success est False
    """
    try:
        youtube_client.pause()

        return jsonify({
            "success": True,
            "status": youtube_client.get_status()
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


@app.route("/api/status")
def api_status():
    """Retourne l'état complet du lecteur (piste en cours, volume, modes, etc.).

    Retourne un JSON :
        success (bool) : toujours True
        status  (dict) : état complet du lecteur (voir get_status())
    """
    return jsonify({
        "success": True,
        "status": youtube_client.get_status()
    })


@app.route("/api/next", methods=["POST"])
def api_next():
    """Passe à la piste suivante dans la playlist.

    Retourne un JSON :
        success (bool) : True si l'opération a réussi
        status  (dict) : état complet du lecteur (voir get_status())
        message (str)  : message d'erreur si success est False
    """
    try:
        youtube_client.next_track()
        return jsonify({
            "success": True,
            "status": youtube_client.get_status()
        })
    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


@app.route("/api/prev", methods=["POST"])
def api_prev():
    """Revient à la piste précédente dans la playlist.

    Retourne un JSON :
        success (bool) : True si l'opération a réussi
        status  (dict) : état complet du lecteur (voir get_status())
        message (str)  : message d'erreur si success est False
    """
    try:
        youtube_client.previous_track()
        return jsonify({
            "success": True,
            "status": youtube_client.get_status()
        })
    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

@app.route("/api/shuffle", methods=["POST"])
def api_shuffle():
    """Active ou désactive le mode lecture aléatoire (toggle).

    Retourne un JSON :
        success (bool) : True si l'opération a réussi
        status  (dict) : état complet du lecteur (voir get_status())
        message (str)  : message d'erreur si success est False
    """
    try:
        youtube_client.toggle_shuffle()
        return jsonify({
            "success": True,
            "status": youtube_client.get_status()
        })
    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


@app.route("/api/repeat", methods=["POST"])
def api_repeat():
    """Active ou désactive le mode répétition (toggle).

    Retourne un JSON :
        success (bool) : True si l'opération a réussi
        status  (dict) : état complet du lecteur (voir get_status())
        message (str)  : message d'erreur si success est False
    """
    try:
        youtube_client.toggle_repeat()
        return jsonify({
            "success": True,
            "status": youtube_client.get_status()
        })
    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

@app.route("/api/remove_youtube", methods=["POST"])
def api_remove_youtube():
    """Supprime une piste de la playlist YouTube par son index.

    Corps JSON attendu :
        index (int) : index de la piste à supprimer (0-based)

    Retourne un JSON :
        success (bool) : True si la suppression a réussi
        status  (dict) : état complet du lecteur (voir get_status())
        message (str)  : message d'erreur si success est False
    """
    data = request.get_json()
    index = data.get("index")

    try:
        index = int(index)

        if 0 <= index < len(youtube_client._playlist):
            youtube_client._playlist.pop(index)

            if youtube_client._current_index >= len(youtube_client._playlist):
                youtube_client._current_index = max(0, len(youtube_client._playlist) - 1)

            return jsonify({
                "success": True,
                "status": youtube_client.get_status()
            })

        return jsonify({
            "success": False,
            "message": "Index invalide"
        }), 400

    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

@app.route("/api/seek", methods=["POST"])
def api_seek():
    """Déplace la tête de lecture à une position donnée.

    Corps JSON attendu :
        seconds (int | float) : position cible en secondes depuis le début de la piste
                                (défaut : 0)

    Retourne un JSON :
        success (bool) : True si le seek a réussi
        status  (dict) : état complet du lecteur (voir get_status())
        message (str)  : message d'erreur si success est False
    """
    data = request.get_json()
    seconds = data.get("seconds", 0)

    try:
        youtube_client.seek(seconds)

        return jsonify({
            "success": True,
            "status": youtube_client.get_status()
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

@app.route("/api/stop", methods=["POST"])
def api_stop():
    """Arrête complètement la lecture en cours.

    Retourne un JSON :
        success (bool) : True si l'arrêt a réussi
        status  (dict) : état complet du lecteur (voir get_status())
        message (str)  : message d'erreur si success est False
    """
    try:
        youtube_client.stop()

        return jsonify({
            "success": True,
            "status": youtube_client.get_status()
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
