import { useState, useRef, useEffect } from 'react';
import { monaco } from '../monaco-setup';

interface EditorSectionProps {
  code: string;
  onCodeChange: (code: string) => void;
}

function EditorSection({ code, onCodeChange }: EditorSectionProps) {
  const [isCodeGenerated, setIsCodeGenerated] = useState(false);
  const editorRef = useRef<HTMLDivElement>(null);
  const monacoEditorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);

  useEffect(() => {
    if (editorRef.current && !monacoEditorRef.current) {
      // Create Monaco Editor instance
      monacoEditorRef.current = monaco.editor.create(editorRef.current, {
        value: code,
        language: 'typescript',
        theme: 'vs-dark',
        fontSize: 13,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        wordWrap: 'on',
        tabSize: 2,
        lineNumbers: 'on',
        automaticLayout: true,
        fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
      });

      // Listen for content changes
      monacoEditorRef.current.onDidChangeModelContent(() => {
        const value = monacoEditorRef.current?.getValue() || '';
        onCodeChange(value);
        if (value !== '// Your Playwright test will appear here\n') {
          setIsCodeGenerated(true);
        }
      });
    }

    return () => {
      monacoEditorRef.current?.dispose();
    };
  }, []);

  useEffect(() => {
    // Update editor content when code prop changes
    if (monacoEditorRef.current && monacoEditorRef.current.getValue() !== code) {
      monacoEditorRef.current.setValue(code);
    }
  }, [code]);

  const handleRun = () => {
    console.log('Run preview - Coming in Milestone 5');
  };

  const handleSave = () => {
    console.log('Save test - Coming in Milestone 7');
  };

  const handleExport = () => {
    console.log('Export test - Coming in Milestone 10');
  };

  return (
    <section className="editor-section">
      <div className="section-header">
        <h2>Playwright Code</h2>
        <div className="editor-actions">
          <button
            className="action-button"
            onClick={handleRun}
            disabled={!isCodeGenerated}
            title="Run Preview"
          >
            Run
          </button>
          <button
            className="action-button secondary"
            onClick={handleSave}
            disabled={!isCodeGenerated}
            title="Save Test"
          >
            Save
          </button>
          <button
            className="action-button secondary"
            onClick={handleExport}
            disabled={!isCodeGenerated}
            title="Export"
          >
            Export
          </button>
        </div>
      </div>
      <div className="editor-container">
        <div ref={editorRef} style={{ width: '100%', height: '100%' }} />
      </div>
    </section>
  );
}

export default EditorSection;