"""
Ethics and Bias Panel Module

Generates professional ethics and bias disclosure panels for:
- Dataset source information
- Known bias risks
- False positive scenarios
- Responsible usage disclaimers

Tone: Professional, courtroom/newsroom safe.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BiasRisk:
    """Individual bias risk entry."""
    category: str
    description: str
    mitigation: str
    severity: str  # low, medium, high


@dataclass
class EthicsPanel:
    """Complete ethics and bias disclosure panel."""
    dataset_info: Dict[str, Any]
    bias_risks: List[BiasRisk]
    false_positive_scenarios: List[Dict[str, str]]
    limitations: List[str]
    responsible_use_guidelines: List[str]
    disclaimer: str
    last_updated: str


class EthicsBiasPanel:
    """
    Generates ethics and bias disclosure panels.
    
    Provides transparency about model limitations, bias risks,
    and responsible usage guidelines for legal and journalistic contexts.
    """
    
    # Dataset information based on common deepfake training data
    DEFAULT_DATASET_INFO = {
        'name': 'Multi-Source Deepfake Detection Dataset',
        'sources': [
            {
                'name': 'FaceForensics++',
                'description': 'Academic dataset with various manipulation methods',
                'size': 'Thousands of videos',
                'manipulations': ['DeepFakes', 'Face2Face', 'FaceSwap', 'NeuralTextures']
            },
            {
                'name': 'Celeb-DF',
                'description': 'Celebrity deepfake videos with high visual quality',
                'size': '590 real, 5,639 fake videos',
                'manipulations': ['DeepFake face swaps']
            },
            {
                'name': 'DFDC (Deepfake Detection Challenge)',
                'description': 'Facebook/Meta research dataset',
                'size': 'Over 100,000 videos',
                'manipulations': ['Various GAN-based methods']
            }
        ],
        'preprocessing': 'Face extraction, alignment, and normalization',
        'augmentation': 'Standard image augmentations for robustness',
        'split': 'Training/Validation/Test with stratified sampling'
    }
    
    DEFAULT_BIAS_RISKS = [
        BiasRisk(
            category='Demographic Representation',
            description='Training data may over-represent certain demographic groups, '
                       'potentially affecting detection accuracy across different ethnicities, '
                       'ages, and genders.',
            mitigation='Cross-reference with multiple detection methods for underrepresented groups. '
                      'Consider manual review for edge cases.',
            severity='high'
        ),
        BiasRisk(
            category='Lighting and Quality',
            description='Model trained primarily on well-lit, high-quality video may perform '
                       'differently on low-light, compressed, or mobile-captured content.',
            mitigation='Account for video quality when interpreting results. '
                      'Lower confidence thresholds for degraded content.',
            severity='medium'
        ),
        BiasRisk(
            category='Generation Method Bias',
            description='Detection accuracy may vary based on the deepfake generation method. '
                       'Newer manipulation techniques not in training data may evade detection.',
            mitigation='Regularly update detection models. Use ensemble methods. '
                      'Do not rely solely on automated detection.',
            severity='high'
        ),
        BiasRisk(
            category='Temporal Limitations',
            description='Model was trained on data available up to a specific date. '
                       'Rapid advancement in generation technology may outpace detection.',
            mitigation='Treat as one input among many in verification workflow. '
                      'Maintain awareness of emerging deepfake technologies.',
            severity='medium'
        ),
        BiasRisk(
            category='Compression Artifacts',
            description='Heavy video compression (common on social media) can mask '
                       'manipulation artifacts or create false positives.',
            mitigation='When possible, analyze original quality content. '
                      'Consider compression level in confidence assessment.',
            severity='medium'
        )
    ]
    
    DEFAULT_FALSE_POSITIVE_SCENARIOS = [
        {
            'scenario': 'Heavy Makeup or Face Paint',
            'description': 'Theatrical makeup, face paint, or heavy cosmetics may '
                          'trigger false positives due to unnatural facial appearance.',
            'recommendation': 'Consider context; theatrical or artistic content may need '
                            'different interpretation.'
        },
        {
            'scenario': 'Plastic Surgery or Medical Conditions',
            'description': 'Individuals with facial surgery, prosthetics, or medical '
                          'conditions affecting facial appearance may be flagged incorrectly.',
            'recommendation': 'Do not use results as sole evidence. Consider medical/cosmetic context.'
        },
        {
            'scenario': 'Poor Video Quality',
            'description': 'Extremely low resolution, heavy compression, or degraded video '
                          'may produce unreliable results in either direction.',
            'recommendation': 'Seek higher quality source material when possible. '
                            'Reduce confidence in results for degraded content.'
        },
        {
            'scenario': 'Animation and CGI',
            'description': 'Computer-generated or animated content featuring realistic faces '
                          'will typically be flagged as fake, even if not a "deepfake."',
            'recommendation': 'Understand the difference between "synthetic" and "deepfake." '
                            'CGI detection is not the same as deceptive manipulation detection.'
        },
        {
            'scenario': 'Unusual Lighting Conditions',
            'description': 'Extreme backlighting, colored lighting, or unusual shadows may '
                          'create artifacts that resemble manipulation.',
            'recommendation': 'Consider filming conditions. Request source context.'
        },
        {
            'scenario': 'Twins or Look-alikes',
            'description': 'Natural resemblance between individuals may not be a manipulation, '
                          'but could be flagged if facial features seem inconsistent.',
            'recommendation': 'Verify subject identity through other means.'
        }
    ]
    
    DEFAULT_LIMITATIONS = [
        'This system is an ASSISTIVE tool, not a definitive truth detector.',
        'Results should be interpreted by trained professionals.',
        'The model cannot detect all forms of manipulation or deception.',
        'New manipulation techniques may evade detection.',
        'Context and provenance are crucial for proper interpretation.',
        'False positives and false negatives are possible in any automated system.',
        'The system cannot determine intent or malice behind content.',
        'Audio-only or audio-focused deepfakes may require specialized tools.',
        'Real-time detection may have different accuracy than offline analysis.',
        'Results are probabilistic, not deterministic.'
    ]
    
    DEFAULT_RESPONSIBLE_USE = [
        'Always use as one component of a comprehensive verification workflow.',
        'Never publicly accuse individuals based solely on automated detection.',
        'Consider the potential harm of both false positives and false negatives.',
        'Maintain awareness of the limitations and biases of the system.',
        'Document methodology and limitations when presenting results.',
        'Seek expert review for high-stakes decisions.',
        'Respect privacy and consent when analyzing content.',
        'Do not use to harass, defame, or discriminate.',
        'Report genuine deepfakes through appropriate channels.',
        'Stay informed about advances in both generation and detection technology.'
    ]
    
    DEFAULT_DISCLAIMER = """
