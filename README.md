# L.A.S.E.R

## Description de l'application

L.A.S.E.R. : Lecteur Audio Sans Efficacité Réelle

Il s'agit d'un lecteur de fichier audio MP3 et Youtube Music fontionant sous Windows.

## Instructions d'instalation : 
### instructions communes
installer les dépendances

### Pour linux fedora
sudo dnf install \
  https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm \
  https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm


## Instruction d'utilisation
### sur windows
lancer le fichier app.py en tant qu'exécutable

### sur Linux Fedora/Cachy

  Sur l'emplacement du fichier rentrer \
  source .venv/bin/activate \
  python3 app.py 
## Résultat attendue
une page web de votre anvigateur par défault devrait s'ouvrir avec ce message dans le terminal

  L.A.S.E.R - Interface Web        \
  Démarrage complet du système      


============================================================ \
✅ Base de données initialisée \
🎵 Initialisation du lecteur de musique... \
✅ Lecteur de musique initialisé avec succès

📝 Commandes disponibles: 
   - Ouvrez http://127.0.0.1:5000 dans votre navigateur 
   - Appuyez sur Ctrl+C pour arrêter le serveur
============================================================ \

🚀 Démarrage du serveur Flask sur http://127.0.0.1:5000 \
 * Serving Flask app 'app' \
 * Debug mode: off 
