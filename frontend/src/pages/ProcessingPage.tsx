import { processDocument, ProcessRequest } from '@/lib/api';
import BaseExtractionPage from './BaseExtractionPage';
import type { ExtractionMethod } from './BaseExtractionPage';

interface ProcessingPageProps {
  isAuthenticated: boolean;
}

export default function ProcessingPage({ isAuthenticated }: ProcessingPageProps) {
  const processWrapper = async (
    fileId: string,
    provider: string,
    model: string,
    extractionMethod: ExtractionMethod,
    schemaId?: number,
    schemaDefinition?: Record<string, unknown>,
    prompt?: string,
    temperature?: number,
    maxTokens?: number,
    qualityThreshold?: number,
    autoPreprocess?: boolean,
    skipQuality?: boolean,
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
      quality_threshold: qualityThreshold,
      auto_preprocess: autoPreprocess,
      skip_quality: skipQuality,
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
    />
  );
}
