"""
Streamlit Animation System
Provides animated backgrounds for themes (Matrix rain, particle effects, etc.)

Features:
- Matrix-style falling symbols with AI icons and currency
- Particle system animations
- Performance-optimized HTML5 Canvas
- Configurable speed and density
"""

import streamlit as st
import streamlit.components.v1 as components
from typing import Optional, List


def cleanup_animations():
    """Remove all existing animation canvases when switching themes."""
    cleanup_script = """
<script>
(function() {
    try {
        const doc = window.parent.document;
        
        // Remove all animation canvases by ID
        const matrixCanvas = doc.getElementById('matrixCanvas');
        const particleCanvas = doc.getElementById('particleCanvas');
        
        if (matrixCanvas) {
            matrixCanvas.remove();
            console.log('🧹 Removed matrix canvas');
        }
        if (particleCanvas) {
            particleCanvas.remove();
            console.log('🧹 Removed particle canvas');
        }
        
        // Also search for any orphaned canvases with these IDs (backup cleanup)
        const allCanvases = doc.querySelectorAll('canvas[id$="Canvas"]');
        allCanvases.forEach(canvas => {
            if (canvas.id === 'matrixCanvas' || canvas.id === 'particleCanvas') {
                canvas.remove();
                console.log('🧹 Removed orphaned canvas:', canvas.id);
            }
        });
        
        console.log('✅ Animation cleanup complete');
    } catch(error) {
        console.error('❌ Cleanup error:', error);
    }
})();
</script>
"""
    components.html(cleanup_script, height=0, scrolling=False)


