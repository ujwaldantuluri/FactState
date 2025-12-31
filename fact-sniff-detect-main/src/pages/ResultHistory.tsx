
import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { History, Search, Filter, Calendar, Download, Eye, Trash2 } from "lucide-react";
import { API_ENDPOINTS } from "@/lib/api";

type HistoryItem = {
  id: string
  type: string
  content: string
  url: string | null
  verdict: string
  riskScore: number
  timestamp: string
  icon?: string
}

const ResultHistory = () => {
  const [results, setResults] = useState<HistoryItem[]>([])
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterVerdict, setFilterVerdict] = useState('all');
  const [deletingId, setDeletingId] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      try {
        const res = await fetch(`${API_ENDPOINTS.DASHBOARD.HISTORY}?limit=200`)
        if (!res.ok) throw new Error("Failed to load history")
        const json = await res.json()
        if (cancelled) return
        setResults(Array.isArray(json?.items) ? json.items : [])
      } catch {
        if (!cancelled) setResults([])
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [])

  const handleDelete = async (id: string) => {
    if (!id) return
    setDeletingId(id)
    try {
      const res = await fetch(`${API_ENDPOINTS.DASHBOARD.HISTORY}/${encodeURIComponent(id)}`, {
        method: "DELETE",
      })
      if (!res.ok) throw new Error("Delete failed")
      setResults(prev => prev.filter(r => r.id !== id))
    } catch {
      // Keep UI simple; failures leave the item visible.
    } finally {
      setDeletingId(prev => (prev === id ? null : prev))
    }
  }

  const getVerdictColor = (verdict: string) => {
    switch (verdict) {
      case 'Safe':
      case 'Authentic':
      case 'Human Made':
      case 'Human Written':
        return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300';
      case 'Suspicious':
        return 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300';
      case 'Fake':
      case 'Scam':
      case 'AI Generated':
      case 'Deepfake':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300';
      default:
        return 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300';
    }
  };

  const getRiskScoreColor = (score: number) => {
    if (score < 30) return 'text-emerald-600';
    if (score < 70) return 'text-amber-600';
    return 'text-red-600';
  };

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const filteredResults = results.filter(result => {
    const matchesSearch = result.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         result.type.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || result.type.toLowerCase().includes(filterType.toLowerCase());
    const matchesVerdict = filterVerdict === 'all' || result.verdict.toLowerCase() === filterVerdict.toLowerCase();
    
    return matchesSearch && matchesType && matchesVerdict;
  });

  return (
    <DashboardLayout>
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center w-16 h-16 bg-gradient-to-br from-slate-600 to-slate-700 rounded-2xl mx-auto">
            <History className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
              📊 Scan History
            </h1>
            <p className="text-slate-600 dark:text-slate-400 text-lg">
              Review and manage your previous content analysis results
            </p>
          </div>
        </div>

        {/* Filters */}
        <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
          <CardHeader>
            <CardTitle className="text-slate-900 dark:text-white">Filter Results</CardTitle>
            <CardDescription>
              Search and filter your analysis history
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    placeholder="Search by content or type..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 bg-white/50 dark:bg-slate-700/50"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <Select value={filterType} onValueChange={setFilterType}>
                  <SelectTrigger className="w-40 bg-white/50 dark:bg-slate-700/50">
                    <SelectValue placeholder="All Types" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="fake news">Fake News</SelectItem>
                    <SelectItem value="e-commerce">E-commerce</SelectItem>
                    <SelectItem value="job">Job Posting</SelectItem>
                    <SelectItem value="social">Social Media</SelectItem>
                    <SelectItem value="ai image">AI Image</SelectItem>
                    <SelectItem value="ai text">AI Text</SelectItem>
                    <SelectItem value="video">Video Content</SelectItem>
                  </SelectContent>
                </Select>

                <Select value={filterVerdict} onValueChange={setFilterVerdict}>
                  <SelectTrigger className="w-40 bg-white/50 dark:bg-slate-700/50">
                    <SelectValue placeholder="All Results" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Results</SelectItem>
                    <SelectItem value="safe">Safe/Authentic</SelectItem>
                    <SelectItem value="suspicious">Suspicious</SelectItem>
                    <SelectItem value="fake">Fake/Scam</SelectItem>
                  </SelectContent>
                </Select>

                <Button variant="outline" className="bg-white/50 dark:bg-slate-700/50">
                  <Download className="w-4 h-4 mr-2" />
                  Export
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        <div className="space-y-4">
          {filteredResults.length === 0 ? (
            <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
              <CardContent className="py-12">
                <div className="text-center space-y-4">
                  <div className="w-16 h-16 bg-slate-100 dark:bg-slate-700 rounded-full mx-auto flex items-center justify-center">
                    <Search className="w-8 h-8 text-slate-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                      No results found
                    </h3>
                    <p className="text-slate-600 dark:text-slate-400">
                      Try adjusting your search terms or filters
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            filteredResults.map((result) => (
              <Card key={result.id} className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20 hover:shadow-lg transition-all duration-200">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4 flex-1">
                      <div className="text-2xl">{(result as any).icon || '📊'}</div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-semibold text-slate-900 dark:text-white">
                            {result.type}
                          </h3>
                          <Badge className={`${getVerdictColor(result.verdict)} border-0`}>
                            {result.verdict}
                          </Badge>
                        </div>
                        <p className="text-slate-600 dark:text-slate-400 mb-2 truncate">
                          {result.content}
                        </p>
                        {result.url && (
                          <p className="text-sm text-slate-500 truncate">
                            {result.url}
                          </p>
                        )}
                        <div className="flex items-center gap-4 mt-3 text-sm text-slate-500">
                          <div className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {formatDate(result.timestamp)}
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4 ml-4">
                      <div className="text-right">
                        <div className={`text-2xl font-bold ${getRiskScoreColor(result.riskScore)}`}>
                          {result.riskScore}%
                        </div>
                        <div className="text-xs text-slate-500">Risk Score</div>
                      </div>
                      
                      <div className="flex gap-2">
                        <Button variant="ghost" size="sm" className="hover:bg-primary/10">
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="hover:bg-red-100 dark:hover:bg-red-900/20 text-red-600"
                          onClick={() => handleDelete(result.id)}
                          disabled={deletingId === result.id}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Pagination */}
        {filteredResults.length > 0 && (
          <div className="flex justify-center">
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" disabled className="bg-white/50 dark:bg-slate-700/50">
                Previous
              </Button>
              <div className="flex gap-1">
                <Button variant="default" size="sm" className="w-8 h-8 text-xs">1</Button>
                <Button variant="outline" size="sm" className="w-8 h-8 text-xs bg-white/50 dark:bg-slate-700/50">2</Button>
                <Button variant="outline" size="sm" className="w-8 h-8 text-xs bg-white/50 dark:bg-slate-700/50">3</Button>
              </div>
              <Button variant="outline" size="sm" className="bg-white/50 dark:bg-slate-700/50">
                Next
              </Button>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default ResultHistory;
