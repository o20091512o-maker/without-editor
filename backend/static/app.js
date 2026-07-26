document.addEventListener('DOMContentLoaded', () => {
    // Initial Staggered Reveal Trigger
    const revealElements = () => {
        const reveals = document.querySelectorAll('.reveal');
        reveals.forEach((el, idx) => {
            setTimeout(() => {
                el.classList.add('visible');
            }, 100 + idx * 80);
        });
    };
    revealElements();

    const colabBanner = document.getElementById('colab-banner');
    const scenesContainer = document.getElementById('scenes-container');
    const addSceneBtn = document.getElementById('add-scene-btn');
    const removeSceneBtn = document.getElementById('remove-scene-btn');
    const generateBtn = document.getElementById('generate-btn');
    const statusArea = document.getElementById('status-area');
    const statusText = document.getElementById('status-text');
    const spinner = document.getElementById('spinner');
    const resultArea = document.getElementById('result-area');
    const resultVideo = document.getElementById('result-video');
    const downloadBtn = document.getElementById('download-btn');

    let scenes = [];
    const MAX_SCENES = 30;

    // Check health on load
    fetch('/api/health-colab')
        .then(res => res.json())
        .then(data => {
            if (data.status !== 'online') {
                colabBanner?.classList.remove('hidden');
            }
        })
        .catch(() => {
            colabBanner?.classList.remove('hidden');
        });

    function checkReadyState() {
        let isReady = scenes.length > 0;
        for (const scene of scenes) {
            if (!scene.uploadedImageName) {
                isReady = false;
                break;
            }
        }
        if (generateBtn) generateBtn.disabled = !isReady;
    }

    function createSceneCard(index) {
        const card = document.createElement('div');
        card.className = 'glass scene-card reveal visible';
        card.id = `scene-${index}`;

        const title = document.createElement('h3');
        title.textContent = `Scene ${index + 1}`;
        card.appendChild(title);

        // File upload wrapper
        const fileWrapper = document.createElement('div');
        fileWrapper.className = 'file-wrapper';

        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'image/png, image/jpeg';

        const fileLabel = document.createElement('div');
        fileLabel.className = 'file-label';
        fileLabel.innerHTML = '<span class="icon">📁</span> Drop or click to upload sticker image';

        fileWrapper.appendChild(fileInput);
        fileWrapper.appendChild(fileLabel);
        card.appendChild(fileWrapper);

        const textArea = document.createElement('textarea');
        textArea.rows = 3;
        textArea.placeholder = `Enter text for scene ${index + 1} (optional)...`;
        card.appendChild(textArea);

        const statusSpan = document.createElement('span');
        statusSpan.className = 'upload-status';
        card.appendChild(statusSpan);

        scenesContainer.appendChild(card);

        const sceneData = {
            fileInput,
            textArea,
            fileWrapper,
            uploadedImageName: null,
            card
        };
        
        scenes.push(sceneData);

        fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            if (file.size > 10 * 1024 * 1024) {
                alert('File too large. Max 10MB.');
                fileInput.value = '';
                return;
            }

            statusSpan.textContent = 'Uploading...';
            statusSpan.className = 'upload-status';
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                fileInput.disabled = true;
                const res = await fetch('/api/upload-image', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Upload failed');
                
                sceneData.uploadedImageName = data.image_name || data.filename;
                statusSpan.textContent = '✓ Image uploaded successfully';
                statusSpan.className = 'upload-status success';
                fileWrapper.classList.add('uploaded');
                fileLabel.innerHTML = '<span class="icon">✅</span> ' + file.name;
                checkReadyState();
            } catch (err) {
                statusSpan.textContent = `Error: ${err.message}`;
                statusSpan.className = 'upload-status error';
                fileInput.value = '';
                sceneData.uploadedImageName = null;
                fileWrapper.classList.remove('uploaded');
                checkReadyState();
            } finally {
                fileInput.disabled = false;
            }
        });

        textArea.addEventListener('input', checkReadyState);
        updateButtons();
    }

    function removeSceneCard() {
        if (scenes.length <= 1) return;
        const sceneData = scenes.pop();
        sceneData.card.remove();
        updateButtons();
        checkReadyState();
    }

    function updateButtons() {
        if (addSceneBtn) addSceneBtn.disabled = scenes.length >= MAX_SCENES;
        if (removeSceneBtn) removeSceneBtn.disabled = scenes.length <= 1;
    }

    if (addSceneBtn) {
        addSceneBtn.addEventListener('click', () => {
            if (scenes.length < MAX_SCENES) {
                createSceneCard(scenes.length);
            }
        });
    }

    if (removeSceneBtn) {
        removeSceneBtn.addEventListener('click', () => {
            removeSceneCard();
        });
    }

    // Create Scene 1 initially
    createSceneCard(0);

    if (generateBtn) {
        generateBtn.addEventListener('click', async () => {
            generateBtn.disabled = true;
            if (addSceneBtn) addSceneBtn.disabled = true;
            if (removeSceneBtn) removeSceneBtn.disabled = true;
            
            statusArea.classList.remove('hidden');
            statusArea.classList.add('visible');
            spinner.style.display = 'inline-block';
            statusText.textContent = "Starting generation...";
            resultArea.classList.add('hidden');

            const payload = {
                scenes: scenes.map(s => ({
                    image_name: s.uploadedImageName,
                    text: s.textArea.value.trim()
                })),
                style: "sticker"
            };

            try {
                const res = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                
                if (res.ok && data.job_id) {
                    pollStatus(data.job_id);
                } else {
                    statusText.textContent = `Error: ${data.detail || 'Failed to start job'}`;
                    spinner.style.display = 'none';
                    resetForm();
                }
            } catch (err) {
                statusText.textContent = `Error: ${err.message}`;
                spinner.style.display = 'none';
                resetForm();
            }
        });
    }

    function getProgressLabel(status) {
        if (!status) return 'Processing...';
        if (status.startsWith('generating_audio')) return '🎙️ Generating audio... ' + extractScene(status);
        if (status.startsWith('aligning')) return '📝 Aligning words... ' + extractScene(status);
        if (status === 'rendering') return '🎬 Rendering video...';
        if (status === 'completed') return '✅ Done!';
        if (status === 'failed') return '❌ Generation failed';
        if (status === 'pending') return '⏳ Waiting in queue...';
        return status;
    }

    function extractScene(status) {
        const match = status.match(/\(scene (\d+)\)/);
        return match ? `(Scene ${match[1]})` : '';
    }

    function pollStatus(jobId) {
        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/api/status/${jobId}`);
                const data = await res.json();

                const progressBarFill = document.getElementById('progress-bar-fill');
                const progressPercentage = document.getElementById('progress-percentage');

                const pct = (data.progress !== undefined && data.progress !== null) ? data.progress : 0;
                if (progressBarFill) progressBarFill.style.width = `${pct}%`;
                if (progressPercentage) progressPercentage.textContent = `${pct}%`;

                if (data.status === 'failed') {
                    clearInterval(interval);
                    statusText.textContent = `❌ ${data.error || 'Generation failed'}`;
                    spinner.style.display = 'none';
                    resetForm();
                } else if (data.status === 'completed') {
                    clearInterval(interval);
                    statusText.textContent = '✅ Video ready!';
                    if (progressBarFill) progressBarFill.style.width = '100%';
                    if (progressPercentage) progressPercentage.textContent = '100%';
                    spinner.style.display = 'none';
                    resultVideo.src = `/api/download/${jobId}`;
                    downloadBtn.href = `/api/download/${jobId}`;
                    resultArea.classList.remove('hidden');
                    resultArea.classList.add('visible');
                    resetForm();
                } else {
                    statusText.textContent = getProgressLabel(data.status);
                }
            } catch (err) {
                clearInterval(interval);
                statusText.textContent = `Connection error: ${err.message}`;
                spinner.style.display = 'none';
                resetForm();
            }
        }, 1000);
    }

    function resetForm() {
        generateBtn.disabled = false;
        checkReadyState();
        updateButtons();
    }
});
