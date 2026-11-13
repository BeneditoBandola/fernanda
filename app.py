import base64
from datetime import datetime
import json
import os
import tempfile
import pandas as pd
import pytz
import requests
import speech_recognition as sr
import streamlit as st

pydeck_imported = True
try:
  import pydeck as pdk
except ImportError:
  pydeck_imported = False

# Page config
st.set_page_config(
    page_title="App de Visitas - Promotora", page_icon="📍", layout="wide"
)

# --- CONFIGURAÇÃO AUTOMÁTICA DO GITHUB VIA SECRETS ---
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
# O script detecta automaticamente o repositório pelas secrets ou usa valores padrão
REPO_OWNER = st.secrets.get("REPO_OWNER", "seu_usuario_github")
REPO_NAME = st.secrets.get("REPO_NAME", "nome_do_repositorio")
FILE_PATH = "visitas_dados.json"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

EXCEL_FILE = "clientes com coordenadas.xlsx"
FUSO_SP = pytz.timezone("America/Sao_Paulo")

CLIENTE_CODES_ROTA = [
    "23485",
    "28572",
    "21115",
    "21816",
    "21609",
    "21161",
    "21648",
    "23128",
    "24334",
    "23804",
    "21918",
    "23754",
    "26377",
    "21933",
    "21121",
    "21927",
    "21522",
    "21917",
    "24724",
    "24270",
    "27010",
    "21921",
    "21874",
]


