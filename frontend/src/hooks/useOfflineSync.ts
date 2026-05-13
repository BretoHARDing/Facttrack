import { useCallback, useEffect, useState } from 'react'

const DB_NAME = 'facttrack-offline'
const STORE_NAME = 'matrix-results'
const DB_VERSION = 1

export type CachedMatrixResult = {
  evidenceId: string
  caseId: string
  title: string
  matrixOutput: string
  cachedAt: string
}

async function openDb() {
  return new Promise<IDBDatabase>((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION)

    request.onupgradeneeded = () => {
      const db = request.result
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'evidenceId' })
      }
    }

    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

async function putMatrixResult(value: CachedMatrixResult) {
  const db = await openDb()

  return new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite')
    tx.objectStore(STORE_NAME).put(value)
    tx.oncomplete = () => resolve()
    tx.onerror = () => reject(tx.error)
  })
}

async function getMatrixResult(evidenceId: string) {
  const db = await openDb()

  return new Promise<CachedMatrixResult | undefined>((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly')
    const request = tx.objectStore(STORE_NAME).get(evidenceId)
    request.onsuccess = () => resolve(request.result as CachedMatrixResult | undefined)
    request.onerror = () => reject(request.error)
  })
}

export function useOfflineSync() {
  const [online, setOnline] = useState(() => navigator.onLine)

  useEffect(() => {
    const onOnline = () => setOnline(true)
    const onOffline = () => setOnline(false)

    window.addEventListener('online', onOnline)
    window.addEventListener('offline', onOffline)

    return () => {
      window.removeEventListener('online', onOnline)
      window.removeEventListener('offline', onOffline)
    }
  }, [])

  const saveMatrixResult = useCallback(async (value: CachedMatrixResult) => {
    await putMatrixResult(value)
  }, [])

  const readMatrixResult = useCallback(async (evidenceId: string) => getMatrixResult(evidenceId), [])

  return {
    online,
    saveMatrixResult,
    getMatrixResult: readMatrixResult,
  }
}
