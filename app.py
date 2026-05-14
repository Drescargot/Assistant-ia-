import streamlit as st
import ollama
import pymupdf
import os
import json
from datetime import datetime

st.set_page_config(
    page_title="Assistant PDF",
    page_icon="📄",
    layout="wide"
)

st.markdown("""
    <style>
    .main { padding: 2rem; }
    .stChatMessage { border-radius: 10px; margin: 0.5rem 0; }
    .sidebar-title { font-size: 1.2rem; font-weight: bold; margin-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Paramètres")
    model = st.selectbox("Modèle", ["llama3.1:8b", "llama3.2:3b"], index=0)
    
    st.divider()
    st.markdown("### 📁 Fichiers chargés")
    if "fichiers_charges" in st.session_state and st.session_state.fichiers_charges:
        for nom in st.session_state.fichiers_charges:
            st.markdown(f"✅ {nom}")
    else:
        st.markdown("*Aucun fichier*")

    st.divider()
    st.markdown("### 💾 Historique")
    if st.button("Sauvegarder la conversation"):
        if "historique" in st.session_state:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nom_fichier = f"conversation_{timestamp}.json"
            with open(nom_fichier, "w", encoding="utf-8") as f:
                json.dump(st.session_state.historique, f, ensure_ascii=False, indent=2)
            st.success(f"Sauvegardé : {nom_fichier}")

    if st.button("🗑️ Nouvelle conversation"):
        for key in ["historique", "fichiers_charges", "contenu_global"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Main
st.title("📄 Assistant PDF")
st.markdown("Upload un ou plusieurs fichiers PDF/TXT et pose des questions dessus.")

uploaded_files = st.file_uploader(
    "Uploade tes fichiers",
    type=['pdf', 'txt'],
    accept_multiple_files=True
)

if uploaded_files:
    nouveaux = [f.name for f in uploaded_files]
    
    if "fichiers_charges" not in st.session_state or st.session_state.fichiers_charges != nouveaux:
        contenu_global = ""
        for uploaded_file in uploaded_files:
            if uploaded_file.name.endswith('.pdf'):
                doc = pymupdf.open(stream=uploaded_file.read(), filetype="pdf")
                for page in doc:
                    contenu_global += page.get_text()
            else:
                contenu_global += uploaded_file.read().decode('utf-8')
            contenu_global += "\n\n"

        st.session_state.fichiers_charges = nouveaux
        st.session_state.contenu_global = contenu_global
        st.session_state.historique = [
            {'role': 'system', 'content': f"Tu es un assistant. Voici le contenu des documents :\n\n{contenu_global}"}
        ]
        with st.spinner("Génération du résumé..."):
            st.session_state.historique.append({'role': 'user', 'content': 'Fais-moi un résumé complet de ces documents.'})
            response = ollama.chat(model=model, messages=st.session_state.historique)
            resume = response['message']['content']
            st.session_state.historique.append({'role': 'assistant', 'content': resume})

    for msg in st.session_state.historique[2:]:
        if msg['role'] == 'user':
            st.chat_message("user").write(msg['content'])
        elif msg['role'] == 'assistant':
            st.chat_message("assistant").write(msg['content'])

    user_input = st.chat_input("Pose une question sur les documents...")
    if user_input:
        st.session_state.historique.append({'role': 'user', 'content': user_input})
        with st.spinner("Réflexion..."):
            response = ollama.chat(model=model, messages=st.session_state.historique)
            reply = response['message']['content']
            st.session_state.historique.append({'role': 'assistant', 'content': reply})
        st.rerun()

else:
    st.info("👆 Upload un fichier pour commencer.")