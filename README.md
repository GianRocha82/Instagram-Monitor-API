# Instagram Monitor API

API localhost para raspagem e monitoramento de perfis estratégicos no Instagram. Desenvolvida com FastAPI, Instaloader e interface web integrada.

## Visão Geral

Esta API automatiza a coleta de dados de perfis do Instagram para análise de engajamento, compatibilidade temática e geração de relatórios em Excel com dashboards interativos. Foi projetada para:

- **Empresas/agências** que precisam avaliar perfis para parcerias e campanhas
- **Pesquisadores** que analisam dinâmicas de engajamento e temáticas no Instagram
- **Gestores de social media** que monitoram concorrentes e influenciadores

---

## Arquitetura do Projeto

```
instagram_monitor_api/
├── app/
│   ├── main.py              # FastAPI application + endpoints
│   ├── models.py            # Pydantic models + configurações
│   ├── scraper.py           # Lógica de raspagem com Instaloader
│   ├── excel_generator.py   # Geração de Excel multi-abas
│   ├── dashboard_analytics.py # Métricas e preparação de dashboards
│   └── __init__.py
├── frontend/
│   └── index.html           # Interface web single-page
├── data/                    # Arquivos Excel gerados
├── venv/                    # Ambiente virtual Python
├── requirements.txt         # Dependências
├── start.sh                 # Script de inicialização (Linux/macOS)
├── start.bat                # Script de inicialização (Windows)
├── start_api.bat            # Inicialização direta com hot-reload
├── test_payload.json        # Exemplo de payload para testes
├── dashboard_fc_horacio.html           # Dashboard standalone (dados embutidos @midiabeijaflor + @fc_horacio)
├── embedded_data.json       # Dados embutidos no dashboard (JSON)
└── GUIA_EXEMPLO_MIDIABEIJAFLOR_FC_HORACIO.pdf  # Guia passo a passo com exemplo
```

---

## Pré-requisitos

- **Python 3.10+**
- **Conta no Instagram** (opcional, para perfis privados)
- **Git** (para clonar/atualizar)

---

## Instalação

### Opção 1: Script Automático (Recomendado)

**Windows:**
```cmd
start.bat
```

**Linux/macOS:**
```bash
chmod +x start.sh
./start.sh
```

Os scripts:
1. Verificam Python instalado
2. Criam/ativam ambiente virtual (`venv/`)
3. Instalam dependências do `requirements.txt`
4. Iniciam o servidor em `http://localhost:8000`

### Opção 2: Manual

```bash
# 1. Criar ambiente virtual
python -m venv venv

# 2. Ativar
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# 4. Iniciar servidor
python -m app.main
```

### Opção 3: Desenvolvimento (Hot-reload)

```bash
# Windows:
start_api.bat

# Ou direto:
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Como Usar

### 1. Acessar a Interface

Abra o navegador em: **http://localhost:8000**

A interface carrega automaticamente com:
- Formulário de configuração (6 passos)
- Seletores de modo de coleta
- Área de acompanhamento de progresso
- Dashboard de resultados

### 2. Configurar o Monitoramento

#### Campos Obrigatórios

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| **URL da Empresa Contratante** | Perfil base para comparação temática (coletam-se os **primeiros 25 posts** para base temática) | `https://www.instagram.com/midiabeijaflor/` |
| **Perfis a Monitorar** | Lista de perfis estratégicos (mín. 1) | `https://www.instagram.com/fc_horacio/` |
| **Caminho de Saída** | Pasta onde salvar os arquivos Excel | `C:\Dados\Instagram` ou `/home/user/dados` |

#### Configurações Opcionais

| Configuração | Opções | Padrão | Descrição |
|-------------|--------|--------|-----------|
| **Período de Análise** | 30, 90, 180 dias | 30 dias | Janela temporal dos posts coletados |
| **Modo de Coleta** | Público / Privado | Público | "Privado" exige login no Instagram |
| **Modo de Monitoramento** | Único / Semanal 30 dias | Único | "Semanal" agenda coletas recorrentes |

#### Credenciais (Apenas Modo Privado)

Se escolher "Coleta Privada":
- **Username Instagram**: Seu usuário de login
- **Senha Instagram**: Sua senha (não salva, usada apenas para criar sessão)

> ⚠️ **Importante**: A API salva o arquivo de sessão (`~/.instaloader_sessions/usuario.session`) para reutilizar o login. Não compartilhe esse arquivo.

### 3. Iniciar Coleta

Clique em **"Iniciar Monitoramento"**. O processo roda em background e mostra progresso em tempo real:

```
Etapa 1/4: Coletando dados da empresa contratante (primeiros 25 posts)... (25%)
Etapa 2/4: Coletando @perfil1 (período selecionado)... (45%)
Etapa 3/4: Coletando @perfil2 (período selecionado)... (65%)
Etapa 4/4: Gerando relatórios e dashboards... (85%)
Concluído! (100%)
```

