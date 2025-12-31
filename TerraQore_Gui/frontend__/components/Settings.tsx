import React, { useEffect, useMemo, useState } from 'react';
import terraqoreAPI, { LLMConfigSnapshot, LLMConfigUpdate, LLMProviderInfo } from '../services/terraqoreAPIService';

interface FormState {
  primary_provider: string;
  model: string;
  api_key: string;
  temperature: number;
  max_tokens: number;
  fallback_provider: string;
  fallback_model: string;
  fallback_api_key: string;
  fallback_temperature: number;
  fallback_max_tokens: number;
}

const Settings: React.FC = () => {
  const [providers, setProviders] = useState<LLMProviderInfo[]>([]);
  const [form, setForm] = useState<FormState>({
    primary_provider: 'gemini',
    model: '',
    api_key: '',
    temperature: 0.7,
    max_tokens: 4096,
    fallback_provider: '',
    fallback_model: '',
    fallback_api_key: '',
    fallback_temperature: 0.7,
    fallback_max_tokens: 2048,
  });
  const [configSnapshot, setConfigSnapshot] = useState<LLMConfigSnapshot | null>(null);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<any>(null);

  const providerDefaults = useMemo(() => {
    const map: Record<string, string> = {};
    providers.forEach((p) => {
      if (p.default_model) map[p.id] = p.default_model;
    });
    return map;
  }, [providers]);

  const providerInfo: Record<string, { name: string; description: string; setupInstructions: string }> = {
    gemini: {
      name: 'Google Gemini',
      description: 'Google\'s latest AI models with strong reasoning capabilities',
      setupInstructions: 'Get your free API key from https://aistudio.google.com/app/apikey'
    },
    groq: {
      name: 'Groq',
      description: 'Ultra-fast inference with open-source models',
      setupInstructions: 'Get your API key from https://console.groq.com/keys'
    },
    openrouter: {
      name: 'OpenRouter',
      description: 'Access 200+ models through a single API',
      setupInstructions: 'Get your API key from https://openrouter.ai/keys'
    },
    ollama: {
      name: 'Ollama (Local)',
      description: 'Run models locally on your machine with complete privacy',
      setupInstructions: 'Install Ollama from https://ollama.ai and pull models like: ollama pull phi3'
    }
  };

  const resolveModel = (providerId: string, modelValue?: string) => {
    if (modelValue && modelValue.trim()) return modelValue;
    return providerDefaults[providerId] || '';
  };

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const [providerList, cfg] = await Promise.all([
          terraqoreAPI.listLLMProviders(),
          terraqoreAPI.getLLMConfig(),
        ]);
        const defaults = providerList.reduce<Record<string, string>>((acc, p) => {
          acc[p.id] = p.default_model || '';
          return acc;
        }, {});
        setProviders(providerList);
        setConfigSnapshot(cfg);
        setForm((prev) => ({
          ...prev,
          primary_provider: cfg.primary_provider,
          model: cfg.primary_model || defaults[cfg.primary_provider] || prev.model,
          temperature: cfg.primary_temperature ?? 0.7,
          max_tokens: cfg.primary_max_tokens ?? 4096,
          fallback_provider: cfg.fallback_provider || '',
          fallback_model: cfg.fallback_model || (cfg.fallback_provider ? defaults[cfg.fallback_provider] : ''),
          fallback_temperature: cfg.fallback_temperature ?? 0.7,
          fallback_max_tokens: cfg.fallback_max_tokens ?? 2048,
        }));
      } catch (err: any) {
        setError(err?.message || 'Failed to load LLM configuration');
      }
    };

    bootstrap();
  }, []);

  const updateField = (key: keyof FormState, value: any) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    setStatus(null);
    setError(null);
    setHealth(null);

    try {
      const payload: LLMConfigUpdate = {
        primary_provider: form.primary_provider,
        model: resolveModel(form.primary_provider, form.model),
        api_key: form.api_key.trim() || undefined,
        temperature: form.temperature,
        max_tokens: form.max_tokens,
        fallback_provider: form.fallback_provider || null,
        fallback_model: form.fallback_provider ? resolveModel(form.fallback_provider, form.fallback_model) : null,
        fallback_api_key: form.fallback_provider ? form.fallback_api_key.trim() || undefined : undefined,
        fallback_temperature: form.fallback_temperature,
        fallback_max_tokens: form.fallback_max_tokens,
      };

      const res = await terraqoreAPI.updateLLMConfig(payload);
      setHealth(res.llm_health);
      const latest = await terraqoreAPI.getLLMConfig();
      setConfigSnapshot(latest);
      setStatus('Saved and tested successfully.');
    } catch (err: any) {
      setError(err?.message || 'Save failed. Check provider, model, or API key.');
    } finally {
      setSaving(false);
    }
  };

  const currentProvider = providers.find((p) => p.id === form.primary_provider);
  const fallbackProvider = providers.find((p) => p.id === form.fallback_provider);

  const renderHealth = () => {
    if (!health) return null;
    const primary = health.primary || {};
    return (
      <div className="mt-4 rounded-xl border border-white/10 bg-white/5 p-4 text-xs text-zinc-200">
        <div className="flex items-center justify-between">
          <span className="font-semibold">Live health check</span>
          <span className={`text-[10px] uppercase font-bold ${primary.success ? 'text-emerald-400' : 'text-amber-400'}`}>
            {primary.success ? 'Healthy' : 'Check failed'}
          </span>
        </div>
        <p className="mt-2 text-zinc-400">{primary.message || primary.error || 'No message returned.'}</p>
        {form.fallback_provider && health.fallback && (
          <p className="mt-2 text-zinc-500">Fallback: {health.fallback.message || 'No message.'}</p>
        )}
      </div>
    );
  };

  return (
    <div className="flex-1 overflow-auto p-8 bg-gradient-to-br from-[#0b0b0f] via-[#0f0f14] to-[#060608] text-zinc-100">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[10px] uppercase tracking-[0.3em] text-zinc-500">LLM Connectivity</p>
            <h2 className="text-2xl font-semibold text-white">Choose your provider & keys</h2>
            <p className="text-sm text-zinc-500">Switch between Gemini, Groq, OpenRouter, or a local Ollama model. Keys are stored server-side and applied immediately.</p>
          </div>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 rounded-lg bg-purple-500/80 hover:bg-purple-500 text-white text-sm font-semibold shadow-lg shadow-purple-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : 'Save & Test'}
          </button>
        </div>

        {(status || error) && (
          <div className={`rounded-xl border p-4 text-sm ${error ? 'border-red-500/40 bg-red-500/10 text-red-100' : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-100'}`}>
            {error || status}
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-6">
          <div className="rounded-2xl border border-white/5 bg-white/5 p-5 backdrop-blur">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold">Primary provider</h3>
              {configSnapshot?.primary_api_key_set && (
                <span className="text-[11px] font-semibold text-emerald-400">✓ Connected</span>
              )}
            </div>

            {currentProvider && (
              <div className="mb-4 p-3 rounded-lg bg-black/20 border border-white/5">
                <p className="text-xs text-zinc-400 mb-1">{providerInfo[form.primary_provider]?.description}</p>
                {!currentProvider.requires_api_key && (
                  <p className="text-xs text-emerald-400 mt-2">✓ Local server - no API key required</p>
                )}
              </div>
            )}

            <label className="block mt-4 text-xs uppercase tracking-wide text-zinc-400">Provider</label>
            <select
              className="mt-1 w-full rounded-lg bg-black/40 border border-white/10 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              value={form.primary_provider}
              onChange={(e) => {
                const providerId = e.target.value;
                const defaultModel = resolveModel(providerId);
                updateField('primary_provider', providerId);
                updateField('model', defaultModel);
              }}
            >
              {providers.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>

            {currentProvider?.requires_api_key && (
              <>
                <label className="block mt-4 text-xs uppercase tracking-wide text-zinc-400">API key</label>
                <input
                  type="password"
                  className="mt-1 w-full rounded-lg bg-black/40 border border-white/10 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="Paste provider API key"
                  value={form.api_key}
                  onChange={(e) => updateField('api_key', e.target.value)}
                />
                {providerInfo[form.primary_provider] && (
                  <p className="mt-2 text-xs text-zinc-500">
                    {providerInfo[form.primary_provider].setupInstructions}
                  </p>
                )}
              </>
            )}

            <label className="block mt-4 text-xs uppercase tracking-wide text-zinc-400">Model</label>
            <input
              type="text"
              className="mt-1 w-full rounded-lg bg-black/40 border border-white/10 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder={currentProvider?.default_model || 'model name'}
              value={form.model}
              onChange={(e) => updateField('model', e.target.value)}
            />

            <div className="grid grid-cols-2 gap-3 mt-4">
              <div>
                <label className="block text-xs uppercase tracking-wide text-zinc-400">Temperature</label>
                <input
                  type="number"
                  step="0.1"
                  min={0}
                  max={2}
                  className="mt-1 w-full rounded-lg bg-black/40 border border-white/10 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                  value={form.temperature}
                  onChange={(e) => updateField('temperature', parseFloat(e.target.value))}
                />
              </div>
              <div>
                <label className="block text-xs uppercase tracking-wide text-zinc-400">Max tokens</label>
                <input
                  type="number"
                  min={1}
                  className="mt-1 w-full rounded-lg bg-black/40 border border-white/10 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                  value={form.max_tokens}
                  onChange={(e) => updateField('max_tokens', parseInt(e.target.value, 10))}
                />
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-white/5 bg-white/5 p-5 backdrop-blur">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">Fallback provider (optional)</h3>
              {configSnapshot?.fallback_api_key_set && configSnapshot?.fallback_provider && (
                <span className="text-[11px] font-semibold text-emerald-400">Key saved</span>
              )}
            </div>

            <label className="block mt-4 text-xs uppercase tracking-wide text-zinc-400">Provider</label>
            <select
              className="mt-1 w-full rounded-lg bg-black/40 border border-white/10 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              value={form.fallback_provider}
              onChange={(e) => {
                const providerId = e.target.value;
                const defaultModel = providerId ? resolveModel(providerId) : '';
                updateField('fallback_provider', providerId);
                updateField('fallback_model', defaultModel);
              }}
            >
              <option value="">None</option>
              {providers.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>

            {form.fallback_provider && fallbackProvider?.requires_api_key && (
              <>
                <label className="block mt-4 text-xs uppercase tracking-wide text-zinc-400">Fallback API key</label>
                <input
                  type="password"
                  className="mt-1 w-full rounded-lg bg-black/40 border border-white/10 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="Paste fallback API key"
                  value={form.fallback_api_key}
                  onChange={(e) => updateField('fallback_api_key', e.target.value)}
                />
              </>
            )}

            {form.fallback_provider && (
              <>
                <label className="block mt-4 text-xs uppercase tracking-wide text-zinc-400">Fallback model</label>
                <input
                  type="text"
                  className="mt-1 w-full rounded-lg bg-black/40 border border-white/10 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder={fallbackProvider?.default_model || 'model name'}
                  value={form.fallback_model}
                  onChange={(e) => updateField('fallback_model', e.target.value)}
                />

                <div className="grid grid-cols-2 gap-3 mt-4">
                  <div>
                    <label className="block text-xs uppercase tracking-wide text-zinc-400">Temperature</label>
                    <input
                      type="number"
                      step="0.1"
                      min={0}
                      max={2}
                      className="mt-1 w-full rounded-lg bg-black/40 border border-white/10 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                      value={form.fallback_temperature}
                      onChange={(e) => updateField('fallback_temperature', parseFloat(e.target.value))}
                    />
                  </div>
                  <div>
                    <label className="block text-xs uppercase tracking-wide text-zinc-400">Max tokens</label>
                    <input
                      type="number"
                      min={1}
                      className="mt-1 w-full rounded-lg bg-black/40 border border-white/10 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                      value={form.fallback_max_tokens}
                      onChange={(e) => updateField('fallback_max_tokens', parseInt(e.target.value, 10))}
                    />
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {renderHealth()}
      </div>
    </div>
  );
};

export default Settings;
