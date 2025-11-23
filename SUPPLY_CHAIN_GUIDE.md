# Supply Chain Logistics API - Complete Guide

## 📦 What This Does

**Combined Solution:**
1. ✅ **Box Inspection** - Inbound quality control (damage detection)
2. ✅ **VAS Label Verification** - PRD v6 workflow (label vs product matching)
3. ✅ **WMS Check** - Order validation
4. ✅ **Exception Handling** - Order holds and alerts

---

## 🎯 The 4-Agent Workflow (PRD v6)

### Agent 1: Inbound Gatekeeper
- **Endpoint:** `/inspect/box`
- **Role:** Inspects incoming boxes for damage
- **Checks:** Crushed, torn, water damage, structural issues

### Agent 2: QC Specialist (VAS Quality Controller)
- **Endpoint:** `/vas/verify_label`
- **Role:** Verifies label text matches physical product
- **PRD v6 Scenario:** Detects "Blue Shirt" label on "Red Shirt" package
- **Technology:** OCR (read label) + Visual AI (identify object)

### Agent 3: GACWare Specialist (WMS Librarian)
- **Endpoint:** `/wms/check`
- **Role:** Validates order details in warehouse system
- **Checks:** Order exists, SKU matches, quantity correct

### Agent 4: Fulfillment Specialist (Resolution Officer)
- **Endpoint:** `/ops/handle_exception`
- **Role:** Handles exceptions, holds orders, sends alerts
- **Actions:** Stop line, quarantine, alert supervisor

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install fastapi uvicorn pydantic requests google-generativeai Pillow python-dotenv
```

### 2. Set Up API Key
Create `.env` file:
```
GEMINI_API_KEY=your_key_here
```

### 3. Start Server
```bash
python3 backend/main_supply_chain.py
```

### 4. Test It
```bash
python3 test_supply_chain.py
```

---

## 📍 API Endpoints

### 1. Box Inspection
**POST** `/inspect/box`

**Request:**
```json
{
  "image_url": "https://example.com/box.jpg",
  "shipment_id": "SHIP-001",
  "expected_condition": "good"
}
```

**Response:**
```json
{
  "shipment_id": "SHIP-001",
  "box_condition": "GOOD",
  "can_ship": true,
  "total_defects": 0,
  "findings": [],
  "reasoning": "Box is in good condition"
}
```

---

### 2. VAS Label Verification (PRD v6)
**POST** `/vas/verify_label`

**Request:**
```json
{
  "image_url": "https://example.com/package.jpg",
  "order_id": "ORDER-999",
  "station_id": "Station-4",
  "expected_sku": "SKU-123"
}
```

**Response:**
```json
{
  "order_id": "ORDER-999",
  "label_text": "Blue Shirt - Size M",
  "visual_object": "Red Shirt visible in package",
  "match": false,
  "confidence": 0.95,
  "action_required": "STOP_LINE",
  "reasoning": "Label says Blue but package contains Red Shirt"
}
```

---

### 3. WMS Check
**POST** `/wms/check`

**Request:**
```json
{
  "order_id": "ORDER-999",
  "sku": "SKU-123"
}
```

**Response:**
```json
{
  "order_id": "ORDER-999",
  "sku": "SKU-123",
  "expected_item": "Blue Shirt - Size M",
  "quantity": 1,
  "status": "FOUND",
  "wms_data": {...}
}
```

---

### 4. Exception Handling
**POST** `/ops/handle_exception`

**Request:**
```json
{
  "order_id": "ORDER-999",
  "exception_type": "LABEL_MISMATCH",
  "details": "Label says Blue but package contains Red",
  "station_id": "Station-4"
}
```

**Response:**
```json
{
  "ticket_id": "TKT-1234567890",
  "order_id": "ORDER-999",
  "status": "HELD",
  "action_taken": "Order ORDER-999 held at Station-4. Alert sent to floor supervisor.",
  "timestamp": "2025-11-22T14:30:00"
}
```

---

## 🔄 Complete Workflow Example (PRD v6)

### Scenario: "The Mismatched Label"

1. **Package arrives at Station 4**
   - Image captured automatically

2. **VAS Supervisor activates**
   - Calls QC Specialist to verify label

3. **QC Specialist analyzes**
   - OCR reads: "Blue Shirt - Size M"
   - Visual AI sees: "Red Shirt"
   - Result: **MISMATCH DETECTED**

4. **Supervisor stops line**
   - Calls GACWare Specialist to check order

5. **GACWare Specialist confirms**
   - Order ORDER-999 requires: "Blue Shirt - Size M"
   - Status: MISMATCH confirmed

6. **Fulfillment Specialist handles**
   - Holds order
   - Creates ticket TKT-1234567890
   - Sends alert to floor supervisor

7. **Result:** Wrong item caught **before** shipping!

---

## 🖼️ Test Images

The test script includes:
- Good boxes (warehouse scenes)
- Damaged boxes (crushed, torn)
- Package images for label verification
- Various supply chain scenarios

---

## 🔗 Integration with watsonx Orchestrate

### Step 1: Expose with ngrok
```bash
ngrok http 8000
# Copy HTTPS URL
```

### Step 2: Create OpenAPI Spec
- Use `openapi_supply_chain.json` (create this from endpoints)
- Update with ngrok URL

### Step 3: Import to watsonx
1. Import OpenAPI as Digital Skills
2. Create 4 agents:
   - Inbound Gatekeeper (uses `/inspect/box`)
   - QC Specialist (uses `/vas/verify_label`)
   - GACWare Specialist (uses `/wms/check`)
   - Fulfillment Specialist (uses `/ops/handle_exception`)
3. Configure VAS Supervisor (Hub Director) to orchestrate

### Step 4: Configure Workflow
- Set up agent collaboration
- Define routing logic
- Test complete workflow

---

## 📊 What Gets Detected

### Box Conditions:
- ✅ **GOOD** - Safe to ship
- ⚠️ **DAMAGED** - Needs review/repack
- ❌ **CRITICAL** - Do not ship

### Label Verification:
- ✅ **MATCH** - Label and product match
- ❌ **MISMATCH** - Label doesn't match product (STOP_LINE)
- ⚠️ **LOW_CONFIDENCE** - Needs manual review

### Exception Types:
- `LABEL_MISMATCH` - Wrong label on package
- `BOX_DAMAGED` - Box condition issues
- `MISSING_ITEM` - Item not found

---

## 🎯 Use Cases

### Use Case 1: Inbound Receiving
- Photo of incoming shipment
- Check box condition
- Auto-quarantine damaged items

### Use Case 2: VAS Repacking Line (PRD v6)
- Photo of labeled package
- Verify label matches product
- Stop line if mismatch detected
- Prevent wrong item shipping

### Use Case 3: Quality Control
- Batch inspection
- Exception handling
- Automated alerts

---

## 🐛 Troubleshooting

### "GEMINI_API_KEY NOT FOUND"
- Check `.env` file exists
- Verify key is correct
- Restart server

### "Failed to download image"
- Check image URL is accessible
- Try different image
- Check internet connection

### "JSON parsing failed"
- Code has fallback handling
- Check server logs
- Gemini sometimes returns text before JSON

---

## ✅ Success Checklist

- [ ] Dependencies installed
- [ ] `.env` file with `GEMINI_API_KEY`
- [ ] Server starts without errors
- [ ] All 4 endpoints working
- [ ] Complete workflow tested
- [ ] Ready for watsonx integration

---

## 📚 Files

- `backend/main_supply_chain.py` - Main server
- `test_supply_chain.py` - Test script
- `SUPPLY_CHAIN_GUIDE.md` - This guide

---

**Ready to automate supply chain logistics!** 🚀

