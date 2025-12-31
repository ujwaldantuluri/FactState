import { useState } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useAuth } from "@/contexts/AuthContext";
import { Settings as SettingsIcon, User, Bell, Shield, Key, Trash2, Save } from "lucide-react";
import { toast } from "sonner";

const Settings = () => {
  const { user } = useAuth();
  const [settings, setSettings] = useState({
    emailNotifications: true,
    pushNotifications: false,
    weeklyReports: true,
    marketingEmails: false,
    twoFactorAuth: false,
    apiAccess: false,
  });

  const [profile, setProfile] = useState({
    name: user?.name || '',
    email: user?.email || '',
    avatar: user?.avatar || '',
  });

  const handleSettingChange = (key: string, value: boolean) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const handleSaveProfile = () => {
    toast.success("Profile updated successfully!");
  };

  const handleSaveSettings = () => {
    toast.success("Settings saved successfully!");
  };

  const handleGenerateApiKey = () => {
    const apiKey = 'fs_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    navigator.clipboard.writeText(apiKey);
    toast.success("API key generated and copied to clipboard!");
  };

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center w-16 h-16 bg-gradient-to-br from-slate-600 to-slate-700 rounded-2xl mx-auto">
            <SettingsIcon className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
              ⚙️ Settings
            </h1>
            <p className="text-slate-600 dark:text-slate-400 text-lg">
              Manage your account, preferences, and security settings
            </p>
          </div>
        </div>

        {/* Profile Settings */}
        <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-slate-900 dark:text-white">
              <User className="w-5 h-5" />
              Profile Information
            </CardTitle>
            <CardDescription>
              Update your personal information and profile details
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center gap-6">
              <img
                src={profile.avatar || `https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=80&h=80&fit=crop&crop=face`}
                alt="Profile"
                className="w-20 h-20 rounded-full object-cover border-4 border-white/50"
              />
              <div className="space-y-2">
                <Button variant="outline" size="sm" className="bg-white/50 dark:bg-slate-700/50">
                  Change Photo
                </Button>
                <p className="text-sm text-slate-500">JPG, PNG up to 2MB</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name" className="text-slate-700 dark:text-slate-300 font-medium">
                  Full Name
                </Label>
                <Input
                  id="name"
                  value={profile.name}
                  onChange={(e) => setProfile(prev => ({ ...prev, name: e.target.value }))}
                  className="bg-white/50 dark:bg-slate-700/50"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email" className="text-slate-700 dark:text-slate-300 font-medium">
                  Email Address
                </Label>
                <Input
                  id="email"
                  type="email"
                  value={profile.email}
                  onChange={(e) => setProfile(prev => ({ ...prev, email: e.target.value }))}
                  className="bg-white/50 dark:bg-slate-700/50"
                />
              </div>
            </div>

            <Button onClick={handleSaveProfile} className="bg-primary hover:bg-primary/90">
              <Save className="w-4 h-4 mr-2" />
              Save Profile
            </Button>
          </CardContent>
        </Card>

        {/* Appearance Settings */}
        <Card className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-white/20">
          <CardHeader>
            <CardTitle className="text-slate-900 dark:text-white">Appearance</CardTitle>
            <CardDescription>
              Customize the look and feel of your dashboard
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-slate-700 dark:text-slate-300 font-medium">Theme</Label>
                <p className="text-sm text-slate-500">Switch between light and dark mode</p>
              </div>
              <ThemeToggle />
            </div>
          </CardContent>
        </Card>

        {/* Save All Settings */}
        <div className="flex justify-center">
          <Button onClick={handleSaveSettings} size="lg" className="bg-primary hover:bg-primary/90">
            <Save className="w-5 h-5 mr-2" />
            Save All Settings
          </Button>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Settings;
