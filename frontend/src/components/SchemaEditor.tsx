import { useState, useEffect } from 'react';
import { getTemplates, Schema } from '../lib/api';

interface SchemaEditorProps {
  schemaId: number | null;
  schemaDefinition: Record<string, any> | null;
  onSchemaSelect: (schemaId: number) => void;
  onDefinitionChange: (definition: Record<string, any>) => void;
}

export default function SchemaEditor({
  schemaId,
  schemaDefinition,
  onSchemaSelect,
  onDefinitionChange,
}: SchemaEditorProps) {
  const [templates, setTemplates] = useState<Schema[]>([]);
  const [loading, setLoading] = useState(true);
  const [jsonInput, setJsonInput] = useState('');
  const [jsonError, setJsonError] = useState<string | null>(null);

  useEffect(() => {
    loadTemplates();
  }, []);

  useEffect(() => {
    if (schemaDefinition) {
      setJsonInput(JSON.stringify(schemaDefinition, null, 2));
      setJsonError(null);
    }
  }, [schemaDefinition]);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const data = await getTemplates();
      setTemplates(data);

      // Auto-select Generic template if nothing selected
      if (!schemaId && !schemaDefinition) {
        const genericTemplate = data.find(t => t.name === 'Generic');
        if (genericTemplate) {
          onSchemaSelect(genericTemplate.id!);
          onDefinitionChange(genericTemplate.definition);
        }
      }
    } catch (err) {
      console.error('Failed to load templates:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleJsonChange = (value: string) => {
    setJsonInput(value);

    try {
      const parsed = JSON.parse(value);
      setJsonError(null);
      onDefinitionChange(parsed);
    } catch (err) {
      setJsonError(err instanceof Error ? err.message : 'Invalid JSON');
    }
  };

  const handleTemplateSelect = (template: Schema) => {
    onSchemaSelect(template.id!);
    onDefinitionChange(template.definition);
  };

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-32 bg-gray-200 rounded"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Schema Template
        </label>
        <div className="grid grid-cols-2 gap-2">
          {templates.map((template) => (
            <button
              key={template.name}
              type="button"
              onClick={() => handleTemplateSelect(template)}
              className={`px-4 py-2 text-left rounded-md border transition-colors ${
                schemaDefinition && template.name === schemaDefinition?.type?.split('-')[0]
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <div className="font-medium">{template.name}</div>
              <div className="text-xs text-gray-500 mt-1">
                Built-in template
              </div>
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Custom Schema Definition (JSON)
        </label>
        <textarea
          value={jsonInput}
          onChange={(e) => handleJsonChange(e.target.value)}
          rows={12}
          className={`w-full px-3 py-2 font-mono text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            jsonError ? 'border-red-300' : 'border-gray-300'
          }`}
          placeholder='{"type": "object", "properties": {...}}'
        />
        {jsonError && (
          <p className="text-sm text-red-600 mt-1">{jsonError}</p>
        )}
        <p className="text-xs text-gray-500 mt-2">
          Use JSON Schema format to define the structure of extracted data
        </p>
      </div>
    </div>
  );
}
