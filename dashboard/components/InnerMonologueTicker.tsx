'use client';

import { useEffect, useState } from 'react';
import { MessageSquareQuote, ChevronLeft, ChevronRight } from 'lucide-react';

interface InnerMonologueTickerProps {
  reactions: any[];
}

export default function InnerMonologueTicker({ reactions }: InnerMonologueTickerProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);

  const quotes = reactions
    .filter(r => r.reasoning && r.reasoning.includes('[Gut]'))
    .map(r => {
      const gutMatch = r.reasoning.match(/\[Gut\]([\s\S]*?)(\[|$)/);
      const quote = gutMatch ? gutMatch[1].trim() : r.reasoning.substring(0, 150);
      return {
        text: quote.length > 250 ? quote.substring(0, 250) + '...' : quote,
        emotion: r.emotional_response || 'Neutral',
        adId: r.ad_id,
      };
    })
    .slice(0, 10);

  useEffect(() => {
    if (quotes.length === 0 || !isAutoPlaying) return;
    
    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % quotes.length);
    }, 6000);

    return () => clearInterval(interval);
  }, [quotes.length, isAutoPlaying]);

  if (quotes.length === 0) return null;

  const handlePrev = () => {
    setIsAutoPlaying(false);
    setCurrentIndex((prev) => (prev - 1 + quotes.length) % quotes.length);
  };

  const handleNext = () => {
    setIsAutoPlaying(false);
    setCurrentIndex((prev) => (prev + 1) % quotes.length);
  };

  const adColors: { [key: string]: string } = {
    ad_1: 'bg-indigo-500',
    ad_2: 'bg-purple-500',
    ad_3: 'bg-emerald-500',
    ad_4: 'bg-amber-500',
  };

  return (
    <section className="animate-in" style={{ animationDelay: '600ms' }}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Inner Monologue</h2>
          <p className="text-sm text-slate-500 mt-1">Real reactions from the simulation</p>
        </div>
      </div>

      <div className="relative glass rounded-3xl border border-white/50 p-8 overflow-hidden">
        {/* Background decoration */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-indigo-500/5 to-purple-500/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
        
        <div className="relative">
          <div className="flex items-start gap-6">
            <div className="hidden sm:flex w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 items-center justify-center shadow-lg shadow-indigo-500/25 flex-shrink-0">
              <MessageSquareQuote className="w-7 h-7 text-white" strokeWidth={1.5} />
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="min-h-[80px] flex items-center">
                <p className="text-lg text-slate-700 leading-relaxed italic">
                  "{quotes[currentIndex].text}"
                </p>
              </div>
              
              <div className="flex flex-wrap items-center gap-3 mt-4">
                <div className={`w-8 h-8 rounded-lg ${adColors[quotes[currentIndex].adId]} flex items-center justify-center`}>
                  <span className="text-white text-xs font-bold">{quotes[currentIndex].adId.replace('ad_', '')}</span>
                </div>
                <span className="text-sm text-slate-500">
                  Response to {quotes[currentIndex].adId.replace('ad_', 'Ad ')}
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200/50">
                  {quotes[currentIndex].emotion}
                </span>
              </div>
            </div>

            {/* Navigation */}
            <div className="hidden sm:flex items-center gap-2">
              <button
                onClick={handlePrev}
                className="w-10 h-10 rounded-xl bg-slate-100/80 hover:bg-slate-200/80 flex items-center justify-center transition-colors border border-slate-200/50"
              >
                <ChevronLeft className="w-5 h-5 text-slate-600" strokeWidth={2} />
              </button>
              <button
                onClick={handleNext}
                className="w-10 h-10 rounded-xl bg-slate-100/80 hover:bg-slate-200/80 flex items-center justify-center transition-colors border border-slate-200/50"
              >
                <ChevronRight className="w-5 h-5 text-slate-600" strokeWidth={2} />
              </button>
            </div>
          </div>

          {/* Progress dots */}
          <div className="flex items-center justify-center gap-2 mt-6">
            {quotes.map((_, index) => (
              <button
                key={index}
                onClick={() => {
                  setIsAutoPlaying(false);
                  setCurrentIndex(index);
                }}
                className={`h-2 rounded-full transition-all duration-300 ${
                  index === currentIndex 
                    ? 'w-8 bg-gradient-to-r from-indigo-500 to-purple-500' 
                    : 'w-2 bg-slate-300 hover:bg-slate-400'
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
