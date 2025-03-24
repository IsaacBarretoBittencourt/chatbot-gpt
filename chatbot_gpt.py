import streamlit as st
import json
import pandas as pd

# Título do app
st.title("🔎 Consolidador de Chats do GPT")

# Upload do arquivo JSON exportado do ChatGPT
uploaded_file = st.file_uploader("📂 Faça upload do arquivo JSON exportado", type=["json"])

if uploaded_file is not None:
    # Carregar o arquivo JSON
    try:
        data = json.load(uploaded_file)
        st.success("✅ Arquivo carregado com sucesso!")

        # Processar os dados para criar um DataFrame
        chats = []
        for conversation in data.get('conversations', []):
            for message in conversation['messages']:
                chats.append({
                    'data': conversation.get('create_time', ''),
                    'tipo': message.get('author', {}).get('role', ''),
                    'conteudo': message.get('content', '')
                })

        # Criar DataFrame
        df = pd.DataFrame(chats)
        
        # Mostrar os dados processados
        st.write("🗂️ **Consolidado de Chats:**")
        st.dataframe(df)

        # Exportar para CSV
        if st.button("📥 Exportar para CSV"):
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar CSV",
                data=csv,
                file_name='chats_gpt.csv',
                mime='text/csv',
            )
            st.success("✅ Arquivo CSV gerado com sucesso!")

    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {e}")

# Informação adicional
st.write("💡 **Dica:** Após exportar o arquivo CSV, você pode abrir no Excel para organizar melhor por tema ou data.")
