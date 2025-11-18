import { useState, useRef, useEffect, ReactNode } from 'react';
import './ResizablePanels.css';

interface ResizablePanelsProps {
  topPanel: ReactNode;
  bottomPanel: ReactNode;
  defaultTopHeight?: number;
  minTopHeight?: number;
  minBottomHeight?: number;
}

function ResizablePanels({
  topPanel,
  bottomPanel,
  defaultTopHeight = 300,
  minTopHeight = 200,
  minBottomHeight = 200,
}: ResizablePanelsProps) {
  const [topHeight, setTopHeight] = useState(defaultTopHeight);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging || !containerRef.current) return;

      const containerRect = containerRef.current.getBoundingClientRect();
      const newTopHeight = e.clientY - containerRect.top;
      const maxTopHeight = containerRect.height - minBottomHeight;

      if (newTopHeight >= minTopHeight && newTopHeight <= maxTopHeight) {
        setTopHeight(newTopHeight);
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'row-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isDragging, minTopHeight, minBottomHeight]);

  const handleMouseDown = () => {
    setIsDragging(true);
  };

  return (
    <div ref={containerRef} className="resizable-panels">
      <div className="resizable-panel top-panel" style={{ height: `${topHeight}px` }}>
        {topPanel}
      </div>
      <div
        className={`resizable-divider ${isDragging ? 'dragging' : ''}`}
        onMouseDown={handleMouseDown}
      >
        <div className="divider-handle">
          <div className="divider-line"></div>
          <div className="divider-line"></div>
        </div>
      </div>
      <div className="resizable-panel bottom-panel" style={{ flex: 1 }}>
        {bottomPanel}
      </div>
    </div>
  );
}

export default ResizablePanels;
