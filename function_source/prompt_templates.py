"""
Civic Intelligence Module – Prompt Templates
=============================================
Centralized prompt engineering for Gemini Pro Vision analysis.
Each prompt instructs the model to act as a civic infrastructure expert
and return a strictly structured JSON report.
"""

# ── Severity Rubric (embedded in prompts for consistency) ────────────────────

SEVERITY_RUBRIC = """
SEVERITY SCALE (use this exact rubric):
  1-2 (Minor):    Cosmetic issue, no safety risk. E.g., faded road markings.
  3-4 (Moderate): Functional degradation, low safety risk. E.g., small pothole, minor leak.
  5-6 (Significant): Notable hazard, moderate risk to public. E.g., large pothole, fallen signage.
  7-8 (Severe):   Immediate hazard, high risk. E.g., flooded road, exposed wiring, large sinkhole.
  9-10 (Critical): Life-threatening, requires emergency response. E.g., structural collapse, gas leak, active fire.
"""

# ── JSON Output Schema Instruction ───────────────────────────────────────────

JSON_SCHEMA_INSTRUCTION = """
You MUST respond with ONLY a valid JSON object (no markdown, no backticks, no explanation).
The JSON must follow this exact schema:

{
  "scene_description": "A detailed, contextual narrative of what is happening in the scene. Do NOT just list objects. Describe the situation as a field investigator would report it. Example: 'Severe flooding has submerged approximately 200 meters of a two-lane residential road, blocking access to a visible school zone ahead.'",

  "incident_type": "One of: infrastructure_damage | flooding | fire_hazard | electrical_hazard | road_obstruction | environmental_hazard | structural_failure | traffic_incident | waste_or_pollution | vegetation_hazard | public_safety | other",

  "severity": {
    "level": <integer 1-10>,
    "label": "Minor | Moderate | Significant | Severe | Critical",
    "justification": "Explain why this severity level was assigned, referencing specific visual evidence."
  },

  "root_cause_analysis": {
    "probable_cause": "What most likely caused this incident based on visual evidence.",
    "contributing_factors": ["factor1", "factor2"],
    "confidence": "low | medium | high"
  },

  "predictive_risks": [
    {
      "risk": "Description of a future risk if this is not addressed.",
      "timeframe": "within_hours | within_days | within_weeks | within_months",
      "probability": "low | medium | high | very_high",
      "mitigation": "Recommended action to prevent this risk."
    }
  ],

  "public_safety_impact": {
    "affected_population_estimate": "Estimated number or range of people affected (e.g., '50-200 residents').",
    "affected_services": ["List of affected services, e.g., 'school access', 'emergency vehicle routes', 'public transit'"],
    "accessibility_impact": "How this affects mobility-impaired individuals, elderly, or children.",
    "urgency_label": "routine | elevated | urgent | emergency"
  },

  "recommended_actions": [
    {
      "priority": <integer 1-5, where 1 is highest>,
      "action": "Specific action to take.",
      "responsible_party": "Which department or service should handle this (e.g., 'Public Works', 'Fire Department', 'Electrical Utility')."
    }
  ],

  "environmental_context": {
    "location_type": "residential | commercial | industrial | highway | school_zone | park | mixed",
    "time_sensitivity": "Is the issue worse at certain times? E.g., 'Rush hour increases risk significantly.'",
    "weather_sensitivity": "Would rain/heat/cold make this worse? E.g., 'Rain will accelerate erosion around the sinkhole.'"
  },

  "authenticity_assessment": {
    "is_ai_generated": <true or false>,
    "confidence": "low | medium | high",
    "indicators": ["List specific signs that led to your conclusion. E.g., 'perfect bilateral symmetry unlikely in real damage', 'text artifacts on signage', 'unnatural lighting gradient', 'too-clean edges on cracks'. If authentic, list indicators of authenticity like 'natural noise grain', 'consistent lens distortion', 'realistic weathering patterns'."],
    "recommendation": "accept | reject | manual_review"
  }
}
"""

# ── STRENGTHENED Standalone Authenticity Check Prompt ────────────────────────

