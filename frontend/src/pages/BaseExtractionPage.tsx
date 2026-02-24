import { useState, useRef, useEffect } from 'react';
import { Job, getAuthToken } from '@/lib/api';
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
        schemaDefinition?: Record<string, any>,
        prompt?: string,
        temperature?: number,
        maxTokens?: number
    ) => Promise<{ job_id: number }>;
    processingMethod?: ExtractionMethod;
    showModeSelector?: boolean;
}

export default function BaseExtractionPage({
    title,
    description,
    processFunction,
    processingMethod = 'auto',
    showModeSelector = true,
}: BaseExtractionPageProps) {
    const [fileId, setFileId] = useState<string | null>(null);
    const [fileName, setFileName] = useState<string | null>(null);
    const [fileType, setFileType] = useState<string | null>(null);
    const [extractionMethod, setExtractionMethod] = useState<ExtractionMethod>(processingMethod);
    const [provider, setProvider] = useState('');
    const [model, setModel] = useState('');
    const [schemaId, setSchemaId] = useState<number | null>(null);
    const [schemaDefinition, setSchemaDefinition] = useState<Record<string, any> | null>(null);
    const [customPrompt, setCustomPrompt] = useState('');
    const [temperature, setTemperature] = useState(0.1);
    const [maxTokens, setMaxTokens] = useState(4096);
    const [currentJob, setCurrentJob] = useState<Job | null>(null);
    const [processing, setProcessing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [validationErrors, setValidationErrors] = useState<{
        prompt?: string;
        temperature?: string;
        maxTokens?: string;
    }>({});

    // WebSocket connection for job status updates
    const wsConnection = useRef<JobStatusWebSocket | null>(null);

    // Cleanup WebSocket on unmount
    useEffect(() => {
        return () => {
            wsConnection.current?.disconnect();
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
                maxTokens
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

            // Connect to WebSocket for real-time status updates
            connectWebSocketForJobStatus(response.job_id);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Processing failed');
            setProcessing(false);
        }
    };

    const connectWebSocketForJobStatus = (jobId: number) => {
        const token = getAuthToken();
        if (!token) {
            setError('Authentication required. Please log in.');
            setProcessing(false);
            return;
        }

        // Disconnect any existing connection
        if (wsConnection.current) {
            wsConnection.current.disconnect();
        }

        // Create new WebSocket connection
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

    const handleReset = () => {
        // Disconnect WebSocket
        wsConnection.current?.disconnect();
        wsConnection.current = null;

        setFileId(null);
        setFileName(null);
        setFileType(null);
        setCurrentJob(null);
        setError(null);
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
                        <FileUpload onUpload={handleFileUpload} />
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
                    <SchemaEditor
                        schemaId={schemaId}
                        schemaDefinition={schemaDefinition}
                        onSchemaSelect={setSchemaId}
                        onDefinitionChange={setSchemaDefinition}
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
                            errors={validationErrors}
                        />
                    </div>
                </section>

                {/* Process Button */}
                {fileId && (
                    <section>
                        <button
                            onClick={handleProcess}
                            disabled={processing || !provider || !model || !schemaDefinition}
                            className="w-full px-6 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                        >
                            {processing ? 'Processing...' : 'Process Document'}
                        </button>

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
