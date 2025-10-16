/**
 * Configuration settings for AI Document Structurer
 */
import dotenv from 'dotenv';

// Load environment variables from .env file
dotenv.config();

class Config {
  constructor() {
    // API Keys
    this.OPENAI_API_KEY = process.env.OPENAI_API_KEY;
    this.BRAVE_API_KEY = process.env.BRAVE_API_KEY;
    this.OPENAI_MODEL = process.env.OPENAI_MODEL || 'gpt-4o-mini';
    this.GOOGLE_API_KEY = process.env.GOOGLE_API_KEY || process.env.GEMINI_API_KEY;

    // Environment info (kept for logging purposes)
    this.ENVIRONMENT = process.env.ENVIRONMENT || 'development';

    // Liberal timeouts and retries (formerly dev-level settings)
    this.API_TIMEOUT = parseInt(process.env.API_TIMEOUT || '60', 10);
    this.MAX_RETRIES = parseInt(process.env.MAX_RETRIES || '3', 10);

    // Generous token limits (formerly dev-level settings) - Increased for article processing
    this.MAX_TOKENS = {
      Concise: parseInt(process.env.MAX_TOKENS_CONCISE || '4000', 10),
      Detailed: parseInt(process.env.MAX_TOKENS_DETAILED || '8000', 10),
      Comprehensive: parseInt(process.env.MAX_TOKENS_COMPREHENSIVE || '12000', 10)
    };
  }
}

export function getConfig() {
  return new Config();
}

// Global configuration instance
export const appConfig = getConfig();
