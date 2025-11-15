import { useState, useEffect } from 'react';
import Header from './components/Header';
import ChatSection from './components/ChatSection';
import EditorSection from './components/EditorSection';
import Footer from './components/Footer';
import { websocketService, type ServerMessage } from './services/websocket';
import './App.css';

export interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Connecting to Agent Q backend...',
      isUser: false,
      timestamp: new Date(),
    },
  ]);
  const [code, setCode] = useState<string>('// Your Playwright test will appear here\n');
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'connecting' | 'error'>('connecting');

  useEffect(() => {
    // Connect to WebSocket
    websocketService.connect()
      .then(() => {
        setConnectionStatus('connected');
        setMessages([{
          id: '1',
          content: 'Welcome to Agent Q! I can help you create and run automated tests for any website.\n\nTry asking: "Navigate to example.com and take a screenshot"',
          isUser: false,
          timestamp: new Date(),
        }]);
      })
      .catch((error) => {
        console.error('Failed to connect:', error);
        setConnectionStatus('error');
        setMessages([{
          id: '1',
          content: 'Failed to connect to backend. Please make sure the backend server is running at http://localhost:8000',
          isUser: false,
          timestamp: new Date(),
        }]);
      });

    // Subscribe to messages
    const unsubscribe = websocketService.onMessage(handleServerMessage);

    return () => {
      unsubscribe();
      websocketService.disconnect();
    };
  }, []);

  const handleServerMessage = (serverMessage: ServerMessage) => {
    if (serverMessage.type === 'connected') {
      return;
    }

    if (serverMessage.type === 'agent_thinking') {
      const thinkingMessage: Message = {
        id: Date.now().toString(),
        content: '[PROCESSING] ' + serverMessage.content,
        isUser: false,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, thinkingMessage]);
    } else if (serverMessage.type === 'agent_response') {
      const botMessage: Message = {
        id: Date.now().toString(),
        content: serverMessage.content,
        isUser: false,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMessage]);
    } else if (serverMessage.type === 'error') {
      const errorMessage: Message = {
        id: Date.now().toString(),
        content: '[ERROR] ' + serverMessage.content,
        isUser: false,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  const handleSendMessage = (message: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      content: message,
      isUser: true,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Send to backend via WebSocket
    websocketService.sendChatMessage(message);
  };

  return (
    <div className="app">
      <Header status={connectionStatus} />
      <main className="main-content">
        <ChatSection messages={messages} onSendMessage={handleSendMessage} />
        <EditorSection code={code} onCodeChange={setCode} />
      </main>
      <Footer />
    </div>
  );
}

export default App;