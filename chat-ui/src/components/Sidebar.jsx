import { useState } from "react";

function Sidebar({ activeChat, setActiveChat, onNewChat }) {
  const [search, setSearch] = useState("");

  const chats = [
    "React Project",
    "Python Questions",
    "Job Preparation",
    "Travel Planning",
    "General Discussion",
  ];

  const filteredChats = chats.filter((chat) =>
    chat.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <aside className="sidebar">

      <div className="sidebar-top">

        <div className="logo">
          <div className="logo-icon">C</div>
          <span>ChatApp</span>
        </div>

        <button className="new-chat-btn" onClick={onNewChat}>
          <span>＋</span>
          New Chat
        </button>

        <div className="search-box">
          <span>⌕</span>
          <input
            type="text"
            placeholder="Search chats..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

      </div>

      <div className="recent-section">

        <p className="section-title">RECENT CHATS</p>

        <div className="chat-list">

          {filteredChats.map((chat) => (
            <button
              key={chat}
              className={`chat-item ${
                activeChat === chat ? "active" : ""
              }`}
              onClick={() => setActiveChat(chat)}
            >
              <span className="chat-icon">💬</span>
              <span>{chat}</span>
            </button>
          ))}

        </div>

      </div>

      <div className="sidebar-bottom">

        <button className="sidebar-option">
          ⚙️
          <span>Settings</span>
        </button>

        <div className="profile">
          <div className="avatar">SR</div>

          <div className="profile-info">
            <strong>User</strong>
            <span>Free Plan</span>
          </div>

          <span className="more">•••</span>
        </div>

      </div>

    </aside>
  );
}

export default Sidebar;