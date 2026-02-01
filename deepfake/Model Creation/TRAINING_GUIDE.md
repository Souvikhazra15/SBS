# Complete Guide to Train Deepfake Detection Model with New Data

> Step-by-step instructions to retrain the deepfake detection model using your own dataset.

## 📋 Table of Contents

- [Overview](#overview)
- [Before You Start](#before-you-start)
- [Step 1: Prepare Your Dataset](#step-1-prepare-your-dataset)
- [Step 2: Preprocess Videos](#step-2-preprocess-videos)
- [Step 3: Create CSV Labels](#step-3-create-csv-labels)
- [Step 4: Train the Model](#step-4-train-the-model)
- [Step 5: Evaluate the Model](#step-5-evaluate-the-model)
- [Step 6: Use Your Trained Model](#step-6-use-your-trained-model)
- [Troubleshooting](#troubleshooting)
- [Performance Tips](#performance-tips)

---

## 🎯 Overview

The training process involves 4 main stages:

```
Raw Videos
    ↓
[preprocessing.ipynb] → Extract frames & crop faces
    ↓
Preprocessed Face Frames
    ↓
[Create CSV Labels] → Define which videos are real/fake
    ↓
CSV Labels File
    ↓
[Model_and_train_csv.ipynb] → Train ResNext + LSTM model
    ↓
Trained Model (.pt file)
    ↓
[Predict.ipynb] → Test on new videos
    ↓
Predictions (Real/Fake)
```

---

## ⚠️ Before You Start

### System Requirements

```
GPU: NVIDIA GPU with 6GB+ VRAM (12GB+ recommended)
RAM: 16GB minimum (32GB recommended)
Disk Space: 100GB+ (for dataset, preprocessing, and models)
Python: 3.6+
```

### Check Your Setup

```bash
# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"

# Check GPU memory
python -c "import torch; print(torch.cuda.get_device_properties(0).total_memory / 1e9, 'GB')"
```

### Using Google Colab (Recommended)

The original project recommends **Google Colab** with GPU:

**Advantages:**
- ✅ Free GPU (Tesla T4)
- ✅ 12GB GPU VRAM
- ✅ Pre-installed dependencies
- ✅ Easy file management with Google Drive

**Steps:**
1. Upload `preprocessing.ipynb` to Google Colab
2. Upload your dataset to Google Drive
3. Mount Google Drive in Colab
4. Run cells sequentially

---

## 📊 Step 1: Prepare Your Dataset

### Dataset Structure

Organize your videos in this folder structure:

```
your_dataset/
├── real/
│   ├── video1.mp4
│   ├── video2.mp4
│   ├── video3.avi
│   └── ...
└── fake/
    ├── deepfake1.mp4
    ├── deepfake2.mp4
    ├── deepfake3.avi
    └── ...
```

### Create These Folders

```bash
# Windows
mkdir your_dataset\real
mkdir your_dataset\fake

# macOS/Linux
mkdir -p your_dataset/real
mkdir -p your_dataset/fake
```

### Video Requirements

- **Format**: MP4, AVI, MOV, MKV
- **Resolution**: 480p or higher (1080p recommended)
- **Duration**: 2-10 seconds per video
- **Codec**: H.264 or similar
- **Frame Rate**: 24-30 FPS

### Dataset Size Recommendations

| Model Accuracy | Minimum Videos | Recommended |
|---|---|---|
| 80%+ | 200 | 500+ |
| 85%+ | 500 | 1000+ |
| 90%+ | 1000 | 2000+ |
| 95%+ | 2000 | 5000+ |

**For best results: 1000+ total videos (500 real + 500 fake)**

### Example: Download Public Datasets

**Option 1: Use Pre-processed Data** (Fastest)

Download already-preprocessed datasets:
- [Celeb-DF Fake](https://drive.google.com/drive/folders/1SxCb_Wr7N4Wsc-uvjUl0i-6PpwYmwN65?usp=sharing)
- [Celeb-DF Real](https://drive.google.com/drive/folders/1g97v9JoD3pCKA2TxHe8ZLRe4buX2siCQ?usp=sharing)
- [FaceForensics++](https://drive.google.com/drive/folders/1VIIWRLs6VBXRYKODgeOU7i6votLPPxT0?usp=sharing)
- [DFDC Fake](https://drive.google.com/drive/folders/1yz3DBeFJvZ_QzWsyY7EwBNm7fx4MiOfF?usp=sharing)
- [DFDC Real](https://drive.google.com/drive/folders/1wN3ZOd0WihthEeH__Lmj_ENhoXJN6U11?usp=sharing)

**Option 2: Create Your Own** (Custom but time-consuming)

1. Record videos of real people
2. Create deepfakes using tools like:
   - FaceSwap
   - DeepFaceLab
   - First Order Motion Model
3. Place in `real/` and `fake/` folders

---

## 🔄 Step 2: Preprocess Videos

This step extracts frames from videos and crops faces.

### Open preprocessing.ipynb

1. Open the file: `Model Creation/preprocessing.ipynb`
2. Use Google Colab or Jupyter Notebook

### Key Steps in the Notebook

**Cell 1: Install Dependencies**
```python
!pip install opencv-python torch torchvision
!pip install mtcnn
!pip install face-recognition
```

**Cell 2: Import Libraries**
```python
import cv2
import os
import numpy as np
from mtcnn import MTCNN
```

**Cell 3: Set Dataset Path**
```python
# Update these paths
dataset_path = 'your_dataset/'  # Your raw videos
output_path = 'your_dataset_processed/'  # Where to save

real_videos = os.path.join(dataset_path, 'real')
fake_videos = os.path.join(dataset_path, 'fake')
```

**Cell 4: Create Output Directories**
```python
os.makedirs(os.path.join(output_path, 'real'), exist_ok=True)
os.makedirs(os.path.join(output_path, 'fake'), exist_ok=True)
```

**Cell 5: Run Face Extraction**
```python
# Extract and crop faces from each frame
# This takes time! (Hours for large datasets)
# For each video:
#   - Extract 10-100 frames
#   - Detect faces using MTCNN
#   - Crop face region
#   - Save cropped frames
```

### Preprocessing Output

```
your_dataset_processed/
├── real/
│   ├── video1/
│   │   ├── frame_0.jpg
│   │   ├── frame_1.jpg
│   │   ├── frame_2.jpg
│   │   └── ...
│   ├── video2/
│   └── ...
└── fake/
    ├── deepfake1/
    │   ├── frame_0.jpg
    │   └── ...
    └── ...
```

### Processing Time Estimates

| Dataset Size | GPU (RTX 3060) | GPU (A100) | CPU |
|---|---|---|---|
| 100 videos | ~2 hours | ~30 min | 8+ hours |
| 500 videos | ~10 hours | 2.5 hours | 40+ hours |
| 1000 videos | ~20 hours | 5 hours | 80+ hours |

**Recommendation**: Use GPU or Google Colab!

---

## 📝 Step 3: Create CSV Labels

Create a CSV file with labels for your dataset.

### CSV Format

Your CSV should have this format:

```csv
filename,label
real/video1,0
real/video2,0
real/video3,0
fake/deepfake1,1
fake/deepfake2,1
fake/deepfake3,1
```

**Where:**
- `filename`: Path to video folder (relative to dataset)
- `label`: 0 = Real, 1 = Fake

### Create CSV Manually (Small Dataset)

**Using Python:**
```python
import os
import csv

dataset_path = 'your_dataset_processed/'

with open('labels.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['filename', 'label'])
    
    # Real videos
    for video in os.listdir(os.path.join(dataset_path, 'real')):
        writer.writerow([f'real/{video}', 0])
    
    # Fake videos
    for video in os.listdir(os.path.join(dataset_path, 'fake')):
        writer.writerow([f'fake/{video}', 1])
```

### Auto-Generate CSV (Large Dataset)

Use the helper script: `Helpers/Create_csv_from_glob.ipynb`

1. Open the notebook
2. Update paths
3. Run all cells
4. Output: `labels.csv`

### Example CSV File

```csv
filename,label
real/person1_video1,0
real/person1_video2,0
real/person2_video1,0
real/person2_video2,0
fake/deepfake1,1
fake/deepfake2,1
fake/deepfake3,1
```

---

## 🧠 Step 4: Train the Model

Open and run: `Model_and_train_csv.ipynb`

### Key Configuration Parameters

**In the notebook, you'll configure:**

```python
# Dataset
dataset_path = 'your_dataset_processed/'
csv_file = 'labels.csv'

# Model Parameters
sequence_length = 100  # Frames per video (10, 20, or 100)
batch_size = 4         # Increase if you have GPU memory
learning_rate = 0.001
num_epochs = 50        # Increase for better accuracy

# GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
```

### Training Process

**Stage 1: Load Data**
```python
# Load video frames and labels
# Split into train/val/test: 70/15/15
```

**Stage 2: Build Model**
```python
# ResNext50 (pretrained on ImageNet)
#   ↓
# Feature Extraction
#   ↓
# LSTM Network (sequence analysis)
#   ↓
# Classification (Real vs Fake)
```

**Stage 3: Train Model**
```python
# For each epoch:
#   1. Forward pass through network
#   2. Calculate loss (BCELoss or CrossEntropyLoss)
#   3. Backward pass (compute gradients)
#   4. Update weights
#   5. Validate on validation set
#   6. Save best model
```

**Stage 4: Evaluate**
```python
# Test on unseen test data
# Calculate metrics:
#   - Accuracy
#   - Precision
#   - Recall
#   - F1-Score
#   - ROC-AUC
```

### Expected Output

```
Epoch 1/50
Loss: 0.6234 | Val_Loss: 0.5823 | Accuracy: 65.2%

Epoch 2/50
Loss: 0.4821 | Val_Loss: 0.4156 | Accuracy: 78.5%

...

Epoch 50/50
Loss: 0.1234 | Val_Loss: 0.2156 | Accuracy: 94.3%

Final Test Accuracy: 93.8%
Precision: 0.94 | Recall: 0.93 | F1: 0.935
```

### Training Tips

1. **Monitor Loss**
   - Loss should decrease over epochs
   - If loss increases → learning rate too high
   - If loss stagnates → increase epochs or data

2. **Avoid Overfitting**
   - Use validation set to monitor
   - If val_loss increases while train_loss decreases → overfitting
   - Solution: Add dropout, use regularization, or reduce epochs

3. **Save Best Model**
   ```python
   # The notebook automatically saves the best model
   # Location: model_sequence_FRAMES_final_data.pt
   torch.save(model.state_dict(), 'model_100_acc_my_data.pt')
   ```

### Save Your Trained Model

The model will be saved as:
```
model_<sequence_length>_acc_<accuracy>_final_data.pt
```

Example:
```
model_100_acc_95.8_final_data.pt
```

---

## ✅ Step 5: Evaluate the Model

Open and run: `Predict.ipynb`

### Test on Known Videos

```python
# Load your trained model
model = load_model('model_100_acc_95.8_final_data.pt')

# Test on known videos
test_video = 'path/to/test_video.mp4'
prediction = model.predict(test_video)

# Output:
# Prediction: Real/Fake
# Confidence: 0.95 (95%)
```

### Evaluate on Test Set

```python
# Test on all test videos
test_accuracy = evaluate_model(model, test_dataset)
print(f"Test Accuracy: {test_accuracy:.2%}")

# If accuracy < 85%:
#   - Add more training data
#   - Increase epochs
#   - Tune learning rate
#   - Use different architecture
```

### Metrics to Check

| Metric | Good | Excellent |
|---|---|---|
| Accuracy | 85%+ | 95%+ |
| Precision | 85%+ | 95%+ |
| Recall | 85%+ | 95%+ |
| F1-Score | 0.85+ | 0.95+ |

---

## 🚀 Step 6: Use Your Trained Model

### Option A: Replace Existing Model

1. Copy your trained model to the models folder:
```bash
cp model_100_acc_95.8_final_data.pt "../Django Application/models/"
```

2. The Django app will automatically use it!

### Option B: Specify Model Manually

In `Django Application/ml_app/views.py`:

```python
# Update model mapping
MODEL_MAPPING = {
    10: 'models/model_84_acc_10_frames_final_data.pt',
    20: 'models/model_87_acc_20_frames_final_data.pt',
    100: 'models/model_100_acc_95.8_final_data.pt',  # Your new model!
}
```

### Option C: Use in Custom Code

```python
import torch
from torch import nn

# Load your model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = YourModel().to(device)
model.load_state_dict(torch.load('model_100_acc_95.8_final_data.pt'))
model.eval()

# Predict
with torch.no_grad():
    output = model(input_tensor)
    prediction = torch.sigmoid(output)
    label = "Real" if prediction < 0.5 else "Fake"
```

---

## 🐛 Troubleshooting

### Issue 1: "Out of Memory" Error

**Error**: `RuntimeError: CUDA out of memory`

**Solutions:**
1. Reduce `batch_size` (from 4 to 2)
2. Reduce `sequence_length` (from 100 to 20)
3. Reduce video resolution during preprocessing
4. Use GPU with more memory (A100 vs RTX 3060)
5. Use Google Colab Pro for more GPU memory

### Issue 2: Face Not Detected in Frames

**Error**: `No faces detected in video`

**Solutions:**
1. Ensure videos have clear face visibility
2. Check video quality (1080p+ recommended)
3. Adjust MTCNN confidence threshold in preprocessing
4. Manually crop faces if necessary

### Issue 3: Model Not Converging (Loss Not Decreasing)

**Error**: Loss remains high, accuracy doesn't improve

**Solutions:**
1. **Increase learning rate**: 0.001 → 0.01
2. **Decrease learning rate**: 0.01 → 0.0001
3. **Use more data**: 100 videos → 1000 videos
4. **Use different optimizer**: Adam instead of SGD
5. **Increase epochs**: 50 → 100+

### Issue 4: Poor Accuracy on New Videos

**Error**: Model gives wrong predictions

**Solutions:**
1. **Add similar data**: If your test videos look different, add similar ones to training
2. **Retrain with more epochs**: 50 → 100
3. **Use larger dataset**: More data = better generalization
4. **Use 100-frame model**: More frames = higher accuracy
5. **Ensemble models**: Use multiple models and average predictions

### Issue 5: GPU Not Being Used

**Error**: Training is very slow

**Check & Fix:**
```python
# Check if GPU is available
import torch
print(torch.cuda.is_available())  # Should be True
print(torch.cuda.get_device_name(0))  # Should show GPU name

# If False, reinstall PyTorch:
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Issue 6: CSV File Not Found

**Error**: `FileNotFoundError: labels.csv not found`

**Solution:**
1. Verify CSV file exists in correct location
2. Use absolute path instead of relative:
```python
csv_file = '/absolute/path/to/labels.csv'
```

---

## ⚡ Performance Tips

### To Improve Accuracy

1. **Use More Data**
   - 100 videos: ~80% accuracy
   - 500 videos: ~88% accuracy
   - 1000+ videos: ~95%+ accuracy

2. **Use More Frames**
   - 10 frames: Fast but lower accuracy
   - 100 frames: Slower but highest accuracy

3. **Use Better GPUs**
   - RTX 3060: OK (~4 hrs for 1000 videos)
   - RTX 4090: Good (~1 hr)
   - A100: Excellent (~30 min)

4. **Data Augmentation**
   ```python
   # In preprocessing, add variations:
   - Random flips
   - Random crops
   - Color adjustments
   - Slight rotations
   ```

5. **Ensemble Multiple Models**
   ```python
   # Train 3 models with different seeds
   # Average their predictions for better accuracy
   prediction = (pred1 + pred2 + pred3) / 3
   ```

### To Speed Up Training

1. **Reduce Sequence Length**: 100 → 20 frames
2. **Reduce Dataset**: Use 500 videos instead of 1000
3. **Increase Batch Size**: 4 → 8 (if GPU memory allows)
4. **Use Gradient Accumulation**: Process multiple batches together
5. **Use Mixed Precision**: torch.cuda.amp for faster training

### To Improve Generalization

1. **Use Diverse Dataset**
   - Different ethnicities
   - Different ages
   - Different lighting conditions
   - Different video qualities

2. **Regular Validation**
   - Check validation accuracy every epoch
   - Stop if validation loss increases (early stopping)

3. **Data Augmentation During Training**
   ```python
   # Apply random transformations to training data
   ```

---

## 📚 Quick Reference

### File Locations

```
Model Creation/
├── preprocessing.ipynb           # 1. Run first - preprocess videos
├── Model_and_train_csv.ipynb     # 2. Run second - train model
├── Predict.ipynb                 # 3. Run third - test model
├── Helpers/
│   └── Create_csv_from_glob.ipynb # Auto-create CSV labels
└── labels/
    └── Gobal_metadata.csv         # Reference label file
```

### Commands Quick Guide

```bash
# Check GPU
python -c "import torch; print(torch.cuda.is_available())"

# Check GPU Memory
python -c "import torch; print(torch.cuda.get_device_properties(0).total_memory / 1e9)"

# Save model
torch.save(model.state_dict(), 'my_model.pt')

# Load model
model.load_state_dict(torch.load('my_model.pt'))

# Move to GPU
model.to('cuda')

# Clear GPU cache
torch.cuda.empty_cache()
```

---

## ✅ Training Checklist

- [ ] Dataset organized (real/ and fake/ folders)
- [ ] Videos are 1080p+, 2-10 sec, H.264 codec
- [ ] GPU memory checked (6GB+ available)
- [ ] preprocessing.ipynb completed successfully
- [ ] Face frames extracted and saved
- [ ] CSV labels file created
- [ ] Model_and_train_csv.ipynb configured
- [ ] Model training started
- [ ] Loss decreasing, accuracy improving
- [ ] Model saved to .pt file
- [ ] Test accuracy > 85%
- [ ] Model copied to Django Application/models/
- [ ] Django app restarted
- [ ] Tested with new videos

---

**Last Updated**: January 2026

Made with ❤️ for better deepfake detection
