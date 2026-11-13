import base64
import json
import pandas as pd
import requests
import streamlit as st

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(
    page_title="Controle de Visitas - Minassal", page_icon="📍", layout="wide"
)

# --- CONFIGURAÇÕES DO GITHUB ---
# Recomendado: Defina GITHUB_TOKEN nos Secrets do Streamlit Cloud (App settings > Secrets)
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "SEU_TOKEN_GITHUB_AQUI")
REPO_OWNER = "seu_usuario_github"  # Substitua pelo seu usuário ou organização
REPO_NAME = "nome_do_repositorio"  # Substitua pelo nome do seu repositório
FILE_PATH = "dados_visitas_minassal.json"  # Nome do arquivo JSON no GitHub

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

# --- BASE INICIAL DE CLIENTES E VISITAS (Caso o JSON ainda não exista no GitHub) ---
DADOS_INICIAIS = [
    {
        "id": 24823128,
        "cliente": "AGRO & PET DOS CAIPIRAS LTDA",
        "cidade": "JUIZ DE FORA",
        "bairro": "BARREIRA DO TRIUNFO",
        "endereco": "AV PRESIDENTE JUSCELINO KUBITSCHECK, 10292 - CASA 01",
        "status_royal": "Não compra Royal, mas tem bastante Mars",
        "visitado": True,
        "data_visita": "12/11/2026 09:25",
        "promotora": "Fernanda",
        "relato": (
            "Loja esta com produtos em dia, arrumei as gôndolas, precifiquei e"
            " realizei a limpeza."
        ),
    },
    {
        "id": 45023485,
        "cliente": "AGROFARMA LTDA",
        "cidade": "GOIANA",
        "bairro": "CENTRO",
        "endereco": "AV 21 DE DEZEMBRO, 875 - LOJA 02",
        "status_royal": "Não compra Royal",
        "visitado": True,
        "data_visita": "12/11/2026 12:45",
        "promotora": "Fernanda",
        "relato": "Loja inexistente estou no endereço, mas ao que tudo indica, ela fechou",
    },
    {
        "id": 64321933,
        "cliente": "AGROPECUARIA GRAMA DOIS IRMAOS LTDA",
        "cidade": "JUIZ DE FORA",
        "bairro": "PARQUE GUARANI",
        "endereco": "AVENIDA JUIZ DE FORA, 1028 - LOJA 01",
        "status_royal": "Só recebeu bonificação, nunca comprou",
        "visitado": False,
        "data_visita": "",
        "promotora": "",
        "relato": "",
    },
    {
        "id": 72821121,
        "cliente": "AGROPECUARIA SAO JORGE LTDA",
        "cidade": "JUIZ DE FORA",
        "bairro": "GRAMA",
        "endereco": "AV JUIZ DE FORA, 3809 - 3813",
        "status_royal": "Não compra Royal",
        "visitado": False,
        "data_visita": "",
        "promotora": "",
        "relato": "",
    },
    {
        "id": 178121874,
        "cliente": "BARBARA FELIPPE COMERCIAL LTDA",
        "cidade": "JUIZ DE FORA",
        "bairro": "CENTRO",
        "endereco": "AV BARAO DO RIO BRANCO, 1960",
        "status_royal": "Compra Royal",
        "visitado": False,
        "data_visita": "",
        "promotora": "",
        "relato": "",
    },
    {
        "id": 202526377,
        "cliente": "BRUNO JOSE DA SILVA",
        "cidade": "JUIZ DE FORA",
        "bairro": "GRANJA GUARUJA",
        "endereco": "AVENIDA JUIZ DE FORA, 4500 - LOTE GRANJAS GUARUJA",
        "status_royal": "Pendente",
        "visitado": False,
        "data_visita": "",
        "promotora": "",
        "relato": "",
    },
    {
        "id": 242721648,
        "cliente": "CASA DO BOIADEIRO LTDA",
        "cidade": "JUIZ DE FORA",
        "bairro": "BARREIRA DO TRIUNFO",
        "endereco": (
            "AVENIDA PRESIDENTE JUSCELINO KUBITSCHECK - DE 9000/9001 AO, 10334 -"
            " GALPAO 01"
        ),
        "status_royal": "Não compra Royal",
        "visitado": True,
        "data_visita": "12/11/2026 09:17",
        "promotora": "Fernanda",
        "relato": (
            "Loja nao está trabalhando com os produtos das nossas marcas no"
            " momento, e não tem interesse em comprar pois nao tem procura dos"
            " mesmos."
        ),
    },
    {
        "id": 253221609,
        "cliente": "CAYO H G PINTO LTDA",
        "cidade": "CORONEL PACHECO",
        "bairro": "CENTRO",
        "endereco": "R SAO VICENTE DE PAULO, 120",
        "status_royal": "Não compra Royal",
        "visitado": True,
        "data_visita": "12/11/2026 13:09",
        "promotora": "Fernanda",
        "relato": (
            "Loja com pouca mercadoria mas está com atendimento do vendedor"
            " pelo WhatsApp, organizei limpei fiz a precificação da forma que a"
            " loja pediu"
        ),
    },
    {
        "id": 265221921,
        "cliente": "CINTHIA COELHO PET SHOP PRODUTOS PARA ANIMAIS LTDA",
        "cidade": "JUIZ DE FORA",
        "bairro": "MANOEL HONORIO",
        "endereco": "AV BARAO DO RIO BRANCO, 490",
        "status_royal": "Compra Royal",
        "visitado": False,
        "data_visita": "",
        "promotora": "",
        "relato": "",
    },
    {
        "id": 328027010,
        "cliente": "DANIELA FERREIRA MAGDALENO",
        "cidade": "JUIZ DE FORA",
        "bairro": "SANTA TEREZINHA",
        "endereco": "RUA AMERICO LOBO, 1177",
        "status_royal": "Compra Royal",
        "visitado": False,
        "data_visita": "",
        "promotora": "",
        "relato": "",
    },
    {
        "id": 344921522,
        "cliente": "DHIEGO MARTINS DE MEDEIROS",
        "cidade": "JUIZ DE FORA",
        "bairro": "BAIRU",
        "endereco": "RUA AMERICO LOBO, 2471 - LOJA",
        "status_royal": "Não compra Royal, mas tem bastante Mars",
        "visitado": False,
        "data_visita": "",
        "promotora": "",
        "relato": "",
    },
    {
        "id": 486821917,
        "cliente": "GOMES MONTEIRO AGROPECUARIA LTDA",
        "cidade": "JUIZ DE FORA",
        "bairro": "BAIRU",
        "endereco": "RUA AMERICO LOBO, 2452 - LOJA",
        "status_royal": "Não compra Royal, mas tem bastante Mars",
        "visitado": False,
        "data_visita": "",
        "promotora": "",
        "relato": "",
    },
    {
        "id": 610924334,
        "cliente": "KALINA DA SILVA CUNHA",
        "cidade": "JUIZ DE FORA",
        "bairro": "GRAMA",
        "endereco": "AVENIDA JUIZ DE FORA, 4500",
        "status_royal": "Não compra Royal",
        "visitado": True,
        "data_visita": "12/11/2026 15:10",
        "promotora": "Fernanda",
        "relato": (
            "Loja foi organizada e realizei limpeza das gôndolas, loja bem"
            " abastecida"
        ),
    },
    {
        "id": 778723804,
        "cliente": "MD AGROPECUARIA LTDA",
        "cidade": "JUIZ DE FORA",
        "bairro": "GRAMA",
        "endereco": "AV JUIZ DE FORA, 2064 - LOJA MAIOR",
        "status_royal": "Não compra Royal",
        "visitado": True,
        "data_visita": "12/11/2026 14:33",
        "promotora": "Fernanda",
        "relato": "Loja nao trabalha com produtos da mas, vemdedor nao faz atendimento.",
    },
    {
        "id": 848521161,
        "cliente": "NUTRI-FAUNA LTDA",
        "cidade": "CORONEL PACHECO",
        "bairro": "CENTRO",
        "endereco": "RODOVIA MG 353, 61 - LOJA",
        "status_royal": "Não compra Royal",
        "visitado": True,
        "data_visita": "12/11/2026 13:17",
        "promotora": "Fernanda",
        "relato": "Lojas sem mercadoria nenhuma e sem atendimento",
    },
    {
        "id": 930321115,
        "cliente": "R E R MOURA AGROPECUARIA LTDA",
        "cidade": "GOIANA",
        "bairro": "SAO SEBASTIAO",
        "endereco": "AV 21 DE DEZEMBRO, 1235",
        "status_royal": "Não compra Royal",
        "visitado": True,
        "data_visita": "12/11/2026 12:25",
        "promotora": "Fernanda",
        "relato": (
            "não tava sendo atendida o vendedor e então tem pouquíssima coisa"
            " tinha cinco opção de sachê só que foi comprado até por outro"
            " distribuidor..."
        ),
    },
    {
        "id": 983421918,
        "cliente": "ROGNEI EGIDIO GOMES",
        "cidade": "JUIZ DE FORA",
        "bairro": "GRAMA",
        "endereco": "AVENIDA JUIZ DE FORA, 1148 - LOJA 1",
        "status_royal": "Não compra Royal",
        "visitado": True,
        "data_visita": "12/11/2026 14:42",
        "promotora": "Fernanda",
        "relato": (
            "Loja tem sache apenas, porém compraram da Martins que está com"
            " melhor preco."
        ),
    },
    {
        "id": 1054124270,
        "cliente": "SUPERMERCADO DO CAO LTDA",
        "cidade": "JUIZ DE FORA",
        "bairro": "BAIRU/PROGRESSO",
        "endereco": "RUA AMERICO LOBO, 1376",
        "status_royal": "Compra Royal",
        "visitado": True,
        "data_visita": "12/11/2026 15:41",
        "promotora": "Fernanda",
        "relato": "Loja e uma clínica veterinária, só compra pra uso próprio.",
    },
    {
        "id": 1077021927,
        "cliente": "TERRA BOA AGROPECUARIA LTDA",
        "cidade": "JUIZ DE FORA",
        "bairro": "PARQUE GUARANI",
        "endereco": "AVENIDA JUIZ DE FORA, 10",
        "status_royal": "Não compra Royal",
        "visitado": True,
        "data_visita": "12/11/2026 15:13",
        "promotora": "Fernanda",
        "relato": "Loja nao trabalha com nenhum produto nosso.",
    },
    {
        "id": 1078824724,
        "cliente": "THAINA DA SILVA NASCIMENTO",
        "cidade": "JUIZ DE FORA",
        "bairro": "PROGRESSO",
        "endereco": "RUA AMERICO LOBO, 2313",
        "status_royal": "Não compra Royal",
        "visitado": False,
        "data_visita": "",
        "promotora": "",
        "relato": "",
    },
    {
        "id": 1091921816,
        "cliente": "TREVO MERCANTIL AGROPECUARIA LTDA",
        "cidade": "GOIANA",
        "bairro": "SAO SEBASTIAO",
        "endereco": "AV 21 DE DEZEMBRO, 1075 - LOJA 01",
        "status_royal": "Não compra Royal, mas tem bastante Mars",
        "visitado": True,
        "data_visita": "12/11/2026 12:34",
        "promotora": "Fernanda",
        "relato": (
            "Loja trabalha com sacaria no granel... Organizei e limpei, porém"
            " mercadoria da concorrência..."
        ),
    },
    {
        "id": 1141423754,
        "cliente": "WALTER D FREGUGLIA",
        "cidade": "JUIZ DE FORA",
        "bairro": "GRAMA",
        "endereco": "AV JUIZ DE FORA, 3659",
        "status_royal": "Não compra Royal",
        "visitado": True,
        "data_visita": "12/11/2026 14:55",
        "promotora": "Fernanda",
        "relato": "Loja organizada e material de mershan positivado.",
    },
    {
        "id": 1184328572,
        "cliente": "MUNDO ANIMAL GOIANA LTDA",
        "cidade": "GOIANA",
        "bairro": "SAO SEBASTIAO",
        "endereco": "AV 21 DE DEZEMBRO, 1225",
        "status_royal": "Não compra Royal",
        "visitado": True,
        "data_visita": "12/11/2026 12:15",
        "promotora": "Fernanda",
        "relato": (
            "loja da bem atendida abastecido trabalho com pouco produto"
            " realizei abastecimento limpeza..."
        ),
    },
]


