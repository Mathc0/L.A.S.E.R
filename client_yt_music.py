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
import time

vlc_path = os.path.join(os.getcwd(), "vlc_files")
os.environ["PATH"] += os.pathsep + vlc_path

import vlc


class YouTubeMusicClient:
    """
    Client YouTube Music avec streaming VLC.
    """

    def __init__(self):
        vlc_args = [
            "--no-video",
            "--aout=pulse",
            "--audio-filter=",
        ]

        self._vlc_instance = vlc.Instance(vlc_args)
        self._player = self._vlc_instance.media_player_new()

        self._playlist = []
        self._current_index = 0
        self._volume = 80
        self._shuffle = False
        self._repeat = False

        self._event_manager = self._player.event_manager()
        self._event_manager.event_attach(
            vlc.EventType.MediaPlayerEndReached,
            self._on_end_reached
        )

    def __del__(self):
        try:
            self._player.stop()
            self._player.release()
            self._vlc_instance.release()
        except Exception:
            pass

    def search_and_play(self, query: str) -> dict:
        """
        Recherche une musique YouTube,
        l'ajoute à la playlist,
        puis lance la lecture.
        """

        track = self._fetch_info(query)

        self._playlist.append(track)
        self._current_index = len(self._playlist) - 1

        self._play_url(track["url"])

        return track

    def search_and_queue(self, query: str) -> dict:
        """
        Recherche une musique YouTube
        et l'ajoute à la playlist sans la lire.
        """

        track = self._fetch_info(query)

        self._playlist.append(track)

        return track

    def _fetch_info(self, query: str) -> dict:
        """
        Recherche une musique sur YouTube avec yt-dlp.

        On récupère :
        - le titre
        - l'artiste / chaîne YouTube
        - l'URL audio
        - la miniature YouTube pour la jaquette
        - le lien de la vidéo
        """

        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                f"ytsearch1:{query}",
                download=False
            )

            if not info or not info.get("entries"):
                raise ValueError("Aucune musique trouvée")

            entry = info["entries"][0]

            audio_url = entry.get("url")

            if not audio_url:
                audio_formats = [
                    f for f in entry.get("formats", [])
                    if f.get("acodec") != "none" and f.get("url")
                ]

                if not audio_formats:
                    raise ValueError("Aucun format audio disponible")

                best_format = max(
                    audio_formats,
                    key=lambda f:
                        f.get("abr")
                        or f.get("tbr")
                        or f.get("quality")
                        or 0
                )

                audio_url = best_format["url"]

            track = {
                "title": entry.get("title", "Titre inconnu"),
                "artist": entry.get("uploader", "YouTube"),
                "url": audio_url,
                "cover": entry.get("thumbnail", ""),
                "webpage_url": entry.get("webpage_url", "")
            }

            return track

    def download_audio(self, query, output_path="%(title)s.%(ext)s"):
        """
        Télécharge l'audio de la première vidéo YouTube trouvée.
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
                info = ydl.extract_info(
                    f"ytsearch:{query}",
                    download=True
                )

                if not info or not info.get("entries"):
                    raise ValueError("Aucune musique trouvée")

                return info["entries"][0].get("title")

        except DownloadError as e:
            raise RuntimeError(f"Échec du téléchargement : {e}") from e

    def _play_url(self, url: str):
        """
        Lance la lecture d'une URL audio avec VLC.
        """

        self._player.stop()

        media = self._vlc_instance.media_new(url)
        self._player.set_media(media)

        try:
            self._player.audio_set_volume(self._volume)
        except Exception as e:
            print(f"[YouTube] Warning volume : {e}")

        self._player.play()

    def play(self, index=None):
        """
        Lance ou reprend la lecture.
        """

        if not self._playlist:
            raise ValueError("Playlist vide")

        if index is not None:
            if index < 0 or index >= len(self._playlist):
                raise IndexError("Index invalide")

            self._current_index = index
            self._play_url(self._playlist[self._current_index]["url"])
            return

        self._player.play()

    def pause(self):
        """
        Met en pause ou reprend la lecture.
        """

        self._player.pause()

    def stop(self):
        """
        Arrête la lecture.
        """

        self._player.stop()

    def next_track(self):
        """
        Passe à la musique suivante.
        """

        if not self._playlist:
            return

        if self._shuffle:
            self._current_index = random.randint(
                0,
                len(self._playlist) - 1
            )
        else:
            self._current_index += 1

            if self._current_index >= len(self._playlist):
                if self._repeat:
                    self._current_index = 0
                else:
                    self._current_index = len(self._playlist) - 1
                    self.stop()
                    return

        self._play_url(
            self._playlist[self._current_index]["url"]
        )

    def previous_track(self):
        """
        Revient à la musique précédente.
        """

        if not self._playlist:
            return

        self._current_index -= 1

        if self._current_index < 0:
            if self._repeat:
                self._current_index = len(self._playlist) - 1
            else:
                self._current_index = 0

        self._play_url(
            self._playlist[self._current_index]["url"]
        )

    def set_volume(self, volume):
        """
        Change le volume entre 0 et 100.
        """

        self._volume = max(0, min(100, int(volume)))
        self._player.audio_set_volume(self._volume)

    def get_volume(self):
        return self._volume

    def toggle_shuffle(self):
        self._shuffle = not self._shuffle
        return self._shuffle

    def toggle_repeat(self):
        self._repeat = not self._repeat
        return self._repeat

    def get_current_track_name(self):
        if not self._playlist:
            return "Aucune piste"

        return self._playlist[self._current_index]["title"]

    def get_current_index(self):
        return self._current_index

    def get_playlist(self):
        return [track["title"] for track in self._playlist]

    def get_playlist_full(self):
        """
        Retourne la playlist complète avec les jaquettes.
        """

        return self._playlist

    def get_duration(self):
        length_ms = self._player.get_length()

        if length_ms <= 0:
            return 0

        return length_ms // 1000

    def get_position(self):
        time_ms = self._player.get_time()

        if time_ms <= 0:
            return 0

        return time_ms // 1000

    def seek(self, seconds):
        self._player.set_time(int(seconds) * 1000)

    def is_playing(self):
        return bool(self._player.is_playing())

    def get_status(self):
        """
        Retourne les infos utiles pour l'interface web.
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

    def _on_end_reached(self, event):
        """
        Quand une musique se termine,
        VLC appelle automatiquement cette fonction.
        """

        is_last_track = self._current_index == len(self._playlist) - 1

        if not is_last_track:
            self.next_track()
        elif self._repeat:
            self.next_track()
