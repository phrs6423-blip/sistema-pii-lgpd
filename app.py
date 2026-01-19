"""
Sistema de Gestão de PII - Conformidade LGPD
=============================================

Interface visual para detecção e gestão de dados pessoais
conforme a Lei Geral de Proteção de Dados (Brasil).

MELHORIAS DE UX/UI:
- Auto-processamento após upload
- Wizard visual de 4 passos
- Modais de sucesso destacados
- Download imediato após mascaramento
- Fluxo lógico de abas
- Breadcrumb na sidebar

Execute: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import sys
import os
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from detector import PIIDetector

# Configuração da página
st.set_page_config(
    page_title="Gestão de PII - LGPD",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para interface brasileira com UX melhorado
st.markdown("""
<style>
    /* Cabeçalho principal */
    .main-header {
        background: linear-gradient(135deg, #009c3b 0%, #002776 50%, #ffdf00 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* Cards de métricas */
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #009c3b;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Zona de perigo (vermelho) - TEXTO LEGÍVEL */
    .danger-zone {
        background: linear-gradient(135deg, #ffe6e6 0%, #ffcccc 100%);
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #ff4b4b;
        box-shadow: 0 2px 4px rgba(255,75,75,0.1);
        color: #1a1a1a;
    }
    .danger-zone h4 {
        color: #c92a2a;
        font-weight: 700;
    }
    .danger-zone p, .danger-zone ul, .danger-zone li {
        color: #2d2d2d;
    }

    /* Zona de sucesso (verde) - TEXTO LEGÍVEL */
    .success-zone {
        background: linear-gradient(135deg, #e6ffe6 0%, #ccffcc 100%);
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #00cc44;
        box-shadow: 0 2px 4px rgba(0,204,68,0.1);
        color: #1a1a1a;
    }
    .success-zone h4 {
        color: #2b8a3e;
        font-weight: 700;
    }
    .success-zone p, .success-zone ul, .success-zone li {
        color: #2d2d2d;
    }

    /* Zona de aviso (amarelo) */
    .warning-zone {
        background: linear-gradient(135deg, #fff4e6 0%, #ffe6cc 100%);
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #ff9800;
        box-shadow: 0 2px 4px rgba(255,152,0,0.1);
        color: #1a1a1a;
    }

    /* Modal de sucesso destacado */
    .success-modal {
        background: linear-gradient(135deg, #00cc44 0%, #009c3b 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 8px 16px rgba(0,204,68,0.3);
        margin: 20px 0;
        font-size: 18px;
    }
    .success-modal h2 {
        color: white;
        font-size: 32px;
        margin-bottom: 10px;
    }

    /* Wizard de passos */
    .wizard-step {
        display: inline-block;
        padding: 10px 20px;
        margin: 5px;
        border-radius: 25px;
        font-weight: 600;
        font-size: 14px;
    }
    .wizard-step-active {
        background: #009c3b;
        color: white;
        border: 2px solid #009c3b;
    }
    .wizard-step-completed {
        background: #00cc44;
        color: white;
        border: 2px solid #00cc44;
    }
    .wizard-step-pending {
        background: #f0f0f0;
        color: #666;
        border: 2px solid #ddd;
    }

    /* Botões aprimorados */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }

    /* Métricas */
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
    }

    /* Breadcrumb visual */
    .breadcrumb {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        border-left: 4px solid #009c3b;
    }
    .breadcrumb-item {
        display: inline-block;
        margin-right: 10px;
        color: #666;
    }
    .breadcrumb-item-active {
        color: #009c3b;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Inicializa o estado da sessão."""
    if 'df_original' not in st.session_state:
        st.session_state.df_original = None
    if 'df_analisado' not in st.session_state:
        st.session_state.df_analisado = None
    if 'df_mascarado_limpo' not in st.session_state:
        st.session_state.df_mascarado_limpo = None
    if 'coluna_texto' not in st.session_state:
        st.session_state.coluna_texto = None
    if 'detector' not in st.session_state:
        with st.spinner('Carregando modelo de IA...'):
            st.session_state.detector = PIIDetector()
    if 'historico_acoes' not in st.session_state:
        st.session_state.historico_acoes = []
    if 'passo_atual' not in st.session_state:
        st.session_state.passo_atual = 1
    if 'arquivo_mascarado_path' not in st.session_state:
        st.session_state.arquivo_mascarado_path = None


def exibir_wizard():
    """Exibe wizard visual de 4 passos."""
    passos = [
        ("1️⃣ Upload", 1),
        ("2️⃣ Análise", 2),
        ("3️⃣ Mascaramento", 3),
        ("4️⃣ Resultados", 4)
    ]

    passo_atual = st.session_state.passo_atual

    wizard_html = '<div style="text-align: center; margin: 20px 0;">'
    for nome, num in passos:
        if num < passo_atual:
            classe = "wizard-step wizard-step-completed"
        elif num == passo_atual:
            classe = "wizard-step wizard-step-active"
        else:
            classe = "wizard-step wizard-step-pending"

        wizard_html += f'<span class="{classe}">{nome}</span>'

    wizard_html += '</div>'
    st.markdown(wizard_html, unsafe_allow_html=True)


def anonimizar_dados(df: pd.DataFrame, tipos_pii: list, modo: str, coluna_texto: str = None) -> pd.DataFrame:
    """
    Anonimiza dados pessoais conforme LGPD usando modos da classe PIIDetector.

    Args:
        df: DataFrame com dados
        tipos_pii: Lista de tipos a anonimizar ['cpf', 'email', etc.] ou 'todos'
        modo: 'PARCIAL' ou 'PROTECAO_TOTAL'
        coluna_texto: Nome da coluna com texto original para mascarar

    Returns:
        DataFrame anonimizado
    """
    df_anonimizado = df.copy()
    detector = st.session_state.detector

    # Se coluna_texto foi fornecida, aplica mascaramento direto no texto
    if coluna_texto and coluna_texto in df_anonimizado.columns:
        progress_bar = st.progress(0)
        status_text = st.empty()

        textos = df_anonimizado[coluna_texto].fillna("").astype(str).tolist()
        total = len(textos)

        # Aplica mascaramento em batch
        textos_mascarados = []
        batch_size = 100

        for i in range(0, total, batch_size):
            batch = textos[i:i+batch_size]
            mascarados = detector.apply_masking_batch(batch, mode=modo)
            textos_mascarados.extend(mascarados)

            progress = min((i + batch_size) / total, 1.0)
            progress_bar.progress(progress)
            status_text.text(f'Mascarando: {i+batch_size}/{total} registros')

        df_anonimizado[coluna_texto] = textos_mascarados
        progress_bar.empty()
        status_text.empty()

    # Também atualiza as colunas de PII detectadas
    if modo == 'PROTECAO_TOTAL':
        # Substitui todas as listas de PII por [INFORMAÇÃO PROTEGIDA LGPD]
        if 'todos' in tipos_pii or len(tipos_pii) > 0:
            for tipo in ['cpf', 'rg', 'email', 'telefone', 'nome']:
                if 'todos' in tipos_pii or tipo in tipos_pii:
                    if f'pii_{tipo}_lista' in df_anonimizado.columns:
                        # Substitui valores não vazios
                        mask = df_anonimizado[f'pii_{tipo}_lista'] != ''
                        df_anonimizado.loc[mask, f'pii_{tipo}_lista'] = '[INFORMAÇÃO PROTEGIDA LGPD]'

    elif modo == 'PARCIAL':
        # Mascara individualmente cada PII
        for idx, row in df_anonimizado.iterrows():
            if 'todos' in tipos_pii or 'cpf' in tipos_pii:
                # CPF VALIDADO - mascara separadamente
                if row.get('pii_cpf_validado_lista') and row['pii_cpf_validado_lista'] != '':
                    cpfs = str(row['pii_cpf_validado_lista']).split(';')
                    cpfs_mascarados = [detector._mascara_cpf_parcial(c) for c in cpfs if c]
                    df_anonimizado.at[idx, 'pii_cpf_validado_lista'] = ';'.join(cpfs_mascarados)

                # CPF NÃO VALIDADO - mascara separadamente
                if row.get('pii_cpf_nao_validado_lista') and row['pii_cpf_nao_validado_lista'] != '':
                    cpfs = str(row['pii_cpf_nao_validado_lista']).split(';')
                    cpfs_mascarados = [detector._mascara_cpf_parcial(c) for c in cpfs if c]
                    df_anonimizado.at[idx, 'pii_cpf_nao_validado_lista'] = ';'.join(cpfs_mascarados)

            if 'todos' in tipos_pii or 'rg' in tipos_pii:
                if row.get('pii_rg_lista') and row['pii_rg_lista'] != '':
                    rgs = str(row['pii_rg_lista']).split(';')
                    rgs_mascarados = [detector._mascara_rg_parcial(r) for r in rgs if r]
                    df_anonimizado.at[idx, 'pii_rg_lista'] = ';'.join(rgs_mascarados)

            if 'todos' in tipos_pii or 'email' in tipos_pii:
                if row.get('pii_email_lista') and row['pii_email_lista'] != '':
                    emails = str(row['pii_email_lista']).split(';')
                    emails_mascarados = [detector._mascara_email_parcial(e) for e in emails if e]
                    df_anonimizado.at[idx, 'pii_email_lista'] = ';'.join(emails_mascarados)

            if 'todos' in tipos_pii or 'telefone' in tipos_pii:
                if row.get('pii_telefone_lista') and row['pii_telefone_lista'] != '':
                    tels = str(row['pii_telefone_lista']).split(';')
                    tels_mascarados = [detector._mascara_telefone_parcial(t) for t in tels if t]
                    df_anonimizado.at[idx, 'pii_telefone_lista'] = ';'.join(tels_mascarados)

            if 'todos' in tipos_pii or 'nome' in tipos_pii:
                if row.get('pii_nome_lista') and row['pii_nome_lista'] != '':
                    nomes = str(row['pii_nome_lista']).split(';')
                    nomes_mascarados = [detector._mascara_nome_parcial(n) for n in nomes if n]
                    df_anonimizado.at[idx, 'pii_nome_lista'] = ';'.join(nomes_mascarados)

    # Registra ação no histórico
    st.session_state.historico_acoes.append({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'acao': f'Mascaramento {modo}',
        'tipos': ', '.join(tipos_pii) if tipos_pii != ['todos'] else 'Todos os tipos',
        'registros': len(df),
        'coluna_processada': coluna_texto if coluna_texto else 'Apenas listas de PII'
    })

    return df_anonimizado


def analisar_arquivo(df: pd.DataFrame, coluna_texto: str) -> pd.DataFrame:
    """
    Analisa o arquivo e detecta PII usando detector híbrido.

    Nova estrutura retorna:
    - verificado: dados validados matematicamente
    - suspeito: padrão correto mas falhou validação
    - score_risco: 0.0 a 1.0
    """
    detector = st.session_state.detector

    # Cria barra de progresso
    progress_bar = st.progress(0)
    status_text = st.empty()

    textos = df[coluna_texto].fillna("").astype(str).tolist()
    total = len(textos)

    # Processa em lotes
    batch_size = 100
    all_results = []

    for i in range(0, total, batch_size):
        batch = textos[i:i+batch_size]
        results = detector.detect_pii_batch(batch, batch_size=50)
        all_results.extend(results)

        progress = min((i + batch_size) / total, 1.0)
        progress_bar.progress(progress)
        status_text.text(f'Analisando: {i+batch_size}/{total} registros (Pipeline Híbrido)')

    progress_bar.empty()
    status_text.empty()

    # Adiciona resultados ao DataFrame (nova estrutura)
    df['contém_pii'] = [r['contem_pii'] for r in all_results]
    df['score_risco'] = [r['score_risco'] for r in all_results]

    # ===================================================================
    # IMPORTANTE: APENAS CPF TEM DUAS CATEGORIAS DIFERENTES!
    # - CPF VALIDADO: Validado matematicamente (Módulo 11) - CPF real
    # - CPF NÃO VALIDADO: Padrão correto mas falhou validação - Erro de digitação
    # ===================================================================

    # CPF - DUAS CATEGORIAS SEPARADAS (ÚNICA SEPARAÇÃO NO SISTEMA)
    df['cpf_validado'] = [len(r['entidades']['cpf']['verificado']) for r in all_results]
    df['cpf_nao_validado'] = [len(r['entidades']['cpf']['suspeito']) for r in all_results]

    # RG (verificado + suspeito somados)
    df['rg_verificado'] = [len(r['entidades']['rg']['verificado']) for r in all_results]
    df['rg_suspeito'] = [len(r['entidades']['rg']['suspeito']) for r in all_results]
    df['rg_detectado'] = df['rg_verificado'] + df['rg_suspeito']

    # E-mail (verificado + suspeito somados)
    df['email_verificado'] = [len(r['entidades']['email']['verificado']) for r in all_results]
    df['email_suspeito'] = [len(r['entidades']['email']['suspeito']) for r in all_results]
    df['email_detectado'] = df['email_verificado'] + df['email_suspeito']

    # Telefone (verificado + suspeito somados)
    df['telefone_verificado'] = [len(r['entidades']['telefone']['verificado']) for r in all_results]
    df['telefone_suspeito'] = [len(r['entidades']['telefone']['suspeito']) for r in all_results]
    df['telefone_detectado'] = df['telefone_verificado'] + df['telefone_suspeito']

    # Nome (NLP)
    df['nome_detectado'] = [len(r['entidades']['nlp_contexto']['pessoas']) for r in all_results]

    # Endereço
    df['endereco_detectado'] = [len(r['entidades']['endereco']['detectado']) for r in all_results]

    # ===================================================================
    # LISTAS DETALHADAS - CPF TEM DUAS COLUNAS SEPARADAS!
    # ===================================================================

    # CPF - DUAS COLUNAS SEPARADAS
    df['pii_cpf_validado_lista'] = [';'.join(r['entidades']['cpf']['verificado']) for r in all_results]
    df['pii_cpf_nao_validado_lista'] = [';'.join(r['entidades']['cpf']['suspeito']) for r in all_results]

    # Outros - UMA COLUNA SÓ (verificado + suspeito juntos)
    df['pii_rg_lista'] = [';'.join(r['entidades']['rg']['verificado'] + r['entidades']['rg']['suspeito']) for r in all_results]
    df['pii_email_lista'] = [';'.join(r['entidades']['email']['verificado'] + r['entidades']['email']['suspeito']) for r in all_results]
    df['pii_telefone_lista'] = [';'.join(r['entidades']['telefone']['verificado'] + r['entidades']['telefone']['suspeito']) for r in all_results]
    df['pii_nome_lista'] = [';'.join(r['entidades']['nlp_contexto']['pessoas']) for r in all_results]
    df['pii_endereco_lista'] = [';'.join(r['entidades']['endereco']['detectado']) for r in all_results]

    df['data_analise'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return df


def pagina_upload():
    """Página de upload e análise - PASSO 1 e 2."""
    st.markdown('<div class="main-header"><h1>🔒 Sistema de Gestão de PII - LGPD</h1><p>Detecção e Gestão de Dados Pessoais Conforme Lei Geral de Proteção de Dados</p></div>', unsafe_allow_html=True)

    # Wizard visual
    exibir_wizard()

    # PASSO 1: UPLOAD
    if st.session_state.df_original is None:
        st.markdown("## 📤 Passo 1: Upload de Dados")
        st.info("📋 **Instruções:** Faça upload do arquivo Excel contendo os dados para análise. O sistema processará automaticamente após o carregamento.")

        uploaded_file = st.file_uploader(
            "Selecione o arquivo Excel (.xlsx ou .xls)",
            type=['xlsx', 'xls'],
            help="Arquivo deve conter uma coluna com os textos das solicitações"
        )

        # AUTO-PROCESSAMENTO: Quando arquivo é carregado, processa imediatamente
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                st.session_state.df_original = df
                st.session_state.passo_atual = 2
                st.success(f"✅ Arquivo carregado: {len(df)} registros")
                st.rerun()  # Recarrega para mostrar próximo passo
            except Exception as e:
                st.error(f"❌ Erro ao processar arquivo: {str(e)}")
                return

    # PASSO 2: ANÁLISE (só aparece se tiver arquivo carregado)
    else:
        df = st.session_state.df_original

        # Se ainda não analisou, mostra configuração de análise
        if st.session_state.df_analisado is None:
            st.markdown("## 🔍 Passo 2: Configurar Análise")

            # Preview colapsável
            with st.expander("👁️ Ver Preview dos Dados (10 primeiras linhas)", expanded=False):
                st.dataframe(df.head(10), use_container_width=True)

            # Detecta coluna de texto
            colunas_texto = [col for col in df.columns if any(
                palavra in col.lower() for palavra in ['texto', 'solicitacao', 'descricao', 'mensagem', 'conteudo']
            )]

            if not colunas_texto:
                colunas_texto = df.columns.tolist()

            st.markdown("### ⚙️ Selecione a Coluna para Análise")
            coluna_selecionada = st.selectbox(
                "Coluna com os textos:",
                options=colunas_texto,
                index=0,
                help="Escolha a coluna que contém o texto a ser analisado para PII"
            )

            # CTA DESTACADO NO TOPO
            st.markdown("---")
            col_btn1, col_btn2, col_btn3 = st.columns([3, 1, 1])

            with col_btn1:
                if st.button("🚀 INICIAR ANÁLISE DE PII", type="primary", use_container_width=True, key="btn_principal"):
                    with st.spinner('🔍 Analisando dados pessoais com Pipeline Híbrido (Regex + Validação + NLP)...'):
                        df_analisado = analisar_arquivo(df.copy(), coluna_selecionada)
                        st.session_state.df_analisado = df_analisado
                        st.session_state.coluna_texto = coluna_selecionada
                        st.session_state.passo_atual = 3

                        # MODAL DE SUCESSO DESTACADO
                        st.markdown(f"""
                        <div class="success-modal">
                            <h2>✅ Análise Concluída com Sucesso!</h2>
                            <p><strong>{len(df_analisado)}</strong> registros processados</p>
                            <p><strong>{df_analisado['contém_pii'].sum()}</strong> registros com dados pessoais detectados</p>
                            <p>➡️ Próximo passo: Navegue para "Mascaramento" ou veja "Resultados"</p>
                        </div>
                        """, unsafe_allow_html=True)

                        st.balloons()
                        st.rerun()

            with col_btn2:
                if st.button("🗑️ Limpar", use_container_width=True):
                    st.session_state.df_original = None
                    st.session_state.df_analisado = None
                    st.session_state.coluna_texto = None
                    st.session_state.passo_atual = 1
                    st.rerun()

            with col_btn3:
                st.metric("Registros", f"{len(df):,}")

        # Se já analisou, mostra resumo
        else:
            st.markdown("## ✅ Análise Concluída")

            df_analisado = st.session_state.df_analisado

            # Métricas de resumo
            col1, col2, col3, col4 = st.columns(4)

            total_registros = len(df_analisado)
            registros_com_pii = df_analisado['contém_pii'].sum()
            percentual_pii = (registros_com_pii / total_registros * 100) if total_registros > 0 else 0
            score_medio = df_analisado['score_risco'].mean() if 'score_risco' in df_analisado.columns else 0.0

            with col1:
                st.metric("Total de Registros", f"{total_registros:,}")
            with col2:
                st.metric("Com PII", f"{registros_com_pii:,}", delta=f"{percentual_pii:.1f}%", delta_color="inverse")
            with col3:
                cor_score = "🔴" if score_medio > 0.7 else "🟡" if score_medio > 0.4 else "🟢"
                st.metric("Score Risco Médio", f"{cor_score} {score_medio:.2f}")
            with col4:
                cpf_verificados = df_analisado['cpf_verificado'].sum() if 'cpf_verificado' in df_analisado.columns else 0
                st.metric("CPF Verificados", f"{cpf_verificados:,}")

            st.success("✅ Dados analisados com sucesso! Navegue para outras abas para ver detalhes ou aplicar mascaramento.")

            # Botão para reprocessar
            col_action1, col_action2 = st.columns([1, 3])
            with col_action1:
                if st.button("🔄 Nova Análise", use_container_width=True):
                    st.session_state.df_original = None
                    st.session_state.df_analisado = None
                    st.session_state.passo_atual = 1
                    st.rerun()


def pagina_mascaramento():
    """Página de mascaramento - PASSO 3."""
    st.markdown('<div class="main-header"><h1>🛡️ Mascaramento de Dados Pessoais</h1></div>', unsafe_allow_html=True)

    # Wizard visual
    exibir_wizard()

    # Verifica se há dados processados
    if 'df_analisado' not in st.session_state or st.session_state.df_analisado is None:
        st.warning("⚠️ Nenhuma análise disponível. Faça o upload e análise de um arquivo primeiro.")
        st.info("💡 Navegue para 'Upload e Análise' → Faça upload → Clique em 'Iniciar Análise'")

        if st.button("⬅️ Ir para Upload", type="primary"):
            st.session_state.passo_atual = 1
        return

    df = st.session_state.df_analisado
    coluna_texto = st.session_state.get('coluna_texto', None)

    st.markdown("## 🛡️ Passo 3: Configurar Mascaramento LGPD")

    st.info("""
    **Bases Legais LGPD (Art. 7º):**
    - ✅ Consentimento do titular
    - ✅ Cumprimento de obrigação legal
    - ✅ Execução de políticas públicas
    - ✅ Proteção da vida ou incolumidade física
    """)

    # Preview de exemplos
    st.markdown("### 👁️ Modos de Mascaramento Disponíveis")
    col_ex1, col_ex2 = st.columns(2)

    with col_ex1:
        st.markdown("""
        <div class="success-zone">
        <h4>🟢 Modo PARCIAL (Utility Masking)</h4>
        <p><strong>Mantém utilidade do dado preservando formato</strong></p>
        <ul>
            <li><strong>CPF:</strong> 123.456.789-00 ➝ ***.456.789-**</li>
            <li><strong>RG:</strong> 1.234.567 ➝ **.234.567</li>
            <li><strong>E-mail:</strong> usuario@email.com ➝ us***@email.com</li>
            <li><strong>Telefone:</strong> (61) 91234-5678 ➝ (61) 9****-5678</li>
            <li><strong>Nome:</strong> Paulo Henrique ➝ P* H*</li>
        </ul>
        <p><em>✅ Ideal para análises internas mantendo referências</em></p>
        </div>
        """, unsafe_allow_html=True)

    with col_ex2:
        st.markdown("""
        <div class="danger-zone">
        <h4>🔴 Modo PROTEÇÃO TOTAL (Full Redaction)</h4>
        <p><strong>Segurança máxima para dados públicos</strong></p>
        <p>Qualquer PII é substituído por:</p>
        <p style="font-size: 16px; font-weight: bold; text-align: center; background: #fff; padding: 10px; border-radius: 5px;">
        [INFORMAÇÃO PROTEGIDA LGPD]
        </p>
        <p><em>🔒 Ideal para publicação externa e máxima conformidade</em></p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Configuração do mascaramento
    st.markdown("### ⚙️ Configurar Mascaramento")

    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        modo_mascaramento = st.radio(
            "Selecione o modo:",
            options=['PARCIAL', 'PROTECAO_TOTAL'],
            help="PARCIAL: mantém formato | PROTEÇÃO TOTAL: segurança máxima"
        )

    with col2:
        tipos_mascarar = st.multiselect(
            "Tipos de dados para mascarar:",
            options=['todos', 'cpf', 'rg', 'email', 'telefone', 'nome'],
            default=['todos'],
            help="Selecione 'todos' ou escolha tipos específicos"
        )

    with col3:
        aplicar_no_texto = st.checkbox(
            "Mascarar no texto original",
            value=True,
            help="Se marcado, aplica mascaramento diretamente no texto da solicitação",
            disabled=(coluna_texto is None)
        )

    # Botões de ação
    st.markdown("---")
    col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 2])

    with col_btn1:
        if st.button("🛡️ APLICAR MASCARAMENTO", type="primary", use_container_width=True, key="btn_mascarar"):
            if tipos_mascarar:
                with st.spinner(f'🔒 Aplicando mascaramento {modo_mascaramento}...'):
                    # IMPORTANTE: Pega o DataFrame ORIGINAL (não o analisado)
                    df_original_para_mascarar = st.session_state.df_original.copy()

                    # Aplica mascaramento APENAS na coluna de texto
                    if coluna_texto and aplicar_no_texto and coluna_texto in df_original_para_mascarar.columns:
                        detector = st.session_state.detector
                        textos = df_original_para_mascarar[coluna_texto].fillna("").astype(str).tolist()

                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        textos_mascarados = []
                        batch_size = 100
                        total = len(textos)

                        for i in range(0, total, batch_size):
                            batch = textos[i:i+batch_size]
                            mascarados = detector.apply_masking_batch(batch, mode=modo_mascaramento)
                            textos_mascarados.extend(mascarados)

                            progress = min((i + batch_size) / total, 1.0)
                            progress_bar.progress(progress)
                            status_text.text(f'Mascarando: {i+batch_size}/{total} registros')

                        df_original_para_mascarar[coluna_texto] = textos_mascarados
                        progress_bar.empty()
                        status_text.empty()

                    # Salva o arquivo mascarado (SÓ com colunas originais)
                    st.session_state.df_mascarado_limpo = df_original_para_mascarar
                    st.session_state.passo_atual = 4

                    # Exporta automaticamente
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    arquivo_saida = f"dados_mascarados_{modo_mascaramento}_{timestamp}.xlsx"

                    output_dir = Path("./output")
                    output_dir.mkdir(exist_ok=True)
                    arquivo_path = output_dir / arquivo_saida

                    df_original_para_mascarar.to_excel(arquivo_path, index=False)
                    st.session_state.arquivo_mascarado_path = str(arquivo_path.absolute())

                    # MODAL DE SUCESSO DESTACADO COM CAMINHO DO ARQUIVO
                    st.markdown(f"""
                    <div class="success-modal">
                        <h2>✅ Mascaramento Concluído!</h2>
                        <p><strong>Modo:</strong> {modo_mascaramento}</p>
                        <p><strong>{len(df_original_para_mascarar)}</strong> registros processados</p>
                        <p style="font-size: 14px; background: rgba(255,255,255,0.2); padding: 10px; border-radius: 5px; margin-top: 10px;">
                        📁 Arquivo salvo em:<br>
                        <code>{st.session_state.arquivo_mascarado_path}</code>
                        </p>
                        <p>➡️ Próximo passo: Baixe o arquivo abaixo ou veja "Resultados"</p>
                    </div>
                    """, unsafe_allow_html=True)

                    st.balloons()
                    st.rerun()
            else:
                st.warning("⚠️ Selecione pelo menos um tipo de dado.")

    with col_btn2:
        if st.button("👁️ Visualizar Preview", use_container_width=True):
            if tipos_mascarar and len(df[df['contém_pii'] == True]) > 0:
                st.markdown("#### 🔍 Preview do Mascaramento")
                # Pega primeiro registro com PII
                registro_exemplo = df[df['contém_pii'] == True].iloc[0]

                if coluna_texto and coluna_texto in registro_exemplo:
                    texto_original = str(registro_exemplo[coluna_texto])
                    detector = st.session_state.detector
                    texto_mascarado = detector.apply_masking(texto_original, mode=modo_mascaramento)

                    col_prev1, col_prev2 = st.columns(2)
                    with col_prev1:
                        st.markdown("**Original:**")
                        st.text_area("", texto_original[:500], height=150, disabled=True, key="prev_orig")
                    with col_prev2:
                        st.markdown("**Mascarado:**")
                        st.text_area("", texto_mascarado[:500], height=150, disabled=True, key="prev_mask")
                else:
                    st.info("Preview disponível apenas quando há coluna de texto.")
            else:
                st.warning("Nenhum registro com PII disponível para preview.")

    with col_btn3:
        if st.button("↩️ Restaurar Original", use_container_width=True):
            if st.checkbox("⚠️ Confirmar restauração", key="confirm_restore"):
                st.session_state.df_analisado = st.session_state.df_original.copy()
                st.success("✅ Dados originais restaurados!")
                st.rerun()

    # DOWNLOAD IMEDIATO (se já mascarou)
    if st.session_state.arquivo_mascarado_path and st.session_state.get('df_mascarado_limpo') is not None:
        st.markdown("---")
        st.markdown("### 💾 Download do Arquivo Mascarado")

        # Cria buffer para download (usa DataFrame limpo - só colunas originais)
        buffer = io.BytesIO()
        st.session_state.df_mascarado_limpo.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)

        col_download1, col_download2 = st.columns([2, 2])
        with col_download1:
            st.download_button(
                label="⬇️ BAIXAR ARQUIVO MASCARADO",
                data=buffer,
                file_name=f"dados_mascarados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
        with col_download2:
            st.info(f"📁 Arquivo também salvo em:\n`{st.session_state.arquivo_mascarado_path}`")


def pagina_resultados():
    """Dashboard com métricas e visualizações - PASSO 4."""
    st.markdown('<div class="main-header"><h1>📊 Resultados e Dashboard</h1></div>', unsafe_allow_html=True)

    # Wizard visual
    exibir_wizard()

    # Verifica se há dados processados
    if 'df_analisado' not in st.session_state or st.session_state.df_analisado is None:
        st.warning("⚠️ Nenhuma análise disponível. Faça o upload e análise de um arquivo primeiro.")
        st.info("💡 Navegue para 'Upload e Análise' → Faça upload → Clique em 'Iniciar Análise'")
        return

    df = st.session_state.df_analisado

    # Métricas principais
    st.markdown("## 📈 Métricas Gerais")

    # Explicação sobre CPF separado
    st.markdown("""
    <div class="warning-zone">
    <h4>⚠️ ATENÇÃO: CPF aparece em DUAS categorias diferentes nas métricas abaixo</h4>
    <p><strong>✅ CPF Validado:</strong> Validado matematicamente (Módulo 11) - CPF real<br>
    <strong>⚠️ CPF Não Validado:</strong> Padrão correto mas falhou validação - Erro de digitação (ainda é risco!)</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    total_registros = len(df)
    registros_com_pii = df['contém_pii'].sum()
    percentual_pii = (registros_com_pii / total_registros * 100) if total_registros > 0 else 0

    # Score de risco médio
    score_medio = df['score_risco'].mean() if 'score_risco' in df.columns else 0.0

    with col1:
        st.metric("Total de Registros", f"{total_registros:,}")
    with col2:
        st.metric("Registros com PII", f"{registros_com_pii:,}",
                 delta=f"{percentual_pii:.1f}%", delta_color="inverse")
    with col3:
        # Score de risco com cor
        cor_score = "🔴" if score_medio > 0.7 else "🟡" if score_medio > 0.4 else "🟢"
        st.metric("Score Risco Médio", f"{cor_score} {score_medio:.2f}",
                 help="0.0 = sem risco | 1.0 = risco máximo")
    with col4:
        # CPF validados (alta confiança)
        cpf_validados = df['cpf_validado'].sum() if 'cpf_validado' in df.columns else 0
        st.metric("✅ CPF Validado", f"{cpf_validados:,}",
                 help="Validado matematicamente - CPF Real")
    with col5:
        # CPF NÃO validados (erro de digitação)
        cpf_nao_validados = df['cpf_nao_validado'].sum() if 'cpf_nao_validado' in df.columns else 0
        st.metric("⚠️ CPF Não Validado", f"{cpf_nao_validados:,}",
                 help="Erro de digitação - Ainda é risco!")
    with col6:
        # Endereços detectados
        enderecos = df['endereco_detectado'].sum() if 'endereco_detectado' in df.columns else 0
        st.metric("Endereços", f"{enderecos:,}",
                 help="Endereços residenciais identificados")

    # Gráficos
    st.markdown("## 📊 Análise Detalhada")

    col1, col2 = st.columns(2)

    with col1:
        # ===================================================================
        # GRÁFICO DE TIPOS DE PII - APENAS CPF TEM DUAS CATEGORIAS!
        # ===================================================================

        # Explicação visível para o usuário
        st.info("ℹ️ **ATENÇÃO:** CPF aparece em DUAS categorias diferentes no gráfico abaixo")

        tipos_pii = {
            '✅ CPF Validado': df['cpf_validado'].sum() if 'cpf_validado' in df.columns else 0,
            '⚠️ CPF Não Validado': df['cpf_nao_validado'].sum() if 'cpf_nao_validado' in df.columns else 0,
            'RG': df['rg_detectado'].sum() if 'rg_detectado' in df.columns else 0,
            'E-mail': df['email_detectado'].sum() if 'email_detectado' in df.columns else 0,
            'Telefone': df['telefone_detectado'].sum() if 'telefone_detectado' in df.columns else 0,
            'Nome': df['nome_detectado'].sum() if 'nome_detectado' in df.columns else 0,
            'Endereço': df['endereco_detectado'].sum() if 'endereco_detectado' in df.columns else 0
        }

        # Cores personalizadas: CPF validado/RG/Endereço=VERMELHO, CPF não validado/Nome=LARANJA, Email/Telefone=AMARELO
        cores = ['#ff0000', '#ff9900', '#ff0000', '#ffcc00', '#ffcc00', '#ff9900', '#ff0000']

        fig_tipos = go.Figure(data=[
            go.Bar(
                x=list(tipos_pii.keys()),
                y=list(tipos_pii.values()),
                marker_color=cores,
                text=list(tipos_pii.values()),
                textposition='auto',
                hovertemplate='<b>%{x}</b><br>Quantidade: %{y}<extra></extra>'
            )
        ])
        fig_tipos.update_layout(
            title="Tipos de Dados Pessoais Detectados",
            xaxis_title="Tipo de PII",
            yaxis_title="Quantidade",
            height=450,
            showlegend=False
        )
        st.plotly_chart(fig_tipos, use_container_width=True)

        # Explicação abaixo do gráfico
        st.markdown("""
        <div class="warning-zone">
        <h4>📌 Diferença entre CPF Validado e CPF Não Validado:</h4>
        <ul>
            <li><strong>✅ CPF Validado:</strong> Validado matematicamente usando algoritmo Módulo 11 da Receita Federal. É um CPF REAL e existente.</li>
            <li><strong>⚠️ CPF Não Validado:</strong> Tem padrão correto (XXX.XXX.XXX-XX) mas FALHOU na validação matemática. Pode ser erro de digitação, mas AINDA REPRESENTA RISCO pois alguém tentou fornecer um CPF.</li>
        </ul>
        <p><strong>⚠️ IMPORTANTE:</strong> AMBOS devem ser considerados pelo usuário para mascaramento!</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Gráfico pizza - Distribuição
        fig_pizza = go.Figure(data=[
            go.Pie(
                labels=['Com PII', 'Sem PII'],
                values=[registros_com_pii, total_registros - registros_com_pii],
                marker_colors=['#ff4b4b', '#00cc44'],
                hole=0.4
            )
        ])
        fig_pizza.update_layout(
            title="Distribuição de Registros",
            height=400
        )
        st.plotly_chart(fig_pizza, use_container_width=True)

    # Exportação de dados
    st.markdown("## 💾 Exportar Dados")

    col_export1, col_export2 = st.columns(2)

    with col_export1:
        # Excel completo
        buffer_excel = io.BytesIO()
        with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Dados Completos', index=False)

            # Aba com apenas registros com PII
            df_pii = df[df['contém_pii'] == True]
            df_pii.to_excel(writer, sheet_name='Com PII', index=False)

            # Aba com estatísticas - APENAS CPF SEPARADO
            stats = {
                'Métrica': [
                    'Total de Registros',
                    'Com PII',
                    '% PII',
                    '',  # linha vazia
                    '=== CPF (DUAS CATEGORIAS) ===',
                    '✅ CPF VALIDADO (Validado Matematicamente - CPF Real)',
                    '⚠️ CPF NÃO VALIDADO (Erro de Digitação - Ainda é Risco)',
                    '',  # linha vazia
                    '=== OUTROS DADOS (UMA CATEGORIA) ===',
                    'RG',
                    'Email',
                    'Telefone',
                    'Nome',
                    'Endereço'
                ],
                'Valor': [
                    len(df),
                    df['contém_pii'].sum(),
                    f"{(df['contém_pii'].sum()/len(df)*100):.1f}%",
                    '',  # linha vazia
                    '',
                    df['cpf_validado'].sum(),
                    df['cpf_nao_validado'].sum(),
                    '',  # linha vazia
                    '',
                    df['rg_detectado'].sum(),
                    df['email_detectado'].sum(),
                    df['telefone_detectado'].sum(),
                    df['nome_detectado'].sum(),
                    df['endereco_detectado'].sum()
                ],
                'Explicação': [
                    'Total de linhas analisadas',
                    'Registros que contêm algum dado pessoal',
                    'Percentual com PII',
                    '',
                    '',
                    'CPF validado pelo algoritmo Módulo 11 da Receita Federal',
                    'CPF com formato correto mas falhou validação - pode ser erro de digitação',
                    '',
                    '',
                    'Documentos de identidade detectados',
                    'Endereços de e-mail detectados',
                    'Números de telefone detectados',
                    'Nomes de pessoas detectados',
                    'Endereços residenciais detectados'
                ]
            }
            pd.DataFrame(stats).to_excel(writer, sheet_name='Estatísticas', index=False)

        buffer_excel.seek(0)

        st.download_button(
            label="📊 Baixar Excel Completo",
            data=buffer_excel,
            file_name=f"analise_pii_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with col_export2:
        # CSV simplificado
        csv = df.to_csv(index=False, encoding='utf-8-sig')

        st.download_button(
            label="📄 Baixar CSV Simplificado",
            data=csv,
            file_name=f"analise_pii_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Tabela de registros com PII (colapsável)
    st.markdown("## ⚠️ Registros com Dados Pessoais")
    df_com_pii = df[df['contém_pii'] == True].copy()

    if len(df_com_pii) > 0:
        with st.expander(f"📋 Ver {len(df_com_pii)} registros com PII", expanded=False):
            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                filtro_cpf = st.checkbox("Apenas com CPF", value=False)
            with col2:
                filtro_email = st.checkbox("Apenas com E-mail", value=False)
            with col3:
                filtro_nome = st.checkbox("Apenas com Nome", value=False)

            df_filtrado = df_com_pii.copy()
            if filtro_cpf:
                # Filtra CPF (validado OU não validado)
                df_filtrado = df_filtrado[(df_filtrado['cpf_validado'] > 0) | (df_filtrado['cpf_nao_validado'] > 0)]
            if filtro_email:
                df_filtrado = df_filtrado[df_filtrado['email_detectado'] > 0]
            if filtro_nome:
                df_filtrado = df_filtrado[df_filtrado['nome_detectado'] > 0]

            # Seleciona colunas para exibir
            colunas_exibir = [col for col in df_filtrado.columns if not col.startswith('pii_') or col.endswith('_lista')]
            st.dataframe(df_filtrado[colunas_exibir], use_container_width=True, height=400)
    else:
        st.success("✅ Nenhum registro com dados pessoais detectado!")


def pagina_relatorio():
    """Relatório de conformidade LGPD."""
    st.markdown('<div class="main-header"><h1>📋 Relatório de Conformidade LGPD</h1></div>', unsafe_allow_html=True)

    # Verifica se há dados processados
    if 'df_analisado' not in st.session_state or st.session_state.df_analisado is None:
        st.warning("⚠️ Nenhuma análise disponível. Faça o upload e análise de um arquivo primeiro.")
        st.info("💡 Navegue para 'Upload e Análise' → Faça upload → Clique em 'Iniciar Análise'")
        return

    df = st.session_state.df_analisado

    st.markdown("## 📄 Relatório Executivo")

    # Dados do relatório
    total = len(df)
    com_pii = df['contém_pii'].sum()
    sem_pii = total - com_pii

    st.markdown(f"""
    ### Resumo da Análise

    **Data do Relatório:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
    **Total de Registros Analisados:** {total:,}
    **Registros com Dados Pessoais:** {com_pii:,} ({(com_pii/total*100):.1f}%)
    **Registros sem Dados Pessoais:** {sem_pii:,} ({(sem_pii/total*100):.1f}%)

    ### Detalhamento por Tipo de Dado

    **⚠️ ATENÇÃO: CPF aparece em DUAS categorias diferentes**

    | Tipo de Dado | Quantidade | Status LGPD | Explicação |
    |--------------|------------|-------------|------------|
    | **✅ CPF Validado** | {df['cpf_validado'].sum():,} | ⚠️ Sensível | Validado matematicamente - CPF real |
    | **⚠️ CPF Não Validado** | {df['cpf_nao_validado'].sum():,} | ⚠️ Sensível | Erro de digitação - Ainda é risco! |
    | RG | {df['rg_detectado'].sum():,} | ⚠️ Sensível | Documento de identidade |
    | E-mail | {df['email_detectado'].sum():,} | ℹ️ Pessoal | Endereço eletrônico |
    | Telefone | {df['telefone_detectado'].sum():,} | ℹ️ Pessoal | Número de contato |
    | Nome | {df['nome_detectado'].sum():,} | ℹ️ Pessoal | Identificação pessoal |

    ### Recomendações de Conformidade

    {
    '🔴 **AÇÃO URGENTE:** Alto volume de dados sensíveis (CPF/RG) detectado. Revisar necessidade de coleta.' if (df['cpf_validado'].sum() + df['cpf_nao_validado'].sum()) > total * 0.3
    else '🟢 **CONFORME:** Volume de dados pessoais dentro do esperado.'
    }

    ✅ Implementar mascaramento para dados não essenciais
    ✅ Documentar base legal para tratamento (Art. 7º LGPD)
    ✅ Estabelecer prazo de retenção dos dados
    ✅ Garantir direitos dos titulares (acesso, correção, exclusão)

    ### Histórico de Tratamento
    """)

    if st.session_state.historico_acoes:
        for acao in st.session_state.historico_acoes:
            st.markdown(f"- **{acao['timestamp']}:** {acao['acao']} - {acao['tipos']} ({acao['registros']} registros)")
    else:
        st.markdown("*Nenhuma ação de tratamento registrada.*")

    # Botão de exportação do relatório
    st.markdown("### 💾 Exportar Relatório")

    if st.button("📄 Gerar Relatório PDF", use_container_width=True):
        st.info("⚠️ Funcionalidade de exportação PDF será implementada em breve.")


def main():
    """Função principal da aplicação - Interface de scroll contínuo."""
    init_session_state()

    # Sidebar bonita e informativa
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/009c3b/FFFFFF?text=Sistema+PII+LGPD", use_container_width=True)

        # Status dos dados processados
        st.markdown("### 📊 Status do Sistema")

        if st.session_state.get('df_analisado') is not None:
            df = st.session_state.df_analisado

            # Card de status com métricas
            st.markdown("""
            <div class="success-zone" style="padding: 15px; margin-bottom: 10px;">
                <h4 style="margin: 0;">✅ Análise Concluída</h4>
            </div>
            """, unsafe_allow_html=True)

            # Métricas resumidas
            total = len(df)
            com_pii = df['contém_pii'].sum()
            score_medio = df['score_risco'].mean() if 'score_risco' in df.columns else 0.0

            st.metric("📄 Total de Registros", f"{total:,}")
            st.metric("⚠️ Com Dados Pessoais", f"{com_pii:,}",
                     delta=f"{(com_pii/total*100):.1f}%", delta_color="inverse")

            # Score de risco com cor
            cor_score = "🔴" if score_medio > 0.7 else "🟡" if score_medio > 0.4 else "🟢"
            st.metric("🎯 Score de Risco", f"{cor_score} {score_medio:.2f}")

            st.markdown("---")

            # Detalhamento por tipo
            st.markdown("### 📋 Dados Detectados")

            cpf_val = df['cpf_validado'].sum() if 'cpf_validado' in df.columns else 0
            cpf_nval = df['cpf_nao_validado'].sum() if 'cpf_nao_validado' in df.columns else 0
            rg = df['rg_detectado'].sum() if 'rg_detectado' in df.columns else 0
            email = df['email_detectado'].sum() if 'email_detectado' in df.columns else 0
            tel = df['telefone_detectado'].sum() if 'telefone_detectado' in df.columns else 0
            nome = df['nome_detectado'].sum() if 'nome_detectado' in df.columns else 0
            end = df['endereco_detectado'].sum() if 'endereco_detectado' in df.columns else 0

            # Cores para cada tipo
            st.markdown(f"""
            <div style="font-size: 13px; line-height: 1.8;">
                <div style="background: #ffe6e6; padding: 8px; border-radius: 5px; margin-bottom: 5px;">
                    🔴 <strong>CPF Validado:</strong> {cpf_val:,}
                </div>
                <div style="background: #fff4e6; padding: 8px; border-radius: 5px; margin-bottom: 5px;">
                    🟠 <strong>CPF Não Validado:</strong> {cpf_nval:,}
                </div>
                <div style="background: #ffe6e6; padding: 8px; border-radius: 5px; margin-bottom: 5px;">
                    🔴 <strong>RG:</strong> {rg:,}
                </div>
                <div style="background: #fffacd; padding: 8px; border-radius: 5px; margin-bottom: 5px;">
                    🟡 <strong>E-mail:</strong> {email:,}
                </div>
                <div style="background: #fffacd; padding: 8px; border-radius: 5px; margin-bottom: 5px;">
                    🟡 <strong>Telefone:</strong> {tel:,}
                </div>
                <div style="background: #fff4e6; padding: 8px; border-radius: 5px; margin-bottom: 5px;">
                    🟠 <strong>Nome:</strong> {nome:,}
                </div>
                <div style="background: #ffe6e6; padding: 8px; border-radius: 5px; margin-bottom: 5px;">
                    🔴 <strong>Endereço:</strong> {end:,}
                </div>
            </div>
            """, unsafe_allow_html=True)

        elif st.session_state.get('df_original') is not None:
            st.markdown("""
            <div class="warning-zone" style="padding: 15px;">
                <h4 style="margin: 0;">⏳ Aguardando Análise</h4>
            </div>
            """, unsafe_allow_html=True)
            st.metric("📄 Registros Carregados", f"{len(st.session_state.df_original):,}")
        else:
            st.markdown("""
            <div class="danger-zone" style="padding: 15px;">
                <h4 style="margin: 0;">⚠️ Nenhum Dado Carregado</h4>
                <p style="margin: 10px 0 0 0; font-size: 12px;">Faça upload de um arquivo para começar</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Informações do sistema
        st.markdown("### ℹ️ Sobre")
        st.markdown("""
        **Sistema de Gestão de PII**
        Versão 2.0 - Scroll Otimizado

        **Conformidade:**
        - 🇧🇷 LGPD (Lei 13.709/2018)
        - 🔒 LAI (Lei 12.527/2011)

        **Hackathon Participa DF 2026**
        Categoria: Acesso à Informação
        """)

        st.markdown("---")

        # Botão de reset
        if st.button("🔄 Reiniciar Sistema", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # ===========================
    # PÁGINA ÚNICA COM SCROLL
    # ===========================

    st.markdown('<div class="main-header"><h1>🔒 Sistema de Gestão de PII - LGPD</h1><p>Detecção e Gestão de Dados Pessoais - Role a página para navegar</p></div>', unsafe_allow_html=True)

    # SEÇÃO 1: UPLOAD
    st.markdown("## 📤 1. Upload de Dados")

    if st.session_state.df_original is None:
        st.info("📋 Faça upload do arquivo Excel para iniciar a análise")

        uploaded_file = st.file_uploader(
            "Selecione o arquivo Excel (.xlsx ou .xls)",
            type=['xlsx', 'xls'],
            help="Arquivo deve conter uma coluna com os textos das solicitações"
        )

        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                st.session_state.df_original = df
                st.success(f"✅ Arquivo carregado: {len(df)} registros")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao processar arquivo: {str(e)}")
    else:
        st.success(f"✅ Arquivo carregado com {len(st.session_state.df_original)} registros")

    st.markdown("---")

    # SEÇÃO 2: ANÁLISE (só aparece se tiver arquivo)
    if st.session_state.df_original is not None:
        st.markdown("## 🔍 2. Análise de Dados Pessoais")

        if st.session_state.df_analisado is None:
            df = st.session_state.df_original

            # Detecta coluna de texto
            colunas_texto = [col for col in df.columns if any(
                palavra in col.lower() for palavra in ['texto', 'solicitacao', 'descricao', 'mensagem', 'conteudo']
            )]

            if not colunas_texto:
                colunas_texto = df.columns.tolist()

            coluna_selecionada = st.selectbox(
                "Selecione a coluna com os textos:",
                options=colunas_texto,
                index=0
            )

            if st.button("🚀 ANALISAR DADOS", type="primary", use_container_width=True):
                with st.spinner('🔍 Analisando dados pessoais...'):
                    df_analisado = analisar_arquivo(df.copy(), coluna_selecionada)
                    st.session_state.df_analisado = df_analisado
                    st.session_state.coluna_texto = coluna_selecionada
                    st.success("✅ Análise concluída!")
                    st.balloons()
                    st.rerun()
        else:
            st.success("✅ Análise concluída")

            df_analisado = st.session_state.df_analisado

            # Métricas resumidas
            col1, col2, col3, col4 = st.columns(4)

            total_registros = len(df_analisado)
            registros_com_pii = df_analisado['contém_pii'].sum()
            cpf_validados = df_analisado['cpf_validado'].sum() if 'cpf_validado' in df_analisado.columns else 0
            score_medio = df_analisado['score_risco'].mean() if 'score_risco' in df_analisado.columns else 0.0

            with col1:
                st.metric("Total", f"{total_registros:,}")
            with col2:
                st.metric("Com PII", f"{registros_com_pii:,}")
            with col3:
                st.metric("CPF Validado", f"{cpf_validados:,}")
            with col4:
                cor_score = "🔴" if score_medio > 0.7 else "🟡" if score_medio > 0.4 else "🟢"
                st.metric("Risco", f"{cor_score} {score_medio:.2f}")

        st.markdown("---")

    # SEÇÃO 3: VISUALIZAÇÃO (só aparece se já analisou)
    if st.session_state.df_analisado is not None:
        st.markdown("## 📊 3. Visualização dos Dados Detectados")

        df = st.session_state.df_analisado

        # Aviso sobre CPF separado
        st.markdown("""
        <div class="warning-zone">
        <p><strong>⚠️ ATENÇÃO:</strong> CPF aparece em DUAS categorias:
        <strong>CPF Validado</strong> (vermelho - validado matematicamente) e
        <strong>CPF Não Validado</strong> (laranja - erro de digitação)</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([3, 2])

        with col1:
            # Gráfico de barras
            tipos_pii = {
                '✅ CPF Validado': df['cpf_validado'].sum() if 'cpf_validado' in df.columns else 0,
                '⚠️ CPF Não Validado': df['cpf_nao_validado'].sum() if 'cpf_nao_validado' in df.columns else 0,
                'RG': df['rg_detectado'].sum() if 'rg_detectado' in df.columns else 0,
                'E-mail': df['email_detectado'].sum() if 'email_detectado' in df.columns else 0,
                'Telefone': df['telefone_detectado'].sum() if 'telefone_detectado' in df.columns else 0,
                'Nome': df['nome_detectado'].sum() if 'nome_detectado' in df.columns else 0,
                'Endereço': df['endereco_detectado'].sum() if 'endereco_detectado' in df.columns else 0
            }

            cores = ['#ff0000', '#ff9900', '#ff0000', '#ffcc00', '#ffcc00', '#ff9900', '#ff0000']

            fig_tipos = go.Figure(data=[
                go.Bar(
                    x=list(tipos_pii.keys()),
                    y=list(tipos_pii.values()),
                    marker_color=cores,
                    text=list(tipos_pii.values()),
                    textposition='auto'
                )
            ])
            fig_tipos.update_layout(
                title="Tipos de Dados Pessoais Detectados",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig_tipos, use_container_width=True)

        with col2:
            # Gráfico pizza
            total_registros = len(df)
            registros_com_pii = df['contém_pii'].sum()

            fig_pizza = go.Figure(data=[
                go.Pie(
                    labels=['Com PII', 'Sem PII'],
                    values=[registros_com_pii, total_registros - registros_com_pii],
                    marker_colors=['#ff4b4b', '#00cc44'],
                    hole=0.4
                )
            ])
            fig_pizza.update_layout(title="Distribuição", height=400)
            st.plotly_chart(fig_pizza, use_container_width=True)

        st.markdown("---")

    # SEÇÃO 4: RELATÓRIO LGPD (sempre aparece após análise)
    if st.session_state.df_analisado is not None:
        st.markdown("## 📋 4. Relatório de Conformidade LGPD")

        df = st.session_state.df_analisado

        # Dados do relatório
        total = len(df)
        com_pii = df['contém_pii'].sum()
        sem_pii = total - com_pii
        score_medio = df['score_risco'].mean() if 'score_risco' in df.columns else 0.0

        # Cabeçalho do relatório em card bonito
        st.markdown(f"""
        <div class="success-zone">
            <h3>📊 Resumo Executivo da Análise</h3>
            <p><strong>Data do Relatório:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
            <p><strong>Total de Registros:</strong> {total:,}</p>
            <p><strong>Score de Risco Médio:</strong> {score_medio:.2f} / 1.00</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); padding: 20px; border-radius: 10px; text-align: center;">
                <h2 style="color: #2e7d32; margin: 0;">✅</h2>
                <h4 style="margin: 10px 0;">Sem Dados Pessoais</h4>
                <h2 style="color: #2e7d32; margin: 0;">{:,}</h2>
                <p style="margin: 5px 0 0 0; font-size: 14px; color: #558b2f;">{:.1f}%</p>
            </div>
            """.format(sem_pii, (sem_pii/total*100)), unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); padding: 20px; border-radius: 10px; text-align: center;">
                <h2 style="color: #f57c00; margin: 0;">⚠️</h2>
                <h4 style="margin: 10px 0;">Com Dados Pessoais</h4>
                <h2 style="color: #f57c00; margin: 0;">{:,}</h2>
                <p style="margin: 5px 0 0 0; font-size: 14px; color: #e65100;">{:.1f}%</p>
            </div>
            """.format(com_pii, (com_pii/total*100)), unsafe_allow_html=True)

        with col3:
            cor_bg = "#ffebee" if score_medio > 0.7 else "#fff8e1" if score_medio > 0.4 else "#e8f5e9"
            cor_texto = "#c62828" if score_medio > 0.7 else "#f57c00" if score_medio > 0.4 else "#2e7d32"
            emoji = "🔴" if score_medio > 0.7 else "🟡" if score_medio > 0.4 else "🟢"

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {cor_bg} 0%, {cor_bg} 100%); padding: 20px; border-radius: 10px; text-align: center;">
                <h2 style="color: {cor_texto}; margin: 0;">{emoji}</h2>
                <h4 style="margin: 10px 0;">Nível de Risco</h4>
                <h2 style="color: {cor_texto}; margin: 0;">{score_medio:.2f}</h2>
                <p style="margin: 5px 0 0 0; font-size: 14px; color: {cor_texto};">
                    {"ALTO" if score_medio > 0.7 else "MÉDIO" if score_medio > 0.4 else "BAIXO"}
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### 📊 Detalhamento por Tipo de Dado Pessoal")

        # Tabela bonita com os dados
        cpf_val = df['cpf_validado'].sum() if 'cpf_validado' in df.columns else 0
        cpf_nval = df['cpf_nao_validado'].sum() if 'cpf_nao_validado' in df.columns else 0
        rg = df['rg_detectado'].sum() if 'rg_detectado' in df.columns else 0
        email = df['email_detectado'].sum() if 'email_detectado' in df.columns else 0
        tel = df['telefone_detectado'].sum() if 'telefone_detectado' in df.columns else 0
        nome = df['nome_detectado'].sum() if 'nome_detectado' in df.columns else 0
        endereco = df['endereco_detectado'].sum() if 'endereco_detectado' in df.columns else 0

        st.markdown("""
        <div class="warning-zone">
        <p><strong>⚠️ IMPORTANTE:</strong> CPF aparece em DUAS categorias distintas conforme validação matemática (Módulo 11)</p>
        </div>
        """, unsafe_allow_html=True)

        # Tabela formatada
        relatorio_html = f"""
        <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
            <thead>
                <tr style="background: #009c3b; color: white;">
                    <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Tipo de Dado</th>
                    <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">Quantidade</th>
                    <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">Classificação LGPD</th>
                    <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Observações</th>
                </tr>
            </thead>
            <tbody>
                <tr style="background: #ffe6e6;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>🔴 CPF Validado</strong></td>
                    <td style="padding: 10px; text-align: center; border: 1px solid #ddd;"><strong>{cpf_val:,}</strong></td>
                    <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">⚠️ Sensível</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">CPF validado matematicamente - Dados reais</td>
                </tr>
                <tr style="background: #fff4e6;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>🟠 CPF Não Validado</strong></td>
                    <td style="padding: 10px; text-align: center; border: 1px solid #ddd;"><strong>{cpf_nval:,}</strong></td>
                    <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">⚠️ Sensível</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">Falha na validação - Possível erro de digitação</td>
                </tr>
                <tr style="background: #ffe6e6;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>🔴 RG</strong></td>
                    <td style="padding: 10px; text-align: center; border: 1px solid #ddd;"><strong>{rg:,}</strong></td>
                    <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">⚠️ Sensível</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">Documento de identidade</td>
                </tr>
                <tr style="background: #fffacd;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>🟡 E-mail</strong></td>
                    <td style="padding: 10px; text-align: center; border: 1px solid #ddd;"><strong>{email:,}</strong></td>
                    <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">ℹ️ Pessoal</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">Endereço eletrônico</td>
                </tr>
                <tr style="background: #fffacd;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>🟡 Telefone</strong></td>
                    <td style="padding: 10px; text-align: center; border: 1px solid #ddd;"><strong>{tel:,}</strong></td>
                    <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">ℹ️ Pessoal</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">Número de contato</td>
                </tr>
                <tr style="background: #fff4e6;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>🟠 Nome</strong></td>
                    <td style="padding: 10px; text-align: center; border: 1px solid #ddd;"><strong>{nome:,}</strong></td>
                    <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">ℹ️ Pessoal</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">Identificação pessoal</td>
                </tr>
                <tr style="background: #ffe6e6;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>🔴 Endereço</strong></td>
                    <td style="padding: 10px; text-align: center; border: 1px solid #ddd;"><strong>{endereco:,}</strong></td>
                    <td style="padding: 10px; text-align: center; border: 1px solid #ddd;">ℹ️ Pessoal</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">Endereço residencial</td>
                </tr>
            </tbody>
        </table>
        """
        st.markdown(relatorio_html, unsafe_allow_html=True)

        st.markdown("### 🎯 Recomendações de Conformidade LGPD")

        # Recomendações baseadas no score
        total_cpf = cpf_val + cpf_nval
        if total_cpf > total * 0.3 or score_medio > 0.7:
            st.markdown("""
            <div class="danger-zone">
                <h4>🔴 AÇÃO URGENTE REQUERIDA</h4>
                <p><strong>Alto volume de dados sensíveis detectado!</strong></p>
                <ul>
                    <li>✅ Aplicar mascaramento imediato (seção abaixo)</li>
                    <li>✅ Revisar necessidade de coleta destes dados</li>
                    <li>✅ Documentar base legal (Art. 7º LGPD)</li>
                    <li>✅ Implementar controles de acesso restritos</li>
                    <li>✅ Estabelecer prazo de retenção máximo</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        elif score_medio > 0.4:
            st.markdown("""
            <div class="warning-zone">
                <h4>🟡 ATENÇÃO NECESSÁRIA</h4>
                <p><strong>Volume moderado de dados pessoais</strong></p>
                <ul>
                    <li>✅ Considerar mascaramento para dados não essenciais</li>
                    <li>✅ Documentar finalidade do tratamento</li>
                    <li>✅ Garantir direitos dos titulares (acesso, correção, exclusão)</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="success-zone">
                <h4>🟢 SITUAÇÃO CONTROLADA</h4>
                <p><strong>Volume baixo de dados pessoais</strong></p>
                <ul>
                    <li>✅ Manter boas práticas de segurança</li>
                    <li>✅ Revisar periodicamente necessidade dos dados</li>
                    <li>✅ Documentar procedimentos de tratamento</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

    # SEÇÃO 5: MASCARAMENTO (opcional - só aparece se já analisou)
    if st.session_state.df_analisado is not None:
        st.markdown("## 🛡️ 5. Mascaramento de Dados (Opcional)")

        st.info("""
        ℹ️ **Esta etapa é opcional!** Se você não precisa mascarar os dados, pode pular direto para a exportação abaixo.
        O mascaramento é recomendado apenas quando você vai compartilhar ou publicar os dados.
        """)

        df = st.session_state.df_analisado
        coluna_texto = st.session_state.get('coluna_texto', None)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class="success-zone">
            <h4>🟢 Modo PARCIAL</h4>
            <p>Mantém formato do dado</p>
            <p><strong>CPF:</strong> 123.456.789-00 ➝ ***.456.789-**</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="danger-zone">
            <h4>🔴 Modo PROTEÇÃO TOTAL</h4>
            <p>Segurança máxima</p>
            <p>Substitui por: <strong>[INFORMAÇÃO PROTEGIDA LGPD]</strong></p>
            </div>
            """, unsafe_allow_html=True)

        col_config1, col_config2 = st.columns(2)

        with col_config1:
            modo_mascaramento = st.radio(
                "Modo:",
                options=['PARCIAL', 'PROTECAO_TOTAL']
            )

        with col_config2:
            tipos_mascarar = st.multiselect(
                "Tipos de dados:",
                options=['todos', 'cpf', 'rg', 'email', 'telefone', 'nome'],
                default=['todos']
            )

        if st.button("🛡️ APLICAR MASCARAMENTO E BAIXAR", type="primary", use_container_width=True):
            if tipos_mascarar:
                with st.spinner(f'🔒 Aplicando mascaramento...'):
                    df_original_para_mascarar = st.session_state.df_original.copy()

                    if coluna_texto and coluna_texto in df_original_para_mascarar.columns:
                        detector = st.session_state.detector
                        textos = df_original_para_mascarar[coluna_texto].fillna("").astype(str).tolist()

                        progress_bar = st.progress(0)
                        textos_mascarados = []
                        batch_size = 100
                        total = len(textos)

                        for i in range(0, total, batch_size):
                            batch = textos[i:i+batch_size]
                            mascarados = detector.apply_masking_batch(batch, mode=modo_mascaramento)
                            textos_mascarados.extend(mascarados)
                            progress_bar.progress(min((i + batch_size) / total, 1.0))

                        df_original_para_mascarar[coluna_texto] = textos_mascarados
                        progress_bar.empty()

                    st.session_state.df_mascarado_limpo = df_original_para_mascarar

                    # Cria arquivo para download
                    buffer = io.BytesIO()
                    df_original_para_mascarar.to_excel(buffer, index=False, engine='openpyxl')
                    buffer.seek(0)

                    st.success("✅ Mascaramento concluído!")

                    st.download_button(
                        label="⬇️ BAIXAR ARQUIVO MASCARADO",
                        data=buffer,
                        file_name=f"dados_mascarados_{modo_mascaramento}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True
                    )

                    st.balloons()
            else:
                st.warning("⚠️ Selecione pelo menos um tipo de dado.")

        st.markdown("---")

    # SEÇÃO 6: EXPORTAÇÃO (sempre visível se há análise)
    if st.session_state.df_analisado is not None:
        st.markdown("## 💾 6. Exportar Relatórios e Dados")

        df = st.session_state.df_analisado

        col1, col2 = st.columns(2)

        with col1:
            # Excel completo
            buffer_excel = io.BytesIO()
            with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Dados Completos', index=False)

                df_pii = df[df['contém_pii'] == True]
                df_pii.to_excel(writer, sheet_name='Com PII', index=False)

                stats = {
                    'Métrica': [
                        'Total de Registros',
                        'Com PII',
                        '✅ CPF VALIDADO',
                        '⚠️ CPF NÃO VALIDADO',
                        'RG',
                        'Email',
                        'Telefone',
                        'Nome',
                        'Endereço'
                    ],
                    'Valor': [
                        len(df),
                        df['contém_pii'].sum(),
                        df['cpf_validado'].sum(),
                        df['cpf_nao_validado'].sum(),
                        df['rg_detectado'].sum(),
                        df['email_detectado'].sum(),
                        df['telefone_detectado'].sum(),
                        df['nome_detectado'].sum(),
                        df['endereco_detectado'].sum()
                    ]
                }
                pd.DataFrame(stats).to_excel(writer, sheet_name='Estatísticas', index=False)

            buffer_excel.seek(0)

            st.download_button(
                label="📊 Baixar Excel Completo",
                data=buffer_excel,
                file_name=f"analise_pii_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col2:
            csv = df.to_csv(index=False, encoding='utf-8-sig')

            st.download_button(
                label="📄 Baixar CSV",
                data=csv,
                file_name=f"analise_pii_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )


if __name__ == "__main__":
    main()
