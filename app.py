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

    hoje_str = date.today().isoformat()

    # --- TAB 1: PICAGEM DE PONTO ---
    with tabs[0]:
        st.markdown("### Picagem de Ponto Diária")
        st.write(f"**Data:** {date.today().strftime('%d/%m/%Y')}")

        try:
            res_ponto = supabase.table("picagens").select("*").eq("username", st.session_state.username).eq("data", hoje_str).execute()
            registo = res_ponto.data[0] if res_ponto.data else None
        except Exception:
            registo = None

        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        
        with col_p1:
            if st.button("Entrada 🟢", disabled=bool(registo and registo.get("hora_entrada"))):
                now_time = datetime.now().strftime("%H:%M:%S")
                if not registo:
                    supabase.table("picagens").insert({"username": st.session_state.username, "data": hoje_str, "hora_entrada": now_time}).execute()
                else:
                    supabase.table("picagens").update({"hora_entrada": now_time}).eq("id", registo["id"]).execute()
                st.rerun()

        with col_p2:
            if st.button("Saída Almoço 🥪", disabled=not (registo and registo.get("hora_entrada")) or bool(registo and registo.get("hora_saida_almoco"))):
                now_time = datetime.now().strftime("%H:%M:%S")
                supabase.table("picagens").update({"hora_saida_almoco": now_time}).eq("id", registo["id"]).execute()
                st.rerun()

        with col_p3:
            if st.button("Entrada Almoço ☕", disabled=not (registo and registo.get("hora_saida_almoco")) or bool(registo and registo.get("hora_entrada_almoco"))):
                now_time = datetime.now().strftime("%H:%M:%S")
                supabase.table("picagens").update({"hora_entrada_almoco": now_time}).eq("id", registo["id"]).execute()
                st.rerun()

        with col_p4:
            if st.button("Saída 🏁", disabled=not (registo and registo.get("hora_entrada")) or bool(registo and registo.get("hora_saida"))):
                now_time = datetime.now().strftime("%H:%M:%S")
                supabase.table("picagens").update({"hora_saida": now_time}).eq("id", registo["id"]).execute()
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if registo:
            h_ent = registo.get('hora_entrada') or '--:--'
            h_s_alm = registo.get('hora_saida_almoco') or '--:--'
            h_e_alm = registo.get('hora_entrada_almoco') or '--:--'
            h_sai = registo.get('hora_saida') or '--:--'

            st.markdown(f"""
                <div class="card-box">
                    <b>Entrada:</b> {h_ent} | 
                    <b>Saída Almoço:</b> {h_s_alm} | 
                    <b>Entrada Almoço:</b> {h_e_alm} | 
                    <b>Saída:</b> {h_sai}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Ainda não registou entrada hoje.")

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
                            "data": hoje_str,
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
                    f_obs = f.get('observacoes', '') or ''
                    cor_est = "🟡" if f_est == "Pendente" else ("🟢" if f_est == "Aprovado" else "🔴")

                    st.markdown(f"""
                        <div class="card-box">
                            <b>Tipo:</b> {f_tipo} | <b>De:</b> {f_ini} <b>Até:</b> {f_fim} ({f_dias} dias)<br>
                            <b>Estado:</b> {cor_est} {f_est} <br>
                            <small><i>{f_obs}</i></small>
                        </div>
                    """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Erro ao carregar histórico de férias: {e}")

    # --- TAB 4: PAINEL ADMIN ---
    if st.session_state.is_admin:
        with tabs[3]:
            st.markdown("### Painel Geral de Administração")
            
            st.markdown("#### 1. Aprovação de Férias Pendentes")
            try:
                res_ferias_pend = supabase.table("ferias").select("*").eq("estado", "Pendente").execute()
                
                if not res_ferias_pend.data:
                    st.info("Não existem pedidos de férias pendentes de aprovação.")
                else:
                    for fp in res_ferias_pend.data:
                        fp_id = fp.get('id', '')
                        fp_user = fp.get('username', '')
                        fp_tipo = fp.get('tipo', '')
                        fp_ini = fp.get('data_inicio', '')
                        fp_fim = fp.get('data_fim', '')
                        fp_dias = fp.get('dias_uteis', '')

                        st.markdown(f"""
                            <div class="card-box">
                                <b>Colaborador:</b> {fp_user} | <b>Tipo:</b> {fp_tipo}<br>
                                <b>Período:</b> {fp_ini} a {fp_fim} ({fp_dias} dias)
                            </div>
                        """, unsafe_allow_html=True)
                        
                        col_ap1, col_ap2 = st.columns(2)
                        with col_ap1:
                            if st.button(f"Aprovar #{fp_id}", key=f"ap_{fp_id}"):
                                supabase.table("ferias").update({"estado": "Aprovado"}).eq("id", fp_id).execute()
                                st.success("Pedido aprovado!")
                                st.rerun()
                        with col_ap2:
                            if st.button(f"Rejeitar #{fp_id}", key=f"rej_{fp_id}"):
                                supabase.table("ferias").update({"estado": "Rejeitado"}).eq("id", fp_id).execute()
                                st.warning("Pedido rejeitado.")
                                st.rerun()
            except Exception as e:
                st.error(f"Erro ao carregar férias pendentes: {e}")

            st.markdown("---")
            st.markdown("#### 2. Registos de Ponto Hoje")
            try:
                res_ponto_hoje = supabase.table("picagens").select("*").eq("data", hoje_str).execute()
                if res_ponto_hoje.data:
                    df_p = pd.DataFrame(res_ponto_hoje.data)
                    cols_ponto = [c for c in ["username", "hora_entrada", "hora_saida_almoco", "hora_entrada_almoco", "hora_saida"] if c in df_p.columns]
                    st.dataframe(df_p[cols_ponto], use_container_width=True)
                else:
                    st.info("Ainda ninguém registou ponto hoje.")
            except Exception as e:
                st.error(f"Erro ao carregar registos de ponto do dia: {e}")
