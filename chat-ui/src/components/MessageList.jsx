import { useEffect, useRef } from "react";
import Message from "./Message";

function MessageList({ messages }) {
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  return (
    <div className="message-list">

      <div className="date-divider">
        <span>Today</span>
      </div>

      {messages.map((message) => (
        <Message
          key={message.id}
          sender={message.sender}
          text={message.text}
          time={message.time}
        />
      ))}

      <div ref={messagesEndRef} />

    </div>
  );
}

export default MessageList;