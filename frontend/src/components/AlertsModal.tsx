import React, { useState, useEffect } from 'react';
import { fetchWebhooks, createWebhook, deleteWebhook, testWebhook, updateWebhook } from '../api/client';
import type { WebhookAlert, WebhookAlertCreate } from '../types';

interface AlertsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AlertsModal: React.FC<AlertsModalProps> = ({ isOpen, onClose }) => {
  const [webhooks, setWebhooks] = useState<WebhookAlert[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [url, setUrl] = useState('');
  const [provider, setProvider] = useState<'discord' | 'slack' | 'generic'>('discord');
  const [countriesInput, setCountriesInput] = useState('');

  const loadWebhooks = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchWebhooks();
      setWebhooks(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadWebhooks();
    }
  }, [isOpen]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setError(null);
      const countries = countriesInput.split(',').map(c => c.trim()).filter(c => c.length > 0);
      
      const payload: WebhookAlertCreate = {
        url,
        provider,
        min_threat_level: 'High',
        is_active: true,
        countries: countries.length > 0 ? countries : undefined,
      };

      await createWebhook(payload);
      setUrl('');
      setCountriesInput('');
      await loadWebhooks();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this alert?')) return;
    try {
      setError(null);
      await deleteWebhook(id);
      await loadWebhooks();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  const handleTest = async (id: string) => {
    try {
      setError(null);
      await testWebhook(id);
      alert('Test payload sent successfully!');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  const handleToggleActive = async (webhook: WebhookAlert) => {
    try {
      setError(null);
      await updateWebhook(webhook.id, { is_active: !webhook.is_active });
      await loadWebhooks();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex justify-center items-center backdrop-blur-sm">
      <div className="bg-gray-800 rounded-xl shadow-2xl w-full max-w-3xl overflow-hidden flex flex-col max-h-[85vh] border border-gray-700">
        <div className="p-4 border-b border-gray-700 flex justify-between items-center bg-gray-900">
          <h2 className="text-xl font-bold text-white flex items-center">
            <span className="text-red-500 mr-2">🔔</span> Webhook Alerts
          </h2>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 flex flex-col space-y-6">
          {error && (
            <div className="bg-red-500 bg-opacity-10 border border-red-500 text-red-500 p-3 rounded text-sm">
              {error}
            </div>
          )}

          {/* Create Form */}
          <form onSubmit={handleCreate} className="bg-gray-700 p-4 rounded-lg space-y-4">
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Create New Alert</h3>
            
            <div className="flex space-x-4">
              <div className="flex-1">
                <label className="block text-xs text-gray-400 mb-1">Webhook URL</label>
                <input 
                  type="url" 
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://hooks.slack.com/..."
                  className="w-full bg-gray-900 text-white border border-gray-600 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
                  required
                />
              </div>
              
              <div className="w-1/3">
                <label className="block text-xs text-gray-400 mb-1">Provider</label>
                <select 
                  value={provider}
                  onChange={(e) => setProvider(e.target.value as any)}
                  className="w-full bg-gray-900 text-white border border-gray-600 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value="discord">Discord</option>
                  <option value="slack">Slack</option>
                  <option value="generic">Generic JSON</option>
                </select>
              </div>
            </div>

            <div className="flex space-x-4">
              <div className="flex-1">
                <label className="block text-xs text-gray-400 mb-1">Target Countries (comma-separated ISO codes)</label>
                <input 
                  type="text" 
                  value={countriesInput}
                  onChange={(e) => setCountriesInput(e.target.value)}
                  placeholder="e.g. US, UA, RU (Leave empty for all)"
                  className="w-full bg-gray-900 text-white border border-gray-600 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <button 
              type="submit" 
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded transition-colors text-sm"
            >
              Add Alert
            </button>
          </form>

          {/* List Webhooks */}
          <div>
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">Active Alerts</h3>
            
            {loading ? (
              <div className="text-gray-400 text-sm text-center py-4">Loading...</div>
            ) : webhooks.length === 0 ? (
              <div className="text-gray-500 text-sm text-center py-4 bg-gray-700 rounded-lg">No webhooks configured.</div>
            ) : (
              <div className="space-y-3">
                {webhooks.map((wh) => (
                  <div key={wh.id} className="bg-gray-700 border border-gray-600 p-4 rounded-lg flex items-center justify-between">
                    <div className="flex-1 overflow-hidden pr-4">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="text-xs uppercase bg-gray-800 text-gray-300 px-2 py-0.5 rounded font-mono">
                          {wh.provider}
                        </span>
                        {wh.countries && (
                          <span className="text-xs uppercase bg-blue-900 bg-opacity-30 text-blue-400 px-2 py-0.5 rounded font-mono border border-blue-800">
                            🌍 {wh.countries.join(', ')}
                          </span>
                        )}
                        <span className={`text-xs px-2 py-0.5 rounded ${wh.is_active ? 'bg-green-900 text-green-400' : 'bg-red-900 text-red-400'}`}>
                          {wh.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                      <div className="text-gray-300 text-sm truncate opacity-70" title={wh.url}>
                        {wh.url}
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <button 
                        onClick={() => handleTest(wh.id)}
                        className="text-xs bg-gray-600 hover:bg-gray-500 text-white px-3 py-1.5 rounded transition-colors"
                        title="Send Test Event"
                      >
                        Test
                      </button>
                      <button 
                        onClick={() => handleToggleActive(wh)}
                        className="text-xs bg-gray-600 hover:bg-gray-500 text-white px-3 py-1.5 rounded transition-colors"
                      >
                        {wh.is_active ? 'Disable' : 'Enable'}
                      </button>
                      <button 
                        onClick={() => handleDelete(wh.id)}
                        className="text-xs bg-red-600 hover:bg-red-500 text-white px-3 py-1.5 rounded transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
};
