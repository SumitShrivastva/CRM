import { useState } from 'react';
import { useDispatch } from 'react-redux';
import { fetchInteractions } from './store/interactionSlice'; // Change this path if needed

export default function ChatInterface() {
    const [messages, setMessages] = useState([{ sender: 'ai', text: 'Hello! Tell me about your HCP interaction today.' }]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const dispatch = useDispatch();

    const sendMessage = async () => {
        if (!input.trim() || isLoading) return;
        
        const userMsg = input;
        setMessages(prev => [...prev, { sender: 'user', text: userMsg }]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await fetch('http://localhost:8000/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMsg }),
            });
            
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data?.detail || 'Server error');
            }
            
            setMessages(prev => [...prev, { sender: 'ai', text: data.reply }]);
            dispatch(fetchInteractions()); 
        } catch (error) {
            setMessages(prev => [...prev, { sender: 'ai', text: `Error: ${error.message}. Check your backend terminal for details.` }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="card" style={{ padding: '20px' }}>
            <h2>AI Assistant</h2>
            
            <div style={{ height: '400px', overflowY: 'auto', border: '1px solid #ccc', padding: '10px', marginBottom: '10px' }}>
                {messages.map((msg, idx) => (
                    <div key={idx} style={{ textAlign: msg.sender === 'user' ? 'right' : 'left', margin: '5px 0' }}>
                        <span style={{
                            display: 'inline-block',
                            padding: '10px',
                            borderRadius: '10px',
                            background: msg.sender === 'user' ? '#007bff' : '#f1f1f1',
                            color: msg.sender === 'user' ? '#fff' : '#000'
                        }}>
                            {msg.text}
                        </span>
                    </div>
                ))}
                {isLoading && <div style={{ color: '#888' }}>Thinking...</div>}
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
                <input 
                    style={{ flex: 1, padding: '10px' }}
                    type="text" 
                    placeholder="Log a meeting with Dr. Smith..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                    disabled={isLoading}
                />
                <button onClick={sendMessage} disabled={isLoading} style={{ padding: '10px 20px', cursor: 'pointer' }}>
                    Send
                </button>
            </div>
        </div>
    );
}