const API_MODE = false;

const sidebar = document.getElementById("sidebar");
const mobileMenuBtn = document.getElementById("mobileMenuBtn");
const playlistMenu = document.getElementById("playlistMenu");
const playlistContainer = document.getElementById("playlistContainer");
const searchInput = document.getElementById("searchInput");
const trackCount = document.getElementById("trackCount");
const playlistTitle = document.getElementById("playlistTitle");
const statusBox = document.getElementById("statusBox");

const trackName = document.getElementById("trackName");
const trackInfo = document.getElementById("trackInfo");
const currentTime = document.getElementById("currentTime");
const durationTime = document.getElementById("durationTime");
const progressBar = document.getElementById("progressBar");
const volumeSlider = document.getElementById("volumeSlider");
const volumeValue = document.getElementById("volumeValue");

const playPauseBtn = document.getElementById("playPauseBtn");
const shuffleBtn = document.getElementById("shuffleBtn");
const repeatBtn = document.getElementById("repeatBtn");

const heroCover = document.getElementById("heroCover");
const largeCover = document.getElementById("largeCover");
const bottomCover = document.getElementById("bottomCover");

let lastPlaylistRenderKey = "";

let state = {
  currentPlaylist: "Mes MP3",
  index: 0,
  playing: false,
  volume: 80,
  shuffle: false,
  repeat: false,
  position: 0,

  tracks: [
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
    "Découvertes": []
  }
};

function formatTime(seconds) {
  const sec = Math.max(0, Math.floor(Number(seconds) || 0));
  const min = Math.floor(sec / 60);
  const rest = sec % 60;
  return `${min}:${String(rest).padStart(2, "0")}`;
}

function getCurrentTrack() {
  return state.tracks[state.index] || null;
}

function getPlaylistIndexes() {
  return state.playlists[state.currentPlaylist] || [];
}

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
  const coverKey = track && track.cover ? track.cover : "default";

  if (element.dataset.coverKey === coverKey) {
    return;
  }

  element.dataset.coverKey = coverKey;

  if (!track || !track.cover) {
    element.innerHTML = "♪";
    return;
  }

  element.innerHTML = `
    <img
      src="${track.cover}"
      alt="Jaquette de ${track.title}"
      loading="lazy"
    >
  `;
}

function updateUI(forcePlaylistRender = false) {
  const track = getCurrentTrack();

  trackName.textContent = track ? track.title : "Aucune piste";
  trackInfo.textContent = track
    ? `${track.artist} • ${state.playing ? "Lecture" : "Pause"}`
    : "Prêt";

  currentTime.textContent = formatTime(state.position);
  durationTime.textContent = formatTime(track ? track.duration : 0);

  progressBar.value =
    track && track.duration
      ? (state.position / track.duration) * 100
      : 0;

  volumeSlider.value = state.volume;
  volumeValue.textContent = state.volume;
  playPauseBtn.textContent = state.playing ? "⏸" : "▶";

  shuffleBtn.classList.toggle("active", state.shuffle);
  repeatBtn.classList.toggle("active", state.repeat);

  setCover(heroCover, track);
  setCover(largeCover, track);
  setCover(bottomCover, track);

  renderPlaylistMenu();
  renderPlaylist(forcePlaylistRender);
  renderStatus();
}

function renderPlaylistMenu() {
  playlistMenu.innerHTML = "";

  Object.keys(state.playlists).forEach(name => {
    const card = document.createElement("div");

    card.className =
      `playlist-card ${state.currentPlaylist === name ? "active-card" : ""}`;

    const emoji =
      name === "Mes MP3"
        ? "🎧"
        : name === "Favoris"
          ? "💚"
          : "✨";

    const count = state.playlists[name].length;

    card.innerHTML = `
      <span>${emoji}</span>
      <div>
        <strong>${name}</strong>
        <small>${count} titre${count > 1 ? "s" : ""}</small>
      </div>
    `;

    card.addEventListener("click", () => {
      state.currentPlaylist = name;
      updateUI(true);
    });

    playlistMenu.appendChild(card);
  });
}

