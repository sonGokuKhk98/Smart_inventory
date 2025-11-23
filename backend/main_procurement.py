"""
VisionFlow Procurement Automation Backend
End-to-End Procure-to-Pay Automation with Multi-Agent Orchestration
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import google.generativeai as genai
from PIL import Image
import requests
from io import BytesIO
import os
from dotenv import load_dotenv
from pathlib import Path
import json
from datetime import datetime
import time
import random
import re

# Load .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

app = FastAPI(
    title="VisionFlow Procurement Automation API",
    description="Multi-Agent System for End-to-End Procure-to-Pay Automation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel("models/gemini-2.5-flash")
    print("✅ Gemini initialized for procurement automation")
else:
    gemini_model = None
    print("⚠️ Gemini not configured")

# Helper Functions
def retry_with_backoff(func, max_retries=3, initial_delay=2):
    """Retry Gemini calls with exponential backoff"""
    retries = 0
    while retries < max_retries:
        try:
            return func()
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                wait_time = initial_delay * (2 ** retries) + random.uniform(0, 1)
                time.sleep(wait_time)
                retries += 1
            else:
                raise e
    raise Exception(f"Failed after {max_retries} retries")

def extract_json_from_text(text: str):
    """Extract JSON from Gemini response"""
    try:
        return json.loads(text)
    except:
        if "```json" in text:
            json_str = text.split("```json")[1].split("```")[0].strip()
            return json.loads(json_str)
        elif "```" in text:
            json_str = text.split("```")[1].split("```")[0].strip()
            try:
                return json.loads(json_str)
            except:
                pass
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
        raise ValueError("No valid JSON found")

# ============================================================================
# Agent 2: Document Intelligence Specialist
# ============================================================================

class DocumentExtractionRequest(BaseModel):
    document_url: str
    document_type: str  # "invoice", "po", "requisition", "receipt"

class DocumentExtractionResult(BaseModel):
    document_type: str
    extracted_data: Dict
    confidence: float
    timestamp: str

@app.post("/procurement/extract_document", response_model=DocumentExtractionResult, operation_id="extractDocument")
async def extract_document(request: DocumentExtractionRequest):
    """
    AGENT 2: Document Intelligence Specialist
    
    Extracts structured data from procurement documents using OCR + Vision.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    
    try:
        print(f"📄 Document Intelligence: Extracting {request.document_type}...")
        
        # Handle local file:// URLs (from Kaggle dataset) or HTTP URLs
        if request.document_url.startswith("file://"):
            # Local file path
            file_path = request.document_url.replace("file://", "")
            img_pil = Image.open(file_path)
            print(f"   📁 Using local file: {file_path}")
        else:
            # HTTP URL - download image
            img_resp = requests.get(request.document_url, timeout=10)
            img_resp.raise_for_status()
            img_pil = Image.open(BytesIO(img_resp.content))
            print(f"   🌐 Downloaded from URL: {request.document_url[:60]}...")
        
        # Create type-specific prompts
        prompts = {
            "invoice": """You are a Document Intelligence Specialist extracting data from an INVOICE.
            
Extract the following fields:
- invoice_number: Invoice number/ID
- vendor_name: Company name issuing the invoice
- invoice_date: Date of invoice
- due_date: Payment due date
- total_amount: Total amount due (numeric)
- line_items: Array of items with description, quantity, unit_price, line_total
- tax_amount: Tax amount if shown
- subtotal: Subtotal before tax

Return ONLY valid JSON:
{
    "invoice_number": "INV-12345",
    "vendor_name": "Office Supplies Co",
    "invoice_date": "2025-01-15",
    "due_date": "2025-02-15",
    "total_amount": 1250.00,
    "subtotal": 1150.00,
    "tax_amount": 100.00,
    "line_items": [
        {"description": "Office Chairs", "quantity": 5, "unit_price": 200.00, "line_total": 1000.00},
        {"description": "Desk Lamps", "quantity": 3, "unit_price": 50.00, "line_total": 150.00}
    ]
}""",
            "po": """You are extracting data from a PURCHASE ORDER.
            
Extract:
- po_number: Purchase order number
- vendor_name: Supplier name
- po_date: Date of PO
- requested_by: Person/department requesting
- line_items: Items with description, quantity, unit_price, line_total
- total_amount: Total PO amount

Return ONLY valid JSON:
{
    "po_number": "PO-2025-001",
    "vendor_name": "Office Supplies Co",
    "po_date": "2025-01-10",
    "requested_by": "IT Department",
    "total_amount": 1250.00,
    "line_items": [
        {"description": "Office Chairs", "quantity": 5, "unit_price": 200.00, "line_total": 1000.00},
        {"description": "Desk Lamps", "quantity": 3, "unit_price": 50.00, "line_total": 150.00}
    ]
}""",
            "requisition": """You are extracting data from a PURCHASE REQUISITION.
            
Extract:
- requisition_number: Req number/ID
- requested_by: Employee/department
- request_date: Date of request
- department: Department code
- cost_center: Cost center if shown
- line_items: Items with description, quantity, estimated_price
- total_estimated_cost: Total estimated amount
- justification: Reason for purchase if shown

Return ONLY valid JSON:
{
    "requisition_number": "REQ-2025-001",
    "requested_by": "John Smith",
    "request_date": "2025-01-08",
    "department": "IT",
    "cost_center": "CC-IT-001",
    "total_estimated_cost": 1250.00,
    "justification": "Office furniture for new hires",
    "line_items": [
        {"description": "Office Chairs", "quantity": 5, "estimated_price": 200.00},
        {"description": "Desk Lamps", "quantity": 3, "estimated_price": 50.00}
    ]
}""",
            "receipt": """You are extracting data from a RECEIVING RECEIPT or GOODS RECEIPT.
            
Extract:
- receipt_number: Receipt/GR number
- po_number: Related PO number if shown
- received_date: Date goods received
- vendor_name: Supplier name
- received_items: Items received with quantity
- condition: Condition of goods (good, damaged, etc.)

Return ONLY valid JSON:
{
    "receipt_number": "GR-2025-001",
    "po_number": "PO-2025-001",
    "received_date": "2025-01-20",
    "vendor_name": "Office Supplies Co",
    "condition": "good",
    "received_items": [
        {"description": "Office Chairs", "quantity": 5},
        {"description": "Desk Lamps", "quantity": 3}
    ]
}"""
        }
        
        prompt = prompts.get(request.document_type, prompts["invoice"])
        
        response = retry_with_backoff(lambda: gemini_model.generate_content([prompt, img_pil]))
        result_text = response.text.strip()
        
        extracted_data = extract_json_from_text(result_text)
        
        return DocumentExtractionResult(
            document_type=request.document_type,
            extracted_data=extracted_data,
            confidence=0.95,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        print(f"❌ Document Extraction Failed: {e}")
        raise HTTPException(status_code=500, detail=f"Document extraction failed: {str(e)}")

# ============================================================================
# Agent 3: Budget & Compliance Specialist
# ============================================================================

class BudgetCheckRequest(BaseModel):
    department: str
    amount: float
    cost_center: Optional[str] = None

class BudgetCheckResult(BaseModel):
    budget_available: bool
    available_budget: float
    approval_required: bool
    approval_chain: List[str]
    compliance_status: str
    timestamp: str

@app.post("/procurement/check_budget", response_model=BudgetCheckResult, operation_id="checkBudget")
async def check_budget(request: BudgetCheckRequest):
    """
    AGENT 3: Budget & Compliance Specialist
    
    Validates budget availability and determines approval requirements.
    """
    print(f"💰 Budget Specialist: Checking budget for {request.department}...")
    
    # Mock budget database
    mock_budgets = {
        "IT": {"total": 50000.0, "spent": 35000.0, "available": 15000.0},
        "HR": {"total": 30000.0, "spent": 12000.0, "available": 18000.0},
        "Finance": {"total": 25000.0, "spent": 20000.0, "available": 5000.0},
        "Operations": {"total": 100000.0, "spent": 75000.0, "available": 25000.0}
    }
    
    dept_budget = mock_budgets.get(request.department, {"total": 0.0, "spent": 0.0, "available": 0.0})
    available = dept_budget["available"]
    
    budget_available = available >= request.amount
    
    # Determine approval chain based on amount
    approval_required = request.amount > 1000.0
    approval_chain = []
    
    if approval_required:
        if request.amount <= 5000.0:
            approval_chain = [f"{request.department} Manager"]
        elif request.amount <= 20000.0:
            approval_chain = [f"{request.department} Manager", "VP Finance"]
        else:
            approval_chain = [f"{request.department} Manager", "VP Finance", "CFO"]
    
    compliance_status = "COMPLIANT" if budget_available else "BUDGET_EXCEEDED"
    
    return BudgetCheckResult(
        budget_available=budget_available,
        available_budget=available,
        approval_required=approval_required,
        approval_chain=approval_chain,
        compliance_status=compliance_status,
        timestamp=datetime.now().isoformat()
    )

# ============================================================================
# Agent 4: Purchase Order Specialist
# ============================================================================

class CreatePORequest(BaseModel):
    requisition_data: Dict
    vendor_name: str
    department: str

class POResult(BaseModel):
    po_number: str
    status: str
    vendor_name: str
    total_amount: float
    created_date: str
    timestamp: str

@app.post("/procurement/create_po", response_model=POResult, operation_id="createPO")
async def create_purchase_order(request: CreatePORequest):
    """
    AGENT 4: Purchase Order Specialist
    
    Creates purchase order from requisition data.
    """
    print(f"📋 PO Specialist: Creating PO for {request.vendor_name}...")
    
    # Generate PO number
    po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    
    # Extract total from requisition, handle None/null values
    total_amount = request.requisition_data.get("total_estimated_cost", 0.0)
    if total_amount is None or total_amount == 'null':
        total_amount = 0.0
    try:
        total_amount = float(total_amount)
    except (TypeError, ValueError):
        total_amount = 0.0
    
    return POResult(
        po_number=po_number,
        status="CREATED",
        vendor_name=request.vendor_name,
        total_amount=total_amount,
        created_date=datetime.now().strftime("%Y-%m-%d"),
        timestamp=datetime.now().isoformat()
    )

class MatchInvoiceRequest(BaseModel):
    invoice_data: Dict
    po_number: str
    receipt_data: Optional[Dict] = None

class MatchInvoiceResult(BaseModel):
    match_status: str  # "MATCHED", "PARTIAL_MATCH", "MISMATCH"
    po_number: str
    invoice_number: str
    discrepancies: List[str]
    match_confidence: float
    timestamp: str

@app.post("/procurement/match_invoice", response_model=MatchInvoiceResult, operation_id="matchInvoice")
async def match_invoice_to_po(request: MatchInvoiceRequest):
    """
    AGENT 4: Purchase Order Specialist (Invoice Matching)
    
    Performs 3-way match: PO, Receiving, Invoice
    """
    try:
        print(f"🔍 PO Specialist: Matching invoice to PO {request.po_number}...")
        
        # Mock PO data (in real system, would query database)
        mock_pos = {
            "PO-20250110-1234": {
                "total_amount": 1250.00,
                "line_items": [
                    {"description": "Office Chairs", "quantity": 5, "unit_price": 200.00},
                    {"description": "Desk Lamps", "quantity": 3, "unit_price": 50.00}
                ]
            }
        }
        
        po_data = mock_pos.get(request.po_number, {})
        
        # Extract invoice total first
        invoice_total = request.invoice_data.get("total_amount", 0.0)
        if invoice_total is None or invoice_total == 'null':
            invoice_total = 0.0
        try:
            invoice_total = float(invoice_total)
        except (TypeError, ValueError):
            invoice_total = 0.0
        
        # If PO not found in mock data, use invoice amount as fallback (for testing)
        if not po_data:
            # Use invoice amount as PO amount (assumes they match for testing)
            po_total = invoice_total if invoice_total > 0 else 1000.0
            po_data = {"total_amount": po_total, "line_items": []}
        else:
            po_total = po_data.get("total_amount", 0.0)
            try:
                po_total = float(po_total)
            except (TypeError, ValueError):
                po_total = invoice_total if invoice_total > 0 else 1000.0
        
        discrepancies = []
        match_status = "MATCHED"
        match_confidence = 1.0
        
        # Check amount match
        if abs(po_total - invoice_total) > 0.01:
            discrepancies.append(f"Amount mismatch: PO=${po_total:.2f}, Invoice=${invoice_total:.2f}")
            match_status = "MISMATCH"
            match_confidence = 0.3
        
        # Check line items if available
        invoice_line_items = request.invoice_data.get("line_items", [])
        po_line_items = po_data.get("line_items", [])
        
        if invoice_line_items and po_line_items:
            try:
                po_items = {item.get("description", ""): item for item in po_line_items if item.get("description")}
                inv_items = {item.get("description", ""): item for item in invoice_line_items if item.get("description")}
                
                for desc, inv_item in inv_items.items():
                    if desc and desc not in po_items:
                        discrepancies.append(f"Item '{desc}' in invoice but not in PO")
                        match_status = "PARTIAL_MATCH"
                        match_confidence = 0.6
                    elif desc:
                        po_item = po_items[desc]
                        if inv_item.get("quantity") != po_item.get("quantity"):
                            discrepancies.append(f"Quantity mismatch for '{desc}': PO={po_item.get('quantity')}, Invoice={inv_item.get('quantity')}")
                            match_status = "PARTIAL_MATCH"
                            match_confidence = 0.7
            except Exception as e:
                print(f"⚠️ Error checking line items: {e}")
                # Continue with amount-only matching
        
        # Check receiving if provided (3-way match)
        if request.receipt_data:
            try:
                receipt_items = {item.get("description", ""): item.get("quantity", 0) 
                               for item in request.receipt_data.get("received_items", []) 
                               if item.get("description")}
                if invoice_line_items:
                    for item in invoice_line_items:
                        desc = item.get("description", "")
                        if desc and desc not in receipt_items:
                            discrepancies.append(f"Item '{desc}' in invoice but not received")
                            match_status = "PARTIAL_MATCH"
                            match_confidence = 0.5
            except Exception as e:
                print(f"⚠️ Error checking receipt: {e}")
                # Continue without receipt matching
        
        invoice_number = request.invoice_data.get("invoice_number", "UNKNOWN")
        if not invoice_number or invoice_number == 'null':
            invoice_number = "UNKNOWN"
        
        return MatchInvoiceResult(
            match_status=match_status,
            po_number=request.po_number,
            invoice_number=invoice_number,
            discrepancies=discrepancies,
            match_confidence=match_confidence,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        print(f"❌ Invoice Matching Failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Invoice matching failed: {str(e)}")

# ============================================================================
# Agent 5: Payment Processing Specialist
# ============================================================================

class ApprovePaymentRequest(BaseModel):
    invoice_id: str
    invoice_data: Dict
    match_result: Dict
    approval_status: str  # "APPROVED", "REJECTED", "HOLD"

class PaymentResult(BaseModel):
    payment_id: str
    invoice_id: str
    status: str
    payment_amount: float
    payment_date: Optional[str]
    duplicate_detected: bool
    exception_reason: Optional[str]
    timestamp: str

@app.post("/procurement/approve_payment", response_model=PaymentResult, operation_id="approvePayment")
async def approve_payment(request: ApprovePaymentRequest):
    """
    AGENT 5: Payment Processing Specialist
    
    Handles invoice approval and payment processing.
    """
    print(f"💳 Payment Specialist: Processing payment for invoice {request.invoice_id}...")
    
    # Check for duplicate invoices (mock check)
    processed_invoices = ["INV-12345", "INV-67890"]  # In real system, query database
    invoice_number = request.invoice_data.get("invoice_number", "")
    duplicate_detected = invoice_number in processed_invoices
    
    payment_id = f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"
    payment_amount = request.invoice_data.get("total_amount", 0.0)
    
    status = "APPROVED"
    payment_date = None
    exception_reason = None
    
    if duplicate_detected:
        status = "REJECTED"
        exception_reason = "Duplicate invoice detected"
    elif request.approval_status == "HOLD":
        status = "ON_HOLD"
        exception_reason = request.match_result.get("discrepancies", ["Manual review required"])
    elif request.approval_status == "REJECTED":
        status = "REJECTED"
        exception_reason = "Manually rejected"
    else:
        # Auto-approve if matched and not duplicate
        if request.match_result.get("match_status") == "MATCHED" and not duplicate_detected:
            status = "APPROVED"
            payment_date = datetime.now().strftime("%Y-%m-%d")
        else:
            status = "ON_HOLD"
            exception_reason = "Mismatch detected - requires review"
    
    return PaymentResult(
        payment_id=payment_id,
        invoice_id=request.invoice_id,
        status=status,
        payment_amount=payment_amount,
        payment_date=payment_date,
        duplicate_detected=duplicate_detected,
        exception_reason=exception_reason,
        timestamp=datetime.now().isoformat()
    )

# ============================================================================
# Agent 6: Inventory Management Specialist
# ============================================================================

class StockLevelRequest(BaseModel):
    sku: str
    warehouse_id: Optional[str] = None

class StockLevelResult(BaseModel):
    sku: str
    current_stock: int
    reorder_point: int
    max_stock: int
    status: str  # "IN_STOCK", "LOW_STOCK", "OUT_OF_STOCK", "OVERSTOCKED"
    recommendations: List[str]
    timestamp: str

@app.post("/inventory/check_stock", response_model=StockLevelResult, operation_id="checkStock")
async def check_stock_level(request: StockLevelRequest):
    """
    AGENT 6: Inventory Management Specialist
    
    Monitors stock levels and provides recommendations.
    """
    print(f"📦 Inventory Specialist: Checking stock for SKU {request.sku}...")
    
    # Mock inventory database
    mock_inventory = {
        "OFFICE-CHAIR-001": {"current": 45, "reorder_point": 20, "max": 100},
        "DESK-LAMP-002": {"current": 8, "reorder_point": 15, "max": 50},
        "MONITOR-003": {"current": 0, "reorder_point": 10, "max": 30},
        "KEYBOARD-004": {"current": 150, "reorder_point": 25, "max": 100}
    }
    
    sku_data = mock_inventory.get(request.sku, {"current": 0, "reorder_point": 10, "max": 50})
    current = sku_data["current"]
    reorder_point = sku_data["reorder_point"]
    max_stock = sku_data["max"]
    
    # Determine status
    if current == 0:
        status = "OUT_OF_STOCK"
        recommendations = ["URGENT: Reorder immediately", "Check alternative suppliers"]
    elif current < reorder_point:
        status = "LOW_STOCK"
        recommendations = [f"Reorder {reorder_point * 2 - current} units", "Monitor daily"]
    elif current > max_stock * 0.9:
        status = "OVERSTOCKED"
        recommendations = ["Consider reducing order quantity", "Check for slow-moving inventory"]
    else:
        status = "IN_STOCK"
        recommendations = ["Stock level healthy", "Continue monitoring"]
    
    return StockLevelResult(
        sku=request.sku,
        current_stock=current,
        reorder_point=reorder_point,
        max_stock=max_stock,
        status=status,
        recommendations=recommendations,
        timestamp=datetime.now().isoformat()
    )

class ReallocateRequest(BaseModel):
    from_warehouse: str
    to_warehouse: str
    sku: str
    quantity: int
    reason: Optional[str] = None

class ReallocateResult(BaseModel):
    reallocation_id: str
    from_warehouse: str
    to_warehouse: str
    sku: str
    quantity: int
    status: str
    estimated_cost: float
    timestamp: str

@app.post("/inventory/reallocate", response_model=ReallocateResult, operation_id="reallocateStock")
async def reallocate_stock(request: ReallocateRequest):
    """
    AGENT 6: Inventory Management Specialist
    
    Reallocates inventory between warehouses to optimize stock levels.
    """
    print(f"🔄 Inventory Specialist: Reallocating {request.quantity} units of {request.sku}...")
    print(f"   From: {request.from_warehouse} → To: {request.to_warehouse}")
    
    # Calculate estimated cost (mock calculation)
    base_cost_per_unit = 5.0  # Mock shipping/handling cost
    estimated_cost = request.quantity * base_cost_per_unit
    
    reallocation_id = f"REALLOC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"
    
    return ReallocateResult(
        reallocation_id=reallocation_id,
        from_warehouse=request.from_warehouse,
        to_warehouse=request.to_warehouse,
        sku=request.sku,
        quantity=request.quantity,
        status="SCHEDULED",
        estimated_cost=estimated_cost,
        timestamp=datetime.now().isoformat()
    )

class AdjustInventoryRequest(BaseModel):
    sku: str
    warehouse_id: str
    adjustment_type: str  # "RECEIVED", "SOLD", "DAMAGED", "RETURNED", "ADJUSTED"
    quantity: int
    reason: Optional[str] = None

class AdjustInventoryResult(BaseModel):
    adjustment_id: str
    sku: str
    warehouse_id: str
    adjustment_type: str
    quantity: int
    previous_stock: int
    new_stock: int
    status: str
    timestamp: str

@app.post("/inventory/adjust", response_model=AdjustInventoryResult, operation_id="adjustInventory")
async def adjust_inventory(request: AdjustInventoryRequest):
    """
    AGENT 6: Inventory Management Specialist
    
    Streamlines inventory adjustments (received, sold, damaged, returned).
    """
    print(f"📊 Inventory Specialist: Adjusting inventory for {request.sku}...")
    print(f"   Type: {request.adjustment_type}, Quantity: {request.quantity}")
    
    # Mock current stock lookup
    mock_inventory = {
        "OFFICE-CHAIR-001": 45,
        "DESK-LAMP-002": 8,
        "MONITOR-003": 0,
        "KEYBOARD-004": 150
    }
    previous_stock = mock_inventory.get(request.sku, 0)
    
    # Calculate new stock based on adjustment type
    if request.adjustment_type in ["RECEIVED", "RETURNED"]:
        new_stock = previous_stock + request.quantity
    elif request.adjustment_type in ["SOLD", "DAMAGED"]:
        new_stock = previous_stock - request.quantity
    else:  # ADJUSTED
        new_stock = request.quantity  # Direct set
    
    adjustment_id = f"ADJ-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"
    
    return AdjustInventoryResult(
        adjustment_id=adjustment_id,
        sku=request.sku,
        warehouse_id=request.warehouse_id,
        adjustment_type=request.adjustment_type,
        quantity=request.quantity,
        previous_stock=previous_stock,
        new_stock=new_stock,
        status="COMPLETED",
        timestamp=datetime.now().isoformat()
    )

class OptimizeInventoryRequest(BaseModel):
    warehouse_id: Optional[str] = None
    analyze_all: bool = True

class OptimizeInventoryResult(BaseModel):
    warehouse_id: str
    total_skus: int
    low_stock_items: int
    overstocked_items: int
    recommendations: List[Dict]
    estimated_savings: float
    timestamp: str

@app.post("/inventory/optimize", response_model=OptimizeInventoryResult, operation_id="optimizeInventory")
async def optimize_inventory(request: OptimizeInventoryRequest):
    """
    AGENT 6: Inventory Management Specialist
    
    Analyzes inventory across warehouses and provides optimization recommendations.
    Reduces carrying costs and ensures product availability.
    """
    print(f"🎯 Inventory Specialist: Optimizing inventory...")
    
    # Mock analysis
    warehouse_id = request.warehouse_id or "WAREHOUSE-001"
    
    recommendations = [
        {
            "sku": "DESK-LAMP-002",
            "issue": "LOW_STOCK",
            "action": "Reorder 22 units to reach optimal level",
            "priority": "HIGH"
        },
        {
            "sku": "MONITOR-003",
            "issue": "OUT_OF_STOCK",
            "action": "URGENT: Reorder 10 units immediately",
            "priority": "CRITICAL"
        },
        {
            "sku": "KEYBOARD-004",
            "issue": "OVERSTOCKED",
            "action": "Consider reducing future orders by 30%",
            "priority": "MEDIUM"
        }
    ]
    
    low_stock = sum(1 for r in recommendations if r["issue"] in ["LOW_STOCK", "OUT_OF_STOCK"])
    overstocked = sum(1 for r in recommendations if r["issue"] == "OVERSTOCKED")
    
    # Estimate savings (mock calculation)
    # Reducing overstock saves carrying costs
    estimated_savings = overstocked * 500.0  # $500 per overstocked item
    
    return OptimizeInventoryResult(
        warehouse_id=warehouse_id,
        total_skus=4,  # Mock
        low_stock_items=low_stock,
        overstocked_items=overstocked,
        recommendations=recommendations,
        estimated_savings=estimated_savings,
        timestamp=datetime.now().isoformat()
    )

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "procurement_automation",
        "gemini": GEMINI_API_KEY is not None,
        "version": "1.0.0",
        "features": ["procurement", "inventory_management"]
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 80)
    print("🎯 VisionFlow Procurement Automation Backend")
    print("=" * 80)
    print("📋 Available Endpoints:")
    print("\n📄 Procurement:")
    print("   POST /procurement/extract_document - Document Intelligence")
    print("   POST /procurement/check_budget - Budget & Compliance")
    print("   POST /procurement/create_po - Create Purchase Order")
    print("   POST /procurement/match_invoice - Match Invoice to PO")
    print("   POST /procurement/approve_payment - Payment Processing")
    print("\n📦 Inventory Management:")
    print("   POST /inventory/check_stock - Monitor Stock Levels")
    print("   POST /inventory/reallocate - Reallocate Resources")
    print("   POST /inventory/adjust - Streamline Adjustments")
    print("   POST /inventory/optimize - Optimize Inventory")
    print("=" * 80 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)

