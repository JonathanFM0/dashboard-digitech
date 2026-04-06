# 🚀 Roadmap Completo: Painel de Desempenho 360º - Digitech

## Visão Geral da Evolução

Este documento apresenta o plano completo de evolução do sistema, desde o MVP atual até uma arquitetura enterprise escalável.

---

## 📍 Estado Atual (MVP)

**Tecnologias:**
- Streamlit (Frontend)
- Pandas (Processamento de dados)
- Plotly (Visualização)
- Arquivos Excel + GitHub (Persistência)

**Limitações:**
- Leitura lenta de múltiplos arquivos
- Conflitos de merge no Git
- Sem autenticação real
- Dados não normalizados

---

## 🎯 Estágio 1: Fundação de Dados (EM ANDAMENTO)

**Status:** ✅ Códigos gerados | ⏳ Aguardando configuração

**Objetivo:** Implementar banco de dados PostgreSQL com fallback para arquivos locais.

**Entregáveis:**
| Arquivo | Status | Descrição |
|---------|--------|-----------|
| `migrations/001_schema_supabase.sql` | ✅ Pronto | Schema completo do banco |
| `utils/database.py` | ✅ Pronto | Módulo de conexão híbrida |
| `migrate.py` | ✅ Pronto | Script de migração de dados |
| `MANUAL_ESTAGIO_1.md` | ✅ Pronto | Manual passo a passo |
| `requirements.txt` | ✅ Atualizado | Novas dependências |
| `.env.example` | ✅ Pronto | Template de configuração |

**Pré-requisitos:**
- [ ] Criar conta no Supabase (5 min)
- [ ] Executar script SQL no Supabase
- [ ] Configurar credenciais em `secrets.toml`
- [ ] Executar `python migrate.py`

**Benefícios Imediatos:**
- Consultas 10x mais rápidas
- Múltiplos usuários sem conflitos
- Histórico de auditoria
- Backup automático na nuvem
- Sistema continua ativo durante migração

**Tempo Estimado:** 1-2 horas

---

## 🟡 Estágio 2: Backend Robusto (Próxima Fase)

**Objetivo:** Separar lógica de negócio em API dedicada com validação rigorosa.

**Entregáveis Planejados:**
```
backend/
├── app/
│   ├── main.py           # API FastAPI
│   ├── models.py         # Modelos SQLAlchemy
│   ├── schemas.py        # Validação Pydantic
│   ├── services.py       # Regras de negócio
│   └── routes/
│       ├── kpi.py
│       ├── upload.py
│       └── calendar.py
├── tests/
└── requirements.txt
```

**Funcionalidades:**
- API REST com documentação Swagger automática
- Validação de dados com Pydantic (schemas rígidos)
- Tratamento de erros padronizado
- Rate limiting e caching
- Logs estruturados

**Endpoints Previstos:**
- `POST /api/upload` - Upload de planilha
- `GET /api/kpis?mes=2026-01` - KPIs do mês
- `GET /api/turmas` - Lista de turmas
- `GET /api/ocupacao?mes=2026-01` - Dados de ocupação
- `PUT /api/metas-ha` - Atualizar meta manual
- `GET /api/calendario?mes=2026-01` - Agenda de eventos

**Tempo Estimado:** 2-3 semanas

---

## 🔵 Estágio 3: Autenticação e UX (Fase 3)

**Objetivo:** Profissionalizar acesso e interface do usuário.

**Funcionalidades:**
- Autenticação real (Supabase Auth ou Auth0)
- Níveis de permissão (Admin, Gestor, Viewer)
- Recuperação de senha
- Log de atividades por usuário
- UI customizada com temas
- Dashboard responsivo mobile

**Integrações:**
- Google OAuth
- Microsoft Azure AD (opcional)
- Email transacional (SendGrid free tier)

**Tempo Estimado:** 2-3 semanas

---

## 🟣 Estágio 4: Automação e Monitoramento (Fase 4)

**Objetivo:** Sistema auto-curável e proativo.

**GitHub Actions Workflows:**
```yaml
# Deploy automático
deploy.yml - Push para main → Deploy no Streamlit Cloud

# Backup diário
backup.yml - Todo dia 00:00 → Exporta DB para S3

# Validação de dados
validate.yml - Após upload → Verifica inconsistências

# Alertas
alerts.yml - Se erro crítico → Notifica no email/Slack
```

**Monitoramento:**
- Sentry (erros em tempo real)
- Uptime monitoring (UptimeRobot free)
- Métricas de performance

**Tempo Estimado:** 1-2 semanas

---

## 🟠 Estágio 5: Frontend Moderno (Opcional/Futuro)

**Objetivo:** Migrar para React se necessidade de UX avançada.

**Stack Proposta:**
- Next.js 14 (React framework)
- TypeScript
- TailwindCSS
- Recharts ou Nivo (gráficos)
- React Query (cache de dados)

**Quando considerar esta migração:**
- Necessidade de gráficos altamente customizados
- Interações complexas (drag-and-drop, tempo real)
- Múltiplas views simultâneas
- App mobile nativo futuro

**Contra-indicações:**
- Se Streamlit atende 100% das necessidades
- Equipe sem experiência em JavaScript/TypeScript
- Orçamento limitado (desenvolvimento 3x mais caro)

**Tempo Estimado:** 6-8 semanas

---

## 📊 Comparativo de Custos (Free Tier)

