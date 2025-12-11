"use client";

import { useState, useRef, useEffect } from "react";
import { useUser } from "@clerk/nextjs";

type TaskPhase = "idle" | "recording" | "understanding" | "planning" | "execution" | "completed" | "error";

interface TaskStatus {
  task_id: string;
  status: string;
  phase: string;
  progress: number;
  message: string;
  data?: {
    transcription?: string;
  };
  result?: {
    video_url?: string;
    intent?: Record<string, unknown>;
    video_prompt?: string;
  };
  error?: string;
}

export default function DashboardPage() {
  const { user } = useUser();
  const [phase, setPhase] = useState<TaskPhase>("idle");
  const [isRecording, setIsRecording] = useState(false);
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [transcription, setTranscription] = useState<string>("");
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

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
        stream.getTracks().forEach(track => track.stop());
        await sendAudioToBackend(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setPhase("recording");
      setErrorMessage("");
    } catch (error) {
      console.error("Error accessing microphone:", error);
      setErrorMessage("Could not access microphone. Please check permissions.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const sendAudioToBackend = async (audioBlob: Blob) => {
    setPhase("understanding");
    
    try {
      // Convert audio to base64 using Promise
      const base64Audio = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          if (reader.result) {
            resolve(reader.result as string);
          } else {
            reject(new Error("Failed to read audio"));
          }
        };
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(audioBlob);
      });
      
      // Send to backend
      const response = await fetch("http://localhost:8000/api/video/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ audio_data: base64Audio }),
      });

      if (!response.ok) {
        throw new Error("Failed to create task");
      }

      const data = await response.json();
      connectWebSocket(data.task_id);
      
    } catch (error) {
      console.error("Error sending audio:", error);
      setPhase("error");
      setErrorMessage("Failed to process audio. Please try again.");
    }
  };

  const sendTextInput = async (text: string) => {
    setPhase("understanding");
    
    try {
      const response = await fetch("http://localhost:8000/api/video/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text_input: text }),
      });

      if (!response.ok) {
        throw new Error("Failed to create task");
      }

      const data = await response.json();
      connectWebSocket(data.task_id);
    } catch (error) {
      console.error("Error sending text:", error);
      setPhase("error");
      setErrorMessage("Failed to process request. Please try again.");
    }
  };

  const connectWebSocket = (taskId: string) => {
    const ws = new WebSocket(`ws://localhost:8000/ws/${taskId}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      // Handle plain text ping
      if (event.data === "ping") {
        ws.send("pong");
        return;
      }
      
      // Parse JSON data
      let data;
      try {
        data = JSON.parse(event.data);
      } catch {
        console.log("Received non-JSON message:", event.data);
        return;
      }
      
      // Handle JSON ping (legacy)
      if (data.type === "ping") {
        ws.send("pong");
        return;
      }

      setTaskStatus(data);
      
      // Save transcription if available
      if (data.data?.transcription) {
        setTranscription(data.data.transcription);
      }
      
      // Update phase based on task status
      if (data.phase) {
        setPhase(data.phase as TaskPhase);
      }
      
      if (data.type === "complete") {
        setPhase("completed");
      } else if (data.type === "error") {
        setPhase("error");
        setErrorMessage(data.error || "An error occurred");
      }
    };

    ws.onerror = () => {
      setPhase("error");
      setErrorMessage("Connection error. Please try again.");
    };
  };

  const resetState = () => {
    setPhase("idle");
    setTaskStatus(null);
    setErrorMessage("");
    setTranscription("");
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  const getPhaseMessage = () => {
    // If we have a task status message, show it (more detailed)
    if (taskStatus?.message && phase !== "idle" && phase !== "recording") {
      return taskStatus.message;
    }
    
    switch (phase) {
      case "recording":
        return "Listening... Click to stop";
      case "understanding":
        return "Processing your voice...";
      case "planning":
        return "Planning video structure...";
      case "execution":
        return "Generating your video...";
      case "completed":
        return "Video ready!";
      case "error":
        return errorMessage || "Something went wrong";
      default:
        return "Click to start speaking";
    }
  };

  return (
    <div className="min-h-screen bg-kiwi-black">
      {/* Main Content */}
      <div className="flex flex-col items-center justify-center min-h-screen px-6 py-20">
        {/* Welcome Message */}
        <div className="text-center mb-12 animate-fade-in">
          <h1 className="text-3xl md:text-4xl font-semibold text-kiwi-white mb-3">
            {user ? `Welcome, ${user.firstName || "Creator"}` : "Welcome"}
          </h1>
          <p className="text-kiwi-gray-400 text-lg">
            Describe your video and watch it come to life
          </p>
        </div>

        {/* Voice Button Container */}
        <div className="relative mb-12">
          {/* Pulse Animation Ring */}
          {isRecording && (
            <>
              <div className="absolute inset-0 rounded-full bg-kiwi-gray-600/30 animate-ping" />
              <div className="absolute inset-[-20px] rounded-full border-2 border-kiwi-gray-600/50 animate-pulse" />
            </>
          )}
          
          {/* Main Voice Button */}
          <button
            onClick={isRecording ? stopRecording : startRecording}
            disabled={phase !== "idle" && phase !== "recording" && phase !== "completed" && phase !== "error"}
            className={`
              relative z-10 w-32 h-32 md:w-40 md:h-40 rounded-full 
              flex items-center justify-center
              transition-all duration-300 
              ${isRecording 
                ? "bg-red-500 hover:bg-red-600 scale-110" 
                : phase === "idle" || phase === "completed" || phase === "error"
                  ? "bg-kiwi-gray-800 hover:bg-kiwi-gray-700 hover:scale-105"
                  : "bg-kiwi-gray-800 opacity-50 cursor-not-allowed"
              }
              shadow-card hover:shadow-card-hover
              border border-kiwi-gray-700
            `}
          >
            {isRecording ? (
              /* Stop Icon */
              <div className="w-10 h-10 md:w-12 md:h-12 bg-kiwi-white rounded-md" />
            ) : (
              /* Microphone Icon */
              <svg
                className="w-12 h-12 md:w-16 md:h-16 text-kiwi-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                />
              </svg>
            )}
          </button>
        </div>

        {/* Status Message */}
        <p className={`text-lg mb-8 transition-colors ${
          phase === "error" ? "text-red-400" : "text-kiwi-gray-400"
        }`}>
          {getPhaseMessage()}
        </p>

        {/* Transcription Display */}
        {transcription && phase !== "idle" && phase !== "recording" && (
          <div className="w-full max-w-lg mb-6 animate-fade-in">
            <div className="bg-kiwi-gray-900 border border-kiwi-gray-700 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <svg className="w-4 h-4 text-kiwi-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
                <span className="text-sm font-medium text-kiwi-gray-400">Transcription</span>
              </div>
              <p className="text-kiwi-white">{transcription}</p>
            </div>
          </div>
        )}

        {/* Progress Bar */}
        {taskStatus && phase !== "idle" && phase !== "error" && (
          <div className="w-full max-w-md mb-8 animate-fade-in">
            <div className="flex justify-between text-sm text-kiwi-gray-500 mb-2">
              <span>{taskStatus.message}</span>
              <span>{taskStatus.progress}%</span>
            </div>
            <div className="h-2 bg-kiwi-gray-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-kiwi-gray-600 to-kiwi-gray-400 transition-all duration-500"
                style={{ width: `${taskStatus.progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Result Display */}
        {phase === "completed" && taskStatus?.result && (
          <div className="w-full max-w-2xl bg-kiwi-dark border border-kiwi-gray-800 rounded-2xl p-6 animate-slide-up">
            <h3 className="text-xl font-semibold text-kiwi-white mb-4">
              {taskStatus.result.video_url ? "🎬 Your Video is Ready" : "✨ Generation Complete"}
            </h3>
            
            {/* Video Player */}
            <div className="aspect-video bg-kiwi-gray-900 rounded-xl flex items-center justify-center mb-4 border border-kiwi-gray-800 overflow-hidden">
              {taskStatus.result.video_url ? (
                <video
                  src={`http://localhost:8000${taskStatus.result.video_url}`}
                  controls
                  autoPlay
                  loop
                  className="w-full h-full object-contain"
                />
              ) : (
                <div className="text-center text-kiwi-gray-500 p-8">
                  <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <p className="font-medium">Video generation not available</p>
                  <p className="text-sm mt-2">Your API may not have Veo access.</p>
                  <p className="text-sm mt-1">Check Google AI Studio for Veo availability.</p>
                </div>
              )}
            </div>

            {/* Transcription */}
            {transcription && (
              <div className="bg-kiwi-gray-900 rounded-xl p-4 border border-kiwi-gray-800 mb-4">
                <h4 className="text-sm font-medium text-kiwi-gray-400 mb-2">🎤 Your Request</h4>
                <p className="text-kiwi-white">
                  {transcription}
                </p>
              </div>
            )}

            {/* Video Prompt Preview */}
            {taskStatus.result.video_prompt && (
              <div className="bg-kiwi-gray-900 rounded-xl p-4 border border-kiwi-gray-800">
                <h4 className="text-sm font-medium text-kiwi-gray-400 mb-2">🎨 Generated Prompt</h4>
                <p className="text-kiwi-white text-sm">
                  {taskStatus.result.video_prompt}
                </p>
              </div>
            )}

            {/* New Video Button */}
            <button
              onClick={resetState}
              className="mt-6 w-full py-3 bg-kiwi-white text-kiwi-black font-medium rounded-xl hover:bg-kiwi-gray-200 transition-colors"
            >
              Create Another Video
            </button>
          </div>
        )}

        {/* Error State */}
        {phase === "error" && (
          <button
            onClick={resetState}
            className="px-6 py-3 bg-kiwi-gray-800 text-kiwi-white rounded-xl hover:bg-kiwi-gray-700 transition-colors"
          >
            Try Again
          </button>
        )}

        {/* Quick Text Input (Alternative to voice) */}
        {phase === "idle" && (
          <div className="mt-8 w-full max-w-md">
            <div className="relative">
              <input
                type="text"
                placeholder="Or type your video idea..."
                className="w-full px-4 py-3 bg-kiwi-gray-900 border border-kiwi-gray-700 rounded-xl text-kiwi-white placeholder-kiwi-gray-500 focus:border-kiwi-gray-500 focus:outline-none transition-colors"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && e.currentTarget.value.trim()) {
                    sendTextInput(e.currentTarget.value.trim());
                    e.currentTarget.value = "";
                  }
                }}
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-kiwi-gray-600 text-sm">
                Press Enter
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

