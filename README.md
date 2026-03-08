# SEBRAE Scraper

Um web scraper em Python que monitora páginas de publicações do SEBRAE em busca de nomes específicos em documentos PDF e envia notificações por email quando correspondências são encontradas.

## Funcionalidades

- Web scraping automatizado de páginas de publicações do SEBRAE
- Análise de conteúdo de PDFs e extração de texto
- Notificações por email quando nomes especificados são detectados
- Rastreamento de URLs para evitar verificações duplicadas
- Containerização Docker para fácil implantação
- Gerenciamento de estado persistente

## Pré-requisitos

- Python 3.12+
- Docker e Docker Compose (para deployment em container)
- Conta Gmail com App Password habilitado

## Início Rápido

### Setup Local de Desenvolvimento

1. Clone o repositório:
```bash
git clone https://github.com/dssantos/scraper-convocacao-sebrae.git
cd scraper-convocacao-sebrae
```

2. Crie um ambiente virtual:
```bash
python3 -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite .env com suas credenciais
```

5. Execute o scraper:
```bash
python sebrae_scraper.py
```

### Deployment com Docker

1. Clone o repositório e navegue até o diretório do projeto

2. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite .env com suas credenciais
```

3. Build e execução com Docker Compose:
```bash
docker-compose build
docker-compose run --rm sebrae-scraper
```

4. Visualize os logs:
```bash
docker-compose logs
```

## Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` com as seguintes variáveis:

- `GOOGLE_EMAIL`: Seu endereço Gmail para enviar notificações
- `GOOGLE_APP_PASSWORD`: Senha de App do Gmail (não é sua senha normal)

### Configurando Gmail App Password

1. Acesse [Configurações da Conta Google](https://myaccount.google.com/security)
2. Habilite a Verificação em duas etapas, se ainda não estiver habilitada
3. Vá em Segurança > Senhas de app
4. Gere uma nova senha de app para "Mail"
5. Copie a senha para seu arquivo `.env`

### Customização

Edite `sebrae_scraper.py` para modificar:
- `name` (linha 97): O nome a ser procurado
- `url` (linha 98): A página do SEBRAE a ser monitorada

## Agendamento

O scraper foi projetado para execução manual. Para execução periódica, use o cron do host:

### Opção 1: Crontab (Recomendado)
```bash
# Editar crontab
crontab -e

# Adicionar linha para executar a cada 6 horas
0 */6 * * * cd /path/to/scraper-convocacao-sebrae && docker-compose run --rm sebrae-scraper
```

### Opção 2: Execução Direta
```bash
# Executar uma vez
docker-compose run --rm sebrae-scraper
```

## Testes

O projeto inclui uma suíte de testes completa usando pytest.

### Executar Testes Localmente

1. Instale as dependências de desenvolvimento:
```bash
pip install -r requirements.txt
```

2. Execute todos os testes:
```bash
pytest tests/ -v
```

3. Execute testes com coverage:
```bash
pytest tests/ -v --cov=sebrae_scraper --cov-report=term-missing
```

4. Execute relatório HTML de coverage:
```bash
pytest tests/ --cov=sebrae_scraper --cov-report=html
# Abra htmlcov/index.html no navegador
```

### Executar Testes no Docker

```bash
# Build a imagem
docker-compose build

# Execute os testes no container
docker-compose run --rm sebrae-scraper pytest tests/ -v
```

### Estrutura dos Testes

- `test_utils.py`: Testes unitários para funções de utilidade (load_checked_data, save_checked_data, is_checked)
- `test_scraper.py`: Testes unitários para funções de scraping com mocks
- `test_integration.py`: Testes de integração para o fluxo completo

## Estrutura do Projeto

```
scraper-convocacao-sebrae/
├── sebrae_scraper.py       # Script principal do scraper
├── requirements.txt         # Dependências Python
├── pytest.ini              # Configuração do pytest
├── Dockerfile              # Configuração da imagem Docker
├── docker-compose.yml      # Orquestração Docker
├── .env.example            # Template de variáveis de ambiente
├── .gitignore              # Regras de ignorar do Git
├── .dockerignore           # Regras de ignorar do Docker
├── tests/                  # Suíte de testes
│   ├── __init__.py
│   ├── conftest.py         # Fixtures e configuração
│   ├── test_utils.py       # Testes de utilitários
│   ├── test_scraper.py     # Testes do scraper
│   └── test_integration.py # Testes de integração
├── checked_urls.json       # Estado persistente (gerado automaticamente)
└── README.md               # Este arquivo
```

## Dependências

- `requests`: Biblioteca HTTP para web scraping
- `lxml`: Processamento de XML e HTML
- `pypdf`: Extração de texto de PDFs
- `python-decouple`: Gerenciamento de variáveis de ambiente

## Como Funciona

1. Busca links de publicações na página do SEBRAE
2. Baixa e analisa arquivos PDF de cada publicação
3. Procura pelo nome especificado no conteúdo do PDF
4. Envia notificação por email se o nome for encontrado
5. Rastreia URLs verificadas para evitar processamento duplicado
