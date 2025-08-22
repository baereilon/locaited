// Test setup file
import '@testing-library/jest-dom';

// Mock browser APIs that don't exist in Node
if (!global.URL.createObjectURL) {
  global.URL.createObjectURL = () => 'blob:mock-url';
}
if (!global.URL.revokeObjectURL) {
  global.URL.revokeObjectURL = () => {};
}