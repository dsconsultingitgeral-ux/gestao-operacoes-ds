from datetime import datetime, date
import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
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

# --- 2. LIGAÇÃO AO SUPABASE ---
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
                        # Identifica se é admin se o username contiver 'admin'
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
        perfil_txt = "Admin Principal" if st.session_state.is_admin else "Colaborador"
        st.markdown(f"👋 **Bem-vindo(a), {st.session_state.nome}** ({perfil_txt})")
    with c_logout:
        if st.button("Sair", key="btn_logout_main"):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown("---")

    hoje_iso = date.today().isoformat()

    # =========================================================================
    # VISÃO DO COLABORADOR (Username começa por "col_")
    # =========================================================================
    if not st.session_state.is_admin:
        tabs = st.tabs(["🕒 Picagem de Ponto", "📁 Projetos & Horas", "🏖️ Férias e Ausências"])

        # --- TAB 1: PICAGEM DE PONTO ---
        with tabs[0]:
            st.markdown("### Picagem de Ponto Diária")
            st.write(f"**Data:** {date.today().strftime('%d/%m/%Y')}")

            def registar_ponto(tipo_evento):
                try:
                    agora_iso = datetime.now().isoformat()
                    supabase.table("picagens").insert({
                        "username": st.session_state.username,
                        "tipo": tipo_evento,
                        "data_hora": agora_iso
                    }).execute()
                    st.success(f"Registo de {tipo_evento.title()} efetuado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao registar picagem: {e}")

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                if st.button("Entrada 🟢", use_container_width=True):
                    registar_ponto("entrada")
            with col_p2:
                if st.button("Saída 🏁", use_container_width=True):
                    registar_ponto("saida")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### Os Seus Registos do Dia")
            try:
                res_hoje = supabase.table("picagens").select("*").eq("username", st.session_state.username).gte("data_hora", f"{hoje_iso}T00:00:00").order("data_hora", desc=True).execute()
                if res_hoje.data:
                    for reg in res_hoje.data:
                        tipo_reg = reg.get("tipo", "").title()
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
                st.error(f"Erro ao carregar picagens: {e}")

        # --- TAB 2: PROJETOS & HORAS ---
        with tabs[1]:
            st.markdown("### Registo de Horas em Projetos")
            try:
                res_proj = supabase.table("projetos").select("*").execute()
                projetos = res_proj.data if res_proj.data else []
            except Exception:
                projetos = []

            if not projetos:
                st.info("Não existem projetos disponíveis de momento.")
            else:
                options_proj = {p.get("nome_projeto", f"Projeto {p.get('id')}"): p.get("id") for p in projetos}
                
                with st.form("form_horas"):
                    proj_nome = st.selectbox("Selecione o Projeto", list(options_proj.keys()))
                    horas = st.number_input("Horas Dedicadas", min_value=0.5, max_value=24.0, value=8.0, step=0.5)
                    descricao = st.text_area("Notas / Descrição do Trabalho Efetuado")
                    
                    if st.form_submit_button("Registar Horas"):
                        if not descricao:
                            st.warning("Insira uma nota sobre o trabalho efetuado.")
                        else:
                            data_h = {
                                "projeto_id": options_proj[proj_nome],
                                "username": st.session_state.username,
                                "data": hoje_iso,
                                "horas_dedicadas": horas,
                                "descricao": descricao
                            }
                            try:
                                supabase.table("projetos_horas").insert(data_h).execute()
                                st.success("Horas registadas com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao registar horas: {e}")

            st.markdown("---")
            st.markdown("### Os Seus Registos Recentes")
            try:
                res_meus_reg = supabase.table("projetos_horas").select("*").eq("username", st.session_state.username).order("data", desc=True).limit(10).execute()
                if res_meus_reg.data:
                    df_h = pd.DataFrame(res_meus_reg.data)
                    cols_to_show = [c for c in ["data", "horas_dedicadas", "descricao"] if c in df_h.columns]
                    st.dataframe(df_h[cols_to_show], use_container_width=True)
                else:
                    st.info("Nenhum registo de horas encontrado.")
            except Exception as e:
                st.error(f"Erro ao carregar registos: {e}")

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
                        try:
                            supabase.table("ferias").insert(data_f).execute()
                            st.success("Pedido de ausência submetido com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao submeter pedido: {e}")

            st.markdown("---")
            st.markdown("### Histórico e Transparência da Equipa")
            try:
                res_ferias_all = supabase.table("ferias").select("*").execute()
                if res_ferias_all.data:
                    for f in res_ferias_all.data:
                        f_user = f.get('username', '')
                        f_tipo = f.get('tipo', '')
                        f_ini = f.get('data_inicio', '')
                        f_fim = f.get('data_fim', '')
                        f_est = f.get('estado', 'Pendente')
                        cor_est = "🟡" if f_est == "Pendente" else ("🟢" if f_est == "Aprovado" else "🔴")

                        st.markdown(f"""
                            <div class="card-box" style="padding:12px 15px; margin-bottom:10px;">
                                <b>{f_user}</b> — {f_tipo} | De: {f_ini} até {f_fim} | <b>Estado:</b> {cor_est} {f_est}
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Sem registos de férias na equipa.")
            except Exception as e:
                st.error(f"Erro ao carregar férias: {e}")

    # =========================================================================
    # VISÃO DO ADMINISTRADOR (Username contém "admin")
    # =========================================================================
    else:
        tabs = st.tabs(["🕒 Gestão de Picagens", "📁 Gestão de Projetos & Horas", "🏖️ Gestão & Mapa de Férias"])

        # --- ADMIN TAB 1: GESTÃO DE PICAGENS ---
        with tabs[0]:
            st.markdown("### Painel de Supervisão e Edição de Picagens")
            st.markdown("Aqui pode visualizar e corrigir os registos de ponto de todos os colaboradores.")
            
            try:
                res_all_p = supabase.table("picagens").select("*").order("data_hora", desc=True).limit(50).execute()
                if res_all_p.data:
                    for p in res_all_p.data:
                        p_id = p.get("id")
                        p_user = p.get("username")
                        p_tipo = p.get("tipo")
                        p_dh = p.get("data_hora")

                        cols_ed = st.columns([2, 2, 2, 1])
                        with cols_ed[0]:
                            st.write(f"**Colab:** {p_user}")
                        with cols_ed[1]:
                            novo_tipo = st.selectbox("Tipo", ["entrada", "saida"], index=0 if p_tipo=="entrada" else 1, key=f"pt_tipo_{p_id}")
                        with cols_ed[2]:
                            nova_datahora = st.text_input("Data/Hora (ISO)", value=p_dh, key=f"pt_dh_{p_id}")
                        with cols_ed[3]:
                            st.write("")
                            if st.button("Guardar", key=f"btn_save_p_{p_id}"):
                                supabase.table("picagens").update({"tipo": novo_tipo, "data_hora": nova_datahora}).eq("id", p_id).execute()
                                st.success("Atualizado!")
                                st.rerun()
                        st.markdown("---")
                else:
                    st.info("Não existem picagens registadas.")
            except Exception as e:
                st.error(f"Erro ao carregar picagens globais: {e}")

        # --- ADMIN TAB 2: GESTÃO DE PROJETOS E HORAS ---
        with tabs[1]:
            st.markdown("### Supervisão e Edição de Horas em Projetos")
            try:
                res_all_h = supabase.table("projetos_horas").select("*").order("data", desc=True).limit(50).execute()
                if res_all_h.data:
                    for h in res_all_h.data:
                        h_id = h.get("id")
                        h_user = h.get("username")
                        h_horas = h.get("horas_dedicadas")
                        h_desc = h.get("descricao")

                        cols_h = st.columns([2, 1, 3, 1])
                        with cols_h[0]:
                            st.write(f"**{h_user}** ({h.get('data')})")
                        with cols_h[1]:
                            novas_horas = st.number_input("Horas", value=float(h_horas), step=0.5, key=f"h_val_{h_id}")
                        with cols_h[2]:
                            nova_desc = st.text_input("Notas", value=h_desc, key=f"h_desc_{h_id}")
                        with cols_h[3]:
                            st.write("")
                            if st.button("Atualizar", key=f"btn_h_{h_id}"):
                                supabase.table("projetos_horas").update({"horas_dedicadas": novas_horas, "descricao": nova_desc}).eq("id", h_id).execute()
                                st.success("Atualizado!")
                                st.rerun()
                        st.markdown("---")
                else:
                    st.info("Sem registos de horas.")
            except Exception as e:
                st.error(f"Erro ao carregar horas: {e}")

        # --- ADMIN TAB 3: GESTÃO DE FÉRIAS E MAPA MENSAL ---
        with tabs[2]:
            st.markdown("### Aprovação e Edição de Férias")
            try:
                res_ferias_all = supabase.table("ferias").select("*").order("created_at", desc=True).execute()
                if res_ferias_all.data:
                    for f in res_ferias_all.data:
                        f_id = f.get("id")
                        f_user = f.get("username")
                        f_tipo = f.get("tipo")
                        f_est = f.get("estado")
                        f_ini = f.get("data_inicio")
                        f_fim = f.get("data_fim")

                        st.markdown(f"**{f_user}** | {f_tipo} | De: {f_ini} até {f_fim} | **Estado Atual:** {f_est}")
                        
                        c_f1, c_f2, c_f3 = st.columns(3)
                        with c_f1:
                            if st.button(f"Aprovar #{f_id}", key=f"adm_ap_{f_id}"):
                                supabase.table("ferias").update({"estado": "Aprovado"}).eq("id", f_id).execute()
                                st.rerun()
                        with c_f2:
                            if st.button(f"Rejeitar #{f_id}", key=f"adm_rej_{f_id}"):
                                supabase.table("ferias").update({"estado": "Rejeitado"}).eq("id", f_id).execute()
                                st.rerun()
                        with c_f3:
                            if st.button(f"Apagar #{f_id}", key=f"adm_del_{f_id}"):
                                supabase.table("ferias").delete().eq("id", f_id).execute()
                                st.rerun()
                        st.markdown("---
