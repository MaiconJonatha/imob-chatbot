/**
 * London Property Agent - Widget Embed
 * Cole este script em qualquer site para adicionar o chat
 *
 * Uso:
 * <script src="https://SEU_DOMINIO/static/js/widget-embed.js"
 *         data-api-url="https://SEU_DOMINIO"
 *         data-company-name="Nome da Imobiliária"
 *         data-primary-color="#1a1f3d"
 *         data-accent-color="#c9a227">
 * </script>
 */

(function() {
    'use strict';

    // Configuração do widget
    const scriptTag = document.currentScript;
    const config = {
        apiUrl: scriptTag?.getAttribute('data-api-url') || window.location.origin,
        companyName: scriptTag?.getAttribute('data-company-name') || 'Property Assistant',
        primaryColor: scriptTag?.getAttribute('data-primary-color') || '#1a1f3d',
        accentColor: scriptTag?.getAttribute('data-accent-color') || '#c9a227',
        position: scriptTag?.getAttribute('data-position') || 'right', // 'left' ou 'right'
        agentName: scriptTag?.getAttribute('data-agent-name') || 'Sophie',
        agentPhoto: scriptTag?.getAttribute('data-agent-photo') || '/static/images/sophie-avatar.png',
        welcomeMessage: scriptTag?.getAttribute('data-welcome-message') ||
            'Hello! Welcome to PropertyBot. I\'m Sophie, your virtual assistant. How may I help you today? Are you interested in <strong>buying</strong>, <strong>renting</strong> or <strong>selling</strong> a property?'
    };

    // CSS do Widget
    const styles = `
        #lpa-widget-container * {
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
        }

        #lpa-chat-toggle {
            position: fixed;
            bottom: 24px;
            ${config.position}: 24px;
            width: 64px;
            height: 64px;
            background: ${config.primaryColor};
            border-radius: 50%;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 999998;
            border: none;
            transition: transform 0.3s, box-shadow 0.3s;
        }

        #lpa-chat-toggle:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 25px rgba(0,0,0,0.4);
        }

        #lpa-chat-toggle::after {
            content: '';
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: ${config.accentColor};
            opacity: 0.4;
            animation: lpa-pulse 2s ease-out infinite;
            z-index: -1;
        }

        @keyframes lpa-pulse {
            0% { transform: scale(1); opacity: 0.4; }
            100% { transform: scale(1.5); opacity: 0; }
        }

        #lpa-chat-toggle svg {
            width: 28px;
            height: 28px;
            fill: ${config.accentColor};
        }

        #lpa-chat-window {
            position: fixed;
            bottom: 100px;
            ${config.position}: 24px;
            width: 380px;
            max-width: calc(100vw - 32px);
            height: 500px;
            max-height: calc(100vh - 140px);
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            z-index: 999999;
            display: none;
            flex-direction: column;
            overflow: hidden;
            animation: lpa-slideUp 0.3s ease-out;
        }

        @keyframes lpa-slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        #lpa-chat-window.lpa-open {
            display: flex;
        }

        #lpa-chat-header {
            background: ${config.primaryColor};
            color: white;
            padding: 16px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        #lpa-chat-header-icon {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            overflow: hidden;
            border: 3px solid ${config.accentColor};
            flex-shrink: 0;
        }

        #lpa-chat-header-icon img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        #lpa-chat-header-text h4 {
            margin: 0;
            font-size: 16px;
            font-weight: 600;
        }

        #lpa-chat-header-text p {
            margin: 2px 0 0;
            font-size: 12px;
            color: ${config.accentColor};
        }

        #lpa-chat-close {
            margin-left: auto;
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            padding: 4px;
            opacity: 0.7;
            transition: opacity 0.2s;
        }

        #lpa-chat-close:hover {
            opacity: 1;
        }

        #lpa-chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            background: #f5f3ef;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        #lpa-chat-messages::-webkit-scrollbar {
            width: 6px;
        }

        #lpa-chat-messages::-webkit-scrollbar-thumb {
            background: ${config.accentColor};
            border-radius: 3px;
        }

        .lpa-message {
            display: flex;
            gap: 8px;
            animation: lpa-fadeIn 0.3s ease-out;
        }

        @keyframes lpa-fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .lpa-message.lpa-user {
            flex-direction: row-reverse;
        }

        .lpa-message-avatar {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            overflow: hidden;
        }

        .lpa-message.lpa-bot .lpa-message-avatar {
            border: 2px solid ${config.accentColor};
        }

        .lpa-message.lpa-bot .lpa-message-avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .lpa-message.lpa-user .lpa-message-avatar {
            background: ${config.accentColor};
        }

        .lpa-message-avatar svg {
            width: 16px;
            height: 16px;
        }

        .lpa-message.lpa-user .lpa-message-avatar svg {
            fill: ${config.primaryColor};
        }

        .lpa-message-content {
            max-width: 75%;
            padding: 10px 14px;
            border-radius: 16px;
            font-size: 14px;
            line-height: 1.4;
        }

        .lpa-message.lpa-bot .lpa-message-content {
            background: white;
            color: #2d3436;
            border-top-left-radius: 4px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }

        .lpa-message.lpa-user .lpa-message-content {
            background: ${config.primaryColor};
            color: white;
            border-top-right-radius: 4px;
        }

        .lpa-typing {
            display: flex;
            gap: 4px;
            padding: 12px 16px;
            background: white;
            border-radius: 16px;
            border-top-left-radius: 4px;
        }

        .lpa-typing span {
            width: 8px;
            height: 8px;
            background: ${config.accentColor};
            border-radius: 50%;
            animation: lpa-bounce 1.4s infinite ease-in-out;
        }

        .lpa-typing span:nth-child(1) { animation-delay: 0s; }
        .lpa-typing span:nth-child(2) { animation-delay: 0.2s; }
        .lpa-typing span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes lpa-bounce {
            0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
            40% { transform: scale(1); opacity: 1; }
        }

        #lpa-chat-input-area {
            padding: 12px;
            background: white;
            border-top: 1px solid #eee;
            display: flex;
            gap: 8px;
        }

        #lpa-chat-input {
            flex: 1;
            padding: 10px 16px;
            border: 1px solid #ddd;
            border-radius: 24px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }

        #lpa-chat-input:focus {
            border-color: ${config.accentColor};
        }

        #lpa-chat-send {
            width: 40px;
            height: 40px;
            background: ${config.primaryColor};
            border: none;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        }

        #lpa-chat-send:hover {
            background: #2d3436;
        }

        #lpa-chat-send svg {
            width: 20px;
            height: 20px;
            fill: ${config.accentColor};
        }

        #lpa-lead-notification {
            display: none;
            background: #d4edda;
            border-top: 1px solid #c3e6cb;
            padding: 10px 12px;
            font-size: 13px;
            color: #155724;
            align-items: center;
            gap: 8px;
        }

        #lpa-lead-notification.lpa-show {
            display: flex;
        }

        @media (max-width: 480px) {
            #lpa-chat-window {
                width: calc(100vw - 16px);
                height: calc(100vh - 100px);
                bottom: 80px;
                ${config.position}: 8px;
                border-radius: 12px;
            }

            #lpa-chat-toggle {
                width: 56px;
                height: 56px;
                bottom: 16px;
                ${config.position}: 16px;
            }
        }
    `;

    // HTML do Widget
    const widgetHTML = `
        <div id="lpa-widget-container">
            <button id="lpa-chat-toggle" aria-label="Open chat">
                <svg id="lpa-icon-chat" viewBox="0 0 24 24">
                    <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
                </svg>
                <svg id="lpa-icon-close" viewBox="0 0 24 24" style="display:none">
                    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                </svg>
            </button>

            <div id="lpa-chat-window">
                <div id="lpa-chat-header">
                    <div id="lpa-chat-header-icon">
                        <img src="${config.agentPhoto}" alt="${config.agentName}">
                    </div>
                    <div id="lpa-chat-header-text">
                        <h4>${config.agentName}</h4>
                        <p>Online now</p>
                    </div>
                    <button id="lpa-chat-close" aria-label="Close chat">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                        </svg>
                    </button>
                </div>

                <div id="lpa-chat-messages">
                    <div class="lpa-message lpa-bot">
                        <div class="lpa-message-avatar">
                            <img src="${config.agentPhoto}" alt="${config.agentName}">
                        </div>
                        <div class="lpa-message-content">${config.welcomeMessage}</div>
                    </div>
                </div>

                <div id="lpa-lead-notification">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="#155724">
                        <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                    </svg>
                    <span>Your details have been registered! We shall be in touch shortly.</span>
                </div>

                <div id="lpa-chat-input-area">
                    <input type="text" id="lpa-chat-input" placeholder="Type your message..." autocomplete="off">
                    <button id="lpa-chat-send" aria-label="Send message">
                        <svg viewBox="0 0 24 24">
                            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    `;

    // Injetar CSS
    const styleSheet = document.createElement('style');
    styleSheet.textContent = styles;
    document.head.appendChild(styleSheet);

    // Injetar HTML
    const container = document.createElement('div');
    container.innerHTML = widgetHTML;
    document.body.appendChild(container.firstElementChild);

    // Lógica do Chat
    class LPAChat {
        constructor() {
            this.toggle = document.getElementById('lpa-chat-toggle');
            this.window = document.getElementById('lpa-chat-window');
            this.messages = document.getElementById('lpa-chat-messages');
            this.input = document.getElementById('lpa-chat-input');
            this.sendBtn = document.getElementById('lpa-chat-send');
            this.closeBtn = document.getElementById('lpa-chat-close');
            this.notification = document.getElementById('lpa-lead-notification');
            this.iconChat = document.getElementById('lpa-icon-chat');
            this.iconClose = document.getElementById('lpa-icon-close');

            this.conversationHistory = [];
            this.isOpen = false;
            this.isLoading = false;

            this.init();
        }

        init() {
            this.toggle.addEventListener('click', () => this.toggleChat());
            this.closeBtn.addEventListener('click', () => this.toggleChat());
            this.sendBtn.addEventListener('click', () => this.sendMessage());
            this.input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.sendMessage();
            });

            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.isOpen) this.toggleChat();
            });
        }

        toggleChat() {
            this.isOpen = !this.isOpen;
            this.window.classList.toggle('lpa-open', this.isOpen);
            this.iconChat.style.display = this.isOpen ? 'none' : 'block';
            this.iconClose.style.display = this.isOpen ? 'block' : 'none';

            if (this.isOpen) {
                this.input.focus();
            }
        }

        async sendMessage() {
            const message = this.input.value.trim();
            if (!message || this.isLoading) return;

            this.input.value = '';
            this.addMessage(message, 'user');
            this.conversationHistory.push({ role: 'user', content: message });

            this.showTyping();
            this.isLoading = true;

            try {
                const response = await fetch(`${config.apiUrl}/api/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: message,
                        conversation_history: this.conversationHistory
                    })
                });

                const data = await response.json();
                this.hideTyping();

                this.addMessage(data.response, 'bot');
                this.conversationHistory.push({ role: 'assistant', content: data.response });

                if (data.lead_captured) {
                    this.showNotification();
                }
            } catch (error) {
                this.hideTyping();
                this.addMessage('I do apologise, an error occurred. Please try again.', 'bot');
            }

            this.isLoading = false;
        }

        addMessage(content, sender) {
            const div = document.createElement('div');
            div.className = `lpa-message lpa-${sender}`;

            const avatarContent = sender === 'bot'
                ? `<img src="${config.agentPhoto}" alt="${config.agentName}">`
                : '<svg viewBox="0 0 20 20"><path d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"/></svg>';

            div.innerHTML = `
                <div class="lpa-message-avatar">
                    ${avatarContent}
                </div>
                <div class="lpa-message-content">${this.formatMessage(content)}</div>
            `;

            this.messages.appendChild(div);
            this.messages.scrollTop = this.messages.scrollHeight;
        }

        formatMessage(content) {
            return content
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/\n/g, '<br>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        }

        showTyping() {
            const div = document.createElement('div');
            div.id = 'lpa-typing';
            div.className = 'lpa-message lpa-bot';
            div.innerHTML = `
                <div class="lpa-message-avatar">
                    <img src="${config.agentPhoto}" alt="${config.agentName}">
                </div>
                <div class="lpa-typing"><span></span><span></span><span></span></div>
            `;
            this.messages.appendChild(div);
            this.messages.scrollTop = this.messages.scrollHeight;
        }

        hideTyping() {
            const typing = document.getElementById('lpa-typing');
            if (typing) typing.remove();
        }

        showNotification() {
            this.notification.classList.add('lpa-show');
            setTimeout(() => this.notification.classList.remove('lpa-show'), 5000);
        }
    }

    // Inicializar quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => new LPAChat());
    } else {
        new LPAChat();
    }
})();
