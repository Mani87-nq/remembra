import { useState, useEffect, useCallback } from 'react';
import { 
  Key, 
  Plus, 
  Trash2, 
  Copy, 
  Check, 
  X, 
  Loader2, 
  Eye,
  EyeOff,
  Shield,
  Calendar,
  Clock,
  AlertTriangle,
  Lock
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import { api, type ApiKeyInfo, type CreateApiKeyResponse } from '../lib/api';

type ApiKey = ApiKeyInfo;
type CreateKeyResponse = CreateApiKeyResponse;

const PERMISSION_STYLES = {
  admin: 'bg-red-500/10 border-red-500/20 text-red-400',
  editor: 'bg-purple-500/10 border-purple-500/20 text-purple-400',
  viewer: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
};

const PERMISSION_LABELS = {
  admin: 'Admin',
  editor: 'Editor',
  viewer: 'Viewer',
};

export function ApiKeyManager() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState<ApiKey | null>(null);
  const [newKeyResult, setNewKeyResult] = useState<CreateKeyResponse | null>(null);

  const fetchKeys = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.listKeys(true);
      setKeys(response.keys);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load API keys');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchKeys();
  }, [fetchKeys]);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit',
    });
  };

  const formatRelativeDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never used';
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) return 'Just now';
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return formatDate(dateStr);
  };

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Lock className="w-5 h-5 text-purple-400" />
            API Keys
          </h2>
          <p className="text-[13px] text-gray-400 mt-1 font-medium">
            Manage programmatic access and agent tokens for this workspace.
          </p>
        </div>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => setShowCreateModal(true)}
          className={clsx(
            'px-4 py-2 rounded-xl text-sm font-semibold',
            'bg-[linear-gradient(135deg,#8B5CF6,#6366f1)] text-white',
            'flex items-center gap-2 shadow-[0_4px_14px_rgba(139,92,246,0.3)]',
            'hover:shadow-[0_6px_20px_rgba(139,92,246,0.4)] transition-all'
          )}
        >
          <Plus className="w-4 h-4" />
          Generate New Key
        </motion.button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-medium">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
        </div>
      ) : keys.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 px-4 text-center rounded-2xl bg-white/[0.02] border border-white/5 border-dashed">
          <div className="w-16 h-16 rounded-full bg-white/[0.03] flex items-center justify-center mb-4 border border-white/10">
            <Key className="w-7 h-7 text-gray-400" />
          </div>
          <h3 className="text-base font-semibold text-white mb-2">No active API keys</h3>
          <p className="text-sm text-gray-400 max-w-sm mb-6">
            Generate a secure token to authenticate external tools, agents, and CI/CD pipelines against the Remembra network.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/15 text-white font-medium text-sm transition-colors"
          >
            Create your first key
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          <AnimatePresence>
            {keys.map((key, index) => (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: Math.min(index * 0.05, 0.3) }}
                key={key.id}
                className={clsx(
                  'group bg-white/[0.02] backdrop-blur-md rounded-2xl border border-white/5',
                  'p-5 transition-all duration-300',
                  'hover:bg-white/[0.04] hover:shadow-xl hover:shadow-purple-500/5 hover:border-purple-500/20'
                )}
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2.5">
                      <h3 className="text-[15px] font-semibold tracking-tight text-white truncate">
                        {key.name || 'Unnamed Application'}
                      </h3>
                      <span className={clsx(
                        'px-2 py-0.5 rounded-md text-[10px] uppercase tracking-wider font-bold border',
                        PERMISSION_STYLES[key.permission || key.role || 'editor']
                      )}>
                        {PERMISSION_LABELS[key.permission || key.role || 'editor']}
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-3 mb-3">
                      <code className="px-2.5 py-1 rounded-md bg-black/40 border border-white/5 text-[13px] font-mono tracking-wider text-gray-300">
                        rem_{key.key_preview}&bull;&bull;&bull;&bull;&bull;&bull;
                      </code>
                    </div>

                    <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-[12px] font-medium text-gray-500">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5 opacity-70" />
                        <span>Created {formatDate(key.created_at)}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 opacity-70" />
                        <span>Last used {formatRelativeDate(key.last_used_at)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center mt-2 md:mt-0 opacity-100 md:opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => setShowDeleteModal(key)}
                      className={clsx(
                        'flex items-center gap-2 px-3 py-2 rounded-xl font-medium text-sm',
                        'bg-red-500/10 text-red-400 hover:bg-red-500 hover:text-white',
                        'border border-red-500/20 hover:border-red-500',
                        'transition-all duration-200'
                      )}
                    >
                      <Trash2 className="w-4 h-4" />
                      Revoke
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      <AnimatePresence>
        {showCreateModal && (
          <CreateKeyModal
            onClose={() => setShowCreateModal(false)}
            onCreated={(result) => {
              setNewKeyResult(result);
              setShowCreateModal(false);
              fetchKeys();
            }}
          />
        )}

        {newKeyResult && (
          <NewKeyResultModal
            keyData={newKeyResult}
            onClose={() => setNewKeyResult(null)}
          />
        )}

        {showDeleteModal && (
          <DeleteKeyModal
            keyData={showDeleteModal}
            onClose={() => setShowDeleteModal(null)}
            onDeleted={() => {
              setShowDeleteModal(null);
              fetchKeys();
            }}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

// ---------------------------------------------------------
// MODALS (Vercel Style)
// ---------------------------------------------------------

function ModalOverlay({ children, onClose }: { children: React.ReactNode, onClose?: () => void }) {
  return (
    <motion.div 
      initial={{ opacity: 0 }} 
      animate={{ opacity: 1 }} 
      exit={{ opacity: 0 }} 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget && onClose) onClose();
      }}
    >
      <motion.div 
        initial={{ scale: 0.95, opacity: 0, y: 10 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.95, opacity: 0, y: 10 }}
        transition={{ type: "spring", duration: 0.4 }}
        className="w-full max-w-md bg-[#111111] border border-white/10 rounded-2xl shadow-[0_0_40px_rgba(0,0,0,0.5)] overflow-hidden"
      >
        {children}
      </motion.div>
    </motion.div>
  );
}

