import { useState } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Search, AlertTriangle, CheckCircle, XCircle, Shield, Clock, Building, DollarSign, MapPin, Globe, Mail, Phone, User } from "lucide-react";
import { toast } from "sonner";
import { API_ENDPOINTS } from "@/lib/api";

interface JobAnalysisResult {
  is_suspicious: boolean;
  confidence_score: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  red_flags: string[];
  warnings: string[];
  recommendations: string[];
  verification_checks: Record<string, string>;
  similarity_matches: string[];
  analysis_id: string;
  timestamp: string;
  final_prediction_reason?: string;
  checks: Record<string, string>;
}

const ScamJobDetector = () => {
  const [formData, setFormData] = useState({
    name: '',
    website: '',
    email: '',
    phone: '',
    address: '',
    job_description: '',
    salary_offered: '',
    requirements: '',
    contact_person: '',
    company_size: '',
    industry: '',
    social_media: {
      linkedin: '',
      facebook: '',
      twitter: '',
      instagram: ''
    },
    job_post_date: ''
  });
  
  const [isScanning, setIsScanning] = useState(false);
  const [results, setResults] = useState<JobAnalysisResult | null>(null);

  const handleInputChange = (field: string, value: string) => {
    if (field.startsWith('social_media.')) {
      const platform = field.split('.')[1];
      setFormData(prev => ({
        ...prev,
        social_media: {
          ...prev.social_media,
          [platform]: value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [field]: value
      }));
    }
  };

  const handleScan = async () => {
    if (!formData.name.trim()) {
      toast.error("Please enter the company name");
      return;
    }
    
    setIsScanning(true);
    toast.info("Analyzing job posting...");
    
    try {
      // Clean up the data before sending
      const payload: any = { name: formData.name };
      
      // Only include non-empty fields
      Object.entries(formData).forEach(([key, value]) => {
        if (key === 'social_media') {
          const socialMedia = Object.entries(formData.social_media)
            .filter(([_, url]) => url.trim())
            .reduce((acc, [platform, url]) => ({ ...acc, [platform]: url }), {});
          
          if (Object.keys(socialMedia).length > 0) {
            payload.social_media = socialMedia;
          }
        } else if (key !== 'name' && value && typeof value === 'string' && value.trim()) {
          payload[key] = value.trim();
        }
      });

  const response = await fetch(API_ENDPOINTS.JOBS.ANALYZE, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setResults(data.result);
      
      const riskLevel = data.result.risk_level;
      if (riskLevel === "CRITICAL" || riskLevel === "HIGH") {
        toast.error("⚠️ High risk job posting detected!");
      } else if (riskLevel === "MEDIUM") {
        toast.warning("⚠️ Some red flags detected - proceed with caution");
      } else {
        toast.success("✅ Job posting appears legitimate");
      }
      
    } catch (error) {
      console.error("Analysis error:", error);
      toast.error("Failed to analyze job posting. Please try again.");
    } finally {
      setIsScanning(false);
    }
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'LOW':
        return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-400';
      case 'MEDIUM':
        return 'bg-amber-100 text-amber-800 dark:bg-amber-900/20 dark:text-amber-400';
      case 'HIGH':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400';
      case 'CRITICAL':
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
      default:
        return 'bg-slate-100 text-slate-800 dark:bg-slate-900/20 dark:text-slate-400';
    }
  };

  const getRiskIcon = (riskLevel: string) => {
    switch (riskLevel) {
      case 'LOW':
        return <CheckCircle className="w-5 h-5 text-emerald-600" />;
      case 'MEDIUM':
        return <AlertTriangle className="w-5 h-5 text-amber-600" />;
      case 'HIGH':
      case 'CRITICAL':
        return <XCircle className="w-5 h-5 text-red-600" />;
      default:
        return <Shield className="w-5 h-5 text-slate-600" />;
    }
  };

  return (
    <DashboardLayout>
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl mx-auto">
            <Search className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
              🧑‍💼 Scam Job Detector
            </h1>
            <p className="text-slate-600 dark:text-slate-400 text-lg">
              Identify fraudulent job postings and employment scams using AI analysis
            </p>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Input Section */}
          <div className="space-y-6">
            <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-slate-900 dark:text-white">
                  <Building className="w-5 h-5" />
                  Company Information
                </CardTitle>
                <CardDescription>
                  Enter the basic company details from the job posting
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name" className="flex items-center gap-2">
                    <Building className="w-4 h-4" />
                    Company Name *
                  </Label>
                  <Input 
                    id="name"
                    value={formData.name} 
                    onChange={(e) => handleInputChange('name', e.target.value)} 
                    placeholder="e.g., Acme Corporation" 
                    required 
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="website" className="flex items-center gap-2">
                    <Globe className="w-4 h-4" />
                    Website
                  </Label>
                  <Input 
                    id="website"
                    value={formData.website} 
                    onChange={(e) => handleInputChange('website', e.target.value)} 
                    placeholder="https://company.com" 
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="email" className="flex items-center gap-2">
                      <Mail className="w-4 h-4" />
                      Email
                    </Label>
                    <Input 
                      id="email"
                      value={formData.email} 
                      onChange={(e) => handleInputChange('email', e.target.value)} 
                      placeholder="hr@company.com" 
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="phone" className="flex items-center gap-2">
                      <Phone className="w-4 h-4" />
                      Phone
                    </Label>
                    <Input 
                      id="phone"
                      value={formData.phone} 
                      onChange={(e) => handleInputChange('phone', e.target.value)} 
                      placeholder="+1 555-1234" 
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="address" className="flex items-center gap-2">
                    <MapPin className="w-4 h-4" />
                    Address
                  </Label>
                  <Input 
                    id="address"
                    value={formData.address} 
                    onChange={(e) => handleInputChange('address', e.target.value)} 
                    placeholder="123 Main St, City, State" 
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="industry">Industry</Label>
                    <Input 
                      id="industry"
                      value={formData.industry} 
                      onChange={(e) => handleInputChange('industry', e.target.value)} 
                      placeholder="Technology" 
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="company_size">Company Size</Label>
                    <Input 
                      id="company_size"
                      value={formData.company_size} 
                      onChange={(e) => handleInputChange('company_size', e.target.value)} 
                      placeholder="50-200 employees" 
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-slate-900 dark:text-white">
                  <DollarSign className="w-5 h-5" />
                  Job Details
                </CardTitle>
                <CardDescription>
                  Provide information about the specific job posting
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="job_description">Job Description</Label>
                  <Textarea 
                    id="job_description"
                    value={formData.job_description} 
                    onChange={(e) => handleInputChange('job_description', e.target.value)} 
                    placeholder="Describe the job role, responsibilities, and benefits..."
                    rows={3}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="salary_offered" className="flex items-center gap-2">
                    <DollarSign className="w-4 h-4" />
                    Salary Offered
                  </Label>
                  <Input 
                    id="salary_offered"
                    value={formData.salary_offered} 
                    onChange={(e) => handleInputChange('salary_offered', e.target.value)} 
                    placeholder="$50,000/year or $25/hour" 
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="requirements">Requirements</Label>
                  <Textarea 
                    id="requirements"
                    value={formData.requirements} 
                    onChange={(e) => handleInputChange('requirements', e.target.value)} 
                    placeholder="List the job requirements and qualifications..."
                    rows={2}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="contact_person" className="flex items-center gap-2">
                      <User className="w-4 h-4" />
                      Contact Person
                    </Label>
                    <Input 
                      id="contact_person"
                      value={formData.contact_person} 
                      onChange={(e) => handleInputChange('contact_person', e.target.value)} 
                      placeholder="Jane Doe" 
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="job_post_date" className="flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      Post Date
                    </Label>
                    <Input 
                      id="job_post_date"
                      type="date"
                      value={formData.job_post_date} 
                      onChange={(e) => handleInputChange('job_post_date', e.target.value)} 
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
              <CardHeader>
                <CardTitle className="text-slate-900 dark:text-white">Social Media Profiles</CardTitle>
                <CardDescription>
                  Company social media presence (optional but helpful for verification)
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="linkedin">LinkedIn</Label>
                    <Input 
                      id="linkedin"
                      value={formData.social_media.linkedin} 
                      onChange={(e) => handleInputChange('social_media.linkedin', e.target.value)} 
                      placeholder="LinkedIn company page URL" 
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="facebook">Facebook</Label>
                    <Input 
                      id="facebook"
                      value={formData.social_media.facebook} 
                      onChange={(e) => handleInputChange('social_media.facebook', e.target.value)} 
                      placeholder="Facebook page URL" 
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="twitter">Twitter</Label>
                    <Input 
                      id="twitter"
                      value={formData.social_media.twitter} 
                      onChange={(e) => handleInputChange('social_media.twitter', e.target.value)} 
                      placeholder="Twitter profile URL" 
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="instagram">Instagram</Label>
                    <Input 
                      id="instagram"
                      value={formData.social_media.instagram} 
                      onChange={(e) => handleInputChange('social_media.instagram', e.target.value)} 
                      placeholder="Instagram profile URL" 
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Button
              onClick={handleScan}
              disabled={isScanning}
              className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white font-semibold py-4 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
              size="lg"
            >
              {isScanning ? (
                <>
                  <Search className="w-5 h-5 mr-2 animate-spin" />
                  Analyzing Job Posting...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5 mr-2" />
                  Analyze Job Legitimacy
                </>
              )}
            </Button>
          </div>

          {/* Results Section */}
          <div className="space-y-6">
            {isScanning && (
              <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
                <CardContent className="py-12">
                  <div className="text-center space-y-4">
                    <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full mx-auto flex items-center justify-center animate-pulse">
                      <Search className="w-8 h-8 text-white" />
                    </div>
                    <div className="space-y-2">
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                        Analyzing Job Posting...
                      </h3>
                      <p className="text-slate-600 dark:text-slate-400">
                        Checking company details, salary authenticity, and red flag indicators
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {results && (
              <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-3 text-slate-900 dark:text-white">
                    {getRiskIcon(results.risk_level)}
                    Analysis Results
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Risk Level Badge */}
                  <div className="flex items-center justify-between">
                    <Badge className={`px-4 py-2 text-sm font-semibold ${getRiskColor(results.risk_level)}`}>
                      Risk Level: {results.risk_level}
                    </Badge>
                    <Badge variant="outline" className="px-3 py-1">
                      {Math.round(results.confidence_score)}% Confidence
                    </Badge>
                  </div>

                  {/* Suspicious Status */}
                  <div className={`p-4 rounded-lg border-2 ${
                    results.is_suspicious 
                      ? 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800' 
                      : 'bg-emerald-50 border-emerald-200 dark:bg-emerald-900/20 dark:border-emerald-800'
                  }`}>
                    <div className="flex items-center gap-2 font-semibold">
                      {results.is_suspicious ? (
                        <XCircle className="w-5 h-5 text-red-600" />
                      ) : (
                        <CheckCircle className="w-5 h-5 text-emerald-600" />
                      )}
                      <span className={results.is_suspicious ? 'text-red-800 dark:text-red-400' : 'text-emerald-800 dark:text-emerald-400'}>
                        {results.is_suspicious ? 'Suspicious Job Posting' : 'Legitimate Job Posting'}
                      </span>
                    </div>
                    {results.final_prediction_reason && (
                      <p className={`mt-2 text-sm ${
                        results.is_suspicious ? 'text-red-700 dark:text-red-300' : 'text-emerald-700 dark:text-emerald-300'
                      }`}>
                        {results.final_prediction_reason}
                      </p>
                    )}
                  </div>

                  {/* Red Flags */}
                  {results.red_flags && results.red_flags.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-red-800 dark:text-red-400 mb-3 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4" />
                        Red Flags Detected ({results.red_flags.length})
                      </h4>
                      <div className="space-y-2">
                        {results.red_flags.map((flag, index) => (
                          <div key={index} className="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                            <XCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                            <span className="text-sm text-red-800 dark:text-red-300">{flag}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Warnings */}
                  {results.warnings && results.warnings.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-amber-800 dark:text-amber-400 mb-3 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4" />
                        Warnings
                      </h4>
                      <div className="space-y-2">
                        {results.warnings.map((warning, index) => (
                          <div key={index} className="flex items-start gap-2 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
                            <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
                            <span className="text-sm text-amber-800 dark:text-amber-300">{warning}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recommendations */}
                  {results.recommendations && results.recommendations.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-blue-800 dark:text-blue-400 mb-3 flex items-center gap-2">
                        <Shield className="w-4 h-4" />
                        Recommendations
                      </h4>
                      <div className="space-y-2">
                        {results.recommendations.map((rec, index) => (
                          <div key={index} className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                            <CheckCircle className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                            <span className="text-sm text-blue-800 dark:text-blue-300">{rec}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <Separator />

                  {/* Analysis Metadata */}
                  <div className="text-xs text-slate-500 dark:text-slate-400 space-y-1">
                    <div>Analysis ID: {results.analysis_id}</div>
                    <div>Analyzed at: {new Date(results.timestamp).toLocaleString()}</div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default ScamJobDetector;
