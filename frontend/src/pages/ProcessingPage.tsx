import { processDocument, ProcessRequest } from '@/lib/api';
import BaseExtractionPage from './BaseExtractionPage';

export default function ProcessingPage() {
  const processWrapper = async (
    fileId: string,
    provider: string,
    model: string,
    schemaId?: number,
    schemaDefinition?: Record<string, any>
  ) => {
    const request: ProcessRequest = {
      file_id: fileId,
      provider,
      model,
      schema_id: schemaId,
      schema_definition: schemaDefinition,
      extraction_method: 'auto',  // NEW: Use auto-detection
    };

    return processDocument(request);
  };

  return (
    <BaseExtractionPage
      title="Smart Extraction"
      description="Automatically selects the best extraction method for your document. Digital PDFs use fast text extraction, while scanned documents use vision models for highest accuracy."
      processFunction={processWrapper}
      processingMethod="auto"  // NEW: Auto mode
    />
  );
}
