import { useState } from 'react'

const TONES = [
  { value: 'neutral', label: 'Neutral' },
  { value: 'executive', label: 'Executive' },
  { value: 'technical', label: 'Technical' },
  { value: 'conversational', label: 'Conversational' },
]

export default function ResearchForm({ onSubmit, disabled }) {
  const [topic, setTopic] = useState('')
  const [depth, setDepth] = useState(2)
  const [tone, setTone] = useState('neutral')
  const [targetWords, setTargetWords] = useState(600)

  const canSubmit = topic.trim().length >= 4 && !disabled

  function handleSubmit(event) {
    event.preventDefault()
    if (!canSubmit) return
    onSubmit({
      topic: topic.trim(),
      depth: Number(depth),
      tone,
      target_words: Number(targetWords),
    })
  }

  return (
    <form className="card research-form" onSubmit={handleSubmit}>
      <div className="field">
        <label htmlFor="topic">Research topic</label>
        <input
          id="topic"
          name="topic"
          type="text"
          value={topic}
          placeholder="How are state graphs used to orchestrate LLM agents?"
          onChange={(event) => setTopic(event.target.value)}
          disabled={disabled}
          required
          minLength={4}
          maxLength={500}
        />
        <p className="hint">At least four characters. Be specific for a sharper brief.</p>
      </div>

      <div className="field-row">
        <div className="field">
          <label htmlFor="depth">Research rounds</label>
          <input
            id="depth"
            name="depth"
            type="number"
            min={1}
            max={4}
            value={depth}
            onChange={(event) => setDepth(event.target.value)}
            disabled={disabled}
          />
        </div>

        <div className="field">
          <label htmlFor="tone">Tone</label>
          <select
            id="tone"
            name="tone"
            value={tone}
            onChange={(event) => setTone(event.target.value)}
            disabled={disabled}
          >
            {TONES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="targetWords">Target length (words)</label>
          <input
            id="targetWords"
            name="targetWords"
            type="number"
            min={150}
            max={2500}
            step={50}
            value={targetWords}
            onChange={(event) => setTargetWords(event.target.value)}
            disabled={disabled}
          />
        </div>
      </div>

      <button type="submit" className="button-primary" disabled={!canSubmit}>
        {disabled ? 'Research in progress...' : 'Start research'}
      </button>
    </form>
  )
}
