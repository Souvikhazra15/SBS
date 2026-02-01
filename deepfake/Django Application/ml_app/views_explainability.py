"""
Enhanced Views for Deepfake Detection with Explainability Features

These views EXTEND the existing functionality without modifying
the core inference logic. They add:
- Explainability analysis endpoints
- Forensics dashboard
- Webcam detection interface
- API endpoints for frontend consumption

IMPORTANT: All business logic is in the explainability module.
Views are thin wrappers that delegate to the module.
"""

import json
import os
import time
from typing import Dict, Any, Optional

from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import torch
import cv2
import numpy as np

# Import explainability modules
from .explainability import (
    ExplainabilityPipeline,
    GradCAMExplainer,
    FrameProbabilityTimeline,
    DeepfakeForensicsAnalyzer,
    AudioVideoAnalyzer,
    FakeTypeClassifier,
    ThreatLevelScorer,
    EthicsBiasPanel,
)

# Import existing model and transforms from views
from .views import Model, train_transforms, get_accurate_model, im_size


# ============================================================================
# TEMPLATE NAMES
# ============================================================================
EXPLAINABILITY_TEMPLATE = 'explainability_dashboard.html'
FORENSICS_TEMPLATE = 'forensics_dashboard.html'
WEBCAM_TEMPLATE = 'webcam_detection.html'
ETHICS_TEMPLATE = 'ethics_panel.html'


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_model_for_explainability(sequence_length: int = 20):
    """Load model for explainability analysis."""
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = Model(2)
    
    try:
        model_path = get_accurate_model(sequence_length)
        model.load_state_dict(torch.load(model_path, map_location=torch.device(device)))
        model.to(device)
        model.eval()
        return model, device
    except Exception as e:
        return None, str(e)


def get_explainability_output_dir():
    """Get output directory for explainability analysis."""
    output_dir = os.path.join(settings.MEDIA_ROOT, 'explainability')
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


# ============================================================================
# EXPLAINABILITY DASHBOARD VIEW
# ============================================================================

def explainability_dashboard(request):
    """
    Main explainability dashboard view.
    
    Displays all explainability features for a previously analyzed video.
    """
    context = {
        'page_title': 'Deepfake Detection - Explainability Dashboard',
    }
    
    # Get video info from session
    if 'file_name' in request.session:
        context['video_path'] = request.session['file_name']
        context['video_name'] = os.path.basename(request.session['file_name'])
    
    if 'prediction_result' in request.session:
        context['prediction'] = request.session['prediction_result']
    
    if 'explainability_result' in request.session:
        context['explainability'] = request.session['explainability_result']
    
    # Get ethics panel
    ethics_panel = EthicsBiasPanel()
    context['ethics_summary'] = ethics_panel.generate_summary()
    
    return render(request, EXPLAINABILITY_TEMPLATE, context)


# ============================================================================
# GRAD-CAM API ENDPOINT
# ============================================================================

