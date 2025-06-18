import { useState } from 'react';
import Header from './components/Header';
import StartExploringForm from './components/StartExploringForm';
import AnalysisHistory from './components/AnalysisHistory';
import { AnalysisItemData } from './components/AnalysisItem';
import { AspectRatio } from "./components/ui/aspect-ratio";
import { analyze, AnalyzeRequest } from "./services/analysis";

function App() {
  const [analyses, setAnalyses] = useState<AnalysisItemData[]>([]);

  const handleAnalyze = async (req: AnalyzeRequest) => {
    try {
      const response = await analyze(req);

      const newAnalysis: AnalysisItemData = {
        id: response.id,
        query: response.query,
        timestamp: new Date(response.timestamp).toLocaleString(),
        type: response.type as 'Research' | 'Community',
        trends: response.trends.map((t) => ({
          id: t.id,
          title: t.title,
          description: t.description,
          articleCount: t.articleCount,
          relevance: t.relevance,
          articles: t.articles,
        })),
        feedUrl: response.feedUrl,
      };

      setAnalyses([newAnalysis, ...analyses]);
    } catch (err) {
      console.error("Analysis failed", err);
      alert("Failed to analyze query. Please try again.");
    }
  };

  const handleRefreshAnalysis = (id: string) => {
    // In a real app, this would refresh the specific analysis
    console.log('Refreshing analysis:', id);
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
            <AnalysisHistory 
              items={analyses}
              onRefreshAnalysis={handleRefreshAnalysis}
            />
          </div>
        </main>
      </div>
    </div>
  );
}

export default App; 