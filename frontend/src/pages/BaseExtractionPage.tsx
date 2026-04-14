import { useState, useRef, useEffect } from 'react';
import { Job, getAuthToken, getJobStatus, suggestSchema, createSchema, SchemaSuggestion } from '@/lib/api';
import { JobStatusWebSocket } from '@/lib/websocket';
import FileUpload from '@/components/FileUpload';
import ModelSelector from '@/components/ModelSelector';
import SchemaEditor from '@/components/SchemaEditor';
import ResultsDisplay from '@/components/ResultsDisplay';
import ExtractionModeSelector, { ExtractionMethod } from '@/components/ExtractionModeSelector';
import AdvancedOptions from '@/components/AdvancedOptions';

export type { ExtractionMethod };

interface BaseExtractionPageProps {
    title: string;
    description: string;
    processFunction: (
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
    ) => Promise<{ job_id: number }>;
    processingMethod?: ExtractionMethod;
    showModeSelector?: boolean;
    isAuthenticated: boolean;
}

export default function BaseExtractionPage({
    title,
    description,
    processFunction,
    processingMethod = 'auto',
    showModeSelector = true,
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
    const [customPrompt, setCustomPrompt] = useState('');
    const [temperature, setTemperature] = useState(0.1);
    const [maxTokens, setMaxTokens] = useState(4096);
    // Quality gate state
    const [qualityThreshold, setQualityThreshold] = useState(40);
    const [autoPreprocess, setAutoPreprocess] = useState(true);
    const [skipQuality, setSkipQuality] = useState(false);
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

    // WebSocket connection for job status updates
    const wsConnection = useRef<JobStatusWebSocket | null>(null);
    const pollingInterval = useRef<number | null>(null);

    // Cleanup WebSocket on unmount
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
        setError(null);
    };

    const validateAdvancedOptions = (): boolean => {
        const errors: { prompt?: string; temperature?: string; maxTokens?: string } = {};

        if (customPrompt.length > 2000) {
            errors.prompt = 'Prompt must be 2000 characters or less';
        }

        if (temperature < 0 || temperature > 2) {
            errors.temperature = 'Temperature must be between 0 and 2';
        }

        if (maxTokens < 256 || maxTokens > 32768) {
            errors.maxTokens = 'Max tokens must be between 256 and 32768';
        }

        setValidationErrors(errors);
        return Object.keys(errors).length === 0;
    };

    const handleProcess = async () => {
        if (!fileId || !provider || !model || !schemaDefinition) {
            setError('Please complete all required fields');
            return;
        }

        if (!isSchemaValid) {
            setError('Please fix the schema definition before processing');
            return;
        }

        if (!validateAdvancedOptions()) {
            setError('Please fix validation errors');
            return;
        }

        setProcessing(true);
        setError(null);

        try {
            const response = await processFunction(
                fileId,
                provider,
                model,
                extractionMethod,
                schemaId || undefined,
                schemaId ? undefined : (schemaDefinition || undefined),
                customPrompt || undefined,
                temperature,
                maxTokens,
                skipQuality ? undefined : qualityThreshold,
                skipQuality ? false : autoPreprocess,
                skipQuality,
            );

            setCurrentJob({
                job_id: response.job_id,
                file_name: fileName || 'Unknown',
                file_type: fileType || 'unknown',
                status: 'pending',
                provider,
                model,
                schema_name: 'Custom',
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
            const suggestion = await suggestSchema([fileId], provider || undefined, model || undefined);
            setSchemaSuggestion(suggestion);
            setSchemaNameDraft(suggestion.draft_name || 'Suggested Schema');
            setSchemaId(null);
            setSchemaDefinition(suggestion.schema_definition);
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

    const connectWebSocketForJobStatus = (jobId: number, token: string) => {
        stopStatusUpdates();

        wsConnection.current = new JobStatusWebSocket();

        // Set up callbacks
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
            // Don't set processing to false - the job may still be running
            // User can check the history page
        });

        // Connect
        wsConnection.current.connect(jobId, token);
    };

    const connectJobStatusUpdates = (jobId: number) => {
        const token = getAuthToken();
        if (token) {
            connectWebSocketForJobStatus(jobId, token);
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
    };

    return (
        <div className="max-w-4xl mx-auto p-6">
            <div className="mb-6">
                <h1 className="text-3xl font-bold mb-2">{title}</h1>
                <p className="text-sm text-gray-600">{description}</p>
            </div>

            <div className="space-y-8">
                {/* File Upload */}
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
                    )}
                </section>

                {/* Extraction Mode Selector */}
                {showModeSelector && (
                    <section>
                        <ExtractionModeSelector
                            value={extractionMethod}
                            onChange={setExtractionMethod}
                            fileType={fileType || undefined}
                        />
                    </section>
                )}

                {/* Provider & Model Selection */}
                <section>
                    <h2 className={`text-xl font-semibold mb-4`}>
                        Step {showModeSelector ? '3' : '2'}: Select Model
                    </h2>
                    <ModelSelector
                        provider={provider}
                        model={model}
                        onProviderChange={setProvider}
                        onModelChange={setModel}
                    />
                </section>

                {/* Schema Definition */}
                <section>
                    <h2 className={`text-xl font-semibold mb-4`}>
                        Step {showModeSelector ? '4' : '3'}: Define Schema
                    </h2>
                    <div className="mb-4 rounded-lg border border-indigo-200 bg-indigo-50 p-4">
                        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                            <div>
                                <p className="text-sm font-medium text-indigo-900">Schema Learning</p>
                                <p className="text-sm text-indigo-800">
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
                        {schemaSuggestion && (
                            <div className="mt-4 space-y-3 border-t border-indigo-200 pt-4">
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
                    <SchemaEditor
                        schemaId={schemaId}
                        schemaDefinition={schemaDefinition}
                        onSchemaSelect={setSchemaId}
                        onDefinitionChange={setSchemaDefinition}
                        onValidityChange={setIsSchemaValid}
                    />
                </section>

                {/* Advanced Options */}
                <section>
                    <h2 className={`text-xl font-semibold mb-4`}>
                        Advanced Options
                    </h2>
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
                        />
                    </div>
                </section>

                {/* Process Button */}
                {(fileId || !isAuthenticated) && (
                    <section>
                        <button
                            onClick={handleProcess}
                            disabled={processing || !fileId || !provider || !model || !schemaDefinition || !isSchemaValid}
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
