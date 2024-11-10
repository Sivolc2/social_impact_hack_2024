import { Client } from '@fetch-ai/web-sdk';

document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const chatMessages = document.getElementById('chat-messages');
    
    // Initialize Fetch.ai client
    const fetchAI = new Client({
        apiKey: 'YOUR_API_KEY'
    });

    let conversationHistory = [];

    async function sendMessage(message) {
        // Add user message to chat
        appendMessage('user', message);
        
        try {
            // Add message to history
            conversationHistory.push({ role: 'user', content: message });
            
            // Get AI response
            const response = await fetchAI.chat.complete({
                messages: conversationHistory,
                model: 'fetch-ai/llama-2-7b-chat'  // or your preferred model
            });
            
            const aiResponse = response.choices[0].message.content;
            
            // Add AI response to history
            conversationHistory.push({ role: 'assistant', content: aiResponse });
            
            // Display AI response
            appendMessage('assistant', aiResponse);
            
        } catch (error) {
            console.error('Error:', error);
            appendMessage('system', 'Sorry, there was an error processing your request.');
        }
    }

    function appendMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', role);
        messageDiv.textContent = content;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Event listeners
    sendButton.addEventListener('click', () => {
        const message = chatInput.value.trim();
        if (message) {
            sendMessage(message);
            chatInput.value = '';
        }
    });

    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendButton.click();
        }
    });
}); 