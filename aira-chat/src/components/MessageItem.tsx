import { Bot } from "lucide-react";
import { motion } from "motion/react";
import type { Message } from "../types";

interface MessageItemProps {
  message: Message;
}

export const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex flex-col ${message.sender === "YOU" ? "items-end" : "items-start"}`}
    >
      <div
        className={`flex items-start gap-3 max-w-[90%] ${message.sender === "YOU" ? "flex-row-reverse" : "flex-row"}`}
      >
        {message.sender === "ARIA" && (
          <div className="w-9 h-9 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
            <Bot size={18} className="text-primary" />
          </div>
        )}

        <div
          className={`flex flex-col gap-1.5 ${message.sender === "YOU" ? "items-end" : "items-start"}`}
        >
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tight px-1">
            {message.sender}
          </span>

          <div
            className={`px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm ${
              message.sender === "YOU"
                ? "bg-primary text-white rounded-tr-none"
                : "bg-slate-800 text-slate-200 border border-slate-700/50 rounded-tl-none"
            }`}
          >
            {message.content}
          </div>

          {message.tags && message.tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-1">
              {message.tags.map((tag, idx) => (
                <button
                  key={idx}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-colors border ${
                    tag.type === "source" || tag.type === "table"
                      ? "bg-primary/10 border-primary/20 text-primary hover:bg-primary/20"
                      : "bg-slate-800 border-slate-700 text-slate-400 hover:bg-slate-700"
                  }`}
                >
                  {tag.icon}
                  {tag.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};
