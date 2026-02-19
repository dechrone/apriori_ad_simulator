'use client';

import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer, ReferenceLine } from 'recharts';
import { Crosshair } from 'lucide-react';

interface BattlefieldSectionProps {
  performances: any;
  reactionData: any[];
}

export default function BattlefieldSection({ performances, reactionData }: BattlefieldSectionProps) {
  const chartData = Object.entries(performances).map(([adId, perf]: [string, any]) => {
    const adReactions = reactionData.filter(r => r.ad_id === adId);
    const avgTrust = adReactions.length > 0
      ? adReactions.reduce((sum, r) => sum + r.trust_score, 0) / adReactions.length
      : 5;
    const avgRelevance = adReactions.length > 0
      ? adReactions.reduce((sum, r) => sum + r.relevance_score, 0) / adReactions.length
      : 5;
    
    return {
      name: adId.replace('ad_', 'Ad '),
      trust: avgTrust,
      greed: avgRelevance,
      clicks: perf.clicks,
      adId: adId,
      conversionRate: perf.conversion_rate,
    };
  });

  const adColors: { [key: string]: string } = {
    ad_1: '#6366f1',
    ad_2: '#8b5cf6',
    ad_3: '#10b981',
    ad_4: '#f59e0b',
  };

  const adGradients: { [key: string]: string } = {
    ad_1: 'from-indigo-500 to-indigo-600',
    ad_2: 'from-purple-500 to-purple-600',
    ad_3: 'from-emerald-500 to-emerald-600',
    ad_4: 'from-amber-500 to-amber-600',
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="glass rounded-xl px-4 py-3 shadow-xl border border-white/50">
          <p className="font-semibold text-slate-900 mb-2">{data.name}</p>
          <div className="space-y-1 text-sm">
            <p className="text-slate-600">Trust: <span className="font-medium text-slate-900">{data.trust.toFixed(1)}/10</span></p>
            <p className="text-slate-600">Greed: <span className="font-medium text-slate-900">{data.greed.toFixed(1)}/10</span></p>
            <p className="text-slate-600">Clicks: <span className="font-medium text-slate-900">{data.clicks}</span></p>
            <p className="text-slate-600">Conv. Rate: <span className="font-medium text-slate-900">{data.conversionRate}%</span></p>
          </div>
        </div>
      );
    }
    return null;
  };

  const winningAds = chartData.filter(d => d.trust >= 7 && d.greed >= 7);

  return (
    <section className="animate-in" style={{ animationDelay: '200ms' }}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">The Battlefield</h2>
          <p className="text-sm text-slate-500 mt-1">Trust vs Greed quadrant analysis</p>
        </div>
      </div>

      <div className="glass rounded-3xl border border-white/50 overflow-hidden">
        <div className="p-6 lg:p-8">
          <div className="flex flex-col lg:flex-row gap-8">
            {/* Chart */}
            <div className="flex-1">
              <div className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 20, right: 20, bottom: 40, left: 20 }}>
                    <defs>
                      <linearGradient id="gridGradient" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stopColor="#6366f1" stopOpacity={0.05} />
                        <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0.05} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" strokeOpacity={0.5} />
                    <XAxis 
                      type="number" 
                      dataKey="greed" 
                      domain={[0, 10]}
                      stroke="#94a3b8"
                      tick={{ fill: '#64748b', fontSize: 12 }}
                      tickLine={{ stroke: '#cbd5e1' }}
                      label={{ value: 'Greed (Savings Appeal)', position: 'bottom', offset: 20, fill: '#64748b', fontSize: 13 }}
                    />
                    <YAxis 
                      type="number" 
                      dataKey="trust" 
                      domain={[0, 10]}
                      stroke="#94a3b8"
                      tick={{ fill: '#64748b', fontSize: 12 }}
                      tickLine={{ stroke: '#cbd5e1' }}
                      label={{ value: 'Trust (Compliance)', angle: -90, position: 'insideLeft', offset: 10, fill: '#64748b', fontSize: 13 }}
                    />
                    <ReferenceLine x={5} stroke="#cbd5e1" strokeDasharray="5 5" />
                    <ReferenceLine y={5} stroke="#cbd5e1" strokeDasharray="5 5" />
                    <Tooltip content={<CustomTooltip />} />
                    <Scatter name="Ads" data={chartData}>
                      {chartData.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={adColors[entry.adId]}
                          fillOpacity={0.9}
                          stroke={adColors[entry.adId]}
                          strokeWidth={2}
                          r={Math.max(entry.clicks * 4, 12)}
                        />
                      ))}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Legend & Insights */}
            <div className="lg:w-72 space-y-4">
              <div className="bg-slate-50/80 rounded-2xl p-4 border border-slate-100">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Ad Legend</p>
                <div className="space-y-3">
                  {chartData.map((ad) => (
                    <div key={ad.adId} className="flex items-center gap-3">
                      <div className={`w-4 h-4 rounded-full bg-gradient-to-br ${adGradients[ad.adId]} shadow-sm`} />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-slate-700">{ad.name}</p>
                        <p className="text-xs text-slate-500">{ad.clicks} clicks</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {winningAds.length > 0 && (
                <div className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-2xl p-4 border border-emerald-100">
                  <div className="flex items-center gap-2 mb-2">
                    <Crosshair className="w-4 h-4 text-emerald-600" strokeWidth={2} />
                    <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">Sweet Spot</p>
                  </div>
                  <p className="text-sm text-emerald-800">
                    <span className="font-semibold">{winningAds.map(a => a.name).join(', ')}</span>
                    {' '}in the High-Trust / High-Greed quadrant
                  </p>
                </div>
              )}

              <div className="text-xs text-slate-400 leading-relaxed">
                Circle size represents click volume. Top-right is the optimal zone.
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
