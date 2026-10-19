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
    # FUNÇÃO AUXILIAR: CALENDÁRIO / GRELHA MENSAL DE AUSÊNCIAS
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

        # --- TAB 2: PROJETOS & HORAS (USANDO AS COLUNAS REAIS DA BD) ---
        with tabs[1]:
            st.markdown("### Registo de Horas em Projetos")
            try:
                res_proj = supabase.table("projetos").select("*").execute()
                projetos = res_proj.data if res_proj.data else []
            except Exception:
                projetos = []

            lista_nomes_projetos = [p.get("nome_projeto") for p in projetos if p.get("nome_projeto")]
            if not lista_nomes_projetos:
                st.warning("Não foram encontrados projetos na tabela 'projetos'. Crie um projeto antes de registar horas.")

            if lista_nomes_projetos:
                with st.form("form_horas"):
                    proj_nome = st.selectbox("Selecione o Projeto", lista_nomes_projetos)
                    tarefa = st.text_input("Tarefa realizada")
                    horas = st.number_input("Horas Dedicadas", min_value=0.5, max_value=24.0, value=1.0, step=0.5)
                    notas = st.text_area("Notas / Descrição do Trabalho Efetuado")

                    if st.form_submit_button("Registar Horas"):
                        if not tarefa.strip() or not notas.strip():
                            st.warning("Preencha a tarefa e a descrição do trabalho efetuado.")
                        else:
                            data_h = {
                                "username": st.session_state.username,
                                "projeto": proj_nome,
                                "tarefa": tarefa.strip(),
                                "horas": horas,
                                "notas": notas.strip(),
                                "data_registo": hoje_iso,
                                "estado": "Pendente"
                            }
                            try:
                                supabase.table("projetos_horas").insert(data_h).execute()
                                st.success("Horas registadas e enviadas para validação!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao registar horas: {e}")
                                st.caption("Confirme se executou a migração SQL para adicionar a coluna 'estado' à tabela projetos_horas.")

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
            st.info("Pode editar as picagens dos colaboradores e clicar em 'Guardar Alterações' no final do formulário.")
            
            try:
                res_all_p = supabase.table("picagens").select("*").order("data_hora", desc=True).limit(30).execute()
                picagens_data = res_all_p.data if res_all_p.data else []

                if picagens_data:
                    with st.form("form_edit_picagens"):
                        novas_picagens = {}
                        for p in picagens_data:
                            p_id = p.get("id")
                            p_user = p.get("username")
                            p_tipo = p.get("tipo")
                            p_dh = p.get("data_hora")

                            cols_ed = st.columns([2, 2, 3])
                            with cols_ed[0]:
                                st.write(f"**Colaborador:** `{p_user}`")
                            with cols_ed[1]:
                                t_sel = st.selectbox(f"Tipo (#{p_id})", ["entrada", "saida"], index=0 if p_tipo=="entrada" else 1, key=f"pt_tipo_{p_id}")
                            with cols_ed[2]:
                                dh_val = st.text_input(f"Data/Hora ISO (#{p_id})", value=str(p_dh), key=f"pt_dh_{p_id}")

                            novas_picagens[p_id] = {"tipo": t_sel, "data_hora": dh_val}
                            st.markdown("---")

                        if st.form_submit_button("💾 Guardar Alterações nas Picagens"):
                            for pid, pdata in novas_picagens.items():
                                supabase.table("picagens").update(pdata).eq("id", pid).execute()
                            st.success("Picagens atualizadas com sucesso!")
                            st.rerun()
                else:
                    st.info("Não existem picagens registadas.")
            except Exception as e:
                st.error(f"Erro ao carregar picagens: {e}")

        # --- ADMIN TAB 2: PAINEL DE GESTÃO, FILTROS E VALIDAÇÃO DE HORAS ---
        with tabs[1]:
            st.markdown("### Gestão de Projetos & Horas")
            st.caption("Os registos e indicadores são carregados da tabela projetos_horas no Supabase.")

            try:
                res_all_h = supabase.table("projetos_horas").select("*").order("data_registo", desc=True).execute()
                horas_data = res_all_h.data if res_all_h.data else []

                if not horas_data:
                    st.info("Ainda não existem registos de horas na base de dados.")
                elif "estado" not in horas_data[0]:
                    st.error("A tabela projetos_horas ainda não tem a coluna 'estado'. Execute o ficheiro supabase_migration_projetos_horas.sql no SQL Editor do Supabase e volte a carregar a aplicação.")
                else:
                    df_horas = pd.DataFrame(horas_data)
                    if "data_registo" not in df_horas.columns:
                        st.error("A tabela projetos_horas não contém a coluna data_registo necessária para filtrar por período.")
                    else:
                        df_horas["estado"] = df_horas["estado"].fillna("Pendente").astype(str).str.strip()
                        df_horas["username"] = df_horas["username"].fillna("Desconhecido").astype(str)
                        df_horas["data_registo_dt"] = pd.to_datetime(df_horas["data_registo"], errors="coerce").dt.date
                        hoje = date.today()
                        primeiro_dia_mes = hoje.replace(day=1)

                        # Indicadores calculados exclusivamente sobre os registos reais devolvidos pelo Supabase.
                        c1, c2, c3, c4 = st.columns(4)
                        pend_df = df_horas[df_horas["estado"].str.casefold() == "pendente"]
                        aprov_df = df_horas[df_horas["estado"].str.casefold() == "aprovado"]
                        rej_df = df_horas[df_horas["estado"].str.casefold() == "rejeitado"]
                        c1.metric("Pendentes", len(pend_df))
                        c2.metric("Aprovadas", len(aprov_df))
                        c3.metric("Rejeitadas", len(rej_df))
                        c4.metric("Horas por validar", round(pd.to_numeric(pend_df["horas"], errors="coerce").fillna(0).sum(), 2))

                        st.markdown("#### Filtrar registos")
                        f1, f2, f3 = st.columns(3)
                        estados_bd = sorted([e for e in df_horas["estado"].dropna().unique().tolist() if e])
                        # Estados suportados pelo fluxo + quaisquer estados adicionais que já existam na BD.
                        estados_fluxo = ["Pendente", "Aprovado", "Rejeitado"]
                        estados_opcoes = ["Todos"] + estados_fluxo + [e for e in estados_bd if e.casefold() not in {x.casefold() for x in estados_fluxo}]
                        estado_default = estados_opcoes.index("Rejeitado")
                        with f1:
                            estado_filtro = st.selectbox("Estado", estados_opcoes, index=estado_default, key="adm_horas_estado")
                        users_bd = sorted(df_horas["username"].dropna().unique().tolist())
                        with f2:
                            colaborador_filtro = st.selectbox("Colaborador", ["Todos"] + users_bd, index=0, key="adm_horas_colaborador")
                        with f3:
                            periodo_filtro = st.selectbox("Período", ["Este mês", "Mês anterior", "Todo o histórico"], index=0, key="adm_horas_periodo")

                        df_filtrado = df_horas.copy()
                        if estado_filtro != "Todos":
                            df_filtrado = df_filtrado[df_filtrado["estado"].str.casefold() == estado_filtro.casefold()]
                        if colaborador_filtro != "Todos":
                            df_filtrado = df_filtrado[df_filtrado["username"] == colaborador_filtro]
                        if periodo_filtro == "Este mês":
                            df_filtrado = df_filtrado[df_filtrado["data_registo_dt"].apply(lambda d: pd.notna(d) and d >= primeiro_dia_mes and d <= hoje)]
                        elif periodo_filtro == "Mês anterior":
                            ultimo_dia_mes_anterior = primeiro_dia_mes - timedelta(days=1)
                            primeiro_dia_mes_anterior = ultimo_dia_mes_anterior.replace(day=1)
                            df_filtrado = df_filtrado[df_filtrado["data_registo_dt"].apply(lambda d: pd.notna(d) and primeiro_dia_mes_anterior <= d <= ultimo_dia_mes_anterior)]

                        total_horas_filtradas = pd.to_numeric(df_filtrado.get("horas", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
                        k1, k2, k3 = st.columns(3)
                        k1.metric("Registos encontrados", len(df_filtrado))
                        k2.metric("Total de horas", round(float(total_horas_filtradas), 2))
                        k3.metric("Período", periodo_filtro)

                        colunas_visiveis = [c for c in ["id", "username", "projeto", "tarefa", "horas", "notas", "data_registo", "estado", "validado_por", "validado_em", "motivo_rejeicao"] if c in df_filtrado.columns]
                        if df_filtrado.empty:
                            st.info("Não existem registos que correspondam a estes filtros.")
                        else:
                            st.dataframe(df_filtrado[colunas_visiveis], use_container_width=True, hide_index=True)

                            st.markdown("#### Ações de validação")
                            st.caption("As ações estão disponíveis para registos pendentes. Para os consultar, selecione Estado = Pendente ou Todos.")
                            pendentes_visiveis = df_filtrado[df_filtrado["estado"].str.casefold() == "pendente"]
                            if pendentes_visiveis.empty:
                                st.info("Não há registos pendentes na seleção atual.")
                            else:
                                for _, reg in pendentes_visiveis.iterrows():
                                    rid = reg.get("id")
                                    with st.container(border=True):
                                        st.markdown(f"**#{rid} · {reg.get('username', 'Desconhecido')} · {reg.get('projeto', 'Sem projeto')}**")
                                        st.write(f"**Tarefa:** {reg.get('tarefa', '') or '—'}  |  **Horas:** {reg.get('horas', 0)}  |  **Data:** {reg.get('data_registo', '—')}")
                                        st.write(reg.get("notas", "") or "Sem descrição.")
                                        motivo = st.text_input("Motivo de rejeição (se aplicável)", key=f"motivo_rej_h_{rid}")
                                        b1, b2 = st.columns(2)
                                        with b1:
                                            if st.button("Aprovar", key=f"aprovar_h_{rid}", use_container_width=True):
                                                try:
                                                    supabase.table("projetos_horas").update({"estado": "Aprovado", "validado_por": st.session_state.username, "validado_em": datetime.now().isoformat(), "motivo_rejeicao": None}).eq("id", rid).execute()
                                                    st.success(f"Registo #{rid} aprovado.")
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Não foi possível aprovar o registo #{rid}: {e}")
                                        with b2:
                                            if st.button("Rejeitar", key=f"rejeitar_h_{rid}", use_container_width=True):
                                                if not motivo.strip():
                                                    st.warning("Indique o motivo da rejeição antes de rejeitar.")
                                                else:
                                                    try:
                                                        supabase.table("projetos_horas").update({"estado": "Rejeitado", "validado_por": st.session_state.username, "validado_em": datetime.now().isoformat(), "motivo_rejeicao": motivo.strip()}).eq("id", rid).execute()
                                                        st.warning(f"Registo #{rid} rejeitado.")
                                                        st.rerun()
                                                    except Exception as e:
                                                        st.error(f"Não foi possível rejeitar o registo #{rid}: {e}")
            except Exception as e:
                st.error(f"Erro ao carregar o painel de projetos e horas: {e}")
                st.caption("Confirme a ligação ao Supabase e que a migração SQL de projetos_horas foi executada.")

        # --- ADMIN TAB 3: GESTÃO DE FÉRIAS E MAPA MENSAL ---
        with tabs[2]:
            st.markdown("### Aprovação e Gestão de Pedidos de Férias")
            try:
                res_ferias_all = supabase.table("ferias").select("*").execute()
                ferias_list = res_ferias_all.data if res_ferias_all.data else []

                pendentes = [f for f in ferias_list if f.get("estado", "Pendente") == "Pendente"]
                outros = [f for f in ferias_list if f.get("estado", "Pendente") != "Pendente"]

                if pendentes:
                    st.markdown("#### 🟡 Pedidos Pendentes de Aprovação")
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
                                st.success("Aprovado!")
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
                    st.markdown("#### 📋 Histórico de Pedidos Processados")
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

                if not ferias_list:
                    st.info("Não existem pedidos de férias registados.")

            except Exception as e:
                st.error(f"Erro ao carregar pedidos de férias: {e}")

            st.markdown("---")
            try:
                render_calendario_ausencias(ferias_list)
            except Exception as e:
                st.error(f"Erro ao gerar grelha mensal: {e}")