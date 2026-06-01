const API_MODE = true;

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

const playPauseBtn = document.getElementById("playPauseBtn");
const shuffleBtn = document.getElementById("shuffleBtn");
const repeatBtn = document.getElementById("repeatBtn");

const heroCover = document.getElementById("heroCover");
const largeCover = document.getElementById("largeCover");
const bottomCover = document.getElementById("bottomCover");

let lastPlaylistRenderKey = "";
let isSearchingYoutube = false;
let isSeeking = false;

let state = {
  currentPlaylist: "Découvertes",
  index: 0,
  playing: false,
  volume: 80,
  shuffle: false,
  repeat: false,
  position: 0,

  tracks: [],
  localTracks: [],
  isViewingLocalLibrary: false,

  playlists: {
    "Favoris": {
      icon: "🩵",
      tracks: []
    },

    "Découvertes": {
      icon: "🗺️",
      tracks: []
    }
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
  if (state.isViewingLocalLibrary) {
    return state.localTracks || [];
  }

  const playlist = state.playlists[state.currentPlaylist];

  if (!playlist) return [];

  return playlist.tracks || [];
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

function addOrUpdateYoutubeTrack(track, backendIndex) {
  const trackKey = track.webpage_url || `${track.title}-${track.artist}`;

  const existingIndex = state.tracks.findIndex(item => {
    const itemKey = item.webpage_url || `${item.title}-${item.artist}`;
    return item.source === "youtube" && itemKey === trackKey;
  });

  if (existingIndex !== -1) {
    state.tracks[existingIndex] = {
      ...state.tracks[existingIndex],
      title: track.title || "Titre inconnu",
      artist: track.artist || "YouTube",
      duration: track.duration || state.tracks[existingIndex].duration || 0,
      cover: track.cover || "",
      webpage_url: track.webpage_url || "",
      source: "youtube",
      backendIndex
    };

    if (!state.playlists["Découvertes"].tracks.includes(existingIndex)) {
      state.playlists["Découvertes"].tracks.push(existingIndex);
    }

    return existingIndex;
  }

  const newTrack = {
    title: track.title || "Titre inconnu",
    artist: track.artist || "YouTube",
    duration: track.duration || 0,
    cover: track.cover || "",
    webpage_url: track.webpage_url || "",
    source: "youtube",
    backendIndex
  };

  state.tracks.push(newTrack);
  const newIndex = state.tracks.length - 1;

  if (!state.playlists["Découvertes"].tracks.includes(newIndex)) {
    state.playlists["Découvertes"].tracks.push(newIndex);
  }

  return newIndex;
}

function addOrUpdateLocalTrack(track, backendIndex) {
  const existingIndex = state.tracks.findIndex(item => item.source === "local" && item.backendIndex === backendIndex);

  if (existingIndex !== -1) {
    state.tracks[existingIndex] = {
      ...state.tracks[existingIndex],
      title: track.title || state.tracks[existingIndex].title,
      artist: track.artist || state.tracks[existingIndex].artist,
      album: track.album || state.tracks[existingIndex].album,
      duration: track.duration || state.tracks[existingIndex].duration,
      source: "local",
      backendIndex
    };
    return existingIndex;
  }

  const newTrack = {
    title: track.title || "Titre inconnu",
    artist: track.artist || "Local",
    album: track.album || "",
    duration: track.duration || 0,
    cover: track.cover || "",
    source: "local",
    backendIndex
  };

  state.tracks.push(newTrack);
  return state.tracks.length - 1;
}

async function loadLocalLibrary() {
  try {
    const result = await apiCall("/api/library");

    state.tracks = state.tracks.filter(track => track.source !== "local");
    state.localTracks = [];
    state.localTracks = [];

    result.tracks.forEach(track => {
      const trackIndex = addOrUpdateLocalTrack(track, track.backendIndex);
      state.localTracks.push(trackIndex);
      state.localTracks.push(trackIndex);
    });

    state.isViewingLocalLibrary = true;
    updateUI(true);
  } catch (error) {
    console.error("Impossible de charger la bibliothèque locale :", error.message);
    alert("Impossible de charger la bibliothèque locale.");
  }
}

function syncStatus(status) {
  if (!status) return;

  state.playing = Boolean(status.playing);
  state.position = Number(status.position || 0);
  state.volume = Number(status.volume || state.volume);
  state.shuffle = Boolean(status.shuffle);
  state.repeat = Boolean(status.repeat);

  const backendIndex = Number(status.index || 1) - 1;

  if (status.mode === "local") {
    state.isViewingLocalLibrary = true;
    const currentIndex = state.tracks.findIndex(
      track => track.source === "local" && track.backendIndex === backendIndex
    );

    if (currentIndex !== -1) {
      state.index = currentIndex;
      if (status.duration !== undefined) {
        state.tracks[currentIndex].duration = Number(status.duration || 0);
      }
      if (status.track) {
        state.tracks[currentIndex].title = status.track;
      }
      if (status.artist) {
        state.tracks[currentIndex].artist = status.artist;
      }
    }

    return;
  }

  if (Array.isArray(status.playlist)) {
    status.playlist.forEach((track, index) => {
      addOrUpdateYoutubeTrack(track, index);
    });
  }

  const currentIndex = state.tracks.findIndex(
    track => track.source === "youtube" && track.backendIndex === backendIndex
  );

  if (currentIndex !== -1) {
    state.index = currentIndex;

    if (status.duration !== undefined) {
      state.tracks[currentIndex].duration = Number(status.duration || 0);
    }

    if (status.cover) {
      state.tracks[currentIndex].cover = status.cover;
    }

    if (status.track) {
      state.tracks[currentIndex].title = status.track;
    }

    if (status.artist) {
      state.tracks[currentIndex].artist = status.artist;
    }
  }
}

async function refreshStatusFromPython() {
  try {
    const result = await apiCall("/api/status");

 if (result.status && !isSeeking) {
  syncStatus(result.status);
  updateUI(false);
}
  } catch (error) {
    console.log("Status non disponible :", error.message);
  }
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

    const emoji = state.playlists[name].icon || "✨";
    const count = state.playlists[name].tracks.length;

    const canDelete = true;

    card.innerHTML = `
      <span>${emoji}</span>

      <div>
        <strong>${name}</strong>
        <small>${count} titre${count > 1 ? "s" : ""}</small>
      </div>

      ${
        canDelete
          ? `
            <button
              class="delete-playlist-btn"
              title="Supprimer"
            >
              ❌
            </button>
          `
          : ""
      }
    `;

    card.addEventListener("click", () => {
      state.currentPlaylist = name;
      state.isViewingLocalLibrary = false;
      updateUI(true);
    });

    const deleteBtn = card.querySelector(".delete-playlist-btn");

    if (deleteBtn) {
      deleteBtn.addEventListener("click", event => {
        event.stopPropagation();
        deletePlaylist(name);
      });
    }

    playlistMenu.appendChild(card);
  });
}

