// Onion Lens - Camera & Video Capture Handler
const CameraModule = {
    stream: null,
    facingMode: 'environment', // 'environment' (rear) or 'user' (front)
    flashOn: false,
    currentImageSource: null,
    sampleType: 'grade-a',

    initCamera: async function(videoElement, fallbackElement) {
        CameraModule.stopCamera();
        
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            console.warn('getUserMedia not supported in this browser environment.');
            CameraModule.showFallback(videoElement, fallbackElement);
            return false;
        }

        // Multi-tier constraint fallback: ideal resolution -> facing mode -> any video
        const constraintTiers = [
            { video: { facingMode: { ideal: CameraModule.facingMode }, width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false },
            { video: { facingMode: { ideal: CameraModule.facingMode } }, audio: false },
            { video: true, audio: false }
        ];

        let stream = null;
        for (const constraints of constraintTiers) {
            try {
                stream = await navigator.mediaDevices.getUserMedia(constraints);
                if (stream) break;
            } catch (err) {
                console.warn('Camera constraint tier attempt failed:', err);
            }
        }

        if (stream && videoElement) {
            CameraModule.stream = stream;
            videoElement.muted = true;
            videoElement.playsInline = true;
            videoElement.setAttribute('playsinline', 'true');
            videoElement.setAttribute('autoplay', 'true');
            videoElement.setAttribute('muted', 'true');
            videoElement.srcObject = stream;
            videoElement.style.display = 'block';
            if (fallbackElement) fallbackElement.style.display = 'none';
            try {
                await videoElement.play();
            } catch (playErr) {
                console.warn('Error calling videoElement.play():', playErr);
            }
            return true;
        } else {
            CameraModule.showFallback(videoElement, fallbackElement);
            return false;
        }
    },


    showFallback: function(videoElement, fallbackElement) {
        if (videoElement) videoElement.style.display = 'none';
        if (fallbackElement) fallbackElement.style.display = 'flex';
    },

    stopCamera: function() {
        if (CameraModule.stream) {
            CameraModule.stream.getTracks().forEach(track => track.stop());
            CameraModule.stream = null;
        }
    },

    toggleFlash: function(overlayElement) {
        CameraModule.flashOn = !CameraModule.flashOn;
        // Check if torch track is available on active camera
        if (CameraModule.stream) {
            const track = CameraModule.stream.getVideoTracks()[0];
            if (track && track.applyConstraints) {
                track.applyConstraints({
                    advanced: [{ torch: CameraModule.flashOn }]
                }).catch(() => {/* Torch not supported on hardware */});
            }
        }
        // UI Visual flash indication
        if (overlayElement) {
            overlayElement.classList.toggle('flash-active', CameraModule.flashOn);
        }
        return CameraModule.flashOn;
    },

    flipCamera: async function(videoElement, fallbackElement) {
        CameraModule.facingMode = (CameraModule.facingMode === 'environment') ? 'user' : 'environment';
        return await CameraModule.initCamera(videoElement, fallbackElement);
    },

    captureFrame: function(videoElement, fallbackImgElement) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        // Flash screen trigger effect
        const flashScreen = document.getElementById('camera-flash-fx');
        if (flashScreen) {
            flashScreen.classList.add('trigger-flash');
            setTimeout(() => flashScreen.classList.remove('trigger-flash'), 250);
        }

        // If live camera is streaming
        if (CameraModule.stream && videoElement && videoElement.videoWidth > 0) {
            canvas.width = videoElement.videoWidth;
            canvas.height = videoElement.videoHeight;
            ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
            const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
            CameraModule.currentImageSource = {
                dataUrl: dataUrl,
                type: 'live'
            };
            return CameraModule.currentImageSource;
        }

        // If an image was selected via gallery upload
        if (fallbackImgElement && fallbackImgElement.src && !fallbackImgElement.src.endsWith('#')) {
            canvas.width = fallbackImgElement.naturalWidth || 600;
            canvas.height = fallbackImgElement.naturalHeight || 750;
            ctx.drawImage(fallbackImgElement, 0, 0, canvas.width, canvas.height);
            const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
            CameraModule.currentImageSource = {
                dataUrl: dataUrl,
                type: 'upload'
            };
            return CameraModule.currentImageSource;
        }

        // Neither camera nor image available: trigger gallery picker
        const galleryInput = document.getElementById('gallery-file-input');
        if (galleryInput) galleryInput.click();
        return null;
    }
};
