'use client';

import { AlertTriangle, Layers, Radar, CheckCircle } from 'lucide-react';

interface CoverageInsightsProps {
  audienceSegments: Record<string, Record<string, number>>;
  overlapMatrix: Record<string, Record<string, number>>;
  validationSummary?: any;
  wastedSpendAlerts?: string[];
}

const formatSegmentLabel = (label: string) => label.replace(/_/g, ' ');

export default function CoverageInsights({
  audienceSegments,
  overlapMatrix,
  validationSummary,
  wastedSpendAlerts,
}: CoverageInsightsProps) {
  const overlapPairs: { pair: string; value: number }[] = [];

  Object.entries(overlapMatrix || {}).forEach(([adA, overlaps]) => {
    Object.entries(overlaps || {}).forEach(([adB, value]) => {
      if (adA !== adB) {
        const key = [adA, adB].sort().join('-');
        if (!overlapPairs.find(p => p.pair.includes(adA) && p.pair.includes(adB))) {
          overlapPairs.push({
            pair: `${adA.replace('ad_', 'Ad ')} / ${adB.replace('ad_', 'Ad ')}`,
            value: Number(value),
          });
        }
      }
    });
  });

  const sortedOverlap = overlapPairs.sort((a, b) => b.value - a.value).slice(0, 3);

  const adGradients: { [key: string]: string } = {
    ad_1: 'from-indigo-500 to-indigo-600',
    ad_2: 'from-purple-500 to-purple-600',
    ad_3: 'from-emerald-500 to-emerald-600',
    ad_4: 'from-amber-500 to-amber-600',
  };

  return (
    <section className="animate-in" style={{ animationDelay: '400ms' }}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Coverage & Integrity</h2>
          <p className="text-sm text-slate-500 mt-1">Audience signals, overlap risk, and validation</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Audience Signals */}
        <div className="glass rounded-3xl border border-white/50 p-6 card-hover">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
              <Radar className="w-5 h-5 text-white" strokeWidth={1.5} />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Audience Signals</h3>
              <p className="text-xs text-slate-500">Top segments per ad</p>
            </div>
          </div>
          <div className="space-y-4">
            {Object.entries(audienceSegments || {}).slice(0, 4).map(([adId, segments]) => {
              const topSegments = Object.entries(segments || {})
                .sort((a, b) => b[1] - a[1])
                .slice(0, 2);

              return (
                <div key={adId}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-6 h-6 rounded-lg bg-gradient-to-br ${adGradients[adId]} flex items-center justify-center`}>
                      <span className="text-white text-xs font-bold">{adId.replace('ad_', '')}</span>
                    </div>
                    <span className="text-sm font-medium text-slate-700">{adId.replace('ad_', 'Ad ')}</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5 ml-8">
                    {topSegments.map(([segment, count]) => (
                      <span
                        key={segment}
                        className="text-xs bg-slate-100/80 text-slate-600 px-2.5 py-1 rounded-lg border border-slate-200/50"
                      >
                        {formatSegmentLabel(segment)} <span className="text-slate-400">({count})</span>
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Overlap Risk */}
        <div className="glass rounded-3xl border border-white/50 p-6 card-hover">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-lg shadow-amber-500/25">
              <Layers className="w-5 h-5 text-white" strokeWidth={1.5} />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Overlap Risk</h3>
              <p className="text-xs text-slate-500">Creative cannibalization</p>
            </div>
          </div>
          {sortedOverlap.length > 0 ? (
            <div className="space-y-3">
              {sortedOverlap.map((item, idx) => (
                <div key={idx} className="bg-slate-50/80 rounded-xl p-4 border border-slate-200/50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-slate-700">{item.pair}</span>
                    <span className={`text-sm font-bold ${
                      item.value > 0.8 ? 'text-red-600' : item.value > 0.6 ? 'text-amber-600' : 'text-emerald-600'
                    }`}>
                      {(item.value * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-200/50 overflow-hidden">
                    <div 
                      className={`h-full rounded-full ${
                        item.value > 0.8 ? 'bg-red-500' : item.value > 0.6 ? 'bg-amber-500' : 'bg-emerald-500'
                      }`}
                      style={{ width: `${item.value * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">No significant overlap detected</p>
          )}
        </div>

        {/* Validation */}
        <div className="glass rounded-3xl border border-white/50 p-6 card-hover">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-500/25">
              {validationSummary?.flagged === 0 ? (
                <CheckCircle className="w-5 h-5 text-white" strokeWidth={1.5} />
              ) : (
                <AlertTriangle className="w-5 h-5 text-white" strokeWidth={1.5} />
              )}
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Integrity Check</h3>
              <p className="text-xs text-slate-500">Validation results</p>
            </div>
          </div>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-50/80 rounded-xl p-3 border border-slate-200/50">
                <p className="text-xs text-slate-500 mb-1">Total</p>
                <p className="text-xl font-bold text-slate-900">{validationSummary?.total ?? 0}</p>
              </div>
              <div className="bg-slate-50/80 rounded-xl p-3 border border-slate-200/50">
                <p className="text-xs text-slate-500 mb-1">Valid</p>
                <p className="text-xl font-bold text-emerald-600">{validationSummary?.valid ?? 0}</p>
              </div>
            </div>

            <div className="bg-slate-50/80 rounded-xl p-4 border border-slate-200/50">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-600">Flagged</span>
                <span className={`text-sm font-bold ${
                  (validationSummary?.flagged || 0) > 0 ? 'text-amber-600' : 'text-emerald-600'
                }`}>
                  {validationSummary?.flagged ?? 0} ({validationSummary?.flagged_percentage?.toFixed(1) ?? 0}%)
                </span>
              </div>
            </div>

            {wastedSpendAlerts && wastedSpendAlerts.length > 0 ? (
              <div className="bg-red-50/80 rounded-xl p-4 border border-red-200/50">
                <p className="text-xs font-semibold text-red-700 uppercase tracking-wider mb-2">Alerts</p>
                {wastedSpendAlerts.map((alert, index) => (
                  <p key={index} className="text-xs text-red-600">{alert}</p>
                ))}
              </div>
            ) : (
              <div className="bg-emerald-50/80 rounded-xl p-4 border border-emerald-200/50">
                <p className="text-xs text-emerald-700">No wasted spend detected</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
