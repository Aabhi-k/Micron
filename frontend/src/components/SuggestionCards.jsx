import { ExternalLink } from "lucide-react"

const suggestions = [
  {
    title: "Help me pick",
    description: "a birthday gift for my mom who likes gardening",
  },
  {
    title: "Suggest some codenames",
    description: "for a project introducing flexible work arrangements",
  },
  {
    title: "Suggest place",
    description: "Suggest the best Parks to visit in a city with descriptions",
  },
]

export default function SuggestionCards({ onSelectSuggestion }) {
  return (
    <div className="flex gap-4 px-10 pb-6">
      {suggestions.map((s, i) => (
        <button
          key={i}
          onClick={() => onSelectSuggestion && onSelectSuggestion(`${s.title} ${s.description}`)}
          className="flex-1 bg-white border border-gray-200 rounded-xl p-4 text-left hover:shadow-md transition-shadow duration-200 group relative min-h-[130px] flex flex-col"
        >
          <p className="font-semibold text-gray-800 text-sm mb-2">{s.title}</p>
          <p className="text-gray-500 text-xs leading-relaxed">{s.description}</p>
          <ExternalLink
            size={14}
            className="absolute bottom-3 right-3 text-gray-400 group-hover:text-gray-600 transition-colors"
          />
        </button>
      ))}
    </div>
  )
}

