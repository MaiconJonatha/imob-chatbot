# London Property Agent

Sistema de Agente de IA para imobiliárias em Londres, com backend em FastAPI e frontend elegante com widget de chat flutuante.

## Funcionalidades

- **Agente de IA Inteligente**: Identifica automaticamente se o cliente quer comprar, alugar ou vender (valuation)
- **Captura de Leads**: Coleta Nome, E-mail, Orçamento (£) e Postcode de forma conversacional
- **Widget de Chat Elegante**: Design minimalista londrino com Tailwind CSS
- **Armazenamento de Leads**: Salva todos os dados em `leads_imobiliaria.csv`

## Estrutura do Projeto

```
london-property-agent/
├── backend/
│   └── main.py              # API FastAPI com integração Claude
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css   # Estilos customizados
│   │   └── js/
│   │       └── chat.js      # Lógica do widget de chat
│   └── templates/
│       └── index.html       # Página principal
├── data/
│   └── leads_imobiliaria.csv # Arquivo de leads (criado automaticamente)
├── requirements.txt
├── .env.example
└── README.md
```

## Instalação

1. **Clone o repositório e entre na pasta:**
   ```bash
   cd london-property-agent
   ```

2. **Crie um ambiente virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate     # Windows
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure a API Key do Anthropic:**
   ```bash
   export ANTHROPIC_API_KEY="sua_chave_api_aqui"
   ```

   Ou crie um arquivo `.env`:
   ```
   ANTHROPIC_API_KEY=sua_chave_api_aqui
   ```

## Execução

```bash
cd backend
python main.py
```

Ou usando uvicorn diretamente:
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Acesse: http://localhost:8000

## API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/chat` | Envia mensagem para o agente |
| GET | `/api/leads` | Lista todos os leads capturados |
| GET | `/api/health` | Verifica status da API |

## Fluxo de Conversação

1. O agente cumprimenta o usuário
2. Identifica a intenção: **Comprar**, **Alugar** ou **Vender**
3. Captura informações de forma natural:
   - Nome completo
   - E-mail
   - Orçamento em £
   - Código Postal (Postcode)
4. Quando todas as informações são coletadas, salva automaticamente no CSV

## Exemplo de Lead Capturado

```csv
timestamp,nome,email,tipo_interesse,orcamento,postcode,detalhes_adicionais
2024-01-15T10:30:00,João Silva,joao@email.com,comprar,£500000,SW1A 1AA,Interessado em apartamento de 2 quartos em Westminster
```

## Personalização

### Cores (Tailwind)
- `london-navy`: #1a1f3d (Azul marinho principal)
- `london-gold`: #c9a227 (Dourado elegante)
- `london-cream`: #f5f3ef (Creme de fundo)
- `london-charcoal`: #2d3436 (Texto escuro)

### Áreas de Londres
O agente conhece as principais áreas:
- Central: Mayfair, Kensington, Chelsea, Westminster
- Norte: Hampstead, Islington, Camden
- Sul: Wimbledon, Richmond, Greenwich
- Leste: Canary Wharf, Shoreditch
- Oeste: Notting Hill, Chiswick

## Licença

MIT License