function CreateKeyModal({ onClose, onCreated }: { onClose: () => void; onCreated: (result: CreateKeyResponse) => void }) {
  const [name, setName] = useState('');
  const [permission, setPermission] = useState<'admin' | 'editor' | 'viewer'>('editor');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return setError('Please enter a name for this token');
    setLoading(true);
    setError(null);
    try {
      const result = await api.createKey(name.trim(), permission);
      onCreated(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create API key');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ModalOverlay onClose={onClose}>
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-white/[0.02]">
        <h2 className="text-[17px] font-semibold tracking-tight text-white flex items-center gap-2">
          <Key className="w-4 h-4 text-purple-400" />
          Generate Access Token
        </h2>
        <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 transition-colors">
          <X className="w-4 h-4" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Token Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. CI/CD Pipeline, Production Bot"
            className={clsx(
              'w-full px-4 py-2.5 rounded-xl border border-white/10 bg-black/40',
              'text-white text-sm placeholder-gray-600 focus:outline-none',
              'focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all'
            )}
            disabled={loading}
            autoFocus
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-3">
            <Shield className="w-4 h-4 inline mr-1.5 opacity-70" />
            Authorization Scope
          </label>
          <div className="space-y-2">
            {(['admin', 'editor', 'viewer'] as const).map((perm) => (
              <label
                key={perm}
                className={clsx(
                  'flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all duration-200',
                  permission === perm
                    ? 'border-purple-500/50 bg-purple-500/10 shadow-[inner_0_0_0_1px_rgba(168,85,247,0.2)]'
                    : 'border-white/10 bg-white/[0.02] hover:bg-white/[0.04]'
                )}
              >
                <input
                  type="radio"
                  name="permission"
                  value={perm}
                  checked={permission === perm}
                  onChange={() => setPermission(perm)}
                  className="hidden"
                />
                <div className={clsx(
                  "w-4 h-4 rounded-full border flex items-center justify-center flex-shrink-0 transition-colors",
                  permission === perm ? "border-purple-500 bg-purple-500" : "border-gray-600"
                )}>
                  {permission === perm && <div className="w-1.5 h-1.5 bg-white rounded-full" />}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white text-sm">{PERMISSION_LABELS[perm]}</span>
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {perm === 'admin' && 'Full root access. Can delete workspaces and manage billing.'}
                    {perm === 'editor' && 'Standard access. Can read, write, and modify memory blocks.'}
                    {perm === 'viewer' && 'Strict read-only access. Cannot create or alter data.'}
                  </p>
                </div>
              </label>
            ))}
          </div>
        </div>

        {error && <div className="text-red-400 text-sm font-medium">{error}</div>}

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} disabled={loading} className="px-4 py-2.5 rounded-xl font-medium text-sm text-gray-400 hover:text-white hover:bg-white/10 transition-colors">
            Cancel
          </button>
          <button type="submit" disabled={loading || !name.trim()} className={clsx(
              'px-5 py-2.5 rounded-xl font-semibold text-sm transition-all',
              'bg-white text-black hover:bg-gray-200',
              (loading || !name.trim()) ? 'opacity-50 cursor-not-allowed' : 'shadow-[0_0_15px_rgba(255,255,255,0.2)]'
            )}>
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Generate Token'}
          </button>
        </div>
      </form>
    </ModalOverlay>
  );
}

