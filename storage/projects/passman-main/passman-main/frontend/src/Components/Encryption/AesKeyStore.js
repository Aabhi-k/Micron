// aesKeyStore.js

let aesKey = null;

export function setAESKey(key) {
    aesKey = key;
    window.crypto.subtle.exportKey('raw', key).then(rawKey => {
        sessionStorage.setItem('aesKey', btoa(String.fromCharCode(...new Uint8Array(rawKey))));
    });
}

export async function getAESKey() {
    if (aesKey) return aesKey;

    const stored = sessionStorage.getItem('aesKey');
    if (!stored) return null;

    const binaryString = atob(stored);
    const byteArray = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
        byteArray[i] = binaryString.charCodeAt(i);
    }

    aesKey = await window.crypto.subtle.importKey(
        'raw',
        byteArray,
        { name: 'AES-GCM' },
        true,
        ['encrypt', 'decrypt']
    );
    return aesKey;
}

export function clearAESKey() {
    aesKey = null;
    sessionStorage.removeItem('aesKey');
}
