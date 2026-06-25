import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
});

export const documentApi = {
  upload: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  list: async () => api.get('/documents/list'),
  delete: async (filename: string) => api.delete(`/documents/${filename}`),
};

export const chatApi = {
  ask: async (question: string, k: number = 4) => {
    return api.post('/chat/ask', { question, k });
  },
};

export const statsApi = {
  getDashboardStats: async () => api.get('/stats/dashboard'),
  getQueryTrends: async () => api.get('/stats/trends'),
};
