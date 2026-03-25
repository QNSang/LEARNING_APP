"use client"

import { Handle, Position } from "@xyflow/react"
import { cn } from "@/lib/utils"
import { Book, Lightbulb, ListChecks } from "lucide-react"

export function KnowledgeNode({ data }: { data: any }) {
    const { label, type, status, importance = "supporting" } = data

    const config = {
        concept: {
            icon: Book,
            accent: "#3B82F6", // Blue
            bg: "bg-[#1E3A5F]/20",
            border: "border-[#3B82F6]",
            text: "text-[#93C5FD]"
        },
        procedure: {
            icon: ListChecks,
            accent: "#F59E0B", // Yellow/Orange
            bg: "bg-[#422D06]/20",
            border: "border-[#F59E0B]",
            text: "text-[#FDE68A]"
        },
        fact: {
            icon: Lightbulb,
            accent: "#8B5CF6", // Purple
            bg: "bg-[#2D1B4B]/20",
            border: "border-[#8B5CF6]",
            text: "text-[#C4B5FD]"
        }
    }

    const nodeStyle = config[type as keyof typeof config] || config.concept
    const { icon: Icon } = nodeStyle

    const importanceStyles = {
        core: {
            container: "w-[220px] p-5 border-2 shadow-[0_0_20px_rgba(59,130,246,0.1)]",
            text: "text-lg"
        },
        supporting: {
            container: "w-[180px] p-4 border-2",
            text: "text-base"
        },
        detail: {
            container: "w-[150px] p-3 border border-dashed",
            text: "text-sm"
        }
    }

    const impStyle = importanceStyles[importance as keyof typeof importanceStyles] || importanceStyles.supporting

    return (
        <div className={cn(
            "rounded-2xl shadow-2xl transition-all duration-300 group backdrop-blur-md",
            impStyle.container,
            nodeStyle.bg,
            nodeStyle.border,
            status === "selected" ? "ring-4 ring-[#3B82F6]/50 scale-105 node-glow" : "hover:scale-102"
        )}>
            <Handle type="target" position={Position.Top} className="w-3 h-3 !bg-[#3B82F6] border-2 border-[#0A0E1A] !-top-1.5" />

            <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                    <div className={cn("p-1.5 rounded-lg bg-white/10", nodeStyle.text)}>
                        <Icon className="w-4 h-4" />
                    </div>
                    <span className={cn("text-[9px] font-bold uppercase tracking-[0.2em] opacity-50", nodeStyle.text)}>
                        {importance}
                    </span>
                </div>

                <div className="min-w-0">
                    <p className={cn("font-bold text-white leading-tight", impStyle.text)}>
                        {label}
                    </p>
                    <p className={cn("text-[10px] mt-1 font-medium uppercase tracking-wider opacity-60", nodeStyle.text)}>
                        {type}
                    </p>
                </div>
            </div>

            <Handle type="source" position={Position.Bottom} className="w-3 h-3 !bg-[#3B82F6] border-2 border-[#0A0E1A] !-bottom-1.5" />
        </div>
    )
}
