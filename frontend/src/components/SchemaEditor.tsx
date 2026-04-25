import { useState, useEffect } from 'react';
import { getTemplates, Schema } from '../lib/api';
import Editor from 'react-simple-code-editor';
import { highlight, languages } from 'prismjs';
import 'prismjs/components/prism-json';
import 'prismjs/themes/prism.css';
import {
  type FieldError,
  type SchemaField,
  MAX_FIELDS,
  validateFields,
} from './schemaEditorValidation';

interface SchemaEditorProps {
  schemaId: number | null;
  schemaDefinition: Record<string, unknown> | null;
  onSchemaSelect: (schemaId: number | null) => void;
  onDefinitionChange: (definition: Record<string, unknown>) => void;
  onValidityChange?: (isValid: boolean) => void;
  restrictedMode?: boolean;
}

export default function SchemaEditor({
  schemaId,
  schemaDefinition,
  onSchemaSelect,
  onDefinitionChange,
  onValidityChange,
  restrictedMode = false,
}: SchemaEditorProps) {
  const [templates, setTemplates] = useState<Schema[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTemplateName, setSelectedTemplateName] = useState<string | null>(null);

  const [mode, setMode] = useState<'visual' | 'json'>('visual');
  const [fields, setFields] = useState<SchemaField[]>([]);
  const [fieldErrors, setFieldErrors] = useState<Record<string, FieldError>>({});

  const [jsonInput, setJsonInput] = useState('');
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [jsonSchemaError, setJsonSchemaError] = useState<string | null>(null);

  useEffect(() => {
    loadTemplates();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Sync incoming schemaDefinition to both inputs
  useEffect(() => {
    if (schemaDefinition) {
      const jsonStr = JSON.stringify(schemaDefinition, null, 2);
      setJsonInput(jsonStr);
      setJsonError(null);
      setJsonSchemaError(null);

      // Try to parse into visual fields
      try {
        const visualFields = parseSchemaToFields(schemaDefinition);
        const nextErrors = validateFields(visualFields);
        setFields(visualFields);
        setFieldErrors(nextErrors);
        onValidityChange?.(Object.keys(nextErrors).length === 0);
      } catch (e) {
        console.log('Schema too complex for visual builder', e);
      }
    } else {
      setFields([]);
      setFieldErrors({});
      setJsonInput('');
      setJsonError(null);
      setJsonSchemaError(null);
      onValidityChange?.(false);
    }
  }, [onValidityChange, schemaDefinition]);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const data = await getTemplates();
      setTemplates(data);

      // Auto-select Generic template if nothing selected
      if (!schemaId && !schemaDefinition) {
        const genericTemplate = data.find(t => t.name === 'Generic');
        if (genericTemplate) {
          setSelectedTemplateName(genericTemplate.name);
          onSchemaSelect(null);
          onDefinitionChange(genericTemplate.definition);
        }
      }
    } catch (err) {
      console.error('Failed to load templates:', err);
    } finally {
      setLoading(false);
    }
  };

  // --- Visual Builder Logic ---

  const parseSchemaToFields = (schema: Record<string, unknown>): SchemaField[] => {
    if (schema.type !== 'object' || !schema.properties) {
      return [];
    }

    const props = schema.properties as Record<string, unknown>;
    return Object.entries(props).map(([key, value]: [string, unknown]) => ({
      id: key, // Use key as ID for stability
      name: key,
      type: (value as { type?: string }).type === 'array' ? 'array' :
        (value as { type?: string }).type === 'number' || (value as { type?: string }).type === 'integer' ? 'number' :
          (value as { type?: string }).type === 'boolean' ? 'boolean' : 'string',
      description: (value as { description?: string }).description || '',
    }));
  };

  const updateSchemaFromFields = (newFields: SchemaField[]) => {
    const properties: Record<string, unknown> = {};

    newFields.forEach(field => {
      if (!field.name) return;

      let fieldDef: Record<string, unknown> = {
        type: field.type,
        description: field.description
      };

      if (field.type === 'array') {
        fieldDef = {
          type: 'array',
          description: field.description,
          items: {
            type: 'string'
          }
        };
      }

      properties[field.name] = fieldDef;
    });

    const newSchema = {
      type: 'object',
      properties,
      required: Object.keys(properties)
    };

    onDefinitionChange(newSchema);
  };

  const validateJsonSchema = (parsed: Record<string, unknown>): string | null => {
    if (parsed.type !== 'object') {
      return 'Root schema must have type: "object"';
    }
    if (!parsed.properties || typeof parsed.properties !== 'object') {
      return 'Schema must have a "properties" object';
    }
    return null;
  };

  const handleAddField = () => {
    if (fields.length >= MAX_FIELDS) {
      return;
    }
    const newField: SchemaField = {
      id: Date.now().toString(),
      name: '',
      type: 'string',
      description: ''
    };
    const newFields = [...fields, newField];
    const nextErrors = validateFields(newFields);
    setFields(newFields);
    setFieldErrors(nextErrors);
    onValidityChange?.(false);
  };

  const handleFieldChange = (id: string, key: keyof SchemaField, value: string) => {
    const newFields = fields.map(f => {
      if (f.id === id) {
        return { ...f, [key]: value };
      }
      return f;
    });
    const nextErrors = validateFields(newFields);
    setFields(newFields);
    setFieldErrors(nextErrors);
    onValidityChange?.(Object.keys(nextErrors).length === 0);

    // Keep the editor interactive, but only publish valid schemas.
    if (Object.keys(nextErrors).length === 0) {
      updateSchemaFromFields(newFields);
    }
  };

  const handleRemoveField = (id: string) => {
    const newFields = fields.filter(f => f.id !== id);
    const nextErrors = validateFields(newFields);
    setFields(newFields);
    setFieldErrors(nextErrors);
    onValidityChange?.(Object.keys(nextErrors).length === 0);
    if (Object.keys(nextErrors).length === 0) {
      updateSchemaFromFields(newFields);
    }
  };

  // --- JSON Editor Logic ---

  const handleJsonChange = (value: string) => {
    setJsonInput(value);

    try {
      const parsed = JSON.parse(value);
      setJsonError(null);
      
      const schemaError = validateJsonSchema(parsed);
      if (schemaError) {
        setJsonSchemaError(schemaError);
        onValidityChange?.(false);
        return;
      }
      setJsonSchemaError(null);
      
      const nextFields = parseSchemaToFields(parsed);
      const nextErrors = validateFields(nextFields);
      onDefinitionChange(parsed);
      setFields(nextFields);
      setFieldErrors(nextErrors);
      onValidityChange?.(Object.keys(nextErrors).length === 0);
    } catch (err) {
      setJsonError(err instanceof Error ? err.message : 'Invalid JSON');
      onValidityChange?.(false);
    }
  };

  const handleTemplateSelect = (template: Schema) => {
    setMode('visual');
    setSelectedTemplateName(template.name);
    onSchemaSelect(null);
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
    <div className="space-y-6">
      {/* Template Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Schema Template
        </label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {templates.map((template) => (
            <button
              key={template.name}
              type="button"
              onClick={() => handleTemplateSelect(template)}
              className={`px-3 py-2 text-left rounded-md border transition-colors ${selectedTemplateName === template.name
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-300 hover:border-gray-400'
                }`}
            >
              <div className="font-medium text-sm">{template.name}</div>
              <div className="text-xs text-gray-500">Built-in</div>
            </button>
          ))}
        </div>
      </div>

      {/* Editor Toggles */}
      <div className="border rounded-md overflow-hidden bg-white">
        <div className="flex border-b bg-gray-50">
          <button
            className={`flex-1 py-2 text-sm font-medium border-r ${mode === 'visual' ? 'bg-white text-blue-600' : 'text-gray-500 hover:text-gray-700'
              }`}
            onClick={() => setMode('visual')}
          >
            Visual Builder
          </button>
          {!restrictedMode && (
            <button
              className={`flex-1 py-2 text-sm font-medium ${mode === 'json' ? 'bg-white text-blue-600' : 'text-gray-500 hover:text-gray-700'
                }`}
              onClick={() => setMode('json')}
            >
              JSON Code
            </button>
          )}
        </div>

        <div className="p-4">
          {mode === 'visual' || restrictedMode ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-medium text-gray-700">Fields to Extract</h3>
              </div>

              {Object.keys(fieldErrors).length > 0 && (
                <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                  Fix the highlighted field errors before the schema definition is updated.
                </div>
              )}

              {fields.length === 0 ? (
                <div className="text-center py-8 bg-gray-50 rounded-md border border-dashed border-gray-300">
                  <p className="text-sm text-gray-500 mb-2">No fields defined yet</p>
                  <button
                    onClick={handleAddField}
                    className="text-sm text-blue-600 font-medium hover:underline"
                  >
                    + Add your first field
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {fields.map((field) => {
                    const error = fieldErrors[field.id];
                    const hasError = Boolean(error && (error.name || error.duplicate));
                    return (
                    <div key={field.id} className={`flex gap-2 items-start bg-gray-50 p-3 rounded-md border ${hasError ? 'border-red-300' : 'border-gray-200'}`}>
                      <div className="flex-1 space-y-2">
                        <div className="flex gap-2">
                          <div className="w-1/3">
                            <label className="text-xs text-gray-500 block mb-1">Field Name</label>
                            <input
                              type="text"
                              value={field.name}
                              onChange={(e) => handleFieldChange(field.id, 'name', e.target.value)}
                              placeholder="e.g. invoice_total"
                              className={`w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 ${error?.name ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}`}
                            />
                            {error?.name && (
                              <p className="text-xs text-red-500 mt-1">{error.name}</p>
                            )}
                            {error?.duplicate && (
                              <p className="text-xs text-red-500 mt-1">Duplicate field name</p>
                            )}
                          </div>
                          <div className="w-1/3">
                            <label className="text-xs text-gray-500 block mb-1">Type</label>
                            <select
                              value={field.type}
                              onChange={(e) => handleFieldChange(field.id, 'type', e.target.value as SchemaField['type'])}
                              className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                            >
                              <option value="string">Text</option>
                              <option value="number">Number</option>
                              <option value="boolean">Boolean</option>
                              <option value="array">List of Text</option>
                            </select>
                          </div>
                          <div className="w-1/3">
                            <div className="h-[21px] mb-1"></div>
                          </div>
                        </div>
                        <div>
                          <label className="text-xs text-gray-500 block mb-1">Description (for AI)</label>
                          <input
                            type="text"
                            value={field.description}
                            onChange={(e) => handleFieldChange(field.id, 'description', e.target.value)}
                            placeholder="Describe what this field is..."
                            className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                          />
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemoveField(field.id)}
                        className="mt-6 text-gray-400 hover:text-red-500 p-1"
                        title="Remove field"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  )})}

                  <button
                    onClick={handleAddField}
                    disabled={fields.length >= MAX_FIELDS}
                    className={`w-full py-2 border-2 border-dashed rounded-md text-sm transition-colors ${
                      fields.length >= MAX_FIELDS
                        ? 'border-gray-200 text-gray-400 cursor-not-allowed'
                        : 'border-gray-300 text-gray-500 hover:border-blue-400 hover:text-blue-600'
                    }`}
                  >
                    {fields.length >= MAX_FIELDS 
                      ? `Maximum ${MAX_FIELDS} fields reached` 
                      : '+ Add Field'}
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  JSON Definition
                </label>
                <span className="text-xs text-gray-500">
                  Reflects the Visual Builder changes
                </span>
              </div>
              <div className={`w-full border rounded-md overflow-hidden ${jsonError ? 'border-red-300' : 'border-gray-300'
                } focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500`}>
                <Editor
                  value={jsonInput}
                  onValueChange={handleJsonChange}
                  highlight={code => highlight(code, languages.json, 'json')}
                  padding={12}
                  style={{
                    fontFamily: '"Fira code", "Fira Mono", monospace',
                    fontSize: 14,
                    minHeight: '300px',
                    backgroundColor: '#fff',
                  }}
                  textareaClassName="focus:outline-none"
                />
              </div>
              {jsonError && (
                <p className="text-sm text-red-600 mt-1">{jsonError}</p>
              )}
              {jsonSchemaError && !jsonError && (
                <p className="text-sm text-amber-600 mt-1">{jsonSchemaError}</p>
              )}
              <p className="text-xs text-gray-500 mt-2">
                Use JSON Schema format to define the structure.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
