"""project_settings URL Configuration

Extended with explainability endpoints for:
- Grad-CAM visual explanations
- Frame probability timeline
- Forensics investigation dashboard
- Real-time webcam detection
- Multi-modal audio-video analysis
- Fake type classification
- Threat level scoring
- Ethics & bias disclosure panel
"""
from django.contrib import admin
from django.urls import path, include
from . import views
from .views import about, index, predict_page, cuda_full
from .urls_explainability import explainability_urlpatterns

app_name = 'ml_app'
handler404 = views.handler404

urlpatterns = [
    # Existing routes
    path('', index, name='home'),
    path('about/', about, name='about'),
    path('predict/', predict_page, name='predict'),
    path('cuda_full/', cuda_full, name='cuda_full'),
    
    # Explainability routes (additive)
] + explainability_urlpatterns
