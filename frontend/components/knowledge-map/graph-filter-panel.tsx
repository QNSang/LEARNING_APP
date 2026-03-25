"use client"

import { useState } from "react"
import { Search, RotateCcw } from "lucide-react"
import { cn } from "@/lib/utils"

interface Node {
  id: string
  label: string
  type: "concept" | "procedure" | "fact"
  importance: "core" | "supporting" | "detail"
  week: number
}

interface GraphFilterPanelProps {
  nodes: Node[]
  selectedNode: string | null
  onSelectNode: (nodeId: string) => void
  onFilterChange: (filters: FilterState) => void
}

export interface FilterState {
  week: number | null
  types: ("concept" | "procedure" | "fact")[]
  importance: ("core" | "supporting" | "detail")[]
  search: string
}

const weeks = ["All", "W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"]

const nodeTypes = [
  { id: "concept" as const, label: "Concept", color: "#3B82F6" },
  { id: "procedure" as const, label: "Procedure", color: "#8B5CF6" },
  { id: "fact" as const, label: "Fact", color: "#10B981" },
]

const importanceLevels = [
  { id: "core" as const, label: "Core" },
  { id: "supporting" as const, label: "Supporting" },
  { id: "detail" as const, label: "Detail" },
]

export function GraphFilterPanel({ 
  nodes, 
  selectedNode, 
  onSelectNode,
  onFilterChange 
}: GraphFilterPanelProps) {
  const [filters, setFilters] = useState<FilterState>({
    week: null,
    types: ["concept", "procedure", "fact"],
    importance: ["core", "supporting", "detail"],
    search: ""
  })

  const updateFilters = (newFilters: Partial<FilterState>) => {
    const updated = { ...filters, ...newFilters }
    setFilters(updated)
    onFilterChange(updated)
  }

  const resetFilters = () => {
    const reset: FilterState = {
      week: null,
      types: ["concept", "procedure", "fact"],
      importance: ["core", "supporting", "detail"],
      search: ""
    }
    setFilters(reset)
    onFilterChange(reset)
  }

  const toggleType = (type: "concept" | "procedure" | "fact") => {
    const types = filters.types.includes(type)
      ? filters.types.filter(t => t !== type)
      : [...filters.types, type]
    updateFilters({ types })
  }

  const toggleImportance = (imp: "core" | "supporting" | "detail") => {
    const importance = filters.importance.includes(imp)
      ? filters.importance.filter(i => i !== imp)
      : [...filters.importance, imp]
    updateFilters({ importance })
  }

  const filteredNodes = nodes.filter(node => {
    if (filters.search && !node.label.toLowerCase().includes(filters.search.toLowerCase())) return false
    if (filters.week !== null && node.week !== filters.week) return false
    if (!filters.types.includes(node.type)) return false
    if (!filters.importance.includes(node.importance)) return false
    return true
  })

  return (
    <div className="w-[260px] h-full bg-[#111827] border-r border-[#1F2D45] flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-[#1F2D45]">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-[#F1F5F9]">Filter</h3>
          <button 
            onClick={resetFilters}
            className="text-xs text-[#3B82F6] hover:text-[#93C5FD] transition-colors"
          >
            Reset
          </button>
        </div>
        
        {/* Week Filter */}
        <div className="flex flex-wrap gap-1.5">
          {weeks.map((week, i) => {
            const weekNum = i === 0 ? null : i
            const isActive = filters.week === weekNum
            return (
              <button
                key={week}
                onClick={() => updateFilters({ week: weekNum })}
                className={cn(
                  "px-2.5 py-1 rounded-md text-xs font-medium transition-all",
                  isActive 
                    ? "bg-[#1E3A5F] border border-[#3B82F6] text-[#93C5FD]"
                    : "bg-[#1C2333] text-[#94A3B8] hover:text-[#F1F5F9]"
                )}
              >
                {week}
              </button>
            )
          })}
        </div>
      </div>
      
      {/* Node Type Filter */}
      <div className="p-4 border-b border-[#1F2D45]">
        <h4 className="text-xs text-[#475569] uppercase tracking-wider mb-3">Node Type</h4>
        <div className="space-y-2">
          {nodeTypes.map((type) => (
            <label key={type.id} className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                checked={filters.types.includes(type.id)}
                onChange={() => toggleType(type.id)}
                className="sr-only"
              />
              <div className={cn(
                "w-4 h-4 rounded border flex items-center justify-center transition-all",
                filters.types.includes(type.id)
                  ? "border-[#3B82F6] bg-[#3B82F6]"
                  : "border-[#475569]"
              )}>
                {filters.types.includes(type.id) && (
                  <svg className="w-2.5 h-2.5 text-white" fill="currentColor" viewBox="0 0 12 12">
                    <path d="M10.28 2.28L3.989 8.575 1.695 6.28A1 1 0 00.28 7.695l3 3a1 1 0 001.414 0l7-7A1 1 0 0010.28 2.28z" />
                  </svg>
                )}
              </div>
              <span 
                className="w-2 h-2 rounded-full" 
                style={{ backgroundColor: type.color }}
              />
              <span className="text-sm text-[#94A3B8] group-hover:text-[#F1F5F9] transition-colors">
                {type.label}
              </span>
            </label>
          ))}
        </div>
      </div>
      
      {/* Importance Filter */}
      <div className="p-4 border-b border-[#1F2D45]">
        <h4 className="text-xs text-[#475569] uppercase tracking-wider mb-3">Importance</h4>
        <div className="flex gap-1.5">
          {importanceLevels.map((level) => (
            <button
              key={level.id}
              onClick={() => toggleImportance(level.id)}
              className={cn(
                "flex-1 px-2 py-1.5 rounded-md text-xs font-medium transition-all",
                filters.importance.includes(level.id)
                  ? "bg-[#1E3A5F] border border-[#3B82F6] text-[#93C5FD]"
                  : "bg-[#1C2333] text-[#94A3B8] hover:text-[#F1F5F9]"
              )}
            >
              {level.label}
            </button>
          ))}
        </div>
      </div>
      
      {/* Node List */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="p-4 pb-2">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-xs text-[#475569] uppercase tracking-wider">
              Nodes ({filteredNodes.length})
            </h4>
          </div>
          
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#475569]" />
            <input
              type="text"
              value={filters.search}
              onChange={(e) => updateFilters({ search: e.target.value })}
              placeholder="Search concepts..."
              className="w-full pl-9 pr-3 py-2 bg-[#0A0E1A] border border-[#1F2D45] rounded-lg text-sm text-[#F1F5F9] placeholder-[#475569] focus:border-[#3B82F6] focus:outline-none transition-colors"
            />
          </div>
        </div>
        
        {/* Scrollable Node List */}
        <div className="flex-1 overflow-y-auto px-4 pb-4">
          <div className="space-y-1">
            {filteredNodes.map((node) => {
              const typeColor = nodeTypes.find(t => t.id === node.type)?.color || "#94A3B8"
              const isSelected = selectedNode === node.id
              return (
                <button
                  key={node.id}
                  onClick={() => onSelectNode(node.id)}
                  className={cn(
                    "w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left transition-all",
                    isSelected 
                      ? "bg-[#1C2333] border-l-[3px] border-[#3B82F6]"
                      : "hover:bg-[#1C2333]/50"
                  )}
                >
                  <span 
                    className="w-2 h-2 rounded-full flex-shrink-0" 
                    style={{ backgroundColor: typeColor }}
                  />
                  <span className={cn(
                    "text-sm truncate flex-1",
                    isSelected ? "text-[#F1F5F9]" : "text-[#94A3B8]"
                  )}>
                    {node.label}
                  </span>
                  <span className="text-[10px] text-[#475569] px-1.5 py-0.5 bg-[#1C2333] rounded">
                    W{node.week}
                  </span>
                </button>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
