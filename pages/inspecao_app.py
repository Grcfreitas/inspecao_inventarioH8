import streamlit as st
import pandas as pd
from PIL import Image
import pytesseract
import os
import re
from datetime import datetime

# --- Configuração do Pytesseract ---
try:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except Exception:
    pass

# --- Título da Página ---
st.title('📦 Sistema de Inspeção por Câmera')
st.write("Aponte a câmera para a etiqueta, identifique o produto e registre seu estado.")

# --- Nomes dos Arquivos ---
NOME_ARQUIVO_DADOS = 'Inventario-H8 - itens.csv'
COLUNAS = ['BMP', 'Itens', 'apartamento', 'situacao', 'data_atualizacao', 'ultimo_comentario']

# --- Funções de Carregamento de Dados (sem cache) ---
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
if 'produto_encontrado' not in st.session_state:
    st.session_state.produto_encontrado = None
if 'numero_lido_ocr' not in st.session_state:
    st.session_state.numero_lido_ocr = ""
if 'item_nao_encontrado_id' not in st.session_state:
    st.session_state.item_nao_encontrado_id = None

# --- Divisão da Tela ---
col1, col2 = st.columns(2)

# --- Coluna da Esquerda: Câmera e Identificação ---
with col1:
    st.header("1. Identificar Produto")
    picture = st.camera_input("Aponte para a etiqueta e tire a foto")

    if picture:
        image = Image.open(picture)
        with st.spinner('Lendo texto da imagem...'):
            try:
                texto_extraido = pytesseract.image_to_string(image)
                match = re.search(r'\d+', texto_extraido)
                numeros_encontrados = match.group(0) if match else ""
                
                st.session_state.numero_lido_ocr = numeros_encontrados
                st.session_state.produto_encontrado = None
                st.session_state.item_nao_encontrado_id = None
            except Exception as e:
                st.error(f"Erro no processamento OCR: {e}")
                st.session_state.numero_lido_ocr = ""

    # Formulário para busca manual ou correção
    with st.form(key="search_form"):
        numero_para_busca = st.text_input(
            "Código do Item (BMP):",
            value=st.session_state.numero_lido_ocr
        )
        buscar_produto_btn = st.form_submit_button("🔎 Buscar Item")

        if buscar_produto_btn:
            st.session_state.produto_encontrado = None
            st.session_state.item_nao_encontrado_id = None
            if numero_para_busca:
                df = carregar_dados()
                produto_info = df[df['BMP'] == numero_para_busca]
                if not produto_info.empty:
                    st.session_state.produto_encontrado = produto_info.iloc[0].to_dict()
                    st.success(f"Item Encontrado: **{st.session_state.produto_encontrado['Itens']}**")
                else:
                    st.warning(f"O item {numero_para_busca} não está no inventário. Cadastre-o abaixo.")
                    st.session_state.item_nao_encontrado_id = numero_para_busca
            else:
                st.warning("Por favor, insira um código para buscar.")

    # --- Formulário para adicionar item não encontrado ---
    if st.session_state.item_nao_encontrado_id:
        st.write("---")
        st.subheader("Cadastrar Novo Item no Inventário")
        with st.form("form_novo_item", clear_on_submit=True):
            codigo_barras = st.session_state.item_nao_encontrado_id
            st.info(f"Cadastrando item com o código: {codigo_barras}")
            
            novo_nome = st.text_input("Nome do Item:", placeholder="Digite a descrição do novo item")
            novo_apto = st.text_input("Apartamento:")
            nova_situacao = st.text_input('Situação do Item:', placeholder='Ex: Em uso, A reparar, etc.')
            
            with st.expander("Adicionar Comentário (Opcional)"):
                comentario = st.text_area("Comentário:", height=100)

            botao_salvar_novo = st.form_submit_button("💾 Salvar Novo Item")

            if botao_salvar_novo:
                if not all([novo_nome, novo_apto, nova_situacao]):
                    st.error("Todos os campos são obrigatórios!")
                else:
                    df = carregar_dados()
                    if codigo_barras in df['BMP'].values:
                        st.error(f"O código {codigo_barras} já existe no inventário.")
                    else:
                        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        novo_item = pd.DataFrame([{'BMP': codigo_barras, 'Itens': novo_nome, 'apartamento': novo_apto, 'situacao': nova_situacao, 'data_atualizacao': data_atual, 'ultimo_comentario': comentario}])
                        df_atualizado = pd.concat([df, novo_item], ignore_index=True)
                        salvar_dados(df_atualizado)
                        st.success(f"Item '{novo_nome}' adicionado ao inventário!")
                        st.session_state.item_nao_encontrado_id = None
                        st.rerun()

# --- Coluna da Direita: Atualização e Inspeção ---
with col2:
    st.header("2. Atualizar e Inspecionar")

    if st.session_state.produto_encontrado:
        produto = st.session_state.produto_encontrado
        st.markdown(f"**Item Selecionado:**")
        st.markdown(f"### {produto['Itens']} (ID: {produto['BMP']})")
        
        with st.form(key="inspection_form"):
            st.write(f"**Apartamento Atual:** {produto.get('apartamento', 'N/A')}")
            
            nova_situacao = st.text_input("Atualizar Situação para:", value=produto.get('situacao', ''))
            
            with st.expander("Adicionar/Editar Comentário de Inspeção (Opcional)"):
                comentario = st.text_area("Comentário:", value=produto.get('ultimo_comentario', ''), height=100)
            
            submit_button = st.form_submit_button("Salvar Alterações")

            if submit_button:
                df = carregar_dados()
                idx = df.index[df['BMP'] == produto['BMP']].tolist()
                if idx:
                    index = idx[0]
                    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    df.loc[index, 'situacao'] = nova_situacao
                    df.loc[index, 'ultimo_comentario'] = comentario
                    df.loc[index, 'data_atualizacao'] = data_atual
                    salvar_dados(df)
                    st.success(f"Item {produto['BMP']} atualizado com sucesso!")
                    st.session_state.produto_encontrado = None
                    st.rerun()
                else:
                    st.error("Ocorreu um erro ao tentar salvar. Item não encontrado.")
    else:
        st.info("Busque ou identifique um item para atualizar.")
