/**
 * Simple logging utility for development vs production
 */

const isDevelopment = import.meta.env.DEV;

export const logger = {
    debug: (...args) => {
        if (isDevelopment) {
            console.log('🔍', ...args);
        }
    },

    info: (...args) => {
        if (isDevelopment) {
            console.log('ℹ️', ...args);
        }
    },

    warn: (...args) => {
        console.warn('⚠️', ...args);
    },

    error: (...args) => {
        console.error('❌', ...args);
    },

    success: (...args) => {
        if (isDevelopment) {
            console.log('✅', ...args);
        }
    }
};

export default logger;
