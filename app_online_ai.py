import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS

# Konfigurasi Tampilan
st.set_page_config(page_title="AI Search Assistant", page_icon="🌐", layout="centered")

st.title("🌐 Program AI Kelompok 1")
st.caption("Aplikasi AI dengan integrasi penelusuran web langsung (Real-Time Web Data)")

# Cek apakah API Key ada di Streamlit Secrets
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    with st.sidebar:
        st.header("⚙️ Pengaturan")
        api_key = st.text_input("Masukkan Google Gemini API Key:", type="password")
        st.markdown("[Dapatkan API Key di sini](https://aistudio.google.com/)")

# Optimasi: Batasi max_results=2 dan batasi panjang teks snippet agar loading web instan
def cari_data_web(query, max_results=2):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            ringkasan_web = ""
            for i, r in enumerate(results, 1):
                body = r.get('body', '')[:250]  # Pangkas ringkasan maksimal 250 karakter
                ringkasan_web += f"\n[Sumber {i}]: {r.get('title', '')} | Info: {body}\n"
            return ringkasan_web if ringkasan_web else "Data web tidak ditemukan."
    except Exception:
        return "Pencarian web terlewati (menggunakan database internal AI)."

# Inisialisasi Riwayat Pesan
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Tampilkan riwayat chat sebelumnya
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Kolom Prompt Pengguna
user_prompt = st.chat_input("Tanyakan apa saja (misal: layar laptop berkedip saat buka tutup)...")

if user_prompt:
    if not api_key:
        st.error("Silakan masukkan Gemini API Key terlebih dahulu di sidebar kiri!")
    else:
        # Tampilkan pesan user
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # Proses pencarian dan jawaban
        with st.chat_message("assistant"):
            status_box = st.status("🔍 Menelusuri ringkasan web...", expanded=False)
            search_context = cari_data_web(user_prompt)
            status_box.update(label="⚡ Menyusun jawaban...", state="running")

            final_prompt = f"""
            Instruksi: Kamu asisten teknis AI solutif. Jawab secara ringkas, to the point, dan terstruktur dalam Bahasa Indonesia.
            
            Konteks Web Terbaru:
            {search_context}
            
            Pertanyaan:
            {user_prompt}
            """

            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("models/gemini-3.6-flash")

                # Optimasi: Gunakan streaming agar teks langsung muncul per suku kata
                response_stream = model.generate_content(final_prompt, stream=True)
                
                status_box.update(label="Selesai!", state="complete", expanded=False)
                
                response_container = st.empty()
                full_text = ""
                for chunk in response_stream:
                    if chunk.text:
                        full_text += chunk.text
                        response_container.markdown(full_text + "▌")
                
                response_container.markdown(full_text)
                st.session_state.chat_history.append({"role": "assistant", "content": full_text})

            except Exception as err:
                status_box.update(label="Gagal menghasilkan respons", state="error", expanded=False)
                if "429" in str(err):
                    st.warning("⏳ Kuota API sedang sibuk/penuh. Silakan tunggu sebentar lalu coba lagi.")
                else:
                    st.error(f"Terjadi kesalahan: {str(err)}")
