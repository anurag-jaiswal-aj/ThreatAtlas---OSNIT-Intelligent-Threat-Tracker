import React from 'react';
import { Search, AlertTriangle, ShieldAlert, ShieldCheck, MapPin, Calendar } from 'lucide-react';
import type { Event, EventFilters } from '../types';

interface FilterPanelProps {
  filters: EventFilters;
  onFilterChange: (filters: EventFilters) => void;
  events: Event[];
  selectedEvent: Event | null;
  onSelectEvent: (event: Event) => void;
  totalEventsCount: number;
}

export const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  onFilterChange,
  events,
  selectedEvent,
  onSelectEvent,
  totalEventsCount,
}) => {
  const highCount = events.filter((e) => e.threat_level === 'High').length;
  const medCount = events.filter((e) => e.threat_level === 'Medium').length;
  const lowCount = events.filter((e) => e.threat_level === 'Low').length;

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({ ...filters, search: e.target.value });
  };

  const handleThreatLevelSelect = (level?: string) => {
    onFilterChange({ ...filters, threat_level: level });
  };

  const handleMinThreatScoreChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({ ...filters, min_threat_score: Number(e.target.value) });
  };

  const handleToggleHideLowThreat = () => {
    const isHidden = filters.min_threat_score === 40;
    onFilterChange({ ...filters, min_threat_score: isHidden ? undefined : 40 });
  };

  return (
    <aside className="w-96 bg-slate-950/95 border-r border-slate-800/80 flex flex-col h-[calc(100vh-4rem)] z-20 backdrop-blur-md select-none">
      {/* Search & Filter Header */}
      <div className="p-4 border-b border-slate-800/80 space-y-3">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
          <input
            type="text"
            placeholder="Search events, keywords..."
            value={filters.search || ''}
            onChange={handleSearchChange}
            className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-all font-mono"
          />
        </div>

        {/* Threat Level Filter Tabs */}
        <div className="flex items-center gap-1 p-1 bg-slate-900/80 border border-slate-800/60 rounded-lg text-xs font-mono">
          <button
            onClick={() => handleThreatLevelSelect(undefined)}
            className={`flex-1 py-1.5 rounded text-center transition-all cursor-pointer ${
              !filters.threat_level
                ? 'bg-slate-800 text-slate-100 font-bold shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            All ({totalEventsCount})
          </button>
          <button
            onClick={() => handleThreatLevelSelect('High')}
            className={`flex-1 py-1.5 rounded text-center transition-all cursor-pointer ${
              filters.threat_level === 'High'
                ? 'bg-red-950/80 text-red-300 font-bold border border-red-800/60'
                : 'text-slate-400 hover:text-red-400'
            }`}
          >
            High ({highCount})
          </button>
          <button
            onClick={() => handleThreatLevelSelect('Medium')}
            className={`flex-1 py-1.5 rounded text-center transition-all cursor-pointer ${
              filters.threat_level === 'Medium'
                ? 'bg-amber-950/80 text-amber-300 font-bold border border-amber-800/60'
                : 'text-slate-400 hover:text-amber-400'
            }`}
          >
            Med ({medCount})
          </button>
          <button
            onClick={() => handleThreatLevelSelect('Low')}
            className={`flex-1 py-1.5 rounded text-center transition-all cursor-pointer ${
              filters.threat_level === 'Low'
                ? 'bg-emerald-950/80 text-emerald-300 font-bold border border-emerald-800/60'
                : 'text-slate-400 hover:text-emerald-400'
            }`}
          >
            Low ({lowCount})
          </button>
        </div>

        {/* Minimum Threat Score Slider */}
        <div className="pt-2 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-300">
            <label htmlFor="minThreatScoreSlider" className="font-semibold">
              Min Threat Score: {filters.min_threat_score ?? 0}
            </label>
            <button
              onClick={handleToggleHideLowThreat}
              aria-pressed={filters.min_threat_score === 40}
              className={`px-2 py-1 rounded transition-colors ${
                filters.min_threat_score === 40
                  ? 'bg-blue-600 hover:bg-blue-500 text-white'
                  : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
              }`}
            >
              Hide Low Threat (&lt;40)
            </button>
          </div>
          <input
            id="minThreatScoreSlider"
            type="range"
            min="0"
            max="100"
            step="5"
            value={filters.min_threat_score ?? 0}
            onChange={handleMinThreatScoreChange}
            aria-label="Minimum Threat Score"
            className="w-full accent-blue-500 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer"
          />
        </div>
      </div>

      {/* Quick Metrics Summary */}
      <div className="grid grid-cols-3 gap-2 p-4 border-b border-slate-800/60 font-mono text-center">
        <div className="bg-red-950/20 border border-red-900/30 p-2 rounded-md">
          <div className="flex items-center justify-center gap-1 text-red-400 text-[10px] uppercase">
            <ShieldAlert className="w-3 h-3" /> High
          </div>
          <div className="text-base font-bold text-red-400">{highCount}</div>
        </div>

        <div className="bg-amber-950/20 border border-amber-900/30 p-2 rounded-md">
          <div className="flex items-center justify-center gap-1 text-amber-400 text-[10px] uppercase">
            <AlertTriangle className="w-3 h-3" /> Medium
          </div>
          <div className="text-base font-bold text-amber-400">{medCount}</div>
        </div>

        <div className="bg-emerald-950/20 border border-emerald-900/30 p-2 rounded-md">
          <div className="flex items-center justify-center gap-1 text-emerald-400 text-[10px] uppercase">
            <ShieldCheck className="w-3 h-3" /> Low
          </div>
          <div className="text-base font-bold text-emerald-400">{lowCount}</div>
        </div>
      </div>

      {/* Event List Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
        <div className="flex items-center justify-between text-xs font-mono text-slate-400 px-1 mb-1">
          <span>INTELLIGENCE STREAM</span>
          <span>{events.length} DISPLAYED</span>
        </div>

        {events.length === 0 ? (
          <div className="text-center py-12 px-4 border border-dashed border-slate-800 rounded-lg text-slate-500 font-mono text-xs">
            No threat intelligence events match the current filter criteria.
          </div>
        ) : (
          events.map((evt) => {
            const isSelected = selectedEvent?.id === evt.id;
            let badgeStyle = 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60';
            if (evt.threat_level === 'High') {
              badgeStyle = 'bg-red-950/80 text-red-400 border-red-800/80 animate-pulse';
            } else if (evt.threat_level === 'Medium') {
              badgeStyle = 'bg-amber-950/60 text-amber-400 border-amber-800/60';
            }

            return (
              <div
                key={evt.id}
                onClick={() => onSelectEvent(evt)}
                className={`p-3 rounded-lg border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-slate-900 border-blue-500 shadow-md shadow-blue-950/40'
                    : 'bg-slate-900/50 border-slate-800/80 hover:bg-slate-900 hover:border-slate-700'
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <h3 className="text-xs font-semibold text-slate-200 line-clamp-1 leading-snug">
                    {evt.title}
                  </h3>
                  <span className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded border uppercase ${badgeStyle}`}>
                    {evt.threat_level} ({evt.threat_score})
                  </span>
                </div>

                <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400">
                  {evt.location_name && (
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-slate-500" />
                      {evt.location_name}
                    </span>
                  )}
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3 text-slate-500" />
                    {new Date(evt.event_timestamp).toLocaleDateString()}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
};