IMPORTANT DISCLAIMER

This deepfake detection system is provided as an analytical tool to assist in 
content verification. It is NOT a definitive determination of authenticity.

LEGAL NOTICE: Results from this system should not be used as the sole basis 
for legal action, public accusations, or employment decisions. All findings 
should be verified through additional means and interpreted by qualified 
professionals.

ACCURACY LIMITATIONS: While this system has been validated on benchmark 
datasets, real-world accuracy may vary based on content quality, manipulation 
method, and other factors. Both false positives (authentic content flagged 
as fake) and false negatives (fake content missed) are possible.

NO WARRANTY: This system is provided "as is" without warranty of any kind. 
The developers do not guarantee detection of all deepfakes or promise zero 
false positives.

RESPONSIBLE USE: Users agree to use this system responsibly, ethically, and 
in compliance with all applicable laws and regulations. Misuse of results to 
harm, defame, or deceive is strictly prohibited.

For critical decisions, always consult with digital forensics experts and 
legal counsel.
"""
    
    def __init__(
        self,
        dataset_info: Optional[Dict[str, Any]] = None,
        additional_biases: Optional[List[BiasRisk]] = None,
        custom_disclaimer: Optional[str] = None
    ):
        """
        Initialize ethics panel generator.
        
        Args:
            dataset_info: Custom dataset information
            additional_biases: Additional bias risks to include
            custom_disclaimer: Custom disclaimer text
        """
        self.dataset_info = dataset_info or self.DEFAULT_DATASET_INFO
        self.bias_risks = list(self.DEFAULT_BIAS_RISKS)
        if additional_biases:
            self.bias_risks.extend(additional_biases)
        self.disclaimer = custom_disclaimer or self.DEFAULT_DISCLAIMER
    
    def generate_panel(
        self,
        include_dataset: bool = True,
        include_biases: bool = True,
        include_false_positives: bool = True,
        include_limitations: bool = True,
        include_guidelines: bool = True,
        include_disclaimer: bool = True
    ) -> EthicsPanel:
        """
        Generate complete ethics and bias panel.
        
        Args:
            include_*: Flags to include specific sections
        
        Returns:
            EthicsPanel with all requested information
        """
        return EthicsPanel(
            dataset_info=self.dataset_info if include_dataset else {},
            bias_risks=self.bias_risks if include_biases else [],
            false_positive_scenarios=self.DEFAULT_FALSE_POSITIVE_SCENARIOS if include_false_positives else [],
            limitations=self.DEFAULT_LIMITATIONS if include_limitations else [],
            responsible_use_guidelines=self.DEFAULT_RESPONSIBLE_USE if include_guidelines else [],
            disclaimer=self.disclaimer if include_disclaimer else "",
            last_updated=datetime.now().strftime("%Y-%m-%d")
        )
    
    def generate_summary(self) -> str:
        """Generate concise summary for display."""
        return """
