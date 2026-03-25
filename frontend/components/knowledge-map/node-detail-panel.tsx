"use client"

import { useState, useEffect } from "react"
import { X, Sparkles, RefreshCw, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface NodeDetailPanelProps {
  node: {
    id: string
    label: string
    type: "concept" | "procedure" | "fact"
    importance: "core" | "supporting" | "detail"
    week: number
  } | null
  onClose: () => void
}

interface GradingResult {
  total: number
  scores: {
    label: string
    score: number
    max: number
    color: string
  }[]
  feedback: string
  missingConcepts: string[]
}

const typeLabels: Record<string, string> = {
  concept: "Khái niệm",
  procedure: "Quy trình",
  fact: "Sự kiện",
}

const importanceLabels: Record<string, string> = {
  core: "Cốt lõi",
  supporting: "Bổ trợ",
  detail: "Chi tiết",
}

const nodeInfo = {
  "gradient-descent": {
    requires: ["Calculus", "Linear Algebra", "Loss Function"],
    unlocks: ["Backpropagation", "Optimizers", "Training Loop"],
    intuition: "Imagine you're blindfolded on a hilly terrain trying to find the lowest valley. Each step you take in the steepest downward direction is one iteration of gradient descent. The gradient tells you which way is 'down', and the learning rate determines how big of a step you take.",
    applications: ["Training neural networks", "Recommendation systems", "Image recognition"],
    learningPath: "Master Calculus → then Gradient Descent → then unlock Backpropagation"
  }
}

export function NodeDetailPanel({ node, onClose }: NodeDetailPanelProps) {
  const [isLoading, setIsLoading] = useState(true)
  const [essay, setEssay] = useState("")
  const [gradingResult, setGradingResult] = useState<GradingResult | null>(null)
  const [isGrading, setIsGrading] = useState(false)

  useEffect(() => {
    if (node) {
      setIsLoading(true)
      setEssay("")
      setGradingResult(null)
      const timer = setTimeout(() => setIsLoading(false), 1200)
      return () => clearTimeout(timer)
    }
  }, [node?.id])

  const handleSubmitEssay = () => {
    setIsGrading(true)
    setTimeout(() => {
      setGradingResult({
        total: 8.5,
        scores: [
          { label: "Accuracy", score: 4, max: 4, color: "#10B981" },
          { label: "Completeness", score: 2, max: 3, color: "#3B82F6" },
          { label: "Own Words", score: 1, max: 2, color: "#F59E0B" },
          { label: "Example Quality", score: 1, max: 1, color: "#10B981" },
        ],
        feedback: "Great explanation of the core concept! You clearly understand how gradient descent iteratively minimizes the loss function. To improve, try explaining the role of the learning rate in more detail.",
        missingConcepts: ["Learning Rate", "Convergence"]
      })
      setIsGrading(false)
    }, 2000)
  }

  const info = nodeInfo["gradient-descent"]

  if (!node) return null

  return (
    <div className="fixed inset-y-0 right-0 w-[420px] bg-[#111827] border-l border-[#1F2D45] shadow-[-8px_0px_32px_rgba(0,0,0,0.4)] z-50 flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-[#1F2D45]">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-[#F1F5F9] mb-2">{node.label}</h2>
            <div className="flex items-center gap-2">
              <span className={cn(
                "px-2.5 py-1 rounded-full text-[11px] font-medium capitalize",
                node.type === "concept" && "bg-[#3B82F6]/20 text-[#93C5FD]",
                node.type === "procedure" && "bg-[#8B5CF6]/20 text-[#C4B5FD]",
                node.type === "fact" && "bg-[#10B981]/20 text-[#6EE7B7]"
              )}>
                {typeLabels[node.type] || node.type}
              </span>
              <span className="px-2.5 py-1 rounded-full text-[11px] font-medium bg-[#1C2333] text-[#94A3B8]">
                Tuần {node.week}
              </span>
              <span className={cn(
                "px-2.5 py-1 rounded-full text-[11px] font-medium capitalize flex items-center gap-1.5",
                node.importance === "core" && "bg-[#10B981]/20 text-[#6EE7B7]",
                node.importance === "supporting" && "bg-[#3B82F6]/20 text-[#93C5FD]",
                node.importance === "detail" && "bg-[#475569]/20 text-[#94A3B8]"
              )}>
                <span className={cn(
                  "w-1.5 h-1.5 rounded-full",
                  node.importance === "core" && "bg-[#10B981]",
                  node.importance === "supporting" && "bg-[#3B82F6]",
                  node.importance === "detail" && "bg-[#475569]"
                )} />
                {importanceLabels[node.importance] || node.importance}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-[#1C2333] text-[#94A3B8] hover:text-[#F1F5F9] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>
      
      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Graph Position */}
        <div className="p-6 border-b border-[#1F2D45]">
          <h3 className="text-[10px] uppercase tracking-wider text-[#475569] font-semibold mb-4">
            Vị trí trong Bản đồ Kiến thức
          </h3>
          <div className="space-y-3">
            <div>
              <p className="text-xs text-[#94A3B8] mb-2">Kiến thức cơ bản cần có:</p>
              <div className="flex flex-wrap gap-1.5">
                {info.requires.map((item) => (
                  <button
                    key={item}
                    className="px-2.5 py-1 rounded-full text-xs bg-[#F59E0B]/10 text-[#FCD34D] border border-[#F59E0B]/30 hover:bg-[#F59E0B]/20 transition-colors"
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <p className="text-xs text-[#94A3B8] mb-2">Mở ra kiến thức về:</p>
              <div className="flex flex-wrap gap-1.5">
                {info.unlocks.map((item) => (
                  <button
                    key={item}
                    className="px-2.5 py-1 rounded-full text-xs bg-[#10B981]/10 text-[#6EE7B7] border border-[#10B981]/30 hover:bg-[#10B981]/20 transition-colors"
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
        
        {/* AI Explanation */}
        <div className="p-6 border-b border-[#1F2D45]">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-4 h-4 text-[#8B5CF6]" />
            <h3 className="text-sm font-semibold text-[#F1F5F9]">Giải thích bởi AI</h3>
          </div>
          
          {isLoading ? (
            <div className="space-y-3">
              <div className="h-4 shimmer rounded" />
              <div className="h-4 shimmer rounded w-5/6" />
              <div className="h-4 shimmer rounded w-4/6" />
            </div>
          ) : (
            <>
              <div className="mb-4">
                <h4 className="text-xs text-[#475569] uppercase tracking-wider mb-2">Cách hiểu trực quan</h4>
                <p className="text-sm text-[#94A3B8] leading-relaxed">{info.intuition}</p>
              </div>
              
              <div className="mb-4">
                <h4 className="text-xs text-[#475569] uppercase tracking-wider mb-2">Ứng dụng thực tế</h4>
                <div className="space-y-2">
                  {info.applications.map((app) => (
                    <div
                      key={app}
                      className="flex items-center gap-2 p-2 bg-[#0A0E1A] rounded-lg"
                    >
                      <ChevronRight className="w-3 h-3 text-[#3B82F6]" />
                      <span className="text-sm text-[#F1F5F9]">{app}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="p-3 bg-[#0A0E1A] border border-[#2D4A7A] rounded-lg">
                <h4 className="text-xs text-[#475569] uppercase tracking-wider mb-1">Lộ trình học tập của bạn</h4>
                <p className="text-sm text-[#93C5FD]">{info.learningPath}</p>
              </div>
              
              <button className="flex items-center gap-1.5 text-xs text-[#94A3B8] hover:text-[#F1F5F9] mt-3 ml-auto transition-colors">
                <RefreshCw className="w-3 h-3" />
                Tạo lại
              </button>
            </>
          )}
        </div>
        
        {/* Essay Section */}
        <div className="p-6">
          <h3 className="text-sm font-semibold text-[#F1F5F9] mb-4">Kiểm tra mức độ thấu hiểu</h3>
          
          {!gradingResult ? (
            <>
              <textarea
                value={essay}
                onChange={(e) => setEssay(e.target.value)}
                placeholder={`Giải thích ${node.label} theo cách hiểu của bạn. Bao gồm: nó làm gì, tại sao nó hoạt động và một ứng dụng thực tế...`}
                className="w-full p-4 bg-[#0A0E1A] border border-[#1F2D45] rounded-lg text-sm text-[#F1F5F9] placeholder-[#475569] resize-none focus:border-[#3B82F6] focus:outline-none transition-colors min-h-[140px]"
              />
              <div className="flex items-center justify-between mt-2">
                <span className={cn(
                  "text-xs",
                  essay.length >= 100 ? "text-[#10B981]" : "text-[#475569]"
                )}>
                  {essay.length} / tối thiểu 100 ký tự
                </span>
              </div>
              <Button
                onClick={handleSubmitEssay}
                disabled={essay.length < 100 || isGrading}
                className={cn(
                  "w-full mt-4 h-11 font-semibold",
                  essay.length >= 100
                    ? "bg-[#3B82F6] hover:bg-[#2563EB] text-white"
                    : "bg-[#1C2333] text-[#475569] cursor-not-allowed"
                )}
              >
                {isGrading ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Đang chấm điểm...
                  </span>
                ) : (
                  "Nộp bài chấm điểm"
                )}
              </Button>
            </>
          ) : (
            <div>
              {/* Score */}
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm text-[#94A3B8]">Điểm của bạn</h4>
                <span className="text-3xl font-bold text-[#3B82F6]">
                  {gradingResult.total} <span className="text-lg text-[#475569]">/ 10</span>
                </span>
              </div>
              
              {/* Score Breakdown */}
              <div className="space-y-3 mb-4">
                {gradingResult.scores.map((score) => (
                  <div key={score.label}>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-[#94A3B8]">{score.label}</span>
                      <span className="text-[#F1F5F9]">{score.score}/{score.max}</span>
                    </div>
                    <div className="h-2 bg-[#1C2333] rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${(score.score / score.max) * 100}%`,
                          backgroundColor: score.color
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Feedback */}
              <div className="p-3 bg-[#0A0E1A] rounded-lg mb-4">
                <h4 className="text-xs text-[#475569] uppercase tracking-wider mb-2">Nhận xét</h4>
                <p className="text-sm text-[#94A3B8]">{gradingResult.feedback}</p>
              </div>
              
              {/* Missing Concepts */}
              {gradingResult.missingConcepts.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-xs text-[#EF4444] uppercase tracking-wider mb-2">Missing Concepts</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {gradingResult.missingConcepts.map((concept) => (
                      <span
                        key={concept}
                        className="px-2.5 py-1 rounded-full text-xs bg-[#EF4444]/10 text-[#FCA5A5] border border-[#EF4444]/30"
                      >
                        {concept}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              <Button
                onClick={() => {
                  setGradingResult(null)
                  setEssay("")
                }}
                variant="outline"
                className="w-full h-10 border-[#2D4A7A] text-[#94A3B8] hover:bg-[#1C2333] hover:text-[#F1F5F9]"
              >
                Thử lại
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
