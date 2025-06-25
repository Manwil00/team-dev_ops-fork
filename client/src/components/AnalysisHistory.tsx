import React from 'react';
import AnalysisItem from './AnalysisItem';

interface Article {
  id: string;
  title: string;
  link: string;
  snippet: string;
}

interface Topic {
  id: string;
  title: string;
  description: string;
  articleCount: number;
  relevance: number;
  articles?: Article[];
}

interface Analysis {
  id: string;
  query: string;
  timestamp: string;
  type: 'Research' | 'Community';
  topics: Topic[];
  feedUrl?: string;
}

interface AnalysisHistoryProps {
  analyses: Analysis[];
  onDeleteAnalysis: (id: string) => void;
  darkMode?: boolean;
}

const AnalysisHistory: React.FC<AnalysisHistoryProps> = ({ 
  analyses, 
  onDeleteAnalysis, 
  darkMode = false 
}) => {
  if (analyses.length === 0) {
    return (
      <div className={`text-center py-8 ${darkMode ? 'text-white/60' : 'text-muted-foreground'}`}>
        <p>No analyses yet. Try analyzing a query above.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {analyses.map((analysis) => (
        <AnalysisItem
          key={analysis.id}
          id={analysis.id}
          query={analysis.query}
          timestamp={analysis.timestamp}
          type={analysis.type}
          topics={analysis.topics}
          feedUrl={analysis.feedUrl}
          onDelete={onDeleteAnalysis}
          darkMode={darkMode}
        />
      ))}
    </div>
  );
};

export default AnalysisHistory; 