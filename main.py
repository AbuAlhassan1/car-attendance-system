import cv2
import easyocr
import qrcode
import numpy as np
from sklearn.cluster import KMeans
from ultralytics import YOLO
from PIL import Image


def generate_qr_code(text):
    qr = qrcode.make(text)
    qr.save("plate_qr.png")
    qr.show()


def get_dominant_color(image, k=3):
    # Resize to speed up processing
    img = cv2.resize(image, (50, 50))
    img = img.reshape((img.shape[0] * img.shape[1], 3))

    # Use KMeans to find dominant color
    kmeans = KMeans(n_clusters=k, n_init=10)
    kmeans.fit(img)
    dominant = kmeans.cluster_centers_[0].astype(int)
    return tuple(dominant)


def closest_color(rgb_color):
    # Basic named color set
    colors = {
        "black": (0, 0, 0),
        "gray": (128, 128, 128),
        "white": (255, 255, 255),
        "red": (255, 0, 0),
        "green": (0, 128, 0),
        "blue": (0, 0, 255),
        "yellow": (255, 255, 0),
        "cyan": (0, 255, 255),
        "magenta": (255, 0, 255),
        "orange": (255, 165, 0),
        "purple": (128, 0, 128),
        "brown": (165, 42, 42)
    }

    min_dist = float('inf')
    closest = None
    for name, value in colors.items():
        dist = np.linalg.norm(np.array(value) - np.array(rgb_color))
        if dist < min_dist:
            min_dist = dist
            closest = name
    return closest


def detect_and_read_plate_with_yolo(image_path):
    model = YOLO('yolov8n.pt')
    reader = easyocr.Reader(['en'])

    frame = cv2.imread(image_path)
    if frame is None:
        print("Error: Could not read image.")
        return

    results = model(frame)

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]

            if label in ['car', 'truck', 'bus', 'motorbike']:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cropped = frame[y1:y2, x1:x2]

                # Detect dominant color
                color_rgb = get_dominant_color(cropped)
                color_name = closest_color(color_rgb)

                # OCR
                ocr_result = reader.readtext(cropped)
                plate_text = None
                if ocr_result:
                    plate_text = max(ocr_result, key=lambda r: r[2])[1]

                # Annotate frame
                label_text = f"{label} | Color: {color_name}"
                if plate_text:
                    label_text += f" | Plate: {plate_text}"
                    generate_qr_code(plate_text)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # Show image
    cv2.imshow("YOLO + OCR + Color", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    image_path = "car.jpg"  # Replace with your image
    detect_and_read_plate_with_yolo(image_path)
