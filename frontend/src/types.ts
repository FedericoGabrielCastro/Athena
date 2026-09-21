export type Category = {
  id: number;
  slug: string;
  name: string;
  description: string;
  color: string;
};

export type Ticket = {
  id: number;
  title: string;
  body: string;
  category: Category;
  priority: "low" | "medium" | "high" | "urgent";
  confidence: number;
  tags: string[];
  rationale: string;
  engine: string;
  corrected: boolean;
  created_at: string;
};

export type ClassificationPreview = {
  category: Category;
  priority: Ticket["priority"];
  confidence: number;
  tags: string[];
  rationale: string;
  engine: string;
  scores: Record<string, number>;
};

export type Stats = {
  total: number;
  by_category: { slug: string; name: string; color: string; count: number }[];
  by_priority: { priority: string; count: number }[];
};