function NewKeyResultModal({ keyData, onClose }: { keyData: CreateKeyResponse; onClose: () => void }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    await navigator.clipboard.writeText(keyData.key).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <ModalOverlay>
      <div className="p-6">
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shadow-[0_0_30px_rgba(16,185,129,0.2)]">
            <Check className="w-8 h-8 text-emerald-400" />
          </div>
        </div>
        
        <h2 className="text-xl font-bold text-center text-white mb-2">Token Generated</h2>
        <p className="text-sm text-center text-emerald-400 font-medium mb-6">
          Please copy this token now. You will not be able to see it again.
        </p>

        <div className="bg-black/50 border border-white/10 rounded-xl p-1 mb-6 flex items-center">
          <code className="flex-1 px-4 text-[13px] font-mono text-white tracking-wider overflow-x-auto scrollbar-hide py-2">
            {keyData.key}
          </code>
          <button onClick={handleCopy} className={clsx(
              "px-4 py-2 ml-1 rounded-lg text-sm font-semibold transition-all flex items-center gap-2",
              copied ? "bg-emerald-500 text-white" : "bg-white/10 text-white hover:bg-white/20"
            )}>
            {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>

        <button onClick={onClose} className="w-full py-3 rounded-xl bg-white text-black font-semibold text-sm hover:bg-gray-200 transition-colors">
          I have securely stored this token
        </button>
      </div>
    </ModalOverlay>
  );
}

function DeleteKeyModal({ keyData, onClose, onDeleted }: { keyData: ApiKey; onClose: () => void; onDeleted: () => void }) {
  const [loading, setLoading] = useState(false);
  const [confirmName, setConfirmName] = useState('');
  
  const handleDelete = async () => {
    if (confirmName !== keyData.name) return;
    setLoading(true);
    try {
      await api.revokeKey(keyData.id, true);
      onDeleted();
    } catch (err) {} finally {
      setLoading(false);
    }
  };

  return (
    <ModalOverlay onClose={onClose}>
      <div className="p-6">
        <div className="flex items-center gap-3 text-red-400 mb-4">
          <AlertTriangle className="w-6 h-6" />
          <h2 className="text-xl font-bold text-white">Revoke Token</h2>
        </div>
        
        <p className="text-sm text-gray-400 mb-6 leading-relaxed">
          This will permanently disable <strong className="text-white">"{keyData.name}"</strong>. 
          Any agents or applications using this token will lose access to Remembra immediately. This action cannot be undone.
        </p>

        <div className="mb-6">
          <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Type "{keyData.name}" to confirm
          </label>
          <input
            type="text"
            value={confirmName}
            onChange={(e) => setConfirmName(e.target.value)}
            className="w-full px-4 py-2.5 rounded-xl border border-red-500/30 bg-red-500/5 text-white text-sm focus:outline-none focus:border-red-500/50 focus:ring-1 focus:ring-red-500/50"
            autoFocus
          />
        </div>

        <div className="flex justify-end gap-3">
          <button onClick={onClose} className="px-5 py-2.5 rounded-xl font-medium text-sm text-gray-400 hover:text-white hover:bg-white/10 transition-colors">
            Cancel
          </button>
          <button 
            onClick={handleDelete} 
            disabled={loading || confirmName !== keyData.name} 
            className="px-5 py-2.5 rounded-xl font-semibold text-sm bg-red-500 text-white hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
            Revoke Permanently
          </button>
        </div>
      </div>
    </ModalOverlay>
  );
}
