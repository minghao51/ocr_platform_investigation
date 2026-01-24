import { processTextDocument } from '@/lib/api';
import BaseExtractionPage from './BaseExtractionPage';

export default function TextExtractionPage() {
  const processWrapper = async (
    fileId: string,
    provider: string,
    model: string,
    schemaId?: number,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    _schemaDefinition?: Record<string, any>
  ) => {
    // Text extraction API currently doesn't support custom schema definitions passed inline?
    // Checking api.ts: processTextDocument(fileId, provider, model, schemaId)
    // It seems text extraction might check schema directly from ID?
    // Let's check text_processing.py.
    // It takes schema_id. If not present, it doesn't look for schema_definition in the request body directly shown in my previous view.
    // Wait, let me check backend/routers/text_processing.py again.
    // class TextProcessRequest(BaseModel): file_id, provider, model, schema_id: Optional[int]
    // It DOES NOT have schema_definition field!
    // So for text extraction, we only support saved schemas for now, or maybe the API needs update?
    // Using BaseExtractionPage, users can define a custom schema in the UI.
    // If they do, schemaId is null.
    // If text extraction backend doesn't support custom schema definition, this feature will fail for Text mode.
    // Ideally, I should strictly follow existing behavior. 
    // The previous TextExtractionPage used SchemaEditor. 
    // Did it support custom schemas?
    // Let's look at the previous content of TextExtractionPage.tsx:
    // It had "schemaDefinition" state.
    // It called processTextDocument(..., schemaId || undefined).
    // It seems it IGNORED schemaDefinition state when calling the API? 
    // Wait, processTextDocument implementation:
    // body: { file_id, provider, model, schema_id }
    // It indeed ignored custom schema definition!
    // So the previous UI was misleading or Custom Schema just didn't work for Text Extraction?
    // I will preserve this behavior (ignoring definition) but maybe I should add a comment or fix it later.
    // For now, I will match the legacy behavior.

    return processTextDocument(fileId, provider, model, schemaId);
  };

  return (
    <BaseExtractionPage
      title="Text Extraction"
      description="Best for text-based PDFs (digital documents). Use Vision tab for scanned documents."
      processFunction={processWrapper}
      processingMethod="text"
    />
  );
}
