import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export interface DocumentInfo {
  filename: string;
  safe_filename: string;
  original_filename: string;
  document_id?: string;
  size: number;
  modified: string;
}

export interface DocumentsResponse {
  documents: DocumentInfo[];
}

export interface ChatSource {
  content: string;
  metadata: Record<string, unknown>;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
}

export interface DashboardStats {
  total_queries: number;
  total_documents: number;
  uptime: string;
  avg_response_time: number;
  last_updated: string;
}

export interface TrendData {
  dates: string[];
  queries: number[];
  avg_response_time: number[];
}

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    return error.message;
  }
  if (error instanceof Error) return error.message;
  return '未知错误';
}

export const api = axios.create({
  baseURL: API_BASE_URL,
});

const apiKey = import.meta.env.VITE_API_KEY;

api.interceptors.request.use((config) => {
  if (apiKey) {
    config.headers.set('X-API-Key', apiKey);
  }
  return config;
});

export const documentApi = {
  upload: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  list: async () => api.get<DocumentsResponse>('/documents/list'),
  delete: async (filename: string) => api.delete(`/documents/${filename}`),
};

export const chatApi = {
  ask: async (question: string, k: number = 4) => {
    return api.post<ChatResponse>('/chat/ask', { question, k });
  },
};

export const statsApi = {
  getDashboardStats: async () => api.get<DashboardStats>('/stats/dashboard'),
  getQueryTrends: async () => api.get<TrendData>('/stats/trends'),
};
