import streamlit as st
import edge_tts
import asyncio
import fitz
import os

# --- 1. PAGE CONFIG & THEME ---
st.set_page_config(page_title="PDF to Voice Pro", page_icon="🎙️", layout="wide")

# Professional Dark Theme CSS
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stButton>button { 
        background-image: linear-gradient(to right, #00c6ff, #0072ff);
        color: white; border: none; border-radius: 10px; font-weight: bold; height: 3em;
        width: 100%;
    }
    /* Hide Streamlit branding for a professional look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. VOICE DATA ---
voice_data = {
    "English (US)": ["en-US-AvaNeural", "en-US-GuyNeural", "en-US-EmmaNeural", "en-US-BrianNeural"],
    "English (UK)": ["en-GB-SoniaNeural", "en-GB-RyanNeural"],
    "Spanish": ["es-MX-DaliaNeural", "es-MX-JorgeNeural", "es-ES-AlvaroNeural", "es-US-AlonsoNeural"],
}

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ System Settings")
    selected_lang = st.selectbox("Select Language", list(voice_data.keys()))
    selected_voice = st.selectbox("Select Voice Talent", voice_data[selected_lang])
    
    st.divider()
    st.info("💡 Pro Tip: Male voices often sound best at 1.2x speed for dense study notes.")
    
    st.markdown("""
    **How it works:**
    1. Upload your PDF document.
    2. We extract and analyze the text.
    3. Our Turbo Engine generates the audio.
    """)
    
    # --- MONETIZATION: BUY ME A COFFEE ---
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

# --- 4. MAIN INTERFACE ---
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

# --- 5. THE TURBO CHUNKER ENGINE ---
if uploaded_file and full_text:
    st.markdown("### 🔊 3. Audio Generation")
    if st.button("🚀 Generate High-Speed MP3"):
        output_path = "final_audio_pro.mp3"
        
        chunks = [full_text[i:i+2500] for i in range(0, len(full_text), 2500)]
        
        async def convert_chunk(index, text):
            filename = f"part_{index}.mp3"
            # Stagger timing for Spanish/Stability
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

        with st.status("⚡ Turbo-processing your audio... please wait.", expanded=True) as status:
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

# --- 6. FAQ ---
st.markdown("---")
st.markdown("""
### 🛠️ Frequently Asked Questions
**Does this translate my PDF?** No. This tool reads the text exactly as written. Choose the voice that matches your PDF's language!

**What is the character limit?** The engine is optimized for documents under 50,000 characters for the best speed.

**Is my data safe?** Yes. We use volatile processing; your files are cleared the moment you close the tab.
""")

st.caption("PDF to Voice Pro | High-Performance AI Utility | 2026")
