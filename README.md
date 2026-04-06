# Painel de Desempenho 360º - Digitech

Sistema completo de análise de desempenho educacional desenvolvido com Streamlit, Pandas e Plotly.

## Funcionalidades

### 🌐 Visão 360º
- KPIs superiores: Qtd Turmas, Total Alunos, Salas Físicas, Qtd Instrutores, Qtd Faltas
- Meta de Hora-Aluno (HA) com cálculo automático baseado em TURMAS x DISCIPLINAS
- Suporte a meta manual via `metas_ha.json`
- Progresso por turma com gráfico de barras horizontais
- Detalhamento do status das disciplinas

### 👥 Análise de Docentes (RH)
- Ranking de horas de Não Regência por instrutor
- Tabela detalhada de atividades

### 🏢 Ocupação e Ambientes
- Visão Geral: Média de ocupação por ambiente
- Evolução Diária: Gráfico de linhas com ocupação média diária
- Mapa de Calor: Matriz de concentração de ocupação

### 📈 Evolução Histórica
- Consolidação de dados de múltiplos arquivos .xlsx
- Comparativo de ocupação média mensal
- Volume total de horas de Não Regência por mês

### 📑 Relatórios Detalhados
- Disciplinas: Tabela cruzada com filtro por STATUS
- Faltas: Evolução temporal e tabela de registros
- Exportação para CSV (UTF-8-SIG, separador ;)

## Estrutura da Planilha Excel

O sistema espera as seguintes abas no arquivo .xlsx:

| Aba | Colunas Principais |
|-----|-------------------|
| TURMAS | ID_TURMA, NOME_TURMA, TURNO, VAGAS_OCUPADAS |
| OCUPAÇÃO | DATA, AMBIENTE, PERCENTUAL_OCUPACAO, TURNO |
| NÃO_REGÊNCIA | ID_INSTRUTOR, INSTRUTOR, DATA_INICIO, DATA_FIM, HORAS_NAO_REGENCIA, TIPO_ATIVIDADE |
| INSTRUTORES | ID, NOME_COMPLETO |
| DISCIPLINAS | ID_TURMA, NOME_DISCIPLINA, CARGA_HORARIA, STATUS |
| AMBIENTES | NOME_AMBIENTE, TIPO, VIRTUAL |
| FALTAS | DATA_FALTA, INSTRUTOR, MOTIVO |
| PARÂMETROS | PARÂMETRO, VALOR |

## Instalação

1. Clone o repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure os secrets no Streamlit Cloud ou localmente em `.streamlit/secrets.toml`:
```toml
GITHUB_TOKEN = "seu_token_github"
GITHUB_REPO = "usuario/repositorio"
```

## Execução

```bash
streamlit run app.py
```

## Login

Senha padrão: `admin123`

## Persistência de Dados

- **Histórico**: Arquivos .xlsx são salvos na pasta `historico_dados/`
- **Metas Manuais**: Arquivo `metas_ha.json` gerencia metas manuais de Hora-Aluno
- **GitHub**: Quando configurado, os dados são sincronizados automaticamente com o repositório

## Deploy no Streamlit Cloud

1. Conecte seu repositório GitHub ao Streamlit Cloud
2. Configure os secrets no dashboard do Streamlit
3. O deploy é automático a cada commit

## Tratamento de Erros

O sistema implementa blocos try-except robustos e verifica a existência de colunas antes de operações críticas, garantindo resiliência a variações na estrutura da planilha.
