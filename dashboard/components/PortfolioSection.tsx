'use client';

import { Percent, Users, TrendingUp, Target } from 'lucide-react';

interface PortfolioSectionProps {
  portfolio: any[];
  segmentOwnership: any;
}

export default function PortfolioSection({ portfolio, segmentOwnership }: PortfolioSectionProps) {
  const adGradients: { [key: string]: string } = {
    ad_1: 'from-indigo-500 to-indigo-600',
    ad_2: 'from-purple-500 to-purple-600',
    ad_3: 'from-emerald-500 to-emerald-600',
    ad_4: 'from-amber-500 to-amber-600',
  };

  const adBgGradients: { [key: string]: string } = {
    ad_1: 'from-indigo-500/10 to-indigo-600/5',
    ad_2: 'from-purple-500/10 to-purple-600/5',
    ad_3: 'from-emerald-500/10 to-emerald-600/5',
    ad_4: 'from-amber-500/10 to-amber-600/5',
  };

  return (
    <section className="animate-in" style={{ animationDelay: '300ms' }}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Portfolio Strategy</h2>
          <p className="text-sm text-slate-500 mt-1">Recommended budget allocation and targeting</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {portfolio.map((item, index) => {
          const segment = Object.values(segmentOwnership).find(
            (s: any) => s.winning_ad === item.ad_id
          ) as any;

          return (
            <div
              key={item.ad_id}
              className={`group relative glass rounded-3xl border border-white/50 overflow-hidden card-hover`}
            >
              {/* Gradient overlay */}
              <div className={`absolute inset-0 bg-gradient-to-br ${adBgGradients[item.ad_id]} opacity-50`} />
              
              <div className="relative p-6">
                {/* Header */}
                <div className="flex items-start justify-between mb-5">
                  <div className="flex items-center gap-4">
                    <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${adGradients[item.ad_id]} flex items-center justify-center shadow-lg`}>
                      <span className="text-white font-bold text-lg">{item.ad_id.replace('ad_', '')}</span>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-slate-900">{item.role}</h3>
                      <p className="text-sm text-slate-500">{item.ad_id.replace('ad_', 'Ad ')}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 border border-slate-200/50 shadow-sm">
                    <Percent className="w-4 h-4 text-indigo-600" strokeWidth={2} />
                    <span className="text-lg font-bold text-slate-900">{item.budget_split}%</span>
                  </div>
                </div>

                {/* Target segment */}
                <p className="text-sm text-slate-600 leading-relaxed mb-5 line-clamp-2">
                  {item.target_segment}
                </p>

                {/* Stats grid */}
                <div className="grid grid-cols-3 gap-3 mb-5">
                  <div className="bg-white/60 rounded-xl p-3 border border-white/50">
                    <div className="flex items-center gap-2 mb-1">
                      <Users className="w-3.5 h-3.5 text-slate-400" strokeWidth={2} />
                      <span className="text-xs text-slate-500">Reach</span>
                    </div>
                    <p className="text-lg font-bold text-slate-900">{item.unique_reach}</p>
                  </div>
                  <div className="bg-white/60 rounded-xl p-3 border border-white/50">
                    <div className="flex items-center gap-2 mb-1">
                      <TrendingUp className="w-3.5 h-3.5 text-slate-400" strokeWidth={2} />
                      <span className="text-xs text-slate-500">Conv.</span>
                    </div>
                    <p className="text-lg font-bold text-slate-900">{item.expected_conversions}</p>
                  </div>
                  <div className="bg-white/60 rounded-xl p-3 border border-white/50">
                    <div className="flex items-center gap-2 mb-1">
                      <Target className="w-3.5 h-3.5 text-slate-400" strokeWidth={2} />
                      <span className="text-xs text-slate-500">Rate</span>
                    </div>
                    <p className="text-lg font-bold text-slate-900">
                      {segment ? `${Math.round(segment.conversion_rate)}%` : '--'}
                    </p>
                  </div>
                </div>

                {/* Reasoning */}
                <div className="pt-4 border-t border-slate-200/50">
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Why This Works</p>
                  <p className="text-sm text-slate-700 leading-relaxed">{item.reasoning}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
