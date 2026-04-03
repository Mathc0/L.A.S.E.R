"""
YouTube Music Client - L.A.S.E.R
Lecteur audio YouTube avec support streaming VLC et téléchargement pygame
"""

import os
import sys
from io import BytesIO
from urllib.request import urlopen
from pathlib import Path

from yt_dlp import YoutubeDL
from PIL import Image
import pygame
import vlc


class YouTubeMusicClient:
    """
    Client pour écouter de la musique depuis YouTube.
    Supporte deux modes : téléchargement + lecture (pygame) ou streaming direct (VLC).
    """

    def __init__(self):
        """Initialise les players audio et le cache."""
        # Initialisation pygame pour le mode téléchargement
        pygame.mixer.init()

        # Initialisation VLC pour le mode streaming
        self.vlc_instance = vlc.Instance()
        self.vlc_player = self.vlc_instance.media_player_new()

        # État de lecture
        self.current_file = None
        self.is_playing = False
        self.use_streaming = False

        # Cache pour les fichiers téléchargés
        self.cache_dir = Path("./music_cache")
        self.cache_dir.mkdir(exist_ok=True)

    def search_and_play(self, query, stream=False):
        """
        Recherche et joue une musique YouTube.

        Args:
            query (str): Terme de recherche
            stream (bool): True pour streaming VLC, False pour téléchargement pygame
        """
        print(f"🔍 Recherche de: {query}")
        self.use_streaming = stream

        if stream:
            self._play_stream(query)
        else:
            self._play_download(query)

    def _play_stream(self, query):
        """Mode streaming : joue directement depuis YouTube via VLC."""
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)

                if not info or not info.get('entries'):
                    print("❌ Aucune musique trouvée")
                    return

                entry = info['entries'][0]

                # Trouver le meilleur format audio disponible
                if 'formats' not in entry:
                    print("❌ Formats audio non disponibles")
                    return

                audio_formats = [f for f in entry['formats'] if f.get('acodec') != 'none']
                if not audio_formats:
                    print("❌ Aucun format audio trouvé")
                    return

                # Sélectionner le format avec le meilleur bitrate
                best_format = max(audio_formats,
                                key=lambda f: f.get('abr', 0) or f.get('quality', 0))

                # Afficher la pochette et lancer le stream
                self.display_cover_ascii(entry.get('thumbnail'))
                self.stream_play(best_format['url'], entry['title'])

        except Exception as e:
            print(f"❌ Erreur streaming: {e}")

    def _play_download(self, query):
        """Mode téléchargement : télécharge puis joue avec pygame."""
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': str(self.cache_dir / '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch:{query}", download=True)

                if not info or not info.get('entries'):
                    print("❌ Aucune musique trouvée")
                    return

                entry = info['entries'][0]
                self.current_file = self.cache_dir / f"{entry['title']}.mp3"

                # Afficher la pochette et lancer la lecture
                self.display_cover_ascii(entry.get('thumbnail'))
                self.play()

        except Exception as e:
            print(f"❌ Erreur téléchargement: {e}")

    def stream_play(self, url, title):
        """Joue un stream audio avec VLC."""
        try:
            media = self.vlc_instance.media_new(url)
            self.vlc_player.set_media(media)
            self.vlc_player.play()
            self.is_playing = True
            print(f"🎵 Streaming: {title}")
        except Exception as e:
            print(f"❌ Erreur lors du streaming: {e}")

    def play(self):
        """Joue le fichier téléchargé avec pygame."""
        if self.current_file and self.current_file.exists():
            pygame.mixer.music.load(str(self.current_file))
            pygame.mixer.music.play()
            self.is_playing = True
            print(f"🎵 Lecture: {self.current_file.name}")
        else:
            print("❌ Aucun fichier à jouer")

    def pause(self):
        """Met en pause la lecture en cours."""
        if self.is_playing:
            if self.use_streaming:
                self.vlc_player.pause()
            else:
                pygame.mixer.music.pause()
            self.is_playing = False
            print("⏸️  Pause")

    def resume(self):
        """Reprend la lecture."""
        if self.use_streaming:
            self.vlc_player.play()
        else:
            pygame.mixer.music.unpause()
        self.is_playing = True
        print("▶️  Reprise")

    def stop(self):
        """Arrête complètement la lecture."""
        if self.use_streaming:
            self.vlc_player.stop()
        else:
            pygame.mixer.music.stop()
        self.is_playing = False
        print("⏹️  Arrêt")

    def download_image(self, url):
        """Télécharge une image depuis une URL."""
        with urlopen(url, timeout=15) as response:
            return Image.open(BytesIO(response.read()))

    def image_to_ascii(self, image, width=60):
        """
        Convertit une image en art ASCII.

        Args:
            image: Objet PIL Image
            width: Largeur maximale en caractères

        Returns:
            str: Représentation ASCII de l'image
        """
        # Conversion en niveaux de gris
        image = image.convert("L")

        # Calcul de la taille adaptée au terminal
        try:
            terminal_width = min(width, os.get_terminal_size().columns)
        except OSError:
            terminal_width = width

        orig_w, orig_h = image.size
        new_width = min(terminal_width, orig_w)
        new_height = max(1, int((orig_h / orig_w) * new_width * 0.55))

        # Redimensionnement
        image = image.resize((new_width, new_height))

        # Conversion pixels -> caractères ASCII
        chars = "@%#*+=-:. "
        pixels = list(image.getdata())
        ascii_str = "".join(chars[pixel * len(chars) // 256] for pixel in pixels)

        # Formatage en lignes
        return "\n".join(ascii_str[i:i+new_width]
                        for i in range(0, len(ascii_str), new_width))

    def display_cover_ascii(self, thumbnail_url):
        """Affiche la pochette d'album en ASCII."""
        if not thumbnail_url:
            print("📀 Aucune miniature disponible.")
            return

        print("🎨 Pochette en ASCII:")
        try:
            image = self.download_image(thumbnail_url)
            print(self.image_to_ascii(image))
        except Exception as e:
            print(f"❌ Impossible d'afficher la pochette: {e}")

    def run(self):
        """Boucle principale de l'interface CLI."""
        print("🎵 YouTube Music Client - L.A.S.E.R")
        print("Commandes disponibles:")
        print("  play <recherche>     - Télécharge et joue (pygame)")
        print("  stream <recherche>   - Stream direct ⚡ (VLC)")
        print("  pause | resume | stop - Contrôles de lecture")
        print("  quit                 - Quitter l'application")
        print()

        while True:
            try:
                cmd = input("> ").strip().split(maxsplit=1)
                if not cmd:
                    continue

                action = cmd[0].lower()

                if action == "play" and len(cmd) > 1:
                    self.search_and_play(cmd[1], stream=False)
                elif action == "stream" and len(cmd) > 1:
                    self.search_and_play(cmd[1], stream=True)
                elif action == "pause":
                    self.pause()
                elif action == "resume":
                    self.resume()
                elif action == "stop":
                    self.stop()
                elif action == "quit":
                    print("👋 Au revoir !")
                    break
                else:
                    print("❓ Commande inconnue. Tapez 'help' pour voir les commandes.")

            except KeyboardInterrupt:
                print("\n👋 Arrêt de L.A.S.E.R...")
                break


if __name__ == "__main__":
    client = YouTubeMusicClient()
    client.run()