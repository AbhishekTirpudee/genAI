import React from 'react';
import { History, Download, Trash2, ExternalLink } from 'lucide-react';
import { downloadPngFromBase64 } from '../services/api';

export default function HistoryGallery({
  history,
  onSelectImage,
  selectedImage,
  onClearHistory
}) {
  if (!history || history.length === 0) return null;

  return (
    <div className="border border-slate-800 rounded-2xl bg-[#0a0d14]/60 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-purple-400" />
          <h3 className="text-sm font-semibold text-slate-200">Session Gallery</h3>
          <span className="text-xs text-slate-500 font-mono">({history.length})</span>
        </div>
        <button
          onClick={onClearHistory}
          className="text-xs text-slate-400 hover:text-red-400 transition-colors flex items-center gap-1 p-1"
          title="Clear session gallery"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Clear</span>
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
        {history.map((item, idx) => {
          const isSelected = selectedImage?.image_base64 === item.image_base64;
          return (
            <div
              key={idx}
              className={`group relative rounded-xl overflow-hidden border aspect-square cursor-pointer transition-all ${
                isSelected
                  ? 'border-purple-500 ring-2 ring-purple-500/50 shadow-lg shadow-purple-900/30'
                  : 'border-slate-800 hover:border-slate-600 bg-black'
              }`}
              onClick={() => onSelectImage(item)}
            >
              <img
                src={`data:image/png;base64,${item.image_base64}`}
                alt={item.prompt}
                className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-between p-2">
                <span className="text-[10px] text-purple-300 font-semibold truncate bg-black/60 px-1.5 py-0.5 rounded self-start">
                  {item.style}
                </span>
                <div className="flex items-center justify-between text-white">
                  <span className="text-[10px] truncate max-w-[80px]">
                    {item.prompt}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      const sanitized = (item.prompt || "artwork").replace(/[^a-z0-9]/g, "-").slice(0, 24);
                      downloadPngFromBase64(item.image_base64, `dreamcanvas-${sanitized}.png`);
                    }}
                    className="p-1 rounded bg-purple-600 hover:bg-purple-500 text-white shadow"
                    title="Download PNG"
                  >
                    <Download className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