function renderPlaylist(force = false) {
  playlistTitle.textContent = state.currentPlaylist;

  const filter = searchInput.value.trim().toLowerCase();

  const indexes = getPlaylistIndexes().filter(index => {
    const track = state.tracks[index];
    if (!track) return false;

    return (
      track.title.toLowerCase().includes(filter) ||
      track.artist.toLowerCase().includes(filter)
    );
  });

  trackCount.textContent =
    `${indexes.length} titre${indexes.length > 1 ? "s" : ""}`;

  const renderKey =
    `${state.currentPlaylist}|${filter}|${indexes.join(",")}|${state.index}`;

  if (!force && renderKey === lastPlaylistRenderKey) {
    return;
  }

  lastPlaylistRenderKey = renderKey;
  playlistContainer.innerHTML = "";

  if (indexes.length === 0) {
    playlistContainer.innerHTML = `
      <div class="track-row">
        <div class="track-number">–</div>
        <div class="track-cover">♪</div>
        <div>
          <div class="track-title">Aucune musique</div>
          <div class="track-subtitle">
            Ajoute des MP3 ou crée une playlist.
          </div>
        </div>
      </div>
    `;
    return;
  }

  indexes.forEach((trackIndex, rowIndex) => {
    const track = state.tracks[trackIndex];

    const row = document.createElement("div");

    row.className =
      `track-row ${trackIndex === state.index ? "active" : ""}`;

    row.innerHTML = `
      <div class="track-number">${rowIndex + 1}</div>

      <div class="track-cover">
        ${track.cover ? `<img src="${track.cover}" alt="">` : "♪"}
      </div>

      <div>
        <div class="track-title">${track.title}</div>
        <div class="track-subtitle">${track.artist}</div>
      </div>

      <div class="track-duration">
        ${formatTime(track.duration)}
      </div>

      <button class="add-track-btn" title="Ajouter à une playlist">＋</button>
    `;

    row.addEventListener("click", () => {
      playTrack(trackIndex);
    });

    row.querySelector(".add-track-btn").addEventListener("click", event => {
      event.stopPropagation();
      addTrackToPlaylist(trackIndex);
    });

    playlistContainer.appendChild(row);
  });
}

function renderStatus() {
  const track = getCurrentTrack();

  statusBox.innerHTML = `
    <strong>Piste :</strong> ${track ? track.title : "Aucune"}<br>
    <strong>Index :</strong> ${state.index + 1}/${state.tracks.length}<br>
    <strong>Lecture :</strong> ${state.playing ? "Oui" : "Non"}<br>
    <strong>Volume :</strong> ${state.volume}/100<br>
    <strong>Shuffle :</strong> ${state.shuffle ? "ON" : "OFF"}<br>
    <strong>Repeat :</strong> ${state.repeat ? "ON" : "OFF"}<br>
    <strong>Position :</strong> ${formatTime(state.position)}
  `;
}

function createPlaylist() {
  const name = prompt("Nom de la playlist :");

  if (!name || !name.trim()) {
    return;
  }

  const cleanName = name.trim();

  if (state.playlists[cleanName]) {
    alert("Cette playlist existe déjà.");
    return;
  }

  state.playlists[cleanName] = [];
  state.currentPlaylist = cleanName;
  updateUI(true);
}

function addTrackToPlaylist(trackIndex) {
  const names = Object.keys(state.playlists).filter(
    name => name !== "Mes MP3"
  );

  if (names.length === 0) {
    alert("Crée d'abord une playlist.");
    createPlaylist();
    return;
  }

  const selected = prompt(
    `Ajouter dans quelle playlist ?\n\n${names.join("\n")}`
  );

  if (!selected || !selected.trim()) {
    return;
  }

  const playlistName = selected.trim();

  if (!state.playlists[playlistName]) {
    alert("Cette playlist n'existe pas.");
    return;
  }

  if (!state.playlists[playlistName].includes(trackIndex)) {
    state.playlists[playlistName].push(trackIndex);
  }

  updateUI(true);
}

