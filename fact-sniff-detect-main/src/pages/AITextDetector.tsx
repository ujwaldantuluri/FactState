
import { useState } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { FileText, Search, AlertTriangle, CheckCircle, XCircle, FileBarChart, Users, Brain } from "lucide-react";
import { toast } from "sonner";

const AITextDetector = () => {
  const [textContent, setTextContent] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [results, setResults] = useState<any>(null);

  const handleScan = async () => {
    if (!textContent.trim()) {
      toast.error("Please enter text content to analyze");
      return;
    }

    setIsScanning(true);
    toast.info("Analyzing text for AI generation...");

    setTimeout(() => {
      const mockResults = {
        verdict: Math.random() > 0.6 ? 'Suspicious' : Math.random() > 0.3 ? 'Human Written' : 'AI Generated',
        riskScore: Math.floor(Math.random() * 100),
        analysis: {
          languagePatterns: Math.floor(Math.random() * 100),
          sentenceStructure: Math.floor(Math.random() * 100),
          vocabularyVariation: Math.floor(Math.random() * 100),
          stylisticConsistency: Math.floor(Math.random() * 100),
        },
        textStats: {
          wordCount: textContent.split(' ').length,
          sentenceCount: textContent.split(/[.!?]+/).length - 1,
          readabilityScore: Math.floor(Math.random() * 100),
          averageWordsPerSentence: Math.round(textContent.split(' ').length / (textContent.split(/[.!?]+/).length - 1)) || 0,
        },
        flags: [
          { type: 'Repetitive Patterns', status: Math.random() > 0.5 ? 'pass' : 'warning', description: 'Unusual repetition of phrases or structures' },
          { type: 'Vocabulary Complexity', status: Math.random() > 0.5 ? 'pass' : 'fail', description: 'Consistency in vocabulary sophistication' },
          { type: 'Sentence Flow', status: Math.random() > 0.5 ? 'pass' : 'warning', description: 'Natural progression and coherence' },
          { type: 'AI Model Signatures', status: Math.random() > 0.5 ? 'pass' : 'fail', description: 'Characteristic patterns of AI text generation' },
        ]
      };
      
      setResults(mockResults);
      setIsScanning(false);
      toast.success("Text analysis complete!");
    }, 3000);
  };

  const getVerdictColor = (verdict: string) => {
    switch (verdict) {
      case 'Human Written':
        return 'text-emerald-600 bg-emerald-50 border-emerald-200 dark:bg-emerald-900/20 dark:border-emerald-800';
      case 'Suspicious':
        return 'text-amber-600 bg-amber-50 border-amber-200 dark:bg-amber-900/20 dark:border-amber-800';
      case 'AI Generated':
        return 'text-red-600 bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800';
      default:
        return 'text-slate-600 bg-slate-50 border-slate-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pass':
        return <CheckCircle className="w-4 h-4 text-emerald-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-amber-500" />;
      case 'fail':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl mx-auto">
            <FileText className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
              📝 AI Text Detector
            </h1>
            <p className="text-slate-600 dark:text-slate-400 text-lg">
              Distinguish between human-written and AI-generated text content
            </p>
          </div>
        </div>

        {/* Input Section */}
        <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
          <CardHeader>
            <CardTitle className="text-slate-900 dark:text-white">Text to Analyze</CardTitle>
            <CardDescription>
              Paste the text content you want to check for AI generation
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label className="text-slate-700 dark:text-slate-300 font-medium">
                Text Content
              </Label>
              <Textarea
                placeholder="Paste your text here to analyze whether it was written by AI or human. The analysis will examine language patterns, sentence structure, vocabulary usage, and other linguistic features to determine the likelihood of AI generation..."
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
                className="bg-white/50 dark:bg-slate-700/50 min-h-[200px] resize-none"
              />
              <div className="flex justify-between text-sm text-slate-500">
                <span>{textContent.length} characters</span>
                <span>{textContent.split(' ').filter(word => word.length > 0).length} words</span>
              </div>
            </div>

            <Button
              onClick={handleScan}
              disabled={isScanning || textContent.trim().length < 50}
              className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-semibold py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
            >
              {isScanning ? (
                <>
                  <Search className="w-5 h-5 mr-2 animate-pulse" />
                  Analyzing Text...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5 mr-2" />
                  Detect AI Generation
                </>
              )}
            </Button>
            {textContent.trim().length < 50 && textContent.length > 0 && (
              <p className="text-sm text-amber-600 text-center">
                Please enter at least 50 characters for accurate analysis
              </p>
            )}
          </CardContent>
        </Card>

        {/* Loading */}
        {isScanning && (
          <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
            <CardContent className="py-12">
              <div className="text-center space-y-4">
                <div className="w-16 h-16 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full mx-auto flex items-center justify-center animate-pulse">
                  <Brain className="w-8 h-8 text-white" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                    Analyzing Text Patterns...
                  </h3>
                  <p className="text-slate-600 dark:text-slate-400">
                    Examining language patterns, structure, and AI generation signatures
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Results */}
        {results && (
          <div className="space-y-6 animate-fade-in">
            {/* Verdict */}
            <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
              <CardContent className="py-8">
                <div className="text-center space-y-4">
                  <div className={`inline-flex items-center gap-2 px-6 py-3 rounded-full text-lg font-semibold border-2 ${getVerdictColor(results.verdict)}`}>
                    {results.verdict === 'Human Written' && <CheckCircle className="w-6 h-6" />}
                    {results.verdict === 'Suspicious' && <AlertTriangle className="w-6 h-6" />}
                    {results.verdict === 'AI Generated' && <XCircle className="w-6 h-6" />}
                    {results.verdict}
                  </div>
                  <div className="space-y-2">
                    <div className="text-4xl font-bold text-slate-900 dark:text-white">
                      {results.riskScore}%
                    </div>
                    <div className="text-slate-600 dark:text-slate-400">
                      AI Generation Probability
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Analysis & Text Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Analysis Metrics */}
              <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
                <CardHeader>
                  <CardTitle className="text-slate-900 dark:text-white">Linguistic Analysis</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {Object.entries(results.analysis).map(([key, value]) => (
                    <div key={key} className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm font-medium text-slate-700 dark:text-slate-300 capitalize">
                          {key.replace(/([A-Z])/g, ' $1').trim()}
                        </span>
                        <span className="text-sm font-semibold text-slate-900 dark:text-white">
                          {value}%
                        </span>
                      </div>
                      <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-indigo-500 to-purple-600 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${value}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Text Statistics */}
              <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
                <CardHeader>
                  <CardTitle className="text-slate-900 dark:text-white">Text Statistics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center gap-3">
                    <FileText className="w-5 h-5 text-slate-400" />
                    <div>
                      <div className="text-sm font-medium text-slate-900 dark:text-white">Word Count</div>
                      <div className="text-sm text-slate-600 dark:text-slate-400">{results.textStats.wordCount.toLocaleString()}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <FileBarChart className="w-5 h-5 text-slate-400" />
                    <div>
                      <div className="text-sm font-medium text-slate-900 dark:text-white">Sentences</div>
                      <div className="text-sm text-slate-600 dark:text-slate-400">{results.textStats.sentenceCount}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Brain className="w-5 h-5 text-slate-400" />
                    <div>
                      <div className="text-sm font-medium text-slate-900 dark:text-white">Readability Score</div>
                      <div className="text-sm text-slate-600 dark:text-slate-400">{results.textStats.readabilityScore}/100</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Users className="w-5 h-5 text-slate-400" />
                    <div>
                      <div className="text-sm font-medium text-slate-900 dark:text-white">Avg Words/Sentence</div>
                      <div className="text-sm text-slate-600 dark:text-slate-400">{results.textStats.averageWordsPerSentence}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Analysis Flags */}
            <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
              <CardHeader>
                <CardTitle className="text-slate-900 dark:text-white">Detection Analysis</CardTitle>
                <CardDescription>
                  Advanced linguistic analysis for AI text generation detection
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {results.flags.map((flag: any, index: number) => (
                    <div key={index} className="flex items-start gap-3 p-4 rounded-lg bg-slate-50/50 dark:bg-slate-700/50">
                      {getStatusIcon(flag.status)}
                      <div className="flex-1">
                        <div className="font-medium text-slate-900 dark:text-white mb-1">
                          {flag.type}
                        </div>
                        <div className="text-sm text-slate-600 dark:text-slate-400">
                          {flag.description}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default AITextDetector;
