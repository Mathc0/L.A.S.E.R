import time
from client_yt_music import YouTubeMusicClient

PROGRESS_LENGTH = 30

def show_music_progress(title: str):
    """Affiche une barre de progression pour la musique en cours de lecture."""
    print(f"🎵 Lecture : {title}")
    for i in range(PROGRESS_LENGTH + 1):
        bar = '█' * i + '-' * (PROGRESS_LENGTH - i)
        print(f"\r|{bar}| {int((i / PROGRESS_LENGTH) * 100)}%", end="", flush=True)
        time.sleep(0.1)
    print()

def show_help():
    print(
        "\nCommandes disponibles :"
        "\n  play      - Rechercher et lire une musique"
        "\n  stop      - Arrêter la lecture en cours"
        "\n  download  - Télécharger une musique en MP3"
        "\n  help      - Afficher ce menu"
        "\n  quit      - Quitter L.A.S.E.R\n"
    )

def main():
    print("Bienvenue dans L.A.S.E.R - Le Lecteur Audio de fichier locaux ou en streaming pour la Musique !")
    show_help()

    client = YouTubeMusicClient()

    while True:
        try:
            choice = input("Commande > ").strip().lower()
        except KeyboardInterrupt:
            print("\nAu revoir.")
            client.stop()
            break

        if choice == 'play':
            try:
                query = input("Nom de la musique : ").strip()
            except KeyboardInterrupt:
                print("\nRetour au menu.")
                continue

            if not query:
                print("Aucune recherche saisie.")
                continue

            try:
                print("Recherche en cours...")
                title = client.search_and_play(query)
                show_music_progress(title or query)
            except ValueError as e:
                print(f"Introuvable : {e}")
            except Exception as e:
                print(f"Erreur lors de la lecture : {e}")

        elif choice == 'stop':
            client.stop()
            print("Lecture arrêtée.")

        elif choice == 'download':
            try:
                query = input("Nom de la musique à télécharger : ").strip()
            except KeyboardInterrupt:
                print("\nRetour au menu.")
                continue

            if not query:
                print("Aucune recherche saisie.")
                continue

            try:
                print("Téléchargement en cours...")
                title = client.download_audio(query)
                print(f"✅ Téléchargé : {title or query}")
            except RuntimeError as e:
                print(f"Erreur : {e}")

        elif choice == 'help':
            show_help()

        elif choice == 'quit':
            print("Merci d'avoir utilisé L.A.S.E.R. À bientôt !")
            client.stop()
            break

        elif choice == '':
            continue

        else:
            print(f"Commande inconnue : '{choice}'. Tapez 'help' pour la liste des commandes.")

main()