### 4. Visualizar Resultados

Após conclusão, o dashboard mostra:
- **Taxa de Engajamento** calculada: (likes + comments + shares + saves) / seguidores × 100
- **Top 5 Categorias** temáticas por interações
- **Timeline** de interações (mensal/trimestral/anual)
- **Score de Compatibilidade** com a empresa (0-100%)
- **Top 20 Hashtags** por frequência e engajamento
- **Evolução de Hashtags** (stacked area chart)
- **Insights Automáticos** baseados nos dados
- **Veredito Final** (Recomendado / Considerar com Ressalvas / Não Recomendado)

Botão **"Baixar Excel"** disponível no header do dashboard.

---

## Dashboard Standalone (Acesso Rápido)

Arquivo: **`dashboard_fc_horacio.html`**

Abre direto no navegador (duplo clique) — **não precisa do servidor rodando**. Contém dados embutidos de exemplo:
- **@midiabeijaflor** (perfil base - empresa contratante): 25 posts, 1.808 seguidores
- **@fc_horacio** (perfil estratégico - influenciador): 97 posts, 48.595 seguidores

Permite alternar entre perfis e filtrar por período (todo período / 1 mês / 3 meses / 6 meses / 1 ano).

---

## Exemplo Prático: @midiabeijaflor (Empresa) vs @fc_horacio (Estratégico)

### Contexto
Empresa de mídia local (**@midiabeijaflor** — Beija-Flor Mídia, Várzea do Poço/BA) avalia parceria com influenciador de futebol amador (**@fc_horacio** — Horácio F Amador, cobertura estadual do Intermunicipal BA).

### Dados Coletados

| Métrica | @midiabeijaflor (Empresa) | @fc_horacio (Estratégico) |
|---------|---------------------------|----------------------------|
| Seguidores | 1.808 | 48.595 |
| Posts analisados | 25 (últimos 25 posts) | 97 (90 dias) |
| Taxa de Engajamento | ~2.1% | **1.01%** (média) |
| Temática principal | Esportes (84% posts) | **Esportes (97.8% interações)** |
| Top 5 Hashtags | #radiobeijaflor, #varzeadopoço, #futebol, #serrolandia, #futebolvarzea | #futebolbaiano, #futebolamador, #fc_horacio, #intermunicipal, #intermunicipal2026 |
| Foco geográfico | Várzea do Poço - BA (município) | Bahia inteira (Intermunicipal) |

### Análise de Compatibilidade

- **Score**: **14.0%** (baixa compatibilidade)
- **Categorias (60%)**: 22% similaridade — ambos "esportes", mas subcategorias diferentes
- **Hashtags (40%)**: 2.1% similaridade — vocabulários quase disjuntos
- **Interpretação**: Embora ambos cubram futebol, a empresa foca em **rádio local + várzea municipal** enquanto o influenciador cobre **campeonato intermunicipal estadual**. Audiências geográficas e linguísticas distintas.

### Insights Gerados

1. ❌ **Baixa compatibilidade (14%)** — temáticas divergentes apesar de ambos serem "esportes"
2. 📊 **Engajamento médio (1.01%)** — 490 interações/post, típico para micro-influenciador esportivo regional
3. 🎯 **Concentração temática extrema (97.8%)** — quase todas interações em "esportes"
4. 📈 **Volume sólido (47.511 interações/90 dias)** — audiência ativa e consistente
5. 🗺️ **Desalinhamento geográfico** — empresa: Várzea do Poço (centro-norte BA); influenciador: Bahia toda
6. 💡 **Recomendação**: Não recomendado para parceria direta. Buscar micro-influenciadores da região sisaleira/centro-norte com hashtags #radiobeijaflor, #varzeadopoço, #futebolvarzea

### Veredito Final

**❌ NÃO RECOMENDADO** — Baixa compatibilidade (14%) apesar de ambos focarem em futebol. O fit estratégico é fraco: audiências, linguagens (hashtags) e alcance geográfico divergem. A taxa de engajamento de 1.01% é adequada ao nicho, mas não compensa a falta de alinhamento. Recomenda-se buscar criadores locais de Várzea do Poço/região sisaleira com sobreposição de hashtags.

### Dashboard Gerado

Arquivo: `data/fc_horacio/Dashboard_fc_horacio.html` (abre direto no navegador)

- KPIs: Taxa de Engajamento (1.01%), Compatibilidade (14%), Total Interações (47.5k), Concentração Temática (97.8%)
- Gráficos: Top 5 Temáticas (pizza), Top 5 Hashtags (barras), Top 5 Hashtags no Tempo (linhas), Timeline Interações (linha Mês/Trimestre/Ano)
- Tabela comparativa empresa vs estratégico
- 5 Insights + Veredito Final

