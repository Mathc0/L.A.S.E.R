#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STARTUP.PY — Script de démarrage complet pour L.A.S.E.R
Lance l'interface web, initialise le lecteur et ouvre le navigateur.
"""

import os
import sys
import time
import webbrowser
import threading
from app import app
from player import MusicPlayer
try:
    from db import init_db
except Exception:
    init_db = None

# Configuration
HOST = "127.0.0.1"
PORT = 5000
URL = f"http://{HOST}:{PORT}"
MUSIC_FOLDER = "./musiques"

def start_flask_server():
    """Lance le serveur Flask en mode debug."""
    print(f"🚀 Démarrage du serveur Flask sur {URL}")
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)

def open_browser():
    """Ouvre le navigateur après un délai pour laisser le serveur démarrer."""
    time.sleep(2)  # Attendre que le serveur soit prêt
    print(f"🌐 Ouverture de {URL} dans le navigateur...")
    webbrowser.open(URL)

def init_music_player():
    """Initialise le lecteur de musique."""
    print("🎵 Initialisation du lecteur de musique...")
    
    # Créer le dossier de musique s'il n'existe pas
    if not os.path.exists(MUSIC_FOLDER):
        os.makedirs(MUSIC_FOLDER)
        print(f"📁 Dossier {MUSIC_FOLDER} créé")
    
    # Initialiser le player
    player = MusicPlayer(music_folder=MUSIC_FOLDER)
    print("✅ Lecteur de musique initialisé avec succès")
    return player

def main():
    """Point d'entrée principal."""
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

    # Initialiser le lecteur
    player = init_music_player()
    
    # Lancer le navigateur dans un thread séparé
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    print("\n📝 Commandes disponibles:")
    print("   - Ouvrez http://127.0.0.1:5000 dans votre navigateur")
    print("   - Appuyez sur Ctrl+C pour arrêter le serveur")
    print("=" * 60 + "\n")
    
    # Lancer le serveur Flask (bloquant)
    try:
        start_flask_server()
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du serveur...")
        sys.exit(0)

if __name__ == "__main__":
    main()
