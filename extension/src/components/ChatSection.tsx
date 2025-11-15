import { useState, useRef, useEffect } from 'react';
import type { Message } from '../App';

interface ChatSectionProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
}

function ChatSection({ messages, onSendMessage }: ChatSectionProps) {
  const [input, setInput] = useState('');
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    // Scroll to bottom when new messages arrive
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = () => {
    if (input.trim()) {
      onSendMessage(input.trim());
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto-resize textarea
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
  };

  return (
    <section className="chat-section">
      <div className="section-header">
        <h2>Chat</h2>
      </div>
      <div className="chat-container" ref={chatContainerRef}>
        {messages.map((message) => (
          <div key={message.id} className={`chat-message ${message.isUser ? 'user-message' : ''}`}>
            <div className={message.isUser ? 'user-avatar' : 'bot-avatar'}>
              {message.isUser ? 'U' : 'AI'}
            </div>
            <div className="message-content">
              {message.content.split('\n').map((line, i) => (
                <p key={i}>{line}</p>
              ))}
            </div>
          </div>
        ))}
      </div>
      <div className="chat-input-container">
        <textarea
          ref={textareaRef}
          className="chat-input"
          placeholder="Describe what you want to test..."
          rows={2}
          value={input}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
        />
        <button className="send-button" onClick={handleSend} disabled={!input.trim()}>
          <span className="send-icon">SEND</span>
        </button>
      </div>
    </section>
  );
}

export default ChatSection;