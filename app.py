from flask import Flask, render_template, jsonify, request
import os

app = Flask(__name__)

MUSIC_FOLDER = "./musiques"
player = None


# =========================
# PAGE PRINCIPALE
# =========================
@app.route("/")
def home():
    return render_template("index.html")


# =========================
# INITIALISER LE PLAYER
# =========================
def init_player():
    global player

    if player is None:
        from player import MusicPlayer
        player = MusicPlayer()


# =========================
# CHARGER LES MP3
# =========================
@app.route("/api/load", methods=["POST"])
def load_music():
    global player

    try:
        init_player()

        if not os.path.isdir(MUSIC_FOLDER):
            return jsonify({"success": False, "message": "Dossier musiques introuvable"}), 400

        count = player.load_folder(MUSIC_FOLDER)

        if count == 0:
            return jsonify({"success": False, "message": "Aucun MP3 trouvé"}), 400

        player.play(0)

        return jsonify({
            "success": True,
            "status": {
                **player.get_status(),
                "playlist": player.get_playlist()
            }
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# =========================
# PLAY
# =========================
@app.route("/api/play", methods=["POST"])
def play():
    init_player()

    data = request.get_json(silent=True) or {}
    index = data.get("index")

    try:
        if index is not None:
            player.play(int(index))
        else:
            player.play()

        return jsonify({
            "success": True,
            "status": {
                **player.get_status(),
                "playlist": player.get_playlist()
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


# =========================
# PAUSE
# =========================
@app.route("/api/pause", methods=["POST"])
def pause():
    init_player()
    player.pause()

    return jsonify({
        "success": True,
        "status": {
            **player.get_status(),
            "playlist": player.get_playlist()
        }
    })


# =========================
# STOP
# =========================
@app.route("/api/stop", methods=["POST"])
def stop():
    init_player()
    player.stop()

    return jsonify({
        "success": True,
        "status": {
            **player.get_status(),
            "playlist": player.get_playlist()
        }
    })


# =========================
# NEXT
# =========================
@app.route("/api/next", methods=["POST"])
def next_music():
    init_player()
    player.next_track()

    return jsonify({
        "success": True,
        "status": {
            **player.get_status(),
            "playlist": player.get_playlist()
        }
    })


# =========================
# PREVIOUS
# =========================
@app.route("/api/prev", methods=["POST"])
def prev_music():
    init_player()
    player.previous_track()

    return jsonify({
        "success": True,
        "status": {
            **player.get_status(),
            "playlist": player.get_playlist()
        }
    })


# =========================
# VOLUME
# =========================
@app.route("/api/volume", methods=["POST"])
def volume():
    init_player()

    data = request.get_json(silent=True) or {}
    player.set_volume(int(data["volume"]))

    return jsonify({
        "success": True,
        "status": {
            **player.get_status(),
            "playlist": player.get_playlist()
        }
    })


# =========================
# SEEK
# =========================
@app.route("/api/seek", methods=["POST"])
def seek():
    init_player()

    data = request.get_json(silent=True) or {}
    player.seek(float(data["seconds"]))

    return jsonify({
        "success": True,
        "status": {
            **player.get_status(),
            "playlist": player.get_playlist()
        }
    })


# =========================
# SHUFFLE
# =========================
@app.route("/api/shuffle", methods=["POST"])
def shuffle():
    init_player()
    player.toggle_shuffle()

    return jsonify({
        "success": True,
        "status": {
            **player.get_status(),
            "playlist": player.get_playlist()
        }
    })


# =========================
# REPEAT
# =========================
@app.route("/api/repeat", methods=["POST"])
def repeat():
    init_player()
    player.toggle_repeat()

    return jsonify({
        "success": True,
        "status": {
            **player.get_status(),
            "playlist": player.get_playlist()
        }
    })


# =========================
# STATUS
# =========================
@app.route("/api/status")
def status():
    if player is None:
        return jsonify({
            "success": True,
            "status": {
                "track": "Aucune piste",
                "index": 0,
                "total": 0,
                "playing": False,
                "volume": 80,
                "shuffle": False,
                "repeat": False,
                "position": 0,
                "duration": 0,
                "playlist": []
            }
        })

    return jsonify({
        "success": True,
        "status": {
            **player.get_status(),
            "playlist": player.get_playlist()
        }
    })


if __name__ == "__main__":
    app.run(debug=False)