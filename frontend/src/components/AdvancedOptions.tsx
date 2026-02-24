import React from 'react';

interface AdvancedOptionsProps {
  prompt: string;
  temperature: number;
  maxTokens: number;
  onPromptChange: (prompt: string) => void;
  onTemperatureChange: (temperature: number) => void;
  onMaxTokensChange: (maxTokens: number) => void;
  errors?: {
    prompt?: string;
    temperature?: string;
    maxTokens?: string;
  };
}

export default function AdvancedOptions({
  prompt,
  temperature,
  maxTokens,
  onPromptChange,
  onTemperatureChange,
  onMaxTokensChange,
  errors,
}: AdvancedOptionsProps) {
  const handleTemperatureChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(e.target.value);
    if (!isNaN(value) && value >= 0 && value <= 2) {
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
    <div className="space-y-6">
      {/* Custom Prompt */}
      <div>
        <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
          Custom Prompt <span className="text-gray-400 font-normal">(Optional)</span>
        </label>
        <textarea
          id="prompt"
          value={prompt}
          onChange={(e) => onPromptChange(e.target.value)}
          maxLength={2000}
          rows={4}
          className={`
            w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500
            ${errors?.prompt ? 'border-red-300' : 'border-gray-300'}
          `}
          placeholder="Enter custom instructions for the AI model to guide extraction behavior..."
        />
        <div className="mt-1 flex justify-between items-center">
          <p className="text-xs text-gray-500">
            Provide specific instructions to improve extraction quality
          </p>
          <span className="text-xs text-gray-400">{prompt.length}/2000</span>
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
          min="0"
          max="1"
          step="0.1"
          value={temperature}
          onChange={handleTemperatureChange}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
        />
        <div className="mt-1 flex justify-between text-xs text-gray-500">
          <span>More focused (0.0)</span>
          <span>More creative (1.0)</span>
        </div>
        {errors?.temperature && (
          <p className="mt-1 text-sm text-red-600">{errors.temperature}</p>
        )}
      </div>

      {/* Max Tokens */}
      <div>
        <label htmlFor="maxTokens" className="block text-sm font-medium text-gray-700 mb-2">
          Max Tokens <span className="text-gray-400 font-normal">(256 - 32768)</span>
        </label>
        <input
          type="number"
          id="maxTokens"
          value={maxTokens}
          onChange={handleMaxTokensChange}
          min="256"
          max="32768"
          step="1"
          className={`
            w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500
            ${errors?.maxTokens ? 'border-red-300' : 'border-gray-300'}
          `}
          placeholder="4096"
        />
        <p className="mt-1 text-xs text-gray-500">
          Maximum number of tokens the model can generate. Higher values allow longer responses but may be slower.
        </p>
        {errors?.maxTokens && (
          <p className="mt-1 text-sm text-red-600">{errors.maxTokens}</p>
        )}
      </div>
    </div>
  );
}
