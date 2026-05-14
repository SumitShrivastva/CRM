import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

const API_URL = 'http://localhost:8000/api';

// Async Thunks for API calls
export const fetchInteractions = createAsyncThunk('interactions/fetch', async () => {
    const response = await fetch(`${API_URL}/interactions`);
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data?.message || 'Unable to fetch interactions');
    }

    return data.data ?? [];
});

export const addManualInteraction = createAsyncThunk('interactions/add', async (logData) => {
    const response = await fetch(`${API_URL}/interactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(logData),
    });
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data?.message || 'Unable to add interaction');
    }

    return data.data;
});

const interactionSlice = createSlice({
    name: 'interactions',
    initialState: {
        logs: [],
        status: 'idle',
        error: null,
    },
    reducers: {},
    extraReducers: (builder) => {
        builder
            .addCase(fetchInteractions.pending, (state) => {
                state.status = 'loading';
                state.error = null;
            })
            .addCase(fetchInteractions.fulfilled, (state, action) => {
                state.logs = action.payload ?? [];
                state.status = 'succeeded';
            })
            .addCase(fetchInteractions.rejected, (state, action) => {
                state.status = 'failed';
                state.error = action.error.message;
                state.logs = [];
            })
            .addCase(addManualInteraction.fulfilled, (state, action) => {
                if (action.payload) {
                    state.logs.unshift(action.payload); // Naya log top pe add hoga
                }
            })
            .addCase(addManualInteraction.rejected, (state, action) => {
                state.error = action.error.message;
            });
    },
});

export default interactionSlice.reducer;