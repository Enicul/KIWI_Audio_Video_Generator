![CodeRabbit Pull Request Reviews](https://img.shields.io/coderabbit/prs/github/Enicul/Audio-Video?label=CodeRabbit%20Reviews)

# **🥝 Kiwi — AI Multi-Agent Video Creation Studio**

Turn simple text descriptions into fully produced videos — automatically.

Kiwi is a multi-agent, multimodal AI system that generates **scripts, storyboards, video scenes, narration, and final MP4 output** end-to-end.

Kiwi acts like an AI film studio: users describe a concept, and specialized agents collaborate to produce a complete video without any editing skills required.

---

## **✨ Key Features**

* **Multi-Agent AI Pipeline** modeled after a real film crew
* **Script, storyboard, video, and voice generation** from a single prompt
* **Dependency-aware parallel execution** (script + storyboard → audio + video)
* **Prompt-chaining** for clarifying vague user requests
* **High-quality video generation using Veo 3**
* **Natural voice narration via ElevenLabs**
* **Secure user sessions with Clerk**
* **Fully in-browser experience built with Next.js**

---

## **🧠 Agent Architecture**

Kiwi uses a coordinated set of specialized agents:

```
DirectorOrchestrator
├── StoryLoaderAgent      (Script generation)
├── StoryboardAgent       (Shot planning)
├── FilmCrewAgent         (Video creation)
└── VoiceActorAgent       (Voice synthesis)
```

### **Parallel Execution**

* Script + Storyboard run in parallel (both depend only on Creative Brief)
* Audio + Video run in parallel (each depends on its respective output)
* Final output merged via MoviePy

This reduces latency and reflects a true autonomous agent workflow.

---

## **🎬 End-to-End Workflow**

1. **User describes the video** in the Web UI
2. **DirectorOrchestrator** expands the idea using prompt-chaining
3. Generates a **Creative Brief** containing style, tone, length, scenes
4. **Parallel Phase 1**
   * StoryLoaderAgent → script
   * StoryboardAgent → shot plan
5. **Parallel Phase 2**
   * VoiceActorAgent → narration (ElevenLabs)
   * FilmCrewAgent → video scenes (Veo 3)
6. **MoviePy** merges the results
7. User receives a downloadable **MP4**

---

## **🛠️ Tech Stack**

**Models & APIs**

* Gemini Pro 3 (agent reasoning)
* Veo 3 (video generation)
* ElevenLabs (voice synthesis)

**Frontend**

* Next.js 15
* Clerk authentication

**Backend / Processing**

* MoviePy (audio-video merging)
* Custom orchestration logic (multi-agent framework)

**Developer Tooling**

* CodeRabbit for automated PR review

---

## **🚀 Running the Project**

Clone the repo:

```bash
git clone https://github.com/<your-org>/<your-repo>.git
cd <your-repo>
```

Install dependencies:

```bash
npm install
```

Add required environment variables:

```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...
CLERK_SECRET_KEY=...
GEMINI_API_KEY=...
ELEVENLABS_API_KEY=...
```

Run the dev server:

```bash
npm run dev
```

Open the app:

```
http://localhost:3000
```

---

## **📦 Folder Structure**

```
/agents
  director.ts
  storyLoader.ts
  storyboard.ts
  filmCrew.ts
  voiceActor.ts

/pages
  index.tsx
  video-result.tsx

/utils
  orchestrator.ts
  videoMerge.ts

/public
  assets/
```

---

## **🧩 Roadmap**

* Add multi-language narration
* Support longer videos and multi-scene stories
* Add custom voice cloning
* Expand to collaborative multi-user workflows

---

## **🤝 Contributing**

1. Fork the repo
2. Create a new branch
3. Submit a PR (automatically reviewed by CodeRabbit)

---

## **📄 License**

MIT License.

