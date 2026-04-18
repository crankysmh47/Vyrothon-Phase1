'use client';

import React, { useState, useCallback } from 'react';
import { Upload, User, Image as ImageIcon, CheckCircle, AlertCircle, Loader2, Camera } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE_URL = 'http://localhost:8000';

export default function GrabPicDashboard() {
  // State for Ingestion
  const [ingestFile, setIngestFile] = useState<File | null>(null);
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestResult, setIngestResult] = useState<any>(null);

  // State for Auth
  const [authFile, setAuthFile] = useState<File | null>(null);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [authData, setAuthData] = useState<any>(null);
  const [photos, setPhotos] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Handle Ingestion
  const handleIngest = async () => {
    if (!ingestFile) return;
    setIsIngesting(true);
    setIngestResult(null);
    setError(null);

    const formData = new FormData();
    formData.append('file', ingestFile);

    try {
      const response = await fetch(`${API_BASE_URL}/ingest`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Ingestion failed');
      const data = await response.json();
      setIngestResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsIngesting(false);
    }
  };

  // Handle Authentication
  const handleAuth = async () => {
    if (!authFile) return;
    setIsAuthenticating(true);
    setAuthData(null);
    setPhotos([]);
    setError(null);

    const formData = new FormData();
    formData.append('file', authFile);

    try {
      const response = await fetch(`${API_BASE_URL}/auth`, {
        method: 'POST',
        body: formData,
      });

      if (response.status === 401) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Access Denied');
      }

      const data = await response.json();
      setAuthData(data);

      if (data.grab_id) {
        // Fetch images
        const imagesRes = await fetch(`${API_BASE_URL}/images/${data.grab_id}`);
        const imagesData = await imagesRes.json();
        setPhotos(imagesData.images || []);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsAuthenticating(false);
    }
  };

  return (
    <main className="min-h-screen p-8 max-w-7xl mx-auto space-y-12 pb-24">
      {/* Header */}
      <header className="text-center space-y-4 pt-12">
        <motion.h1 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-7xl font-black tracking-tighter bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent"
        >
          GRABPIC
        </motion.h1>
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="text-xl text-slate-400 font-medium"
        >
          Selfie-as-a-Key Retrieval Engine
        </motion.p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Ingestion Section */}
        <section className="glass rounded-3xl p-8 space-y-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <ImageIcon className="text-purple-400" size={24} />
            </div>
            <h2 className="text-2xl font-bold">Event Ingestion</h2>
          </div>
          
          <p className="text-slate-400 text-sm">Upload raw event photos to index unique biometric identities.</p>

          <div 
            className="border-2 border-dashed border-slate-700/50 rounded-2xl p-10 flex flex-col items-center justify-center space-y-4 hover:border-purple-500/50 transition-colors cursor-pointer group"
            onClick={() => document.getElementById('ingest-input')?.click()}
          >
            <input 
              id="ingest-input"
              type="file" 
              className="hidden" 
              onChange={(e) => setIngestFile(e.target.files?.[0] || null)}
            />
            {ingestFile ? (
              <div className="flex items-center space-x-2 text-purple-400">
                <CheckCircle size={20} />
                <span className="font-mono">{ingestFile.name}</span>
              </div>
            ) : (
              <Upload className="text-slate-500 group-hover:text-purple-400 transition-colors" size={48} />
            )}
            <p className="text-slate-500 text-sm font-medium">Click to browse or drag and drop</p>
          </div>

          <button
            onClick={handleIngest}
            disabled={!ingestFile || isIngesting}
            className="w-full py-4 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-xl font-bold transition-all flex items-center justify-center space-x-2"
          >
            {isIngesting ? <Loader2 className="animate-spin" /> : <span>Start Ingestion</span>}
          </button>

          <AnimatePresence>
            {ingestResult && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="bg-green-500/10 border border-green-500/20 rounded-xl p-4 text-green-400 text-sm"
              >
                Successfully indexed {ingestResult.faces_detected} new identities.
              </motion.div>
            )}
          </AnimatePresence>
        </section>

        {/* Auth Section */}
        <section className="glass rounded-3xl p-8 space-y-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-2 bg-cyan-500/20 rounded-lg">
              <Camera className="text-cyan-400" size={24} />
            </div>
            <h2 className="text-2xl font-bold">Find My Photos</h2>
          </div>
          
          <p className="text-slate-400 text-sm">Upload a selfie to unlock your personalized image gallery.</p>

          <div 
            className="border-2 border-dashed border-slate-700/50 rounded-2xl p-10 flex flex-col items-center justify-center space-y-4 hover:border-cyan-500/50 transition-colors cursor-pointer group"
            onClick={() => document.getElementById('auth-input')?.click()}
          >
            <input 
              id="auth-input"
              type="file" 
              className="hidden" 
              onChange={(e) => setAuthFile(e.target.files?.[0] || null)}
            />
            {authFile ? (
              <div className="flex items-center space-x-2 text-cyan-400">
                <CheckCircle size={20} />
                <span className="font-mono">{authFile.name}</span>
              </div>
            ) : (
              <User className="text-slate-500 group-hover:text-cyan-400 transition-colors" size={48} />
            )}
            <p className="text-slate-500 text-sm font-medium">Capture or upload your selfie</p>
          </div>

          <button
            onClick={handleAuth}
            disabled={!authFile || isAuthenticating}
            className="w-full py-4 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white rounded-xl font-bold transition-all flex items-center justify-center space-x-2"
          >
            {isAuthenticating ? <Loader2 className="animate-spin" /> : <span>Verify Identity</span>}
          </button>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-red-400 text-sm flex items-start space-x-2">
              <AlertCircle size={16} className="mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </section>
      </div>

      {/* Results Display */}
      <AnimatePresence>
        {authData && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
          >
            <div className="glass rounded-3xl p-8 flex flex-col md:flex-row items-center justify-between gap-8">
              <div className="flex items-center space-x-6">
                <div className="relative">
                  <div className="w-24 h-24 rounded-full overflow-hidden border-2 border-purple-500 auth-ring">
                    <img 
                      src={authFile ? URL.createObjectURL(authFile) : ''} 
                      className="w-full h-full object-cover"
                      alt="Authenticated selfie"
                    />
                  </div>
                  <div className="absolute -bottom-1 -right-1 bg-green-500 rounded-full p-1 border-2 border-slate-900">
                    <CheckCircle size={16} className="text-white" />
                  </div>
                </div>
                <div>
                  <h3 className="text-2xl font-bold">Biometric Match Locked</h3>
                  <div className="text-slate-400 font-mono text-sm mt-1">ID: {authData.grab_id}</div>
                </div>
              </div>
              
              <div className="text-right">
                <div className="text-slate-500 uppercase text-xs font-bold tracking-widest">Similarity Score</div>
                <div className="text-4xl font-black text-cyan-400 italic">
                  {(authData.similarity_score * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            {/* Photo Gallery Grid */}
            <div className="space-y-4">
              <h3 className="text-xl font-bold flex items-center space-x-2">
                <ImageIcon size={20} className="text-purple-400" />
                <span>Your Professional Gallery ({photos.length} photos)</span>
              </h3>
              
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {photos.map((url, i) => (
                  <motion.div 
                    key={i}
                    whileHover={{ scale: 1.05 }}
                    className="aspect-square relative rounded-2xl overflow-hidden glass group cursor-zoom-in"
                  >
                    <img 
                      src={url} 
                      className="w-full h-full object-cover transition-transform duration-500 group-hover:rotate-2" 
                      alt={`Gallery item ${i}`}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-900/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  </motion.div>
                ))}
              </div>

              {photos.length === 0 && (
                <div className="text-center py-20 bg-slate-800/20 rounded-3xl border border-slate-800">
                  <p className="text-slate-500 font-medium">No associated photos found for this identity.</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}
