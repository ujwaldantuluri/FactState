import { useState } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { 
  Search, 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Clock,
  ExternalLink,
  Info,
  TrendingUp,
  MessageSquare,
  RefreshCw,
  History
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { API_ENDPOINTS, validateAndFormatUrl, handleApiError } from "@/lib/api";

interface AnalysisReason {
  layer: string;
  message: string;
  weight: number;
  score: number;
}

interface AnalysisResult {
  url: string;
  risk_score: number;
  badge: string;
  reasons: AnalysisReason[];
  advice: {
    payment: string;
    actions: string[];
  };
  scanned_at: string;
  analysis_type: string;
}

interface ComparisonResult {
  url: string;
  basic_analysis: {
    risk_score: number;
    verdict: string;
    checks_count: number;
  };
  advanced_analysis: {
    risk_score: number;
    badge: string;
    layers_count: number;
    has_advice: boolean;
  };
  comparison: {
    score_difference: number;
    analysis_depth: string;
  };
}

const FakeEcommerceDetector = () => {
  const [url, setUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [activeTab, setActiveTab] = useState("detector");
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisResult[]>([]);
  const { toast } = useToast();

  const getBadgeColor = (badge: string) => {
    if (badge.includes("Verified Safe")) return "bg-emerald-500";
    if (badge.includes("Low Risk")) return "bg-green-500";
    if (badge.includes("Caution")) return "bg-yellow-500";
    if (badge.includes("High Risk")) return "bg-orange-500";
    if (badge.includes("Critical")) return "bg-red-500";
    return "bg-slate-500";
  };

  const getBadgeIcon = (badge: string) => {
    if (badge.includes("Verified Safe")) return <Shield className="w-4 h-4" />;
    if (badge.includes("Low Risk")) return <CheckCircle className="w-4 h-4" />;
    if (badge.includes("Caution")) return <AlertTriangle className="w-4 h-4" />;
    if (badge.includes("High Risk")) return <XCircle className="w-4 h-4" />;
    if (badge.includes("Critical")) return <XCircle className="w-4 h-4" />;
    return <Info className="w-4 h-4" />;
  };

  // Removed per request: layer-by-layer UI helpers

  const analyzeWebsite = async (analysisType: "basic" | "advanced" = "advanced") => {
    if (!url.trim()) {
      toast({
        title: "Error",
        description: "Please enter a website URL",
        variant: "destructive",
      });
      return;
    }

    // Validate and format URL
    let formattedUrl: string;
    try {
      formattedUrl = validateAndFormatUrl(url);
    } catch (error) {
      toast({
        title: "Invalid URL",
        description: handleApiError(error),
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);

    try {
      const endpoint = analysisType === "basic" 
        ? API_ENDPOINTS.ECOMMERCE.ANALYZE_BASIC
        : API_ENDPOINTS.ECOMMERCE.ANALYZE_ADVANCED;

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: formattedUrl }),
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

  const data: AnalysisResult = await response.json();
      setResult(data);
      
      // Add to history
      setAnalysisHistory(prev => [data, ...prev.slice(0, 9)]);

      toast({
        title: "Analysis Complete",
        description: `Website analyzed${data.analysis_type ? ` with ${data.analysis_type} method` : ''}`,
      });

    } catch (error) {
      console.error("Analysis error:", error);
      toast({
        title: "Analysis Failed",
        description: handleApiError(error),
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const compareAnalysis = async () => {
    if (!url.trim()) {
      toast({
        title: "Error",
        description: "Please enter a website URL",
        variant: "destructive",
      });
      return;
    }

    let formattedUrl: string;
    try {
      formattedUrl = validateAndFormatUrl(url);
    } catch (error) {
      toast({
        title: "Invalid URL",
        description: handleApiError(error),
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(`${API_ENDPOINTS.ECOMMERCE.COMPARE}?url=${encodeURIComponent(formattedUrl)}`);

      if (!response.ok) {
        throw new Error(`Comparison failed: ${response.statusText}`);
      }

      const data: ComparisonResult = await response.json();
      setComparison(data);

      toast({
        title: "Comparison Complete",
        description: "Basic vs Advanced analysis completed",
      });

    } catch (error) {
      console.error("Comparison error:", error);
      toast({
        title: "Comparison Failed",
        description: handleApiError(error),
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const submitFeedback = async (delivered: boolean) => {
    if (!result?.url) return;

    try {
      const response = await fetch(API_ENDPOINTS.ECOMMERCE.FEEDBACK, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: result.url,
          delivered,
          order_hash: `order_${Date.now()}`
        }),
      });

      if (response.ok) {
        toast({
          title: "Feedback Submitted",
          description: "Thank you for your feedback!",
        });
      }
    } catch (error) {
      console.error("Feedback error:", error);
      toast({
        title: "Feedback Error",
        description: "Failed to submit feedback",
        variant: "destructive",
      });
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-gradient-to-r from-white/70 to-orange-50/70 dark:from-slate-800/70 dark:to-orange-900/70 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 rounded-xl bg-gradient-to-br from-orange-50 to-red-100 dark:from-orange-900/20 dark:to-red-800/20">
              <Shield className="w-8 h-8 text-orange-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
                Advanced E-commerce Detection
              </h1>
              <p className="text-slate-600 dark:text-slate-400">
                Comprehensive 8-layer analysis for e-commerce website verification
              </p>
            </div>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="detector">Advanced Analysis</TabsTrigger>
            <TabsTrigger value="comparison">Compare Methods</TabsTrigger>
            <TabsTrigger value="history">Analysis History</TabsTrigger>
          </TabsList>

          <TabsContent value="detector" className="space-y-6">
            {/* Input Section */}
            <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Search className="w-5 h-5" />
                  Website Analysis
                </CardTitle>
                <CardDescription>
                  Enter an e-commerce website URL for comprehensive fraud detection analysis
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex gap-3">
                  <Input
                    placeholder="https://example-store.com"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    className="flex-1"
                    onKeyPress={(e) => e.key === 'Enter' && analyzeWebsite('advanced')}
                  />
                  <Button 
                    onClick={() => analyzeWebsite('advanced')}
                    disabled={isLoading}
                    className="bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700"
                  >
                    {isLoading ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Search className="w-4 h-4" />
                    )}
                    Analyze
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Results */}
            {result && (
              <div className="space-y-6">
                {/* Overall Result */}
                <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center gap-2">
                        {getBadgeIcon(result.badge)}
                        Analysis Result
                      </CardTitle>
                      <Badge className={`${getBadgeColor(result.badge)} text-white`}>
                        {result.badge}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-lg font-medium">Risk Score</span>
                      <span className="text-2xl font-bold">{result.risk_score.toFixed(1)}/100</span>
                    </div>
                    <Progress value={result.risk_score} className="h-3" />
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                      <div>
                        <h4 className="font-medium mb-2">Payment Recommendation</h4>
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                          {result.advice.payment}
                        </p>
                      </div>
                      <div>
                        <h4 className="font-medium mb-2">Recommended Actions</h4>
                        <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-1">
                          {result.advice.actions.map((action, index) => (
                            <li key={index}>• {action}</li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 text-sm text-slate-500">
                      <Clock className="w-4 h-4" />
                      Analyzed on {new Date(result.scanned_at).toLocaleString()}
                    </div>
                  </CardContent>
                </Card>

                {/* Layer-by-Layer Analysis removed per request */}

                {/* Feedback Section */}
                <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <MessageSquare className="w-5 h-5" />
                      Help Improve Our Analysis
                    </CardTitle>
                    <CardDescription>
                      If you've purchased from this website, let us know about your experience
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex gap-3">
                      <Button 
                        variant="outline" 
                        onClick={() => submitFeedback(true)}
                        className="flex-1"
                      >
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Order Delivered Successfully
                      </Button>
                      <Button 
                        variant="outline" 
                        onClick={() => submitFeedback(false)}
                        className="flex-1"
                      >
                        <XCircle className="w-4 h-4 mr-2" />
                        Had Issues / Scam
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          <TabsContent value="comparison" className="space-y-6">
            <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Analysis Method Comparison
                </CardTitle>
                <CardDescription>
                  Compare basic and advanced analysis methods side by side
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex gap-3 mb-6">
                  <Input
                    placeholder="https://example-store.com"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    className="flex-1"
                  />
                  <Button 
                    onClick={compareAnalysis}
                    disabled={isLoading}
                    className="bg-gradient-to-r from-blue-500 to-purple-600"
                  >
                    {isLoading ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      "Compare"
                    )}
                  </Button>
                </div>

                {comparison && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <h3 className="text-lg font-medium">Basic Analysis</h3>
                      <div className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span>Risk Score</span>
                          <span className="font-bold">{comparison.basic_analysis.risk_score.toFixed(1)}</span>
                        </div>
                        <Progress value={comparison.basic_analysis.risk_score} className="mb-3" />
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                          Verdict: {comparison.basic_analysis.verdict} • Checks: {comparison.basic_analysis.checks_count}
                        </p>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <h3 className="text-lg font-medium">Advanced Analysis</h3>
                      <div className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span>Risk Score</span>
                          <span className="font-bold">{comparison.advanced_analysis.risk_score.toFixed(1)}</span>
                        </div>
                        <Badge className={`${getBadgeColor(comparison.advanced_analysis.badge)} text-white mb-3`}>
                          {comparison.advanced_analysis.badge}
                        </Badge>
                        <Progress value={comparison.advanced_analysis.risk_score} className="mb-3" />
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                          Layers: {comparison.advanced_analysis.layers_count} • Advice: {comparison.advanced_analysis.has_advice ? 'Yes' : 'No'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="history" className="space-y-6">
            <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <History className="w-5 h-5" />
                  Analysis History
                </CardTitle>
                <CardDescription>
                  Previous website analysis results
                </CardDescription>
              </CardHeader>
              <CardContent>
                {analysisHistory.length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    No analysis history yet. Start by analyzing a website!
                  </div>
                ) : (
                  <div className="space-y-4">
                    {analysisHistory.map((item, index) => (
                      <div key={index} className="border rounded-lg p-4 hover:bg-slate-50/50 dark:hover:bg-slate-700/50 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <ExternalLink className="w-4 h-4" />
                            <span className="font-medium truncate">{item.url}</span>
                          </div>
                          <Badge className={`${getBadgeColor(item.badge)} text-white`}>
                            {item.badge}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between text-sm text-slate-600 dark:text-slate-400">
                          <span>Risk Score: {item.risk_score.toFixed(1)}/100</span>
                          <span>{new Date(item.scanned_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
};

export default FakeEcommerceDetector;
