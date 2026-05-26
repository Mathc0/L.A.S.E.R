from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from client_yt_music import YouTubeMusicClient

app = Flask(__name__)
CORS(app)

# On crée le client YouTube une seule fois
youtube_client = YouTubeMusicClient()


@app.route("/")
def home():
    return send_from_directory("interface_test", "index.html")


@app.route("/style.css")
def style():
    return send_from_directory("interface_test", "style.css")


@app.route("/script.js")
def script():
    return send_from_directory("interface_test", "script.js")


@app.route("/api/test")
def test():
    return jsonify({
        "success": True,
        "message": "Connexion Python ↔ Interface OK"
    })


@app.route("/api/youtube", methods=["POST"])
def search_youtube():
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
    return jsonify({
        "success": True,
        "status": youtube_client.get_status()
    })


@app.route("/api/next", methods=["POST"])
def api_next():
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