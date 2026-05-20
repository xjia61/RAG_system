import React, { useMemo, useState } from "react";
import "./App.css";
import {
  Upload,
  Search,
  FileText,
  Brain,
  Database,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Volume2,
  BarChart3,
  MessageSquarePlus,
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const ENDPOINTS = {
  upload: `${API_URL}/upload`,
  chat: `${API_URL}/chat`,
  speak: `${API_URL}/speak`,
  chart: `${API_URL}/chart`,
  extract: `${API_URL}/extract`,
};

export default function App() {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("idle");
  const [uploadMessage, setUploadMessage] = useState("");

  const [question, setQuestion] = useState("What is the final diagnosis?");
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState([]);
  const [context, setContext] = useState([]);
  const [extraction, setExtraction] = useState(null);

  const [audioUrl, setAudioUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [error, setError] = useState("");

  const [chartTitle, setChartTitle] = useState("Generated Chart");
  const [chartType, setChartType] = useState("bar");
  const [chartInput, setChartInput] = useState(`{
  "Melanoma": 12,
  "SCC": 8,
  "BCC": 15
}`);
  const [chartUrl, setChartUrl] = useState("");
  const [chartLoading, setChartLoading] = useState(false);

  const exampleQuestions = [
    "What is the final diagnosis?",
    "What specimen was submitted?",
    "Are the margins involved?",
    "Is lymph node metastasis mentioned?",
    "What biomarkers are reported?",
    "Summarize this case in one paragraph.",
  ];

  const fileLabel = useMemo(() => {
    if (!file) return "Choose a pathology report or synthetic EHR document";
    return `${file.name} (${Math.round(file.size / 1024)} KB)`;
  }, [file]);

  const lastAssistantMessage = useMemo(() => {
    return [...messages].reverse().find((msg) => msg.role === "assistant");
  }, [messages]);

  async function handleUpload() {
    if (!file) {
      setError("Please choose a file first.");
      return;
    }

    setError("");
    setUploadStatus("loading");
    setUploadMessage("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(ENDPOINTS.upload, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed with status ${response.status}`);
      }

      const data = await response.json();
      setUploadStatus("success");
      setUploadMessage(data.message || "Document uploaded and indexed successfully.");

      if (data.session_id) {
        setSessionId(data.session_id);
      }
    } catch (err) {
      console.error(err);
      setUploadStatus("error");
      setError(err.message || "Upload failed. Please check the backend connection.");
    }
  }

  async function handleAsk() {
    if (!question.trim()) return;

    const currentQuestion = question.trim();
    setError("");
    setAudioUrl("");
    setQuestion("");
    setLoading(true);

    setMessages((prev) => [
      ...prev,
      { role: "user", content: currentQuestion },
    ]);

    try {
      const response = await fetch(ENDPOINTS.chat, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: currentQuestion,
          session_id: sessionId || null,
        }),
      });

      if (!response.ok) {
        throw new Error(`Backend error with status ${response.status}`);
      }

      const data = await response.json();

      if (data.session_id) {
        setSessionId(data.session_id);
      }

      const assistantAnswer = data.answer || data.response || "No answer returned.";

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: assistantAnswer },
      ]);

      setContext(data.context || data.sources || data.retrieved_context || []);
    } catch (err) {
      console.error(err);
      setError(err.message || "Could not connect to the RAG backend.");
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error: could not connect to the RAG backend." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function handleExtract() {
    setError("");
    setExtraction(null);
    setLoading(true);

    try {
      const response = await fetch(ENDPOINTS.extract, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId || null }),
      });

      if (!response.ok) {
        throw new Error(`Extraction request failed with status ${response.status}`);
      }

      const data = await response.json();
      setExtraction(data.extraction || data.structured_data || data);
    } catch (err) {
      console.error(err);
      setError(err.message || "Structured extraction failed. If your backend does not have /extract yet, add it later or hide this button for now.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSpeakLastAnswer() {
    if (!lastAssistantMessage) return;

    setError("");
    setSpeaking(true);
    setAudioUrl("");

    try {
      const response = await fetch(ENDPOINTS.speak, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: lastAssistantMessage.content,
          voice: "Samantha",
          rate: 180,
        }),
      });

      if (!response.ok) {
        throw new Error(`Speak backend error with status ${response.status}`);
      }

      const data = await response.json();

      if (data.error) {
        setError(data.error);
        return;
      }

      setAudioUrl(data.audio_url || data.url || "");
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to generate audio.");
    } finally {
      setSpeaking(false);
    }
  }

  function handleNewChat() {
    setQuestion("What is the final diagnosis?");
    setSessionId("");
    setMessages([]);
    setContext([]);
    setExtraction(null);
    setAudioUrl("");
    setError("");
  }

  async function handleGenerateChart() {
    setError("");
    setChartLoading(true);
    setChartUrl("");

    try {
      const parsedData = JSON.parse(chartInput);

      const response = await fetch(ENDPOINTS.chart, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: chartTitle,
          chart_type: chartType,
          x_label: "Category",
          y_label: "Value",
          data: parsedData,
        }),
      });

      if (!response.ok) {
        throw new Error(`Chart backend error with status ${response.status}`);
      }

      const data = await response.json();

      if (data.error) {
        setError(data.error);
        return;
      }

      setChartUrl(data.chart_url || data.url || "");
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to generate chart. Check your JSON format.");
    } finally {
      setChartLoading(false);
    }
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleAsk();
    }
  }

  return (
    <main className="app-shell">
      <section className="app-container">
        <header className="hero-card">
          <div className="hero-left">
            <div className="eyebrow">
              <Brain size={16} />
              Pathology RAG Demo
            </div>
            <h1>PathologyAI</h1>
            <p>
              A full-stack AI assistant for pathology reports and synthetic EHR-style documents.
              Upload a report, ask clinically relevant questions, generate audio, and create simple charts.
            </p>
            {sessionId && <div className="session-badge">Session: {sessionId.slice(0, 8)}</div>}
          </div>

          <div className="hero-metrics">
            <Metric icon={<Upload size={22} />} label="Upload" />
            <Metric icon={<Database size={22} />} label="Index" />
            <Metric icon={<Search size={22} />} label="Ask" />
          </div>
        </header>

        {error && (
          <div className="alert-card">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        <div className="layout-grid">
          <aside className="side-column">
            <Card title="1. Upload document" icon={<Upload size={20} />}>
              <label className="file-dropzone">
                <input
                  type="file"
                  accept=".txt,.pdf,.docx,.epub"
                  onChange={(event) => setFile(event.target.files?.[0] || null)}
                />
                <FileText size={36} />
                <strong>{fileLabel}</strong>
                <span>PDF, TXT, DOCX, EPUB</span>
              </label>

              <button className="primary-button full-width" onClick={handleUpload} disabled={uploadStatus === "loading"}>
                {uploadStatus === "loading" ? <Loader2 className="spin" size={18} /> : <Upload size={18} />}
                Upload and index
              </button>

              {uploadStatus === "success" && <StatusMessage text={uploadMessage} />}
            </Card>

            <Card title="Example questions" icon={<Search size={20} />}>
              <div className="question-chips">
                {exampleQuestions.map((item) => (
                  <button key={item} onClick={() => setQuestion(item)}>
                    {item}
                  </button>
                ))}
              </div>
            </Card>

            <Card title="Audio tool" icon={<Volume2 size={20} />}>
              <button className="secondary-button full-width" onClick={handleSpeakLastAnswer} disabled={speaking || !lastAssistantMessage}>
                {speaking ? <Loader2 className="spin" size={18} /> : <Volume2 size={18} />}
                {speaking ? "Generating audio..." : "Speak last answer"}
              </button>

              {audioUrl && (
                <div className="media-box">
                  <strong>Audio</strong>
                  <audio controls src={audioUrl}>
                    Your browser does not support audio playback.
                  </audio>
                </div>
              )}
            </Card>

            <Card title="Chart tool" icon={<BarChart3 size={20} />}>
              <div className="form-stack">
                <input value={chartTitle} onChange={(event) => setChartTitle(event.target.value)} placeholder="Chart title" />
                <select value={chartType} onChange={(event) => setChartType(event.target.value)}>
                  <option value="bar">Bar Chart</option>
                  <option value="line">Line Chart</option>
                  <option value="pie">Pie Chart</option>
                </select>
                <textarea value={chartInput} onChange={(event) => setChartInput(event.target.value)} rows={6} />
                <button className="primary-button full-width" onClick={handleGenerateChart} disabled={chartLoading}>
                  {chartLoading ? <Loader2 className="spin" size={18} /> : <BarChart3 size={18} />}
                  {chartLoading ? "Generating chart..." : "Generate chart"}
                </button>
                {chartUrl && <img className="chart-image" src={chartUrl} alt="Generated chart" />}
              </div>
            </Card>
          </aside>

          <section className="main-column">
            <Card title="2. Ask a question" icon={<Search size={20} />}>
              <textarea
                className="question-input"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about diagnosis, margins, lymph nodes, biomarkers..."
                rows={4}
              />

              <div className="button-row">
                <button className="primary-button" onClick={handleAsk} disabled={loading}>
                  {loading ? <Loader2 className="spin" size={18} /> : <Search size={18} />}
                  {loading ? "Thinking..." : "Ask"}
                </button>
                <button className="secondary-button" onClick={handleNewChat}>
                  <MessageSquarePlus size={18} />
                  New chat
                </button>
                <button className="secondary-button" onClick={handleExtract} disabled={loading}>
                  <FileText size={18} />
                  Extract fields
                </button>
              </div>
            </Card>

            <Card title="Conversation" icon={<Brain size={20} />}>
              {messages.length === 0 && <EmptyState text="Ask a question to start chatting with the uploaded document." />}
              <div className="messages-list">
                {messages.map((msg, index) => (
                  <div key={`${msg.role}-${index}`} className={msg.role === "user" ? "message-bubble user-bubble" : "message-bubble assistant-bubble"}>
                    <div className="message-role">{msg.role === "user" ? "You" : "Assistant"}</div>
                    <div className="message-content">{msg.content}</div>
                  </div>
                ))}
                {loading && (
                  <div className="message-bubble assistant-bubble loading-bubble">
                    <Loader2 className="spin" size={18} />
                    Thinking...
                  </div>
                )}
              </div>
            </Card>

            <Card title="Structured extraction" icon={<FileText size={20} />}>
              {extraction ? <StructuredData data={extraction} /> : <EmptyState text="Click Extract fields to display diagnosis, specimen, margins, lymph nodes, biomarkers, and other key fields." />}
            </Card>

            <Card title="Retrieved context" icon={<Database size={20} />}>
              {Array.isArray(context) && context.length > 0 ? (
                <div className="context-list">
                  {context.map((item, index) => (
                    <div key={index} className="context-card">
                      <strong>Source chunk {index + 1}</strong>
                      <p>{typeof item === "string" ? item : item.text || item.page_content || JSON.stringify(item, null, 2)}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState text="Retrieved source chunks will appear here if your backend returns context, sources, or retrieved_context." />
              )}
            </Card>
          </section>
        </div>
      </section>
    </main>
  );
}

function Metric({ icon, label }) {
  return (
    <div className="metric-card">
      <div>{icon}</div>
      <span>{label}</span>
    </div>
  );
}

function Card({ title, icon, children }) {
  return (
    <section className="panel-card">
      <div className="panel-header">
        <div className="panel-icon">{icon}</div>
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

function StatusMessage({ text }) {
  return (
    <div className="success-card">
      <CheckCircle2 size={18} />
      <span>{text}</span>
    </div>
  );
}

function EmptyState({ text }) {
  return <div className="empty-state">{text}</div>;
}

function StructuredData({ data }) {
  if (!data || typeof data !== "object") {
    return <p>{String(data)}</p>;
  }

  return (
    <div className="structured-grid">
      {Object.entries(data).map(([key, value]) => (
        <div key={key} className="structured-card">
          <strong>{key.replaceAll("_", " ")}</strong>
          <p>{typeof value === "object" ? JSON.stringify(value, null, 2) : String(value || "Not mentioned")}</p>
        </div>
      ))}
    </div>
  );
}



