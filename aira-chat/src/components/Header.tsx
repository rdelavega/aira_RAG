import { ArrowLeft, MoreVertical } from "lucide-react";

interface HeaderProps {
  title: string;
  subtitle: string;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle }) => {
  return (
    <header className="flex items-center justify-between p-4 border-b border-slate-800 bg-background-dark/80 backdrop-blur-md sticky top-0 z-10">
      <div className="flex items-center gap-3">
        <button className="p-2 rounded-full bg-slate-800/50 hover:bg-slate-800 transition-colors text-slate-300">
          <ArrowLeft size={20} />
        </button>
        <div>
          <h1 className="text-lg font-bold text-slate-100 leading-tight">
            {title}
          </h1>
          <div className="flex items-center gap-1.5">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
            <p className="text-xs font-medium text-slate-400">{subtitle}</p>
          </div>
        </div>
      </div>
      <button className="p-2 rounded-full hover:bg-slate-800 transition-colors text-slate-400">
        <MoreVertical size={20} />
      </button>
    </header>
  );
};
