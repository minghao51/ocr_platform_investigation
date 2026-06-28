import { defineConfig } from 'vitest/config'

export default defineConfig({
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
    coverage: {
      reporter: ['text', 'html'],
      exclude: ['**/*.d.ts', 'e2e/**', 'dist/**'],
      thresholds: {
        lines: 70,
        functions: 70,
        branches: 60,
        statements: 70,
      },
    },
  },
})
