# PRD: VisionFlow Procurement Automation

## 1. Executive Summary

**VisionFlow Procurement Automation** is a multi-agent cognitive system built on **IBM watsonx Orchestrate**, designed to automate the **End-to-End Procure-to-Pay** workflow. It eliminates manual data entry, reduces processing time from 5-7 days to under 1 day, and prevents costly errors like duplicate payments.

**Target Use Case:** Automated procurement document processing, budget validation, PO creation, invoice matching, and payment approval.

**Business Value:** 
- Reduce cycle time by 60% (5-7 days → <1 day)
- Eliminate 15-20% error rate
- Prevent duplicate payments
- Save $200K-500K annually per organization

---

## 2. The 5-Agent Procurement Swarm

### **Agent 1: Procurement Supervisor (Hub Director)**
- **Role:** Central orchestrator and decision-maker
- **Goal:** Coordinate entire procure-to-pay workflow
- **Agentic Behavior:**
  - Routes tasks based on document type and amount
  - Makes approval decisions autonomously (< $1000 auto-approve)
  - Escalates exceptions to appropriate specialists
  - Adapts workflow based on exception types
- **Logic:** "New requisition → Check budget → Create PO → Process invoice → Approve payment"

### **Agent 2: Document Intelligence Specialist**
- **Role:** Extracts structured data from unstructured documents
- **Skills:** 
  - `extract_document` - OCR + Vision for invoices, POs, requisitions, receipts
- **Capabilities:**
  1. **OCR (Optical Character Recognition):** Reads text from documents
  2. **Visual Reasoning (V-LLM):** Identifies document type and structure
  3. **Data Extraction:** Converts unstructured documents to structured JSON
- **Agentic Behavior:**
  - Chooses extraction method based on document type
  - Validates extracted data quality
  - Flags low-confidence extractions for review

### **Agent 3: Budget & Compliance Specialist**
- **Role:** Validates budget and compliance rules
- **Skills:**
  - `check_budget` - Verify available budget
  - `validate_approval_chain` - Determine approval requirements
  - `check_vendor_status` - Verify vendor is approved
- **Agentic Behavior:**
  - Decides if budget check is needed based on amount
  - Determines approval chain based on department/amount
  - Flags compliance violations autonomously

### **Agent 4: Purchase Order Specialist**
- **Role:** Creates and manages POs, matches documents
- **Skills:**
  - `create_po` - Generate PO from requisition
  - `match_invoice` - 3-way match (PO, Receiving, Invoice)
- **Agentic Behavior:**
  - Decides PO number format based on department
  - Chooses matching strategy (2-way vs 3-way match)
  - Flags discrepancies autonomously

### **Agent 5: Payment Processing Specialist**
- **Role:** Handles invoice approval and payment execution
- **Skills:**
  - `approve_payment` - Approve for payment
  - `flag_exceptions` - Handle mismatches/duplicates
  - `generate_payment` - Create payment record
- **Agentic Behavior:**
  - Decides payment priority based on due date
  - Detects duplicate invoices autonomously
  - Chooses payment method based on vendor preferences

---

## 3. The Workflow: Complete Procure-to-Pay Cycle

### Scenario: "New Office Supplies Requisition"

**Context:** Employee needs office furniture. Submits requisition form.

1. **Trigger:** Requisition document uploaded
2. **Supervisor:** "New requisition received. @Document_Intelligence, extract data."
3. **Document Intelligence Specialist:** 
   - Extracts: Item="Office Chairs", Quantity=5, Cost=$1000
   - Returns structured JSON
4. **Supervisor:** "Data extracted. @Budget_Specialist, check if budget available."
5. **Budget Specialist:**
   - Checks IT department budget: $15,000 available
   - Amount $1,000 < $1,000 threshold → Auto-approve
   - Returns: "Budget OK, no approval needed"
6. **Supervisor:** "Budget approved. @PO_Specialist, create purchase order."
7. **PO Specialist:**
   - Creates PO-2025-001-1234
   - Sends to vendor
8. **Receiving:** Goods arrive → Receiving slip scanned
9. **Invoice Processing:** Vendor sends invoice → Document Intelligence extracts data
10. **PO Matching:** 
    - Match invoice to PO (3-way: PO, Receiving, Invoice)
    - All match → Status: MATCHED
11. **Payment Specialist:**
    - Check for duplicates → None found
    - Auto-approve payment
    - Generate payment record
12. **Result:** Complete cycle automated in <1 day (vs 5-7 days manual)

---

## 4. Technical Implementation

### 4.1. Backend "Skills" (Python/FastAPI)

**File:** `backend/main_procurement.py`

1. `POST /procurement/extract_document`
   - **Input:** Document URL, document type (invoice/po/requisition/receipt)
   - **Technology:** Gemini Vision + OCR
   - **Output:** Structured JSON with extracted fields

