import React, { useState } from 'react';
import { Badge } from "@/components/ui/badge";

interface Article {
  id: string;
  title: string;
  link: string;
  snippet: string;
}

interface TrendResultProps {
  title: string;
  description: string;
  articleCount: number;
  relevance: number;
  articles?: Article[];
  darkMode?: boolean;
}

const TrendResult: React.FC<TrendResultProps> = ({
  title,
  description,
  articleCount,
  relevance,
  articles = [],
  darkMode = false
}) => {
  const [showArticles, setShowArticles] = useState(false);
  return (
    <div className={`border ${darkMode ? 'border-white/10' : 'border-black/5'} rounded-lg p-4 mb-4 ${darkMode ? 'hover:border-primary/50' : 'hover:border-primary/20'} transition-all duration-300 ease-in-out group`}>
      <div className="flex justify-between items-start mb-2">
        <h3 className={`font-medium ${darkMode ? 'text-white' : 'text-foreground'}`}>{title}</h3>
        <Badge 
          variant="outline" 
          className={`ml-2 ${darkMode ? 'border-white/20 text-white/90' : 'border-black/10'} text-xs`}
        >
          {articleCount} articles
        </Badge>
      </div>
      
      <p className={`text-sm ${darkMode ? 'text-white/70' : 'text-muted-foreground'} mb-3`}>{description}</p>
      
      <div className="w-full mt-3">
        <div className={`flex justify-between text-xs mb-1 ${darkMode ? 'text-white/80' : ''}`}>
          <span>Relevance</span>
          <span>{relevance}%</span>
        </div>
        <div className={`h-1.5 w-full ${darkMode ? 'bg-white/10' : 'bg-black/5'} rounded-full overflow-hidden`}>
          <div 
            className={`h-full ${darkMode ? 'bg-primary/80 group-hover:bg-primary' : 'bg-primary/70 group-hover:bg-primary'} rounded-full transition-colors duration-300`}
            style={{ 
              animation: 'growWidth 1.5s ease-out',
              animationFillMode: 'forwards',
              animationDelay: '100ms',
              width: '0%'
            }}
          />
        </div>
        <style>{`
          @keyframes growWidth {
            from { width: 0%; }
            to { width: ${relevance}%; }
          }
        `}</style>
      </div>

      {articles.length > 0 && (
        <button
          className="text-xs text-primary mt-2 underline"
          onClick={() => setShowArticles(!showArticles)}
        >
          {showArticles ? 'Hide Articles' : `Show ${articles.length} Articles`}
        </button>
      )}

      {showArticles && (
        <ul className="mt-2 list-disc list-inside space-y-1 text-sm">
          {articles.map((a) => (
            <li key={a.id}>
              <a href={a.link} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                {a.title}
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default TrendResult; 