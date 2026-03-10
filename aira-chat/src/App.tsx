import { useState, useRef, useEffect } from "react";
import { FileText } from "lucide-react";
import { AnimatePresence } from "motion/react";
import type { Message } from "./types";
import { Header } from "./components/Header";
import { MessageItem } from "./components/MessageItem";
import { InputArea } from "./components/InputArea";
import { BottomNav } from "./components/BottomNav";

const API_BASE = "http://127.0.0.1:8000"; // Adjust if backend is on different port

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleFileUpload = async (files: FileList) => {
    setIsUploading(true);
    const formData = new FormData();

    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }

    try {
      const response = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const result = await response.json();

      // Add a system message about successful upload
      const uploadMessage: Message = {
        id: Date.now().toString(),
        sender: "ARIA",
        content: `Documents uploaded successfully: ${result.message}`,
        timestamp: "Today",
      };
      setMessages((prev) => [...prev, uploadMessage]);
    } catch (error) {
      console.error("Upload error:", error);
      const errorMessage: Message = {
        id: Date.now().toString(),
        sender: "ARIA",
        content: "Sorry, there was an error uploading your documents.",
        timestamp: "Today",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isStreaming) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      sender: "YOU",
      content: inputValue,
      timestamp: "Today",
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsStreaming(true);

    // Add a placeholder for the bot response
    const botMessageId = (Date.now() + 1).toString();
    const botMessage: Message = {
      id: botMessageId,
      sender: "ARIA",
      content: "",
      timestamp: "Today",
      tags: [],
    };
    setMessages((prev) => [...prev, botMessage]);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: inputValue }),
      });

      if (!response.ok) {
        console.log(response);
        throw new Error("Failed to get response");
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        let accumulatedContent = "";
        let sources: string[] = [];

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.type === "chunk") {
                  accumulatedContent += data.content;
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === botMessageId
                        ? { ...msg, content: accumulatedContent }
                        : msg,
                    ),
                  );
                } else if (data.type === "sources") {
                  sources = data.content;
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === botMessageId
                        ? {
                            ...msg,
                            content: accumulatedContent,
                            tags: sources.map((source) => ({
                              type: "source" as const,
                              label: `Source: ${source}`,
                              icon: <FileText size={12} />,
                            })),
                          }
                        : msg,
                    ),
                  );
                }
              } catch (e) {
                console.error("Failed to parse SSE data:", e);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error("Error:", error);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === botMessageId
            ? {
                ...msg,
                content:
                  "Sorry, I encountered an error processing your request.",
              }
            : msg,
        ),
      );
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-md mx-auto bg-background-dark border-x border-slate-800 overflow-hidden font-sans">
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.md"
        onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
        className="hidden"
      />
      <Header title="ARIA" subtitle="Researching: Project_Alpha.pdf" />

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-hide">
        <div className="flex justify-center py-2">
          <span className="px-3 py-1 rounded-full bg-slate-800/50 text-slate-500 text-[10px] font-bold uppercase tracking-widest">
            Today
          </span>
        </div>

        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <MessageItem key={msg.id} message={msg} />
          ))}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </main>

      <InputArea
        value={inputValue}
        onChange={setInputValue}
        onSend={handleSendMessage}
        disabled={isStreaming}
        onFileSelect={handleFileSelect}
        isUploading={isUploading}
      />

      <BottomNav />
    </div>
  );
}
