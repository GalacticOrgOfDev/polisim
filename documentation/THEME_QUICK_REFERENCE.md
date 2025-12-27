# Theme System Quick Reference
**Last Updated:** December 26, 2025

## 🎨 Available Themes

| Theme | ID | Purpose | Animation | Font |
|-------|----|---------|-----------| ------|
| **Light Mode** | `light` | Professional Windows-style | None | Segoe UI |
| **Dark Mode** | `dark` | Eye-friendly dark theme | Optional particles | Segoe UI |
| **Matrix AI** | `matrix` | Hacker/AI aesthetic | ✅ Matrix rain | Courier New |
| **Cyberpunk 2077** | `cyberpunk` | Neon yellow/magenta vibes | ✅ Neon particles | Orbitron |
| **Nord Arctic** | `nord` | Cool minimalist palette | None | Inter |
| **Solarized Dark** | `solarized` | Classic coding theme | None | Source Code Pro |

## 🔧 Applying Themes

### In Code
```python
from ui.themes import apply_theme, apply_plotly_theme

# Apply theme
current_theme = st.session_state.settings.get('theme', 'light')
apply_theme(current_theme)

# Apply to Plotly charts
fig = go.Figure(...)
apply_plotly_theme(fig, current_theme)
st.plotly_chart(fig)
```

### In Dashboard
1. Navigate to **⚙️ Settings**
2. Select theme from dropdown
3. Click **Apply Theme Now**
4. (Optional) Expand preview to customize colors

## 🎯 Theme Color Palettes

### Light Mode
- Background: `#FFFFFF` (white)
- Text: `#262730` (dark gray)
- Primary: `#0078D4` (Windows blue)
- Hover: `#106EBE` (darker blue)

### Dark Mode
- Background: `#0E1117` (deep charcoal)
- Text: `#FAFAFA` (white)
- Primary: `#FF4B4B` (Streamlit red)
- Hover: `#FF6B6B` (lighter red)

### Matrix AI
- Background: `#000000` (black, transparent)
- Text: `#FFFFFF` (white) ⚠️ **Not green!**
- Primary: `#00FF41` (neon green)
- Accent: `#39FF14` (brighter green)

### Cyberpunk 2077
- Background: `#0A0E27` (deep blue, transparent)
- Text: `#FFFFFF` (white) ⚠️ **Not yellow!**
- Primary: `#FFFF00` (neon yellow)
- Secondary: `#FF00FF` (neon magenta)

### Nord Arctic
- Background: `#2E3440` (dark gray)
- Text: `#ECEFF4` (bright white)
- Primary: `#88C0D0` (frost blue)
- Accent: `#81A1C1` (light blue)

### Solarized Dark
- Background: `#002B36` (solarized base03)
- Text: `#93A1A1` (solarized base1)
- Primary: `#268BD2` (solarized blue)
- Accent: `#2AA198` (solarized cyan)

## ⚡ Adding a New Theme

### Step 1: Define Theme Config
```python
# In ui/themes.py, add to THEMES dict:
"my_theme": ThemeConfig(
    name="My Theme Name",
    id="my_theme",
    primary_color="#HEX",
    background_color="#HEX",
    secondary_background_color="#HEX",
    text_color="#HEX",
    accent_color="#HEX",
    font_family="'Font Name', sans-serif",
    
    # Element styles
    button=ElementStyle(
        background="#HEX",
        color="#HEX",
        hover_bg="#HEX",
    ),
    radio=ElementStyle(...),
    selectbox=ElementStyle(...),
    # ... etc
    
    # Optional
    animation="animation_type",  # or None
    needs_transparency=True/False,
)
```

### Step 2: Add Chart Colors
```python
# In get_chart_colors() function:
if theme.id == "my_theme":
    return ["#COLOR1", "#COLOR2", "#COLOR3", ...]
```

### Step 3: Add Plotly Template Mapping
```python
# In get_plotly_template() function:
if theme.id == "my_theme":
    return "plotly_white"  # or plotly_dark, seaborn, etc.
```

### Step 4: (Optional) Add Animation
```python
# In ui/animations.py, extend apply_animation():
elif theme_id == "my_theme":
    matrix_rain_animation(...)  # or particle_system_animation(...)

# And add to get_animation_config():
"my_theme": {
    "type": "matrix_rain",  # or "particle_system" or "none"
    "enabled_by_default": True/False,
    ...
}
```

## 🧪 Testing Your Theme

Use the comprehensive [THEME_TESTING_GUIDE.md](THEME_TESTING_GUIDE.md), or quick checks:

**Visual Check:**
```python
# Run dashboard
streamlit run ui/dashboard.py

# Go to Settings → Theme Settings
# Select your theme
# Check:
- [ ] Background color correct
- [ ] Text readable
- [ ] Buttons have hover effect
- [ ] Dropdowns work
- [ ] Sliders visible
- [ ] Charts match theme
```

