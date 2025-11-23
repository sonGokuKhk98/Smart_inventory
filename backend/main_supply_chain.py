"""
Supply Chain Logistics API - Combined Solution
Combines: Box Inspection + VAS Label Verification (PRD v6)
Simplified but complete workflow
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import google.generativeai as genai
from PIL import Image
import io
import os
import json
import requests
import random  # Added for auto-generating IDs
from io import BytesIO
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# watsonx Orchestrate Configuration
WATSONX_API_KEY = os.getenv("WATSONX_API_KEY")
WATSONX_URL = os.getenv("WATSONX_URL", "https://api.au-syd.watson-orchestrate.cloud.ibm.com/instances/3503a2be-de47-472c-8069-2b7dcf945e1c")
WATSONX_WEB_CHAT = "https://au-syd.watson-orchestrate.cloud.ibm.com/chat"  # For reference

# Global State for Contextual Memory (Hub Director)
SHIPMENT_HISTORY = {}  # {shipment_id: [list of events]}

app = FastAPI(
    title="Supply Chain Logistics API",
    description="Box inspection + VAS label verification for supply chain automation",
    version="1.0.0",
    servers=[
        {"url": "https://6681f65112a9.ngrok-free.app", "description": "Production Server (ngrok)"},
        {"url": "http://localhost:8000", "description": "Local Development Server"}
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, # Must be False for wildcard origin to work in some browsers
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    print(f"✅ GEMINI_API_KEY found")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("models/gemini-2.5-flash")
else:
    print("❌ WARNING: GEMINI_API_KEY NOT FOUND!")
    model = None

# ============================================================================
# MODELS
# ============================================================================

# Box Inspection Models
class BoxInspectionRequest(BaseModel):
    image_url: str
    shipment_id: Optional[str] = "UNKNOWN"
    expected_condition: Optional[str] = "good"
    priority: str = "STANDARD"           # New: STANDARD, RUSH, CRITICAL
    temperature: Optional[float] = None  # IoT Data
    dimensions: Optional[dict] = None    # {"length": 10, "width": 10, "height": 10}

class DefectFinding(BaseModel):
    defect_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    location: str
    confidence: float
    recommended_action: str

class BoxInspectionResult(BaseModel):
    shipment_id: str
    timestamp: str
    box_condition: str  # GOOD, DAMAGED, CRITICAL
    total_defects: int
    findings: List[DefectFinding]
    can_ship: bool
    conditional_acceptance: bool = False # New: Accept with warnings
    volumetric_check: str = "PASS"       # New: PASS/FAIL based on dimensions
    reasoning: str

# VAS Label Verification Models (PRD v6)
class VASInspectionRequest(BaseModel):
    image_url: str
    station_id: Optional[str] = "Station-1"
    order_id: Optional[str] = "UNKNOWN"
    priority: str = "STANDARD"               # New
    expected_sku: Optional[str] = None
    kitting_list: Optional[List[str]] = None # New: ["Phone", "Charger"]
    aesthetic_check: bool = False            # New: Check for scratches/dust

class LabelMatchResult(BaseModel):
    order_id: str
    station_id: str
    timestamp: str
    label_text: str
    visual_object: str
    match: bool
    kitting_verified: bool = True            # New
    aesthetic_score: float = 1.0             # New: 0.0 to 1.0
    confidence: float
    action_required: str
    reasoning: str

# WMS Check Models
class WMSCheckRequest(BaseModel):
    order_id: str
    sku: Optional[str] = None

class WMSResult(BaseModel):
    order_id: str
    sku: str
    expected_item: str
    quantity: int
    status: str
    predicted_cause: Optional[str] = None        # New: Why mismatch happened
    optimization_suggestion: Optional[str] = None # New: Bin move suggestion
    wms_data: dict

# Exception Handling Models
class ExceptionRequest(BaseModel):
    order_id: str
    exception_type: str
    details: str
    station_id: Optional[str] = None
    vendor_id: Optional[str] = "VENDOR-001" # New

class ExceptionResult(BaseModel):
    ticket_id: str
    order_id: str
    status: str
    action_taken: str
    vendor_email_draft: Optional[str] = None # New
    carrier_rates: Optional[dict] = None     # New
    timestamp: str

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_json_from_text(text: str) -> dict:
    """Extract JSON from Gemini response"""
    try:
        return json.loads(text)
    except:
        pass
    
    clean_text = text.strip()
    if "```json" in clean_text:
        clean_text = clean_text.split("```json")[1].split("```")[0].strip()
    elif "```" in clean_text:
        clean_text = clean_text.split("```")[1].split("```")[0].strip()
    
    try:
        return json.loads(clean_text)
    except:
        pass
    
    start = clean_text.find('{')
    end = clean_text.rfind('}')
    if start != -1 and end != -1:
        try:
            return json.loads(clean_text[start:end+1])
        except:
            pass
    
    raise ValueError(f"Could not parse JSON: {text[:200]}")

# Request/Response Models for watsonx-compatible JSON endpoints
class InspectionRequest(BaseModel):
    image_url: str
    shipment_id: Optional[str] = None
    expected_condition: Optional[str] = "good"
    temperature: Optional[float] = None
    dimensions_str: Optional[str] = None

class VASRequest(BaseModel):
    image_url: str
    expected_label: str
    expected_sku: str

# ============================================================================
# ENDPOINT 1: BOX INSPECTION (Inbound Quality Control)
# ============================================================================

@app.post("/inspect/box", response_model=BoxInspectionResult, operation_id="inspectBox")
async def inspect_box(
    http_request: Request,
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    shipment_id: Optional[str] = Form(None),
    priority: Optional[str] = Form("STANDARD"),
    temperature: Optional[float] = Form(None),
    dimensions_str: Optional[str] = Form(None)
):
    """
    Inspect a box for damage using AI vision analysis.
    
    **For watsonx Orchestrate**: Send JSON body with image_url parameter.
    **For file upload**: Use multipart/form-data with file parameter.
    
    **Parameters**:
    - image_url: Direct URL to box image (required if file not provided)
    - file: Image file upload (required if image_url not provided)
    - shipment_id: Shipment identifier (auto-generated if not provided)
    - priority: STANDARD, RUSH, or CRITICAL (default: STANDARD)
    - temperature: Temperature requirement in Celsius (optional)
    
    **Returns**: Box condition assessment with defect findings and shipping recommendation.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    
    # Check content type to determine if JSON or Form data
    content_type = http_request.headers.get("content-type", "").lower()
    
    # Handle JSON request (from watsonx)
    if "application/json" in content_type:
        try:
            body = await http_request.json()
            request = BoxInspectionRequest(**body)
            image_url = request.image_url
            shipment_id = request.shipment_id or f"SHIP-{random.randint(1000, 9999)}"
            priority = request.priority
            temperature = request.temperature
            dimensions = request.dimensions
        except Exception as e:
            print(f"❌ Error parsing JSON request: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON request: {str(e)}")
    else:
        # Handle Form data (file upload)
        if not shipment_id:
            shipment_id = f"SHIP-{random.randint(1000, 9999)}"
        dimensions = None
        if dimensions_str:
            try:
                dimensions = json.loads(dimensions_str)
            except:
                pass
    
    print(f"🔍 [Agent 1] Inspecting Box: {shipment_id}")
    
    # Handle Image Source
    image = None
    if file:
        content = await file.read()
        image = Image.open(BytesIO(content))
        print(f"  → Image loaded from file upload")
    elif image_url:
        print(f"📥 Downloading image from URL: {image_url}")
        try:
            response = requests.get(image_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            print(f"  ✅ Image downloaded successfully")
        except Exception as e:
            print(f"  ❌ Failed to download image: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to load image from URL: {e}")
    else:
        raise HTTPException(status_code=400, detail="No image provided (file or image_url required)")

    # 1. Contextual Memory Update
    if shipment_id not in SHIPMENT_HISTORY:
        SHIPMENT_HISTORY[shipment_id] = []
    SHIPMENT_HISTORY[shipment_id].append({
        "event": "INSPECTION_REQUESTED",
        "timestamp": datetime.now().isoformat(),
        "priority": priority
    })
    
    try:
        # print(f"📦 Inspecting box: {shipment_id}") # Redundant with line above
        
        # Contextual Memory Update (already done above, but keeping for consistency with original structure)
        # if shipment_id not in SHIPMENT_HISTORY:
        #     SHIPMENT_HISTORY[shipment_id] = []
        # SHIPMENT_HISTORY[shipment_id].append(f"Inspection started at {datetime.now()}")

        # Download image (replaced by image loading logic above)
        # img_resp = requests.get(request.image_url, timeout=10)
        # img_resp.raise_for_status()
        # img_pil = Image.open(BytesIO(img_resp.content))
        
        # Enhanced Prompt for Multi-modal & Granular Defect
        iot_context = ""
        if temperature:
            iot_context = f"IOT SENSOR DATA: Temperature is {temperature}°C. (Safe range: 15-25°C)."
        
        volumetric_context = ""
        if dimensions:
            volumetric_context = f"DIMENSIONS: {dimensions}. Check for volumetric weight discrepancies."

        prompt = f"""
You are a supply chain quality inspector analyzing a SHIPPING BOX.

TASK: Examine this box image and determine if it's safe to ship.

{iot_context}
{volumetric_context}

CHECK FOR:
1. STRUCTURAL DAMAGE (Critical): Crushed, torn, water damage.
2. COSMETIC DAMAGE (Minor): Scratches, dents that don't affect integrity.
3. LABELS: Readable and attached.

Return ONLY valid JSON:
{{
    "box_condition": "GOOD|DAMAGED|CRITICAL",
    "can_ship": true or false,
    "conditional_acceptance": true or false,
    "volumetric_check": "PASS|FAIL",
    "findings": [
        {{
            "defect_type": "crushed|torn|water_damage|missing_label|structural_damage|cosmetic_dent",
            "severity": "LOW|MEDIUM|HIGH|CRITICAL",
            "location": "describe where on the box",
            "confidence": 0.95,
            "recommended_action": "Ship as is|Repack|Reject"
        }}
    ],
    "reasoning": "Brief explanation including IoT/Volumetric analysis if applicable"
}}
"""
        
        response = model.generate_content([prompt, image])
        analysis = extract_json_from_text(response.text.strip())
        
        findings = [
            DefectFinding(
                defect_type=f.get("defect_type", "unknown"),
                severity=f.get("severity", "MEDIUM"),
                location=f.get("location", "unknown"),
                confidence=f.get("confidence", 0.8),
                recommended_action=f.get("recommended_action", "Review manually")
            ) for f in analysis.get("findings", [])
        ]
        
        box_condition = analysis.get("box_condition", "UNKNOWN")
        can_ship = analysis.get("can_ship", False)
        conditional_acceptance = analysis.get("conditional_acceptance", False)
        volumetric_check = analysis.get("volumetric_check", "PASS")
        
        # Logic for Conditional Acceptance
        if any(f.severity == "CRITICAL" for f in findings):
            box_condition = "CRITICAL"
            can_ship = False
            conditional_acceptance = False
        elif any(f.severity == "MEDIUM" for f in findings) and not can_ship:
             # If AI said no ship but only medium defects, maybe conditional?
             # Trusting AI output for now, but this logic could be refined.
             pass

        # IoT Override
        if temperature and (temperature < 15 or temperature > 25):
            box_condition = "CRITICAL"
            can_ship = False
            findings.append(DefectFinding(
                defect_type="temperature_excursion",
                severity="CRITICAL",
                location="internal_sensor",
                confidence=1.0,
                recommended_action="Reject - Temp Spoilage"
            ))

        return BoxInspectionResult(
            shipment_id=shipment_id,
            timestamp=datetime.now().isoformat(),
            box_condition=box_condition,
            total_defects=len(findings),
            findings=findings,
            can_ship=can_ship,
            conditional_acceptance=conditional_acceptance,
            volumetric_check=volumetric_check,
            reasoning=analysis.get("reasoning", "Inspection completed")
        )
        
    except Exception as e:
        print(f"❌ Box inspection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Inspection failed: {str(e)}")

# ============================================================================
# ENDPOINT 2: VAS LABEL VERIFICATION (PRD v6 - The Mismatched Label Scenario)
# ============================================================================

# ============================================================================
# V2 JSON ENDPOINT: Damage Inspection (compatible with watsonx OpenAPI)
# ============================================================================

@app.post("/v2/inspect/damage", response_model=BoxInspectionResult, operation_id="inspectDamage")
async def inspect_damage(request: InspectionRequest):
    """Endpoint matching openapi_visionflow.json for damage inspection.
    Accepts a JSON payload with image_url, shipment_id, and optional expected_condition.
    """
    # Auto‑generate shipment_id if not provided
    shipment_id = request.shipment_id or f"SHIP-{random.randint(1000, 9999)}"
    print(f"🔍 [Agent 1] Inspecting Box (JSON): {shipment_id}")

    # Load image from URL
    try:
        resp = requests.get(request.image_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        image = Image.open(BytesIO(resp.content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to load image from URL: {e}")

    # Contextual memory update
    if shipment_id not in SHIPMENT_HISTORY:
        SHIPMENT_HISTORY[shipment_id] = []
    SHIPMENT_HISTORY[shipment_id].append({"event": "INSPECTION_REQUESTED", "timestamp": datetime.now().isoformat()})

    # Build prompt (reuse logic from inspect_box)
    iot_context = ""
    if hasattr(request, "temperature") and request.temperature:
        iot_context = f"IOT SENSOR DATA: Temperature is {request.temperature}°C. (Safe range: 15‑25°C)."
    dimensions = None
    if hasattr(request, "dimensions_str") and request.dimensions_str:
        try:
            dimensions = json.loads(request.dimensions_str)
        except:
            pass
    volumetric_context = ""
    if dimensions:
        volumetric_context = f"DIMENSIONS: {dimensions}. Check for volumetric weight discrepancies."

    prompt = f"""
You are a supply chain quality inspector analyzing a SHIPPING BOX.

TASK: Examine this box image and determine if it's safe to ship.

{iot_context}
{volumetric_context}

CHECK FOR:
1. STRUCTURAL DAMAGE (Critical): Crushed, torn, water damage.
2. COSMETIC DAMAGE (Minor): Scratches, dents that don't affect integrity.
3. LABELS: Readable and attached.

Return ONLY valid JSON:
{{
    \"box_condition\": \"GOOD|DAMAGED|CRITICAL\",
    \"defects\": [],
    \"reasoning\": \"...\"
}}
"""
    response = model.generate_content([prompt, image])
    analysis = extract_json_from_text(response.text.strip())

    result = BoxInspectionResult(
        shipment_id=shipment_id,
        timestamp=datetime.now().isoformat(),
        box_condition=analysis.get("box_condition", "UNKNOWN"),
        total_defects=len(analysis.get("defects", [])),
        findings=analysis.get("defects", []),
        can_ship=analysis.get("box_condition", "UNKNOWN") == "GOOD",
        reasoning=analysis.get("reasoning", "")
    )
    return result

# ============================================================================
# END OF V2 JSON ENDPOINTS
# ============================================================================
@app.post("/vas/verify_label", response_model=LabelMatchResult, operation_id="verifyVASLabel")
async def verify_vas_label(
    http_request: Request,
    image_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    station_id: Optional[str] = Form("Station-1"),
    order_id: Optional[str] = Form("UNKNOWN"),
    priority: Optional[str] = Form("STANDARD"),
    expected_sku: Optional[str] = Form(None),
    kitting_list_str: Optional[str] = Form(None),
    aesthetic_check: Optional[bool] = Form(False)
):
    """
    Agent 2: QC Specialist (VAS Quality Controller)
    PRD v6: Verifies label text (OCR) matches physical object (Visual)
    This is the "Blue Shirt label on Red Shirt" detection
    
    **For watsonx Orchestrate**: Send JSON body with image_url parameter.
    **For file upload**: Use multipart/form-data with file parameter.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    
    # Check content type to determine if JSON or Form data
    content_type = http_request.headers.get("content-type", "").lower()
    
    # Handle JSON request (from watsonx)
    if "application/json" in content_type:
        try:
            body = await http_request.json()
            request = VASInspectionRequest(**body)
            image_url = request.image_url
            station_id = request.station_id or "Station-1"
            order_id = request.order_id or "UNKNOWN"
            priority = request.priority
            expected_sku = request.expected_sku
            kitting_list = request.kitting_list
            aesthetic_check = request.aesthetic_check
        except Exception as e:
            print(f"❌ Error parsing JSON request: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON request: {str(e)}")
    else:
        # Handle Form data (file upload)
        kitting_list = None
        if kitting_list_str:
            try:
                kitting_list = json.loads(kitting_list_str)
            except:
                pass
    
    print(f"🏷️ [Agent 2] Verifying Label: {order_id}")

    # Handle Image Source
    image = None
    if file:
        content = await file.read()
        image = Image.open(BytesIO(content))
    elif image_url:
        try:
            response = requests.get(image_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to load image from URL: {e}")
    else:
        raise HTTPException(status_code=400, detail="No image provided (file or image_url required)")
        
    try:
        # print(f"🔍 QC Specialist: Verifying label at {request.station_id}") # Replaced
        # print(f"   Order: {request.order_id}") # Replaced
        
        # Download image (replaced by image loading logic above)
        # img_resp = requests.get(request.image_url, timeout=10)
        # img_resp.raise_for_status()
        # img_pil = Image.open(BytesIO(img_resp.content))
        
        expected_text = f"Expected SKU: {expected_sku}" if expected_sku else ""
        
        kitting_instruction = ""
        if kitting_list: # Check if kitting_list is not None
            kitting_instruction = f"KITTING CHECK: Verify these items are present: {', '.join(kitting_list)}."
            
        aesthetic_instruction = ""
        if aesthetic_check: # Use the aesthetic_check parameter directly
            aesthetic_instruction = "AESTHETIC CHECK: Look for minor scratches, dust, or packaging misalignment. Rate condition 0.0-1.0."

        prompt = f"""
You are a VAS (Value-Added Services) Quality Control Specialist on a repacking line.

YOUR CRITICAL TASK: Verify that the shipping label matches the physical product.

STEP 1 - READ THE LABEL (OCR):
- Extract ALL text visible on labels, barcodes, or packaging

STEP 2 - IDENTIFY THE PHYSICAL OBJECT:
- What product/item is actually in the package?
- Look for: Product color, size, type, visible features

STEP 3 - COMPARE AND VERIFY:
- Does the label text match what you see?
- {expected_text}

STEP 4 - SPECIAL CHECKS:
{kitting_instruction}
{aesthetic_instruction}

Return ONLY valid JSON:
{{
    "label_text": "exact text read from label (OCR)",
    "visual_object": "description of what you see in the package",
    "match": true or false,
    "kitting_verified": true or false,
    "aesthetic_score": 0.95,
    "confidence": 0.95,
    "action_required": "PASS|STOP_LINE|RELABEL",
    "reasoning": "explain why match/mismatch"
}}

CRITICAL: If label and object don't match, set match=false and action_required="STOP_LINE"
"""
        
        print("  → Running OCR + Visual Analysis...")
        response = model.generate_content([prompt, image])
        analysis = extract_json_from_text(response.text.strip())
        
        label_text = analysis.get("label_text", "Could not read label")
        visual_object = analysis.get("visual_object", "Could not identify object")
        match = analysis.get("match", False)
        confidence = analysis.get("confidence", 0.8)
        kitting_verified = analysis.get("kitting_verified", True)
        aesthetic_score = analysis.get("aesthetic_score", 1.0)
        
        # Determine action
        if not match:
            action_required = "STOP_LINE"
        elif not kitting_verified:
             action_required = "STOP_LINE_KITTING_FAIL"
        elif aesthetic_check and aesthetic_score < 0.9:
             action_required = "REJECT_QUALITY"
        elif confidence < 0.7:
            action_required = "RELABEL"  # Low confidence, needs review
        else:
            action_required = "PASS"
        
        print(f"  ✅ Label: '{label_text}' | Object: '{visual_object}' | Match: {match}")
        
        return LabelMatchResult(
            order_id=order_id,
            station_id=station_id,
            timestamp=datetime.now().isoformat(),
            label_text=label_text,
            visual_object=visual_object,
            match=match,
            kitting_verified=kitting_verified,
            aesthetic_score=aesthetic_score,
            confidence=confidence,
            action_required=action_required,
            reasoning=analysis.get("reasoning", "Verification completed")
        )
        
    except Exception as e:
        print(f"❌ Label verification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

# ============================================================================
# ENDPOINT 3: WMS CHECK (GACWare Specialist)
# ============================================================================

@app.post("/wms/check", response_model=WMSResult, operation_id="checkWMS")
async def check_wms(request: WMSCheckRequest):
    """
    Agent 3: GACWare Specialist (WMS Librarian)
    Checks order details in warehouse management system
    """
    print(f"📋 GACWare: Checking order {request.order_id}")
    
    # Mock WMS database
    mock_orders = {
        "ORDER-999": {
            "sku": "SKU-123",
            "expected_item": "Blue Shirt - Size M",
            "quantity": 1,
            "status": "IN_PROGRESS"
        },
        "ORDER-888": {
            "sku": "SKU-456",
            "expected_item": "Red Shirt - Size L",
            "quantity": 2,
            "status": "PENDING"
        }
    }
    
    # Check if order exists
    if request.order_id in mock_orders:
        order_data = mock_orders[request.order_id]
        status = "FOUND"
        predicted_cause = None
        optimization_suggestion = None
        
        # If SKU provided, verify it matches
        if request.sku and request.sku != order_data["sku"]:
            status = "MISMATCH"
            predicted_cause = "Possible Picking Error: Item often confused with SKU-999 (Green Shirt)."
            optimization_suggestion = "Suggestion: Move SKU-123 to Bin B-02 to separate from similar items."
    else:
        # Generate realistic mock data for unknown orders
        order_data = {
            "sku": request.sku or "SKU-UNKNOWN",
            "expected_item": f"Item for {request.order_id}",
            "quantity": 1,
            "status": "UNKNOWN"
        }
        status = "NOT_FOUND"
        predicted_cause = "Order not yet synced from ERP."
        optimization_suggestion = None
    
    return WMSResult(
        order_id=request.order_id,
        sku=order_data["sku"],
        expected_item=order_data["expected_item"],
        quantity=order_data["quantity"],
        status=status,
        predicted_cause=predicted_cause,
        optimization_suggestion=optimization_suggestion,
        wms_data=order_data
    )

# ============================================================================
# ENDPOINT 4: EXCEPTION HANDLING (Fulfillment Specialist)
# ============================================================================

@app.post("/ops/handle_exception", response_model=ExceptionResult, operation_id="handleException")
async def handle_exception(request: ExceptionRequest):
    """
    Agent 4: Fulfillment Specialist (Resolution Officer)
    Handles exceptions: holds orders, sends alerts, creates tickets
    """
    print(f"⚠️ Exception Handler: {request.exception_type} for {request.order_id}")
    
    ticket_id = f"TKT-{int(datetime.now().timestamp())}"
    vendor_email_draft = None
    carrier_rates = None
    
    # Determine action based on exception type
    if request.exception_type == "LABEL_MISMATCH":
        action_taken = f"Order {request.order_id} held at {request.station_id}. Alert sent to floor supervisor. Label mismatch detected."
        status = "HELD"
    elif request.exception_type == "BOX_DAMAGED":
        action_taken = f"Order {request.order_id} quarantined. Box damage detected. Requires repack."
        status = "QUARANTINED"
        # Automated Vendor Negotiation
        vendor_email_draft = f"""
        To: claims@{request.vendor_id}.com
        Subject: Damage Claim - Shipment {request.order_id}
        
        Attached is evidence of damage for Order {request.order_id}. 
        Damage detected upon arrival. Requesting immediate credit of $500.
        """
    else:
        action_taken = f"Exception logged for {request.order_id}. Manual review required."
        status = "ALERT_SENT"
        # Dynamic Carrier Selection for returns
        carrier_rates = {
            "FedEx": "$12.50 (2 days)",
            "UPS": "$14.00 (1 day)",
            "USPS": "$8.50 (4 days)"
        }
    
    return ExceptionResult(
        ticket_id=ticket_id,
        order_id=request.order_id,
        status=status,
        action_taken=action_taken,
        vendor_email_draft=vendor_email_draft,
        carrier_rates=carrier_rates,
        timestamp=datetime.now().isoformat()
    )

# ============================================================================
# BATCH PROCESSING
# ============================================================================

class BatchInspectionRequest(BaseModel):
    image_urls: List[str]

@app.post("/inspect/batch", operation_id="inspectBatch")
async def inspect_batch(request: BatchInspectionRequest):
    """
    Batch box inspection - Inspect multiple boxes at once.
    
    **Parameters**:
    - image_urls: Array of image URLs to inspect (can be single or multiple)
    
    **Returns**: Summary statistics and detailed results for each box.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    
    if not request.image_urls or len(request.image_urls) == 0:
        raise HTTPException(status_code=400, detail="image_urls array cannot be empty")
    
    image_urls = request.image_urls
    print(f"📦 [Batch Inspection] Processing {len(image_urls)} boxes")
    
    results = []
    for i, url in enumerate(image_urls):
        try:
            print(f"  → Inspecting box {i+1}/{len(image_urls)}: {url[:60]}...")
            
            # Create a mock request object for inspect_box
            class MockRequest:
                def __init__(self, image_url, shipment_id):
                    self.headers = {"content-type": "application/json"}
                    self._image_url = image_url
                    self._shipment_id = shipment_id
                async def json(self):
                    return {
                        "image_url": self._image_url,
                        "shipment_id": self._shipment_id,
                        "priority": "STANDARD"
                    }
            
            mock_req = MockRequest(url, f"BATCH-{i+1}")
            
            # Call inspect_box with the mock request
            result = await inspect_box(
                http_request=mock_req,
                file=None,
                image_url=url,
                shipment_id=f"BATCH-{i+1}",
                priority="STANDARD",
                temperature=None,
                dimensions_str=None
            )
            results.append(result)
        except Exception as e:
            print(f"  ⚠️ Failed to inspect box {i+1}: {str(e)}")
            import traceback
            traceback.print_exc()
            # Add error result
            error_result = BoxInspectionResult(
                shipment_id=f"BATCH-{i+1}",
                box_condition="CRITICAL",
                can_ship=False,
                total_defects=0,
                findings=[],
                reasoning=f"Inspection failed: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
            results.append(error_result)
            continue
    
    if not results:
        return {
            "total_boxes": 0,
            "good_boxes": 0,
            "damaged_boxes": 0,
            "can_ship_count": 0,
            "ship_rate": "0%",
            "results": []
        }
    
    good_count = sum(1 for r in results if hasattr(r, "box_condition") and r.box_condition == "GOOD")
    damaged_count = sum(1 for r in results if hasattr(r, "box_condition") and r.box_condition in ["DAMAGED", "CRITICAL"])
    can_ship_count = sum(1 for r in results if hasattr(r, "can_ship") and r.can_ship)
    
    # Convert results to dict format
    results_dict = []
    for r in results:
        if hasattr(r, "dict"):
            results_dict.append(r.dict())
        else:
            results_dict.append({
                "shipment_id": getattr(r, "shipment_id", "UNKNOWN"),
                "box_condition": getattr(r, "box_condition", "UNKNOWN"),
                "can_ship": getattr(r, "can_ship", False),
                "total_defects": getattr(r, "total_defects", 0),
                "findings": getattr(r, "findings", []),
                "reasoning": getattr(r, "reasoning", "No reasoning available"),
                "timestamp": getattr(r, "timestamp", datetime.now().isoformat())
            })
    
    return {
        "total_boxes": len(results),
        "good_boxes": good_count,
        "damaged_boxes": damaged_count,
        "can_ship_count": can_ship_count,
        "ship_rate": f"{(can_ship_count / len(results) * 100):.1f}%",
        "results": results_dict
    }

# ============================================================================
# ENDPOINT 6: WATSONX CHAT (Hub Director Communication)
# ============================================================================

class ChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None

class ChatResponse(BaseModel):
    response: str
    agent: str = "Hub Director"

@app.post("/chat", response_model=ChatResponse)
async def chat_with_watsonx(request: ChatRequest):
    """
    Chat with watsonx Orchestrate Hub Director agent
    """
    try:
        # Prepare the request to watsonx Orchestrate
        headers = {
            "Content-Type": "application/json",
            "x-watson-channel": "agentic_chat"
        }
        
        # Build context-aware message
        context_info = ""
        if request.context:
            if "box_condition" in request.context:
                context_info = f"\n\nContext: Last box inspection showed {request.context['box_condition']} condition."
            elif "match" in request.context:
                match_status = "MATCH" if request.context["match"] else "MISMATCH"
                context_info = f"\n\nContext: Last label verification showed {match_status}."
        
        full_message = request.message + context_info
        
        # watsonx Orchestrate runs endpoint (from browser network inspection)
        chat_endpoint = "https://au-syd.watson-orchestrate.cloud.ibm.com/mfe_home_archer/api/v1/orchestrate/runs"
        
        # Get IAM token from API key
        print(f"🔑 Getting IAM token...")
        iam_response = requests.post(
            "https://iam.cloud.ibm.com/identity/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={WATSONX_API_KEY}",
            timeout=10
        )
        
        if iam_response.status_code == 200:
            iam_token = iam_response.json().get("access_token")
            headers["Authorization"] = f"Bearer {iam_token}"
            print(f"✅ Got IAM token")
        else:
            print(f"❌ Failed to get IAM token: {iam_response.status_code}")
            return ChatResponse(
                response=f"Authentication failed. Could not get IAM token (status {iam_response.status_code}). Please check your API key.",
                agent="Hub Director (Auth Error)"
            )
        
        # Payload format for orchestrate/runs endpoint
        payload = {
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": full_message
                        }
                    ]
                }
            ]
        }
        
        print(f"🤖 Calling watsonx: {chat_endpoint}")
        response = requests.post(
            chat_endpoint,
            headers=headers,
            json=payload,
            timeout=30,
            stream=False  # Set to True if you want streaming
        )
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📨 Response: {str(data)[:200]}")
            
            # Extract response from watsonx format
            agent_response = (
                data.get("output", [{}])[0].get("content", [{}])[0].get("text") or
                data.get("response") or
                str(data)
            )
            
            return ChatResponse(
                response=agent_response,
                agent="Hub Director"
            )
        else:
            error_detail = response.text[:300] if response.text else f"Status {response.status_code}"
            print(f"❌ watsonx error: {error_detail}")
            return ChatResponse(
                response=f"watsonx API error (status {response.status_code}): {error_detail}",
                agent="Hub Director (Error)"
            )
            
    except Exception as e:
        print(f"❌ watsonx chat error: {str(e)}")
        # Intelligent local fallback
        response_text = generate_intelligent_response(request.message, request.context)
        return ChatResponse(
            response=response_text,
            agent="Hub Director (Local Mode)"
        )

def generate_intelligent_response(message: str, context: dict = None):
    """Generate intelligent responses based on message and context"""
    msg_lower = message.lower()
    
    # Context-aware responses
    if context:
        if "box_condition" in context:
            condition = context["box_condition"]
            can_ship = context.get("can_ship", False)
            
            if "status" in msg_lower or "what" in msg_lower:
                return f"Based on the last inspection, the box condition is **{condition}**. Can ship: {'✓ YES' if can_ship else '✗ NO'}. {context.get('reasoning', '')}"
            
            if "ship" in msg_lower:
                if can_ship:
                    return f"Yes, this shipment can proceed. The box is in {condition} condition with {context.get('total_defects', 0)} defects found."
                else:
                    return f"No, I recommend holding this shipment. The box is {condition} with critical issues. Action required: {context.get('findings', [{}])[0].get('recommended_action', 'Review manually')}"
        
        elif "match" in context:
            match_status = "MATCH ✓" if context["match"] else "MISMATCH ✗"
            return f"Label verification shows: {match_status}. Label text: '{context.get('label_text', 'N/A')}' vs Visual object: '{context.get('visual_object', 'N/A')}'. {context.get('reasoning', '')}"
    
    # General help
    if "help" in msg_lower:
        return """I'm the Hub Director. I can help you with:
• **Box Inspection**: Upload an image to check for damage
• **Label Verification**: Verify shipping labels match items
• **Status Queries**: Ask about your last analysis
• **Recommendations**: Get action items based on findings

Just upload an image or ask me a question!"""
    
    # Greeting
    if any(word in msg_lower for word in ["hello", "hi", "hey"]):
        return "Hello! I'm the Hub Director. Upload a shipment image for analysis, or ask me about your last inspection."
    
    # Default intelligent response
    return f"I understand your query: '{message}'. Upload an image for analysis, or ask me about shipment status, defects, or recommendations. For full multi-agent collaboration, we're working on connecting to watsonx Orchestrate."

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "gemini_configured": GEMINI_API_KEY is not None,
        "watsonx_configured": bool(WATSONX_API_KEY and WATSONX_URL),
        "endpoints": [
            "/inspect/box - Box condition inspection",
            "/vas/verify_label - VAS label verification (PRD v6)",
            "/wms/check - WMS order check",
            "/ops/handle_exception - Exception handling",
            "/chat - Chat with watsonx Hub Director"
        ]
    }

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("📦 Supply Chain Logistics API")
    print("   Box Inspection + VAS Label Verification")
    print("="*60)
    print(f"✅ Server starting on http://0.0.0.0:8000")
    print(f"📖 API docs: http://localhost:8000/docs")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)



