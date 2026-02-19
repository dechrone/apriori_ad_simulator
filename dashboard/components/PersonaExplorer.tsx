'use client';

import { useMemo, useState } from 'react';
import { Briefcase, MapPin, Search, Shield, UserRound, ChevronDown, Wallet, Smartphone, Globe } from 'lucide-react';

interface PersonaExplorerProps {
  personas: any[];
  reactions: any[];
}

const getPersonaName = (professionalPersona: string, fallback?: string) => {
  if (!professionalPersona) return fallback || 'Persona';
  const name = professionalPersona.split(',')[0]?.trim();
  return name || fallback || 'Persona';
};

const formatList = (value?: string) => {
  if (!value) return '--';
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
    .join(', ');
};

const formatCurrency = (value: number) => {
  if (!value && value !== 0) return '--';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

export default function PersonaExplorer({ personas, reactions }: PersonaExplorerProps) {
  const [activeId, setActiveId] = useState(personas?.[0]?.uuid ?? '');
  const [query, setQuery] = useState('');

  const filteredPersonas = useMemo(() => {
    if (!query) return personas;
    const search = query.toLowerCase();
    return personas.filter((p: any) => {
      const name = getPersonaName(p.professional_persona, p.occupation).toLowerCase();
      return (
        name.includes(search) ||
        p.occupation?.toLowerCase().includes(search) ||
        p.first_language?.toLowerCase().includes(search) ||
        p.state?.toLowerCase().includes(search) ||
        p.district?.toLowerCase().includes(search)
      );
    });
  }, [personas, query]);

  const activePersona = useMemo(() => {
    return filteredPersonas.find((p: any) => p.uuid === activeId) || filteredPersonas[0];
  }, [filteredPersonas, activeId]);

  const personaReactions = useMemo(() => {
    if (!activePersona) return [];
    return reactions.filter((r: any) => r.persona_uuid === activePersona.uuid);
  }, [activePersona, reactions]);

  const actionSummary = useMemo(() => {
    return personaReactions.reduce(
      (acc: any, item: any) => {
        acc[item.action] = (acc[item.action] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>
    );
  }, [personaReactions]);

  if (!activePersona) return null;

  const adColors: { [key: string]: string } = {
    ad_1: 'bg-indigo-500',
    ad_2: 'bg-purple-500',
    ad_3: 'bg-emerald-500',
    ad_4: 'bg-amber-500',
  };

  return (
    <section className="animate-in" style={{ animationDelay: '500ms' }}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Persona Intelligence</h2>
          <p className="text-sm text-slate-500 mt-1">Click personas to explore their reactions</p>
        </div>
      </div>

      <div className="glass rounded-3xl border border-white/50 overflow-hidden">
        <div className="flex flex-col lg:flex-row">
          {/* Sidebar - Persona List */}
          <div className="lg:w-80 border-b lg:border-b-0 lg:border-r border-slate-200/50">
            <div className="p-4">
              <div className="relative">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" strokeWidth={2} />
                <input
                  type="text"
                  placeholder="Search personas..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 text-sm bg-slate-50/80 border border-slate-200/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/50 transition-all"
                />
              </div>
            </div>
            <div className="max-h-[500px] overflow-y-auto scrollbar-thin px-4 pb-4 space-y-2">
              {filteredPersonas.map((persona: any) => {
                const name = getPersonaName(persona.professional_persona, persona.occupation);
                const isActive = persona.uuid === activePersona.uuid;
                const pReactions = reactions.filter((r: any) => r.persona_uuid === persona.uuid);
                const clickCount = pReactions.filter((r: any) => r.action === 'CLICK').length;

                return (
                  <button
                    key={persona.uuid}
                    onClick={() => setActiveId(persona.uuid)}
                    className={`w-full text-left rounded-xl p-4 transition-all duration-200 ${
                      isActive
                        ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/25'
                        : 'bg-slate-50/80 hover:bg-slate-100/80 border border-slate-200/50'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                        isActive ? 'bg-white/20' : 'bg-white border border-slate-200/50'
                      }`}>
                        <UserRound className={`w-5 h-5 ${isActive ? 'text-white' : 'text-indigo-500'}`} strokeWidth={1.5} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm font-semibold truncate ${isActive ? 'text-white' : 'text-slate-900'}`}>
                          {name}
                        </p>
                        <p className={`text-xs truncate ${isActive ? 'text-white/70' : 'text-slate-500'}`}>
                          {persona.age}yo {persona.sex} • {persona.district}
                        </p>
                      </div>
                      <div className={`px-2 py-1 rounded-md text-xs font-medium ${
                        isActive 
                          ? 'bg-white/20 text-white' 
                          : clickCount > 0 
                            ? 'bg-emerald-50 text-emerald-600' 
                            : 'bg-slate-100 text-slate-500'
                      }`}>
                        {clickCount} clicks
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Main content - Persona Detail */}
          <div className="flex-1 p-6 lg:p-8">
            {/* Header */}
            <div className="flex flex-wrap items-start justify-between gap-4 mb-8">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
                  <UserRound className="w-8 h-8 text-white" strokeWidth={1.5} />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-slate-900">
                    {getPersonaName(activePersona.professional_persona, activePersona.occupation)}
                  </h3>
                  <div className="flex flex-wrap items-center gap-3 mt-1 text-sm text-slate-500">
                    <span className="flex items-center gap-1">
                      <Briefcase className="w-4 h-4" strokeWidth={1.5} />
                      {activePersona.occupation}
                    </span>
                    <span className="flex items-center gap-1">
                      <MapPin className="w-4 h-4" strokeWidth={1.5} />
                      {activePersona.district}, {activePersona.state}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-3 py-1.5 rounded-full text-xs font-medium ${
                  actionSummary.CLICK > 0 
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                    : 'bg-slate-50 text-slate-600 border border-slate-200'
                }`}>
                  {actionSummary.CLICK || 0} Clicks
                </span>
                <span className="px-3 py-1.5 rounded-full text-xs font-medium bg-slate-50 text-slate-600 border border-slate-200">
                  {actionSummary.IGNORE || 0} Ignores
                </span>
              </div>
            </div>

            {/* Quick stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <div className="bg-slate-50/80 rounded-2xl p-4 border border-slate-200/50">
                <div className="flex items-center gap-2 mb-2">
                  <Wallet className="w-4 h-4 text-slate-400" strokeWidth={1.5} />
                  <span className="text-xs text-slate-500">Income</span>
                </div>
                <p className="text-lg font-bold text-slate-900">{formatCurrency(activePersona.monthly_income_inr)}</p>
              </div>
              <div className="bg-slate-50/80 rounded-2xl p-4 border border-slate-200/50">
                <div className="flex items-center gap-2 mb-2">
                  <Smartphone className="w-4 h-4 text-slate-400" strokeWidth={1.5} />
                  <span className="text-xs text-slate-500">Digital Score</span>
                </div>
                <p className="text-lg font-bold text-slate-900">{activePersona.digital_literacy}/10</p>
              </div>
              <div className="bg-slate-50/80 rounded-2xl p-4 border border-slate-200/50">
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="w-4 h-4 text-slate-400" strokeWidth={1.5} />
                  <span className="text-xs text-slate-500">Scam Risk</span>
                </div>
                <p className="text-lg font-bold text-slate-900">{activePersona.scam_vulnerability}</p>
              </div>
              <div className="bg-slate-50/80 rounded-2xl p-4 border border-slate-200/50">
                <div className="flex items-center gap-2 mb-2">
                  <Globe className="w-4 h-4 text-slate-400" strokeWidth={1.5} />
                  <span className="text-xs text-slate-500">Zone</span>
                </div>
                <p className="text-lg font-bold text-slate-900">{activePersona.zone}</p>
              </div>
            </div>

            {/* Persona details */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
              <div className="bg-white/80 rounded-2xl p-4 border border-slate-200/50">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Demographics</p>
                <div className="space-y-2 text-sm text-slate-700">
                  <p>
                    <span className="text-slate-500">Age:</span> {activePersona.age}
                  </p>
                  <p>
                    <span className="text-slate-500">Sex:</span> {activePersona.sex}
                  </p>
                  <p>
                    <span className="text-slate-500">Marital:</span> {activePersona.marital_status || '--'}
                  </p>
                  <p>
                    <span className="text-slate-500">Education:</span> {activePersona.education_level || '--'}
                  </p>
                </div>
              </div>
              <div className="bg-white/80 rounded-2xl p-4 border border-slate-200/50">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Language & Device</p>
                <div className="space-y-2 text-sm text-slate-700">
                  <p>
                    <span className="text-slate-500">Language:</span> {activePersona.first_language || '--'}
                  </p>
                  <p>
                    <span className="text-slate-500">Secondary:</span> {activePersona.second_language || '--'}
                  </p>
                  <p>
                    <span className="text-slate-500">Device:</span> {activePersona.primary_device || '--'}
                  </p>
                </div>
              </div>
              <div className="bg-white/80 rounded-2xl p-4 border border-slate-200/50 md:col-span-2">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Interests & Skills</p>
                <div className="space-y-2 text-sm text-slate-700">
                  <p>
                    <span className="text-slate-500">Interests:</span>{' '}
                    {formatList(activePersona.hobbies_and_interests_list || activePersona.hobbies_and_interests)}
                  </p>
                  <p>
                    <span className="text-slate-500">Skills:</span>{' '}
                    {formatList(activePersona.skills_and_expertise_list || activePersona.skills_and_expertise)}
                  </p>
                </div>
              </div>
            </div>

            {/* Professional summary */}
            <div className="mb-8">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Professional Profile</p>
              <p className="text-sm text-slate-700 leading-relaxed">
                {activePersona.professional_persona || 'No professional narrative available.'}
              </p>
            </div>

            {/* Reactions */}
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">Ad Reactions</p>
              <div className="space-y-3">
                {personaReactions.map((reaction: any, index: number) => (
                  <details 
                    key={`${reaction.ad_id}-${index}`} 
                    className="group bg-slate-50/80 rounded-2xl border border-slate-200/50 overflow-hidden"
                  >
                    <summary className="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-100/80 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-xl ${adColors[reaction.ad_id]} flex items-center justify-center text-white font-bold`}>
                          {reaction.ad_id.replace('ad_', '')}
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-slate-900">{reaction.ad_id.replace('ad_', 'Ad ')}</p>
                          <p className="text-xs text-slate-500">{reaction.emotional_response}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          reaction.action === 'CLICK'
                            ? 'bg-emerald-100 text-emerald-700'
                            : 'bg-slate-200 text-slate-600'
                        }`}>
                          {reaction.action}
                        </span>
                        <div className="flex items-center gap-2 text-xs text-slate-500">
                          <span>Trust {reaction.trust_score}/10</span>
                          <span>Greed {reaction.relevance_score}/10</span>
                        </div>
                        <ChevronDown className="w-4 h-4 text-slate-400 group-open:rotate-180 transition-transform" strokeWidth={2} />
                      </div>
                    </summary>
                    <div className="px-4 pb-4 pt-2 border-t border-slate-200/50">
                      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Internal Monologue</p>
                      <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{reaction.reasoning}</p>
                      {reaction.barriers?.length > 0 && (
                        <div className="mt-4">
                          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Barriers</p>
                          <div className="flex flex-wrap gap-2">
                            {reaction.barriers.map((barrier: string, idx: number) => (
                              <span
                                key={idx}
                                className="text-xs bg-red-50 text-red-700 px-3 py-1 rounded-full border border-red-100"
                              >
                                {barrier}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </details>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
