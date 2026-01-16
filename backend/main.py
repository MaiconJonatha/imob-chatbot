"""
London Property Agent - Backend FastAPI
Sistema de Agente de IA para imobiliárias em Londres
Usando Google Gemini
"""

import os
import re
import csv
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
import google.generativeai as genai

# Configuração
DATA_DIR = Path(__file__).parent.parent / "data"
CSV_FILE = DATA_DIR / "leads_imobiliaria.csv"

# Garantir que o diretório de dados existe
DATA_DIR.mkdir(exist_ok=True)

# Configurar Gemini
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# Configuração de email (opcional)
EMAIL_CONFIG = {
    "smtp_server": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
    "sender_email": os.environ.get("SENDER_EMAIL", ""),
    "sender_password": os.environ.get("SENDER_PASSWORD", ""),
    "recipient_email": os.environ.get("RECIPIENT_EMAIL", ""),
}


def validate_email(email: str) -> bool:
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_uk_postcode(postcode: str) -> bool:
    """Valida formato de postcode do Reino Unido"""
    # Padrão UK: AA9A 9AA, A9A 9AA, A9 9AA, A99 9AA, AA9 9AA, AA99 9AA
    pattern = r'^[A-Z]{1,2}[0-9][A-Z0-9]?\s*[0-9][A-Z]{2}$'
    return bool(re.match(pattern, postcode.upper().strip()))


