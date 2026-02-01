# Deepfake Detection Explainability Module

**"We show WHY the model thinks it's fake - this system can be used in courts, newsrooms, and cybersecurity SOCs."**

## Overview

This module adds comprehensive explainability, forensics, and visualization capabilities to the existing deepfake detection system. All features are **ADDITIVE** - they extend the system without modifying the existing model or inference logic.

## Features

### 1. Grad-CAM Visual Explanations
**Location:** `ml_app/explainability/gradcam.py`

Shows WHERE the model is looking when making predictions.

```python
from ml_app.explainability import GradCAMExplainer

explainer = GradCAMExplainer(model)
heatmap = explainer.generate_gradcam_heatmap(frame)
sequence_heatmaps = explainer.generate_sequence_gradcam(frames)
```

- Uses forward/backward hooks on ResNeXt final conv block
- Generates attention heatmaps overlaid on original frames
- No model modification required

### 2. Frame-wise Probability Timeline
**Location:** `ml_app/explainability/timeline.py`

Shows HOW fake probability varies across frames.

```python
from ml_app.explainability import FrameProbabilityTimeline

timeline = FrameProbabilityTimeline(model)
chart_data = timeline.get_chartjs_data(video_path)
stats = timeline.get_statistics()
```

- Temporal consistency analysis
- Anomaly detection with rolling average comparison
- Chart.js compatible output for visualization
- Identifies suspicious spikes in probability

### 3. Forensics Investigation Dashboard
**Location:** `ml_app/explainability/forensics.py`

**"This is not a classifier, it's an investigation tool."**

```python
from ml_app.explainability import DeepfakeForensicsAnalyzer

analyzer = DeepfakeForensicsAnalyzer()
metrics = analyzer.analyze_video(video_path)
summary = analyzer.generate_report(metrics)
```

Metrics include:
- **Face Consistency Score** (0-100): Facial feature stability
- **Eye Blink Pattern Analysis**: Natural blink rate detection
- **Temporal Stability Score** (0-100): Frame-to-frame consistency
- **Compression Artifact Detection**: Blockiness and frequency anomalies

### 4. Real-Time Webcam Detection
**Location:** `ml_app/explainability/webcam.py`

Live demo capability for hackathons and demonstrations.

```python
from ml_app.explainability import WebcamDeepfakeDetector

detector = WebcamDeepfakeDetector(
    model=model,
    inference_interval=15,  # Run every 15 frames
    fake_threshold=0.6
)
detector.start()
```

Features:
- Live probability meter
- Warning overlay on fake detection
- Frame skipping for performance
- CPU-optimized inference

### 5. Multi-Modal Audio-Video Analysis
**Location:** `ml_app/explainability/multimodal.py`

Cross-modal consistency checking.

```python
from ml_app.explainability import AudioVideoAnalyzer

analyzer = AudioVideoAnalyzer()
result = analyzer.analyze_video(video_path)
```

Analyzes:
- **Audio Authenticity**: Pitch variance, jitter analysis
- **Lip-Sync Correlation**: Audio-visual synchronization
- **Mismatch Detection**: Cross-modal inconsistencies

**Note:** Requires `ffmpeg` binary installed on system.

### 6. Fake Type Classification
**Location:** `ml_app/explainability/classifier.py`

**"We don't just detect fake, we classify it."**

```python
from ml_app.explainability import FakeTypeClassifier

classifier = FakeTypeClassifier()
result = classifier.classify(video_path, model_prediction)
```

Categories:
- `GAN_FACE_SWAP`: Face swap using GAN
- `LIP_SYNC`: Lip-sync manipulation
- `FACE_REENACTMENT`: Expression transfer
- `AUTHENTIC`: Genuine content
- `UNKNOWN_MANIPULATION`: Detected but unclassified

### 7. Threat Level Scoring
**Location:** `ml_app/explainability/threat_level.py`

SOC-style decision abstraction for security operations.

```python
from ml_app.explainability import ThreatLevelScorer

scorer = ThreatLevelScorer()
assessment = scorer.assess(
    prediction=model_prediction,
    forensics=forensics_metrics,
    multimodal=multimodal_result
)
```

Levels:
- 🟢 **SAFE** (0-25): Low risk, likely authentic
- 🟡 **SUSPICIOUS** (25-55): Review recommended
- 🟠 **HIGH_RISK** (55-80): Likely manipulated
- 🔴 **CRITICAL** (80-100): High confidence fake

