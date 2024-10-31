import streamlit as st
import pandas as pd
import requests
import time
from io import BytesIO

# st.markdown(
#     """
#     <style>
#         section[data-testid="stSidebar"] {
#             width: 100px !important; # Set the width to your desired value
#         }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

@st.cache_data
def converte_csv(df):
    return df.to_csv(index=False).encode('utf-8')

def converte_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        
    processed_data = output.getvalue()
    return processed_data

def mensagem_sucesso():
    sucesso = st.success('Download realizado com sucesso!', icon="✅")
    time.sleep(5)
    sucesso.empty()

st.title('Dados Brutos')

@st.cache_data
def get_data():
    url = 'https://labdados.com/produtos'
    reponse = requests.get(url)
    return pd.DataFrame.from_dict(reponse.json())

dados = get_data()
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

with st.expander('Colunas'):
    colunas = st.multiselect('Selecione as colunas', list(dados.columns), list(dados.columns))
    colunas_existentes = [col for col in colunas if col in dados.columns]

st.sidebar.title('Filtros')

with st.sidebar.expander('Nome do produto'):
    produtos = st.multiselect('Selecione os produtos', dados['Produto'].unique(), dados['Produto'].unique())

with st.sidebar.expander('Preço do produto'):
    preco = st.slider('Selecione o preço', 0, 5000, (0, 5000))

with st.sidebar.expander('Data da Compra'):
    data_compra = st.date_input('Selecione a data', (dados['Data da Compra'].min(), dados['Data da Compra'].max()))

query = """
    Produto in @produtos and \
    @preco[0] <= Preço <= @preco[1] and \
    @data_compra[0] <= `Data da Compra` <= @data_compra[1]
"""

dados_filtrados = dados.query(query)

if colunas_existentes:
    dados_filtrados = dados[colunas_existentes]
else:
    st.error("Nenhuma das colunas especificadas existe no DataFrame.")

st.dataframe(dados_filtrados)

st.markdown(f'## A tabela possui :blue[{dados_filtrados.shape[0]}] linhas e :blue[{dados_filtrados.shape[1]}] colunas')

st.markdown('Escreva um nome para o arquivo')

col1, col2 = st.columns(2)

with col1:
    nome_arquivo = st.text_input('', label_visibility='collapsed', value='dados')
    nome_arquivo += '.xlsx'

with col2:
    st.download_button('Fazer o download da tabela em Excel', 
                        data=converte_excel(dados_filtrados), 
                        file_name=nome_arquivo, 
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                        on_click=mensagem_sucesso)
