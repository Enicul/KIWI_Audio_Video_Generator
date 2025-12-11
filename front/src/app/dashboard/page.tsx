"use client";

import { useState, useRef, useEffect } from "react";
import { useUser } from "@clerk/nextjs";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  type: string;
  timestamp: string;
}

interface ConversationState {
  conversation_id: string;
  state: string;
  ai_response: string;
  needs_clarification: boolean;
  questions: string[];
  accumulated_intent: Record<string, unknown>;
  ready_to_generate: boolean;
  task_id?: string;
  messages: Message[];
}

interface TaskStatus {
  task_id: string;
  status: string;
  phase: string;
  progress: number;
  message: string;
  transcription?: string;
  result?: {
    video_url?: string;
    video_prompt?: string;
  };
  error?: string;
}

// Main phases of the app
type AppPhase = "welcome" | "chatting" | "generating" | "completed" | "error";

// Generation mode
type GenerationMode = "direct" | "discuss";

export default function DashboardPage() {
  const { user } = useUser();
  
  // App state
  const [appPhase, setAppPhase] = useState<AppPhase>("welcome");
  const [generationMode, setGenerationMode] = useState<GenerationMode>("discuss");
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // Conversation state
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [readyToGenerate, setReadyToGenerate] = useState(false);
  
  // Task state
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [transcription, setTranscription] = useState("");

  // Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Cleanup WebSocket
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // ========== Recording Functions ==========
  
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        stream.getTracks().forEach((track) => track.stop());

        const reader = new FileReader();
        reader.onloadend = async () => {
          const base64Audio = reader.result as string;
          
          if (generationMode === "direct") {
            // Direct generation - skip discussion
            await handleDirectGeneration("", base64Audio);
          } else {
            // Discussion mode - enter chat
            await handleFirstInput("", base64Audio);
          }
        };
        reader.readAsDataURL(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Microphone error:", error);
      setErrorMessage("Could not access microphone. Please check permissions.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // ========== Direct Generation (No Discussion) ==========
  
  const handleDirectGeneration = async (text: string, audioData?: string) => {
    if (!text && !audioData) return;

    setIsLoading(true);
    setAppPhase("generating");
    
    try {
      const response = await fetch("http://localhost:8000/api/video/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          audio_data: audioData || undefined,
          text_input: text || undefined,
        }),
      });

      if (!response.ok) throw new Error("Failed to create task");

      const data = await response.json();
      connectWebSocket(data.task_id);
    } catch (error) {
      console.error("Error:", error);
      setAppPhase("error");
      setErrorMessage("Failed to start video generation. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // ========== Discussion Mode (First Input) ==========
  
  const handleFirstInput = async (text: string, audioData?: string) => {
    if (!text && !audioData) return;

    setIsLoading(true);
    setAppPhase("chatting");

    const greeting: Message = {
      id: "greeting",
      role: "assistant",
      content: `Let me help you create your video! I'll ask a few questions to understand exactly what you want.`,
      type: "text",
      timestamp: new Date().toISOString(),
    };
    setMessages([greeting]);

    await sendMessage(text, audioData, true);
  };

  // ========== Chat Functions ==========
  
  const sendMessage = async (text: string, audioData?: string, isFirst: boolean = false) => {
    if (!text && !audioData) return;

    setIsLoading(true);

    if (text) {
      const userMessage: Message = {
        id: Date.now().toString(),
        role: "user",
        content: text,
        type: "text",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
    }

    try {
      const response = await fetch("http://localhost:8000/api/conversation/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: conversationId,
          message: text || undefined,
          audio_data: audioData || undefined,
          confirm_generate: false,
        }),
      });

      if (!response.ok) throw new Error("Failed to send message");

      const data: ConversationState = await response.json();

      if (!conversationId) {
        setConversationId(data.conversation_id);
      }

      // Show transcribed message
      if (audioData && !text) {
        const transcribedMsg = data.messages.filter(m => m.role === "user").pop();
        if (transcribedMsg) {
          const userMessage: Message = {
            id: transcribedMsg.id || Date.now().toString(),
            role: "user",
            content: transcribedMsg.content,
            type: "audio",
            timestamp: transcribedMsg.timestamp || new Date().toISOString(),
          };
          setMessages((prev) => [...prev, userMessage]);
        }
      }

      // Add AI response
      if (data.ai_response) {
        const aiMessage: Message = {
          id: Date.now().toString() + "-ai",
          role: "assistant",
          content: data.ai_response,
          type: "text",
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, aiMessage]);
      }

      setReadyToGenerate(data.ready_to_generate);

      if (data.task_id) {
        setAppPhase("generating");
        connectWebSocket(data.task_id);
      }
    } catch (error) {
      console.error("Error:", error);
      const errorMsg: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: "Sorry, I had trouble processing that. Please try again.",
        type: "text",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
      setInputText("");
    }
  };

  const confirmGeneration = async () => {
    if (!conversationId) return;

    setIsLoading(true);

    const confirmMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: "Let's generate the video!",
      type: "text",
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, confirmMsg]);

    try {
      const response = await fetch(
        `http://localhost:8000/api/conversation/${conversationId}/generate`,
        { method: "POST" }
      );

      if (!response.ok) throw new Error("Failed to start generation");

      const data = await response.json();

      const aiMsg: Message = {
        id: Date.now().toString() + "-ai",
        role: "assistant",
        content: "🎬 Starting video generation! This usually takes 1-2 minutes...",
        type: "text",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, aiMsg]);

      setAppPhase("generating");
      setReadyToGenerate(false);
      connectWebSocket(data.task_id);
    } catch (error) {
      console.error("Error:", error);
      setErrorMessage("Failed to start video generation");
    } finally {
      setIsLoading(false);
    }
  };

  // ========== WebSocket ==========
  
  const connectWebSocket = (taskId: string) => {
    const ws = new WebSocket(`ws://localhost:8000/ws/${taskId}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      if (event.data === "ping") {
        ws.send("pong");
        return;
      }

      let data: TaskStatus;
      try {
        data = JSON.parse(event.data);
      } catch {
        return;
      }

      if (data.type === "ping") {
        ws.send("pong");
        return;
      }

      setTaskStatus(data);
      
      // Save transcription for direct mode
      if (data.transcription) {
        setTranscription(data.transcription);
      }

      if (data.type === "complete" || data.status === "completed") {
        setAppPhase("completed");
        
        if (generationMode === "discuss") {
          const completeMsg: Message = {
            id: Date.now().toString(),
            role: "assistant",
            content: data.result?.video_url
              ? "🎉 Your video is ready!"
              : "Generation complete, but video was not available.",
            type: "text",
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, completeMsg]);
        }
      } else if (data.type === "error" || data.status === "failed") {
        setAppPhase("error");
        setErrorMessage(data.error || "An error occurred");
      }
    };

    ws.onerror = () => {
      setAppPhase("error");
      setErrorMessage("Connection error");
    };
  };

  // ========== Reset ==========
  
  const resetAll = () => {
    setAppPhase("welcome");
    setGenerationMode("discuss");
    setMessages([]);
    setConversationId(null);
    setReadyToGenerate(false);
    setTaskStatus(null);
    setErrorMessage("");
    setInputText("");
    setTranscription("");
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  // ========== Welcome Screen ==========
  
  const renderWelcomeScreen = () => (
    <div className="flex flex-col items-center justify-center min-h-screen px-6 py-20">
      {/* Welcome */}
      <div className="text-center mb-10 animate-fade-in">
        <h1 className="text-3xl md:text-4xl font-semibold text-kiwi-white mb-3">
          {user ? `Welcome, ${user.firstName || "Creator"}` : "Welcome"}
        </h1>
        <p className="text-kiwi-gray-400 text-lg">
          Describe your video and watch it come to life
        </p>
      </div>

      {/* Mode Selection */}
      <div className="flex gap-4 mb-10">
        <button
          onClick={() => setGenerationMode("discuss")}
          className={`px-6 py-3 rounded-xl font-medium transition-all ${
            generationMode === "discuss"
              ? "bg-kiwi-white text-kiwi-black"
              : "bg-kiwi-gray-800 text-kiwi-gray-300 hover:bg-kiwi-gray-700"
          }`}
        >
          💬 Discuss with AI
        </button>
        <button
          onClick={() => setGenerationMode("direct")}
          className={`px-6 py-3 rounded-xl font-medium transition-all ${
            generationMode === "direct"
              ? "bg-kiwi-white text-kiwi-black"
              : "bg-kiwi-gray-800 text-kiwi-gray-300 hover:bg-kiwi-gray-700"
          }`}
        >
          ⚡ Generate Directly
        </button>
      </div>

      {/* Mode Description */}
      <p className="text-sm text-kiwi-gray-500 mb-8 max-w-md text-center">
        {generationMode === "discuss"
          ? "Chat with AI to refine your video idea before generating"
          : "Skip the discussion and generate video immediately from your input"}
      </p>

      {/* Voice Button */}
      <div className="relative mb-8">
        {isRecording && (
          <>
            <div className="absolute inset-0 rounded-full bg-kiwi-gray-600/30 animate-ping" />
            <div className="absolute inset-[-20px] rounded-full border-2 border-kiwi-gray-600/50 animate-pulse" />
          </>
        )}

        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isLoading}
          className={`
            relative z-10 w-32 h-32 md:w-40 md:h-40 rounded-full 
            flex items-center justify-center transition-all duration-300 
            ${isRecording 
              ? "bg-red-500 hover:bg-red-600 scale-110" 
              : "bg-kiwi-gray-800 hover:bg-kiwi-gray-700 hover:scale-105"
            }
            shadow-card hover:shadow-card-hover border border-kiwi-gray-700 disabled:opacity-50
          `}
        >
          {isRecording ? (
            <div className="w-10 h-10 md:w-12 md:h-12 bg-kiwi-white rounded-md" />
          ) : (
            <svg className="w-12 h-12 md:w-16 md:h-16 text-kiwi-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          )}
        </button>
      </div>

      <p className="text-lg mb-8 text-kiwi-gray-400">
        {isRecording ? "Listening... Click to stop" : "Click to start speaking"}
      </p>

      {/* Text Input */}
      <div className="w-full max-w-md">
        <div className="relative">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Or type your video idea..."
            disabled={isLoading || isRecording}
            className="w-full px-4 py-3 pr-24 bg-kiwi-gray-900 border border-kiwi-gray-700 rounded-xl text-kiwi-white placeholder-kiwi-gray-500 focus:border-kiwi-gray-500 focus:outline-none transition-colors disabled:opacity-50"
            onKeyDown={(e) => {
              if (e.key === "Enter" && inputText.trim()) {
                if (generationMode === "direct") {
                  handleDirectGeneration(inputText.trim());
                } else {
                  handleFirstInput(inputText.trim());
                }
              }
            }}
          />
          <button
            onClick={() => {
              if (inputText.trim()) {
                if (generationMode === "direct") {
                  handleDirectGeneration(inputText.trim());
                } else {
                  handleFirstInput(inputText.trim());
                }
              }
            }}
            disabled={!inputText.trim() || isLoading}
            className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-1.5 bg-kiwi-white text-kiwi-black text-sm font-medium rounded-lg hover:bg-kiwi-gray-200 transition-colors disabled:opacity-50"
          >
            {generationMode === "direct" ? "Generate" : "Start"}
          </button>
        </div>
      </div>

      {isLoading && (
        <div className="mt-8 flex items-center gap-2 text-kiwi-gray-400">
          <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span>Processing...</span>
        </div>
      )}
    </div>
  );

  // ========== Direct Generation Screen ==========
  
  const renderDirectGenerationScreen = () => (
    <div className="flex flex-col items-center justify-center min-h-screen px-6 py-20">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-xl font-semibold text-kiwi-white">Generating Video</h2>
          <button onClick={resetAll} className="text-sm text-kiwi-gray-400 hover:text-kiwi-white">
            Cancel
          </button>
        </div>

        {/* Transcription */}
        {transcription && (
          <div className="bg-kiwi-gray-900 border border-kiwi-gray-700 rounded-xl p-4 mb-6">
            <p className="text-sm text-kiwi-gray-400 mb-1">Your request:</p>
            <p className="text-kiwi-white">{transcription}</p>
          </div>
        )}

        {/* Progress */}
        {taskStatus && (
          <div className="bg-kiwi-gray-900 border border-kiwi-gray-800 rounded-xl p-6 mb-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-kiwi-gray-700 flex items-center justify-center">
                <svg className="w-6 h-6 text-kiwi-white animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              </div>
              <div className="flex-1">
                <p className="text-kiwi-white font-medium">{taskStatus.message}</p>
                <div className="mt-3 h-2 bg-kiwi-gray-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-kiwi-gray-600 to-kiwi-gray-400 transition-all duration-500"
                    style={{ width: `${taskStatus.progress}%` }}
                  />
                </div>
              </div>
              <span className="text-lg font-semibold text-kiwi-gray-400">{taskStatus.progress}%</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  // ========== Completed Screen (Direct Mode) ==========
  
  const renderDirectCompletedScreen = () => (
    <div className="flex flex-col items-center justify-center min-h-screen px-6 py-20">
      <div className="w-full max-w-2xl">
        <h2 className="text-2xl font-semibold text-kiwi-white mb-6 text-center">
          🎉 Your Video is Ready!
        </h2>

        {/* Video Player */}
        {taskStatus?.result?.video_url ? (
          <div className="bg-kiwi-gray-900 border border-kiwi-gray-800 rounded-2xl overflow-hidden mb-6">
            <video
              src={`http://localhost:8000${taskStatus.result.video_url}`}
              controls
              autoPlay
              loop
              className="w-full aspect-video"
            />
          </div>
        ) : (
          <div className="bg-kiwi-gray-900 border border-kiwi-gray-800 rounded-2xl p-8 text-center mb-6">
            <p className="text-kiwi-gray-400">Video not available</p>
          </div>
        )}

        {/* Transcription */}
        {transcription && (
          <div className="bg-kiwi-gray-900 border border-kiwi-gray-700 rounded-xl p-4 mb-4">
            <p className="text-sm text-kiwi-gray-400 mb-1">🎤 Your request:</p>
            <p className="text-kiwi-white">{transcription}</p>
          </div>
        )}

        {/* Prompt */}
        {taskStatus?.result?.video_prompt && (
          <div className="bg-kiwi-gray-900 border border-kiwi-gray-700 rounded-xl p-4 mb-6">
            <p className="text-sm text-kiwi-gray-400 mb-1">🎨 Generated prompt:</p>
            <p className="text-kiwi-white text-sm">{taskStatus.result.video_prompt}</p>
          </div>
        )}

        <button
          onClick={resetAll}
          className="w-full py-3 bg-kiwi-white text-kiwi-black font-medium rounded-xl hover:bg-kiwi-gray-200 transition-colors"
        >
          Create Another Video
        </button>
      </div>
    </div>
  );

  // ========== Chat Screen ==========
  
  const renderChatScreen = () => (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="flex-shrink-0 px-6 py-4 border-b border-kiwi-gray-800">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <h1 className="text-lg font-medium text-kiwi-white">Video Creator</h1>
          <button onClick={resetAll} className="text-sm text-kiwi-gray-400 hover:text-kiwi-white">
            Start Over
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                message.role === "user"
                  ? "bg-kiwi-gray-700 text-kiwi-white"
                  : "bg-kiwi-gray-900 border border-kiwi-gray-800 text-kiwi-white"
              }`}>
                {message.type === "audio" && (
                  <span className="text-xs text-kiwi-gray-400 mb-1 block">🎤 Voice</span>
                )}
                <p className="whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-kiwi-gray-900 border border-kiwi-gray-800 rounded-2xl px-4 py-3">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-kiwi-gray-500 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-kiwi-gray-500 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} />
                  <div className="w-2 h-2 bg-kiwi-gray-500 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
                </div>
              </div>
            </div>
          )}

          {/* Progress in chat */}
          {appPhase === "generating" && taskStatus && (
            <div className="bg-kiwi-gray-900 border border-kiwi-gray-800 rounded-2xl p-4">
              <div className="flex items-center gap-3">
                <svg className="w-5 h-5 text-kiwi-white animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <div className="flex-1">
                  <p className="text-sm text-kiwi-gray-300">{taskStatus.message}</p>
                  <div className="mt-2 h-2 bg-kiwi-gray-800 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-kiwi-gray-600 to-kiwi-gray-400 transition-all" style={{ width: `${taskStatus.progress}%` }} />
                  </div>
                </div>
                <span className="text-sm text-kiwi-gray-500">{taskStatus.progress}%</span>
              </div>
            </div>
          )}

          {/* Video Result */}
          {appPhase === "completed" && taskStatus?.result?.video_url && (
            <div className="bg-kiwi-gray-900 border border-kiwi-gray-800 rounded-2xl overflow-hidden">
              <video src={`http://localhost:8000${taskStatus.result.video_url}`} controls autoPlay loop className="w-full aspect-video" />
              {taskStatus.result.video_prompt && (
                <div className="p-4 border-t border-kiwi-gray-800">
                  <p className="text-xs text-kiwi-gray-500 mb-1">Prompt:</p>
                  <p className="text-sm text-kiwi-gray-300">{taskStatus.result.video_prompt}</p>
                </div>
              )}
            </div>
          )}

          {appPhase === "error" && (
            <div className="bg-red-900/20 border border-red-800 rounded-2xl p-4 text-red-400">
              <p>{errorMessage}</p>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Generate Button */}
      {readyToGenerate && appPhase === "chatting" && (
        <div className="flex-shrink-0 px-6 py-3 border-t border-kiwi-gray-800 bg-kiwi-gray-900/50">
          <div className="max-w-3xl mx-auto">
            <button
              onClick={confirmGeneration}
              disabled={isLoading}
              className="w-full py-3 bg-gradient-to-r from-green-600 to-green-500 text-white font-medium rounded-xl hover:from-green-500 hover:to-green-400 disabled:opacity-50"
            >
              ✨ Generate Video Now
            </button>
          </div>
        </div>
      )}

      {/* Input */}
      {(appPhase === "chatting" || appPhase === "completed") && (
        <div className="flex-shrink-0 px-6 py-4 border-t border-kiwi-gray-800 bg-kiwi-black">
          <div className="max-w-3xl mx-auto flex items-center gap-3">
            <button
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isLoading}
              className={`w-12 h-12 rounded-full flex items-center justify-center ${
                isRecording ? "bg-red-500 animate-pulse" : "bg-kiwi-gray-800 hover:bg-kiwi-gray-700"
              } disabled:opacity-50`}
            >
              {isRecording ? <div className="w-4 h-4 bg-white rounded-sm" /> : (
                <svg className="w-5 h-5 text-kiwi-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              )}
            </button>
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && inputText.trim() && !isLoading && sendMessage(inputText.trim())}
              placeholder={isRecording ? "Recording..." : "Type your message..."}
              disabled={isLoading || isRecording}
              className="flex-1 px-4 py-3 bg-kiwi-gray-900 border border-kiwi-gray-700 rounded-xl text-kiwi-white placeholder-kiwi-gray-500 focus:border-kiwi-gray-500 focus:outline-none disabled:opacity-50"
            />
            <button
              onClick={() => inputText.trim() && sendMessage(inputText.trim())}
              disabled={!inputText.trim() || isLoading || isRecording}
              className="w-12 h-12 rounded-full bg-kiwi-white text-kiwi-black flex items-center justify-center hover:bg-kiwi-gray-200 disabled:opacity-50"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* New Video */}
      {(appPhase === "completed" || appPhase === "error") && (
        <div className="flex-shrink-0 px-6 py-3 border-t border-kiwi-gray-800 bg-kiwi-gray-900/50">
          <div className="max-w-3xl mx-auto">
            <button onClick={resetAll} className="w-full py-3 bg-kiwi-white text-kiwi-black font-medium rounded-xl hover:bg-kiwi-gray-200">
              Create Another Video
            </button>
          </div>
        </div>
      )}
    </div>
  );

  // ========== Main Render ==========
  
  return (
    <div className="min-h-screen bg-kiwi-black">
      {appPhase === "welcome" && renderWelcomeScreen()}
      {appPhase === "chatting" && renderChatScreen()}
      {appPhase === "generating" && generationMode === "direct" && renderDirectGenerationScreen()}
      {appPhase === "generating" && generationMode === "discuss" && renderChatScreen()}
      {appPhase === "completed" && generationMode === "direct" && renderDirectCompletedScreen()}
      {appPhase === "completed" && generationMode === "discuss" && renderChatScreen()}
      {appPhase === "error" && generationMode === "direct" && renderDirectCompletedScreen()}
      {appPhase === "error" && generationMode === "discuss" && renderChatScreen()}
    </div>
  );
}
