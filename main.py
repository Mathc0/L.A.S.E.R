import time
import client_yt_music

def show_music_progress():
    # Affiche une barre de progression pour la musique en cours de lecture
    progress_length = 30
    for i in range(progress_length + 1):
        bar = '█' * i + '-' * (progress_length - i)
        print(f"\r🎵 Lecture en cours: |{bar}| {int((i/progress_length)*100)}%", end="")
        time.sleep(0.1)


def main():
    #Menu de lancement
    print("Bienvenue dans L.A.S.E.R - Le Lecteur Audio de Streaming pour la Musique !")
    while True:
        try:
            choice = input("Entrez votre choix (play ou quit): ")
        except KeyboardInterrupt:
            print("Aurevoir.")
            break
        if choice == 'play':
            try:
                query = input("Entrez le nom de la musique à jouer: ")
            except KeyboardInterrupt:
                print("Retour au menu principal.")
                break
            client = client_yt_music.YouTubeMusicClient()
            client.search_and_play(query)
            show_music_progress()
        elif choice == 'quit':
            print("Merci d'avoir utilisé L.A.S.E.R. À bientôt !")
            break
        else:
            print("Choix invalide, veuillez réessayer.")

main()
