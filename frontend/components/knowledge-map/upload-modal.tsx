"use client"

import { useState, useCallback } from "react"
import { X, Upload, Check, Loader2, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface UploadModalProps {
  isOpen: boolean
  onClose: () => void
}

type UploadState = "select" | "processing" | "complete"
type ProcessingStep = "parsing" | "summarizing" | "extracting" | "done"

const steps: { id: ProcessingStep; label: string }[] = [
  { id: "parsing", label: "Parsing" },
  { id: "summarizing", label: "Summarizing" },
  { id: "extracting", label: "Extracting Graph" },
  { id: "done", label: "Done" },
]

export function UploadModal({ isOpen, onClose }: UploadModalProps) {
  const [state, setState] = useState<UploadState>("select")
  const [currentStep, setCurrentStep] = useState<ProcessingStep>("parsing")
  const [files, setFiles] = useState<File[]>([])
  const [subject, setSubject] = useState("")
  const [isDragging, setIsDragging] = useState(false)

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const newFiles = Array.from(e.dataTransfer.files)
    if (newFiles.length > 0) {
      setFiles(prev => [...prev, ...newFiles])
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files ? Array.from(e.target.files) : []
    if (selectedFiles.length > 0) {
      setFiles(prev => [...prev, ...selectedFiles])
    }
  }

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (files.length === 0 || !subject) return

    setState("processing")
    setCurrentStep("parsing")

    const formData = new FormData()
    files.forEach(f => formData.append("files", f))
    formData.append("subject", subject)

    try {
      const response = await fetch("http://localhost:8000/api/upload", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        throw new Error("Upload failed")
      }

      const data = await response.json()
      // The backend processes in background, so we just show "complete" 
      // when the upload itself is successful and processing has started.
      setState("complete")

      setTimeout(() => {
        onClose()
        // Reset state
        setState("select")
        setCurrentStep("parsing")
        setFiles([])
        setSubject("")
      }, 2000)

    } catch (error) {
      console.error("Upload error:", error)
      alert("Failed to upload document. Please check if the backend is running.")
      setState("select")
    }
  }

  const getStepStatus = (stepId: ProcessingStep): "completed" | "active" | "pending" => {
    const stepOrder: ProcessingStep[] = ["parsing", "summarizing", "extracting", "done"]
    const currentIndex = stepOrder.indexOf(currentStep)
    const stepIndex = stepOrder.indexOf(stepId)

    if (stepIndex < currentIndex) return "completed"
    if (stepIndex === currentIndex) return "active"
    return "pending"
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-[#0A0E1A]/80 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-[560px] bg-[#111827] border border-[#1F2D45] rounded-2xl shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[#1F2D45]">
          <h2 className="text-lg font-semibold text-[#F1F5F9]">Upload Document</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-[#1C2333] text-[#94A3B8] hover:text-[#F1F5F9] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {state === "select" && (
            <>
              {/* Drop Zone */}
              <div
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                className={cn(
                  "border-2 border-dashed rounded-xl h-[200px] flex flex-col items-center justify-center transition-all",
                  isDragging
                    ? "border-[#3B82F6] bg-[#3B82F6]/10"
                    : files.length > 0
                      ? "border-[#10B981] bg-[#10B981]/10"
                      : "border-[#2D4A7A] hover:border-[#3B82F6] hover:bg-[#1C2333]"
                )}
              >
                {files.length > 0 ? (
                  <div className="w-full px-6 py-4 max-h-[160px] overflow-y-auto space-y-2 custom-scrollbar">
                    {files.map((f, i) => (
                      <div key={i} className="flex items-center justify-between p-2 bg-[#0A0E1A] border border-[#1F2D45] rounded-lg group/item">
                        <div className="flex items-center gap-3 min-w-0">
                          <FileText className="w-4 h-4 text-[#3B82F6] shrink-0" />
                          <span className="text-xs text-[#F1F5F9] truncate font-medium">{f.name}</span>
                          <span className="text-[10px] text-[#475569] shrink-0">{(f.size / 1024 / 1024).toFixed(1)}MB</span>
                        </div>
                        <button
                          onClick={(e) => { e.stopPropagation(); removeFile(i) }}
                          className="p-1 hover:bg-[#EF4444]/10 text-[#475569] hover:text-[#EF4444] rounded transition-colors"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                    <label className="block text-center mt-2">
                      <input
                        type="file"
                        multiple
                        accept=".pdf,.pptx,.docx"
                        onChange={handleFileSelect}
                        className="hidden"
                      />
                      <span className="text-[10px] text-[#3B82F6] hover:underline cursor-pointer font-bold uppercase tracking-wider">
                        + Add more files
                      </span>
                    </label>
                  </div>
                ) : (
                  <>
                    <Upload className="w-8 h-8 text-[#94A3B8] mb-3" />
                    <p className="text-[#F1F5F9] font-medium mb-1">Drop files here</p>
                    <p className="text-[#94A3B8] text-sm mb-3">PDF, PPTX, DOCX up to 50MB</p>
                    <label>
                      <input
                        type="file"
                        multiple
                        accept=".pdf,.pptx,.docx"
                        onChange={handleFileSelect}
                        className="hidden"
                      />
                      <span className="px-4 py-2 bg-transparent border border-[#2D4A7A] text-[#94A3B8] hover:text-[#F1F5F9] hover:border-[#3B82F6] rounded-lg text-sm font-medium cursor-pointer transition-colors">
                        Browse files
                      </span>
                    </label>
                  </>
                )}
              </div>

              {/* Form Fields */}
              <div className="space-y-4 mt-6">
                <div>
                  <label className="block text-sm text-[#94A3B8] mb-2">Subject / Course name</label>
                  <input
                    type="text"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && files.length > 0 && subject) {
                        e.preventDefault()
                        handleUpload()
                      }
                    }}
                    placeholder="e.g. Machine Learning, Data Structures"
                    className="w-full px-4 py-3 bg-[#0A0E1A] border border-[#1F2D45] rounded-lg text-[#F1F5F9] placeholder-[#475569] focus:border-[#3B82F6] focus:outline-none transition-colors"
                  />
                </div>
              </div>

              {/* Submit Button */}
              <Button
                onClick={handleUpload}
                disabled={files.length === 0 || !subject}
                className={cn(
                  "w-full mt-6 h-12 text-base font-semibold rounded-lg transition-all",
                  files.length > 0 && subject
                    ? "bg-[#3B82F6] hover:bg-[#2563EB] text-white"
                    : "bg-[#1C2333] text-[#475569] cursor-not-allowed"
                )}
              >
                Upload {files.length} {files.length === 1 ? 'Document' : 'Documents'}
              </Button>
            </>
          )}

          {state === "processing" && (
            <div className="py-4">
              <div className="space-y-4">
                {steps.map((step, index) => {
                  const status = getStepStatus(step.id)
                  return (
                    <div key={step.id} className="flex items-center gap-4">
                      <div className={cn(
                        "w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all",
                        status === "completed" && "bg-[#10B981] text-white",
                        status === "active" && "bg-[#3B82F6] text-white",
                        status === "pending" && "bg-[#1C2333] text-[#475569]"
                      )}>
                        {status === "completed" ? (
                          <Check className="w-4 h-4" />
                        ) : status === "active" ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          index + 1
                        )}
                      </div>
                      <div className="flex-1">
                        <p className={cn(
                          "font-medium",
                          status === "pending" ? "text-[#475569]" : "text-[#F1F5F9]"
                        )}>
                          {step.label}
                        </p>
                        {status === "active" && (
                          <div className="mt-2">
                            <div className="h-1 bg-[#1C2333] rounded-full overflow-hidden">
                              <div className="h-full bg-[#3B82F6] rounded-full animate-pulse w-2/3" />
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>

              <p className="text-center text-[#94A3B8] text-sm mt-6">
                Analyzing concepts and building neural connections...
              </p>

              <Button
                variant="outline"
                onClick={onClose}
                className="w-full mt-6 h-10 border-[#2D4A7A] text-[#EF4444] hover:bg-[#EF4444]/10 hover:border-[#EF4444]"
              >
                Cancel
              </Button>
            </div>
          )}

          {state === "complete" && (
            <div className="py-8 text-center">
              <div className="w-16 h-16 rounded-full bg-[#10B981]/20 flex items-center justify-center mx-auto mb-4">
                <Check className="w-8 h-8 text-[#10B981]" />
              </div>
              <h3 className="text-xl font-semibold text-[#F1F5F9] mb-2">Upload Complete!</h3>
              <p className="text-[#94A3B8]">Your document is ready to explore.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
