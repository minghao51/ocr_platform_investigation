# Frontend Architecture

## Entry Point
- `frontend/src/main.tsx` - React app bootstrap
- `frontend/src/App.tsx` - Main app with routing

## Pages (`frontend/src/pages/`)
| File | Purpose |
|------|---------|
| `LoginPage.tsx` | Authentication UI |
| `ProcessingPage.tsx` | Document extraction interface |
| `HistoryPage.tsx` | Past extraction jobs |
| `MethodologyPage.tsx` | Documentation/info |
| `BaseExtractionPage.tsx` | Shared extraction logic |

## Components (`frontend/src/components/`)
| File | Purpose |
|------|---------|
| `FileUpload.tsx` | Drag-drop file upload |
| `ExtractionModeSelector.tsx` | Auto/Text/Vision/Hybrid selection |
| `ModelSelector.tsx` | VLM provider & model dropdown |
| `SchemaEditor.tsx` | JSON schema builder |
| `ExtractedDataDisplay.tsx` | Results display |
| `ResultsDisplay.tsx` | Output formatting |
| `ProcessingStatus.tsx` | Job progress tracking |
| `AdvancedOptions.tsx` | Temperature, max tokens, custom prompt |

## API Client
- `frontend/src/lib/api.ts` - Fetch wrappers, auth token management