@require_POST
@csrf_exempt
def api_gradcam_analysis(request):
    """
    API endpoint for Grad-CAM heatmap generation.
    
    POST /api/explainability/gradcam/
    Body: { "video_path": "path/to/video", "frame_indices": [0, 5, 10] }
    
    Returns: { "heatmaps": [...], "summary": {...} }
    """
    try:
        data = json.loads(request.body)
        video_path = data.get('video_path')
        frame_indices = data.get('frame_indices', [])
        sequence_length = data.get('sequence_length', 20)
        
        if not video_path or not os.path.exists(video_path):
            return JsonResponse({'error': 'Invalid video path'}, status=400)
        
        # Load model
        model, device = load_model_for_explainability(sequence_length)
        if model is None:
            return JsonResponse({'error': f'Failed to load model: {device}'}, status=500)
        
        # Load video frames
        cap = cv2.VideoCapture(video_path)
        frames = []
        while len(frames) < sequence_length:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        
        if len(frames) < sequence_length:
            return JsonResponse({'error': 'Not enough frames in video'}, status=400)
        
        # Preprocess frames
        processed = []
        for frame in frames:
            tensor = train_transforms(frame)
            processed.append(tensor)
        
        input_tensor = torch.stack(processed).unsqueeze(0)
        
        # Generate Grad-CAM
        output_dir = os.path.join(get_explainability_output_dir(), 'gradcam')
        os.makedirs(output_dir, exist_ok=True)
        
        from .explainability.gradcam import generate_sequence_gradcam
        results = generate_sequence_gradcam(
            model, input_tensor, frames,
            output_dir, os.path.basename(video_path).split('.')[0]
        )
        
        # Convert paths to URLs
        heatmaps = []
        for r in results:
            if r.get('save_path'):
                rel_path = os.path.relpath(r['save_path'], settings.MEDIA_ROOT)
                heatmaps.append({
                    'frame_idx': r['frame_idx'],
                    'url': f"{settings.MEDIA_URL}{rel_path}",
                    'confidence': r['confidence']
                })
        
        return JsonResponse({
            'heatmaps': heatmaps,
            'summary': {
                'frames_processed': len(results),
                'average_confidence': np.mean([r['confidence'] for r in results]) if results else 0
            }
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# TIMELINE API ENDPOINT
# ============================================================================

@require_POST
@csrf_exempt
def api_timeline_analysis(request):
    """
    API endpoint for frame probability timeline.
    
    POST /api/explainability/timeline/
    Body: { "video_path": "path/to/video" }
    
    Returns: Chart.js compatible data
    """
    try:
        data = json.loads(request.body)
        video_path = data.get('video_path')
        sequence_length = data.get('sequence_length', 20)
        
        if not video_path or not os.path.exists(video_path):
            return JsonResponse({'error': 'Invalid video path'}, status=400)
        
        # Load model
        model, device = load_model_for_explainability(sequence_length)
        if model is None:
            return JsonResponse({'error': f'Failed to load model: {device}'}, status=500)
        
        # Load and preprocess video
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        
        frames = []
        while len(frames) < sequence_length:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        
        if len(frames) < sequence_length:
            return JsonResponse({'error': 'Not enough frames'}, status=400)
        
        # Preprocess
        processed = [train_transforms(f) for f in frames]
        input_tensor = torch.stack(processed).unsqueeze(0)
        
        # Extract timeline
        from .explainability.timeline import extract_frame_probabilities_from_model
        timeline = extract_frame_probabilities_from_model(model, input_tensor, fps)
        
        return JsonResponse({
            'chartjs_data': timeline.to_chartjs_data(),
            'statistics': timeline.get_temporal_stats()
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# FORENSICS API ENDPOINT
# ============================================================================

@require_POST
@csrf_exempt
def api_forensics_analysis(request):
    """
    API endpoint for forensics analysis.
    
    POST /api/explainability/forensics/
    Body: { "video_path": "path/to/video", "max_frames": 100 }
    
    Returns: Forensics metrics
    """
    try:
        data = json.loads(request.body)
        video_path = data.get('video_path')
        max_frames = data.get('max_frames', 100)
        
        if not video_path or not os.path.exists(video_path):
            return JsonResponse({'error': 'Invalid video path'}, status=400)
        
        # Run forensics analysis
        analyzer = DeepfakeForensicsAnalyzer()
        metrics = analyzer.analyze_video(video_path, max_frames)
        
        return JsonResponse({
            'metrics': analyzer.to_dict(),
            'summary': {
                'face_consistency': metrics.face_consistency_score,
                'eye_blink': metrics.eye_blink_score,
                'temporal_stability': metrics.temporal_stability_score,
                'artifacts': metrics.compression_artifact_score,
                'overall': metrics.overall_forensics_score
            }
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# MULTIMODAL API ENDPOINT
# ============================================================================

@require_POST
@csrf_exempt
def api_multimodal_analysis(request):
    """
    API endpoint for audio-video analysis.
    
    POST /api/explainability/multimodal/
    Body: { "video_path": "path/to/video" }
    
    Returns: Multi-modal analysis results
    """
    try:
        data = json.loads(request.body)
        video_path = data.get('video_path')
        
        if not video_path or not os.path.exists(video_path):
            return JsonResponse({'error': 'Invalid video path'}, status=400)
        
        # Run multi-modal analysis
        analyzer = AudioVideoAnalyzer()
        result = analyzer.analyze(video_path)
        
        return JsonResponse(analyzer.to_dict(result))
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# THREAT LEVEL API ENDPOINT
# ============================================================================

@require_POST
@csrf_exempt
def api_threat_assessment(request):
    """
    API endpoint for threat level assessment.
    
    POST /api/explainability/threat/
    Body: { 
        "prediction": {"prediction_label": "FAKE", "confidence": 85.5},
        "forensics": {...},
        "multimodal": {...}
    }
    
    Returns: Threat assessment
    """
    try:
        data = json.loads(request.body)
        prediction = data.get('prediction', {})
        forensics = data.get('forensics')
        multimodal = data.get('multimodal')
        timeline = data.get('timeline')
        fake_type = data.get('fake_type')
        
        # Run threat assessment
        scorer = ThreatLevelScorer()
        result = scorer.assess(
            model_prediction=prediction,
            forensics_metrics=forensics,
            multimodal_metrics=multimodal,
            timeline_stats=timeline,
            fake_type_result=fake_type
        )
        
        return JsonResponse(scorer.to_dict(result))
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# FAKE TYPE CLASSIFICATION API ENDPOINT
# ============================================================================

@require_POST
@csrf_exempt
def api_fake_classification(request):
    """
    API endpoint for fake type classification.
    
    POST /api/explainability/classify/
    Body: { 
        "prediction": {...},
        "forensics": {...},
        "multimodal": {...},
        "timeline": {...}
    }
    
    Returns: Fake type classification
    """
    try:
        data = json.loads(request.body)
        
        classifier = FakeTypeClassifier()
        result = classifier.classify(
            model_prediction=data.get('prediction', {}),
            forensics_metrics=data.get('forensics'),
            multimodal_metrics=data.get('multimodal'),
            timeline_stats=data.get('timeline')
        )
        
        return JsonResponse(classifier.get_classification_report(result))
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# COMPLETE ANALYSIS API ENDPOINT
# ============================================================================

@require_POST
@csrf_exempt
def api_complete_analysis(request):
    """
    API endpoint for complete explainability analysis.
    
    POST /api/explainability/analyze/
    Body: { 
        "video_path": "path/to/video",
        "prediction": {...},
        "sequence_length": 20,
        "enable_gradcam": true,
        "enable_forensics": true,
        ...
    }
    
    Returns: Complete ExplainabilityResult
    """
    try:
        data = json.loads(request.body)
        video_path = data.get('video_path')
        prediction = data.get('prediction', {})
        sequence_length = data.get('sequence_length', 20)
        
        if not video_path or not os.path.exists(video_path):
            return JsonResponse({'error': 'Invalid video path'}, status=400)
        
        # Load model
        model, device = load_model_for_explainability(sequence_length)
        
        # Create pipeline
        pipeline = ExplainabilityPipeline(
            model=model,
            transform=train_transforms,
            device=device,
            output_dir=get_explainability_output_dir()
        )
        
        # Load frames and prepare input tensor
        cap = cv2.VideoCapture(video_path)
        frames = []
        while len(frames) < sequence_length:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        
        input_tensor = None
        if frames and model is not None:
            processed = [train_transforms(f) for f in frames]
            if len(processed) >= sequence_length:
                input_tensor = torch.stack(processed[:sequence_length]).unsqueeze(0)
        
        # Run analysis
        result = pipeline.analyze_video(
            video_path=video_path,
            model_prediction=prediction,
            input_tensor=input_tensor,
            frames=frames,
            enable_gradcam=data.get('enable_gradcam', True),
            enable_timeline=data.get('enable_timeline', True),
            enable_forensics=data.get('enable_forensics', True),
            enable_multimodal=data.get('enable_multimodal', True),
            enable_classification=data.get('enable_classification', True),
            enable_threat=data.get('enable_threat', True),
            max_frames=data.get('max_frames', 100),
            video_name=os.path.basename(video_path).split('.')[0]
        )
        
        return JsonResponse(pipeline.to_dict(result))
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# ETHICS PANEL VIEW
# ============================================================================

def ethics_panel_view(request):
    """Display ethics and bias panel."""
    ethics = EthicsBiasPanel()
    panel = ethics.generate_panel()
    
    context = {
        'panel': ethics.to_dict(panel),
        'html_panel': ethics.generate_html_panel(),
        'summary': ethics.generate_summary()
    }
    
    return render(request, ETHICS_TEMPLATE, context)


@require_GET
def api_ethics_panel(request):
    """API endpoint for ethics panel data."""
    ethics = EthicsBiasPanel()
    panel = ethics.generate_panel()
    
    return JsonResponse(ethics.to_dict(panel))


# ============================================================================
# WEBCAM DETECTION VIEW
# ============================================================================

def webcam_detection_view(request):
    """
    Webcam detection interface.
    
    This renders the webcam page. Actual detection happens client-side
    with periodic API calls to the backend.
    """
    context = {
        'page_title': 'Real-Time Deepfake Detection',
        'inference_interval': 15,  # Frames between inferences
        'fake_threshold': 0.6,
        'sequence_length': 20
    }
    
    return render(request, WEBCAM_TEMPLATE, context)


@require_POST
@csrf_exempt
def api_webcam_inference(request):
    """
    API endpoint for webcam frame inference.
    
    POST /api/webcam/infer/
    Body: { "frames": [base64_encoded_frames], "sequence_length": 20 }
    
    Returns: { "prediction": "FAKE/REAL", "confidence": 85.5, "fake_probability": 0.855 }
    """
    try:
        import base64
        
        data = json.loads(request.body)
        frames_b64 = data.get('frames', [])
        sequence_length = data.get('sequence_length', 20)
        
        if len(frames_b64) < sequence_length:
            return JsonResponse({'error': 'Not enough frames'}, status=400)
        
        # Decode frames
        frames = []
        for b64 in frames_b64[-sequence_length:]:
            img_data = base64.b64decode(b64)
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is not None:
                frames.append(frame)
        
        if len(frames) < sequence_length:
            return JsonResponse({'error': 'Failed to decode frames'}, status=400)
        
        # Load model
        model, device = load_model_for_explainability(sequence_length)
        if model is None:
            return JsonResponse({'error': 'Failed to load model'}, status=500)
        
        # Preprocess
        processed = [train_transforms(f) for f in frames]
        input_tensor = torch.stack(processed).unsqueeze(0).to(device)
        
        # Inference
        import torch.nn.functional as F
        
        model.eval()
        with torch.no_grad():
            fmap, logits = model(input_tensor)
            probs = F.softmax(logits, dim=1)
        
        fake_prob = probs[0, 0].item()
        real_prob = probs[0, 1].item()
        
        prediction = 'FAKE' if fake_prob > real_prob else 'REAL'
        confidence = max(fake_prob, real_prob) * 100
        
        return JsonResponse({
            'prediction': prediction,
            'confidence': confidence,
            'fake_probability': fake_prob,
            'real_probability': real_prob
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# FORENSICS DASHBOARD VIEW
# ============================================================================

def forensics_dashboard_view(request):
    """
    Forensics investigation dashboard.
    
    Displays all forensic metrics in an investigation-style interface.
    """
    context = {
        'page_title': 'Deepfake Forensics Investigation Dashboard',
    }
    
    # Get video from session if available
    if 'file_name' in request.session:
        video_path = request.session['file_name']
        context['video_path'] = video_path
        context['video_name'] = os.path.basename(video_path)
        
        # Run quick forensics if video exists
        if os.path.exists(video_path):
            try:
                analyzer = DeepfakeForensicsAnalyzer()
                metrics = analyzer.analyze_video(video_path, max_frames=50)
                context['metrics'] = analyzer.to_dict()
            except Exception as e:
                context['error'] = str(e)
    
    return render(request, FORENSICS_TEMPLATE, context)
