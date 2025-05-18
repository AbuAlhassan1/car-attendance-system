// YOLO model loading and inference using TensorFlow.js
let model = null;

async function loadModel() {
    try {
        model = await tf.loadGraphModel('model/model.json');
        console.log('YOLOv8 model loaded successfully');
        return true;
    } catch (error) {
        console.error('Error loading model:', error);
        return false;
    }
}

async function preprocessImage(imageData) {
    // Convert to tensor
    const tensor = tf.browser.fromPixels(imageData);

    // Normalize and resize
    const resized = tf.image.resizeBilinear(tensor, [640, 640]);
    const normalized = resized.div(255.0);
    const batched = normalized.expandDims(0);

    tensor.dispose();
    resized.dispose();
    normalized.dispose();

    return batched;
}

async function detectObjects(imageElement) {
    if (!model) {
        console.error('Model not loaded');
        return null;
    }

    const batched = await preprocessImage(imageElement);
    const predictions = await model.predict(batched);
    batched.dispose();

    // Process predictions
    const [boxes, scores, classes] = predictions;
    const validDetections = predictions[3];

    return {
        boxes: boxes.arraySync(),
        scores: scores.arraySync(),
        classes: classes.arraySync(),
        validDetections: validDetections.arraySync()[0]
    };
}

async function detectLicensePlate(image) {
    const predictions = await detectObjects(image);
    if (!predictions) return null;

    // Filter for license plate detections
    const results = [];
    for (let i = 0; i < predictions.validDetections; i++) {
        const score = predictions.scores[0][i];
        const classId = predictions.classes[0][i];
        const bbox = predictions.boxes[0][i];

        if (score > 0.5 && classId === 0) { // Assuming 0 is the class ID for license plates
            results.push({
                confidence: score,
                bbox: bbox
            });
        }
    }

    return results;
}

// Initialize the model when the script loads
loadModel();
