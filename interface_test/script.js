/*
  L.A.S.E.R - Interface web responsive
  Version pensée pour :
  - montrer une belle maquette en HTML/CSS/JS
  - créer des playlists côté interface
  - être connectée plus tard à un backend Python avec fetch('/api/...')
*/

// Éléments HTML
const sidebar = document.getElementById("sidebar");
const mobileBtn = document.getElementById("mobileBtn");
const playlistContainer = document.getElementById("playlistContainer");
const playlistMenu = document.getElementById("playlistMenu");
const statusBox = document.getElementById("statusBox");
const searchInput = document.getElementById("searchInput");
const trackName = document.getElementById("trackName");
const trackInfo = document.getElementById("trackInfo");
const currentTime = document.getElementById("currentTime");
const durationTime = document.getElementById("durationTime");
const progressBar = document.getElementById("progressBar");
const volumeSlider = document.getElementById("volumeSlider");
const volumeValue = document.getElementById("volumeValue");
const shuffleBtn = document.getElementById("shuffleBtn");
const repeatBtn = document.getElementById("repeatBtn");
const playPauseBtn = document.getElementById("playPauseBtn");
const trackCount = document.getElementById("trackCount");
const playlistTitle = document.getElementById("playlistTitle");
const playlistSubtitle = document.getElementById("playlistSubtitle");
const smallCover = document.getElementById("smallCover");
const bigCover = document.getElementById("bigCover");
const bigCoverTitle = document.getElementById("bigCoverTitle");

// Mets true quand ton backend Python sera prêt.
const API_MODE = false;

// État global de l'interface
let state = {
  currentView: "local",
  index: 0,
  playing: false,
  volume: 80,
  shuffle: false,
  repeat: false,
  position: 0,
  playlist: [
    {
      title: "Dernière danse",
      artist: "Indila",
      duration: 212,
      cover: "https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/ea/4f/30/ea4f3085-5fd7-f2ea-cd95-df97fd1274e5/13UAAIM12708.rgb.jpg/300x300bb.jpg"
    },
    {
      title: "Formidable",
      artist: "Stromae",
      duration: 205,
      cover: "https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/88/0e/1c/880e1c50-cfea-739c-aa87-98a41a2fd4e5/13UMGIM73047.rgb.jpg/300x300bb.jpg"
    },
    {
      title: "Voilà",
      artist: "Barbara Pravi",
      duration: 196,
      cover: "https://is1-ssl.mzstatic.com/image/thumb/Music114/v4/c9/70/7e/c9707e9c-3d4d-9c6f-4677-c73680d52524/21UMGIM09944.rgb.jpg/300x300bb.jpg"
    },
    {
      title: "Je te promets",
      artist: "Johnny Hallyday",
      duration: 245,
      cover: ""
    }
  ],
  playlists: {
    "Mes MP3": [0, 1, 2, 3],
    "Favoris": [],
    "Révisions": []
  }
};

function formatTime(seconds) {
  const sec = Math.max(0, Math.floor(Number(seconds) || 0));
  const min = Math.floor(sec / 60);
  const rest = sec % 60;
  return `${min}:${String(rest).padStart(2, "0")}`;
}

function currentTrack() {
  return state.playlist[state.index] || null;
}

