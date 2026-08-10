// Client-side AI Chatbot synchronization logic

document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById('ai-chat-form');
    const chatInput = document.getElementById('ai-chat-input');
    const messagesDiv = document.getElementById('ai-chat-messages');
    const tokenIdInput = document.getElementById('ai-token-id');
    
    function appendMessage(sender, text, isError = false) {
        if (!messagesDiv) return;
        const msg = document.createElement('div');
        msg.className = `p-3 rounded-xl border ${sender === 'user' ? 'bg-brand-950/20 border-brand-900/40 text-brand-300' : isError ? 'bg-red-950/30 border-red-900/40 text-red-400' : 'bg-slate-900/60 border-slate-850 text-slate-300'}`;
        msg.innerHTML = `<strong>${sender === 'user' ? 'You' : 'WaitWise AI'}:</strong><p class="mt-1 leading-relaxed whitespace-pre-wrap">${text}</p>`;
        messagesDiv.appendChild(msg);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
    
    if (chatForm && chatInput && messagesDiv) {
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const message = chatInput.value.trim();
            if (!message) return;
            
            appendMessage('user', message);
            chatInput.value = '';
            
            // Append loading text
            const loading = document.createElement('div');
            loading.id = 'ai-loading-indicator';
            loading.className = 'text-[10px] text-slate-500 italic p-1';
            loading.innerText = 'AI is preparing details...';
            messagesDiv.appendChild(loading);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            const payload = { message: message };
            if (tokenIdInput) {
                payload.token_id = parseInt(tokenIdInput.value);
            }
            
            fetch('/api/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(res => {
                const ld = document.getElementById('ai-loading-indicator');
                if (ld) ld.remove();
                
                if (res.success) {
                    appendMessage('ai', res.data.response);
                } else {
                    appendMessage('ai', res.error.message, true);
                }
            })
            .catch(err => {
                const ld = document.getElementById('ai-loading-indicator');
                if (ld) ld.remove();
                appendMessage('ai', 'Connection lost. Failed to fetch response.', true);
            });
        });
    }
});
