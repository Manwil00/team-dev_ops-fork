import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import QueryForm from './QueryForm';
import SettingsForm from './SettingsForm';
import { AnalyzeRequest } from "../services/analysis";

interface StartExploringFormProps {
  onAnalyze: (req: AnalyzeRequest) => void;
}

const StartExploringForm: React.FC<StartExploringFormProps> = ({ onAnalyze }) => {
  const [showSettings, setShowSettings] = useState<boolean>(false);
  const [query, setQuery] = useState<string>("");
  const [autoDetect, setAutoDetect] = useState<boolean>(true);
  const [maxArticles, setMaxArticles] = useState<number>(50);
  const [trendClusters, setTrendClusters] = useState<number>(3);
  const [source, setSource] = useState<"research" | "community">("research");
  const [feed, setFeed] = useState<string>("cs.CV");

  const handleAnalyze = () => {
    if (!query.trim()) return;

    const req: AnalyzeRequest = {
      query,
      autoDetect,
      maxArticles,
      trendClusters,
    };

    if (!autoDetect) {
      req.source = source;
      req.feed = feed;
    }

    onAnalyze(req);
  };

  const toggleSettings = () => {
    setShowSettings(!showSettings);
  };

  return (
    <Card className="w-full border bg-white relative overflow-hidden hover:shadow-md transition-all duration-500">
      {/* Background pattern */}
      <div className="absolute inset-0 -z-10 bg-white bg-[size:20px_20px] opacity-10 
                   bg-[linear-gradient(to_right,#f0f0f0_1px,transparent_1px),linear-gradient(to_bottom,#f0f0f0_1px,transparent_1px)]"></div>
      
      <CardHeader>
        <CardTitle className="text-2xl font-semibold">Start Exploring</CardTitle>
        <CardDescription>
          Enter your niche query to discover emerging trends from reddit or arXiv RSS feeds
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div>
          {/* Always show the query form */}
          <QueryForm
            query={query}
            onQueryChange={setQuery}
            onAnalyze={handleAnalyze}
            onSwitchToSettings={toggleSettings}
            showSettings={showSettings}
          />
          
          {/* Settings section that expands/collapses */}
          <div 
            className={`overflow-hidden transition-all duration-500 ease-in-out mt-4 border-t ${
              showSettings ? 'max-h-[900px] opacity-100 pt-4' : 'max-h-0 opacity-0 pt-0 border-transparent'
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium">Advanced Settings</h3>
              <Button 
                variant="ghost" 
                size="sm" 
                className="h-8 w-8 p-0" 
                onClick={toggleSettings}
              >
                <ChevronUp className="h-4 w-4" />
                <span className="sr-only">Close Settings</span>
              </Button>
            </div>
            
            <SettingsForm
              autoDetect={autoDetect}
              maxArticles={maxArticles}
              trendClusters={trendClusters}
              query={query}
              source={source}
              feed={feed}
              onAutoDetectChange={setAutoDetect}
              onMaxArticlesChange={setMaxArticles}
              onTrendClustersChange={setTrendClusters}
              onSourceChange={setSource}
              onFeedChange={setFeed}
              onBackToInput={() => setShowSettings(false)}
              onAnalyze={handleAnalyze}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default StartExploringForm;