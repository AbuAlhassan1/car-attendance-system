# Car Park Attendance System

A modern web-based car park attendance system with automatic license plate recognition and driver management.

## Features

- Automatic license plate detection using YOLOv8
- Real-time camera integration
- Driver photo capture
- QR code generation for each vehicle
- Search functionality
- Responsive design

## Tech Stack

- Backend: Flask (Python)
- Frontend: HTML5, CSS3, JavaScript
- Database: SQLite
- Computer Vision: YOLOv8, EasyOCR
- UI Framework: Bootstrap 5

## Local Development

1. Clone the repository:
```bash
git clone <your-repo-url>
cd car-attendance-system
```

2. Install dependencies:
```bash
pip3 install flask flask-sqlalchemy opencv-python-headless easyocr torch torchvision qrcode pillow scikit-learn
```

3. Run the application:
```bash
python3 app.py
```

4. Visit http://localhost:5001 in your web browser

## Deployment

The application is split into two parts:

1. Frontend (GitHub Pages)
   - Handles UI and client-side processing
   - Uses TensorFlow.js for license plate detection
   - Deployed automatically via GitHub Actions
   - Available at: https://your-username.github.io/car-attendance-system

2. Backend API (Separate Repository)
   - Handles database operations
   - Stores driver photos and QR codes
   - Provides REST API endpoints
   - Repository: https://github.com/your-username/car-attendance-api

### Setting up GitHub Pages

1. Go to your repository settings
2. Navigate to "Pages"
3. Select "Source" as "GitHub Actions"

The GitHub Actions workflow will:
- Convert the YOLOv8 model to TensorFlow.js format
- Build and deploy the static assets
- Update the live site automatically on each push to main

## Project Structure

```
car-attendance-system/
├── app.py                # Main Flask application
├── models.py            # Database models
├── main.py             # Core detection functions
├── static/             # Static assets (CSS, JS, images)
├── templates/          # HTML templates
└── database/          # SQLite database
```

## License

MIT License - see LICENSE file for details
