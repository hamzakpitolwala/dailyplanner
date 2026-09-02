import React, { useEffect, useState, useMemo, type FC } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area
} from 'recharts';
import { TrendingUp, CheckCircle, Clock, CalendarX, Brain, Target, Activity } from 'lucide-react';
import { analyticsApi } from '../api/analyticsApi';

const COLORS = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#ec4899'];
const GRADIENTS = [
  'from-purple-500 to-indigo-600',
  'from-blue-400 to-emerald-400',
  'from-rose-400 to-orange-300',
  'from-teal-400 to-cyan-500'
];

interface CardProps {
  children: React.ReactNode;
  className?: string;
}

const Card: FC<CardProps> = ({ children, className = '' }) => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.4 }}
    className={`bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl shadow-xl rounded-2xl border border-white/20 dark:border-gray-700/50 p-6 ${className}`}
  >
    {children}
  </motion.div>
);

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: any;
  colorIdx?: number;
  delay?: number;
}

const StatCard: FC<StatCardProps> = ({ title, value, subtitle, icon: Icon, colorIdx = 0, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, scale: 0.95 }}
    animate={{ opacity: 1, scale: 1 }}
    transition={{ duration: 0.5, delay }}
    className={`relative overflow-hidden rounded-2xl p-6 text-white bg-gradient-to-br ${GRADIENTS[colorIdx]} shadow-lg`}
  >
    <div className="relative z-10 flex flex-col h-full justify-between">
      <div className="flex justify-between items-start">
        <h3 className="text-white/80 font-medium text-sm tracking-wider uppercase">{title}</h3>
        <div className="bg-white/20 p-2 rounded-full backdrop-blur-sm">
          <Icon size={20} className="text-white" />
        </div>
      </div>
      <div className="mt-4">
        <span className="text-4xl font-bold tracking-tight">{value}</span>
        {subtitle && <p className="text-white/70 text-sm mt-1">{subtitle}</p>}
      </div>
    </div>
    <div className="absolute -right-8 -bottom-8 w-32 h-32 bg-white/10 rounded-full blur-2xl"></div>
  </motion.div>
);

