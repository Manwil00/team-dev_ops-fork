export interface ArticleDto {
  id: string;
  title: string;
  link: string;
  snippet: string;
}

export interface TopicDto {
  id: string;
  title: string;
  description: string;
  articleCount: number;
  relevance: number;
  articles: ArticleDto[];
}

export interface AnalysisResponse {
  id: string;
  query: string;
  timestamp: string;
  type: string;
  feedUrl?: string;
  trends: TopicDto[];
}

export interface AnalyzeRequest {
  query: string;
  autoDetect?: boolean;
  maxArticles?: number;
  source?: string; // "research" | "community"
  feed?: string;   // e.g. "cs.CV" or "computervision"
}

export async function analyze(request: AnalyzeRequest): Promise<AnalysisResponse> {
  const res = await fetch("http://localhost:8080/api/analyze", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    throw new Error(`Server returned ${res.status}`);
  }

  return res.json();
}

export async function getAnalysisHistory(queryFilter?: string, limit: number = 20): Promise<AnalysisResponse[]> {
  const params = new URLSearchParams();
  if (queryFilter) params.append('query', queryFilter);
  params.append('limit', limit.toString());

  const res = await fetch(`http://localhost:8080/api/analysis/history?${params}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch analysis history: ${res.status}`);
  }

  return res.json();
}

export async function deleteAnalysis(analysisId: string): Promise<void> {
  const res = await fetch(`http://localhost:8080/api/analysis/${analysisId}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!res.ok) {
    throw new Error(`Failed to delete analysis: ${res.status}`);
  }
} 