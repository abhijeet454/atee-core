"use client";

import React, { useState, useEffect, useRef } from "react";
import SpeechRecognition, { useSpeechRecognition } from "react-speech-recognition";
import { Mic, MicOff, Send, Activity } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import "regenerator-runtime/runtime";

export default function Home() {
  const [mounted, setMounted] = useState(false);
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);

  useEffect(() => {
    setMounted(true);
  }, []);
  const [inputText, setInputText] = useState("");
  const [isWakeWordActive, setIsWakeWordActive] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [wakeWordMatch, setWakeWordMatch] = useState("");
  const [manualMic, setManualMic] = useState(false);
  const [wakeEnabled, setWakeEnabled] = useState(false);
  const wakeCommandStartRef = useRef<number | null>(null);

  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition,
  } = useSpeechRecognition();

  const ws = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Connect to WebSocket
  useEffect(() => {
    ws.current = new WebSocket("ws://localhost:8000/api/v1/voice/stream");

    ws.current.onopen = () => {
      console.log("WebSocket connected");
      setIsConnected(true);
    };

    ws.current.onmessage = (event) => {
      // In a full implementation, we'd handle binary TTS streams here
      try {
        const data = JSON.parse(event.data);
        if (data.chunk) {
           // Handle streaming chat chunk
        }
      } catch (e) {
        // Binary audio data
      }
    };

    ws.current.onclose = () => {
      console.log("WebSocket disconnected");
      setIsConnected(false);
    };

    return () => {
      ws.current?.close();
    };
  }, []);

  // Continuous Wake Word Detection
  useEffect(() => {
    if (!wakeEnabled) return;
    if (!manualMic && browserSupportsSpeechRecognition && !listening) {
      SpeechRecognition.startListening({ continuous: true, language: "hi-IN" }).catch((e: unknown) => {
        console.error("Failed to start wake-word listening:", e);
        setWakeEnabled(false);
      });
    }
  }, [listening, manualMic, browserSupportsSpeechRecognition]);

  const enableWakeWord = async () => {
    if (!browserSupportsSpeechRecognition) return;
    try {
      resetTranscript();
      wakeCommandStartRef.current = null;
      setWakeEnabled(true);
      await SpeechRecognition.startListening({ continuous: true, language: "hi-IN" });
    } catch (e) {
      console.error("Enable wake word failed:", e);
      setWakeEnabled(false);
    }
  };

  const toggleMic = async () => {
    if (!browserSupportsSpeechRecognition) return;
    if (listening) {
      SpeechRecognition.stopListening();
      setManualMic(false);
      return;
    }
    // Manual “push-to-talk” style: start listening, user speaks, silence detector auto-submits.
    setManualMic(true);
    resetTranscript();
    wakeCommandStartRef.current = 0;
    await SpeechRecognition.startListening({ continuous: true, language: "hi-IN" });
  };

  useEffect(() => {
    if (!wakeEnabled) return;
    if (manualMic) return; // manual mic doesn't need wake word
    if (isWakeWordActive) return;

    const lowerTranscript = transcript.toLowerCase();
    // Require a greeting + name to reduce false positives.
    // Matches: "hi atee", "hey atte", "hello ati", "oye aarti", etc.
    const wakeRegex = /\b(hi|hey|hello|hlo|namaste|oye)\s+(atee|atte|ati|aati|aarti)\b/;
    const match = lowerTranscript.match(wakeRegex);
    if (!match || match.index === undefined) return;

    const matchedText = match[0];
    const start = match.index + matchedText.length;
    wakeCommandStartRef.current = start;
    setIsWakeWordActive(true);
    setWakeWordMatch(matchedText);
    console.log("Wake word detected:", matchedText);
  }, [transcript, isWakeWordActive]);

  // Silence detection for auto-submit
  useEffect(() => {
    let timeout: NodeJS.Timeout;
    if ((isWakeWordActive || manualMic) && transcript) {
      timeout = setTimeout(() => {
        const start = wakeCommandStartRef.current ?? 0;
        const command = transcript.slice(start).trim();
        // Filter out tiny/noise commands
        if (command.length > 2) {
          submitCommand(command);
          resetTranscript();
        }
      }, 2000); // 2 seconds of silence
    }
    return () => clearTimeout(timeout);
  }, [transcript, isWakeWordActive, wakeWordMatch]);

  const submitCommand = async (text: string) => {
    if (!text.trim()) return;
    
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInputText("");
    setIsWakeWordActive(false);
    setWakeWordMatch("");
    wakeCommandStartRef.current = null;

    try {
      const res = await fetch("http://localhost:8000/api/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, include_memory: true }),
      });
      
      if (!res.ok) throw new Error("Chat failed");
      
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "assistant", content: data.response }]);
      
      // Fetch TTS
      const audioRes = await fetch(`http://localhost:8000/api/v1/voice/speak?text=${encodeURIComponent(data.response)}`, {
        method: "POST"
      });
      if (audioRes.ok) {
        const audioBlob = await audioRes.blob();
        if (audioBlob.size > 0) {
          const audioUrl = URL.createObjectURL(audioBlob);
          const audio = new Audio(audioUrl);
          audio.play().catch(e => console.error("Audio playback failed:", e));
        } else {
          console.warn("Received empty audio blob from TTS engine.");
        }
      }
    } catch (err) {
      console.error(err);
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, I encountered an error." }]);
    }
  };

  if (!mounted) return null;

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col font-sans">
      <header className="flex items-center justify-between p-6 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="bg-indigo-600 p-2 rounded-lg">
            <Activity className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Atee (Hindi)</h1>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-emerald-500" : "bg-red-500"}`} />
          {isConnected ? "Backend Connected" : "Backend Disconnected"}
        </div>
      </header>

      <main className="flex-1 overflow-y-auto p-6 space-y-6">
        <AnimatePresence>
          {messages.map((m, i) => (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              key={i}
              className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-2xl p-4 rounded-2xl ${
                  m.role === "user"
                    ? "bg-indigo-600 text-white rounded-br-none"
                    : "bg-gray-800 text-gray-100 rounded-bl-none shadow-lg shadow-black/20 border border-gray-700"
                }`}
              >
                {m.content}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </main>

      <div className="flex justify-center p-4">
        <motion.div
          animate={isWakeWordActive ? { scale: [1, 1.05, 1], boxShadow: "0 0 20px rgba(99, 102, 241, 0.4)" } : {}}
          transition={{ repeat: isWakeWordActive ? Infinity : 0, duration: 1.5 }}
          className={`flex items-center gap-3 px-6 py-3 rounded-full transition-colors ${
            isWakeWordActive ? "bg-indigo-900/80 border border-indigo-500 text-indigo-100" : "bg-gray-900 border border-gray-800 text-gray-400"
          }`}
        >
          {browserSupportsSpeechRecognition ? (
            <>
              {listening ? (
                 <Mic className={isWakeWordActive ? "text-indigo-400" : "text-gray-500"} />
              ) : (
                 <MicOff className="text-red-500" />
              )}
              <span className="text-sm font-medium">
                {!wakeEnabled
                  ? "Wake word is off — click Enable"
                  : isWakeWordActive
                    ? "Atee is listening..."
                    : `Say "Hi Atee" to wake`}
              </span>
              {!wakeEnabled && (
                <button
                  type="button"
                  onClick={enableWakeWord}
                  className="ml-2 bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1 rounded-lg text-xs font-medium"
                >
                  Enable
                </button>
              )}
            </>
          ) : (
            <>
              <MicOff className="text-gray-600" />
              <span className="text-sm font-medium text-gray-500">
                Speech Recognition unsupported (Use Chrome)
              </span>
            </>
          )}
        </motion.div>
      </div>

      <div className="p-6 bg-gray-900 border-t border-gray-800">
        <div className="max-w-4xl mx-auto flex gap-4">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submitCommand(inputText)}
            placeholder="Or type your message in Hindi/Hinglish..."
            className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-6 py-4 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all text-lg placeholder-gray-500"
          />
          <button
            type="button"
            onClick={toggleMic}
            disabled={!browserSupportsSpeechRecognition}
            className={`px-5 py-4 rounded-xl font-medium transition-all shadow-lg flex items-center gap-2 border ${
              browserSupportsSpeechRecognition
                ? listening
                  ? "bg-emerald-600 hover:bg-emerald-500 text-white border-emerald-500"
                  : "bg-gray-800 hover:bg-gray-700 text-gray-100 border-gray-700"
                : "bg-gray-800 text-gray-500 border-gray-800 cursor-not-allowed"
            }`}
            title={browserSupportsSpeechRecognition ? (listening ? "Stop microphone" : "Start microphone") : "Speech Recognition unsupported (Use Chrome)"}
          >
            {listening ? <Mic className="w-5 h-5" /> : <MicOff className="w-5 h-5" />}
            <span className="hidden sm:inline">{listening ? "Mic On" : "Mic Off"}</span>
          </button>
          <button
            onClick={() => submitCommand(inputText)}
            className="bg-indigo-600 hover:bg-indigo-500 text-white px-8 py-4 rounded-xl font-medium transition-all shadow-lg flex items-center gap-2"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
