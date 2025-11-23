# 🚀 Quick Test Commands - Copy & Paste Ready

## Your Test Data
- **Image 1:** https://i.ibb.co/C3QgwbCy/Banner-Landscape-Design.png
- **Image 2:** https://i.ibb.co/S7XyKjPZ/1.png
- **SKU:** [Replace with your SKU]

---

## 📦 Agent 1: Box Inspection

### Test 1: Single Box Inspection
```
Inspect this box for shipping: https://i.ibb.co/C3QgwbCy/Banner-Landscape-Design.png
Priority: STANDARD
Shipment ID: SHIP-TEST-001
```

### Test 2: Box with Temperature & Dimensions
```
Inspect box: https://i.ibb.co/S7XyKjPZ/1.png
Priority: CRITICAL
Temperature: 2°C
Dimensions: 200x300
Shipment ID: SHIP-TEST-002
```

### Test 3: Batch Box Inspection
```
Perform batch box inspection on these images:
1. https://i.ibb.co/C3QgwbCy/Banner-Landscape-Design.png
2. https://i.ibb.co/S7XyKjPZ/1.png
```

---

## 🏷️ Agent 2: VAS Label Verification

### Test 1: Label Verification
```
Verify the VAS label on this package: https://i.ibb.co/C3QgwbCy/Banner-Landscape-Design.png
Expected SKU: [YOUR_SKU]
Order ID: ORD-TEST-001
Station: Station-1
```

### Test 2: Label with Kitting List
```
Verify VAS label: https://i.ibb.co/S7XyKjPZ/1.png
Order ID: ORD-TEST-002
Expected SKU: [YOUR_SKU]
Kitting list: ["Item-A", "Item-B"]
Aesthetic check: true
```

---

## 📦 Agent 3: WMS Check

### Test 1: Order Lookup
```
Check order ORD-TEST-001 in the warehouse management system
SKU: [YOUR_SKU]
```

### Test 2: SKU Validation
```
Validate SKU [YOUR_SKU] for order ORD-TEST-002 in WMS
```

---

## ⚠️ Agent 4: Exception Handling

### Test 1: Label Mismatch Exception
```
Handle exception for order ORD-TEST-001
Exception type: LABEL_MISMATCH
Details: Label shows wrong SKU
Station: Station-1
```

### Test 2: Box Damage Exception
```
Handle exception for damaged box
Order ID: ORD-TEST-002
Exception type: BOX_DAMAGED
Details: Box has severe crushing and tears
Station: Station-2
```

---

## 🔄 Multi-Agent Workflow

### Test 1: Complete Inbound Workflow
```
Process this inbound shipment:
1. Inspect box: https://i.ibb.co/C3QgwbCy/Banner-Landscape-Design.png
2. Verify VAS label with SKU: [YOUR_SKU]
3. Check order ORD-TEST-001 in WMS
4. If any issues, handle exception
```

### Test 2: Exception Escalation
```
Process shipment with potential issues:
Box: https://i.ibb.co/S7XyKjPZ/1.png
Order: ORD-TEST-004
SKU: [YOUR_SKU]

If box is damaged OR label doesn't match, handle exception immediately.
```

---

## 📊 Batch Processing

### Test: Batch Inspection
```
Inspect these 2 boxes in batch:
1. https://i.ibb.co/C3QgwbCy/Banner-Landscape-Design.png
2. https://i.ibb.co/S7XyKjPZ/1.png

Provide summary statistics and individual results.
```

---

## 🎯 One-Liner Quick Tests

```
# Box Inspection
Inspect box: https://i.ibb.co/C3QgwbCy/Banner-Landscape-Design.png

# VAS Label
Verify label: https://i.ibb.co/S7XyKjPZ/1.png with SKU [YOUR_SKU]

# WMS Check
Check order ORD-TEST-001 in WMS

# Exception
Handle LABEL_MISMATCH exception for order ORD-TEST-001

# Batch
Batch inspect: https://i.ibb.co/C3QgwbCy/Banner-Landscape-Design.png and https://i.ibb.co/S7XyKjPZ/1.png
```

---

**💡 Tip:** Copy any command above and paste directly into watsonx Orchestrate chat!