2. `POST /procurement/check_budget`
   - **Input:** Department, amount, cost center
   - **Output:** Budget available, approval required, approval chain

3. `POST /procurement/create_po`
   - **Input:** Requisition data, vendor name, department
   - **Output:** PO number, status, total amount

4. `POST /procurement/match_invoice`
   - **Input:** Invoice data, PO number, receipt data (optional)
   - **Output:** Match status, discrepancies, confidence

5. `POST /procurement/approve_payment`
   - **Input:** Invoice ID, invoice data, match result, approval status
   - **Output:** Payment ID, status, duplicate detection, exceptions

### 4.2. IBM watsonx Orchestrate Configuration

- **Agent 1 (Supervisor):** Configured to orchestrate workflow
- **Agent 2-5:** Each mapped to respective backend endpoints
- **Decision Logic:** Supervisor makes routing decisions based on:
  - Document type
  - Amount thresholds
  - Match status
  - Exception types

---

## 5. Demo Scenarios

### Scenario 1: Happy Path (All Automated)
- Requisition → Budget OK → PO Created → Goods Received → Invoice Matched → Payment Approved
- **Time:** 2 minutes (vs 5-7 days manual)
- **Agents Used:** All 5 agents
- **Result:** Complete automation, no human intervention

### Scenario 2: Exception Handling
- Invoice amount doesn't match PO → Flagged for review
- Missing receiving slip → Hold payment
- Duplicate invoice detected → Prevent duplicate payment
- **Agents Used:** All 5 agents with exception routing
- **Result:** Exceptions caught and handled autonomously

### Scenario 3: Multi-Document Batch
- Process 10 invoices simultaneously
- Generate batch approval report
- Identify trends (late payments, vendor issues)
- **Agents Used:** All agents in parallel
- **Result:** Scalable batch processing

---

## 6. Open-Source Data Sources

### For Testing:
- **Invoice Images:** GitHub repositories, Kaggle datasets
- **PO Templates:** Public procurement document samples
- **Receipt Images:** Unsplash/Pexels (receipt photos)
- **Government Procurement:** Public procurement sites with sample documents

### Example Sources:
- GitHub: Sample invoice repositories
- Kaggle: "Invoice Processing Dataset"
- Government procurement portals
- Public invoice samples

---

## 7. Success Metrics

- **Automation Rate:** 80%+ of invoices processed without human intervention
- **Cycle Time:** Reduce from 5-7 days to <1 day
- **Error Rate:** Reduce from 15-20% to <5%
- **Cost Savings:** $200K-500K annually per organization
- **Duplicate Prevention:** 100% duplicate detection rate

---

## 8. Advantages

1. **Data Availability:** Procurement documents are publicly available
2. **Clear Business Value:** Direct cost savings, compliance, efficiency
3. **Hackathon Alignment:** Perfect for "Workflow Automation" and "Digital Skills"
4. **Real-World Impact:** Solves actual enterprise pain point
5. **Leverages Existing Tech:** Reuses Gemini OCR/Vision capabilities
6. **Multi-Agent Orchestration:** Clear agent handoffs and decision trees
7. **Agentic Behavior:** Agents make autonomous decisions at each step

---

## 10. Inventory Management Extension

### Agent 6: Inventory Management Specialist

After procurement is complete, the system automatically manages inventory:

**Capabilities:**
- **Monitor Stock Levels:** Real-time tracking of inventory across warehouses
- **Reallocate Resources:** Automatically balance stock between warehouses
- **Streamline Adjustments:** Automate updates for received, sold, damaged, returned items
- **Optimize Inventory:** Reduce carrying costs, prevent stockouts, minimize overstock
- **Minimize Manual Updates:** Automatic inventory tracking from procurement workflow

**Endpoints:**
- `POST /inventory/check_stock` - Monitor stock levels
- `POST /inventory/reallocate` - Reallocate between warehouses
- `POST /inventory/adjust` - Streamline adjustments
- `POST /inventory/optimize` - Optimize inventory across warehouses

**Workflow Integration:**
1. Payment approved → Goods received → Inventory automatically updated
2. Stock level checked → Low stock detected → Recommend new requisition
3. Inventory optimized → Reallocation recommended → Execute reallocation
4. Adjustments streamlined → Manual updates minimized → Cost savings achieved

**Business Value:**
- Reduce carrying costs by 15-20%
- Prevent stockouts (99.5% availability)
- Minimize manual inventory updates (90% reduction)
- Optimize warehouse utilization

---

## 11. Implementation Checklist

- [x] **Phase 1:** Create procurement backend with document extraction
- [x] **Phase 2:** Implement budget checking and PO creation
- [x] **Phase 3:** Add invoice matching and payment processing
- [x] **Phase 4:** Add inventory management endpoints
- [ ] **Phase 5:** Configure agents in watsonx Orchestrate
- [ ] **Phase 6:** Test with real procurement documents
- [ ] **Phase 7:** Create demo scenarios and presentation

