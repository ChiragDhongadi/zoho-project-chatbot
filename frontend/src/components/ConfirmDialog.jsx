import React from 'react';
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

function ConfirmDialog({ action, onConfirm, onDecline }) {
    if (!action) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md animate-fade-in">
            <div className="w-[480px] max-w-[90%] p-8 glass-card border-amber-500/20 shadow-2xl shadow-amber-500/5 text-center flex flex-col items-center">
                {/* Animated Warning Icon */}
                <div className="w-14 h-14 rounded-full bg-amber-500/10 flex items-center justify-center mb-5 text-amber-500 animate-pulse">
                    <AlertTriangle className="w-7 h-7" />
                </div>

                <h3 className="text-xl font-semibold text-slate-100 mb-2">
                    HIL Security Gate
                </h3>
                <p className="text-slate-400 text-sm mb-6 leading-relaxed">
                    The Action Agent has intercepted a write operation. Please review the details below before authorizing execution:
                </p>

                {/* Highlighted payload container */}
                <div className="w-full text-left bg-slate-950/80 p-5 rounded-xl border border-white/5 font-mono text-xs text-amber-400 mb-6 overflow-x-auto whitespace-pre-wrap max-h-48">
                    {action.description || JSON.stringify(action, null, 2)}
                </div>

                {/* Glow Action buttons */}
                <div className="flex gap-4 w-full">
                    <button
                        onClick={() => onDecline()}
                        className="flex-1 py-3 px-4 rounded-xl border border-white/10 hover:bg-rose-500/10 hover:border-rose-500/20 text-rose-400 hover:text-rose-300 font-medium transition-all duration-300 flex items-center justify-center gap-2 cursor-pointer"
                    >
                        <XCircle className="w-4 h-4" /> Cancel
                    </button>

                    <button
                        onClick={() => onConfirm()}
                        className="flex-1 py-3 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium shadow-lg shadow-emerald-600/20 hover:shadow-emerald-500/30 transition-all duration-300 flex items-center justify-center gap-2 cursor-pointer"
                    >
                        <CheckCircle className="w-4 h-4" /> Confirm & Run
                    </button>
                </div>
            </div>
        </div>
    );
}

export default ConfirmDialog;
