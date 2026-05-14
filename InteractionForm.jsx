import { useState } from 'react';
import { useDispatch } from 'react-redux';
import { addManualInteraction } from './store/interactionSlice';

export default function InteractionForm() {
    const dispatch = useDispatch();
    const [formData, setFormData] = useState({
        hcp_name: '', date: '', topic: '', summary: '', follow_up_date: ''
    });

    const handleSubmit = (e) => {
        e.preventDefault();
        dispatch(addManualInteraction(formData));
        setFormData({ hcp_name: '', date: '', topic: '', summary: '', follow_up_date: '' });
        alert("Interaction Logged Manually!");
    };

    return (
        <div className="card form-container">
            <h2>Manual Log Entry</h2>
            <form onSubmit={handleSubmit} className="custom-form">
                <input required type="text" placeholder="HCP Name (e.g., Dr. Sharma)" 
                    value={formData.hcp_name} onChange={e => setFormData({...formData, hcp_name: e.target.value})} />
                
                <input required type="date" 
                    value={formData.date} onChange={e => setFormData({...formData, date: e.target.value})} />
                
                <input required type="text" placeholder="Topic of Discussion" 
                    value={formData.topic} onChange={e => setFormData({...formData, topic: e.target.value})} />
                
                <textarea required placeholder="Meeting Summary" 
                    value={formData.summary} onChange={e => setFormData({...formData, summary: e.target.value})} />
                
                <div>
                    <label style={{fontSize: '0.875rem', color: '#4b5563'}}>Follow-up Date (Optional)</label>
                    <input type="date" 
                        value={formData.follow_up_date} onChange={e => setFormData({...formData, follow_up_date: e.target.value})} />
                </div>
                
                <button type="submit" className="btn-green">
                    Save Record
                </button>
            </form>
        </div>
    );
}