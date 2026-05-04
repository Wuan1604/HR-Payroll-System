const IconBase = ({ children, size = 18, strokeWidth = 1.8, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={strokeWidth}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    {...props}
  >
    {children}
  </svg>
)

export const LayoutDashboard = (props) => <IconBase {...props}><rect x="3" y="3" width="7" height="8" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="15" width="7" height="6" rx="1.5"/></IconBase>
export const Users = (props) => <IconBase {...props}><path d="M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2"/><circle cx="9.5" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></IconBase>
export const UserPlus = (props) => <IconBase {...props}><path d="M15 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><path d="M19 8v6"/><path d="M22 11h-6"/></IconBase>
export const UserRoundPlus = UserPlus
export const UserCircle2 = (props) => <IconBase {...props}><circle cx="12" cy="12" r="10"/><circle cx="12" cy="9" r="3"/><path d="M6.2 19a6 6 0 0 1 11.6 0"/></IconBase>
export const UserCog = (props) => <IconBase {...props}><circle cx="9" cy="7" r="4"/><path d="M2 21v-2a4 4 0 0 1 4-4h4"/><circle cx="17" cy="17" r="3"/><path d="M17 12.5v1"/><path d="M17 20.5v1"/><path d="M12.5 17h1"/><path d="M20.5 17h1"/><path d="m13.8 13.8.7.7"/><path d="m19.5 19.5.7.7"/><path d="m13.8 20.2.7-.7"/><path d="m19.5 14.5.7-.7"/></IconBase>
export const Building2 = (props) => <IconBase {...props}><path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18"/><path d="M6 12H4a2 2 0 0 0-2 2v8"/><path d="M18 9h2a2 2 0 0 1 2 2v11"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/></IconBase>
export const BriefcaseBusiness = (props) => <IconBase {...props}><path d="M10 6V5a2 2 0 0 1 2-2h0a2 2 0 0 1 2 2v1"/><rect x="3" y="6" width="18" height="14" rx="2"/><path d="M3 12h18"/><path d="M12 12v2"/></IconBase>
export const Wallet = (props) => <IconBase {...props}><path d="M20 7V6a2 2 0 0 0-2-2H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v9a2 2 0 0 1-2 2H5a3 3 0 0 1-3-3V6"/><path d="M16 13h2"/></IconBase>
export const FileSpreadsheet = (props) => <IconBase {...props}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M8 13h8"/><path d="M8 17h8"/><path d="M10 9v10"/></IconBase>
export const FileText = (props) => <IconBase {...props}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M8 13h8"/><path d="M8 17h6"/><path d="M8 9h2"/></IconBase>
export const History = (props) => <IconBase {...props}><path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v6h6"/><path d="M12 7v5l3 2"/></IconBase>
export const Clock3 = (props) => <IconBase {...props}><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></IconBase>
export const Medal = (props) => <IconBase {...props}><path d="M7 2h10l-2 6H9z"/><circle cx="12" cy="15" r="5"/><path d="m10.5 15 1 1 2-2"/></IconBase>
export const Mail = (props) => <IconBase {...props}><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></IconBase>
export const MailPlus = (props) => <IconBase {...props}><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/><path d="M18 14v4"/><path d="M20 16h-4"/></IconBase>
export const Send = (props) => <IconBase {...props}><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></IconBase>
export const ShieldCheck = (props) => <IconBase {...props}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/><path d="m9 12 2 2 4-5"/></IconBase>
export const LogOut = (props) => <IconBase {...props}><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/></IconBase>
export const LogIn = (props) => <IconBase {...props}><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><path d="M10 17l5-5-5-5"/><path d="M15 12H3"/></IconBase>
export const KeyRound = (props) => <IconBase {...props}><circle cx="7.5" cy="15.5" r="3.5"/><path d="m10 13 9-9"/><path d="m15 4 2 2"/><path d="m13 6 2 2"/></IconBase>
export const LockKeyhole = (props) => <IconBase {...props}><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/><circle cx="12" cy="16" r="1"/><path d="M12 17v1"/></IconBase>
export const RefreshCw = (props) => <IconBase {...props}><path d="M21 12a9 9 0 0 0-15.5-6.3L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 15.5 6.3L21 16"/><path d="M21 21v-5h-5"/></IconBase>
export const Plus = (props) => <IconBase {...props}><path d="M12 5v14"/><path d="M5 12h14"/></IconBase>
export const Pencil = (props) => <IconBase {...props}><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></IconBase>
export const Trash2 = (props) => <IconBase {...props}><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></IconBase>
export const X = (props) => <IconBase {...props}><path d="M18 6 6 18"/><path d="m6 6 12 12"/></IconBase>
export const Save = (props) => <IconBase {...props}><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2"/><path d="M17 21v-8H7v8"/><path d="M7 3v5h8"/></IconBase>
export const Search = (props) => <IconBase {...props}><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></IconBase>
export const ArrowLeft = (props) => <IconBase {...props}><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></IconBase>
export const Calculator = (props) => <IconBase {...props}><rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 6h8"/><path d="M8 10h.01"/><path d="M12 10h.01"/><path d="M16 10h.01"/><path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 14h.01"/><path d="M8 18h.01"/><path d="M12 18h.01"/><path d="M16 18h.01"/></IconBase>
export const RotateCcw = (props) => <IconBase {...props}><path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v6h6"/></IconBase>
export const BadgeInfo = (props) => <IconBase {...props}><path d="M12 2 4 6v6c0 5 8 10 8 10s8-5 8-10V6z"/><path d="M12 10v5"/><path d="M12 7h.01"/></IconBase>
