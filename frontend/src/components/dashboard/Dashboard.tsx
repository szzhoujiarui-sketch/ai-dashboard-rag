import { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';
import { statsApi, type DashboardStats, type TrendData } from '../../services/api';

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [trends, setTrends] = useState<TrendData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, trendsRes] = await Promise.all([
          statsApi.getDashboardStats(),
          statsApi.getQueryTrends(),
        ]);
        setStats(statsRes.data);
        setTrends(trendsRes.data);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  const trendData = trends
    ? trends.dates.map((date, i) => ({
        date,
        queries: trends.queries[i],
        avg_response_time: trends.avg_response_time[i],
      }))
    : [];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">系统概览</h2>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title="总查询数" value={stats?.total_queries} />
        <StatCard title="文档数量" value={stats?.total_documents} />
        <StatCard title="平均响应时间" value={stats?.avg_response_time} suffix="s" />
        <StatCard title="系统运行时间" value={stats?.uptime} />
      </div>

      {/* 趋势图 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">查询趋势（近7天）</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="queries"
              stroke="#3b82f6"
              name="查询数"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="avg_response_time"
              stroke="#10b981"
              name="平均响应时间（秒）"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* 响应时间分布 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">性能指标</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="queries" fill="#8b5cf6" name="查询量" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function StatCard({ title, value, suffix = '' }: { title: string; value?: number | string; suffix?: string }) {
  return (
    <div className="bg-white rounded-lg shadow p-5">
      <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
      <dd className="mt-1 text-3xl font-semibold text-gray-900">
        {value !== undefined ? `${value}${suffix}` : '-'}
      </dd>
    </div>
  );
}