AUTHENTICITY_PROMPT = """You are a FORENSIC IMAGE ANALYST specializing in detecting AI-generated and manipulated images. You must be EXTREMELY CRITICAL and SUSPICIOUS of any image that shows signs of artificial generation.

YOUR MISSION: Determine if this is a REAL PHOTOGRAPH or FAKE/AI-GENERATED.

═══════════════════════════════════════════════════════════════════════
STEP 1: PRIMARY IMAGE TYPE CLASSIFICATION
═══════════════════════════════════════════════════════════════════════

Classify this image into EXACTLY ONE category. BE STRICT:

✅ "photograph" = ONLY if this is clearly a real photo from a physical camera/phone
   - Must show natural imperfections (noise, slight blur, real-world chaos)
   - Must have realistic lighting physics
   - Must NOT be too perfect or artificial

❌ "ai_generated" = Created by AI (Stable Diffusion, Midjourney, DALL-E, ChatGPT, etc.)
   - Look for: impossible geometry, melted details, wrong perspective
   - Look for: too-perfect textures, unnatural smoothness
   - Look for: inconsistent lighting, wrong shadows
   - Look for: text artifacts, warped lettering
   - Look for: repetitive patterns, copy-paste look
   
❌ "3d_render" = CGI, game graphics, architectural renders
❌ "digital_art" = Digital painting, heavily composited/edited beyond recognition
❌ "illustration" = Cartoon, infographic, designed graphic
❌ "drawing" = Sketch, pencil, pen drawing
❌ "screenshot" = Screen capture from software
❌ "painting" = Traditional or digital paint strokes

⚠️ CRITICAL: Do NOT make excuses for suspicious images. If it looks artificial, it IS artificial.

═══════════════════════════════════════════════════════════════════════
STEP 2: FORENSIC SCORING (Score 1-5, where 5 = REAL, 1 = FAKE)
═══════════════════════════════════════════════════════════════════════

Score these 6 metrics critically:

1. TEXTURE_REALISM (Are surfaces realistic?)
   5 = Surfaces look genuinely real with natural imperfections
   4 = Mostly realistic with minor smoothing
   3 = Noticeably smooth but could be phone processing
   2 = Textures look artificial, too clean or too perfect
   1 = Obviously synthetic textures (plastic-looking, melted, wrong)

2. NOISE_GRAIN (Is camera sensor noise present?)
   5 = Natural grain/noise visible especially in shadows/sky
   4 = Minimal noise but still detectable
   3 = Very clean but plausible from modern phone
   2 = Suspiciously clean, lacks natural imperfections
   1 = Completely artificial smoothness, no noise at all

3. LIGHTING_PHYSICS (Does lighting obey physics?)
   5 = Shadows, reflections, and highlights are perfectly realistic
   4 = Lighting is good with minor inconsistencies
   3 = Lighting is acceptable but something feels off
   2 = Clear lighting errors (wrong shadows, impossible reflections)
   1 = Lighting is completely unrealistic or broken

4. EDGE_DEFINITION (How are edges and boundaries handled?)
   5 = Sharp, clean edges where appropriate, natural blur where expected
   4 = Good edge quality with minor artifacts
   3 = Some edge issues but could be compression
   2 = Edges look processed, halos, or unnatural sharpening
   1 = Melted edges, objects bleeding together, AI artifacts

5. DETAIL_CONSISTENCY (Is detail level consistent?)
   5 = Detail is appropriate and consistent throughout
   4 = Minor variations in detail that are natural
   3 = Some areas oddly sharp/blurry but explainable
   2 = Random patches of high/low detail (AI hallmark)
   1 = Severe inconsistency, obvious AI generation patterns

6. REALISM_CHECK (Overall gut check - does this look real?)
   5 = Absolutely looks like a real place/thing photographed
   4 = Looks mostly real with minor questions
   3 = Something feels off but can't pinpoint it
   2 = This doesn't look quite real
   1 = Obviously fake, clearly not a real photograph

═══════════════════════════════════════════════════════════════════════
STEP 3: DETECT AI ARTIFACTS AND RED FLAGS
═══════════════════════════════════════════════════════════════════════

List SPECIFIC observations. Look for these AI tells:

🚨 COMMON AI GENERATION ARTIFACTS:
- Warped or melted text/lettering
- Impossible geometry (buildings bending wrong)
- Inconsistent perspective or vanishing points
- Objects that morph or blend incorrectly
- Too-perfect symmetry in organic elements
- Repetitive patterns that look copy-pasted
- Backgrounds that fade to mush or nonsense
- Details that don't make physical sense
- Lighting from multiple impossible directions
- Shadows that don't match objects
- Reflections that don't match reality
- Textures that repeat artificially
- Colors that are too saturated or wrong
- Depth of field that doesn't follow optics
- Objects floating or defying physics

✅ AUTHENTIC PHOTO INDICATORS:
- Visible sensor noise or grain (especially in sky/shadows)
- JPEG compression artifacts
- Natural lens characteristics (slight distortion, vignetting)
- Motion blur or camera shake
- Realistic depth of field from camera optics
- Natural weathering, dirt, imperfections
- Consistent lighting physics
- Random, chaotic real-world details
- Appropriate metadata artifacts

═══════════════════════════════════════════════════════════════════════
OUTPUT FORMAT (RESPOND WITH ONLY THIS JSON - NO MARKDOWN!)
═══════════════════════════════════════════════════════════════════════

{
  "image_type": "<photograph|ai_generated|3d_render|digital_art|illustration|drawing|screenshot|painting>",
  "scores": {
    "texture_realism": <1-5>,
    "noise_grain": <1-5>,
    "lighting_physics": <1-5>,
    "edge_definition": <1-5>,
    "detail_consistency": <1-5>,
    "realism_check": <1-5>
  },
  "indicators": [
    "List SPECIFIC details you observed",
    "Be precise: 'Text on sign shows warping artifacts' not just 'looks fake'",
    "Include both suspicious AND authentic indicators",
    "Minimum 3 indicators, more is better"
  ]
}

═══════════════════════════════════════════════════════════════════════
REMEMBER: BE SUSPICIOUS. BE CRITICAL. CATCH THE FAKES.
Real photos are IMPERFECT. AI images try to be PERFECT and fail in specific ways.
═══════════════════════════════════════════════════════════════════════
"""

