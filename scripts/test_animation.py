"""Manual Streamlit check for Matrix animation rendering."""
import streamlit as st
from ui.animations import matrix_rain_animation

st.set_page_config(page_title="Animation Test", layout="wide")

st.title("🎬 Matrix Animation Test")

st.write("If the animation is working, you should see falling 0s and 1s in neon green behind this text.")

# Apply Matrix rain
matrix_rain_animation(speed="normal", density="medium", glow=True)

st.markdown("---")

st.write("### Debug Info:")
st.write("- Animation function called: ✅")
st.write("- Theme: Matrix")
st.write("- Speed: normal")
st.write("- Density: medium")
st.write("- Glow: enabled")

st.markdown("---")

st.info("Open browser console (F12) and look for: '🎬 Matrix rain animation initialized'")
