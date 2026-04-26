import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownViewerProps {
  markdown: string;
  fileName?: string;
}

export default function MarkdownViewer({ markdown, fileName }: MarkdownViewerProps) {
  const [copySuccess, setCopySuccess] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(markdown);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${fileName || 'document'}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex-1">
          <p className="text-sm text-gray-500">File: {fileName}</p>
          <p className="text-xs text-gray-400 mt-1">Markdown transcription</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleCopy}
            className="px-4 py-2 text-sm text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50 transition-colors"
          >
            {copySuccess ? '✓ Copied!' : 'Copy'}
          </button>
          <button
            onClick={handleDownload}
            className="px-4 py-2 text-sm text-green-600 border border-green-300 rounded-md hover:bg-green-50 transition-colors"
          >
            Download .md
          </button>
        </div>
      </div>

      <div className="border border-gray-200 rounded-md overflow-hidden">
        <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-400"></div>
              <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
              <div className="w-3 h-3 rounded-full bg-green-400"></div>
            </div>
            <span className="text-xs text-gray-500 ml-2">Preview</span>
          </div>
        </div>
        <div className="p-4 overflow-auto max-h-96">
          <ReactMarkdown
            className="prose prose-sm max-w-none text-gray-800 leading-relaxed"
            remarkPlugins={[remarkGfm]}
            components={{
              pre: ({ children }) => (
                <pre className="bg-gray-100 p-3 rounded-md my-3 overflow-x-auto">
                  {children}
                </pre>
              ),
              code: ({ children, className, ...props }) => {
                const inline = !className;
                if (inline) {
                  return (
                    <code className="bg-gray-100 px-1 rounded" {...props}>
                      {children}
                    </code>
                  );
                }
                return (
                  <code className={className} {...props}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {markdown}
          </ReactMarkdown>
        </div>
      </div>

      <div className="mt-4">
        <details className="text-sm">
          <summary className="cursor-pointer text-gray-600 hover:text-gray-800 mb-2">
            View raw Markdown source
          </summary>
          <pre className="bg-gray-50 p-4 rounded-md overflow-auto max-h-64 text-xs text-gray-700 border border-gray-200">
            {markdown}
          </pre>
        </details>
      </div>
    </div>
  );
}
