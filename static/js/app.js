/**
 * Ollamometer Frontend JavaScript
 */

// Load models from API and display them
async function loadModels() {
    const container = document.getElementById('models-container');
    const loading = document.getElementById('models-loading');
    const error = document.getElementById('ollama-error');

    try {
        // First check if Ollama is available
        const statusResponse = await fetch('/api/status');
        const statusData = await statusResponse.json();

        if (!statusData.ollama_available) {
            loading.style.display = 'none';
            error.style.display = 'block';
            return;
        }

        // Load models
        const response = await fetch('/api/models');
        const data = await response.json();

        // Store model info globally
        allModels = data.models;

        // Hide loading, show container
        loading.style.display = 'none';
        container.style.display = 'block';

        // Render models in multi-select dropdown
        const select = document.getElementById('models-select');
        select.innerHTML = '';

        data.models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.name;
            option.selected = model.downloaded; // Auto-select downloaded models

            // Format: "model-name [Ready]" or "model-name [Need Pull]"
            const badge = model.downloaded ? '[Ready]' : '[Need Pull]';
            option.textContent = `${model.name} ${badge}`;

            // Store download status as data attribute
            option.dataset.downloaded = model.downloaded;

            select.appendChild(option);
        });

        // Add change listener to select element
        select.addEventListener('change', updateTotalTests);

        updateTotalTests();

    } catch (err) {
        console.error('Error loading models:', err);
        loading.style.display = 'none';
        error.style.display = 'block';
        error.innerHTML = `ERROR: ${err.message}`;
    }
}

// Global variable to store model info
let allModels = [];

// Start benchmark process
async function startBenchmark() {
    // Get selected models from multi-select
    const select = document.getElementById('models-select');
    const selectedModels = Array.from(select.selectedOptions).map(option => option.value);

    // Get selected prompts
    const selectedPrompts = Array.from(
        document.querySelectorAll('.prompt-item input[type="checkbox"]:checked')
    ).map(cb => cb.value);

    // Get runs
    const runs = parseInt(document.getElementById('runs-per-test').value);

    console.log('Starting benchmark with:', {
        models: selectedModels,
        prompts: selectedPrompts,
        runs: runs
    });

    // Check which models need to be pulled
    const modelsToPull = selectedModels.filter(modelName => {
        const modelInfo = allModels.find(m => m.name === modelName);
        return modelInfo && !modelInfo.downloaded;
    });

    // If any models need pulling, pull them first
    if (modelsToPull.length > 0) {
        console.log('Models need pulling:', modelsToPull);
        await pullModelsSequentially(modelsToPull);

        // Reload model list to update status
        await loadModels();
    }

    // Start benchmark
    try {
        const response = await fetch('/api/benchmark', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                models: selectedModels,
                prompts: selectedPrompts,
                runs: runs
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to start benchmark');
        }

        const data = await response.json();
        console.log('Benchmark started:', data);

        // Redirect to progress page
        window.location.href = '/progress';

    } catch (error) {
        console.error('Error starting benchmark:', error);
        alert('Failed to start benchmark: ' + error.message);
    }
}

// Pull models sequentially with progress modal
async function pullModelsSequentially(models) {
    const modal = document.getElementById('progress-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalStatus = document.getElementById('modal-status');
    const modalProgress = document.getElementById('modal-progress-fill');
    const modalDetails = document.getElementById('modal-details');

    for (let i = 0; i < models.length; i++) {
        const model = models[i];

        // Update modal title
        modalTitle.textContent = `Downloading Models (${i + 1}/${models.length})`;
        modalStatus.textContent = `Preparing to download ${model}...`;
        modalProgress.style.width = '0%';
        modalDetails.textContent = '';

        // Show modal
        modal.style.display = 'flex';

        try {
            // Start the pull
            const response = await fetch('/api/pull', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model: model })
            });

            if (!response.ok) {
                throw new Error(`Failed to start pull: ${response.statusText}`);
            }

            // Connect to SSE for progress updates
            await new Promise((resolve, reject) => {
                const eventSource = new EventSource('/api/progress');

                eventSource.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    console.log('Progress update:', data);

                    if (data.status === 'idle') {
                        // No operation running
                        return;
                    }

                    // Update modal with progress
                    modalStatus.textContent = data.message || 'Downloading...';

                    if (data.progress !== undefined) {
                        modalProgress.style.width = (data.progress * 100) + '%';
                    }

                    if (data.completed && data.total) {
                        const mb_completed = (data.completed / (1024 * 1024)).toFixed(1);
                        const mb_total = (data.total / (1024 * 1024)).toFixed(1);
                        modalDetails.textContent = `${mb_completed} MB / ${mb_total} MB`;
                    }

                    // Handle completion
                    if (data.status === 'complete') {
                        modalProgress.style.width = '100%';
                        eventSource.close();
                        setTimeout(() => resolve(), 500);
                    }

                    // Handle errors
                    if (data.status === 'error') {
                        eventSource.close();
                        reject(new Error(data.error || 'Download failed'));
                    }
                };

                eventSource.onerror = (error) => {
                    console.error('SSE error:', error);
                    eventSource.close();
                    reject(new Error('Connection lost'));
                };
            });

            console.log(`Successfully pulled ${model}`);

        } catch (error) {
            console.error(`Error pulling ${model}:`, error);
            alert(`Failed to download ${model}: ${error.message}`);
            modal.style.display = 'none';
            throw error;
        }
    }

    // Hide modal
    modal.style.display = 'none';
}
