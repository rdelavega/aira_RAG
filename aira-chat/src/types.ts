export interface Tag {
  type: "source" | "note" | "table";
  label: string;
  icon: React.ReactNode;
}

export interface Message {
  id: string;
  sender: "ARIA" | "YOU";
  content: string;
  timestamp: string;
  tags?: Tag[];
}