# --- FUNÇÕES DE SINCRONIZAÇÃO COM GITHUB ---
def carregar_dados():
  """Lê o JSON direto do GitHub se houver token configurado"""
  if GITHUB_TOKEN:
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    try:
      response = requests.get(url, headers=HEADERS)
      if response.status_code == 200:
        file_content = response.json()
        decoded_content = base64.b64decode(file_content["content"]).decode(
            "utf-8"
        )
        return json.loads(decoded_content)
    except Exception:
      pass

  # Fallback para arquivo local
  if os.path.exists(FILE_PATH):
    try:
      with open(FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      return []
  return []


def salvar_dados(dados):
  """Salva localmente e envia automaticamente um commit para o GitHub"""
  with open(FILE_PATH, "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=4)

  if GITHUB_TOKEN:
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    try:
      resp_get = requests.get(url, headers=HEADERS)
      sha = resp_get.json().get("sha") if resp_get.status_code == 200 else None

      json_str = json.dumps(dados, ensure_ascii=False, indent=4)
      content_base64 = base64.b64encode(json_str.encode("utf-8")).decode(
          "utf-8"
      )

      payload = {
          "message": "Atualização automática de visitas via App",
          "content": content_base64,
      }
      if sha:
        payload["sha"] = sha

      requests.put(url, headers=HEADERS, json=payload)
    except Exception:
      pass


# Load clients from Excel file
@st.cache_data
def carregar_clientes():
  if os.path.exists(EXCEL_FILE):
    try:
      df_excel = pd.read_excel(EXCEL_FILE, engine="openpyxl")
      df_excel["CODIGO"] = (
          pd.to_numeric(df_excel["CODIGO"], errors="coerce")
          .fillna(0)
          .astype(int)
          .astype(str)
      )
      df_filtrado = df_excel[
          df_excel["CODIGO"].isin(CLIENTE_CODES_ROTA)
      ].copy()

      for col in ["LATITUDE", "LONGITUDE"]:
        if col in df_filtrado.columns:
          if df_filtrado[col].dtype == object:
            df_filtrado[col] = (
                df_filtrado[col]
                .astype(str)
                .str.replace(",", ".", regex=False)
            )
          df_filtrado[col] = pd.to_numeric(df_filtrado[col], errors="coerce")

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
          "21874": ("Compra Royal", ""),
      }

      df_filtrado["OBS"] = df_filtrado["CODIGO"].map(
          lambda x: obs_dict.get(x, ("", ""))[0]
      )
      df_filtrado["OBS_2"] = df_filtrado["CODIGO"].map(
          lambda x: obs_dict.get(x, ("", ""))[1]
      )

      return df_filtrado
    except Exception as e:
      st.error(f"Erro ao ler a planilha: {e}")
      return pd.DataFrame()
  return pd.DataFrame()


df_clientes = carregar_clientes()

st.title("App de Roteiro e Visitas - Promotora")
st.markdown(
    "Consulte a relação dos clientes da rota, filtre por cidade, registre"
    " atendimentos em campo com fotos e relatos, e gere relatórios em PDF para"
    " a diretoria."
)

st.sidebar.header("Navegação")
menu_opcoes = [
    "Nova Visita / Check-in",
    "Relação de Clientes & Endereços",
    "Histórico de Visitas & PDF",
]
menu = st.sidebar.selectbox("Escolha a opção", menu_opcoes, index=0)

if menu == "Relação de Clientes & Endereços":
  st.subheader("📋 Relação de Clientes e Endereços da Rota")

  if df_clientes.empty:
    st.warning(
        f"O arquivo '{EXCEL_FILE}' não foi encontrado ou nenhum cliente da"
        " rota foi encontrado na planilha."
    )
  else:
    cidades_disponiveis = ["Todas"] + sorted(
        df_clientes["CIDADE"].dropna().unique().tolist()
    )
    cidade_escolhida = st.selectbox("🏙️ Filtrar por Cidade", cidades_disponiveis)

    df_exibicao = df_clientes.copy()
    if cidade_escolhida != "Todas":
      df_exibicao = df_exibicao[df_exibicao["CIDADE"] == cidade_escolhida]

    busca = st.text_input("🔍 Pesquisar por Nome, Código ou Bairro", "")
    if busca:
      mask = (
          df_exibicao.astype(str)
          .apply(lambda x: x.str.contains(busca, case=False, na=False))
          .any(axis=1)
      )
      df_exibicao = df_exibicao[df_exibicao.index.isin(df_exibicao[mask].index)]

    st.info(f"Mostrando {len(df_exibicao)} cliente(s).")

    colunas_exibir = [
        c
        for c in [
            "CODIGO",
            "NOME",
            "ENDEREÇO",
            "BAIRRO",
            "CIDADE",
            "UF",
            "OBS",
            "OBS_2",
            "LATITUDE",
            "LONGITUDE",
        ]
        if c in df_exibicao.columns
    ]
    st.dataframe(df_exibicao[colunas_exibir], use_container_width=True)

    if (
        "LATITUDE" in df_exibicao.columns
        and "LONGITUDE" in df_exibicao.columns
        and pydeck_imported
    ):
      df_mapa = df_exibicao.dropna(subset=["LATITUDE", "LONGITUDE"]).copy()
      if not df_mapa.empty:
        lat_centro = df_mapa["LATITUDE"].mean()
        lon_centro = df_mapa["LONGITUDE"].mean()
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_mapa,
            get_position="[LONGITUDE, LATITUDE]",
            get_color="[226, 0, 26, 200]",
            get_radius=300,
            pickable=True,
            auto_highlight=True,
        )
        view_state = pdk.ViewState(
            latitude=lat_centro, longitude=lon_centro, zoom=12, pitch=0
        )
        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={
                "html": (
                    "<b>Cliente:</b> {NOME}<br/><b>Endereço:</b>"
                    " {ENDEREÇO}<br/><b>Cidade:</b> {CIDADE}"
                ),
                "style": {
                    "background": "black",
                    "color": "white",
                    "font-family": "sans-serif",
                    "z-index": "10000",
                },
            },
        )
        st.pydeck_chart(r)