# --- FUNÇÕES DE INTEGRAÇÃO COM GITHUB ---
def carregar_dados_github():
  url = (
      f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
  )
  try:
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
      file_content = response.json()
      decoded_content = base64.b64decode(file_content["content"]).decode(
          "utf-8"
      )
      return json.loads(decoded_content), file_content["sha"]
    elif response.status_code == 404:
      return DADOS_INICIAIS, None
    else:
      st.error(f"Erro ao carregar do GitHub: {response.status_code}")
      return DADOS_INICIAIS, None
  except Exception as e:
    st.warning(f"Erro de conexão com GitHub: {e}. Usando dados padrão.")
    return DADOS_INICIAIS, None


def salvar_dados_github(dados, sha):
  url = (
      f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
  )
  json_str = json.dumps(dados, ensure_ascii=False, indent=4)
  content_base64 = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

  payload = {
      "message": "Atualização automática de visitas via Streamlit",
      "content": content_base64,
  }
  if sha:
    payload["sha"] = sha

  response = requests.put(url, headers=HEADERS, json=payload)
  if response.status_code in [200, 201]:
    st.success("💾 Dados salvos e sincronizados no GitHub com sucesso!")
    return response.json()["content"]["sha"]
  else:
    st.error(f"Erro ao salvar no GitHub: {response.json().get('message')}")
    return sha


