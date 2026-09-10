// ==============================================================================
// Inventory Management AI: Natural Language AI Assistant Slide-over Drawer
// ==============================================================================

const AIChatDrawer = {
  isOpen: false,
  messages: [],
  activeProvider: null,

  async init() {
    this.messages = [
      {
        sender: 'ai',
        text: "Namaskaram! I am your Inventory AI Assistant for Sri Murugan Super Store. Ask me anything about stockout risks, replenishment quantities, supplier comparisons, or dead stock.",
        tamil: "வணக்கம்! உங்கள் கடையின் இருப்பு, மறுஆர்டர் மற்றும் விநியோகஸ்தர்கள் பற்றிய கேள்விகளை நீங்கள் கேட்கலாம்."
      }
    ];

    document.getElementById('ai-chat-trigger').addEventListener('click', () => {
      this.toggleDrawer();
    });

    document.getElementById('drawer-close-btn').addEventListener('click', () => {
      this.closeDrawer();
    });

    document.getElementById('drawer-backdrop').addEventListener('click', (e) => {
      if (e.target.id === 'drawer-backdrop') this.closeDrawer();
    });

    document.getElementById('chat-input-form').addEventListener('submit', (e) => {
      e.preventDefault();
      this.handleSend();
    });

    // Quick prompt chips
    document.querySelectorAll('.chat-prompt-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const text = chip.innerText.replace(/^[^\s]+ /, '');
        const input = document.getElementById('chat-input-text');
        if (input) {
          input.value = text;
          this.handleSend();
        }
      });
    });

    this.checkLLMStatus();
  },

  async checkLLMStatus() {
    try {
      const status = await API.get('/api/ai/llm-status');
      this.activeProvider = status;
      const textEl = document.getElementById('llm-name-text');
      if (textEl && status) {
        textEl.innerText = `${status.name} (${status.model})`;
      }
    } catch (e) {
      console.warn("Could not fetch LLM status:", e);
    }
  },

  toggleDrawer() {
    this.isOpen ? this.closeDrawer() : this.openDrawer();
  },

  openDrawer() {
    this.isOpen = true;
    const backdrop = document.getElementById('drawer-backdrop');
    backdrop.classList.add('active');
    this.renderMessages();
    this.checkLLMStatus();
    setTimeout(() => {
      document.getElementById('chat-input-text')?.focus();
    }, 200);
  },

  closeDrawer() {
    this.isOpen = false;
    const backdrop = document.getElementById('drawer-backdrop');
    backdrop.classList.remove('active');
  },

  renderMessages() {
    const list = document.getElementById('chat-messages-list');
    if (!list) return;

    list.innerHTML = this.messages.map(m => {
      const isUser = m.sender === 'user';
      return `
        <div style="display: flex; flex-direction: column; align-items: ${isUser ? 'flex-end' : 'flex-start'}; margin-bottom: 1rem;">
          <div style="max-width: 88%; background: ${isUser ? 'var(--gradient-ai-red)' : '#FFFFFF'}; color: ${isUser ? '#FFFFFF' : 'var(--text-primary)'}; border-radius: 16px; padding: 0.85rem 1.15rem; font-size: 0.85rem; line-height: 1.5; border: 1px solid ${isUser ? 'transparent' : 'var(--border-color)'}; box-shadow: 0 4px 12px rgba(0,0,0,0.04);">
            <div style="white-space: pre-wrap;">${this.formatMarkdown(m.text)}</div>
            ${m.tool_used ? `
              <div style="margin-top: 0.5rem; font-size: 0.725rem; color: #15803D; background: #DCFCE7; padding: 0.2rem 0.5rem; border-radius: 6px; display: inline-flex; align-items: center; gap: 0.35rem; font-weight: 700;">
                <span>⚡ Live Tool Executed:</span> <code>${m.tool_used}</code>
              </div>
            ` : ''}
            ${m.tamil ? `
              <div style="margin-top: 0.6rem; padding-top: 0.5rem; border-top: 1px dashed var(--border-color); font-size: 0.775rem; color: #B45309; font-weight: 600;">
                <strong>தமிழ் விளக்கம்:</strong> ${m.tamil}
              </div>
            ` : ''}
          </div>
        </div>
      `;
    }).join('');

    list.scrollTop = list.scrollHeight;
  },

  formatMarkdown(text) {
    if (!text) return '';
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/• (.*?)/g, '• $1');
  },

  async handleSend() {
    const input = document.getElementById('chat-input-text');
    const query = input.value.trim();
    if (!query) return;

    // Add user message
    this.messages.push({ sender: 'user', text: query });
    input.value = '';
    this.renderMessages();

    // Show typing state
    const list = document.getElementById('chat-messages-list');
    const typingId = 'typing-indicator';
    const typingEl = document.createElement('div');
    typingEl.id = typingId;
    typingEl.style.color = 'var(--text-muted)';
    typingEl.style.fontSize = '0.8rem';
    typingEl.style.padding = '0.5rem 1rem';
    typingEl.innerText = '🤖 AI Copilot running live database tools...';
    list.appendChild(typingEl);
    list.scrollTop = list.scrollHeight;

    try {
      const res = await API.post('/api/ai/chat', { query });
      typingEl.remove();

      this.messages.push({
        sender: 'ai',
        text: res.answer,
        tamil: res.tamil_summary,
        tool_used: res.tool_used,
        provider: res.provider,
        model: res.model
      });
      this.renderMessages();
    } catch (e) {
      typingEl.remove();
      this.messages.push({
        sender: 'ai',
        text: "Sorry, I encountered an issue querying the database. Please try again.",
        tamil: "மன்னிக்கவும், தகவல் பெறுவதில் சிக்கல் ஏற்பட்டது."
      });
      this.renderMessages();
    }
  }
};
