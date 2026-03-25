"use client"

import { useState, useEffect } from "react"
import { Sidebar } from "@/components/knowledge-map/sidebar"
import { StatsCard } from "@/components/knowledge-map/stats-card"
import {
    Trophy,
    Flame,
    Target,
    ChevronRight,
    Clock,
    Brain,
    AlertCircle
} from "lucide-react"
import { cn } from "@/lib/utils"

export default function ProgressPage() {
    // Spotlight effect tracker
    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            document.documentElement.style.setProperty('--mouse-x', `${e.clientX}px`)
            document.documentElement.style.setProperty('--mouse-y', `${e.clientY}px`)
        }
        window.addEventListener('mousemove', handleMouseMove)
        return () => window.removeEventListener('mousemove', handleMouseMove)
    }, [])

    return (
        <div className="min-h-screen bg-[#0A0E1A] overflow-x-hidden spotlight">
            <Sidebar />

            <main className="ml-[280px] min-h-screen relative p-10 max-w-7xl mx-auto">
                <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-[#8B5CF6]/5 blur-[120px] rounded-full -mr-32 -mt-32 pointer-events-none" />
                <div className="absolute inset-0 dot-grid opacity-[0.05] pointer-events-none" />

                <div className="relative z-10 space-y-12">
                    {/* Header */}
                    <header className="flex items-end justify-between">
                        <div>
                            <p className="text-[#3B82F6] text-xs font-bold uppercase tracking-[0.3em] mb-2">Personal Growth</p>
                            <h1 className="text-4xl font-bold text-[#F1F5F9] tracking-tight">Mastery Analytics</h1>
                        </div>
                        <div className="flex bg-[#111827] border border-[#1F2D45] rounded-xl p-1 shrink-0">
                            {["Global", "ML Fundamentals", "Algorithms"].map((tab, i) => (
                                <button
                                    key={tab}
                                    className={cn(
                                        "px-4 py-2 text-xs font-bold rounded-lg transition-all",
                                        i === 0 ? "bg-[#1F2D45] text-white shadow-sm" : "text-[#475569] hover:text-[#94A3B8]"
                                    )}
                                >
                                    {tab}
                                </button>
                            ))}
                        </div>
                    </header>

                    {/* Top Stats */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="bg-[#111827] border border-[#1F2D45] rounded-2xl p-8 relative overflow-hidden group">
                            <div className="relative z-10">
                                <p className="text-[10px] font-bold text-[#475569] uppercase tracking-[0.2em] mb-4">Readiness Score</p>
                                <div className="flex items-end gap-2">
                                    <span className="text-5xl font-bold text-white leading-none">84</span>
                                    <span className="text-lg text-[#10B981] font-bold mb-1">%</span>
                                </div>
                                <div className="mt-6 flex items-center justify-between">
                                    <div className="flex-1 h-2 bg-[#0A0E1A] rounded-full overflow-hidden mr-4">
                                        <div className="h-full bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] w-[84%] rounded-full shadow-[0_0_12px_rgba(59,130,246,0.5)]" />
                                    </div>
                                    <span className="text-[10px] font-bold text-[#94A3B8] uppercase">TOP 12%</span>
                                </div>
                            </div>
                            <Target className="absolute -right-4 -bottom-4 w-32 h-32 text-white/5 group-hover:text-white/10 transition-colors rotate-12" />
                        </div>

                        <div className="bg-[#111827] border border-[#1F2D45] rounded-2xl p-8 relative overflow-hidden group">
                            <div className="relative z-10">
                                <p className="text-[10px] font-bold text-[#475569] uppercase tracking-[0.2em] mb-4">Study Streak</p>
                                <div className="flex items-end gap-2">
                                    <span className="text-5xl font-bold text-white leading-none">12</span>
                                    <span className="text-lg text-[#F59E0B] font-bold mb-1">DAYS</span>
                                </div>
                                <p className="mt-4 text-xs text-[#94A3B8]">Higher than last week. Keep it up!</p>
                            </div>
                            <Flame className="absolute -right-4 -bottom-4 w-32 h-32 text-white/5 group-hover:text-white/10 transition-colors rotate-12" />
                        </div>

                        <div className="bg-[#111827] border border-[#1F2D45] rounded-2xl p-8 relative overflow-hidden group">
                            <div className="relative z-10">
                                <p className="text-[10px] font-bold text-[#475569] uppercase tracking-[0.2em] mb-4">Mastery Level</p>
                                <div className="flex items-center gap-3">
                                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#3B82F6] to-[#8B5CF6] flex items-center justify-center shadow-lg shadow-[#3B82F6]/20">
                                        <Trophy className="w-6 h-6 text-white" />
                                    </div>
                                    <div>
                                        <span className="text-2xl font-bold text-white block">Adept</span>
                                        <span className="text-[10px] font-bold text-[#3B82F6] uppercase tracking-widest">340 Points to Master</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Chart & History Area */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {/* Weekly Activity */}
                        <div className="lg:col-span-2 bg-[#111827] border border-[#1F2D45] rounded-2xl p-8">
                            <h3 className="text-sm font-bold text-white mb-8 flex items-center gap-2">
                                <Clock className="w-4 h-4 text-[#3B82F6]" />
                                Learning Activity
                            </h3>
                            <div className="h-64 flex items-end justify-between gap-4">
                                {[35, 65, 45, 90, 70, 40, 55].map((val, i) => (
                                    <div key={i} className="flex-1 flex flex-col items-center gap-4">
                                        <div
                                            className="w-full bg-[#1F2D45] hover:bg-[#3B82F6] transition-all rounded-t-lg relative group cursor-pointer"
                                            style={{ height: `${val}%` }}
                                        >
                                            <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-[#3B82F6] text-white text-[10px] font-bold px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                                                {val}m
                                            </div>
                                        </div>
                                        <span className="text-[10px] font-bold text-[#475569] uppercase tracking-widest">
                                            {["M", "T", "W", "T", "F", "S", "S"][i]}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Recent Insights */}
                        <div className="bg-[#111827] border border-[#1F2D45] rounded-2xl p-8 flex flex-col">
                            <h2 className="text-sm font-bold text-white mb-6 uppercase tracking-widest">Neural Insights</h2>
                            <div className="space-y-6 flex-1">
                                <div className="flex gap-4">
                                    <div className="shrink-0 w-8 h-8 rounded-lg bg-[#3B82F6]/10 flex items-center justify-center">
                                        <Brain className="w-4 h-4 text-[#3B82F6]" />
                                    </div>
                                    <div>
                                        <p className="text-xs text-[#F1F5F9] font-bold mb-1">Focus on Regularization</p>
                                        <p className="text-[10px] text-[#94A3B8] leading-relaxed">Your essay responses on L1/L2 penalties show gaps in understanding the bias-variance trade-off.</p>
                                    </div>
                                </div>
                                <div className="flex gap-4">
                                    <div className="shrink-0 w-8 h-8 rounded-lg bg-[#F59E0B]/10 flex items-center justify-center">
                                        <AlertCircle className="w-4 h-4 text-[#F59E0B]" />
                                    </div>
                                    <div>
                                        <p className="text-xs text-[#F1F5F9] font-bold mb-1">Consistency Check</p>
                                        <p className="text-[10px] text-[#94A3B8] leading-relaxed">You haven't reviewed "Backpropagation" in 3 days. We recommend a quick recap.</p>
                                    </div>
                                </div>
                            </div>
                            <Button className="mt-8 w-full bg-[#1C2333] hover:bg-[#1F2D45] text-white border border-[#1F2D45] transition-all group font-bold">
                                Personalized Plan
                                <ChevronRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                            </Button>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    )
}

function Button({ className, children, ...props }: any) {
    return (
        <button
            className={cn(
                "flex items-center justify-center rounded-xl px-4 py-2 transition-all active:scale-95 text-sm",
                className
            )}
            {...props}
        >
            {children}
        </button>
    )
}
