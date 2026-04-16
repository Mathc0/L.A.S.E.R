// On récupère les éléments HTML qu'on va utiliser
const playlistContainer = document.getElementById("playlistContainer");
const playlistSidebar = document.getElementById("playlistSidebar");
const statusBox = document.getElementById("statusBox");
const trackName = document.getElementById("trackName");
const trackInfo = document.getElementById("trackInfo");
const currentTime = document.getElementById("currentTime");
const durationTime = document.getElementById("durationTime");
const progressBar = document.getElementById("progressBar");
const volumeSlider = document.getElementById("volumeSlider");
const youtubeQuery = document.getElementById("youtubeQuery");
const shuffleBtn = document.getElementById("shuffleBtn");
const repeatBtn = document.getElementById("repeatBtn");

// Objet qui stocke l'état actuel du lecteur
let state = {
  mode: "local",
  track: "Aucune piste",
  index: 0,
  total: 0,
  playing: false,
  volume: 80,
  shuffle: false,
  repeat: false,
  position: 0,
  duration: 0,
  playlist: []
};

// Fonction pour convertir des secondes en format mm:ss
function formatTime(seconds) {
  const sec = Math.max(0, Math.floor(Number(seconds) || 0));
  const min = Math.floor(sec / 60);
  const rest = sec % 60;
  return `${min}:${String(rest).padStart(2, "0")}`;
}

// Met à jour toute l'interface à partir du state
function updateUI() {
  trackName.textContent = state.track || "Aucune piste";
  trackInfo.textContent = `${state.playing ? "Lecture" : "Pause"} • Volume ${state.volume}/100`;
  currentTime.textContent = formatTime(state.position);
  durationTime.textContent = formatTime(state.duration);
  volumeSlider.value = state.volume ?? 80;

  // Mise à jour de la barre de progression
  if (state.duration > 0) {
    progressBar.value = (state.position / state.duration) * 100;
  } else {
    progressBar.value = 0;
  }

  // Met en vert si actif
  shuffleBtn.classList.toggle("active", !!state.shuffle);
  repeatBtn.classList.toggle("active", !!state.repeat);

  renderPlaylist();
  renderStatus();
}

// Affiche la playlist dans le bloc principal et dans la sidebar
function renderPlaylist() {
  playlistContainer.innerHTML = "";
  playlistSidebar.innerHTML = "";

  // Si playlist vide
  if (!state.playlist || state.playlist.length === 0) {
    playlistContainer.innerHTML = `
      <div class="track-row">
        <div>
          <div class="track-title">Aucune piste</div>
          <div class="track-subtitle">Charge tes MP3 locaux</div>
        </div>
      </div>
    `;
    return;
  }

  // Boucle sur chaque musique
  state.playlist.forEach((track, index) => {
    const activeClass = index === (state.index - 1) ? "active" : "";

    // Ligne dans le panneau principal
    const row = document.createElement("div");
    row.className = `track-row ${activeClass}`;
    row.innerHTML = `
      <div>
        <div class="track-title">${index + 1}. ${track}</div>
        <div class="track-subtitle">Cliquer pour lire</div>
      </div>
      <button>▶</button>
    `;
    row.addEventListener("click", () => playTrack(index));
    playlistContainer.appendChild(row);

    // Ligne dans la sidebar
    const side = document.createElement("div");
    side.className = "sidebar-track";
    side.textContent = track;
    side.addEventListener("click", () => playTrack(index));
    playlistSidebar.appendChild(side);
  });
}

// Affiche les infos du player
function renderStatus() {
  statusBox.innerHTML = `
    <strong>Piste :</strong> ${state.track}<br>
    <strong>Index :</strong> ${state.index}/${state.total}<br>
    <strong>Lecture :</strong> ${state.playing ? "Oui" : "Non"}<br>
    <strong>Volume :</strong> ${state.volume}/100<br>
    <strong>Shuffle :</strong> ${state.shuffle ? "ON" : "OFF"}<br>
    <strong>Repeat :</strong> ${state.repeat ? "ON" : "OFF"}<br>
    <strong>Position :</strong> ${formatTime(state.position)} / ${formatTime(state.duration)}<br>
    <strong>Mode :</strong> ${state.mode}
  `;
}

// Fonction générique pour appeler le backend Flask
async function apiCall(url, method = "GET", data = null) {
  const options = {
    method,
    headers: {
      "Content-Type": "application/json"
    }
  };

  // Si on envoie des données
  if (data) {
    options.body = JSON.stringify(data);
  }

  // Appel au backend
  const response = await fetch(url, options);
  const result = await response.json();

  // Si erreur
  if (!response.ok || result.success === false) {
    throw new Error(result.message || "Erreur");
  }

  return result;
}