**Code Check:**
```python
from ui.themes import get_theme, preview_theme

# Get theme
theme = get_theme("my_theme")
print(theme.name)
print(theme.primary_color)

# Preview in Streamlit
preview_theme("my_theme")
```

## 🐛 Common Issues

### Text Not Readable
**Problem:** Text color too similar to background  
**Fix:** Ensure high contrast ratio (4.5:1 minimum for body text)
```python
# Use color contrast checker online
# Adjust text_color in ThemeConfig
```

### Elements Not Themed
**Problem:** Some UI elements still use default colors  
**Fix:** Add ElementStyle configuration for that element
```python
# In ThemeConfig:
my_element=ElementStyle(
    background="#HEX",
    color="#HEX",
    border_color="#HEX",
    # ...
)
```

### Animation Not Appearing
**Problem:** Canvas element not visible  
**Fix:** Check z-index and position
```javascript
// In animation JS:
canvas.style.cssText = 'position:fixed!important;z-index:-1!important;...';
```

### Font Not Loading
**Problem:** Custom font not displaying  
**Fix:** Add to Google Fonts import
```python
# In apply_theme():
@import url('https://fonts.googleapis.com/css2?family=Your+Font&display=swap');
```

## 📋 Element Style Properties

### ElementStyle Fields
```python
@dataclass
class ElementStyle:
    background: Optional[str] = None         # Background color
    color: Optional[str] = None              # Text/foreground color
    border: Optional[str] = None             # Border CSS (e.g., "1px solid #HEX")
    border_color: Optional[str] = None       # Border color only
    hover_bg: Optional[str] = None           # Background on hover
    hover_color: Optional[str] = None        # Text color on hover
    hover_border: Optional[str] = None       # Border color on hover
    active_bg: Optional[str] = None          # Background when active/selected
    active_color: Optional[str] = None       # Color when active/selected
    text_shadow: Optional[str] = None        # CSS text-shadow
    box_shadow: Optional[str] = None         # CSS box-shadow
    additional_css: Optional[str] = None     # Free-form CSS
```

### Available Element Types
- `button` - Primary buttons
- `radio` - Radio button groups
- `selectbox` - Dropdown selects
- `text_input` - Text input fields
- `slider` - Range sliders
- `checkbox` - Checkboxes
- `tooltip` - Tooltip popups
- `sidebar` - Sidebar background/text
- `expander` - Collapsible expanders
- `number_input` - Number inputs (new)
- `date_input` - Date pickers (new)
- `multiselect` - Multi-select dropdowns (new)
- `file_uploader` - File upload areas (new)

## 🔗 Related Files

| File | Purpose |
|------|---------|
| `ui/themes.py` | Theme definitions & application |
| `ui/animations.py` | Animation effects |
| `ui/dashboard.py` | Theme integration in main app |
| `documentation/THEME_AUDIT_DEC26.md` | Full audit report |
| `documentation/THEME_TESTING_GUIDE.md` | Testing protocol |
| `documentation/THEME_SUMMARY_DEC26.md` | Implementation summary |

## 💡 Tips & Best Practices

### Do's ✅
- Use high contrast ratios for accessibility
- Test in multiple browsers
- Provide fallback fonts in font-family
- Use rgba() for transparency when animations present
- Include hover states for interactive elements
- Test with real content (long text, many options, etc.)

### Don'ts ❌
- Don't use low contrast (hard to read)
- Don't rely on color alone (use icons too)
- Don't forget mobile/responsive design
- Don't use too many different colors
- Don't make buttons look like plain text
- Don't forget to test animations on lower-end hardware

### Performance Tips 🚀
- Limit animation particle count (<100)
- Use CSS transforms for animations (GPU-accelerated)
- Minimize canvas size when possible
- Cleanup animations when switching themes
- Use throttling for resize handlers
- Test on target deployment hardware

## 📞 Support

**Issues?**
1. Check [THEME_TESTING_GUIDE.md](THEME_TESTING_GUIDE.md) troubleshooting section
2. Review browser console for errors (F12)
3. Verify theme applied: check `st.session_state.settings['theme']`
4. Try refreshing page (F5)
5. Clear browser cache if persistent

**Contributing?**
1. Follow existing theme structure
2. Add comprehensive ElementStyle configs
3. Test all interactive elements
4. Document in code comments
5. Add to testing guide

---

**Quick Links:**
- [Full Audit Report](THEME_AUDIT_DEC26.md)
- [Testing Guide](THEME_TESTING_GUIDE.md)
- [Implementation Summary](THEME_SUMMARY_DEC26.md)
