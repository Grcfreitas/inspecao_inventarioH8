import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURAÇÕES GERAIS ---
NOME_ARQUIVO_DADOS = 'inventario_geral_h8.csv'
# Colunas unificadas para compatibilidade com a página de inspeção
COLUNAS = [
    'codigo_barras', 'nome_item', 'apartamento', 'situacao',
    'data_cadastro', 'data_atualizacao', 'ultimo_comentario'
]

# --- FUNÇÕES AUXILIARES ---
def carregar_dados():
    """
    Carrega os dados do arquivo CSV, criando o arquivo ou colunas se não existirem.
    """
    if os.path.exists(NOME_ARQUIVO_DADOS):
        df = pd.read_csv(NOME_ARQUIVO_DADOS, dtype={'codigo_barras': str})
        # Garante que todas as colunas necessárias existam
        for col in COLUNAS:
            if col not in df.columns:
                df[col] = ''
    else:
        df = pd.DataFrame(columns=COLUNAS)
    return df

def salvar_dados(df):
    """
    Salva o DataFrame completo no arquivo CSV.
    """
    df.to_csv(NOME_ARQUIVO_DADOS, index=False)

# --- TÍTULO PRINCIPAL ---
st.set_page_config(layout="wide")
st.title('📦 Sistema de Inventário H8')
st.write('Use as abas abaixo para gerenciar seu inventário.')

# --- ABAS DE NAVEGAÇÃO ---
tab1, tab2 = st.tabs(["✍️ Cadastrar / Apagar Itens", "📋 Visualizar Inventário"])

# --- Aba 1: Cadastro e Deleção ---
with tab1:
    st.header('Adicionar Novo Item')
    with st.form(key='cadastro_form', clear_on_submit=True):
        codigo_barras = st.text_input('Código de Barras do Item:', placeholder='Leia ou digite o código')
        nome_item = st.text_input('Nome do Item:', placeholder='Ex: Cadeira de Escritório')
        apartamento = st.text_input('Apartamento:', placeholder='Ex: 101A')
        opcoes_situacao = ['Em uso', 'Bem cedido', 'Est. distrib.', 'Aguard. confirmação', 'A alienar', 'Est. interno', 'Em reparo', 'A reparar', 'Em trânsito']
        situacao = st.selectbox('Situação Inicial do Item:', options=opcoes_situacao)

        botao_cadastrar = st.form_submit_button('💾 Cadastrar Item')
        if botao_cadastrar:
            df_inventario = carregar_dados()
            if not all([codigo_barras, nome_item, apartamento]):
                st.error('❌ ERRO: Todos os campos são obrigatórios!')
            elif codigo_barras in df_inventario['codigo_barras'].values:
                st.error(f'❌ ERRO: O código "{codigo_barras}" já foi cadastrado!')
            else:
                data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                novo_item = {
                    'codigo_barras': codigo_barras, 'nome_item': nome_item,
                    'apartamento': apartamento, 'situacao': situacao,
                    'data_cadastro': data_atual, 'data_atualizacao': '', 'ultimo_comentario': ''
                }
                df_atualizado = pd.concat([df_inventario, pd.DataFrame([novo_item])], ignore_index=True)
                salvar_dados(df_atualizado)
                st.success(f'✅ SUCESSO: Item "{nome_item}" cadastrado!')
                st.rerun()

    st.divider()

    st.header('🗑️ Apagar Itens')
    df_inventario = carregar_dados()
    if not df_inventario.empty:
        with st.form(key='delete_form'):
            codigos_para_apagar = []
            for index, row in df_inventario.iterrows():
                label = f"**{row['nome_item']}** (Cód: {row['codigo_barras']}, Apto: {row['apartamento']})"
                if st.checkbox(label, key=f"delete_{row['codigo_barras']}"):
                    codigos_para_apagar.append(row['codigo_barras'])
            
            botao_apagar = st.form_submit_button('Apagar Itens Selecionados')
            if botao_apagar:
                if codigos_para_apagar:
                    df_filtrado = df_inventario[~df_inventario['codigo_barras'].isin(codigos_para_apagar)]
                    salvar_dados(df_filtrado)
                    st.success(f'{len(codigos_para_apagar)} item(s) apagados com sucesso!')
                    st.rerun()
                else:
                    st.warning('Nenhum item foi selecionado.')

# --- Aba 2: Visualização do Inventário ---
with tab2:
    st.header('Inventário Completo')
    df_para_exibir = carregar_dados()

    if df_para_exibir.empty:
        st.info('Ainda não há itens cadastrados no inventário.')
    else:
        # Layout de colunas para exibir o inventário com o botão de ação
        col_headers = st.columns((1, 2, 1, 1, 1.5, 1.5, 3, 1))
        headers = ["Cód. Barras", "Nome", "Apto", "Situação", "Cadastro", "Últ. Atualização", "Últ. Comentário", "Ação"]
        for col, header in zip(col_headers, headers):
            col.write(f"**{header}**")
        
        st.divider()

        for index, row in df_para_exibir.iterrows():
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns((1, 2, 1, 1, 1.5, 1.5, 3, 1))
            col1.write(row['codigo_barras'])
            col2.write(row['nome_item'])
            col3.write(row['apartamento'])
            col4.write(row['situacao'])
            col5.write(str(row.get('data_cadastro', '')))
            col6.write(str(row.get('data_atualizacao', '')))
            col7.write(str(row.get('ultimo_comentario', '')))
            
            # Botão que chama a outra página
            if col8.button('Inspecionar', key=f"inspect_{row['codigo_barras']}"):
                 st.switch_page("pages/pagina_inspecao.py")