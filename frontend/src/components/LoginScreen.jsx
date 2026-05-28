import React from 'react';
import { Shield, Sparkles, Database, Layers } from 'lucide-react';

function LoginScreen() {
    const handleLogin = () => {
        // Redirect to the FastAPI Backend OAuth entrance!
        window.location.href = 'http://localhost:8000/auth/login';
    };

    return (
        <div className="z-10 w-[460px] max-w-[90%] p-8 glass-card animate-fade-in flex flex-col items-center text-center">
            {/* Sleek App Icon Container */}
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center mb-6 shadow-lg shadow-indigo-500/20">
                <Layers className="w-8 h-8 text-white" />
            </div>

            <h1 className="text-3xl font-bold tracking-tight text-white mb-2">
                Zoho Projects AI
            </h1>
            <p className="text-slate-400 text-sm mb-8 leading-relaxed">
                Connect your Zoho account and chat with your projects using a multi-agent stateful graph.
            </p>

            {/* Feature list */}
            <div className="w-full text-left space-y-4 mb-8 bg-slate-900/40 p-5 rounded-xl border border-white/5">
                <div className="flex items-start gap-3">
                    <Sparkles className="w-5 h-5 text-indigo-400 mt-0.5" />
                    <div>
                        <h4 className="text-sm font-medium text-slate-200">Multi-Agent Brain</h4>
                        <p className="text-xs text-slate-400">Coordinated Query and Action specialists powered by Groq.</p>
                    </div>
                </div>

                <div className="flex items-start gap-3">
                    <Shield className="w-5 h-5 text-indigo-400 mt-0.5" />
                    <div>
                        <h4 className="text-sm font-medium text-slate-200">Human-In-The-Loop</h4>
                        <p className="text-xs text-slate-400">All task updates and deletions require your explicit confirmation.</p>
                    </div>
                </div>

                <div className="flex items-start gap-3">
                    <Database className="w-5 h-5 text-indigo-400 mt-0.5" />
                    <div>
                        <h4 className="text-sm font-medium text-slate-200">Long-Term Memory</h4>
                        <p className="text-xs text-slate-400">Persists your preferred projects and context automatically across logins.</p>
                    </div>
                </div>
            </div>

            {/* Login Button */}
            <button
                onClick={handleLogin}
                className="w-full py-3.5 px-6 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow-lg shadow-indigo-600/30 transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
            >
                Sign In with Zoho
            </button>

            <span className="text-[10px] text-slate-500 mt-4">
                Deploying to Zoho India Region (.in accounts)
            </span>
        </div>
    );
}

export default LoginScreen;
