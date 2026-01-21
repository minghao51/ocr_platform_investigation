# Frontend Improvements Design

**Date:** 2026-01-21
**Status:** Approved
**Priority:** High

## Overview

This design addresses 5 main frontend issues to improve user experience and fix critical bugs:

1. **History page not loading** - Fix API connection/routing issues
2. **Provider selection UX** - Grey out disabled providers, auto-select Gemini by default
3. **Results visibility** - Better visual separation with dedicated components
4. **Processing status persistence** - Keep metadata visible after completion
5. **Website branding** - Add favicon using icon library

## Architecture & Approach

**Design Philosophy:** "Defensive Enhancement" - Fix bugs while improving UX without changing core architecture.

**Key Decisions:**
- Keep the current polling mechanism for job status (works well)
- Add a `has_api_key` boolean to the Provider interface from the backend
- Use Heroicons (already available in React projects) for consistency
- Make Gemini the default through intelligent provider sorting rather than hardcoding
- Separate extracted data into its own reusable component

## Components & Changes

### 1. Backend API Changes

**File:** `backend/routers/providers.py`

**Change:** Modify `/providers` endpoint to include API key availability

```python
# Add to Provider response model
has_api_key: bool = Field(..., description="Whether provider has valid API key configured")

# Implementation: Check environment variables
gemini_has_key = bool(os.getenv("GEMINI_API_KEY"))
nebius_has_key = bool(os.getenv("NEBIUS_API_KEY"))
openrouter_has_key = bool(os.getenv("OPENROUTER_API_KEY"))
```

### 2. ModelSelector Component

**File:** `frontend/src/components/ModelSelector.tsx`

**Changes:**
- Add `has_api_key?: boolean` to Provider interface
- Sort providers on load: Gemini → enabled providers → disabled providers
- Render disabled providers as greyed-out, unselectable options
- Add visual indicator (2px blue left border) for Gemini
- Auto-select first available provider with API key
- Add hover tooltip for disabled providers

**Provider Sorting Logic:**
```typescript
const sortedProviders = providers.sort((a, b) => {
  // Gemini first
  if (a.name === 'gemini') return -1;
  if (b.name === 'gemini') return 1;

  // Enabled providers before disabled
  if (a.has_api_key && !b.has_api_key) return -1;
  if (!a.has_api_key && b.has_api_key) return 1;

  return 0;
});
```

**Styling for Disabled Providers:**
```tsx
<option
  key={p.name}
  value={p.name}
  disabled={!p.has_api_key}
  className={!p.has_api_key ? 'text-gray-400 bg-gray-50' : ''}
  title={!p.has_api_key ? 'No API key configured' : undefined}
>
  {p.display_name} {!p.has_api_key && '(No key)'}
</option>
```

### 3. New: ProcessingStatus Component

**File:** `frontend/src/components/ProcessingStatus.tsx`

**Purpose:** Dedicated component for displaying job processing metadata

**Features:**
- Always shows processing status card
- Displays: file name, type, provider, model, schema, timestamps
- Status badge with color coding
- Completion timestamp when job finishes
- Processing time display
- Clean, organized grid layout

**Props:**
```typescript
interface ProcessingStatusProps {
  job: Job;
}
```

### 4. New: ExtractedDataDisplay Component

**File:** `frontend/src/components/ExtractedDataDisplay.tsx`

**Purpose:** Dedicated component for displaying extracted JSON results

**Features:**
- Formatted JSON display with basic syntax highlighting
- "Copy JSON" button with success feedback
- Max height with scrollbar for large responses
- File name header
- Clean visual separation from status
- Reusable across ProcessingPage and HistoryPage

**Props:**
```typescript
interface ExtractedDataDisplayProps {
  result: any;
  fileName: string;
}
```

**Syntax Highlighting:**
```typescript
const syntaxHighlight = (json: any) => {
  if (typeof json !== 'string') {
    json = JSON.stringify(json, null, 2);
  }
  return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, (match) => {
    let cls = 'text-purple-600'; // number
    if (/^"/.test(match)) {
      if (/:$/.test(match)) {
        cls = 'text-blue-600'; // key
      } else {
        cls = 'text-green-600'; // string
      }
    } else if (/true|false/.test(match)) {
      cls = 'text-red-600'; // boolean
    } else if (/null/.test(match)) {
      cls = 'text-gray-500'; // null
    }
    return `<span class="${cls}">${match}</span>`;
  });
};
```

