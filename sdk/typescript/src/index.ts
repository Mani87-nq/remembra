/**
 * Remembra - AI Memory Layer SDK
 * 
 * @packageDocumentation
 * 
 * @example
 * ```typescript
 * import { Remembra } from 'remembra';
 * 
 * const memory = new Remembra({
 *   url: 'http://localhost:8787',
 *   apiKey: 'your-api-key',
 *   userId: 'user_123',
 * });
 * 
 * // Store memories
 * await memory.store('User prefers dark mode');
 * 
 * // Recall memories
 * const result = await memory.recall('preferences');
 * console.log(result.context);
 * 
 * // Ingest conversations
 * await memory.ingestConversation([
 *   { role: 'user', content: 'My name is John' },
 * ]);
 * ```
 */

// Main client
export { Remembra } from './client';

// Types
export type {
  RemembraConfig,
  StoreOptions,
  StoreResult,
  RecallOptions,
  RecallResult,
  ForgetOptions,
  ForgetResult,
  Message,
  IngestOptions,
  IngestResult,
  ExtractedFact,
  ExtractedEntity,
  IngestStats,
  Memory,
  EntityRef,
} from './types';

// Errors
export {
  RemembraError,
  AuthenticationError,
  NotFoundError,
  ValidationError,
  RateLimitError,
  ServerError,
  NetworkError,
  TimeoutError,
} from './errors';
