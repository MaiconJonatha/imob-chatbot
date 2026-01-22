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
import httpx

# Configuração
DATA_DIR = Path(__file__).parent.parent / "data"
CSV_FILE = DATA_DIR / "leads_imobiliaria.csv"

# Garantir que o diretório de dados existe
DATA_DIR.mkdir(exist_ok=True)

# API Key do Gemini
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "").strip()
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_API_KEY}"

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
    """Send email notification when a lead is captured"""
    if not EMAIL_CONFIG["sender_email"] or not EMAIL_CONFIG["recipient_email"]:
        print("[INFO] Email not configured, skipping notification")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG["sender_email"]
        msg['To'] = EMAIL_CONFIG["recipient_email"]
        msg['Subject'] = f"🏠 New Lead Captured - {lead_data.get('tipo_interesse', 'N/A').upper()}"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #1a1f3d;">🏠 New Property Lead</h2>
            <hr style="border: 1px solid #c9a227;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px; font-weight: bold;">Name:</td>
                    <td style="padding: 10px;">{lead_data.get('nome', 'N/A')}</td>
                </tr>
                <tr style="background: #f5f3ef;">
                    <td style="padding: 10px; font-weight: bold;">Email:</td>
                    <td style="padding: 10px;">{lead_data.get('email', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; font-weight: bold;">Interest:</td>
                    <td style="padding: 10px;">{lead_data.get('tipo_interesse', 'N/A').upper()}</td>
                </tr>
                <tr style="background: #f5f3ef;">
                    <td style="padding: 10px; font-weight: bold;">Budget:</td>
                    <td style="padding: 10px;">{lead_data.get('orcamento', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; font-weight: bold;">Postcode:</td>
                    <td style="padding: 10px;">{lead_data.get('postcode', 'N/A')}</td>
                </tr>
                <tr style="background: #f5f3ef;">
                    <td style="padding: 10px; font-weight: bold;">Details:</td>
                    <td style="padding: 10px;">{lead_data.get('detalhes_adicionais', 'N/A')}</td>
                </tr>
            </table>
            <hr style="border: 1px solid #c9a227;">
            <p style="color: #666; font-size: 12px;">
                Captured on: {datetime.now().strftime('%d/%m/%Y at %H:%M')}
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

        print("[INFO] Notification email sent successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {str(e)}")
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
                "whatsapp",
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
SYSTEM_PROMPT = """You are a professional and elegant virtual estate agent called Sophie, specialising in the London property market.
You work for PropertyBot, a premium AI-powered estate agency.

PERSONALITY:
- Professional, courteous and sophisticated
- Expert in the London property market
- Always respond in British English
- Elegant yet approachable tone

MAIN OBJECTIVE:
Identify the client's needs and capture essential information to qualify the lead.

YOU MUST IDENTIFY:
1. TYPE OF INTEREST:
   - BUY: Client wants to purchase a property
   - RENT: Client wants to let a property
   - SELL (VALUATION): Client wants to sell their property or get a valuation

MANDATORY INFORMATION TO CAPTURE:
1. Full name
2. Mobile number (UK format, e.g., 07700900123)
3. Email address (must be valid)
4. Budget in pounds (£) - for purchase/rental or estimated value for sale
5. Postcode of interest or property location (UK format: SW1A 1AA, E14 5AB, etc.)

CONVERSATION STRATEGY:
1. Greet warmly and ask how you can help
2. Identify whether the client wants to BUY, RENT or SELL
3. Capture information naturally through conversation
4. Provide useful information about London areas mentioned
5. When you have ALL 5 pieces of information, confirm the details

LONDON AREAS YOU KNOW WELL:
- Central: Mayfair, Kensington, Chelsea, Westminster, Knightsbridge
- North: Hampstead, Islington, Camden
- South: Wimbledon, Richmond, Greenwich
- East: Canary Wharf, Shoreditch, Stratford
- West: Notting Hill, Chiswick, Ealing

SPECIAL RESPONSE FORMAT:
When you have collected ALL 5 mandatory pieces of information (name, mobile, email, budget, postcode),
include at the END of your response a JSON block in the following format:

[LEAD_DATA]
{
    "nome": "Client Name",
    "whatsapp": "07700900123",
    "email": "email@example.com",
    "tipo_interesse": "buy|rent|sell",
    "orcamento": "value in £",
    "postcode": "postcode",
    "detalhes_adicionais": "conversation summary"
}
[/LEAD_DATA]

IMPORTANT:
- Be patient and don't ask for all information at once
- Ask natural questions throughout the conversation
- Demonstrate knowledge of London neighbourhoods
- Use £ for monetary values
- London postcodes follow the format: SW1A 1AA, E14 5AB, W1K 7AA, etc.
- Validate the email appears valid before including in JSON
- Validate the postcode follows UK format
"""

async def call_gemini_api(messages: list) -> str:
    """Chama a API do Gemini via REST"""
    payload = {
        "contents": messages,
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1024
        }
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            GEMINI_API_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code != 200:
            print(f"[ERROR] Gemini API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail=f"Gemini API error: {response.status_code}")

        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


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
    """Validate lead data and return errors"""
    errors = []

    email = lead_data.get("email", "")
    if not validate_email(email):
        errors.append(f"Invalid email: {email}")

    postcode = lead_data.get("postcode", "")
    if not validate_uk_postcode(postcode):
        errors.append(f"Invalid postcode: {postcode} (expected format: SW1A 1AA)")

    return len(errors) == 0, errors


def save_lead_to_csv(lead_data: dict, email_valid: bool, postcode_valid: bool):
    """Salva os dados do lead no arquivo CSV"""
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            lead_data.get("nome", ""),
            lead_data.get("whatsapp", ""),
            lead_data.get("email", ""),
            lead_data.get("tipo_interesse", ""),
            lead_data.get("orcamento", ""),
            lead_data.get("postcode", ""),
            lead_data.get("detalhes_adicionais", ""),
            "Yes" if email_valid else "No",
            "Yes" if postcode_valid else "No"
        ])


@app.post("/api/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    """Endpoint principal do chat com o agente"""
    try:
        # Construir histórico para o Gemini (formato REST API)
        contents = []

        for msg in chat_message.conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        # Adicionar mensagem atual
        contents.append({
            "role": "user",
            "parts": [{"text": chat_message.message}]
        })

        print(f"[DEBUG] Enviando mensagem para Gemini: {chat_message.message}")
        print(f"[DEBUG] Histórico: {len(contents)} mensagens")

        # Chamar API REST do Gemini
        response_text = await call_gemini_api(contents)

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
    return {"status": "healthy", "service": "PropertyBot"}


# Painel Admin HTML
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en-GB">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin - PropertyBot</title>
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
                        <h1 class="font-serif text-xl font-semibold">PropertyBot</h1>
                        <p class="text-london-gold text-xs tracking-widest uppercase">Leads Dashboard</p>
                    </div>
                </div>
                <a href="/" class="text-sm hover:text-london-gold transition-colors">← Back to Site</a>
            </div>
        </div>
    </header>

    <main class="container mx-auto px-6 py-8">
        <!-- Stats -->
        <div class="grid md:grid-cols-4 gap-6 mb-8">
            <div class="bg-white rounded-lg shadow-sm p-6">
                <p class="text-london-slate text-sm">Total Leads</p>
                <p id="total-leads" class="font-serif text-3xl text-london-navy">-</p>
            </div>
            <div class="bg-white rounded-lg shadow-sm p-6">
                <p class="text-london-slate text-sm">Buyers</p>
                <p id="total-comprar" class="font-serif text-3xl text-green-600">-</p>
            </div>
            <div class="bg-white rounded-lg shadow-sm p-6">
                <p class="text-london-slate text-sm">Tenants</p>
                <p id="total-alugar" class="font-serif text-3xl text-blue-600">-</p>
            </div>
            <div class="bg-white rounded-lg shadow-sm p-6">
                <p class="text-london-slate text-sm">Sellers</p>
                <p id="total-vender" class="font-serif text-3xl text-purple-600">-</p>
            </div>
        </div>

        <!-- Leads Table -->
        <div class="bg-white rounded-lg shadow-sm overflow-hidden">
            <div class="p-6 border-b border-gray-100">
                <div class="flex justify-between items-center">
                    <h2 class="font-serif text-xl text-london-charcoal">Captured Leads</h2>
                    <button onclick="loadLeads()" class="bg-london-navy text-white px-4 py-2 rounded text-sm hover:bg-london-charcoal transition-colors">
                        Refresh
                    </button>
                </div>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full">
                    <thead class="bg-london-cream">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-london-slate uppercase tracking-wider">Date</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-london-slate uppercase tracking-wider">Name</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-london-slate uppercase tracking-wider">Mobile</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-london-slate uppercase tracking-wider">Email</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-london-slate uppercase tracking-wider">Interest</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-london-slate uppercase tracking-wider">Budget</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-london-slate uppercase tracking-wider">Postcode</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-london-slate uppercase tracking-wider">Validation</th>
                        </tr>
                    </thead>
                    <tbody id="leads-table" class="divide-y divide-gray-100">
                        <tr>
                            <td colspan="8" class="px-6 py-8 text-center text-london-slate">Loading...</td>
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

                const comprar = data.leads.filter(l => l.tipo_interesse?.toLowerCase().includes('buy')).length;
                const alugar = data.leads.filter(l => l.tipo_interesse?.toLowerCase().includes('rent')).length;
                const vender = data.leads.filter(l => l.tipo_interesse?.toLowerCase().includes('sell')).length;

                document.getElementById('total-comprar').textContent = comprar;
                document.getElementById('total-alugar').textContent = alugar;
                document.getElementById('total-vender').textContent = vender;

                // Update table
                const tbody = document.getElementById('leads-table');

                if (data.leads.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="8" class="px-6 py-8 text-center text-london-slate">No leads captured yet</td></tr>';
                    return;
                }

                tbody.innerHTML = data.leads.reverse().map(lead => {
                    const date = new Date(lead.timestamp).toLocaleDateString('en-GB', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    });

                    const interestColor = {
                        'buy': 'bg-green-100 text-green-800',
                        'rent': 'bg-blue-100 text-blue-800',
                        'sell': 'bg-purple-100 text-purple-800'
                    }[lead.tipo_interesse?.toLowerCase()] || 'bg-gray-100 text-gray-800';

                    const emailValid = lead.email_valido === 'Yes';
                    const postcodeValid = lead.postcode_valido === 'Yes';

                    const interestText = {'buy': 'buying', 'rent': 'renting', 'sell': 'selling'}[lead.tipo_interesse?.toLowerCase()] || 'property';
                    const whatsappMsg = encodeURIComponent(`Hello ${lead.nome}! I hope you're well. I noticed you're interested in ${interestText} in the ${lead.postcode || 'London'} area. I'm Sophie from PropertyBot and would love to assist you. Would you be available for a quick chat?`);
                    const whatsappLink = lead.whatsapp ? `<a href="https://wa.me/44${lead.whatsapp.replace(/\\D/g,'').replace(/^0/,'')}" target="_blank" class="text-green-600 hover:underline">${lead.whatsapp}</a>` : '-';

                    const emailSubject = encodeURIComponent(`Your ${interestText} enquiry - PropertyBot`);
                    const emailBody = encodeURIComponent(`Dear ${lead.nome},\n\nI hope this email finds you well.\n\nI noticed you expressed interest in ${interestText} in the ${lead.postcode || 'London'} area with a budget of ${lead.orcamento || 'to be confirmed'}.\n\nI would be delighted to arrange a call to discuss your requirements and present our best options.\n\nWhen would be a convenient time for a chat?\n\nKind regards,\nSophie\nPropertyBot Team`);
                    const emailLink = lead.email ? `<a href="mailto:${lead.email}?subject=${emailSubject}&body=${emailBody}" class="text-red-600 hover:underline">${lead.email}</a>` : '-';

                    return `
                        <tr class="hover:bg-gray-50">
                            <td class="px-6 py-4 text-sm text-london-charcoal">${date}</td>
                            <td class="px-6 py-4 text-sm font-medium text-london-charcoal">${lead.nome || '-'}</td>
                            <td class="px-6 py-4 text-sm text-london-charcoal">${whatsappLink}</td>
                            <td class="px-6 py-4 text-sm text-london-charcoal">${emailLink}</td>
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


@app.get("/terms")
async def serve_terms():
    """Serve the Terms of Service page"""
    return FileResponse(frontend_path / "templates" / "terms.html")


@app.get("/privacy")
async def serve_privacy():
    """Serve the Privacy Policy page"""
    return FileResponse(frontend_path / "templates" / "privacy.html")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
