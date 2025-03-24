import os
import sqlite3
from datetime import datetime
from difflib import get_close_matches
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np
import json
import pandas as pd
import streamlit as st
from openai import OpenAI

# ==========================
# 🔑 Configuração da API GPT
# ==========================
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ API Key para OpenAI não configurada!")
else:
    client = OpenAI(api_key=api_key)

# ==========================
# 🗄️ Criação da base de dados
# ==========================
DB_NAME = 'chat_history.db'

def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            user_input TEXT,
            gpt_response TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ==========================
# 💾 Salva chats na base de dados
# ==========================
def save_chat(date, user_input, gpt_response):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO chats (date, user_input, gpt_response) VALUES (?, ?, ?)',
        (date, user_input, gpt_response)
    )
    conn.commit()
    conn.close()

# ==========================
# 🔎 Busca com NLP (Natural Language Processing)
# ==========================
def search_chat(query):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_input, gpt_response FROM chats")
    data = cursor.fetchall()
    conn.close()

    inputs = [d[0] for d in data]
    matches = get_close_matches(query, inputs, n=5, cutoff=0.5)

    results = []
    for match in matches:
        for d in data:
            if match in d[0]:
                results.append(d)
    return results

# ==========================
# 📊 Organiza chats por tema (Clusterização)
# ==========================
def cluster_chats():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_input FROM chats")
    data = [row[0] for row in cursor.fetchall()]
    conn.close()

    if len(data) > 1:
        vectorizer = TfidfVectorizer(stop_words='english')
        X = vectorizer.fit_transform(data)

        n_clusters = min(5, len(data))
        model = KMeans(n_clusters=n_clusters, random_state=42)
        model.fit(X)

        clusters = {i: [] for i in range(n_clusters)}
        for i, label in enumerate(model.labels_):
            clusters[label].append(data[i])

        return clusters
    else:
        return {}

# ==========================
# 🤖 Gera resposta com GPT
# ==========================
def generate_gpt_response(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"⚠️ Erro na API OpenAI: {e}")
        return None

# ==========================
# 📥 Importa histórico de chats
# ==========================
def import_chat_history(file):
    try:
        with open(file, 'r') as f:
            chats = json.load(f)
            for chat in chats:
                date = chat.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                user_input = chat.get('user_input')
                gpt_response = chat.get('gpt_response')
                if user_input and gpt_response:
                    save_chat(date, user_input, gpt_response)
        st.success("✅ Histórico importado com sucesso!")
    except Exception as e:
        st.error(f"⚠️ Erro ao importar histórico: {e}")

# ==========================
# 📤 Exporta chats para Excel
# ==========================
def export_chats_to_excel():
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM chats", conn)
        conn.close()
        df.to_excel('chat_history.xlsx', index=False)
        st.success("✅ Histórico de chats exportado para Excel!")
    except Exception as e:
        st.error(f"⚠️ Erro ao exportar para Excel: {e}")

# ==========================
# 🚀 Interface Streamlit
# ==========================
def main():
    st.title("🤖 Chat History GPT Bot")

    # Importar histórico JSON
    uploaded_file = st.file_uploader("📥 Importar Histórico de Chat (JSON)")
    if uploaded_file is not None:
        with open("imported_chats.json", "wb") as f:
            f.write(uploaded_file.getbuffer())
        import_chat_history("imported_chats.json")

    # Exportar para Excel
    if st.button("📊 Exportar para Excel"):
        export_chats_to_excel()

    # Buscar chats
    search_query = st.text_input("🔎 Buscar Histórico:")
    if st.button("🔍 Buscar"):
        if search_query:
            results = search_chat(search_query)
            for result in results:
                st.write(f"**Pergunta:** {result[0]}")
                st.write(f"**Resposta:** {result[1]}")
                st.write("---")

    # Organizar por clusters
    if st.button("🗂️ Organizar Chats por Tema"):
        clusters = cluster_chats()
        for cluster_id, chats in clusters.items():
            st.write(f"### 🏷️ Tópico {cluster_id + 1}")
            for chat in chats:
                st.write(f"- {chat}")
            st.write("---")

    # Chat com GPT
    user_input = st.text_area("💬 Digite sua mensagem:")
    if st.button("💡 Obter Resposta GPT"):
        if user_input:
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            gpt_response = generate_gpt_response(user_input)
            if gpt_response:
                save_chat(date, user_input, gpt_response)
                st.write(f"**GPT Response:** {gpt_response}")

# ==========================
# ▶️ Execução principal
# ==========================
if __name__ == "__main__":
    create_database()
    main()
