import React from 'react';
import { Layers, Wifi, Cpu, Globe } from 'lucide-react';

function Navbar() {
    return (
        <nav className="w-full max-w-[1000px] glass-card px-6 py-3 mb-5 flex justify-between items-center z-20 animate-fade-in bg-slate-950/20">
            {/* Brand Logo & Title */}
            <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center shadow-md shadow-indigo-500/20">
                    <Layers className="w-4 h-4 text-white" />
                </div>
                <span className="font-semibold text-sm tracking-tight text-white flex items-center gap-1.5 select-none">
                    Zoho Projects AI <span className="text-[10px] py-0.5 px-1.5 rounded bg-indigo-500/20 text-indigo-300 font-medium">v1.0</span>
                </span>
            </div>

            {/* Nav Middle Badges */}
            <div className="hidden sm:flex items-center gap-6 text-[11px] font-medium text-slate-400">
                <span className="flex items-center gap-1.5 text-indigo-400 cursor-default select-none">
                    <Cpu className="w-3.5 h-3.5" /> Llama-3.3 Brain
                </span>
                <span className="flex items-center gap-1.5 text-slate-300 cursor-default select-none">
                    <Globe className="w-3.5 h-3.5" /> Zoho India Server
                </span>
            </div>

            {/* Pulsating Connection Status */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold tracking-wider uppercase select-none shadow-sm shadow-emerald-500/5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping"></span>
                <Wifi className="w-3.5 h-3.5" /> Live
            </div>
        </nav>
    );
}

export default Navbar;
