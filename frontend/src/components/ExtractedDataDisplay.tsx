import { useState } from 'react';

interface ExtractedDataDisplayProps {
  result: unknown;
  fileName: string;
}

export default function ExtractedDataDisplay({ result, fileName }: ExtractedDataDisplayProps) {
  const [copySuccess, setCopySuccess] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(result, null, 2));
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  // Basic syntax highlighting for JSON
  const syntaxHighlight = (json: unknown): string => {
    if (typeof json !== 'string') {
      json = JSON.stringify(json, null, 2);
    }

    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g, (match: string) => {
      let cls = 'text-purple-600 font-medium'; // number
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = 'text-blue-600 font-medium'; // key
        } else {
          cls = 'text-green-600'; // string
        }
      } else if (/true|false/.test(match)) {
        cls = 'text-red-600 font-medium'; // boolean
      } else if (/null/.test(match)) {
        cls = 'text-gray-500 font-medium'; // null
      }
      return `<span class="${cls}">${match}</span>`;
    });
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-gray-500">File: {fileName}</p>
        <button
          onClick={handleCopy}
          className="px-4 py-2 text-sm text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50 transition-colors"
        >
          {copySuccess ? '✓ Copied!' : 'Copy JSON'}
        </button>
      </div>
      <pre
        className="bg-gray-50 p-4 rounded-md overflow-auto max-h-96 text-sm leading-relaxed"
        dangerouslySetInnerHTML={{ __html: syntaxHighlight(result) }}
      />
    </div>
  );
}
