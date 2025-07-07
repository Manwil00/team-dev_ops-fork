import React, { useState, useEffect } from 'react';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { BarChart3, ChevronDown, ChevronUp, Loader2 } from "lucide-react";

interface SettingsFormProps {
  autoDetect: boolean;
  maxArticles: number;
  nrTopics: number;
  query: string;
  source: "research" | "community";
  feed: string;
  onAutoDetectChange: (checked: boolean) => void;
  onMaxArticlesChange: (value: number) => void;
  onNrTopicsChange: (value: number) => void;
  onSourceChange: (value: "research" | "community") => void;
  onFeedChange: (value: string) => void;
  onBackToInput: () => void;
  onAnalyze: () => void;
  isLoading?: boolean;
  loadingMessage?: string;
}

const SettingsForm: React.FC<SettingsFormProps> = ({
  autoDetect,
  maxArticles,
  nrTopics,
  query,
  source,
  feed,
  onAutoDetectChange,
  onMaxArticlesChange,
  onNrTopicsChange,
  onSourceChange,
  onFeedChange,
  onBackToInput,
  onAnalyze,
  isLoading = false,
  loadingMessage = "Discovering Topics..."
}) => {
  const [advancedMode, setAdvancedMode] = useState(false);
  const [searchTerms, setSearchTerms] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('cs.CV');
  const [categories, setCategories] = useState<Record<string, string[]>>({});
  const [categoriesLoading, setCategoriesLoading] = useState(true);
  const [showCategories, setShowCategories] = useState(false);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        setCategoriesLoading(true);
        const response = await fetch('/api/v1/sources/arxiv/categories');
        if (!response.ok) {
          throw new Error('Failed to fetch categories');
        }
        const data = await response.json();
        setCategories(data);
      } catch (error) {
        console.error(error);
        // On error, categories will remain an empty object.
        // The UI will show a loading or empty state.
      } finally {
        setCategoriesLoading(false);
    }
    };

    fetchCategories();
  }, []);

  // Build advanced query when search terms or category changes
  useEffect(() => {
    if (advancedMode && searchTerms.trim() && source === 'research') {
      fetch('/api/query/build?source=arxiv', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ search_terms: searchTerms, category: selectedCategory })
      })
        .then(res => res.json())
        .then(data => onFeedChange(data.query))
        .catch(err => console.error('Failed to build advanced query:', err));
    }
  }, [advancedMode, searchTerms, selectedCategory, source, onFeedChange]);
  return (
    <div className="flex flex-col space-y-6 h-full">
      <div className="flex items-center justify-between space-x-4">
        <div className="space-y-0.5">
          <Label htmlFor="auto-detect">Auto-detect source</Label>
          <p className="text-sm text-muted-foreground">
            Automatically determine if query is research or community focused
          </p>
        </div>
        <Switch
          id="auto-detect"
          checked={autoDetect}
          onCheckedChange={onAutoDetectChange}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="max-articles">Maximum articles to analyze</Label>
        <Input
          id="max-articles"
          type="number"
          min={1}
          max={150}
          value={maxArticles}
          onChange={(e) => {
            const raw = parseInt(e.target.value, 10);
            const clamped = isNaN(raw) ? 1 : Math.min(150, Math.max(1, raw));
            onMaxArticlesChange(clamped);
          }}
          className="w-full"
        />
        <p className="text-sm text-muted-foreground">
          Maximum number of articles (1-150) to use for the analysis.
        </p>
      </div>

      {/* Number of topics selection */}
      <div className="space-y-2">
        <Label htmlFor="nr-topics">Maximum number of topics</Label>
        <Input
          id="nr-topics"
          type="number"
          min={1}
          max={7}
          value={nrTopics}
          onChange={(e) => {
            const raw = parseInt(e.target.value, 10);
            const clamped = isNaN(raw) ? 1 : Math.min(7, Math.max(1, raw));
            onNrTopicsChange(clamped);
          }}
          className="w-full"
        />
        <p className="text-sm text-muted-foreground">
          Upper limit (1–7). The algorithm may return fewer clusters if the data doesn&apos;t support more.
        </p>
      </div>

      {/* Manual source selection */}
      {!autoDetect && (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="source-select">Source</Label>
            <select
              id="source-select"
              value={source}
              onChange={(e) => onSourceChange(e.target.value as "research" | "community")}
              className="w-full border border-input rounded-md p-2"
            >
              <option value="research">Research (arXiv)</option>
            </select>
          </div>

          {source === "research" ? (
            <div className="space-y-4">
              {/* Advanced Query Toggle */}
              <div className="flex items-center justify-between space-x-4">
                <div className="space-y-0.5">
                  <Label htmlFor="advanced-mode">Advanced ArXiv Search</Label>
                  <p className="text-sm text-muted-foreground">
                    Build advanced queries with specific search terms
                  </p>
                </div>
                <Switch
                  id="advanced-mode"
                  checked={advancedMode}
                  onCheckedChange={setAdvancedMode}
                />
              </div>

              {advancedMode ? (
                <>
                  {/* Search Terms Input */}
                  <div className="space-y-2">
                    <Label htmlFor="search-terms">Search Terms</Label>
                    <Input
                      id="search-terms"
                      placeholder="e.g., graph neural network, transformer"
                      value={searchTerms}
                      onChange={(e) => setSearchTerms(e.target.value)}
                      className="w-full"
                    />
                    <p className="text-sm text-muted-foreground">
                      Enter specific research terms you want to search for
                    </p>
                  </div>

                  {/* Category Selection */}
                  <div className="space-y-2">
                    <Label htmlFor="category-select">ArXiv Category</Label>
                    <div className="relative">
                      <select
                        id="category-select"
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                        className="w-full border border-input rounded-md p-2 appearance-none"
                        disabled={categoriesLoading || Object.keys(categories).length === 0}
                      >
                        {categoriesLoading ? (
                          <option>Loading categories...</option>
                        ) : Object.keys(categories).length === 0 ? (
                          <option>Could not load categories</option>
                        ) : (
                          Object.entries(categories).map(([field, categories]) => (
                          <optgroup key={field} label={field}>
                            {categories.map(cat => {
                                // The category format can be either "cs.AI" or "cs.AI - Artificial Intelligence"
                                const [code, ...nameParts] = cat.split(' - ');
                                const name = nameParts.join(' - ');
                                return <option key={code} value={code}>{code}{name ? ` - ${name}` : ''}</option>;
                            })}
                          </optgroup>
                          ))
                        )}
                      </select>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowCategories(!showCategories)}
                        className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1"
                      >
                        {showCategories ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>

                  {/* Generated Query Preview */}
                  {feed && (
                    <div className="space-y-2">
                      <Label>Generated Query</Label>
                      <div className="p-3 bg-muted rounded-md text-sm font-mono">
                        {feed}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <>
                  {/* Simple Category Input */}
                  <div className="space-y-2">
                    <Label htmlFor="feed-input">ArXiv Category</Label>
                    <Input
                      id="feed-input"
                      placeholder="e.g., cs.CV, cs.AI, cs.LG"
                      value={feed}
                      onChange={(e) => onFeedChange(e.target.value)}
                      className="w-full"
                    />
                    <p className="text-sm text-muted-foreground">
                      Specify the arXiv category ID (<a href="https://arxiv.org/category_taxonomy" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">View arXiv taxonomy</a>)
                    </p>
                  </div>
                </>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              <Label htmlFor="feed-input">Subreddit Name</Label>
              <Input
                id="feed-input"
                placeholder="e.g., computervision"
                value={feed}
                onChange={(e) => onFeedChange(e.target.value)}
                className="w-full"
              />
              <p className="text-sm text-muted-foreground">
                Specify the subreddit name without r/
              </p>
            </div>
          )}
        </div>

      )}

      <div className="flex justify-between pt-4 mt-auto">
        <Button
          variant="outline"
          onClick={onBackToInput}
          className="border-black/10 hover:border-primary/50 transition-all duration-300"
        >
          Back to Input
        </Button>

        <div className="relative">
          <Button
            onClick={onAnalyze}
            className="flex items-center gap-2 bg-gradient-to-r from-primary to-primary/80 hover:bg-primary/90 transition-all duration-300 disabled:opacity-50"
            variant="default"
            disabled={!query.trim() || isLoading}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <BarChart3 className="h-4 w-4" />
            )}
            <span className="analyze-text relative">
              {isLoading ? loadingMessage : "Analyze Trends"}
              <span className="analyze-underline"></span>
            </span>
          </Button>
          <style dangerouslySetInnerHTML={{
            __html: `
              .analyze-underline {
                position: absolute;
                left: 0;
                right: 0;
                bottom: -1px;
                height: 1px;
                background: rgba(255, 255, 255, 0.5);
                transform: scaleX(0);
                transform-origin: left;
                transition: transform 0.5s ease-in-out;
              }
              button:hover .analyze-underline {
                transform: scaleX(1);
              }
            `
          }} />
        </div>
      </div>
    </div>
  );
};

export default SettingsForm;
