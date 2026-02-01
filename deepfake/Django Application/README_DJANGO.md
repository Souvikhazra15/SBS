# Deepfake Detection Django Web Application

> A Django-based web application for real-time deepfake detection with ResNext CNN and LSTM neural networks.

## 📋 Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Using the Web Interface](#using-the-web-interface)
- [API Endpoints](#api-endpoints)
- [Database](#database)
- [Static Files & Media](#static-files--media)
- [Docker Deployment](#docker-deployment)
- [Troubleshooting](#troubleshooting)
- [Performance Tips](#performance-tips)

---

## 🎯 Overview

This is the main Django web application for the deepfake detection system. It provides:

- **Web Interface**: User-friendly UI for uploading and analyzing videos
- **Real-time Processing**: Instant deepfake detection results
- **Multiple Models**: Choose between 3 trained models (84%, 87%, 97% accuracy)
- **Frame Selection**: Flexible frame count selection (10, 20, or 100 frames)
- **GPU Acceleration**: Full CUDA support for fast inference
- **Face Detection**: Visual feedback with face-api.js integration
- **Responsive Design**: Bootstrap-based mobile-friendly interface

---

## 📁 Project Structure

```
Django Application/
├── ml_app/                          # Main Django app
│   ├── migrations/                  # Database migrations
│   ├── templates/
│   │   ├── 404.html                # Error page
│   │   ├── about.html              # About page
│   │   ├── cuda_full.html          # CUDA configuration page
│   │   ├── index.html              # Home page
│   │   └── predict.html            # Prediction/upload page
│   ├── __init__.py
│   ├── admin.py                    # Django admin configuration
│   ├── apps.py                     # App configuration
│   ├── forms.py                    # Django forms (file uploads, inputs)
│   ├── models.py                   # Database models
│   ├── tests.py                    # Unit tests
│   ├── urls.py                     # URL routing
│   ├── views.py                    # View logic & ML inference
│   └── __pycache__/
│
├── project_settings/                # Django configuration
│   ├── __init__.py
│   ├── asgi.py                     # ASGI config (async)
│   ├── settings.py                 # Main Django settings
│   ├── urls.py                     # Main URL router
│   ├── wsgi.py                     # WSGI config (production)
│   └── __pycache__/
│
├── static/                          # Static files (CSS, JS, images)
│   ├── bootstrap/
│   │   └── bootstrap.min.css       # Bootstrap framework
│   ├── css/
│   │   ├── jquery-ui.css
│   │   └── styles.css              # Custom styling
│   ├── images/                     # Images for UI
│   ├── js/
│   │   ├── face-api.js             # Face detection (uncompressed)
│   │   ├── face-api.min.js         # Face detection (minified)
│   │   ├── jquery-3.4.1.min.js     # jQuery library
│   │   ├── jquery-3.5.0.min.js
│   │   ├── jquery-ui.min.js        # jQuery UI
│   │   ├── popper.min.js           # Popper.js
│   │   └── script.js               # Custom JavaScript
│   └── json/                       # Face-API model files
│       ├── age_gender_model-*
│       ├── face_expression_model-*
│       ├── face_landmark_68_model-*
│       ├── face_landmark_68_tiny_model-*
│       ├── face_recognition_model-*
│       ├── mtcnn_model-*
│       ├── ssd_mobilenetv1_model-*
│       └── tiny_face_detector_model-*
│
├── templates/                       # Base templates (shared)
│   ├── base.html                   # Base template
│   ├── cuda_full.html
│   ├── footer.html                 # Footer component
│   └── nav-bar.html                # Navigation component
│
├── media/                           # User uploads
│   ├── images/                     # Uploaded images
│   └── videos/                     # Uploaded videos
│
├── models/                          # Trained PyTorch models
│   ├── model_84_acc_10_frames_final_data.pt
│   ├── model_87_acc_20_frames_final_data.pt
│   ├── model_97_acc_100_frames_FF_data.pt
│   └── placeholder_model.txt
│
├── uploaded_images/                 # Alternative image upload location
│   └── Readme.txt
│
├── uploaded_videos/                 # Alternative video upload location
│   └── Readme.txt
│
├── db.sqlite3                       # SQLite database
├── manage.py                        # Django management script
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

---

## 📋 Requirements

### System Requirements

```
OS: Windows, macOS, or Linux
GPU: NVIDIA GPU with Compute Capability > 3.0 (HIGHLY RECOMMENDED)
CUDA: Version >= 10.0 (for GPU acceleration)
RAM: Minimum 8GB (16GB+ recommended)
Disk Space: ~5GB (for models and dependencies)
```

### Python & Software

```
Python: 3.6 or higher
pip: Latest version
virtualenv: For environment isolation
```

### Python Packages

```
Django >= 5.0
PyTorch >= 1.9
OpenCV (cv2)
NumPy
Pandas
torch-hub
torchvision
torchaudio
face-recognition
matplotlib
Pillow
scikit-learn
```

See [requirements.txt](requirements.txt) for complete list.

---

## 🔧 Installation

### Step 1: Navigate to Django Application Directory

```bash
cd "Django Application"
```

### Step 2: Create Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Upgrade pip

```bash
pip install --upgrade pip
```

### Step 4: Install Requirements

```bash
pip install -r requirements.txt
```

**If you encounter issues:**

- **Windows Build Tools Issue**: 
  - Download [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
  - Install Visual Studio Build Tools

- **Face Recognition/dlib Issue**:
  - Windows: Use precompiled wheels
  - macOS: `brew install cmake` then `pip install dlib`
  - Linux: `apt-get install cmake libboost-all-dev` then `pip install dlib`

### Step 5: Download Trained Models

1. Download models from [Google Drive](https://drive.google.com/drive/folders/1UX8jXUXyEjhLLZ38tcgOwGsZ6XFSLDJ-?usp=sharing)
2. Extract to `models/` folder
3. Verify these files exist:
   - `model_84_acc_10_frames_final_data.pt` (64 MB)
   - `model_87_acc_20_frames_final_data.pt` (64 MB)
   - `model_97_acc_100_frames_FF_data.pt` (64 MB)

### Step 6: Create Required Directories

**Windows:**
```bash
mkdir media\videos
mkdir media\images
mkdir uploaded_videos
mkdir uploaded_images
```

**macOS/Linux:**
```bash
mkdir -p media/videos media/images uploaded_videos uploaded_images
```

### Step 7: Database Setup

```bash
# Create database tables
python manage.py migrate

# (Optional) Create superuser for admin panel
python manage.py createsuperuser
```

### Step 8: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

---

## ⚙️ Configuration

### Django Settings

Edit `project_settings/settings.py` to configure:

```python
# Database (default: SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Allowed hosts
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Media files location
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Static files location
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

### Model Selection

In `ml_app/views.py`, the application automatically selects models:

```python
# Model mapping by frame count
MODEL_MAPPING = {
    10: 'models/model_84_acc_10_frames_final_data.pt',
    20: 'models/model_87_acc_20_frames_final_data.pt',
    100: 'models/model_97_acc_100_frames_FF_data.pt',
}
```

### GPU Configuration

To enable CUDA/GPU:

```python
# In views.py
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")
```

---

## 🚀 Running the Application

### Development Server

```bash
python manage.py runserver
```

**Expected Output:**
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### Access the Application

Open browser → **http://localhost:8000/**

### With Custom Port

```bash
python manage.py runserver 8001
```

### With Custom IP

```bash
python manage.py runserver 0.0.0.0:8000
```

### Production Server (Gunicorn)

```bash
pip install gunicorn
gunicorn project_settings.wsgi --bind 0.0.0.0:8000 --workers 4
```

---

## 💻 Using the Web Interface

### Home Page
- **URL**: `http://localhost:8000/`
- **Description**: Welcome page with navigation
- **Features**: About section, CUDA status check

### Prediction Page
- **URL**: `http://localhost:8000/predict/`
- **Functions**:
  1. Upload video file
  2. Select frame count (10, 20, or 100)
  3. Choose model (auto-selected based on frames)
  4. Submit for analysis

### Upload Process

**Step 1: Select Video**
- Click "Choose File" or drag-and-drop
- Supported formats: MP4, AVI, MOV, MKV, etc.
- Max recommended size: 100MB

**Step 2: Select Frame Count**
```
10 frames  → 84% accuracy  (~5-10 sec)
20 frames  → 87% accuracy  (~10-15 sec)  [Default]
100 frames → 97% accuracy  (~30-60 sec)  [Recommended]
```

**Step 3: Click "Predict"**
- Video processing starts
- Frames are extracted
- Features are computed
- Model inference runs
- Results are displayed

### Results Display

**Prediction Result:**
- **Real** - Video appears to be authentic
- **Fake** - Video appears to be a deepfake

**Confidence Score:**
- 0-50%: Low confidence
- 50-75%: Medium confidence
- 75-95%: High confidence
- 95-100%: Very high confidence

**Visualization:**
- Face detection overlay (if available)
- Frame-by-frame confidence scores
- Processing statistics

---

## 🔌 API Endpoints

### Main Routes

| URL | View | Method | Description |
|-----|------|--------|-------------|
| `/` | home | GET | Home page |
| `/predict/` | predict | GET, POST | Upload and predict |
| `/about/` | about | GET | About page |
| `/cuda/` | cuda_full | GET | CUDA info |
| `/admin/` | Django admin | GET | Admin panel |

### Prediction Endpoint

**POST** `/predict/`

```json
{
  "video_file": "<uploaded file>",
  "sequence_length": 100
}
```

**Response:**
```json
{
  "prediction": "Real/Fake",
  "confidence": 0.97,
  "processing_time": 45.2,
  "frames_processed": 100
}
```

---

## 💾 Database

### Models

The application uses Django ORM with the following models (defined in `ml_app/models.py`):

- **PredictionHistory** - Stores prediction records
- **UploadedVideo** - Tracks uploaded videos
- **ModelInfo** - Model metadata and statistics

### Database Operations

```bash
# View database shell
python manage.py shell

# Backup database
sqlite3 db.sqlite3 .dump > backup.sql

# Reset database
python manage.py flush
```

---

## 📁 Static Files & Media

### Static Files Location
```
static/
├── css/          # Stylesheets
├── js/           # JavaScript files
├── json/         # Face-API models
├── images/       # UI images
└── bootstrap/    # Bootstrap framework
```

### Media Uploads Location
```
media/
├── videos/       # Uploaded video files
└── images/       # Frame extractions & screenshots
```

### Collect Static Files (for production)

```bash
python manage.py collectstatic --noinput
```

---

## 🐳 Docker Deployment

### Build Docker Image

Create a `Dockerfile` in the Django Application directory:

```dockerfile
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y python3-pip
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### Build & Run

```bash
# Build image
docker build -t deepfake-django:latest .

# Run container
docker run --rm --gpus all -p 8000:8000 \
  -v $(pwd)/media:/app/media \
  -v $(pwd)/models:/app/models \
  deepfake-django:latest
```

### Docker Compose

```yaml
version: '3.8'

services:
  deepfake-app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./media:/app/media
      - ./models:/app/models
    environment:
      - CUDA_VISIBLE_DEVICES=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

Run with:
```bash
docker-compose up
```

---

## 🐛 Troubleshooting

### Issue 1: ModuleNotFoundError

**Error**: `ModuleNotFoundError: No module named 'torch'`

**Solution**:
```bash
pip install -r requirements.txt
# or
pip install torch torchvision torchaudio
```

### Issue 2: Model Not Found

**Error**: `FileNotFoundError: models/model_97_acc_100_frames_FF_data.pt`

**Solution**:
1. Download models from Google Drive
2. Place in `models/` folder
3. Verify file names match exactly

### Issue 3: CUDA Not Available

**Error**: `torch.cuda.is_available()` returns `False`

**Check & Fix**:
```bash
# Check CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Reinstall PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Issue 4: Out of Memory (OOM)

**Error**: `RuntimeError: CUDA out of memory`

**Solutions**:
- Use fewer frames (10 or 20 instead of 100)
- Close other GPU applications
- Reduce batch size in inference
- Upgrade GPU memory or use CPU mode

### Issue 5: Permission Denied

**Error**: `PermissionError: Permission denied`

**Solution**:
```bash
# Windows
icacls "Django Application" /grant %username%:F /T

# Linux/Mac
chmod -R u+w .
```

### Issue 6: Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Use different port
python manage.py runserver 8001

# Or kill process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -i :8000
kill -9 <PID>
```

### Issue 7: Slow Processing

**Cause**: GPU not being used (CPU mode)

**Check & Fix**:
```python
import torch
print(f"GPU Available: {torch.cuda.is_available()}")
print(f"GPU Name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'}")
```

### Issue 8: Migrations Failed

**Error**: `django.db.utils.OperationalError`

**Solution**:
```bash
python manage.py migrate --run-syncdb
python manage.py migrate ml_app
```

---

## ⚡ Performance Tips

### For Faster Processing

1. **Use Fewer Frames**
   - 10 frames: ~5-10 seconds (84% accuracy)
   - Better for real-time applications

2. **Enable GPU**
   - Verify CUDA is available
   - Use RTX series GPUs for best performance
   - A100 or RTX 4090 optimal

3. **Optimize Video**
   - Lower resolution videos process faster
   - Shorter videos obviously faster
   - Pre-compress videos to H.264

4. **Use Process Pooling**
   ```python
   from multiprocessing import Pool
   # Process multiple videos in parallel
   ```

### For Better Accuracy

1. **Use 100-Frame Model**
   - 97% accuracy
   - Takes ~30-60 seconds per video

2. **High-Quality Videos**
   - 1080p or higher recommended
   - Good lighting improves accuracy
   - Clear face visibility essential

3. **Ensemble Predictions**
   - Run all three models
   - Average predictions for robustness

### System Optimization

```python
# In views.py - Reduce memory usage
import torch
torch.cuda.empty_cache()  # Clear GPU cache
torch.set_num_threads(4)   # Limit CPU threads
```

---

## 📞 Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review parent project [README.md](../README.md)
3. Check [MODEL_GUIDE.md](../MODEL_GUIDE.md)
4. Create issue on [GitHub](https://github.com/Zala0007/deepfake/issues)

---

**Last Updated**: January 2026  
**Django Version**: 5.0+  
**Python Version**: 3.6+

Made with ❤️ for deepfake detection
