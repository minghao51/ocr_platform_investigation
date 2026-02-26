import { processDocument, ProcessRequest } from '@/lib/api';
import BaseExtractionPage from './BaseExtractionPage';
import type { ExtractionMethod } from './BaseExtractionPage';

interface ProcessingPageProps {
  isAuthenticated: boolean;
  onLoginSuccess: () => void;
}

export default function ProcessingPage({ isAuthenticated, onLoginSuccess }: ProcessingPageProps) {
  const processWrapper = async (
    fileId: string,
    provider: string,
    model: string,
    extractionMethod: ExtractionMethod,
    schemaId?: number,
    schemaDefinition?: Record<string, unknown>,
    prompt?: string,
    temperature?: number,
    maxTokens?: number
  ) => {
    const request: ProcessRequest = {
      file_id: fileId,
      provider,
      model,
      extraction_method: extractionMethod,
      schema_id: schemaId,
      schema_definition: schemaDefinition,
      prompt,
      temperature,
      max_tokens: maxTokens,
    };

    return processDocument(request);
  };

  return (
    <BaseExtractionPage
      title="Smart Extraction"
      description="Upload your document and choose the extraction method that best fits your needs. Auto mode automatically selects the optimal method based on document type."
      processFunction={processWrapper}
      processingMethod="auto"
      showModeSelector={true}
      isAuthenticated={isAuthenticated}
      onLoginSuccess={onLoginSuccess}
    />
  );
}
