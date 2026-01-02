#!/usr/bin/env python3
"""Debug Pydantic validation."""

from api.validation_models import SimulateRequest

test_data = {
    'policy_name': 'Tax Reform 2025',
    'revenue_change_pct': 10.5,
    'spending_change_pct': -5.0,
    'years': 10,
    'iterations': 100,
}

try:
    req = SimulateRequest(**test_data)
    print('✓ Validation successful')
    print(f'Request: {req}')
except Exception as e:
    print(f'✗ Validation failed: {e}')
    print(f'Error type: {type(e).__name__}')
    import traceback
    traceback.print_exc()
