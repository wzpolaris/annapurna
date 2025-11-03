export const MAX_PREVIEW_ROWS = 150;
export const MAX_PREVIEW_COLUMNS = 24;
export const MAX_PREVIEW_CHARS = 200_000;
const MAX_CELL_LENGTH = 200;

const DELIMITER_CANDIDATES = [
  { char: ',', label: 'Comma' },
  { char: '\t', label: 'Tab' },
  { char: ';', label: 'Semicolon' },
  { char: '|', label: 'Pipe' }
] as const;

const EM_DASH = '…';

export interface DelimitedPreview {
  headers: string[];
  rows: string[][];
  delimiterLabel: string;
}

export interface TextPreviewResult {
  truncatedText: string;
  truncated: boolean;
  tablePreview: DelimitedPreview | null;
}

const truncateCell = (value: string): string => {
  if (value.length <= MAX_CELL_LENGTH) {
    return value;
  }
  return `${value.slice(0, MAX_CELL_LENGTH - 1)}${EM_DASH}`;
};

const splitDelimitedLine = (line: string, delimiter: string): string[] => {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '"') {
      const next = line[i + 1];
      if (inQuotes && next === '"') {
        current += '"';
        i += 1;
        continue;
      }
      inQuotes = !inQuotes;
      continue;
    }

    if (char === delimiter && !inQuotes) {
      result.push(truncateCell(current.trim()));
      current = '';
      continue;
    }

    current += char;
  }

  result.push(truncateCell(current.trim()));
  return result;
};

export const analyzeDelimitedText = (text: string): DelimitedPreview | null => {
  if (!text) {
    return null;
  }

  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trimEnd())
    .filter((line) => line.length > 0);

  if (lines.length < 2) {
    return null;
  }

  const limitedLines = lines.slice(0, MAX_PREVIEW_ROWS + 1);
  const majorityThreshold = Math.max(2, Math.floor(limitedLines.length * 0.6));

  for (const candidate of DELIMITER_CANDIDATES) {
    const parsed = limitedLines.map((line) => splitDelimitedLine(line, candidate.char));
    const columnCounts = parsed.map((row) => row.length);
    const firstCount = columnCounts[0];

    if (firstCount <= 1 || firstCount > MAX_PREVIEW_COLUMNS) {
      continue;
    }

    const consistent = columnCounts.filter((count) => count === firstCount).length;
    if (consistent < majorityThreshold) {
      continue;
    }

    const [headerRow, ...rows] = parsed;

    return {
      headers: headerRow,
      rows: rows.slice(0, MAX_PREVIEW_ROWS).map((row) => {
        if (row.length === firstCount) {
          return row;
        }
        const adjusted = [...row];
        while (adjusted.length < firstCount) {
          adjusted.push('');
        }
        return adjusted.slice(0, firstCount);
      }),
      delimiterLabel: candidate.label
    };
  }

  return null;
};

export const prepareTextPreview = (text: string): TextPreviewResult => {
  const truncated = text.length > MAX_PREVIEW_CHARS;
  const sample = truncated ? text.slice(0, MAX_PREVIEW_CHARS) : text;
  const truncatedText = truncated ? `${sample}\n${EM_DASH}` : sample;
  const tablePreview = analyzeDelimitedText(sample);
  return {
    truncatedText,
    truncated,
    tablePreview
  };
};
