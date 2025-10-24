import streamlit as st
import pandas as pd
from PIL import Image
import pytesseract
import os
import re
from datetime import datetime
import google.generativeai as genai

# --- Configuração do Pytesseract ---
try:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except Exception:
    pass

# --- Configuração da Página ---
st.set_page_config(
    page_title="Inventário Inteligente com Gemini",
    page_icon="🤖",
    layout="wide"
)

# --- Barra Lateral para Configuração da IA ---
with st.sidebar:
    st.header("🤖 Configuração da IA")
    gemini_api_key = st.text_input(
        "Chave da API do Google Gemini",
        type="password",
        help="Obtenha sua chave em https://aistudio.google.com/app/apikey"
    )
    if gemini_api_key:
        st.session_state.gemini_api_key = gemini_api_key
        st.success("API Key inserida!", icon="✅")

# --- Título da Página ---
st.title('📦 Sistema de Inspeção por Câmera com IA')
st.write("Aponte a câmera, identifique o produto e use a IA para registrar seu estado.")

# --- Nomes dos Arquivos e Colunas (Seu original) ---
NOME_ARQUIVO_DADOS = 'Inventario-H8 - itens.csv'
COLUNAS = ['BMP', 'Itens', 'apartamento', 'situacao', 'data_atualizacao', 'ultimo_comentario']

# --- Funções ---

# ↓↓↓ CORREÇÃO APLICADA AQUI ↓↓↓
def preprocess_image_for_ocr(image):
    """Converte a imagem para escala de cinza, que o Tesseract (OEM 3) processa bem."""
    grayscale_image = image.convert('L')
    # Remoção da binarização manual (threshold). 
    # Deixar o Tesseract lidar com a escala de cinza é melhor para superfícies reflexivas.
    return grayscale_image

def carregar_dados():
    if os.path.exists(NOME_ARQUIVO_DADOS):
        df = pd.read_csv(NOME_ARQUIVO_DADOS, dtype={'BMP': str})
        for col in COLUNAS:
            if col not in df.columns:
                df[col] = ''
    else:
        df = pd.DataFrame(columns=COLUNAS)
    return df

def salvar_dados(df):
    df.to_csv(NOME_ARQUIVO_DADOS, index=False)

def analisar_imagem_com_gemini(api_key, imagem, prompt):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([prompt, imagem])
        return response.text
    except Exception as e:
        return f"Erro ao conectar com a API do Gemini: {e}"

# --- Inicialização do Session State ---
if 'produto_encontrado' not in st.session_state:
    st.session_state.produto_encontrado = None
if 'numero_lido_ocr' not in st.session_state:
    st.session_state.numero_lido_ocr = ""
if 'item_nao_encontrado_id' not in st.session_state:
    st.session_state.item_nao_encontrado_id = None
if 'ai_comment' not in st.session_state:
    st.session_state.ai_comment = ""
if 'inspection_mode' not in st.session_state:
    st.session_state.inspection_mode = None # 'choice', 'camera_ia' ou 'manual'

# --- Divisão da Tela ---
col1, col2 = st.columns(2)

