
export type ExtractionMethod = 'auto' | 'text' | 'vision' | 'hybrid' | 'docling-parse' | 'docling-extract' | 'transcription';

interface ExtractionModeSelectorProps {
  value: ExtractionMethod;
  onChange: (method: ExtractionMethod) => void;
  fileType?: string;
}

const modes = [
  {
    id: 'auto' as ExtractionMethod,
    name: 'Auto',
    shortName: 'Smart',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    description: 'Automatically selects the best extraction method. Digital PDFs use fast text extraction, scanned documents use vision models.',
    color: 'purple',
  },
  {
    id: 'text' as ExtractionMethod,
    name: 'Text',
    shortName: 'Text',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    description: 'Fast text extraction from digital PDFs. Best for documents with selectable text. Not suitable for scanned documents or images.',
    color: 'green',
  },
  {
    id: 'vision' as ExtractionMethod,
    name: 'Vision',
    shortName: 'Vision',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
      </svg>
    ),
    description: 'Uses AI vision models to understand document structure. Best for scanned PDFs, images, and complex layouts.',
    color: 'blue',
  },
  {
    id: 'hybrid' as ExtractionMethod,
    name: 'Hybrid',
    shortName: 'Hybrid',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
      </svg>
    ),
    description: 'Combines text extraction and vision processing. Extracts text first, then uses vision to validate and enhance results.',
    color: 'orange',
  },
  {
    id: 'docling-parse' as ExtractionMethod,
    name: 'Docling Parse',
    shortName: 'Parse',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    description: 'Multi-format support (PDF, DOCX, PPTX, images). Free extraction + cheap structuring. Use for cost-sensitive processing.',
    color: 'indigo',
  },
  {
    id: 'docling-extract' as ExtractionMethod,
    name: 'Docling Extract',
    shortName: 'Extract',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    description: 'Best accuracy (86%). Local VLM, completely free, 100% private. Slower (~26s) but no API costs. Use for accuracy-critical applications.',
    color: 'emerald',
  },
  {
    id: 'transcription' as ExtractionMethod,
    name: 'Transcription',
    shortName: 'Transcription',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
      </svg>
    ),
    description: 'Full document transcription to Markdown. Ideal for documents, reports, and articles where you need the complete text content.',
    color: 'teal',
  },
];

export default function ExtractionModeSelector({ value, onChange, fileType }: ExtractionModeSelectorProps) {
  const getImageBasedWarning = () => {
    if (fileType && (fileType.startsWith('image/') || fileType === 'application/pdf') && value === 'text') {
      return (
        <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-yellow-600 mr-2 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div className="text-sm text-yellow-800">
              <p className="font-medium">Text mode may not work well with this file type</p>
              <p className="mt-1">Images and scanned PDFs typically require Vision or Hybrid mode for accurate extraction.</p>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  const colorClasses: Record<string, {
    bg: string;
    border: string;
    text: string;
    selected: string;
    icon: string;
  }> = {
    purple: {
      bg: 'bg-purple-50',
      border: 'border-purple-200',
      text: 'text-purple-900',
      selected: 'border-purple-500 ring-purple-500',
      icon: 'text-purple-600',
    },
    green: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      text: 'text-green-900',
      selected: 'border-green-500 ring-green-500',
      icon: 'text-green-600',
    },
    blue: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-900',
      selected: 'border-blue-500 ring-blue-500',
      icon: 'text-blue-600',
    },
    orange: {
      bg: 'bg-orange-50',
      border: 'border-orange-200',
      text: 'text-orange-900',
      selected: 'border-orange-500 ring-orange-500',
      icon: 'text-orange-600',
    },
    indigo: {
      bg: 'bg-indigo-50',
      border: 'border-indigo-200',
      text: 'text-indigo-900',
      selected: 'border-indigo-500 ring-indigo-500',
      icon: 'text-indigo-600',
    },
    teal: {
      bg: 'bg-teal-50',
      border: 'border-teal-200',
      text: 'text-teal-900',
      selected: 'border-teal-500 ring-teal-500',
      icon: 'text-teal-600',
    },
    emerald: {
      bg: 'bg-emerald-50',
      border: 'border-emerald-200',
      text: 'text-emerald-900',
      selected: 'border-emerald-500 ring-emerald-500',
      icon: 'text-emerald-600',
    },
  };

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-3">
        Extraction Method
      </label>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {modes.map((mode) => {
          const colors = colorClasses[mode.color];
          const isSelected = value === mode.id;

          return (
            <button
              key={mode.id}
              onClick={() => onChange(mode.id)}
              className={`
                relative p-4 rounded-lg border-2 text-left transition-all
                ${colors.bg} ${colors.border} ${colors.text}
                ${isSelected ? colors.selected + ' ring-2' : 'hover:opacity-80'}
              `}
            >
              <div className="flex items-start">
                <div className={`${colors.icon} flex-shrink-0`}>
                  {mode.icon}
                </div>
                <div className="ml-3 flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold">{mode.name}</h3>
                    {mode.id === 'auto' && (
                      <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full font-medium">
                        Recommended
                      </span>
                    )}
                  </div>
                  <p className="text-sm mt-1 opacity-80">{mode.description}</p>
                </div>
              </div>
            </button>
          );
        })}
      </div>
      {getImageBasedWarning()}
    </div>
  );
}
