export interface SchemaField {
  id: string;
  name: string;
  type: 'string' | 'number' | 'boolean' | 'array';
  description: string;
}

export interface FieldError {
  name?: string;
  duplicate?: boolean;
}

export const MAX_FIELDS = 50;
export const FIELD_NAME_REGEX = /^[a-zA-Z_][a-zA-Z0-9_]*$/;

export function validateFieldName(name: string): string | null {
  if (!name.trim()) {
    return 'Field name is required';
  }
  if (!FIELD_NAME_REGEX.test(name)) {
    return 'Field name must start with a letter or underscore, and contain only letters, numbers, and underscores';
  }
  return null;
}

function findDuplicateNames(fields: SchemaField[]): Set<string> {
  const seen = new Set<string>();
  const duplicates = new Set<string>();

  fields.forEach((field) => {
    if (field.name && seen.has(field.name)) {
      duplicates.add(field.name);
    }
    seen.add(field.name);
  });

  return duplicates;
}

export function validateFields(fields: SchemaField[]): Record<string, FieldError> {
  const errors: Record<string, FieldError> = {};
  const duplicates = findDuplicateNames(fields);

  fields.forEach((field) => {
    const fieldError: FieldError = {};

    const nameError = validateFieldName(field.name);
    if (nameError) fieldError.name = nameError;

    if (field.name && duplicates.has(field.name)) {
      fieldError.duplicate = true;
    }

    if (Object.keys(fieldError).length > 0) {
      errors[field.id] = fieldError;
    }
  });

  return errors;
}
