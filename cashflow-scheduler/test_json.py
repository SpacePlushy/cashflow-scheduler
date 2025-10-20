#!/usr/bin/env python3
import json
from pathlib import Path

plan_path = Path('assets/example_plans/simple_plan.json')
print(f'Validating: {plan_path}')

try:
    with open(plan_path) as f:
        data = json.load(f)

    # Check required fields
    required = ['start_balance', 'target_end', 'band', 'rent_guard', 'deposits', 'bills']
    missing = [f for f in required if f not in data]

    if missing:
        print(f'❌ Missing required fields: {missing}')
    else:
        print('✅ All required fields present')
        print(f'   - start_balance: ${data["start_balance"]:.2f}')
        print(f'   - target_end: ${data["target_end"]:.2f}')
        print(f'   - band: ${data["band"]:.2f}')
        print(f'   - rent_guard: ${data["rent_guard"]:.2f}')
        print(f'   - deposits: {len(data["deposits"])} items')
        print(f'   - bills: {len(data["bills"])} items')

    # Validate JSON structure
    print('✅ Valid JSON structure')

except json.JSONDecodeError as e:
    print(f'❌ Invalid JSON: {e}')
except Exception as e:
    print(f'❌ Error: {e}')
