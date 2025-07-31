document.addEventListener('DOMContentLoaded', () => {
    // --- Configuration ---
    const API_BASE_URL = 'http://127.0.0.1:8000';
    const TOKEN_STORAGE_KEY = 'g7_auth_token';
    const USERNAME_STORAGE_KEY = 'g7_auth_username';

    // --- DOM Elements ---
    const mainCard = document.getElementById('main-card');
    const messageArea = document.getElementById('message-area');
    const loadingSpinner = document.getElementById('loading-spinner');
    const loadingText = document.getElementById('loading-text');

    // Auth Section
    const authSection = document.getElementById('auth-section');
    const loginBtn = document.getElementById('login-btn');
    const registerBtn = document.getElementById('register-btn');
    const authUsernameInput = document.getElementById('auth-username');
    const authPasswordInput = document.getElementById('auth-password');
    const togglePasswordVisibilityBtn = document.getElementById('toggle-password-visibility');
    const eyeIcon = document.getElementById('eye-icon');
    const eyeOffIcon = document.getElementById('eye-off-icon');

    // Dashboard Section
    const dashboardSection = document.getElementById('dashboard-section');
    const displayUsernameSpan = document.getElementById('display-username');
    const uploadAudioForm = document.getElementById('upload-audio-form');
    const audioFileInput = document.getElementById('audio-file');
    const logoutBtn = document.getElementById('logout-btn');

    // Tabs and Panels
    const audioTab = document.getElementById('audio-tab');
    const transcriptsTab = document.getElementById('transcripts-tab');
    const audioPanel = document.getElementById('audio-panel');
    const transcriptPanel = document.getElementById('transcript-panel');
    const audioFileList = document.getElementById('audio-file-list');
    const transcriptFileList = document.getElementById('transcript-file-list');

    // --- Utility Functions ---

    function displayMessage(message, type = 'info') {
        messageArea.textContent = message;
        messageArea.className = 'mb-6 p-3 rounded-lg text-center transition-all duration-300 ease-in-out';
        if (type === 'success') messageArea.classList.add('bg-green-100', 'text-green-800');
        else if (type === 'error') messageArea.classList.add('bg-red-100', 'text-red-800');
        else messageArea.classList.add('bg-blue-100', 'text-blue-800');
        setTimeout(() => { messageArea.classList.add('hidden'); }, 5000);
    }

    function showLoader(text = 'Processing...') {
        loadingText.textContent = text;
        loadingSpinner.classList.remove('hidden');
        document.querySelectorAll('button').forEach(btn => btn.disabled = true);
    }

    function hideLoader() {
        loadingSpinner.classList.add('hidden');
        document.querySelectorAll('button').forEach(btn => btn.disabled = false);
    }

    function getErrorMessage(detail) {
        if (typeof detail === 'string') return detail;
        if (Array.isArray(detail)) return detail.map(err => err.msg || JSON.stringify(err)).join('; ');
        return 'An unknown error occurred.';
    }
    
    // --- UI Update Functions ---

    function updateDashboardUI(show) {
        const token = localStorage.getItem(TOKEN_STORAGE_KEY);
        const username = localStorage.getItem(USERNAME_STORAGE_KEY);
        
        if (show && token && username) {
            authSection.classList.add('hidden');
            dashboardSection.classList.remove('hidden');
            displayUsernameSpan.textContent = username;
            mainCard.classList.remove('max-w-md');
            mainCard.classList.add('md:max-w-4xl');
            fetchAllFiles();
        } else {
            authSection.classList.remove('hidden');
            dashboardSection.classList.add('hidden');
            mainCard.classList.remove('md:max-w-4xl');
            mainCard.classList.add('max-w-md');
        }
    }

    function renderFileList(container, files, renderItemFunc, emptyMessage) {
        container.innerHTML = '';
        if (!files || files.length === 0) {
            container.innerHTML = `<p class="text-center text-gray-500 p-4">${emptyMessage}</p>`;
        } else {
            files.forEach(file => container.appendChild(renderItemFunc(file)));
        }
    }

    function createAudioItemElement(file) {
        const item = document.createElement('div');
        item.className = 'flex items-center justify-between p-3 bg-white rounded-lg shadow-sm';
        item.innerHTML = `
            <div class="flex items-center min-w-0 mr-4">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-5 h-5 text-purple-500 mr-3 flex-shrink-0"><path d="M9 18V5l7-3v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="16" cy="15" r="3"></circle></svg>
                <span class="font-medium text-gray-800 truncate" title="${file.original_filename}">${file.original_filename}</span>
            </div>
            <div class="flex items-center flex-shrink-0 space-x-2">
                <span class="text-sm text-gray-500">${(file.file_size / 1024).toFixed(2)} KB</span>
                <button data-id="${file.file_id}" data-type="audio" class="download-btn p-1.5 text-blue-600 hover:bg-blue-100 rounded-full transition-colors" title="Download Audio"><svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 pointer-events-none" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg></button>
                <button data-id="${file.file_id}" data-name="${file.original_filename}" data-type="audio" class="delete-btn p-1.5 text-red-600 hover:bg-red-100 rounded-full transition-colors" title="Delete Audio"><svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 pointer-events-none" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg></button>
            </div>
        `;
        return item;
    }

    function createTranscriptItemElement(file) {
        const item = document.createElement('div');
        item.className = 'flex items-center justify-between p-3 bg-white rounded-lg shadow-sm';
        const fileName = file.key.split('/').pop();
        item.innerHTML = `
            <div class="flex items-center min-w-0 mr-4">
                 <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                <span class="font-medium text-gray-800 truncate" title="${fileName}">${fileName}</span>
            </div>
            <div class="flex items-center flex-shrink-0 space-x-2">
                <span class="text-sm text-gray-500">${(file.size / 1024).toFixed(2)} KB</span>
                <button data-key="${file.key}" data-type="transcript" class="download-btn p-1.5 text-blue-600 hover:bg-blue-100 rounded-full transition-colors" title="Download Transcript"><svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 pointer-events-none" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg></button>
                <button data-key="${file.key}" data-name="${fileName}" data-type="transcript" class="delete-btn p-1.5 text-red-600 hover:bg-red-100 rounded-full transition-colors" title="Delete Transcript"><svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 pointer-events-none" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg></button>
            </div>
        `;
        return item;
    }

    // --- API Call Functions ---

    async function apiRequest(endpoint, options = {}) {
        const token = localStorage.getItem(TOKEN_STORAGE_KEY);
        const headers = new Headers(options.headers || {});
        if (token) {
            headers.append('Authorization', `Bearer ${token}`);
        }
        
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers });
            
            // Handle success with no content (for DELETE requests)
            if (response.status === 204) return null;
            
            const data = await response.json();
            if (!response.ok) {
                if (response.status === 401) handleLogout();
                throw new Error(getErrorMessage(data.detail));
            }
            return data;
        } catch (error) {
            displayMessage(error.message || 'A network error occurred.', 'error');
            throw error;
        }
    }

    async function fetchAllFiles() {
        audioFileList.innerHTML = `<p class="text-center text-gray-500 p-4">Loading audio files...</p>`;
        transcriptFileList.innerHTML = `<p class="text-center text-gray-500 p-4">Loading transcripts...</p>`;

        try {
            const [audioFiles, transcriptFiles] = await Promise.all([
                apiRequest('/files/audio'),
                apiRequest('/files/transcripts')
            ]);
            renderFileList(audioFileList, audioFiles, createAudioItemElement, 'No audio files uploaded yet.');
            renderFileList(transcriptFileList, transcriptFiles, createTranscriptItemElement, 'No transcripts available yet.');
        } catch (error) {
            audioFileList.innerHTML = `<p class="text-center text-red-500 p-4">Failed to load audio files.</p>`;
            transcriptFileList.innerHTML = `<p class="text-center text-red-500 p-4">Failed to load transcripts.</p>`;
        }
    }
    
    // --- Event Handlers ---

    async function handleAuth(isLogin) {
        const username = authUsernameInput.value.trim();
        const password = authPasswordInput.value.trim();
        if (!username || !password) return displayMessage('Username and password are required.', 'error');
        
        const endpoint = isLogin ? '/auth/login' : '/auth/register';
        const options = isLogin 
            ? { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams({ username, password }) }
            : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) };
        
        showLoader(isLogin ? 'Logging in...' : 'Registering...');
        try {
            const data = await apiRequest(endpoint, options);
            localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token);
            localStorage.setItem(USERNAME_STORAGE_KEY, username);
            displayMessage(`${isLogin ? 'Login' : 'Registration'} successful!`, 'success');
            updateDashboardUI(true);
        } catch (error) { /* Handled by apiRequest */ } 
        finally { hideLoader(); }
    }

    async function handleUploadAudio(event) {
        event.preventDefault();
        const file = audioFileInput.files[0];
        if (!file) return displayMessage('Please select a file to upload.', 'error');

        const formData = new FormData();
        formData.append('file', file);
        
        showLoader('Uploading file...');
        try {
            await apiRequest('/upload/audio', { method: 'POST', body: formData });
            displayMessage('File uploaded successfully!', 'success');
            audioFileInput.value = '';
            await fetchAllFiles();
        } catch (error) { /* Handled by apiRequest */ } 
        finally { hideLoader(); }
    }
    
    async function handleListInteraction(event) {
        const button = event.target.closest('button');
        if (!button) return;

        if (button.classList.contains('download-btn')) await handleDownload(button);
        if (button.classList.contains('delete-btn')) await handleDelete(button);
    }

    async function handleDownload(button) {
        const type = button.dataset.type;
        const id = button.dataset.id;
        const key = button.dataset.key;
        
        let endpoint = '';
        if (type === 'audio' && id) endpoint = `/files/audio/${id}/download`;
        else if (type === 'transcript' && key) endpoint = `/files/transcripts/download?key=${encodeURIComponent(key)}`;
        else return;
        
        showLoader('Preparing download...');
        try {
            const data = await apiRequest(endpoint);
            if (data.download_url) window.open(data.download_url, '_blank');
        } catch (error) { /* Handled by apiRequest */ } 
        finally { hideLoader(); }
    }

    async function handleDelete(button) {
        const type = button.dataset.type;
        const id = button.dataset.id;
        const key = button.dataset.key;
        const name = button.dataset.name;
        
        if (!confirm(`Are you sure you want to delete "${name}"? This action cannot be undone.`)) return;

        let endpoint = '';
        if (type === 'audio' && id) {
            endpoint = `/files/audio/${id}`;
        } else if (type === 'transcript' && key) {
            endpoint = `/files/transcripts?key=${encodeURIComponent(key)}`;
        } else {
            return;
        }

        showLoader('Deleting file...');
        try {
            const data = await apiRequest(endpoint, { method: 'DELETE' });
            displayMessage(data.message, 'success');
            await fetchAllFiles();
        } catch (error) { /* Handled by apiRequest */ } 
        finally { hideLoader(); }
    }

    function handleLogout() {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        localStorage.removeItem(USERNAME_STORAGE_KEY);
        displayMessage('You have been logged out.', 'info');
        updateDashboardUI(false);
    }

    function handleTabClick(event) {
        const isAudioTab = event.target.id === 'audio-tab';
        audioTab.className = isAudioTab ? 'tab-btn tab-active' : 'tab-btn tab-inactive';
        transcriptsTab.className = !isAudioTab ? 'tab-btn tab-active' : 'tab-btn tab-inactive';
        audioPanel.classList.toggle('hidden', !isAudioTab);
        transcriptPanel.classList.toggle('hidden', isAudioTab);
    }

    // --- Attach Event Listeners ---
    loginBtn.addEventListener('click', () => handleAuth(true));
    registerBtn.addEventListener('click', () => handleAuth(false));
    uploadAudioForm.addEventListener('submit', handleUploadAudio);
    logoutBtn.addEventListener('click', handleLogout);
    
    audioTab.addEventListener('click', handleTabClick);
    transcriptsTab.addEventListener('click', handleTabClick);
    
    audioFileList.addEventListener('click', handleListInteraction);
    transcriptFileList.addEventListener('click', handleListInteraction);
    
    togglePasswordVisibilityBtn.addEventListener('click', () => {
        const isPassword = authPasswordInput.type === 'password';
        authPasswordInput.type = isPassword ? 'text' : 'password';
        eyeIcon.classList.toggle('hidden', isPassword);
        eyeOffIcon.classList.toggle('hidden', !isPassword);
    });
    
    // --- Initial UI state check ---
    updateDashboardUI(!!localStorage.getItem(TOKEN_STORAGE_KEY));
});