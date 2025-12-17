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
const pgyGroup = document.getElementById('pgyGroup');
const pgySelect = document.getElementById('pgySelect');
const subtitleBox = document.getElementById('subtitleBox');

let lastMarkTs = -999;
let selectedRole = null; // Will be 'attending' or 'resident' after submit
let pgyValue = null; // PGY value (1-7) for residents, null for attendings
let subtitles = []; // Array of subtitle objects with start, end, text
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
  // Pre-select the current role and PGY if already selected
  if (selectedRole) {
    document.querySelector(`input[name="role"][value="${selectedRole}"]`).checked = true;
    updateRoleBasedFields();
  }
  if (pgyValue) {
    pgySelect.value = pgyValue;
  } else {
    pgySelect.value = '';
  }
  // Focus on PGY select if resident is selected
  if (selectedRole === 'resident') {
    pgySelect.focus();
  }
}

function updateRoleBasedFields() {
  const selected = document.querySelector('input[name="role"]:checked');
  if (selected && selected.value === 'resident') {
    pgyGroup.style.display = 'block';
    pgySelect.setAttribute('required', 'required');
  } else {
    pgyGroup.style.display = 'none';
    pgySelect.removeAttribute('required');
  }
}

function hideRoleModal() {
  roleModal.classList.remove('show');
}

function updateRoleDisplay() {
  if (selectedRole) {
    const roleText = selectedRole === 'resident' ? 'Resident or Fellow' : 'Attending';
    if (selectedRole === 'resident' && pgyValue) {
      roleDisplay.textContent = `${roleText} PGY${pgyValue}`;
    } else {
      roleDisplay.textContent = roleText;
    }
  } else {
    roleDisplay.textContent = '-';
  }
}

// Update field visibility when role changes
roleAttending.addEventListener('change', updateRoleBasedFields);
roleResident.addEventListener('change', updateRoleBasedFields);

nextBtn.addEventListener('click', () => {
  const selected = document.querySelector('input[name="role"]:checked');
  
  if (!selected) {
    setStatus('Please select Attending or Resident or Fellow');
    return;
  }
  
  if (selected.value === 'resident') {
    const pgyVal = pgySelect.value;
    if (!pgyVal) {
      setStatus('Please select PGY');
      pgySelect.focus();
      return;
    }
    pgyValue = pgyVal;
  } else {
    pgyValue = null;
  }
  
  selectedRole = selected.value;
  hideRoleModal();
  updateRoleDisplay();
  setStatus(`Role selected: ${selectedRole.charAt(0).toUpperCase() + selectedRole.slice(1)}`);
});

editRoleBtn.addEventListener('click', () => {
  showRoleModal();
});

// Allow Enter key to submit the modal
pgySelect.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    nextBtn.click();
  }
});

saveBtn.addEventListener('click', async () => {
  if (!selectedRole) {
    setStatus('Please complete role selection first');
    return;
  }
  // For residents, pass PGY value in format "pgy1", "pgy2", etc.
  // For attendings, pass null (no last name)
  const nameValue = (selectedRole === 'resident' && pgyValue) ? `pgy${pgyValue}` : null;
  const res = await getAPI().save_csv(null, selectedRole, nameValue);
  if (res.error) {
    setStatus(`Error saving: ${res.error}`);
    console.error('Save error:', res.error);
  } else {
    setStatus(`Saved ${res.count} marks → ${res.saved_to}`);
    console.log('File saved to:', res.saved_to);
  }
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
    
    // Get file:// URL from Python (handles path conversion correctly)
    const filePath = result.file_path;
    const fileName = filePath.split(/[/\\]/).pop(); // Get filename
    
    const videoUrlResult = await getAPI().get_video_url(filePath);
    if (videoUrlResult.error) {
      setStatus(`Error: ${videoUrlResult.error}`);
      return;
    }
    
    // Try to load SRT file with same base name
    const srtResult = await getAPI().load_srt_file(filePath);
    if (srtResult.error) {
      console.warn('Error loading SRT:', srtResult.error);
      subtitles = [];
    } else if (srtResult.subtitles) {
      subtitles = srtResult.subtitles;
      console.log(`Loaded ${subtitles.length} subtitles from ${srtResult.file_name}`);
    } else {
      subtitles = [];
      console.log('No SRT file found');
    }
    
    // Use file:// URL directly - works in pywebview's local context
    vid.src = videoUrlResult.url;
    vid.load();
    vid.play().then(() => (playBtn.textContent = 'Pause')).catch(e => {
      console.error('Error playing video:', e);
      setStatus(`Loaded: ${videoUrlResult.file_name || fileName} (click Play to start)`);
    });
    setStatus(`Loaded: ${videoUrlResult.file_name || fileName}${subtitles.length > 0 ? ` (${subtitles.length} subtitles)` : ''}`);
  } catch (e) {
    console.error('Error opening file:', e);
    setStatus('Error opening file');
  }
});

// Update subtitles based on video current time
function updateSubtitles() {
  const currentTime = vid.currentTime || 0;
  const activeSubtitle = subtitles.find(sub => 
    currentTime >= sub.start && currentTime <= sub.end
  );
  
  if (activeSubtitle) {
    subtitleBox.textContent = activeSubtitle.text;
  } else {
    subtitleBox.textContent = '';
  }
}

// Listen to video time updates to show subtitles
vid.addEventListener('timeupdate', updateSubtitles);

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
