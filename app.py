from datetime import datetime, date, timedelta
import calendar
import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gestão e Operações | Digital Solutions",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilização CSS minimalista e moderna com realce de cores
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
    .card-pendente {
        background: #fffbe6;
        padding: 18px;
        border-radius: 12px;
        border-left: 5px solid #faad14;
        margin-bottom: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .card-aprovado {
        background: #f6ffed;
        padding: 18px;
        border-radius: 12px;
        border-left: 5px solid #52c41a;
        margin-bottom: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .card-rejeitado {
        background: #fff2f0;
        padding: 18px;
        border-radius: 12px;
        border-left: 5px solid #ff4d4f;
        margin-bottom: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .card-box {
        background: white;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 15px;
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
        st.markdown(f"👋 **Bem-vindo(a), {st.session_state.nome}** (`{st.session_state.username}` — {perfil_txt})")
    with c_logout:
        if st.button("Sair", key="btn_logout_main"):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown("---")

    hoje_iso = date.today().isoformat()

    # =========================================================================
    # FUNÇÃO AUXILIAR: GERAR GRELHA / CALENDÁRIO MENSAL DE AUSÊNCIAS
    # =========================================================================
    def render_calendario_ausencias(res_ferias):
        st.markdown("#### 📅 Calendário / Grelha Mensal de Ausências")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            ano_sel = st.selectbox("Ano", [2026, 2027], index=0)
        with col_m2:
            mes_sel = st.selectbox("Mês", list(range(1, 13)), index=date.today().month - 1)

        num_dias = calendar.monthrange(ano_sel, mes_sel)[1]
        dias_mes = [date(ano_sel, mes_sel, d) for d in range(1, num_dias + 1)]

        colabs = set()
        ferias_validas = []
        if res_ferias:
            for f in res_ferias:
                user = f.get("username", "Desconhecido")
                colabs.add(user)
                try:
                    dt_i = datetime.strptime(f.get("data_inicio"), "%Y-%m-%d").date()
                    dt_f = datetime.strptime(f.get("data_fim"), "%Y-%m-%d").date()
                    est = f.get("estado", "Pendente") or "Pendente"
                    tipo = f.get("tipo", "Ausência") or "Ausência"
                    ferias_validas.append({"user": user, "ini": dt_i, "fim": dt_f, "estado": est, "tipo": tipo})
                except Exception:
                    pass

        if not colabs:
            st.info("Nenhuma ausência registada para construir a grelha.")
            return

        cols_df = ["Colaborador"] + [f"{d.day:02d}/{d.month:02d}" for d in dias_mes]
        matrix_data = []

        for c in sorted(colabs):
            row = [c]
            for d in dias_mes:
                status_dia = "🟢 Presente"
                for f in ferias_validas:
                    if f["user"] == c and f["ini"] <= d <= f["fim"]:
                        if f["estado"] == "Aprovado":
                            status_dia = f"🏖️ {f['tipo']} (Aprovado)"
                        elif f["estado"] == "Pendente":
                            status_dia = f"🟡 {f['tipo']} (Pendente)"
                        elif f["estado"] == "Rejeitado":
                            status_dia = "🔴 Rejeitado"
                        break
                row.append(status_dia)
            matrix_data.append(row)

        df_grid = pd.DataFrame(matrix_data, columns=cols_df)
        st.dataframe(df_grid, use_container_width=True)

    # =========================================================================
    # VISÃO DO COLABORADOR
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
                res_meus_reg = supabase.table("projetos_horas").select("*").eq("username", st.session_state.username).limit(10).execute()
                if res_meus_reg.data:
                    df_h = pd.DataFrame(res_meus_reg.data)
                    st.dataframe(df_h, use_container_width=True)
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
            try:
                res_f_all = supabase.table("ferias").select("*").execute()
                render_calendario_ausencias(res_f_all.data if res_f_all.data else [])
            except Exception as e:
                st.error(f"Erro ao carregar calendário: {e}")

    # =========================================================================
    # VISÃO DO ADMINISTRADOR
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
                            st.write(f"**Colab:** `{p_user}`")
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
                res_all_h = supabase.table("projetos_horas").select("*").limit(50).execute()
                if res_all_h.data:
                    for h in res_all_h.data:
                        h_id = h.get("id")
                        h_user = h.get("username", "Colaborador")
                        h_horas = h.get("horas_dedicadas", 8.0) or 8.0
                        h_desc = h.get("descricao", "") or ""

                        cols_h = st.columns([2, 1, 3, 1])
                        with cols_h[0]:
                            st.write(f"**`{h_user}`**")
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
            st.markdown("### Aprovação e Edição de Pedidos de Férias")
            try:
                res_ferias_all = supabase.table("ferias").select("*").execute()
                ferias_list = res_ferias_all.data if res_ferias_all.data else []

                # Separar pendentes
                pendentes = [f for f in ferias_list if f.get("estado", "Pendente") == "Pendente"]
                outros = [f for f in ferias_list if f.get("estado", "Pendente") != "Pendente"]

                if pendentes:
                    st.markdown("#### 🟡 Pedidos A Aguardar A Tua Aprovação")
                    for f in pendentes:
                        f_id = f.get("id")
                        f_user = f.get("username", "Desconhecido")
                        f_tipo = f.get("tipo", "Férias")
                        f_ini = f.get("data_inicio")
                        f_fim = f.get("data_fim")
                        f_obs = f.get("observacoes", "") or "Sem notas"

                        st.markdown(f"""
                            <div class="card-pendente">
                                <b>Colaborador:</b> <code>{f_user}</code> | <b>Tipo:</b> {f_tipo}<br>
                                <b>Período:</b> {f_ini} até {f_fim}<br>
                                <i>Nota: {f_obs}</i>
                            </div>
                        """, unsafe_allow_html=True)

                        c_f1, c_f2, c_f3 = st.columns(3)
                        with c_f1:
                            if st.button(f"Aprovar #{f_id}", key=f"adm_ap_{f_id}"):
                                supabase.table("ferias").update({"estado": "Aprovado"}).eq("id", f_id).execute()
                                st.success("Aprovado com sucesso!")
                                st.rerun()
                        with c_f2:
                            if st.button(f"Rejeitar #{f_id}", key=f"adm_rej_{f_id}"):
                                supabase.table("ferias").update({"estado": "Rejeitado"}).eq("id", f_id).execute()
                                st.warning("Rejeitado!")
                                st.rerun()
                        with c_f3:
                            if st.button(f"Apagar #{f_id}", key=f"adm_del_{f_id}"):
                                supabase.table("ferias").delete().eq("id", f_id).execute()
                                st.rerun()
                        st.markdown("---")

                if outros:
                    st.markdown("#### 📋 Pedidos Já Processados")
                    for f in outros:
                        f_id = f.get("id")
                        f_user = f.get("username", "Desconhecido")
                        f_tipo = f.get("tipo", "Férias")
                        f_est = f.get("estado", "Aprovado")
                        f_ini = f.get("data_inicio")
                        f_fim = f.get("data_fim")
                        css_class = "card-aprovado" if f_est == "Aprovado" else "card-rejeitado"

                        st.markdown(f"""
                            <div class="{css_class}">
                                <b>Colaborador:</b> <code>{f_user}</code> | <b>Tipo:</b> {f_tipo} | <b>Estado:</b> {f_est}<br>
                                <b>Período:</b> {f_ini} até {f_fim}
                            </div>
                        """, unsafe_allow_html=True)
                        st.markdown("---")

                if not ferias_list:
                    st.info("Não existem pedidos de férias registados.")

            except Exception as e:
                st.error(f"Erro ao carregar pedidos de férias: {e}")

            st.markdown("---")
            # Renderizar o calendário/grelha mensal para o Admin
            try:
                render_calendario_ausencias(ferias_list)
            except Exception as e:
                st.error(f"Erro ao gerar grelha mensal: {e}")