# --- CARREGAMENTO DOS DADOS ---
if "dados_clientes" not in st.session_state:
  dados, sha = carregar_dados_github()
  st.session_state["dados_clientes"] = dados
  st.session_state["file_sha"] = sha

# --- INTERFACE DO APLICATIVO ---
st.title("📍 Controle de Visitas e Trade Marketing - Minassal")
st.markdown(
    "Gerenciamento de roteiros, status de lojas e salvamento automático em"
    " nuvem (GitHub)."
)

# Métricas rápidas
df_clientes = pd.DataFrame(st.session_state["dados_clientes"])
total_clientes = len(df_clientes)
total_visitados = (
    df_clientes["visitado"].sum() if "visitado" in df_clientes.columns else 0
)
total_faltantes = total_clientes - total_visitados

col1, col2, col3 = st.columns(3)
col1.metric("Total de Clientes", total_clientes)
col2.metric("Já Visitados", total_visitados)
col3.metric("Faltam Visitar", total_faltantes)

st.divider()

# Abas de navegação
aba1, aba2 = st.tabs(["📋 Lista de Clientes & Status", "✏️ Atualizar / Registrar Visita"])

with aba1:
  st.subheader("Filtros e Visualização Geral")
  filtro_status = st.selectbox(
      "Filtrar por Status de Visita", ["Todos", "Visitados", "Falta Visitar"]
  )

  df_view = df_clientes.copy()
  if filtro_status == "Visitados":
    df_view = df_view[df_view["visitado"] == True]
  elif filtro_status == "Falta Visitar":
    df_view = df_view[df_view["visitado"] == False]

  st.dataframe(
      df_view[
          [
              "id",
              "cliente",
              "cidade",
              "bairro",
              "status_royal",
              "visitado",
              "data_visita",
              "promotora",
          ]
      ],
      use_container_width=True,
  )

  # Botão de exportação rápida para CSV/Excel local caso queira backup
  csv = df_clientes.to_csv(index=False).encode("utf-8")
  st.download_button(
      label="📥 Baixar Backup em CSV",
      data=csv,
      file_name="backup_visitas_minassal.csv",
      mime="text/csv",
  )

