import React, { useState, useRef, useEffect } from 'react';

// Add new DatasetSuggestion component
function DatasetSuggestion({ dataset, onAddDataset }) {
  return (
    <div className="bg-gray-800 rounded p-3 mb-2 border border-gray-700">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h4 className="text-blue-300 font-semibold">{dataset.name}</h4>
          <p className="text-sm text-gray-300">{dataset.description}</p>
          <div className="mt-2 text-xs">
            <span className="bg-gray-700 rounded px-2 py-1 mr-2">
              Time: {dataset.temporal_range}
            </span>
            <span className="bg-gray-700 rounded px-2 py-1">
              Resolution: {dataset.spatial_resolution}
            </span>
          </div>
          {dataset.relevance_context && (
            <p className="mt-2 text-xs text-gray-400 italic">
              {dataset.relevance_context}
            </p>
          )}
        </div>
        <button
          onClick={() => onAddDataset(dataset)}
          className="ml-3 px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm rounded-md transition-colors flex items-center gap-1"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add
        </button>
      </div>
    </div>
  );
}

function ChatPanel() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleAddDataset = (dataset) => {
    console.log('Adding dataset:', dataset);
    // TODO: Implement dataset addition logic
  };

  const renderMessageContent = (message) => {
    if (message.role === 'assistant' && message.suggested_datasets?.length > 0) {
      return (
        <div>
          <p className="whitespace-pre-wrap mb-4">{message.content}</p>
          <div className="mt-4">
            <h3 className="text-green-300 font-semibold mb-2">Suggested Datasets:</h3>
            {message.suggested_datasets.map((dataset, idx) => (
              <DatasetSuggestion 
                key={idx} 
                dataset={dataset} 
                onAddDataset={handleAddDataset}
              />
            ))}
          </div>
        </div>
      );
    }
    return <p className="whitespace-pre-wrap">{message.content}</p>;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = '';

      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: '',
        suggested_datasets: [] 
      }]);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        // Split the text into SSE messages
        const messages = text.split('\n\n');
        
        for (const message of messages) {
          if (message.startsWith('data: ')) {
            const data = message.slice(6); // Remove 'data: ' prefix
            if (data === '[DONE]') {
              // Process dataset suggestions after the full message is received
              const datasetIds = [...assistantMessage.matchAll(/\[Dataset ID:\s*([^\]]+)\]/g)]
                .map(match => match[1].trim());
              
              if (datasetIds.length > 0) {
                // Fetch full dataset details for each ID
                const datasets = await Promise.all(datasetIds.map(async (id) => {
                  try {
                    const response = await fetch(`http://localhost:8000/api/chat/datasets/${id}`);
                    if (!response.ok) {
                      console.error(`Failed to fetch dataset ${id}: ${response.status}`);
                      throw new Error('Failed to fetch dataset details');
                    }
                    const data = await response.json();
                    console.log(`Received dataset ${id}:`, data);
                    return data;
                  } catch (error) {
                    console.error(`Error fetching dataset ${id}:`, error);
                    return {
                      id,
                      name: `Dataset ${id}`,
                      description: "Error loading dataset details",
                      temporal_range: "Unknown",
                      spatial_resolution: "Unknown",
                      relevance_context: "",
                      source: "Unknown",
                      category: "Unknown",
                      variables: [],
                      availability: "Unknown"
                    };
                  }
                }));

                setMessages(prev => {
                  const newMessages = [...prev];
                  const lastMessage = newMessages[newMessages.length - 1];
                  console.log('Setting suggested datasets:', datasets);
                  lastMessage.suggested_datasets = datasets;
                  return newMessages;
                });
              }
              break;
            }
            
            assistantMessage += data;
            setMessages(prev => {
              const newMessages = [...prev];
              const lastMessage = newMessages[newMessages.length - 1];
              lastMessage.content = assistantMessage;
              return newMessages;
            });
          }
        }
      }
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, there was an error processing your request.',
        suggested_datasets: []
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-96 bg-gray-900/90 backdrop-blur-sm text-white rounded-lg shadow-lg flex flex-col h-[calc(100vh-2rem)]">
      <div className="p-4 flex-1 overflow-y-auto">
        {messages.map((message, index) => (
          <div key={index} className={`mb-4 ${
            message.role === 'user' ? 'text-blue-300' : 'text-green-300'
          }`}>
            <strong>{message.role === 'user' ? 'You: ' : 'Assistant: '}</strong>
            {renderMessageContent(message)}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-800">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about environmental data..."
            className="flex-1 p-3 rounded bg-gray-800/90 focus:outline-none focus:ring-2 focus:ring-green-600"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading}
            className={`px-4 py-2 rounded transition-colors ${
              isLoading
                ? 'bg-gray-600 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default ChatPanel; 