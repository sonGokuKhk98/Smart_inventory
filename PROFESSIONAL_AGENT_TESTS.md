# 🧪 Professional Agent Test Scenarios

## Test Data
- **Image 1:** https://i.ibb.co/C3QgwbCy/Banner-Landscape-Design.png
- **Image 2:** https://i.ibb.co/S7XyKjPZ/1.png
- **SKU:** [Your SKU - to be provided]

---

## 📋 Test Execution Guide

### How to Use These Tests
1. Open watsonx Orchestrate Chat: https://au-syd.watson-orchestrate.cloud.ibm.com/chat
2. Copy and paste each test scenario below
3. Verify the agent responds correctly
4. Check that all expected outcomes occur

---

## 🎯 Agent 1: Inbound Gatekeeper (Box Inspection)

### Test 1.1: Single Box Inspection - Standard Priority
**Copy this into watsonx chat:**
```
Inspect this box for shipping: https://i.ibb.co/C3QgwbCy/Banner-Landscape-Design.png
Priority: STANDARD
Shipment ID: SHIP-TEST-001
```

**Expected Results:**
- ✅ Agent calls `inspect_box` tool
- ✅ Returns box condition (GOOD/DAMAGED/CRITICAL)
- ✅ Lists all defects found
- ✅ Provides shipping recommendation (can_ship: true/false)
- ✅ Includes reasoning for decision

**Validation Checklist:**
- [ ] Box condition is one of: GOOD, DAMAGED, CRITICAL
- [ ] Total defects count is provided
- [ ] Each defect has: type, severity, location, recommended action
- [ ] Shipping decision is clear (YES/NO)
- [ ] Reasoning explains the decision

---

### Test 1.2: Single Box Inspection - Critical Priority
**Copy this into watsonx chat:**
```
Inspect this box with CRITICAL priority: https://i.ibb.co/S7XyKjPZ/1.png
Shipment ID: SHIP-TEST-002
Temperature requirement: 2°C
Dimensions: 200x300
```

**Expected Results:**
- ✅ Agent processes with CRITICAL priority
- ✅ Temperature requirement is considered
- ✅ Dimensions are validated
- ✅ Faster processing (if implemented)

**Validation Checklist:**
- [ ] Priority is recognized as CRITICAL
- [ ] Temperature is included in analysis
- [ ] Dimensions are validated
- [ ] Response time is appropriate

---

### Test 1.3: Batch Box Inspection
**Copy this into watsonx chat:**
```
Perform batch box inspection on these images:
1. https://i.ibb.co/C3QgwbCy/Banner-Landscape-Design.png
2. https://i.ibb.co/S7XyKjPZ/1.png
```

**Expected Results:**
- ✅ Agent calls `inspect_batch` tool
- ✅ Processes both images
- ✅ Returns summary statistics:
  - Total boxes inspected
  - Good boxes count
  - Damaged boxes count
  - Ship rate percentage
- ✅ Provides detailed results for each box

**Validation Checklist:**
- [ ] Both boxes are processed
- [ ] Summary statistics are accurate
- [ ] Individual results are provided for each box
- [ ] Ship rate is calculated correctly

---

## 🏷️ Agent 2: QC Specialist (VAS Label Verification)

### Test 2.1: Label Verification - Match Expected
**Copy this into watsonx chat:**
```
Verify the VAS label on this package: https://i.ibb.co/C3QgwbCy/Banner-Landscape-Design.png
Expected SKU: [YOUR_SKU_HERE]
Order ID: ORD-TEST-001
Station: Station-1
```

**Expected Results:**
- ✅ Agent calls `verify_vas_label` tool
- ✅ Extracts label text using OCR
- ✅ Identifies visual object in image
- ✅ Compares label text vs visual object
- ✅ Returns match status (true/false)
- ✅ Provides action required (PASS/STOP_LINE/RELABEL)

**Validation Checklist:**
- [ ] Label text is extracted correctly
- [ ] Visual object is identified
- [ ] Match status is accurate
- [ ] Confidence score is provided
- [ ] Action required is appropriate
- [ ] Reasoning explains the decision

---

### Test 2.2: Label Verification - Mismatch Detection
**Copy this into watsonx chat:**
```
Check if the label matches the product in this image: https://i.ibb.co/S7XyKjPZ/1.png
Expected SKU: [YOUR_SKU_HERE]
Order ID: ORD-TEST-002
```

