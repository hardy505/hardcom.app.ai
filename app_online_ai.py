import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS

# Konfigurasi Tampilan
st.set_page_config(page_title="AI Search Assistant", page_icon="🌐", layout="centered")

st.title("🌐 AI Search Assistant")
st.caption("Aplikasi AI dengan integrasi penelusuran web langsung (Real-Time Web Data)")

# Input API Key (Bisa diisi di UI atau disimpan di Secrets saat hosting)
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
                ringkasan_web += f"\n[Sumber {i}]: {r['title']}\nURL: {r['href']}\nKonten: {r['body']}\n"
            return ringkasan_web
    except Exception as e:
        return f"Gagal mengambil data web: {str(e)}"

# Inisialisasi Riwayat Pesan
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Tampilkan riwayat chat sebelumnya
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Kolom Prompt Pengguna
user_prompt = st.chat_input("Tanyakan apa saja (misal: berita terkini, teknologi baru, dll)...")

if user_prompt:
    if not api_key:
        st.error("Silakan masukkan Gemini API Key terlebih dahulu di sidebar kiri!")
    else:
        # Konfigurasi AI
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Tampilkan pesan user
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # Proses pencarian dan pembuatan jawaban
        with st.chat_message("assistant"):
            status_box = st.status("Sedang mencari data terbaru di web...", expanded=False)
            
            # 1. Cari data di internet
            search_context = cari_data_web(user_prompt)
            status_box.update(label="Menganalisis hasil pencarian dengan AI...", state="running")

            # 2. Rancang prompt gabungan (RAG sederhana)
            final_prompt = f"""
            Kamu adalah asisten AI pintar. Jawab pertanyaan pengguna berdasarkan konteks penelusuran web terbaru berikut:
            
            --- DATA DARI HASIL PENCARIAN WEB ---
            {search_context}
            -------------------------------------
            
            Pertanyaan Pengguna: {user_prompt}
            
            Instruksi:
            - Berikan jawaban yang informatif, ringkas, dan to-the-point.
            - Cantumkan tautan/sumber URL jika relevan dari hasil pencarian di atas.
            """

            # 3. Minta jawaban ke AI
            response = model.generate_content(final_prompt)
            status_box.update(label="Selesai!", state="complete", expanded=False)

            # 4. Tampilkan hasil
            st.markdown(response.text)
            st.session_state.chat_history.append({"role": "assistant", "content": response.text})