with aba2:
  st.subheader("Atualizar Dados de um Cliente")

  # Selecionar cliente pelo nome
  nomes_clientes = df_clientes["cliente"].tolist()
  cliente_selecionado = st.selectbox(
      "Selecione o Cliente para Editar", nomes_clientes
  )

  # Encontrar dados atuais do cliente selecionado
  idx = df_clientes[df_clientes["cliente"] == cliente_selecionado].index[0]
  cliente_atual = df_clientes.loc[idx]

  with st.form("form_atualizacao"):
    col_a, col_b = st.columns(2)
    with col_a:
      novo_visitado = st.checkbox(
          "Cliente Visitado?", value=bool(cliente_atual["visitado"])
      )
      nova_data = st.text_input(
          "Data/Hora da Visita",
          value=str(cliente_atual.get("data_visita", "")),
      )
    with col_b:
      nova_promotora = st.text_input(
          "Promotora / Responsável",
          value=str(cliente_atual.get("promotora", "")),
      )
      novo_status_royal = st.text_input(
          "Status Royal / Observação Curta",
          value=str(cliente_atual.get("status_royal", "")),
      )

    novo_relato = st.text_area(
        "Relato / Ações Realizadas no PDV",
        value=str(cliente_atual.get("relato", "")),
    )

    salvar_btn = st.form_submit_button("💾 Salvar Alterações e Enviar para o GitHub")

    if salvar_btn:
      # Atualiza no session state
      st.session_state["dados_clientes"][idx]["visitado"] = novo_visitado
      st.session_state["dados_clientes"][idx]["data_visita"] = nova_data
      st.session_state["dados_clientes"][idx]["promotora"] = nova_promotora
      st.session_state["dados_clientes"][idx]["status_royal"] = (
          novo_status_royal
      )
      st.session_state["dados_clientes"][idx]["relato"] = novo_relato

      # Salva de forma permanente no GitHub
      new_sha = salvar_dados_github(
          st.session_state["dados_clientes"], st.session_state["file_sha"]
      )
      st.session_state["file_sha"] = new_sha
      st.rerun()