| Serviço | Plano Free | Limites | Adequado para |
|---------|-----------|---------|---------------|
| **Supabase** | Free | 500MB DB, 50k req/mês | ~100k registros, 10 usuários |
| **Streamlit Cloud** | Free | Repos público | Projetos open source |
| **Render** | Free | 750 hrs/mês | API pequena (dorme após inatividade) |
| **Railway** | Trial $5 | Uso conforme | Testes rápidos |
| **Vercel** | Free | 100GB banda | Frontend React |
| **MongoDB Atlas** | Free | 512MB | Alternativa NoSQL |

**Custo Total Mensal: R$ 0,00** (até ~50 usuários ativos)

---

## 🔄 Estratégia de Migração "Trocar a Roda Andando"

### Princípios:
1. **Zero Downtime:** Sistema sempre disponível
2. **Rollback Automático:** Se algo falhar, volta ao anterior
3. **Teste Progressivo:** Valida cada etapa antes de prosseguir
4. **Dados Íntegros:** Nenhuma informação é perdida

### Fluxo de Transição:

```
FASE 1: Dual Write (2 semanas)
┌─────────────┐
│   UPLOAD    │
└──────┬──────┘
       │
   ┌───▼───┐
   │ Grava │
   └───┬───┘
       │
   ┌───▼────┐
   │ Excel  │◄── Fallback ativo
   │ + Git  │
   └────────┘
       │
   ┌───▼────┐
   │ Supa-  │◄── Fonte primária
   │ base   │
   └────────┘

FASE 2: Migration Completa (após validação)
┌─────────────┐
│   UPLOAD    │
└──────┬──────┘
       │
   ┌───▼───┐
   │ Grava │
   └───┬───┘
       │
   ┌───▼────┐
   │ Supa-  │◄── Única fonte
   │ base   │
   └────────┘
       │
   ┌───▼────┐
   │ Excel  │◄── Apenas backup
   │ + Git  │
   └────────┘
```

---

## 📈 Métricas de Sucesso

### Estágio 1 (Banco de Dados):
- [ ] Tempo de carregamento < 2 segundos
- [ ] Zero erros de leitura de dados
- [ ] 100% dos dados históricos migrados
- [ ] Upload funcionando com dual write

### Estágio 2 (API):
- [ ] 99% uptime da API
- [ ] Validação rejeita dados inválidos
- [ ] Documentação Swagger acessível
- [ ] Tests cobrindo 80% do código

### Estágio 3 (Auth):
- [ ] Login funcional com Google
- [ ] Permissões respeitadas
- [ ] Recuperação de senha funcionando
- [ ] Log de auditoria completo

### Estágio 4 (Automação):
- [ ] Deploy automático em < 5 minutos
- [ ] Backup diário confirmado
- [ ] Alertas chegando em < 1 minuto
- [ ] Zero intervenção manual

---

## 🛠️ Stack Tecnológica Consolidada

### Backend:
- Python 3.11+
- FastAPI (API REST)
- SQLAlchemy (ORM)
- Pydantic (Validação)
- Supabase Client (PostgreSQL)

### Frontend:
- Streamlit (Fase atual)
- Plotly Express (Gráficos)
- Pandas (Processamento)

### Infraestrutura:
- Supabase (PostgreSQL + Auth + Storage)
- Streamlit Cloud (Hospedagem)
- GitHub Actions (CI/CD)
- Sentry (Monitoramento)

### Desenvolvimento:
- Git (Versionamento)
- VS Code (IDE)
- Docker (Containerização futura)
- pytest (Testes)

---

## 📅 Cronograma Sugerido

| Semana | Foco | Entregáveis |
|--------|------|-------------|
| 1-2 | Estágio 1 | DB configurado, dados migrados |
| 3-4 | Estágio 1 | Validação e ajustes |
| 5-7 | Estágio 2 | API FastAPI implementada |
| 8-9 | Estágio 2 | Validação e testes |
| 10-12 | Estágio 3 | Autenticação e UX |
| 13-14 | Estágio 4 | Automação e monitoramento |

**Total:** 14 semanas (~3.5 meses) para sistema enterprise completo

---

## 🎯 Próximos Passos Imediatos

### Hoje (30 minutos):
1. Ler `MANUAL_ESTAGIO_1.md`
2. Criar conta no Supabase
3. Copiar credenciais para `.streamlit/secrets.toml`

### Amanhã (1 hora):
1. Executar script SQL no Supabase
2. Rodar `python migrate.py`
3. Testar dashboard com `streamlit run app.py`

### Esta Semana:
1. Validar todos os dados migrados
2. Testar upload de novo arquivo
3. Confirmar fallback funciona
4. Marcar Estágio 1 como ✅ COMPLETO

---

## 📞 Suporte e Recursos

### Documentação:
- [Supabase Docs](https://supabase.com/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Streamlit Docs](https://docs.streamlit.io)

### Comunidades:
- Discord Supabase
- Fórum Streamlit
- GitHub Discussions

### Em Caso de Problemas:
1. Verifique logs no terminal
2. Consulte `MANUAL_ESTAGIO_1.md` seção de troubleshooting
3. Teste fallback desconectando internet
4. Reexecute migração (é idempotente)

---

**Última Atualização:** Janeiro 2026  
**Versão do Roadmap:** 2.0  
**Responsável:** Equipe de Desenvolvimento Digitech
