from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from client_yt_music import YouTubeMusicClient

import os
import time
import threading
import webbrowser
from player import MusicPlayer
try:
    from db import init_db
except Exception:
    init_db = None

app = Flask(__name__)
CORS(app)

# On crée le client YouTube une seule fois
youtube_client = YouTubeMusicClient()
local_player = None
active_source = "youtube"

# Configuration de démarrage (fusion avec startup.py)
HOST = "127.0.0.1"
PORT = 5000
URL = f"http://{HOST}:{PORT}"
MUSIC_FOLDER = "./musiques"


def open_browser(delay: float = 2.0):
    time.sleep(delay)
    try:
        print(f"🌐 Ouverture de {URL} dans le navigateur...")
        webbrowser.open(URL)
    except Exception:
        pass


def init_music_player():
    global local_player
    print("🎵 Initialisation du lecteur de musique...")
    if not os.path.exists(MUSIC_FOLDER):
        try:
            os.makedirs(MUSIC_FOLDER, exist_ok=True)
            print(f"📁 Dossier {MUSIC_FOLDER} créé")
        except Exception:
            pass
    local_player = MusicPlayer(music_folder=MUSIC_FOLDER)
    print("✅ Lecteur de musique initialisé avec succès")
    return local_player


def set_active_source(source: str):
    global active_source
    if source in ("youtube", "local"):
        active_source = source


def stop_other_source(source: str):
    if source == "local":
        try:
            youtube_client.stop()
        except Exception:
            pass
    elif source == "youtube" and local_player is not None:
        try:
            local_player.stop()
        except Exception:
            pass


def get_current_status():
    if active_source == "local" and local_player is not None:
        return {
            "mode": "local",
            "track": local_player.get_current_track_name(),
            "index": local_player.get_current_index() + 1,
            "total": len(local_player.get_playlist()),
            "playing": local_player.is_playing(),
            "volume": local_player.get_volume(),
            "shuffle": local_player._shuffle,
            "repeat": local_player._repeat,
            "position": local_player.get_position(),
            "duration": local_player.get_duration(),
            "playlist": local_player.get_playlist(show_path=True)
        }
    return youtube_client.get_status()


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
        stop_other_source("youtube")
        set_active_source("youtube")
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
            stop_other_source("youtube")
            set_active_source("youtube")
            youtube_client.play(int(index))
            return jsonify({
                "success": True,
                "status": youtube_client.get_status()
            })

        if active_source == "local" and local_player is not None:
            local_player.play()
            return jsonify({
                "success": True,
                "status": get_current_status()
            })

        stop_other_source("youtube")
        set_active_source("youtube")
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
        if active_source == "local" and local_player is not None:
            local_player.pause()
            return jsonify({
                "success": True,
                "status": get_current_status()
            })

        youtube_client.pause()
        set_active_source("youtube")
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
        "status": get_current_status()
    })


@app.route("/api/library")
def api_library():
    from db import SessionLocal
    from models import Track
    
    audio_exts = (".mp3", ".flac", ".wav", ".m4a", ".aac", ".ogg")
    tracks = []
    index = 0
    
    # Charger les musiques locales
    if os.path.isdir(MUSIC_FOLDER):
        for root, dirs, files in os.walk(MUSIC_FOLDER):
            for filename in sorted(files):
                if not filename.lower().endswith(audio_exts):
                    continue

                full_path = os.path.join(root, filename)
                title = os.path.splitext(filename)[0]
                rel_path = os.path.relpath(full_path, start=MUSIC_FOLDER)
                parts = rel_path.split(os.sep)
                artist = ""
                album = ""
                if len(parts) >= 3:
                    artist = parts[0]
                    album = parts[1]
                elif len(parts) == 2:
                    artist = parts[0]

                tracks.append({
                    "title": title,
                    "artist": artist,
                    "album": album,
                    "duration": 0,
                    "source": "local",
                    "backendIndex": index
                })
                index += 1
    
    # Charger aussi les musiques YouTube de la DB avec leurs métadonnées correctes
    try:
        session = SessionLocal()
        youtube_tracks = session.query(Track).filter(
            Track.path.like('%youtube.com%')
        ).all()
        
        for track in youtube_tracks:
            tracks.append({
                "title": track.title or "Unknown",
                "artist": track.artist or "Unknown Artist",
                "album": track.album or "YouTube",
                "duration": track.duration or 0,
                "source": "youtube",
                "path": track.path,
                "play_count": track.play_count or 0,
                "last_played": track.last_played.isoformat() if track.last_played else None
            })
        session.close()
    except Exception as e:
        print(f"⚠️  Erreur lors de la récupération des musiques YouTube : {e}")

    return jsonify({
        "success": True,
        "tracks": tracks
    })


