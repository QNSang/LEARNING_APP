import { LucideIcon } from "lucide-react"

interface StatsCardProps {
  icon: LucideIcon
  value: string | number
  label: string
  iconColor?: string
}

export function StatsCard({ icon: Icon, value, label, iconColor = "#3B82F6" }: StatsCardProps) {
  return (
    <div className="bg-[#111827] border border-[#1F2D45] rounded-xl p-5">
      <div className="flex items-center gap-4">
        <div 
          className="w-11 h-11 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: `${iconColor}20` }}
        >
          <Icon className="w-5 h-5" style={{ color: iconColor }} />
        </div>
        <div>
          <p className="text-[#F1F5F9] text-2xl font-bold">{value}</p>
          <p className="text-[#94A3B8] text-sm">{label}</p>
        </div>
      </div>
    </div>
  )
}
