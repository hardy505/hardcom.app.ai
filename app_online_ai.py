import streamlit as st
from groq import Groq
from duckduckgo_search import DDGS

# Konfigurasi Tampilan
st.set_page_config(page_title="AI Search Assistant", page_icon="🌐", layout="centered")

st.title("🌐 Program AI Kelompok 1")
st.caption("Aplikasi AI dengan integrasi penelusuran web langsung (Real-Time Web Data)")

# Cek API Key Groq (Bisa dari Secrets atau Sidebar)
api_key = None
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    with st.sidebar:
        st.header("⚙️ Pengaturan")
        api_key = st.text_input("Masukkan Groq API Key:", type="password")
        st.markdown("[Dapatkan API Key Gratis](https://console.groq.com/)")

# Fungsi pencarian web dengan batas ringkas
def cari_data_web(query):
    # Lewati pencarian jika hanya sapaan pendek agar respon instan
    if len(query.strip().split()) <= 1 or query.lower() in ["halo", "hallo", "hai", "p", "test"]:
        return ""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=2))
            if not results:
                return ""
            ringkasan = ""
            for i, r in enumerate(results, 1):
                snippet = r.get("body", "")[:200]
                ringkasan += f"\n[Sumber {i}]: {r.get('title', '')} | {snippet}"
            return ringkasan
    except Exception:
        return ""

# Riwayat Chat
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_prompt = st.chat_input("Tanyakan apa saja (misal: layar laptop berkedip saat buka tutup)...")

if user_prompt:
    if not api_key:
        st.error("Silakan masukkan Groq API Key di sidebar atau Secrets!")
    else:
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            status_box = st.status("🔍 Memeriksa referensi...", expanded=False)
            web_info = cari_data_web(user_prompt)
            
            status_box.update(label="⚡ Tanya Hardy sedang menjawab...", state="running")

            client = Groq(api_key=api_key)

            system_instruction = (
                "Kamu adalah asisten AI teknis yang cerdas, cepat, dan solutif. "
                "Jawab langsung to-the-point dalam Bahasa Indonesia yang ramah dan rapi. "
                "Jika ada konteks web tambahan, gunakan untuk memperkaya jawabanmu."
            )

            prompt_lengkap = user_prompt
            if web_info:
                prompt_lengkap = f"Konteks Web:\n{web_info}\n\nPertanyaan: {user_prompt}"

            messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt_lengkap}
            ]

            response_container = st.empty()
            full_text = ""

            try:
                # Groq memproses jawaban dalam hitungan milidetik
                completion = client.chat.completions.create(
                    model="qwen/qwen3.8-27b",
                    messages=messages,
                    stream=True
                )

                status_box.update(label="Selesai!", state="complete", expanded=False)

                for chunk in completion:
                    content = chunk.choices[0].delta.content
                    if content:
                        full_text += content
                        response_container.markdown(full_text + "▌")

                response_container.markdown(full_text)
                st.session_state.chat_history.append({"role": "assistant", "content": full_text})

            except Exception as e:
                status_box.update(label="Gagal menghasilkan respons", state="error", expanded=False)
                st.error(f"Terjadi kesalahan: {str(e)}")
