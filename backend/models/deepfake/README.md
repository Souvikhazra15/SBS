# Deepfake Models

This directory contains the deepfake detection model files.

## Model Files

Model files (`.pt`, `.pth`, `.h5`, etc.) are **not tracked in git** due to their large size.

### Getting the Model

You should:
1. Download the model from your model storage (e.g., cloud storage, model registry)
2. Place the model file in this directory
3. The model file will be automatically ignored by git

### Expected Files

- `deepfake_model.pt` - PyTorch model for deepfake detection

## Note

Never commit large model files to git. Use Git LFS or external storage for model versioning.
