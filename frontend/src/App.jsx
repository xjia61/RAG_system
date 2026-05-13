import { useState } from "react";
import "./App.css";

function App() {
  const [question, setQuestion] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState([]);
  const [audioUrl, setAudioUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [chartTitle, setChartTitle] = useState("Generated Chart");
  const [chartType, setChartType] = useState("bar");
  const [chartInput, setChartInput] = useState(`{
    "Melanoma": 12,
    "SCC": 8,
    "BCC": 15
  }`);
  const [chartUrl, setChartUrl] = useState("");
  const [chartLoading, setChartLoading] = useState(false);

  async function handleAsk() {
    if (!question.trim()) return;

    const currentQuestion = question;

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: currentQuestion,
      },
    ]);

    setQuestion("");
    setLoading(true);
    setAudioUrl("");

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: currentQuestion,
          session_id: sessionId || null,
        }),
      });

      if (!response.ok) {
        throw new Error("Backend error");
      }

      const data = await response.json();

      setSessionId(data.session_id);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
        },
      ]);
    } catch (error) {
      console.error(error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Error: could not connect to the RAG backend.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function handleSpeakLastAnswer() {
    const lastAssistantMessage = [...messages]
      .reverse()
      .find((msg) => msg.role === "assistant");

    if (!lastAssistantMessage) return;

    setSpeaking(true);
    setAudioUrl("");

    try {
      const response = await fetch("http://localhost:8000/speak", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: lastAssistantMessage.content,
          voice: "Samantha",
          rate: 180,
        }),
      });

      if (!response.ok) {
        throw new Error("Speak backend error");
      }

      const data = await response.json();

      if (data.error) {
        alert(data.error);
        return;
      }

      setAudioUrl(data.audio_url);
    } catch (error) {
      console.error(error);
      alert("Failed to generate audio.");
    } finally {
      setSpeaking(false);
    }
  }

  async function handleNewChat() {
    setQuestion("");
    setSessionId("");
    setMessages([]);
    setAudioUrl("");
  }
  async function handleGenerateChart() {
    setChartLoading(true);
    setChartUrl("");

    try {
      const parsedData = JSON.parse(chartInput);

      const response = await fetch("http://localhost:8000/chart", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: chartTitle,
          chart_type: chartType,
          x_label: "Category",
          y_label: "Value",
          data: parsedData,
        }),
      });

      if (!response.ok) {
        throw new Error("Chart backend error");
      }

      const data = await response.json();

      if (data.error) {
        alert(data.error);
        return;
      }

      setChartUrl(data.chart_url);
    } catch (error) {
      console.error(error);
      alert("Failed to generate chart. Check your JSON format.");
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
    <div className="app">
      <div className="container">
        <header className="header">
          <h1>Local Book RAG Chat</h1>
          <p>Chat with your PDF and EPUB documents.</p>

          {sessionId && (
            <p className="session-id">
              Session: {sessionId.slice(0, 8)}
            </p>
          )}
        </header>

        <div className="top-actions">
          <button onClick={handleNewChat}>
            New Chat
          </button>

          <button onClick={handleSpeakLastAnswer} disabled={speaking || messages.length === 0}>
            {speaking ? "Generating Audio..." : "Speak Last Answer"}
          </button>
        </div>

        <div className="messages">
          {messages.length === 0 && (
            <div className="empty-state">
              Ask a question to start chatting.
            </div>
          )}

          {messages.map((msg, index) => (
            <div
              key={index}
              className={
                msg.role === "user"
                  ? "message user-message"
                  : "message assistant-message"
              }
            >
              <div className="message-role">
                {msg.role === "user" ? "You" : "Assistant"}
              </div>
              <div className="message-content">
                {msg.content}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message assistant-message">
              <div className="message-role">Assistant</div>
              <div className="message-content">Thinking...</div>
            </div>
          )}
        </div>

        {audioUrl && (
          <div className="audio-player">
            <h3>Audio</h3>
            <audio controls src={audioUrl}>
              Your browser does not support audio playback.
            </audio>
          </div>
        )}

        <div className="chat-box">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a follow-up question..."
          />

          <button onClick={handleAsk} disabled={loading}>
            {loading ? "Thinking..." : "Send"}
          </button>
        </div>
        <div className="chart-panel">
  <h2>Chart Tool</h2>

  <input
    value={chartTitle}
    onChange={(e) => setChartTitle(e.target.value)}
    placeholder="Chart title"
  />

  <select
    value={chartType}
    onChange={(e) => setChartType(e.target.value)}
  >
    <option value="bar">Bar Chart</option>
    <option value="line">Line Chart</option>
    <option value="pie">Pie Chart</option>
  </select>

  <textarea
    value={chartInput}
    onChange={(e) => setChartInput(e.target.value)}
    placeholder='{"A": 10, "B": 20}'
  />

  <button onClick={handleGenerateChart} disabled={chartLoading}>
    {chartLoading ? "Generating Chart..." : "Generate Chart"}
  </button>

  {chartUrl && (
    <div className="chart-result">
      <h3>Chart</h3>
      <img src={chartUrl} alt="Generated chart" />
    </div>
  )}
</div>
      </div>
    </div>
  );
}

export default App;