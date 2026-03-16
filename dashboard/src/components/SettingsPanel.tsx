import { useState, useEffect } from 'react';
import { 
  X, 
  Settings as SettingsIcon, 
  Key, 
  User, 
  Database, 
  Wifi, 
  WifiOff, 
  Copy, 
  Check,
  LogOut,
  Globe
} from 'lucide-react';
import clsx from 'clsx';
import { api } from '../lib/api';
import { API_V1 } from '../config';

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onLogout: () => void;
}

export function SettingsPanel({ isOpen, onClose, onLogout }: SettingsPanelProps) {
  const [apiUrl, setApiUrl] = useState('');
  const [projectId, setProjectId] = useState('');
  const [userId, setUserId] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [apiKeyPreview, setApiKeyPreview] = useState('');
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [showApiKey, setShowApiKey] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadSettings();
      checkConnection();
    }
  }, [isOpen]);

  const loadSettings = async () => {
    // Get API URL
    const baseUrl = API_V1.replace('/api/v1', '');
    setApiUrl(baseUrl);

    // Get Project ID
    const project = api.getProjectId() || 'default';
    setProjectId(project);

    // Get User ID
    const user = api.getUserId();
    setUserId(user);

    // Get API Key preview
    const key = api.getApiKey();
    if (key) {
      setApiKeyPreview(`${key.substring(0, 8)}...${key.substring(key.length - 4)}`);
      setApiKey(key);
    } else {
      // Check for JWT token
      const token = api.getJwtToken();
      if (token) {
        setApiKeyPreview('JWT Token (via login)');
      }
    }
  };

  const checkConnection = async () => {
    try {
      const response = await fetch(`${API_V1}/health`);
      setIsConnected(response.ok);
    } catch {
      setIsConnected(false);
    }
  };

  const copyToClipboard = async (text: string, field: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const handleApiKeyUpdate = () => {
    if (apiKey.trim()) {
      api.setApiKey(apiKey.trim());
      setApiKeyPreview(`${apiKey.substring(0, 8)}...${apiKey.substring(apiKey.length - 4)}`);
      setShowApiKey(false);
      // Reload to apply new key
      window.location.reload();
    }
  };

  const handleDisconnect = () => {
    if (confirm('Are you sure you want to disconnect? You will need to sign in again.')) {
      onLogout();
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed inset-y-0 right-0 w-full max-w-md dashboard-surface border-l border-[hsl(var(--border))/0.72] z-50 overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 dashboard-surface border-b border-[hsl(var(--border))/0.72] px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-[hsl(var(--primary))]/10">
                <SettingsIcon className="w-5 h-5 text-[hsl(var(--primary))]" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-[hsl(var(--foreground))]">
                  Settings
                </h2>
                <p className="text-xs text-[hsl(var(--muted-foreground))]">
                  Connection & Account
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-[hsl(var(--muted))/0.78] text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Connection Status */}
          <div className="premium-chip rounded-2xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-[hsl(var(--foreground))]">
                Connection Status
              </h3>
              {isConnected ? (
                <div className="flex items-center gap-2 text-xs text-emerald-400">
                  <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                  Connected
                </div>
              ) : (
                <div className="flex items-center gap-2 text-xs text-red-400">
                  <WifiOff className="w-3 h-3" />
                  Disconnected
                </div>
              )}
            </div>
            <div className="flex items-center gap-2 text-xs text-[hsl(var(--muted-foreground))]">
              {isConnected ? (
                <>
                  <Wifi className="w-3.5 h-3.5 text-emerald-400" />
                  API responding normally
                </>
              ) : (
                <>
                  <WifiOff className="w-3.5 h-3.5" />
                  Cannot reach API server
                </>
              )}
            </div>
          </div>

          {/* API URL */}
          <div>
            <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
              <Globe className="w-4 h-4 inline mr-2" />
              API URL
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={apiUrl}
                readOnly
                className="flex-1 px-3 py-2 rounded-lg premium-chip text-sm text-[hsl(var(--foreground))] font-mono"
              />
              <button
                onClick={() => copyToClipboard(apiUrl, 'apiUrl')}
                className="p-2 rounded-lg premium-chip hover:bg-[hsl(var(--muted))/0.82] text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] transition-colors"
                title="Copy"
              >
                {copiedField === 'apiUrl' ? (
                  <Check className="w-4 h-4 text-emerald-400" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {/* Project ID */}
          <div>
            <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
              <Database className="w-4 h-4 inline mr-2" />
              Current Project ID
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={projectId}
                readOnly
                className="flex-1 px-3 py-2 rounded-lg premium-chip text-sm text-[hsl(var(--foreground))] font-mono"
              />
              <button
                onClick={() => copyToClipboard(projectId, 'projectId')}
                className="p-2 rounded-lg premium-chip hover:bg-[hsl(var(--muted))/0.82] text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] transition-colors"
                title="Copy"
              >
                {copiedField === 'projectId' ? (
                  <Check className="w-4 h-4 text-emerald-400" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            </div>
            <p className="mt-1 text-xs text-[hsl(var(--muted-foreground))]">
              Use the project switcher in the header to change projects
            </p>
          </div>

          {/* User ID */}
          <div>
            <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
              <User className="w-4 h-4 inline mr-2" />
              User ID
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={userId}
                readOnly
                className="flex-1 px-3 py-2 rounded-lg premium-chip text-sm text-[hsl(var(--foreground))] font-mono"
              />
              <button
                onClick={() => copyToClipboard(userId, 'userId')}
                className="p-2 rounded-lg premium-chip hover:bg-[hsl(var(--muted))/0.82] text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] transition-colors"
                title="Copy"
              >
                {copiedField === 'userId' ? (
                  <Check className="w-4 h-4 text-emerald-400" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {/* API Key Management */}
          <div>
            <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
              <Key className="w-4 h-4 inline mr-2" />
              API Key
            </label>
            {!showApiKey ? (
              <div className="space-y-2">
                <div className="flex gap-2">
                  <input
                    type="password"
                    value={apiKeyPreview}
                    readOnly
                    className="flex-1 px-3 py-2 rounded-lg premium-chip text-sm text-[hsl(var(--muted-foreground))] font-mono"
                  />
                  <button
                    onClick={() => setShowApiKey(true)}
                    className="px-3 py-2 rounded-lg premium-chip hover:bg-[hsl(var(--muted))/0.82] text-[hsl(var(--foreground))] text-sm transition-colors"
                  >
                    Edit
                  </button>
                </div>
                <p className="text-xs text-[hsl(var(--muted-foreground))]">
                  {api.getJwtToken() ? 'Authenticated via JWT token' : 'Authenticated via API key'}
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <input
                  type="text"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="rem_..."
                  className="w-full px-3 py-2 rounded-lg premium-chip text-sm text-[hsl(var(--foreground))] font-mono focus:ring-2 focus:ring-[hsl(var(--primary))]"
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleApiKeyUpdate}
                    className="flex-1 px-3 py-2 rounded-lg bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary))]/90 text-white text-sm font-medium transition-colors"
                  >
                    Save
                  </button>
                  <button
                    onClick={() => {
                      setShowApiKey(false);
                      setApiKey(api.getApiKey() || '');
                    }}
                    className="flex-1 px-3 py-2 rounded-lg premium-chip hover:bg-[hsl(var(--muted))/0.82] text-[hsl(var(--foreground))] text-sm transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="pt-4 border-t border-[hsl(var(--border))/0.72] space-y-2">
            <button
              onClick={handleDisconnect}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-red-500/30 bg-red-500/10 hover:bg-red-500/20 text-red-500 font-medium transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Disconnect / Switch Account
            </button>
          </div>

          {/* Info */}
          <div className="premium-chip rounded-2xl p-4">
            <h4 className="text-xs font-semibold text-[hsl(var(--foreground))] mb-2">
              Need Help?
            </h4>
            <p className="text-xs text-[hsl(var(--muted-foreground))] leading-relaxed">
              To manage API keys or change your account settings, visit the{' '}
              <button
                onClick={() => {
                  onClose();
                  // Navigate to keys tab - implement via callback if needed
                }}
                className="text-[hsl(var(--primary))] hover:underline"
              >
                API Keys
              </button>{' '}
              tab.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
