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
<<<<<<< HEAD
import subprocess
import urllib.parse

import platform
=======
import time
import threading
>>>>>>> origin/Emmeline

vlc_path = os.path.join(os.getcwd(), "vlc_files")
os.environ["PATH"] += os.pathsep + vlc_path

import vlc


class YouTubeMusicClient:
    """
    Client YouTube Music avec streaming VLC.
<<<<<<< HEAD

    Fonctionnalités :
      - Rechercher et ajouter des pistes YouTube dans une playlist
      - Play / Pause / Stop
      - Piste suivante / précédente
      - Contrôle du volume (0-100)
      - Mode aléatoire (shuffle)
      - Mode répétition (repeat)
      - Seek (déplacement dans la piste)
      - Récupérer les infos de la piste en cours
      - Télécharger l'audio d'une piste
    """

    def __init__(self):
        vlc_args = ['--no-video', '--quiet', '--verbose=-1']
        if platform.system() == 'Linux':
            vlc_args.append('--aout=pulse')
=======
    """

    def __init__(self):
        vlc_args = [
            "--no-video",
            "--aout=pulse",
            "--audio-filter=",
        ]

>>>>>>> origin/Emmeline
        self._vlc_instance = vlc.Instance(vlc_args)
        self._vlc_instance.log_unset()
        self._player = self._vlc_instance.media_player_new()

        self._playlist = []
        self._current_index = 0
        self._volume = 80
        self._shuffle = False
        self._repeat = False
        self._last_search_query = ""

        self._is_changing_track = False
        self._manual_stop = False
        self._is_paused = False

        self._event_manager = self._player.event_manager()
        self._event_manager.event_attach(
            vlc.EventType.MediaPlayerEndReached,
            self._on_end_reached
        )

        self._monitor_thread = threading.Thread(
            target=self._monitor_playback,
            daemon=True
        )
        self._monitor_thread.start()

    def __del__(self):
        try:
            self._player.stop()
            self._player.release()
            self._vlc_instance.release()
        except Exception:
            pass

    def search_and_play(self, query: str) -> dict:
        self._last_search_query = query

        track = self._fetch_info(query)

<<<<<<< HEAD
        :param query: terme de recherche.
        :return: titre de la piste trouvée.
        """
        title, url = self._fetch_info(query)
        self._playlist.append({"title": title, "url": url, "video_url": None})
=======
        self._playlist.append(track)
>>>>>>> origin/Emmeline
        self._current_index = len(self._playlist) - 1

        self._manual_stop = False
        self._is_paused = False
        self._play_url(track["url"])

