import React, { useState } from "react";
import { Bot, Send, User, Sparkles, ShieldCheck, Wrench, FileText, ChevronRight } from "lucide-react";
import { Card, Badge, Button } from "../components/ui";
import { api } from "../services/api";
import { ChatMessage } from "../types";

const INITIAL_MESSAGES: ChatMessage[] = [
  {
    role: "assistant",
    content: "Hello Yash! I am your Agentic Personal Finance Advisor. I analyze your approved ledger, budget utilizations, and 30-day cash forecasts to provide grounded financial guidance. How can I help you today?",
    tool_calls: [],
    cited_insights: []
  }
];

const SUGGESTIONS = [
  "Why is my Food & Dining budget in warning status?",
  "What is my projected cash runway if my salary is delayed?",
  "Did the system detect any unusual transactions or anomalies?",
  "How much could I save annually by canceling recurring subscriptions?"
];

export default function AdvisorPage() {
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async (textToSend?: string) => {
    const query = textToSend || input;
    if (!query.trim() || loading) return;

    const userMsg: ChatMessage = { role: "user", content: query };
    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setInput("");
    setLoading(true);

    try {
      const res = await api.sendAdvisorChat(query, messages);
      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: res.answer,
        tool_calls: res.tool_calls,
        cited_insights: res.cited_insights,
        cited_transactions: res.cited_transactions
      };
      setMessages([...newHistory, assistantMsg]);
    } catch (err: any) {
      setMessages([
        ...newHistory,
        {
          role: "assistant",
          content: `Apologies, I encountered an error: ${err.message || "Could not retrieve financial context."}`
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full max-w-5xl mx-auto p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-line">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-accent flex items-center justify-center text-white shadow-sm">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-ink tracking-tight flex items-center gap-2">
              Conversational Financial Advisor
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-accent/15 text-accent">
                Agentic LLM
              </span>
            </h1>
            <p className="text-xs text-muted">
              Tool-augmented financial reasoning grounded strictly in your verified transactions and metrics
            </p>
          </div>
        </div>

        {/* Guardrail Pill */}
        <Badge variant="pass" className="text-[11px] hidden sm:inline-flex gap-1.5">
          <ShieldCheck className="h-3.5 w-3.5" />
          Read-Only Guardrails Enforced
        </Badge>
      </div>

      {/* Chat Messages Scroll Window */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex items-start gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}
          >
            <div
              className={`h-8 w-8 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 ${m.role === "user" ? "bg-accent text-white" : "bg-sunken text-accent border border-line"
                }`}
            >
              {m.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
            </div>

            <div className={`space-y-2 max-w-2xl ${m.role === "user" ? "items-end" : ""}`}>
              {/* Tool Execution Pill */}
              {m.tool_calls && m.tool_calls.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {m.tool_calls.map((t, ti) => (
                    <span
                      key={ti}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-sunken text-[10px] font-mono text-muted border border-line"
                    >
                      <Wrench className="h-3 w-3 text-accent" />
                      Executed: {t.tool_name}()
                    </span>
                  ))}
                </div>
              )}

              {/* Message Bubble */}
              <div
                className={`p-4 rounded-2xl text-xs leading-relaxed ${m.role === "user"
                    ? "bg-accent text-white rounded-tr-none shadow-sm"
                    : "bg-surface border border-line text-ink rounded-tl-none shadow-sm"
                  }`}
              >
                <p className="whitespace-pre-line">{m.content}</p>

                {/* Evidence Citations */}
                {m.cited_insights && m.cited_insights.length > 0 && (
                  <div className="mt-3 pt-2 border-t border-line/40 flex items-center gap-1.5 flex-wrap">
                    <span className="text-[10px] text-muted font-medium">Cited Evidence:</span>
                    {m.cited_insights.map((cit, ci) => (
                      <span key={ci} className="text-[10px] font-mono font-semibold text-accent px-1.5 py-0.5 rounded bg-accent/10">
                        {cit.toUpperCase()}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-sunken flex items-center justify-center text-accent">
              <Bot className="h-4 w-4" />
            </div>
            <div className="p-3 rounded-2xl bg-surface border border-line text-xs text-muted flex items-center gap-2">
              <Sparkles className="h-3.5 w-3.5 animate-spin text-accent" />
              <span>Analyzing ledger facts and executing tools...</span>
            </div>
          </div>
        )}
      </div>

      {/* Suggested Follow-Ups */}
      <div className="flex items-center gap-2 overflow-x-auto py-1">
        <span className="text-[10px] font-semibold text-muted uppercase shrink-0">Suggestions:</span>
        {SUGGESTIONS.map((s, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(s)}
            className="text-[11px] whitespace-nowrap px-3 py-1.5 rounded-full border border-line bg-surface text-muted hover:text-ink hover:border-accent transition-colors"
          >
            {s}
          </button>
        ))}
      </div>

      {/* Input Box */}
      <div className="relative pt-2">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            placeholder="Ask about your budget, cash forecast, or unusual transactions..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            className="flex-1 px-4 py-3 text-xs rounded-xl border border-line bg-surface text-ink placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent"
          />
          <Button type="submit" variant="primary" disabled={!input.trim() || loading} className="px-5 py-3">
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}