---

## Estrutura dos Arquivos Excel Gerados

Cada perfil monitorado gera um arquivo: `{perfil}_{periodo}_{data}.xlsx` com **4 abas**:

### Aba 1: Postagens

| Coluna | Descrição |
|--------|-----------|
| `id_perfil` | ID numérico do perfil no Instagram |
| `nome_perfil` | Username (@perfil) |
| `id_postagem` | ID único do post (mediaid) |
| `data_postagem` | Data/hora no fuso de Brasília (YYYY-MM-DD HH:MM:SS) |
| `tipo_postagem` | `image`, `video` ou `carousel` |
| `legenda_postagem` | Texto completo da legenda |
| `numero_likes` | Curtidas |
| `numero_views` | Visualizações (vídeos/reels) |
| `numero_republicado` | Compartilhamentos (shares) |
| `numero_compartilhamento` | Salvamentos (saves) |
| `numero_comentarios` | Comentários |
| `hashtags` | Lista de hashtags em minúsculas, separadas por vírgula |

### Aba 2: Hashtags

Matriz binária: cada linha = post, cada coluna `hashtag_N` = hashtag do ranking global (ordenada por frequência). Valor = hashtag se presente no post, vazio se ausente.

### Aba 3: Conteúdo

| Coluna | Descrição |
|--------|-----------|
| `id_perfil` | ID do perfil |
| `id_postagem` | ID do post |
| `tematica_conteudo` | Categoria classificada |

### Aba 4: Metadados

Informações do perfil analisado, empresa contratante, período, data da coleta e estatísticas resumidas.

---

## Sistema de Categorização de Conteúdo

O scraper classifica automaticamente cada post em **12 categorias** baseadas em palavras-chave nas legendas e hashtags:

| Categoria | Palavras-chave Principais |
|-----------|---------------------------|
| **notícias** | notícia, jornal, política, governo, eleição, oficial, comunicado |
| **esportes** | futebol, campeonato, jogo, gol, vitória, time, estádio, torcida |
| **curiosidades** | curiosidade, sabia, fato, estranho, incrível, ciência, descoberta |
| **festas** | festa, show, carnaval, natal, formatura, casamento, festival, arraial |
| **cultura** | cultura, arte, museu, teatro, cinema, livro, música, dança, patrimônio |
| **religião** | igreja, missa, culto, deus, jesus, bíblia, fé, pastor, padre, oração |
| **educação** | escola, universidade, curso, professor, aluno, educação, enem, vestibular |
| **saúde** | saúde, hospital, médico, vacina, tratamento, prevenção, exame, campanha |
| **economia** | economia, emprego, vaga, empresa, comércio, mercado, investimento, banco |
| **turismo** | turismo, viagem, hotel, praia, serra, passeio, gastronomia, roteiro |
| **meio ambiente** | natureza, floresta, rio, preservação, sustentabilidade, reciclagem, biodiversidade |
| **segurança** | polícia, bombeiro, segurança, crime, roubo, prisão, justiça, delegacia |
| **infraestrutura** | obra, construção, asfalto, ponte, saneamento, energia, transporte, internet |

**Lógica**: Conta ocorrências de palavras-chave por categoria; a maior pontuação define a categoria. Se nenhuma palavra-chave casa → `"outros"`.

---

## Métricas Calculadas

### Taxa de Engajamento

```
Engajamento = (Σ likes + comments + shares + saves) / n_posts
Taxa (%) = (Engajamento / Seguidores) × 100
```

### Score de Compatibilidade (0-100%)

Combina similaridade temática entre empresa e perfil monitorado:
- **60% Categorias** (Jaccard ponderado por frequência)
- **40% Hashtags** (Jaccard ponderado por frequência)

| Score | Interpretação |
|-------|---------------|
| ≥ 70% | Alta compatibilidade — forte alinhamento temático |
| 40-69% | Moderada — alinhamento parcial, avaliar nichos |
| < 40% | Baixa — temáticas divergentes |

---

## Endpoints da API (Para Integração)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/` | Interface web |
| `POST` | `/api/start-monitoring` | Inicia job de monitoramento |
| `GET` | `/api/job/{job_id}` | Status do job (progresso, resultado, erro) |
| `GET` | `/api/dashboard/{profile}` | Dados do dashboard (JSON) |
| `GET` | `/api/download/{profile}` | Download do arquivo Excel |
| `GET` | `/api/list-profiles` | Lista perfis com dados salvos |
| `GET` | `/health` | Health check |

### Exemplo: Iniciar via API

```bash
curl -X POST "http://localhost:8000/api/start-monitoring" \
  -H "Content-Type: application/json" \
  -d '{
    "company_url": "https://www.instagram.com/midiabeijaflor/",
    "profiles": ["https://www.instagram.com/fc_horacio/"],
    "time_range": "90",
    "collection_mode": "public",
    "monitoring_mode": "once",
    "output_path": "C:/Dados/Instagram"
  }'
```

