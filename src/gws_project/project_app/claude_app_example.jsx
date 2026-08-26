
//  FILE GENERATE BY CLAUDE APP TO WORK ON UI
import { useState, useRef, useEffect } from "react";

/* ===== PALETTE ===== */
const P = { 0: "#000000", 5: "#041210", 10: "#07241f", 15: "#0b362f", 20: "#0e483e", 30: "#166c5e", 40: "#1d907d", 50: "#25b49c", 60: "#50c3b0", 70: "#7cd2c4", 80: "#a7e1d7", 85: "#bde9e1", 90: "#d3f0eb", 95: "#e9f8f5", 100: "#ffffff" };
const A = { 0: "#291a67", 5: "#392a75", 10: "#483a82", 15: "#584a90", 20: "#675a9d", 30: "#877bb8", 40: "#a69bd3", 50: "#c5bbee", 60: "#d1c9f1", 70: "#dcd6f5", 80: "#e8e4f8", 85: "#eeebfa", 90: "#f3f1fc", 95: "#f9f8fd", 100: "#fff" };
const S = { 0: "#6a003c", 5: "#790f4b", 10: "#881d5a", 15: "#972c68", 20: "#a63b77", 30: "#c35895", 40: "#e176b2", 50: "#ff93d0", 60: "#ffa9d9", 70: "#ffbee3", 80: "#ffd4ec", 85: "#ffdff1", 90: "#ffe9f6", 95: "#fff4fa", 100: "#fff" };

/* ===== DATA ===== */
const projects = [
    { id: 1, title: "BIZ02–Marketing", dates: ["Nov 13, 2025", "Dec 31, 2029"], progress: 25, manager: { name: "Adama Ouattara", initials: "AO", color: "#6C63FF" }, created: "Nov 13, 2025", createdTime: "Nov 13, 2025 22:47", tasks: 4, completed: 1 },
    { id: 2, title: "CSS01–Customer Success", dates: ["Nov 13, 2025", "Dec 31, 2029"], progress: 0, manager: { name: "Adama Ouattara", initials: "AO", color: "#6C63FF" }, created: "Nov 13, 2025", createdTime: "Nov 13, 2025 14:30", tasks: 8, completed: 0 },
    { id: 3, title: "DEV01–Constellab-Innovation", dates: ["Nov 13, 2025", "Dec 31, 2029"], progress: 0, manager: { name: "Benjamin Maisonneuve", initials: "BM", color: "#FF6B6B" }, created: "Nov 13, 2025", createdTime: "Nov 13, 2025 10:15", tasks: 12, completed: 0 },
    { id: 4, title: "DEV02–Community-Innovation", dates: ["Nov 13, 2025", "Dec 31, 2029"], progress: 80, manager: { name: "Valentin Foex", initials: "VF", color: "#4ECDC4" }, created: "Nov 13, 2025", createdTime: "Nov 13, 2025 09:00", tasks: 10, completed: 8 },
    { id: 5, title: "DEV03–Constellab-Update", dates: ["Nov 13, 2025", "Dec 31, 2029"], progress: 0, manager: { name: "Benjamin Maisonneuve", initials: "BM", color: "#FF6B6B" }, created: "Nov 13, 2025", createdTime: "Nov 13, 2025 11:20", tasks: 5, completed: 0 },
    { id: 6, title: "ORD102–DataHub", dates: ["Nov 13, 2025", "Dec 31, 2029"], progress: 0, manager: { name: "Benjamin Maisonneuve", initials: "BM", color: "#FF6B6B" }, created: "Nov 13, 2025", createdTime: "Nov 13, 2025 15:45", tasks: 3, completed: 0 },
    { id: 7, title: "ORD207–Vibiosphen-PMO", dates: ["Dec 5, 2025", "Dec 31, 2030"], progress: 100, manager: { name: "Maëva Beugin", initials: "MB", color: "#FFB347" }, created: "Dec 5, 2025", createdTime: "Dec 5, 2025 08:30", tasks: 6, completed: 6 },
    { id: 8, title: "ORD208–Transcure", dates: ["Feb 3, 2025", "Dec 15, 2025"], progress: 0, manager: { name: "Maëva Beugin", initials: "MB", color: "#FFB347" }, created: "Nov 17, 2025", createdTime: "Nov 17, 2025 16:00", tasks: 2, completed: 0 },
    { id: 9, title: "ORD211–Algama-NationAlg", dates: ["Jun 1, 2025", "May 31, 2029"], progress: 78, manager: { name: "Maëva Beugin", initials: "MB", color: "#FFB347" }, created: "Nov 16, 2025", createdTime: "Nov 16, 2025 13:10", tasks: 9, completed: 7 },
    { id: 10, title: "ORD212–Meddenovo-Peptide", dates: ["Nov 1, 2025", "Jan 29, 2026"], progress: 0, manager: { name: "Nour Larifi", initials: "NL", color: "#A78BFA" }, created: "Nov 16, 2025", createdTime: "Nov 16, 2025 17:30", tasks: 4, completed: 0 },
];

const tasks = [
    { id: 1, title: "Videos", dates: ["Nov 17, 2025", "Nov 30, 2025"], status: "doing", priority: "medium", assignee: { name: "Adama Ouattara", initials: "AO", color: "#6C63FF" }, progress: 0, subtasks: 2, createdBy: { name: "Adama Ouattara", initials: "AO", color: "#6C63FF" }, createdAt: "Nov 17, 2025 10:30", lastModifiedBy: { name: "Adama Ouattara", initials: "AO", color: "#6C63FF" }, lastModifiedAt: "Dec 10, 2025 14:22", description: "", docs: [{ id: 1, name: "brief-video.pdf", type: "pdf" }, { id: 2, name: "script-v2.docx", type: "docx" }] },
    { id: 2, title: "Video Livre Blanc Chapitre 1", dates: ["Nov 17, 2025", "Nov 29, 2025"], status: "doing", priority: "medium", assignee: { name: "Adama Ouattara", initials: "AO", color: "#6C63FF" }, progress: 0, subtasks: 0, createdBy: { name: "Adama Ouattara", initials: "AO", color: "#6C63FF" }, createdAt: "Nov 17, 2025 11:00", lastModifiedBy: { name: "Nour Larifi", initials: "NL", color: "#A78BFA" }, lastModifiedAt: "Dec 15, 2025 09:45", description: "Réaliser la vidéo de présentation du **chapitre 1** du Livre Blanc.", docs: [] },
    { id: 3, title: "Vidéo", dates: ["Dec 22, 2025", "Dec 29, 2025"], status: "done", priority: "high", assignee: { name: "Nour Larifi", initials: "NL", color: "#A78BFA" }, progress: 100, subtasks: 3, createdBy: { name: "Benjamin Maisonneuve", initials: "BM", color: "#FF6B6B" }, createdAt: "Dec 20, 2025 16:45", lastModifiedBy: { name: "Nour Larifi", initials: "NL", color: "#A78BFA" }, lastModifiedAt: "Dec 29, 2025 18:00", description: "Production vidéo finale pour la campagne de lancement.", docs: [{ id: 3, name: "export-final.mp4", type: "mp4" }, { id: 4, name: "thumbnail.png", type: "png" }] },
    { id: 4, title: "Constellab Connect 2026", dates: ["Dec 26, 2025", "Jan 15, 2026"], status: "doing", priority: "medium", assignee: { name: "Adama Ouattara", initials: "AO", color: "#6C63FF" }, progress: 0, subtasks: 5, createdBy: { name: "Adama Ouattara", initials: "AO", color: "#6C63FF" }, createdAt: "Dec 26, 2025 09:00", lastModifiedBy: { name: "Maëva Beugin", initials: "MB", color: "#FFB347" }, lastModifiedAt: "Jan 5, 2026 11:30", description: "Organisation de l'événement **Constellab Connect 2026**.", docs: [{ id: 6, name: "planning-event.xlsx", type: "xlsx" }] },
];

