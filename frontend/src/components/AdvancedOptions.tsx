import React, { useState } from 'react';

interface AdvancedOptionsProps {
  prompt: string;
  temperature: number;
  maxTokens: number;
  onPromptChange: (prompt: string) => void;
  onTemperatureChange: (temperature: number) => void;
  onMaxTokensChange: (maxTokens: number) => void;
  qualityThreshold: number;
  autoPreprocess: boolean;
  skipQuality: boolean;
  onQualityThresholdChange: (threshold: number) => void;
  onAutoPreprocessChange: (enabled: boolean) => void;
  onSkipQualityChange: (skip: boolean) => void;
  errors?: {
    prompt?: string;
    temperature?: string;
    maxTokens?: string;
  };
  settings?: {
    temperature?: { min?: number; max?: number; step?: number };
    max_tokens?: { min?: number; max?: number; step?: number };
    quality_threshold?: { min?: number; max?: number; step?: number };
    prompt_max_length?: number;
  };
}

export default function AdvancedOptions({
  prompt,
  temperature,
  maxTokens,
  onPromptChange,
  onTemperatureChange,
  onMaxTokensChange,
  qualityThreshold,
  autoPreprocess,
  skipQuality,
  onQualityThresholdChange,
  onAutoPreprocessChange,
  onSkipQualityChange,
  errors,
  settings,
}: AdvancedOptionsProps) {
  const [expanded, setExpanded] = useState(false);

  const tempMin = settings?.temperature?.min ?? 0;
  const tempMax = settings?.temperature?.max ?? 1;
  const tempStep = settings?.temperature?.step ?? 0.1;
  const tokensMin = settings?.max_tokens?.min ?? 256;
  const tokensMax = settings?.max_tokens?.max ?? 128000;
  const qualityMin = settings?.quality_threshold?.min ?? 0;
  const qualityMax = settings?.quality_threshold?.max ?? 80;
  const qualityStep = settings?.quality_threshold?.step ?? 5;
  const promptMaxLen = settings?.prompt_max_length ?? 10000;

  const handleTemperatureChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(e.target.value);
    if (!isNaN(value) && value >= tempMin && value <= tempMax) {
      onTemperatureChange(value);
    }
  };

  const handleMaxTokensChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value >= 1) {
      onMaxTokensChange(value);
    }
  };

  const temperaturePresets = [
    { label: 'Focused', value: 0.0, description: 'More deterministic' },
    { label: 'Balanced', value: 0.1, description: 'Default' },
    { label: 'Creative', value: 0.7, description: 'More varied' },
  ];

  return (
    <div className="space-y-0">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
      >
        <svg
          className={`w-4 h-4 transition-transform ${expanded ? 'rotate-90' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        Advanced Options
        <span className="text-xs text-gray-400 font-normal">(click to expand)</span>
      </button>
      {expanded && (
    <div className="space-y-6 mt-4">
      {/* Custom Prompt */}
      <div>
        <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
          Custom Prompt <span className="text-gray-400 font-normal">(Overrides Default)</span>
        </label>
        <textarea
          id="prompt"
          value={prompt}
          onChange={(e) => onPromptChange(e.target.value)}
          maxLength={promptMaxLen}
          rows={4}
          className={`
            w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500
            ${errors?.prompt ? 'border-red-300' : 'border-gray-300'}
          `}
          placeholder="Your instructions replace the default extraction prompt..."
        />
        <div className="mt-1 flex justify-between items-center">
          <p className="text-xs text-gray-500">
            Replaces the default extraction prompt with your custom instructions
          </p>
          <span className="text-xs text-gray-400">{prompt.length}/{promptMaxLen}</span>
        </div>
        {errors?.prompt && (
          <p className="mt-1 text-sm text-red-600">{errors.prompt}</p>
        )}
      </div>

      {/* Temperature */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Temperature: {temperature.toFixed(1)}
        </label>
        <div className="mb-3 flex flex-wrap gap-2">
          {temperaturePresets.map((preset) => (
            <button
              key={preset.label}
              onClick={() => onTemperatureChange(preset.value)}
              className={`
                px-3 py-1.5 text-xs font-medium rounded-full border transition-colors
                ${temperature === preset.value
                  ? 'bg-blue-100 border-blue-300 text-blue-700'
                  : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
                }
              `}
            >
              {preset.label} ({preset.value})
            </button>
          ))}
        </div>
        <input
          type="range"
          min={tempMin}
          max={tempMax}
          step={tempStep}
          value={temperature}
          onChange={handleTemperatureChange}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
        />
        <div className="mt-1 flex justify-between text-xs text-gray-500">
          <span>More focused ({tempMin})</span>
          <span>More creative ({tempMax})</span>
        </div>
        {errors?.temperature && (
          <p className="mt-1 text-sm text-red-600">{errors.temperature}</p>
        )}
      </div>

      {/* Max Tokens */}
      <div>
        <label htmlFor="maxTokens" className="block text-sm font-medium text-gray-700 mb-2">
          Max Tokens <span className="text-gray-400 font-normal">({tokensMin} - {tokensMax})</span>
        </label>
        <input
          type="number"
          id="maxTokens"
          value={maxTokens}
          onChange={handleMaxTokensChange}
          min={tokensMin}
          max={tokensMax}
          step="1"
          className={`
            w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500
            ${errors?.maxTokens ? 'border-red-300' : 'border-gray-300'}
          `}
          placeholder="8192"
        />
        <p className="mt-1 text-xs text-gray-500">
          Maximum number of tokens the model can generate. Higher values allow longer responses but may be slower.
        </p>
        {errors?.maxTokens && (
          <p className="mt-1 text-sm text-red-600">{errors.maxTokens}</p>
        )}
      </div>

      {/* Quality Gate */}
      <div className="pt-4 border-t border-gray-200">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Quality Gate</h4>
        <div className="space-y-4">
          {/* Skip quality gate */}
          <div className="flex items-center justify-between">
            <div>
              <label htmlFor="skipQuality" className="text-sm font-medium text-gray-700">
                Skip Quality Check
              </label>
              <p className="text-xs text-gray-500">Bypass quality assessment to save time (not recommended)</p>
            </div>
            <button
              id="skipQuality"
              type="button"
              role="switch"
              aria-checked={skipQuality}
              onClick={() => onSkipQualityChange(!skipQuality)}
              className={`
                relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                ${skipQuality ? 'bg-red-500' : 'bg-gray-300'}
              `}
            >
              <span
                className={`
                  inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                  ${skipQuality ? 'translate-x-6' : 'translate-x-1'}
                `}
              />
            </button>
          </div>

          {!skipQuality && (
            <>
              {/* Auto-preprocess */}
              <div className="flex items-center justify-between">
                <div>
                  <label htmlFor="autoPreprocess" className="text-sm font-medium text-gray-700">
                    Auto-Preprocess
                  </label>
                  <p className="text-xs text-gray-500">Automatically fix issues (deskew, denoise, contrast)</p>
                </div>
                <button
                  id="autoPreprocess"
                  type="button"
                  role="switch"
                  aria-checked={autoPreprocess}
                  onClick={() => onAutoPreprocessChange(!autoPreprocess)}
                  className={`
                    relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                    ${autoPreprocess ? 'bg-blue-500' : 'bg-gray-300'}
                  `}
                >
                  <span
                    className={`
                      inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                      ${autoPreprocess ? 'translate-x-6' : 'translate-x-1'}
                    `}
                  />
                </button>
              </div>

              {/* Quality threshold */}
              <div>
                <label htmlFor="qualityThreshold" className="block text-sm font-medium text-gray-700 mb-1">
                  Minimum Quality Score: {qualityThreshold.toFixed(0)}/100
                </label>
                <input
                  type="range"
                  id="qualityThreshold"
                  min={qualityMin}
                  max={qualityMax}
                  step={qualityStep}
                  value={qualityThreshold}
                  onChange={(e) => onQualityThresholdChange(parseFloat(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
                <div className="mt-1 flex justify-between text-xs text-gray-500">
                  <span>Lenient ({qualityMin})</span>
                  <span>Strict ({qualityMax})</span>
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  Images scoring below this threshold will be rejected (after auto-preprocessing if enabled)
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
      )}
    </div>
  );
}
