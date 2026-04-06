# ============================================================
# MANUAL DE INSTALAÇÃO - ESTÁGIO 1
# Painel de Desempenho 360º - Digitech
# Arquitetura Híbrida: Banco de Dados + Fallback Local
# ============================================================

## 📋 VISÃO GERAL

Este manual guia você na migração do sistema baseado em arquivos Excel/Git 
para uma arquitetura com banco de dados PostgreSQL (Supabase), mantendo o 
sistema ativo durante toda a transição ("trocar a roda do caminhão andando").

### Benefícios desta migração:
- ✅ Consultas 10x mais rápidas
- ✅ Múltiplos usuários simultâneos sem conflitos
- ✅ Histórico de auditoria completo
- ✅ Backup automático na nuvem
- ✅ Sistema continua funcionando mesmo se DB falhar (fallback)

---

## 🚀 PASSO A PASSO

### PASSO 1: Criar Conta no Supabase (5 minutos)

1. Acesse https://supabase.com
2. Clique em "Start your project" ou "Sign Up"
3. Use conta Google ou crie com email
4. **Plano Free inclui:**
   - 500MB de banco de dados
   - 50.000 requisições/mês na API
   - 1GB de armazenamento de arquivos
   - Projetos ilimitados

### PASSO 2: Criar Projeto no Supabase

1. No dashboard, clique "New Project"
2. Preencha:
   - **Name:** `Digitech-Painel`
   - **Database Password:** (guarde em local seguro!)
   - **Region:** Escolha a mais próxima (US East ou Europe)
3. Aguarde ~2 minutos para provisionamento

### PASSO 3: Obter Credenciais

1. No projeto criado, vá em **Settings** (engrenagem na sidebar)
2. Clique em **API**
3. Copie estas 3 informações:
   ```
   Project URL: https://xxxxx.supabase.co
   anon/public key: eyJhbG... (chave longa)
   service_role key: eyJhbG... (chave ainda mais longa)
   ```

### PASSO 4: Configurar Secrets no Streamlit

#### Opção A: Para desenvolvimento local (.streamlit/secrets.toml)

Crie/edit o arquivo `.streamlit/secrets.toml`:

```toml
[supabase]
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "eyJhbG..."  # Use service_role key para operações admin
```

#### Opção B: Para produção (Streamlit Cloud)

1. Vá no seu repositório GitHub
2. Settings > Secrets and variables > Actions
3. Adicione:
   - `SUPABASE_URL` = sua URL
   - `SUPABASE_KEY` = sua chave service_role

#### Opção C: Arquivo .env (para script de migração)

Crie arquivo `.env` na raiz do projeto:

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbG...
```

### PASSO 5: Executar Script SQL no Supabase

1. No dashboard do Supabase, vá em **SQL Editor** (sidebar esquerda)
2. Clique em "New Query"
3. Copie TODO o conteúdo do arquivo `migrations/001_schema_supabase.sql`
4. Cole no editor
5. Clique em "Run" ou pressione Ctrl+Enter
6. Verifique mensagem de sucesso

**O que este script faz:**
- Cria 11 tabelas normalizadas
- Cria índices para performance
- Cria triggers para atualização automática
- Cria view para consultas consolidadas

### PASSO 6: Instalar Dependências

No terminal, na pasta do projeto:

```bash
pip install -r requirements.txt
```

Ou manualmente:

```bash
pip install supabase psycopg2-binary sqlalchemy python-dotenv
```

### PASSO 7: Migrar Dados Históricos

Com os arquivos Excel já na pasta `historico_dados/`:

```bash
python migrate.py
```

**O script fará:**
- Ler todos os .xlsx da pasta historico_dados/
- Extrair mês/ano automaticamente dos dados
- Inserir cada registro nas tabelas corretas
- Registrar auditoria de cada upload
- Mostrar relatório final

**Exemplo de saída:**
```
============================================================
🚀 MIGRAÇÃO DE DADOS HISTÓRICOS - DIGITECH
============================================================
📁 3 arquivo(s) encontrado(s)
✅ Conectado ao Supabase com sucesso!

📄 Processando: Consolidado_Jan_2026.xlsx
   📅 Mês/Ano detectado: 2026-01
   ✅ Turmas migradas: 15
   ✅ Ocupação migrada: 450
   ✅ Não Regência migrada: 23
   ✅ Disciplinas migradas: 45
   ✅ Faltas migradas: 8
   ✅ Calendário migrado: 5
   ✅ Instrutores migrados: 12
   ✅ Ambientes migrados: 10

[... mais arquivos ...]

============================================================
📊 RESUMO DA MIGRAÇÃO
============================================================
✅ Sucessos: 3/3
❌ Falhas: 0
📈 Total de registros migrados: 1658

