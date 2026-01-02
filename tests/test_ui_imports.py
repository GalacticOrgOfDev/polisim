#!/usr/bin/env python
"""Test all dashboard UI imports"""

print('Starting UI imports...')

try:
    from ui.auth import StreamlitAuth, show_user_profile_page
    print('✓ ui.auth')
except Exception as e:
    print(f'✗ ui.auth: {e}')
    import traceback
    traceback.print_exc()
    
try:
    from ui.themes import apply_theme, get_theme_list, preview_theme, customize_theme_colors, apply_plotly_theme
    print('✓ ui.themes')
except Exception as e:
    print(f'✗ ui.themes: {e}')
    import traceback
    traceback.print_exc()
    
try:
    from ui.animations import apply_animation
    print('✓ ui.animations')
except Exception as e:
    print(f'✗ ui.animations: {e}')
    import traceback
    traceback.print_exc()
    
try:
    from ui.tooltip_registry import get_tooltip as registry_get_tooltip
    print('✓ ui.tooltip_registry')
except Exception as e:
    print(f'✗ ui.tooltip_registry: {e}')
    import traceback
    traceback.print_exc()

print('All UI imports tested!')