const kanbanTasks = [
    { id: 101, title: "Write procedures", project: "QUA01–Quality", folder: "Procedures", priority: "medium", assignee: { name: "Maëva Beugin", initials: "MB", color: "#FFB347" }, status: "todo", dates: ["Jan 6", "Jan 17"] },
    { id: 102, title: "Error backend Community Prod", project: "DEV02–Community-Innovation", folder: null, priority: "high", assignee: { name: "Valentin Foex", initials: "VF", color: "#4ECDC4" }, status: "todo", dates: ["Jan 8", "Jan 10"] },
    { id: 103, title: "Developpement", project: "ORD226–Constellab Form", folder: null, priority: "medium", assignee: { name: "Benjamin Maisonneuve", initials: "BM", color: "#FF6B6B" }, status: "todo", dates: ["Jan 10", "Jan 24"] },
    { id: 104, title: "Deployment", project: "ORD225–Conidia-Search", folder: null, priority: "medium", assignee: { name: "Benjamin Maisonneuve", initials: "BM", color: "#FF6B6B" }, status: "todo", dates: ["Jan 13", "Jan 15"] },
    { id: 105, title: "Faire réunion pour valider document Process lab avec Benjamin", project: "ORD211–Algama-NationAlg", folder: "Relevé de besoins", priority: "medium", assignee: { name: "Maëva Beugin", initials: "MB", color: "#FFB347" }, status: "todo", dates: ["Jan 6", "Jan 10"] },
    { id: 106, title: "Faire document de réponse pour process lab", project: "ORD211–Algama-NationAlg", folder: "Relevé de besoins", priority: "medium", assignee: { name: "Maëva Beugin", initials: "MB", color: "#FFB347" }, status: "todo", dates: ["Jan 10", "Jan 17"] },
    { id: 107, title: "Review API documentation", project: "DEV03–Constellab-Update", folder: null, priority: "low", assignee: { name: "Nour Larifi", initials: "NL", color: "#A78BFA" }, status: "todo", dates: ["Jan 15", "Jan 20"] },
    { id: 108, title: "Setup CI/CD pipeline", project: "DEV01–Constellab-Innovation", folder: null, priority: "high", assignee: { name: "Benjamin Maisonneuve", initials: "BM", color: "#FF6B6B" }, status: "todo", dates: ["Jan 8", "Jan 12"] },
    { id: 201, title: "Define procedures", project: "QUA01–Quality", folder: "Procedures", priority: "medium", assignee: { name: "Adama Ouattara", initials: "AO", color: "#6C63FF" }, status: "inprogress", dates: ["Jan 3", "Jan 10"] },
    { id: 301, title: "Envoyer un message sur Constellab avec le lien de la note et de la vidéo", project: "ORD211–Algama-NationAlg", folder: "Envoi ELN + note à Algama", priority: "medium", assignee: { name: "Maëva Beugin", initials: "MB", color: "#FFB347" }, status: "done", dates: ["Dec 28", "Jan 3"] },
];

const projectDocuments = [
    { id: 1, name: "Cahier des charges Marketing Q1.pdf", type: "pdf", size: "2.4 MB", date: "Dec 15, 2025" },
    { id: 2, name: "Budget prévisionnel 2026.xlsx", type: "xlsx", size: "890 KB", date: "Dec 20, 2025" },
    { id: 3, name: "Maquettes Constellab Connect.fig", type: "fig", size: "14.2 MB", date: "Jan 3, 2026" },
    { id: 4, name: "Compte-rendu réunion kickoff.docx", type: "docx", size: "156 KB", date: "Nov 18, 2025" },
    { id: 5, name: "Charte graphique v2.pdf", type: "pdf", size: "5.8 MB", date: "Jan 10, 2026" },
];

const projectDescription = `## Objectifs du projet\n\nLe projet **BIZ02–Marketing** vise à structurer et déployer la stratégie marketing de Constellab pour la période 2025-2029.\n\n## Périmètre\n\n- Création de contenu vidéo\n- Rédaction du Livre Blanc\n- Organisation de l'événement **Constellab Connect 2026**\n- Refonte de la stratégie social media`;

const members = [
    { name: "Claudia Gossec", initials: "CG", color: "#34D399" },
    { name: "Benjamin Maisonneuve", initials: "BM", color: "#FF6B6B" },
    { name: "Adama Ouattara", initials: "AO", color: "#6C63FF" },
    { name: "Maëva Beugin", initials: "MB", color: "#FFB347" },
    { name: "Nour Larifi", initials: "NL", color: "#A78BFA" },
];

/* ===== COMPONENTS ===== */
const Avatar = ({ initials, color, size = 32 }) => (
    <div style={{ width: size, height: size, borderRadius: "50%", background: `linear-gradient(135deg, ${color}, ${color}dd)`, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: size * 0.38, fontWeight: 600, letterSpacing: "0.02em", flexShrink: 0 }}>{initials}</div>
);

const ProgressRing = ({ progress, size = 44 }) => {
    const r = (size - 6) / 2, circ = 2 * Math.PI * r, offset = circ - (progress / 100) * circ;
    const color = progress === 100 ? P[40] : progress >= 60 ? P[50] : progress > 0 ? A[20] : P[85];
    return (
        <div style={{ position: "relative", width: size, height: size }}>
            <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}><circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={P[95]} strokeWidth={4} /><circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={4} strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round" style={{ transition: "stroke-dashoffset 0.8s cubic-bezier(.4,0,.2,1)" }} /></svg>
            <span style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", fontSize: size <= 44 ? 11 : 14, fontWeight: 700, color: progress > 0 ? P[10] : P[70] }}>{progress}%</span>
        </div>
    );
};

