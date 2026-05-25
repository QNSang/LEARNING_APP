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

export type KnowledgeNode = {
  id: string
  document_id: string
  node_key: string
  label: string
  term?: string | null
  type: string
  importance: "core" | "supporting" | "detail"
  difficulty?: number | null
  description?: string | null
  node_data?: Record<string, unknown>
  created_at: string
}

export type KnowledgeEdge = {
  id: string
  document_id: string
  from_node_id: string
  to_node_id: string
  edge_type: string
  reason?: string | null
  confidence?: number | null
  created_at: string
}

export type NodeChunkRef = {
  id: string
  node_id: string
  chunk_id: string
  evidence?: string | null
  source_ref?: string | null
  confidence?: number | null
  created_at: string
}

export type LearningGraph = {
  document_id: string
  nodes: KnowledgeNode[]
  edges: KnowledgeEdge[]
  citations: NodeChunkRef[]
}

export type DocumentStatus =
  | "new"
  | "processing"
  | "ready"
  | "partial_success"
  | "error"
  | "cancelled"
  | "ready_to_reprocess"

export type Document = {
  id: string
  title: string
  subject?: string | null
  file_path?: string | null
  file_hash?: string | null
  status: DocumentStatus
  token_count?: number | null
  selected_model?: string | null
  processing_config: Record<string, unknown>
  error_message?: string | null
  created_at: string
  updated_at: string
}

export type PipelineJobStatus = "pending" | "processing" | "success" | "failed"

export type PipelineJobStage =
  | "queued"
  | "parse"
  | "chunk"
  | "extract"
  | "cleanup"
  | "done"
  | "failed"

export type PipelineJob = {
  id: string
  document_id: string
  celery_task_id?: string | null
  status: PipelineJobStatus
  stage: PipelineJobStage
  progress: number
  error_message?: string | null
  result: Record<string, unknown>
  created_at: string
  updated_at: string
}

export type DocumentUploadResponse = {
  document: Document
  job_id: string
  task_id: string
  status: PipelineJobStatus
}

export type ChunkingResult = {
  document_id: string
  chunk_count: number
  chunks: Array<{
    id: string
    chunk_index: number
    token_count?: number | null
    source_ref?: string | null
  }>
}

export type GraphCleanupResult = {
  document_id: string
  deduplication: Record<string, unknown>
  validation: Record<string, unknown>
  graph: LearningGraph
}

export async function getDocuments() {
  const response = await fetch(`${getApiBaseUrl()}/api/documents`, {
    cache: "no-store",
  })

  if (!response.ok) {
    throw new Error("Unable to load documents")
  }

  return (await response.json()) as Document[]
}

export async function uploadDocument(input: {
  file: File
  subject?: string
  selectedModel?: string
}) {
  const formData = new FormData()
  formData.append("file", input.file)

  if (input.subject) {
    formData.append("subject", input.subject)
  }

  if (input.selectedModel) {
    formData.append("selected_model", input.selectedModel)
  }

  const response = await fetch(`${getApiBaseUrl()}/api/documents/upload`, {
    method: "POST",
    body: formData,
  })

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "Unable to upload document"))
  }

  return (await response.json()) as DocumentUploadResponse
}

export async function getPipelineJob(jobId: string) {
  const response = await fetch(`${getApiBaseUrl()}/api/pipeline-jobs/${jobId}`, {
    cache: "no-store",
  })

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "Unable to load pipeline job"))
  }

  return (await response.json()) as PipelineJob
}

export async function getLatestDocumentPipelineJob(documentId: string) {
  const response = await fetch(
    `${getApiBaseUrl()}/api/documents/${documentId}/pipeline-jobs/latest`,
    { cache: "no-store" }
  )

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "Unable to load pipeline job"))
  }

  return (await response.json()) as PipelineJob
}

export async function processDocument(documentId: string) {
  const response = await fetch(
    `${getApiBaseUrl()}/api/documents/${documentId}/process`,
    { method: "POST" }
  )

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "Unable to process document"))
  }

  return (await response.json()) as ChunkingResult
}

export async function extractDocumentGraph(documentId: string) {
  const response = await fetch(
    `${getApiBaseUrl()}/api/documents/${documentId}/extract-graph`,
    { method: "POST" }
  )

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "Unable to extract graph"))
  }

  return (await response.json()) as LearningGraph
}

export async function cleanupDocumentGraph(documentId: string) {
  const response = await fetch(
    `${getApiBaseUrl()}/api/documents/${documentId}/cleanup-graph`,
    { method: "POST" }
  )

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "Unable to cleanup graph"))
  }

  return (await response.json()) as GraphCleanupResult
}

export async function getDocumentGraph(documentId: string) {
  const response = await fetch(
    `${getApiBaseUrl()}/api/documents/${documentId}/graph`,
    { cache: "no-store" }
  )

  if (!response.ok) {
    throw new Error("Unable to load document graph")
  }

  return (await response.json()) as LearningGraph
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

async function getErrorMessage(response: Response, fallback: string) {
  try {
    const data = (await response.json()) as { detail?: string }
    return data.detail ?? fallback
  } catch {
    return fallback
  }
}