Resposta:
```json
{"job_id": "a1b2c3d4", "status": "started"}
```

Acompanhar:
```bash
curl "http://localhost:8000/api/job/a1b2c3d4"
```

---

## Limitações e Considerações

### Rate Limiting do Instagram

- Instaloader respeita limites, mas coletas grandes podem ser lentas
- Modo público: ~100-200 posts/minuto
- Modo privado (logado): limites mais altos, mas risco de bloqueio temporário

### Perfis Privados

- Exigem login válido
- A API cria sessão persistente (`~/.instaloader_sessions/`)
- Use conta dedicada, não a principal

### Dados Não Disponíveis via API Pública

- **Shares** (compartilhamentos reais) — sempre 0
- **Saves** (salvamentos) — sempre 0
- **Alcance/Impressões** — não expostos
- **Dados demográficos da audiência** — não disponíveis

### Monitoramento Semanal

Atualmente **simulado** (marca como configurado). Para produção, implementar com:
- `APScheduler` ou `cron` no servidor
- Persistência de jobs (Redis/PostgreSQL)
- Notificações (e-mail, webhook, Telegram)

---

## Solução de Problemas

### Erro: "ProfileNotExistsException"

- Perfil não existe ou username errado
- Verifique a URL (use `instagram.com/username`, não `instagram.com/@username`)

### Erro: "LoginRequiredException"

- Perfil é privado e modo está em "Público"
- Mude para "Coleta Privada" e forneça credenciais válidas

### Erro: "TooManyRequests" / 429

- Instagram bloqueou temporariamente
- Aguarde 15-60 minutos
- Considere usar proxy ou reduzir frequência

### Arquivo Excel não abre

- Verifique se `openpyxl` está instalado
- Tente abrir com LibreOffice/Google Sheets se Excel der erro

### Interface não carrega

- Verifique se `frontend/index.html` existe
- Limpe cache do navegador (Ctrl+Shift+R)
- Confira console do navegador (F12) para erros JS

---

## Estrutura de Dados (Modelos Pydantic)

### ProfileInput (Request)

```python
company_url: HttpUrl
profiles: List[HttpUrl]          # min 1
time_range: TimeRange            # "30" | "90" | "180"
collection_mode: CollectionMode  # "private" | "public"
monitoring_mode: MonitoringMode  # "once" | "weekly"
output_path: str                 # pasta de saída
instagram_username: Optional[str]
instagram_password: Optional[str]
```

### PostData (Response)

```python
shortcode: str
post_id: int
date_utc: datetime
date_br: str           # "YYYY-MM-DD HH:MM:SS" (UTC-3)
is_video: bool
typename: str          # "GraphImage" | "GraphVideo" | "GraphSidecar"
post_type: str         # "image" | "video" | "carousel"
caption: str
likes: int
comments: int
views: int
shares: int            # sempre 0 (API pública)
saves: int             # sempre 0 (API pública)
hashtags: List[str]    # minúsculas
category: str          # uma das 12 categorias + "outros"
url: str               # "https://www.instagram.com/p/{shortcode}/"
```

---

## Desenvolvimento

### Rodar Testes

```bash
# Criar payload de teste
cat > test_payload.json << 'EOF'
{
  "company_url": "https://www.instagram.com/midiabeijaflor/",
  "profiles": ["https://www.instagram.com/fc_horacio/"],
  "time_range": "90",
  "collection_mode": "public",
  "monitoring_mode": "once",
  "output_path": "./data"
}
EOF

# Testar endpoint
curl -X POST http://localhost:8000/api/start-monitoring \
  -H "Content-Type: application/json" \
  -d @test_payload.json
```

### Adicionar Novas Categorias

Edite `app/scraper.py` → dicionário `CATEGORIES` (linha 17-100). Mantenha chaves em minúsculas, valores como lista de strings minúsculas.

### Estender Métricas

Adicione funções em `app/dashboard_analytics.py` e inclua no `DashboardData` model (`app/models.py`).

---

## Licença

Uso interno / acadêmico. Respeite os Termos de Uso do Instagram e a LGPD ao coletar e processar dados.

---

## Contato / Suporte

Para dúvidas sobre a implementação, consulte o código-fonte em `app/` — cada módulo tem docstrings explicativas.

**Arquivos de apoio:**
- `GUIA_EXEMPLO_MIDIABEIJAFLOR_FC_HORACIO.pdf` — Passo a passo detalhado com capturas de tela do exemplo @midiabeijaflor/@fc_horacio
- `dashboard_fc_horacio.html` — Dashboard standalone com dados de exemplo embutidos
- `embedded_data.json` — JSON com dados brutos para referência