def matrix_rain_animation(
    symbols: Optional[List[str]] = None,
    colors: Optional[List[str]] = None,
    speed: str = "normal",
    density: str = "medium",
    glow: bool = True,
    font_size: int = 16
):
    """
    Classic Matrix-style falling rain animation with 0s and 1s.
    
    Args:
        symbols: List of symbols to animate (defaults to 0 and 1)
        colors: List of hex colors for symbols (defaults to neon green)
        speed: Animation speed ('slow', 'normal', 'fast')
        density: Column density ('low', 'medium', 'high')
        glow: Enable glow effect on symbols
        font_size: Size of characters in pixels (default 16)
    """
    
    # NOTE: Removed cleanup script - using unique component key instead
    # The key parameter prevents unnecessary re-creation of the animation
    # while still allowing updates when settings actually change
    
    # Classic Matrix: just 0s and 1s
    if symbols is None:
        symbols = ['0', '1']
    
    # Default colors: Matrix neon green palette
    if colors is None:
        colors = ['#00FF41', '#39FF14', '#00CC33']
    
    # Speed mapping (milliseconds between frames)
    speed_map = {
        'slow': 50,
        'normal': 33,
        'fast': 20,
        'off': 9999
    }
    frame_delay = speed_map.get(speed, 33)
    
    # Density mapping (percentage of screen width)
    density_map = {
        'low': 0.5,
        'medium': 0.8,
        'high': 1.2
    }
    density_multiplier = density_map.get(density, 0.8)
    
    # Convert Python lists to JavaScript arrays
    symbols_js = str(symbols).replace("'", '"')
    colors_js = str(colors).replace("'", '"')
    
    html_code = f"""
<script>
(function() {{
    try {{
        console.log('🔍 Matrix animation script started');
        
        // Access parent document
        const doc = window.parent.document;
        console.log('📄 Parent document accessed:', doc ? 'SUCCESS' : 'FAILED');
        
        // CLEANUP: Remove particle canvas if it exists (from other themes)
        const oldParticleCanvas = doc.getElementById('particleCanvas');
        if (oldParticleCanvas) {{
            oldParticleCanvas.remove();
            console.log('🧹 Removed old particle canvas');
        }}
        
        // Get or create matrix canvas
        let canvas = doc.getElementById('matrixCanvas');
        
        // Create canvas if it doesn't exist
        if (!canvas) {{
            console.log('➕ Creating new matrix canvas');
            canvas = doc.createElement('canvas');
            canvas.id = 'matrixCanvas';
            canvas.style.cssText = 'position:fixed!important;top:0!important;left:0!important;right:0!important;bottom:0!important;width:100vw!important;height:100vh!important;max-width:100vw!important;max-height:100vh!important;z-index:-1!important;pointer-events:none!important;margin:0!important;padding:0!important;border:none!important;';
            // Insert at beginning of body to ensure it's truly behind everything
            doc.body.insertBefore(canvas, doc.body.firstChild);
            console.log('✅ Canvas appended to body');
        }} else {{
            console.log('♻️  Reusing existing matrix canvas');
        }}
        
        canvas.setAttribute('data-matrix-active', 'true');
        const ctx = canvas.getContext('2d');
        
        // Set canvas size IMMEDIATELY to full document dimensions
        const fullWidth = Math.max(window.parent.innerWidth, doc.documentElement.clientWidth, doc.body.clientWidth);
        const fullHeight = Math.max(window.parent.innerHeight, doc.documentElement.clientHeight, doc.body.clientHeight);
        canvas.width = fullWidth;
        canvas.height = fullHeight;
        console.log('🎬 Matrix rain animation initialized - Canvas:', canvas.width, 'x', canvas.height, '(Window:', window.parent.innerWidth, 'x', window.parent.innerHeight, ')');

    // Configuration
    const symbols = {symbols_js};
    const colors = {colors_js};
    const fontSize = {font_size};
    const columnWidth = fontSize;
    
    // Calculate columns to exactly fill the canvas width
    let columns = Math.ceil(canvas.width / columnWidth);
    let drops = Array(columns).fill(1);
    let columnColors = Array(columns).fill(0).map(() => 
        colors[Math.floor(Math.random() * colors.length)]
    );
    console.log('📊 Matrix columns calculated:', columns, 'for width:', canvas.width, '(columnWidth:', columnWidth, 'coverage:', columns * columnWidth, 'px)');

    // Set canvas size to full document dimensions
    function resizeCanvas() {{
        const width = Math.max(window.parent.innerWidth, doc.documentElement.clientWidth, doc.body.clientWidth);
        const height = Math.max(window.parent.innerHeight, doc.documentElement.clientHeight, doc.body.clientHeight);
        if (canvas.width !== width || canvas.height !== height) {{
            canvas.width = width;
            canvas.height = height;
            console.log('📐 Matrix canvas resized:', canvas.width, 'x', canvas.height);
            // Recalculate columns to exactly fill the canvas width
            const newColumns = Math.ceil(canvas.width / columnWidth);
            if (newColumns !== columns) {{
                columns = newColumns;
                drops = Array(columns).fill(1);
                columnColors = Array(columns).fill(0).map(() => 
                    colors[Math.floor(Math.random() * colors.length)]
                );
                console.log('📊 Matrix columns recalculated:', columns, 'for width:', canvas.width, 'coverage:', columns * columnWidth, 'px');
            }}
        }}
    }}
    resizeCanvas();
    window.parent.addEventListener('resize', resizeCanvas);
    // Also check on scroll in case viewport changes
    setInterval(resizeCanvas, 1000);

// Animation function
function draw() {{
    // Semi-transparent fade effect (creates trailing effect while staying transparent)
    ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Draw characters
    ctx.font = fontSize + 'px monospace';
    
    for (let i = 0; i < drops.length; i++) {{
        // Random symbol from array
        const symbol = symbols[Math.floor(Math.random() * symbols.length)];
        
        // Column color (neon green)
        ctx.fillStyle = columnColors[i];
        
        // Glow effect
        {'ctx.shadowBlur = 15; ctx.shadowColor = columnColors[i];' if glow else 'ctx.shadowBlur = 0;'}
        
        // Draw symbol
        const x = i * columnWidth;
        const y = drops[i] * fontSize;
        ctx.fillText(symbol, x, y);
        
        // Reset shadow
        ctx.shadowBlur = 0;
        
        // Random reset (creates varying column lengths)
        if (y > canvas.height && Math.random() > 0.975) {{
            drops[i] = 0;
            // Occasionally change column color
            if (Math.random() > 0.95) {{
                columnColors[i] = colors[Math.floor(Math.random() * colors.length)];
            }}
        }}
        
        // Move drop down
        drops[i]++;
    }}
}}

// Animation loop
let frameCount = 0;
setInterval(() => {{
    draw();
    frameCount++;
    if (frameCount === 10) {{
        console.log('🎨 Drawing frame 10 - columns:', columns, 'drops:', drops.slice(0, 3));
    }}
}}, {frame_delay});
console.log('🔄 Animation loop started with interval:', {frame_delay}, 'ms');

// Handle visibility change (pause when tab not visible)
document.addEventListener('visibilitychange', function() {{
    if (document.hidden) {{
        // Pause animation when tab is hidden
    }} else {{
        // Resume animation
    }}
}});
console.log('👁️  Visibility handler attached');
}} catch(error) {{
    console.error('❌ Matrix animation error:', error);
}}
}})();
</script>
"""
    
    # Use components.html to inject the animation
    # Canvas detection logic in JavaScript prevents duplicate creation
    components.html(html_code, height=0, scrolling=False)


