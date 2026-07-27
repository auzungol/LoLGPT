import streamlit as st
from rag import answer_query

st.set_page_config(page_title="LoLGPT", page_icon="🎮", layout="centered")

st.title("🎮 LoLGPT — League of Legends Şampiyon Asistanı")
st.caption("Foundry Local ile çalışan, tamamen çevrimdışı yerel RAG asistanı")

with st.sidebar:
    st.header("Örnek sorular")
    example_questions = [
        "yasuo q",
        "veigar lane",
        "assassin champions",
        "hangi şampiyonlar ionialı",
        "zoe'yi anlat",
        "garen vs darius",
    ]
    for q in example_questions:
        if st.button(q, use_container_width=True):
            st.session_state.pending_question = q

    st.divider()
    st.caption(
        "Bu proje tamamen yerel çalışır — hiçbir veri internete gönderilmez. "
        "Yapılandırılmış sorular (ability, lane, region, role, kaynak) anında "
        "veritabanından cevaplanır; diğer sorular yerel LLM ile üretilir."
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Bir şampiyon hakkında soru sor...")

if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Düşünüyor..."):
            try:
                answer = answer_query(question, top_k=5)
            except Exception as e:
                answer = f"Bir hata oluştu: {e}"
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})