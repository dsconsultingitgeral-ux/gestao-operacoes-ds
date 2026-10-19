from datetime import datetime, date
import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. CONFIGURAÇÃO DA PÁGINA (ESTILO CLEAN / APPLE) ---
st.set_page_config(
    page_title="Gestão e Operações | Digital Solutions",
    page_icon="⚙️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilização CSS minimalista e moderna
st.markdown("""
    <style>
    .main {
        background-color: #fafafa;
    }
    h1, h2, h3 {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        color: #1d1d1f;
    }
    .stButton>button {
        background-color: #000000;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #333333;
        color: white;
    }
    .card-box {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        margin-bottom: 20px;
        border: 1px solid #e5e5ea;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. LIGAÇÃO AO SUPABASE VIA SECRETS ---
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_supabase()

# --- 3. LOGÓTIPO ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        st.image("logo.jpg", use_column_width=True)
    except Exception:
        pass

st.markdown("<p style='text-align: center; color: #86868b; margin-top: 5px; margin-bottom: 25px;'>Portal de Gestão & Operações Internas</p>", unsafe_allow_html=True)

# --- 4. GESTÃO DE SESSÃO E LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.nome = None
    st.session_state.is_admin = False

if not st.session_state.logged_in:
    st.markdown("### Iniciar Sessão")
    with st.form("login_form"):
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        submit_login = st.form_submit_button("Entrar")
        
        if submit_login:
            try:
                response = supabase.table("utilizadores").select("*").eq("username", username_input).execute()
                users = response.data
                
                if users and users[0]["password"] == password_input:
                    user = users[0]
                    if user.get("plataforma") in ["gestao", "ambas"]:
                        st.session_state.logged_in = True
                        st.session_state.username = user["username"]
                        st.session_state.nome = user["nome"]
                        st.session_state.is_admin = "admin" in user["username"].lower()
                        st.rerun()
                    else:
                        st.error("Este utilizador não tem permissão para aceder à plataforma de Gestão.")
                else:
                    st.error("Username ou password incorretos.")
            except Exception as e:
                st.error(f"Erro no login: {e}")

else:
    c_user, c_logout = st.columns([3, 1])
    with c_user:
        st.markdown(f"👋 **Bem-vindo(a), {st.session_state.nome}**")
    with c_logout:
        if st.button("Sair", key="btn_logout_main"):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown("---")

    tabs = st.tabs(["🕒 Picagem de Ponto", "📁 Projetos & Horas", "🏖️ Férias e Ausências", "👑 Painel Admin"] if st.session_state.is_admin else ["🕒 Picagem de Ponto", "📁 Projetos & Horas", "🏖️ Férias e Ausências"])

    hoje_iso = date.today().isoformat()

    # --- TAB 1: PICAGEM DE PONTO (ESTRUTURA ORIGINAL: TIPO + DATA_HORA) ---
    with tabs[0]:
        st.markdown("### Picagem de Ponto Diária")
        st.write(f"**Data:** {date.today().strftime('%d/%m/%Y')}")

        # Registar nova picagem
        def registar_ponto(tipo_evento):
            try:
                agora_iso = datetime.now().isoformat()
                supabase.table("picagens").insert({
                    "username": st.session_state.username,
                    "tipo": tipo_evento,
                    "data_hora": agora_iso
                }).execute()
                st.success(f"Registo de {tipo_evento.replace('_', ' ')} efetuado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao registar picagem: {e}")

        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        
        with col_p1:
            if st.button("Entrada 🟢"):
                registar_ponto("entrada")

        with col_p2:
            if st.button("Saída Almoço 🥪"):
                registar_ponto("saida_almoco")

        with col_p3:
            if st.button("Entrada Almoço ☕"):
                registar_ponto("entrada_almoco")

        with col_p4:
            if st.button("Saída 🏁"):
                registar_ponto("saida")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Os Seus Registos do Dia")
        
        try:
            # Buscar registos do utilizador atual para o dia de hoje
            res_hoje = supabase.table("picagens").select("*").eq("username", st.session_state.username).gte("data_hora", f"{hoje_iso}T00:00:00").order("data_hora", desc=True).execute()
            if res_hoje.data:
                for reg in res_hoje.data:
                    tipo_reg = reg.get("tipo", "").replace("_", " ").title()
                    dh_raw = reg.get("data_hora", "")
                    try:
                        hora_f = datetime.fromisoformat(dh_raw.replace("Z", "+00:00")).strftime("%H:%M:%S")
                    except Exception:
                        hora_f = dh_raw

                    st.markdown(f"""
                        <div class="card-box" style="padding:10px 15px; margin-bottom:8px;">
                            <b>{tipo_reg}</b> — <span style="color:#555;">{hora_f}</span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Ainda não efetuou nenhuma picagem de ponto hoje.")
        except Exception as e:
            st.error(f"Erro ao carregar picagens do dia: {e}")

    # --- TAB 2: PROJETOS E HORAS ---
    with tabs[1]:
        st.markdown("### Registo de Horas em Projetos")
        try:
            res_proj = supabase.table("projetos").select("*").eq("estado", "Ativo").execute()
            projetos = res_proj.data
        except Exception:
            projetos = []

        if not projetos:
            st.info("Não existem projetos ativos disponíveis de momento.")
        else:
            options_proj = {p["nome_projeto"]: p["id"] for p in projetos}
            
            with st.form("form_horas"):
                proj_nome = st.selectbox("Selecione o Projeto", list(options_proj.keys()))
                horas = st.number_input("Horas Dedicadas", min_value=0.5, max_value=24.0, step=0.5)
                descricao = st.text_area("Descrição do Trabalho Efetuado")
                
                if st.form_submit_button("Registar Horas"):
                    if not descricao:
                        st.warning("Descreva o trabalho efetuado.")
                    else:
                        data_h = {
                            "projeto_id": options_proj[proj_nome],
                            "username": st.session_state.username,
                            "data": hoje_iso,
                            "horas_dedicadas": horas,
                            "descricao": descricao
                        }
                        supabase.table("projetos_horas").insert(data_h).execute()
                        st.success("Horas registadas com sucesso!")
                        st.rerun()

        st.markdown("---")
        st.markdown("### Os Seus Registos Recentes")
        try:
            res_meus_reg = supabase.table("projetos_horas").select("*, projetos(nome_projeto)").eq("username", st.session_state.username).order("data", desc=True).limit(10).execute()
            if res_meus_reg.data:
                df_h = pd.DataFrame(res_meus_reg.data)
                cols_to_show = [c for c in ["data", "horas_dedicadas", "descricao"] if c in df_h.columns]
                st.dataframe(df_h[cols_to_show], use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao carregar registos recentes: {e}")

    # --- TAB 3: FÉRIAS E AUSÊNCIAS ---
    with tabs[2]:
        st.markdown("### Marcar Férias ou Ausência")
        
        with st.form("form_ferias"):
            tipo_ausencia = st.selectbox("Tipo de Ausência", ["Férias", "Doença", "Formação", "Outros"])
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                dt_ini = st.date_input("Data de Início", min_value=date.today())
            with c_d2:
                dt_fim = st.date_input("Data de Fim", min_value=date.today())
            
            obs = st.text_input("Observações (Opcional)")
            
            if st.form_submit_button("Submeter Pedido"):
                if dt_fim < dt_ini:
                    st.error("A data de fim não pode ser anterior à data de início.")
                else:
                    dias = (dt_fim - dt_ini).days + 1
                    data_f = {
                        "username": st.session_state.username,
                        "tipo": tipo_ausencia,
                        "data_inicio": dt_ini.isoformat(),
                        "data_fim": dt_fim.isoformat(),
                        "dias_uteis": dias,
                        "estado": "Pendente",
                        "observacoes": obs
                    }
                    supabase.table("ferias").insert(data_f).execute()
                    st.success("Pedido de ausência submetido com sucesso para aprovação!")
                    st.rerun()

        st.markdown("---")
        st.markdown("### Histórico de Pedidos de Férias")
        try:
            res_minhas_ferias = supabase.table("ferias").select("*").eq("username", st.session_state.username).order("created_at", desc=True).execute()
            if res_minhas_ferias.data:
                for f in res_minhas_ferias.data:
                    f_tipo = f.get('tipo', '')
                    f_ini = f.get('data_inicio', '')
                    f_fim = f.get('data_fim', '')
                    f_dias = f.get('dias_uteis', '')
                    f_est = f.get('estado', 'Pendente')
                    f_obs = f.
