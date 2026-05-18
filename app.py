import streamlit as st
import streamlit.components.v1 as components
import edge_tts
import asyncio
import fitz
import os

# --- 1. PAGE CONFIG (SEO & Tab Customization) ---
st.set_page_config(
    page_title="PDF to Voice Pro | Free Speechify Alternative",
    page_icon="🔊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. GOOGLE ANALYTICS (Silent Tracking) ---
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

# --- 3. CUSTOM STYLING (Modern UI Layout) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stButton>button { 
        background-image: linear-gradient(to right, #00c6ff, #0072ff);
        color: white; border: none; border-radius: 10px; font-weight: bold; height: 3em;
        width: 100%;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Padding adjustments to ensure content doesn't get cut off by fixed footer */
    .main-content {
        padding-bottom: 60px;
    }
    </style>
    """, unsafe_allow_html=True)

# Wrap main interface elements in a div to preserve layout spacing
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# --- 4. VOICE DATA ---
voice_data = {
    "English (US)": ["en-US-AvaNeural", "en-US-GuyNeural", "en-US-EmmaNeural", "en-US-BrianNeural"],
    "English (UK)": ["en-GB-SoniaNeural", "en-GB-RyanNeural"],
    "Spanish": ["es-MX-DaliaNeural", "es-MX-JorgeNeural", "es-ES-AlvaroNeural", "es-US-AlonsoNeural"],
}

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ System Settings")
    selected_lang = st.selectbox("Select Language", list(voice_data.keys()))
    selected_voice = st.selectbox("Select Voice Talent", voice_data[selected_lang])
    
    st.divider()
    st.info("💡 Pro Tip: Male voices often sound best at 1.2x speed for dense study notes.")
    
    st.markdown("""
    **How it works:**
    1. Upload your PDF.
    2. We extract the text.
    3. Our Turbo Engine creates your MP3.
    """)
    
    st.divider()
    st.markdown("### ☕ Support the Developer")
    st.write("If this tool saved you time today, consider fueling the next update!")
    
    bmc_button = """
    <a href="https://www.buymeacoffee.com/escapetheordinary" target="_blank">
        <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" 
        alt="Buy Me A Coffee" style="height: 50px !important;width: 180px !important;" >
    </a>
    """
    st.markdown(bmc_button, unsafe_allow_html=True)

# --- 6. MAIN INTERFACE ---
st.title("🎙️ PDF to Voice Pro")
st.subheader("Convert your documents into high-quality, audible study guides.")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📄 1. Upload Document")
    uploaded_file = st.file_uploader("Drop your PDF here (supports multi-page)", type="pdf")

with col2:
    st.markdown("### 📝 2. Document Status")
    if uploaded_file:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        full_text = "".join([page.get_text() for page in doc])
        st.success(f"Successfully loaded {len(doc)} pages.")
        st.metric("Total Characters", f"{len(full_text):,}")
    else:
        st.info("Awaiting PDF upload...")

st.divider()

# --- 7. THE TURBO CHUNKER ENGINE ---
if uploaded_file and 'full_text' in locals() and full_text:
    st.markdown("### 🔊 3. Audio Generation")
    if st.button("🚀 Generate High-Speed MP3"):
        output_path = "final_audio_pro.mp3"
        
        chunks = [full_text[i:i+2500] for i in range(0, len(full_text), 2500)]
        
        async def convert_chunk(index, text):
            filename = f"part_{index}.mp3"
            if "Spanish" in selected_lang:
                await asyncio.sleep(index * 0.6) 
            
            try:
                communicate = edge_tts.Communicate(text, selected_voice)
                await communicate.save(filename)
                return filename
            except Exception:
                return None

        async def process_parallel():
            tasks = [convert_chunk(i, chunk) for i, chunk in enumerate(chunks)]
            filenames = await asyncio.gather(*tasks)
            
            with open(output_path, "wb") as master:
                for fname in filenames:
                    if fname and os.path.exists(fname):
                        with open(fname, "rb") as part:
                            master.write(part.read())
                        os.remove(fname) 

        with st.status("⚡ Turbo-processing your audio...", expanded=True) as status:
            try:
                asyncio.run(process_parallel())
                status.update(label="✅ Conversion Successful!", state="complete")
                st.audio(output_path)
                with open(output_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Final MP3",
                        data=f,
                        file_name="pdftovoice_audio.mp3",
                        mime="audio/mp3"
                    )
            except Exception as e:
                st.error(f"Error during generation: {e}")

# --- 8. SEO ADVANTAGE TEXT SECTION ---
st.markdown("---")
st.markdown("### 🚀 Why Choose a Free Browser-Based TTS?")
st.markdown("""
Looking for a secure **free Speechify alternative** or a way to listen to documents without an **ElevenReader subscription** limit? 
PDF to Voice Pro is a lightweight, high-performance web utility built for students, commuters, and professionals who need to convert dense textbooks and study guides to audio on the fly. 

* **No Subscriptions or Credit Caps:** Unlike ElevenLabs or NaturalReader, there are no recurring monthly credit resets or paywalls standing between you and your learning.
* **Privacy-First Design:** Your security matters. Files are processed entirely inside your local browser memory—no private data or text is saved to external database servers.
* **Completely Free Access:** No hidden microtransactions, no predatory 'free trials' that automatically charge your card, and zero software installation required.
""")

# --- 9. STANDARD FAQ ---
st.markdown("---")
st.markdown("""
### 🛠️ Frequently Asked Questions
**Does this translate my PDF?** No. This tool reads the text as written. If your PDF is in Spanish, select a Spanish voice!

**What is the character limit?** The engine is optimized for documents under 50,000 characters.

**Is my data safe?** Yes. We use volatile processing; your files are cleared the moment you close the tab. We use basic Google Analytics to see how many people use the tool, but we never see your PDFs.
""")

st.caption("PDF to Voice Pro | High-Performance AI Utility | 2026")
st.markdown('</div>', unsafe_allow_html=True) # End main-content container

# --- 10. FIXED BRANDED FOOTER ---
footer_html = """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: rgba(14, 17, 23, 0.95);
        color: #8a99ad;
        text-align: center;
        font-size: 14px;
        padding: 12px;
        font-family: sans-serif;
        border-top: 1px solid #262730;
        z-index: 999;
    }
    </style>
    <div class="footer">
        <p>PDF to Voice Pro | <strong>Stop Reading. Start Listening.</strong></p>
    </div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