const StatusBadge = ({ status }) => {
    const c = { doing: { label: "DOING", bg: S[95], color: S[10], dot: S[30] }, done: { label: "DONE", bg: P[95], color: P[30], dot: P[40] }, todo: { label: "TODO", bg: P[90], color: P[30], dot: P[70] } }[status] || { label: "TODO", bg: P[90], color: P[30], dot: P[70] };
    return <span style={{ display: "inline-flex", alignItems: "center", gap: 6, padding: "4px 10px", borderRadius: 99, background: c.bg, color: c.color, fontSize: 12, fontWeight: 600 }}><span style={{ width: 6, height: 6, borderRadius: "50%", background: c.dot }} />{c.label}</span>;
};

const PriorityBadge = ({ priority, compact }) => {
    const c = { high: { label: "HIGH", bg: S[90], color: S[5], icon: "▲" }, medium: { label: "MEDIUM", bg: A[90], color: A[5], icon: "◆" }, low: { label: "LOW", bg: P[90], color: P[20], icon: "▼" } }[priority] || { label: "MEDIUM", bg: A[90], color: A[5], icon: "◆" };
    return <span style={{ display: "inline-flex", alignItems: "center", gap: compact ? 3 : 5, padding: compact ? "3px 8px" : "4px 10px", borderRadius: 99, background: c.bg, color: c.color, fontSize: compact ? 10 : 12, fontWeight: 600 }}><span style={{ fontSize: compact ? 6 : 8 }}>{c.icon}</span>{c.label}</span>;
};

const ProgressBar = ({ progress, height = 6 }) => {
    const color = progress === 100 ? P[40] : progress >= 60 ? P[50] : progress > 0 ? A[20] : "transparent";
    return <div style={{ width: "100%", height, borderRadius: 99, background: P[95], overflow: "hidden" }}><div style={{ width: `${Math.max(progress, 0)}%`, height: "100%", borderRadius: 99, background: `linear-gradient(90deg, ${color}, ${color}cc)`, transition: "width 0.8s cubic-bezier(.4,0,.2,1)" }} /></div>;
};

const ThreeDotIcon = ({ size = 18 }) => <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="5" r="2" /><circle cx="12" cy="12" r="2" /><circle cx="12" cy="19" r="2" /></svg>;

const DropdownMenu = ({ items, open, onClose }) => {
    const ref = useRef(null);
    useEffect(() => { if (!open) return; const h = (e) => { if (ref.current && !ref.current.contains(e.target)) onClose(); }; document.addEventListener("mousedown", h); return () => document.removeEventListener("mousedown", h); }, [open, onClose]);
    if (!open) return null;
    return (
        <div ref={ref} style={{ position: "absolute", right: 0, top: "100%", marginTop: 4, background: "#fff", border: `1px solid ${P[90]}`, borderRadius: 10, padding: "4px 0", minWidth: 180, zIndex: 100 }}>
            {items.map((item, i) => item.divider ? <div key={i} style={{ height: 1, background: P[95], margin: "4px 0" }} /> : (
                <button key={i} onClick={(e) => { e.stopPropagation(); item.onClick?.(); onClose(); }} style={{ display: "flex", alignItems: "center", gap: 10, width: "100%", padding: "8px 14px", border: "none", background: "transparent", cursor: "pointer", fontSize: 13, fontWeight: 500, color: item.danger ? S[0] : P[10] }}
                    onMouseEnter={e => e.currentTarget.style.background = item.danger ? S[95] : P[95]} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                    <span style={{ width: 18, textAlign: "center", fontSize: 14 }}>{item.icon}</span>{item.label}
                </button>
            ))}
        </div>
    );
};

const MenuButton = ({ id, openId, setOpenId, items }) => (
    <div style={{ position: "relative" }}>
        <button onClick={(e) => { e.stopPropagation(); setOpenId(openId === id ? null : id); }} style={{ display: "flex", alignItems: "center", justifyContent: "center", width: 32, height: 32, borderRadius: 8, border: openId === id ? `1px solid ${P[90]}` : "1px solid transparent", background: openId === id ? P[95] : "transparent", cursor: "pointer", color: P[60] }}
            onMouseEnter={e => { if (openId !== id) e.currentTarget.style.borderColor = P[90]; }} onMouseLeave={e => { if (openId !== id) e.currentTarget.style.borderColor = "transparent"; }}>
            <ThreeDotIcon size={16} />
        </button>
        <DropdownMenu items={items} open={openId === id} onClose={() => setOpenId(null)} />
    </div>
);

const DocTypeIcon = ({ type }) => {
    const c = { pdf: { bg: S[90], color: S[10], label: "PDF" }, xlsx: { bg: P[90], color: P[30], label: "XLS" }, docx: { bg: A[90], color: A[10], label: "DOC" }, fig: { bg: A[85], color: A[0], label: "FIG" }, mp4: { bg: S[85], color: S[5], label: "MP4" }, png: { bg: P[85], color: P[20], label: "PNG" }, srt: { bg: A[95], color: A[15], label: "SRT" } }[type] || { bg: P[90], color: P[30], label: type?.toUpperCase()?.slice(0, 3) || "FILE" };
    return <div style={{ width: 36, height: 36, borderRadius: 8, background: c.bg, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9, fontWeight: 800, color: c.color, letterSpacing: "0.02em", flexShrink: 0 }}>{c.label}</div>;
};

const MarkdownContent = ({ content }) => {
    if (!content) return <p style={{ fontSize: 14, color: P[60], fontStyle: "italic" }}>Écrivez quelque chose, utilisez la touche / pour les commandes…</p>;
    return <div>{content.split("\n").map((line, i) => {
        if (line.startsWith("## ")) return <h2 key={i} style={{ fontSize: 18, fontWeight: 750, margin: "28px 0 12px", color: P[10] }}>{line.slice(3)}</h2>;
        if (line.startsWith("- ")) return <div key={i} style={{ display: "flex", gap: 10, padding: "4px 0" }}><span style={{ color: P[40], fontSize: 8, marginTop: 6 }}>●</span><span style={{ fontSize: 14, color: P[20], lineHeight: 1.7 }}>{line.slice(2)}</span></div>;
        if (line.trim() === "") return <div key={i} style={{ height: 8 }} />;
        const rendered = line.replace(/\*\*(.*?)\*\*/g, (_, b) => `<strong style="color:${P[10]}">${b}</strong>`);
        return <p key={i} style={{ fontSize: 14, color: P[20], lineHeight: 1.8, margin: "4px 0" }} dangerouslySetInnerHTML={{ __html: rendered }} />;
    })}</div>;
};

const DetailRow = ({ label, children }) => (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", minHeight: 32 }}>
        <span style={{ fontSize: 12, color: P[60], fontWeight: 500 }}>{label}</span>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>{children}</div>
    </div>
);

