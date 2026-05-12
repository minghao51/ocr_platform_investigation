export type ExtractionMethod =
  | 'auto'
  | 'text'
  | 'vision'
  | 'hybrid'
  | 'docling-parse'
  | 'docling-extract'
  | 'transcription';

export interface MethodMeta {
  id: ExtractionMethod;
  label: string;
  badgeLabel: string;
  description: string;
  color: string;
  badgeClass: string;
  pillClass: string;
  cardClass: string;
}

export const ALL_METHODS: ExtractionMethod[] = [
  'docling-extract',
  'docling-parse',
  'auto',
  'text',
  'vision',
  'hybrid',
  'transcription',
];

export const PROVIDER_REQUIRED_METHODS: ExtractionMethod[] = [
  'auto',
  'text',
  'vision',
  'hybrid',
  'docling-parse',
  'transcription',
];

export const FILE_TYPE_METHODS: Record<string, ExtractionMethod[]> = {
  image: ['docling-extract', 'vision'],
  audio: ['transcription'],
  document: ['docling-parse', 'transcription'],
};

const METHOD_META: Record<ExtractionMethod, MethodMeta> = {
  auto: {
    id: 'auto',
    label: 'Auto',
    badgeLabel: 'Auto-Detection',
    description: 'Automatically selects the best extraction method. Digital PDFs use fast text extraction, scanned documents use vision models.',
    color: 'purple',
    badgeClass: 'bg-purple-100 text-purple-800',
    pillClass: 'bg-purple-100 border-purple-300 text-purple-800',
    cardClass: 'border-purple-300 bg-purple-50 text-purple-800',
  },
  text: {
    id: 'text',
    label: 'Text',
    badgeLabel: 'Text Extraction',
    description: 'Fast text extraction from digital PDFs. Best for documents with selectable text.',
    color: 'green',
    badgeClass: 'bg-green-100 text-green-800',
    pillClass: 'bg-green-100 border-green-300 text-green-800',
    cardClass: 'border-green-300 bg-green-50 text-green-800',
  },
  vision: {
    id: 'vision',
    label: 'Vision',
    badgeLabel: 'Vision Extraction',
    description: 'Uses AI vision models to understand document structure. Best for scanned PDFs, images, and complex layouts.',
    color: 'blue',
    badgeClass: 'bg-blue-100 text-blue-800',
    pillClass: 'bg-blue-100 border-blue-300 text-blue-800',
    cardClass: 'border-blue-300 bg-blue-50 text-blue-800',
  },
  hybrid: {
    id: 'hybrid',
    label: 'Hybrid',
    badgeLabel: 'Hybrid Extraction',
    description: 'Combines text extraction and vision processing. Extracts text first, then uses vision to validate.',
    color: 'orange',
    badgeClass: 'bg-orange-100 text-orange-800',
    pillClass: 'bg-orange-100 border-orange-300 text-orange-800',
    cardClass: 'border-orange-300 bg-orange-50 text-orange-800',
  },
  'docling-parse': {
    id: 'docling-parse',
    label: 'PyMuPDF + LLM',
    badgeLabel: 'PyMuPDF + LLM',
    description: 'PyMuPDF parsing for PDFs (Docling fallback for DOCX/PPTX), then LLM structuring. Cost-sensitive with flexible provider/model control.',
    color: 'indigo',
    badgeClass: 'bg-indigo-100 text-indigo-800',
    pillClass: 'bg-indigo-100 border-indigo-300 text-indigo-800',
    cardClass: 'border-indigo-300 bg-indigo-50 text-indigo-800',
  },
  'docling-extract': {
    id: 'docling-extract',
    label: 'Docling Local Extract',
    badgeLabel: 'Docling Local Extract',
    description: 'Best accuracy (86%). Local VLM, completely free, 100% private. Slower (~26s) but no API costs.',
    color: 'emerald',
    badgeClass: 'bg-emerald-100 text-emerald-800',
    pillClass: 'bg-emerald-100 border-emerald-300 text-emerald-800',
    cardClass: 'border-emerald-300 bg-emerald-50 text-emerald-800',
  },
  transcription: {
    id: 'transcription',
    label: 'Transcription',
    badgeLabel: 'Transcription',
    description: 'Full document transcription to Markdown. Ideal for documents, reports, and articles.',
    color: 'teal',
    badgeClass: 'bg-teal-100 text-teal-800',
    pillClass: 'bg-teal-100 border-teal-300 text-teal-800',
    cardClass: 'border-teal-300 bg-teal-50 text-teal-800',
  },
};

export function getMethodMeta(method: ExtractionMethod): MethodMeta {
  return METHOD_META[method] || {
    id: method,
    label: method,
    badgeLabel: 'Unknown',
    description: '',
    color: 'gray',
    badgeClass: 'bg-gray-100 text-gray-800',
    pillClass: 'bg-gray-100 border-gray-300 text-gray-800',
    cardClass: 'border-gray-300 bg-gray-50 text-gray-800',
  };
}

export function getMethodBadgeClass(method: ExtractionMethod): string {
  return getMethodMeta(method).badgeClass;
}

export function getMethodBadgeLabel(method: ExtractionMethod): string {
  return getMethodMeta(method).badgeLabel;
}

export function getMethodPillClass(method: ExtractionMethod): string {
  return getMethodMeta(method).pillClass;
}

export const PILL_CLASS_DISABLED = 'bg-gray-100 border-gray-200 text-gray-400 cursor-not-allowed';