function renderPlaylist(force = false) {
  playlistTitle.textContent = state.isViewingLocalLibrary ? "Bibliothèque locale" : state.currentPlaylist;

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
    `${state.currentPlaylist}|${filter}|${indexes.join(",")}|${state.index}|${state.playing}`;

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
            Cherche une musique avec YouTube.
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

      <div class="track-actions">
        <button class="icon-btn favorite-btn ${
          state.playlists["Favoris"].tracks.includes(trackIndex)
            ? "active-favorite"
            : ""
        }">
          ${
            state.playlists["Favoris"].tracks.includes(trackIndex)
              ? "🩵"
              : "🤍"
          }
        </button>

        <button class="icon-btn add-track-btn" title="Ajouter à une playlist">+</button>
        <button class="icon-btn remove-track-btn" title="Retirer de la playlist">🗑️</button>
      </div>
    `;

    row.addEventListener("click", () => {
      playTrack(trackIndex);
    });

    row.querySelector(".favorite-btn").addEventListener("click", event => {
      event.stopPropagation();
      toggleFavorite(trackIndex);
    });

    row.querySelector(".add-track-btn").addEventListener("click", event => {
      event.stopPropagation();
      addTrackToPlaylist(trackIndex);
    });

    row.querySelector(".remove-track-btn").addEventListener("click", event => {
      event.stopPropagation();
      removeTrackFromPlaylist(trackIndex);
    });

    playlistContainer.appendChild(row);
  });
}

function renderStatus() {
  const track = getCurrentTrack();

  statusBox.innerHTML = `
    <strong>Piste :</strong> ${track ? track.title : "Aucune"}<br>
    <strong>Playlist :</strong> ${state.isViewingLocalLibrary ? "Bibliothèque locale" : state.currentPlaylist}<br>
    <strong>Lecture :</strong> ${state.playing ? "Oui" : "Non"}<br>
    <strong>Shuffle :</strong> ${state.shuffle ? "ON" : "OFF"}<br>
    <strong>Repeat :</strong> ${state.repeat ? "ON" : "OFF"}<br>
    <strong>Temps :</strong> ${formatTime(state.position)}
  `;
}

function createPlaylist() {
  const name = prompt("Nom de la playlist :");

  if (!name || !name.trim()) {
    return;
  }

  const icon = prompt("Choisis un emoji pour la playlist 🎵") || "✨";

  const cleanName = name.trim();

  if (state.playlists[cleanName]) {
    alert("Cette playlist existe déjà.");
    return;
  }

  state.playlists[cleanName] = {
    icon: icon,
    tracks: []
  };

  state.currentPlaylist = cleanName;

  updateUI(true);
}

function deletePlaylist(name) {

  if (
    name === "Favoris" ||
    name === "Découvertes"
  ) {
    return;
  }

  const confirmDelete = confirm(
    `Supprimer la playlist "${name}" ?`
  );

  if (!confirmDelete) {
    return;
  }

  delete state.playlists[name];

  if (state.currentPlaylist === name) {
    state.currentPlaylist = "Découvertes";
  }

  updateUI(true);
}

function toggleFavorite(trackIndex) {
  const favorites = state.playlists["Favoris"].tracks;

  if (favorites.includes(trackIndex)) {
    state.playlists["Favoris"].tracks =
      favorites.filter(index => index !== trackIndex);
  } else {
    favorites.push(trackIndex);
  }

  updateUI(true);
}

function addTrackToPlaylist(trackIndex) {
  const names = Object.keys(state.playlists).filter(
    name => name !== "Découvertes" && name !== "Favoris"
  );

  if (names.length === 0) {
    alert("Crée d'abord une playlist.");
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

  if (!state.playlists[playlistName].tracks.includes(trackIndex)) {
    state.playlists[playlistName].tracks.push(trackIndex);
  }

  updateUI(true);
}

async function removeTrackFromPlaylist(trackIndex) {
  const playlist = state.playlists[state.currentPlaylist];

  if (!playlist) return;

  const track = state.tracks[trackIndex];

  state.playlists[state.currentPlaylist].tracks =
    playlist.tracks.filter(index => index !== trackIndex);

  if (state.currentPlaylist === "Découvertes" && track?.source === "youtube") {
    try {
      await apiCall("/api/remove_youtube", "POST", {
        index: track.backendIndex
      });
    } catch (error) {
      console.log("Suppression côté Python impossible :", error.message);
    }
  }

  if (state.index === trackIndex) {
    state.playing = false;
    state.position = 0;

    const remaining = state.playlists[state.currentPlaylist].tracks;

    if (remaining.length > 0) {
      state.index = remaining[0];
    }
  }

  updateUI(true);
}

async function playTrack(index) {
  const track = state.tracks[index];

  if (!track) {
    return;
  }

  try {
    state.index = index;
    state.position = 0;
    state.playing = true;
    updateUI(true);

    const backendIndex =
      track.backendIndex !== undefined
        ? track.backendIndex
        : index;

    let result;
    if (track.source === "local") {
      result = await apiCall("/api/local_play", "POST", {
        index: backendIndex
      });
    } else {
      result = await apiCall("/api/play", "POST", {
        index: backendIndex
      });
    }

    if (result.status) {
      syncStatus(result.status);
    }

    updateUI(true);
    setTimeout(refreshStatusFromPython, 500);

  } catch (error) {
    alert("Erreur lecture : " + error.message);
  }
}
async function playPause() {
  try {
    const url = state.playing ? "/api/pause" : "/api/play";
    const result = await apiCall(url, "POST");

    if (result.status) {
      syncStatus(result.status);
    }

    updateUI(false);
    setTimeout(refreshStatusFromPython, 500);

  } catch (error) {
    alert("Erreur play/pause : " + error.message);
  }
}

async function stopTrack() {
  try {
    const result = await apiCall("/api/stop", "POST");

    if (result.status) {
      syncStatus(result.status);
    }

    state.playing = false;
    state.position = 0;

    updateUI(false);
    setTimeout(refreshStatusFromPython, 500);

  } catch (error) {
    alert("Erreur stop : " + error.message);
  }
}

async function nextTrack() {
  try {
    const result = await apiCall("/api/next", "POST");

    if (result.status) {
      syncStatus(result.status);
    }

    updateUI(true);
    setTimeout(refreshStatusFromPython, 500);

  } catch (error) {
    alert("Erreur suivant : " + error.message);
  }
}

async function previousTrack() {
  try {
    const result = await apiCall("/api/prev", "POST");

    if (result.status) {
      syncStatus(result.status);
    }

    updateUI(true);
    setTimeout(refreshStatusFromPython, 500);

  } catch (error) {
    alert("Erreur précédent : " + error.message);
  }
}

async function searchYoutube() {
  const youtubeButton = document.getElementById("youtubeBtn");
  const query = searchInput.value.trim();

  if (!query) {
    alert("Écris une musique dans la barre de recherche.");
    return;
  }

  if (isSearchingYoutube) {
    return;
  }

  isSearchingYoutube = true;
  youtubeButton.classList.add("loading");
  youtubeButton.textContent = "Recherche...";

  try {
    const data = await apiCall("/api/youtube", "POST", {
      query
    });

    if (data.track) {
      const backendIndex = data.status?.playlist
        ? data.status.playlist.length - 1
        : state.playlists["Découvertes"].tracks.length;

      const newIndex = addOrUpdateYoutubeTrack(data.track, backendIndex);

      state.currentPlaylist = "Découvertes";
      state.index = newIndex;
      state.playing = true;
      state.position = 0;
    }

    if (data.status) {
      syncStatus(data.status);
    }

    searchInput.value = "";
    updateUI(true);
    setTimeout(refreshStatusFromPython, 700);

  } catch (error) {
    alert("Erreur YouTube : " + error.message);
  } finally {
    isSearchingYoutube = false;
    youtubeButton.classList.remove("loading");
    youtubeButton.textContent = "YouTube";
  }
}

mobileMenuBtn.addEventListener("click", event => {
  event.stopPropagation();
  sidebar.classList.toggle("open");
});

document.addEventListener("click", event => {
  const clickInsideSidebar = sidebar.contains(event.target);
  const clickOnMenuButton = mobileMenuBtn.contains(event.target);

  if (!clickInsideSidebar && !clickOnMenuButton) {
    sidebar.classList.remove("open");
  }
});

document.getElementById("createPlaylistBtn").addEventListener("click", () => {
  createPlaylist();
});


document.getElementById("loadBtn").addEventListener("click", () => {
  loadLocalLibrary();
});


document.getElementById("heroPlayBtn").addEventListener("click", async () => {
  await loadLocalLibrary();
  const localTracks = state.localTracks;
  if (localTracks.length > 0) {
    playTrack(localTracks[0]);
  }
});


document.getElementById("youtubeBtn").addEventListener("click", () => {
  searchYoutube();
});

    searchInput.addEventListener("keypress", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        searchYoutube();
      }
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

shuffleBtn.addEventListener("click", async () => {
  try {
    const result = await apiCall("/api/shuffle", "POST");

    if (result.status) {
      syncStatus(result.status);
    }

    updateUI(false);
  } catch (error) {
    alert("Erreur shuffle : " + error.message);
  }
});

repeatBtn.addEventListener("click", async () => {
  try {
    const result = await apiCall("/api/repeat", "POST");

    if (result.status) {
      syncStatus(result.status);
    }

    updateUI(false);
  } catch (error) {
    alert("Erreur repeat : " + error.message);
  }
});

progressBar.addEventListener("input", () => {
  const track = getCurrentTrack();

  if (!track || !track.duration) {
    return;
  }

  isSeeking = true;
  state.position = (Number(progressBar.value) / 100) * track.duration;

  currentTime.textContent = formatTime(state.position);
});

progressBar.addEventListener("change", async () => {
  const track = getCurrentTrack();

  if (!track || !track.duration) {
    isSeeking = false;
    return;
  }

  const seconds = (Number(progressBar.value) / 100) * track.duration;

  try {
    await apiCall("/api/seek", "POST", {
      seconds
    });

    state.position = seconds;
    updateUI(false);
    setTimeout(refreshStatusFromPython, 400);

  } catch (error) {
    console.log("Erreur seek :", error.message);
  } finally {
    isSeeking = false;
  }
});

searchInput.addEventListener("input", () => {
  renderPlaylist(true);
});

searchInput.addEventListener("keydown", event => {
  if (event.key === "Enter") {
    event.preventDefault();
    searchYoutube();
  }
});

document.addEventListener("keydown", event => {
  const activeElement = document.activeElement;
  const isWriting =
    activeElement &&
    (
      activeElement.tagName === "INPUT" ||
      activeElement.tagName === "TEXTAREA"
    );

  if (isWriting) {
    return;
  }

  if (event.code === "Space") {
    event.preventDefault();
    playPause();
  }
});


setInterval(() => {
  refreshStatusFromPython();
}, 1000);

loadLocalLibrary();
updateUI(true);