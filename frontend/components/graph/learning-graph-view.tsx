"use client"

import { useMemo, useState } from "react"
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"

import type { KnowledgeNode, LearningGraph, NodeChunkRef } from "@/lib/api"

type LearningNodeData = {
  node: KnowledgeNode
}

const importanceClasses: Record<string, string> = {
  core: "border-[#3B82F6] bg-[#1E3A5F] text-[#DBEAFE]",
  supporting: "border-[#8B5CF6] bg-[#1E1B4B] text-[#EDE9FE]",
  detail: "border-[#475569] bg-[#1C2333] text-[#E2E8F0]",
}

function LearningGraphNode({ data }: NodeProps<Node<LearningNodeData>>) {
  const node = data.node
  const className =
    importanceClasses[node.importance] ?? importanceClasses.supporting

  return (
    <div className={`w-56 rounded-md border px-3 py-2 shadow-lg ${className}`}>
      <Handle type="target" position={Position.Top} className="!bg-[#94A3B8]" />
      <div className="text-xs uppercase text-[#CBD5E1]">{node.type}</div>
      <div className="mt-1 line-clamp-2 text-sm font-semibold">{node.label}</div>
      <div className="mt-2 flex items-center justify-between text-xs text-[#CBD5E1]">
        <span>{node.importance}</span>
        {node.difficulty ? <span>Level {node.difficulty}</span> : null}
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-[#94A3B8]" />
    </div>
  )
}

const nodeTypes = {
  learningNode: LearningGraphNode,
}

export function LearningGraphView({ graph }: { graph: LearningGraph }) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(
    graph.nodes[0]?.id ?? null
  )

  const selectedNode = useMemo(
    () => graph.nodes.find((node) => node.id === selectedNodeId) ?? null,
    [graph.nodes, selectedNodeId]
  )
  const selectedCitations = useMemo(
    () =>
      selectedNode
        ? graph.citations.filter((citation) => citation.node_id === selectedNode.id)
        : [],
    [graph.citations, selectedNode]
  )

  const flowNodes = useMemo<Node<LearningNodeData>[]>(
    () =>
      graph.nodes.map((node, index) => {
        const columns = 4
        return {
          id: node.id,
          type: "learningNode",
          position: {
            x: (index % columns) * 300,
            y: Math.floor(index / columns) * 180,
          },
          data: { node },
        }
      }),
    [graph.nodes]
  )

  const flowEdges = useMemo<Edge[]>(
    () =>
      graph.edges.map((edge) => ({
        id: edge.id,
        source: edge.from_node_id,
        target: edge.to_node_id,
        label: edge.edge_type,
        type: "smoothstep",
        markerEnd: {
          type: MarkerType.ArrowClosed,
        },
        style: {
          stroke: "#64748B",
          strokeWidth: 2,
        },
        labelStyle: {
          fill: "#CBD5E1",
          fontSize: 12,
        },
      })),
    [graph.edges]
  )

  if (!graph.nodes.length) {
    return (
      <div className="mt-6 rounded-md border border-border px-5 py-12 text-sm text-muted-foreground">
        No graph nodes found for this document. Run document processing, graph
        extraction, and graph cleanup first.
      </div>
    )
  }

  return (
    <div className="mt-6 grid min-h-[680px] gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
      <section className="min-h-[620px] overflow-hidden rounded-md border border-border bg-[#0A0E1A]">
        <ReactFlow
          nodes={flowNodes}
          edges={flowEdges}
          nodeTypes={nodeTypes}
          fitView
          minZoom={0.25}
          maxZoom={1.5}
          onNodeClick={(_, node) => setSelectedNodeId(node.id)}
        >
          <Background color="#1F2D45" gap={24} />
          <Controls />
        </ReactFlow>
      </section>

      <CitationPanel node={selectedNode} citations={selectedCitations} />
    </div>
  )
}

function CitationPanel({
  node,
  citations,
}: {
  node: KnowledgeNode | null
  citations: NodeChunkRef[]
}) {
  if (!node) {
    return (
      <aside className="rounded-md border border-border p-5 text-sm text-muted-foreground">
        Select a node to inspect its source evidence.
      </aside>
    )
  }

  return (
    <aside className="rounded-md border border-border bg-card">
      <div className="border-b border-border px-5 py-4">
        <div className="text-xs uppercase text-muted-foreground">{node.type}</div>
        <h2 className="mt-1 text-lg font-semibold">{node.label}</h2>
        <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
          <span className="rounded-sm border border-border px-2 py-1">
            {node.importance}
          </span>
          {node.difficulty ? (
            <span className="rounded-sm border border-border px-2 py-1">
              Level {node.difficulty}
            </span>
          ) : null}
        </div>
      </div>

      <div className="space-y-5 px-5 py-5">
        {node.description ? (
          <section>
            <div className="text-xs uppercase text-muted-foreground">Description</div>
            <p className="mt-2 text-sm leading-6 text-[#CBD5E1]">{node.description}</p>
          </section>
        ) : null}

        <section>
          <div className="text-xs uppercase text-muted-foreground">Citations</div>
          {citations.length ? (
            <div className="mt-3 space-y-3">
              {citations.map((citation) => (
                <div key={citation.id} className="rounded-md border border-border p-3">
                  <div className="text-xs text-muted-foreground">
                    {citation.source_ref ?? "Unknown source"}
                  </div>
                  {citation.evidence ? (
                    <p className="mt-2 text-sm leading-6 text-[#E2E8F0]">
                      {citation.evidence}
                    </p>
                  ) : (
                    <p className="mt-2 text-sm text-muted-foreground">
                      No evidence text stored for this citation.
                    </p>
                  )}
                  {typeof citation.confidence === "number" ? (
                    <div className="mt-2 text-xs text-muted-foreground">
                      Confidence {Math.round(citation.confidence * 100)}%
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-3 text-sm text-muted-foreground">
              No citation is linked to this node yet.
            </p>
          )}
        </section>
      </div>
    </aside>
  )
}
