import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS

# Konfigurasi Tampilan
st.set_page_config(page_title="AI Search Assistant", page_icon="🌐", layout="centered")

st.title("🌐 AI Search Assistant")
st.caption("Aplikasi AI dengan integrasi penelusuran web langsung (Real-Time Web Data)")

# Input API Key di sidebar
with st.sidebar:
    st.header("⚙️ Pengaturan")
    api_key = st.text_input("Masukkan Google Gemini API Key:", type="password")
    st.markdown("[Dapatkan API Key di sini](https://aistudio.google.com/)")

# Fungsi untuk mencari data di web
def cari_data_web(query, max_results=3):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            ringkasan_web = ""
            for i, r in enumerate(results, 1):
                ringkasan_web += f"\n[Sumber {i}]: {r.get('title', '')}\nURL: {r.get('href', '')}\nKonten: {r.get('body', '')}\n"
            return ringkasan_web if ringkasan_web else "Tidak ditemukan hasil web yang spesifik."
    except Exception as e:
        return f"Catatan: Pencarian web sedang terbatas ({str(e)}). Menggunakan pengetahuan internal AI."

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
        # Konfigurasi AI
        genai.configure(api_key=api_key)

        # Otomatis deteksi model yang tersedia di akun pengguna
        target_model_name = "gemini-1.5-flash"
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            # Prioritaskan flash, jika tidak ada cari model pertama yang support
            flash_models = [m for m in available_models if 'flash' in m]
            if flash_models:
                target_model_name = flash_models[0]
            elif available_models:
                target_model_name = available_models[0]
        except Exception:
            target_model_name = "models/gemini-1.5-flash"

        model = genai.GenerativeModel(target_model_name)

        # Tampilkan pesan user
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # Proses pencarian dan jawaban
        with st.chat_message("assistant"):
            status_box = st.status("Sedang mencari informasi di internet...", expanded=False)
            
            search_context = cari_data_web(user_prompt)
            status_box.update(label="AI sedang menganalisis jawaban...", state="running")

            final_prompt = f"""
            Kamu adalah asisten AI teknis yang cerdas dan solutif.
            Jawab pertanyaan pengguna secara jelas, terstruktur, dan ramah.
            
            Informasi Tambahan dari Web:
            {search_context}
            
            Pertanyaan Pengguna:
            {user_prompt}
            
            Berikan analisis penyebab masalah dan langkah-langkah solusinya.
            """

            try:
                response = model.generate_content(final_prompt)
                status_box.update(label="Selesai!", state="complete", expanded=False)
                st.markdown(response.text)
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
            except Exception as err:
                status_box.update(label="Gagal menghasilkan respons", state="error", expanded=False)
                st.error(f"Terjadi kesalahan saat memanggil AI: {str(err)}")
