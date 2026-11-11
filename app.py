import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd
import tempfile
import speech_recognition as sr

# Page config
st.set_page_config(
    page_title="App de Visitas - Promotora",
    page_icon="📍",
    layout="wide"
)

DATA_FILE = "visitas_dados.json"
EXCEL_FILE = "clientes com coordenadas.xlsx"

# Specific client codes for the route
CLIENTE_CODES_ROTA = [
    "23485", "28572", "21115", "21816", "21609", "21161", "21648", 
    "23128", "24334", "23804", "21918", "23754", "26377", "21933", 
    "21121", "21927", "21522", "21917", "24724", "24270", "27010", 
    "21921", "21874"
]

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

# Load clients from Excel file on GitHub and filter only route clients
@st.cache_data
def carregar_clientes():
    if os.path.exists(EXCEL_FILE):
        try:
            df_excel = pd.read_excel(EXCEL_FILE, engine='openpyxl')
            df_excel['CODIGO'] = df_excel['CODIGO'].astype(str).str.replace(r'\\.0$', '', regex=True)
            df_filtrado = df_excel[df_excel['CODIGO'].isin(CLIENTE_CODES_ROTA)].copy()
            
            # Converter latitude e longitude para formato numérico correto (substituindo vírgula por ponto se necessário)
            for col in ['LATITUDE', 'LONGITUDE']:
                if col in df_filtrado.columns:
                    if df_filtrado[col].dtype == object:
                        df_filtrado[col] = df_filtrado[col].astype(str).str.replace(',', '.', regex=False)
                    df_filtrado[col] = pd.to_numeric(df_filtrado[col], errors='coerce')
            
            obs_dict = {
                "23485": ("Não compra Royal", ""),
                "28572": ("Não compra Royal", ""),
                "21115": ("Não compra Royal", ""),
                "21816": ("Não compra Royal, mas tem bastante Mars", ""),
                "21609": ("Não compra Royal", "Não passa na frente"),
                "21161": ("Não compra Royal", ""),
                "21648": ("Não compra Royal", ""),
                "23128": ("Não compra Royal, mas tem bastante Mars", ""),
                "24334": ("Não compra Royal", ""),
                "23804": ("Não compra Royal", ""),
                "21918": ("Não compra Royal", ""),
                "23754": ("Não compra Royal", ""),
                "26377": ("", ""),
                "21933": ("Só recebeu bonificação, nunca comprou", ""),
                "21121": ("Não compra Royal", ""),
                "21927": ("Não compra Royal", ""),
                "21522": ("Não compra Royal, mas tem bastante Mars", ""),
                "21917": ("Não compra Royal, mas tem bastante Mars", ""),
                "24724": ("Não compra Royal", ""),
                "24270": ("Compra Royal", ""),
                "27010": ("Compra Royal", "Clínica veterinária"),
                "21921": ("Compra Royal", ""),
                "21874": ("Compra Royal", "")
            }
            
            df_filtrado['OBS'] = df_filtrado['CODIGO'].map(lambda x: obs_dict.get(x, ("", ""))[0])
            df_filtrado['OBS_2'] = df_filtrado['CODIGO'].map(lambda x: obs_dict.get(x, ("", ""))[1])
            
            return df_filtrado
        except Exception as e:
            st.error(f"Erro ao ler a planilha: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

df_clientes = carregar_clientes()

st.title("App de Roteiro e Visitas - Promotora")
st.markdown("Consulte a relação dos clientes da rota, filtre por cidade, registre atendimentos em campo com fotos e relatos, e gere relatórios em PDF para a diretoria.")

st.sidebar.header("Navegação")
menu = st.sidebar.selectbox("Escolha a opção", ["Relação de Clientes & Endereços", "Nova Visita / Check-in", "Histórico de Visitas & PDF"])

if menu == "Relação de Clientes & Endereços":
    st.subheader("📋 Relação de Clientes e Endereços da Rota")
    
    if df_clientes.empty:
        st.warning(f"O arquivo '{EXCEL_FILE}' não foi encontrado ou nenhum cliente da rota foi encontrado na planilha.")
    else:
        cidades_disponiveis = ["Todas"] + sorted(df_clientes['CIDADE'].dropna().unique().tolist())
        cidade_escolhida = st.selectbox("🏙️ Filtrar por Cidade", cidades_disponiveis)
        
        df_exibicao = df_clientes.copy()
        if cidade_escolhida != "Todas":
            df_exibicao = df_exibicao[df_exibicao['CIDADE'] == cidade_escolhida]
            
        busca = st.text_input("🔍 Pesquisar por Nome, Código ou Bairro", "")
        if busca:
            mask = df_exibicao.astype(str).apply(lambda x: x.str.contains(busca, case=False, na=False)).any(axis=1)
            df_exibicao = df_exibicao[df_exibicao.index.isin(df_exibicao[mask].index)]
            
        st.info(f"Mostrando {len(df_exibicao)} cliente(s).")
        
        colunas_exibir = [c for c in ['CODIGO', 'NOME', 'ENDEREÇO', 'BAIRRO', 'CIDADE', 'UF', 'OBS', 'OBS_2', 'LATITUDE', 'LONGITUDE'] if c in df_exibicao.columns]
        st.dataframe(df_exibicao[colunas_exibir], use_container_width=True)
        
        if 'LATITUDE' in df_exibicao.columns and 'LONGITUDE' in df_exibicao.columns:
            df_mapa = df_exibicao.dropna(subset=['LATITUDE', 'LONGITUDE'])
            if not df_mapa.empty:
                st.markdown("### 🗺️ Mapa dos Clientes")
                st.map(df_mapa, latitude='LATITUDE', longitude='LONGITUDE', zoom=11)

elif menu == "Nova Visita / Check-in":
    st.subheader("📝 Registrar Atendimento em PDV")
    
    if df_clientes.empty:
        st.warning("Nenhum cliente carregado da planilha do GitHub.")
    else:
        cidades_disponiveis = ["Todas"] + sorted(df_clientes['CIDADE'].dropna().unique().tolist())
        cidade_checkin = st.selectbox("🏙️ Filtrar Cidade para Atendimento", cidades_disponiveis, key="cidade_chk")
        
        df_chk = df_clientes.copy()
        if cidade_checkin != "Todas":
            df_chk = df_chk[df_chk['CIDADE'] == cidade_checkin]
            
        if df_chk.empty:
            st.warning("Nenhum cliente encontrado para esta cidade.")
        else:
            df_chk['OPCAO_STR'] = df_chk['CODIGO'] + " - " + df_chk['NOME'].fillna('') + " (" + df_chk['CIDADE'].fillna('') + ")"
            cliente_opcoes = df_chk['OPCAO_STR'].tolist()
            
            cliente_selecionado_str = st.selectbox("Selecione o Cliente / Loja", cliente_opcoes)
            cliente_info = df_chk[df_chk['OPCAO_STR'] == cliente_selecionado_str].iloc[0]
            
            st.markdown("---")
            st.markdown("### 📍 Informações do Cliente Selecionado")
            st.write(f"**Código:** {cliente_info.get('CODIGO', '')}")
            st.write(f"**Nome:** {cliente_info.get('NOME', '')}")
            st.write(f"**Endereço:** {cliente_info.get('ENDEREÇO', '')} - Bairro: {cliente_info.get('BAIRRO', '')}")
            st.write(f"**Cidade/UF:** {cliente_info.get('CIDADE', '')} - {cliente_info.get('UF', '')}")
            st.write(f"**Obs:** {cliente_info.get('OBS', '')}")
            if cliente_info.get('OBS_2'):
                st.write(f"**Obs 2:** {cliente_info.get('OBS_2', '')}")
            
            lat = cliente_info.get('LATITUDE')
            lon = cliente_info.get('LONGITUDE')
            if pd.notna(lat) and pd.notna(lon):
                maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                st.markdown(f"🗺️ **Abrir localização no Google Maps:** [Clique aqui para abrir a rota]({maps_url})", unsafe_allow_html=True)
            else:
                st.write("🗺️ **Google Maps:** Coordenadas não disponíveis para este cliente.")
                
            st.markdown("---")
            
            promotora_nome = st.text_input("Nome da Promotora", value="Fernanda")
            data_visita = st.date_input("Data da Visita", value=datetime.now())
            
            st.markdown("### 📸 Fotos do Ponto de Venda")
            fotos_upload = st.file_uploader("Tirar ou carregar fotos da gôndola/exposição", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
            
            st.markdown("### 🎙️ Relato por Voz / Áudio (Transcrição)")
            st.info("💡 A promotora pode ditar o áudio ou escrever o relato do que tem de produtos e o que foi arrumado.")
            
            if 'texto_transcrito_voz' not in st.session_state:
                st.session_state['texto_transcrito_voz'] = ""
            if 'audio_key_id' not in st.session_state:
                st.session_state['audio_key_id'] = 0

            audio_gravado = st.audio_input("🎙️ Grave o áudio falando as observações da loja:", key=f"audio_input_{st.session_state['audio_key_id']}")
            
            if audio_gravado is not None:
                col_transc, col_apagar = st.columns([3, 1])
                with col_transc:
                    if st.button("✨ Transcrever Áudio em Texto"):
                        with st.spinner("Interpretando e transcrevendo áudio..."):
                            try:
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f_audio:
                                    f_audio.write(audio_gravado.read())
                                    caminho_audio_temp = f_audio.name

                                r = sr.Recognizer()
                                with sr.AudioFile(caminho_audio_temp) as source:
                                    audio_data = r.record(source)
                                    texto_falado = r.recognize_google(audio_data, language="pt-BR")
                                    st.session_state['texto_transcrito_voz'] = texto_falado
                                    st.success("✅ Áudio transcrito com sucesso!")
                            except sr.UnknownValueError:
                                st.warning("⚠️ Não foi possível entender o áudio. Tente falar mais perto.")
                            except Exception as e:
                                st.error(f"Erro ao transcrever: {e}")
                with col_apagar:
                    if st.button("🗑️ Apagar Tudo"):
                        st.session_state['texto_transcrito_voz'] = ""
                        st.session_state['audio_key_id'] += 1
                        st.rerun()

            relato_texto = st.text_area(
                "Relato do Atendimento (Transcrito ou Digitado)",
                value=st.session_state['texto_transcrito_voz'],
                placeholder="Ex: Gôndola organizada, colocado ponto extra de sachê..."
            )
            
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
                    
                    data_formatada = data_visita.strftime('%d/%m/%Y')
                    hora_envio = datetime.now().strftime('%H:%M')
                    
                    nova_visita = {
                        "id": datetime.now().strftime('%Y%m%d%H%M%S'),
                        "data": data_formatada,
                        "hora": hora_envio,
                        "promotora": promotora_nome,
                        "codigo": str(cliente_info.get('CODIGO', '')),
                        "cliente": str(cliente_info.get('NOME', '')),
                        "cidade": str(cliente_info.get('CIDADE', '')),
                        "endereco": str(cliente_info.get('ENDEREÇO', '')),
                        "bairro": str(cliente_info.get('BAIRRO', '')),
                        "obs": str(cliente_info.get('OBS', '')),
                        "obs_2": str(cliente_info.get('OBS_2', '')),
                        "relato": relato_texto,
                        "fotos": fotos_salvas
                    }
                    
                    dados_existentes = carregar_dados()
                    dados_existentes.append(nova_visita)
                    salvar_dados(dados_existentes)
                    
                    st.success("Visita registrada com sucesso e salva no JSON com segurança! 🚀")

elif menu == "Histórico de Visitas & PDF":
    st.subheader("📊 Histórico de Visitas Realizadas e Exclusão / PDF")
    
    dados = carregar_dados()
    
    if not dados:
        st.info("Nenhuma visita registrada até o momento.")
    else:
        st.markdown("### 🗑️ Gerenciar / Apagar Visitas Incorretas")
        visita_opcoes = {f"[{v['data']} às {v.get('hora', '--:--')}] {v['codigo']} - {v['cliente']} (Promotora: {v['promotora']}) (ID: {v['id']})": v['id'] for v in dados}
        visita_para_apagar = st.selectbox("Selecione uma visita para remover, se necessário", ["Nenhuma"] + list(visita_opcoes.keys()))
        
        if visita_para_apagar != "Nenhuma":
            if st.button("🗑️ Apagar Visita Selecionada", type="secondary"):
                id_alvo = visita_opcoes[visita_para_apagar]
                dados_atualizados = [v for v in dados if v['id'] != id_alvo]
                salvar_dados(dados_atualizados)
                st.success("Visita apagada com sucesso! Atualize a página se necessário.")
                st.rerun()
                
        st.markdown("---")
        st.markdown("### 📋 Visitas Registradas")
        df_visitas = pd.DataFrame(dados)
        if 'hora' not in df_visitas.columns:
            df_visitas['hora'] = '--:--'
        st.dataframe(df_visitas[["data", "hora", "promotora", "codigo", "cliente", "cidade", "relato"]], use_container_width=True)
        
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
                if v.get('obs'):
                    story.append(Paragraph(f"<b>Obs:</b> {v.get('obs', '')}", styles['Normal']))
                if v.get('obs_2'):
                    story.append(Paragraph(f"<b>Obs 2:</b> {v.get('obs_2', '')}", styles['Normal']))
                hora_str = f" às {v['hora']}" if v.get('hora') else ""
                story.append(Paragraph(f"<b>Data:</b> {v['data']}{hora_str} | <b>Promotora:</b> {v['promotora']}", styles['Normal']))
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
