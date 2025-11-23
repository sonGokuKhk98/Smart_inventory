# 🧪 Test Scenarios for VisionFlow Multi-Agent System

## Overview
This document provides comprehensive test scenarios for the VisionFlow Procurement Automation and Supply Chain Management system powered by IBM watsonx Orchestrate.

---

## 📋 Table of Contents
1. [Procurement Automation Scenarios](#procurement-automation-scenarios)
2. [Supply Chain Management Scenarios](#supply-chain-management-scenarios)
3. [Inventory Management Scenarios](#inventory-management-scenarios)
4. [Multi-Agent Workflow Scenarios](#multi-agent-workflow-scenarios)
5. [Edge Cases & Exception Handling](#edge-cases--exception-handling)

---

## 🛒 Procurement Automation Scenarios

### Scenario 1: Happy Path - Complete Procure-to-Pay Cycle
**Objective:** Test the complete automated workflow from requisition to payment

**Steps:**
1. **Submit Requisition**
   - "I need to order 10 office chairs for the IT department, budget is $2,000"
   - Expected: Document Intelligence extracts requisition data

2. **Budget Check**
   - Expected: Budget Specialist validates budget availability
   - Expected: Approval chain determined

3. **PO Creation**
   - Expected: PO Specialist creates purchase order automatically
   - Expected: PO number generated

4. **Goods Receipt**
   - "The office chairs have arrived. Here's the receiving slip: [image]"
   - Expected: Document Intelligence reads receiving slip

5. **Invoice Processing**
   - "Vendor sent invoice: [invoice image]"
   - Expected: Document Intelligence extracts invoice data

6. **3-Way Match**
   - Expected: PO Specialist matches PO, Receiving, Invoice
   - Expected: All match successfully

7. **Payment Approval**
   - Expected: Payment Specialist approves and processes payment
   - Expected: Payment record created

**Expected Result:** Complete cycle automated in <2 minutes (vs 5-7 days manual)

---

### Scenario 2: Budget Exceeded
**Objective:** Test budget validation and approval escalation

**Steps:**
1. "I need to order $50,000 worth of server equipment for IT department"
2. Expected: Budget Specialist flags budget exceeded
3. Expected: Approval chain escalated to CFO
4. Expected: System waits for approval before creating PO

**Expected Result:** Exception flagged, approval required

---

### Scenario 3: Invoice Amount Mismatch
**Objective:** Test exception handling for invoice discrepancies

**Steps:**
1. Create PO for $1,000
2. Receive invoice for $1,200
3. Expected: PO Specialist flags mismatch
4. Expected: Payment Specialist holds payment
5. Expected: Exception report generated

**Expected Result:** Payment blocked, exception flagged for review

---

### Scenario 4: Duplicate Invoice Detection
**Objective:** Test duplicate payment prevention

**Steps:**
1. Process invoice #INV-001 for $500
2. Try to process same invoice #INV-001 again
3. Expected: Payment Specialist detects duplicate
4. Expected: Payment blocked
5. Expected: Alert generated

**Expected Result:** Duplicate detected, payment prevented

---

### Scenario 5: Missing Receiving Slip
**Objective:** Test 3-way match with missing document

**Steps:**
1. Create PO
2. Receive invoice
3. No receiving slip provided
4. Expected: PO Specialist flags missing receiving slip
5. Expected: Payment held until receiving slip provided

**Expected Result:** Payment on hold, missing document flagged

---

### Scenario 6: Multi-Line Item Invoice
**Objective:** Test complex invoice with multiple line items

**Steps:**
1. "Process this invoice with 15 different line items: [invoice image]"
2. Expected: Document Intelligence extracts all line items
3. Expected: Each line item matched to PO
4. Expected: Partial matches flagged if any discrepancies

**Expected Result:** All line items processed and matched

---

### Scenario 7: Vendor Status Check
**Objective:** Test compliance with vendor approval

**Steps:**
1. "Create PO with vendor 'New Supplier Inc'"
2. Expected: Budget Specialist checks vendor status
3. Expected: If vendor not approved, flag for vendor onboarding
4. Expected: PO creation blocked until vendor approved

**Expected Result:** Vendor compliance validated

---

## 📦 Supply Chain Management Scenarios

### Scenario 8: Box Inspection - Good Condition
**Objective:** Test box inspection for shipping approval

**Steps:**
1. Upload box image: "Inspect this box for shipping: [image]"
2. Expected: System analyzes box condition
3. Expected: Defects identified (dents, tears, etc.)
4. Expected: Shipping decision made (can ship / cannot ship)

**Expected Result:** Box approved for shipping, defects documented

---

### Scenario 9: Box Inspection - Critical Defects
**Objective:** Test rejection of damaged boxes

**Steps:**
1. Upload image of severely damaged box
2. Expected: System identifies critical defects
3. Expected: Box marked as "cannot ship"
4. Expected: Reason provided (e.g., "Multiple tears, structural damage")

**Expected Result:** Box rejected, replacement required

---

### Scenario 10: VAS Label Verification - Match
**Objective:** Test VAS label matching

**Steps:**
1. Upload image with VAS label: "Verify this VAS label: [image]"
2. Expected: System extracts label text and visual object
3. Expected: Compares with order requirements
4. Expected: Match confirmed

**Expected Result:** Label verified, match confirmed

---

### Scenario 11: VAS Label Verification - Mismatch
**Objective:** Test VAS label mismatch detection

**Steps:**
1. Upload image with incorrect VAS label
2. Expected: System detects mismatch
3. Expected: Action required flagged
4. Expected: Correct label specified

**Expected Result:** Mismatch detected, correction required

---

### Scenario 12: Batch Box Inspection
**Objective:** Test processing multiple boxes

**Steps:**
1. "Inspect these 20 boxes: [multiple images]"
2. Expected: System processes each box
3. Expected: Summary report generated
4. Expected: Shipping decisions for each box

**Expected Result:** All boxes processed, batch report generated

---

## 📊 Inventory Management Scenarios

### Scenario 13: Stock Level Check
**Objective:** Test inventory monitoring

**Steps:**
1. "Check stock levels for SKU-12345"
2. Expected: System checks current stock
3. Expected: Reorder point checked
4. Expected: Recommendations provided

**Expected Result:** Stock level reported, reorder suggested if low

---

### Scenario 14: Inventory Reallocation
**Objective:** Test resource reallocation

**Steps:**
1. "Reallocate 50 units of SKU-12345 from Warehouse A to Warehouse B"
2. Expected: System validates availability
3. Expected: Reallocation plan created
4. Expected: Confirmation provided

**Expected Result:** Reallocation executed, inventory updated

---

### Scenario 15: Inventory Optimization
**Objective:** Test inventory optimization recommendations

**Steps:**
1. "Optimize inventory for Warehouse A"
2. Expected: System analyzes stock levels
3. Expected: Identifies overstock/understock items
4. Expected: Recommendations provided

**Expected Result:** Optimization recommendations generated

---

## 🔄 Multi-Agent Workflow Scenarios

### Scenario 16: End-to-End Procurement with Inventory Check
**Objective:** Test integrated workflow across multiple agents

**Steps:**
1. "I need 50 laptops for the sales team"
2. Expected: Procurement Supervisor orchestrates workflow
3. Expected: Document Intelligence extracts requisition
4. Expected: Budget Specialist checks budget
5. Expected: Inventory Specialist checks if items in stock
6. Expected: If in stock, suggest internal transfer
7. Expected: If not in stock, create PO
8. Expected: Complete workflow automated

**Expected Result:** Multi-agent collaboration, optimal path chosen

---

### Scenario 17: Exception Escalation
**Objective:** Test exception handling across agents

**Steps:**
1. Process invoice with multiple issues:
   - Amount mismatch
   - Missing receiving slip
   - Vendor not approved
2. Expected: Each agent flags their issue
3. Expected: Procurement Supervisor coordinates resolution
4. Expected: Exception report with all issues

**Expected Result:** All exceptions captured, coordinated resolution

---

### Scenario 18: Batch Processing
**Objective:** Test processing multiple invoices simultaneously

**Steps:**
1. "Process these 10 invoices: [multiple invoice images]"
2. Expected: Document Intelligence processes all invoices
3. Expected: Each invoice matched to PO
4. Expected: Batch approval report generated
5. Expected: Exceptions highlighted

**Expected Result:** All invoices processed, batch report with exceptions

---

## ⚠️ Edge Cases & Exception Handling

### Scenario 19: Unreadable Document
**Objective:** Test handling of poor quality images

**Steps:**
1. Upload blurry/low-quality invoice image
2. Expected: Document Intelligence attempts extraction
3. Expected: If extraction fails, flag for manual review
4. Expected: Clear error message provided

**Expected Result:** Graceful failure, manual review flagged

---

### Scenario 20: Invalid Document Type
**Objective:** Test handling of unsupported documents

**Steps:**
1. Upload non-procurement document (e.g., contract)
2. Expected: Document Intelligence identifies document type
3. Expected: If unsupported, error message provided
4. Expected: Suggestion to use correct document type

**Expected Result:** Clear error, guidance provided

---

### Scenario 21: Network/API Failure
**Objective:** Test resilience to external service failures

**Steps:**
1. Simulate Gemini API failure
2. Expected: System handles error gracefully
3. Expected: Retry mechanism activated
4. Expected: User notified of delay

**Expected Result:** Graceful degradation, retry attempted

---

### Scenario 22: Concurrent Requests
**Objective:** Test system under load

**Steps:**
1. Submit 5 different requests simultaneously
2. Expected: All requests processed
3. Expected: No data corruption
4. Expected: Responses returned correctly

**Expected Result:** System handles concurrent requests correctly

---

## 🎯 Professional Test Questions for Each Agent

### For Procurement Supervisor (Agent 1):
1. "Process a new requisition for office supplies worth $5,000"
2. "What's the status of requisition REQ-12345?"
3. "Show me all pending approvals"
4. "Create a purchase order for the IT department's laptop request"

### For Document Intelligence Specialist (Agent 2):
1. "Extract data from this invoice: [image]"
2. "Read this purchase order and tell me the line items: [image]"
3. "What's the total amount on this invoice: [image]"
4. "Extract vendor information from this requisition: [image]"

### For Budget & Compliance Specialist (Agent 3):
1. "Check if the IT department has budget for a $10,000 purchase"
2. "What approvals are needed for a $50,000 purchase?"
3. "Is vendor 'ABC Corp' approved for procurement?"
4. "Check compliance for purchase order PO-12345"

### For Purchase Order Specialist (Agent 4):
1. "Create a purchase order from requisition REQ-001"
2. "Match invoice INV-001 to purchase order PO-001"
3. "Track the receiving status for PO-001"
4. "Show me all unmatched invoices"

### For Payment Processing Specialist (Agent 5):
1. "Approve invoice INV-001 for payment"
2. "Check if invoice INV-001 is a duplicate"
3. "Flag invoice INV-001 for exception review"
4. "Generate payment batch for approved invoices"

---

## 📝 Testing Checklist

### Pre-Testing Setup
- [ ] Backend server running on `http://localhost:8000`
- [ ] watsonx Orchestrate agent configured
- [ ] OpenAPI spec imported to watsonx
- [ ] Test images/documents prepared

### Test Execution
- [ ] Run happy path scenario (Scenario 1)
- [ ] Test exception handling (Scenarios 2-5)
- [ ] Test supply chain scenarios (Scenarios 8-12)
- [ ] Test inventory scenarios (Scenarios 13-15)
- [ ] Test multi-agent workflows (Scenarios 16-18)
- [ ] Test edge cases (Scenarios 19-22)

### Validation
- [ ] All agents respond correctly
- [ ] Exceptions handled gracefully
- [ ] Error messages are clear
- [ ] Workflow completes end-to-end
- [ ] Performance is acceptable (<2 min for full cycle)

---

## 🚀 Quick Test Commands

### Test via watsonx Orchestrate Chat:
```
"I need to order 10 office chairs for $2,000. Process this requisition: [upload image]"
```

### Test via API (curl):
```bash
# Test document extraction
curl -X POST http://localhost:8000/procurement/extract_document \
  -H "Content-Type: application/json" \
  -d '{"document_url": "https://example.com/invoice.jpg", "document_type": "invoice"}'

# Test budget check
curl -X POST http://localhost:8000/procurement/check_budget \
  -H "Content-Type: application/json" \
  -d '{"department": "IT", "amount": 1000.0}'
```

---

## 📊 Success Metrics

- **Automation Rate:** 80%+ of invoices processed without human intervention
- **Cycle Time:** <1 day (vs 5-7 days manual)
- **Error Rate:** <5% (vs 15-20% manual)
- **Exception Detection:** 100% of mismatches detected
- **Duplicate Prevention:** 100% of duplicates blocked

---

## 💡 Tips for Testing

1. **Start Simple:** Begin with happy path scenarios
2. **Test Incrementally:** Test one agent at a time
3. **Use Real Data:** Use actual invoice/PO images when possible
4. **Document Issues:** Note any errors or unexpected behavior
5. **Test Edge Cases:** Don't just test happy paths
6. **Verify Results:** Check that all expected outcomes occur

---

**Last Updated:** 2024
**Version:** 1.0

