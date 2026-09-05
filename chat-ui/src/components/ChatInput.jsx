import { useState } from "react";

function ChatInput({ onSend }) {
  const [message, setMessage] = useState("");

  const handleSubmit = () => {
    if (!message.trim()) return;

    onSend(message);
    setMessage("");
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="input-area">
      <div className="input-wrapper">

        <button
          type="button"
          className="attach-btn"
          title="Attach file"
        >
          📎
        </button>

        <textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          rows={1}
          aria-label="Message input"
        />

        <button
          type="button"
          className="send-btn"
          onClick={handleSubmit}
          disabled={!message.trim()}
        >
          ➤
        </button>

      </div>

      <p className="input-hint">
        Press <strong>Enter</strong> to send •
        <strong> Shift + Enter</strong> for a new line
      </p>
    </div>
  );
}

export default ChatInput;