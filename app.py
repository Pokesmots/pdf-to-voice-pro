import streamlit as st
import streamlit.components.v1 as components
import os
import re
import subprocess
import pdfplumber
import gc

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

# Premium High-Contrast CSS Styling
st.markdown("""
<style>
    /* Global Base Dark Background */
    .stApp { background-color: #0f172a; color: #f1f5f9; font-family: 'Inter', sans-serif; }
    .main .block-container { max-width: 1050px; padding-top: 2.5rem; padding-bottom: 6rem; }
    
    /* Modern Premium Hero Banner */
    .hero-container {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-left: 6px solid #00c6ff;
        padding: 32px;
        border-radius: 12px;
        margin-bottom: 35px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
    }
    
    /* Vibrant Left-Aligned Gradient Header Title */
    .gradient-title {
        background: linear-gradient(to right, #00c6ff, #0072ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 44px !important;
        font-weight: 800 !important;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
    }
    
    /* High-Contrast Lightened Structural Step Cards */
    .step-card {
        background-color: #1e293b; 
        padding: 30px; 
        border-radius: 12px; 
        border: 1px solid #475569; 
        margin-top: 20px;
        margin-bottom: 25px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
    }
    
    /* True White Text Overrides for Clear Reading Hierarchy */
    .step-card h3 { color: #ffffff !important; font-weight: 700 !important; margin-bottom: 15px !important; }
    .step-card p, .step-card label { color: #f8fafc !important; font-weight: 500; }
    
    /* High-Visibility Custom Form Input Framing */
    div[data-baseweb="select"] { background-color: #0f172a !important; border-radius: 8px; }
    div[data-testid="stFileUploaderDropzone"] { background-color: #0f172a !important; border: 2px dashed #64748b !important; }
    
    /* Premium Action Button Customizations */
    div.stButton > button:first-child {
        background-image: linear-gradient(to right, #00c6ff, #0072ff);
        color: white; border: none; border-radius: 10px; font-weight: bold; height: 3.5em; width: 100%;
        box-shadow: 0 4px 18px rgba(0, 198, 255, 0.35);
        transition: all 0.25s ease;
        font-size: 16px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div.stButton > button:first-child:hover {
        background-image: linear-gradient(to right, #0072ff, #00c6ff);
        transform: translateY(-2px);
        box-shadow: 0 6px 22px rgba(0, 114, 255, 0.45);
    }
    
    /* Hide Default System Menu Wrappers cleanly */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Amazon Product Card Placements */
    .main-content { padding-bottom: 80px; }
    .gear-card {
        background-color: #1e293b; 
        padding: 24px; 
        border-radius: 12px; 
        border: 1px solid #334155; 
        text-align: center; 
        height: 300px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 6px 16px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-content">', unsafe_allow_html=True)

# ==============================================================================
# SECTION 2: AUDIO PROCESSING HELPER FUNCTIONS
# ==============================================================================
def clean_extracted_text(text):
    """Cleans whitespace and basic formatting anomalies."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(?<=\s)[•*-]\s+', '', text)
    return text.strip()

def split_text_into_chunks(text, max_chars=2000):
    """Splits text intelligently at sentence boundaries to respect CLI argument limits."""
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

def generate_chunk_audio_via_cli(text, voice_id, output_path):
    """Executes the voice generation directly via system subprocess to completely bypass asyncio errors."""
    sanitized_text = text.replace('"', '').replace("'", "").replace('$', '').replace('`', '').replace('\\', '')
    command = f'edge-tts --voice {voice_id} --text "{sanitized_text}" --write-media {output_path}'
    subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ==============================================================================
# SECTION 3: HEADER & APP INTRODUCTION
# ==============================================================================
st.markdown("""
<div class="hero-container">
    <div class="gradient-title">🎙️ PDF to Voice Pro</div>
    <h3 style="margin-top: 0; margin-bottom: 12px; font-weight: 600; color: #ffffff;">Convert your documents into high-quality, audible study guides.</h3>
    <p style="color: #cbd5e1; margin: 0; font-size: 15px; line-height: 1.6;">A 100% free, privacy-first open-source utility with zero subscription paywalls, no character limits, and no registration required.</p>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# SECTION 4: VOICE SELECTION & LANGUAGE SETTINGS
# ==============================================================================
st.markdown('<div class="step-card">', unsafe_allow_html=True)
st.markdown("<h3>⚙️ 1. System Configuration</h3>", unsafe_allow_html=True)

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
    st.markdown("<div style='padding-top: 24px;'></div>", unsafe_allow_html=True)
    st.info("💡 Pro Tip: Male voices often sound best at 1.2x speed for dense study notes.")
st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# SECTION 5: FILE UPLOAD INTERFACE
# ==============================================================================
st.markdown('<div class="step-card">', unsafe_allow_html=True)
st.markdown("<h3>📄 2. Upload Document</h3>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("Drag and drop your file here (Supports PDF and TXT formats)", type=["pdf", "txt"])
st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# SECTION 6: MAIN AUDIO GENERATION WORKFLOW
# ==============================================================================
if uploaded_file is not None:
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.success(f"Successfully loaded: **{uploaded_file.name}**")
    full_raw_text = ""
    
    if uploaded_file.name.endswith('.txt'):
        full_raw_text = uploaded_file.read().decode("utf-8", errors="ignore")
    else:
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                extracted_pages = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        extracted_pages.append(text)
                    page.flush_cache()
                full_raw_text = " ".join(extracted_pages)
                del extracted_pages
                gc.collect()
        except Exception as e:
            st.error(f"Error parsing content structure: {e}")

    cleaned_text = clean_extracted_text(full_raw_text)
    total_chars = len(cleaned_text)
    
    del full_raw_text
    gc.collect()
    
    if total_chars < 10:
        st.error("Could not parse enough clear text from this document layout. Please make sure this is a text-based document or upload a plain .txt file!")
    else:
        st.metric(label="Total Processable Characters", value=f"{total_chars:,}")
        
        text_chunks = split_text_into_chunks(cleaned_text, max_chars=2000)
        total_chunks = len(text_chunks)
        
        del cleaned_text
        gc.collect()
        
        st.markdown("<h3 style='margin-top:15px;'>⚡ 3. Compile Master Audio File</h3>", unsafe_allow_html=True)
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
                    generate_chunk_audio_via_cli(chunk, selected_voice_id, temp_filename)
                    if os.path.exists(temp_filename):
                        chunk_files.append(temp_filename)
                    else:
                        raise FileNotFoundError("Audio segment file production drop failure.")
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
                        )
                except Exception as merge_error:
                    st.error(f"Error compiling master output file track assembly: {str(merge_error)}")
                finally:
                    for temp_file in chunk_files:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    if os.path.exists(master_output_filename):
                        os.remove(master_output_filename)
                    del chunk_files
                    gc.collect()
            else:
                st.error("Audio conversion failed during step compilation tracking pipeline updates.")
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# SECTION 7: NATIVE AMAZON ASSOCIATES MONETIZATION HUB
# ==============================================================================
st.write("---")
st.markdown("### 🎒 Essential Study & Commute Gear")
st.caption("Disclaimer: As an Amazon Associate, PDF to Voice Pro earns a small commission from qualifying purchases at no extra cost to you. Helps keep our open-source servers completely free! ☕")

gear_col1, gear_col2, gear_col3 = st.columns(3)

with gear_col1:
    st.markdown("""
    <div class="gear-card">
        <div>
            <span style="font-size: 32px;">🎧</span>
            <h4 style="margin: 10px 0; color: #00c6ff; font-weight:700;">Soundcore by Anker Life Q30</h4>
            <p style="font-size: 13px; color: #cbd5e1; line-height: 1.4;">The absolute gold standard for budget active noise-canceling headphones. Block out loud libraries or loud traffic commutes.</p>
        </div>
        <a href="https://amzn.to/4dxfJ5K" target="_blank" style="display: block; background: #FF9900; color: #111; padding: 10px; border-radius: 5px; font-weight: bold; text-decoration: none; font-size: 14px;">View Deal on Amazon ➔</a>
    </div>
    """, unsafe_allow_html=True)

with gear_col2:
    st.markdown("""
    <div class="gear-card">
        <div>
            <span style="font-size: 32px;">🔋</span>
            <h4 style="margin: 10px 0; color: #00c6ff; font-weight:700;">Anker Prime Power Bank</h4>
            <p style="font-size: 13px; color: #cbd5e1; line-height: 1.4;">20,000mAh, 220W high-capacity portable charger. Keeps your phones or tablets fully powered up on long campus days or work shifts.</p>
        </div>
        <a href="https://amzn.to/3PsFc7h" target="_blank" style="display: block; background: #FF9900; color: #111; padding: 10px; border-radius: 5px; font-weight: bold; text-decoration: none; font-size: 14px;">View Deal on Amazon ➔</a>
    </div>
    """, unsafe_allow_html=True)

with gear_col3:
    st.markdown("""
    <div class="gear-card">
        <div>
            <span style="font-size: 32px;">💻</span>
            <h4 style="margin: 10px 0; color: #00c6ff; font-weight:700;">Lamicall Foldable Stand</h4>
            <p style="font-size: 13px; color: #cbd5e1; line-height: 1.4;">Premium adjustable aluminum laptop and tablet stand. Folds flat to fit in your backpack for a perfectly ergonomic study setup anywhere.</p>
        </div>
        <a href="https://amzn.to/3PwJ3Ad" target="_blank" style="display: block; background: #FF9900; color: #111; padding: 10px; border-radius: 5px; font-weight: bold; text-decoration: none; font-size: 14px;">View Deal on Amazon ➔</a>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# SECTION 8: SEO LONG-TAIL MARKETING CONTENT (OPTIMIZED)
# ==============================================================================
st.write("---")
st.markdown("### 🚀 Free Text to Speech Alternative for Students & Professionals")
st.markdown("""
Looking for a secure **free Speechify alternative**, a high-quality way to **read research papers aloud**, or a tool to **convert PDF to MP3 online free** without hitting an **ElevenReader, NaturalReader, or Paper2Audio subscription** limit? 

PDF to Voice Pro is a lightweight, high-performance web utility built specifically for students, academics, commuters, and professionals who need an **unlimited text to speech tool** to convert dense textbooks, training manuals, and study guides into downloadable audio on the fly.

* **Best Free Speechify Alternative:** Unlike premium platforms, there are no recurring monthly credit resets, weekly hour caps, or aggressive paywalls standing between you and your learning.
* **Convert PDF to Audiobook Instantly:** Turn any digital textbook, chapter assignment, or study note outline into a portable audio file you can listen to during your commute, at the gym, or while multitasking.
* **Secure Local Text Processing:** Your document privacy matters. Files are processed cleanly without saving your private text, academic research, or corporate data to external database servers.
* **100% Free AI Voice Generator:** No hidden microtransactions, no predatory 'free trials' that automatically charge your card, and zero software installations or browser extensions required.
""")

# ==============================================================================
# SECTION 9: FREQUENTLY ASKED QUESTIONS & FOOTER
# ==============================================================================
st.write("---")
st.markdown("### 🛠️ Frequently Asked Questions")

st.markdown("""
**Does this translate my PDF?**  
No. This tool reads the text as written. If your PDF is in Spanish or French, select the matching language variant!

**What is the character limit?**  
The engine is optimized for documents under 50,000 characters.

**Is my data safe?**  
Yes. We use volatile processing; your files are cleared the moment you close the tab. We use basic Google Analytics to see how many people use the tool, but we never see your PDFs.
""")

st.caption("PDF to Voice Pro | High-Performance AI Utility | 2026")
st.markdown('</div>', unsafe_allow_html=True)

footer_html = """
    <style>
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: rgba(30, 41, 59, 0.98); color: #cbd5e1;
        display: flex; justify-content: space-between; align-items: center;
        padding: 12px 40px; font-family: sans-serif; font-size: 14px;
        border-top: 1px solid #475569; z-index: 999; box-sizing: border-box;
    }
    .footer-text { margin: 0; font-weight: 500; }
    .footer-btn { height: 36px !important; width: 129px !important; }
    </style>
    <div class="footer">
        <p class="footer-text">PDF to Voice Pro | <strong>Stop Reading. Start Listening.</strong></p>
        <a href="https://www.buymeacoffee.com/escapetheordinary" target="_blank">
            <img class="footer-btn" src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee">
        </a>
    </div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
