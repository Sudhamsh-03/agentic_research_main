const LABELS = {
  pending: 'Queued',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
}

export default function StatusBadge({ status }) {
  const label = LABELS[status] || status
  return <span className={'badge badge-' + status}>{label}</span>
}
