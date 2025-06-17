export interface ArticleDto {
  id: string;
  title: string;
  link: string;
  snippet: string;
}

export interface TrendDto {
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
  feedUrl: string;
  trends: TrendDto[];
}

export interface AnalyzeRequest {
  query: string;
  autoDetect?: boolean;
  maxArticles?: number;
  trendClusters?: number;
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