/* ===== KANBAN CARD ===== */
const KanbanCard = ({ task, onHover, hovered }) => (
    <div
        onMouseEnter={() => onHover(task.id)} onMouseLeave={() => onHover(null)}
        style={{
            background: "#fff", borderRadius: 12, padding: "16px 18px",
            border: `1px solid ${hovered ? P[85] : P[90]}`,
            cursor: "pointer", transition: "all 0.15s ease",
            transform: hovered ? "translateY(-1px)" : "none",
        }}>
        {/* Title + priority */}
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 10, marginBottom: 12 }}>
            <div style={{ fontWeight: 650, fontSize: 14, color: P[10], lineHeight: 1.4 }}>{task.title}</div>
            <PriorityBadge priority={task.priority} compact />
        </div>
        {/* Project tag */}
        <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
            <div style={{ width: 7, height: 7, borderRadius: "50%", background: S[30], flexShrink: 0 }} />
            <span style={{ fontSize: 12, color: P[30], fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{task.project}</span>
        </div>
        {/* Folder if present */}
        {task.folder && (
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
                <span style={{ fontSize: 12 }}>📁</span>
                <span style={{ fontSize: 12, color: P[60] }}>{task.folder}</span>
            </div>
        )}
        {/* Footer: dates + assignee */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 12, paddingTop: 10, borderTop: `1px solid ${P[95]}` }}>
            <span style={{ fontSize: 11, color: P[60], fontWeight: 500 }}>{task.dates[0]} → {task.dates[1]}</span>
            <Avatar initials={task.assignee.initials} color={task.assignee.color} size={26} />
        </div>
    </div>
);

