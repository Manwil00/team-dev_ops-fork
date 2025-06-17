import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RefreshCcw, ChevronDown, ChevronUp, Clock } from "lucide-react";
import TrendResult from './TrendResult';

export interface Article {
  id: string;
  title: string;
  link: string;
  snippet: string;
}

export interface Trend {
  id: string;
  title: string;
  description: string;
  articleCount: number;
  relevance: number;
  articles?: Article[];
}

export interface AnalysisItemData {
  id: string;
  query: string;
  timestamp: string;
  type: 'Research' | 'Community';
  trends: Trend[];
  feedUrl: string;
}

interface AnalysisItemProps {
  item: AnalysisItemData;
  onRefresh: (id: string) => void;
}

const AnalysisItem: React.FC<AnalysisItemProps> = ({ item, onRefresh }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="border border-black/10 rounded-lg overflow-hidden bg-white/60 backdrop-blur-sm transition-all duration-300 ease-out hover:border-primary/30 hover:shadow-sm">
      <div className="p-4">
        <div className="flex justify-between items-start">
          <h3 className="font-medium text-foreground">{item.query}</h3>
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-8 w-8 text-muted-foreground hover:text-primary group transition-all duration-300"
            onClick={() => onRefresh(item.id)}
          >
            <RefreshCcw className="h-4 w-4 group-hover:rotate-180 transition-transform duration-500 ease-in-out" />
            <span className="sr-only">Refresh analysis</span>
          </Button>
        </div>
        
        <div className="flex items-center mt-2 text-muted-foreground text-sm">
          <Clock className="h-3.5 w-3.5 mr-1.5" />
          <span>{item.timestamp}</span>
          <a href={item.feedUrl} target="_blank" rel="noopener noreferrer" className="ml-3 text-xs text-blue-600 underline">
            source
          </a>
          <Badge
            variant={item.type === 'Research' ? "default" : "secondary"}
            className={`ml-3 px-2 py-0 text-xs h-5 ${
              item.type === 'Research' ? 'bg-gray-600 text-white' : 'bg-purple-600 text-white'
            }`}
          >
            {item.type}
          </Badge>
        </div>
      </div>

      <div 
        className={`overflow-hidden transition-all duration-500 ease-in-out ${
          isExpanded ? 'max-h-[1000px] opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="px-4 pb-4 pt-1 bg-accent/5">
          {item.trends.map((trend, index) => (
            <div 
              key={trend.id}
              className="animate-fadeIn"
              style={{ 
                animationDelay: `${index * 150}ms`,
                opacity: 0, 
                animation: isExpanded ? `fadeIn 0.5s ease-out forwards ${index * 150}ms` : 'none' 
              }}
            >
              <TrendResult
                title={trend.title}
                description={trend.description}
                articleCount={trend.articleCount}
                relevance={trend.relevance}
                articles={trend.articles}
              />
            </div>
          ))}
        </div>
      </div>

      <Button
        variant="ghost"
        className={`w-full flex items-center justify-center h-9 rounded-none border-t border-black/5 hover:bg-accent/10 text-muted-foreground hover:text-foreground transition-all duration-300 ${
          isExpanded ? 'bg-accent/5' : ''
        }`}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded ? (
          <ChevronUp className="h-4 w-4 transition-transform duration-300 animate-bounce" />
        ) : (
          <ChevronDown className="h-4 w-4 transition-transform duration-300 hover:translate-y-1" />
        )}
        <span className="sr-only">{isExpanded ? 'Collapse' : 'Expand'}</span>
      </Button>
      
      <style dangerouslySetInnerHTML={{
        __html: `
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
          }
        `
      }} />
    </div>
  );
};

export default AnalysisItem; 