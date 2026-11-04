export function sanitizeSearchTerm(term: string): string {
	return term
		.replace(/[^\p{L}\p{N}\s]/gu, '')
		.replace(/\s+/g, ' ')
		.trim();
}
