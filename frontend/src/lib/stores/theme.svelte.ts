import { browser } from '$app/environment';
import { get, writable } from 'svelte/store';

export type ThemeMode = 'system' | 'light' | 'dark';
export type ResolvedThemeMode = 'light' | 'dark';

const STORAGE_KEY = 'appgoblin-theme-mode';
const themeModeStore = writable<ThemeMode>('system');
const resolvedThemeModeStore = writable<ResolvedThemeMode>('light');

let initialized = false;
let systemThemeMediaQuery: MediaQueryList | null = null;

function resolveThemeMode(themeMode: ThemeMode, prefersDark: boolean): ResolvedThemeMode {
	if (themeMode === 'system') {
		return prefersDark ? 'dark' : 'light';
	}

	return themeMode;
}

function getStoredThemeMode(): ThemeMode {
	if (!browser) {
		return 'system';
	}

	const storedThemeMode = window.localStorage.getItem(STORAGE_KEY);

	if (storedThemeMode === 'light' || storedThemeMode === 'dark' || storedThemeMode === 'system') {
		return storedThemeMode;
	}

	return 'system';
}

function applyThemeMode(themeMode: ThemeMode) {
	if (!browser) {
		return;
	}

	const prefersDark =
		systemThemeMediaQuery?.matches ?? window.matchMedia('(prefers-color-scheme: dark)').matches;
	const resolvedThemeMode = resolveThemeMode(themeMode, prefersDark);

	document.documentElement.dataset.mode = resolvedThemeMode;
	document.documentElement.style.colorScheme = resolvedThemeMode;
	resolvedThemeModeStore.set(resolvedThemeMode);

	if (themeMode === 'system') {
		window.localStorage.removeItem(STORAGE_KEY);
		return;
	}

	window.localStorage.setItem(STORAGE_KEY, themeMode);
}

themeModeStore.subscribe((themeMode) => {
	if (!browser || !initialized) {
		return;
	}

	applyThemeMode(themeMode);
});

export const themeMode = {
	subscribe: themeModeStore.subscribe
};

export const resolvedThemeMode = {
	subscribe: resolvedThemeModeStore.subscribe
};

export function initializeTheme() {
	if (!browser || initialized) {
		return;
	}

	systemThemeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
	initialized = true;

	const handleSystemThemeChange = () => {
		applyThemeMode(get(themeModeStore));
	};

	systemThemeMediaQuery.addEventListener('change', handleSystemThemeChange);
	themeModeStore.set(getStoredThemeMode());
}

export function setThemeMode(themeMode: ThemeMode) {
	themeModeStore.set(themeMode);
}

export function toggleTheme() {
	themeModeStore.set(get(resolvedThemeModeStore) === 'dark' ? 'light' : 'dark');
}
