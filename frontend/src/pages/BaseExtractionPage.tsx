import { useState, useRef, useEffect } from 'react';
import { Job, getAuthToken, getJobStatus, suggestSchema, createSchema, SchemaSuggestion, checkFileQuality, QualityReport, listSchemaSuggestions, getExtractSettings, ExtractSettings } from '@/lib/api';
import { JobStatusWebSocket } from '@/lib/websocket';
import FileUpload from '@/components/FileUpload';
import MethodModelSelector from '@/components/MethodModelSelector';
import SchemaEditor from '@/components/SchemaEditor';
import ResultsDisplay from '@/components/ResultsDisplay';
import type { ExtractionMethod } from '@/lib/methods';
import AdvancedOptions from '@/components/AdvancedOptions';
import { QualityBadge } from '@/components/QualityBadge';

export type { ExtractionMethod };

interface BaseExtractionPageProps {
    title: string;
    description: string;
    processFunction: (
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
    ) => Promise<{ job_id: number }>;
    processingMethod?: ExtractionMethod;
    isAuthenticated: boolean;
}

export default function BaseExtractionPage({
    title,
    description,
    processFunction,
    processingMethod = 'auto',
    isAuthenticated,
}: BaseExtractionPageProps) {
    const [fileId, setFileId] = useState<string | null>(null);
    const [fileName, setFileName] = useState<string | null>(null);
    const [fileType, setFileType] = useState<string | null>(null);
    const [extractionMethod, setExtractionMethod] = useState<ExtractionMethod>(processingMethod);
    const [provider, setProvider] = useState('');
    const [model, setModel] = useState('');
    const [schemaId, setSchemaId] = useState<number | null>(null);
    const [schemaDefinition, setSchemaDefinition] = useState<Record<string, unknown> | null>(null);
    const [isSchemaValid, setIsSchemaValid] = useState(false);
    const [schemaMode, setSchemaMode] = useState<'raw' | 'auto-detect' | 'manual'>('auto-detect');
    const [cachedAutoSchema, setCachedAutoSchema] = useState<Record<string, unknown> | null>(null);
    const [customPrompt, setCustomPrompt] = useState('');
    const [temperature, setTemperature] = useState(0.1);
    const [maxTokens, setMaxTokens] = useState(8192);
    const [qualityThreshold, setQualityThreshold] = useState(40);
    const [autoPreprocess, setAutoPreprocess] = useState(true);
    const [skipQuality, setSkipQuality] = useState(false);
    const [settings, setSettings] = useState<ExtractSettings | null>(null);
    const [currentJob, setCurrentJob] = useState<Job | null>(null);
    const [processing, setProcessing] = useState(false);
    const [schemaSuggestion, setSchemaSuggestion] = useState<SchemaSuggestion | null>(null);
    const [suggestingSchema, setSuggestingSchema] = useState(false);
    const [schemaNameDraft, setSchemaNameDraft] = useState('');
    const [savingSchema, setSavingSchema] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [validationErrors, setValidationErrors] = useState<{
        prompt?: string;
        temperature?: string;
        maxTokens?: string;
    }>({});
    const [qualityReport, setQualityReport] = useState<QualityReport | null>(null);
    const [checkingQuality, setCheckingQuality] = useState(false);
    const [suggestionHistory, setSuggestionHistory] = useState<SchemaSuggestion[]>([]);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const [showHistory, setShowHistory] = useState(false);

    const requiresProvider = ['auto', 'text', 'vision', 'hybrid', 'docling-parse', 'transcription'].includes(extractionMethod);
    const supportsRawSchemaMode = extractionMethod === 'docling-parse';

    const wsConnection = useRef<JobStatusWebSocket | null>(null);
    const pollingInterval = useRef<number | null>(null);

    useEffect(() => {
        if (!supportsRawSchemaMode && schemaMode === 'raw') {
            setSchemaMode('auto-detect');
        }
    }, [schemaMode, supportsRawSchemaMode]);

    useEffect(() => {
        getExtractSettings()
            .then((s) => {
                setSettings(s);
                setTemperature(s.defaults.temperature.default);
                setMaxTokens(s.defaults.max_tokens.default);
                setQualityThreshold(s.defaults.quality_threshold.default);
                setAutoPreprocess(s.defaults.auto_preprocess.default);
                setSkipQuality(s.defaults.skip_quality.default);
            })
            .catch(() => {});
    }, []);

    useEffect(() => {
        return () => {
            wsConnection.current?.disconnect();
            if (pollingInterval.current !== null) {
                window.clearInterval(pollingInterval.current);
            }
        };
    }, []);

    const handleFileUpload = (uploadedFileId: string, uploadedFileName: string, uploadedFileType?: string) => {
        setFileId(uploadedFileId);
        setFileName(uploadedFileName);
        setFileType(uploadedFileType || null);
        const ftm = settings?.file_type_methods;
        if (ftm) {
            if (ftm[uploadedFileType || '']) {
                setExtractionMethod(ftm[uploadedFileType || ''] as ExtractionMethod);
            } else if (uploadedFileType?.startsWith('image/') && ftm['image/*']) {
                setExtractionMethod(ftm['image/*'] as ExtractionMethod);
            } else if (uploadedFileType?.startsWith('audio/') && ftm['audio/*']) {
                setExtractionMethod(ftm['audio/*'] as ExtractionMethod);
            } else {
                setExtractionMethod('docling-parse');
            }
        } else {
            if (uploadedFileType === 'application/pdf') {
                setExtractionMethod('docling-extract');
            } else if (uploadedFileType?.startsWith('image/')) {
                setExtractionMethod('docling-extract');
            } else if (uploadedFileType?.startsWith('audio/')) {
                setExtractionMethod('transcription');
            } else {
                setExtractionMethod('docling-parse');
            }
        }
        setError(null);
        setQualityReport(null);
        setCachedAutoSchema(null);
        setSchemaSuggestion(null);
    };

    const handleQualityCheck = async () => {
        if (!fileId) return;
        const isImage = fileType?.startsWith('image/');
        if (!isImage) return;
        setCheckingQuality(true);
        try {
            const report = await checkFileQuality(fileId);
            setQualityReport(report);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Quality check failed');
        } finally {
            setCheckingQuality(false);
        }
    };

    const validateAdvancedOptions = (): boolean => {
        const errors: { prompt?: string; temperature?: string; maxTokens?: string } = {};
        const maxPromptLen = settings?.defaults.prompt_max_length ?? 2000;
        const tempMax = settings?.defaults.temperature.max ?? 2;
        const tokensMin = settings?.defaults.max_tokens.min ?? 256;
        const tokensMax = settings?.defaults.max_tokens.max ?? 65536;

        if (customPrompt.length > maxPromptLen) {
            errors.prompt = `Prompt must be ${maxPromptLen} characters or less`;
        }

        if (temperature < 0 || temperature > tempMax) {
            errors.temperature = `Temperature must be between 0 and ${tempMax}`;
        }

        if (maxTokens < tokensMin || maxTokens > tokensMax) {
            errors.maxTokens = `Max tokens must be between ${tokensMin} and ${tokensMax}`;
        }

        setValidationErrors(errors);
        return Object.keys(errors).length === 0;
    };

    const isTranscription = extractionMethod === 'transcription';

    const handleProcess = async () => {
        if (!fileId || (requiresProvider && (!provider || !model))) {
            setError('Please complete all required fields');
            return;
        }

        if (!isTranscription && schemaMode === 'manual' && !schemaDefinition) {
            setError('Please define a schema before processing');
            return;
        }

        if (!isTranscription && schemaMode === 'manual' && schemaDefinition && !isSchemaValid) {
            setError('Please fix the schema definition before processing');
            return;
        }

        if (!validateAdvancedOptions()) {
            setError('Please fix validation errors');
            return;
        }

        let effectiveSchemaDefinition = schemaDefinition;

        if (schemaMode === 'auto-detect' && !cachedAutoSchema) {
            setError('Auto-detecting schema...');
            setSuggestingSchema(true);
            try {
                const suggestion = await suggestSchema([fileId]);
                setSchemaSuggestion(suggestion);
                setSchemaNameDraft(suggestion.draft_name || 'Suggested Schema');
                setSchemaDefinition(suggestion.schema_definition);
                setCachedAutoSchema(suggestion.schema_definition);
                effectiveSchemaDefinition = suggestion.schema_definition;
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to suggest schema');
                setSuggestingSchema(false);
                return;
            } finally {
                setSuggestingSchema(false);
            }
        } else if (schemaMode === 'auto-detect' && cachedAutoSchema) {
            effectiveSchemaDefinition = cachedAutoSchema;
        }

        setProcessing(true);
        setError(null);

        try {
            const response = await processFunction(
                fileId,
                provider,
                model,
                extractionMethod,
                isTranscription ? undefined : (schemaId || undefined),
                schemaMode === 'raw' ? undefined : (schemaId ? undefined : (effectiveSchemaDefinition || undefined)),
                customPrompt || undefined,
                temperature,
                maxTokens,
                skipQuality ? undefined : qualityThreshold,
                skipQuality ? false : autoPreprocess,
                skipQuality,
                schemaMode,
            );

            setCurrentJob({
                job_id: response.job_id,
                file_name: fileName || 'Unknown',
                file_type: fileType || 'unknown',
                status: 'pending',
                provider: provider || 'docling-local',
                model: model || extractionMethod,
                schema_name: schemaMode === 'raw' ? 'Raw' : effectiveSchemaDefinition ? 'Custom' : 'Auto-detect',
                processing_method: extractionMethod === 'auto' ? undefined : extractionMethod,
            });

            connectJobStatusUpdates(response.job_id);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Processing failed');
            setProcessing(false);
        }
    };

    const handleSuggestSchema = async () => {
        if (!fileId) {
            setError('Upload a file before requesting a schema suggestion');
            return;
        }

        setSuggestingSchema(true);
        setError(null);
        try {
            const suggestion = await suggestSchema([fileId]);
            setSchemaSuggestion(suggestion);
            setSchemaNameDraft(suggestion.draft_name || 'Suggested Schema');
            setSchemaId(null);
            setSchemaDefinition(suggestion.schema_definition);
            setCachedAutoSchema(suggestion.schema_definition);
            setIsSchemaValid(true);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to suggest schema');
        } finally {
            setSuggestingSchema(false);
        }
    };

    const handleSaveSchema = async () => {
        if (!schemaDefinition || !schemaNameDraft.trim()) {
            setError('Enter a schema name before saving');
            return;
        }

        setSavingSchema(true);
        setError(null);
        try {
            const created = await createSchema({
                name: schemaNameDraft.trim(),
                description: schemaSuggestion?.rationale || 'Saved from schema suggestion',
                definition: schemaDefinition,
            });
            setSchemaId(created.id || null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to save schema');
        } finally {
            setSavingSchema(false);
        }
    };

    const loadSuggestionHistory = async () => {
        if (showHistory) {
            setShowHistory(false);
            return;
        }
        setLoadingHistory(true);
        try {
            const data = await listSchemaSuggestions();
            setSuggestionHistory(data);
            setShowHistory(true);
        } catch {
            setSuggestionHistory([]);
        } finally {
            setLoadingHistory(false);
        }
    };

    const applyHistorySuggestion = (suggestion: SchemaSuggestion) => {
        setSchemaDefinition(suggestion.schema_definition);
        setSchemaSuggestion(suggestion);
        setSchemaNameDraft(suggestion.draft_name || 'Suggested Schema');
        setSchemaId(null);
        setIsSchemaValid(true);
        setShowHistory(false);
    };

    const stopStatusUpdates = () => {
        wsConnection.current?.disconnect();
        wsConnection.current = null;
        if (pollingInterval.current !== null) {
            window.clearInterval(pollingInterval.current);
            pollingInterval.current = null;
        }
    };

    const startPollingJobStatus = (jobId: number) => {
        stopStatusUpdates();

        const poll = async () => {
            try {
                const job = await getJobStatus(jobId);
                setCurrentJob(job);

                if (job.status === 'success' || job.status === 'error') {
                    setProcessing(false);
                    stopStatusUpdates();
                }
            } catch (pollError) {
                console.error('Polling error:', pollError);
                setError(pollError instanceof Error ? pollError.message : 'Failed to refresh job status');
                setProcessing(false);
                stopStatusUpdates();
            }
        };

        void poll();
        pollingInterval.current = window.setInterval(() => {
            void poll();
        }, 2000);
    };

    const connectWebSocketForJobStatus = async (jobId: number) => {
        stopStatusUpdates();

        wsConnection.current = new JobStatusWebSocket();

        wsConnection.current.onStatusChange((job) => {
            console.log('Job status update:', job);
            setCurrentJob(job);

            if (job.status === 'success' || job.status === 'error') {
                setProcessing(false);
            }
        });

        wsConnection.current.onError((error) => {
            console.error('WebSocket error:', error);
            setError(`Connection error: ${error.message}`);
        });

        await wsConnection.current.connect(jobId);
    };

    const connectJobStatusUpdates = (jobId: number) => {
        const token = getAuthToken();
        if (token) {
            void connectWebSocketForJobStatus(jobId);
            return;
        }
        startPollingJobStatus(jobId);
    };



    const handleReset = () => {
        stopStatusUpdates();

        setFileId(null);
        setFileName(null);
        setFileType(null);
        setCurrentJob(null);
        setError(null);
        setSchemaSuggestion(null);
        setSchemaNameDraft('');
        setIsSchemaValid(Boolean(schemaDefinition));
        setValidationErrors({});
        setQualityReport(null);
        setCachedAutoSchema(null);
        setSchemaMode('auto-detect');
    };

    return (
        <div className="max-w-4xl mx-auto p-6">
            <div className="mb-6">
                <h1 className="text-3xl font-bold mb-2">{title}</h1>
                <p className="text-sm text-gray-600">{description}</p>
            </div>

            <div className="space-y-8">
                {/* Step 1: File Upload */}
                <section>
                    <h2 className="text-xl font-semibold mb-4">Step 1: Upload Document</h2>
                    {!fileId ? (
                        <div className="space-y-4">
                            <FileUpload
                                onUpload={handleFileUpload}
                                disabled={false}
                                disabledMessage="Guest uploads are available with rate limits."
                            />
                            {!isAuthenticated && (
                                <p className="text-sm text-gray-500">
                                    Guest mode can upload and test extraction with rate limits. Sign in from the top-right menu if you want saved account history.
                                </p>
                            )}
                        </div>
                    ) : (
                        <div className="space-y-3">
                            <div className="p-4 bg-green-50 border border-green-200 rounded-md flex items-center justify-between">
                                <div>
                                    <p className="font-medium text-green-800">{fileName}</p>
                                    <p className="text-sm text-green-600">File uploaded successfully</p>
                                </div>
                                <button
                                    onClick={handleReset}
                                    className="px-4 py-2 text-sm text-green-700 border border-green-300 rounded-md hover:bg-green-100"
                                >
                                    Change File
                                </button>
                            </div>
                            {fileType?.startsWith('image/') && (
                                <div className="space-y-3">
                                    <button
                                        onClick={handleQualityCheck}
                                        disabled={checkingQuality}
                                        className="px-4 py-2 text-sm font-medium text-slate-700 border border-slate-300 rounded-md hover:bg-slate-50 disabled:bg-slate-100"
                                    >
                                        {checkingQuality ? 'Checking...' : 'Check Image Quality'}
                                    </button>
                                    {qualityReport && <QualityBadge report={qualityReport} />}
                                </div>
                            )}
                        </div>
                    )}
                </section>

                {/* Step 2: Method & Model Selection */}
                <section>
                    <h2 className="text-xl font-semibold mb-4">Step 2: Select Method & Model</h2>
                    <MethodModelSelector
                        provider={provider}
                        model={model}
                        extractionMethod={extractionMethod}
                        fileType={fileType}
                        fileId={fileId}
                        onProviderChange={setProvider}
                        onModelChange={setModel}
                        onMethodChange={setExtractionMethod}
                    />
                </section>

                {/* Step 3: Schema Configuration */}
                {!isTranscription && (
                <section>
                    <h2 className="text-xl font-semibold mb-4">Step 3: Schema Configuration</h2>

                    {/* Schema Mode Selector */}
                    <div className="mb-4">
                        <div className="flex gap-2">
                            <button
                                onClick={() => setSchemaMode('raw')}
                                disabled={!supportsRawSchemaMode}
                                className={`px-4 py-2 text-sm font-medium rounded-md border transition-colors ${
                                    schemaMode === 'raw'
                                        ? 'bg-teal-100 border-teal-300 text-teal-800'
                                        : 'border-gray-300 text-gray-600 hover:bg-gray-50'
                                }`}
                            >
                                Raw
                            </button>
                            <button
                                onClick={() => setSchemaMode('auto-detect')}
                                className={`px-4 py-2 text-sm font-medium rounded-md border transition-colors ${
                                    schemaMode === 'auto-detect'
                                        ? 'bg-indigo-100 border-indigo-300 text-indigo-800'
                                        : 'border-gray-300 text-gray-600 hover:bg-gray-50'
                                }`}
                            >
                                Auto-detect
                            </button>
                            <button
                                onClick={() => setSchemaMode('manual')}
                                className={`px-4 py-2 text-sm font-medium rounded-md border transition-colors ${
                                    schemaMode === 'manual'
                                        ? 'bg-blue-100 border-blue-300 text-blue-800'
                                        : 'border-gray-300 text-gray-600 hover:bg-gray-50'
                                }`}
                            >
                                Manual
                            </button>
                        </div>
                    </div>

                    {!supportsRawSchemaMode && (
                        <p className="mb-4 text-sm text-gray-500">
                            Raw Markdown output is currently available with the PyMuPDF + LLM method.
                        </p>
                    )}

                    {/* Raw Mode */}
                    {schemaMode === 'raw' && (
                        <div className="rounded-lg border border-teal-200 bg-teal-50 p-4">
                            <p className="text-sm text-teal-800">
                                <strong>Raw output:</strong> Output will be raw text/markdown without structure. No schema is required.
                            </p>
                        </div>
                    )}

                    {/* Auto-detect Mode */}
                    {schemaMode === 'auto-detect' && (
                        <div className="space-y-4">
                            <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-4">
                                <p className="text-sm text-indigo-800">
                                    <strong>Auto-detect:</strong> Schema will be auto-detected from the document when you process. No manual schema definition needed.
                                </p>
                            </div>

                            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                                <div>
                                    <p className="text-sm font-medium text-indigo-900">Schema Suggestion</p>
                                    <p className="text-sm text-indigo-700">
                                        {cachedAutoSchema
                                            ? 'Schema detected — review and re-run suggestion if needed'
                                            : 'Run suggestion to preview schema before processing'}
                                    </p>
                                </div>
                                <button
                                    onClick={handleSuggestSchema}
                                    disabled={!fileId || suggestingSchema}
                                    className="px-4 py-2 text-sm font-medium text-indigo-700 border border-indigo-300 rounded-md hover:bg-indigo-100 disabled:bg-indigo-100/50 disabled:text-indigo-400"
                                >
                                    {suggestingSchema ? 'Detecting...' : 'Suggest Schema'}
                                </button>
                            </div>

                            {schemaSuggestion && (
                                <div className="space-y-3 border-t border-indigo-200 pt-4">
                                    <div className="flex flex-wrap items-center gap-2 text-sm">
                                        <span className="rounded-full bg-white px-3 py-1 text-indigo-700 border border-indigo-200">
                                            {schemaSuggestion.document_type || 'document'}
                                        </span>
                                        <span className="text-indigo-800">
                                            Confidence: {(schemaSuggestion.confidence * 100).toFixed(0)}%
                                        </span>
                                        <span className="text-indigo-700">
                                            via {schemaSuggestion.provider} / {schemaSuggestion.model}
                                        </span>
                                    </div>
                                    <p className="text-sm text-indigo-900">{schemaSuggestion.rationale}</p>
                                    {Object.keys(schemaSuggestion.field_descriptions || {}).length > 0 && (
                                        <div className="rounded-md bg-white/70 p-3">
                                            <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">Suggested fields</p>
                                            <div className="mt-2 grid gap-2 md:grid-cols-2">
                                                {Object.entries(schemaSuggestion.field_descriptions).map(([field, description]) => (
                                                    <div key={field} className="text-sm text-indigo-900">
                                                        <span className="font-medium">{field}:</span> {description}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                    {isAuthenticated && (
                                        <div className="flex flex-col gap-2 md:flex-row">
                                            <input
                                                value={schemaNameDraft}
                                                onChange={(e) => setSchemaNameDraft(e.target.value)}
                                                placeholder="Schema name"
                                                className="flex-1 rounded-md border border-indigo-200 px-3 py-2 text-sm"
                                            />
                                            <button
                                                onClick={handleSaveSchema}
                                                disabled={savingSchema || !schemaDefinition || !isSchemaValid}
                                                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:bg-indigo-300"
                                            >
                                                {savingSchema ? 'Saving...' : 'Save Schema'}
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Manual Mode */}
                    {schemaMode === 'manual' && (
                        <div className="space-y-4">
                            <SchemaEditor
                                schemaId={schemaId}
                                schemaDefinition={schemaDefinition}
                                onSchemaSelect={setSchemaId}
                                onDefinitionChange={setSchemaDefinition}
                                onValidityChange={setIsSchemaValid}
                            />

                            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between rounded-lg border border-indigo-200 bg-indigo-50 p-4">
                                <div>
                                    <p className="text-sm font-medium text-indigo-900">Schema Learning</p>
                                    <p className="text-sm text-indigo-700">
                                        Generate a draft schema from the uploaded document, then review and refine it in the editor.
                                    </p>
                                </div>
                                <button
                                    onClick={handleSuggestSchema}
                                    disabled={!fileId || suggestingSchema}
                                    className="px-4 py-2 text-sm font-medium text-indigo-700 border border-indigo-300 rounded-md hover:bg-indigo-100 disabled:bg-indigo-100/50 disabled:text-indigo-400"
                                >
                                    {suggestingSchema ? 'Suggesting...' : 'Suggest Schema From Document'}
                                </button>
                            </div>
                        </div>
                    )}
                </section>
                )}

                {/* Schema Suggestion History */}
                {isAuthenticated && !isTranscription && (
                <div className="space-y-3">
                    <button
                        onClick={loadSuggestionHistory}
                        className="text-sm text-indigo-700 hover:text-indigo-900 font-medium"
                    >
                        {showHistory ? 'Hide past suggestions' : 'Show past suggestions'}
                    </button>
                    {loadingHistory && <p className="text-sm text-gray-500">Loading...</p>}
                    {showHistory && suggestionHistory.length === 0 && !loadingHistory && (
                        <p className="text-sm text-gray-500">No past suggestions found.</p>
                    )}
                    {showHistory && suggestionHistory.length > 0 && (
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                            {suggestionHistory.slice(0, 10).map((s) => (
                                <button
                                    key={s.id}
                                    onClick={() => applyHistorySuggestion(s)}
                                    className="w-full text-left p-3 rounded-md border border-gray-200 hover:bg-indigo-50 transition-colors"
                                >
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm font-medium text-gray-900">
                                            {s.draft_name || s.document_type || `Suggestion #${s.id}`}
                                        </span>
                                        <span className="text-xs text-gray-500">
                                            {(s.confidence * 100).toFixed(0)}% confidence
                                        </span>
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">
                                        {s.provider}/{s.model} — {new Date(s.created_at).toLocaleDateString()}
                                    </p>
                                </button>
                            ))}
                        </div>
                    )}
                </div>
                )}

                {isTranscription && (
                <div className="rounded-lg border border-teal-200 bg-teal-50 p-4">
                    <p className="text-sm text-teal-800">
                        Transcription mode outputs raw Markdown — no schema is required. You can optionally add a custom prompt in Advanced Options to guide formatting.
                    </p>
                </div>
                )}

                {/* Advanced Options (collapsed by default) */}
                <section>
                    <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
                        <AdvancedOptions
                            prompt={customPrompt}
                            temperature={temperature}
                            maxTokens={maxTokens}
                            onPromptChange={setCustomPrompt}
                            onTemperatureChange={setTemperature}
                            onMaxTokensChange={setMaxTokens}
                            qualityThreshold={qualityThreshold}
                            autoPreprocess={autoPreprocess}
                            skipQuality={skipQuality}
                            onQualityThresholdChange={setQualityThreshold}
                            onAutoPreprocessChange={setAutoPreprocess}
                            onSkipQualityChange={setSkipQuality}
                            errors={validationErrors}
                            settings={settings?.defaults}
                        />
                    </div>
                </section>

                {/* Process Button */}
                {(fileId || !isAuthenticated) && (
                    <section>
                        <button
                            onClick={handleProcess}
                            disabled={
                                processing ||
                                !fileId ||
                                (requiresProvider && (!provider || !model)) ||
                                (!isTranscription && schemaMode === 'manual' && (!schemaDefinition || !isSchemaValid))
                            }
                            className="w-full px-6 py-3 font-medium rounded-md transition-colors bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                        >
                            {processing ? 'Processing...' : 'Process Document'}
                        </button>

                        {!isAuthenticated && (
                            <p className="mt-2 text-sm text-gray-600">
                                Guest processing is rate-limited and temporary. Sign in from the top-right menu if you want persistent account history.
                            </p>
                        )}

                        {error && (
                            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                                <p className="text-sm text-red-600">{error}</p>
                            </div>
                        )}
                    </section>
                )}

                {/* Results */}
                {currentJob && (
                    <section>
                        <h2 className="text-xl font-semibold mb-4">Results</h2>
                        <ResultsDisplay job={currentJob} processingMethod={extractionMethod} />
                    </section>
                )}
            </div>
        </div>
    );
}
