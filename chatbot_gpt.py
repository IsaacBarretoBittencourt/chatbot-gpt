import os
import sqlite3
import openai
from datetime import datetime
from difflib import get_close_matches
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np
import json
import pandas as pd

# Configuração da API GPT
import os
openai.api_key = os.getenv('OPENAI_API_KEY')


# Criação da base de dados
DB_NAME = 'chat_history.db'

def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS chats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT,
                        user_input TEXT,
                        gpt_response TEXT
                    )''')
    conn.commit()
    conn.close()

# Salva chats
def save_chat(date, user_input, gpt_response):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO chats (date, user_input, gpt_response) VALUES (?, ?, ?)',
                   (date, user_input, gpt_response))
    conn.commit()
    conn.close()

# Busca com NLP
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

# Importa o histórico de chats e organiza por tema
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
        model = KMeans(n_clusters=n_clusters)
        model.fit(X)

        clusters = {i: [] for i in range(n_clusters)}
        for i, label in enumerate(model.labels_):
            clusters[label].append(data[i])

        return clusters
    else:
        return {}

# Gera resposta com GPT
def generate_gpt_response(prompt):
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Importar histórico de chats de um arquivo JSON
def import_chat_history(file):
    with open(file, 'r') as f:
        chats = json.load(f)
        for chat in chats:
            date = chat.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            user_input = chat.get('user_input')
            gpt_response = chat.get('gpt_response')
            if user_input and gpt_response:
                save_chat(date, user_input, gpt_response)

# Exportar chats para Excel
def export_chats_to_excel():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM chats", conn)
    conn.close()
    df.to_excel('chat_history.xlsx', index=False)

# Exportar chats para PDF
def export_chats_to_pdf():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM chats", conn)
    conn.close()
    df.to_csv("chat_history.csv", index=False)
    os.system("libreoffice --headless --convert-to pdf chat_history.csv")

# Streamlit interface
import streamlit as st

def main():
    st.title("Chat History GPT Bot")

    # Upload de arquivo JSON
    uploaded_file = st.file_uploader("Import Chat History (JSON)")
    if uploaded_file is not None:
        with open("imported_chats.json", "wb") as f:
            f.write(uploaded_file.getbuffer())
        import_chat_history("imported_chats.json")
        st.success("Chat history imported successfully!")

    # Exportar chats
    if st.button("Export to Excel"):
        export_chats_to_excel()
        st.success("Chat history exported to Excel!")

    if st.button("Export to PDF"):
        export_chats_to_pdf()
        st.success("Chat history exported to PDF!")

    # Search Functionality
    search_query = st.text_input("Search Chat History:")
    if st.button("Search"):
        if search_query:
            results = search_chat(search_query)
            for result in results:
                st.write(f"**User Input:** {result[0]}")
                st.write(f"**GPT Response:** {result[1]}")
                st.write("---")

    # Cluster de chats
    st.subheader("Organized Chats by Topic:")
    if st.button("Organize Chats"):
        clusters = cluster_chats()
        for cluster_id, chats in clusters.items():
            st.write(f"### Topic {cluster_id + 1}")
            for chat in chats:
                st.write(f"- {chat}")
            st.write("---")

    # GPT Chat Functionality
    st.subheader("Chat with GPT:")
    user_input = st.text_area("Type your message:")
    if st.button("Get GPT Response"):
        if user_input:
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            gpt_response = generate_gpt_response(user_input)
            save_chat(date, user_input, gpt_response)
            st.write(f"**GPT Response:** {gpt_response}")

if __name__ == "__main__":
    create_database()
    main()
