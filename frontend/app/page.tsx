import Link from "next/link"
import type React from "react"
import { Activity, Database, Network, ShieldCheck } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { DocumentWorkbench } from "@/components/document-workbench"
import {
  getDocuments,
  getHealthUrl,
  getNeo4jStatus,
  type Document,
  type Neo4jRuntimeStatus,
} from "@/lib/api"

async function getBackendStatus() {
  try {
    const response = await fetch(getHealthUrl(), {
      cache: "no-store",
    })

    if (!response.ok) {
      return "offline"
    }

    const data = (await response.json()) as { status?: string }
    return data.status === "ok" ? "online" : "offline"
  } catch {
    return "offline"
  }
}

export default async function HomePage() {
  const backendStatus = await getBackendStatus()
  const isOnline = backendStatus === "online"
  let documents: Document[] = []
  let neo4jStatus: Neo4jRuntimeStatus | null = null

  if (isOnline) {
    try {
      documents = await getDocuments()
    } catch {
      documents = []
    }

    try {
      neo4jStatus = await getNeo4jStatus()
    } catch {
      neo4jStatus = null
    }
  }

  const readyCount = documents.filter((document) => document.status === "ready").length
  const totalTokens = documents.reduce(
    (sum, document) => sum + (document.token_count ?? 0),
    0
  )

  return (
    <main className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border bg-[#0A0E1A]/95">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-md border border-cyan-300/30 bg-cyan-300/10">
                <Network className="size-5 text-cyan-100" />
              </div>
              <div>
                <p className="text-xs font-medium uppercase text-muted-foreground">
                  AI Learning OS
                </p>
                <h1 className="text-2xl font-semibold tracking-tight">
                  Knowledge graph workspace
                </h1>
              </div>
            </div>
          </div>

          <nav className="flex flex-wrap items-center gap-2 text-sm">
            <Link
              className="rounded-md px-3 py-2 text-muted-foreground transition hover:bg-secondary hover:text-foreground"
              href="/dashboard"
            >
              Dashboard
            </Link>
            <Link
              className="rounded-md px-3 py-2 text-muted-foreground transition hover:bg-secondary hover:text-foreground"
              href="/progress"
            >
              Progress
            </Link>
            <Badge
              variant="outline"
              className={
                isOnline
                  ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-100"
                  : "border-rose-400/30 bg-rose-400/10 text-rose-100"
              }
            >
              <span
                className={`size-2 rounded-full ${
                  isOnline ? "bg-emerald-300" : "bg-rose-300"
                }`}
              />
              API {backendStatus}
            </Badge>
          </nav>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-6">
        <div className="grid gap-4 md:grid-cols-4">
          <SystemMetric
            icon={<Activity className="size-4" />}
            label="Documents"
            value={documents.length.toString()}
            detail={`${readyCount} ready`}
          />
          <SystemMetric
            icon={<Database className="size-4" />}
            label="Token corpus"
            value={totalTokens.toLocaleString("vi-VN")}
            detail="Parsed source tokens"
          />
          <SystemMetric
            icon={<ShieldCheck className="size-4" />}
            label="Graph runtime"
            value={neo4jStatus?.state.replaceAll("_", " ") ?? "unknown"}
            detail={neo4jStatus?.enabled ? "Neo4j enabled" : "Local graph mode"}
          />
          <SystemMetric
            icon={<Network className="size-4" />}
            label="API base"
            value="localhost:8000"
            detail="FastAPI backend"
          />
        </div>

        <div className="mt-6">
          <DocumentWorkbench
            initialDocuments={documents}
            backendOnline={isOnline}
          />
        </div>
      </section>
    </main>
  )
}

function SystemMetric({
  icon,
  label,
  value,
  detail,
}: {
  icon: React.ReactNode
  label: string
  value: string
  detail: string
}) {
  return (
    <div className="rounded-lg border border-border bg-[#111827]/90 px-4 py-4">
      <div className="flex items-center justify-between gap-3 text-muted-foreground">
        <span className="text-sm">{label}</span>
        <span className="text-cyan-100">{icon}</span>
      </div>
      <p className="mt-3 truncate text-2xl font-semibold capitalize">{value}</p>
      <p className="mt-1 truncate text-sm text-muted-foreground">{detail}</p>
    </div>
  )
}
