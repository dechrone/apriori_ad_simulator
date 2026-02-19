'use client';

import { useState } from 'react';
import { Sparkles, X, TrendingUp, AlertTriangle, Lightbulb, ChevronRight } from 'lucide-react';

export default function CreativeRecommender() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Floating button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-2xl shadow-lg shadow-indigo-500/40 flex items-center justify-center transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-indigo-500/50 z-50 group"
        >
          <Sparkles className="w-6 h-6 group-hover:rotate-12 transition-transform" strokeWidth={2} />
        </button>
      )}

      {/* Sidebar panel */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 bg-slate-900/20 backdrop-blur-sm z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="fixed inset-y-0 right-0 w-full max-w-md glass-dark border-l border-white/10 shadow-2xl z-50 overflow-hidden">
            <div className="h-full flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-white/10">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-white" strokeWidth={2} />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">AI Recommendations</h3>
                    <p className="text-xs text-slate-400">Creative optimization suggestions</p>
                  </div>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="w-10 h-10 rounded-xl bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
                >
                  <X className="w-5 h-5 text-white" strokeWidth={2} />
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin">
                {/* Primary recommendation */}
                <div className="bg-gradient-to-br from-amber-500/20 to-orange-500/20 rounded-2xl p-5 border border-amber-500/30">
                  <div className="flex items-start gap-3 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center flex-shrink-0">
                      <AlertTriangle className="w-5 h-5 text-white" strokeWidth={1.5} />
                    </div>
                    <div>
                      <h4 className="text-base font-semibold text-white">Fix Ad 4 in 2 Minutes</h4>
                      <p className="text-sm text-slate-300 mt-1">Low trust among skeptical managers</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <p className="text-xs font-semibold text-amber-300 uppercase tracking-wider mb-2">AI Suggestion</p>
                      <div className="bg-white/10 rounded-xl p-4 border border-white/10">
                        <p className="text-sm text-white mb-2">
                          Change "0 Lost in FX Charges" to "Minimize FX Leakage"
                        </p>
                        <p className="text-xs text-slate-400">
                          The "zero" claim triggers skepticism. "Minimize" is more credible.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 bg-emerald-500/20 rounded-xl p-3 border border-emerald-500/30">
                      <TrendingUp className="w-5 h-5 text-emerald-400" strokeWidth={2} />
                      <div>
                        <span className="text-sm font-semibold text-emerald-400">+15% Trust</span>
                        <span className="text-xs text-slate-400 ml-2">predicted impact</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Other recommendations */}
                <div className="space-y-3">
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Other Optimizations</p>
                  
                  <div className="bg-white/5 rounded-2xl p-4 border border-white/10 hover:bg-white/10 transition-colors cursor-pointer group">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-lg bg-purple-500 flex items-center justify-center text-white font-bold text-sm">2</div>
                        <div>
                          <p className="text-sm font-medium text-white">Amplify Compliance</p>
                          <p className="text-xs text-slate-400 mt-1">Add "RBI OPGSP Certified" badge prominently</p>
                        </div>
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors" strokeWidth={2} />
                    </div>
                    <div className="mt-3 flex items-center gap-2">
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-400" strokeWidth={2} />
                      <span className="text-xs text-emerald-400 font-medium">+8% conversion in 45+ age group</span>
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-2xl p-4 border border-white/10 hover:bg-white/10 transition-colors cursor-pointer group">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center text-white font-bold text-sm">3</div>
                        <div>
                          <p className="text-sm font-medium text-white">Localize Messaging</p>
                          <p className="text-xs text-slate-400 mt-1">Test "Mumbai ka #1 Cross-Border Platform"</p>
                        </div>
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors" strokeWidth={2} />
                    </div>
                    <div className="mt-3 flex items-center gap-2">
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-400" strokeWidth={2} />
                      <span className="text-xs text-emerald-400 font-medium">+12% click rate in Urban High</span>
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-2xl p-4 border border-white/10">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center text-white font-bold text-sm">1</div>
                      <div>
                        <p className="text-sm font-medium text-white">Already Optimal</p>
                        <p className="text-xs text-slate-400 mt-1">No changes recommended. 77.8% conversion rate.</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Insights */}
                <div className="bg-white/5 rounded-2xl p-5 border border-white/10">
                  <div className="flex items-center gap-2 mb-4">
                    <Lightbulb className="w-4 h-4 text-amber-400" strokeWidth={2} />
                    <p className="text-sm font-semibold text-white">Key Insights</p>
                  </div>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between items-start">
                      <span className="text-slate-400">Top Barrier</span>
                      <span className="text-white text-right">"Too good to be true" skepticism</span>
                    </div>
                    <div className="h-px bg-white/10" />
                    <div className="flex justify-between items-start">
                      <span className="text-slate-400">Top Trust Signal</span>
                      <span className="text-white text-right">RBI regulatory mentions</span>
                    </div>
                    <div className="h-px bg-white/10" />
                    <div className="flex justify-between items-start">
                      <span className="text-slate-400">Best Segment</span>
                      <span className="text-white text-right">Middle Age 35-49, Urban, High</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}