# ── Master Image Analysis Prompt ─────────────────────────────────────────────

IMAGE_ANALYSIS_PROMPT = f"""You are an expert civic infrastructure analyst and public safety assessor.
You are analyzing an image submitted as a citizen incident report.

Your task is to provide a COMPREHENSIVE civic intelligence assessment.

IMPORTANT GUIDELINES:
1. CONTEXTUAL UNDERSTANDING: Do NOT just identify objects. Understand the SITUATION.
   - BAD: "water, road, car"
   - GOOD: "Severe flooding has blocked a major residential road. Water level is approximately 30cm deep, submerging the curb line. A sedan appears stranded mid-road."

2. PREDICTIVE ANALYSIS: Based on visual evidence, predict what could happen next.
   - If you see sparking wires → predict fire/explosion risk with timeframe.
   - If you see a crack in a wall → predict structural failure progression.
   - If you see pooling water → predict flooding escalation during rain.

3. PUBLIC SAFETY FIRST: Always assess the human impact.
   - How many people live/work/travel through this area?
   - Are schools, hospitals, or emergency routes affected?
   - Are vulnerable populations (elderly, children, disabled) at higher risk?

4. BE SPECIFIC WITH NUMBERS: Don't say "some people affected." Estimate: "approximately 100-300 daily commuters on this route."

{SEVERITY_RUBRIC}

VISION AI LABELS DETECTED: {{vision_labels}}

These labels give you baseline object detection. Use them as context but go FAR BEYOND simple labeling.

{JSON_SCHEMA_INSTRUCTION}"""

# ── Video Analysis Prompt ────────────────────────────────────────────────────

VIDEO_ANALYSIS_PROMPT = f"""You are an expert civic infrastructure analyst reviewing a short video clip (up to 10 seconds) from a citizen incident report.

Your task is to provide a COMPREHENSIVE civic intelligence assessment with TEMPORAL ANALYSIS.

CRITICAL VIDEO-SPECIFIC INSTRUCTIONS:
1. TEMPORAL CHANGE DETECTION: Analyze how the situation changes across the video.
   - Is a water leak gushing or dripping? Is the flow rate increasing?
   - Is smoke thickening or dissipating?
   - Are cracks visibly expanding?
   - Is traffic building up around an obstruction?

2. RATE OF CHANGE: Estimate how quickly the situation is deteriorating or improving.
   - "Water flow appears to be increasing at approximately X liters/minute."
   - "Smoke density doubled over the 10-second clip, suggesting active fire growth."

3. MOTION ANALYSIS: Note any moving elements.
   - Vehicles navigating around hazards (indicates road partially passable).
   - People in the area (indicates populated zone at risk).
   - Debris movement (indicates wind or water current direction/speed).

{SEVERITY_RUBRIC}

In addition to the standard assessment fields, you MUST also include a "video_analysis" section:

"video_analysis": {{
  "temporal_trend": "stable | worsening | improving | fluctuating",
  "rate_of_change": "Description of how fast the situation is changing.",
  "duration_estimate": "How long has this been going on based on visual evidence? E.g., 'Flooding appears recent (within 1-2 hours) based on water clarity and minimal debris accumulation.'",
  "key_moments": ["Describe significant moments observed in the video."]
}}

{JSON_SCHEMA_INSTRUCTION}

The "video_analysis" field MUST be included as an additional top-level key in the JSON response.
"""