/* ===== MAIN APP ===== */
export default function ConstellabRedesign() {
    const [view, setView] = useState("projects");
    const [selectedProject, setSelectedProject] = useState(null);
    const [selectedTask, setSelectedTask] = useState(null);
    const [activeNav, setActiveNav] = useState("projects");
    const [hoveredRow, setHoveredRow] = useState(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [detailOpen, setDetailOpen] = useState(true);
    const [projectTab, setProjectTab] = useState("tasks");
    const [openMenuId, setOpenMenuId] = useState(null);
    const [openDocMenuId, setOpenDocMenuId] = useState(null);
    const [openTaskMenuId, setOpenTaskMenuId] = useState(null);
    const [openTaskDocMenuId, setOpenTaskDocMenuId] = useState(null);
    const [taskMenuOpen, setTaskMenuOpen] = useState(false);
    // Kanban states
    const [kanbanSearch, setKanbanSearch] = useState("");
    const [kanbanProject, setKanbanProject] = useState("all");
    const [kanbanUser, setKanbanUser] = useState("all");
    const [hoveredCard, setHoveredCard] = useState(null);

    const openProject = (p) => { setSelectedProject(p); setView("projectDetail"); setProjectTab("tasks"); setDetailOpen(true); };
    const openTask = (t) => { setSelectedTask(t); setView("taskDetail"); setDetailOpen(true); };
    const goToProjects = () => { setView("projects"); setSelectedProject(null); setSelectedTask(null); };
    const goToProject = () => { setView("projectDetail"); setSelectedTask(null); };
    const navTo = (key) => { setActiveNav(key); if (key === "projects") goToProjects(); if (key === "kanban") setView("kanban"); };

    const filteredProjects = projects.filter(p => p.title.toLowerCase().includes(searchQuery.toLowerCase()));

    const filteredKanban = kanbanTasks.filter(t => {
        if (kanbanSearch && !t.title.toLowerCase().includes(kanbanSearch.toLowerCase())) return false;
        if (kanbanProject !== "all" && !t.project.includes(kanbanProject)) return false;
        if (kanbanUser !== "all" && t.assignee.name !== kanbanUser) return false;
        return true;
    });

    const kanbanColumns = [
        { key: "todo", label: "To Do", color: A[20], bg: A[95], tasks: filteredKanban.filter(t => t.status === "todo") },
        { key: "inprogress", label: "In Progress", color: S[20], bg: S[95], tasks: filteredKanban.filter(t => t.status === "inprogress") },
        { key: "done", label: "Done", color: P[30], bg: P[95], tasks: filteredKanban.filter(t => t.status === "done") },
    ];

    const projectMenuItems = [{ icon: "✏️", label: "Modifier", onClick: () => { } }, { icon: "📋", label: "Dupliquer", onClick: () => { } }, { icon: "📤", label: "Exporter", onClick: () => { } }, { divider: true }, { icon: "🗑️", label: "Supprimer", onClick: () => { }, danger: true }];
    const taskMenuItems = [{ icon: "✏️", label: "Modifier", onClick: () => { } }, { icon: "📋", label: "Dupliquer", onClick: () => { } }, { icon: "👤", label: "Réassigner", onClick: () => { } }, { divider: true }, { icon: "🗑️", label: "Supprimer", onClick: () => { }, danger: true }];
    const docMenuItems = [{ icon: "📥", label: "Télécharger", onClick: () => { } }, { icon: "✏️", label: "Renommer", onClick: () => { } }, { icon: "📋", label: "Copier le lien", onClick: () => { } }, { divider: true }, { icon: "🗑️", label: "Supprimer", onClick: () => { }, danger: true }];
    const tabConfig = [{ key: "tasks", label: "Tâches", count: tasks.length }, { key: "description", label: "Description" }, { key: "documents", label: "Documents", count: projectDocuments.length }];

    const uniqueKanbanProjects = [...new Set(kanbanTasks.map(t => t.project))];
    const uniqueKanbanUsers = [...new Set(kanbanTasks.map(t => t.assignee.name))];

    return (
        <div style={{ display: "flex", height: "100vh", fontFamily: "'DM Sans','Segoe UI',sans-serif", background: P[95], color: P[10], overflow: "hidden" }}>
            {/* ===== SIDEBAR ===== */}
            <aside style={{ width: 240, background: "#fff", borderRight: `1px solid ${P[90]}`, display: "flex", flexDirection: "column", flexShrink: 0 }}>
                <div style={{ padding: "24px 20px 20px", display: "flex", alignItems: "center", gap: 12 }}>
                    <div style={{ width: 36, height: 36, borderRadius: 10, background: `linear-gradient(135deg, ${P[40]}, ${P[50]})`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3" fill="#fff" /><circle cx="12" cy="4" r="2" fill="#fff" opacity="0.7" /><circle cx="12" cy="20" r="2" fill="#fff" opacity="0.7" /><circle cx="4" cy="12" r="2" fill="#fff" opacity="0.7" /><circle cx="20" cy="12" r="2" fill="#fff" opacity="0.7" /></svg>
                    </div>
                    <div><div style={{ fontWeight: 700, fontSize: 15, letterSpacing: "-0.02em", color: P[10] }}>Constellab</div><div style={{ fontSize: 11, color: P[60], fontWeight: 500 }}>Project Manager</div></div>
                </div>
                <nav style={{ padding: "8px 12px", flex: 1 }}>
                    {[{ key: "projects", label: "Projets", icon: "M3 7h4v10H3zm7-4h4v14h-4zm7 7h4v7h-4z" }, { key: "kanban", label: "Kanban", icon: "M4 4h5v16H4zM10 4h5v12h-5zM16 4h5v8h-5z" }, { key: "gantt", label: "Gantt", icon: "M3 6h10M3 12h14M3 18h8" }, { key: "templates", label: "Templates", icon: "M4 4h16v4H4zM4 10h7v10H4zM13 10h7v10h-7z" }].map(item => {
                        const isActive = activeNav === item.key;
                        return <button key={item.key} onClick={() => navTo(item.key)} style={{ display: "flex", alignItems: "center", gap: 12, width: "100%", padding: "10px 14px", borderRadius: 10, border: "none", cursor: "pointer", background: isActive ? P[95] : "transparent", color: isActive ? P[30] : P[60], fontWeight: isActive ? 650 : 500, fontSize: 14, transition: "all 0.2s ease", marginBottom: 2 }}>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d={item.icon} /></svg>{item.label}
                            {isActive && <div style={{ marginLeft: "auto", width: 6, height: 6, borderRadius: "50%", background: P[40] }} />}
                        </button>;
                    })}
                </nav>
                <div style={{ padding: "16px 20px", borderTop: `1px solid ${P[95]}`, display: "flex", alignItems: "center", gap: 10 }}>
                    <Avatar initials="AO" color="#6C63FF" size={34} /><div><div style={{ fontSize: 13, fontWeight: 600, color: P[10] }}>Adama Ouattara</div><div style={{ fontSize: 11, color: P[60] }}>Admin</div></div>
                </div>
            </aside>

            {/* ===== MAIN ===== */}
            <main style={{ flex: 1, overflow: "auto", display: "flex", flexDirection: "column" }}>

                {/* ==================== KANBAN ==================== */}
                {view === "kanban" && (
                    <div style={{ padding: "32px 40px", display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
                        {/* Header */}
                        <div style={{ marginBottom: 24, flexShrink: 0 }}>
                            <h1 style={{ fontSize: 26, fontWeight: 800, letterSpacing: "-0.03em", margin: 0, color: P[5] }}>Task Board</h1>
                            <p style={{ color: P[60], fontSize: 14, margin: "4px 0 0", fontWeight: 500 }}>{kanbanTasks.length} tâches au total</p>
                        </div>

                        {/* Filters */}
                        <div style={{ display: "flex", gap: 12, marginBottom: 24, alignItems: "center", flexShrink: 0, flexWrap: "wrap" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 8, background: "#fff", borderRadius: 10, padding: "8px 14px", border: `1px solid ${P[90]}`, flex: "0 1 220px" }}>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={P[70]} strokeWidth="2"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
                                <input value={kanbanSearch} onChange={e => setKanbanSearch(e.target.value)} placeholder="Title" style={{ border: "none", outline: "none", flex: 1, fontSize: 13, background: "transparent", color: P[10] }} />
                            </div>
                            <select value={kanbanProject} onChange={e => setKanbanProject(e.target.value)} style={{ padding: "8px 14px", borderRadius: 10, border: `1px solid ${P[90]}`, fontSize: 13, color: P[30], background: "#fff", cursor: "pointer" }}>
                                <option value="all">All Projects</option>
                                {uniqueKanbanProjects.map(p => <option key={p} value={p}>{p}</option>)}
                            </select>
                            <select value={kanbanUser} onChange={e => setKanbanUser(e.target.value)} style={{ padding: "8px 14px", borderRadius: 10, border: `1px solid ${P[90]}`, fontSize: 13, color: P[30], background: "#fff", cursor: "pointer" }}>
                                <option value="all">All Users</option>
                                {uniqueKanbanUsers.map(u => <option key={u} value={u}>{u}</option>)}
                            </select>
                            <button onClick={() => { setKanbanSearch(""); setKanbanProject("all"); setKanbanUser("all"); }} style={{ padding: "8px 16px", borderRadius: 10, border: `1px solid ${P[90]}`, fontSize: 13, fontWeight: 600, color: P[30], background: "#fff", cursor: "pointer" }}>Clear</button>
                        </div>

                        {/* Columns */}
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20, flex: 1, overflow: "hidden" }}>
                            {kanbanColumns.map(col => (
                                <div key={col.key} style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
                                    {/* Column header */}
                                    <div style={{
                                        borderTop: `3px solid ${col.color}`, borderRadius: "12px 12px 0 0",
                                        background: col.bg, padding: "14px 18px",
                                        display: "flex", alignItems: "center", justifyContent: "space-between",
                                    }}>
                                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                                            <span style={{ fontWeight: 750, fontSize: 15, color: P[10] }}>{col.label}</span>
                                            <span style={{
                                                fontSize: 12, fontWeight: 700, padding: "2px 8px", borderRadius: 99,
                                                background: col.color + "22", color: col.color,
                                            }}>{col.tasks.length}</span>
                                        </div>
                                    </div>

                                    {/* Cards container */}
                                    <div style={{
                                        flex: 1, overflow: "auto",
                                        background: col.bg + "88",
                                        borderRadius: "0 0 12px 12px",
                                        border: `1px solid ${P[90]}`, borderTop: "none",
                                        padding: "12px",
                                        display: "flex", flexDirection: "column", gap: 10,
                                    }}>
                                        {col.tasks.length === 0 && (
                                            <div style={{ padding: "40px 20px", textAlign: "center" }}>
                                                <div style={{ fontSize: 28, marginBottom: 8, opacity: 0.5 }}>📋</div>
                                                <p style={{ fontSize: 13, color: P[70] }}>Aucune tâche</p>
                                            </div>
                                        )}
                                        {col.tasks.map(task => (
                                            <KanbanCard key={task.id} task={task} hovered={hoveredCard === task.id} onHover={setHoveredCard} />
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* ==================== PROJECTS LIST ==================== */}
                {view === "projects" && (
                    <div style={{ padding: "32px 40px", maxWidth: 1200 }}>
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 28 }}>
                            <div><h1 style={{ fontSize: 26, fontWeight: 800, letterSpacing: "-0.03em", margin: 0, color: P[5] }}>Mes projets</h1><p style={{ color: P[60], fontSize: 14, margin: "4px 0 0", fontWeight: 500 }}>{projects.length} projets · {projects.filter(p => p.progress === 100).length} terminés</p></div>
                            <button style={{ display: "flex", alignItems: "center", gap: 8, padding: "10px 20px", borderRadius: 12, border: "none", background: `linear-gradient(135deg, ${P[40]}, ${P[30]})`, color: "#fff", fontWeight: 650, fontSize: 14, cursor: "pointer" }}><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>Nouveau projet</button>
                        </div>
                        <div style={{ display: "flex", gap: 12, marginBottom: 24, alignItems: "center" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 8, background: "#fff", borderRadius: 10, padding: "8px 14px", border: `1px solid ${P[90]}`, flex: "0 1 300px" }}>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={P[70]} strokeWidth="2"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
                                <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)} placeholder="Rechercher un projet…" style={{ border: "none", outline: "none", flex: 1, fontSize: 13, background: "transparent", color: P[10] }} />
                            </div>
                            <select style={{ padding: "8px 14px", borderRadius: 10, border: `1px solid ${P[90]}`, fontSize: 13, color: P[30], background: "#fff", cursor: "pointer" }}><option>Tous les managers</option></select>
                            <button onClick={() => setSearchQuery("")} style={{ padding: "8px 16px", borderRadius: 10, border: `1px solid ${P[90]}`, fontSize: 13, fontWeight: 600, color: P[30], background: "#fff", cursor: "pointer" }}>Clear</button>
                        </div>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 28 }}>
                            {[{ label: "Total projets", value: projects.length, icon: "📊", accent: A[10], bg: A[95] }, { label: "En cours", value: projects.filter(p => p.progress > 0 && p.progress < 100).length, icon: "🚀", accent: S[10], bg: S[95] }, { label: "Terminés", value: projects.filter(p => p.progress === 100).length, icon: "✅", accent: P[30], bg: P[95] }, { label: "Non démarrés", value: projects.filter(p => p.progress === 0).length, icon: "⏳", accent: P[60], bg: P[95] }].map((s, i) => (
                                <div key={i} style={{ background: "#fff", borderRadius: 14, padding: "18px 20px", border: `1px solid ${P[90]}`, display: "flex", alignItems: "center", gap: 14 }}>
                                    <div style={{ width: 42, height: 42, borderRadius: 12, background: s.bg, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20 }}>{s.icon}</div>
                                    <div><div style={{ fontSize: 22, fontWeight: 800, letterSpacing: "-0.02em", color: s.accent }}>{s.value}</div><div style={{ fontSize: 12, color: P[60], fontWeight: 500 }}>{s.label}</div></div>
                                </div>
                            ))}
                        </div>
                        <div style={{ background: "#fff", borderRadius: 16, border: `1px solid ${P[90]}`, overflow: "hidden" }}>
                            <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 120px 1fr 80px 48px", gap: 12, padding: "14px 24px", background: P[95], borderBottom: `1px solid ${P[90]}`, fontSize: 11, fontWeight: 700, color: P[60], textTransform: "uppercase", letterSpacing: "0.06em" }}><span>Projet</span><span>Période</span><span>Progression</span><span>Manager</span><span style={{ textAlign: "right" }}>Tâches</span><span /></div>
                            {filteredProjects.map((p, i) => (
                                <div key={p.id} onMouseEnter={() => setHoveredRow(p.id)} onMouseLeave={() => setHoveredRow(null)} style={{ display: "grid", gridTemplateColumns: "2fr 1fr 120px 1fr 80px 48px", gap: 12, padding: "16px 24px", alignItems: "center", background: hoveredRow === p.id ? P[95] : "transparent", borderBottom: i < filteredProjects.length - 1 ? `1px solid ${P[95]}` : "none", transition: "background 0.15s ease" }}>
                                    <div onClick={() => openProject(p)} style={{ display: "flex", alignItems: "center", gap: 12, cursor: "pointer" }}><div style={{ width: 8, height: 8, borderRadius: "50%", flexShrink: 0, background: p.progress === 100 ? P[40] : p.progress > 0 ? S[30] : P[85] }} /><div style={{ fontWeight: 650, fontSize: 14, color: P[10] }}>{p.title}</div></div>
                                    <div onClick={() => openProject(p)} style={{ fontSize: 12, color: P[60], cursor: "pointer" }}><div>{p.dates[0]}</div><div style={{ color: P[80] }}>→ {p.dates[1]}</div></div>
                                    <ProgressRing progress={p.progress} size={42} />
                                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}><Avatar initials={p.manager.initials} color={p.manager.color} size={30} /><span style={{ fontSize: 13, fontWeight: 500, color: P[15] }}>{p.manager.name}</span></div>
                                    <div style={{ textAlign: "right" }}><span style={{ fontSize: 13, fontWeight: 700, color: P[10] }}>{p.completed}</span><span style={{ fontSize: 13, color: P[80] }}> / {p.tasks}</span></div>
                                    <MenuButton id={p.id} openId={openMenuId} setOpenId={setOpenMenuId} items={projectMenuItems} />
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* ==================== PROJECT DETAIL ==================== */}
                {view === "projectDetail" && (
                    <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
                        <div style={{ flex: 1, padding: "32px 40px", overflow: "auto" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8, fontSize: 13, color: P[60] }}><span onClick={goToProjects} style={{ cursor: "pointer", color: P[40], fontWeight: 600 }}>Projets</span><span>›</span><span style={{ color: P[30] }}>{selectedProject?.title}</span></div>
                            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
                                <div style={{ display: "flex", alignItems: "center", gap: 14 }}><h1 style={{ fontSize: 24, fontWeight: 800, letterSpacing: "-0.03em", margin: 0, color: P[5] }}>{selectedProject?.title}</h1><span style={{ padding: "4px 12px", borderRadius: 99, fontSize: 12, fontWeight: 700, background: selectedProject?.progress === 100 ? P[95] : S[95], color: selectedProject?.progress === 100 ? P[30] : S[10] }}>{selectedProject?.progress === 100 ? "Terminé" : "En cours"}</span></div>
                                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                                    {projectTab === "tasks" && <button style={{ display: "flex", alignItems: "center", gap: 8, padding: "10px 20px", borderRadius: 12, border: "none", background: `linear-gradient(135deg, ${P[40]}, ${P[30]})`, color: "#fff", fontWeight: 650, fontSize: 14, cursor: "pointer" }}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>Nouvelle tâche</button>}
                                    {projectTab === "documents" && <button style={{ display: "flex", alignItems: "center", gap: 8, padding: "10px 20px", borderRadius: 12, border: "none", background: `linear-gradient(135deg, ${P[40]}, ${P[30]})`, color: "#fff", fontWeight: 650, fontSize: 14, cursor: "pointer" }}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>Ajouter un document</button>}
                                    {!detailOpen && <button onClick={() => setDetailOpen(true)} style={{ display: "flex", alignItems: "center", justifyContent: "center", width: 38, height: 38, borderRadius: 10, border: `1px solid ${P[90]}`, background: "#fff", cursor: "pointer", color: P[30] }}><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" /></svg></button>}
                                </div>
                            </div>
                            <div style={{ display: "flex", borderBottom: `2px solid ${P[90]}`, marginBottom: 24 }}>{tabConfig.map(tab => { const isActive = projectTab === tab.key; return <button key={tab.key} onClick={() => setProjectTab(tab.key)} style={{ padding: "10px 20px", border: "none", cursor: "pointer", background: "transparent", fontSize: 14, fontWeight: isActive ? 700 : 500, color: isActive ? P[30] : P[60], borderBottom: isActive ? `2px solid ${P[40]}` : "2px solid transparent", marginBottom: -2, display: "flex", alignItems: "center", gap: 8 }}>{tab.label}{tab.count != null && <span style={{ fontSize: 11, fontWeight: 700, padding: "2px 7px", borderRadius: 99, background: isActive ? P[95] : P[90], color: isActive ? P[30] : P[60] }}>{tab.count}</span>}</button>; })}</div>
                            {projectTab === "tasks" && <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>{tasks.map(t => <div key={t.id} onClick={() => openTask(t)} style={{ background: "#fff", borderRadius: 14, padding: "18px 22px", border: `1px solid ${P[90]}`, cursor: "pointer" }}><div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}><div style={{ display: "flex", alignItems: "center", gap: 12 }}><div style={{ width: 32, height: 32, borderRadius: 8, background: t.status === "done" ? P[95] : A[95], display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14 }}>{t.subtasks > 0 ? "📁" : "📄"}</div><div><div style={{ fontWeight: 650, fontSize: 14, textDecoration: t.status === "done" ? "line-through" : "none", color: t.status === "done" ? P[70] : P[10] }}>{t.title}</div><div style={{ fontSize: 12, color: P[70], marginTop: 2 }}>{t.dates[0]} → {t.dates[1]}{t.subtasks > 0 && <span style={{ marginLeft: 10, color: P[60] }}>· {t.subtasks} sous-tâches</span>}</div></div></div><div style={{ display: "flex", alignItems: "center", gap: 10 }}><PriorityBadge priority={t.priority} /><StatusBadge status={t.status} /><Avatar initials={t.assignee.initials} color={t.assignee.color} size={30} /><MenuButton id={t.id} openId={openTaskMenuId} setOpenId={setOpenTaskMenuId} items={taskMenuItems} /></div></div><ProgressBar progress={t.progress} /></div>)}</div>}
                            {projectTab === "description" && <div style={{ background: "#fff", borderRadius: 14, padding: "32px 36px", border: `1px solid ${P[90]}`, maxWidth: 780 }}><MarkdownContent content={projectDescription} /></div>}
                            {projectTab === "documents" && <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>{projectDocuments.map(doc => <div key={doc.id} style={{ background: "#fff", borderRadius: 12, padding: "14px 20px", border: `1px solid ${P[90]}`, display: "flex", alignItems: "center", gap: 16 }}><DocTypeIcon type={doc.type} /><div style={{ flex: 1, minWidth: 0 }}><div style={{ fontWeight: 620, fontSize: 14, color: P[10], whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{doc.name}</div><div style={{ fontSize: 12, color: P[60], marginTop: 2 }}>{doc.size} · {doc.date}</div></div><button style={{ display: "flex", alignItems: "center", gap: 6, padding: "7px 14px", borderRadius: 8, border: `1px solid ${P[90]}`, background: "#fff", cursor: "pointer", fontSize: 13, fontWeight: 600, color: P[40] }} onMouseEnter={e => e.currentTarget.style.background = P[95]} onMouseLeave={e => e.currentTarget.style.background = "#fff"}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" /><polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" /></svg>Ouvrir</button><MenuButton id={doc.id} openId={openDocMenuId} setOpenId={setOpenDocMenuId} items={docMenuItems} /></div>)}</div>}
                        </div>
                        {detailOpen && <aside style={{ width: 320, background: "#fff", borderLeft: `1px solid ${P[90]}`, padding: "32px 24px", overflow: "auto", flexShrink: 0 }}>
                            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}><h3 style={{ fontSize: 12, fontWeight: 700, color: P[60], textTransform: "uppercase", letterSpacing: "0.08em", margin: 0 }}>Détails du projet</h3><button onClick={() => setDetailOpen(false)} style={{ display: "flex", alignItems: "center", justifyContent: "center", width: 28, height: 28, borderRadius: 8, border: `1px solid ${P[90]}`, background: "transparent", cursor: "pointer", color: P[60] }}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg></button></div>
                            <div style={{ display: "flex", justifyContent: "center", marginBottom: 24 }}><ProgressRing progress={selectedProject?.progress || 0} size={80} /></div>
                            <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
                                <div><div style={{ fontSize: 11, fontWeight: 700, color: P[60], textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>Manager</div><div style={{ display: "flex", alignItems: "center", gap: 10 }}><Avatar initials={selectedProject?.manager.initials} color={selectedProject?.manager.color} size={34} /><span style={{ fontWeight: 600, fontSize: 14, color: P[10] }}>{selectedProject?.manager.name}</span></div></div>
                                <div><div style={{ fontSize: 11, fontWeight: 700, color: P[60], textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>Période</div><div style={{ background: P[95], borderRadius: 10, padding: "12px 14px", display: "flex", alignItems: "center", gap: 10, fontSize: 13, color: P[30], fontWeight: 500 }}><span>{selectedProject?.dates[0]}</span><span style={{ color: P[80] }}>→</span><span>{selectedProject?.dates[1]}</span></div></div>
                                <div><div style={{ fontSize: 11, fontWeight: 700, color: P[60], textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 10 }}>Membres</div><div style={{ display: "flex", flexDirection: "column", gap: 8 }}>{members.map((m, i) => <div key={i} style={{ display: "flex", alignItems: "center", gap: 10 }}><Avatar initials={m.initials} color={m.color} size={28} /><span style={{ fontSize: 13, fontWeight: 500, color: P[15] }}>{m.name}</span></div>)}</div></div>
                                <div style={{ borderTop: `1px solid ${P[90]}`, paddingTop: 16, marginTop: 4, display: "flex", flexDirection: "column", gap: 10 }}><DetailRow label="Créé par"><span style={{ fontWeight: 600, fontSize: 12, color: P[15] }}>{selectedProject?.manager.name}</span></DetailRow><DetailRow label="Créé le"><span style={{ fontWeight: 600, fontSize: 12, color: P[15] }}>{selectedProject?.created}</span></DetailRow></div>
                            </div>
                        </aside>}
                    </div>
                )}

                {/* ==================== TASK DETAIL ==================== */}
                {view === "taskDetail" && selectedTask && (
                    <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
                        <div style={{ flex: 1, padding: "32px 40px", overflow: "auto" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12, fontSize: 13, color: P[60] }}><span onClick={goToProjects} style={{ cursor: "pointer", color: P[40], fontWeight: 600 }}>Projets</span><span>›</span><span onClick={goToProject} style={{ cursor: "pointer", color: P[40], fontWeight: 600 }}>{selectedProject?.title}</span><span>›</span><span style={{ color: P[30] }}>{selectedTask.title}</span></div>
                            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 32 }}>
                                <div style={{ display: "flex", alignItems: "center", gap: 14 }}><div style={{ fontSize: 22, lineHeight: 1 }}>📋</div><h1 style={{ fontSize: 24, fontWeight: 800, letterSpacing: "-0.03em", margin: 0, color: P[5] }}>{selectedTask.title}</h1></div>
                                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                                    {!detailOpen && <button onClick={() => setDetailOpen(true)} style={{ display: "flex", alignItems: "center", justifyContent: "center", width: 38, height: 38, borderRadius: 10, border: `1px solid ${P[90]}`, background: "#fff", cursor: "pointer", color: P[30] }}><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" /></svg></button>}
                                    <div style={{ position: "relative" }}><button onClick={() => setTaskMenuOpen(!taskMenuOpen)} style={{ display: "flex", alignItems: "center", justifyContent: "center", width: 38, height: 38, borderRadius: 10, border: `1px solid ${P[90]}`, background: taskMenuOpen ? P[95] : "#fff", cursor: "pointer", color: P[30] }}><ThreeDotIcon size={18} /></button><DropdownMenu items={taskMenuItems} open={taskMenuOpen} onClose={() => setTaskMenuOpen(false)} /></div>
                                </div>
                            </div>
                            <div style={{ marginBottom: 36 }}><div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}><h2 style={{ fontSize: 16, fontWeight: 750, margin: 0, color: P[10] }}>Description</h2><button style={{ display: "flex", alignItems: "center", gap: 6, padding: "7px 14px", borderRadius: 8, border: `1px solid ${P[90]}`, background: "#fff", cursor: "pointer", fontSize: 13, fontWeight: 600, color: P[30] }}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" /></svg>Edit</button></div><div style={{ background: "#fff", borderRadius: 12, padding: "20px 24px", border: `1px solid ${P[90]}`, minHeight: 80 }}><MarkdownContent content={selectedTask.description} /></div></div>
                            <div><div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}><h2 style={{ fontSize: 16, fontWeight: 750, margin: 0, color: P[10] }}>Documents</h2><button style={{ display: "flex", alignItems: "center", gap: 6, padding: "7px 14px", borderRadius: 8, border: `1px solid ${P[90]}`, background: "#fff", cursor: "pointer", fontSize: 13, fontWeight: 600, color: P[30] }}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></svg>Upload File</button></div>
                                {selectedTask.docs.length === 0 ? <div style={{ background: "#fff", borderRadius: 12, border: `1px solid ${P[90]}`, padding: "40px 24px", textAlign: "center" }}><div style={{ fontSize: 32, marginBottom: 8 }}>📂</div><p style={{ color: P[60], fontSize: 14 }}>Aucun document</p></div>
                                    : <div style={{ background: "#fff", borderRadius: 12, border: `1px solid ${P[90]}`, overflow: "hidden" }}>
                                        <div style={{ display: "grid", gridTemplateColumns: "1fr 120px 140px", padding: "12px 20px", background: P[95], borderBottom: `1px solid ${P[90]}`, fontSize: 11, fontWeight: 700, color: P[60], textTransform: "uppercase", letterSpacing: "0.06em" }}><span>Nom</span><span>Type</span><span style={{ textAlign: "right" }}>Actions</span></div>
                                        {selectedTask.docs.map((doc, i) => <div key={doc.id} style={{ display: "grid", gridTemplateColumns: "1fr 120px 140px", padding: "12px 20px", alignItems: "center", borderBottom: i < selectedTask.docs.length - 1 ? `1px solid ${P[95]}` : "none" }}><div style={{ display: "flex", alignItems: "center", gap: 12 }}><DocTypeIcon type={doc.type} /><span style={{ fontSize: 14, fontWeight: 600, color: P[10] }}>{doc.name}</span></div><span style={{ fontSize: 12, color: P[60], textTransform: "uppercase", fontWeight: 600 }}>DOCUMENT</span><div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 8 }}><button style={{ display: "flex", alignItems: "center", gap: 6, padding: "6px 12px", borderRadius: 8, border: `1px solid ${P[90]}`, background: "#fff", cursor: "pointer", fontSize: 12, fontWeight: 600, color: P[40] }} onMouseEnter={e => e.currentTarget.style.background = P[95]} onMouseLeave={e => e.currentTarget.style.background = "#fff"}><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" /><polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" /></svg>Open object</button><MenuButton id={doc.id} openId={openTaskDocMenuId} setOpenId={setOpenTaskDocMenuId} items={docMenuItems} /></div></div>)}
                                    </div>}
                            </div>
                        </div>
                        {detailOpen && <aside style={{ width: 340, background: "#fff", borderLeft: `1px solid ${P[90]}`, padding: "32px 24px", overflow: "auto", flexShrink: 0 }}>
                            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}><h3 style={{ fontSize: 12, fontWeight: 700, color: P[60], textTransform: "uppercase", letterSpacing: "0.08em", margin: 0 }}>Details</h3><button onClick={() => setDetailOpen(false)} style={{ display: "flex", alignItems: "center", justifyContent: "center", width: 28, height: 28, borderRadius: 8, border: `1px solid ${P[90]}`, background: "transparent", cursor: "pointer", color: P[60] }}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg></button></div>
                            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                                <DetailRow label="Assigned to"><Avatar initials={selectedTask.assignee.initials} color={selectedTask.assignee.color} size={26} /><span style={{ fontSize: 13, fontWeight: 600, color: P[10] }}>{selectedTask.assignee.name}</span></DetailRow>
                                <DetailRow label="Status"><StatusBadge status={selectedTask.status} /></DetailRow>
                                <DetailRow label="Priority"><PriorityBadge priority={selectedTask.priority} /></DetailRow>
                                <DetailRow label="Progress"><ProgressRing progress={selectedTask.progress} size={44} /></DetailRow>
                                <div style={{ height: 1, background: P[90] }} />
                                <DetailRow label="Start date"><span style={{ fontSize: 13, fontWeight: 600, color: P[10] }}>{selectedTask.dates[0]}</span></DetailRow>
                                <DetailRow label="Due date"><span style={{ fontSize: 13, fontWeight: 600, color: P[10] }}>{selectedTask.dates[1]}</span></DetailRow>
                                <div style={{ height: 1, background: P[90] }} />
                                <DetailRow label="Created by"><Avatar initials={selectedTask.createdBy.initials} color={selectedTask.createdBy.color} size={26} /><span style={{ fontSize: 13, fontWeight: 600, color: P[10] }}>{selectedTask.createdBy.name}</span></DetailRow>
                                <DetailRow label="Created at"><span style={{ fontSize: 13, fontWeight: 600, color: P[10] }}>{selectedTask.createdAt}</span></DetailRow>
                                <DetailRow label="Last modified by"><Avatar initials={selectedTask.lastModifiedBy.initials} color={selectedTask.lastModifiedBy.color} size={26} /><span style={{ fontSize: 13, fontWeight: 600, color: P[10] }}>{selectedTask.lastModifiedBy.name}</span></DetailRow>
                                <DetailRow label="Last modified at"><span style={{ fontSize: 13, fontWeight: 600, color: P[10] }}>{selectedTask.lastModifiedAt}</span></DetailRow>
                            </div>
                        </aside>}
                    </div>
                )}
            </main>
        </div>
    );
}