### 5. Refactored: ResultsDisplay Component

**File:** `frontend/src/components/ResultsDisplay.tsx`

**Changes:**
- Always render ProcessingStatus component
- Add visual spacing before ExtractedDataDisplay
- Only show ExtractedDataDisplay when job.status === 'success' and job.result exists
- Always show error card when job.status === 'error'
- Simplify component logic by delegating to child components

**New Structure:**
```tsx
<div className="space-y-6">
  {/* Always show status */}
  <ProcessingStatus job={job} />

  {/* Show error if present */}
  {job.status === 'error' && job.error && (
    <ErrorCard error={job.error} />
  )}

  {/* Show results on success */}
  {job.status === 'success' && job.result && (
    <ExtractedDataDisplay result={job.result} fileName={job.file_name} />
  )}
</div>
```

### 6. HistoryPage Component

**File:** `frontend/src/pages/HistoryPage.tsx`

**Changes:**
- Add error boundary wrapper around component
- Add comprehensive error handling in `loadJobs()`
- Show loading skeleton during initial load
- Add retry button when API calls fail
- Log errors to console with context
- Verify API endpoint is correct

**Error State UI:**
```tsx
{loadError && (
  <div className="bg-red-50 border border-red-200 rounded-lg p-6">
    <h4 className="text-sm font-semibold text-red-800 mb-2">Unable to Load Jobs</h4>
    <p className="text-sm text-red-700 mb-4">{loadError}</p>
    <button
      onClick={loadJobs}
      className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
    >
      Retry
    </button>
  </div>
)}
```

### 7. Favicon Implementation

**File:** `frontend/index.html`

**Change:** Add SVG favicon using Heroicons "DocumentText" icon

**Implementation:**
```html
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%233B82F6'><path d='M9 2a1 1 0 00-.894.553L7.382 5H4a1 1 0 000 2v10a2 2 0 002 2h12a2 2 0 002-2V7a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0012 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1zm5 1a1 1 0 012 0v6a1 1 0 11-2 0V8z'/></svg>" />
```

