import { useState, useEffect } from 'react';
import Header from './components/Header';
import StartExploringForm from './components/StartExploringForm';
import AnalysisHistory from './components/AnalysisHistory';
import { AspectRatio } from "./components/ui/aspect-ratio";
import { analyze, getAnalysisHistory, deleteAnalysis, AnalyzeRequest } from "./services/analysis";

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
  trends: Topic[];
  feedUrl?: string;
}

function App() {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);

  const handleAnalyze = async (req: AnalyzeRequest) => {
    try {
      const response = await analyze(req);

      const newAnalysis: Analysis = {
        id: response.id,
        query: response.query,
        timestamp: response.timestamp,
        type: response.type as 'Research' | 'Community',
        feedUrl: response.feedUrl,
        trends: response.trends.map((t) => ({
          id: t.id,
          title: t.title,
          description: t.description,
          articleCount: t.articleCount,
          relevance: t.relevance,
          articles: t.articles,
        })),
      };

      setAnalyses([newAnalysis, ...analyses]);
    } catch (err) {
      console.error("Analysis failed", err);
      alert("Failed to analyze query. Please try again.");
    }
  };

  // Load analysis history from database on component mount
  useEffect(() => {
    const loadAnalysisHistory = async () => {
      try {
        setIsLoadingHistory(true);
        const historyData = await getAnalysisHistory();
        
        const analysisItems: Analysis[] = historyData.map((analysis) => ({
          id: analysis.id,
          query: analysis.query,
          timestamp: analysis.timestamp,
          type: analysis.type as 'Research' | 'Community',
          feedUrl: analysis.feedUrl,
          trends: analysis.trends.map((t) => ({
            id: t.id,
            title: t.title,
            description: t.description,
            articleCount: t.articleCount,
            relevance: t.relevance,
            articles: t.articles,
          })),
        }));
        
        setAnalyses(analysisItems);
      } catch (error) {
        console.error('Failed to load analysis history:', error);
        // Don't show error to user, just log it - app can still function
      } finally {
        setIsLoadingHistory(false);
      }
    };

    loadAnalysisHistory();
  }, []);

  const handleDeleteAnalysis = async (id: string) => {
    try {
      await deleteAnalysis(id);
      // Remove from local state after successful deletion
      setAnalyses(analyses.filter(a => a.id !== id));
    } catch (error) {
      console.error('Failed to delete analysis:', error);
      alert('Failed to delete analysis. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-background relative">
      {/* Background image with AspectRatio */}
      <div className="fixed inset-0 w-full h-full z-0">
        <div className="w-full h-full overflow-hidden">
          <AspectRatio ratio={16 / 9} className="w-full h-full">
            <img
              src="https://images.unsplash.com/photo-1588345921523-c2dcdb7f1dcd?w=800&dpr=2&q=80"
              alt="Background"
              className="w-full h-full object-cover brightness-110 blur-lg"
              style={{ transform: 'scale(1.1)' }} // Ensures blur doesn't show edges
            />
          </AspectRatio>
        </div>
      </div>
      
      <div className="relative z-10">
        <Header />
        
        <main className="container mx-auto py-8 px-4 max-w-4xl">
          <div className="space-y-8">
            <StartExploringForm onAnalyze={handleAnalyze} />
            
            <div className="bg-white/80 backdrop-blur-sm rounded-lg p-6 border border-black/10">
              <h2 className="text-xl font-semibold mb-4">Analysis History</h2>
              {isLoadingHistory ? (
                <p className="text-muted-foreground text-center py-8">Loading analysis history...</p>
              ) : (
                <AnalysisHistory 
                  analyses={analyses} 
                  onDeleteAnalysis={handleDeleteAnalysis}
                  darkMode={false}
                />
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App; 