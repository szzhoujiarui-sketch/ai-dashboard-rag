import { useState, useRef, useEffect } from 'react';
import { Upload, Send, FileText, Trash2, Loader2 } from 'lucide-react';
import { documentApi, chatApi, getApiErrorMessage, type DocumentInfo } from '../../services/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Array<{ content: string; metadata: Record<string, unknown> }>;
}

export default function RAGPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadDocuments = async () => {
    try {
      const res = await documentApi.list();
      setDocuments(res.data.documents || []);
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      await documentApi.upload(file);
      await loadDocuments();
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `文档 "${file.name}" 已成功上传并处理。您现在可以基于该文档提问了。`
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `上传失败: ${getApiErrorMessage(error)}`
      }]);
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (filename: string) => {
    try {
      await documentApi.delete(filename);
      await loadDocuments();
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `删除失败: ${getApiErrorMessage(error)}`
      }]);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const res = await chatApi.ask(input);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.data.answer,
        sources: res.data.sources
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `查询失败: ${getApiErrorMessage(error)}`
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">RAG 智能问答</h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 文档管理 */}
        <div className="lg:col-span-1 bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">文档库</h3>
          
          <div className="mb-4">
            <label className="flex items-center justify-center w-full px-4 py-6 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-blue-500 transition-colors">
              <div className="text-center">
                <Upload className="mx-auto h-8 w-8 text-gray-400" />
                <p className="mt-1 text-sm text-gray-600">
                  {uploading ? '上传中...' : '点击上传文档'}
                </p>
              </div>
              <input
                type="file"
                accept=".pdf,.txt,.md"
                onChange={handleUpload}
                disabled={uploading}
                className="hidden"
              />
            </label>
          </div>

          <div className="space-y-2">
            {documents.map((doc) => (
              <div
                key={doc.filename}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center space-x-2">
                  <FileText className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 truncate max-w-[150px]">
                      {doc.original_filename}
                    </p>
                    <p className="text-xs text-gray-500">
                      {(doc.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(doc.safe_filename || doc.filename)}
                  className="text-red-600 hover:text-red-800"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
            {documents.length === 0 && (
              <p className="text-sm text-gray-500 text-center py-4">
                暂无文档，请上传 PDF 或 TXT 文件
              </p>
            )}
          </div>
        </div>

        {/* 问答面板 */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow flex flex-col h-[600px]">
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 mt-20">
                <p className="text-lg">👋 欢迎使用 RAG 智能问答</p>
                <p className="text-sm mt-2">上传文档后，即可基于文档内容进行智能问答</p>
              </div>
            )}
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-200">
                      <p className="text-xs text-gray-500 mb-1">参考来源:</p>
                      {msg.sources.map((source, i) => (
                        <div key={i} className="text-xs bg-white p-2 rounded mt-1">
                          {source.content}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg px-4 py-2">
                  <Loader2 className="h-5 w-5 animate-spin text-gray-500" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="border-t p-4">
            <div className="flex space-x-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="输入您的问题..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              />
              <button
                onClick={handleSend}
                disabled={loading || !input.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
