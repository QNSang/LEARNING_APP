"use client"

import { useState, useEffect } from "react"
import { Sidebar } from "@/components/knowledge-map/sidebar"
import { DocumentCard, EmptyDocumentCard } from "@/components/knowledge-map/document-card"
import { StatsCard } from "@/components/knowledge-map/stats-card"
import { UploadModal } from "@/components/knowledge-map/upload-modal"
import { FileText, Network, PenLine, Upload } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useSidebar } from "@/components/sidebar-context"
import { cn } from "@/lib/utils"

const CACHE_KEY = "cached_documents"

interface Document {
  id: string
  title: string
  subject: string
  status: "ready" | "processing" | "error"
  created_at: string
}

function loadCache(): Document[] {
  if (typeof window === "undefined") return []
  try {
    const cached = localStorage.getItem(CACHE_KEY)
    return cached ? JSON.parse(cached) : []
  } catch {
    return []
  }
}

function saveCache(docs: Document[]) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(docs))
  } catch {
    // localStorage might be unavailable (e.g. private mode quota)
  }
}

export default function DashboardPage() {
  const { isCollapsed } = useSidebar()
  const [isUploadOpen, setIsUploadOpen] = useState(false)
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    setIsMounted(true)
    const cached = loadCache()
    if (cached.length > 0) {
      setDocuments(cached)
    }
    setIsLoading(!cached.length)
  }, [])

  // Spotlight effect tracker
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      document.documentElement.style.setProperty('--mouse-x', `${e.clientX}px`)
      document.documentElement.style.setProperty('--mouse-y', `${e.clientY}px`)
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  const fetchDocuments = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/documents")
      if (response.ok) {
        const data: Document[] = await response.json()
        setDocuments(data)
        saveCache(data)
      }
    } catch (error) {
      console.error("Fetch error:", error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchDocuments()

    const interval = setInterval(() => {
      const isProcessing = documents.some(doc => doc.status === "processing")
      if (isProcessing) {
        fetchDocuments()
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [documents.map(d => d.status).join(',')])

  const handleDelete = (deletedId: string) => {
    const updated = documents.filter(d => d.id !== deletedId)
    setDocuments(updated)
    saveCache(updated)
  }

  const totalConcepts = documents.length * 15 // Placeholder logic

  return (
    <div className="min-h-screen bg-[#0A0E1A] overflow-x-hidden spotlight">
      <Sidebar />

      <main className={cn(
        "transition-all duration-300 ease-in-out min-h-screen relative",
        isCollapsed ? "ml-[80px]" : "ml-[280px]"
      )}>
        {/* PRE-LOADING MESH GRADIENT */}
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-[#3B82F6]/5 blur-[120px] rounded-full -mr-32 -mt-32 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-[#8B5CF6]/5 blur-[100px] rounded-full -ml-32 -mb-32 pointer-events-none" />

        <div className="absolute inset-0 dot-grid opacity-[0.05] pointer-events-none" />

        <div className="relative p-10 max-w-7xl mx-auto">
          <div className="flex items-end justify-between mb-12">
            <div>
              <p className="text-[#3B82F6] text-xs font-bold uppercase tracking-[0.3em] mb-2">Learning OS</p>
              <h1 className="text-4xl font-bold text-[#F1F5F9] tracking-tight">Knowledge Space</h1>
            </div>
            <Button
              onClick={() => setIsUploadOpen(true)}
              className="bg-[#3B82F6] hover:bg-[#2563EB] text-white h-11 px-6 font-bold shadow-lg shadow-[#3B82F6]/20 transition-all active:scale-95"
            >
              <Upload className="w-4 h-4 mr-2" />
              Upload Document
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <StatsCard
              icon={FileText}
              value={documents.length.toString()}
              label="Documents"
              iconColor="#3B82F6"
            />
            <StatsCard
              icon={Network}
              value={totalConcepts.toString()}
              label="Concepts"
              iconColor="#8B5CF6"
            />
            <StatsCard
              icon={PenLine}
              value="0"
              label="Graded Essays"
              iconColor="#10B981"
            />
          </div>

          <div className="h-px bg-gradient-to-r from-transparent via-[#1F2D45] to-transparent mb-12" />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {documents.map((doc) => (
              <DocumentCard
                key={doc.id}
                id={doc.id}
                title={doc.title}
                subject={doc.subject}
                status={doc.status}
                onDelete={handleDelete}
              />
            ))}
            <EmptyDocumentCard onClick={() => setIsUploadOpen(true)} />
          </div>

          {/* Chỉ hiện spinner khi chưa có cache (lần đầu tiên vào app) */}
          {isLoading && documents.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 gap-4">
              <div className="w-10 h-10 border-2 border-[#3B82F6] border-t-transparent rounded-full animate-spin" />
              <p className="text-[#475569] font-bold text-xs uppercase tracking-widest">Đang truy cập kho tri thức...</p>
            </div>
          )}
        </div>
      </main>

      <UploadModal isOpen={isUploadOpen} onClose={() => {
        setIsUploadOpen(false)
        fetchDocuments()
      }} />
    </div>
  )
}