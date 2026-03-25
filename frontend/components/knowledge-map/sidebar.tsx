"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  Network,
  TrendingUp,
  Settings,
  Upload,
  ChevronRight,
  Trash2,
  PanelLeftClose,
  PanelLeftOpen
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { useSidebar } from "@/components/sidebar-context"

const navItems = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
]

type Status = "ready" | "processing" | "error"

interface Document {
  id: string
  title: string
  subject: string
  status: Status
}

function StatusBadge({ status }: { status: Status }) {
  const styles: Record<Status, string> = {
    ready: "bg-[#10B981]/20 text-[#10B981]",
    processing: "bg-[#F59E0B]/20 text-[#F59E0B]",
    error: "bg-[#EF4444]/20 text-[#EF4444]",
  }

  return (
    <span className={cn(
      "px-2 py-0.5 rounded-full text-[10px] font-medium capitalize flex items-center gap-1",
      styles[status]
    )}>
      {status === "processing" && (
        <span className="w-2 h-2 border border-current border-t-transparent rounded-full animate-spin" />
      )}
      {status}
    </span>
  )
}

export function Sidebar() {
  const { isCollapsed, toggleSidebar } = useSidebar()
  const pathname = usePathname()
  const router = useRouter()
  const [recentDocuments, setRecentDocuments] = useState<Document[]>([])

  const fetchRecent = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/documents")
      if (response.ok) {
        const data = await response.json()
        setRecentDocuments(data)
      }
    } catch (error) {
      // Backend maybe slow to start due to ML models loading, don't throw console.error 
      // which triggers Next.js dev overlay. Just log silently.
      console.log("Waiting for backend to be ready...")
    }
  }

  useEffect(() => {
    fetchRecent()
  }, [])

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    if (!confirm("Are you sure you want to delete this document?")) return

    try {
      const res = await fetch(`http://localhost:8000/api/documents/${id}`, {
        method: "DELETE"
      })
      if (res.ok) {
        setRecentDocuments(prev => prev.filter(d => d.id !== id))
        if (pathname.includes(`/graph/${id}`)) {
          router.push("/")
        }
      }
    } catch (error) {
      console.error("Delete failed:", error)
    }
  }

  return (
    <aside className={cn(
      "h-screen bg-[#0A0E1A] border-r border-[#1F2D45] flex flex-col fixed left-0 top-0 z-50 transition-all duration-300 ease-in-out",
      isCollapsed ? "w-[80px]" : "w-[280px]"
    )}>
      {/* Logo */}
      <div className={cn(
        "p-6 flex items-center justify-between border-b border-[#1F2D45]/30",
        isCollapsed ? "justify-center" : ""
      )}>
        <Link href="/" className="flex items-center gap-3 overflow-hidden">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#3B82F6] to-[#8B5CF6] flex items-center justify-center shadow-lg shadow-[#3B82F6]/20 shrink-0">
            <Network className="w-6 h-6 text-white" />
          </div>
          {!isCollapsed && (
            <div className="animate-in fade-in slide-in-from-left-4 duration-500">
              <h1 className="text-[#F1F5F9] font-bold text-xl tracking-tight leading-none">Knowledge</h1>
              <p className="text-[#3B82F6] text-[10px] font-bold uppercase tracking-[0.2em] mt-1">Learning OS</p>
            </div>
          )}
        </Link>
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={toggleSidebar}
          className="text-[#475569] hover:bg-[#111827] hover:text-[#F1F5F9] shrink-0"
        >
          {isCollapsed ? <PanelLeftOpen className="w-5 h-5" /> : <PanelLeftClose className="w-5 h-5" />}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="px-4 py-2 space-y-1 shrink-0">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all duration-200",
                  isActive
                    ? "bg-[#111827] text-white shadow-sm ring-1 ring-[#1F2D45] border-l-4 border-[#3B82F6]"
                    : "text-[#475569] hover:text-[#F1F5F9] hover:bg-[#111827]/50",
                  isCollapsed ? "px-0 justify-center h-12" : "px-4 py-3"
                )}
              >
                <item.icon className={cn("w-4 h-4 shrink-0", isActive ? "text-[#3B82F6]" : "opacity-70")} />
                {!isCollapsed && <span className="animate-in fade-in slide-in-from-left-2 duration-300">{item.label}</span>}
              </Link>
          )
        })}
      </nav>

      {/* Recent Documents */}
      <div className="flex-1 min-h-0 flex flex-col py-8 mt-4 border-t border-[#1F2D45]/50">
        <h3 className={cn(
          "text-[10px] uppercase font-bold tracking-[0.2em] text-[#475569] mb-4 transition-all",
          isCollapsed ? "text-center opacity-0 h-0 overflow-hidden" : "px-8 mb-4"
        )}>
          RECENT MAPS
        </h3>
        <div className="flex-1 overflow-y-auto px-4 space-y-1 custom-scrollbar">
          {recentDocuments.map((doc) => (
            <div key={doc.id} className="relative group px-2">
              <button
                onClick={() => doc.status === "ready" && router.push(`/graph/${doc.id}`)}
                className={cn(
                  "w-full flex items-center justify-between py-2.5 rounded-lg hover:bg-[#111827] transition-all text-left group/btn",
                  doc.status !== "ready" && "cursor-default opacity-50",
                  isCollapsed ? "px-0 justify-center h-12" : "px-3"
                )}
              >
                <div className={cn("flex-1 min-w-0 pr-2", isCollapsed ? "hidden" : "block")}>
                  <p className="text-sm text-[#94A3B8] font-bold truncate group-hover/btn:text-white transition-colors">{doc.title}</p>
                </div>
                <div className="shrink-0">
                  {isCollapsed ? (
                    <div className={cn("w-2 h-2 rounded-full", doc.status === "ready" ? "bg-[#10B981]" : doc.status === "processing" ? "bg-[#F59E0B] animate-pulse" : "bg-[#EF4444]")} />
                  ) : (
                    <StatusBadge status={doc.status} />
                  )}
                </div>
              </button>
              <button
                onClick={(e) => handleDelete(e, doc.id)}
                className="absolute right-4 top-1/2 -translate-y-1/2 p-1.5 text-[#475569] hover:text-[#EF4444] opacity-0 group-hover:opacity-100 transition-all rounded-md hover:bg-[#EF4444]/10"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
          {recentDocuments.length === 0 && (
            <p className="text-xs text-[#475569] px-4 italic">No documents yet</p>
          )}
        </div>
      </div>

      {/* User Section */}
      <div className={cn(
        "p-6 border-t border-[#1F2D45] bg-[#111827]/20 transition-all",
        isCollapsed ? "px-0 flex flex-col items-center" : "p-6"
      )}>
        <div className={cn("flex items-center gap-3", isCollapsed ? "" : "px-2")}>
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#1E3A5F] to-[#1C2333] flex items-center justify-center text-white text-xs font-bold border border-[#1F2D45] shrink-0">
            QS
          </div>
          {!isCollapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm text-[#F1F5F9] font-bold truncate">Quang Sang</p>
              <p className="text-[10px] text-[#3B82F6] font-bold uppercase tracking-wider">Pro Neuralist</p>
            </div>
          )}
        </div>
      </div>
    </aside>
  )
}
