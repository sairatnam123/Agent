import { useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatHeader from "./components/ChatHeader";
import MessageList from "./components/MessageList";
import ChatInput from "./components/ChatInput";
import "./App.css";

function App() {

  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: "assistant",
      text: "Hello! 👋 How can I help you?",
      time: new Date().toLocaleTimeString(),
    },
  ]);

  const [activeChat, setActiveChat] = useState("New Chat");

  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);


  const handleSendMessage = async (text) => {

    if (!text.trim()) {
      return;
    }


    // Add user message
    const userMessage = {
      id: Date.now(),
      sender: "user",
      text: text,
      time: new Date().toLocaleTimeString(),
    };


    setMessages((previousMessages) => [
      ...previousMessages,
      userMessage,
    ]);


    setLoading(true);


    try {

      // Call Python FastAPI
      const response = await fetch(
        "http://localhost:8000/chat",
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            message: text,
            conversation_id: conversationId,
          }),
        }
      );


      if (!response.ok) {
        throw new Error("API request failed");
      }


      const data = await response.json();
      setConversationId(data.conversation_id);


      // Add assistant response
      const assistantMessage = {
        id: Date.now() + 1,
        sender: "assistant",
        text: data.response,
        time: new Date().toLocaleTimeString(),
      };


      setMessages((previousMessages) => [
        ...previousMessages,
        assistantMessage,
      ]);

    } catch (error) {

      console.error("API Error:", error);


      const errorMessage = {
        id: Date.now() + 1,
        sender: "assistant",
        text: "Sorry, something went wrong while connecting to the server.",
        time: new Date().toLocaleTimeString(),
      };


      setMessages((previousMessages) => [
        ...previousMessages,
        errorMessage,
      ]);

    } finally {

      setLoading(false);

    }
  };


  const handleNewChat = () => {

    setMessages([
      {
        id: Date.now(),
        sender: "assistant",
        text: "New chat started. How can I help you?",
        time: new Date().toLocaleTimeString(),
      },
    ]);

    setActiveChat("New Chat");
    setConversationId(null);
  };


  return (
    <div className="app">

      <Sidebar
        activeChat={activeChat}
        setActiveChat={setActiveChat}
        onNewChat={handleNewChat}
      />

      <main className="chat-container">

        <ChatHeader />

        <MessageList
          messages={messages}
          loading={loading}
        />

        <ChatInput
          onSend={handleSendMessage}
          loading={loading}
        />

      </main>

    </div>
  );
}

export default App;