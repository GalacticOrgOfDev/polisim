# Theme System Testing Guide
**Created:** December 26, 2025  
**Purpose:** Comprehensive testing protocol for all 6 UI themes

## Quick Start Testing

### 1. Launch the Dashboard
```powershell
# From project root
& "E:\AI Projects\polisim\.venv\Scripts\Activate.ps1"
streamlit run ui/dashboard.py
```

### 2. Navigate to Settings
- Click on **⚙️ Settings** in the sidebar
- You should see the Theme Settings section at the top

### 3. Test Each Theme
Follow the per-theme checklist below for each of the 6 themes.

---

## Per-Theme Testing Protocol

### Theme 1: Light Mode (Default)
**Purpose:** Professional Windows-style interface for standard use

#### Color Verification
- [ ] Main background: Pure white (#FFFFFF)
- [ ] Sidebar: Light gray (#F0F2F6)
- [ ] Primary text: Dark gray (#262730)
- [ ] Primary button: Windows blue (#0078D4)
- [ ] Hover button: Darker blue (#106EBE)

#### Critical Elements
- [ ] **Hamburger Menu**: White background, black icon
- [ ] **Dropdown Arrow**: Black color, visible on white background
- [ ] **Radio Buttons**: Gray outline, blue when selected with filled center
- [ ] **Checkboxes**: Gray border, blue when checked with white checkmark
- [ ] **Sliders**: Blue track and thumb
- [ ] **Text Inputs**: White background, black text, gray border
- [ ] **Number Inputs**: White with up/down arrows
- [ ] **Buttons**: Blue with white text, darker blue on hover

#### Special Features
- [ ] No animation by default
- [ ] All text clearly readable (black on white)
- [ ] Form elements have standard Windows appearance

---

### Theme 2: Dark Mode
**Purpose:** Eye-friendly dark theme with subtle red accents

#### Color Verification
- [ ] Main background: Deep charcoal (#0E1117)
- [ ] Sidebar: Lighter charcoal (#262730)
- [ ] Primary text: Pure white (#FAFAFA)
- [ ] Primary button: Streamlit red (#FF4B4B)
- [ ] Hover button: Lighter red (#FF6B6B)

#### Critical Elements
- [ ] **All Text**: White/off-white, clearly readable
- [ ] **Radio Buttons**: Gray outline, red when selected
- [ ] **Checkboxes**: Gray border, red when checked
- [ ] **Sliders**: Red track and thumb
- [ ] **Dropdowns**: Dark background (#262730), white text
- [ ] **Tooltips**: Dark gray background, white text

#### Animation Options
- [ ] **Optional**: Subtle red particle animation
- [ ] Particles should be visible but not distracting
- [ ] Toggle in Settings → Animation Settings

---

### Theme 3: Matrix AI Theme
**Purpose:** Hacker/AI aesthetic with Matrix-style rain animation

#### Color Verification
- [ ] Main background: Pure black (#000000) with transparency
- [ ] Sidebar: Near-black with transparency (rgba)
- [ ] Primary text: **White** (#FFFFFF) - not green!
- [ ] Primary accent: Neon green (#00FF41)
- [ ] Buttons: Dark green background, green text with glow

#### Critical Text Readability
**CRITICAL**: All text must be **WHITE** for readability
- [ ] **Radio labels**: White text
- [ ] **Dropdown text**: White text (not green)
- [ ] **Input field text**: White text
- [ ] **Sidebar text**: White text
- [ ] **Button text**: Green only (contrast on dark background)
- [ ] **All body text**: White

#### Animation Verification
- [ ] **Matrix Rain**: Falling 0s and 1s in green
- [ ] Animation covers full viewport
- [ ] Animation is behind content (z-index: -1)
- [ ] Symbols are visible and crisp
- [ ] Frame rate is smooth (33ms default)
- [ ] Adjustable speed: slow, normal, fast
- [ ] Adjustable font size (16px default)

#### Interactive Elements
- [ ] **Checkboxes**: Green border, semi-transparent green when checked
- [ ] **Sliders**: Green track and thumb
- [ ] **Expanders**: Green border with glow effect
- [ ] **Radio buttons**: Green border and fill when selected

#### Transparency Check
- [ ] Content blocks semi-transparent (see animation behind)
- [ ] Background opacity: 60% default (adjustable)
- [ ] Content opacity: 80% default (adjustable)
- [ ] Sidebar opacity: 90% default (adjustable)

---

### Theme 4: Cyberpunk 2077
**Purpose:** Neon yellow/magenta aesthetic with vibrant glow effects

#### Color Verification
- [ ] Main background: Deep blue (#0A0E27) with transparency
- [ ] Sidebar: Lighter blue with transparency
- [ ] Primary text: Bright off-white (#E0E0E0 or #FFFFFF)
- [ ] Primary accent: Neon yellow (#FFFF00)
- [ ] Secondary accent: Neon magenta (#FF00FF)

#### Critical Text Readability
**CRITICAL**: All text must be bright white/off-white
- [ ] **All body text**: White or bright off-white
- [ ] **Radio labels**: White
- [ ] **Dropdown text**: White (not yellow)
- [ ] **Input text**: White
- [ ] **Tooltips**: Yellow text OK (short text)

#### Glow Effects
- [ ] **Buttons**: Yellow glow on hover
- [ ] **Borders**: Magenta/yellow neon glow
- [ ] **Interactive elements**: Glow feedback on hover

#### Animation Verification
- [ ] **Particle System**: Yellow/magenta/cyan particles
- [ ] Particles float smoothly across screen
- [ ] Particles have glow effect
- [ ] Animation visible through transparent background
- [ ] Particle count: ~40 (adjustable)

#### Interactive Elements
- [ ] **Checkboxes**: Magenta border, yellow when checked
- [ ] **Sliders**: Yellow track, magenta accents
- [ ] **Buttons**: Semi-transparent yellow with glow
- [ ] **Expanders**: Magenta border, yellow hover

---

### Theme 5: Nord Arctic
**Purpose:** Cool, minimalist theme inspired by Arctic landscapes

#### Color Verification
- [ ] Main background: Dark gray (#2E3440)
- [ ] Sidebar: Slightly lighter gray (#3B4252)
- [ ] Primary text: Bright white (#ECEFF4)
- [ ] Primary accent: Frost blue (#88C0D0)
- [ ] Buttons: Light blue (#88C0D0) with dark text

#### Aesthetic Check
- [ ] Cool, calming color palette
- [ ] High readability with white text
- [ ] Subtle, professional appearance
- [ ] No harsh contrasts

#### Interactive Elements
- [ ] **Checkboxes**: Gray border, blue when checked
- [ ] **Sliders**: Blue track and thumb
- [ ] **Radio buttons**: Blue when selected
- [ ] **Expanders**: Gray background with blue border on hover

#### Charts
- [ ] Chart colors: Blues and aurora colors (blue/teal/green/amber)
- [ ] Chart background matches theme
- [ ] Grid lines subtle and gray

#### Animation
- [ ] **No animation** by default (clean, minimal)
- [ ] Animation toggle should be disabled

---

### Theme 6: Solarized Dark
**Purpose:** Classic Solarized color scheme, popular for coding

#### Color Verification
- [ ] Main background: Solarized base03 (#002B36)
- [ ] Sidebar: Solarized base02 (#073642)
- [ ] Primary text: Solarized base1 (#93A1A1)
- [ ] Primary accent: Solarized blue (#268BD2)
- [ ] Secondary accent: Cyan (#2AA198)

#### Aesthetic Check
- [ ] Distinctive solarized palette
- [ ] Low contrast but readable
- [ ] Comfortable for extended use
- [ ] Monospace font (Source Code Pro)

#### Interactive Elements
- [ ] **Checkboxes**: Gray border, blue when checked
- [ ] **Sliders**: Blue track
- [ ] **Buttons**: Blue background with cream text
- [ ] **Radio buttons**: Blue when selected

#### Charts
- [ ] Chart colors: Official Solarized accent colors
- [ ] Colors: Blue, cyan, green, yellow, orange, red, magenta, violet

---

## Universal Testing Checklist
**Test these in ALL themes:**

### Text Readability
- [ ] All body text is easily readable
- [ ] Headings stand out from body text
- [ ] Labels are visible and clear
- [ ] Tooltips are readable

### Interactive Elements
- [ ] **Buttons** have clear hover states
- [ ] **Radio buttons** show selection clearly
- [ ] **Checkboxes** show checked state clearly
- [ ] **Dropdowns** open with readable options
- [ ] **Sliders** have visible track and thumb
- [ ] **Text inputs** accept input with visible text
- [ ] **Number inputs** have working up/down buttons

### Navigation
- [ ] **Sidebar** is readable and navigable
- [ ] **Hamburger menu** (if collapsed) is visible and functional
- [ ] **Page transitions** maintain theme
- [ ] **Expanders** open/close smoothly

### Charts (Plotly)
- [ ] **Chart backgrounds** match theme
- [ ] **Chart text** (titles, labels, legends) is readable
- [ ] **Grid lines** are visible but not distracting
- [ ] **Series colors** are distinct and harmonious
- [ ] **Tooltips** on hover are readable

### Feedback Elements
- [ ] **Success messages** are visible (green checkmark)
- [ ] **Error messages** are visible (red X)
- [ ] **Warning messages** are visible (yellow triangle)
- [ ] **Info messages** are visible (blue i)

### Layout
- [ ] **Margins** are appropriate
- [ ] **Padding** around elements is sufficient
- [ ] **Borders** are visible where expected
- [ ] **Shadows** provide depth without distraction

---

## Animation-Specific Testing

### Matrix Rain Animation
**Themes:** Matrix AI

#### Startup
- [ ] Animation starts immediately when theme applied
- [ ] Covers full viewport (no gaps)
- [ ] Appears behind all content

#### Performance
- [ ] Smooth frame rate (no stuttering)
- [ ] CPU usage reasonable (check Task Manager)
- [ ] No memory leaks (check over 5+ minutes)

#### Customization
- [ ] **Speed slider** changes animation speed
  - [ ] Slow: Symbols fall slowly
  - [ ] Normal: Default speed
  - [ ] Fast: Rapid symbol fall
  - [ ] Off: Animation stops
- [ ] **Font size slider** changes symbol size
  - [ ] Smaller: More columns, denser
  - [ ] Larger: Fewer columns, sparser
- [ ] **Density** (if exposed): Adjusts column count

#### Cleanup
- [ ] Switching to another theme removes animation
- [ ] No lingering canvas elements
- [ ] No console errors about missing canvas

### Particle System Animation
**Themes:** Cyberpunk, Dark (optional)

#### Startup
- [ ] Particles appear immediately
- [ ] Particles float across screen
- [ ] Particles are behind content

#### Appearance
- [ ] **Cyberpunk**: Yellow/magenta/cyan particles with glow
- [ ] **Dark**: Subtle red particles
- [ ] Particles have varying opacity
- [ ] Glow effect visible

#### Performance
- [ ] Smooth motion (60fps ideal)
- [ ] Reasonable CPU usage
- [ ] No lag or stuttering

#### Customization
- [ ] **Speed** affects particle velocity
- [ ] **Count** (if exposed) adjusts particle number
- [ ] Toggle on/off works correctly

#### Cleanup
- [ ] Switching themes removes particles
- [ ] No orphaned canvas elements

---

## Common Issues & Solutions

### Issue: Text is Hard to Read
**Symptoms:** Low contrast, hard to see labels, buttons blend in  
**Check:**
- Theme text_color setting
- Element-specific color overrides
- CSS specificity (may need !important)

**Solution:** Verify ElementStyle.color for that element, ensure high contrast

### Issue: Animation Not Appearing
**Symptoms:** No Matrix rain or particles visible  
**Check:**
- Animation toggle in Settings
- Browser console for JavaScript errors
- Canvas element in DOM (F12 → Elements)

**Solution:**
- Enable animation in Settings
- Check z-index (should be -1)
- Verify canvas injection script ran

### Issue: Animation Visible in Front of Content
**Symptoms:** Symbols/particles cover text and buttons  
**Check:**
- Canvas z-index
- Canvas CSS position

**Solution:**
- Canvas should have `z-index: -1 !important`
- Canvas should be `position: fixed`

### Issue: Theme Not Applying
**Symptoms:** Old theme colors remain after switching  
**Check:**
- Session state updated
- Page refreshed
- CSS injection ran

**Solution:**
- Click "Apply Theme Now" button
- Manually refresh page (F5)
- Check browser console for errors

### Issue: Custom Colors Not Working
**Symptoms:** Custom color picker doesn't affect theme  
**Check:**
- "Enable Custom Colors" checkbox checked
- Custom colors saved in session state
- CSS generation uses custom_colors parameter

**Solution:**
- Verify checkbox is enabled
- Re-apply theme after setting colors
- Check apply_theme() receives custom_colors dict

### Issue: Dropdown Text Invisible
**Symptoms:** Can't read options in selectbox  
**Check:**
- Selectbox ElementStyle.color
- Dropdown list background color
- Text contrast ratio

**Solution:**
- Ensure dropdown background contrasts with text
- Check [role="option"] CSS rules
- Verify text-shadow not hiding text

### Issue: Slider Not Visible
**Symptoms:** Can't see slider track or thumb  
**Check:**
- Slider ElementStyle colors
- Theme-specific slider CSS
- Background transparency

**Solution:**
- Verify slider.active_color is visible
- Check track background color
- Ensure thumb contrasts with track

---

## Regression Testing
**After any theme changes, run this quick checklist:**

1. [ ] Default theme is 'light' on first launch
2. [ ] Theme persists across page reloads
3. [ ] All 6 themes are selectable
4. [ ] Theme preview shows correct colors
5. [ ] Apply button triggers theme change
6. [ ] Animations start/stop correctly
7. [ ] No console errors when switching themes
8. [ ] Plotly charts match theme colors
9. [ ] Settings page is fully functional
10. [ ] User preferences save correctly

---

## Browser Compatibility
**Test on these browsers:**

- [ ] **Chrome** (latest)
- [ ] **Firefox** (latest)
- [ ] **Edge** (latest)
- [ ] **Safari** (if on Mac)

**Known Limitations:**
- Some CSS features may not work in older browsers
- Animations require HTML5 Canvas support
- Custom fonts require internet connection for Google Fonts

---

## Performance Benchmarks

### Expected Performance

#### Light/Dark/Nord/Solarized (No Animation)
- **FPS:** 60 (capped by Streamlit)
- **CPU:** < 5% idle, < 20% during interaction
- **Memory:** Stable, no leaks

#### Matrix Animation
- **FPS:** 30-60 (depending on speed setting)
- **CPU:** < 15% idle, < 30% during interaction
- **Memory:** Stable, canvas reuses memory

#### Particle Animation
- **FPS:** 60
- **CPU:** < 10% idle, < 25% during interaction
- **Memory:** Stable

### Red Flags
- **Stuttering:** Animation frame drops, choppy motion
- **High CPU:** > 40% CPU when idle
- **Memory Leak:** Memory increases continuously over time
- **Slow Page Load:** > 3 seconds to render page

If experiencing red flags:
1. Reduce animation speed or disable
2. Lower particle count or font size
3. Check for browser extensions interfering
4. Update browser to latest version

---

## Test Report Template

```markdown
## Theme Test Report
**Date:** [Date]
**Tester:** [Your Name]
**Browser:** [Browser Name/Version]
**OS:** [Windows/Mac/Linux]

### Themes Tested
- [ ] Light Mode
- [ ] Dark Mode
- [ ] Matrix AI
- [ ] Cyberpunk 2077
- [ ] Nord Arctic
- [ ] Solarized Dark

### Issues Found
| Theme | Issue | Severity | Screenshot |
|-------|-------|----------|------------|
| [Theme name] | [Description] | [High/Med/Low] | [Link] |

### Passed Tests
[List of features/elements that worked correctly]

### Notes
[Any additional observations or comments]
```

---

## Next Steps After Testing

1. **Document Issues:** Use the test report template above
2. **Prioritize Fixes:** High → Medium → Low severity
3. **Update Code:** Fix identified issues in themes.py
4. **Re-test:** Verify fixes don't introduce new issues
5. **Update Docs:** Mark issues as resolved in THEME_AUDIT_DEC26.md

---

## Quick Reference: Theme Files

- **Theme Definitions:** `ui/themes.py` (lines 66-427)
- **Theme Application:** `ui/themes.py` apply_theme() (lines 432-924)
- **Animations:** `ui/animations.py`
- **Dashboard Integration:** `ui/dashboard.py` main() (lines 3411-3423)
- **Settings Page:** `ui/dashboard.py` page_settings() (lines 223-382)

---

## Conclusion

This testing guide ensures all 6 themes are fully functional, visually consistent, and provide excellent user experience. Complete testing helps identify edge cases and ensures the theme system works reliably for all users.

**Happy Testing! 🎨**
