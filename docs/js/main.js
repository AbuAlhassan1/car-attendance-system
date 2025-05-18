// API Configuration
const API_CONFIG = {
    local: {
        baseUrl: 'http://localhost:5001'
    },
    production: {
        baseUrl: 'https://car-attendance-api.yourdomain.com' // You'll need to deploy your backend API separately
    }
};

// Initialize TensorFlow.js and YOLO model
let modelLoaded = false;
async function ensureModelLoaded() {
    if (!modelLoaded) {
        const loadingOverlay = document.getElementById('loadingOverlay');
        loadingOverlay.style.display = 'flex';
        modelLoaded = await loadModel();
        loadingOverlay.style.display = 'none';
        if (!modelLoaded) {
            alert('Failed to load AI model. Please refresh the page.');
        }
    }
    return modelLoaded;
}

// Determine if we're running on GitHub Pages
const isProduction = window.location.hostname !== 'localhost';
const API_BASE_URL = isProduction ? API_CONFIG.production.baseUrl : API_CONFIG.local.baseUrl;

document.addEventListener('DOMContentLoaded', function () {
    // DOM Elements
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const openCameraBtn = document.getElementById('openCameraBtn');
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const captureBtn = document.getElementById('captureBtn');
    const retryBtn = document.getElementById('retryBtn');
    const detectionResults = document.getElementById('detectionResults');
    const registrationForm = document.getElementById('registrationForm');
    const cameraModal = new bootstrap.Modal(document.getElementById('cameraModal'));
    const cameraMode = document.getElementById('cameraMode');
    const cameraTitle = document.getElementById('cameraTitle');
    const cameraOverlay = document.getElementById('cameraOverlay');
    const driverPhotoPreview = document.getElementById('driverPhotoPreview');

    let currentMode = 'plate'; // 'plate' or 'driver'
    let plateDetected = false;
    let stream = null;

    // Add loading overlay elements
    const loadingOverlay = document.getElementById('loadingOverlay');
    const tableLoader = document.getElementById('tableLoader');

    // Initialize data table
    loadVehicles();

    // Event Listeners
    searchButton.addEventListener('click', () => {
        loadVehicles(searchInput.value);
    });

    // Debounce function for search
    function debounce(func, wait) {
        let timeout;
        return function (...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    // Update search input event listener with debounce
    searchInput.removeEventListener('keypress', null);
    searchInput.addEventListener('input', debounce((e) => {
        loadVehicles(e.target.value);
    }, 300));

    openCameraBtn.addEventListener('click', initializeCamera);
    captureBtn.addEventListener('click', function () {
        if (currentMode === 'plate') {
            capturePlate();
        } else {
            captureDriverPhoto();
        }
    });
    retryBtn.addEventListener('click', function () {
        setPlateMode();
        retryBtn.style.display = 'none';
    });
    registrationForm.addEventListener('submit', handleRegistration);

    // Functions
    function loadVehicles(search = '') {
        tableLoader.style.display = 'block';

        fetch(`${API_BASE_URL}/api/vehicles?search=${encodeURIComponent(search)}`)
            .then(response => response.json())
            .then(vehicles => {
                const tableBody = document.getElementById('vehiclesTableBody');
                tableBody.innerHTML = '';

                vehicles.forEach(vehicle => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${vehicle.plate_number}</td>
                        <td>
                            <div class="d-flex align-items-center">
                                <img src="${vehicle.driver_photo_path}" alt="Driver photo" class="rounded-circle me-2" style="width: 50px; height: 50px; object-fit: cover;">
                                ${vehicle.driver_name}
                            </div>
                        </td>
                        <td>${vehicle.car_color}</td>
                        <td>${vehicle.car_type}</td>
                        <td>${vehicle.registration_date}</td>
                        <td class="qr-code-cell">
                            <img src="${vehicle.qr_code_path}" alt="QR Code" onclick="window.open(this.src)">
                        </td>
                    `;
                    tableBody.appendChild(row);
                });
            })
            .catch(error => console.error('Error loading vehicles:', error))
            .finally(() => {
                tableLoader.style.display = 'none';
            });
    }

    async function initializeCamera() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
            cameraModal.show();
            setPlateMode();
        } catch (err) {
            console.error('Error accessing camera:', err);
            alert('Could not access the camera. Please make sure you have granted camera permissions.');
        }
    }

    function setPlateMode() {
        currentMode = 'plate';
        cameraMode.textContent = 'Plate Detection Mode';
        cameraTitle.textContent = 'Vehicle Scanner';
        captureBtn.textContent = 'Capture Plate';
        retryBtn.style.display = 'none';
        detectionResults.style.display = 'none';
        plateDetected = false;
    }

    function setDriverMode() {
        currentMode = 'driver';
        cameraMode.textContent = 'Driver Photo Mode';
        cameraTitle.textContent = 'Driver Photo Capture';
        captureBtn.textContent = 'Capture Photo';
    }

    async function capturePlate() {
        if (!await ensureModelLoaded()) return;
        
        const context = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        cameraOverlay.style.display = 'flex';
        captureBtn.disabled = true;

        try {
            const results = await detectLicensePlate(canvas);
            
            if (!results || results.length === 0) {
                throw new Error('No license plate detected. Please ensure the plate is clearly visible and try again.');
            }

            // Get the highest confidence detection
            const bestResult = results.reduce((prev, current) => 
                (current.confidence > prev.confidence) ? current : prev
            );

            // Extract the license plate region and show results
            document.getElementById('detectedInfo').innerHTML = `
                <div class="alert alert-info">
                    <strong>Detection Details:</strong><br>
                    License Plate Detection Confidence: ${(bestResult.confidence * 100).toFixed(1)}%
                </div>
            `;
            
            detectionResults.style.display = 'block';
            plateDetected = true;
            retryBtn.style.display = 'inline-block';
            setDriverMode();

            // Here you would typically make an API call to perform OCR on the extracted plate region
            // For now, we'll let the user manually enter the plate number
            document.getElementById('plateNumber').focus();
        } catch (error) {
            console.error('Error detecting plate:', error);
            const errorMessage = error.message || 'An unexpected error occurred. Please try again.';
            alert(errorMessage);
            retryBtn.style.display = 'inline-block';
        } finally {
            cameraOverlay.style.display = 'none';
            captureBtn.disabled = false;
        }
    }

    function captureDriverPhoto() {
        const context = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Convert canvas to data URL and display preview
        const dataURL = canvas.toDataURL('image/jpeg');
        driverPhotoPreview.src = dataURL;
        driverPhotoPreview.style.display = 'block';
        document.getElementById('driverPhotoData').value = dataURL;
    }

    // Update handleRegistration function
    function handleRegistration(e) {
        e.preventDefault();
        if (!plateDetected) {
            alert('Please detect a license plate first');
            return;
        }

        const formData = new FormData();
        formData.append('plate_number', document.getElementById('plateNumber').value);
        formData.append('driver_name', document.getElementById('driverName').value);
        formData.append('car_color', document.getElementById('carColor').value);
        formData.append('car_type', document.getElementById('carType').value);

        // Convert data URL to blob
        const driverPhotoData = document.getElementById('driverPhotoData').value;
        if (driverPhotoData) {
            const binary = atob(driverPhotoData.split(',')[1]);
            const array = new Uint8Array(binary.length);
            for (let i = 0; i < binary.length; i++) {
                array[i] = binary.charCodeAt(i);
            }
            const blob = new Blob([array], { type: 'image/jpeg' });
            formData.append('driver_photo', blob, 'driver_photo.jpg');
        }

        loadingOverlay.style.display = 'flex';

        fetch(`${API_BASE_URL}/api/register_vehicle`, {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    // Reset form
                    document.getElementById('plateNumber').value = '';
                    document.getElementById('driverName').value = '';
                    document.getElementById('carColor').value = '';
                    document.getElementById('carType').value = '';
                    document.getElementById('driverPhotoData').value = '';
                    driverPhotoPreview.style.display = 'none';
                    detectionResults.style.display = 'none';
                    document.getElementById('detectedInfo').innerHTML = '';

                    alert('Vehicle registered successfully!');
                    cameraModal.hide();
                    loadVehicles();
                    stopCamera();
                }
            })
            .catch(error => {
                console.error('Error registering vehicle:', error);
                alert('Error registering vehicle. Please try again.');
            })
            .finally(() => {
                loadingOverlay.style.display = 'none';
            });
    }

    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            video.srcObject = null;
        }
        setPlateMode();
    }

    // Clean up when modal is closed
    document.getElementById('cameraModal').addEventListener('hidden.bs.modal', stopCamera);
});
