import { useState, useEffect, type FC, type FormEvent } from 'react';
import { userApi } from '../api/userApi';
import { changePassword } from '../api/authApi';
import { getGoogleCalendarAuthUrl, getGoogleCalendarStatus, disconnectGoogleCalendar } from '../api/integrationApi';
import { User, Lock, Edit3, Shield, Mail, Calendar, CheckCircle2, AlertCircle } from 'lucide-react';

interface UserProfilePageProps {
  profile: any;
  setProfile: (p: any) => void;
  setMessage: (m: string) => void;
  setAppView: (view: string) => void;
}

export const UserProfilePage: FC<UserProfilePageProps> = ({ profile, setProfile, setMessage, setAppView }) => {
  const [activeTab, setActiveTab] = useState<'general' | 'onboarding' | 'security' | 'integrations'>('general');
  const [loading, setLoading] = useState(false);

  // Integrations state
  const [calendarConnected, setCalendarConnected] = useState(false);
  const [importEvents, setImportEvents] = useState(true);
  const [allowUpdates, setAllowUpdates] = useState(true);

  useEffect(() => {
    fetchCalendarStatus();
    if (window.location.hash.includes('calendar_connected')) {
      setCalendarConnected(true);
      setMessage("Google Calendar connected successfully!");
    } else if (window.location.hash.includes('calendar_error')) {
      const err = window.location.hash.split('calendar_error=')[1]?.split('&')[0];
      setMessage(`Google Calendar connection error: ${decodeURIComponent(err || 'Unknown error')}`);
    }
  }, []);

  const fetchCalendarStatus = async () => {
    try {
      const status = await getGoogleCalendarStatus();
      setCalendarConnected(!!status?.connected);
    } catch {
      setCalendarConnected(false);
    }
  };

  const handleConnectCalendar = async () => {
    setLoading(true);
    try {
      const res = await getGoogleCalendarAuthUrl();
      if (res?.url) {
        if (res.url.includes('accounts.google.com')) {
          window.location.href = res.url;
        } else {
          // Dev mock mode or same-origin fallback
          setCalendarConnected(true);
          setMessage("Google Calendar connected successfully!");
        }
      }
    } catch (err: any) {
      setMessage(err.message || "Failed to initiate Google Calendar connection.");
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnectCalendar = async () => {
    if (!window.confirm("Are you sure you want to disconnect Google Calendar?")) return;
    setLoading(true);
    try {
      await disconnectGoogleCalendar();
      setCalendarConnected(false);
      setMessage("Google Calendar disconnected.");
    } catch (err: any) {
      setMessage(err.message || "Failed to disconnect Google Calendar.");
    } finally {
      setLoading(false);
    }
  };

  // General & Onboarding Form State
  const [profileForm, setProfileForm] = useState({
    username: profile?.username || '',
    dob: profile?.dob || '',
    gender: profile?.gender || '',
    goals: profile?.goals || '',
    focus_times: profile?.focus_times || '',
    typical_disruptions: profile?.typical_disruptions || '',
    structure_preference: profile?.structure_preference || 'Flexible',
  });

  useEffect(() => {
    if (profile) {
      setProfileForm({
        username: profile.username || '',
        dob: profile.dob || '',
        gender: profile.gender || '',
        goals: profile.goals || '',
        focus_times: profile.focus_times || '',
        typical_disruptions: profile.typical_disruptions || '',
        structure_preference: profile.structure_preference || 'Flexible',
      });
    }
  }, [profile]);

  const handleInputChange = (field: string, value: string) => {
    setProfileForm(prev => ({ ...prev, [field]: value }));
  };

  // Security Form
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleGeneralSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const updated = await userApi.updateUserProfile({
        username: profileForm.username,
        dob: profileForm.dob,
        gender: profileForm.gender
      });
      setProfile(updated);
      setMessage("Profile updated successfully!");
    } catch (err: any) {
      setMessage(err.message || "Failed to update profile.");
    } finally {
      setLoading(false);
    }
  };

  const handleOnboardingSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const updated = await userApi.updateUserProfile({
        goals: profileForm.goals,
        focus_times: profileForm.focus_times,
        typical_disruptions: profileForm.typical_disruptions,
        structure_preference: profileForm.structure_preference
      });
      setProfile(updated);
      setMessage("Onboarding details updated!");
    } catch (err: any) {
      setMessage(err.message || "Failed to update onboarding details.");
    } finally {
      setLoading(false);
    }
  };

  const handleSecuritySubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setMessage("New passwords do not match.");
      return;
    }
    if (newPassword.length < 8) {
      setMessage("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    try {
      await changePassword(oldPassword, newPassword);
      setMessage("Password changed successfully!");
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setMessage(err.message || "Failed to change password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-y-auto bg-zinc-50/50 dark:bg-zinc-900/50 p-6 md:p-12 relative z-10">
      <div className="max-w-4xl w-full mx-auto space-y-8">

        <div className="flex items-center gap-4 mb-4">
          <button
            onClick={() => setAppView('planner')}
            className="px-4 py-2 text-sm font-medium text-zinc-600 dark:text-zinc-300 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg hover:bg-zinc-50 dark:hover:bg-zinc-700 transition-colors shadow-sm"
          >
            &larr; Back to Planner
          </button>
          <h2 className="text-3xl font-bold text-zinc-800 dark:text-white flex items-center gap-3">
            <User className="w-8 h-8 text-primary" />
            User Profile
          </h2>
        </div>

        <div className="bg-white dark:bg-zinc-800 rounded-2xl shadow-sm border border-zinc-200 dark:border-zinc-700 overflow-hidden">
          <div className="flex border-b border-zinc-200 dark:border-zinc-700 overflow-x-auto">
            <button
              onClick={() => setActiveTab('general')}
              className={`flex-1 py-4 px-4 text-sm font-medium flex items-center justify-center gap-2 transition-colors whitespace-nowrap ${activeTab === 'general' ? 'text-primary border-b-2 border-primary bg-orange-50/50 dark:bg-orange-950/20' : 'text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-700/50'}`}
            >
              <User className="w-4 h-4" /> General Info
            </button>
            <button
              onClick={() => setActiveTab('onboarding')}
              className={`flex-1 py-4 px-4 text-sm font-medium flex items-center justify-center gap-2 transition-colors whitespace-nowrap ${activeTab === 'onboarding' ? 'text-primary border-b-2 border-primary bg-orange-50/50 dark:bg-orange-950/20' : 'text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-700/50'}`}
            >
              <Edit3 className="w-4 h-4" /> Preferences
            </button>
            <button
              onClick={() => setActiveTab('integrations')}
              className={`flex-1 py-4 px-4 text-sm font-medium flex items-center justify-center gap-2 transition-colors whitespace-nowrap ${activeTab === 'integrations' ? 'text-primary border-b-2 border-primary bg-orange-50/50 dark:bg-orange-950/20' : 'text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-700/50'}`}
            >
              <Calendar className="w-4 h-4" /> Integrations
            </button>
            <button
              onClick={() => setActiveTab('security')}
              className={`flex-1 py-4 px-4 text-sm font-medium flex items-center justify-center gap-2 transition-colors whitespace-nowrap ${activeTab === 'security' ? 'text-primary border-b-2 border-primary bg-orange-50/50 dark:bg-orange-950/20' : 'text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-700/50'}`}
            >
              <Shield className="w-4 h-4" /> Security
            </button>
          </div>

          <div className="p-6 md:p-8">
            {activeTab === 'general' && (
              <form onSubmit={handleGeneralSubmit} className="space-y-6 max-w-xl">
                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">Username</label>
                  <input
                    type="text"
                    value={profileForm.username}
                    onChange={e => handleInputChange('username', e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                    placeholder="e.g. daily_planner_user"
                  />
                  <p className="mt-2 text-xs text-zinc-500">Your unique handle.</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">Date of Birth</label>
                  <input
                    type="date"
                    value={profileForm.dob}
                    onChange={e => handleInputChange('dob', e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">Gender</label>
                  <select
                    value={profileForm.gender}
                    onChange={e => handleInputChange('gender', e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  >
                    <option value="">Select gender...</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Prefer not to say">Prefer not to say</option>
                  </select>
                </div>
                <div className="pt-4">
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full md:w-auto px-6 py-3 bg-primary hover:bg-primary-hover text-white rounded-xl font-medium transition-colors disabled:opacity-50"
                  >
                    {loading ? 'Saving...' : 'Save General Info'}
                  </button>
                </div>
              </form>
            )}

            {activeTab === 'onboarding' && (
              <form onSubmit={handleOnboardingSubmit} className="space-y-6 max-w-xl">
                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">What are your main goals?</label>
                  <textarea
                    value={profileForm.goals}
                    onChange={e => handleInputChange('goals', e.target.value)}
                    rows={3}
                    className="w-full px-4 py-3 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none"
                    placeholder="e.g. Build an app, run a marathon..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">When are you most focused?</label>
                  <input
                    type="text"
                    value={profileForm.focus_times}
                    onChange={e => handleInputChange('focus_times', e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                    placeholder="e.g. Early mornings, late nights"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">What typically disrupts your plans?</label>
                  <input
                    type="text"
                    value={profileForm.typical_disruptions}
                    onChange={e => handleInputChange('typical_disruptions', e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                    placeholder="e.g. Social media, meetings"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">Preferred Structure</label>
                  <select
                    value={profileForm.structure_preference}
                    onChange={e => handleInputChange('structure_preference', e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  >
                    <option value="Flexible">Flexible (Loose guidelines)</option>
                    <option value="Moderate">Moderate (Some fixed blocks)</option>
                    <option value="Strict">Strict (Minute-by-minute)</option>
                  </select>
                </div>
                <div className="pt-4">
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full md:w-auto px-6 py-3 bg-primary hover:bg-primary-hover text-white rounded-xl font-medium transition-colors disabled:opacity-50"
                  >
                    {loading ? 'Saving...' : 'Save Preferences'}
                  </button>
                </div>
              </form>
            )}

            {activeTab === 'security' && (
              <form onSubmit={handleSecuritySubmit} className="space-y-6 max-w-xl">
                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">Current Password</label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400" />
                    <input
                      type="password"
                      value={oldPassword}
                      onChange={e => setOldPassword(e.target.value)}
                      required
                      className="w-full pl-12 pr-4 py-3 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                      placeholder="Enter current password"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">New Password</label>
                  <div className="relative">
                    <Shield className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400" />
                    <input
                      type="password"
                      value={newPassword}
                      onChange={e => setNewPassword(e.target.value)}
                      required
                      className="w-full pl-12 pr-4 py-3 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                      placeholder="At least 8 characters"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">Confirm New Password</label>
                  <div className="relative">
                    <Shield className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400" />
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={e => setConfirmPassword(e.target.value)}
                      required
                      className="w-full pl-12 pr-4 py-3 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                      placeholder="Repeat new password"
                    />
                  </div>
                </div>
                <div className="pt-4">
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full md:w-auto px-6 py-3 bg-zinc-900 hover:bg-zinc-800 dark:bg-white dark:hover:bg-zinc-200 text-white dark:text-zinc-900 rounded-xl font-medium transition-colors disabled:opacity-50"
                  >
                    {loading ? 'Updating...' : 'Update Password'}
                  </button>
                </div>
              </form>
            )}

            {activeTab === 'integrations' && (
              <div className="space-y-8 max-w-xl">
                <div className="p-6 rounded-2xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50/50 dark:bg-zinc-900/50 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-3 bg-blue-100 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 rounded-xl">
                        <Calendar className="w-6 h-6" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-zinc-900 dark:text-white text-base">Google Calendar</h4>
                        <p className="text-xs text-zinc-500">Sync events directly to your daily planner timeline</p>
                      </div>
                    </div>
                    {calendarConnected ? (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Connected
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-400">
                        Not connected
                      </span>
                    )}
                  </div>

                  <div className="pt-2">
                    {calendarConnected ? (
                      <button
                        onClick={handleDisconnectCalendar}
                        disabled={loading}
                        className="px-4 py-2 text-sm font-medium text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800/40 rounded-xl hover:bg-red-100 transition-colors"
                      >
                        Disconnect Google Calendar
                      </button>
                    ) : (
                      <button
                        onClick={handleConnectCalendar}
                        className="px-5 py-2.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-xl transition-colors shadow-sm flex items-center gap-2"
                      >
                        <Calendar className="w-4 h-4" /> Connect Google Calendar
                      </button>
                    )}
                  </div>
                </div>

                <div className="space-y-4 pt-2">
                  <h4 className="text-sm font-semibold text-zinc-800 dark:text-zinc-200">Integration Preferences</h4>
                  
                  <label className="flex items-center justify-between p-4 rounded-xl border border-zinc-200 dark:border-zinc-700 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-900/30 transition-colors">
                    <div>
                      <span className="text-sm font-medium text-zinc-900 dark:text-white block">Import events as external tasks</span>
                      <span className="text-xs text-zinc-500 block">Automatically layer Google events onto daily planner timeline</span>
                    </div>
                    <input
                      type="checkbox"
                      checked={importEvents}
                      onChange={e => setImportEvents(e.target.checked)}
                      className="w-4 h-4 accent-primary rounded"
                    />
                  </label>

                  <label className="flex items-center justify-between p-4 rounded-xl border border-zinc-200 dark:border-zinc-700 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-900/30 transition-colors">
                    <div>
                      <span className="text-sm font-medium text-zinc-900 dark:text-white block">Allow updating Google events</span>
                      <span className="text-xs text-zinc-500 block">Editing an external task updates the event in Google Calendar</span>
                    </div>
                    <input
                      type="checkbox"
                      checked={allowUpdates}
                      onChange={e => setAllowUpdates(e.target.checked)}
                      className="w-4 h-4 accent-primary rounded"
                    />
                  </label>
                </div>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