**Expected Results:**
- ✅ Detects mismatch if label doesn't match visual
- ✅ Flags for STOP_LINE or RELABEL
- ✅ Provides clear reasoning for mismatch

**Validation Checklist:**
- [ ] Mismatch is detected correctly
- [ ] Appropriate action is recommended
- [ ] Reasoning explains the mismatch

---

### Test 2.3: Label Verification with Kitting List
**Copy this into watsonx chat:**
```
Verify VAS label with kitting list: https://i.ibb.co/C3QgwbCy/Banner-Landscape-Design.png
Order ID: ORD-TEST-003
Kitting list: ["Item-A", "Item-B", "Item-C"]
Aesthetic check: true
```

**Expected Results:**
- ✅ Validates against kitting list
- ✅ Performs aesthetic check
- ✅ Returns kitting verification status
- ✅ Provides aesthetic score

**Validation Checklist:**
- [ ] Kitting list is validated
- [ ] Aesthetic check is performed
- [ ] Kitting verified status is provided
- [ ] Aesthetic score is included

---

## 📦 Agent 3: GACWare Specialist (WMS Check)

### Test 3.1: Order Lookup in WMS
**Copy this into watsonx chat:**
```
Check order ORD-TEST-001 in the warehouse management system
SKU: [YOUR_SKU_HERE]
```

**Expected Results:**
- ✅ Agent calls `check_wms` tool
- ✅ Looks up order in WMS
- ✅ Returns order details:
  - Expected item
  - Quantity
  - Status (FOUND/NOT_FOUND/MISMATCH)
- ✅ Provides WMS data

**Validation Checklist:**
- [ ] Order is found in WMS
- [ ] Expected item matches
- [ ] Quantity is correct
- [ ] Status is accurate
- [ ] WMS data is returned

---

### Test 3.2: WMS Check with SKU Validation
**Copy this into watsonx chat:**
```
Validate SKU [YOUR_SKU_HERE] for order ORD-TEST-002 in WMS
```

**Expected Results:**
- ✅ Validates SKU against order
- ✅ Checks if SKU matches expected item
- ✅ Identifies mismatches if any

**Validation Checklist:**
- [ ] SKU validation is performed
- [ ] Mismatches are detected
- [ ] Status reflects validation result

---

## ⚠️ Agent 4: Fulfillment Specialist (Exception Handling)

### Test 4.1: Handle Label Mismatch Exception
**Copy this into watsonx chat:**
```
Handle exception for order ORD-TEST-001
Exception type: LABEL_MISMATCH
Details: Label shows SKU-123 but product is SKU-456
Station: Station-1
```

**Expected Results:**
- ✅ Agent calls `handle_exception` tool
- ✅ Creates exception ticket
- ✅ Holds the order
- ✅ Sends alerts
- ✅ Returns ticket ID and status

**Validation Checklist:**
- [ ] Exception ticket is created
- [ ] Order is held (status: HELD)
- [ ] Ticket ID is generated
- [ ] Action taken is documented
- [ ] Timestamp is provided

---

### Test 4.2: Handle Box Damage Exception
**Copy this into watsonx chat:**
```
Handle exception for damaged box
Order ID: ORD-TEST-002
Exception type: BOX_DAMAGED
Details: Box has severe crushing and tears, cannot ship
Station: Station-2
```

**Expected Results:**
- ✅ Exception is logged
- ✅ Order is quarantined
- ✅ Alert is sent
- ✅ Replacement is flagged

**Validation Checklist:**
- [ ] Exception is handled correctly
- [ ] Order status is QUARANTINED
- [ ] Alert is sent
- [ ] Appropriate action is taken

---

### Test 4.3: Handle Missing Item Exception
**Copy this into watsonx chat:**
```
Handle missing item exception
Order ID: ORD-TEST-003
Exception type: MISSING_ITEM
Details: Expected 3 items but only 2 found in package
Station: Station-1
```

**Expected Results:**
- ✅ Missing item exception is created
- ✅ Order is held
- ✅ Inventory check is triggered
- ✅ Alert is sent to fulfillment team

**Validation Checklist:**
- [ ] Exception type is correct
- [ ] Order is held
- [ ] Alert is sent
- [ ] Action taken is appropriate

---

## 🔄 Multi-Agent Workflow Tests

