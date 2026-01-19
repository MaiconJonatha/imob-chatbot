/**
 * London Property Agent - Chat Widget JavaScript
 * Sistema de chat com IA para imobiliárias
 */

class PropertyChatWidget {
    constructor() {
        this.chatToggle = document.getElementById('chat-toggle');
        this.chatWindow = document.getElementById('chat-window');
        this.chatIcon = document.getElementById('chat-icon');
        this.closeIcon = document.getElementById('close-icon');
        this.chatMessages = document.getElementById('chat-messages');
        this.chatForm = document.getElementById('chat-form');
        this.chatInput = document.getElementById('chat-input');
        this.leadNotification = document.getElementById('lead-notification');

        this.conversationHistory = [];
        this.isOpen = false;
        this.isLoading = false;

        this.init();
    }

    init() {
        // Toggle chat window
        this.chatToggle.addEventListener('click', () => this.toggleChat());

        // Handle form submission
        this.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));

        // Close chat on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.toggleChat();
            }
        });
    }

    toggleChat() {
        this.isOpen = !this.isOpen;

        if (this.isOpen) {
            this.chatWindow.classList.remove('hidden');
            this.chatIcon.classList.add('hidden');
            this.closeIcon.classList.remove('hidden');
            this.chatInput.focus();
        } else {
            this.chatWindow.classList.add('hidden');
            this.chatIcon.classList.remove('hidden');
            this.closeIcon.classList.add('hidden');
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        const message = this.chatInput.value.trim();
        if (!message || this.isLoading) return;

        // Clear input
        this.chatInput.value = '';

        // Add user message to UI
        this.addMessage(message, 'user');

        // Add to conversation history
        this.conversationHistory.push({
            role: 'user',
            content: message
        });

        // Show typing indicator
        this.showTypingIndicator();
        this.isLoading = true;

        try {
            const response = await this.sendMessage(message);

            // Remove typing indicator
            this.hideTypingIndicator();

            // Add bot response to UI
            this.addMessage(response.response, 'bot');

            // Add to conversation history
            this.conversationHistory.push({
                role: 'assistant',
                content: response.response
            });

            // Show lead notification if captured
            if (response.lead_captured) {
                this.showLeadNotification();
            }

        } catch (error) {
            this.hideTypingIndicator();
            this.addMessage('Desculpe, ocorreu um erro. Por favor, tente novamente.', 'bot');
            console.error('Chat error:', error);
        }

        this.isLoading = false;
    }

    async sendMessage(message) {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                conversation_history: this.conversationHistory
            })
        });

        if (!response.ok) {
            throw new Error('Failed to send message');
        }

        return response.json();
    }

    addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex items-start space-x-2 chat-message';

        if (sender === 'user') {
            messageDiv.className += ' flex-row-reverse space-x-reverse';
            messageDiv.innerHTML = `
                <div class="w-8 h-8 bg-london-gold rounded-full flex items-center justify-center flex-shrink-0">
                    <svg class="w-4 h-4 text-london-navy" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="user-message rounded-2xl rounded-tr-none p-3 shadow-sm max-w-[80%]">
                    <p class="text-sm">${this.escapeHtml(content)}</p>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="w-12 h-12 rounded-full overflow-hidden border-2 border-london-gold flex-shrink-0">
                    <img src="https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91?w=400&h=400&fit=crop&crop=face&facepad=2" alt="Sophie" class="w-full h-full object-cover">
                </div>
                <div class="bot-message rounded-2xl rounded-tl-none p-3 shadow-sm max-w-[80%]">
                    <p class="text-sm text-london-charcoal">${this.formatMessage(content)}</p>
                </div>
            `;
        }

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'flex items-start space-x-2';
        typingDiv.innerHTML = `
            <div class="w-12 h-12 rounded-full overflow-hidden border-2 border-london-gold flex-shrink-0">
                <img src="https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91?w=400&h=400&fit=crop&crop=face&facepad=2" alt="Sophie" class="w-full h-full object-cover">
            </div>
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;

        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    showLeadNotification() {
        this.leadNotification.classList.remove('hidden');

        // Hide after 5 seconds
        setTimeout(() => {
            this.leadNotification.classList.add('hidden');
        }, 5000);
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatMessage(content) {
        // Convert line breaks to <br>
        let formatted = this.escapeHtml(content).replace(/\n/g, '<br>');

        // Bold text between **
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        return formatted;
    }
}

// Initialize chat widget when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new PropertyChatWidget();
});
