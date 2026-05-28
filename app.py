import streamlit as st
import streamlit.components.v1 as components
import os
import re
import edge_tts
import asyncio

# Try importing pypdf safely; if it's missing, it won't crash the app boot cycle
try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

# ==============================================================================
# SECTION 1: APP CONFIGURATION, SEO & TRACKING
# ==============================================================================
st.set_page_config(
    page_title="PDF to Voice Pro | Free Speechify Alternative",
    page_icon="🔊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Google Analytics Silent Tracking
ga_code = """
<script async src="https://www.googletagmanager.com/gtag/js?id=G-SD6ELDD8LV"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-SD6ELDD8LV');
</script>
"""
components.html(ga_code, height=0)

# Custom Styling for UI elements, Hidden Headers, and Amazon Cards
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .main .block-container { max-width: 1200px; padding-top: 2rem; }
    div.stButton > button:first-child {
        background-image: linear-gradient(to right, #00c6ff, #0072ff);
        color: white; border: none; border-radius: 10px; font-weight: bold; height: 3em; width: 100%;
    }
    div.stButton > button:first-child:hover {
        background-image: linear-gradient(to right, #0072ff, #00c6ff);
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    .main-content { padding-bottom: 80px; }
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

st.markdown('<div class="main-content">', unsafe_allow_html=True)

# ==============================================================================
# SECTION 2: AUDIO PROCESSING HELPER FUNCTIONS
# ==============================================================================
def clean_extracted_text(text):
    """Cleans whitespace, line breaks, and formatting from document text."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(?<=\s)[•*-]\s+', '', text)
    return text.strip()

def split_text_into_chunks(text, max_chars=1500):
    """Splits text intelligently at sentence boundaries to respect API payload limits."""
    if not text:
        return []
    
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
st.subheader("Convert your documents into high-quality, audible study guides.")
st.write("A 100% free, privacy-first open-source utility with zero subscription paywalls, no character limits, and no registration required.")

# ==============================================================================
# SECTION 4: VOICE SELECTION & LANGUAGE SETTINGS
# ==============================================================================
st.write("---")
st.markdown("### ⚙️ System Configuration")

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

voice_col1, voice_col2 = st.columns(2)
with voice_col1:
    voice_selection = st.selectbox("Select an AI Voice Talent:", options=list(AVAILABLE_VOICES.keys()), index=0)
    selected_voice_id = AVAILABLE_VOICES[voice_selection]
with voice_col2:
    st.info("💡 Pro Tip: Male voices often sound best at 1.2x speed for dense study notes.")

# ==============================================================================
# SECTION 5: FILE UPLOAD INTERFACE
# ==============================================================================
st.write("---")
st.markdown("### 📄 2. Upload Document")
uploaded_file = st.file_uploader("Drag and drop your file here (Supports PDF and TXT formats)", type=["pdf", "txt"])

# ==============================================================================
# SECTION 6: MAIN AUDIO GENERATION WORKFLOW
# ==============================================================================
if uploaded_file is not None:
    st.success(f"Successfully loaded: **{uploaded_file.name}**")
    full_raw_text = ""
    
    if uploaded_file.name.endswith('.txt'):
        full_raw_text = uploaded_file.read().decode("utf-8", errors="ignore")
    else:
        # Check package initialization safety bounds
        if not PYPDF_AVAILABLE:
            st.error("Text extraction components are missing. Please verify your requirements.txt contains 'pypdf'.")
            # Secondary text extraction fallback logic
            try:
                raw_bytes = uploaded_file.read()
                strings = re.findall(b"[a-zA-Z0-9\s\.\,\!\?\:\;\-\(\)\'\"\`]{4,}", raw_bytes)
                full_raw_text = " ".join([s.decode('utf-8', errors='ignore') for s in strings])
            except Exception:
                full_raw_text = ""
        else:
            try:
                pdf_reader = PdfReader(uploaded_file)
                total_pages = len(pdf_reader.pages)
                for page_num in range(total_pages):
                    page_text = pdf_reader.pages[page_num].extract_text()
                    if page_text:
                        full_raw_text += page_text + " "
            except Exception as e:
                st.error(f"Error decoding layout structure: {e}")

    cleaned_text = clean_extracted_text(full_raw_text)
    total_chars = len(cleaned_text)
    
    if total_chars < 10:
        st.error("Could not parse enough structural text from this document. If this is a scanned PDF image, please copy-paste the text directly into a .txt file and upload it here!")
    else:
        st.metric(label="Total Processable Characters", value=f"{total_chars:,}")
        
        text_chunks = split_text_into_chunks(cleaned_text, max_chars=1800)
        total_chunks = len(text_chunks)
        
        st.markdown("### ⚡ 3. Compile Master Audio File")
        st.write(f"The text has been formatted into **{total_chunks} optimized chunks** for high-speed streaming processing.")
        
        if st.button("Generate MP3 Audio Guide"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            chunk_files = []
            compiled_success = True
            
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
                    
                progress_bar.progress(int(((i + 1) / total_chunks) * 100))
            
            if compiled_success and chunk_files:
                master_output_filename = "PDF_to_Voice_Pro_Master.mp3"
                status_text.write("Assembling voice master track...")
                
                try:
                    with open(master_output_filename, "wb") as master_file:
                        for temp_file in chunk_files:
                            with open(temp_file, "rb") as f:
                                master_file.write(f.read())
                    
                    st.success("🎉 Master Audio Guide Compiled Successfully!")
                    
                    with open(master_output_filename, "rb") as final_audio:
                        audio_bytes = final_audio.read()
                        
                        st.audio(audio_bytes, format="audio/mp3")
                        st.download_button(
                            label="⬇️ Download Full Master MP3 Guide",
                            data=audio_bytes,
                            file_name=f"{os.path.splitext(uploaded_file.name)[0]}_audio.mp3",
                            mime="audio/mp3"
