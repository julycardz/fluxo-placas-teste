import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import os

# --- CRIAÇÃO AUTOMÁTICA DAS PASTAS DE ARMAZENAMENTO ---
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
PASTA_CROQUIS = os.path.join(diretorio_atual, "fotos_croquis")
PASTA_ANTES = os.path.join(diretorio_atual, "fotos_antes")
PASTA_DEPOIS = os.path.join(diretorio_atual, "fotos_depois")

for pasta in [PASTA_CROQUIS, PASTA_ANTES, PASTA_DEPOIS]:
    if not os.path.exists(pasta):
        os.makedirs(pasta)

# --- CONEXÃO COM O BANCO DE TESTE (SQLITE) ---
engine = create_engine("sqlite:///fluxo_teste.db")

# Cria a tabela automaticamente 
with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS fluxo_notas (
            PLACA VARCHAR(50) PRIMARY KEY,
            NSPR VARCHAR(50),
            SUPERVISOR VARCHAR(100),
            SOLICITANTE VARCHAR(100),
            CROQUI VARCHAR(255),
            CENTRO_TRABALHO VARCHAR(150),
            DATA_SOLICITACAO VARCHAR(10),
            DATA_VENCIMENTO VARCHAR(10),
            STATUS VARCHAR(50),
            ORCAMENTO_MATERIAL DECIMAL(10,2),
            NOME_ALMOXARIFE VARCHAR(100),
            DATA_LIBERADA VARCHAR(10),
            INSTALADOR VARCHAR(100),
            DATA_INSTALADA VARCHAR(10),
            FOTO_ANTES VARCHAR(255),
            FOTO_DEPOIS VARCHAR(255),
            FECHADOR VARCHAR(100),
            DATA_FECHAMENTO VARCHAR(10)
        )
    """))
    conn.commit()

st.title("🔄 Fluxo de Notas e Instalações")

# Menu lateral
papel = st.sidebar.selectbox(
    "Selecione sua Etapa de Trabalho", 
    ["📊 Painel de Controle (Acompanhamento)",
     "1. Criar Solicitação (Pessoa A)", 
     "2. Orçamento e Almoxarifado (Pessoa B)", 
     "3. Fila de Instalação/Campo (Pessoa C)", 
     "4. Fechamento da Nota (Pessoa D)"]
)

# ================= PAINEL DE CONTROLE (ACOMPANHAMENTO) =================
if papel == "📊 Painel de Controle (Acompanhamento)":
    st.subheader("🔍 Acompanhamento Geral das Placas")
    
    try:
        df_geral = pd.read_sql("SELECT * FROM fluxo_notas", con=engine)
    except Exception:
        df_geral = pd.DataFrame()

    if df_geral.empty:
        st.info("Nenhuma solicitação cadastrada no sistema ainda! Vá na 'Etapa 1' para começar.")
    else:
        tot_geral = len(df_geral)
        tot_almox = len(df_geral[df_geral['STATUS'] == 'Aguardando Orçamento/Material'])
        tot_campo = len(df_geral[df_geral['STATUS'] == 'Aguardando Instalação'])
        tot_fech = len(df_geral[df_geral['STATUS'] == 'Instalado - Aguardando Fechamento'])
        tot_ok = len(df_geral[df_geral['STATUS'] == 'Finalizado'])

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("📌 Cadastradas", tot_geral)
        c2.metric("📦 Almoxarifado", tot_almox)
        c3.metric("🛠️ Em Campo", tot_campo)
        c4.metric("📝 Aguardando Nota", tot_fech)
        c5.metric("✅ Finalizadas", tot_ok)

        st.markdown("---")
        st.write("### 🗂️ Status de Cada Placa")
        
        aba1, aba2, aba3, aba4, aba_busca = st.tabs([
            "🕒 1. No Almoxarifado", 
            "🛠️ 2. Pendentes (Em Campo)", 
            "📝 3. Instaladas (Aguardando Nota)", 
            "✅ 4. Concluídas",
            "🔍 Buscar Placa / NSPR"
        ])

        with aba1:
            st.markdown("#### 📦 Placas aguardando liberação de material/orçamento")
            df_aba1 = df_geral[df_geral['STATUS'] == 'Aguardando Orçamento/Material']
            if df_aba1.empty:
                st.success("Nenhuma placa parada nesta etapa! 🎉")
            else:
                st.dataframe(df_aba1[['PLACA', 'NSPR', 'SUPERVISOR', 'SOLICITANTE', 'CENTRO_TRABALHO', 'DATA_SOLICITACAO', 'DATA_VENCIMENTO']], use_container_width=True, hide_index=True)
                placa_croqui_ver = st.selectbox("Selecione uma placa para visualizar o Croqui de Serviço:", df_aba1['PLACA'], key="ver_croqui_aba1")
                reg_croqui = df_aba1[df_aba1['PLACA'] == placa_croqui_ver].iloc[0]
                if os.path.exists(str(reg_croqui['CROQUI'])):
                    st.image(reg_croqui['CROQUI'], caption="Croqui Anexado para o Serviço", width=350)

        with aba2:
            st.markdown("#### 🛠️ Placas liberadas que o instalador precisa colocar em campo")
            df_aba2 = df_geral[df_geral['STATUS'] == 'Aguardando Instalação']
            if df_aba2.empty:
                st.success("Sem pendências de instalação no campo! 🚀")
            else:
                st.dataframe(df_aba2[['PLACA', 'NSPR', 'SUPERVISOR', 'CENTRO_TRABALHO', 'NOME_ALMOXARIFE', 'DATA_LIBERADA', 'ORCAMENTO_MATERIAL', 'DATA_VENCIMENTO']], use_container_width=True, hide_index=True)

        with aba3:
            st.markdown("#### 📝 Placas já instaladas esperando fechamento de nota no financeiro")
            df_aba3 = df_geral[df_geral['STATUS'] == 'Instalado - Aguardando Fechamento']
            if df_aba3.empty:
                st.info("Nenhuma nota pendente de fechamento.")
            else:
                st.dataframe(df_aba3[['PLACA', 'NSPR', 'SUPERVISOR', 'INSTALADOR', 'DATA_INSTALADA', 'SOLICITANTE']], use_container_width=True, hide_index=True)
                placa_fotos = st.selectbox("Selecione a placa instalada para checar o trabalho:", df_aba3['PLACA'], key="fotos_aba3")
                reg_foto = df_aba3[df_aba3['PLACA'] == placa_fotos].iloc[0]
                
                col_img1, col_img2 = st.columns(2)
                with col_img1:
                    if os.path.exists(str(reg_foto['FOTO_ANTES'])):
                        st.image(reg_foto['FOTO_ANTES'], caption="Antes (Local)", use_container_width=True)
                with col_img2:
                    if os.path.exists(str(reg_foto['FOTO_DEPOIS'])):
                        st.image(reg_foto['FOTO_DEPOIS'], caption="Depois (Instalada)", use_container_width=True)

        with aba4:
            st.markdown("#### ✅ Histórico de solicitações 100% finalizadas e fechadas")
            df_aba4 = df_geral[df_geral['STATUS'] == 'Finalizado']
            if df_aba4.empty:
                st.info("Nenhuma solicitação finalizada ainda.")
            else:
                st.dataframe(df_aba4[['PLACA', 'NSPR', 'SUPERVISOR', 'SOLICITANTE', 'INSTALADOR', 'FECHADOR', 'DATA_FECHAMENTO']], use_container_width=True, hide_index=True)

        with aba_busca:
            st.markdown("#### 🔍 Rastrear por Placa ou NSPR")
            busca = st.text_input("Digite a Placa ou o número da NSPR:", "").upper().strip()
            if busca:
                resultado = df_geral[
                    df_geral['PLACA'].str.contains(busca, na=False) | 
                    df_geral['NSPR'].str.contains(busca, na=False)
                ]
                if resultado.empty:
                    st.warning("Nenhum registro encontrado com esse termo de busca.")
                else:
                    for _, row in resultado.iterrows():
                        st.info(f"📍 A Placa **{row['PLACA']}** (NSPR: **{row['NSPR']}**) está na etapa: **{row['STATUS']}**")
                        st.write(row.dropna().to_dict())

# ================= ETAPA 1 (PESSOA A) =================
elif papel == "1. Criar Solicitação (Pessoa A)":
    st.subheader("📝 Nova Solicitação de Placa")
    
    col1, col2 = st.columns(2)
    with col1:
        placa = st.text_input("Placa:").upper()
        nspr = st.text_input("Número da NSPR (Identificador do Serviço):").upper()
        supervisor = st.text_input("Nome do Supervisor:")
        solicitante = st.text_input("Quem está solicitando?")
    with col2:
        centro_trabalho = st.text_input("Centro de Trabalho:")
        foto_croqui = st.file_uploader("Insira a foto/croqui do serviço:", type=["png", "jpg", "jpeg"])
        data_vencimento = st.date_input("Data de Vencimento:", min_value=datetime.today())
    
    if foto_croqui:
        st.image(foto_croqui, caption="Pré-visualização do Croqui", width=250)

    if st.button("Enviar para Almoxarifado", type="primary"):
        if placa and nspr and supervisor and solicitante and foto_croqui:
            caminho_croqui = os.path.join(PASTA_CROQUIS, f"{placa}_croqui.jpg")
            with open(caminho_croqui, "wb") as f:
                f.write(foto_croqui.getbuffer())

            novo = {
                'PLACA': placa,
                'NSPR': nspr,
                'SUPERVISOR': supervisor,
                'SOLICITANTE': solicitante,
                'CROQUI': caminho_croqui,
                'CENTRO_TRABALHO': centro_trabalho,
                'DATA_SOLICITACAO': datetime.now().strftime("%Y-%m-%d"),
                'DATA_VENCIMENTO': data_vencimento.strftime("%Y-%m-%d"),
                'STATUS': 'Aguardando Orçamento/Material'
            }
            pd.DataFrame([novo]).to_sql('fluxo_notas', con=engine, if_exists='append', index=False)
            st.success(f"Solicitação da placa {placa} (NSPR: {nspr}) registrada com sucesso!")
            st.rerun()
        else:
            st.error("Por favor, preencha todos os campos obrigatórios (Placa, NSPR, Supervisor, Solicitante e Croqui)!")

# ================= ETAPA 2 (PESSOA B) =================
elif papel == "2. Orçamento e Almoxarifado (Pessoa B)":
    st.subheader("📦 Orçamento e Almoxarifado")
    
    df_almox = pd.read_sql("SELECT * FROM fluxo_notas WHERE STATUS = 'Aguardando Orçamento/Material'", con=engine)
    
    if df_almox.empty:
        st.info("Nenhuma placa aguardando liberação de material! 🎉")
    else:
        opcoes = {f"{row['PLACA']} (NSPR: {row['NSPR']})": row['PLACA'] for _, row in df_almox.iterrows()}
        opcao_selecionada = st.selectbox("Selecione o serviço para liberar:", list(opcoes.keys()))
        placa_selecionada = opcoes[opcao_selecionada]
        
        registro = df_almox[df_almox['PLACA'] == placa_selecionada].iloc[0]
        st.info(f"**NSPR:** {registro['NSPR']} | **Supervisor:** {registro['SUPERVISOR']} | **Solicitante:** {registro['SOLICITANTE']}\n\n🏢 **Centro de Trabalho:** {registro['CENTRO_TRABALHO']}")
        
        if os.path.exists(str(registro['CROQUI'])):
            st.image(registro['CROQUI'], caption="Croqui Anexado pela Solicitação", width=300)

        col1, col2 = st.columns(2)
        with col1:
            nome_almoxarife = st.text_input("Nome do Almoxarife:")
            orcamento = st.number_input("Orçamento do Material (R$):", min_value=0.0)
        with col2:
            data_liberada = st.date_input("Data Liberada para Instalar:")
            
        if st.button("Liberar para Instalação", type="primary"):
            if nome_almoxarife and orcamento > 0:
                with engine.connect() as conn:
                    conn.execute(
                        text("""UPDATE fluxo_notas 
                                SET STATUS='Aguardando Instalação', 
                                    ORCAMENTO_MATERIAL=:orcamento, 
                                    NOME_ALMOXARIFE=:almox, 
                                    DATA_LIBERADA=:data_lib 
                                WHERE PLACA=:placa"""),
                        {"orcamento": orcamento, "almox": nome_almoxarife, "data_lib": data_liberada.strftime("%Y-%m-%d"), "placa": placa_selecionada}
                    )
                    conn.commit()
                st.success(f"Material para a placa {placa_selecionada} liberado!")
                st.rerun()

# ================= ETAPA 3 (PESSOA C) =================
elif papel == "3. Fila de Instalação/Campo (Pessoa C)":
    st.subheader("🛠️ Fila de Instalação (Campo)")
    
    df_campo = pd.read_sql("SELECT * FROM fluxo_notas WHERE STATUS = 'Aguardando Instalação'", con=engine)
    
    if df_campo.empty:
        st.info("Nenhuma instalação pendente no momento!")
    else:
        opcoes = {f"{row['PLACA']} (NSPR: {row['NSPR']})": row['PLACA'] for _, row in df_campo.iterrows()}
        opcao_selecionada = st.selectbox("Escolha a placa que está instalada:", list(opcoes.keys()))
        placa_selecionada = opcoes[opcao_selecionada]
        
        registro_campo = df_campo[df_campo['PLACA'] == placa_selecionada].iloc[0]
        st.info(f"🏢 **Centro de Trabalho:** {registro_campo['CENTRO_TRABALHO']} | **NSPR:** {registro_campo['NSPR']} | **Supervisor:** {registro_campo['SUPERVISOR']}")
        
        if os.path.exists(str(registro_campo['CROQUI'])):
            st.image(registro_campo['CROQUI'], caption="Croqui/Modelo de Referência", width=300)

        col1, col2 = st.columns(2)
        with col1:
            instalador = st.text_input("Seu Nome:")
        with col2:
            data_instalada = st.date_input("Data Instalada:")
            
        col_foto1, col_foto2 = st.columns(2)
        with col_foto1:
            foto_antes = st.file_uploader("Tire foto do ANTES (Local vazio):", type=["png", "jpg", "jpeg"])
        with col_foto2:
            foto_depois = st.file_uploader("Tire foto do DEPOIS (Placa instalada):", type=["png", "jpg", "jpeg"])
            
        if st.button("Confirmar Instalação", type="primary"):
            if instalador and foto_antes and foto_depois:
                caminho_antes = os.path.join(PASTA_ANTES, f"{placa_selecionada}_antes.jpg")
                caminho_depois = os.path.join(PASTA_DEPOIS, f"{placa_selecionada}_depois.jpg")
                
                with open(caminho_antes, "wb") as f:
                    f.write(foto_antes.getbuffer())
                with open(caminho_depois, "wb") as f:
                    f.write(foto_depois.getbuffer())
                
                with engine.connect() as conn:
                    conn.execute(
                        text("""UPDATE fluxo_notas 
                                SET STATUS='Instalado - Aguardando Fechamento', 
                                    INSTALADOR=:instalador, 
                                    DATA_INSTALADA=:data_inst, 
                                    FOTO_ANTES=:f_antes, 
                                    FOTO_DEPOIS=:f_depois 
                                WHERE PLACA=:placa"""),
                        {
                            "instalador": instalador, 
                            "data_inst": data_instalada.strftime("%Y-%m-%d"), 
                            "f_antes": caminho_antes, 
                            "f_depois": caminho_depois, 
                            "placa": placa_selecionada
                        }
                    )
                    conn.commit()
                st.success("Instalação concluída com as fotos registradas!")
                st.rerun()

# ================= ETAPA 4 (PESSOA D) =================
elif papel == "4. Fechamento da Nota (Pessoa D)":
    st.subheader("🏁 Fechamento da Nota")
    
    df_fechamento = pd.read_sql("SELECT * FROM fluxo_notas WHERE STATUS = 'Instalado - Aguardando Fechamento'", con=engine)
    
    if df_fechamento.empty:
        st.info("Nenhuma nota pendente de fechamento!")
    else:
        opcoes = {f"{row['PLACA']} (NSPR: {row['NSPR']})": row['PLACA'] for _, row in df_fechamento.iterrows()}
        opcao_selecionada = st.selectbox("Selecione a placa para Fechamento:", list(opcoes.keys()))
        placa_selecionada = opcoes[opcao_selecionada]
        
        registro = df_fechamento[df_fechamento['PLACA'] == placa_selecionada].iloc[0]
        st.write(f"**NSPR:** {registro['NSPR']} | **Supervisor:** {registro['SUPERVISOR']} | **Instalado por:** {registro['INSTALADOR']} em {registro['DATA_INSTALADA']}")
        
        st.markdown("##### 🔍 Comparativo Completo do Serviço:")
        col_c, col_a, col_d = st.columns(3)
        with col_c:
            if os.path.exists(str(registro['CROQUI'])):
                st.image(registro['CROQUI'], caption="1. Croqui de Origem", use_container_width=True)
        with col_a:
            if os.path.exists(str(registro['FOTO_ANTES'])):
                st.image(registro['FOTO_ANTES'], caption="2. Foto do Antes (Campo)", use_container_width=True)
        with col_d:
            if os.path.exists(str(registro['FOTO_DEPOIS'])):
                st.image(registro['FOTO_DEPOIS'], caption="3. Foto do Depois (Instalada)", use_container_width=True)
                
        col1, col2 = st.columns(2)
        with col1:
            fechador = st.text_input("Nome de quem fechou:")
        with col2:
            data_fechamento = st.date_input("Data que fechou:")
            
        if st.button("Finalizar e Fechar Nota", type="primary"):
            if fechador:
                with engine.connect() as conn:
                    conn.execute(
                        text("""UPDATE fluxo_notas 
                                SET STATUS='Finalizado', 
                                    FECHADOR=:fechador, 
                                    DATA_FECHAMENTO=:data_fech 
                                WHERE PLACA=:placa"""),
                        {"fechador": fechador, "data_fech": data_fechamento.strftime("%Y-%m-%d"), "placa": placa_selecionada}
                    )
                    conn.commit()
                st.success("Nota encerrada e armazenada no histórico!")
                st.rerun()