def particle_system_animation(
    particle_count: int = 50,
    colors: Optional[List[str]] = None,
    speed: str = "normal"
):
    """
    Floating particle system animation.
    
    Args:
        particle_count: Number of particles (10-200)
        colors: Particle colors (defaults to theme accent colors)
        speed: Particle speed ('slow', 'normal', 'fast')
    """
    
    if colors is None:
        colors = ['#00FF41', '#39FF14', '#00FFFF']
    
    # Speed multiplier
    speed_map = {'slow': 0.5, 'normal': 1.0, 'fast': 2.0}
    speed_mult = speed_map.get(speed, 1.0)
    
    # NOTE: Removed cleanup script - using unique component key instead
    # The key parameter prevents unnecessary re-creation of the animation
    
    colors_js = str(colors).replace("'", '"')
    
    html_code = f"""
<script>
(function() {{
    try {{
        console.log('🔍 Particle animation script started');
        
        // Access parent document
        const doc = window.parent.document;
        
        // CLEANUP: Remove matrix canvas if it exists (from other themes)
        const oldMatrixCanvas = doc.getElementById('matrixCanvas');
        if (oldMatrixCanvas) {{
            oldMatrixCanvas.remove();
            console.log('🧹 Removed old matrix canvas');
        }}
        
        // Get or create particle canvas
        let canvas = doc.getElementById('particleCanvas');
        
        // Create canvas if it doesn't exist
        if (!canvas) {{
            console.log('➕ Creating new particle canvas');
            canvas = doc.createElement('canvas');
            canvas.id = 'particleCanvas';
            canvas.style.cssText = 'position:fixed!important;top:0!important;left:0!important;right:0!important;bottom:0!important;width:100vw!important;height:100vh!important;max-width:100vw!important;max-height:100vh!important;z-index:-1!important;pointer-events:none!important;margin:0!important;padding:0!important;border:none!important;';
            // Insert at beginning of body to ensure it's truly behind everything
            doc.body.insertBefore(canvas, doc.body.firstChild);
            console.log('✅ Particle canvas appended to body');
        }} else {{
            console.log('♻️  Reusing existing particle canvas');
        }}
        
        canvas.setAttribute('data-particles-active', 'true');
        const ctx = canvas.getContext('2d');
        
        // Set canvas size IMMEDIATELY to full document dimensions
        const fullWidth = Math.max(window.parent.innerWidth, doc.documentElement.clientWidth, doc.body.clientWidth);
        const fullHeight = Math.max(window.parent.innerHeight, doc.documentElement.clientHeight, doc.body.clientHeight);
        canvas.width = fullWidth;
        canvas.height = fullHeight;
        console.log('🎬 Particle animation initialized - Canvas:', canvas.width, 'x', canvas.height, '(Window:', window.parent.innerWidth, 'x', window.parent.innerHeight, ')');

// Add resize listener to keep canvas full-size
window.parent.addEventListener('resize', () => {{
    const newWidth = Math.max(window.parent.innerWidth, doc.documentElement.clientWidth, doc.body.clientWidth);
    const newHeight = Math.max(window.parent.innerHeight, doc.documentElement.clientHeight, doc.body.clientHeight);
    canvas.width = newWidth;
    canvas.height = newHeight;
    console.log('📐 Particle canvas resized:', canvas.width, 'x', canvas.height);
}});

const colors = {colors_js};
const particleCount = {particle_count};
const speedMultiplier = {speed_mult};

class Particle {{
    constructor() {{
        this.reset();
    }}
    
    reset() {{
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.vx = (Math.random() - 0.5) * 2 * speedMultiplier;
        this.vy = (Math.random() - 0.5) * 2 * speedMultiplier;
        this.radius = Math.random() * 3 + 1;
        this.color = colors[Math.floor(Math.random() * colors.length)];
        this.opacity = Math.random() * 0.5 + 0.2;
    }}
    
    update() {{
        this.x += this.vx;
        this.y += this.vy;
        
        // Bounce off edges
        if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
        if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
        
        // Keep in bounds
        this.x = Math.max(0, Math.min(canvas.width, this.x));
        this.y = Math.max(0, Math.min(canvas.height, this.y));
    }}
    
    draw() {{
        ctx.globalAlpha = this.opacity;
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fill();
        
        // Glow effect
        ctx.shadowBlur = 10;
        ctx.shadowColor = this.color;
        ctx.fill();
        ctx.shadowBlur = 0;
        
        ctx.globalAlpha = 1;
    }}
}}

// Create particles
const particles = Array(particleCount).fill(0).map(() => new Particle());

// Animation loop
function animate() {{
    ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    particles.forEach(particle => {{
        particle.update();
        particle.draw();
    }});
    
    requestAnimationFrame(animate);
}}

animate();
console.log('✅ Particle animation loop started');
}} catch(error) {{
    console.error('❌ Particle animation error:', error);
}}
}})();
</script>
"""
    
    # Use components.html to inject the particle animation
    # Canvas detection logic in JavaScript prevents duplicate creation
    components.html(html_code, height=0, scrolling=False)