<<<<<<< HEAD
        :param query: terme de recherche.
        :return: titre de la piste ajoutée.
        """
        title, url = self._fetch_info(query)
        self._playlist.append({"title": title, "url": url, "video_url": None})
        return title

    def search_playlist_and_play(self, query: str) -> tuple:
        """
        Recherche une playlist YouTube, charge toutes ses pistes (lazy)
        et démarre la lecture de la première.

        :param query: terme de recherche de la playlist.
        :return: (titre_playlist, nombre_de_pistes)
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
        """
        Recherche une playlist YouTube et retourne (titre_playlist, [(titre, video_url)]).
        Utilise le filtre playlist de YouTube pour ne chercher que des playlists.
        """
        encoded_query = urllib.parse.quote_plus(query)
        # sp=EgIQAw%3D%3D filtre les résultats pour n'afficher que les playlists
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}&sp=EgIQAw%3D%3D"

        flat_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'playlistend': 3,
        }

        with YoutubeDL(flat_opts) as ydl:
            search_results = ydl.extract_info(search_url, download=False)

        if not search_results or not search_results.get('entries'):
            raise ValueError("Aucune playlist trouvée pour cette recherche")

        first_result = search_results['entries'][0]
        playlist_url = first_result.get('url') or first_result.get('webpage_url', '')
        playlist_id = first_result.get('id', '')
        if playlist_id and not playlist_url.startswith('http'):
            playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
        playlist_title = first_result.get('title', query)

        tracks_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }

        tracks = []
        with YoutubeDL(tracks_opts) as ydl:
            playlist_data = ydl.extract_info(playlist_url, download=False)

        if not playlist_data:
            raise ValueError("Impossible d'extraire les données de la playlist")

        for entry in playlist_data.get('entries') or []:
            if not entry:
                continue
            title = entry.get('title', 'Titre inconnu')
            video_id = entry.get('id', '')
            video_url = entry.get('url') or entry.get('webpage_url', '')
            if video_id and not (video_url and video_url.startswith('http')):
                video_url = f"https://www.youtube.com/watch?v={video_id}"
            if video_url:
                tracks.append((title, video_url))

        if not tracks:
            raise ValueError("La playlist est vide ou inaccessible")

        return playlist_title, tracks

    def _resolve_audio_url(self, video_url: str) -> str:
        """Résout l'URL du flux audio à partir de l'URL d'une vidéo YouTube."""
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        if not info:
            raise ValueError(f"Impossible d'extraire l'audio : {video_url}")

        audio_url = info.get('url')
        if not audio_url:
            audio_formats = [
                f for f in info.get('formats', [])
                if f.get('acodec') != 'none' and f.get('url')
            ]
            if not audio_formats:
                raise ValueError("Aucun format audio disponible")
            best_format = max(
                audio_formats,
                key=lambda f: f.get('abr') or f.get('tbr') or f.get('quality') or 0
            )
            audio_url = best_format['url']

        return audio_url

    def _play_current_track(self):
        """Joue la piste courante, en résolvant l'URL audio si nécessaire."""
        track = self._playlist[self._current_index]
        if not track.get('url'):
            if not track.get('video_url'):
                raise ValueError("Aucune URL disponible pour cette piste")
            track['url'] = self._resolve_audio_url(track['video_url'])
        self._play_url(track['url'])

    def _fetch_info(self, query: str) -> tuple:
