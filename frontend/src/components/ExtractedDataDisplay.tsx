import { useMemo, useState } from 'react';

interface ExtractedDataDisplayProps {
  result: unknown;
  fileName: string;
}

export default function ExtractedDataDisplay({ result, fileName }: ExtractedDataDisplayProps) {
  const [copySuccess, setCopySuccess] = useState(false);
  const formattedJson = useMemo(
    () => JSON.stringify(result, null, 2),
    [result]
  );

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
