import { useEffect, useState } from "react";
import { AnalysisResults, Resort } from "@/types";
import { calcAverages } from "@/lib/calc-averages";
import { ResortCard } from "@/components/ResortCard";
import { Mountain, Clock } from "lucide-react";

// Configure this to your CloudFront distribution URL
const DATA_URL = import.meta.env.VITE_DATA_URL || "/analysis_results.json";

function App() {
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(DATA_URL);
      if (!response.ok) {
        throw new Error(`Failed to fetch: ${response.status}`);
      }
      const data: AnalysisResults = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Sort resorts by composite score
  const sortedResorts: Resort[] = results
    ? [...results.resorts].sort((a, b) => {
        const avgA = calcAverages(a.cameras);
        const avgB = calcAverages(b.cameras);
        return avgB.composite - avgA.composite;
      })
    : [];

  return (
    <div className="min-h-screen bg-gray-50 relative">
      {/* Background images - hidden on mobile, visible on larger screens */}
      <div
        className="hidden xl:block fixed left-0 top-0 h-full bg-cover bg-center opacity-30 pointer-events-none"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1605540436563-5bca919ae766?w=2160&q=90')`,
          width: 'calc(50% - 522px)',
        }}
      />
      <div
        className="hidden xl:block fixed right-0 top-0 h-full bg-cover bg-center opacity-30 pointer-events-none"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1491002052546-bf38f186af56?w=2160&q=90')`,
          width: 'calc(50% - 522px)',
        }}
      />

      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Mountain className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-2xl font-bold">PNW Resort Conditions</h1>
                <p className="text-sm text-muted-foreground">AI-powered webcam analysis to help you decide which resort to visit · Updated every 10 mins</p>
              </div>
            </div>
            <div className="flex items-center">
              <span className="text-sm text-muted-foreground mr-2">Vision AI by</span>
              <a href="https://perceptron.inc" target="_blank" rel="noopener noreferrer">
                <img
                  src="https://mintcdn.com/perceptron/CuyGah1e2BqRrsVm/logo/perceptron-full-logo-dark.svg?fit=max&auto=format&n=CuyGah1e2BqRrsVm&q=85&s=859b1eeb3fa33674275135e6590684df"
                  alt="Perceptron"
                  className="h-6 brightness-0"
                />
              </a>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        {results?.updated_at && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-6">
            <Clock className="h-4 w-4" />
            <span>
              Last updated:{" "}
              {new Date(results.updated_at).toLocaleString(undefined, {
                dateStyle: "medium",
                timeStyle: "short",
              })}
            </span>
          </div>
        )}

        {loading && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">Loading resort data...</p>
          </div>
        )}

        {error && (
          <div className="text-center py-12">
            <p className="text-red-500">Error: {error}</p>
            <button
              onClick={fetchData}
              className="mt-4 px-4 py-2 rounded-md bg-primary text-primary-foreground"
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && sortedResorts.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No resort data available.</p>
          </div>
        )}

        {!loading && !error && sortedResorts.length > 0 && (
          <div className="space-y-4">
            {sortedResorts.map((resort, index) => (
              <ResortCard key={resort.resort_key} resort={resort} rank={index + 1} />
            ))}
          </div>
        )}
      </main>

      <footer className="border-t bg-white mt-12">
        <div className="max-w-5xl mx-auto px-4 py-6 text-center text-sm text-muted-foreground">
          <p>All webcam imagery remains the property of the respective ski resorts and is used for informational purposes only.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
