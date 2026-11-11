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

# Clients list (pre-loaded without days division)
CLIENTES_INICIAIS = [
    {"codigo": "23485", "nome": "AGROFARMA LTDA", "endereco": "Av. 21 de Dezembro, 875 - Loja 02, Centro", "cidade": "Goiana", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Agropecuária", "ultima_compra": "20/09/2023", "obs": "Não compra Royal"},
    {"codigo": "28572", "nome": "MUNDO ANIMAL GOIANA LTDA", "endereco": "Av. 21 de Dezembro, 1225, São Sebastião", "cidade": "Goiana", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Clínica Veterinária com Pet Shop", "ultima_compra": "10/08/2026", "obs": "Não compra Royal"},
    {"codigo": "21115", "nome": "R E R MOURA AGROPECUARIA LTDA", "endereco": "Av. 21 de Dezembro, 1235, São Sebastião", "cidade": "Goiana", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Agropecuária", "ultima_compra": "14/05/2026", "obs": "Não compra Royal"},
    {"codigo": "21816", "nome": "TREVO MERCANTIL AGROPECUARIA LTDA", "endereco": "Av. 21 de Dezembro, 1075 - Loja 01, São Sebastião", "cidade": "Goiana", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Agropecuária", "ultima_compra": "10/11/2026", "obs": "Não compra Royal, mas tem bastante Mars"},
    {"codigo": "21609", "nome": "CAYO H G PINTO LTDA", "endereco": "R. São Vicente de Paulo, 120, Centro", "cidade": "Coronel Pacheco", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Agropecuária", "ultima_compra": "30/05/2025", "obs": "Não compra Royal | Obs 2: Não passa na frente"},
    {"codigo": "21161", "nome": "NUTRI-FAUNA LTDA", "endereco": "Rodovia MG 353, 61 - Loja, Centro", "cidade": "Coronel Pacheco", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Agropecuária", "ultima_compra": "30/08/2024", "obs": "Não compra Royal"},
    {"codigo": "21648", "nome": "CASA DO BOIADEIRO LTDA", "endereco": "Av. Presidente Juscelino Kubitschek, 10334 - Galpão 01, Barreira do Triunfo", "cidade": "Juiz de Fora", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Agropecuária", "ultima_compra": "20/02/2026", "obs": "Não compra Royal"},
    {"codigo": "23128", "nome": "AGRO & PET DOS CAIPIRAS LTDA", "endereco": "Av. Presidente Juscelino Kubitschek, 10292 - Casa 01, Barreira do Triunfo", "cidade": "Juiz de Fora", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Agropecuária", "ultima_compra": "28/09/2026", "obs": "Não compra Royal, mas tem bastante Mars"},
    {"codigo": "24334", "nome": "KALINA DA SILVA CUNHA", "endereco": "Avenida Juiz de Fora, 4500, Grama", "cidade": "Juiz de Fora", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Médico Veterinário", "ultima_compra": "29/01/2026", "obs": "Não compra Royal"},
    {"codigo": "23804", "nome": "MD AGROPECUARIA LTDA", "endereco": "Av. Juiz de Fora, 2064 - Loja Maior, Grama", "cidade": "Juiz de Fora", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Agropecuária", "ultima_compra": "x", "obs": ""},
    {"codigo": "21918", "nome": "ROGNEI EGIDIO GOMES", "endereco": "Avenida Juiz de Fora, 1148 - Loja 1, Grama", "cidade": "Juiz de Fora", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Agropecuária", "ultima_compra": "06/11/2024", "obs": "Não compra Royal"},
    {"codigo": "23754", "nome": "WALTER D FREGUGLIA", "endereco": "Av. Juiz de Fora, 3659, Grama", "cidade": "Juiz de Fora", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Agropecuária", "ultima_compra": "11/06/2026", "obs": "Não compra Royal"},
    {"codigo": "26377", "nome": "BRUNO JOSE DA SILVA", "endereco": "Avenida Juiz de Fora, 4500 - Lote Granjas Guarujá, Grama", "cidade": "Juiz de Fora", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Agropecuária", "ultima_compra": "x", "obs": ""},
    {"codigo": "21933", "nome": "AGROPECUARIA GRAMA DOIS IRMAOS LTDA", "endereco": "Avenida Juiz de Fora, 1028 - Loja 01, Parque Guarani", "cidade": "Juiz de Fora", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Agropecuária", "ultima_compra": "x", "obs": "Só recebeu bonificação, nunca comprou"},
    {"codigo": "21121", "nome": "AGROPECUARIA SAO JORGE LTDA", "endereco": "Av. Juiz de Fora, 3809 - 3813, Grama", "cidade": "Juiz de Fora", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Agropecuária", "ultima_compra": "26/10/2026", "obs": "Não compra Royal"},
    {"codigo": "21927", "nome": "TERRA BOA AGROPECUARIA LTDA", "endereco": "Avenida Juiz de Fora, 10, Parque Guarani", "cidade": "Juiz de Fora", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Agropecuária", "ultima_compra": "15/01/2024", "obs": "Não compra Royal"},
    {"codigo": "21522", "nome": "DHIEGO MARTINS DE MEDEIROS", "endereco": "Rua Americo Lobo, 2471 - Loja, Bairu", "cidade": "Juiz de Fora", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Agropecuária", "ultima_compra": "01/10/2026", "obs": "Não compra Royal, mas tem bastante Mars"},
    {"codigo": "21917", "nome": "GOMES MONTEIRO AGROPECUARIA LTDA", "endereco": "Rua Americo Lobo, 2452 - Loja, Bairu", "cidade": "Juiz de Fora", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Agropecuária", "ultima_compra": "29/10/2026", "obs": "Não compra Royal, mas tem bastante Mars"},
    {"codigo": "24724", "nome": "THAINA DA SILVA NASCIMENTO", "endereco": "Rua Americo Lobo, 2313, Progresso", "cidade": "Juiz de Fora", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Agropecuária", "ultima_compra": "31/10/2024", "obs": "Não compra Royal"},
    {"codigo": "24270", "nome": "SUPERMERCADO DO CAO LTDA", "endereco": "Rua Americo Lobo, 1376, Bairu/Progresso", "cidade": "Juiz de Fora", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Agropecuária", "ultima_compra": "21/10/2026", "obs": "Compra Royal"},
    {"codigo": "27010", "nome": "DANIELA FERREIRA MAGDALENO", "endereco": "Rua Americo Lobo, 1177, Santa Terezinha", "cidade": "Juiz de Fora", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Clínicas Veterinárias", "ultima_compra": "01/10/2026", "obs": "Compra Royal | Clínica veterinária"},
    {"codigo": "21921", "nome": "CINTHIA COELHO PET SHOP PRODUTOS PARA ANIMAIS LTDA", "endereco": "Av. Barão do Rio Branco, 490, Manoel Honório", "cidade": "Juiz de Fora", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Pet Shop c/ Granel", "ultima_compra": "09/11/2026", "obs": "Compra Royal"},
    {"codigo": "21874", "nome": "BARBARA FELIPPE COMERCIAL LTDA", "endereco": "Av. Barão do Rio Branco, 1960, Centro", "cidade": "Juiz de Fora", "uf": "MG", "classificacao": "Especialista Pet", "ramo": "Agropecuária", "ultima_compra": "10/11/2026", "obs": "Compra Royal"}
]

st.title("🛒 App de Roteiro e Visitas - Promotora")
st.markdown("Registre as visitas em campo, adicione fotos, relate o que foi feito por áudio/texto e gere o relatório PDF para a diretoria.")

st.sidebar.header("Navegação")
menu = st.sidebar.selectbox("Escolha a opção", ["Nova Visita / Check-in", "Histórico de Visitas & PDF"])

if menu == "Nova Visita / Check-in":
    st.subheader("📝 Registrar Atendimento em PDV")
    
    # Seleção de Cliente
    cliente_opcoes = {f"{c['codigo']} - {c['nome']} ({c['cidade']})": c for c in CLIENTES_INICIAIS}
    cliente_selecionado_str = st.selectbox("Selecione o Cliente / Loja", list(cliente_opcoes.keys()))
    cliente_info = cliente_opcoes[cliente_selecionado_str]
    
    with st.expander("Ver Detalhes do Cliente Cadastrado"):
        st.write(f"**Código:** {cliente_info['codigo']}")
        st.write(f"**Endereço:** {cliente_info['endereco']}")
        st.write(f"**Cidade/UF:** {cliente_info['cidade']} - {cliente_info['uf']}")
        st.write(f"**Ramo:** {cliente_info['ramo']} | **Classificação:** {cliente_info['classificacao']}")
        st.write(f"**Última Compra:** {cliente_info['ultima_compra']}")
        st.write(f"**Observações:** {cliente_info['obs']}")
        
    st.markdown("---")
    
    # Captura de dados da visita
    promotora_nome = st.text_input("Nome da Promotora", value="Promotora Campo")
    data_visita = st.date_input("Data da Visita", value=datetime.now())
    
    st.markdown("### 📸 Fotos do Ponto de Venda")
    fotos_upload = st.file_uploader("Tirar ou carregar fotos da gôndola/exposição", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    st.markdown("### 🎙️ Relato por Voz / Áudio (Transcrição)")
    st.info("💡 A promotora pode ditar o áudio ou escrever o relato do que tem de produtos e o que foi arrumado.")
    relato_texto = st.text_area("Relato do Atendimento (Transcrito ou Digitado)", placeholder="Ex: Gôndola organizada, colocado ponto extra de sachê, cliente possui bastante estoque de concorrente...")
    
    if st.button("💾 Enviar e Salvar Visita", type="primary"):
        if not relato_texto and not fotos_upload:
            st.warning("Por favor, adicione pelo menos um relato ou uma foto antes de salvar.")
        else:
            # Salvar fotos se houver
            fotos_salvas = []
            os.makedirs("fotos_visitas", exist_ok=True)
            if fotos_upload:
                for idx, f in enumerate(fotos_upload):
                    f_path = os.path.join("fotos_visitas", f"{cliente_info['codigo']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{idx}.jpg")
                    with open(f_path, "wb") as f_out:
                        f_out.write(f.getbuffer())
                    fotos_salvas.append(f_path)
            
            nova_visita = {
                "id": datetime.now().strftime('%Y%m%d%H%M%S'),
                "data": str(data_visita),
                "promotora": promotora_nome,
                "codigo": cliente_info["codigo"],
                "cliente": cliente_info["nome"],
                "cidade": cliente_info["cidade"],
                "endereco": cliente_info["endereco"],
                "ramo": cliente_info["ramo"],
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
        df = pd.DataFrame(dados)
        st.dataframe(df[["data", "promotora", "codigo", "cliente", "cidade", "relato"]])
        
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
