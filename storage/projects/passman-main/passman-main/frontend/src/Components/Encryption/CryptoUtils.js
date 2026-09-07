/**
 * Derives an AES-256 key from a password and salt using PBKDF2
 * @param {string} password - User's password
 * @param {string} base64Salt - Base64 encoded salt from server
 * @returns {CryptoKey} The derived AES-GCM key
 */
export async function deriveAESKey(password, base64Salt) {
    try {
        
        if (!password || typeof password !== 'string') {
            throw new Error('Password must be a non-empty string');
        }
        
        if (!base64Salt || typeof base64Salt !== 'string') {
            throw new Error('Salt must be a non-empty string');
        }
        
        const salt = base64ToArrayBuffer(base64Salt);
        const enc = new TextEncoder();

        const keyMaterial = await window.crypto.subtle.importKey(
            'raw',
            enc.encode(password),
            'PBKDF2',
            false,
            ['deriveKey']
        );
        
        return await window.crypto.subtle.deriveKey(
            {
                name: 'PBKDF2',
                salt: salt,
                iterations: 100000,
                hash: 'SHA-256',
            },
            keyMaterial,
            {
                name: 'AES-GCM',
                length: 256,
            },
            true,
            ['encrypt', 'decrypt']
        );
    } catch (error) {
        console.error('Failed to derive AES key:', error);
        throw error; 
    }
}

/**
 * Encrypts data using AES-256-GCM
 * @param {Object} plainObject - Data object to encrypt
 * @param {CryptoKey} aesKey - AES key for encryption
 * @returns {Object} Object containing encrypted data, IV, and auth tag
 */
export async function encryptData(plainObject, aesKey) {
    const iv = window.crypto.getRandomValues(new Uint8Array(12)); 
    const enc = new TextEncoder();
    const data = enc.encode(JSON.stringify(plainObject));

    const encryptedBuffer = await window.crypto.subtle.encrypt(
        {
            name: 'AES-GCM',
            iv: iv,
        },
        aesKey,
        data
    );

    const encryptedBytes = new Uint8Array(encryptedBuffer);

    const cipherText = encryptedBytes.slice(0, encryptedBytes.length - 16);
    const authTag = encryptedBytes.slice(encryptedBytes.length - 16);

    return {
        encryptedData: arrayBufferToBase64(cipherText),
        iv: arrayBufferToBase64(iv),
        authTag: arrayBufferToBase64(authTag),
    };
}

/**
 * Decrypts data that was encrypted with AES-256-GCM
 * @param {Object} encryptedPackage - Object containing encryptedData, iv, and authTag
 * @param {CryptoKey} aesKey - AES key for decryption
 * @returns {Object} Decrypted data object
 */
export async function decryptData(encryptedPackage, aesKey) {
    try {
        const { encryptedData, iv, authTag } = encryptedPackage;
        const { id, createdAt, updatedAt } = encryptedPackage;
        
        const cipherTextArray = base64ToArrayBuffer(encryptedData);
        const ivArray = base64ToArrayBuffer(iv);
        const authTagArray = base64ToArrayBuffer(authTag);
        
        const encryptedContent = new Uint8Array(cipherTextArray.length + authTagArray.length);
        encryptedContent.set(new Uint8Array(cipherTextArray), 0);
        encryptedContent.set(new Uint8Array(authTagArray), cipherTextArray.length);
        
       const decryptedBuffer = await window.crypto.subtle.decrypt(
            {
                name: 'AES-GCM',
                iv: ivArray,
            },
            aesKey,
            encryptedContent
        );
        
        const dec = new TextDecoder();
        const decryptedString = dec.decode(decryptedBuffer);
       
        const decryptedData = JSON.parse(decryptedString);
        return {
            ...decryptedData,
            id,
            createdAt,
            updatedAt
        };
    } catch (error) {
        console.error('Decryption failed:', error);
        throw new Error('Failed to decrypt data. The key may be incorrect or the data corrupted.');
    }
}

/**
 * Convert an ArrayBuffer to a Base64 string
 * @param {ArrayBuffer|Uint8Array} buffer - The buffer to convert
 * @returns {string} Base64 string
 */
export function arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
}

/**
 * Convert a Base64 string to an ArrayBuffer
 * @param {string} base64 - Base64 string to convert
 * @returns {Uint8Array} The resulting array buffer
 */
export function base64ToArrayBuffer(base64) {
    try {
        if (typeof base64 !== 'string') {
            console.error('Expected a base64 string but got:', typeof base64);
            throw new Error('Invalid input: not a string');
        }

        const cleanBase64 = base64.trim().replace(/\s/g, '');
        
        if (!/^[A-Za-z0-9+/]+={0,2}$/.test(cleanBase64)) {
            console.error('Invalid base64 string format:', cleanBase64);
            throw new Error('Invalid base64 format');
        }
        
        try {
            const binaryString = atob(cleanBase64);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            return bytes;
        } catch (e) {
            console.error('atob failed:', e);
            throw e;
        }
    } catch (error) {
        console.error('Base64 decoding failed:', error, 'Input was:', base64);
        throw new Error('Failed to decode Base64 string: ' + error.message);
    }
}