async function loadMusic() {
  if (!API_MODE) {
    alert(
      "Mode maquette : plus tard, ce bouton appellera player.load_folder('./musiques')."
    );
    return;
  }

  try {
    const result = await apiCall("/api/load", "POST");
    state = result.status;
    updateUI(true);
  } catch (error) {
    alert(error.message);
  }
}

function playTrack(index) {
  if (API_MODE) {
    apiCall("/api/play", "POST", { index });
  }

  state.index = index;
  state.position = 0;
  state.playing = true;
  updateUI(true);
}

function playPause() {
  state.playing = !state.playing;
  updateUI(false);

  if (API_MODE) {
    apiCall(state.playing ? "/api/play" : "/api/pause", "POST");
  }
}

function stopTrack() {
  state.playing = false;
  state.position = 0;
  updateUI(false);

  if (API_MODE) {
    apiCall("/api/stop", "POST");
  }
}

function nextTrack() {
  if (state.tracks.length === 0) return;

  if (state.shuffle) {
    state.index = Math.floor(Math.random() * state.tracks.length);
  } else {
    state.index = (state.index + 1) % state.tracks.length;
  }

  state.position = 0;
  state.playing = true;
  updateUI(true);

  if (API_MODE) {
    apiCall("/api/next", "POST");
  }
}

function previousTrack() {
  if (state.tracks.length === 0) return;

  state.index =
    (state.index - 1 + state.tracks.length) % state.tracks.length;

  state.position = 0;
  state.playing = true;
  updateUI(true);

  if (API_MODE) {
    apiCall("/api/prev", "POST");
  }
}

mobileMenuBtn.addEventListener("click", () => {
  sidebar.classList.toggle("open");
});

document.getElementById("createPlaylistBtn").addEventListener("click", () => {
  createPlaylist();
});

document.getElementById("loadBtn").addEventListener("click", () => {
  loadMusic();
});

document.getElementById("heroLoadBtn").addEventListener("click", () => {
  loadMusic();
});

document.getElementById("heroPlayBtn").addEventListener("click", () => {
  const firstTrackIndex = getPlaylistIndexes()[0] || 0;
  playTrack(firstTrackIndex);
});

document.getElementById("youtubeBtn").addEventListener("click", () => {
  alert("Plus tard, ce bouton appellera client_yt_music.py.");
});

playPauseBtn.addEventListener("click", () => {
  playPause();
});

document.getElementById("stopBtn").addEventListener("click", () => {
  stopTrack();
});

document.getElementById("nextBtn").addEventListener("click", () => {
  nextTrack();
});

document.getElementById("prevBtn").addEventListener("click", () => {
  previousTrack();
});

shuffleBtn.addEventListener("click", () => {
  state.shuffle = !state.shuffle;
  updateUI(false);
});

repeatBtn.addEventListener("click", () => {
  state.repeat = !state.repeat;
  updateUI(false);
});

volumeSlider.addEventListener("input", event => {
  state.volume = Number(event.target.value);
  updateUI(false);

  if (API_MODE) {
    apiCall("/api/volume", "POST", { volume: state.volume });
  }
});

progressBar.addEventListener("input", () => {
  const track = getCurrentTrack();

  if (!track) {
    return;
  }

  state.position =
    (Number(progressBar.value) / 100) * track.duration;

  updateUI(false);

  if (API_MODE) {
    apiCall("/api/seek", "POST", { seconds: state.position });
  }
});

searchInput.addEventListener("input", () => {
  renderPlaylist(true);
});

setInterval(() => {
  const track = getCurrentTrack();

  if (!track || !state.playing || API_MODE) {
    return;
  }

  state.position += 1;

  if (state.position >= track.duration) {
    if (state.repeat) {
      state.position = 0;
    } else {
      nextTrack();
      return;
    }
  }

  updateUI(false);
}, 1000);

updateUI(true);