@app.route("/api/local_play", methods=["POST"])
def api_local_play():
    if local_player is None:
        return jsonify({
            "success": False,
            "message": "Lecteur local non initialisé"
        }), 500

    data = request.get_json(silent=True) or {}
    index = data.get("index")
    if index is None:
        return jsonify({
            "success": False,
            "message": "Index local manquant"
        }), 400

    if index < 0 or index >= len(local_player.get_playlist()):
        return jsonify({
            "success": False,
            "message": "Index local invalide"
        }), 400

    try:
        stop_other_source("local")
        set_active_source("local")
        local_player.play(int(index))
        return jsonify({
            "success": True,
            "status": get_current_status()
        })
    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


@app.route("/api/next", methods=["POST"])
def api_next():
    try:
        if active_source == "local" and local_player is not None:
            local_player.next_track()
            return jsonify({
                "success": True,
                "status": get_current_status()
            })

        youtube_client.next_track()
        set_active_source("youtube")
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
        if active_source == "local" and local_player is not None:
            local_player.previous_track()
            return jsonify({
                "success": True,
                "status": get_current_status()
            })

        youtube_client.previous_track()
        set_active_source("youtube")
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
        if active_source == "local" and local_player is not None:
            local_player.toggle_shuffle()
            return jsonify({
                "success": True,
                "status": get_current_status()
            })

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
        if active_source == "local" and local_player is not None:
            local_player.toggle_repeat()
            return jsonify({
                "success": True,
                "status": get_current_status()
            })

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
        if active_source == "local" and local_player is not None:
            local_player.seek(seconds)
            return jsonify({
                "success": True,
                "status": get_current_status()
            })

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
        if active_source == "local" and local_player is not None:
            local_player.stop()
            return jsonify({
                "success": True,
                "status": get_current_status()
            })

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


@app.route("/api/youtube/playlist", methods=["GET"])
def api_youtube_playlist():
    """Retourne la playlist YouTube avec les métadonnées correctes."""
    try:
        playlist = youtube_client.get_playlist_full()
        
        if not playlist:
            return jsonify({
                "success": True,
                "tracks": [],
                "total": 0
            })
        
        tracks = []
        for i, track in enumerate(playlist):
            tracks.append({
                "index": i,
                "title": track.get("title", "Unknown"),
                "artist": track.get("artist", "Unknown Artist"),
                "album": track.get("channel", "YouTube"),
                "cover": track.get("cover", ""),
                "duration": track.get("duration", 0),
                "url": track.get("webpage_url", ""),
                "source": "youtube"
            })
        
        return jsonify({
            "success": True,
            "tracks": tracks,
            "total": len(tracks),
            "current_index": youtube_client.get_current_index()
        })
    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


@app.route("/api/youtube/sync", methods=["POST"])
def api_youtube_sync():
    """Synchronise les métadonnées de toutes les musiques YouTube de la DB."""
    try:
        synced, total = youtube_client.sync_youtube_metadata()
        return jsonify({
            "success": True,
            "synced": synced,
            "total": total,
            "message": f"Synchronisation terminée : {synced}/{total} musiques YouTube mises à jour"
        })
    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


@app.route("/api/youtube/metadata", methods=["POST"])
def api_youtube_metadata():
    """Met à jour les métadonnées d'une musique YouTube."""
    try:
        from mp3_tagger import tag_youtube_track
        
        data = request.get_json()
        path = data.get("path")
        title = data.get("title")
        artist = data.get("artist")
        album = data.get("album", "YouTube")
        
        if not path or not title or not artist:
            return jsonify({
                "success": False,
                "message": "Paramètres manquants (path, title, artist requis)"
            }), 400
        
        if tag_youtube_track(path, title, artist, album):
            return jsonify({
                "success": True,
                "message": f"Métadonnées mises à jour : {title} par {artist}"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Erreur lors de la mise à jour des métadonnées"
            }), 500
            
    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


def start_flask_server():
    print(f"🚀 Démarrage du serveur Flask sur {URL}")
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


def main():
    print("=" * 60)
    print("╔════════════════════════════════════════════════════════╗")
    print("║          L.A.S.E.R - Interface Web                   ║")
    print("║          Démarrage complet du système                 ║")
    print("╚════════════════════════════════════════════════════════╝")
    print("=" * 60)

    # Initialiser la base de données (si configurée)
    if init_db:
        try:
            init_db()
            print("✅ Base de données initialisée")
        except Exception as e:
            print(f"⚠️  Échec initialisation DB : {e}")

    # Initialiser le lecteur local
    player = init_music_player()

    # Ouvrir le navigateur dans un thread séparé
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    print("\n📝 Commandes disponibles:")
    print("   - Ouvrez http://127.0.0.1:5000 dans votre navigateur")
    print("   - Appuyez sur Ctrl+C pour arrêter le serveur")
    print("=" * 60 + "\n")

    try:
        start_flask_server()
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du serveur...")


if __name__ == "__main__":
    main()