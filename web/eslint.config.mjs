import js from '@eslint/js';
import ts from 'typescript-eslint';
import globals from 'globals';
export default [
  { ignores: ['public/**', 'node_modules/**', 'src/reactbits/**'] },
  js.configs.recommended,
  ...ts.configs.recommended,
  { files: ['**/*.js', '**/*.mjs', '**/*.ts', '**/*.tsx'], languageOptions: { globals: { ...globals.browser, ...globals.node } }, rules: { 'no-empty': ['error', { allowEmptyCatch: true }], '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_', caughtErrors: 'none' }], 'no-unused-vars': 'off' } }
];
