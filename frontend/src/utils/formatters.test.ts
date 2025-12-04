import {
  formatRelativeTime,
  formatDate,
  truncateText,
  parseStatusChange,
  parseStatusChanges,
} from './formatters';

describe('formatRelativeTime', () => {
  it('formats recent time as "just now"', () => {
    const now = new Date().toISOString();
    expect(formatRelativeTime(now)).toBe('just now');
  });

  it('formats minutes ago', () => {
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString();
    expect(formatRelativeTime(fiveMinutesAgo)).toBe('5 minutes ago');
  });

  it('formats hours ago', () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString();
    expect(formatRelativeTime(twoHoursAgo)).toBe('2 hours ago');
  });

  it('formats days ago', () => {
    const threeDaysAgo = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString();
    expect(formatRelativeTime(threeDaysAgo)).toBe('3 days ago');
  });

  it('formats old dates as locale date string', () => {
    const longAgo = new Date('2020-01-01').toISOString();
    const result = formatRelativeTime(longAgo);
    expect(result).toContain('2020');
  });
});

describe('formatDate', () => {
  it('formats date to locale string', () => {
    const date = '2024-01-15T12:30:00Z';
    const result = formatDate(date);
    expect(result).toContain('2024');
  });
});

describe('truncateText', () => {
  it('returns text as-is when shorter than max length', () => {
    expect(truncateText('short', 10)).toBe('short');
  });

  it('truncates text when longer than max length', () => {
    expect(truncateText('this is a long text', 10)).toBe('this is a ...');
  });

  it('handles exact length', () => {
    expect(truncateText('exactly10!', 10)).toBe('exactly10!');
  });
});

describe('parseStatusChange', () => {
  it('parses arrow format "Key: OLD → NEW"', () => {
    const result = parseStatusChange('Status: Open → Closed');
    expect(result).toEqual({
      key: 'Status',
      oldValue: 'Open',
      newValue: 'Closed',
    });
  });

  it('parses "changed from" format', () => {
    const result = parseStatusChange('Price changed from $10 to $15');
    expect(result).toEqual({
      key: 'Price',
      oldValue: '$10',
      newValue: '$15',
    });
  });

  it('returns null for non-matching format', () => {
    const result = parseStatusChange('Just a regular description');
    expect(result).toBeNull();
  });

  it('handles whitespace correctly', () => {
    const result = parseStatusChange('Status:   Open   →   Closed  ');
    expect(result).toEqual({
      key: 'Status',
      oldValue: 'Open',
      newValue: 'Closed',
    });
  });
});

describe('parseStatusChanges', () => {
  it('parses multiple status changes from multiline text', () => {
    const text = `Status: Open → Closed
Price changed from $10 to $15`;
    const result = parseStatusChanges(text);
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual({
      key: 'Status',
      oldValue: 'Open',
      newValue: 'Closed',
    });
    expect(result[1]).toEqual({
      key: 'Price',
      oldValue: '$10',
      newValue: '$15',
    });
  });

  it('returns empty array for non-matching text', () => {
    const result = parseStatusChanges('No status changes here');
    expect(result).toEqual([]);
  });

  it('handles mixed content', () => {
    const text = `Some regular text
Status: Open → Closed
More regular text
Price changed from $10 to $15`;
    const result = parseStatusChanges(text);
    expect(result).toHaveLength(2);
  });
});
