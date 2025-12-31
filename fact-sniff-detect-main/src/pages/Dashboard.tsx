import { DashboardLayout } from "@/components/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { API_ENDPOINTS } from "@/lib/api";
import { 
  FileText, 
  AlertTriangle, 
  Search, 
  MessageSquare, 
  Image, 
  TrendingUp,
  Shield,
  Clock,
  Plus
} from "lucide-react";

const detectionServices = [
  {
    icon: FileText,
    title: "Fake News Detection",
    description: "Analyze news articles for misinformation",
    path: "/fake-news",
    color: "from-red-500 to-red-600",
    bgColor: "from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20"
  },
  {
    icon: Shield,
    title: "E-commerce Fraud Detection",
    description: "Advanced 8-layer e-commerce website verification",
    path: "/fake-ecommerce",
    color: "from-orange-500 to-red-600",
    bgColor: "from-orange-50 to-red-100 dark:from-orange-900/20 dark:to-red-800/20"
  },
  {
    icon: Search,
    title: "Job Scam Detection",
    description: "Identify fraudulent job postings",
    path: "/scam-jobs",
    color: "from-blue-500 to-blue-600",
    bgColor: "from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20"
  },
  {
    icon: Image,
    title: "AI Image Detection",
    description: "Spot AI-generated or manipulated images",
    path: "/ai-images",
    color: "from-green-500 to-emerald-600",
    bgColor: "from-green-50 to-emerald-100 dark:from-green-900/20 dark:to-emerald-800/20"
  }
];

type DashboardStats = {
  scansToday: number
  accuracy: number
  totalScans: number
  fakeDetected: number
  safeContent: number
}

