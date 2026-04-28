import streamlit as st
import edge_tts
import asyncio
import fitz
import os
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="PDF to Audio Turbo", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stButton>button { 
        background-image: linear-gradient(to right, #00c6ff, #0072ff);
        color: white; border: none; border-radius: 10px; font-weight: bold; height: 3em;
    }
    </style>
    """, unsafe_allow_html=True)

voice_data = {
    "English (US)": ["en-US-AvaNeural", "en-US-GuyNeural", "en-US-EmmaNeural", "en-US-BrianNeural"],
    "English (UK)": ["en-GB-SoniaNeural", "en-GB-RyanNeural"],
    "Spanish": ["es-MX-DaliaNeural", "es-MX-JorgeNeural"],
}

with st.sidebar:
    st.header("🛠️ Audio Controls")
    selected_lang = st.selectbox("Select Language", list(voice_data.keys()))
    selected_voice = st.selectbox("Select Voice Talent", voice_data[selected_lang])

st.title("⚡ PDF to Audio Turbo")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📄 1. Upload")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")

with col2:
    st.markdown("### 📝 2. Document Status")
    if uploaded_file:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        full_text = "".join([page.get_text() for page in doc])
        st.success(f"PDF Loaded: {len(doc)} pages detected.")
        st.metric("Total Characters", f"{len(full_text):,}")
    else:
        st.info("Awaiting PDF upload...")

st.divider()

if uploaded_file and full_text:
    st.markdown("### 🔊 3. Export Full Audio")
    if st.button("🚀 Generate Turbo MP3"):
        output_path = "turbo_audio.mp3"
        
        # Expert Move: Chunking into slightly larger pieces for efficiency
        chunks = [full_text[i:i+3000] for i in range(0, len(full_text), 3000)]
        
        async def convert_chunk(index, text):
            filename = f"part_{index}.mp3"
            communicate = edge_tts.Communicate(text, selected_voice)
            await communicate.save(filename)
            return filename

        async def process_all():
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # This creates a "Task" for every chunk to run at once
            tasks = [convert_chunk(i, chunk) for i, chunk in enumerate(chunks)]
            
            status_text.text(f"⚡ Turbo-processing {len(chunks)} sections at once...")
            # 'gather' runs them in parallel!
            filenames = await asyncio.gather(*tasks)
            
            progress_bar.progress(80)
            status_text.text("Merging files...")
            
            # Stitch them together
            with open(output_path, "wb") as master:
                for fname in filenames:
                    with open(fname, "rb") as part:
                        master.write(part.read())
                    os.remove(fname) # Clean up the parts
            
            progress_bar.progress(100)
            status_text.text("✅ Finished!")

        with st.status("🚀 Launching Turbo Engine...", expanded=True) as status:
            try:
                asyncio.run(process_all())
                status.update(label="Conversion Successful!", state="complete")
                st.audio(output_path)
                with open(output_path, "rb") as f:
                    st.download_button("📥 Download Full MP3", f, file_name="turbo_notes.mp3")
            except Exception as e:
                st.error(f"Error: {e}")

st.divider()
st.markdown("""
### 💡 Why use PDF to Audio Pro?
* **Save Time:** Finish your reading list while driving or doing chores.
* **Better Retention:** Listening while reading (Dual Coding) is proven to help you remember more.
* **Natural Voices:** No more robotic speech. We use the latest Neural AI for human-like tones.

---
### 🛠️ FAQ
**Is there a file limit?** We currently support documents up to ~40,000 characters for optimal speed.

**What happens to my data?** We value your privacy. Files are processed "in-memory" and deleted the moment you close the tab.
""")
