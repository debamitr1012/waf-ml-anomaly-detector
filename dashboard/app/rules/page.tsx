'use client';

import { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import { apiClient } from '@/lib/api-client';
import { SecurityRule } from '@/types';
import { Shield, Download, Plus, CheckCircle } from 'lucide-react';

export default function RulesPage() {
  const [rules, setRules] = useState<SecurityRule[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      const data = await apiClient.getRules();
      setRules(data.rules || []);
    } catch (error) {
      console.error('Failed to fetch rules:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateRules = async () => {
    setIsGenerating(true);
    try {
      const result = await apiClient.generateRules({ confidence_threshold: 0.7, max_rules: 10 });
      setRules([...result.rules, ...rules]);
    } catch (error) {
      console.error('Failed to generate rules:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleExport = async (format: 'json' | 'modsecurity' | 'nginx') => {
    try {
      const result = await apiClient.exportRules(format);
      const blob = new Blob([result.content], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `waf_rules_${Date.now()}.${format === 'json' ? 'json' : 'conf'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export rules:', error);
    }
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critical: 'bg-red-100 text-red-800 border-red-300',
      high: 'bg-orange-100 text-orange-800 border-orange-300',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      low: 'bg-blue-100 text-blue-800 border-blue-300',
    };
    return colors[severity] || colors.medium;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <main className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Shield className="text-purple-600" />
            Security Rules
          </h1>
          <div className="flex gap-3">
            <button
              onClick={handleGenerateRules}
              disabled={isGenerating}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
            >
              <Plus size={20} />
              {isGenerating ? 'Generating...' : 'Generate Rules'}
            </button>
            <div className="relative group">
              <button className="flex items-center gap-2 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-800 transition-colors">
                <Download size={20} />
                Export
              </button>
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                <button onClick={() => handleExport('json')} className="block w-full text-left px-4 py-2 hover:bg-gray-100">JSON Format</button>
                <button onClick={() => handleExport('modsecurity')} className="block w-full text-left px-4 py-2 hover:bg-gray-100">ModSecurity</button>
                <button onClick={() => handleExport('nginx')} className="block w-full text-left px-4 py-2 hover:bg-gray-100">NGINX</button>
              </div>
            </div>
          </div>
        </div>

        {rules.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <Shield size={48} className="mx-auto text-gray-400 mb-4" />
            <h3 className="text-xl font-semibold text-gray-700 mb-2">No Rules Yet</h3>
            <p className="text-gray-600 mb-6">Generate security rules from detected anomalies</p>
            <button
              onClick={handleGenerateRules}
              className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              Generate Your First Rules
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {rules.map((rule) => (
              <div key={rule.id} className="bg-white rounded-lg shadow-md p-6 card-hover">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getSeverityColor(rule.severity)}`}>
                        {rule.severity.toUpperCase()}
                      </span>
                      <span className="px-3 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-800">
                        {rule.attack_type}
                      </span>
                      <span className="text-sm text-gray-500">
                        Confidence: {(rule.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      Rule #{rule.rule_id}
                    </h3>
                    <p className="text-gray-700">{rule.description}</p>
                  </div>
                  <CheckCircle className="text-green-500" size={24} />
                </div>

                <div className="border-t pt-4">
                  <details className="cursor-pointer">
                    <summary className="font-medium text-gray-700 mb-2">View Rule Formats</summary>
                    <div className="mt-4 space-y-3">
                      <div>
                        <div className="text-sm font-medium text-gray-600 mb-1">ModSecurity Format:</div>
                        <pre className="bg-gray-100 p-3 rounded text-xs overflow-x-auto">
                          {rule.formats?.modsecurity}
                        </pre>
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-600 mb-1">NGINX Format:</div>
                        <pre className="bg-gray-100 p-3 rounded text-xs overflow-x-auto">
                          {rule.formats?.nginx}
                        </pre>
                      </div>
                    </div>
                  </details>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
