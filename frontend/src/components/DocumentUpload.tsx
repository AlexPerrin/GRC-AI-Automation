import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { ChangeEvent } from 'react'
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
      <label className="block">
        <span className="text-sm font-medium text-gray-700">Upload document</span>
        <input
          type="file"
          onChange={handleChange}
          disabled={mutation.isPending}
          className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:rounded-md file:border-0 file:bg-blue-50 file:px-4 file:py-2 file:text-sm file:font-medium file:text-blue-700 hover:file:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-50"
        />
      </label>
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
