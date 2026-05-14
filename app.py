import streamlit as st
import ollama
import pymupdf
import os
import json
import numpy as np
import faiss
from datetime import datetime
from sentence_transformers import SentenceTransformer

st.set_page_config(
    page_title="Assistant PDF",
    page_icon="📄",
    layout="wide"
)

st.markdown("""
    <style>
    .main { padding: 2rem; }
    .stChatMessage { border-radius: 10px; margin: 0.5rem 0; }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def charger_modele_embedding():
    return SentenceTransformer('all-MiniLM-L6-v2')

def decouper_texte(texte, taille=500, overlap=50):
    mots = texte.split()
    morceaux = []
    i = 0
    while i < len(mots):
        morceau = ' '.join(mots[i:i+taille])
        morceaux.append(morceau)
        i += taille - overlap
    return morceaux

def construire_index(morceaux, modele_embedding):
    embeddings = modele_embedding.encode(morceaux)
    embeddings = np.array(embeddings).astype('float32')
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index, embeddings

def rechercher_morceaux(question, index, morceaux, modele_embedding, k=5):
    question_embedding = modele_embedding.encode([question]).astype('float32')
    distances, indices = index.search(question_embedding, k)
    return [morceaux[i] for i in indices[0]]

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
        for key in ["historique", "fichiers_charges", "morceaux", "index_faiss"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Main
st.title("📄 Assistant PDF")
st.markdown("Upload un ou plusieurs fichiers PDF/TXT et pose des questions dessus.")

modele_embedding = charger_modele_embedding()

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

        with st.spinner("Indexation du document..."):
            morceaux = decouper_texte(contenu_global)
            index_faiss, _ = construire_index(morceaux, modele_embedding)

        st.session_state.fichiers_charges = nouveaux
        st.session_state.morceaux = morceaux
        st.session_state.index_faiss = index_faiss
        st.session_state.historique = [
            {'role': 'system', 'content': "Tu es un assistant qui répond aux questions sur des documents."}
        ]

        with st.spinner("Génération du résumé..."):
            contexte_resume = '\n\n'.join(morceaux[:10])
            messages_resume = [
                {'role': 'system', 'content': f"Tu es un assistant. Voici le début du document :\n\n{contexte_resume}"},
                {'role': 'user', 'content': 'Fais-moi un résumé complet de ce document.'}
            ]
            response = ollama.chat(model=model, messages=messages_resume)
            resume = response['message']['content']
            st.session_state.historique.append({'role': 'assistant', 'content': resume})

    for msg in st.session_state.historique[1:]:
        if msg['role'] == 'user':
            st.chat_message("user").write(msg['content'])
        elif msg['role'] == 'assistant':
            st.chat_message("assistant").write(msg['content'])

    user_input = st.chat_input("Pose une question sur les documents...")
    if user_input:
        morceaux_pertinents = rechercher_morceaux(
            user_input,
            st.session_state.index_faiss,
            st.session_state.morceaux,
            modele_embedding
        )
        contexte = '\n\n'.join(morceaux_pertinents)

        st.session_state.historique.append({'role': 'user', 'content': user_input})

        messages_avec_contexte = [
            {'role': 'system', 'content': f"Tu es un assistant. Voici les passages pertinents du document :\n\n{contexte}"},
            *st.session_state.historique[1:]
        ]

        with st.spinner("Réflexion..."):
            response = ollama.chat(model=model, messages=messages_avec_contexte)
            reply = response['message']['content']
            st.session_state.historique.append({'role': 'assistant', 'content': reply})
        st.rerun()

else:
    st.info("👆 Upload un fichier pour commencer.")