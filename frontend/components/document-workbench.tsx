"use client"

import Link from "next/link"
import { useEffect, useMemo, useState, useTransition } from "react"
import {
  ArrowRight,
  Brain,
  CheckCircle2,
  FileText,
  GitBranch,
  Loader2,
  RefreshCw,
  Upload,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import {
  getLatestDocumentPipelineJob,
  getDocuments,
  getPipelineJob,
  uploadDocument,
  type Document,
  type PipelineJob,
} from "@/lib/api"
import { cn } from "@/lib/utils"

type PipelineStage = "upload" | "pipeline"

type WorkbenchEvent = {
  id: string
  label: string
  tone: "success" | "info" | "warning"
}

const statusStyles: Record<Document["status"], string> = {
  new: "border-sky-400/30 bg-sky-400/10 text-sky-100",
  processing: "border-amber-400/30 bg-amber-400/10 text-amber-100",
  ready: "border-emerald-400/30 bg-emerald-400/10 text-emerald-100",
  partial_success: "border-cyan-400/30 bg-cyan-400/10 text-cyan-100",
  error: "border-rose-400/30 bg-rose-400/10 text-rose-100",
  cancelled: "border-slate-400/30 bg-slate-400/10 text-slate-200",
  ready_to_reprocess: "border-cyan-400/30 bg-cyan-400/10 text-cyan-100",
}

const PIPELINE_POLL_INTERVAL_MS = Number(
  process.env.NEXT_PUBLIC_PIPELINE_POLL_INTERVAL_MS ?? 2000
)

export function DocumentWorkbench({
  initialDocuments,
  backendOnline,
}: {
  initialDocuments: Document[]
  backendOnline: boolean
}) {
  const [documents, setDocuments] = useState(initialDocuments)
  const [selectedDocumentId, setSelectedDocumentId] = useState(
    initialDocuments[0]?.id ?? ""
  )
  const [file, setFile] = useState<File | null>(null)
  const [subject, setSubject] = useState("")
  const [selectedModel, setSelectedModel] = useState("gemini-2.5-flash-lite")
  const [activeStage, setActiveStage] = useState<PipelineStage | null>(null)
  const [activeJob, setActiveJob] = useState<PipelineJob | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [events, setEvents] = useState<WorkbenchEvent[]>([])
  const [isPending, startTransition] = useTransition()

  const selectedDocument = useMemo(
    () => documents.find((document) => document.id === selectedDocumentId),
    [documents, selectedDocumentId]
  )

  const readyDocuments = documents.filter(
    (document) =>
      document.status === "ready" || document.status === "partial_success"
  )
  const errorDocuments = documents.filter((document) => document.status === "error")
  const completion = documents.length
    ? Math.round((readyDocuments.length / documents.length) * 100)
    : 0
  const pipelineActive =
    activeJob?.status === "pending" || activeJob?.status === "processing"
  const selectedPipelineJob =
    activeJob?.document_id === selectedDocument?.id ? activeJob : null

  useEffect(() => {
    if (!activeJob || !pipelineActive) return

    const timer = window.setInterval(() => {
      void (async () => {
        try {
          const latestJob = await getPipelineJob(activeJob.id)
          setActiveJob(latestJob)
          if (latestJob.status === "success") {
            await refreshDocuments(latestJob.document_id)
            setMessage("Pipeline completed. The graph is ready to inspect.")
            addEvent("Async document pipeline completed.", "success")
          } else if (latestJob.status === "failed") {
            await refreshDocuments(latestJob.document_id)
            setMessage(latestJob.error_message ?? "Pipeline failed.")
            addEvent("Pipeline failed. Check the error message.", "warning")
          }
        } catch (error) {
          setMessage(error instanceof Error ? error.message : "Unable to poll job")
        }
      })()
    }, PIPELINE_POLL_INTERVAL_MS)

    return () => window.clearInterval(timer)
  }, [activeJob, pipelineActive])

  useEffect(() => {
    if (!selectedDocument || selectedDocument.status !== "processing") return

    void (async () => {
      try {
        const latestJob = await getLatestDocumentPipelineJob(selectedDocument.id)
        if (latestJob.status === "pending" || latestJob.status === "processing") {
          setActiveJob(latestJob)
        }
      } catch {
        // Older documents may not have async pipeline jobs yet.
      }
    })()
  }, [selectedDocument])

  function addEvent(label: string, tone: WorkbenchEvent["tone"] = "info") {
    setEvents((current) => [
      { id: crypto.randomUUID(), label, tone },
      ...current,
    ].slice(0, 5))
  }

  async function refreshDocuments(nextSelectedId?: string) {
    const latest = await getDocuments()
    setDocuments(latest)
    if (nextSelectedId) {
      setSelectedDocumentId(nextSelectedId)
    } else if (!latest.some((document) => document.id === selectedDocumentId)) {
      setSelectedDocumentId(latest[0]?.id ?? "")
    }
    return latest
  }

  function runAction(stage: PipelineStage, action: () => Promise<void>) {
    setActiveStage(stage)
    setMessage(null)
    startTransition(() => {
      void (async () => {
        try {
          await action()
        } catch (error) {
          setMessage(error instanceof Error ? error.message : "Action failed")
          addEvent("Pipeline stopped. Check the message above.", "warning")
        } finally {
          setActiveStage(null)
        }
      })()
    })
  }

  function handleUpload() {
    if (!file) {
      setMessage("Choose a PDF or TXT file first.")
      return
    }

    runAction("upload", async () => {
      const response = await uploadDocument({
        file,
        subject: subject.trim() || undefined,
        selectedModel: selectedModel.trim() || undefined,
      })
      const { document } = response
      const job = await getPipelineJob(response.job_id)
      setActiveJob(job)
      await refreshDocuments(document.id)
      setFile(null)
      setMessage(`${document.title} uploaded. Pipeline queued.`)
      addEvent("Document uploaded and async pipeline queued.", "success")
    })
  }

  const busy = isPending || activeStage !== null || pipelineActive

  return (
    <div className="grid gap-5 xl:grid-cols-[360px_minmax(0,1fr)]">
      <section className="rounded-lg border border-border bg-[#111827]/90">
        <div className="border-b border-border px-5 py-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase text-muted-foreground">
                Intake
              </p>
              <h2 className="mt-1 text-lg font-semibold">Upload document</h2>
            </div>
            <Upload className="size-5 text-cyan-200" />
          </div>
        </div>

        <div className="space-y-5 px-5 py-5">
          <div className="space-y-2">
            <Label htmlFor="document-file">Source file</Label>
            <Input
              id="document-file"
              type="file"
              accept=".pdf,.txt"
              disabled={!backendOnline || busy}
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="subject">Subject</Label>
            <Input
              id="subject"
              placeholder="Machine learning, biology, history..."
              value={subject}
              disabled={!backendOnline || busy}
              onChange={(event) => setSubject(event.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="model">Extraction model</Label>
            <Input
              id="model"
              value={selectedModel}
              disabled={!backendOnline || busy}
              onChange={(event) => setSelectedModel(event.target.value)}
            />
          </div>

          <Button
            className="w-full"
            disabled={!backendOnline || busy}
            onClick={handleUpload}
          >
            {activeStage === "upload" ? (
              <Loader2 className="animate-spin" />
            ) : (
              <Upload />
            )}
            Upload
          </Button>

          <div className="rounded-md border border-border bg-[#0A0E1A] px-4 py-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Ready documents</span>
              <span className="font-medium">{completion}%</span>
            </div>
            <Progress className="mt-3" value={completion} />
          </div>
        </div>
      </section>

      <section className="min-w-0 rounded-lg border border-border bg-[#111827]/90">
        <div className="flex flex-col gap-4 border-b border-border px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-medium uppercase text-muted-foreground">
              Workspace
            </p>
            <h2 className="mt-1 text-lg font-semibold">Document pipeline</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={!backendOnline || busy}
              onClick={() =>
                runAction("upload", async () => {
                  await refreshDocuments()
                  addEvent("Document list refreshed.", "info")
                })
              }
            >
              <RefreshCw className={cn(activeStage === "upload" && "animate-spin")} />
              Refresh
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link href="/dashboard">
                <Brain />
                Dashboard
              </Link>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link href="/progress">
                <CheckCircle2 />
                Reviews
              </Link>
            </Button>
          </div>
        </div>

        <div className="grid min-h-[520px] gap-0 lg:grid-cols-[minmax(0,1fr)_320px]">
          <div className="min-w-0 border-b border-border lg:border-b-0 lg:border-r">
            <div className="grid grid-cols-[1fr_110px_120px] gap-3 border-b border-border bg-[#0A0E1A] px-4 py-3 text-xs font-medium uppercase text-muted-foreground md:grid-cols-[1fr_130px_150px]">
              <span>Document</span>
              <span>Status</span>
              <span>Updated</span>
            </div>

            {documents.length ? (
              <div className="divide-y divide-border">
                {documents.map((document) => (
                  <button
                    key={document.id}
                    className={cn(
                      "grid w-full grid-cols-[1fr_110px_120px] gap-3 px-4 py-4 text-left transition hover:bg-[#1C2333] md:grid-cols-[1fr_130px_150px]",
                      selectedDocumentId === document.id && "bg-[#1C2333]"
                    )}
                    onClick={() => setSelectedDocumentId(document.id)}
                  >
                    <span className="min-w-0">
                      <span className="flex items-center gap-2">
                        <FileText className="size-4 shrink-0 text-cyan-200" />
                        <span className="truncate font-medium">{document.title}</span>
                      </span>
                      <span className="mt-1 block truncate text-sm text-muted-foreground">
                        {document.subject || "No subject"} -{" "}
                        {document.token_count ?? 0} tokens
                      </span>
                    </span>
                    <span>
                      <Badge
                        variant="outline"
                        className={cn("capitalize", statusStyles[document.status])}
                      >
                        {document.status.replaceAll("_", " ")}
                      </Badge>
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {new Intl.DateTimeFormat("vi-VN", {
                        day: "2-digit",
                        month: "2-digit",
                        hour: "2-digit",
                        minute: "2-digit",
                      }).format(new Date(document.updated_at))}
                    </span>
                  </button>
                ))}
              </div>
            ) : (
              <div className="px-5 py-16 text-sm text-muted-foreground">
                Upload your first PDF or TXT file to start building a learning graph.
              </div>
            )}
          </div>

          <aside className="bg-[#0A0E1A]/60 px-5 py-5">
            {selectedDocument ? (
              <div className="space-y-5">
                <div>
                  <p className="text-xs font-medium uppercase text-muted-foreground">
                    Selected
                  </p>
                  <h3 className="mt-2 text-base font-semibold">
                    {selectedDocument.title}
                  </h3>
                  {selectedDocument.error_message ? (
                    <p className="mt-2 text-sm text-rose-200">
                      {selectedDocument.error_message}
                    </p>
                  ) : null}
                </div>

                <div className="grid gap-3">
                  <div className="rounded-md border border-border bg-[#111827] px-4 py-3">
                    <div className="flex items-center justify-between gap-3 text-sm">
                      <span className="flex items-center gap-2 text-muted-foreground">
                        {selectedPipelineJob?.status === "pending" ||
                        selectedPipelineJob?.status === "processing" ? (
                          <Loader2 className="size-4 animate-spin text-amber-200" />
                        ) : (
                          <GitBranch className="size-4 text-cyan-200" />
                        )}
                        Pipeline
                      </span>
                      <span className="capitalize">
                        {selectedPipelineJob?.stage ?? selectedDocument.status}
                      </span>
                    </div>
                    <Progress
                      className="mt-3"
                      value={selectedPipelineJob?.progress ?? 0}
                    />
                    {selectedPipelineJob ? (
                      <p className="mt-2 text-xs text-muted-foreground">
                        {selectedPipelineJob.status} - {selectedPipelineJob.progress}%
                      </p>
                    ) : (
                      <p className="mt-2 text-xs text-muted-foreground">
                        Upload a document to queue the full async pipeline.
                      </p>
                    )}
                  </div>

                  {selectedDocument.status === "ready" ||
                  selectedDocument.status === "partial_success" ? (
                    <Button asChild>
                      <Link href={`/graph/${selectedDocument.id}`}>
                        Open graph
                        <ArrowRight />
                      </Link>
                    </Button>
                  ) : (
                    <Button disabled>
                      Open graph
                      <ArrowRight />
                    </Button>
                  )}
                </div>

                {message ? (
                  <div className="rounded-md border border-cyan-400/30 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-50">
                    {message}
                  </div>
                ) : null}

                <div className="space-y-3">
                  <p className="text-xs font-medium uppercase text-muted-foreground">
                    Activity
                  </p>
                  {events.length ? (
                    events.map((event) => (
                      <div
                        key={event.id}
                        className={cn(
                          "rounded-md border px-3 py-2 text-sm",
                          event.tone === "success" &&
                            "border-emerald-400/30 bg-emerald-400/10 text-emerald-50",
                          event.tone === "info" &&
                            "border-sky-400/30 bg-sky-400/10 text-sky-50",
                          event.tone === "warning" &&
                            "border-amber-400/30 bg-amber-400/10 text-amber-50"
                        )}
                      >
                        {event.label}
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      Pipeline events will appear here as you work.
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">
                Select or upload a document to run the learning pipeline.
              </div>
            )}
          </aside>
        </div>

        {errorDocuments.length ? (
          <div className="border-t border-border px-5 py-3 text-sm text-amber-100">
            {errorDocuments.length} document needs attention before continuing.
          </div>
        ) : null}
      </section>
    </div>
  )
}
