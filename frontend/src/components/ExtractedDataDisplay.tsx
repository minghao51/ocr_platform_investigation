import { useMemo, useState } from 'react';
import MarkdownViewer from './MarkdownViewer';

interface ExtractedDataDisplayProps {
  result: unknown;
  fileName: string;
  processingMethod?: 'docling-parse' | 'transcription' | string;
}

export default function ExtractedDataDisplay({ result, fileName, processingMethod }: ExtractedDataDisplayProps) {
  const [copySuccess, setCopySuccess] = useState(false);

  // Check if result is markdown content
  const isMarkdownResult = processingMethod === 'docling-parse' || processingMethod === 'transcription';

  // Compute formattedJson unconditionally (hooks can't be called conditionally)
  const formattedJson = useMemo(
    () => JSON.stringify(result, null, 2),
    [result]
  );

  if (isMarkdownResult && typeof result === 'string') {
    return <MarkdownViewer markdown={result} fileName={fileName} />;
  }

  // Handle markdown within JSON result (e.g., { markdown: "..." })
  if (result && typeof result === 'object' && 'markdown' in result && typeof result.markdown === 'string') {
    return <MarkdownViewer markdown={result.markdown} fileName={fileName} />;
  }

  // Handle markdown within JSON result (e.g., { text: "..." })
  if (result && typeof result === 'object' && 'text' in result && typeof result.text === 'string' && isMarkdownResult) {
    return <MarkdownViewer markdown={result.text} fileName={fileName} />;
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(formattedJson);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
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
      <pre className="bg-gray-50 p-4 rounded-md overflow-auto max-h-96 text-sm leading-relaxed text-gray-800">
        {formattedJson}
      </pre>
    </div>
  );
}
