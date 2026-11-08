import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

function download(filename, text) {
  const blob = new Blob([text], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}

function slugify(value) {
  return (
    value
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 60) || 'brief'
  )
}

export default function BriefView({ topic, report }) {
  if (!report) return null

  return (
    <section className="card brief">
      <div className="brief-header">
        <h2>Brief</h2>
        <button
          type="button"
          className="button-secondary"
          onClick={() => download(slugify(topic) + '.md', report.summary_markdown)}
        >
          Download Markdown
        </button>
      </div>

      <article className="markdown">
        <Markdown remarkPlugins={[remarkGfm]}>{report.summary_markdown}</Markdown>
      </article>

      {report.sources.length > 0 && (
        <details className="sources">
          <summary>{report.sources.length} source(s) used</summary>
          <ul>
            {report.sources.map((source) => (
              <li key={source.url}>
                <a href={source.url} target="_blank" rel="noreferrer noopener">
                  {source.title || source.url}
                </a>
                <p>{source.snippet}</p>
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  )
}
