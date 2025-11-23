# Demo Mode Quick Start 🎬

## Perfect for Hackathon Demo!

I've created a **demo mode** that gives you **realistic, consistent responses** without needing perfect test images.

## Quick Start

### 1. Start Demo Server

```bash
python3 backend/main_vas_demo.py
```

### 2. Test with Demo Scenarios

```bash
python3 test_vas_workflows.py
```

The test script now uses demo mode automatically!

## Demo Scenarios

### ✅ Good Workflow (PASS)
```bash
curl -X POST "http://localhost:8000/logistics/inspect_vas_item?demo_mode=good_match" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "any-url",
    "station_id": "Station-4",
    "order_id": "ORDER-888"
  }'
```

**Returns:**
- Label: "Blue Shirt - Size M - SKU-123"
- Object: "Blue Shirt"
- Match: **true** ✅
- Status: **PASS**

### ❌ Bad Workflow (FAIL - Mismatch)
```bash
curl -X POST "http://localhost:8000/logistics/inspect_vas_item?demo_mode=bad_mismatch" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "any-url",
    "station_id": "Station-4",
    "order_id": "ORDER-999"
  }'
```

**Returns:**
- Label: "Blue Shirt - Size M - SKU-123"
- Object: "Red Shirt"
- Match: **false** ❌
- Status: **FAIL**
- Reason: "Label says Blue but object is Red"

### ❌ Damaged Package (FAIL)
```bash
curl -X POST "http://localhost:8000/logistics/inspect_vas_item?demo_mode=damaged" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "any-url",
    "station_id": "Station-4",
    "order_id": "ORDER-777"
  }'
```

**Returns:**
- Label: "Unable to read label - label torn"
- Object: "Damaged package with water stains"
- Match: **false** ❌
- Status: **FAIL**

## Complete Workflow Demo

The test script (`test_vas_workflows.py`) now automatically uses demo mode:

1. **Good Workflow**: `demo_mode=good_match` → PASS → Release
2. **Bad Workflow**: `demo_mode=bad_mismatch` → FAIL → Hold → Alert
3. **Damaged Package**: `demo_mode=damaged` → FAIL → Quarantine

## For watsonx Orchestrate Demo

When configuring agents in watsonx, you can:

1. **Use demo mode in URLs:**
   ```
   http://your-ngrok-url/logistics/inspect_vas_item?demo_mode=good_match
   ```

2. **Or pass in request body:**
   ```json
   {
     "image_url": "any-url",
     "demo_scenario": "bad_mismatch"
   }
   ```

## Benefits

✅ **Reliable** - Consistent responses every time  
✅ **Realistic** - Matches real-world scenarios  
✅ **Fast** - No image processing needed  
✅ **Perfect for Demo** - Shows complete workflow  
✅ **No Image Generation Needed** - Works immediately  

## Note About Gemini

Gemini 2.5 Flash **analyzes** images (doesn't generate them). The demo mode provides realistic responses based on scenarios, which is perfect for demonstrating the multi-agent workflow!

## Next Steps

1. ✅ Start demo server: `python3 backend/main_vas_demo.py`
2. ✅ Run tests: `python3 test_vas_workflows.py`
3. ✅ Generate OpenAPI: `curl http://localhost:8000/openapi.json > openapi_vas.json`
4. ✅ Import to watsonx Orchestrate
5. ✅ Demo the complete workflow! 🎉

