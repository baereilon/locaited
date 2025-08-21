import { describe, it, expect } from 'vitest';
import { LOCATIONS } from '../config/constants';

describe('Smoke Tests - Basic Setup', () => {
  it('vitest is working', () => {
    expect(1 + 1).toBe(2);
  });
  
  it('can import constants', () => {
    expect(LOCATIONS).toBeDefined();
    expect(LOCATIONS.length).toBeGreaterThan(0);
  });
});