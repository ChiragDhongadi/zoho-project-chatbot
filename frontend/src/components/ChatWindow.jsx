import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, LogOut, MessageSquare, Bot, User, Sparkles } from 'lucide-react';
import ConfirmDialog from './ConfirmDialog';

function ChatWindow({ sessionId, onLogout }) {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: '👋 **Welcome back!** I am your Zoho Projects Assistant. How can I help you check task loads or automate work today?' }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [pendingAction, setPendingAction] = useState(null);
    const [userEmail, setUserEmail] = useState('');
    const messagesEndRef = useRef(null);

    // Auto-scroll to bottom of thread on new messages
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, loading]);

    // Session verification on mount
    useEffect(() => {
        const verifySession = async () => {
            try {
                const response = await fetch(`http://localhost:8000/auth/session?session_id=${sessionId}`);
                if (!response.ok) {
                    onLogout();
                } else {
                    const data = await response.json();
                    setUserEmail(data.email || 'Zoho User');
                }
            } catch (err) {
                console.error('Session verification failed', err);
            }
        };
        verifySession();
    }, [sessionId]);

    const handleSend = async (e) => {
        e.preventDefault();
        const query = input.trim();
        if (!query || loading) return;

        setInput('');
        setMessages((prev) => [...prev, { role: 'user', content: query }]);
        setLoading(true);

        try {
            const response = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${sessionId}`
                },
                body: JSON.stringify({ message: query })
            });

            if (!response.ok) {
                throw new Error('API Error');
            }

            const data = await response.json();

            setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }]);

            // If a write tool execution is intercepted (HIL Gateway triggered), save payload!
            if (data.pending_action) {
                setPendingAction(data.pending_action);
            }
        } catch (err) {
            setMessages((prev) => [...prev, { role: 'assistant', content: '❌ Sorry, I encountered an error communicating with the agent backend. Please ensure the server is active.' }]);
        } finally {
            setLoading(false);
        }
    };

    // Human-in-the-Loop Gateway Choices
    const handleConfirmAction = async (confirmed) => {
        const actionPayload = pendingAction;
        setPendingAction(null); // Close modal first
        setLoading(true);

        try {
            const response = await fetch('http://localhost:8000/chat/confirm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${sessionId}`
                },
                body: JSON.stringify({ confirmed })
            });

            if (!response.ok) {
                throw new Error('HIL Resume failed');
            }

            const data = await response.json();
            setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }]);
        } catch (err) {
            setMessages((prev) => [...prev, { role: 'assistant', content: `❌ FAILED: Resuming action '${actionPayload?.tool}' failed.` }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="z-10 w-[1000px] h-[640px] max-w-[95%] max-h-[90%] glass-card flex flex-col overflow-hidden animate-fade-in">
            {/* Active HIL Modal pop-up overlay */}
            <ConfirmDialog
                action={pendingAction}
                onConfirm={() => handleConfirmAction(true)}
                onDecline={() => handleConfirmAction(false)}
            />

            {/* Header Container */}
            <header className="px-6 py-4 border-b border-white/5 flex justify-between items-center bg-slate-950/20">
                <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-indigo-600/30 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                        <MessageSquare className="w-5 h-5" />
                    </div>
                    <div>
                        <h3 className="font-semibold text-slate-100 text-sm flex items-center gap-1.5">
                            Zoho Project Workspace <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                        </h3>
                        <p className="text-[10px] text-slate-400">{userEmail}</p>
                    </div>
                </div>

                <button
                    onClick={onLogout}
                    className="py-1.5 px-3 rounded-lg hover:bg-rose-500/10 text-slate-400 hover:text-rose-400 text-xs font-medium transition-colors duration-200 flex items-center gap-1.5 cursor-pointer"
                >
                    <LogOut className="w-3.5 h-3.5" /> Disconnect
                </button>
            </header>

            {/* Message Feed Logging Container */}
            <main className="flex-1 p-6 overflow-y-auto space-y-6 bg-slate-900/10">
                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        className={`flex gap-4 animate-fade-in ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        {msg.role !== 'user' && (
                            <div className="w-8 h-8 rounded-lg bg-indigo-900/40 border border-indigo-500/10 flex items-center justify-center text-indigo-300 flex-shrink-0">
                                <Bot className="w-4.5 h-4.5" />
                            </div>
                        )}

                        <div className={`max-w-[75%] p-4 rounded-2xl text-sm leading-relaxed ${msg.role === 'user'
                            ? 'bg-indigo-600 text-white rounded-br-none shadow-md shadow-indigo-600/10'
                            : 'bg-slate-900/50 border border-white/5 rounded-bl-none text-slate-200'
                            }`}>
                            <ReactMarkdown className="markdown-body prose prose-invert max-w-none">
                                {msg.content}
                            </ReactMarkdown>
                        </div>

                        {msg.role === 'user' && (
                            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white flex-shrink-0 shadow-md">
                                <User className="w-4.5 h-4.5" />
                            </div>
                        )}
                    </div>
                ))}

                {/* Thinking / Bouncing dots load state */}
                {loading && (
                    <div className="flex gap-4 items-center animate-pulse">
                        <div className="w-8 h-8 rounded-lg bg-indigo-900/40 border border-indigo-500/10 flex items-center justify-center text-indigo-300 flex-shrink-0">
                            <Bot className="w-4.5 h-4.5" />
                        </div>
                        <div className="py-3 px-5 rounded-2xl bg-slate-900/50 border border-white/5 rounded-bl-none flex items-center gap-1.5">
                            <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '0ms' }}></span>
                            <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '150ms' }}></span>
                            <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '300ms' }}></span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </main>

            {/* Input Form Bar Container */}
            <form onSubmit={handleSend} className="p-4 border-t border-white/5 bg-slate-950/10 flex gap-3">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask me to show tasks, projects, check loads, or create/delete task..."
                    className="flex-1 px-4 py-3 glass-input text-sm"
                    disabled={loading || pendingAction !== null}
                />
                <button
                    type="submit"
                    disabled={loading || !input.trim() || pendingAction !== null}
                    className="px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:hover:bg-indigo-600 disabled:cursor-not-allowed text-white transition-all duration-200 flex items-center justify-center shadow-lg shadow-indigo-600/10 hover:shadow-indigo-500/20 cursor-pointer"
                >
                    <Send className="w-4 h-4" />
                </button>
            </form>
        </div>
    );
}

export default ChatWindow;