### 8. Ethics & Bias Disclosure Panel
**Location:** `ml_app/explainability/ethics.py`

Professional ethics disclosure for legal and journalistic use.

```python
from ml_app.explainability import EthicsBiasPanel

panel = EthicsBiasPanel()
summary = panel.get_summary()
full_disclosure = panel.to_dict()
```

Includes:
- Dataset source documentation
- Known bias risks and mitigations
- False positive scenarios
- System limitations
- Responsible use guidelines
- Legal disclaimer

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/explainability/` | GET | Main explainability dashboard |
| `/forensics/` | GET | Forensics investigation panel |
| `/webcam/` | GET | Real-time webcam detection |
| `/ethics/` | GET | Ethics disclosure panel |
| `/api/explainability/gradcam/` | POST | Generate Grad-CAM heatmaps |
| `/api/explainability/timeline/` | POST | Get probability timeline |
| `/api/explainability/forensics/` | POST | Run forensics analysis |
| `/api/explainability/multimodal/` | POST | Multi-modal analysis |
| `/api/explainability/threat/` | POST | Threat assessment |
| `/api/explainability/classify/` | POST | Fake type classification |
| `/api/explainability/analyze/` | POST | Complete analysis |
| `/api/webcam/infer/` | POST | Webcam frame inference |

## Integration with Existing System

### Unified Pipeline

```python
from ml_app.explainability import ExplainabilityPipeline

pipeline = ExplainabilityPipeline(model)
result = pipeline.analyze_video(
    video_path,
    prediction,
    enable_gradcam=True,
    enable_forensics=True,
    enable_timeline=True,
    enable_multimodal=True,
    enable_classification=True,
    enable_threat=True
)

# Access results
print(result.threat_level)
print(result.forensics_metrics)
print(result.timeline_stats)
```

### Session-Based Integration

The explainability views integrate with Django sessions to access the current video and prediction:

```python
# In views, after prediction
request.session['video_path'] = video_path
request.session['prediction'] = {
    'prediction_label': 'FAKE',
    'confidence': 87.5
}
# Redirect to explainability dashboard
return redirect('ml_app:explainability_dashboard')
```

## Installation

1. Install additional dependencies:
```bash
pip install ffmpeg-python>=0.2.0
```

2. Install ffmpeg binary (for audio extraction):
   - **Windows:** `choco install ffmpeg` or download from ffmpeg.org
   - **Linux:** `apt install ffmpeg`
   - **macOS:** `brew install ffmpeg`

3. No model retraining required - all features work with existing model.

## Architecture

```
ml_app/explainability/
├── __init__.py           # Package exports
├── gradcam.py            # Visual explanations
├── timeline.py           # Probability timeline
├── forensics.py          # Investigation metrics
├── webcam.py             # Real-time detection
├── multimodal.py         # Audio-video analysis
├── classifier.py         # Fake type classification
├── threat_level.py       # Threat scoring
├── ethics.py             # Bias disclosure
└── integration.py        # Unified pipeline
```

## Design Principles

1. **ADDITIVE Only**: No modification to existing model or inference
2. **Modular**: Each feature is independently usable
3. **CPU-Only**: Works without GPU (performance optimized)
4. **Backward Compatible**: Existing functionality unchanged
5. **Demo-Safe**: Suitable for live demonstrations
6. **Judge-Safe**: Includes ethics disclosure for legal contexts
7. **Explainable**: Every prediction has visible justification

## CPU Performance Considerations

- Grad-CAM: ~500ms per frame on CPU
- Timeline: ~2-3 seconds for 30 frames
- Forensics: ~5 seconds for 100 frames
- Webcam: Configurable inference interval (default: every 15 frames)

## Troubleshooting

### ffmpeg not found
```
Audio extraction requires ffmpeg. Install via:
- Windows: choco install ffmpeg
- Linux: apt install ffmpeg
- macOS: brew install ffmpeg
```

### Slow inference
- Increase `inference_interval` for webcam detection
- Reduce `max_frames` for forensics analysis
- Use smaller frame samples for Grad-CAM

### Memory issues
- Process videos in chunks
- Limit timeline to key frames
- Clear frame buffers after processing

## Legal Disclaimer

This system is provided for research and educational purposes. Detection results should NOT be used as sole evidence in legal proceedings. Always consult with forensic experts and use additional verification methods.

---

*"We show WHY the model thinks it's fake"*