def send_email_notification(lead_data: dict):
    """Envia notificação por email quando um lead é capturado"""
    if not EMAIL_CONFIG["sender_email"] or not EMAIL_CONFIG["recipient_email"]:
        print("[INFO] Email não configurado, pulando notificação")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG["sender_email"]
        msg['To'] = EMAIL_CONFIG["recipient_email"]
        msg['Subject'] = f"🏠 Novo Lead Capturado - {lead_data.get('tipo_interesse', 'N/A').upper()}"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #1a1f3d;">🏠 Novo Lead Imobiliário</h2>
            <hr style="border: 1px solid #c9a227;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px; font-weight: bold;">Nome:</td>
                    <td style="padding: 10px;">{lead_data.get('nome', 'N/A')}</td>
                </tr>
                <tr style="background: #f5f3ef;">
                    <td style="padding: 10px; font-weight: bold;">Email:</td>
                    <td style="padding: 10px;">{lead_data.get('email', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; font-weight: bold;">Interesse:</td>
                    <td style="padding: 10px;">{lead_data.get('tipo_interesse', 'N/A').upper()}</td>
                </tr>
                <tr style="background: #f5f3ef;">
                    <td style="padding: 10px; font-weight: bold;">Orçamento:</td>
                    <td style="padding: 10px;">{lead_data.get('orcamento', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; font-weight: bold;">Postcode:</td>
                    <td style="padding: 10px;">{lead_data.get('postcode', 'N/A')}</td>
                </tr>
                <tr style="background: #f5f3ef;">
                    <td style="padding: 10px; font-weight: bold;">Detalhes:</td>
                    <td style="padding: 10px;">{lead_data.get('detalhes_adicionais', 'N/A')}</td>
                </tr>
            </table>
            <hr style="border: 1px solid #c9a227;">
            <p style="color: #666; font-size: 12px;">
                Capturado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
            </p>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"])
        server.starttls()
        server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
        server.send_message(msg)
        server.quit()

        print("[INFO] Email de notificação enviado com sucesso")
        return True
    except Exception as e:
        print(f"[ERROR] Erro ao enviar email: {str(e)}")
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialização da aplicação"""
    # Criar arquivo CSV com cabeçalhos se não existir
    if not CSV_FILE.exists():
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "nome",
                "email",
                "tipo_interesse",
                "orcamento",
                "postcode",
                "detalhes_adicionais",
                "email_valido",
                "postcode_valido"
            ])
    yield


app = FastAPI(
    title="London Property Agent",
    description="Agente de IA para imobiliárias em Londres",
    version="1.0.0",
    lifespan=lifespan
)

# CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sistema de prompts para o agente
SYSTEM_PROMPT = """Você é um agente imobiliário virtual profissional e elegante, especializado no mercado imobiliário de Londres.
Seu nome é "London Property Assistant" e você trabalha para uma agência premium.

PERSONALIDADE:
- Profissional, cordial e sofisticado
- Conhecedor do mercado imobiliário londrino
- Responde sempre em português brasileiro
- Tom elegante mas acessível

OBJETIVO PRINCIPAL:
Identificar a necessidade do cliente e capturar informações essenciais para qualificar o lead.

VOCÊ DEVE IDENTIFICAR:
1. TIPO DE INTERESSE:
   - COMPRAR: Cliente quer comprar um imóvel
   - ALUGAR: Cliente quer alugar um imóvel
   - VENDER (VALUATION): Cliente quer vender seu imóvel ou saber o valor

INFORMAÇÕES OBRIGATÓRIAS A CAPTURAR:
1. Nome completo
2. E-mail (deve ser um email válido)
3. Orçamento em libras (£) - para compra/aluguel ou valor estimado para venda
4. Código Postal (Postcode) de interesse ou do imóvel (formato UK: SW1A 1AA, E14 5AB, etc.)

ESTRATÉGIA DE CONVERSA:
1. Cumprimente calorosamente e pergunte como pode ajudar
2. Identifique se o cliente quer COMPRAR, ALUGAR ou VENDER
3. Capture as informações de forma natural e conversacional
4. Forneça informações úteis sobre as áreas de Londres mencionadas
5. Quando tiver TODAS as 4 informações, confirme os dados

ÁREAS DE LONDRES QUE VOCÊ CONHECE BEM:
- Central: Mayfair, Kensington, Chelsea, Westminster, Knightsbridge
- Norte: Hampstead, Islington, Camden
- Sul: Wimbledon, Richmond, Greenwich
- Leste: Canary Wharf, Shoreditch, Stratford
- Oeste: Notting Hill, Chiswick, Ealing

FORMATO DE RESPOSTA ESPECIAL:
Quando você tiver coletado TODAS as 4 informações obrigatórias (nome, email, orçamento, postcode),
inclua no FINAL da sua resposta um bloco JSON no seguinte formato:

[LEAD_DATA]
{
    "nome": "Nome do Cliente",
    "email": "email@exemplo.com",
    "tipo_interesse": "comprar|alugar|vender",
    "orcamento": "valor em £",
    "postcode": "código postal",
    "detalhes_adicionais": "resumo da conversa"
}
[/LEAD_DATA]

IMPORTANTE:
- Seja paciente e não peça todas as informações de uma vez
- Faça perguntas naturais ao longo da conversa
- Demonstre conhecimento sobre os bairros de Londres
- Use £ para valores monetários
- Postcodes em Londres seguem o formato: SW1A 1AA, E14 5AB, W1K 7AA, etc.
- Valide se o email parece válido antes de incluir no JSON
- Valide se o postcode segue o padrão UK
"""

# Modelo Gemini
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=SYSTEM_PROMPT
)


class ChatMessage(BaseModel):
    """Modelo para mensagens do chat"""
    message: str
    conversation_history: list = []


class ChatResponse(BaseModel):
    """Modelo para resposta do chat"""
    response: str
    lead_captured: bool = False
    lead_data: Optional[dict] = None
    validation_errors: Optional[list] = None


class LeadData(BaseModel):
    """Modelo para dados do lead"""
    nome: str
    email: str
    tipo_interesse: str
    orcamento: str
    postcode: str
    detalhes_adicionais: str = ""


def extract_lead_data(response_text: str) -> Optional[dict]:
    """Extrai dados do lead da resposta"""
    try:
        if "[LEAD_DATA]" in response_text and "[/LEAD_DATA]" in response_text:
            start = response_text.index("[LEAD_DATA]") + len("[LEAD_DATA]")
            end = response_text.index("[/LEAD_DATA]")
            json_str = response_text[start:end].strip()
            return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def clean_response(response_text: str) -> str:
    """Remove o bloco JSON da resposta para exibição"""
    if "[LEAD_DATA]" in response_text:
        return response_text[:response_text.index("[LEAD_DATA]")].strip()
    return response_text


def validate_lead_data(lead_data: dict) -> tuple[bool, list]:
    """Valida os dados do lead e retorna erros"""
    errors = []

    email = lead_data.get("email", "")
    if not validate_email(email):
        errors.append(f"Email inválido: {email}")

    postcode = lead_data.get("postcode", "")
    if not validate_uk_postcode(postcode):
        errors.append(f"Postcode inválido: {postcode} (formato esperado: SW1A 1AA)")

    return len(errors) == 0, errors


def save_lead_to_csv(lead_data: dict, email_valid: bool, postcode_valid: bool):
    """Salva os dados do lead no arquivo CSV"""
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            lead_data.get("nome", ""),
            lead_data.get("email", ""),
            lead_data.get("tipo_interesse", ""),
            lead_data.get("orcamento", ""),
            lead_data.get("postcode", ""),
            lead_data.get("detalhes_adicionais", ""),
            "Sim" if email_valid else "Não",
            "Sim" if postcode_valid else "Não"
        ])


@app.post("/api/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    """Endpoint principal do chat com o agente"""
    try:
        # Construir histórico para o Gemini
        history = []

        for msg in chat_message.conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            history.append({
                "role": role,
                "parts": [msg["content"]]
            })

        print(f"[DEBUG] Enviando mensagem para Gemini: {chat_message.message}")
        print(f"[DEBUG] Histórico: {len(history)} mensagens")

        # Criar chat com histórico
        chat_session = model.start_chat(history=history)

        # Enviar mensagem
        response = chat_session.send_message(chat_message.message)
        response_text = response.text

        print(f"[DEBUG] Resposta recebida do Gemini")

        # Verificar se há dados de lead na resposta
        lead_data = extract_lead_data(response_text)
        lead_captured = False
        validation_errors = None

        if lead_data:
            # Validar dados
            email_valid = validate_email(lead_data.get("email", ""))
            postcode_valid = validate_uk_postcode(lead_data.get("postcode", ""))

            is_valid, errors = validate_lead_data(lead_data)

            if not is_valid:
                validation_errors = errors
                print(f"[WARNING] Dados com validação: {errors}")

            # Salvar lead no CSV (mesmo com erros de validação, para não perder dados)
            save_lead_to_csv(lead_data, email_valid, postcode_valid)
            lead_captured = True

            # Enviar notificação por email
            send_email_notification(lead_data)

        # Limpar resposta para exibição
        clean_text = clean_response(response_text)

        return ChatResponse(
            response=clean_text,
            lead_captured=lead_captured,
            lead_data=lead_data,
            validation_errors=validation_errors
        )

    except Exception as e:
        print(f"[ERROR] Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")


@app.get("/api/leads")
async def get_leads():
    """Retorna todos os leads capturados"""
    leads = []
    if CSV_FILE.exists():
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            leads = list(reader)
    return {"leads": leads, "total": len(leads)}


@app.get("/api/health")
async def health_check():
    """Verificação de saúde da API"""
    return {"status": "healthy", "service": "London Property Agent"}


# Painel Admin HTML
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin - London Property Agent</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        'london': {
                            'navy': '#1a1f3d',
                            'gold': '#c9a227',
                            'cream': '#f5f3ef',
                            'slate': '#64748b',
                            'charcoal': '#2d3436',
                        }
                    },
                    fontFamily: {
                        'serif': ['Playfair Display', 'serif'],
                        'sans': ['Inter', 'sans-serif'],
                    }
                }
            }
        }
    </script>
</head>
<body class="bg-london-cream font-sans min-h-screen">
    <!-- Header -->
    <header class="bg-london-navy text-white py-4 shadow-lg">
        <div class="container mx-auto px-6">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 bg-london-gold rounded-full flex items-center justify-center">
                        <svg class="w-6 h-6 text-london-navy" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z"/>
                        </svg>
                    </div>
                    <div>
                        <h1 class="font-serif text-xl font-semibold">London Property</h1>
                        <p class="text-london-gold text-xs tracking-widest uppercase">Painel de Leads</p>
                    </div>
                </div>
                <a href="/" class="text-sm hover:text-london-gold transition-colors">← Voltar ao Site</a>
            </div>
        </div>
    </header>

    <main class="container mx-auto px-6 py-8">
        <!-- Stats -->
        <div class="grid md:grid-cols-4 gap-6 mb-8">
            <div class="bg-white rounded-lg shadow-sm p-6">
                <p class="text-london-slate text-sm">Total de Leads</p>
                <p id="total-leads" class="font-serif text-3xl text-london-navy">-</p>
            </div>
            <div class="bg-white rounded-lg shadow-sm p-6">
                <p class="text-london-slate text-sm">Compradores</p>
                <p id="total-comprar" class="font-serif text-3xl text-green-600">-</p>
            </div>
            <div class="bg-white rounded-lg shadow-sm p-6">
                <p class="text-london-slate text-sm">Locatários</p>
                <p id="total-alugar" class="font-serif text-3xl text-blue-600">-</p>
            </div>
            <div class="bg-white rounded-lg shadow-sm p-6">
                <p class="text-london-slate text-sm">Vendedores</p>
                <p id="total-vender" class="font-serif text-3xl text-purple-600">-</p>
            </div>
        </div>

        <!-- Leads Table -->
        <div class="bg-white rounded-lg shadow-sm overflow-hidden">
            <div class="p-6 border-b border-gray-100">
                <div class="flex justify-between items-center">
                    <h2 class="font-serif text-xl text-london-charcoal">Leads Capturados</h2>
                    <button onclick="loadLeads()" class="bg-london-navy text-white px-4 py-2 rounded text-sm hover:bg-london-charcoal transition-colors">
                        Atualizar
                    </button>
                </div>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full">
                    <thead class="bg-london-cream">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-london-slate uppercase tracking-wider">Data</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-london-slate uppercase tracking-wider">Nome</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-london-slate uppercase tracking-wider">Email</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-london-slate uppercase tracking-wider">Interesse</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-london-slate uppercase tracking-wider">Orçamento</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-london-slate uppercase tracking-wider">Postcode</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-london-slate uppercase tracking-wider">Validação</th>
                        </tr>
                    </thead>
                    <tbody id="leads-table" class="divide-y divide-gray-100">
                        <tr>
                            <td colspan="7" class="px-6 py-8 text-center text-london-slate">Carregando...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </main>

    <script>
        async function loadLeads() {
            try {
                const response = await fetch('/api/leads');
                const data = await response.json();

                // Update stats
                document.getElementById('total-leads').textContent = data.total;

                const comprar = data.leads.filter(l => l.tipo_interesse?.toLowerCase().includes('comprar')).length;
                const alugar = data.leads.filter(l => l.tipo_interesse?.toLowerCase().includes('alugar')).length;
                const vender = data.leads.filter(l => l.tipo_interesse?.toLowerCase().includes('vender')).length;

                document.getElementById('total-comprar').textContent = comprar;
                document.getElementById('total-alugar').textContent = alugar;
                document.getElementById('total-vender').textContent = vender;

                // Update table
                const tbody = document.getElementById('leads-table');

                if (data.leads.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" class="px-6 py-8 text-center text-london-slate">Nenhum lead capturado ainda</td></tr>';
                    return;
                }

                tbody.innerHTML = data.leads.reverse().map(lead => {
                    const date = new Date(lead.timestamp).toLocaleDateString('pt-BR', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    });

                    const interestColor = {
                        'comprar': 'bg-green-100 text-green-800',
                        'alugar': 'bg-blue-100 text-blue-800',
                        'vender': 'bg-purple-100 text-purple-800'
                    }[lead.tipo_interesse?.toLowerCase()] || 'bg-gray-100 text-gray-800';

                    const emailValid = lead.email_valido === 'Sim';
                    const postcodeValid = lead.postcode_valido === 'Sim';

                    return `
                        <tr class="hover:bg-gray-50">
                            <td class="px-6 py-4 text-sm text-london-charcoal">${date}</td>
                            <td class="px-6 py-4 text-sm font-medium text-london-charcoal">${lead.nome || '-'}</td>
                            <td class="px-6 py-4 text-sm text-london-charcoal">${lead.email || '-'}</td>
                            <td class="px-6 py-4">
                                <span class="px-2 py-1 text-xs rounded-full ${interestColor}">
                                    ${lead.tipo_interesse || '-'}
                                </span>
                            </td>
                            <td class="px-6 py-4 text-sm text-london-charcoal">${lead.orcamento || '-'}</td>
                            <td class="px-6 py-4 text-sm text-london-charcoal">${lead.postcode || '-'}</td>
                            <td class="px-6 py-4 text-sm">
                                <span class="inline-flex items-center space-x-1">
                                    <span title="Email" class="${emailValid ? 'text-green-500' : 'text-red-500'}">✉️</span>
                                    <span title="Postcode" class="${postcodeValid ? 'text-green-500' : 'text-red-500'}">📍</span>
                                </span>
                            </td>
                        </tr>
                    `;
                }).join('');

            } catch (error) {
                console.error('Erro ao carregar leads:', error);
                document.getElementById('leads-table').innerHTML =
                    '<tr><td colspan="7" class="px-6 py-8 text-center text-red-500">Erro ao carregar leads</td></tr>';
            }
        }

        // Load leads on page load
        loadLeads();

        // Auto-refresh every 30 seconds
        setInterval(loadLeads, 30000);
    </script>
</body>
</html>
"""


@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    """Painel administrativo para visualizar leads"""
    return ADMIN_HTML


# Servir arquivos estáticos
frontend_path = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_path / "static"), name="static")


@app.get("/")
async def serve_frontend():
    """Serve a página principal do frontend"""
    return FileResponse(frontend_path / "templates" / "index.html")


@app.get("/landing")
async def serve_landing():
    """Serve a landing page de vendas"""
    return FileResponse(frontend_path / "templates" / "landing.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
