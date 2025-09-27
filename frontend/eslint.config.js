import js from '@eslint/js';
import tseslint from 'typescript-eslint';

/** @type {import('eslint').Linter.FlatConfig[]} */
export default [
  {
    ...js.configs.recommended,
    languageOptions: {
      ...js.configs.recommended.languageOptions,
      globals: {
        ...js.configs.recommended.languageOptions?.globals,
        document: 'readonly',
        window: 'readonly',
        localStorage: 'readonly',
        navigator: 'readonly',
        fetch: 'readonly',
        FormData: 'readonly',
        File: 'readonly',
        Response: 'readonly',
        setTimeout: 'readonly',
      },
    },
  },
  {
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
      },
    },
    plugins: {
      '@typescript-eslint': tseslint.plugin,
    },
    rules: {
      ...tseslint.configs.recommended.rules,
      'no-undef': 'off',
      'no-unused-vars': 'off',
    },
  },
];