=======
        return track

    def search_and_queue(self, query: str) -> dict:
        track = self._fetch_info(query)
        self._playlist.append(track)
        return track
    
    def _auto_add_related_track(self):
        """
        Ajoute automatiquement une musique liée,
        en évitant surtout les longues playlists/albums.
>>>>>>> origin/Emmeline
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

            existing_urls = [
                item.get("webpage_url")
                for item in self._playlist
            ]

            for query in related_queries:
                with YoutubeDL({
                    "format": "bestaudio[ext=m4a]/bestaudio/best",
                    "quiet": True,
                    "no_warnings": True,
                    "noplaylist": True,
                }) as ydl:

                    info = ydl.extract_info(
                        f"ytsearch15:{query}",
                        download=False
                    )

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

                        # On refuse seulement les vidéos vraiment trop longues
                        if duration and duration > 600:
                            continue

                        # On refuse seulement les vrais albums/playlists longues
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
                            "webpage_url": webpage_url
                        }

                        self._playlist.append(track)

                        print("[AUTOPLAY] Ajout automatique :", track["title"])

                        return True

            print("[AUTOPLAY] Aucun résultat correct trouvé")
            return False

        except Exception as error:
            print("[AUTOPLAY] Erreur :", error)
            return False

    def _fetch_info(self, query: str) -> dict:
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

<<<<<<< HEAD
            return entry.get('title'), audio_url
=======
                audio_url = best_format["url"]
>>>>>>> origin/Emmeline

            return {
                "title": entry.get("title", "Titre inconnu"),
                "artist": entry.get("uploader", "YouTube"),
                "url": audio_url,
                "cover": entry.get("thumbnail", ""),
                "webpage_url": entry.get("webpage_url", "")
            }

    def download_audio(self, query, output_path="%(title)s.%(ext)s"):
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
        self._manual_stop = False
        self._is_paused = False

        self._player.stop()

        media = self._vlc_instance.media_new(url)
        self._player.set_media(media)

        try:
            self._player.audio_set_volume(self._volume)
        except Exception as e:
<<<<<<< HEAD
            print(f"[YouTube] Warning: Could not set volume: {e}")
        self._player.play()

    def get_current_track_name(self) -> str:
        """Retourne le titre de la piste actuellement sélectionnée."""
        if not self._playlist:
            return "Aucune piste"
        return self._playlist[self._current_index]["title"]

    def get_current_index(self) -> int:
        return self._current_index

    def get_playlist(self) -> list:
        return [item["title"] for item in self._playlist]

    def get_volume(self) -> int:
        return self._volume

    def set_volume(self, value: int):
        self._volume = max(0, min(100, int(value)))
        try:
            self._player.audio_set_volume(self._volume)
        except Exception:
            pass

    def pause(self):
        """Met en pause ou reprend la lecture."""
        self._player.pause()

    def stop(self):
=======
            print(f"[YouTube] Warning volume : {e}")

        self._player.play()

    def play(self, index=None):
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
        self._player.pause()
        self._is_paused = not self._is_paused

    def stop(self):
        self._manual_stop = True
        self._is_paused = False
>>>>>>> origin/Emmeline
        self._player.stop()

    def next_track(self):
        if not self._playlist:
            return
<<<<<<< HEAD
        if self._shuffle:
            self._current_index = random.randrange(len(self._playlist))
        else:
            self._current_index = (self._current_index + 1) % len(self._playlist)
        self._play_current_track()
=======

        if self._shuffle and len(self._playlist) > 1:
            old_index = self._current_index

            while self._current_index == old_index:
                self._current_index = random.randint(
                    0,
                    len(self._playlist) - 1
                )
        else:
            self._current_index += 1

            if self._current_index >= len(self._playlist):
                self._current_index = 0

        self._play_url(
            self._playlist[self._current_index]["url"]
        )
>>>>>>> origin/Emmeline

    def previous_track(self):
        if not self._playlist:
            return
<<<<<<< HEAD
        if self._shuffle:
            self._current_index = random.randrange(len(self._playlist))
        else:
            self._current_index = (self._current_index - 1) % len(self._playlist)
        self._play_current_track()

    def toggle_shuffle(self) -> bool:
        self._shuffle = not self._shuffle
        return self._shuffle

    def toggle_repeat(self) -> bool:
        self._repeat = not self._repeat
        return self._repeat

    def get_status(self) -> dict:
        return {
            "track": self.get_current_track_name(),
            "index": self._current_index + 1,
            "total": len(self._playlist),
            "playing": self.is_playing(),
            "volume": self.get_volume(),
            "shuffle": self._shuffle,
            "repeat": self._repeat,
            "position": round(self.get_position(), 1),
            "duration": round(self.get_duration(), 1),
        }

    def is_playing(self) -> bool:
        return self._player.is_playing() == 1

    def get_duration(self) -> float:
        ms = self._player.get_length()
        return ms / 1000 if ms > 0 else -1

    def get_position(self) -> float:
        ms = self._player.get_time()
        return ms / 1000 if ms >= 0 else -1
=======

        self._current_index -= 1

        if self._current_index < 0:
            self._current_index = len(self._playlist) - 1

        self._play_url(
            self._playlist[self._current_index]["url"]
        )

    def set_volume(self, volume):
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
        self._manual_stop = False
        self._is_paused = False
        self._player.set_time(int(seconds) * 1000)

    def is_playing(self):
        return bool(self._player.is_playing())

    def get_status(self):
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

    def _go_to_next_or_repeat(self):
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
        if self._manual_stop or self._is_paused:
            return

        self._go_to_next_or_repeat()

    def _monitor_playback(self):
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
>>>>>>> origin/Emmeline
