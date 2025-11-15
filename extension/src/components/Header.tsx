interface HeaderProps {
  status: 'connected' | 'connecting' | 'error';
}

function Header({ status }: HeaderProps) {
  const statusConfig = {
    connected: { dot: 'connected', text: 'Ready' },
    connecting: { dot: '', text: 'Connecting...' },
    error: { dot: 'error', text: 'Disconnected' },
  };

  const config = statusConfig[status];

  return (
    <header className="header">
      <div className="header-content">
        <div className="logo">
          <span className="logo-icon">AQ</span>
          <h1 className="logo-text">Agent Q</h1>
        </div>
        <div className="status-indicator">
          <span className={`status-dot ${config.dot}`}></span>
          <span className="status-text">{config.text}</span>
        </div>
      </div>
    </header>
  );
}

export default Header;