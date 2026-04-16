import { useState, useRef } from 'react';
import { uploadFile } from '../lib/api';

interface FileUploadProps {
  onUpload: (fileId: string, fileName: string, fileType?: string) => void;
  disabled?: boolean;
  disabledMessage?: string;
}

export default function FileUpload({
  onUpload,
  disabled = false,
  disabledMessage = 'Login required to upload files.',
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const acceptedTypes = [
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
    'application/vnd.openxmlformats-officedocument.presentationml.presentation', // .pptx
    'text/plain',
    'text/markdown',
    'text/html',
  ];
  const maxSize = 10 * 1024 * 1024; // 10MB

  const validateFile = (file: File): string | null => {
    if (!acceptedTypes.includes(file.type)) {
      return 'Invalid file type. Please upload an image (JPEG, PNG, GIF, WebP), PDF, DOCX, PPTX, TXT, MD, or HTML file.';
    }
    if (file.size > maxSize) {
      return 'File size exceeds 10MB limit.';
    }
    return null;
  };

  const handleFile = async (file: File) => {
    if (disabled) return;

    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    setError(null);
    setIsUploading(true);

    try {
      const result = await uploadFile(file);
      onUpload(result.file_id, file.name, file.type);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (disabled) return;
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled) return;
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  return (
    <div
      className={'border-2 border-dashed rounded-lg p-8 text-center transition-colors ' +
        (disabled
          ? 'border-gray-200 bg-gray-100 opacity-80'
          : isDragging
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-300 hover:border-gray-400'
        )}
      onDrop={disabled ? undefined : handleDrop}
      onDragOver={disabled ? undefined : handleDragOver}
      onDragLeave={disabled ? undefined : handleDragLeave}
    >
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept={acceptedTypes.join(',')}
        onChange={handleInputChange}
      />

      <div className="space-y-4">
        <div className="flex justify-center">
          <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </div>

        <div>
          <p className="text-lg font-medium text-gray-700">
            {disabled ? 'Upload locked' : (isDragging ? 'Drop your file here' : 'Upload a document')}
          </p>
          <p className="text-sm text-gray-500 mt-1">
            {disabled ? disabledMessage : 'Drag and drop, or click to browse'}
          </p>
          <p className="text-xs text-gray-400 mt-2">
            Supports: JPEG, PNG, GIF, WebP, PDF, DOCX, PPTX, TXT, MD, HTML (max 10MB)
          </p>
        </div>

        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || isUploading}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {disabled ? 'Login Required' : (isUploading ? 'Uploading...' : 'Select File')}
        </button>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}
