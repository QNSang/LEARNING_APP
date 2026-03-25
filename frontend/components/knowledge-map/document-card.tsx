"use client"

import { ArrowRight, Plus, Trash2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { cn } from "@/lib/utils"

interface DocumentCardProps {
  id: string
  title: string
  subject: string
  status: "ready" | "processing" | "error"
  nodes?: number
  edges?: number
  onDelete?: (id: string) => void
}

export function DocumentCard({
  id,
  title,
  subject,
  status,
  nodes = 0,
  edges = 0,
  onDelete,
}: DocumentCardProps) {
  const router = useRouter()
  const isReady = status === "ready"
  const progressValue = 35 // Placeholder for demo

  const handleDelete = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (!confirm("Bạn có chắc chắn muốn xóa tài liệu này không?")) return

    try {
      const res = await fetch(`http://localhost:8000/api/documents/${id}`, {
        method: "DELETE"
      })
      if (res.ok) {
        onDelete?.(id)
      }
    } catch (error) {
      console.error("Delete failed:", error)
    }
  }

  return (
    <div
      onClick={() => isReady && router.push(`/graph/${id}`)}
      className={cn(
        "relative bg-[#111827] border border-[#1F2D45] rounded-xl p-6 transition-all duration-200 group spotlight",
        isReady ? "hover:border-[#2D4A7A] hover:bg-[#111827]/80 cursor-pointer" : "opacity-75 cursor-default"
      )}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 min-w-0 pr-6">
          <h3 className="text-[#F1F5F9] font-bold text-lg truncate mb-1" title={title}>{title}</h3>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#3B82F6]/10 text-[#3B82F6] uppercase tracking-wider">
            {subject}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className={cn(
            "px-2 py-0.5 rounded-full text-[10px] font-bold capitalize flex items-center gap-1.5",
            status === "ready" && "bg-[#10B981]/10 text-[#10B981]",
            status === "processing" && "bg-[#F59E0B]/10 text-[#F59E0B]",
            status === "error" && "bg-[#EF4444]/10 text-[#EF4444]"
          )}>
            {status === "processing" && (
              <span className="w-2.5 h-2.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
            )}
            {status === "ready" ? "Hoàn tất" : status === "processing" ? "Đang xử lý" : "Lỗi"}
          </span>
          <button
            onClick={handleDelete}
            className="p-2 text-[#475569] hover:text-[#EF4444] rounded-lg hover:bg-[#EF4444]/10 transition-colors z-10"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="mb-6">
        <div className="flex items-center justify-between text-xs mb-2">
          <span className="text-[#94A3B8] font-medium">Tiến độ Học tập</span>
          <span className="text-[#3B82F6] font-bold">{progressValue}%</span>
        </div>
        <div className="h-1.5 w-full bg-[#1C2333] rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6] rounded-full transition-all duration-1000"
            style={{ width: `${progressValue}%` }}
          />
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex gap-4">
          <div className="text-center">
            <p className="text-[10px] text-[#475569] font-bold uppercase tracking-widest">Khái niệm</p>
            <p className="text-sm text-[#F1F5F9] font-mono font-bold">{nodes}</p>
          </div>
          <div className="text-center">
            <p className="text-[10px] text-[#475569] font-bold uppercase tracking-widest">Liên kết</p>
            <p className="text-sm text-[#F1F5F9] font-mono font-bold">{edges}</p>
          </div>
        </div>

        <div className={cn(
          "flex items-center text-sm font-bold transition-all",
          isReady ? "text-[#3B82F6] group-hover:text-white" : "text-[#475569]"
        )}>
          {isReady ? (
            <>
              Khám phá Map
              <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
            </>
          ) : (
            "Đang phân tích..."
          )}
        </div>
      </div>
    </div>
  )
}

export function EmptyDocumentCard({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex flex-col items-center justify-center bg-transparent border-2 border-dashed border-[#1F2D45] rounded-xl p-8 hover:border-[#3B82F6] hover:bg-[#3B82F6]/5 transition-all duration-200 min-h-[220px] group"
    >
      <div className="w-14 h-14 rounded-full bg-[#1C2333] flex items-center justify-center mb-4 group-hover:bg-[#3B82F6]/20 transition-colors">
        <Plus className="w-6 h-6 text-[#475569] group-hover:text-[#3B82F6]" />
      </div>
      <p className="text-[#94A3B8] text-sm font-bold group-hover:text-[#F1F5F9]">Tải lên Tài liệu</p>
      <p className="text-[#475569] text-xs mt-1">Bắt đầu hành trình học tập</p>
    </button>
  )
}
