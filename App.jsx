import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import ChatInterface from './ChatInterface';
import InteractionForm from './InteractionForm';
import { fetchInteractions } from './store/interactionSlice';

function App() {
    const dispatch = useDispatch();
    const { logs = [] } = useSelector((state) => state.interactions);

    useEffect(() => {
        dispatch(fetchInteractions());
    }, [dispatch]);

    return (
        <div className="app-container">
            <header className="header">
                <h1>AI-First CRM: HCP Module</h1>
                <p>Log interactions manually or use the LangGraph AI Assistant</p>
            </header>

            <div className="main-grid">
                {/* Left Side: Manual Form */}
                <InteractionForm />
                
                {/* Right Side: AI Chatbot */}
                <ChatInterface />
            </div>

            {/* Display Recent Logs below */}
            <div className="table-section">
                <h2>Recent Interactions Database</h2>
                <div className="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>HCP Name</th>
                                <th>Date</th>
                                <th>Topic</th>
                            </tr>
                        </thead>
                        <tbody>
                            {logs.map((log) => (
                                <tr key={log.id}>
                                    <td>{log.id}</td>
                                    <td><strong>{log.hcp_name}</strong></td>
                                    <td>{log.date}</td>
                                    <td>{log.topic}</td>
                                </tr>
                            ))}
                            {logs.length === 0 && (
                                <tr>
                                    <td colSpan="4" className="empty-state">No logs found. Start by adding one!</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

export default App;