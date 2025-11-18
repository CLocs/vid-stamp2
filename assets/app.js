const vid = document.getElementById('vid');
const playBtn = document.getElementById('playBtn');
const openBtn = document.getElementById('openBtn');
const filePicker = document.getElementById('filePicker');
const saveBtn = document.getElementById('saveBtn');
const markBtn = document.getElementById('markBtn');
const undoBtn = document.getElementById('undoBtn');
const statusEl = document.getElementById('status');
const markList = document.getElementById('markList');
const countEl = document.getElementById('count');
const roleModal = document.getElementById('roleModal');
const roleAttending = document.getElementById('roleAttending');
const roleResident = document.getElementById('roleResident');
const nextBtn = document.getElementById('nextBtn');
const roleDisplay = document.getElementById('roleDisplay');
const editRoleBtn = document.getElementById('editRoleBtn');

let lastMarkTs = -999;
let selectedRole = null; // Will be 'attending' or 'resident' after submit
const DEBOUNCE = 0.25; // seconds

function fmt(s) { return s.toFixed(3); }
function setStatus(msg) { statusEl.textContent = msg; }

function getAPI() {
  if (!window.pywebview || !window.pywebview.api) {
    throw new Error('pywebview API not ready');
  }
  return window.pywebview.api;
}

function renderMarks(marks) {
  markList.innerHTML = '';
  marks.forEach(s => {
    const li = document.createElement('li');
    li.textContent = fmt(s);
    markList.appendChild(li);
  });
  countEl.textContent = marks.length;
}

async function refreshMarks() {
  const marks = await getAPI().get_marks();
  renderMarks(marks);
}

async function doMark() {
  const t = vid.currentTime || 0;
  if (t - lastMarkTs < DEBOUNCE) {
    setStatus('(debounced)');
    return;
  }
  lastMarkTs = t;
  const res = await getAPI().mark(t);
  setStatus(`Marked @ ${fmt(t)}s`);
  await refreshMarks();
}

// UI wiring
playBtn.addEventListener('click', () => {
  if (vid.paused) { vid.play(); playBtn.textContent = 'Pause'; }
  else { vid.pause(); playBtn.textContent = 'Play'; }
});

markBtn.addEventListener('dblclick', doMark);
undoBtn.addEventListener('click', async () => {
  await getAPI().undo();
  await refreshMarks();
});

function showRoleModal() {
  roleModal.classList.add('show');
  // Pre-select the current role if one is already selected
  if (selectedRole) {
    document.querySelector(`input[name="role"][value="${selectedRole}"]`).checked = true;
  }
}

function hideRoleModal() {
  roleModal.classList.remove('show');
}

function updateRoleDisplay() {
  if (selectedRole) {
    const roleText = selectedRole.charAt(0).toUpperCase() + selectedRole.slice(1);
    roleDisplay.textContent = roleText;
  } else {
    roleDisplay.textContent = '-';
  }
}

nextBtn.addEventListener('click', () => {
  const selected = document.querySelector('input[name="role"]:checked');
  if (!selected) {
    setStatus('Please select Attending or Resident');
    return;
  }
  selectedRole = selected.value;
  hideRoleModal();
  updateRoleDisplay();
  setStatus(`Role selected: ${selectedRole.charAt(0).toUpperCase() + selectedRole.slice(1)}`);
});

editRoleBtn.addEventListener('click', () => {
  showRoleModal();
});

saveBtn.addEventListener('click', async () => {
  if (!selectedRole) {
    setStatus('Please select and submit a role first');
    return;
  }
  const res = await getAPI().save_csv(null, selectedRole);
  setStatus(`Saved ${res.count} marks → ${res.saved_to}`);
});

// Open local video using native file dialog
openBtn.addEventListener('click', async () => {
  try {
    const result = await getAPI().open_video_file();
    if (result.error) {
      setStatus(`Error: ${result.error}`);
      return;
    }
    if (!result.file_path) {
      setStatus('No file selected');
      return;
    }
    
    // Read the video file through Python and get it as a data URL
    // This avoids file:// URL security restrictions
    const filePath = result.file_path;
    const fileName = filePath.split(/[/\\]/).pop(); // Get filename
    
    const videoData = await getAPI().read_video_file(filePath);
    if (videoData.error) {
      setStatus(`Error: ${videoData.error}`);
      return;
    }
    
    // Create blob URL from base64 data
    const byteCharacters = atob(videoData.data);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: videoData.mime_type || 'video/mp4' });
    const blobUrl = URL.createObjectURL(blob);
    
    vid.src = blobUrl;
    vid.load();
    vid.play().then(() => (playBtn.textContent = 'Pause')).catch(e => {
      console.error('Error playing video:', e);
      setStatus(`Loaded: ${videoData.file_name || fileName} (click Play to start)`);
    });
    setStatus(`Loaded: ${videoData.file_name || fileName}`);
  } catch (e) {
    console.error('Error opening file:', e);
    setStatus('Error opening file');
  }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  if (e.key === ' ') { e.preventDefault(); playBtn.click(); }
  if (e.key === 'm' || e.key === 'M') { e.preventDefault(); doMark(); }
  if (e.key === 'u' || e.key === 'U') { e.preventDefault(); undoBtn.click(); }
});

// Wait for pywebview to be ready before accessing the API
window.addEventListener('pywebviewready', () => {
  refreshMarks().catch(console.error);
  // Show role selection modal on app launch
  showRoleModal();
});
