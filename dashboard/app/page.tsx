'use client';

import { useEffect, useState } from 'react';
import PulseSection from '../components/PulseSection';
import BattlefieldSection from '../components/BattlefieldSection';
import PortfolioSection from '../components/PortfolioSection';
import InnerMonologueTicker from '../components/InnerMonologueTicker';
import CreativeRecommender from '../components/CreativeRecommender';
import DecisionHero from '../components/DecisionHero';
import PersonaExplorer from '../components/PersonaExplorer';
import CoverageInsights from '../components/CoverageInsights';

interface SimulationData {
  winning_portfolio: any[];
  all_performances: any;
  segment_ownership: any;
  audience_segments: any;
  overlap_matrix: any;
  wasted_spend_alerts: string[];
  validation_summary: any;
  metadata: any;
}

interface ReactionData {
  persona_uuid: string;
  ad_id: string;
  reasoning: string;
  emotional_response: string;
  trust_score: number;
  relevance_score: number;
  action: string;
  barriers?: string[];
}

export default function Dashboard() {
  const [simulationData, setSimulationData] = useState<SimulationData | null>(null);
  const [reactionData, setReactionData] = useState<ReactionData[]>([]);
  const [signalReactions, setSignalReactions] = useState<ReactionData[]>([]);
  const [personaData, setPersonaData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch('/data/simulation_report.json').then((res) => res.json()),
      fetch('/data/raw_reactions.json').then((res) => res.json()),
      fetch('/data/enriched_personas.json').then((res) => res.json()),
    ])
      .then(([simulation, reactions, personas]) => {
        setSimulationData(simulation);
        setReactionData(reactions);
        setSignalReactions(
          reactions.filter(
            (r: ReactionData) => r.action === 'CLICK' && r.reasoning !== 'Fallback heuristic'
          )
        );
        setPersonaData(personas);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error loading dashboard data:', err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
          <p className="text-slate-600 font-medium">Loading simulation data...</p>
        </div>
      </div>
    );
  }

  if (!simulationData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="glass rounded-2xl p-8 text-center">
          <p className="text-slate-700 font-medium">Error loading data</p>
        </div>
      </div>
    );
  }

  const totalReactions = simulationData.metadata?.total_reactions || 0;
  const validReactions = simulationData.metadata?.valid_reactions || 0;
  const confidenceScore =
    totalReactions > 0 ? Math.round((validReactions / totalReactions) * 100) : 0;

  const totalClicks = Object.values(simulationData.all_performances).reduce(
    (sum: number, perf: any) => sum + perf.clicks,
    0
  );
  const theoreticalMinCAC = totalClicks > 0 ? Math.round(10000 / totalClicks) : 0;

  const totalUniqueReach = Object.values(simulationData.all_performances).reduce(
    (sum: number, perf: any) => sum + perf.unique_reach,
    0
  );
  const personaCount = simulationData.metadata?.num_personas || 0;
  const marketSaturation =
    personaCount > 0 ? Math.min(100, Math.round((totalUniqueReach / personaCount) * 100)) : 0;

  const avgTrustScore =
    reactionData.length > 0
      ? reactionData.reduce((sum, r) => sum + r.trust_score, 0) / reactionData.length
      : 0;

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-white/20">
        <div className="max-w-[1600px] mx-auto px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
                <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h1 className="text-lg font-semibold text-slate-900">
                  Oh So U Adset Audit
                </h1>
                <p className="text-xs text-slate-500">Pre-Flight Simulation</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-50 border border-emerald-200">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span className="text-sm font-medium text-emerald-700">
                  {confidenceScore}% Confidence
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1600px] mx-auto px-6 lg:px-8 py-8 space-y-8">
        <DecisionHero
          portfolio={simulationData.winning_portfolio}
          segmentOwnership={simulationData.segment_ownership}
          performances={simulationData.all_performances}
          confidenceScore={confidenceScore}
          metadata={simulationData.metadata}
        />

        <PulseSection
          theoreticalMinCAC={theoreticalMinCAC}
          marketSaturation={marketSaturation}
          trustBaseline={avgTrustScore}
        />

        <BattlefieldSection
          performances={simulationData.all_performances}
          reactionData={signalReactions}
        />

        <PortfolioSection
          portfolio={simulationData.winning_portfolio}
          segmentOwnership={simulationData.segment_ownership}
        />

        <CoverageInsights
          audienceSegments={simulationData.audience_segments}
          overlapMatrix={simulationData.overlap_matrix}
          validationSummary={simulationData.validation_summary}
          wastedSpendAlerts={simulationData.wasted_spend_alerts}
        />

        <PersonaExplorer personas={personaData} reactions={reactionData} />

        <InnerMonologueTicker reactions={signalReactions} />
      </main>

      <CreativeRecommender />
    </div>
  );
}