// Fonction prévue pour connecter Python plus tard
async function apiCall(url, method = "GET", data = null) {
  const options = {
    method,
    headers: { "Content-Type": "application/json" }
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  const response = await fetch(url, options);
  const result = await response.json();

  if (!response.ok || result.success === false) {
    throw new Error(result.message || "Erreur API");
  }

  return result;
}

function setCover(element, track) {
  if (!track || !track.cover) {
    element.innerHTML = "♪";
    return;
  }

  element.innerHTML = `<img src="${track.cover}" alt="Jaquette de ${track.title}">`;
}

function updateUI() {
  const track = currentTrack();

  trackName.textContent = track ? track.title : "Aucune piste";
  trackInfo.textContent = track
    ? `${track.artist} • ${state.playing ? "Lecture" : "Pause"}`
    : "Prêt";

  currentTime.textContent = formatTime(state.position);
  durationTime.textContent = formatTime(track ? track.duration : 0);
  progressBar.value = track && track.duration ? (state.position / track.duration) * 100 : 0;
  volumeSlider.value = state.volume;
  volumeValue.textContent = state.volume;
  playPauseBtn.textContent = state.playing ? "⏸" : "▶";

  shuffleBtn.classList.toggle("active", state.shuffle);
  repeatBtn.classList.toggle("active", state.repeat);

  setCover(smallCover, track);
  setCover(bigCover, track);
  bigCoverTitle.textContent = track ? track.title : "Aucune piste";

  renderPlaylist();
  renderPlaylistMenu();
  renderStatus();
}

function getDisplayedIndexes() {
  if (state.currentView === "local") {
    return state.playlist.map((_, index) => index);
  }

  return state.playlists[state.currentView] || [];
}

function renderPlaylist() {
  playlistContainer.innerHTML = "";

  const filter = searchInput.value.toLowerCase().trim();
  const displayedIndexes = getDisplayedIndexes();

  const filteredIndexes = displayedIndexes.filter(index => {
    const track = state.playlist[index];
    if (!track) return false;
    return (
      track.title.toLowerCase().includes(filter) ||
      track.artist.toLowerCase().includes(filter)
    );
  });

  playlistTitle.textContent =
    state.currentView === "local" ? "Playlist locale" : `Playlist : ${state.currentView}`;

  playlistSubtitle.textContent =
    state.currentView === "local"
      ? "Clique sur une musique pour la lancer."
      : "Cette playlist a été créée dans l’interface.";

  trackCount.textContent = `${filteredIndexes.length} titre${filteredIndexes.length > 1 ? "s" : ""}`;

  if (filteredIndexes.length === 0) {
    playlistContainer.innerHTML = `
      <div class="track-row">
        <div class="track-number">–</div>
        <div class="track-cover">♪</div>
        <div>
          <div class="track-title">Aucune musique</div>
          <div class="track-subtitle">Charge des MP3 ou ajoute un titre à cette playlist.</div>
        </div>
      </div>
    `;
    return;
  }

  filteredIndexes.forEach((trackIndex, rowIndex) => {
    const track = state.playlist[trackIndex];
    const row = document.createElement("div");
    row.className = `track-row ${trackIndex === state.index ? "active" : ""}`;

    row.innerHTML = `
      <div class="track-number">${rowIndex + 1}</div>
      <div class="track-cover">${track.cover ? `<img src="${track.cover}" alt="">` : "♪"}</div>
      <div>
        <div class="track-title">${track.title}</div>
        <div class="track-subtitle">${track.artist}</div>
      </div>
      <div class="track-duration">${formatTime(track.duration)}</div>
      <div class="row-menu">
        <button title="Ajouter à une playlist">＋</button>
      </div>
    `;

    row.addEventListener("click", () => playTrack(trackIndex));

    // Le bouton + ajoute le titre à une playlist, sans déclencher la lecture.
    row.querySelector(".row-menu button").addEventListener("click", (event) => {
      event.stopPropagation();
      addTrackToPlaylist(trackIndex);
    });

    playlistContainer.appendChild(row);
  });
}

function renderPlaylistMenu() {
  playlistMenu.innerHTML = "";

  const allCard = document.createElement("div");
  allCard.className = `playlist-card ${state.currentView === "local" ? "active" : ""}`;
  allCard.innerHTML = `<strong>Mes MP3</strong><small>${state.playlist.length} titres locaux</small>`;
  allCard.addEventListener("click", () => {
    state.currentView = "local";
    updateUI();
  });
  playlistMenu.appendChild(allCard);

  Object.keys(state.playlists).forEach(name => {
    if (name === "Mes MP3") return;

    const card = document.createElement("div");
    card.className = `playlist-card ${state.currentView === name ? "active" : ""}`;
    const count = state.playlists[name].length;
    card.innerHTML = `<strong>${name}</strong><small>${count} titre${count > 1 ? "s" : ""}</small>`;
    card.addEventListener("click", () => {
      state.currentView = name;
      updateUI();
    });

    playlistMenu.appendChild(card);
  });
}

function renderStatus() {
  const track = currentTrack();
  statusBox.innerHTML = `
    <strong>Piste :</strong> ${track ? track.title : "Aucune"}<br>
    <strong>Artiste :</strong> ${track ? track.artist : "-"}<br>
    <strong>Index :</strong> ${state.index + 1}/${state.playlist.length}<br>
    <strong>Lecture :</strong> ${state.playing ? "Oui" : "Non"}<br>
    <strong>Volume :</strong> ${state.volume}/100<br>
    <strong>Shuffle :</strong> ${state.shuffle ? "ON" : "OFF"}<br>
    <strong>Repeat :</strong> ${state.repeat ? "ON" : "OFF"}<br>
    <strong>Position :</strong> ${formatTime(state.position)} / ${formatTime(track ? track.duration : 0)}
  `;
}

function createPlaylist() {
  const name = prompt("Nom de la nouvelle playlist :");

  if (!name || !name.trim()) return;

  const cleanName = name.trim();

  if (state.playlists[cleanName]) {
    alert("Cette playlist existe déjà.");
    return;
  }

  state.playlists[cleanName] = [];
  state.currentView = cleanName;
  updateUI();

  // Plus tard avec Python :
  // apiCall('/api/playlists', 'POST', { name: cleanName });
}

function addTrackToPlaylist(trackIndex) {
  const names = Object.keys(state.playlists).filter(name => name !== "Mes MP3");

  if (names.length === 0) {
    alert("Crée d'abord une playlist.");
    createPlaylist();
    return;
  }

  const choice = prompt(`Ajouter dans quelle playlist ?\n\n${names.join("\n")}`);

  if (!choice || !choice.trim()) return;

  const playlistName = choice.trim();

  if (!state.playlists[playlistName]) {
    alert("Cette playlist n'existe pas.");
    return;
  }

  if (!state.playlists[playlistName].includes(trackIndex)) {
    state.playlists[playlistName].push(trackIndex);
  }

  updateUI();

  // Plus tard avec Python :
  // apiCall('/api/playlists/add', 'POST', { playlist: playlistName, index: trackIndex });
}

async function playTrack(index) {
  if (API_MODE) {
    try {
      const result = await apiCall("/api/play", "POST", { index });
      state = result.status;
    } catch (error) {
      alert(error.message);
    }
  } else {
    state.index = index;
    state.position = 0;
    state.playing = true;
  }

  updateUI();
}

function playPause() {
  if (API_MODE) {
    // Plus tard : appeler /api/play ou /api/pause selon l'état.
    return;
  }

  state.playing = !state.playing;
  updateUI();
}

function stopTrack() {
  state.playing = false;
  state.position = 0;
  updateUI();
}

function nextTrack() {
  if (state.playlist.length === 0) return;

  if (state.shuffle) {
    state.index = Math.floor(Math.random() * state.playlist.length);
  } else {
    state.index = (state.index + 1) % state.playlist.length;
  }

  state.position = 0;
  state.playing = true;
  updateUI();
}

function previousTrack() {
  if (state.playlist.length === 0) return;

  state.index = (state.index - 1 + state.playlist.length) % state.playlist.length;
  state.position = 0;
  state.playing = true;
  updateUI();
}

// Simulation de chargement. Plus tard, cette fonction appellera /api/load.
async function loadMusic() {
  if (API_MODE) {
    try {
      const result = await apiCall("/api/load", "POST");
      state = result.status;
      updateUI();
    } catch (error) {
      alert(error.message);
    }
  } else {
    alert("Mode maquette : avec Python, ce bouton appellera player.load_folder('./musiques').");
  }
}

function searchYoutube() {
  const query = document.getElementById("youtubeQuery").value.trim();

  if (!query) {
    alert("Tape le nom d'une musique YouTube.");
    return;
  }

  alert(`Plus tard, cette recherche appellera client_yt_music.py avec : ${query}`);
}

// Boutons
mobileBtn.addEventListener("click", () => sidebar.classList.toggle("open"));
document.getElementById("newPlaylistBtn").addEventListener("click", createPlaylist);
document.getElementById("createPlaylistHeroBtn").addEventListener("click", createPlaylist);
document.getElementById("heroLoadBtn").addEventListener("click", loadMusic);
document.getElementById("loadBtn").addEventListener("click", loadMusic);
document.getElementById("refreshBtn").addEventListener("click", updateUI);
document.getElementById("youtubeBtn").addEventListener("click", searchYoutube);

playPauseBtn.addEventListener("click", playPause);
document.getElementById("stopBtn").addEventListener("click", stopTrack);
document.getElementById("nextBtn").addEventListener("click", nextTrack);
document.getElementById("prevBtn").addEventListener("click", previousTrack);

shuffleBtn.addEventListener("click", () => {
  state.shuffle = !state.shuffle;
  updateUI();
});

repeatBtn.addEventListener("click", () => {
  state.repeat = !state.repeat;
  updateUI();
});

volumeSlider.addEventListener("input", event => {
  state.volume = Number(event.target.value);
  updateUI();

  // Plus tard avec Python :
  // apiCall('/api/volume', 'POST', { volume: state.volume });
});

progressBar.addEventListener("input", () => {
  const track = currentTrack();
  if (!track) return;

  state.position = (Number(progressBar.value) / 100) * track.duration;
  updateUI();

  // Plus tard avec Python :
  // apiCall('/api/seek', 'POST', { seconds: state.position });
});

searchInput.addEventListener("input", renderPlaylist);

// Avancement automatique en mode maquette.
// Avec Python, il faudra plutôt récupérer player.get_status() toutes les secondes.
setInterval(() => {
  const track = currentTrack();
  if (!track || !state.playing || API_MODE) return;

  state.position += 1;

  if (state.position >= track.duration) {
    if (state.repeat) {
      state.position = 0;
    } else {
      nextTrack();
      return;
    }
  }

  updateUI();
}, 1000);

updateUI();