export const DashboardPage: FC = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>({
    overview: null,
    patterns: null,
    conflicts: null,
    focus: null,
    ai: null
  });

  useEffect(() => {
    // We assume token is managed via some context or local storage.
    const token = localStorage.getItem('token') || '';
    
    const loadData = async () => {
      try {
        const [overview, patterns, conflicts, focus, ai] = await Promise.all([
          analyticsApi.fetchOverview(token).catch(() => ({ trends: [], kpis: {}, top_missed_reasons: [] })),
          analyticsApi.fetchTimePatterns(token).catch(() => ({ time_blocks: [], weekdays: [] })),
          analyticsApi.fetchCalendarConflicts(token).catch(() => []),
          analyticsApi.fetchFocusMetrics(token).catch(() => []),
          analyticsApi.fetchAiEffectiveness(token).catch(() => [])
        ]);
        
        setData({ overview, patterns, conflicts, focus, ai });
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const trendsData = useMemo(() => {
    return data.overview?.trends?.map((t: any) => ({
      name: t.date.split('-').slice(1).join('/'),
      rate: Math.round(t.completion_rate * 100),
      completed: t.completed,
      notDone: t.not_done
    })) || [];
  }, [data.overview?.trends]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center w-full h-full">
        <motion.div 
          animate={{ rotate: 360 }} 
          transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
          className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  const { overview, patterns, ai } = data;

  return (
    <div className="w-full h-full overflow-y-auto bg-transparent dark:bg-transparent p-8 font-sans text-slate-800 dark:text-slate-100 transition-colors duration-300">
      <div className="max-w-7xl mx-auto space-y-8">
        
        <header className="mb-10">
          <motion.h1 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-400 dark:to-purple-400"
          >
            Analytics Dashboard
          </motion.h1>
          <p className="text-slate-500 dark:text-slate-400 mt-2">Your daily productivity insights and patterns.</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard 
            title="Completion Rate" 
            value={`${Math.round((overview?.kpis?.completion_rate || 0) * 100)}%`} 
            subtitle="Overall across all activities"
            icon={CheckCircle}
            colorIdx={0}
            delay={0.1}
          />
          <StatCard 
            title="Total Completed" 
            value={overview?.kpis?.total_completed || 0} 
            subtitle="Tasks finished"
            icon={Target}
            colorIdx={1}
            delay={0.2}
          />
          <StatCard 
            title="Top Missed Reason" 
            value={overview?.top_missed_reasons?.[0]?.name || 'N/A'} 
            subtitle={`${overview?.top_missed_reasons?.[0]?.value || 0} occurrences`}
            icon={TrendingUp}
            colorIdx={2}
            delay={0.3}
          />
          <StatCard 
            title="AI Acceptance" 
            value={`${ai?.length > 0 ? 'High' : 'N/A'}`} 
            subtitle={`${ai?.length || 0} recommendations accepted`}
            icon={Brain}
            colorIdx={3}
            delay={0.4}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          <Card className="col-span-1 lg:col-span-2">
            <div className="flex items-center space-x-2 mb-6">
              <Activity className="text-indigo-500" />
              <h2 className="text-xl font-bold">Activity Completion Trends</h2>
            </div>
            <div className="h-72 w-full">
              <ResponsiveContainer>
                <AreaChart data={trendsData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorRate" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#64748b'}} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b'}} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                  />
                  <Area type="monotone" dataKey="rate" stroke="#8b5cf6" strokeWidth={3} fillOpacity={1} fill="url(#colorRate)" name="Completion %" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card>
            <div className="flex items-center space-x-2 mb-6">
              <CalendarX className="text-rose-500" />
              <h2 className="text-xl font-bold">Missed Reasons</h2>
            </div>
            <div className="h-72 w-full">
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={overview?.top_missed_reasons || []}
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {(overview?.top_missed_reasons || []).map((_entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }} />
                  <Legend verticalAlign="bottom" height={36} iconType="circle" />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card>
            <div className="flex items-center space-x-2 mb-6">
              <Clock className="text-emerald-500" />
              <h2 className="text-xl font-bold">Time of Day Patterns</h2>
            </div>
            <div className="h-64 w-full">
              <ResponsiveContainer>
                <BarChart data={patterns?.time_blocks || []}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="time_bucket" axisLine={false} tickLine={false} tick={{fill: '#64748b'}} dy={10} />
                  <YAxis hide />
                  <Tooltip cursor={{fill: 'transparent'}} />
                  <Bar dataKey="completion_rate" name="Completion Rate" fill="#10b981" radius={[6, 6, 0, 0]} barSize={40}>
                    {(patterns?.time_blocks || []).map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.completion_rate > 0.5 ? '#10b981' : '#f59e0b'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card className="col-span-1 lg:col-span-2">
            <div className="flex items-center space-x-2 mb-6">
              <Brain className="text-purple-500" />
              <h2 className="text-xl font-bold">AI Effectiveness</h2>
            </div>
            {ai?.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Date</th>
                      <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Recommendation</th>
                      <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ai.map((item: any, idx: number) => (
                      <motion.tr 
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        key={idx} 
                        className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                      >
                        <td className="py-3 px-4 text-gray-500 dark:text-gray-400 text-sm">{item.date}</td>
                        <td className="py-3 px-4 font-medium">{item.title}</td>
                        <td className="py-3 px-4">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                            {item.decision}
                          </span>
                        </td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-48 text-gray-400">
                <Brain size={48} className="mb-4 opacity-20" />
                <p>No AI recommendations accepted yet.</p>
              </div>
            )}
          </Card>

        </div>
      </div>
    </div>
  );
};
