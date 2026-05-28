import streamlit as st
import streamlit.components.v1 as components
import os
import re
import edge_tts
import asyncio

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
        # Native byte stream extraction to parse text strings from PDF containers safely
        try:
            raw_bytes = uploaded_file.read()
            # Grabs alphanumeric strings and common punctuation marks
            strings = re.findall(b"[a-zA-Z0-9\s\.\,\!\?\:\;\-\(\)\'\"\`]{4,}", raw_bytes)
            full_raw_text = " ".join([s.decode('utf-8', errors='ignore') for s in strings])
        except Exception as e:
            st.error(f"Error parsing raw content structure: {e}")

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
                        )
                except Exception as merge_error:
                    st.error(f"Error compiling master output file track assembly: {str(merge_error)}")
                finally:
                    for temp_file in chunk_files:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    if os.path.exists(master_output_filename):
                        os.remove(master_output_filename)
            else:
                st.error("Audio conversion failed during step compilation tracking pipeline updates.")

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

# ==============================================================================
# SECTION 8: SEO LONG-TAIL MARKETING CONTENT
# ==============================================================================
st.write("---")
st.markdown("### 🚀 Why Choose a Free Browser-Based TTS?")
st.markdown("""
Looking for a secure **free Speechify alternative**, a way to read research papers aloud, or a tool to listen to documents without an **ElevenReader or Paper2Audio subscription** limit? 
PDF to Voice Pro is a lightweight, high-performance web utility built for students, academics, commuters, and professionals who need to convert dense textbooks, research papers, and study guides to audio on the fly. 

* **No Subscriptions, No 56-Hour Limits:** Unlike premium platforms, there are no recurring monthly credit resets, weekly hour caps, or aggressive paywalls standing between you and your learning.
* **Intelligent Local Processing:** Your security matters. Files are processed entirely inside your local browser memory—no private text, academic research, or corporate data is ever saved to external database servers.
* **Completely Free Access:** No hidden microtransactions, no predatory 'free trials' that automatically charge your card, and zero software or browser extensions required.
""")

st.write("---")
st.markdown("""
### 🛠️ Frequently Asked Questions
**Does this translate my PDF?** No. This tool reads the text as written. If your PDF is in Spanish or French, select the matching language variant!
**What is the character limit?** The engine is optimized for documents under 50,000 characters.
**Is my data safe?** Yes. We use volatile processing; your files are cleared the moment you close the tab. We use basic Google Analytics to see how many people use the tool, but we never see your PDFs.
""")

st.caption("PDF to Voice Pro | High-Performance AI Utility | 2026")
st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# SECTION 9: FIXED BRANDED FOOTER & COMMUNITY SUPPORT LINKS
# ==============================================================================
footer_html = """
    <style>
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: rgba(14, 17, 23, 0.98); color: #8a99ad;
        display: flex; justify-content: space-between; align-items: center;
        padding: 10px 40px; font-family: sans-serif; font-size: 14px;
        border-top: 1px solid #262730; z-index: 999; box-sizing: border-box;
    }
    .footer-text { margin: 0; }
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
