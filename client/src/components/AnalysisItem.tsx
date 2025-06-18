import React, { useState } from 'react';
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp, Trash2 } from "lucide-react";
import TrendResult from './TrendResult';

interface Article {
  id: string;
  title: string;
  link: string;
  snippet: string;
}

interface Trend {
  id: string;
  title: string;
  description: string;
  articleCount: number;
  relevance: number;
  articles?: Article[];
}

interface AnalysisItemProps {
  id: string;
  query: string;
  timestamp: string;
  type: 'Research' | 'Community';
  trends: Trend[];
  onDelete: (id: string) => void;
  darkMode?: boolean;
}

const AnalysisItem: React.FC<AnalysisItemProps> = ({
  id,
  query,
  timestamp,
  type,
  trends,
  onDelete,
  darkMode = false
}) => {
  const [showTrends, setShowTrends] = useState(false);

  const formatDate = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const totalArticles = trends.reduce((sum, trend) => sum + trend.articleCount, 0);

  return (
    <div className={`border rounded-lg p-4 mb-4 ${
      darkMode 
        ? 'border-white/10 bg-black/20' 
        : 'border-black/10 bg-white'
    }`}>
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h3 className={`font-medium text-lg mb-1 ${
            darkMode ? 'text-white' : 'text-foreground'
          }`}>
            {query}
          </h3>
          <div className="flex items-center gap-2 text-sm">
            <span className={darkMode ? 'text-white/60' : 'text-muted-foreground'}>
              {formatDate(timestamp)}
            </span>
            <Badge 
              variant="outline" 
              className={`${
                darkMode ? 'border-blue-400/30 text-blue-400' : 'border-blue-600/20 text-blue-600'
              } text-xs`}
            >
              {type}
            </Badge>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onDelete(id)}
          className={`p-2 ${
            darkMode 
              ? 'text-red-400 hover:text-red-300 hover:bg-red-400/10' 
              : 'text-red-600 hover:text-red-700 hover:bg-red-50'
          }`}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex justify-between items-center mb-3">
        <div className="flex items-center gap-4 text-sm">
          <span className={`${darkMode ? 'text-white/80' : 'text-foreground'} font-medium`}>
            {trends.length} topics • {totalArticles} articles
          </span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowTrends(!showTrends)}
          className={`text-xs ${
            darkMode 
              ? 'text-white/80 hover:text-white' 
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <span>View All Topics</span>
          {showTrends ? <ChevronUp className="h-3 w-3 ml-1" /> : <ChevronDown className="h-3 w-3 ml-1" />}
        </Button>
      </div>

      {showTrends && (
        <div className="space-y-3 mt-4">
          {trends.map((trend, index) => (
            <TrendResult
              key={trend.id}
              title={trend.title}
              description={trend.description}
              articleCount={trend.articleCount}
              relevance={trend.relevance}
              articles={trend.articles}
              darkMode={darkMode}
              rank={index + 1}
              trendId={trend.id}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default AnalysisItem; 