### Test 5.1: Complete Inbound Workflow
**Copy this into watsonx chat:**
```
Process this inbound shipment:
1. Inspect box: https://i.ibb.co/C3QgwbCy/Banner-Landscape-Design.png
2. Verify VAS label with SKU: [YOUR_SKU_HERE]
3. Check order ORD-TEST-001 in WMS
4. If any issues, handle exception
```

**Expected Results:**
- ✅ All agents work together
- ✅ Box is inspected first
- ✅ Label is verified
- ✅ WMS is checked
- ✅ Exceptions are handled if needed
- ✅ Complete workflow report is provided

**Validation Checklist:**
- [ ] All agents are called in sequence
- [ ] Results from each agent are used by next
- [ ] Exceptions trigger appropriate handling
- [ ] Final report is comprehensive

---

### Test 5.2: Exception Escalation Workflow
**Copy this into watsonx chat:**
```
Process shipment with potential issues:
Box: https://i.ibb.co/S7XyKjPZ/1.png
Order: ORD-TEST-004
SKU: [YOUR_SKU_HERE]

If box is damaged OR label doesn't match, handle exception immediately.
```

**Expected Results:**
- ✅ Box inspection triggers exception if damaged
- ✅ Label verification triggers exception if mismatch
- ✅ Exception handling is automatic
- ✅ Workflow stops at first exception

**Validation Checklist:**
- [ ] Exceptions are detected automatically
- [ ] Exception handling is triggered
- [ ] Workflow stops appropriately
- [ ] Clear error messages are provided

---

## 📊 Batch Processing Tests

### Test 6.1: Batch Box Inspection
**Copy this into watsonx chat:**
```
Inspect these 2 boxes in batch:
1. https://i.ibb.co/C3QgwbCy/Banner-Landscape-Design.png
2. https://i.ibb.co/S7XyKjPZ/1.png

Provide summary statistics and individual results.
```

**Expected Results:**
- ✅ Both boxes are processed
- ✅ Summary shows:
  - Total boxes: 2
  - Good boxes count
  - Damaged boxes count
  - Ship rate percentage
- ✅ Individual results for each box

**Validation Checklist:**
- [ ] Both boxes are processed
- [ ] Summary statistics are accurate
- [ ] Individual results are detailed
- [ ] Ship rate is calculated correctly

---

## 🎯 Quick Test Commands (Copy-Paste Ready)

### Single Agent Tests
```
# Box Inspection
Inspect box: https://i.ibb.co/C3QgwbCy/Banner-Landscape-Design.png

# VAS Label Verification
Verify label: https://i.ibb.co/S7XyKjPZ/1.png with SKU [YOUR_SKU]

# WMS Check
Check order ORD-TEST-001 in WMS

# Exception Handling
Handle LABEL_MISMATCH exception for order ORD-TEST-001
```

### Multi-Agent Tests
```
# Complete Workflow
Inspect box https://i.ibb.co/C3QgwbCy/Banner-Landscape-Design.png, verify label with SKU [YOUR_SKU], check WMS for order ORD-TEST-001

# Batch Processing
Batch inspect: https://i.ibb.co/C3QgwbCy/Banner-Landscape-Design.png and https://i.ibb.co/S7XyKjPZ/1.png
```

---

## ✅ Test Results Template

Use this template to document your test results:

```
Test: [Test Name]
Date: [Date]
Agent: [Agent Name]
Status: ✅ PASS / ❌ FAIL

Results:
- [Result 1]
- [Result 2]
- [Result 3]

Issues Found:
- [Issue 1]
- [Issue 2]

Notes:
[Additional notes]
```

---

## 🔍 Validation Criteria

### For Each Agent Test:
1. **Correct Tool Called:** Agent uses the right tool/endpoint
2. **Parameters Passed:** All required parameters are provided
3. **Response Format:** Response matches expected schema
4. **Business Logic:** Decision-making logic is correct
5. **Error Handling:** Errors are handled gracefully
6. **Response Time:** Response is timely (< 5 seconds)

### For Multi-Agent Tests:
1. **Agent Coordination:** Agents work together correctly
2. **Data Flow:** Data passes correctly between agents
3. **Exception Handling:** Exceptions are caught and handled
4. **Workflow Completion:** Complete workflow executes successfully

---

## 📝 Notes

- Replace `[YOUR_SKU_HERE]` with your actual SKU value
- Replace `ORD-TEST-XXX` with actual order IDs if needed
- Adjust image URLs if you have different test images
- Document any deviations from expected results
- Note any performance issues or errors

---

**Last Updated:** 2024
**Version:** 1.0