✨ Migração concluída!
```

### PASSO 8: Testar o Dashboard

Execute o Streamlit:

```bash
streamlit run app.py
```

**Verifique:**
1. Mensagem "✅ Conectado ao Supabase" aparece no topo
2. Seleção de meses carrega rapidamente
3. Todas as páginas funcionam
4. Upload de novo arquivo salva no DB E no Git

---

## 🔧 ARQUITETURA HÍBRIDA EM DETALHES

### Como funciona o fallback:

```
┌─────────────────────────────────────────┐
│         SOLICITAÇÃO DE DADOS            │
└─────────────────┬───────────────────────┘
                  │
         ┌────────▼────────┐
         │  Tentar Supabase│
         └────────┬────────┘
                  │
    ┌─────────────┴─────────────┐
    │                           │
✅ Sucesso                 ❌ Falha
    │                           │
    │                    ┌──────▼──────┐
    │                    │ Fallback:   │
    │                    │ Arquivos    │
    │                    │ Locais      │
    │                    └──────┬──────┘
    │                           │
    └─────────────┬─────────────┘
                  │
         ┌────────▼────────┐
         │  Retorna Dados  │
         └─────────────────┘
```

### Vantagens deste modelo:

1. **Zero Downtime:** Se o Supabase sair do ar, sistema continua
2. **Migração Gradual:** Pode testar antes de desligar fallback
3. **Backup Duplo:** Dados no DB + arquivos originais no Git
4. **Performance:** DB é prioritário (mais rápido)

---

## 📁 ESTRUTURA DE ARQUIVOS ATUALIZADA

```
workspace/
├── app.py                      # Dashboard principal (atualizado)
├── requirements.txt            # Dependências atualizadas
├── migrate.py                  # Script de migração (NOVO)
├── .env                        # Variáveis de ambiente (criar)
├── .streamlit/
│   └── secrets.toml           # Credenciais Supabase
├── utils/
│   └── database.py            # Módulo de conexão (NOVO)
├── migrations/
│   └── 001_schema_supabase.sql # Schema do banco (NOVO)
├── historico_dados/           # Arquivos Excel originais
└── README.md                  # Documentação
```

---

## 🔍 VERIFICAÇÃO DE PROBLEMAS COMUNS

### Problema: "Biblioteca supabase não instalada"
**Solução:**
```bash
pip install supabase
```

### Problema: "Credenciais não encontradas"
**Solução:** Verifique se `.streamlit/secrets.toml` existe e tem:
```toml
[supabase]
SUPABASE_URL = "https://..."
SUPABASE_KEY = "eyJ..."
```

### Problema: "Erro ao executar SQL"
**Solução:** 
- Verifique se copiou o script inteiro
- Execute em partes menores se necessário
- Confira permissões do usuário

### Problema: "Script migrate.py não encontra arquivos"
**Solução:**
```bash
# Verifique se pasta existe
ls historico_dados/

# Se vazia, coloque seus .xlsx lá
cp /caminho/da/planilha.xlsx historico_dados/
```

### Problema: "Dashboard lento mesmo com DB"
**Solução:**
- Reinicie o Streamlit (Ctrl+C e execute novamente)
- Limpe cache: `rm -rf ~/.streamlit/cache`
- Verifique conexão com internet (Supabase é cloud)

---

## 📊 PRÓXIMOS PASSOS (ESTÁGIO 2)

Após completar este estágio:

1. **Validar dados migrados:**
   - Compare KPIs antes/depois
   - Verifique se todos os meses aparecem

2. **Testar upload de novo arquivo:**
   - Faça upload pelo dashboard
   - Verifique no Supabase (Table Editor)

3. **Configurar backup automático:**
   - Supabase já faz backup diário automático
   - Exporte CSV mensal como backup extra

4. **Preparar Estágio 2:**
   - Implementar API FastAPI
   - Adicionar validação Pydantic
   - Criar endpoints REST

---

## 🆘 SUPORTE

### Documentação Oficial:
- Supabase: https://supabase.com/docs
- Streamlit + DB: https://docs.streamlit.io/knowledge-base/tutorials/databases

### Comunidade:
- Discord Supabase: https://discord.supabase.com
- Fórum Streamlit: https://discuss.streamlit.io

### Em caso de emergência:
Se algo der errado na migração:
1. Os arquivos Excel originais NÃO são modificados
2. O sistema volta ao modo fallback automaticamente
3. Pode reexecutar `migrate.py` quantas vezes precisar (idempotente)

---

## ✅ CHECKLIST FINAL

Antes de considerar Estágio 1 completo:

- [ ] Conta Supabase criada
- [ ] Projeto provisionado
- [ ] Credenciais salvas em secrets.toml
- [ ] Script SQL executado sem erros
- [ ] Dependências instaladas
- [ ] Script migrate.py executado com sucesso
- [ ] Dashboard carregando com "✅ Conectado ao Supabase"
- [ ] Todos os meses históricos visíveis
- [ ] Upload de novo arquivo funcionando
- [ ] Fallback testado (opcional: desconecte internet e teste)

**Parabéns! Seu sistema agora tem banco de dados profissional! 🎉**
