"use client"

import { useEffect, useMemo, useState } from "react"
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Panel,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
  useEdgesState,
  useNodesState,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"

import type { KnowledgeNode, LearningGraph, NodeChunkRef } from "@/lib/api"

type LearningNodeData = {
  node: KnowledgeNode
}

const importanceStyles: Record<
  string,
  {
    node: string
    handle: string
    minimap: string
  }
> = {
  core: {
    node: "border-[#38BDF8] bg-[#0F2A44] text-[#E0F2FE] shadow-[0_0_32px_rgba(56,189,248,0.18)]",
    handle: "!bg-[#38BDF8]",
    minimap: "#38BDF8",
  },
  supporting: {
    node: "border-[#A78BFA] bg-[#221B46] text-[#EDE9FE] shadow-[0_0_28px_rgba(167,139,250,0.14)]",
    handle: "!bg-[#A78BFA]",
    minimap: "#A78BFA",
  },
  detail: {
    node: "border-[#64748B] bg-[#172033] text-[#E2E8F0]",
    handle: "!bg-[#94A3B8]",
    minimap: "#64748B",
  },
}

function LearningGraphNode({ data }: NodeProps<Node<LearningNodeData>>) {
  const node = data.node
  const style = importanceStyles[node.importance] ?? importanceStyles.supporting

  return (
    <div
      className={`w-64 cursor-grab rounded-lg border px-3.5 py-3 active:cursor-grabbing ${style.node}`}
    >
      <Handle type="target" position={Position.Top} className={style.handle} />
      <div className="flex items-center justify-between gap-3">
        <div className="truncate text-[11px] font-medium uppercase text-[#CBD5E1]">
          {node.type}
        </div>
        {node.difficulty ? (
          <span className="rounded border border-white/10 bg-white/5 px-1.5 py-0.5 text-[11px] text-[#CBD5E1]">
            L{node.difficulty}
          </span>
        ) : null}
      </div>
      <div className="mt-2 line-clamp-2 text-sm font-semibold leading-5">
        {node.label}
      </div>
      {node.description ? (
        <p className="mt-2 line-clamp-2 text-xs leading-5 text-[#CBD5E1]">
          {node.description}
        </p>
      ) : null}
      <div className="mt-3 flex items-center justify-between text-[11px] uppercase text-[#CBD5E1]">
        <span>{node.importance}</span>
        <span>{node.term ?? node.node_key}</span>
      </div>
      <Handle type="source" position={Position.Bottom} className={style.handle} />
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

  const initialNodes = useMemo(() => createFlowNodes(graph), [graph])
  const initialEdges = useMemo(() => createFlowEdges(graph), [graph])
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  useEffect(() => {
    setNodes(initialNodes)
    setEdges(initialEdges)
  }, [initialNodes, initialEdges, setEdges, setNodes])

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

  if (!graph.nodes.length) {
    return (
      <div className="mt-6 rounded-md border border-border px-5 py-12 text-sm text-muted-foreground">
        No graph nodes found for this document. Run document processing, graph
        extraction, and graph cleanup first.
      </div>
    )
  }

  return (
    <div className="mt-6 grid min-h-[720px] gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
      <section className="min-h-[680px] overflow-hidden rounded-lg border border-border bg-[#08111F]">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
          fitViewOptions={{ padding: 0.18 }}
          minZoom={0.25}
          maxZoom={1.8}
          nodesDraggable
          nodesConnectable={false}
          elementsSelectable
          selectNodesOnDrag={false}
          panOnDrag
          onNodeClick={(_, node) => setSelectedNodeId(node.id)}
        >
          <Background color="#1F2D45" gap={24} size={1.2} />
          <MiniMap
            pannable
            zoomable
            nodeColor={(node) => {
              const data = node.data as LearningNodeData
              return (
                importanceStyles[data.node.importance]?.minimap ??
                importanceStyles.supporting.minimap
              )
            }}
            maskColor="rgba(8, 17, 31, 0.72)"
            className="!bg-[#0A0E1A] !border !border-border"
          />
          <Controls
            showInteractive={false}
            className="!border !border-border !bg-[#111827] [&_button]:!border-border [&_button]:!bg-[#111827] [&_button]:!text-[#E2E8F0] [&_button:hover]:!bg-[#1C2333]"
          />
          <Panel position="top-left">
            <div className="flex flex-wrap items-center gap-2 rounded-md border border-border bg-[#111827]/95 px-3 py-2 text-xs text-muted-foreground shadow-xl">
              <span>{graph.nodes.length} nodes</span>
              <span className="text-[#475569]">/</span>
              <span>{graph.edges.length} edges</span>
              <span className="text-[#475569]">/</span>
              <span>drag nodes to arrange the map</span>
            </div>
          </Panel>
        </ReactFlow>
      </section>

      <CitationPanel node={selectedNode} citations={selectedCitations} />
    </div>
  )
}

function createFlowNodes(graph: LearningGraph): Node<LearningNodeData>[] {
  const radiusX = 360
  const radiusY = 240
  const centerX = 420
  const centerY = 300

  return graph.nodes.map((node, index) => {
    const angle = (index / Math.max(graph.nodes.length, 1)) * Math.PI * 2
    const ring = node.importance === "core" ? 0.55 : node.importance === "detail" ? 1.2 : 0.9

    return {
      id: node.id,
      type: "learningNode",
      position: {
        x: centerX + Math.cos(angle) * radiusX * ring,
        y: centerY + Math.sin(angle) * radiusY * ring,
      },
      data: { node },
      draggable: true,
    }
  })
}

function createFlowEdges(graph: LearningGraph): Edge[] {
  return graph.edges.map((edge) => ({
    id: edge.id,
    source: edge.from_node_id,
    target: edge.to_node_id,
    label: edge.edge_type.replaceAll("_", " "),
    type: "bezier",
    animated: edge.confidence ? edge.confidence >= 0.75 : false,
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: "#64748B",
    },
    style: {
      stroke: "#64748B",
      strokeWidth: 2,
    },
    labelBgPadding: [8, 4],
    labelBgBorderRadius: 4,
    labelBgStyle: {
      fill: "#111827",
      fillOpacity: 0.9,
    },
    labelStyle: {
      fill: "#CBD5E1",
      fontSize: 12,
      fontWeight: 500,
    },
  }))
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
