'use client';

import { TrendingDown, Target, Shield } from 'lucide-react';

interface PulseSectionProps {
  theoreticalMinCAC: number;
  marketSaturation: number;
  trustBaseline: number;
}

export default function PulseSection({
  theoreticalMinCAC,
  marketSaturation,
  trustBaseline,
}: PulseSectionProps) {
  return (
    <section className="animate-in" style={{ animationDelay: '100ms' }}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">The Pulse</h2>
          <p className="text-sm text-slate-500 mt-1">Key performance indicators at a glance</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* CAC Card */}
        <div className="group relative glass rounded-2xl p-6 border border-white/50 card-hover overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-teal-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="relative">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-500/25">
                <TrendingDown className="w-6 h-6 text-white" strokeWidth={1.5} />
              </div>
              <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full">
                Optimal
              </span>
            </div>
            <p className="text-sm font-medium text-slate-500 mb-2">Theoretical Min. CAC</p>
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-bold text-slate-900">{theoreticalMinCAC}</span>
              <span className="text-lg text-slate-400">INR</span>
            </div>
            <p className="text-xs text-slate-400 mt-3">Based on winning portfolio performance</p>
          </div>
        </div>

        {/* Market Saturation Card */}
        <div className="group relative glass rounded-2xl p-6 border border-white/50 card-hover overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="relative">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
                <Target className="w-6 h-6 text-white" strokeWidth={1.5} />
              </div>
              <span className="text-xs font-medium text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">
                Coverage
              </span>
            </div>
            <p className="text-sm font-medium text-slate-500 mb-2">Market Saturation</p>
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-bold text-slate-900">{marketSaturation}</span>
              <span className="text-lg text-slate-400">%</span>
            </div>
            <div className="mt-3">
              <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                <div 
                  className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-1000"
                  style={{ width: `${Math.min(marketSaturation, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Trust Baseline Card */}
        <div className="group relative glass rounded-2xl p-6 border border-white/50 card-hover overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-amber-500/5 to-orange-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="relative">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-lg shadow-amber-500/25">
                <Shield className="w-6 h-6 text-white" strokeWidth={1.5} />
              </div>
              <span className="text-xs font-medium text-amber-600 bg-amber-50 px-3 py-1 rounded-full">
                Trust
              </span>
            </div>
            <p className="text-sm font-medium text-slate-500 mb-2">Trust Baseline</p>
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-bold text-slate-900">{trustBaseline.toFixed(1)}</span>
              <span className="text-lg text-slate-400">/10</span>
            </div>
            <p className="text-xs text-slate-400 mt-3">Average audit score across cohort</p>
          </div>
        </div>
      </div>
    </section>
  );
}
