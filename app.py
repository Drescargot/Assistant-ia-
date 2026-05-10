import streamlit as st
import ollama
import pymupdf
import os

st.title("📄 Assistant PDF")

def lire_fichier(chemin):
    extension = os.path.splitext(chemin)[1].lower()
    if extension == '.pdf':
        doc = pymupdf.open(chemin)
        contenu = ""
        for page in doc:
            contenu += page.get_text()
        return contenu
    elif extension == '.txt':
        with open(chemin, 'r', encoding='utf-8') as f:
            return f.read()
    return None

uploaded_file = st.file_uploader("Uploade ton fichier", type=['pdf', 'txt'])

if uploaded_file:
    contenu = ""
    if uploaded_file.name.endswith('.pdf'):
        doc = pymupdf.open(stream=uploaded_file.read(), filetype="pdf")
        for page in doc:
            contenu += page.get_text()
    else:
        contenu = uploaded_file.read().decode('utf-8')

    if "historique" not in st.session_state:
        st.session_state.historique = [
            {'role': 'system', 'content': f"Tu es un assistant. Voici le contenu d'un document :\n\n{contenu}"}
        ]
        with st.spinner("Génération du résumé..."):
            st.session_state.historique.append({'role': 'user', 'content': 'Fais-moi un résumé complet de ce document.'})
            response = ollama.chat(model='llama3.1:8b', messages=st.session_state.historique)
            resume = response['message']['content']
            st.session_state.historique.append({'role': 'assistant', 'content': resume})

    for msg in st.session_state.historique[2:]:
        if msg['role'] == 'user':
            st.chat_message("user").write(msg['content'])
        elif msg['role'] == 'assistant':
            st.chat_message("assistant").write(msg['content'])

    user_input = st.chat_input("Pose une question sur le document...")
    if user_input:
        st.session_state.historique.append({'role': 'user', 'content': user_input})
        with st.spinner("Réflexion..."):
            response = ollama.chat(model='llama3.1:8b', messages=st.session_state.historique)
            reply = response['message']['content']
            st.session_state.historique.append({'role': 'assistant', 'content': reply})
        st.rerun()