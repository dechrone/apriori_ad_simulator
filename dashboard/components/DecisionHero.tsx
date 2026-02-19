'use client';

import { Crown, Zap, Users, Timer, ChevronRight } from 'lucide-react';

interface DecisionHeroProps {
  portfolio: any[];
  segmentOwnership: any;
  performances: any;
  confidenceScore: number;
  metadata: any;
}

export default function DecisionHero({
  portfolio,
  segmentOwnership,
  performances,
  confidenceScore,
  metadata,
}: DecisionHeroProps) {
  const winner = portfolio?.[0];
  const winnerSegment = winner
    ? (Object.values(segmentOwnership).find((s: any) => s.winning_ad === winner.ad_id) as any)
    : null;
  const winnerPerf = winner ? performances?.[winner.ad_id] : null;

  const reasons = winner?.reasoning
    ? winner.reasoning.split(' \u2022 ').filter(Boolean)
    : [];

  return (
    <section className="animate-in">
      <div className="relative overflow-hidden rounded-3xl hero-gradient p-8 lg:p-10">
        {/* Decorative elements */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-gradient-to-tr from-blue-500/10 to-cyan-500/10 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />
        
        <div className="relative z-10">
          {/* Top badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/10 mb-6">
            <Crown className="w-4 h-4 text-amber-400" strokeWidth={2} />
            <span className="text-sm font-medium text-white/90">Winning Creative</span>
          </div>

          <div className="flex flex-col lg:flex-row lg:items-start gap-8">
            {/* Left side - Main info */}
            <div className="flex-1">
              <h2 className="text-3xl lg:text-4xl font-bold text-white mb-3">
                {winner ? winner.ad_id.replace('ad_', 'Ad ') : 'Loading...'}
              </h2>
              <p className="text-xl text-indigo-200 font-medium mb-4">
                {winner?.role || 'Analyzing...'}
              </p>
              <p className="text-white/70 text-sm leading-relaxed max-w-xl mb-6">
                {winner?.target_segment || 'Target segment analysis in progress'}
              </p>

              {/* Stats row */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/10">
                  <p className="text-xs text-white/50 uppercase tracking-wider mb-1">Budget</p>
                  <p className="text-2xl font-bold text-white">{winner?.budget_split || 0}%</p>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/10">
                  <p className="text-xs text-white/50 uppercase tracking-wider mb-1">Conversions</p>
                  <p className="text-2xl font-bold text-white">{winner?.expected_conversions || 0}</p>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/10">
                  <p className="text-xs text-white/50 uppercase tracking-wider mb-1">Conv. Rate</p>
                  <p className="text-2xl font-bold text-white">
                    {winnerSegment?.conversion_rate ? `${Math.round(winnerSegment.conversion_rate)}%` : '--'}
                  </p>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/10">
                  <p className="text-xs text-white/50 uppercase tracking-wider mb-1">Trust Score</p>
                  <p className="text-2xl font-bold text-white">
                    {winnerSegment?.trust_score || '--'}<span className="text-base text-white/50">/10</span>
                  </p>
                </div>
              </div>
            </div>

            {/* Right side - Why it wins */}
            <div className="lg:w-80">
              <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
                <div className="flex items-center gap-2 mb-4">
                  <Zap className="w-4 h-4 text-amber-400" strokeWidth={2} />
                  <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Why It Wins</h3>
                </div>
                <ul className="space-y-3">
                  {reasons.length > 0 ? (
                    reasons.map((reason: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-3 text-sm text-white/80">
                        <ChevronRight className="w-4 h-4 text-indigo-400 mt-0.5 flex-shrink-0" strokeWidth={2} />
                        <span>{reason}</span>
                      </li>
                    ))
                  ) : (
                    <li className="text-sm text-white/60">Analysis loading...</li>
                  )}
                </ul>
              </div>
            </div>
          </div>

          {/* Bottom row - Quick stats */}
          <div className="mt-8 pt-6 border-t border-white/10">
            <div className="flex flex-wrap items-center gap-6 text-sm">
              <div className="flex items-center gap-2 text-white/60">
                <Users className="w-4 h-4" strokeWidth={1.5} />
                <span>{metadata?.num_personas || 0} Personas</span>
              </div>
              <div className="flex items-center gap-2 text-white/60">
                <Zap className="w-4 h-4" strokeWidth={1.5} />
                <span>{metadata?.num_ads || 0} Ads Tested</span>
              </div>
              <div className="flex items-center gap-2 text-white/60">
                <Timer className="w-4 h-4" strokeWidth={1.5} />
                <span>{metadata?.execution_time_seconds ? `${Math.round(metadata.execution_time_seconds)}s runtime` : '--'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