**Icon Choice:** DocumentText (document with text lines) represents OCR functionality
**Color:** Blue (#3B82F6) matches app's primary color scheme

## Data Flow & State Management

### Provider Selection Flow
1. Component mount → `listProviders()` fetches all providers with `has_api_key` flag
2. Providers sorted: Gemini → other enabled → disabled
3. First provider with `has_api_key=true` auto-selected
4. User changes provider → first model of that provider auto-selected
5. Disabled providers render as greyed-out, cannot be selected

### Results Display Flow
1. User submits document → processing starts
2. Polling updates `currentJob` state every 2 seconds
3. ProcessingStatus always renders with current job data
4. Job completes → ExtractedDataDisplay renders below status
5. Status remains visible with completion timestamp added
6. Error state shows error card below status card

### Error Handling Strategy
- **History page loading failures**: Catch in `loadJobs()`, show error state with retry
- **Provider API failures**: Show error in ModelSelector, disable dropdown
- **Processing failures**: Display error in ProcessingStatus, show error details
- **Network timeouts**: Add 10-second timeout to fetch calls
- **Console logging**: Log all errors with context for debugging

### State Management
- Continue using React's local state (no Redux/context needed)
- Each component manages its own loading/error states
- Parent components pass data down via props
- Keep state simple and co-located with usage

## Visual Design

### Results Section Layout
```
┌─────────────────────────────────┐
│ Processing Status               │  ← Always visible
│ ✓ SUCCESS    Completed at: ...  │
│                                  │
│ File: document.pdf               │
│ Provider: Gemini                │
│ Model: gemini-2.0-flash-exp     │
│ Schema: Invoice Template        │
│ Processing Time: 3.42s          │
└─────────────────────────────────┘
         ↓ (spacing: 1.5rem / 24px)
┌─────────────────────────────────┐
│ Extracted Data                  │  ← Only when success
│ File: document.pdf    [Copy]    │
│ ┌───────────────────────────┐   │
│ │ {                         │   │
│ │   "invoice_number": ...   │   │
│ │   "total": 1250.00,       │   │
│ │   ...                     │   │
│ │ }                         │   │
│ └───────────────────────────┘   │
└─────────────────────────────────┘
```

### Provider Dropdown Styling
- **Enabled providers:** `text-gray-900 bg-white hover:bg-gray-50`
- **Disabled providers:** `text-gray-400 bg-gray-50 cursor-not-allowed`
- **Gemini indicator:** 2px blue left border (`border-l-4 border-blue-500`)
- **Tooltip:** HTML `title` attribute on hover for disabled options

### Error States
- **Loading failure:** Red card with "Unable to load jobs" + "Retry" button
- **Empty state:** Illustration + "No jobs found" (existing)
- **Network error:** "Check your connection and try again"
- **Processing error:** Red card with error details

### JSON Display
- **Syntax highlighting:** Keys (blue), strings (green), numbers (purple), booleans (red), null (gray)
- **Scrollable:** `max-h-96 overflow-auto` for large responses
- **Copy button:** Changes to "Copied!" for 2 seconds on success

## Testing Plan

### Unit Tests
1. **ModelSelector**
   - Verify provider sorting (Gemini first, then enabled, then disabled)
   - Test auto-selection of first available provider
   - Verify disabled providers are unselectable

2. **ProcessingStatus**
   - Verify all job metadata displays correctly
   - Test status badge color coding
   - Verify timestamp formatting

3. **ExtractedDataDisplay**
   - Test JSON syntax highlighting
   - Verify copy to clipboard functionality
   - Test with various JSON structures

### Integration Tests
1. **Provider Selection Flow**
   - Load page → verify Gemini auto-selected
   - Switch provider → verify model updates
   - Verify disabled providers shown correctly

2. **Results Display Flow**
   - Submit document → verify status appears
   - Wait for completion → verify results appear below
   - Verify status persists after completion

3. **History Page**
   - Load page → verify jobs display
   - Click job → verify details shown
   - Test filter functionality
   - Verify error states display correctly

### Manual Testing Checklist
- [ ] Favicon displays in browser tab
- [ ] History page loads and displays jobs
- [ ] Gemini auto-selected on processing page
- [ ] Disabled providers appear greyed out
- [ ] Disabled providers cannot be selected
- [ ] Processing status always visible during/after processing
- [ ] Extracted data displays in separate section below status
- [ ] Copy JSON button works correctly
- [ ] Error states display appropriate messages
- [ ] Retry buttons work in error states

## Implementation Order

1. **Backend API** - Add `has_api_key` to providers endpoint (30 min)
2. **ModelSelector** - Implement sorting and disabled state (1 hour)
3. **ProcessingStatus** - Create new component (30 min)
4. **ExtractedDataDisplay** - Create new component with syntax highlighting (1 hour)
5. **ResultsDisplay** - Refactor to use new components (30 min)
6. **HistoryPage** - Add error handling and retry (30 min)
7. **Favicon** - Add to index.html (5 min)
8. **Testing** - Manual and automated testing (1 hour)

**Total Estimated Time:** ~5 hours

## Success Criteria

- [ ] History page loads successfully and displays all jobs
- [ ] Gemini is automatically selected as default provider
- [ ] Providers without API keys are greyed out and unselectable
- [ ] Processing status remains visible after completion
- [ ] Extracted data displays in a dedicated, visually separated section
- [ ] Favicon appears in browser tab
- [ ] All error states have clear messaging and retry options
- [ ] No console errors on any page
- [ ] Copy to clipboard functionality works
- [ ] JSON is syntax-highlighted for better readability

## Open Questions

None - design is complete and ready for implementation.

## Related Documentation

- [Testing Guide](../TESTING_GUIDE.md)
- [User Guide](../USER_GUIDE.md)
- [Troubleshooting](../TROUBLESHOOTING.md)
