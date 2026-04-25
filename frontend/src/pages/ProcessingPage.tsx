import { processDocument, ProcessRequest } from '@/lib/api';
import BaseExtractionPage from './BaseExtractionPage';
import type { ExtractionMethod } from './BaseExtractionPage';

interface ProcessingPageProps {
  isAuthenticated: boolean;
}

export default function ProcessingPage({ isAuthenticated }: ProcessingPageProps) {
  const processWrapper = async (
    fileId: string,
    provider: string | undefined,
    model: string | undefined,
    extractionMethod: ExtractionMethod,
    schemaId?: number,
    schemaDefinition?: Record<string, unknown>,
    prompt?: string,
    temperature?: number,
    maxTokens?: number,
    qualityThreshold?: number,
    autoPreprocess?: boolean,
    skipQuality?: boolean,
    schemaMode?: 'raw' | 'auto-detect' | 'manual',
  ) => {
    const request: ProcessRequest = {
      file_id: fileId,
      extraction_method: extractionMethod,
      schema_id: schemaId,
      schema_definition: schemaDefinition,
      schema_mode: schemaMode,
      prompt,
      temperature,
      max_tokens: maxTokens,
      quality_threshold: qualityThreshold,
      auto_preprocess: autoPreprocess,
      skip_quality: skipQuality,
    };
    if (provider) {
      request.provider = provider;
    }
    if (model) {
      request.model = model;
    }

    return processDocument(request);
  };

  return (
    <BaseExtractionPage
      title="Smart Extraction"
      description="Upload your document. The extraction method is auto-detected based on file type, but you can override it."
      processFunction={processWrapper}
      processingMethod="auto"
      isAuthenticated={isAuthenticated}
    />
  );
}
