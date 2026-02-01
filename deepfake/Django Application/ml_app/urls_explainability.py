"""
URL Configuration for Explainability Features

These URLs are ADDITIVE and extend the existing URL configuration.
Include this in the main urls.py to enable explainability endpoints.
"""

from django.urls import path
from . import views_explainability as explainability_views

# Explainability URL patterns - to be added to existing urlpatterns
explainability_urlpatterns = [
    # Dashboard views
    path('explainability/', explainability_views.explainability_dashboard, name='explainability_dashboard'),
    path('forensics/', explainability_views.forensics_dashboard_view, name='forensics_dashboard'),
    path('webcam/', explainability_views.webcam_detection_view, name='webcam_detection'),
    path('ethics/', explainability_views.ethics_panel_view, name='ethics_panel'),
    
    # API endpoints
    path('api/explainability/gradcam/', explainability_views.api_gradcam_analysis, name='api_gradcam'),
    path('api/explainability/timeline/', explainability_views.api_timeline_analysis, name='api_timeline'),
    path('api/explainability/forensics/', explainability_views.api_forensics_analysis, name='api_forensics'),
    path('api/explainability/multimodal/', explainability_views.api_multimodal_analysis, name='api_multimodal'),
    path('api/explainability/threat/', explainability_views.api_threat_assessment, name='api_threat'),
    path('api/explainability/classify/', explainability_views.api_fake_classification, name='api_classify'),
    path('api/explainability/analyze/', explainability_views.api_complete_analysis, name='api_complete'),
    path('api/explainability/ethics/', explainability_views.api_ethics_panel, name='api_ethics'),
    
    # Webcam API
    path('api/webcam/infer/', explainability_views.api_webcam_inference, name='api_webcam_infer'),
]
