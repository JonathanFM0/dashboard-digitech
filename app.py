"""
Painel de Desempenho 360º - Digitech
Sistema completo de análise de desempenho educacional
Tecnologias: Streamlit, Pandas, Plotly Express, PyGithub
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from datetime import datetime
from pathlib import Path
import io

# Configuração da página
st.set_page_config(
    page_title="Painel de Desempenho 360º - Digitech",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constantes e configurações
HISTORICO_DIR = Path("historico_dados")
METAS_FILE = Path("metas_ha.json")
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "")

# Inicialização do session_state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_month" not in st.session_state:
    st.session_state.current_month = None
if "data_cache" not in st.session_state:
    st.session_state.data_cache = {}


def login_screen():
    """Tela de login do sistema"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 50px;">
            <h1>🔐 Painel de Desempenho 360º - Digitech</h1>
            <p>Sistema de Análise de Desempenho Educacional</p>
        </div>
        """, unsafe_allow_html=True)
        
        password = st.text_input("Senha de acesso:", type="password", placeholder="Digite a senha...")
        
        if st.button("Entrar", use_container_width=True):
            if password == "admin123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Senha incorreta!")


def setup_github():
    """Configura cliente GitHub se tokens estiverem disponíveis"""
    try:
        if GITHUB_TOKEN and GITHUB_REPO:
            from github import Github
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(GITHUB_REPO)
            return repo
    except Exception:
        pass
    return None


def save_to_github(repo, file_path, content, commit_message):
    """Salva arquivo no GitHub"""
    if repo:
        try:
            # Tenta obter o arquivo existente
            try:
                contents = repo.get_contents(str(file_path))
                repo.update_file(
                    path=str(file_path),
                    message=commit_message,
                    content=content,
                    sha=contents.sha,
                    branch="main"
                )
            except Exception:
                # Arquivo não existe, cria novo
                repo.create_file(
                    path=str(file_path),
                    message=commit_message,
                    content=content,
                    branch="main"
                )
        except Exception as e:
            st.warning(f"Erro ao salvar no GitHub: {str(e)}")


def load_from_github(repo, file_path):
    """Carrega arquivo do GitHub"""
    if repo:
        try:
            contents = repo.get_contents(str(file_path))
            return contents.decoded_content.decode('utf-8')
        except Exception:
            pass
    return None


def init_historico_dir():
    """Inicializa diretório de histórico"""
    HISTORICO_DIR.mkdir(exist_ok=True)


def get_available_months():
    """Retorna lista de meses disponíveis no histórico com informações de período"""
    init_historico_dir()
    months = []
    
    # Processa arquivos na pasta historico_dados
    for f in HISTORICO_DIR.glob("*.xlsx"):
        try:
            # Carrega dados para extrair período
            data = load_excel_data(str(f))
            date_ranges = extract_date_range(data)
            periodo_info = get_periodo_info(date_ranges)
            
            if periodo_info:
                month_name = f"{periodo_info['mes_ano']} ({f.stem})"
                months.append((f.name, month_name, periodo_info))
            else:
                # Fallback para nome do arquivo
                month_name = f.stem.replace("_", " ").replace("-", " ")
                months.append((f.name, month_name, None))
        except Exception:
            continue
    
    # Adiciona arquivos na raiz também
    for f in Path(".").glob("*.xlsx"):
        if "Consolidado" in f.name or "Status" in f.name:
            try:
                data = load_excel_data(str(f))
                date_ranges = extract_date_range(data)
                periodo_info = get_periodo_info(date_ranges)
                
                if periodo_info:
                    month_name = f"{periodo_info['mes_ano']} ({f.stem})"
                    months.append((str(f), month_name, periodo_info))
                else:
                    month_name = f.stem.replace("_", " ").replace("-", " ")
                    months.append((str(f), month_name, None))
            except Exception:
                continue
    
    return sorted(months, key=lambda x: x[1], reverse=True)


def extract_month_from_data(df_ocupacao):
    """Extrai mês/ano dos dados de ocupação"""
    try:
        if 'DATA' in df_ocupacao.columns and len(df_ocupacao) > 0:
            data_col = pd.to_datetime(df_ocupacao['DATA'], errors='coerce')
            min_date = data_col.min()
            if pd.notna(min_date):
                return min_date.strftime("%Y-%m")
    except Exception:
        pass
    return datetime.now().strftime("%Y-%m")


def extract_date_range(data):
    """Extrai intervalo de datas de todos os dataframes relevantes"""
    date_ranges = {}
    
    # Verifica OCUPAÇÃO
    if 'OCUPAÇÃO' in data and data['OCUPAÇÃO'] is not None and len(data['OCUPAÇÃO']) > 0:
        df = data['OCUPAÇÃO']
        if 'DATA' in df.columns:
            try:
                data_col = pd.to_datetime(df['DATA'], errors='coerce')
                valid_dates = data_col.dropna()
                if len(valid_dates) > 0:
                    date_ranges['ocupacao'] = {
                        'min': valid_dates.min(),
                        'max': valid_dates.max()
                    }
            except Exception:
                pass
    
    # Verifica FALTAS
    if 'FALTAS' in data and data['FALTAS'] is not None and len(data['FALTAS']) > 0:
        df = data['FALTAS']
        if 'DATA_FALTA' in df.columns:
            try:
                data_col = pd.to_datetime(df['DATA_FALTA'], errors='coerce')
                valid_dates = data_col.dropna()
                if len(valid_dates) > 0:
                    date_ranges['faltas'] = {
                        'min': valid_dates.min(),
                        'max': valid_dates.max()
                    }
            except Exception:
                pass
    
    # Verifica NÃO_REGÊNCIA
    if 'NÃO_REGÊNCIA' in data and data['NÃO_REGÊNCIA'] is not None and len(data['NÃO_REGÊNCIA']) > 0:
        df = data['NÃO_REGÊNCIA']
        if 'DATA_INICIO' in df.columns and 'DATA_FIM' in df.columns:
            try:
                inicio_col = pd.to_datetime(df['DATA_INICIO'], errors='coerce')
                fim_col = pd.to_datetime(df['DATA_FIM'], errors='coerce')
                valid_inicio = inicio_col.dropna()
                valid_fim = fim_col.dropna()
                if len(valid_inicio) > 0 or len(valid_fim) > 0:
                    all_dates = pd.concat([valid_inicio, valid_fim])
                    date_ranges['nao_regencia'] = {
                        'min': all_dates.min(),
                        'max': all_dates.max()
                    }
            except Exception:
                pass
    
    # Verifica CALENDÁRIO
    if 'CALENDÁRIO' in data and data['CALENDÁRIO'] is not None and len(data['CALENDÁRIO']) > 0:
        df = data['CALENDÁRIO']
        date_cols = [col for col in df.columns if 'DATA' in col.upper() or 'DATE' in col.upper()]
        if date_cols:
            try:
                all_dates = pd.Series()
                for col in date_cols:
                    data_col = pd.to_datetime(df[col], errors='coerce')
                    valid_dates = data_col.dropna()
                    all_dates = pd.concat([all_dates, valid_dates])
                if len(all_dates) > 0:
                    date_ranges['calendario'] = {
                        'min': all_dates.min(),
                        'max': all_dates.max()
                    }
            except Exception:
                pass
    
    return date_ranges


def get_periodo_info(date_ranges):
    """Gera informações formatadas sobre o período dos dados"""
    if not date_ranges:
        return None
    
    all_mins = []
    all_maxs = []
    
    # Prioriza ocupacao e nao_regencia (dados reais do mês)
    # Calendário é apenas referência anual e NÃO deve ser usado para definir o período
    priority_sources = ['ocupacao', 'nao_regencia', 'faltas']
    
    for source in priority_sources:
        if source in date_ranges:
            range_data = date_ranges[source]
            if 'min' in range_data and pd.notna(range_data['min']):
                all_mins.append(range_data['min'])
            if 'max' in range_data and pd.notna(range_data['max']):
                all_maxs.append(range_data['max'])
    
    # Se não houver dados prioritários, usa calendário como fallback
    if not all_mins and 'calendario' in date_ranges:
        range_data = date_ranges['calendario']
        if 'min' in range_data and pd.notna(range_data['min']):
            all_mins.append(range_data['min'])
        if 'max' in range_data and pd.notna(range_data['max']):
            all_maxs.append(range_data['max'])
    
    if not all_mins or not all_maxs:
        return None
    
    periodo_min = min(all_mins)
    periodo_max = max(all_maxs)
    
    # Formata nome do mês em português
    meses_pt = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
               'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    mes_nome = meses_pt[periodo_min.month - 1]
    
    return {
        'inicio': periodo_min,
        'fim': periodo_max,
        'mes_ano': f"{mes_nome}/{periodo_min.year}",
        'dias_totais': (periodo_max - periodo_min).days + 1
    }


def load_excel_data(file_path):
    """Carrega dados do Excel com tratamento de erros robusto"""
    try:
        xl = pd.ExcelFile(file_path)
        data = {}
        
        # Mapeamento de abas (considerando variações de nomes)
        sheet_mappings = {
            'TURMAS': ['TURMAS', 'TURNO'],
            'OCUPAÇÃO': ['OCUPAÇÃO', 'OCUPACAO'],
            'NÃO_REGÊNCIA': ['NÃO_REGÊNCIA', 'NAO_REGENCIA', 'NÃO_REGENCIA'],
            'INSTRUTORES': ['INSTRUTORES'],
            'DISCIPLINAS': ['DISCIPLINAS', 'APOIO_DISCIPLINA'],
            'AMBIENTES': ['AMBIENTES'],
            'FALTAS': ['FALTAS'],
            'PARÂMETROS': ['PARÂMETROS', 'PARAMETROS'],
            'CALENDÁRIO': ['CALENDÁRIO', 'CALENDARIO']
        }
        
        available_sheets = xl.sheet_names
        
        for key, possible_names in sheet_mappings.items():
            for name in possible_names:
                if name in available_sheets:
                    try:
                        if key == 'DISCIPLINAS':
                            # DISCIPLINAS tem header na linha 2 (índice 1)
                            df = pd.read_excel(xl, sheet_name=name, header=1)
                        elif key == 'PARÂMETROS':
                            # PARÂMETROS tem estrutura especial
                            df = pd.read_excel(xl, sheet_name=name, header=None)
                        else:
                            df = pd.read_excel(xl, sheet_name=name)
                        data[key] = df
                    except Exception:
                        continue
                    break
        
        return data
    except Exception as e:
        st.error(f"Erro ao carregar Excel: {str(e)}")
        return {}


def validate_excel_structure(data):
    """Valida estrutura mínima do Excel"""
    required_sheets = ['TURMAS', 'OCUPAÇÃO', 'DISCIPLINAS']
    missing = []
    
    for sheet in required_sheets:
        if sheet not in data:
            missing.append(sheet)
    
    if missing:
        return False, f"Faltam abas obrigatórias: {', '.join(missing)}"
    
    return True, "Estrutura válida"


def load_metas_ha():
    """Carrega metas manuais de Hora-Aluno"""
    if METAS_FILE.exists():
        try:
            with open(METAS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_metas_ha(metas):
    """Salva metas manuais de Hora-Aluno"""
    try:
        with open(METAS_FILE, 'w', encoding='utf-8') as f:
            json.dump(metas, f, indent=2, ensure_ascii=False)
        
        # Sincroniza com GitHub
        repo = setup_github()
        if repo:
            with open(METAS_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            save_to_github(repo, METAS_FILE, content, "Atualização de metas HA")
    except Exception as e:
        st.warning(f"Erro ao salvar metas: {str(e)}")


def calculate_hora_aluno_meta(turmas_df, disciplinas_df):
    """Calcula meta de Hora-Aluno cruzando TURMAS e DISCIPLINAS"""
    try:
        if turmas_df is None or disciplinas_df is None:
            return 0, 0, pd.DataFrame()
        
        # Verifica colunas necessárias
        turmas_cols = turmas_df.columns.tolist()
        disc_cols = disciplinas_df.columns.tolist()
        
        if 'ID_TURMA' not in turmas_cols or 'VAGAS_OCUPADAS' not in turmas_cols:
            return 0, 0, pd.DataFrame()
        
        if 'ID_TURMA' not in disc_cols or 'CARGA_HORARIA' not in disc_cols or 'STATUS' not in disc_cols:
            return 0, 0, pd.DataFrame()
        
        # Merge dos dataframes
        merged = pd.merge(
            turmas_df[['ID_TURMA', 'NOME_TURMA', 'VAGAS_OCUPADAS']],
            disciplinas_df[['ID_TURMA', 'CARGA_HORARIA', 'STATUS', 'NOME_DISCIPLINA']],
            on='ID_TURMA',
            how='left'
        )
        
        # Calcula HA por disciplina (CARGA_HORARIA * VAGAS_OCUPADAS)
        merged['HA_DISCIPLINA'] = merged['CARGA_HORARIA'] * merged['VAGAS_OCUPADAS']
        
        # Meta total (soma de todas as disciplinas)
        meta_total = merged['HA_DISCIPLINA'].sum()
        
        # Realizado (apenas disciplinas FINALIZADO)
        realizado = merged[merged['STATUS'].str.upper().str.contains('FINALIZADO', na=False)]['HA_DISCIPLINA'].sum()
        
        # Agrupa por turma para progresso
        progresso_turma = merged.groupby('NOME_TURMA').agg({
            'HA_DISCIPLINA': 'sum',
            'CARGA_HORARIA': lambda x: x.sum(),
            'STATUS': lambda x: (x.str.upper().str.contains('FINALIZADO', na=False)).sum()
        }).reset_index()
        
        return meta_total, realizado, merged, progresso_turma
    except Exception as e:
        st.warning(f"Erro ao calcular Hora-Aluno: {str(e)}")
        return 0, 0, pd.DataFrame(), pd.DataFrame()


def format_dataframe_for_csv(df):
    """Formata DataFrame para exportação CSV"""
    output = io.StringIO()
    df.to_csv(output, index=False, sep=';', encoding='utf-8-sig')
    return output.getvalue()


def render_visao_360(data):
    """Renderiza página Visão 360º"""
    st.header("🌐 Visão 360º")
    
    turmas_df = data.get('TURMAS', pd.DataFrame())
    ocupacao_df = data.get('OCUPAÇÃO', pd.DataFrame())
    ambientes_df = data.get('AMBIENTES', pd.DataFrame())
    instrutores_df = data.get('INSTRUTORES', pd.DataFrame())
    disciplinas_df = data.get('DISCIPLINAS', pd.DataFrame())
    faltas_df = data.get('FALTAS', pd.DataFrame())
    
    # KPIs Superiores
    kpi_cols = st.columns(5)
    
    # Qtd Turmas
    qtd_turmas = len(turmas_df) if turmas_df is not None and len(turmas_df) > 0 else 0
    kpi_cols[0].metric("Qtd Turmas", qtd_turmas)
    
    # Total Alunos
    total_alunos = turmas_df['VAGAS_OCUPADAS'].sum() if turmas_df is not None and 'VAGAS_OCUPADAS' in turmas_df.columns else 0
    kpi_cols[1].metric("Total Alunos", int(total_alunos))
    
    # Salas Físicas
    salas_fisicas = 0
    if ambientes_df is not None and len(ambientes_df) > 0:
        if 'VIRTUAL' in ambientes_df.columns:
            salas_fisicas = len(ambientes_df[ambientes_df['VIRTUAL'].isna() | (ambientes_df['VIRTUAL'] == False)])
        else:
            salas_fisicas = len(ambientes_df)
    kpi_cols[2].metric("Salas Físicas", salas_fisicas)
    
    # Qtd Instrutores
    qtd_instrutores = len(instrutores_df) if instrutores_df is not None and len(instrutores_df) > 0 else 0
    kpi_cols[3].metric("Qtd Instrutores", qtd_instrutores)
    
    # Qtd Faltas
    qtd_faltas = len(faltas_df) if faltas_df is not None and len(faltas_df) > 0 else 0
    kpi_cols[4].metric("Qtd Faltas", qtd_faltas)
    
    st.divider()
    
    # Meta de Hora-Aluno
    st.subheader("⏱️ Meta de Hora-Aluno (HA)")
    
    meta_total, realizado, merged_df, progresso_turma = calculate_hora_aluno_meta(turmas_df, disciplinas_df)
    
    # Carrega metas manuais
    metas_manuais = load_metas_ha()
    
    # Verifica se há meta manual que sobrescreva
    meta_exibicao = meta_total
    if metas_manuais and 'meta_manual' in metas_manuais:
        meta_exibicao = metas_manuais['meta_manual']
        st.info(f"📝 Meta manual definida: {meta_exibicao:,.0f} HA")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Meta Total HA", f"{meta_exibicao:,.0f}")
        st.metric("Realizado HA", f"{realizado:,.0f}")
        
        if meta_exibicao > 0:
            percentual = (realizado / meta_exibicao) * 100
            st.progress(min(percentual / 100, 1.0))
            st.write(f"**Progresso:** {percentual:.1f}%")
    
    with col2:
        # Gráfico de gauge
        if meta_exibicao > 0:
            percentual = min((realizado / meta_exibicao) * 100, 100)
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=percentual,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Progresso HA (%)", 'font': {'size': 18}},
                delta={'reference': 80, 'increasing': {'color': "green"}},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "blue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 80
                    }
                }
            ))
            fig_gauge.update_layout(height=250)
            st.plotly_chart(fig_gauge, use_container_width=True)
    
    # Editor de meta manual
    with st.expander("✏️ Editar Meta Manual de HA"):
        nova_meta = st.number_input(
            "Definir meta manual (deixe 0 para usar cálculo automático)",
            min_value=0,
            value=metas_manuais.get('meta_manual', 0),
            step=1000
        )
        if st.button("Salvar Meta Manual"):
            if nova_meta > 0:
                metas_manuais['meta_manual'] = nova_meta
                metas_manuais['data_atualizacao'] = datetime.now().isoformat()
                save_metas_ha(metas_manuais)
                st.success("Meta manual salva com sucesso!")
                st.rerun()
            else:
                if 'meta_manual' in metas_manuais:
                    del metas_manuais['meta_manual']
                    save_metas_ha(metas_manuais)
                    st.success("Meta manual removida. Usando cálculo automático.")
                    st.rerun()
    
    st.divider()
    
    # Progresso por Turma
    st.subheader("📊 Progresso de HA por Turma")
    
    if progresso_turma is not None and len(progresso_turma) > 0:
        # Calcula percentual por turma
        progresso_turma['PERCENTUAL'] = (progresso_turma['STATUS'] / progresso_turma['HA_DISCIPLINA'].count()) * 100
        
        fig_barras = px.bar(
            progresso_turma.sort_values('PERCENTUAL', ascending=True),
            x='PERCENTUAL',
            y='NOME_TURMA',
            orientation='h',
            title='% de Conclusão de HA por Turma',
            labels={'PERCENTUAL': 'Percentual (%)', 'NOME_TURMA': 'Turma'},
            color='PERCENTUAL',
            color_continuous_scale='RdYlGn'
        )
        fig_barras.update_layout(height=max(300, len(progresso_turma) * 40))
        st.plotly_chart(fig_barras, use_container_width=True)
        
        # Expander com tabela de detalhamento
        with st.expander("📋 Detalhamento do Status das Disciplinas"):
            if merged_df is not None and len(merged_df) > 0:
                display_df = merged_df[['NOME_TURMA', 'NOME_DISCIPLINA', 'CARGA_HORARIA', 'VAGAS_OCUPADAS', 'HA_DISCIPLINA', 'STATUS']].copy()
                display_df.columns = ['Turma', 'Disciplina', 'Carga Horária', 'Vagas Ocupadas', 'HA', 'Status']
                st.dataframe(display_df, use_container_width=True)
    else:
        st.warning("Dados insuficientes para calcular progresso por turma.")


def render_analise_docentes(data):
    """Renderiza página Análise de Docentes (RH)"""
    st.header("👥 Análise de Docentes (RH)")
    
    nao_regencia_df = data.get('NÃO_REGÊNCIA', pd.DataFrame())
    
    if nao_regencia_df is None or len(nao_regencia_df) == 0:
        st.warning("Nenhum dado de Não Regência disponível.")
        return
    
    # Verifica colunas necessárias
    required_cols = ['INSTRUTOR', 'HORAS_NAO_REGENCIA', 'TIPO_ATIVIDADE']
    missing_cols = [col for col in required_cols if col not in nao_regencia_df.columns]
    
    if missing_cols:
        st.warning(f"Colunas faltantes: {missing_cols}")
        return
    
    # Ranking de horas de Não Regência por instrutor
    st.subheader("🏆 Ranking de Horas de Não Regência")
    
    ranking = nao_regencia_df.groupby('INSTRUTOR')['HORAS_NAO_REGENCIA'].sum().reset_index()
    ranking = ranking.sort_values('HORAS_NAO_REGENCIA', ascending=True)
    
    fig_ranking = px.bar(
        ranking,
        x='HORAS_NAO_REGENCIA',
        y='INSTRUTOR',
        orientation='h',
        title='Horas de Não Regência por Instrutor',
        labels={'HORAS_NAO_REGENCIA': 'Horas', 'INSTRUTOR': 'Instrutor'},
        color='HORAS_NAO_REGENCIA',
        color_continuous_scale='Blues'
    )
    fig_ranking.update_layout(height=max(300, len(ranking) * 40))
    st.plotly_chart(fig_ranking, use_container_width=True)
    
    # Tabela detalhada
    st.subheader("📋 Detalhamento de Atividades")
    
    display_df = nao_regencia_df.copy()
    
    # Formata datas se existirem
    date_cols = ['DATA_INICIO', 'DATA_FIM']
    for col in date_cols:
        if col in display_df.columns:
            display_df[col] = pd.to_datetime(display_df[col], errors='coerce').dt.strftime('%d/%m/%Y')
    
    # Seleciona colunas para exibição
    cols_to_show = [col for col in ['DATA_INICIO', 'DATA_FIM', 'INSTRUTOR', 'TIPO_ATIVIDADE', 'HORAS_NAO_REGENCIA'] 
                    if col in display_df.columns]
    
    if cols_to_show:
        st.dataframe(display_df[cols_to_show], use_container_width=True)
    else:
        st.dataframe(display_df, use_container_width=True)


def render_ocupacao_ambientes(data):
    """Renderiza página Ocupação e Ambientes"""
    st.header("🏢 Ocupação e Ambientes")
    
    ocupacao_df = data.get('OCUPAÇÃO', pd.DataFrame())
    
    if ocupacao_df is None or len(ocupacao_df) == 0:
        st.warning("Nenhum dado de Ocupação disponível.")
        return
    
    # Verifica colunas necessárias
    if 'AMBIENTE' not in ocupacao_df.columns or 'PERCENTUAL_OCUPACAO' not in ocupacao_df.columns:
        st.warning("Colunas necessárias não encontradas.")
        return
    
    visao = st.selectbox(
        "Selecione a visão:",
        ["1) Visão Geral", "2) Evolução Diária", "3) Mapa de Calor"]
    )
    
    if "Visão Geral" in visao:
        st.subheader("Média de Ocupação por Ambiente")
        
        media_ambiente = ocupacao_df.groupby('AMBIENTE')['PERCENTUAL_OCUPACAO'].mean().reset_index()
        media_ambiente = media_ambiente.sort_values('PERCENTUAL_OCUPACAO', ascending=True)
        
        fig = px.bar(
            media_ambiente,
            x='PERCENTUAL_OCUPACAO',
            y='AMBIENTE',
            orientation='h',
            title='Média de Percentual de Ocupação por Ambiente',
            labels={'PERCENTUAL_OCUPACAO': 'Ocupação Média (%)', 'AMBIENTE': 'Ambiente'},
            color='PERCENTUAL_OCUPACAO',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(height=max(300, len(media_ambiente) * 40))
        st.plotly_chart(fig, use_container_width=True)
    
    elif "Evolução Diária" in visao:
        st.subheader("Evolução Diária da Ocupação")
        
        if 'DATA' not in ocupacao_df.columns:
            st.warning("Coluna DATA não encontrada.")
            return
        
        # Converte DATA para datetime
        ocupacao_df['DATA_DT'] = pd.to_datetime(ocupacao_df['DATA'], errors='coerce')
        
        # Média diária
        media_diaria = ocupacao_df.groupby('DATA_DT')['PERCENTUAL_OCUPACAO'].mean().reset_index()
        media_diaria = media_diaria.sort_values('DATA_DT')
        
        fig = px.line(
            media_diaria,
            x='DATA_DT',
            y='PERCENTUAL_OCUPACAO',
            title='Evolução Diária da Ocupação Média',
            labels={'DATA_DT': 'Data', 'PERCENTUAL_OCUPACAO': 'Ocupação Média (%)'},
            markers=True
        )
        fig.update_traces(line_shape='spline')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    elif "Mapa de Calor" in visao:
        st.subheader("Mapa de Calor de Ocupação")
        
        if 'DATA' not in ocupacao_df.columns:
            st.warning("Coluna DATA não encontrada.")
            return
        
        # Prepara matriz para heatmap
        ocupacao_df['DATA_DT'] = pd.to_datetime(ocupacao_df['DATA'], errors='coerce')
        ocupacao_df['DATA_STR'] = ocupacao_df['DATA_DT'].dt.strftime('%d/%m')
        
        # Pivot table
        pivot = ocupacao_df.pivot_table(
            values='PERCENTUAL_OCUPACAO',
            index='AMBIENTE',
            columns='DATA_STR',
            aggfunc='mean'
        )
        
        fig = px.imshow(
            pivot,
            labels={'x': 'Data', 'y': 'Ambiente', 'color': 'Ocupação (%)'},
            title='Mapa de Calor - Concentração de Ocupação',
            color_continuous_scale='YlOrRd'
        )
        fig.update_layout(height=max(400, len(pivot) * 30))
        st.plotly_chart(fig, use_container_width=True)


def render_evolucao_historica():
    """Renderiza página Evolução Histórica"""
    st.header("📈 Evolução Histórica")
    
    init_historico_dir()
    
    # Coleta todos os arquivos do histórico
    all_files = list(HISTORICO_DIR.glob("*.xlsx"))
    
    # Adiciona arquivo atual se existir
    current_file = Path("Consolidado - Status 2026.xlsx")
    if current_file.exists():
        all_files.append(current_file)
    
    if len(all_files) == 0:
        st.warning("Nenhum arquivo de histórico encontrado.")
        return
    
    # Processa cada arquivo
    historico_ocupacao = []
    historico_nao_regencia = []
    
    for file_path in all_files:
        try:
            data = load_excel_data(str(file_path))
            
            if 'OCUPAÇÃO' in data:
                df_ocup = data['OCUPAÇÃO'].copy()
                if 'DATA' in df_ocup.columns and 'PERCENTUAL_OCUPACAO' in df_ocup.columns:
                    df_ocup['DATA_DT'] = pd.to_datetime(df_ocup['DATA'], errors='coerce')
                    
                    # Extrai mês
                    df_ocup['MES'] = df_ocup['DATA_DT'].dt.to_period('M').astype(str)
                    
                    # Média mensal
                    if len(df_ocup) > 0:
                        media_mensal = df_ocup.groupby('MES')['PERCENTUAL_OCUPACAO'].mean().iloc[0]
                        historico_ocupacao.append({
                            'MES': df_ocup['MES'].iloc[0],
                            'OCUPACAO_MEDIA': media_mensal,
                            'ARQUIVO': file_path.name
                        })
            
            if 'NÃO_REGÊNCIA' in data:
                df_nr = data['NÃO_REGÊNCIA'].copy()
                if 'HORAS_NAO_REGENCIA' in df_nr.columns:
                    total_horas = df_nr['HORAS_NAO_REGENCIA'].sum()
                    
                    # Tenta extrair mês da DATA_INICIO
                    mes_ref = file_path.stem
                    if 'DATA_INICIO' in df_nr.columns:
                        df_nr['DATA_INICIO_DT'] = pd.to_datetime(df_nr['DATA_INICIO'], errors='coerce')
                        valid_dates = df_nr['DATA_INICIO_DT'].dropna()
                        if len(valid_dates) > 0:
                            mes_ref = valid_dates.min().to_period('M').astype(str)
                    
                    historico_nao_regencia.append({
                        'MES': mes_ref,
                        'HORAS_TOTAL': total_horas,
                        'ARQUIVO': file_path.name
                    })
        except Exception as e:
            st.warning(f"Erro ao processar {file_path.name}: {str(e)}")
            continue
    
    if len(historico_ocupacao) == 0 and len(historico_nao_regencia) == 0:
        st.warning("Dados históricos insuficientes para análise.")
        return
    
    # Gráfico de ocupação média mensal
    if len(historico_ocupacao) > 0:
        st.subheader("📊 Evolução da Ocupação Média Mensal")
        
        df_hist_ocup = pd.DataFrame(historico_ocupacao)
        df_hist_ocup = df_hist_ocup.sort_values('MES')
        
        fig_ocup = px.line(
            df_hist_ocup,
            x='MES',
            y='OCUPACAO_MEDIA',
            title='Ocupação Média por Mês',
            labels={'MES': 'Mês', 'OCUPACAO_MEDIA': 'Ocupação Média (%)'},
            markers=True
        )
        fig_ocup.update_traces(line_shape='spline')
        st.plotly_chart(fig_ocup, use_container_width=True)
    
    # Gráfico de horas de Não Regência
    if len(historico_nao_regencia) > 0:
        st.subheader("⏱️ Volume Total de Horas de Não Regência")
        
        df_hist_nr = pd.DataFrame(historico_nao_regencia)
        df_hist_nr = df_hist_nr.sort_values('MES')
        
        fig_nr = px.bar(
            df_hist_nr,
            x='MES',
            y='HORAS_TOTAL',
            title='Horas de Não Regência por Mês',
            labels={'MES': 'Mês', 'HORAS_TOTAL': 'Horas Totais'},
            color='HORAS_TOTAL',
            color_continuous_scale='Oranges'
        )
        st.plotly_chart(fig_nr, use_container_width=True)


def render_relatorios_detalhados(data):
    """Renderiza página Relatórios Detalhados"""
    st.header("📑 Relatórios Detalhados")
    
    tab1, tab2 = st.tabs(["Disciplinas", "Faltas"])
    
    with tab1:
        st.subheader("📚 Relatório de Disciplinas")
        
        disciplinas_df = data.get('DISCIPLINAS', pd.DataFrame())
        turmas_df = data.get('TURMAS', pd.DataFrame())
        
        if disciplinas_df is None or len(disciplinas_df) == 0:
            st.warning("Nenhum dado de Disciplinas disponível.")
        else:
            # Merge com TURMAS se possível
            if turmas_df is not None and len(turmas_df) > 0 and 'ID_TURMA' in turmas_df.columns:
                if 'ID_TURMA' in disciplinas_df.columns:
                    merged = pd.merge(
                        disciplinas_df,
                        turmas_df[['ID_TURMA', 'NOME_TURMA', 'TURNO']],
                        on='ID_TURMA',
                        how='left'
                    )
                else:
                    merged = disciplinas_df.copy()
            else:
                merged = disciplinas_df.copy()
            
            # Filtro por STATUS
            status_options = merged['STATUS'].unique().tolist() if 'STATUS' in merged.columns else []
            status_filter = st.multiselect("Filtrar por Status:", status_options, default=status_options)
            
            if status_filter and 'STATUS' in merged.columns:
                filtered = merged[merged['STATUS'].isin(status_filter)]
            else:
                filtered = merged
            
            st.dataframe(filtered, use_container_width=True)
            
            # Download CSV
            csv_data = format_dataframe_for_csv(filtered)
            st.download_button(
                label="📥 Baixar Disciplinas (CSV)",
                data=csv_data,
                file_name="disciplinas.csv",
                mime="text/csv"
            )
    
    with tab2:
        st.subheader("❌ Relatório de Faltas")
        
        faltas_df = data.get('FALTAS', pd.DataFrame())
        
        if faltas_df is None or len(faltas_df) == 0:
            st.warning("Nenhum dado de Faltas disponível.")
        else:
            # Gráfico de linha temporal
            if 'DATA_FALTA' in faltas_df.columns:
                faltas_df['DATA_FALTA_DT'] = pd.to_datetime(faltas_df['DATA_FALTA'], errors='coerce')
                
                # Conta faltas por dia
                faltas_por_dia = faltas_df.groupby('DATA_FALTA_DT').size().reset_index(name='QTD_FALTAS')
                faltas_por_dia = faltas_por_dia.sort_values('DATA_FALTA_DT')
                
                if len(faltas_por_dia) > 0:
                    fig_faltas = px.line(
                        faltas_por_dia,
                        x='DATA_FALTA_DT',
                        y='QTD_FALTAS',
                        title='Evolução de Faltas por Dia',
                        labels={'DATA_FALTA_DT': 'Data', 'QTD_FALTAS': 'Quantidade de Faltas'},
                        markers=True
                    )
                    fig_faltas.update_traces(line_shape='spline')
                    st.plotly_chart(fig_faltas, use_container_width=True)
            
            # Tabela de registro
            st.dataframe(faltas_df, use_container_width=True)
            
            # Download CSV
            csv_data = format_dataframe_for_csv(faltas_df)
            st.download_button(
                label="📥 Baixar Faltas (CSV)",
                data=csv_data,
                file_name="faltas.csv",
                mime="text/csv"
            )


def render_agenda_eventos(data, periodo_info=None):
    """Renderiza página Agenda de Eventos do Mês"""
    st.header("📅 Agenda de Eventos")
    
    calendario_df = data.get('CALENDÁRIO', pd.DataFrame())
    
    if calendario_df is None or len(calendario_df) == 0:
        st.warning("Nenhum dado de Calendário disponível.")
        return
    
    # Verifica colunas necessárias (com variações de nomes)
    possible_date_cols = ['DATA', 'DATA_EVENTO', 'DATE']
    date_col = None
    for col in possible_date_cols:
        if col in calendario_df.columns:
            date_col = col
            break
    
    if not date_col:
        st.warning("Coluna de DATA não encontrada no Calendário.")
        return
    
    # Identifica colunas disponíveis
    tipo_dia_col = None
    for col in ['TIPO_DIA', 'TIPO', 'CATEGORIA']:
        if col in calendario_df.columns:
            tipo_dia_col = col
            break
    
    descricao_col = None
    for col in ['DESCRICAO', 'DESCRIÇÃO', 'DESCRIPTION', 'EVENTO']:
        if col in calendario_df.columns:
            descricao_col = col
            break
    
    if not tipo_dia_col:
        st.warning("Coluna de TIPO_DIA não encontrada no Calendário.")
        return
    
    # Converte DATA para datetime
    try:
        calendario_df = calendario_df.copy()
        calendario_df['DATA_DT'] = pd.to_datetime(calendario_df[date_col], errors='coerce')
        calendario_df = calendario_df.dropna(subset=['DATA_DT'])
    except Exception:
        st.warning("Erro ao converter datas do Calendário.")
        return
    
    # Usa período_info se disponível, senão extrai dos dados
    if periodo_info and 'inicio' in periodo_info and 'fim' in periodo_info:
        mes_ano_exibicao = periodo_info['mes_ano']
        data_inicio = periodo_info['inicio']
        data_fim = periodo_info['fim']
        
        # FILTRA calendário pelo período dos dados reais (OCUPAÇÃO/NÃO_REGÊNCIA)
        calendario_df = calendario_df[
            (calendario_df['DATA_DT'] >= data_inicio) & 
            (calendario_df['DATA_DT'] <= data_fim)
        ]
        
        st.info(f"📊 **Período dos dados:** {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')} ({periodo_info['dias_totais']} dias)")
    else:
        # Extrai dos dados do calendário
        data_inicio = calendario_df['DATA_DT'].min()
        data_fim = calendario_df['DATA_DT'].max()
        mes_ano_exibicao = data_inicio.strftime("%B/%Y").capitalize()
    
    if len(calendario_df) == 0:
        st.warning(f"⚠️ Nenhum evento encontrado no período de {data_inicio.strftime('%d/%m')} a {data_fim.strftime('%d/%m/%Y')}.")
        st.info("💡 Dica: Verifique se a aba CALENDÁRIO contém eventos dentro do período dos dados de OCUPAÇÃO.")
        return
    
    st.subheader(f"📆 {mes_ano_exibicao}")
    
    # Filtros interativos
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tipo_dia_options = calendario_df[tipo_dia_col].dropna().unique().tolist()
        tipo_filtro = st.multiselect(
            "Tipo de Dia:",
            tipo_dia_options,
            default=tipo_dia_options
        )
    
    with col2:
        eventos_tipos = [t for t in tipo_dia_options if any(x in str(t).lower() for x in ['evento', 'visita', 'reunião', 'reuniao'])]
        mostrar_somente_eventos = st.checkbox("Mostrar apenas Eventos/Visitas/Reuniões", value=False)
    
    with col3:
        mostrar_dias_uteis = st.checkbox("Ocultar dias não úteis", value=False)
    
    # Aplica filtros
    filtered_df = calendario_df.copy()
    
    if tipo_filtro:
        filtered_df = filtered_df[filtered_df[tipo_dia_col].isin(tipo_filtro)]
    
    if mostrar_somente_eventos and eventos_tipos:
        filtered_df = filtered_df[filtered_df[tipo_dia_col].isin(eventos_tipos)]
    
    if mostrar_dias_uteis:
        if 'DIA_UTIL' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['DIA_UTIL'].astype(str).str.upper() == 'SIM']
        elif 'UTIL' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['UTIL'].astype(str).str.upper() == 'SIM']
    
    # Ordena por data
    filtered_df = filtered_df.sort_values('DATA_DT')
    
    st.divider()
    
    # KPIs do mês
    kpi_cols = st.columns(4)
    
    total_dias = len(calendario_df)
    dias_uteis = len(calendario_df[calendario_df['DIA_UTIL'].astype(str).str.upper() == 'SIM']) if 'DIA_UTIL' in calendario_df.columns else 0
    qtd_eventos = len(calendario_df[calendario_df[tipo_dia_col].astype(str).str.lower().str.contains('evento|visita|reuni', na=False)]) if tipo_dia_col else 0
    qtd_feriados = len(calendario_df[calendario_df[tipo_dia_col].astype(str).str.lower().str.contains('feriado|recesso', na=False)]) if tipo_dia_col else 0
    
    kpi_cols[0].metric("Total Dias", total_dias)
    kpi_cols[1].metric("Dias Úteis", dias_uteis)
    kpi_cols[2].metric("Eventos/Visitas/Reuniões", qtd_eventos)
    kpi_cols[3].metric("Feriados/Recessos", qtd_feriados)
    
    st.divider()
    
    # Visualização principal - Tabela de eventos
    st.subheader("📋 Lista de Eventos e Ocorrências")
    
    # Seleciona colunas para exibição
    display_cols = ['DATA_DT', tipo_dia_col]
    if descricao_col:
        display_cols.append(descricao_col)
    if 'DIA_SEMANA' in filtered_df.columns:
        display_cols.insert(1, 'DIA_SEMANA')
    if 'DIA_UTIL' in filtered_df.columns:
        display_cols.append('DIA_UTIL')
    
    display_df = filtered_df[display_cols].copy()
    
    # Renomeia colunas para exibição
    col_names = {
        'DATA_DT': 'Data',
        'DIA_SEMANA': 'Dia da Semana',
        tipo_dia_col: 'Tipo',
        'DESCRICAO': 'Descrição',
        'DESCRIÇÃO': 'Descrição',
        'EVENTO': 'Descrição',
        'DIA_UTIL': 'Dia Útil'
    }
    display_df.rename(columns={k: v for k, v in col_names.items() if k in display_df.columns}, inplace=True)
    
    # Formata data para exibição
    if 'Data' in display_df.columns:
        display_df['Data'] = display_df['Data'].dt.strftime('%d/%m/%Y')
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Gráfico de distribuição de tipos
    st.subheader("📊 Distribuição de Tipos de Dia")
    
    if tipo_dia_col and len(filtered_df) > 0:
        fig_pizza = px.pie(
            filtered_df,
            names=tipo_dia_col,
            title='Distribuição por Tipo de Dia',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pizza.update_layout(height=400)
        st.plotly_chart(fig_pizza, use_container_width=True)
    
    # Timeline visual de eventos importantes
    st.subheader("🗓️ Timeline de Eventos")
    
    eventos_importantes = calendario_df[calendario_df[tipo_dia_col].astype(str).str.lower().str.contains('evento|visita|reuni|feriado|recesso', na=False)] if tipo_dia_col else pd.DataFrame()
    
    if len(eventos_importantes) > 0:
        timeline_data = []
        for _, row in eventos_importantes.iterrows():
            tipo = str(row.get(tipo_dia_col, '')).lower()
            icon = '🔴' if 'feriado' in tipo else '🟠' if 'recesso' in tipo else '🟢' if 'evento' in tipo else '🔵' if 'visita' in tipo else '🟣' if 'reuni' in tipo else '⚪'
            descricao = row.get(descricao_col, '') if descricao_col else ''
            timeline_data.append({
                'Data': row['DATA_DT'].strftime('%d/%m'),
                'Evento': f"{icon} {row.get(tipo_dia_col, '')}: {descricao}" if descricao else f"{icon} {row.get(tipo_dia_col, '')}",
                'Tipo': row.get(tipo_dia_col, '')
            })
        
        timeline_df = pd.DataFrame(timeline_data)
        st.dataframe(timeline_df[['Data', 'Evento']], use_container_width=True, hide_index=True)
    
    # Exportação CSV
    st.divider()
    csv_data = format_dataframe_for_csv(display_df)
    st.download_button(
        label="📥 Baixar Calendário (CSV)",
        data=csv_data,
        file_name=f"calendario_{mes_ano_exibicao.replace('/', '-')}.csv",
        mime="text/csv"
    )


def handle_upload():
    """Gerencia upload de planilha"""
    st.sidebar.subheader("📤 Upload de Planilha")
    
    uploaded_file = st.sidebar.file_uploader(
        "Carregar novo .xlsx",
        type=['xlsx'],
        help="Faça upload de uma planilha com a estrutura esperada"
    )
    
    if uploaded_file is not None:
        try:
            # Salva temporariamente
            temp_path = Path("temp_upload.xlsx")
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.getvalue())
            
            # Carrega e valida
            data = load_excel_data(temp_path)
            is_valid, msg = validate_excel_structure(data)
            
            if not is_valid:
                st.sidebar.error(msg)
                os.remove(temp_path)
                return
            
            # Extrai mês dos dados
            month_str = extract_month_from_data(data.get('OCUPAÇÃO', pd.DataFrame()))
            
            # Nome do arquivo de destino
            dest_filename = f"historico_{month_str}.xlsx"
            dest_path = HISTORICO_DIR / dest_filename
            
            # Move para histórico
            init_historico_dir()
            os.rename(temp_path, dest_path)
            
            # Commit no GitHub
            repo = setup_github()
            if repo:
                with open(dest_path, 'rb') as f:
                    content = f.read()
                save_to_github(repo, dest_path, content, f"Upload de dados - {month_str}")
            
            st.sidebar.success(f"Dados salvos para {month_str}!")
            st.session_state.current_month = dest_filename
            st.rerun()
            
        except Exception as e:
            st.sidebar.error(f"Erro no upload: {str(e)}")
            if temp_path.exists():
                os.remove(temp_path)


def main():
    """Função principal do aplicativo"""
    
    # Verifica login
    if not st.session_state.logged_in:
        login_screen()
        return
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/dashboard--v1.png", width=80)
        st.title("Painel 360º")
        
        # Botão de logout
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
        
        st.divider()
        
        # Navegação de Meses
        st.subheader("📅 Selecionar Mês")
        months = get_available_months()
        
        if months:
            # Cria dicionário com caminho completo (path, nome_display, periodo_info)
            month_options = {name: (path, periodo) for path, name, periodo in months}
            selected_name = st.selectbox(
                "Mês de análise:",
                list(month_options.keys()),
                index=0
            )
            selected_file, periodo_info = month_options[selected_name]
            
            # Mostra informações do período selecionado
            if periodo_info:
                st.info(f"📊 **Período:** {periodo_info['inicio'].strftime('%d/%m/%Y')} a {periodo_info['fim'].strftime('%d/%m/%Y')} ({periodo_info['dias_totais']} dias)")
            
            if selected_file != st.session_state.get('current_file'):
                st.session_state.current_file = selected_file
                st.session_state.data_cache = {}  # Limpa cache
                st.rerun()
        else:
            st.warning("Nenhum arquivo disponível.")
            selected_file = None
            periodo_info = None
        
        st.divider()
        
        # Upload
        handle_upload()
        
        st.divider()
        
        # Menu de Páginas
        st.subheader("📊 Menu")
        page = st.radio(
            "Navegação:",
            [
                "🌐 Visão 360º",
                "👥 Análise de Docentes (RH)",
                "🏢 Ocupação e Ambientes",
                "📈 Evolução Histórica",
                "📑 Relatórios Detalhados",
                "📅 Agenda de Eventos"
            ],
            label_visibility="collapsed"
        )
    
    # Conteúdo principal
    if selected_file:
        try:
            # Carrega dados (com cache simples)
            if selected_file not in st.session_state.data_cache:
                st.session_state.data_cache[selected_file] = load_excel_data(selected_file)
            
            data = st.session_state.data_cache[selected_file]
            
            # Renderiza página selecionada
            if page == "🌐 Visão 360º":
                render_visao_360(data)
            elif page == "👥 Análise de Docentes (RH)":
                render_analise_docentes(data)
            elif page == "🏢 Ocupação e Ambientes":
                render_ocupacao_ambientes(data)
            elif page == "📈 Evolução Histórica":
                render_evolucao_historica()
            elif page == "📑 Relatórios Detalhados":
                render_relatorios_detalhados(data)
            elif page == "📅 Agenda de Eventos":
                render_agenda_eventos(data, periodo_info)
        
        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")
    else:
        st.info("👈 Selecione um mês na barra lateral ou faça upload de uma nova planilha.")
    
    # Footer
    st.divider()
    st.caption("Painel de Desempenho 360º - Digitech © 2024 | Desenvolvido com Streamlit + Pandas + Plotly")


if __name__ == "__main__":
    main()
