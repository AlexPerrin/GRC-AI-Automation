import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { ChangeEvent } from 'react'
import { useRef } from 'react'
import { uploadDocument } from '../api/client'
import type { Document, DocumentStage } from '../types'
import Spinner from './ui/Spinner'

interface DocumentUploadProps {
  vendorId: number
  stage: DocumentStage
  docType: string
  documents: Document[]
}

export default function DocumentUpload({
  vendorId,
  stage,
  docType,
  documents,
}: DocumentUploadProps) {
  const queryClient = useQueryClient()
  const inputRef = useRef<HTMLInputElement>(null)
  const mutation = useMutation({
    mutationFn: (file: File) => uploadDocument(vendorId, stage, docType, file),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['documents', String(vendorId)] })
    },
  })

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      mutation.mutate(file)
      e.target.value = ''
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-gray-700">Upload document</span>
        <input
          ref={inputRef}
          type="file"
          onChange={handleChange}
          disabled={mutation.isPending}
          className="sr-only"
        />
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={mutation.isPending}
          className="rounded-md bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
        >
          Choose File
        </button>
      </div>
      {mutation.isPending && (
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Spinner className="h-4 w-4" />
          Uploading…
        </div>
      )}
      {mutation.isError && (
        <p className="text-sm text-red-600">{(mutation.error as Error).message}</p>
      )}
      {documents.length > 0 && (
        <ul className="divide-y divide-gray-100 rounded-md border border-gray-200">
          {documents.map((doc) => (
            <li key={doc.id} className="flex items-center justify-between px-3 py-2">
              <span className="text-sm text-gray-700 truncate">{doc.filename}</span>
              <span className="ml-4 text-xs text-gray-400 whitespace-nowrap">
                {new Date(doc.uploaded_at).toLocaleDateString()}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