DEEPFAKE DETECTION ETHICS SUMMARY

⚠️ IMPORTANT: This tool provides probabilistic assessments, not definitive truth.

KEY POINTS:
• Results require professional interpretation
• Demographic and quality biases may affect accuracy  
• Both false positives and false negatives are possible
• Never use as sole basis for accusations or legal action
• Context and provenance are essential for proper interpretation

This system is designed to ASSIST human judgment, not replace it.
For high-stakes decisions, consult digital forensics experts.
"""
    
    def to_dict(self, panel: EthicsPanel) -> Dict[str, Any]:
        """Convert panel to dictionary for JSON serialization."""
        return {
            'dataset_info': panel.dataset_info,
            'bias_risks': [
                {
                    'category': br.category,
                    'description': br.description,
                    'mitigation': br.mitigation,
                    'severity': br.severity
                }
                for br in panel.bias_risks
            ],
            'false_positive_scenarios': panel.false_positive_scenarios,
            'limitations': panel.limitations,
            'responsible_use_guidelines': panel.responsible_use_guidelines,
            'disclaimer': panel.disclaimer,
            'last_updated': panel.last_updated
        }
    
    def generate_html_panel(self) -> str:
        """Generate HTML formatted ethics panel."""
        panel = self.generate_panel()
        
        html = """
<div class="ethics-panel">
    <h3>⚖️ Ethics & Bias Disclosure</h3>
    
    <div class="ethics-section">
        <h4>📊 Dataset Sources</h4>
        <p>Model trained on: {sources}</p>
    </div>
    
    <div class="ethics-section">
        <h4>⚠️ Known Bias Risks</h4>
        <ul>
            {biases}
        </ul>
    </div>
    
    <div class="ethics-section">
        <h4>🔍 Potential False Positive Scenarios</h4>
        <ul>
            {false_positives}
        </ul>
    </div>
    
    <div class="ethics-section">
        <h4>📋 System Limitations</h4>
        <ul>
            {limitations}
        </ul>
    </div>
    
    <div class="ethics-section">
        <h4>✅ Responsible Use Guidelines</h4>
        <ul>
            {guidelines}
        </ul>
    </div>
    
    <div class="disclaimer">
        <h4>📜 Legal Disclaimer</h4>
        <p>{disclaimer}</p>
    </div>
    
    <p class="updated">Last updated: {date}</p>
</div>
""".format(
            sources=', '.join([s['name'] for s in panel.dataset_info.get('sources', [])]),
            biases='\n'.join([f"<li><strong>{br.category}:</strong> {br.description}</li>" 
                             for br in panel.bias_risks[:3]]),
            false_positives='\n'.join([f"<li><strong>{fp['scenario']}:</strong> {fp['description']}</li>" 
                                       for fp in panel.false_positive_scenarios[:3]]),
            limitations='\n'.join([f"<li>{lim}</li>" for lim in panel.limitations[:5]]),
            guidelines='\n'.join([f"<li>{g}</li>" for g in panel.responsible_use_guidelines[:5]]),
            disclaimer=panel.disclaimer.replace('\n', '<br>'),
            date=panel.last_updated
        )
        
        return html