# --- Coluna da Esquerda: Câmera e Identificação ---
with col1:
    st.header("1. Identificar Produto")
    picture_label = st.camera_input("Aponte para a ETIQUETA e tire a foto")

    if picture_label:
        image = Image.open(picture_label)
        with st.spinner('Lendo texto da etiqueta...'):
            try:
                preprocessed_image = preprocess_image_for_ocr(image)
                
                # ↓↓↓ CORREÇÃO APLICADA AQUI ↓↓↓
                # ATUALIZAÇÃO: Mudando de psm 6 para 11 (Sparse text) para melhor detecção
                custom_config = r'--oem 3 --psm 11 -c tessedit_char_whitelist=0123456789'
                
                texto_extraido = pytesseract.image_to_string(preprocessed_image, config=custom_config)
                match = re.search(r'\d+', texto_extraido)
                st.session_state.numero_lido_ocr = match.group(0) if match else ""
            except Exception as e:
                st.error(f"Erro no processamento OCR: {e}")
                st.session_state.numero_lido_ocr = ""

    with st.form(key="search_form"):
        numero_para_busca = st.text_input("Código do Item (BMP):", value=st.session_state.numero_lido_ocr)
        buscar_produto_btn = st.form_submit_button("🔎 Buscar Item")

        if buscar_produto_btn:
            st.session_state.produto_encontrado = None
            st.session_state.item_nao_encontrado_id = None
            st.session_state.ai_comment = ""
            st.session_state.inspection_mode = None
            
            if numero_para_busca:
                df = carregar_dados()
                produto_info = df[df['BMP'] == numero_para_busca]
                if not produto_info.empty:
                    st.session_state.produto_encontrado = produto_info.iloc[0].to_dict()
                    st.session_state.inspection_mode = 'choice'
                else:
                    st.warning(f"O item {numero_para_busca} não está no inventário. Cadastre-o abaixo.")
                    st.session_state.item_nao_encontrado_id = numero_para_busca
            else:
                st.warning("Por favor, insira um código para buscar.")
    
    if st.session_state.produto_encontrado:
        st.success(f"Item Encontrado: **{st.session_state.produto_encontrado['Itens']}**")

    if st.session_state.item_nao_encontrado_id:
        st.write("---")
        st.subheader("Cadastrar Novo Item no Inventário")
        # (código de cadastro omitido para brevidade, mas está no seu original)

# --- Coluna da Direita: Atualização e Inspeção ---
with col2:
    st.header("2. Atualizar e Inspecionar")

    if st.session_state.produto_encontrado:
        produto = st.session_state.produto_encontrado
        st.markdown(f"**Item Selecionado:**")
        st.markdown(f"### {produto['Itens']} (ID: {produto['BMP']})")

        # Escolha de Ação
        if st.session_state.inspection_mode == 'choice':
            if st.button("📸 Analisar com Câmera (IA)"):
                st.session_state.inspection_mode = 'camera_ia'
                st.rerun()
            if st.button("✍️ Atualizar Manualmente"):
                st.session_state.inspection_mode = 'manual'
                st.rerun()

        # Modo Câmera IA
        elif st.session_state.inspection_mode == 'camera_ia':
            st.info("Agora tire uma foto do ITEM COMPLETO para a análise da IA.")
            picture_item = st.camera_input("Aponte para o ITEM e tire a foto", key="analysis_camera")

            if picture_item:
                if 'gemini_api_key' not in st.session_state or not st.session_state.gemini_api_key:
                    st.error("AVISO: Chave da API do Gemini não inserida. Por favor, insira a chave na barra lateral para continuar.")
                else:
                    with st.spinner("A IA está analisando a imagem do item..."):
                        img_para_analise = Image.open(picture_item)
                        prompt = "Descreva o estado de conservação do objeto principal nesta imagem. Foque em detalhes como arranhões, amassados, manchas, rasgos ou qualquer outro defeito visível. Se o objeto parecer estar em bom estado, mencione isso também."
                        st.session_state.ai_comment = analisar_imagem_com_gemini(st.session_state.gemini_api_key, img_para_analise, prompt)
                    
                    st.session_state.inspection_mode = 'manual'
                    st.rerun()

        # Modo Formulário (Manual ou Pós-IA)
        elif st.session_state.inspection_mode == 'manual':
            with st.form(key="inspection_form"):
                st.write(f"**Apartamento Atual:** {produto.get('apartamento', 'N/A')}")
                nova_situacao = st.text_input("Atualizar Situação para:", value=produto.get('situacao', ''))
                
                comentario_valor_inicial = st.session_state.ai_comment if st.session_state.ai_comment else produto.get('ultimo_comentario', '')
                comentario = st.text_area("Comentário de Inspeção:", value=comentario_valor_inicial, height=150)
                
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
                        st.session_state.ai_comment = ""
                        st.session_state.inspection_mode = None
                        st.rerun()
                    else:
                        st.error("Ocorreu um erro ao tentar salvar. Item não encontrado.")
    else:
        st.info("Busque e identifique um item para atualizar.")
