# 🎵 Tagging des Musiques YouTube - L.A.S.E.R

## 📋 Résumé des Améliorations

Ce document explique les améliorations apportées au système de tagging des musiques YouTube dans L.A.S.E.R.

## 🎯 Problème Résolu

Avant ces modifications:
- Les musiques YouTube avaient des métadonnées incorrectes ou incomplètes
- L'artiste était souvent remplacé par le nom du channel YouTube
- Les métadonnées n'étaient pas synchronisées entre l'interface et la DB
- Les titres YouTube n'étaient pas parseés correctement (ex: "Artist - Title" au lieu de séparer artist et titre)

## ✨ Améliorations Apportées

### 1. **Extraction Améliorée des Métadonnées YouTube** (`client_yt_music.py`)

**Nouvelle méthode:** `_extract_artist_from_title()`
- Parse le titre YouTube pour extraire l'artiste et le titre séparés
- Supporte les formats courants:
  - "Artist - Title"
  - "Artist — Title"
  - "Artist | Title"
  - "Artist: Title"
- Retourne un tuple `(artist, clean_title)`

**Impact:** Les musiques YouTube sont maintenant taguées avec le bon artiste, pas le nom du channel

### 2. **Enregistrement Amélioré en Base de Données** (`client_yt_music.py`)

**Fonction modifiée:** `_record_play_youtube()`
- Capture correctement les métadonnées: `title`, `artist`, `album` (channel), `duration`
- Marque les musiques comme `scanned=True` et `tagged=True` (car venant de YouTube)
- Met à jour les métadonnées existantes s'ils sont vides ou par défaut

### 3. **Nouveau Système de Tagging YouTube** (`mp3_tagger.py`)

**Nouvelle fonction:** `tag_youtube_track(path, title, artist, album)`
- Crée ou met à jour les entrées YouTube dans la DB
- Accepte les métadonnées directement (sans chercher sur MusicBrainz)
- Idéale pour les musiques de streaming sans fichier local

### 4. **Synchronisation des Métadonnées** (`client_yt_music.py`)

**Nouvelle méthode:** `sync_youtube_metadata()`
- Synchronise les métadonnées de TOUTES les musiques YouTube de la DB
- Retourne un rapport: `(nombre_synchronisé, nombre_total)`
- Accessible via l'endpoint `/api/youtube/sync` (POST)

### 5. **Nouveaux Endpoints API** (`app.py`)

#### `/api/youtube/playlist` (GET)
```json
{
  "success": true,
  "tracks": [
    {
      "index": 0,
      "title": "Song Title",
      "artist": "Artist Name",
      "album": "Channel Name",
      "cover": "thumbnail_url",
      "duration": 180,
      "url": "youtube_url",
      "source": "youtube"
    }
  ],
  "total": 1,
  "current_index": 0
}
```

#### `/api/youtube/sync` (POST)
Synchronise tous les métadonnées YouTube dans la DB
```json
{
  "success": true,
  "synced": 5,
  "total": 10,
  "message": "Synchronisation terminée : 5/10 musiques YouTube mises à jour"
}
```

#### `/api/youtube/metadata` (POST)
Met à jour les métadonnées d'une musique spécifique
```json
{
  "path": "https://youtube.com/watch?v=...",
  "title": "Song Title",
  "artist": "Artist Name",
  "album": "Album or Channel"
}
```

### 6. **Amélioration du Endpoint `/api/library`** (`app.py`)

- Retourne maintenant les musiques locales + les musiques YouTube de la DB
- Les musiques YouTube incluent:
  - Métadonnées correctes (`title`, `artist`, `album`)
  - Statistiques (`play_count`, `last_played`)
  - Source ("youtube")
  - URL

### 7. **Intégration avec l'Interface** (`script.js`)

L'interface utilise déjà les bonnes métadonnées:
- `addOrUpdateYoutubeTrack()` récupère les champs: `title`, `artist`, `cover`, `duration`, `webpage_url`
- L'affichage est automatiquement amélioré grâce aux meilleures données de l'API

## 🔧 Utilisation

### Via l'Interface Web

1. **Jouer une musique YouTube**
   - Utiliser la barre de recherche pour chercher une musique
   - Les métadonnées sont maintenant correctement extraites et affichées

2. **Synchroniser tous les Métadonnées**
   - Accéder à `/api/youtube/sync` (POST request)
   - Ou ajouter un bouton dans l'interface pour appeler cet endpoint

### Via le Backend

```python
# Synchroniser les métadonnées YouTube
synced, total = youtube_client.sync_youtube_metadata()
print(f"Synchronisé: {synced}/{total}")

# Tagger une musique spécifique
from mp3_tagger import tag_youtube_track
tag_youtube_track(
    path="https://youtube.com/watch?v=...",
    title="Song Title",
    artist="Artist Name",
    album="Channel Name"
)
```

## 📊 Architecture de la Base de Données

La table `Track` est utilisée pour stocker:
- **Musiques Locales**: chemin du fichier
- **Musiques YouTube**: URL de la vidéo YouTube
- **Métadonnées**: `title`, `artist`, `album` (unifié)
- **Statut**: `scanned=True`, `tagged=True` pour les musiques YouTube
- **Statistiques**: `play_count`, `last_played`

## 🚀 Prochaines Étapes Possibles

1. **Téléchargement et Tagging Local**
   - Ajouter un endpoint pour télécharger les musiques YouTube localement
   - Appliquer le tagging MP3 complet avec MusicBrainz

2. **Interface Améliorée**
   - Ajouter un bouton pour synchroniser les métadonnées
   - Afficher les statistiques des musiques YouTube (dernier écoute, nombre d'écoutes)

3. **Détection d'Artiste Améliorée**
   - Utiliser des services comme Genius ou Musixmatch pour extraire l'artiste correct
   - Implémenter un fallback sur MusicBrainz pour les musiques YouTube

## 📝 Notes

- Les musiques YouTube de streaming ne sont pas téléchargées localement (sauf demande explicite)
- Les métadonnées sont parsées depuis le titre YouTube et le channel (pas d'API ID tiers)
- Le système est rétrocompatible avec les musiques locales existantes

## ✅ Tests Recommandés

1. Jouer une musique YouTube avec format "Artist - Title"
2. Vérifier que les métadonnées sont correctes dans l'interface
3. Vérifier que les métadonnées sont enregistrées dans la DB
4. Appeler `/api/youtube/sync` et vérifier la synchronisation
5. Vérifier que `/api/library` retourne les musiques YouTube avec les bonnes métadonnées