type HistoryItem = {
  id: string
  type: string
  content: string
  url: string | null
  verdict: string
  riskScore: number
  timestamp: string
}

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [stats, setStats] = useState<DashboardStats>({
    scansToday: 0,
    accuracy: 0,
    totalScans: 0,
    fakeDetected: 0,
    safeContent: 0,
  })
  const [recentScans, setRecentScans] = useState<HistoryItem[]>([])

  const timeAgo = useMemo(() => {
    return (iso: string) => {
      const then = new Date(iso).getTime()
      const now = Date.now()
      const diffSec = Math.max(0, Math.floor((now - then) / 1000))
      const mins = Math.floor(diffSec / 60)
      const hours = Math.floor(mins / 60)
      const days = Math.floor(hours / 24)
      if (days > 0) return `${days} day${days === 1 ? "" : "s"} ago`
      if (hours > 0) return `${hours} hour${hours === 1 ? "" : "s"} ago`
      if (mins > 0) return `${mins} minute${mins === 1 ? "" : "s"} ago`
      return "just now"
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      try {
        const [statsRes, histRes] = await Promise.all([
          fetch(API_ENDPOINTS.DASHBOARD.STATS),
          fetch(`${API_ENDPOINTS.DASHBOARD.HISTORY}?limit=10`),
        ])

        if (!statsRes.ok) throw new Error("Failed to load stats")
        if (!histRes.ok) throw new Error("Failed to load history")

        const statsJson = await statsRes.json()
        const histJson = await histRes.json()

        if (cancelled) return

        setStats({
          scansToday: Number(statsJson?.scansToday || 0),
          accuracy: Number(statsJson?.accuracy || 0),
          totalScans: Number(statsJson?.totalScans || 0),
          fakeDetected: Number(statsJson?.fakeDetected || 0),
          safeContent: Number(statsJson?.safeContent || 0),
        })
        setRecentScans(Array.isArray(histJson?.items) ? histJson.items : [])
      } catch {
        // Keep dashboard usable even if backend isn't running.
        if (!cancelled) {
          setStats({
            scansToday: 0,
            accuracy: 0,
            totalScans: 0,
            fakeDetected: 0,
            safeContent: 0,
          })
          setRecentScans([])
        }
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [])

  const getResultColor = (result: string) => {
    switch (result) {
      case "Safe":
      case "Verified Safe":
        return "text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20";
      case "Low Risk":
        return "text-green-600 bg-green-50 dark:bg-green-900/20";
      case "Suspicious":
      case "Caution Required":
        return "text-amber-600 bg-amber-50 dark:bg-amber-900/20";
      case "High Risk":
        return "text-orange-600 bg-orange-50 dark:bg-orange-900/20";
      case "Fake":
      case "Critical Risk":
      case "AI Generated":
        return "text-red-600 bg-red-50 dark:bg-red-900/20";
      default:
        return "text-slate-600 bg-slate-50 dark:bg-slate-900/20";
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Welcome Header */}
        <div className="bg-gradient-to-r from-white/70 to-blue-50/70 dark:from-slate-800/70 dark:to-indigo-900/70 backdrop-blur-sm rounded-2xl p-8 border border-white/20">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                Welcome back, {user?.name?.split(' ')[0]}! 👋
              </h1>
              <p className="text-slate-600 dark:text-slate-400 text-lg">
                Ready to detect fake content and verify authenticity?
              </p>
            </div>
            <div className="hidden md:flex items-center gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-primary">{stats.scansToday}</div>
                <div className="text-sm text-slate-500">Scans Today</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-emerald-500">{Math.round(stats.accuracy)}%</div>
                <div className="text-sm text-slate-500">Accuracy</div>
              </div>
            </div>
          </div>
        </div>

        {/* Detection Services Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
          {detectionServices.map((service, index) => (
            <Card 
              key={service.title}
              className="group hover:scale-105 transition-all duration-300 cursor-pointer bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20 hover:shadow-2xl animate-scale-in overflow-hidden"
              style={{ animationDelay: `${index * 100}ms` }}
              onClick={() => navigate(service.path)}
            >
              <div className={`h-2 bg-gradient-to-r ${service.color}`} />
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className={`p-3 rounded-xl bg-gradient-to-br ${service.bgColor}`}>
                    <service.icon className="w-6 h-6 group-hover:scale-110 transition-transform duration-300" />
                  </div>
                  <div>
                    <CardTitle className="text-lg text-slate-900 dark:text-white">
                      {service.title}
                    </CardTitle>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-slate-600 dark:text-slate-400 mb-4">
                  {service.description}
                </CardDescription>
                <Button 
                  size="sm" 
                  className="w-full bg-gradient-to-r from-primary to-indigo-600 hover:from-primary/90 hover:to-indigo-600/90 text-white"
                >
                  Start Detection
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Stats & Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Quick Stats */}
          <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-slate-900 dark:text-white">
                <TrendingUp className="w-5 h-5 text-primary" />
                Quick Stats
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-slate-600 dark:text-slate-400">Total Scans</span>
                <span className="text-xl font-bold text-slate-900 dark:text-white">{stats.totalScans}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-600 dark:text-slate-400">Fake Detected</span>
                <span className="text-xl font-bold text-red-500">{stats.fakeDetected}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-600 dark:text-slate-400">Safe Content</span>
                <span className="text-xl font-bold text-emerald-500">{stats.safeContent}</span>
              </div>
            </CardContent>
          </Card>

          {/* Recent Scans */}
          <Card className="lg:col-span-2 bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-slate-900 dark:text-white">
                <Clock className="w-5 h-5 text-primary" />
                Recent Scans
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentScans.map((scan, index) => (
                  <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-slate-50/50 dark:bg-slate-700/50">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium text-slate-900 dark:text-white">
                          {scan.type}
                        </span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getResultColor(scan.verdict)}`}>
                          {scan.verdict}
                        </span>
                      </div>
                      <p className="text-sm text-slate-600 dark:text-slate-400 truncate">
                        {scan.content}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">{timeAgo(scan.timestamp)}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-slate-900 dark:text-white">
                        {Math.round(scan.riskScore)}%
                      </div>
                      <div className="text-xs text-slate-500">Risk Score</div>
                    </div>
                  </div>
                ))}
              </div>
              <Button 
                variant="outline" 
                className="w-full mt-4 bg-white/50 dark:bg-slate-700/50"
                onClick={() => navigate('/history')}
              >
                View All History
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Floating Action Button */}
        <Button
          size="lg"
          className="fixed bottom-8 right-8 w-16 h-16 rounded-full bg-primary hover:bg-primary/90 shadow-2xl hover:shadow-3xl transition-all duration-300 animate-pulse-glow z-20"
          onClick={() => navigate('/fake-news')}
        >
          <Plus className="w-8 h-8 text-white" />
        </Button>
      </div>
    </DashboardLayout>
  );
};

export default Dashboard;