elif menu == "Nova Visita / Check-in":
  st.subheader("📝 Registrar Atendimento em PDV")

  if df_clientes.empty:
    st.warning("Nenhum cliente carregado da planilha do GitHub.")
  else:
    visitas_ja_feitas = carregar_dados()
    codigos_visitados = [str(v["codigo"]) for v in visitas_ja_feitas]

    df_pendentes = df_clientes[
        ~df_clientes["CODIGO"].isin(codigos_visitados)
    ].copy()

    if df_pendentes.empty:
      st.success(
          "🎉 Parabéns! Todas as lojas da rota já foram visitadas com sucesso!"
      )
    else:
      cidades_disponiveis = ["Todas"] + sorted(
          df_pendentes["CIDADE"].dropna().unique().tolist()
      )
      cidade_checkin = st.selectbox(
          "🏙️ Filtrar Cidade para Atendimento",
          cidades_disponiveis,
          key="cidade_chk",
      )

      df_chk = df_pendentes.copy()
      if cidade_checkin != "Todas":
        df_chk = df_chk[df_chk["CIDADE"] == cidade_checkin]

      if df_chk.empty:
        st.warning("Nenhuma loja pendente encontrada para esta cidade.")
      else:
        df_chk["OPCAO_STR"] = (
            df_chk["CODIGO"]
            + " - "
            + df_chk["NOME"].fillna("")
            + " ("
            + df_chk["CIDADE"].fillna("")
            + ")"
        )
        cliente_opcoes = df_chk["OPCAO_STR"].tolist()

        cliente_selecionado_str = st.selectbox(
            "Selecione o Cliente / Loja Pendente", cliente_opcoes
        )
        cliente_info = df_chk[
            df_chk["OPCAO_STR"] == cliente_selecionado_str
        ].iloc[0]

        st.markdown("---")
        st.markdown("### 📍 Informações do Cliente Selecionado")
        st.write(f"**Código:** {cliente_info.get('CODIGO', '')}")
        st.write(f"**Nome:** {cliente_info.get('NOME', '')}")
        st.write(
            f"**Endereço:** {cliente_info.get('ENDEREÇO', '')} - Bairro:"
            f" {cliente_info.get('BAIRRO', '')}"
        )
        st.write(
            f"**Cidade/UF:** {cliente_info.get('CIDADE', '')} -"
            f" {cliente_info.get('UF', '')}"
        )
        st.write(f"**Obs:** {cliente_info.get('OBS', '')}")
        if cliente_info.get("OBS_2"):
          st.write(f"**Obs 2:** {cliente_info.get('OBS_2', '')}")

        lat = cliente_info.get("LATITUDE")
        lon = cliente_info.get("LONGITUDE")
        if pd.notna(lat) and pd.notna(lon):
          maps_url = (
              f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
          )
          st.markdown(
              f"🗺️ **Abrir localização no Google Maps:** [Clique aqui para abrir"
              f" a rota]({maps_url})",
              unsafe_allow_html=True,
          )

        st.markdown("---")
        promotora_nome = st.text_input("Nome da Promotora", value="Fernanda")

        st.markdown("📅 **Data da Visita**")
        data_atual_sp = datetime.now(FUSO_SP).date()
        data_visita_input = st.text_input(
            "Digite a data (DD/MM/AAAA)",
            value=data_atual_sp.strftime("%d/%m/%Y"),
        )

        st.markdown("### 📸 Fotos do Ponto de Venda")
        fotos_upload = st.file_uploader(
            "Tirar ou carregar fotos da gôndola/exposição",
            type=["jpg", "jpeg", "png", "heic", "webp"],
            accept_multiple_files=True,
        )

        st.markdown("### 🎙️ Relato por Voz / Áudio (Transcrição)")
        if "texto_transcrito_voz" not in st.session_state:
          st.session_state["texto_transcrito_voz"] = ""
        if "audio_key_id" not in st.session_state:
          st.session_state["audio_key_id"] = 0
        if "ultimo_audio_bytes" not in st.session_state:
          st.session_state["ultimo_audio_bytes"] = None

        audio_gravado = st.audio_input(
            "🎙️ Grave o áudio falando as observações da loja:",
            key=f"audio_input_{st.session_state['audio_key_id']}",
        )

        if audio_gravado is not None:
          st.session_state["ultimo_audio_bytes"] = audio_gravado.getvalue()
          col_transc, col_apagar = st.columns([3, 1])
          with col_transc:
            if st.button("✨ Transcrever Áudio em Texto"):
              with st.spinner("Interpretando e transcrevendo áudio..."):
                try:
                  with tempfile.NamedTemporaryFile(
                      delete=False, suffix=".wav"
                  ) as f_audio:
                    f_audio.write(st.session_state["ultimo_audio_bytes"])
                    caminho_audio_temp = f_audio.name
                  r = sr.Recognizer()
                  with sr.AudioFile(caminho_audio_temp) as source:
                    audio_data = r.record(source)
                    texto_falado = r.recognize_google(
                        audio_data, language="pt-BR"
                    )
                    st.session_state["texto_transcrito_voz"] = texto_falado
                    st.success("✅ Áudio transcrito com sucesso!")
                except Exception as e:
                  st.error(f"Erro ao transcrever: {e}")
          with col_apagar:
            if st.button("🗑️ Apagar Tudo"):
              st.session_state["texto_transcrito_voz"] = ""
              st.session_state["ultimo_audio_bytes"] = None
              st.session_state["audio_key_id"] += 1
              st.rerun()

        relato_texto = st.text_area(
            "Relato do Atendimento (Transcrito ou Digitado)",
            value=st.session_state["texto_transcrito_voz"],
            height=200,
        )

        if st.button("💾 Enviar e Salvar Visita", type="primary"):
          if (
              not relato_texto
              and not fotos_upload
              and not st.session_state["ultimo_audio_bytes"]
          ):
            st.warning("Adicione pelo menos um relato, foto ou áudio.")
          else:
            fotos_salvas = []
            os.makedirs("fotos_visitas", exist_ok=True)
            if fotos_upload:
              from PIL import Image as PILImage, ImageOps

              for idx, f in enumerate(fotos_upload):
                try:
                  img = PILImage.open(f)
                  img = ImageOps.exif_transpose(img)
                  if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                  img.thumbnail((1200, 1200))
                  f_path = os.path.join(
                      "fotos_visitas",
                      f"{cliente_info['CODIGO']}_{datetime.now(FUSO_SP).strftime('%Y%m%d_%H%M%S')}_{idx}.jpg",
                  )
                  img.save(f_path, "JPEG", quality=85)
                  fotos_salvas.append(f_path)
                except Exception:
                  f_path = os.path.join(
                      "fotos_visitas",
                      f"{cliente_info['CODIGO']}_{datetime.now(FUSO_SP).strftime('%Y%m%d_%H%M%S')}_{idx}.jpg",
                  )
                  with open(f_path, "wb") as f_out:
                    f_out.write(f.getbuffer())
                  fotos_salvas.append(f_path)

            audio_salvo_path = None
            if st.session_state["ultimo_audio_bytes"]:
              os.makedirs("audios_visitas", exist_ok=True)
              audio_salvo_path = os.path.join(
                  "audios_visitas",
                  f"{cliente_info['CODIGO']}_{datetime.now(FUSO_SP).strftime('%Y%m%d_%H%M%S')}.wav",
              )
              with open(audio_salvo_path, "wb") as f_audio_out:
                f_audio_out.write(st.session_state["ultimo_audio_bytes"])

            hora_envio = datetime.now(FUSO_SP).strftime("%H:%M")
            nova_visita = {
                "id": datetime.now(FUSO_SP).strftime("%Y%m%d%H%M%S"),
                "data": data_visita_input,
                "hora": hora_envio,
                "promotora": promotora_nome,
                "codigo": str(cliente_info.get("CODIGO", "")),
                "cliente": str(cliente_info.get("NOME", "")),
                "cidade": str(cliente_info.get("CIDADE", "")),
                "endereco": str(cliente_info.get("ENDEREÇO", "")),
                "bairro": str(cliente_info.get("BAIRRO", "")),
                "obs": str(cliente_info.get("OBS", "")),
                "obs_2": str(cliente_info.get("OBS_2", "")),
                "relato": relato_texto,
                "fotos": fotos_salvas,
                "audio_path": audio_salvo_path,
            }

            dados_existentes = carregar_dados()
            dados_existentes.append(nova_visita)
            salvar_dados(dados_existentes)

            st.session_state["ultimo_audio_bytes"] = None
            st.session_state["texto_transcrito_voz"] = ""
            st.success(
                "Visita registrada com sucesso e sincronizada no GitHub! 🚀"
            )
            st.rerun()

