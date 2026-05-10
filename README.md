# 📄 Assistant PDF IA Local

Un assistant IA qui lit et résume tes fichiers PDF et TXT, 
et répond à tes questions dessus. Tourne entièrement en local 
sur ta machine, sans API payante.

## Fonctionnalités
- Upload de fichiers PDF et TXT
- Résumé automatique du document
- Chat pour poser des questions sur le contenu

## Prérequis
- [Ollama](https://ollama.com) installé avec le modèle `llama3.1:8b`
- Python 3.x

## Installation

1. Clone le repo
2. Installe les dépendances :
   pip install streamlit ollama pymupdf
3. Lance Ollama en arrière-plan
4. Lance l'app :
   streamlit run app.py
