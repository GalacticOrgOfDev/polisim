#!/usr/bin/env python3
"""Quick test to measure validation timing on high iteration count."""

import pytest
from core.combined_outlook import CombinedFiscalOutlookModel
from core.validation import ValidationError
import time
import sys

def test_validation_timing():
    """Test if 100k iteration validation happens early."""
    model = CombinedFiscalOutlookModel()
    
    # Test that 100k iterations is rejected
    start = time.time()
    with pytest.raises(ValidationError):
        model.project_unified_budget(years=10, iterations=100000)
    
    elapsed = time.time() - start
    
    # Validation should happen early (< 5s), not after computation
    assert elapsed < 5, f"Validation took {elapsed:.1f}s - too slow, computation happened before validation"


if __name__ == '__main__':
    test_validation_timing()
    print("Test passed!")
    sys.exit(0)
