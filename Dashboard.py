import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(layout='wide')
regioes = ['Brasil', 'Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul']
url = 'https://labdados.com/produtos'


with st.sidebar:
    st.sidebar.success('Select page above.')
    st.sidebar.title('Filtros')
    regiao = st.sidebar.selectbox('Região', regioes)

    if regiao == 'Brasil':
        regiao = ''

    todos_anos = st.sidebar.checkbox('Dados de todo o período', value=True)

    if todos_anos:
        ano = ''
    else:
        ano = st.sidebar.slider('Ano', 2020, 2023)

    

query_string = {'regiao': regiao.lower(), 'ano': ano}

def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if abs(valor) < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    
    return f'{prefixo} {valor:.2f} milhões'

@st.cache_data
def fetch_data(url, query_string = {}):
    response = requests.get(url, params=query_string)
    return pd.DataFrame.from_dict(response.json())

st.title('Dashboard de Vendas :shopping_trolley:')

df = fetch_data(url, query_string)

df['Data da compra'] = pd.to_datetime(df['Data da Compra'], format='%d/%m/%Y')

filtro_vendedores = st.sidebar.multiselect('Vendedores', df['Vendedor'].unique())

if filtro_vendedores:
    df = df[df['Vendedor'].isin(filtro_vendedores)]


## TABELAS

receita_estados = df.groupby('Local da compra')[['Preço']].sum()
receita_estados = df.drop_duplicates(
    subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(
        receita_estados, left_on='Local da compra', 
        right_index=True).sort_values('Preço', ascending=False)

receita_mensal = df.set_index('Data da compra').groupby(
    pd.Grouper(freq='M'))[['Preço']].sum().reset_index()
receita_mensal['Mes'] = receita_mensal['Data da compra'].dt.month_name()
receita_mensal['Ano'] = receita_mensal['Data da compra'].dt.year

receita_categorias = df.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

vendedores = pd.DataFrame(df.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

## GRAFICOS

fig_mapa_receita = px.scatter_geo(receita_estados, 
                                    lat='lat', 
                                    lon='lon', 
                                    scope = 'south america',
                                    size='Preço', 
                                    template='seaborn',
                                    hover_name='Local da compra',
                                    hover_data={'lat': False, 'lon': False},
                                    title='Receita por Estado')

fig_receita_mensal = px.line(receita_mensal,
                                x='Mes',
                                y='Preço',
                                markers=True,
                                range_y=(receita_mensal['Preço'].min()-10000, 
                                         receita_mensal['Preço'].max()+10000),
                                color='Ano',
                                line_dash='Ano',
                                title='Receita Mensal')

fig_receita_mensal.update_layout(yaxis_title='Receita')
fig_receita_mensal.update_layout(legend=dict(
    orientation='h',
    yanchor='bottom',
    y=-0.5,
    xanchor='right',
    x=1,

))

fig_receita_estados = px.bar(receita_estados.head(5),
                                x='Local da compra',
                                y='Preço',
                                text_auto=True,
                                title='Top Estados (receita)')

fig_receita_mensal.update_layout(yaxis_title='Receita')

fig_receita_categorias = px.bar(receita_categorias,
                                text_auto=True,
                                title='Receita por Categoria')

fig_receita_categorias.update_layout(yaxis_title='Receita')

## VISUALIZAÇÃO

aba1, aba2, aba3, aba4 = st.tabs(['Receita', 'Quantidade de Vendas', 'Vendedores', 'Tabela'])

with aba1:
    col1, col2 = st.columns(2)
    with col1:
        st.metric('Receita', formata_numero(df['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_estados, use_container_width=True)

    with col2:
        col2.metric('Quantidade de Produtos', formata_numero(df.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categorias, use_container_width=True)

with aba2:
    col1, col2 = st.columns(2)
    with col1:
        st.metric('Receita', formata_numero(df['Preço'].sum(), 'R$'))

    with col2:
        st.metric('Quantidade de Produtos', formata_numero(df.shape[0]))

with aba3:
    qtd_vendedores = st.number_input('Quantidade de Vendedores', 2, 10, 5)

    col1, col2 = st.columns(2)
    with col1:
        st.metric('Receita', formata_numero(df['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending=True).head(qtd_vendedores),
                                        x = 'sum',
                                        y = vendedores[['sum']].sort_values('sum', ascending=True).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title=f'Top {qtd_vendedores} Vendedores (receita)')
        st.plotly_chart(fig_receita_vendedores, use_container_width=True)

    with col2:
        st.metric('Quantidade de Produtos', formata_numero(df.shape[0]))
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending=True).head(qtd_vendedores),
                                        x = 'count',
                                        y = vendedores[['count']].sort_values('count', ascending=True).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title=f'Top {qtd_vendedores} Vendedores (quantidade de vendas)')
        st.plotly_chart(fig_vendas_vendedores, use_container_width=True)

with aba4:
    st.dataframe(df)