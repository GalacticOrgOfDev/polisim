"""
Theme and Dashboard Conflict Test Suite
Tests the interaction between themes.py and dashboard.py to verify ElementStyle usage.

Usage:
    python tests/test_themes_dash_manual.py

This script performs automated testing of:
1. CSS generation from ElementStyle configs
2. Theme switching behavior
3. Element rendering with correct colors
4. CSS accumulation detection
"""
import sys
from pathlib import Path
import re
from unittest.mock import Mock, patch

# Ensure project root on sys.path for direct execution
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402
from ui.themes import get_theme, apply_theme, THEMES, ElementStyle, ThemeConfig  # noqa: E402


class ThemeTestSuite:
    """Test suite for theme system."""

    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []

    def test_theme_loading(self):
        """Test that themes load correctly with ElementStyle configs."""
        print("\n" + "=" * 70)
        print("TEST 1: Theme Loading")
        print("=" * 70)

        try:
            light_theme = get_theme('light')
            assert isinstance(light_theme, ThemeConfig), "Light theme should be ThemeConfig"
            assert light_theme.id == 'light', "Theme ID should be 'light'"
            assert isinstance(light_theme.radio, ElementStyle), "radio should be ElementStyle"
            assert isinstance(light_theme.button, ElementStyle), "button should be ElementStyle"
            assert isinstance(light_theme.menu, ElementStyle), "menu should be ElementStyle"
            assert light_theme.radio.background == "#FFFFFF", "Expected white background"
            assert light_theme.radio.border_color == "#808080", "Expected grey border"
            assert light_theme.radio.active_color == "#0078D4", "Expected blue active color"
            assert light_theme.menu.background == "#F0F2F6", "Expected grey menu background"

            print("✅ PASS: Theme loading works correctly")
            print(f"   - Light theme loaded with ID: {light_theme.id}")
            print(f"   - Radio: background={light_theme.radio.background}, active_color={light_theme.radio.active_color}")
            print(f"   - Menu: background={light_theme.menu.background}, hover_bg={light_theme.menu.hover_bg}")
            self.tests_passed += 1

        except AssertionError as e:
            print(f"❌ FAIL: {e}")
            self.tests_failed += 1
            self.failures.append(("Theme Loading", str(e)))
        except Exception as e:
            print(f"❌ ERROR: {e}")
            self.tests_failed += 1
            self.failures.append(("Theme Loading", str(e)))

    def test_css_generation(self):
        """Test that CSS generation uses ElementStyle properties."""
        print("\n" + "=" * 70)
        print("TEST 2: CSS Generation from ElementStyle")
        print("=" * 70)

        try:
            css_output = []

            def mock_markdown(content, unsafe_allow_html=False):
                if unsafe_allow_html and '<style>' in content:
                    css_output.append(content)

            with patch.object(st, 'markdown', side_effect=mock_markdown):
                with patch.object(st, 'session_state', {}):
                    apply_theme('light')

            assert len(css_output) > 0, "No CSS was generated"
            full_css = '\n'.join(css_output)

            checks = [
                (r'background-color:\s*#FFFFFF', "Radio background"),
                (r'border-color:\s*#808080', "Radio border"),
                (r'background-color:\s*#0078D4', "Radio active"),
                (r'background-color:\s*#F0F2F6', "Menu background"),
            ]

            print(f"Generated {len(css_output)} CSS block(s)")
            print(f"Total CSS length: {len(full_css)} characters")
            print("\nChecking for ElementStyle properties in CSS:")

            for pattern, description in checks:
                if re.search(pattern, full_css):
                    print(f"   ✅ Found: {description}")
                else:
                    print(f"   ❌ Missing: {description}")
                    raise AssertionError(f"CSS missing {description}")

            print("\n✅ PASS: CSS correctly uses ElementStyle properties")
            self.tests_passed += 1

        except AssertionError as e:
            print(f"\n❌ FAIL: {e}")
            self.tests_failed += 1
            self.failures.append(("CSS Generation", str(e)))
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            self.tests_failed += 1
            self.failures.append(("CSS Generation", str(e)))

    def test_theme_mutation(self):
        """Test that custom colors don't mutate the original theme."""
        print("\n" + "=" * 70)
        print("TEST 3: Theme Mutation Prevention")
        print("=" * 70)

        try:
            original_theme = get_theme('light')
            original_primary = original_theme.primary_color
            custom_colors = {'primary_color': '#FF0000'}

            with patch.object(st, 'markdown', Mock()):
                with patch.object(st, 'session_state', {}):
                    apply_theme('light', custom_colors)

            current_theme = get_theme('light')
            current_primary = current_theme.primary_color

            if current_primary != original_primary:
                print(f"❌ FAIL: Theme was mutated! Changed from {original_primary} to {current_primary}")
                raise AssertionError("Theme mutation detected - apply_theme mutates global THEMES dict")

            print("✅ PASS: Theme not mutated by custom colors")
            self.tests_passed += 1

        except AssertionError as e:
            print(f"❌ FAIL: {e}")
            self.tests_failed += 1
            self.failures.append(("Theme Mutation", str(e)))
        except Exception as e:
            print(f"❌ ERROR: {e}")
            self.tests_failed += 1
            self.failures.append(("Theme Mutation", str(e)))

    def test_unused_properties(self):
        """Test for unused properties in ElementStyle."""
        print("\n" + "=" * 70)
        print("TEST 4: Unused ElementStyle Properties")
        print("=" * 70)

        try:
            from dataclasses import fields

            element_fields = [f.name for f in fields(ElementStyle)]
            element_specific = [
                'radio', 'selectbox', 'text_input', 'slider', 'checkbox',
                'tooltip', 'sidebar', 'expander', 'number_input', 'date_input',
                'multiselect', 'file_uploader'
            ]

            found_unused = [prop for prop in element_specific if prop in element_fields]

            if found_unused:
                print(f"⚠️  WARNING: Found {len(found_unused)} unused element-specific properties in ElementStyle:")
                for prop in found_unused:
                    print(f"   - {prop}")
                print("   Recommendation: move element-specific styling into dedicated config classes.")
            else:
                print("✅ PASS: No unused element-specific properties detected in ElementStyle")
            self.tests_passed += 1

        except Exception as e:
            print(f"❌ ERROR: {e}")
            self.tests_failed += 1
            self.failures.append(("Unused Properties", str(e)))

    def test_css_accumulation(self):
        """Detect CSS accumulation issues when switching themes multiple times."""
        print("\n" + "=" * 70)
        print("TEST 5: CSS Accumulation Detection")
        print("=" * 70)

        try:
            css_output = []

            def mock_markdown(content, unsafe_allow_html=False):
                if unsafe_allow_html and '<style>' in content:
                    css_output.append(content)

            with patch.object(st, 'markdown', side_effect=mock_markdown):
                with patch.object(st, 'session_state', {}):
                    apply_theme('light')
                    apply_theme('matrix')
                    apply_theme('cyberpunk')

            combined_css = '\n'.join(css_output)
            occurrences = combined_css.count('<style>')

            print(f"Generated {occurrences} style block(s) across theme switches")
            if occurrences > 3:
                print("⚠️  WARNING: CSS may be accumulating across theme switches. Consider clearing or overwriting styles.")
            else:
                print("✅ PASS: CSS accumulation appears controlled")
            self.tests_passed += 1

        except Exception as e:
            print(f"❌ ERROR: {e}")
            self.tests_failed += 1
            self.failures.append(("CSS Accumulation", str(e)))

    def summary(self):
        print("\n" + "=" * 70)
        print("TEST SUITE SUMMARY")
        print("=" * 70)
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        if self.failures:
            print("Failures:")
            for name, msg in self.failures:
                print(f" - {name}: {msg}")
        else:
            print("All checks passed")


def main():
    suite = ThemeTestSuite()
    suite.test_theme_loading()
    suite.test_css_generation()
    suite.test_theme_mutation()
    suite.test_unused_properties()
    suite.test_css_accumulation()
    suite.summary()


if __name__ == "__main__":
    main()
