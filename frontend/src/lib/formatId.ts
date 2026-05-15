/** Shorten UUIDs / long identifiers for dense UI (full value still in API / tooltips). */
export function shortId(value: string, head = 8): string {
  const t = value.trim();
  if (t.length <= head + 1) {
    return t;
  }
  return `${t.slice(0, head)}…`;
}