elif menu == "Histórico de Visitas & PDF":
  st.subheader("📊 Histórico de Visitas Realizadas, Edição e Exclusão / PDF")
  dados = carregar_dados()

  if not dados:
    st.info("Nenhuma visita registrada até o momento.")
  else:
    st.markdown("### ✏️ Editar Relato de uma Visita")
    visita_opcoes_edicao = {
        f"[{v['data']} às {v.get('hora', '--:--')}] {v['codigo']} -"
        f" {v['cliente']} (ID: {v['id']})": v
        for v in dados
    }
    visita_sel_str = st.selectbox(
        "Selecione uma visita para editar o texto",
        ["Nenhuma"] + list(visita_opcoes_edicao.keys()),
        key="sel_edicao",
    )

    if visita_sel_str != "Nenhuma":
      v_obj = visita_opcoes_edicao[visita_sel_str]
      novo_relato = st.text_area(
          "Editar Relato:",
          value=v_obj["relato"],
          height=150,
          key=f"edit_relato_{v_obj['id']}",
      )
      if st.button("💾 Salvar Alterações do Relato", type="primary"):
        for item in dados:
          if item["id"] == v_obj["id"]:
            item["relato"] = novo_relato
            break
        salvar_dados(dados)
        st.success("Relato atualizado e sincronizado no GitHub! 🚀")
        st.rerun()

    st.markdown("---")
    st.markdown("### 🗑️ Gerenciar / Apagar Visitas Incorretas")
    visita_opcoes = {
        f"[{v['data']} às {v.get('hora', '--:--')}] {v['codigo']} -"
        f" {v['cliente']} (Promotora: {v['promotora']}) (ID: {v['id']})": v[
            "id"
        ]
        for v in dados
    }
    visita_para_apagar = st.selectbox(
        "Selecione uma visita para remover, se necessário",
        ["Nenhuma"] + list(visita_opcoes.keys()),
        key="sel_apagar",
    )

    if visita_para_apagar != "Nenhuma":
      if st.button(
          "🗑️ Apagar Visita Selecionada (Retorna loja para a rota)",
          type="secondary",
      ):
        id_alvo = visita_opcoes[visita_para_apagar]
        dados_atualizados = [v for v in dados if v["id"] != id_alvo]
        salvar_dados(dados_atualizados)
        st.success("Visita apagada e alteração salva no GitHub!")
        st.rerun()

    st.markdown("---")
    st.markdown("### 📋 Visitas Registradas")
    df_visitas = pd.DataFrame(dados)
    if "hora" not in df_visitas.columns:
      df_visitas["hora"] = "--:--"
    st.dataframe(
        df_visitas[
            ["data", "hora", "promotora", "codigo", "cliente", "cidade", "relato"]
        ],
        use_container_width=True,
    )

    st.markdown("---")
    st.markdown("### 📄 Gerar Relatório Executivo em PDF para a Diretoria")
    incluir_fotos = st.checkbox(
        "Incluir registros fotográficos no relatório PDF", value=True
    )

    fotos_selecionadas_dict = {}
    if incluir_fotos:
      for i, v in enumerate(dados):
        if v.get("fotos"):
          with st.expander(f"📷 Fotos da visita: {v['cliente']} ({v['data']})"):
            fotos_selecionadas_dict[v["id"]] = []
            for f_idx, foto_path in enumerate(v["fotos"]):
              if os.path.exists(foto_path):
                col_img, col_chk = st.columns([1, 2])
                with col_img:
                  st.image(foto_path, width=100)
                with col_chk:
                  manter = st.checkbox(
                      f"Incluir foto {f_idx+1}",
                      value=True,
                      key=f"chk_foto_{v['id']}_{f_idx}",
                  )
                  if manter:
                    fotos_selecionadas_dict[v["id"]].append(foto_path)

    if st.button("Gerar PDF Executivo", type="primary"):
      from reportlab.lib import colors
      from reportlab.lib.pagesizes import letter
      from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
      from reportlab.platypus import (
          Image as RLImage,
          Paragraph,
          SimpleDocTemplate,
          Spacer,
          Table,
          TableStyle,
      )

      pdf_filename = "relatorio_visitas_diretoria.pdf"
      doc = SimpleDocTemplate(
          pdf_filename,
          pagesize=letter,
          rightMargin=30,
          leftMargin=30,
          topMargin=30,
          bottomMargin=30,
      )
      story = []
      styles = getSampleStyleSheet()

      title_style = ParagraphStyle(
          "TitleStyle",
          parent=styles["Heading1"],
          fontSize=18,
          textColor=colors.HexColor("#1A365D"),
          spaceAfter=15,
      )
      subtitle_style = ParagraphStyle(
          "SubTitleStyle",
          parent=styles["Normal"],
          fontSize=10,
          textColor=colors.HexColor("#4A5568"),
          spaceAfter=20,
      )

      story.append(
          Paragraph("Relatório de Visitas e Execução em PDV", title_style)
      )
      story.append(
          Paragraph(
              f"Gerado em: {datetime.now(FUSO_SP).strftime('%d/%m/%Y às %H:%M')}",
              subtitle_style,
          )
      )
      story.append(Spacer(1, 10))

      for v in dados:
        story.append(
            Paragraph(
                f"<b>Cliente:</b> {v['codigo']} - {v['cliente']}"
                f" ({v['cidade']})",
                styles["Heading3"],
            )
        )
        story.append(
            Paragraph(
                f"<b>Endereço:</b> {v.get('endereco', '')} - Bairro:"
                f" {v.get('bairro', '')}",
                styles["Normal"],
            )
        )
        if v.get("obs"):
          story.append(
              Paragraph(f"<b>Obs:</b> {v.get('obs', '')}", styles["Normal"])
          )
        if v.get("obs_2"):
          story.append(
              Paragraph(f"<b>Obs 2:</b> {v.get('obs_2', '')}", styles["Normal"])
          )
        hora_str = f" às {v['hora']}" if v.get("hora") else ""
        story.append(
            Paragraph(
                f"<b>Data:</b> {v['data']}{hora_str} | <b>Promotora:</b>"
                f" {v['promotora']}",
                styles["Normal"],
            )
        )
        story.append(
            Paragraph(f"<b>Relato / Ações:</b> {v['relato']}", styles["Normal"])
        )
        story.append(Spacer(1, 5))

        if incluir_fotos and v.get("fotos"):
          fotos_para_usar = fotos_selecionadas_dict.get(v["id"], v["fotos"])
          if fotos_para_usar:
            story.append(
                Paragraph("<b>Registros Fotográficos:</b>", styles["Normal"])
            )
            img_elements = []
            for foto_path in fotos_para_usar:
              if os.path.exists(foto_path):
                try:
                  img = RLImage(foto_path, width=120, height=160)
                  img_elements.append(img)
                except Exception:
                  pass
            if img_elements:
              t = Table(
                  [img_elements], colWidths=[130] * len(img_elements)
              )
              t.setStyle(
                  TableStyle([
                      ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                      ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                  ])
              )
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
            type="primary",
        )
      st.success("PDF gerado com sucesso!")
