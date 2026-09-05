// ==============================================================================
// Inventory Management AI: Natural Language AI Assistant Slide-over Drawer
// ==============================================================================

const AIChatDrawer = {
  isOpen: false,
  messages: [],

  init() {
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
        const text = chip.innerText;
        document.getElementById('chat-input-text').value = text;
        this.handleSend();
      });
    });
  },

  toggleDrawer() {
    this.isOpen ? this.closeDrawer() : this.openDrawer();
  },

  openDrawer() {
    this.isOpen = true;
    const backdrop = document.getElementById('drawer-backdrop');
    backdrop.classList.add('active');
    this.renderMessages();
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
          <div style="max-width: 85%; background: ${isUser ? 'var(--brand-primary)' : 'var(--bg-card-hover)'}; color: ${isUser ? '#FFFFFF' : 'var(--text-primary)'}; border-radius: 12px; padding: 0.85rem 1rem; font-size: 0.85rem; line-height: 1.45; border: 1px solid ${isUser ? 'transparent' : 'var(--border-color)'};">
            <div style="white-space: pre-wrap;">${this.formatMarkdown(m.text)}</div>
            ${m.tamil ? `
              <div style="margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px dashed rgba(255,255,255,0.15); font-size: 0.775rem; color: var(--accent-saffron);">
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
    typingEl.style.padding = '0.5rem';
    typingEl.innerText = '🤖 Agent inspecting live database...';
    list.appendChild(typingEl);
    list.scrollTop = list.scrollHeight;

    try {
      const res = await API.post('/api/ai/chat', { query });
      typingEl.remove();

      this.messages.push({
        sender: 'ai',
        text: res.answer,
        tamil: res.tamil_summary
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
