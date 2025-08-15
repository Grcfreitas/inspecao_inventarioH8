import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- Configuração da Página ---
st.set_page_config(
    page_title="Gerenciar Inventário",
    page_icon="📝",
    layout="wide"
)

# --- CONFIGURAÇÕES GERAIS ---
NOME_ARQUIVO_DADOS = 'Inventario-H8 - itens.csv'
COLUNAS = ['BMP', 'Itens', 'apartamento', 'situacao', 'data_atualizacao', 'ultimo_comentario']

# --- FUNÇÕES AUXILIARES ---
def carregar_dados():
    """Carrega os dados do arquivo de inventário e garante que todas as colunas existam."""
    if os.path.exists(NOME_ARQUIVO_DADOS):
        df = pd.read_csv(NOME_ARQUIVO_DADOS, dtype={'BMP': str})
        for col in COLUNAS:
            if col not in df.columns:
                df[col] = ''
    else:
        df = pd.DataFrame(columns=COLUNAS)
    return df

def salvar_dados(df):
    """Salva o DataFrame no arquivo de inventário único."""
    df.to_csv(NOME_ARQUIVO_DADOS, index=False)

# --- Inicialização do Session State ---
if 'item_selecionado' not in st.session_state:
    st.session_state.item_selecionado = None

# --- INTERFACE DA APLICAÇÃO ---
st.title('📝 Gerenciar Inventário H8')
st.write('Use este formulário para adicionar ou atualizar itens no inventário.')
st.info("👈 Para inspecionar um item com a câmera, use o menu na barra lateral.")

# --- ETAPA 1: BUSCAR O ITEM ---
st.subheader("1. Buscar Item para Editar ou Adicionar")
with st.form(key='search_form'):
    codigo_para_buscar = st.text_input('Digite o Código do Item (BMP):', placeholder='Leia ou digite o código')
    buscar_btn = st.form_submit_button('🔎 Buscar / Iniciar Cadastro')

    if buscar_btn and codigo_para_buscar:
        df = carregar_dados()
        item_existente = df[df['BMP'] == codigo_para_buscar]
        if not item_existente.empty:
            st.session_state.item_selecionado = item_existente.iloc[0].to_dict()
        else:
            st.session_state.item_selecionado = {'BMP': codigo_para_buscar, 'Itens': '', 'apartamento': '', 'situacao': ''}
        st.rerun()

# --- ETAPA 2: ADICIONAR OU ATUALIZAR ITEM ---
if st.session_state.item_selecionado:
    item = st.session_state.item_selecionado
    st.subheader(f"2. Editando ou Adicionando Item: {item['BMP']}")

    with st.form(key='edit_form'):
        nome_item = st.text_input('Nome/Descrição do Item:', value=item.get('Itens', ''))
        apartamento = st.text_input('Apartamento:', value=item.get('apartamento', ''))
        situacao = st.text_input('Situação do Item:', value=item.get('situacao', ''))
        
        # MODIFICADO: Comentário agora é opcional dentro de um expander
        with st.expander("Adicionar/Editar Comentário (Opcional)"):
            comentario = st.text_area("Último Comentário:", value=item.get('ultimo_comentario', ''), height=100)
        
        salvar_btn = st.form_submit_button('💾 Salvar Item')

        if salvar_btn:
            if not all([nome_item, apartamento, situacao]):
                st.error('❌ ERRO: Os campos Nome, Apartamento e Situação são obrigatórios!')
            else:
                df = carregar_dados()
                data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                
                if item['BMP'] in df['BMP'].values:
                    # Atualiza o item existente
                    index = df.index[df['BMP'] == item['BMP']][0]
                    df.loc[index, 'Itens'] = nome_item
                    df.loc[index, 'apartamento'] = apartamento
                    df.loc[index, 'situacao'] = situacao
                    df.loc[index, 'data_atualizacao'] = data_atual
                    df.loc[index, 'ultimo_comentario'] = comentario
                    st.success(f'✅ SUCESSO: Item "{nome_item}" (BMP: {item["BMP"]}) foi atualizado!')
                else:
                    # Adiciona o novo item
                    novo_item = pd.DataFrame([{
                        'BMP': item['BMP'], 'Itens': nome_item, 'apartamento': apartamento,
                        'situacao': situacao, 'data_atualizacao': data_atual,
                        'ultimo_comentario': comentario
                    }])
                    df = pd.concat([df, novo_item], ignore_index=True)
                    st.success(f'✅ SUCESSO: Item "{nome_item}" (BMP: {item["BMP"]}) foi cadastrado!')

                salvar_dados(df)
                st.session_state.item_selecionado = None
                st.rerun()

# --- EXIBIÇÃO E EXCLUSÃO DO INVENTÁRIO ---
st.header('📋 Inventário Completo')
df_para_exibir = carregar_dados()

if df_para_exibir.empty:
    st.info('Ainda não há itens no inventário.')
else:
    colunas_visiveis = ['BMP', 'Itens', 'apartamento', 'situacao', 'data_atualizacao', 'ultimo_comentario']
    st.dataframe(df_para_exibir[colunas_visiveis], use_container_width=True)

    with st.expander("🗑️ Apagar Itens do Inventário"):
        with st.form(key='delete_form'):
            st.write("Marque os itens que deseja apagar e clique no botão abaixo.")
            indices_para_apagar = []
            for index, row in df_para_exibir.iterrows():
                label = f"**{row['Itens']}** (Cód: {row['BMP']}, Apto: {row.get('apartamento', 'N/A')}, Situação: {row.get('situacao', 'N/A')})"
                if st.checkbox(label, key=f"delete_{row['BMP']}_{index}"):
                    indices_para_apagar.append(index)
            
            st.warning('ATENÇÃO: A exclusão é permanente!', icon="⚠️")
            botao_apagar = st.form_submit_button('Apagar Itens Selecionados')

            if botao_apagar:
                if not indices_para_apagar:
                    st.warning('Nenhum item foi selecionado para exclusão.')
                else:
                    df_filtrado = df_para_exibir.drop(indices_para_apagar)
                    salvar_dados(df_filtrado)
                    st.success(f'{len(indices_para_apagar)} item(s) foram apagados com sucesso!')
                    st.rerun()
