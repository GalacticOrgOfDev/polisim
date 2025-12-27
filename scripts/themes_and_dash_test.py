"""
Theme and Dashboard Conflict Test Suite
Tests the interaction between themes.py and dashboard.py to verify ElementStyle usage.

Usage:
    python scripts/themes_and_dash_test.py

This script performs automated testing of:
1. CSS generation from ElementStyle configs
2. Theme switching behavior
3. Element rendering with correct colors
4. CSS accumulation detection
"""

import re
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Ensure project root is on sys.path when run directly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from ui.themes import ElementStyle, THEMES, ThemeConfig, apply_theme, get_theme


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
            assert light_theme.menu.hover_bg == "#0078D4", "Expected blue hover color"

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

    def test_light_overrides(self):
        """Test if light theme has hardcoded overrides."""
        print("\n" + "=" * 70)
        print("TEST 5: Light Theme Hardcoded Overrides Detection")
        print("=" * 70)

        try:
            themes_file = PROJECT_ROOT / 'ui' / 'themes.py'
            content = themes_file.read_text(encoding='utf-8')

            if 'light_overrides = """' in content:
                start = content.find('light_overrides = """')
                end = content.find('"""', start + 25)
                overrides_section = content[start:end]
                hardcoded_colors = re.findall(r'#[0-9A-Fa-f]{6}', overrides_section)

                print(f"⚠️  WARNING: Found light_overrides section with {len(hardcoded_colors)} hardcoded color values")
                print("   This section should be removed - base CSS should handle all styling")
                print("   Hardcoded colors override ElementStyle configurations")
                unique_colors = list(set(hardcoded_colors))[:10]
                print(f"   Sample hardcoded colors: {', '.join(unique_colors)}")
                print("\n⚠️  ACTION NEEDED: Remove light_overrides section")
            else:
                print("✅ PASS: No light_overrides section found - base CSS is handling all styling")

            self.tests_passed += 1

        except Exception as e:
            print(f"❌ ERROR: {e}")
            self.tests_failed += 1
            self.failures.append(("Light Overrides", str(e)))

    def test_css_injection_count(self):
        """Test how many times CSS is injected."""
        print("\n" + "=" * 70)
        print("TEST 6: CSS Injection Count")
        print("=" * 70)

        try:
            css_injections = []

            def mock_markdown(content, unsafe_allow_html=False):
                if unsafe_allow_html and '<style>' in content:
                    css_injections.append(content)

            with patch.object(st, 'markdown', side_effect=mock_markdown):
                with patch.object(st, 'session_state', {}):
                    apply_theme('light')

            injection_count = len(css_injections)
            print(f"CSS was injected {injection_count} time(s)")

            if injection_count > 1:
                print("⚠️  WARNING: Multiple CSS injections detected")
                print("   This can cause order-dependency issues and bloat")
                print("   Recommendation: Concatenate all CSS before single injection")
            else:
                print("✅ GOOD: Single CSS injection")

            total_size = sum(len(css) for css in css_injections)
            print(f"\nTotal CSS size: {total_size:,} characters ({total_size/1024:.1f} KB)")

            if total_size > 50000:
                print("⚠️  WARNING: CSS is very large (>50KB)")
                print("   Consider optimization or removal of redundant rules")

            self.tests_passed += 1

        except Exception as e:
            print(f"❌ ERROR: {e}")
            self.tests_failed += 1
            self.failures.append(("CSS Injection Count", str(e)))

    def run_all_tests(self):
        """Run all tests and print summary."""
        print("\n" + "=" * 70)
        print("THEME AND DASHBOARD CONFLICT TEST SUITE")
        print("=" * 70)

        self.test_theme_loading()
        self.test_css_generation()
        self.test_theme_mutation()
        self.test_unused_properties()
        self.test_light_overrides()
        self.test_css_injection_count()

        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_failed}")
        print(f"Total Tests: {self.tests_passed + self.tests_failed}")

        if self.tests_failed > 0:
            print("\n" + "=" * 70)
            print("FAILURES:")
            print("=" * 70)
            for test_name, error in self.failures:
                print(f"\n{test_name}:")
                print(f"  {error}")

        print("\n" + "=" * 70)
        if self.tests_failed == 0:
            print("✅ ALL TESTS PASSED")
        else:
            print(f"❌ {self.tests_failed} TEST(S) FAILED")
        print("=" * 70 + "\n")

        return self.tests_failed == 0


def main():
    """Main test runner."""
    suite = ThemeTestSuite()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
