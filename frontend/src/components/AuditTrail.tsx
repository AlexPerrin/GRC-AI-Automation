import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { getAuditLogs } from '../api/client'

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

// Known acronyms that should stay fully uppercase
const ACRONYMS = new Set(['NDA', 'AI', 'ID', 'API'])

function formatEventType(eventType: string): string {
  return eventType
    .split('_')
    .map(w => ACRONYMS.has(w) ? w : w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ')
}

function eventBadgeColor(eventType: string): string {
  if (eventType.includes('APPROVED'))
    return 'bg-green-100 text-green-800'
  if (eventType.includes('REJECTED') || eventType.includes('ERROR'))
    return 'bg-red-100 text-red-800'
  return 'bg-gray-100 text-gray-700'
}

function EventBadge({ eventType }: { eventType: string }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap ${eventBadgeColor(eventType)}`}>
      {formatEventType(eventType)}
    </span>
  )
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
            <EventBadge eventType={log.event_type} />
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
