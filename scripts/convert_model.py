import tensorflowjs as tfjs
from ultralytics import YOLO

def convert_yolo_to_tfjs():
    # Load YOLOv8 model
    model = YOLO('yolov8n.pt')
    
    # Export to ONNX format first
    model.export(format='onnx', dynamic=True)
    
    # Convert ONNX to TensorFlow.js format
    tfjs.converters.convert_tf_saved_model(
        'yolov8n_saved_model',
        'static/model'
    )

if __name__ == '__main__':
    convert_yolo_to_tfjs()
