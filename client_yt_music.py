"""
YouTube Music Client - L.A.S.E.R
Lecteur audio YouTube avec streaming VLC.
"""

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
import static_ffmpeg
import contextlib
import io
import os
import random
import urllib.parse
import time
import threading

vlc_path = os.path.join(os.getcwd(), "vlc_files")
os.environ["PATH"] += os.pathsep + vlc_path

import vlc


class YouTubeMusicClient:
    """Client YouTube Music avec streaming VLC.

    Fournit recherche, lecture, téléchargement et gestion de playlist via yt-dlp + VLC.
    """

    def __init__(self):
        """Initialise l'instance VLC, le lecteur audio et tous les états internes.

        Crée un thread de surveillance en arrière-plan pour détecter la fin des pistes
        et passer automatiquement à la suivante.
        """
        vlc_args = [
            "--no-video",
            "--aout=pulse",
            "--audio-filter=",
        ]

        self._vlc_instance = vlc.Instance(vlc_args)
        try:
            self._vlc_instance.log_unset()
        except Exception:
            pass
        self._player = self._vlc_instance.media_player_new()

        self._playlist = []          # liste de dicts {title, artist, url, cover, webpage_url}
        self._current_index = 0      # index de la piste en cours
        self._volume = 80            # volume initial (0-100)
        self._shuffle = False        # mode aléatoire
        self._repeat = False         # mode répétition
        self._last_search_query = ""

        self._is_changing_track = False  # verrou pour éviter les changements simultanés
        self._manual_stop = False        # True si l'arrêt vient de l'utilisateur
        self._is_paused = False          # True si la lecture est en pause

        self._event_manager = self._player.event_manager()
        self._event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_end_reached)

        self._monitor_thread = threading.Thread(target=self._monitor_playback, daemon=True)
        self._monitor_thread.start()

    def __del__(self):
        """Libère proprement les ressources VLC à la destruction de l'objet."""
        try:
            self._player.stop()
            self._player.release()
            self._vlc_instance.release()
        except Exception:
            pass

    def search_and_play(self, query: str) -> str:
        """Recherche une piste sur YouTube et la joue immédiatement.

        :param query: terme de recherche (str), ex. "daft punk harder better faster"
        :return: titre de la piste trouvée (str)
        """
        track = self._fetch_info(query)
        self._playlist.append(track)
        self._current_index = len(self._playlist) - 1
        self._manual_stop = False
        self._is_paused = False
        self._play_url(track["url"])
        return track.get("title", "Titre inconnu")

    def search_and_queue(self, query: str) -> str:
        """Recherche une piste sur YouTube et l'ajoute à la fin de la playlist sans la jouer.

        :param query: terme de recherche (str), ex. "daft punk harder better faster"
        :return: titre de la piste ajoutée (str)
        """
        track = self._fetch_info(query)
        self._playlist.append(track)
        return track.get("title", "Titre inconnu")

    def search_playlist_and_play(self, query: str) -> tuple:
        """Recherche une playlist YouTube, charge ses pistes (lazy) et joue la première.

        Les URLs audio des pistes sont résolues à la demande (lazy loading) pour éviter
        de tout télécharger d'un coup.

        :param query: terme de recherche pour trouver la playlist (str)
        :return: tuple (titre_playlist: str, nombre_de_pistes: int)
        :raises ValueError: si aucune piste n'est trouvée
        """
        playlist_title, tracks = self._fetch_playlist_videos(query)
        if not tracks:
            raise ValueError("Aucune piste trouvée dans la playlist")

        start_index = len(self._playlist)
        for title, video_url in tracks:
            self._playlist.append({"title": title, "url": None, "video_url": video_url})

        self._current_index = start_index
        self._play_current_track()
        return playlist_title, len(tracks)

    def _fetch_playlist_videos(self, query: str) -> tuple:
        """Recherche une playlist YouTube et retourne la liste de ses vidéos.

        Effectue deux requêtes yt-dlp : une pour trouver la playlist, une pour lister ses vidéos.

        :param query: terme de recherche pour trouver la playlist (str)
        :return: tuple (titre_playlist: str, liste de (titre, url_video))
        :raises ValueError: si aucune playlist ou vidéo n'est trouvée
        """
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}&sp=EgIQAw%3D%3D"

        flat_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "playlistend": 50,
        }

        with YoutubeDL(flat_opts) as ydl:
            search_results = ydl.extract_info(search_url, download=False)

        if not search_results or not search_results.get("entries"):
            raise ValueError("Aucune playlist trouvée pour cette recherche")

        first_result = search_results["entries"][0]
        playlist_url = first_result.get("url") or first_result.get("webpage_url", "")
        playlist_id = first_result.get("id", "")
        if playlist_id and not playlist_url.startswith("http"):
            playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
        playlist_title = first_result.get("title", query)

        tracks = []
        tracks_opts = {"quiet": True, "no_warnings": True, "extract_flat": True}
        with YoutubeDL(tracks_opts) as ydl:
            playlist_data = ydl.extract_info(playlist_url, download=False)

        if not playlist_data:
            raise ValueError("Impossible d'extraire les données de la playlist")

        for entry in playlist_data.get("entries") or []:
            if not entry:
                continue
            title = entry.get("title", "Titre inconnu")
            video_id = entry.get("id", "")
            video_url = entry.get("url") or entry.get("webpage_url", "")
            if video_id and not (video_url and video_url.startswith("http")):
                video_url = f"https://www.youtube.com/watch?v={video_id}"
            if video_url:
                tracks.append((title, video_url))

        if not tracks:
            raise ValueError("La playlist est vide ou inaccessible")

        return playlist_title, tracks

    def _resolve_audio_url(self, video_url: str) -> str:
        """Résout l'URL directe du flux audio à partir d'une URL de vidéo YouTube.

        Utilisé pour le lazy loading des pistes de playlist dont seule l'URL vidéo est connue.

        :param video_url: URL complète de la vidéo YouTube (str)
        :return: URL directe du flux audio (str)
        :raises ValueError: si aucun format audio n'est disponible
        """
        ydl_opts = {"format": "bestaudio[ext=m4a]/bestaudio/best", "quiet": True, "no_warnings": True}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        if not info:
            raise ValueError(f"Impossible d'extraire l'audio : {video_url}")

        audio_url = info.get("url")
        if not audio_url:
            audio_formats = [f for f in info.get("formats", []) if f.get("acodec") != "none" and f.get("url")]
            if not audio_formats:
                raise ValueError("Aucun format audio disponible")
            best_format = max(audio_formats, key=lambda f: f.get("abr") or f.get("tbr") or f.get("quality") or 0)
            audio_url = best_format["url"]

        return audio_url

    def _play_current_track(self):
        """Lance la lecture de la piste à l'index courant (_current_index).

        Résout l'URL audio si nécessaire (lazy loading pour les playlists).
        """
        track = self._playlist[self._current_index]
        if not track.get("url"):
            if not track.get("video_url"):
                raise ValueError("Aucune URL disponible pour cette piste")
            track["url"] = self._resolve_audio_url(track["video_url"])
        self._play_url(track["url"])

    def _fetch_info(self, query: str) -> dict:
        """Recherche une piste sur YouTube via yt-dlp et retourne ses métadonnées + URL audio.

        :param query: terme de recherche (str)
        :return: dict avec les clés : title (str), artist (str), url (str), cover (str), webpage_url (str)
        :raises ValueError: si aucune piste n'est trouvée ou aucun format audio disponible
        """
        ydl_opts = {"format": "bestaudio[ext=m4a]/bestaudio/best", "quiet": True, "no_warnings": True, "noplaylist": True}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)

            if not info or not info.get("entries"):
                raise ValueError("Aucune musique trouvée")

            entry = info["entries"][0]

            audio_url = entry.get("url")
            if not audio_url:
                audio_formats = [f for f in entry.get("formats", []) if f.get("acodec") != "none" and f.get("url")]
                if not audio_formats:
                    raise ValueError("Aucun format audio disponible")
                best_format = max(audio_formats, key=lambda f: f.get("abr") or f.get("tbr") or f.get("quality") or 0)
                audio_url = best_format["url"]

            return {
                "title": entry.get("title", "Titre inconnu"),
                "artist": entry.get("uploader", "YouTube"),
                "url": audio_url,
                "cover": entry.get("thumbnail", ""),
                "webpage_url": entry.get("webpage_url", ""),
            }

    def download_audio(self, query, output_path="%(title)s.%(ext)s"):
        """Télécharge une piste YouTube en MP3 sur le disque.

        :param query: terme de recherche ou URL YouTube (str)
        :param output_path: modèle de nom de fichier de sortie (str),
                            utilise la syntaxe yt-dlp (défaut : "%(title)s.%(ext)s")
        :return: titre de la piste téléchargée (str | None)
        :raises RuntimeError: si le téléchargement échoue
        """
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            static_ffmpeg.add_paths()

        def _progress_hook(d):
            if d["status"] == "downloading":
                percent = d.get("_percent_str", "").strip()
                print(f"\rTéléchargement... {percent}", end="", flush=True)
            elif d["status"] == "finished":
                print("\rTéléchargement... 100%           ")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [_progress_hook],
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "retries": 10,
            "fragment_retries": 10,
            "http_chunk_size": 1048576,
            "socket_timeout": 30,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            },
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch:{query}", download=True)

                if not info or not info.get("entries"):
                    raise ValueError("Aucune musique trouvée")

                return info["entries"][0].get("title")

        except DownloadError as e:
            raise RuntimeError(f"Échec du téléchargement : {e}") from e

    def _play_url(self, url: str):
        """Crée un média VLC depuis une URL et lance la lecture immédiatement.

        :param url: URL directe du flux audio (str)
        """
        self._manual_stop = False
        self._is_paused = False

        self._player.stop()

        media = self._vlc_instance.media_new(url)
        self._player.set_media(media)

        try:
            self._player.audio_set_volume(self._volume)
        except Exception as e:
            print(f"[YouTube] Warning volume : {e}")

        self._player.play()

    def play(self, index=None):
        """Démarre ou reprend la lecture.

        :param index: index de la piste à jouer dans la playlist (int, 0-based).
                      Si None, reprend la piste en pause ou continue la lecture en cours.
        :raises ValueError: si la playlist est vide
        :raises IndexError: si l'index est hors limites
        """
        if not self._playlist:
            raise ValueError("Playlist vide")

        self._manual_stop = False

        if index is not None:
            index = int(index)
            if index < 0 or index >= len(self._playlist):
                raise IndexError("Index invalide")
            self._is_paused = False
            self._current_index = index
            self._play_url(self._playlist[self._current_index]["url"])
            return

        if self._is_paused:
            self._is_paused = False
            self._player.play()
            return

        self._player.play()

    def pause(self):
        """Bascule entre pause et lecture (toggle play/pause)."""
        self._player.pause()
        self._is_paused = not self._is_paused

    def stop(self):
        """Arrête complètement la lecture et réinitialise les flags d'état."""
        self._manual_stop = True
        self._is_paused = False
        self._player.stop()

    def next_track(self):
        """Passe à la piste suivante dans la playlist.

        En mode shuffle, choisit une piste aléatoire différente de la piste actuelle.
        En mode normal, avance d'un index et revient au début si on est à la fin.
        """
        if not self._playlist:
            return

        if self._shuffle and len(self._playlist) > 1:
            old_index = self._current_index
            while self._current_index == old_index:
                self._current_index = random.randint(0, len(self._playlist) - 1)
        else:
            self._current_index += 1
            if self._current_index >= len(self._playlist):
                self._current_index = 0

        self._play_url(self._playlist[self._current_index]["url"])

    def previous_track(self):
        """Revient à la piste précédente dans la playlist.

        Revient à la dernière piste si on est déjà à la première (comportement cyclique).
        """
        if not self._playlist:
            return

        self._current_index -= 1
        if self._current_index < 0:
            self._current_index = len(self._playlist) - 1

        self._play_url(self._playlist[self._current_index]["url"])

    def set_volume(self, volume):
        """Définit le volume de lecture.

        :param volume: entier entre 0 (muet) et 100 (maximum). Valeur clampée automatiquement.
        """
        self._volume = max(0, min(100, int(volume)))
        try:
            self._player.audio_set_volume(self._volume)
        except Exception:
            pass

    def get_volume(self):
        """Retourne le volume actuel.

        :return: volume (int) entre 0 et 100
        """
        return self._volume

    def toggle_shuffle(self):
        """Active ou désactive le mode lecture aléatoire.

        :return: nouvel état du shuffle (bool) : True si activé, False sinon
        """
        self._shuffle = not self._shuffle
        return self._shuffle

    def toggle_repeat(self):
        """Active ou désactive le mode répétition de la piste en cours.

        :return: nouvel état du repeat (bool) : True si activé, False sinon
        """
        self._repeat = not self._repeat
        return self._repeat

    def get_current_track_name(self):
        """Retourne le titre de la piste en cours de lecture.

        :return: titre de la piste (str), ou "Aucune piste" si la playlist est vide
        """
        if not self._playlist:
            return "Aucune piste"
        return self._playlist[self._current_index]["title"]

    def get_current_index(self):
        """Retourne l'index (0-based) de la piste en cours.

        :return: index courant (int)
        """
        return self._current_index

    def get_playlist(self):
        """Retourne la liste des titres de toutes les pistes de la playlist.

        :return: liste de titres (list[str])
        """
        return [track["title"] for track in self._playlist]

    def get_playlist_full(self):
        """Retourne la playlist complète avec toutes les métadonnées de chaque piste.

        :return: liste de dicts, chaque dict contenant : title, artist, url, cover, webpage_url
        """
        return self._playlist

    def get_duration(self):
        """Retourne la durée totale de la piste en cours en secondes.

        :return: durée en secondes (int), ou 0 si non disponible (piste non encore chargée)
        """
        length_ms = self._player.get_length()
        return length_ms // 1000 if length_ms and length_ms > 0 else 0

    def get_position(self):
        """Retourne la position de lecture actuelle en secondes.

        :return: position en secondes (int), ou 0 si aucune piste en cours
        """
        time_ms = self._player.get_time()
        return time_ms // 1000 if time_ms and time_ms > 0 else 0

    def seek(self, seconds):
        """Déplace la tête de lecture à une position donnée.

        :param seconds: position cible en secondes depuis le début de la piste (int | float)
        """
        self._manual_stop = False
        self._is_paused = False
        self._player.set_time(int(seconds) * 1000)

    def is_playing(self):
        """Indique si le lecteur est actuellement en train de lire.

        :return: True si en lecture, False sinon (bool)
        """
        return bool(self._player.is_playing())

    def get_status(self):
        """Retourne un dictionnaire récapitulatif de l'état complet du lecteur.

        :return: dict avec les clés :
            mode       (str)  : toujours "youtube"
            track      (str)  : titre de la piste en cours
            artist     (str)  : nom de l'artiste
            cover      (str)  : URL de la miniature YouTube
            webpage_url(str)  : URL de la page YouTube de la piste
            index      (int)  : numéro de la piste (1-based)
            total      (int)  : nombre total de pistes dans la playlist
            playing    (bool) : True si en lecture
            volume     (int)  : volume actuel (0-100)
            shuffle    (bool) : True si le mode aléatoire est actif
            repeat     (bool) : True si le mode répétition est actif
            position   (int)  : position en secondes
            duration   (int)  : durée totale en secondes
            playlist   (list) : liste complète des pistes
        """
        if self._playlist:
            current_track = self._playlist[self._current_index]
        else:
            current_track = None

        return {
            "mode": "youtube",
            "track": current_track["title"] if current_track else "Aucune piste",
            "artist": current_track["artist"] if current_track else "",
            "cover": current_track["cover"] if current_track else "",
            "webpage_url": current_track["webpage_url"] if current_track else "",
            "index": self._current_index + 1 if self._playlist else 0,
            "total": len(self._playlist),
            "playing": self.is_playing(),
            "volume": self._volume,
            "shuffle": self._shuffle,
            "repeat": self._repeat,
            "position": self.get_position(),
            "duration": self.get_duration(),
            "playlist": self._playlist,
        }

    def _auto_add_related_track(self):
        """Cherche et ajoute automatiquement une piste liée à celle en cours (autoplay).

        Utilisé quand la playlist est épuisée pour éviter le silence.
        Filtre les compilations et vidéos trop longues (> 10 minutes).

        :return: True si une piste a été ajoutée, False sinon (bool)
        """
        if not self._playlist:
            return False

        try:
            current_track = self._playlist[self._current_index]
            current_title = current_track.get("title", "")
            current_artist = current_track.get("artist", "")

            related_queries = [
                f"{current_artist} popular songs",
                f"{current_artist} official music video",
                f"{current_artist} hits",
                f"songs like {current_title} {current_artist}",
            ]

            blocked_words = [
                "full album",
                "album complet",
                "playlist complète",
                "compilation",
                "1 hour",
                "2 hours",
                "one hour",
                "two hours",
            ]

            existing_urls = [item.get("webpage_url") for item in self._playlist]

            for q in related_queries:
                with YoutubeDL({
                    "format": "bestaudio[ext=m4a]/bestaudio/best",
                    "quiet": True,
                    "no_warnings": True,
                    "noplaylist": True,
                }) as ydl:
                    info = ydl.extract_info(f"ytsearch15:{q}", download=False)

                    if not info or not info.get("entries"):
                        continue

                    for entry in info["entries"]:
                        title = entry.get("title", "")
                        title_lower = title.lower()
                        webpage_url = entry.get("webpage_url", "")
                        duration = entry.get("duration") or 0

                        if not title or not webpage_url:
                            continue

                        if webpage_url in existing_urls:
                            continue

                        if duration and duration > 600:
                            continue

                        if any(word in title_lower for word in blocked_words):
                            continue

                        audio_url = entry.get("url")
                        if not audio_url:
                            continue

                        track = {
                            "title": entry.get("title", "Titre inconnu"),
                            "artist": entry.get("uploader", "YouTube"),
                            "url": audio_url,
                            "cover": entry.get("thumbnail", ""),
                            "webpage_url": webpage_url,
                        }

                        self._playlist.append(track)
                        print("[AUTOPLAY] Ajout automatique :", track["title"])
                        return True

            print("[AUTOPLAY] Aucun résultat correct trouvé")
            return False

        except Exception as error:
            print("[AUTOPLAY] Erreur :", error)
            return False

    def _go_to_next_or_repeat(self):
        """Gère la transition de piste en fin de lecture.

        En mode repeat, rejoue la piste en cours.
        Sinon, passe à la suivante ou tente un autoplay si la playlist est terminée.
        Utilise un verrou (_is_changing_track) pour éviter les appels simultanés.
        """
        if self._is_changing_track:
            return

        self._is_changing_track = True
        try:
            if not self._playlist:
                return

            if self._repeat:
                current_track = self._playlist[self._current_index]
                self._manual_stop = False
                self._is_paused = False
                self._play_url(current_track["url"])
                return

            if self._current_index < len(self._playlist) - 1:
                self.next_track()
            else:
                added = self._auto_add_related_track()
                if added:
                    self.next_track()
                else:
                    self.stop()

        finally:
            time.sleep(1)
            self._is_changing_track = False

    def _on_end_reached(self, event):
        """Callback VLC déclenché automatiquement quand une piste se termine.

        :param event: événement VLC (vlc.Event), non utilisé directement
        """
        if self._manual_stop or self._is_paused:
            return
        self._go_to_next_or_repeat()

    def _monitor_playback(self):
        """Thread de surveillance en arrière-plan qui vérifie l'avancement de la lecture.

        Déclenche le passage à la piste suivante si la piste est presque terminée
        ou si la lecture semble bloquée (position figée en fin de piste).
        Tourne en boucle infinie (thread daemon, s'arrête avec le programme).
        """
        last_position = 0
        stuck_counter = 0

        while True:
            time.sleep(1)
            try:
                if self._manual_stop or self._is_paused:
                    continue
                if not self._playlist:
                    continue
                duration = self.get_duration()
                position = self.get_position()
                if duration <= 0:
                    continue
                if position >= duration - 5:
                    self._go_to_next_or_repeat()
                    continue
                if position == last_position and position >= duration - 10:
                    stuck_counter += 1
                    if stuck_counter >= 2:
                        self._go_to_next_or_repeat()
                        stuck_counter = 0
                        continue
                else:
                    stuck_counter = 0
                last_position = position
            except Exception as error:
                print(f"[YouTube monitor] Erreur : {error}")
