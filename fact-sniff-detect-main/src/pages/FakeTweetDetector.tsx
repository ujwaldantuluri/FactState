
import { useState } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { MessageSquare, Link2, FileText, Search, AlertTriangle, CheckCircle, XCircle, User, Calendar, Heart, MessageCircle } from "lucide-react";
import { toast } from "sonner";

const FakeTweetDetector = () => {
  const [inputType, setInputType] = useState<'url' | 'text'>('url');
  const [inputValue, setInputValue] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [results, setResults] = useState<any>(null);

  const handleScan = async () => {
    if (!inputValue.trim()) {
      toast.error("Please enter a tweet URL or content to analyze");
      return;
    }

    setIsScanning(true);
    toast.info("Analyzing social media content...");

    setTimeout(() => {
      const mockResults = {
        verdict: Math.random() > 0.6 ? 'Suspicious' : Math.random() > 0.3 ? 'Authentic' : 'Fake',
        riskScore: Math.floor(Math.random() * 100),
        analysis: {
          accountVerification: Math.floor(Math.random() * 100),
          contentAuthenticity: Math.floor(Math.random() * 100),
          engagementPattern: Math.floor(Math.random() * 100),
          languageAnalysis: Math.floor(Math.random() * 100),
        },
        socialMetrics: {
          followers: '12.3K',
          following: '1.2K',
          likes: '45',
          retweets: '12',
        },
        flags: [
          { type: 'Account Age', status: Math.random() > 0.5 ? 'pass' : 'warning', description: 'Account creation date and activity history' },
          { type: 'Bot Detection', status: Math.random() > 0.5 ? 'pass' : 'fail', description: 'Automated behavior pattern analysis' },
          { type: 'Content Analysis', status: Math.random() > 0.5 ? 'pass' : 'warning', description: 'Text authenticity and manipulation detection' },
          { type: 'Network Analysis', status: Math.random() > 0.5 ? 'pass' : 'fail', description: 'Follower quality and interaction patterns' },
        ]
      };
      
      setResults(mockResults);
      setIsScanning(false);
      toast.success("Social media analysis complete!");
    }, 3000);
  };

  const getVerdictColor = (verdict: string) => {
    switch (verdict) {
      case 'Authentic':
        return 'text-emerald-600 bg-emerald-50 border-emerald-200 dark:bg-emerald-900/20 dark:border-emerald-800';
      case 'Suspicious':
        return 'text-amber-600 bg-amber-50 border-amber-200 dark:bg-amber-900/20 dark:border-amber-800';
      case 'Fake':
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
          <div className="flex items-center justify-center w-16 h-16 bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl mx-auto">
            <MessageSquare className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
              🐦 Fake Tweet Detector
            </h1>
            <p className="text-slate-600 dark:text-slate-400 text-lg">
              Verify authenticity of social media posts and detect manipulation
            </p>
          </div>
        </div>

        {/* Input Section */}
        <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
          <CardHeader>
            <CardTitle className="text-slate-900 dark:text-white">Social Media Content</CardTitle>
            <CardDescription>
              Enter a tweet URL or paste the social media content
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Input Type Toggle */}
            <div className="flex gap-2 p-1 bg-slate-100 dark:bg-slate-700 rounded-lg">
              <Button
                variant={inputType === 'url' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setInputType('url')}
                className="flex-1"
              >
                <Link2 className="w-4 h-4 mr-2" />
                URL
              </Button>
              <Button
                variant={inputType === 'text' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setInputType('text')}
                className="flex-1"
              >
                <FileText className="w-4 h-4 mr-2" />
                Content
              </Button>
            </div>

            {/* Input Field */}
            <div className="space-y-2">
              <Label className="text-slate-700 dark:text-slate-300 font-medium">
                {inputType === 'url' ? 'Tweet/Post URL' : 'Social Media Content'}
              </Label>
              {inputType === 'url' ? (
                <Input
                  placeholder="https://twitter.com/user/status/123456789"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  className="bg-white/50 dark:bg-slate-700/50"
                />
              ) : (
                <Textarea
                  placeholder="Paste the social media content here..."
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  className="bg-white/50 dark:bg-slate-700/50 min-h-[100px]"
                />
              )}
            </div>

            <Button
              onClick={handleScan}
              disabled={isScanning}
              className="w-full bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white font-semibold py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
            >
              {isScanning ? (
                <>
                  <Search className="w-5 h-5 mr-2 animate-pulse" />
                  Analyzing Content...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5 mr-2" />
                  Check Authenticity
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Loading */}
        {isScanning && (
          <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
            <CardContent className="py-12">
              <div className="text-center space-y-4">
                <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-purple-600 rounded-full mx-auto flex items-center justify-center animate-pulse">
                  <MessageSquare className="w-8 h-8 text-white" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                    Analyzing Social Content...
                  </h3>
                  <p className="text-slate-600 dark:text-slate-400">
                    Checking account authenticity, engagement patterns, and content manipulation
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
                    {results.verdict === 'Authentic' && <CheckCircle className="w-6 h-6" />}
                    {results.verdict === 'Suspicious' && <AlertTriangle className="w-6 h-6" />}
                    {results.verdict === 'Fake' && <XCircle className="w-6 h-6" />}
                    {results.verdict}
                  </div>
                  <div className="space-y-2">
                    <div className="text-4xl font-bold text-slate-900 dark:text-white">
                      {results.riskScore}%
                    </div>
                    <div className="text-slate-600 dark:text-slate-400">
                      Risk Score
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Analysis & Social Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Analysis Metrics */}
              <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
                <CardHeader>
                  <CardTitle className="text-slate-900 dark:text-white">Analysis Breakdown</CardTitle>
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
                          className="bg-gradient-to-r from-purple-500 to-purple-600 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${value}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Social Metrics */}
              <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
                <CardHeader>
                  <CardTitle className="text-slate-900 dark:text-white">Social Metrics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center gap-3">
                    <User className="w-5 h-5 text-slate-400" />
                    <div>
                      <div className="text-sm font-medium text-slate-900 dark:text-white">Followers</div>
                      <div className="text-sm text-slate-600 dark:text-slate-400">{results.socialMetrics.followers}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <User className="w-5 h-5 text-slate-400" />
                    <div>
                      <div className="text-sm font-medium text-slate-900 dark:text-white">Following</div>
                      <div className="text-sm text-slate-600 dark:text-slate-400">{results.socialMetrics.following}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Heart className="w-5 h-5 text-slate-400" />
                    <div>
                      <div className="text-sm font-medium text-slate-900 dark:text-white">Likes</div>
                      <div className="text-sm text-slate-600 dark:text-slate-400">{results.socialMetrics.likes}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <MessageCircle className="w-5 h-5 text-slate-400" />
                    <div>
                      <div className="text-sm font-medium text-slate-900 dark:text-white">Retweets</div>
                      <div className="text-sm text-slate-600 dark:text-slate-400">{results.socialMetrics.retweets}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Verification Flags */}
            <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
              <CardHeader>
                <CardTitle className="text-slate-900 dark:text-white">Authenticity Checks</CardTitle>
                <CardDescription>
                  Comprehensive social media verification analysis
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

export default FakeTweetDetector;
