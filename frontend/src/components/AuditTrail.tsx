import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { getAuditLogs } from '../api/client'
import Badge from './ui/Badge'

interface AuditTrailProps {
  vendorId: number
}

function formatTimestamp(ts: string) {
  const d = new Date(ts)
  return d.toLocaleString('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

export default function AuditTrail({ vendorId }: AuditTrailProps) {
  const { data: logs } = useQuery({
    queryKey: ['audit-logs', String(vendorId)],
    queryFn: () => getAuditLogs(vendorId),
    refetchInterval: 5000,
  })

  const [expanded, setExpanded] = useState<Set<number>>(new Set())

  const toggle = (id: number) =>
    setExpanded((s) => {
      const next = new Set(s)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })

  if (!logs || logs.length === 0) {
    return <p className="text-sm text-gray-500">No audit events recorded yet.</p>
  }

  return (
    <ol className="relative border-l border-gray-200 space-y-6 ml-4">
      {logs.map((log) => (
        <li key={log.id} className="ml-4">
          <div className="absolute -left-1.5 mt-1.5 h-3 w-3 rounded-full border border-white bg-blue-400" />
          <div className="flex flex-wrap items-start gap-2">
            <time className="text-xs text-gray-400 whitespace-nowrap">
              {formatTimestamp(log.timestamp)}
            </time>
            <Badge label={log.event_type} />
            <span className="text-xs text-gray-600">{log.actor}</span>
          </div>
          {log.payload && (
            <div className="mt-1">
              <button
                onClick={() => toggle(log.id)}
                className="text-xs text-blue-500 hover:underline"
              >
                {expanded.has(log.id) ? 'hide payload' : 'show payload'}
              </button>
              {expanded.has(log.id) && (
                <pre className="mt-1 rounded bg-gray-100 p-2 text-xs text-gray-700 overflow-auto max-h-40">
                  {JSON.stringify(log.payload, null, 2)}
                </pre>
              )}
            </div>
          )}
        </li>
      ))}
    </ol>
  )
}
