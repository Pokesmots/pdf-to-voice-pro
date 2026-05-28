import streamlit as st
import os
import re
import math
from pypdf import PdfReader
import edge_tts
import asyncio

# ==============================================================================
# SECTION 1: APP CONFIGURATION & STYLING
# ==============================================================================
st.set_page_config(
    page_title="PDF to Voice Pro",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Dark Theme and Amazon Gear Cards
st.markdown("""
<style>
    .main .block-container { max-width: 1200px; padding-top: 2rem; }
    div.stButton > button:first-child {
        background-color: #00c6ff; color: #111; font-weight: bold; border: none; width: 100%;
    }
    div.stButton > button:first-child:hover {
        background-color: #0072ff; color: #fff;
    }
    .gear-card {
        background-color: #1e222b; 
        padding: 20px; 
        border-radius: 8px; 
        border: 1px solid #262730; 
        text-align: center; 
        height: 280px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# SECTION 2: AUDIO PROCESSING HELPER FUNCTIONS
# ==============================================================================
def clean_extracted_text(text):
    """Cleans whitespace, line breaks, and formatting from PDF text."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(?<=\s)[•*-]\s+', '', text)
    return text.strip()

def split_text_into_chunks(text, max_chars=1500):
    """Splits text intelligently at sentence boundaries to respect API limits."""
    if not text:
        return []
    
    # Sentence boundary split regex
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        if current_length + len(sentence) + 1 > max_chars:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_length = len(sentence)
        else:
            current_chunk.append(sentence)
            current_length += len(sentence) + 1
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks

async def generate_chunk_audio(text, voice_id, output_path):
    """Asynchronously generates an MP3 file for a single text chunk."""
    communicate = edge_tts.Communicate(text, voice_id)
    await communicate.save(output_path)

# ==============================================================================
# SECTION 3: HEADER & APP INTRODUCTION
# ==============================================================================
st.title("🎙️ PDF to Voice Pro")
st.subheader("Convert your multi-page documents into studio-quality audio guides instantly.")
st.write("A 100% free, privacy-first open-source utility with zero subscription paywalls, no character limits, and no registration required.")

# ==============================================================================
# SECTION 4: VOICE SELECTION & LANGUAGE SETTINGS
# ==============================================================================
st.write("---")
st.markdown("### 🎙️ 1. Choose Voice Profile & Language")

# Dictionary of available premium edge-tts voices
AVAILABLE_VOICES = {
    "English (US) - Guy (Neural Male)": "en-US-GuyNeural",
    "English (US) - Ava (Neural Female)": "en-US-AvaNeural",
    "English (UK) - Ryan (Neural Male)": "en-GB-RyanNeural",
    "English (UK) - Sonia (Neural Female)": "en-GB-SoniaNeural",
    "Spanish (ES) - Alvaro (Neural Male)": "es-ES-AlvaroNeural",
    "Spanish (ES) - Elvira (Neural Female)": "es-ES-ElviraNeural",
    "French (FR) - Henri (Neural Male)": "fr-FR-HenriNeural",
    "French (FR) - Denise (Neural Female)": "fr-FR-DeniseNeural"
}

voice_selection = st.selectbox(
    "Select an AI Voice Talent:",
    options=list(AVAILABLE_VOICES.keys()),
    index=0
)
selected_voice_id = AVAILABLE_VOICES[voice_selection]

# ==============================================================================
# SECTION 5: FILE UPLOAD INTERFACE
# ==============================================================================
st.markdown("### 📄 2. Upload PDF Document")
uploaded_file = st.file_uploader("Drag and drop your PDF file here (Books, research papers, or study guides)", type=["pdf"])

# ==============================================================================
# SECTION 6: MAIN AUDIO GENERATION WORKFLOW
# ==============================================================================
if uploaded_file is not None:
    st.success(f"Successfully loaded: **{uploaded_file.name}**")
    
    # Read and extract PDF pages
    pdf_reader = PdfReader(uploaded_file)
    total_pages = len(pdf_reader.pages)
    
    st.info(f"Detected **{total_pages}** document pages. Extracting content...")
    
    full_raw_text = ""
    for page_num in range(total_pages):
        page_text = pdf_reader.pages[page_num].extract_text()
        if page_text:
            full_raw_text += page_text + " "
            
    cleaned_text = clean_extracted_text(full_raw_text)
    total_chars = len(cleaned_text)
    
    if total_chars == 0:
        st.error("Could not extract any structural text from this PDF. Please verify it isn't an un-scanned graphical image document.")
    else:
        st.metric(label="Total Processable Characters", value=f"{total_chars:,}")
        
        # Split text into manageable payload pieces
        text_chunks = split_text_into_chunks(cleaned_text, max_chars=1800)
        total_chunks = len(text_chunks)
        
        st.markdown("### ⚡ 3. Compile Master Audio File")
        st.write(f"The text has been formatted into **{total_chunks} optimized chunks** for high-speed streaming processing.")
        
        if st.button("Generate MP3 Audio Guide"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Temporary storage lists
            chunk_files = []
            compiled_success = True
            
            # Run asynchronous edge-tts operations
            for i, chunk in enumerate(text_chunks):
                status_text.write(f"Processing audio packet **{i+1}/{total_chunks}**...")
                temp_filename = f"chunk_{i}.mp3"
                
                try:
                    asyncio.run(generate_chunk_audio(chunk, selected_voice_id, temp_filename))
                    chunk_files.append(temp_filename)
                except Exception as e:
                    st.error(f"Processing error on fragment {i+1}: {str(e)}")
                    compiled_success = False
                    break
                    
                # Update visual progress tracking
                progress_bar.progress(int(((i + 1) / total_chunks) * 100))
            
            if compiled_success and chunk_files:
                master_output_filename = "PDF_to_Voice_Pro_Master.mp3"
                status_text.write("Assembling voice master track...")
                
                try:
                    # Merge all temporary chunk audio files into a single master MP3
                    with open(master_output_filename, "wb") as master_file:
                        for temp_file in chunk_files:
                            with open(temp_file, "rb") as f:
                                master_file.write(f.read())
                    
                    st.success("🎉 Master Audio Guide Compiled Successfully!")
                    
                    # Read back generated file to present layout player and download button
                    with open(master_output_filename, "rb") as final_audio:
                        audio_bytes = final_audio.read()
                        
                        st.audio(audio_bytes, format="audio/mp3")
                        st.download_button(
                            label="⬇️ Download Full Master MP3 Guide",
                            data=audio_bytes,
                            file_name=f"{os.path.splitext(uploaded_file.name)[0]}_audio.mp3",
                            mime="audio/mp3"
                        )
                except Exception as merge_error:
                    st.error(f"Error compiling master output file track assembly: {str(merge_error)}")
                finally:
                    # Clean up local temporary scratch files to free browser/server memory
                    for temp_file in chunk_files:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    if os.path.exists(master_output_filename):
                        os.remove(master_output_filename)
            else:
                st.error("Audio conversion failed during step compilation tracking pipeline updates.")

# ==============================================================================
# SECTION 7: FILE MANAGEMENT & MANAGEMENT UTILITIES (END)
# ==============================================================================

# --- NEW MONETIZATION SECTION: AMAZON ASSOCIATES NATIVE GEAR HUB ---
st.write("---")
st.markdown("### 🎒 Essential Study & Commute Gear")
st.caption("Disclaimer: As an Amazon Associate, PDF to Voice Pro earns a small commission from qualifying purchases at no extra cost to you. Helps keep our open-source servers completely free! ☕")

gear_col1, gear_col2, gear_col3 = st.columns(3)

with gear_col1:
    st.markdown("""
    <div class="gear-card">
        <div>
            <span style="font-size: 32px;">🎧</span>
            <h4 style="margin: 10px 0; color: #00c6ff;">Soundcore by Anker Life Q30</h4>
            <p style="font-size: 13px; color: #8a99ad; line-height: 1.4;">The absolute gold standard for budget active noise-canceling headphones. Block out loud libraries or loud traffic commutes.</p>
        </div>
        <a href="https://amzn.to/4dxfJ5K" target="_blank" style="display: block; background: #FF9900; color: #111; padding: 10px; border-radius: 5px; font-weight: bold; text-decoration: none; font-size: 14px;">View Deal on Amazon ➔</a>
    </div>
    """, unsafe_allow_html=True)

with gear_col2:
    st.markdown("""
    <div class="gear-card">
        <div>
            <span style="font-size: 32px;">🔋</span>
            <h4 style="margin: 10px 0; color: #00c6ff;">Anker Prime Power Bank</h4>
            <p style="font-size: 13px; color: #8a99ad; line-height: 1.4;">20,000mAh, 220W high-capacity portable charger. Keeps your phones or tablets fully powered up on long campus days or work shifts.</p>
        </div>
        <a href="https://amzn.to/3PsFc7h" target="_blank" style="display: block; background: #FF9900; color: #111; padding: 10px; border-radius: 5px; font-weight: bold; text-decoration: none; font-size: 14px;">View Deal on Amazon ➔</a>
    </div>
    """, unsafe_allow_html=True)

with gear_col3:
    st.markdown("""
    <div class="gear-card">
        <div>
            <span style="font-size: 32px;">💻</span>
            <h4 style="margin: 10px 0; color: #00c6ff;">Lamicall Foldable Stand</h4>
            <p style="font-size: 13px; color: #8a99ad; line-height: 1.4;">Premium adjustable aluminum laptop and tablet stand. Folds flat to fit in your backpack for a perfectly ergonomic study setup anywhere.</p>
        </div>
        <a href="https://amzn.to/3PwJ3Ad" target="_blank" style="display: block; background: #FF9900; color: #111; padding: 10px; border-radius: 5px; font-weight: bold; text-decoration: none; font-size: 14px;">View Deal on Amazon ➔</a>
    </div>
    """, unsafe_allow_html=True)

st.write("---")

# ==============================================================================
# SECTION 8: FOOTER & COMMUNITY SUPPORT
# ==============================================================================
footer_col1, footer_col2 = st.columns([2, 1])
with footer_col1:
    st.markdown("""
    **PDF to Voice Pro** | Maintained with 💙 by the Open Source Community.  
    All document rendering processes are strictly local. No user files or text extracts are ever recorded or preserved.
    """)
with footer_col2:
    st.markdown("""
    <a href="https://www.buymeacoffee.com/" target="_blank">
        <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 42px !important; width: 151px !important;" >
    </a>
    """, unsafe_allow_html=True)
