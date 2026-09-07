import { useState } from "react"
import {
  Folder,
  FolderOpen,
  FileText,
  FileCode,
  FileImage,
  File,
  ChevronRight,
  ChevronDown,
} from "lucide-react"

// Map extension → icon + color
function getFileIcon(name) {
  const ext = name.split(".").pop().toLowerCase()
  const codeExts = ["js", "jsx", "ts", "tsx", "py", "java", "cpp", "c", "cs", "go", "rs", "php", "rb", "swift", "kt", "html", "css", "scss", "json", "xml", "yaml", "yml", "toml", "sh", "bat", "md"]
  const imgExts = ["png", "jpg", "jpeg", "gif", "svg", "webp", "ico", "bmp"]
  const textExts = ["txt", "log", "env", "csv", "sql"]

  if (codeExts.includes(ext)) return { icon: FileCode, color: "text-blue-400" }
  if (imgExts.includes(ext))  return { icon: FileImage, color: "text-yellow-400" }
  if (textExts.includes(ext)) return { icon: FileText, color: "text-gray-400" }
  return { icon: File, color: "text-gray-500" }
}

// A single tree node (recursive)
function TreeNode({ node, depth = 0, path = "", selectedPath, onSelectFile }) {
  const [open, setOpen] = useState(depth === 0)
  const currentPath = path ? `${path}/${node.name}` : node.name
  const isSelected = selectedPath === currentPath

  const indent = depth * 10

  if (node.kind === "directory") {
    return (
      <div>
        <button
          onClick={() => {
            setOpen((o) => !o)
            if (onSelectFile) onSelectFile(currentPath)
          }}
          className={`flex items-center gap-1.5 w-full text-left rounded px-1 py-[3px] transition-colors group ${
            isSelected ? "bg-white/15 text-white" : "hover:bg-white/8 text-[#ececec]"
          }`}
          style={{ paddingLeft: `${4 + indent}px` }}
        >
          {open ? (
            <ChevronDown size={11} className="text-[#8e8ea0] shrink-0" />
          ) : (
            <ChevronRight size={11} className="text-[#8e8ea0] shrink-0" />
          )}
          {open ? (
            <FolderOpen size={13} className="text-[#10a37f] shrink-0" />
          ) : (
            <Folder size={13} className="text-[#10a37f] shrink-0" />
          )}
          <span className="text-[11px] truncate font-medium">{node.name}</span>
        </button>
        {open && node.children && (
          <div>
            {node.children.map((child) => (
              <TreeNode
                key={child.name + child.kind}
                node={child}
                depth={depth + 1}
                path={currentPath}
                selectedPath={selectedPath}
                onSelectFile={onSelectFile}
              />
            ))}
          </div>
        )}
      </div>
    )
  }

  // File node
  const { icon: Icon, color } = getFileIcon(node.name)
  return (
    <button
      onClick={() => onSelectFile && onSelectFile(currentPath)}
      className={`flex items-center gap-1.5 w-full text-left rounded px-1 py-[3px] transition-colors ${
        isSelected ? "bg-white/15 text-white" : "hover:bg-white/8 text-[#b4b4c0]"
      }`}
      style={{ paddingLeft: `${18 + indent}px` }}
    >
      <Icon size={12} className={`${color} shrink-0`} />
      <span className="text-[11px] truncate">{node.name}</span>
    </button>
  )
}

export default function FileTree({ tree, selectedPath, onSelectFile }) {
  if (!tree) return null
  return (
    <div className="mt-2 overflow-y-auto">
      {tree.map((node) => (
        <TreeNode
          key={node.name + node.kind}
          node={node}
          depth={0}
          selectedPath={selectedPath}
          onSelectFile={onSelectFile}
        />
      ))}
    </div>
  )
}

