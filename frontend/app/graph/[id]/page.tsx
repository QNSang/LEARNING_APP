"use client"

import { useState, useEffect, useCallback, use } from "react"
import {
    ReactFlow,
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    MarkerType,
    Node as FlowNode,
    Edge as FlowEdge
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"

import { Sidebar } from "@/components/knowledge-map/sidebar"
import { KnowledgeNode } from "@/components/knowledge-map/knowledge-node"
import { Button } from "@/components/ui/button"
import { ChevronLeft, Info, BrainCircuit, X, Sparkles, Loader2, LayoutDashboard, Share2 } from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { useSidebar } from "@/components/sidebar-context"

export interface AIExplanation {
    intuition: string;
    applications: string[];
    requirements?: string[];
}

export interface NodeData extends Record<string, unknown> {
    id: string;
    label: string;
    type: string;
    importance: string;
    status: string;
    explanation: AIExplanation | null;
}

export type KnowledgeGraphNode = FlowNode<NodeData>;

export interface DocInfo {
    id?: string;
    title: string;
    subject: string;
    [key: string]: unknown;
}

const nodeTypes = {
    knowledgeNode: KnowledgeNode
}

export default function GraphPage({ params }: { params: Promise<{ id: string }> }) {
    const { isCollapsed } = useSidebar()
    const { id } = use(params)
    const [nodes, setNodes, onNodesChange] = useNodesState<KnowledgeGraphNode>([])
    const [edges, setEdges, onEdgesChange] = useEdgesState<FlowEdge>([])
    const [selectedNode, setSelectedNode] = useState<KnowledgeGraphNode | null>(null)
    const [docInfo, setDocInfo] = useState<DocInfo | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [zoomLevel, setZoomLevel] = useState(100)

    // Filter States
    const [activeTypes, setActiveTypes] = useState(["concept", "procedure", "fact"])
    const [activeImportance, setActiveImportance] = useState(["core", "supporting", "detail"])

    // Spotlight effect tracker
    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            document.documentElement.style.setProperty('--mouse-x', `${e.clientX}px`)
            document.documentElement.style.setProperty('--mouse-y', `${e.clientY}px`)
        }
        window.addEventListener('mousemove', handleMouseMove)
        return () => window.removeEventListener('mousemove', handleMouseMove)
    }, [])

    const fetchGraphData = useCallback(async () => {
        if (!id || id === "undefined") return;

        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

        try {
            const docRes = await fetch(`${API_URL}/api/documents/${id}`)
            if (docRes.ok) {
                setDocInfo(await docRes.json())
            }

            const graphRes = await fetch(`${API_URL}/api/graph/${id}`)
            if (graphRes.ok) {
                const data = await graphRes.json()

                const normalizeType = (t: string) => {
                    const s = String(t || "").toLowerCase().trim()
                    if (s.includes("khái niệm") || s.includes("concept") || s.includes("định nghĩa")) return "concept"
                    if (s.includes("quy trình") || s.includes("procedure") || s.includes("thao tác") || s.includes("phương pháp")) return "procedure"
                    if (s.includes("thực tế") || s.includes("fact") || s.includes("sự thật")) return "fact"
                    return "concept"
                }

                const normalizeImportance = (i: string) => {
                    const s = String(i || "").toLowerCase().trim()
                    if (s.includes("cốt lõi") || s.includes("core") || s.includes("chính")) return "core"
                    if (s.includes("hỗ trợ") || s.includes("supporting") || s.includes("phụ") || s.includes("non_core") || s.includes("non-core")) return "supporting"
                    if (s.includes("chi tiết") || s.includes("detail") || s.includes("nhỏ")) return "detail"
                    return "supporting"
                }

                const flowNodes: KnowledgeGraphNode[] = data.nodes.map((node: any, idx: number) => {
                    const type = normalizeType(node.type)
                    const importance = normalizeImportance(node.importance)

                    return {
                        id: node.node_id,
                        type: "knowledgeNode",
                        position: { x: 100 + (idx % 4) * 300, y: 100 + Math.floor(idx / 4) * 200 },
                        data: {
                            id: node.id,
                            label: node.label,
                            type: type,
                            importance: importance,
                            status: "default",
                            explanation: node.explanation
                        },
                        // We don't set hidden here anymore as it's handled by the filter useEffect
                        hidden: false
                    }
                })

                const flowEdges: FlowEdge[] = data.edges.map((edge: any) => ({
                    id: edge.id,
                    source: edge.from_node,
                    target: edge.to_node,
                    label: edge.edge_type,
                    animated: true,
                    style: { stroke: "#3B82F6", strokeWidth: 2, opacity: 0.6 },
                    markerEnd: {
                        type: MarkerType.ArrowClosed,
                        color: "#3B82F6",
                    },
                }))

                setNodes(flowNodes)
                setEdges(flowEdges)
            }
        } catch (error) {
            console.error("Error fetching graph:", error)
        } finally {
            setIsLoading(false)
        }
    }, [id, setNodes, setEdges])

    useEffect(() => {
        fetchGraphData()
    }, [fetchGraphData])

    const onNodeClick = (_: any, node: KnowledgeGraphNode) => {
        setSelectedNode(node)
    }

    // Effect to handle subsequent filtering by setting 'hidden' property
    useEffect(() => {
        setNodes((nds) =>
            nds.map((node: KnowledgeGraphNode) => ({
                ...node,
                hidden: !activeTypes.includes(String(node.data?.type).toLowerCase()) ||
                    !activeImportance.includes(String(node.data?.importance).toLowerCase())
            }))
        )
    }, [activeTypes, activeImportance, setNodes])

    const toggleType = (type: string) => {
        const t = type.toLowerCase()
        setActiveTypes(prev =>
            prev.includes(t) ? prev.filter(x => x !== t) : [...prev, t]
        )
    }

    const toggleImportance = (imp: string) => {
        const i = imp.toLowerCase()
        setActiveImportance(prev =>
            prev.includes(i) ? prev.filter(x => x !== i) : [...prev, i]
        )
    }

    return (
        <div className="h-screen w-screen bg-[#0A0E1A] overflow-hidden flex spotlight">
            <Sidebar />

            <main className={cn(
                "flex-1 relative flex flex-col h-full transition-all duration-300 ease-in-out",
                isCollapsed ? "ml-[80px]" : "ml-[280px]"
            )}>
                {/* PRE-LOADING MESH GRADIENT */}
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-[#3B82F6]/5 blur-[120px] rounded-full -mr-64 -mt-64" />
                <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-[#8B5CF6]/5 blur-[100px] rounded-full -ml-32 -mb-32" />

                {/* Header */}
                <header className="h-16 border-b border-[#1F2D45] bg-[#0A0E1A]/60 backdrop-blur-xl flex items-center justify-between px-6 z-20">
                    <div className="flex items-center gap-4">
                        <Link href="/">
                            <Button variant="ghost" size="sm" className="text-[#94A3B8] hover:text-white hover:bg-[#1C2333]">
                                <ChevronLeft className="w-4 h-4 mr-1" />
                                Dashboard
                            </Button>
                        </Link>
                        <div className="h-4 w-px bg-[#1F2D45]" />
                        <div className="flex flex-col">
                            <h2 className="text-[#F1F5F9] font-bold text-sm tracking-tight">{docInfo?.title || "Loading Map..."}</h2>
                            <span className="text-[10px] font-bold text-[#3B82F6] uppercase tracking-widest leading-none mt-0.5">
                                {docInfo?.subject}
                            </span>
                        </div>
                    </div>

                    <div className="flex items-center gap-6">
                        <div className="flex items-center bg-[#111827] border border-[#1F2D45] rounded-lg p-1">
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-[#94A3B8] hover:text-white">
                                <LayoutDashboard className="w-4 h-4" />
                            </Button>
                            <div className="w-px h-4 bg-[#1F2D45] mx-1" />
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-[#94A3B8] hover:text-white">
                                <Share2 className="w-4 h-4" />
                            </Button>
                        </div>

                        <Button className="bg-[#3B82F6] hover:bg-[#2563EB] text-white font-bold h-9">
                            <BrainCircuit className="w-4 h-4 mr-2" />
                            Ask AI
                        </Button>
                    </div>
                </header>

                <div className="flex-1 flex overflow-hidden">
                    {/* Left Filter Panel */}
                    <aside className="w-[260px] border-r border-[#1F2D45] bg-[#111827]/40 backdrop-blur-md p-6 flex flex-col gap-8 z-10 overflow-y-auto">
                        <div>
                            <h3 className="text-[10px] font-bold text-[#475569] uppercase tracking-widest mb-4">Node Types</h3>
                            <div className="space-y-3">
                                {["Concept", "Procedure", "Fact"].map(type => (
                                    <label key={type} className="flex items-center gap-3 cursor-pointer group">
                                        <div className={cn(
                                            "w-3 h-3 rounded-full",
                                            type === "Concept" ? "bg-[#3B82F6]" : type === "Procedure" ? "bg-[#F59E0B]" : "bg-[#8B5CF6]"
                                        )} />
                                        <span className={cn(
                                            "text-sm transition-colors",
                                            activeTypes.includes(type.toLowerCase()) ? "text-[#94A3B8] group-hover:text-white" : "text-[#1F2D45] group-hover:text-[#475569]"
                                        )}>{type}</span>
                                        <input
                                            type="checkbox"
                                            checked={activeTypes.includes(type.toLowerCase())}
                                            onChange={() => toggleType(type)}
                                            className="ml-auto accent-[#3B82F6]"
                                        />
                                    </label>
                                ))}
                            </div>
                        </div>

                        <div>
                            <h3 className="text-[10px] font-bold text-[#475569] uppercase tracking-widest mb-4">Importance</h3>
                            <div className="grid grid-cols-1 gap-2">
                                {["Core", "Supporting", "Detail"].map(imp => {
                                    const isActive = activeImportance.includes(imp.toLowerCase())
                                    return (
                                        <Button
                                            key={imp}
                                            variant="outline"
                                            size="sm"
                                            onClick={() => toggleImportance(imp)}
                                            className={cn(
                                                "justify-start transition-all",
                                                isActive
                                                    ? "border-[#1F2D45] text-[#94A3B8] hover:text-white hover:border-[#3B82F6]"
                                                    : "opacity-40 border-transparent text-[#475569] hover:opacity-100"
                                            )}
                                        >
                                            <div className={cn(
                                                "w-1.5 h-1.5 rounded-full mr-2",
                                                imp === "Core" ? "bg-[#10B981]" : imp === "Supporting" ? "bg-[#3B82F6]" : "bg-[#475569]"
                                            )} />
                                            {imp}
                                        </Button>
                                    )
                                })}
                            </div>
                        </div>

                        <div className="mt-auto pt-6 border-t border-[#1F2D45]">
                            <div className="bg-[#0A0E1A] rounded-xl p-4 border border-[#1F2D45]">
                                <p className="text-[10px] font-bold text-[#475569] uppercase mb-2">Map Stats</p>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <p className="text-xl font-mono font-bold text-white">{nodes.length}</p>
                                        <p className="text-[10px] text-[#475569]">Nodes</p>
                                    </div>
                                    <div>
                                        <p className="text-xl font-mono font-bold text-white">{edges.length}</p>
                                        <p className="text-[10px] text-[#475569]">Edges</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </aside>

                    {/* React Flow Workspace */}
                    <div className="flex-1 relative bg-[#0A0E1A]">
                        <div className="absolute inset-0 dot-grid opacity-[0.05]" />

                        {isLoading ? (
                            <div className="absolute inset-0 flex items-center justify-center bg-[#0A0E1A] z-20">
                                <div className="flex flex-col items-center gap-6">
                                    <div className="relative">
                                        <div className="w-16 h-16 border-2 border-[#3B82F6]/20 rounded-full" />
                                        <div className="absolute inset-0 w-16 h-16 border-t-2 border-[#3B82F6] rounded-full animate-spin" />
                                    </div>
                                    <p className="text-[#94A3B8] font-bold text-sm tracking-widest uppercase">Initializing Neural Map</p>
                                </div>
                            </div>
                        ) : (
                            <ReactFlow
                                nodes={nodes}
                                edges={edges}
                                onNodesChange={onNodesChange}
                                onEdgesChange={onEdgesChange}
                                onNodeClick={onNodeClick}
                                nodeTypes={nodeTypes}
                                fitView
                                colorMode="dark"
                                minZoom={0.05}
                                maxZoom={4}
                            >
                                <Background color="#1F2D45" gap={24} size={1} />
                                <Controls className="!bg-[#111827] !border-[#1F2D45] !shadow-2xl" />
                                <div className="absolute bottom-6 left-6 glass-panel px-3 py-1.5 rounded-full border border-[#1F2D45] text-[10px] font-bold text-[#475569] uppercase tracking-widest">
                                    {Math.round(zoomLevel)}% Zoom
                                </div>
                            </ReactFlow>
                        )}
                    </div>
                </div>

                {/* Node Detail Side Panel */}
                {selectedNode && (
                    <NodeDetailPanel
                        node={selectedNode}
                        onClose={() => setSelectedNode(null)}
                    />
                )}
            </main>
        </div>
    )
}

function NodeDetailPanel({ node, onClose }: { node: KnowledgeGraphNode; onClose: () => void }) {
    const [explanation, setExplanation] = useState<AIExplanation | null>(null)
    const [isGenerating, setIsGenerating] = useState(false)

    useEffect(() => {
        setExplanation(node.data?.explanation || null)
    }, [node])

    const handleGenerateIntuition = async () => {
        setIsGenerating(true)
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        try {
            const res = await fetch(`${API_URL}/api/ai/explain/${node.data.id}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ node_label: node.data.label })
            })
            if (res.ok) {
                const data = await res.json()
                setExplanation(data)
                // Cập nhật giá trị trong node flow data để khỏi load lại nữa khi tắt đi bật lại panel
                node.data.explanation = data
            }
        } catch (error) {
            console.error(error)
        } finally {
            setIsGenerating(false)
        }
    }

    return (
        <div className="fixed top-0 right-0 w-[420px] h-full bg-[#111827] border-l border-[#1F2D45] shadow-[-8px_0px_32px_rgba(0,0,0,0.4)] z-50 flex flex-col animate-in slide-in-from-right duration-300">
            <header className="p-6 border-b border-[#1F2D45] flex items-start justify-between">
                <div className="flex-1 min-w-0 pr-6">
                    <p className="text-[10px] font-bold text-[#3B82F6] uppercase tracking-[0.2em] mb-1">{node.data.type}</p>
                    <h3 className="text-[#F1F5F9] font-bold text-2xl leading-tight truncate">{node.data.label}</h3>
                    <div className="flex gap-2 mt-2">
                        <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-[#10B981]/10 text-[#10B981] border border-[#10B981]/20 uppercase">
                            {node.data.importance}
                        </span>
                    </div>
                </div>
                <Button variant="ghost" size="icon" className="text-[#475569] hover:text-white hover:bg-[#1C2333]" onClick={onClose}>
                    <X className="w-5 h-5" />
                </Button>
            </header>

            <div className="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar pb-20">
                {/* AI Explanation Section */}
                <section className="space-y-4">
                    <h4 className="text-[10px] font-bold text-[#475569] uppercase tracking-widest flex items-center gap-2">
                        <Sparkles className="w-3.5 h-3.5 text-[#8B5CF6]" />
                        AI Explanation
                    </h4>

                    {!explanation ? (
                        <div className="p-5 bg-gradient-to-br from-[#1E3A5F] to-[#111827] rounded-2xl border border-[#3B82F6]/30 relative overflow-hidden group">
                            <div className="relative z-10">
                                <p className="text-sm text-[#F1F5F9] leading-relaxed mb-4">
                                    Need a better way to understand this? Let Gemini 2.0 generate a real-world analogy and practical applications.
                                </p>
                                <Button
                                    onClick={handleGenerateIntuition}
                                    disabled={isGenerating}
                                    className="w-full bg-[#3B82F6] hover:bg-[#2563EB] text-white font-bold h-11"
                                >
                                    {isGenerating ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <BrainCircuit className="w-4 h-4 mr-2" />}
                                    Generate Intuition
                                </Button>
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-6 animate-in fade-in duration-500">
                            <div className="bg-[#0A0E1A] p-4 rounded-xl border border-[#1F2D45]">
                                <p className="text-sm text-[#F1F5F9] leading-relaxed italic">
                                    "{explanation.intuition}"
                                </p>
                            </div>

                            <div className="grid gap-3">
                                {explanation.applications.map((app: string, i: number) => (
                                    <div key={i} className="flex items-center gap-3 p-3 bg-[#1C2333] rounded-lg border border-[#1F2D45]">
                                        <div className="w-6 h-6 rounded-full bg-[#3B82F6]/20 flex flex-shrink-0 items-center justify-center text-[#3B82F6] text-[10px] font-bold">
                                            {i + 1}
                                        </div>
                                        <span className="text-xs text-[#94A3B8]">{app}</span>
                                    </div>
                                ))}
                            </div>

                            {explanation.requirements && explanation.requirements.length > 0 && (
                                <div className="mt-6">
                                    <h5 className="text-[10px] font-bold text-[#10B981] uppercase tracking-widest mb-3">Yêu cầu cần đạt</h5>
                                    <div className="grid gap-2">
                                        {explanation.requirements.map((req: string, i: number) => (
                                            <div key={i} className="flex items-center gap-3 p-2.5 bg-[#10B981]/10 rounded-lg border border-[#10B981]/20">
                                                <div className="w-1.5 h-1.5 rounded-full bg-[#10B981] flex-shrink-0" />
                                                <span className="text-xs text-[#10B981]">{req}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </section>
            </div>
        </div>
    )
}
