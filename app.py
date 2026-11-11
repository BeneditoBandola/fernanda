import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd

# Page config
st.set_page_config(
    page_title="App de Visitas - Promotora",
    page_icon="🛒",
    layout="wide"
)

DATA_FILE = "visitas_dados.json"
EXCEL_FILE = "clientes com coordenadas.xlsx"

# Load saved visits
def carregar_dados():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

# Save visits
def salvar_dados(dados):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# Load clients from Excel file on GitHub
@st.cache_data
def carregar_clientes():
    if os.path.exists(EXCEL_FILE):
        try:
            df_excel = pd.read_excel(EXCEL_FILE)
            # Clean columns
            df_excel['CODIGO'] = df_excel['CODIGO'].astype(str).str.replace(r'\.0$', '', regex=True)
            return df_excel
        except Exception as e:
            st.error(f"Erro ao ler a planilha: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

df_clientes = carregar_clientes()

st.title("🛒 App de Roteiro e Visitas - Promotora")
st.markdown("Consulte a relação de clientes e endereços da planilha do GitHub, registre atendimentos em campo com fotos e relatos, e gere relatórios em PDF para a diretoria.")

st.sidebar.header("Navegação")
menu = st.sidebar.selectbox("Escolha a opção", ["Relação de Clientes & Endereços", "Nova Visita / Check-in", "Histórico de Visitas & PDF"])

if menu == "Relação de Clientes & Endereços":
    st.subheader("📋 Relação de Clientes e Endereços (Planilha do GitHub)")
    
    if df_clientes.empty:
        st.warning(f"O arquivo '{EXCEL_FILE}' não foi encontrado no repositório.")
    else:
        # Search filter
        busca = st.text_input("🔍 Pesquisar por Nome, Código, Bairro ou Cidade", "")
        
        df_exibicao = df_clientes.copy()
        if busca:
            mask = df_exibicao.astype(str).apply(lambda x: x.str.contains(busca, case=False, na=False)).any(axis=1)
            df_exibicao = df_exibicao[df_exibicao.index.isin(df_exibicao[mask].index)]
            
        st.info(f"Mostrando {len(df_exibicao)} cliente(s) cadastrados na planilha.")
        
        # Show table with main columns
        colunas_exibir = [c for c in ['CODIGO', 'NOME', 'ENDEREÇO', 'BAIRRO', 'CIDADE', 'UF', 'LATITUDE', 'LONGITUDE'] if c in df_exibicao.columns]
        st.dataframe(df_exibicao[colunas_exibir], use_container_width=True)

elif menu == "Nova Visita / Check-in":
    st.subheader("📝 Registrar Atendimento em PDV")
    
    if df_clientes.empty:
        st.warning("Nenhum cliente carregado da planilha do GitHub.")
    else:
        # Prepare client options
        df_clientes['OPCAO_STR'] = df_clientes['CODIGO'] + " - " + df_clientes['NOME'].fillna('') + " (" + df_clientes['CIDADE'].fillna('') + ")"
        cliente_opcoes = df_clientes['OPCAO_STR'].tolist()
        
        cliente_selecionado_str = st.selectbox("Selecione o Cliente / Loja", cliente_opcoes)
        
        # Get selected client row
        cliente_info = df_clientes[df_clientes['OPCAO_STR'] == cliente_selecionado_str].iloc[0]
        
        with st.expander("📍 Ver Endereço Completo e Coordenadas"):
            st.write(f"**Código:** {cliente_info.get('CODIGO', '')}")
            st.write(f"**Nome:** {cliente_info.get('NOME', '')}")
            st.write(f"**Endereço:** {cliente_info.get('ENDEREÇO', '')}")
            st.write(f"**Bairro:** {cliente_info.get('BAIRRO', '')}")
            st.write(f"**Cidade/UF:** {cliente_info.get('CIDADE', '')} - {cliente_info.get('UF', '')}")
            st.write(f"**Latitude / Longitude:** {cliente_info.get('LATITUDE', '')}, {cliente_info.get('LONGITUDE', '')}")
            
        st.markdown("---")
        
        promotora_nome = st.text_input("Nome da Promotora", value="Promotora Campo")
        data_visita = st.date_input("Data da Visita", value=datetime.now())
        
        st.markdown("### 📸 Fotos do Ponto de Venda")
        fotos_upload = st.file_uploader("Tirar ou carregar fotos da gôndola/exposição", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        
        st.markdown("### 🎙️ Relato por Voz / Áudio (Transcrição)")
        st.info("💡 A promotora pode ditar o áudio ou escrever o relato do que tem de produtos e o que foi arrumado.")
        relato_texto = st.text_area("Relato do Atendimento (Transcrito ou Digitado)", placeholder="Ex: Gôndola organizada, colocado ponto extra de sachê...")
        
        if st.button("💾 Enviar e Salvar Visita", type="primary"):
            if not relato_texto and not fotos_upload:
                st.warning("Por favor, adicione pelo menos um relato ou uma foto antes de salvar.")
            else:
                fotos_salvas = []
                os.makedirs("fotos_visitas", exist_ok=True)
                if fotos_upload:
                    for idx, f in enumerate(fotos_upload):
                        f_path = os.path.join("fotos_visitas", f"{cliente_info['CODIGO']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{idx}.jpg")
                        with open(f_path, "wb") as f_out:
                            f_out.write(f.getbuffer())
                        fotos_salvas.append(f_path)
                
                nova_visita = {
                    "id": datetime.now().strftime('%Y%m%d%H%M%S'),
                    "data": str(data_visita),
                    "promotora": promotora_nome,
                    "codigo": str(cliente_info.get('CODIGO', '')),
                    "cliente": str(cliente_info.get('NOME', '')),
                    "cidade": str(cliente_info.get('CIDADE', '')),
                    "endereco": str(cliente_info.get('ENDEREÇO', '')),
                    "bairro": str(cliente_info.get('BAIRRO', '')),
                    "relato": relato_texto,
                    "fotos": fotos_salvas
                }
                
                dados_existentes = carregar_dados()
                dados_existentes.append(nova_visita)
                salvar_dados(dados_existentes)
                
                st.success("Visita registrada com sucesso e salva no JSON com segurança! 🚀")

elif menu == "Histórico de Visitas & PDF":
    st.subheader("📊 Histórico de Visitas Realizadas e Relatório PDF")
    
    dados = carregar_dados()
    
    if not dados:
        st.info("Nenhuma visita registrada até o momento.")
    else:
        df_visitas = pd.DataFrame(dados)
        st.dataframe(df_visitas[["data", "promotora", "codigo", "cliente", "cidade", "relato"]], use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 📄 Gerar Relatório Executivo em PDF para a Diretoria")
        
        if st.button("Gerar PDF Executivo", type="primary"):
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            
            pdf_filename = "relatorio_visitas_diretoria.pdf"
            doc = SimpleDocTemplate(pdf_filename, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            story = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor("#1A365D"), spaceAfter=15)
            subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor("#4A5568"), spaceAfter=20)
            
            story.append(Paragraph("Relatório de Visitas e Execução em PDV", title_style))
            story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", subtitle_style))
            story.append(Spacer(1, 10))
            
            for v in dados:
                story.append(Paragraph(f"<b>Cliente:</b> {v['codigo']} - {v['cliente']} ({v['cidade']})", styles['Heading3']))
                story.append(Paragraph(f"<b>Endereço:</b> {v.get('endereco', '')} - Bairro: {v.get('bairro', '')}", styles['Normal']))
                story.append(Paragraph(f"<b>Data:</b> {v['data']} | <b>Promotora:</b> {v['promotora']}", styles['Normal']))
                story.append(Paragraph(f"<b>Relato / Ações:</b> {v['relato']}", styles['Normal']))
                story.append(Spacer(1, 5))
                
                if v.get("fotos"):
                    story.append(Paragraph("<b>Registros Fotográficos:</b>", styles['Normal']))
                    img_elements = []
                    for foto_path in v["fotos"]:
                        if os.path.exists(foto_path):
                            try:
                                img = RLImage(foto_path, width=120, height=160)
                                img_elements.append(img)
                            except Exception:
                                pass
                    if img_elements:
                        t = Table([img_elements], colWidths=[130]*len(img_elements))
                        t.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
                        story.append(t)
                story.append(Spacer(1, 15))
                story.append(Paragraph("-" * 80, subtitle_style))
            
            doc.build(story)
            
            with open(pdf_filename, "rb") as pdf_file:
                st.download_button(
                    label="📥 Baixar PDF Relatório Diretoria",
                    data=pdf_file,
                    file_name="relatorio_visitas_executivo.pdf",
                    mime="application/pdf",
                    type="primary"
                )
            st.success("PDF gerado com sucesso!")
