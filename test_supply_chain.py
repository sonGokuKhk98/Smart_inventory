"""
Test Script for Combined Supply Chain API
Tests: Box Inspection + VAS Label Verification (PRD v6)
"""

import requests
import json
from typing import Dict

BASE_URL = "http://localhost:8000"

def print_section(title: str):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

# ============================================================================
# TEST 1: BOX INSPECTION
# ============================================================================

def test_box_inspection():
    """Test box condition inspection"""
    print_section("TEST 1: BOX INSPECTION (Inbound Gatekeeper)")
    
    test_cases = [
        {
            "name": "Good Box",
            "url": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=800",
            "shipment_id": "SHIP-001"
        },
        {
            "name": "Damaged Box",
            "url": "https://images.unsplash.com/photo-1563207153-f403bf289096?w=800",
            "shipment_id": "SHIP-002"
        }
    ]
    
    for case in test_cases:
        print(f"\n📦 Testing: {case['name']}")
        response = requests.post(
            f"{BASE_URL}/inspect/box",
            json={
                "image_url": case["url"],
                "shipment_id": case["shipment_id"]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Condition: {result['box_condition']}")
            print(f"   📊 Can Ship: {result['can_ship']}")
            print(f"   🔍 Defects: {result['total_defects']}")
            if result['findings']:
                for f in result['findings']:
                    print(f"      - {f['defect_type']} ({f['severity']})")
        else:
            print(f"   ❌ Error: {response.status_code}")

# ============================================================================
# TEST 2: VAS LABEL VERIFICATION (PRD v6)
# ============================================================================

def test_vas_label_verification():
    """Test VAS label verification - The Mismatched Label Scenario"""
    print_section("TEST 2: VAS LABEL VERIFICATION (QC Specialist)")
    print("   PRD v6: Detects 'Blue Shirt' label on 'Red Shirt' package")
    
    test_cases = [
        {
            "name": "Label Verification Test",
            "url": "https://images.unsplash.com/photo-1553413077-190dd305871c?w=800",
            "order_id": "ORDER-999",
            "station_id": "Station-4",
            "expected_sku": "SKU-123"
        }
    ]
    
    for case in test_cases:
        print(f"\n🔍 Testing: {case['name']}")
        print(f"   Order: {case['order_id']} at {case['station_id']}")
        
        response = requests.post(
            f"{BASE_URL}/vas/verify_label",
            json={
                "image_url": case["url"],
                "order_id": case["order_id"],
                "station_id": case["station_id"],
                "expected_sku": case.get("expected_sku")
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Label Text: '{result['label_text']}'")
            print(f"   👁️  Visual Object: '{result['visual_object']}'")
            print(f"   ✅ Match: {result['match']}")
            print(f"   📊 Confidence: {result['confidence']}")
            print(f"   ⚠️  Action: {result['action_required']}")
            print(f"   💭 Reasoning: {result['reasoning'][:100]}...")
        else:
            print(f"   ❌ Error: {response.status_code}")

# ============================================================================
# TEST 3: WMS CHECK
# ============================================================================

def test_wms_check():
    """Test WMS order check"""
    print_section("TEST 3: WMS CHECK (GACWare Specialist)")
    
    test_cases = [
        {"order_id": "ORDER-999", "sku": "SKU-123"},
        {"order_id": "ORDER-888", "sku": None},
        {"order_id": "ORDER-UNKNOWN", "sku": None}
    ]
    
    for case in test_cases:
        print(f"\n📋 Checking: {case['order_id']}")
        response = requests.post(
            f"{BASE_URL}/wms/check",
            json=case,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Status: {result['status']}")
            print(f"   📦 SKU: {result['sku']}")
            print(f"   📝 Expected: {result['expected_item']}")
            print(f"   🔢 Quantity: {result['quantity']}")
        else:
            print(f"   ❌ Error: {response.status_code}")

# ============================================================================
# TEST 4: EXCEPTION HANDLING
# ============================================================================

def test_exception_handling():
    """Test exception handling"""
    print_section("TEST 4: EXCEPTION HANDLING (Fulfillment Specialist)")
    
    test_cases = [
        {
            "exception_type": "LABEL_MISMATCH",
            "order_id": "ORDER-999",
            "details": "Label says Blue Shirt but package contains Red Shirt",
            "station_id": "Station-4"
        },
        {
            "exception_type": "BOX_DAMAGED",
            "order_id": "SHIP-002",
            "details": "Box is crushed and torn",
            "station_id": None
        }
    ]
    
    for case in test_cases:
        print(f"\n⚠️  Handling: {case['exception_type']}")
        response = requests.post(
            f"{BASE_URL}/ops/handle_exception",
            json=case,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Ticket ID: {result['ticket_id']}")
            print(f"   📊 Status: {result['status']}")
            print(f"   📝 Action: {result['action_taken']}")
        else:
            print(f"   ❌ Error: {response.status_code}")

# ============================================================================
# TEST 5: COMPLETE WORKFLOW (PRD v6 Scenario)
# ============================================================================

def test_complete_workflow():
    """Test complete PRD v6 workflow: Mismatched Label Scenario"""
    print_section("TEST 5: COMPLETE WORKFLOW - PRD v6 Scenario")
    print("   Scenario: 'Blue Shirt' label on 'Red Shirt' package")
    
    order_id = "ORDER-999"
    station_id = "Station-4"
    image_url = "https://images.unsplash.com/photo-1553413077-190dd305871c?w=800"
    
    print("\n📋 Step 1: VAS Supervisor receives package")
    print(f"   Order: {order_id} at {station_id}")
    
    print("\n🔍 Step 2: QC Specialist verifies label...")
    label_result = requests.post(
        f"{BASE_URL}/vas/verify_label",
        json={
            "image_url": image_url,
            "order_id": order_id,
            "station_id": station_id,
            "expected_sku": "SKU-123"
        },
        timeout=30
    ).json()
    
    print(f"   Label: '{label_result['label_text']}'")
    print(f"   Object: '{label_result['visual_object']}'")
    print(f"   Match: {label_result['match']}")
    
    if not label_result['match']:
        print("\n⚠️  Step 3: MISMATCH DETECTED!")
        print("   Supervisor: Stop line and check WMS")
        
        print("\n📋 Step 4: GACWare Specialist checks order...")
        wms_result = requests.post(
            f"{BASE_URL}/wms/check",
            json={"order_id": order_id},
            timeout=10
        ).json()
        
        print(f"   Expected: {wms_result['expected_item']}")
        print(f"   Status: {wms_result['status']}")
        
        print("\n🚨 Step 5: Fulfillment Specialist handles exception...")
        exception_result = requests.post(
            f"{BASE_URL}/ops/handle_exception",
            json={
                "order_id": order_id,
                "exception_type": "LABEL_MISMATCH",
                "details": f"Label mismatch: {label_result['label_text']} vs {label_result['visual_object']}",
                "station_id": station_id
            },
            timeout=10
        ).json()
        
        print(f"   ✅ Order held: {exception_result['ticket_id']}")
        print(f"   📊 Status: {exception_result['status']}")
        print(f"   📝 Action: {exception_result['action_taken']}")
        
        print("\n✅ Workflow Complete: Wrong item caught before shipping!")
    else:
        print("\n✅ Label matches - Package can proceed")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print_section("SUPPLY CHAIN LOGISTICS API - TEST SUITE")
    print("   Box Inspection + VAS Label Verification (PRD v6)")
    
    try:
        # Test individual endpoints
        test_box_inspection()
        test_vas_label_verification()
        test_wms_check()
        test_exception_handling()
        
        # Test complete workflow
        test_complete_workflow()
        
        print_section("✅ ALL TESTS COMPLETE")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Server not running!")
        print("   Start server: python3 backend/main_supply_chain.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    main()



