import streamlit as st
import numpy as np
import soundfile as sf
import io
from pathlib import Path

# Set up clean web page configurations
st.set_page_config(page_title="WAV False Stereo Splitter", page_icon="🎵", layout="centered")

st.title("🎵 WAV False Stereo Splitter")
st.write("Upload your stereo WAV stems. Our cross-correlation engine will analyze them, ignore dither/phase offsets, and let you download clean true mono copies.")

# 1. Detection Sensitivity Option
mode = st.radio(
    "Select Detection Sensitivity:",
    ("Smart Cross-Correlation Mode (Recommended)", "Strict Mode (100% Bit-for-Bit Identical)")
)

# 2. File Upload Box
uploaded_files = st.file_uploader("Drag & Drop your WAV files here", type=["wav"], accept_multiple_files=True)

if uploaded_files:
    st.write(f"### 📊 Processing Queue ({len(uploaded_files)} files loaded)")
    
    for uploaded_file in uploaded_files:
        filename = uploaded_file.name
        st.write(f"**Analyzing:** {filename}")
        
        try:
            # Read file data directly from web browser memory buffer
            file_bytes = uploaded_file.read()
            data, sample_rate = sf.read(io.BytesIO(file_bytes), always_2d=True)
            subtype = sf.info(io.BytesIO(file_bytes)).subtype
            
            if data.shape[1] < 2:
                st.info(f"ℹ️ {filename} is already a single-channel mono file.")
                continue
                
            left_channel = data[:, 0]
            right_channel = data[:, 1]
            is_mono_match = False
            
            if mode == "Strict Mode (100% Bit-for-Bit Identical)":
                is_mono_match = np.array_equal(left_channel, right_channel)
            else:
                # Core Cross-Correlation Math Engine
                num_samples = len(left_channel)
                start_s = max(0, num_samples // 4)
                end_s = min(num_samples, start_s + (sample_rate * 20))
                
                L = left_channel[start_s:end_s]
                R = right_channel[start_s:end_s]
                
                if np.max(np.abs(L)) > 0.0001 and np.max(np.abs(R)) > 0.0001:
                    correlation_matrix = np.corrcoef(L, R)
                    if correlation_matrix[0, 1] > 0.995:
                        is_mono_match = True
                else:
                    is_mono_match = np.array_equal(left_channel, right_channel)
            
            if is_mono_match:
                st.success(f"✅ MATCH: False Stereo detected in {filename}!")
                
                # Write mono file directly into virtual cloud RAM memory buffer
                mono_buffer = io.BytesIO()
                sf.write(mono_buffer, left_channel, sample_rate, format='WAV', subtype=subtype)
                mono_buffer.seek(0)
                
                # Render clean web interface button for the user to grab their file
                st.download_button(
                    label=f"⬇️ Download Mono {filename}",
                    data=mono_buffer,
                    file_name=f"{Path(filename).stem}_mono.wav",
                    mime="audio/wav",
                    key=filename
                )
            else:
                st.error(f"❌ SKIPPED: {filename} contains True Stereo data.")
                
        except Exception as e:
            st.error(f"⚠️ Error reading {filename}: {str(e)}")

st.write("---")
st.caption("Built with AI • Open Source & Free to modify on GitHub.")
