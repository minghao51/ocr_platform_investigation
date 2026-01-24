import { useState } from 'react';
import { Job, getJobStatus as getVisionJobStatus, pollJobStatus as getTextJobStatus } from '@/lib/api';
import FileUpload from '@/components/FileUpload';
import ModelSelector from '@/components/ModelSelector';
import SchemaEditor from '@/components/SchemaEditor';
import ResultsDisplay from '@/components/ResultsDisplay';

interface BaseExtractionPageProps {
    title: string;
    description: string;
    processFunction: (
        fileId: string,
        provider: string,
        model: string,
        schemaId?: number,
        schemaDefinition?: Record<string, any>
    ) => Promise<{ job_id: number }>;
    processingMethod: 'vision' | 'text' | 'auto';  // NEW: Added 'auto'
}

export default function BaseExtractionPage({
    title,
    description,
    processFunction,
    processingMethod,
}: BaseExtractionPageProps) {
    const [fileId, setFileId] = useState<string | null>(null);
    const [fileName, setFileName] = useState<string | null>(null);
    const [provider, setProvider] = useState(processingMethod === 'text' ? 'gemini' : '');
    const [model, setModel] = useState(processingMethod === 'text' ? 'gemini-2.5-flash' : '');
    const [schemaId, setSchemaId] = useState<number | null>(null);
    const [schemaDefinition, setSchemaDefinition] = useState<Record<string, any> | null>(null);
    const [currentJob, setCurrentJob] = useState<Job | null>(null);
    const [processing, setProcessing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleFileUpload = (uploadedFileId: string, uploadedFileName: string) => {
        setFileId(uploadedFileId);
        setFileName(uploadedFileName);
        setError(null);
    };

    const handleProcess = async () => {
        if (!fileId || !provider || !model || !schemaDefinition) {
            setError('Please complete all fields');
            return;
        }

        setProcessing(true);
        setError(null);

        try {
            const response = await processFunction(
                fileId,
                provider,
                model,
                schemaId || undefined,
                schemaId ? undefined : (schemaDefinition || undefined)
            );

            setCurrentJob({
                job_id: response.job_id,
                file_name: fileName || 'Unknown',
                file_type: processingMethod === 'text' ? 'pdf' : 'unknown',
                status: 'pending',
                provider,
                model,
                schema_name: 'Custom',
                processing_method: processingMethod === 'auto' ? undefined : processingMethod,
            });

            // Poll for status
            pollJobStatusInterval(response.job_id);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Processing failed');
            setProcessing(false);
        }
    };

    const pollJobStatusInterval = async (jobId: number) => {
        let errorCount = 0;
        const maxErrors = 3;

        const pollInterval = setInterval(async () => {
            try {
                // Choose correct polling function based on method
                // 'auto' uses vision endpoint since all jobs go through /api/process/
                const job = processingMethod === 'text'
                    ? await getTextJobStatus(jobId)
                    : await getVisionJobStatus(jobId);

                setCurrentJob(job);
                errorCount = 0; // Reset error count on successful fetch

                if (job.status === 'success' || job.status === 'error') {
                    clearInterval(pollInterval);
                    setProcessing(false);
                }
            } catch (err) {
                errorCount++;
                console.error('Error polling job status:', err);

                // Only stop polling after multiple consecutive errors
                if (errorCount >= maxErrors) {
                    clearInterval(pollInterval);
                    setError('Failed to get job status. Please check if the job completed in the history page.');
                    setProcessing(false);
                }
            }
        }, 2000);
    };

    const handleReset = () => {
        setFileId(null);
        setFileName(null);
        setCurrentJob(null);
        setError(null);
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

                {/* Provider & Model Selection */}
                <section>
                    <h2 className="text-xl font-semibold mb-4">Step 2: Select Model</h2>
                    <ModelSelector
                        provider={provider}
                        model={model}
                        onProviderChange={setProvider}
                        onModelChange={setModel}
                    />
                </section>

                {/* Schema Definition */}
                <section>
                    <h2 className="text-xl font-semibold mb-4">Step 3: Define Schema</h2>
                    <SchemaEditor
                        schemaId={schemaId}
                        schemaDefinition={schemaDefinition}
                        onSchemaSelect={setSchemaId}
                        onDefinitionChange={setSchemaDefinition}
                    />
                </section>

                {/* Process Button */}
                {fileId && (
                    <section>
                        <button
                            onClick={handleProcess}
                            disabled={processing || !provider || !model || !schemaDefinition}
                            className="w-full px-6 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                        >
                            {processing ? 'Processing...' : `Process Document (${processingMethod === 'text' ? 'Text' : 'Vision'} Extraction)`}
                        </button>

                        {error && (
                            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                                <p className="text-sm text-red-600">{error}</p>
                                {processingMethod === 'text' && error.includes('image-based') && (
                                    <button
                                        onClick={() => window.location.href = '/'}
                                        className="mt-2 text-blue-600 hover:underline text-sm"
                                    >
                                        Switch to Vision Extraction
                                    </button>
                                )}
                            </div>
                        )}
                    </section>
                )}

                {/* Results */}
                {currentJob && (
                    <section>
                        <h2 className="text-xl font-semibold mb-4">Results</h2>
                        <ResultsDisplay job={currentJob} processingMethod={processingMethod} />
                    </section>
                )}
            </div>
        </div>
    );
}
