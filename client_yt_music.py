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
vlc_path = os.path.join(os.getcwd(), "vlc_files")
os.environ['PATH'] += os.pathsep + vlc_path
import vlc

class YouTubeMusicClient:
    """Client minimal pour jouer ou télécharger de l'audio YouTube."""

    def __init__(self):
        self.vlc_instance = vlc.Instance()
        self.vlc_player = self.vlc_instance.media_player_new()

    def __del__(self):
        try:
            self.vlc_player.stop()
            self.vlc_player.release()
            self.vlc_instance.release()
        except Exception:
            pass

    def search_and_play(self, query):
        """Recherche une piste YouTube et la lit en streaming via VLC."""
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)

            if not info or not info.get('entries'):
                raise ValueError("Aucune musique trouvée")

            entry = info['entries'][0]

            # Récupère l'URL directement si yt-dlp l'a déjà sélectionnée
            audio_url = entry.get('url')

            # Sinon, sélection manuelle du meilleur format audio
            if not audio_url:
                audio_formats = [
                    f for f in entry.get('formats', [])
                    if f.get('acodec') != 'none' and f.get('url')
                ]

                if not audio_formats:
                    raise ValueError("Aucun format audio disponible")

                best_format = max(
                    audio_formats,
                    key=lambda f: f.get('abr') or f.get('tbr') or f.get('quality') or 0
                )
                audio_url = best_format['url']

            self._play_url(audio_url)
            return entry.get('title')

    def download_audio(self, query, output_path='%(title)s.%(ext)s'):
        """Télécharge l'audio de la première vidéo YouTube correspondant à la recherche."""
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            static_ffmpeg.add_paths()

        def _progress_hook(d):
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', '').strip()
                print(f"\rTéléchargement... {percent}", end='', flush=True)
            elif d['status'] == 'finished':
                print("\rTéléchargement... 100%           ")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [_progress_hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            # Robustesse réseau : retries + fragments + user-agent navigateur
            'retries': 10,
            'fragment_retries': 10,
            'http_chunk_size': 1048576,  # 1 Mo par fragment pour éviter les coupures
            'socket_timeout': 30,
            'http_headers': {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/124.0.0.0 Safari/537.36'
                ),
            },
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch:{query}", download=True)

                if not info or not info.get('entries'):
                    raise ValueError("Aucune musique trouvée")

                return info['entries'][0].get('title')

        except DownloadError as e:
            raise RuntimeError(f"Échec du téléchargement : {e}") from e

    def stop(self):
        """Arrête la lecture en cours."""
        self.vlc_player.stop()

    def _play_url(self, url):
        """Arrête la lecture précédente et démarre le nouveau flux."""
        self.vlc_player.stop()
        media = self.vlc_instance.media_new(url)
        self.vlc_player.set_media(media)
        self.vlc_player.play()