function tryParseJson(output: string) {
  try {
    return JSON.parse(output) as Record<string, unknown>
  } catch {
    return null
  }
}

type ParsedSection = {
  title: string
  paragraphs: string[]
  tables: Array<{
    headers: string[]
    rows: string[][]
  }>
}

function parseMarkdown(output: string): ParsedSection[] {
  const sections: ParsedSection[] = []
  const lines = output.split(/\r?\n/)
  let current: ParsedSection = { title: 'Matrix output', paragraphs: [], tables: [] }
  let index = 0

  while (index < lines.length) {
    const line = lines[index].trim()

    if (line.startsWith('#')) {
      if (current.paragraphs.length || current.tables.length) {
        sections.push(current)
      }
      current = { title: line.replace(/^#+\s*/, ''), paragraphs: [], tables: [] }
      index += 1
      continue
    }

    if (line.includes('|') && index + 1 < lines.length && /^\|?\s*[-:]/.test(lines[index + 1].trim())) {
      const headers = line
        .split('|')
        .map((value) => value.trim())
        .filter(Boolean)
      const rows: string[][] = []
      index += 2
      while (index < lines.length && lines[index].includes('|')) {
        rows.push(
          lines[index]
            .split('|')
            .map((value) => value.trim())
            .filter(Boolean),
        )
        index += 1
      }
      current.tables.push({ headers, rows })
      continue
    }

    if (line) {
      current.paragraphs.push(line)
    }
    index += 1
  }

  if (current.paragraphs.length || current.tables.length || !sections.length) {
    sections.push(current)
  }

  return sections
}

function objectToRows(value: unknown) {
  if (!Array.isArray(value)) {
    return null
  }

  const rows = value.filter((item): item is Record<string, unknown> => typeof item === 'object' && item !== null)
  if (!rows.length) {
    return null
  }

  const headers = Array.from(new Set(rows.flatMap((item) => Object.keys(item))))
  return {
    headers,
    rows: rows.map((row) => headers.map((header) => String(row[header] ?? '—'))),
  }
}

export function MatrixRenderer({ output }: { output: string }) {
  const parsedJson = tryParseJson(output)

  if (parsedJson) {
    return (
      <div className="space-y-6">
        {Object.entries(parsedJson).map(([key, value]) => {
          const table = objectToRows(value)
          return (
            <section key={key} className="rounded-3xl border border-white/10 bg-slate-950/70 p-4">
              <h4 className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">{key.replace(/_/g, ' ')}</h4>
              {table ? (
                <div className="mt-4 overflow-x-auto rounded-2xl border border-white/10">
                  <table className="min-w-full divide-y divide-white/10 text-sm">
                    <thead className="bg-slate-900/80 text-left text-slate-200">
                      <tr>
                        {table.headers.map((header) => (
                          <th key={header} className="px-4 py-3 font-medium capitalize">
                            {header.replace(/_/g, ' ')}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 bg-slate-950/70 text-slate-300">
                      {table.rows.map((row, rowIndex) => (
                        <tr key={`${key}-${rowIndex}`}>
                          {row.map((cell, cellIndex) => (
                            <td key={`${key}-${rowIndex}-${cellIndex}`} className="px-4 py-3 align-top">
                              {cell}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <pre className="mt-4 overflow-x-auto rounded-2xl bg-slate-900/80 p-4 text-xs text-slate-300">
                  {JSON.stringify(value, null, 2)}
                </pre>
              )}
            </section>
          )
        })}
      </div>
    )
  }

  const sections = parseMarkdown(output)

  return (
    <div className="space-y-6">
      {sections.map((section) => (
        <section key={section.title} className="rounded-3xl border border-white/10 bg-slate-950/70 p-4">
          <h4 className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">{section.title}</h4>
          {section.paragraphs.length ? (
            <div className="mt-4 space-y-3 text-sm leading-7 text-slate-300">
              {section.paragraphs.map((paragraph, index) => (
                <p key={`${section.title}-${index}`}>{paragraph}</p>
              ))}
            </div>
          ) : null}
          {section.tables.map((table, tableIndex) => (
            <div key={`${section.title}-${tableIndex}`} className="mt-4 overflow-x-auto rounded-2xl border border-white/10">
              <table className="min-w-full divide-y divide-white/10 text-sm">
                <thead className="bg-slate-900/80 text-left text-slate-100">
                  <tr>
                    {table.headers.map((header) => (
                      <th key={header} className="px-4 py-3 font-medium">
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 bg-slate-950/70 text-slate-300">
                  {table.rows.map((row, rowIndex) => (
                    <tr key={`${section.title}-${tableIndex}-${rowIndex}`}>
                      {row.map((cell, cellIndex) => (
                        <td key={`${section.title}-${tableIndex}-${rowIndex}-${cellIndex}`} className="px-4 py-3 align-top">
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </section>
      ))}
    </div>
  )
}
