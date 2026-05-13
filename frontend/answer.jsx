{answer && (
  <div className="answer-card">
    <h2>Answer</h2>
    <p>{answer}</p>

    <div className="action-buttons">
      <button onClick={saveAnswerToGoogleDoc}>
        Save to Google Doc
      </button>

      <button onClick={scheduleFollowUp}>
        Schedule Review
      </button>
    </div>
  </div>
)}