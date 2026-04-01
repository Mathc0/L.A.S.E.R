import os
import sys
from io import BytesIO
from urllib.request import urlopen
from yt_dlp import YoutubeDL
from PIL import Image
import pygame
import time
from pathlib import Path

class YouTubeMusicClient:
    def __init__(self):
        pygame.mixer.init()
        self.current_file = None
        self.is_playing = False
        self.cache_dir = Path("./music_cache")
        self.cache_dir.mkdir(exist_ok=True)

    def search_and_play(self, query):
        """Recherche et joue une musique YouTube Music"""
        print(f"Recherche de: {query}")
        
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
                if info:
                    entry = info['entries'][0]
                    self.current_file = self.cache_dir / f"{entry['title']}.mp3"
                    self.display_cover_ascii(entry.get('thumbnail'))
                    self.play()
        except Exception as e:
            print(f"Erreur: {e}")

    def play(self):
        """Joue le fichier actuel"""
        if self.current_file and self.current_file.exists():
            pygame.mixer.music.load(str(self.current_file))
            pygame.mixer.music.play()
            self.is_playing = True
            print(f"Lecture: {self.current_file.name}")

    def pause(self):
        """Met en pause"""
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False

    def resume(self):
        """Reprend la lecture"""
        pygame.mixer.music.unpause()
        self.is_playing = True

    def stop(self):
        """Arrête la lecture"""
        pygame.mixer.music.stop()
        self.is_playing = False

    def download_image(self, url):
        with urlopen(url, timeout=15) as response:
            return Image.open(BytesIO(response.read()))

    def image_to_ascii(self, image, width=60):
        image = image.convert("L")
        try:
            terminal_width = min(width, os.get_terminal_size().columns)
        except OSError:
            terminal_width = width
        orig_w, orig_h = image.size
        new_width = min(terminal_width, orig_w)
        new_height = max(1, int((orig_h / orig_w) * new_width * 0.55))
        image = image.resize((new_width, new_height))
        chars = "@%#*+=-:. "
        pixels = list(image.getdata())
        ascii_str = "".join(chars[pixel * len(chars) // 256] for pixel in pixels)
        return "\n".join(ascii_str[i:i+new_width] for i in range(0, len(ascii_str), new_width))

    def display_cover_ascii(self, thumbnail_url):
        if not thumbnail_url:
            print("Aucune miniature disponible.")
            return
        print("Affichage de la pochette en ASCII:")
        try:
            image = self.download_image(thumbnail_url)
            print(self.image_to_ascii(image))
        except Exception as e:
            print(f"Impossible d'afficher la pochette ASCII: {e}")

    def run(self):
        """Boucle CLI interactive"""
        print("🎵 YouTube Music Client")
        print("Commandes: play <query> | pause | resume | stop | quit\n")
        
        while True:
            try:
                cmd = input("> ").strip().split(maxsplit=1)
                if not cmd:
                    continue
                
                action = cmd[0].lower()
                
                if action == "play" and len(cmd) > 1:
                    self.search_and_play(cmd[1])
                elif action == "pause":
                    self.pause()
                elif action == "resume":
                    self.resume()
                elif action == "stop":
                    self.stop()
                elif action == "quit":
                    break
                else:
                    print("Commande inconnue")
            except KeyboardInterrupt:
                print("\nArrêt...")
                break

if __name__ == "__main__":
    client = YouTubeMusicClient()
    client.run()