const DEFAULT_API_BASE_URL = "http://localhost:8000"

export function getApiBaseUrl() {
  return (
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    DEFAULT_API_BASE_URL
  )
}

export function getHealthUrl() {
  return `${getApiBaseUrl()}/health`
}

export type ReviewQueue = {
  user_id?: string | null
  due_at: string
  items: Array<{
    node_label: string
    node_description?: string | null
    prerequisite_count: number
    priority: number
    mastery: {
      id: string
      node_id: string
      mastery_score: number
      status: string
      next_review_at?: string | null
      review_count: number
      correct_count: number
      wrong_count: number
    }
    practice_item?: {
      id: string
      question: string
      type: string
    } | null
  }>
}

export async function getReviewQueue(userId?: string) {
  const params = userId ? `?user_id=${encodeURIComponent(userId)}` : ""
  const response = await fetch(`${getApiBaseUrl()}/api/review/queue${params}`, {
    cache: "no-store",
  })

  if (!response.ok) {
    throw new Error("Unable to load review queue")
  }

  return (await response.json()) as ReviewQueue
}

export type Workspace = {
  id: string
  title: string
  subject?: string | null
  description?: string | null
  created_at: string
}

export type WorkspaceKnowledgeBase = {
  workspace: Workspace
  documents: Array<{
    id: string
    title: string
    subject?: string | null
    status: string
    created_at: string
  }>
  cross_document_concepts: Array<{
    canonical_key: string
    label: string
    document_count: number
    node_count: number
    descriptions: string[]
  }>
}

export async function getWorkspaces() {
  const response = await fetch(`${getApiBaseUrl()}/api/workspaces`, {
    cache: "no-store",
  })

  if (!response.ok) {
    throw new Error("Unable to load workspaces")
  }

  return (await response.json()) as Workspace[]
}

export async function getWorkspaceKnowledgeBase(workspaceId: string) {
  const response = await fetch(
    `${getApiBaseUrl()}/api/workspaces/${workspaceId}/knowledge-base`,
    { cache: "no-store" }
  )

  if (!response.ok) {
    throw new Error("Unable to load workspace knowledge base")
  }

  return (await response.json()) as WorkspaceKnowledgeBase
}

export type Neo4jRuntimeStatus = {
  state: "disabled" | "not_configured" | "ready" | "unavailable"
  enabled: boolean
  configured: boolean
  message: string
}

export async function getNeo4jStatus() {
  const response = await fetch(`${getApiBaseUrl()}/api/neo4j/status`, {
    cache: "no-store",
  })

  if (!response.ok) {
    throw new Error("Unable to load Neo4j status")
  }

  return (await response.json()) as Neo4jRuntimeStatus
}
