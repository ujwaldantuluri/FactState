
import { DashboardLayout } from "@/components/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { HelpCircle, Search, MessageCircle, Mail, FileText, Video, BookOpen, Zap } from "lucide-react";
import { useState } from "react";

const faqData = [
  {
    question: "How accurate is Trustify's AI detection?",
    answer: "Trustify uses advanced machine learning algorithms with an average accuracy rate of 94-98% across different content types. Our models are continuously updated with the latest detection techniques and trained on millions of data points."
  },
  {
    question: "What types of content can Trustify analyze?",
    answer: "Trustify can analyze fake news articles, fraudulent e-commerce sites, scam job postings, manipulated social media content, AI-generated images, deepfake videos, and AI-written text. We support URLs, direct text input, and file uploads."
  },
  {
    question: "How long does it take to analyze content?",
    answer: "Analysis time varies by content type: Text and URLs typically take 10-30 seconds, images take 30-60 seconds, and videos can take 1-3 minutes depending on length and complexity."
  },
  {
    question: "Is my data stored or shared?",
    answer: "We prioritize your privacy. Content is analyzed in real-time and not permanently stored unless you save it to your history. We never share your data with third parties and use enterprise-grade encryption."
  },
  {
    question: "Can I use Trustify for commercial purposes?",
    answer: "Yes! We offer business plans with API access, bulk analysis, and white-label solutions. Contact our sales team for enterprise pricing and custom integrations."
  },
  {
    question: "What should I do if I disagree with a result?",
    answer: "If you believe a result is incorrect, you can report it through the 'Report Issue' button on any analysis page. Our team reviews all reports and continuously improves our algorithms based on feedback."
  },
  {
    question: "Do you offer API access?",
    answer: "Yes, we provide REST API access for developers and businesses. API documentation, rate limits, and pricing are available in your account settings under the 'API Access' section."
  },
  {
    question: "How do I interpret the risk scores?",
    answer: "Risk scores range from 0-100%: 0-30% indicates authentic/safe content, 31-70% suggests suspicious content requiring caution, and 71-100% indicates high probability of fake/manipulated content."
  }
];

const Help = () => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredFAQs = faqData.filter(faq =>
    faq.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
    faq.answer.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl mx-auto">
            <HelpCircle className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
              🆘 Help & Support
            </h1>
            <p className="text-slate-600 dark:text-slate-400 text-lg">
              Get answers to common questions and learn how to use Trustify effectively
            </p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20 hover:shadow-lg transition-all duration-200 cursor-pointer">
            <CardContent className="p-6 text-center space-y-3">
              <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-blue-100 to-indigo-100 dark:from-blue-900/30 dark:to-indigo-900/30 rounded-xl mx-auto">
                <Video className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="font-semibold text-slate-900 dark:text-white">Video Tutorials</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">Watch step-by-step guides</p>
            </CardContent>
          </Card>

          <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20 hover:shadow-lg transition-all duration-200 cursor-pointer">
            <CardContent className="p-6 text-center space-y-3">
              <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-green-100 to-emerald-100 dark:from-green-900/30 dark:to-emerald-900/30 rounded-xl mx-auto">
                <MessageCircle className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="font-semibold text-slate-900 dark:text-white">Live Chat</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">Get instant support</p>
            </CardContent>
          </Card>

          <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20 hover:shadow-lg transition-all duration-200 cursor-pointer">
            <CardContent className="p-6 text-center space-y-3">
              <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-purple-100 to-purple-100 dark:from-purple-900/30 dark:to-purple-900/30 rounded-xl mx-auto">
                <Mail className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="font-semibold text-slate-900 dark:text-white">Email Support</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">Contact our team</p>
            </CardContent>
          </Card>
        </div>

        {/* Getting Started Guide */}
        <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-slate-900 dark:text-white">
              <Zap className="w-5 h-5" />
              Quick Start Guide
            </CardTitle>
            <CardDescription>
              Get up and running with Trustify in minutes
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="flex items-center justify-center w-8 h-8 bg-primary rounded-full text-white text-sm font-bold">
                    1
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 dark:text-white mb-1">Choose Detection Type</h4>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      Select the appropriate detector for your content type from the dashboard
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="flex items-center justify-center w-8 h-8 bg-primary rounded-full text-white text-sm font-bold">
                    2
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 dark:text-white mb-1">Input Your Content</h4>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      Paste URLs, upload files, or enter text directly into the analysis field
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="flex items-center justify-center w-8 h-8 bg-primary rounded-full text-white text-sm font-bold">
                    3
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 dark:text-white mb-1">Start Analysis</h4>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      Click the analysis button and wait for our AI to process your content
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="flex items-center justify-center w-8 h-8 bg-primary rounded-full text-white text-sm font-bold">
                    4
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 dark:text-white mb-1">Review Results</h4>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      Examine the verdict, risk score, and detailed analysis breakdown
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* FAQ Search */}
        <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
          <CardHeader>
            <CardTitle className="text-slate-900 dark:text-white">Search FAQs</CardTitle>
            <CardDescription>
              Find answers to frequently asked questions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Search for answers..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-white/50 dark:bg-slate-700/50"
              />
            </div>
          </CardContent>
        </Card>

        {/* FAQ Accordion */}
        <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-slate-900 dark:text-white">
              <BookOpen className="w-5 h-5" />
              Frequently Asked Questions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Accordion type="single" collapsible className="space-y-2">
              {filteredFAQs.map((faq, index) => (
                <AccordionItem key={index} value={`item-${index}`} className="border border-white/20 rounded-lg px-4">
                  <AccordionTrigger className="text-left font-medium text-slate-900 dark:text-white hover:no-underline">
                    {faq.question}
                  </AccordionTrigger>
                  <AccordionContent className="text-slate-600 dark:text-slate-400 pt-2">
                    {faq.answer}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>

            {filteredFAQs.length === 0 && searchTerm && (
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-slate-100 dark:bg-slate-700 rounded-full mx-auto mb-4 flex items-center justify-center">
                  <Search className="w-8 h-8 text-slate-400" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                  No results found
                </h3>
                <p className="text-slate-600 dark:text-slate-400">
                  Try different keywords or contact support for help
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Contact Support */}
        <Card className="bg-gradient-to-br from-primary/10 to-indigo-500/10 border-primary/20">
          <CardContent className="p-8 text-center">
            <div className="space-y-4">
              <div className="flex items-center justify-center w-16 h-16 bg-primary rounded-2xl mx-auto">
                <MessageCircle className="w-8 h-8 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
                  Still need help?
                </h3>
                <p className="text-slate-600 dark:text-slate-400 mb-6">
                  Our support team is available 24/7 to assist you with any questions or issues
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Button className="bg-primary hover:bg-primary/90">
                  <MessageCircle className="w-4 h-4 mr-2" />
                  Start Live Chat
                </Button>
                <Button variant="outline" className="bg-white/50 dark:bg-slate-700/50">
                  <Mail className="w-4 h-4 mr-2" />
                  Email Support
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default Help;
