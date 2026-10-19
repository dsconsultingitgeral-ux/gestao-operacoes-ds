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