// Récupère l'état actuel du lecteur
async function refreshStatus() {
  try {
    const result = await apiCall("/api/status");
    state = result.status;
    updateUI();
  } catch (error) {
    console.error(error);
  }
}

// Charge les MP3 du dossier musiques/
async function loadMusic() {
  try {
    const result = await apiCall("/api/load", "POST");
    state = result.status;
    updateUI();
  } catch (error) {
    alert(error.message);
  }
}

// Lance une musique selon son index
async function playTrack(index) {
  try {
    const result = await apiCall("/api/play", "POST", { index });
    state = result.status;
    updateUI();
  } catch (error) {
    alert(error.message);
  }
}

// Bouton play
async function playCurrent() {
  try {
    const result = await apiCall("/api/play", "POST");
    state = result.status;
    updateUI();
  } catch (error) {
    alert(error.message);
  }
}

// Bouton pause
async function pauseCurrent() {
  try {
    const result = await apiCall("/api/pause", "POST");
    state = result.status;
    updateUI();
  } catch (error) {
    alert(error.message);
  }
}

// Bouton stop
async function stopCurrent() {
  try {
    const result = await apiCall("/api/stop", "POST");
    state = result.status;
    updateUI();
  } catch (error) {
    alert(error.message);
  }
}

// Musique suivante
async function nextTrack() {
  try {
    const result = await apiCall("/api/next", "POST");
    state = result.status;
    updateUI();
  } catch (error) {
    alert(error.message);
  }
}

// Musique précédente
async function prevTrack() {
  try {
    const result = await apiCall("/api/prev", "POST");
    state = result.status;
    updateUI();
  } catch (error) {
    alert(error.message);
  }
}

// Change le volume
async function changeVolume(volume) {
  try {
    const result = await apiCall("/api/volume", "POST", { volume });
    state = result.status;
    updateUI();
  } catch (error) {
    console.error(error);
  }
}

// Change la position dans la musique
async function seekTrack(seconds) {
  try {
    const result = await apiCall("/api/seek", "POST", { seconds });
    state = result.status;
    updateUI();
  } catch (error) {
    console.error(error);
  }
}

// Active/désactive shuffle
async function toggleShuffle() {
  try {
    const result = await apiCall("/api/shuffle", "POST");
    state = result.status;
    updateUI();
  } catch (error) {
    alert(error.message);
  }
}

// Active/désactive repeat
async function toggleRepeat() {
  try {
    const result = await apiCall("/api/repeat", "POST");
    state = result.status;
    updateUI();
  } catch (error) {
    alert(error.message);
  }
}

// Recherche une musique sur YouTube
async function searchYoutube() {
  const query = youtubeQuery.value.trim();

  if (!query) {
    alert("Tape une recherche.");
    return;
  }

  try {
    const result = await apiCall("/api/youtube", "POST", { query });
    state = result.status;
    updateUI();
  } catch (error) {
    alert(error.message);
  }
}

// On relie les boutons HTML aux fonctions JavaScript
document.getElementById("loadBtn").addEventListener("click", loadMusic);
document.getElementById("youtubeBtn").addEventListener("click", searchYoutube);
document.getElementById("youtubeSearchBtn").addEventListener("click", searchYoutube);
document.getElementById("refreshBtn").addEventListener("click", refreshStatus);
document.getElementById("playBtn").addEventListener("click", playCurrent);
document.getElementById("pauseBtn").addEventListener("click", pauseCurrent);
document.getElementById("stopBtn").addEventListener("click", stopCurrent);
document.getElementById("nextBtn").addEventListener("click", nextTrack);
document.getElementById("prevBtn").addEventListener("click", prevTrack);
document.getElementById("shuffleBtn").addEventListener("click", toggleShuffle);
document.getElementById("repeatBtn").addEventListener("click", toggleRepeat);

// Quand on bouge le volume
volumeSlider.addEventListener("input", (e) => {
  changeVolume(Number(e.target.value));
});

// Quand on bouge la barre de progression
progressBar.addEventListener("change", () => {
  if (state.duration > 0) {
    const seconds = (Number(progressBar.value) / 100) * state.duration;
    seekTrack(seconds);
  }
});

// Mise à jour auto toutes les secondes
setInterval(refreshStatus, 1000);

// Premier chargement au démarrage
refreshStatus();