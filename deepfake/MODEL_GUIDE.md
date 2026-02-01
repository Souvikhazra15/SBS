# Deepfake Detection Model Guide

## Available Models

You currently have **3 models** installed:

| Model File | Accuracy | Frames | Speed | Best For |
|------------|----------|--------|-------|----------|
| `model_84_acc_10_frames_final_data.pt` | 84% | 10 | ⚡ Very Fast | Quick testing |
| `model_87_acc_20_frames_final_data.pt` | 87% | 20 | ⚡ Fast | Balanced |
| `model_97_acc_100_frames_FF_data.pt` | **97%** ⭐ | 100 | 🐢 Slower | **Best accuracy** |

## Recommended Settings

### For Best Accuracy (Recommended)
- **Sequence Length**: 100 frames
- **Model**: `model_97_acc_100_frames_FF_data.pt` (97% accuracy)
- **Processing Time**: ~30-60 seconds per video
- **Use Case**: Final production, critical analysis

### For Quick Testing
- **Sequence Length**: 20 frames
- **Model**: `model_87_acc_20_frames_final_data.pt` (87% accuracy)
- **Processing Time**: ~10-15 seconds per video
- **Use Case**: Fast previews, development

## What Changed

✅ **Default setting is now 100 frames** (97% accuracy model)
✅ **Added helpful tip on the upload page**
✅ **App automatically selects the best model for your chosen frame count**

## How It Works

The application automatically selects the best available model based on your sequence length:
- Choose **10 frames** → uses 84% accuracy model
- Choose **20 frames** → uses 87% accuracy model
- Choose **100 frames** → uses **97% accuracy model** ⭐

## Using the Application

1. Go to http://localhost:8000/
2. Upload your video file
3. **Slide the selector to 100** (default, highest accuracy)
4. Click "Upload"
5. Wait for processing (may take 30-60 seconds for 100 frames)
6. View results with 97% accuracy

## Why More Frames = Better Accuracy?

- **More frames** = More data for the LSTM model to analyze
- **Temporal patterns** are more evident over longer sequences
- **Face movements** and artifacts are better detected with more samples
- **Trade-off**: Higher accuracy requires more processing time

## Performance Tips

- For **real-time demos**: Use 10-20 frames
- For **production/critical work**: Use 100 frames
- **Video length**: Longer videos take more time to process
- **GPU**: If available, significantly speeds up processing (not required)

## Error Prevention

✅ Make sure your video contains faces
✅ Use good quality videos (not too blurry)
✅ Adequate lighting in the video helps face detection
✅ Wait for processing to complete (don't refresh the page)

---

**Current Server Status**: ✅ Running on http://localhost:8000/
**Last Updated**: January 26, 2026
