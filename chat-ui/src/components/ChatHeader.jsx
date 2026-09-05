function ChatHeader() {
  return (
    <header className="chat-header">

      <div className="chat-title">

        <div className="bot-avatar">
          🤖
        </div>

        <div>
          <h2>AI Assistant</h2>

          <div className="online-status">
            <span className="status-dot"></span>
            Online
          </div>
        </div>

      </div>

    </header>
  );
}

export default ChatHeader;