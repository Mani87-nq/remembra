import { describe, expect, it } from 'vitest';

import { Remembra, RemembraError, ValidationError } from '../src/index';

describe('remembra SDK exports', () => {
  it('exports the Remembra client class', () => {
    expect(Remembra).toBeTypeOf('function');
  });

  it('exports the base error type', () => {
    expect(RemembraError).toBeTypeOf('function');
  });

  it('validates required config on construction', () => {
    expect(() => new Remembra({ url: 'http://localhost:8787', userId: '' })).toThrow(ValidationError);
  });
});

