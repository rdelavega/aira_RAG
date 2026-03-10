import { PlusCircle, Send } from "lucide-react";

interface InputAreaProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled?: boolean;
  onFileSelect?: () => void;
  isUploading?: boolean;
}

export const InputArea: React.FC<InputAreaProps> = ({
  value,
  onChange,
  onSend,
  disabled = false,
  onFileSelect,
  isUploading = false,
}) => {
  return (
    <div className="p-4 bg-background-dark border-t border-slate-800">
      <div className="flex items-end gap-2">
        <button
          onClick={onFileSelect}
          disabled={isUploading}
          className={`p-2.5 rounded-full transition-colors ${
            isUploading
              ? "bg-slate-800 text-slate-600 cursor-not-allowed"
              : "bg-slate-800 text-slate-400 hover:text-primary"
          }`}
        >
          <PlusCircle size={22} className={isUploading ? "animate-spin" : ""} />
        </button>
        <div className="flex-1 relative">
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                onSend();
              }
            }}
            placeholder="Ask ARIA a question..."
            rows={1}
            disabled={disabled}
            className={`w-full bg-slate-900/50 border border-slate-800 rounded-2xl py-3 pl-4 pr-12 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-primary/50 resize-none transition-all ${
              disabled ? "opacity-50 cursor-not-allowed" : ""
            }`}
          />
          <button
            onClick={onSend}
            disabled={!value.trim() || disabled}
            className={`absolute right-2 bottom-2 p-1.5 rounded-xl transition-all ${
              value.trim() && !disabled
                ? "bg-primary text-white shadow-lg shadow-primary/20"
                : "bg-slate-800 text-slate-600"
            }`}
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};
