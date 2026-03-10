import { MessageSquare, Library, History, Settings } from "lucide-react";

interface NavItemProps {
  icon: React.ReactNode;
  label: string;
  active?: boolean;
}

const NavItem: React.FC<NavItemProps> = ({ icon, label, active = false }) => {
  return (
    <button
      className={`flex flex-col items-center gap-1 flex-1 py-1 transition-colors ${active ? "text-primary" : "text-slate-500 hover:text-slate-300"}`}
    >
      <div className="h-8 flex items-center justify-center">{icon}</div>
      <span className="text-[10px] font-bold uppercase tracking-wider">
        {label}
      </span>
    </button>
  );
};

export const BottomNav: React.FC = () => {
  return (
    <nav className="flex items-center justify-around px-4 pt-2 pb-6 border-t border-slate-800 bg-background-dark">
      <NavItem icon={<MessageSquare size={20} />} label="Research" active />
      <NavItem icon={<Library size={20} />} label="Library" />
      <NavItem icon={<History size={20} />} label="History" />
      <NavItem icon={<Settings size={20} />} label="Settings" />
    </nav>
  );
};
