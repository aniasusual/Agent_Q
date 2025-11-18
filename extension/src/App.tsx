import { useState, useEffect } from 'react';
import Header from './components/Header';
import ChatSection from './components/ChatSection';
import EditorSection from './components/EditorSection';
import Footer from './components/Footer';
import ResizablePanels from './components/ResizablePanels';
import { websocketService, type ServerMessage } from './services/websocket';
import './App.css';

export interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  imageUrl?: string;
  imageCaption?: string;
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
        id: 'thinking',
        content: '[PROCESSING] ' + serverMessage.content,
        isUser: false,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, thinkingMessage]);
    } else if (serverMessage.type === 'agent_response_chunk') {
      // Handle streaming chunks - append to the last bot message or create new one
      setMessages((prev) => {
        // Remove the thinking message if it exists
        const withoutThinking = prev.filter(msg => msg.id !== 'thinking');

        // Check if the last message is a bot message being streamed
        const lastMsg = withoutThinking[withoutThinking.length - 1];
        if (lastMsg && !lastMsg.isUser && lastMsg.id === 'streaming') {
          // Append to existing streaming message
          return [
            ...withoutThinking.slice(0, -1),
            {
              ...lastMsg,
              content: lastMsg.content + serverMessage.content,
            }
          ];
        } else {
          // Create new streaming message
          return [
            ...withoutThinking,
            {
              id: 'streaming',
              content: serverMessage.content,
              isUser: false,
              timestamp: new Date(),
            }
          ];
        }
      });
    } else if (serverMessage.type === 'agent_response') {
      // Final response - replace streaming message with final one
      setMessages((prev) => {
        const withoutThinking = prev.filter(msg => msg.id !== 'thinking');
        const withoutStreaming = withoutThinking.filter(msg => msg.id !== 'streaming');

        const botMessage: Message = {
          id: Date.now().toString(),
          content: serverMessage.content,
          isUser: false,
          timestamp: new Date(),
        };
        return [...withoutStreaming, botMessage];
      });
    } else if (serverMessage.type === 'screenshot') {
      const screenshotMessage: Message = {
        id: Date.now().toString(),
        content: serverMessage.imageCaption || 'Screenshot captured',
        isUser: false,
        timestamp: new Date(),
        imageUrl: serverMessage.imageUrl,
        imageCaption: serverMessage.imageCaption,
      };
      setMessages((prev) => [...prev, screenshotMessage]);
    } else if (serverMessage.type === 'code_generated') {
      // Update the code editor with generated Playwright code
      if (serverMessage.code) {
        setCode(serverMessage.code);
      }
    } else if (serverMessage.type === 'code_execution_started') {
      const executionMessage: Message = {
        id: Date.now().toString(),
        content: '[RUNNING] ' + serverMessage.content,
        isUser: false,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, executionMessage]);
    } else if (serverMessage.type === 'code_execution_result') {
      const resultMessage: Message = {
        id: Date.now().toString(),
        content: `[${serverMessage.success ? 'SUCCESS' : 'FAILED'}] ${serverMessage.content}\n\nOutput:\n${serverMessage.output || 'No output'}`,
        isUser: false,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, resultMessage]);
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
        <ResizablePanels
          topPanel={<ChatSection messages={messages} onSendMessage={handleSendMessage} />}
          bottomPanel={<EditorSection code={code} onCodeChange={setCode} />}
          defaultTopHeight={400}
          minTopHeight={200}
          minBottomHeight={200}
        />
      </main>
      <Footer />
    </div>
  );
}

export default App;