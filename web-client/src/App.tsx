import { useState, useEffect } from 'react';
import Header from './components/Header';
import StartExploringForm from './components/StartExploringForm';
import AnalysisHistory from './components/AnalysisHistory';
import { AspectRatio } from "./components/ui/aspect-ratio";
import { analysisService, AnalyzeRequest, AnalysisResponse } from "./services/analysis";
import { AnalysisResponseStatusEnum } from "@/generated/api/models/analysis-response";

// Use OpenAPI generated types directly - no local interfaces needed

function App() {
  const [analyses, setAnalyses] = useState<AnalysisResponse[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [loadingMessage, setLoadingMessage] = useState<string>('');

  const handleAnalyze = async (req: AnalyzeRequest): Promise<void> => {
    return new Promise<void>(async (resolve) => {
      try {
        setLoadingMessage('Starting analysis...');
        const analysisId = await analysisService.startAnalysis(req);
        const pollInterval = 2000;
        const maxWaitMs = 120000;
        const startTs = Date.now();

        const poll = async () => {
          try {
            const details = await analysisService.getAnalysis(analysisId);
            setLoadingMessage(details.status as string || 'Polling...');
            if (details.status === AnalysisResponseStatusEnum.Completed || details.status === AnalysisResponseStatusEnum.Failed) {
              const historyData = await analysisService.getAnalyses(20);
              setAnalyses(historyData);
              setLoadingMessage('');
              resolve();
              return;
            }
          } catch (err) {
            console.error('Polling failed', err);
          }
          if (Date.now() - startTs < maxWaitMs) {
            setTimeout(poll, pollInterval);
          } else {
            setLoadingMessage('');
            resolve();
          }
        };

        poll();
      } catch (err) {
        console.error('Analysis failed', err);
        alert('Failed to start analysis. Please try again.');
        setLoadingMessage('');
        resolve();
      }
    });
  };

  // Load analysis history from database on component mount
  useEffect(() => {
    const loadAnalysisHistory = async () => {
      try {
        setIsLoadingHistory(true);
        const historyData = await analysisService.getAnalyses(20);
        setAnalyses(historyData);
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
      await analysisService.deleteAnalysis(id);
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
            <StartExploringForm onAnalyze={handleAnalyze} loadingMessage={loadingMessage} />

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