def apply_animation(theme_id: str, animation_enabled: bool = True, speed: str = "normal", matrix_font_size: int = 16):
    """
    Apply appropriate animation for the selected theme.
    
    Args:
        theme_id: Theme identifier (e.g., 'matrix', 'cyberpunk')
        animation_enabled: Whether to enable animation
        speed: Animation speed setting
        matrix_font_size: Font size for Matrix rain animation
    """
    
    if not animation_enabled or speed == "off":
        # If animations disabled, cleanup all canvases
        cleanup_animations()
        return
    
    # Theme-specific animations (each handles its own cleanup)
    if theme_id == "matrix":
        matrix_rain_animation(speed=speed, density="medium", glow=True, font_size=matrix_font_size)
    
    elif theme_id == "cyberpunk":
        # Cyberpunk: Yellow/Magenta particles
        particle_system_animation(
            particle_count=40,
            colors=['#FFFF00', '#FF00FF', '#00FFFF', '#FF6600'],
            speed=speed
        )
    
    elif theme_id == "dark":
        # Subtle particle effect for dark theme
        particle_system_animation(
            particle_count=20,
            colors=['#FF4B4B', '#FF6B6B', '#FFB4B4'],
            speed=speed
        )


def get_animation_config(theme_id: str) -> dict:
    """
    Get default animation configuration for theme.
    
    Returns:
        Dictionary with animation settings
    """
    configs = {
        "matrix": {
            "type": "matrix_rain",
            "enabled_by_default": True,
            "supports_speed": True,
            "supports_density": True,
            "description": "Classic Matrix rain with falling 0s and 1s in neon green"
        },
        "cyberpunk": {
            "type": "particle_system",
            "enabled_by_default": True,
            "supports_speed": True,
            "supports_density": False,
            "description": "Floating neon particles with glow effect"
        },
        "dark": {
            "type": "particle_system",
            "enabled_by_default": False,
            "supports_speed": True,
            "supports_density": False,
            "description": "Subtle floating particles"
        },
        "light": {
            "type": "none",
            "enabled_by_default": False,
            "supports_speed": False,
            "supports_density": False,
            "description": "No animation"
        },
        "nord": {
            "type": "none",
            "enabled_by_default": False,
            "supports_speed": False,
            "supports_density": False,
            "description": "No animation"
        },
        "solarized": {
            "type": "none",
            "enabled_by_default": False,
            "supports_speed": False,
            "supports_density": False,
            "description": "No animation"
        },
    }
    
    return configs.get(theme_id, {
        "type": "none",
        "enabled_by_default": False,
        "supports_speed": False,
        "supports_density": False,
        "description": "No animation available"
    })
