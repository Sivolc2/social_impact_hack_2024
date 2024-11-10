// Remove the import and create the module immediately
(function() {
    // Create the module first
    window.chatModule = {
        addMessageToChat: function(role, message, summaryTable = '') {
            const messagesContainer = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${role}-message`;
            
            if (summaryTable || message.includes('<')) {
                messageDiv.innerHTML = `
                    <div class="message-text">${message}</div>
                    ${summaryTable ? `
                        <div class="summary-section">
                            <h4 style="color: #ffffff; margin-bottom: 0.5rem;">Summary Table</h4>
                            ${summaryTable}
                        </div>
                    ` : ''}
                `;
            } else {
                const textDiv = document.createElement('div');
                textDiv.className = 'message-text';
                textDiv.textContent = message;
                messageDiv.appendChild(textDiv);
            }
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        },

        sendMessage: async function() {
            const userInput = document.getElementById('user-input');
            const message = userInput.value.trim();
            if (!message) return;
            
            // Add user message to chat
            this.addMessageToChat('user', message);
            userInput.value = '';
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        mode: window.currentMode || 'data'
                    })
                });

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let assistantMessage = '';
                
                while (true) {
                    const {done, value} = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value);
                    const messages = chunk.split('\n\n');
                    
                    for (const message of messages) {
                        if (message.trim().startsWith('data: ')) {
                            try {
                                const data = JSON.parse(message.replace('data: ', '').trim());
                                if (data.chunk) {
                                    assistantMessage += data.chunk;
                                    this.updateOrCreateAssistantMessage(assistantMessage);
                                }
                            } catch (e) {
                                console.error('JSON parse error:', e);
                            }
                        }
                    }
                }
            } catch (error) {
                console.error('Error sending message:', error);
                this.addMessageToChat('system', 'Sorry, there was an error processing your message.');
            }
        },

        updateOrCreateAssistantMessage: function(content) {
            const chatMessages = document.querySelector('.chat-messages');
            let lastMessage = chatMessages.lastElementChild;
            
            if (lastMessage && lastMessage.classList.contains('assistant-message')) {
                const contentDiv = lastMessage.querySelector('.message-text');
                if (contentDiv) {
                    contentDiv.innerHTML = markdownRenderer(content || '');
                    scrollToBottom();
                }
            } else {
                this.addMessageToChat('assistant', content);
                scrollToBottom();
            }
        },

        sendToMap: async function() {
            try {
                // Force switch to analysis mode
                const analysisButton = document.querySelector('.toggle-button[data-mode="analysis"]');
                if (analysisButton) {
                    analysisButton.classList.add('active');
                    const dataButton = document.querySelector('.toggle-button[data-mode="data"]');
                    if (dataButton) {
                        dataButton.classList.remove('active');
                    }
                    
                    // Update the current mode
                    window.currentMode = 'analysis';
                    
                    // Update placeholder and messages
                    const chatInput = document.getElementById('user-input');
                    const chatMessages = document.getElementById('chat-messages');
                    
                    chatInput.placeholder = 'Ask for analysis of the selected region...';
                    chatMessages.innerHTML = '';
                    this.addMessageToChat('assistant', 'I can help analyze the environmental data for your selected region. What would you like to know?');
                }

                const chatMessages = document.getElementById('chat-messages');
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'chat-message loading-message';
                loadingDiv.innerHTML = '<div class="loading-dots"><span>.</span><span>.</span><span>.</span></div>';
                chatMessages.appendChild(loadingDiv);

                // Set the dataRequested flag to true
                window.dataRequested = true;

                // Get chat history
                const messages = Array.from(chatMessages.children)
                    .filter(msg => !msg.classList.contains('loading-message'))
                    .map(msg => ({
                        role: msg.classList.contains('user-message') ? 'user' : 
                              msg.classList.contains('assistant-message') ? 'assistant' : 'system',
                        content: msg.textContent.trim()
                    }));

                const response = await fetch('/send-to-map', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        messages: messages
                    })
                });

                if (!response.ok) {
                    throw new Error(`Server responded with status: ${response.status}`);
                }

                const data = await response.json();
                await window.handleMapUpdate(data);

                // Remove loading indicator
                loadingDiv.remove();

            } catch (error) {
                console.error('Error sending to map:', error);
                const errorMessage = error.message || 'An unknown error occurred';
                this.addMessageToChat('system', `Error loading data to map: ${errorMessage}`);
                
                // Remove loading indicator if it exists
                const loadingDiv = document.querySelector('.loading-message');
                if (loadingDiv) {
                    loadingDiv.remove();
                }
            }
        }
    };

    // Make sendMessage globally available
    window.sendMessage = function() {
        window.chatModule.sendMessage();
    };

    // Dispatch an event when the module is ready
    window.dispatchEvent(new Event('chatModuleReady'));
})();