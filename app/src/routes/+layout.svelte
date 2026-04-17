<script lang="ts">
	import { getSettings, subscribe } from '$lib/store.js';
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();

	let theme = $state(getSettings().theme);
	let fontSize = $state(getSettings().fontSize);

	$effect(() => {
		const unsub = subscribe(() => {
			theme = getSettings().theme;
			fontSize = getSettings().fontSize;
		});
		return unsub;
	});

	let resolvedTheme = $derived.by(() => {
		if (theme === 'system') {
			if (typeof window !== 'undefined') {
				return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
			}
			return 'light';
		}
		return theme;
	});

	$effect(() => {
		document.documentElement.setAttribute('data-theme', resolvedTheme);
		document.documentElement.setAttribute('data-font-size', fontSize);
	});
</script>

<div class="app-shell">
	{@render children()}
</div>

<style>
	:global(*) {
		margin: 0;
		padding: 0;
		box-sizing: border-box;
	}

	:global(html) {
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
			'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji';
		-webkit-font-smoothing: antialiased;
		-moz-osx-font-smoothing: grayscale;
		-webkit-text-size-adjust: 100%;
	}

	:global(html[data-font-size='small']) {
		font-size: 14px;
	}
	:global(html[data-font-size='medium']) {
		font-size: 16px;
	}
	:global(html[data-font-size='large']) {
		font-size: 18px;
	}

	/* Light theme (default) */
	:global(html),
	:global(html[data-theme='light']) {
		--bg: #f0f2f5;
		--bg-secondary: #e4e6eb;
		--card: #ffffff;
		--card-hover: #f8f9fa;
		--text: #1a1a2e;
		--text-secondary: #65676b;
		--text-muted: #8a8d91;
		--border: #e4e6eb;
		--primary: #3b82f6;
		--primary-light: #dbeafe;
		--success: #10b981;
		--success-light: #d1fae5;
		--danger: #ef4444;
		--danger-light: #fee2e2;
		--warning: #f59e0b;
		--warning-light: #fef3c7;
		--purple: #8b5cf6;
		--purple-light: #ede9fe;
		--shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.06);
		--shadow-lg: 0 4px 12px rgba(0, 0, 0, 0.1);
		--radius: 12px;
		--radius-sm: 8px;
		--radius-pill: 20px;
		color-scheme: light;
	}

	/* Dark theme */
	:global(html[data-theme='dark']) {
		--bg: #1a1a1a;
		--bg-secondary: #2d2d2d;
		--card: #2d2d2d;
		--card-hover: #3a3a3a;
		--text: #e4e6eb;
		--text-secondary: #b0b3b8;
		--text-muted: #8a8d91;
		--border: #3e4042;
		--primary: #5b9bf6;
		--primary-light: #1e3a5f;
		--success: #34d399;
		--success-light: #064e3b;
		--danger: #f87171;
		--danger-light: #7f1d1d;
		--warning: #fbbf24;
		--warning-light: #78350f;
		--purple: #a78bfa;
		--purple-light: #3b2e6e;
		--shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
		--shadow-lg: 0 4px 12px rgba(0, 0, 0, 0.4);
		color-scheme: dark;
	}

	:global(body) {
		background: var(--bg);
		color: var(--text);
		min-height: 100dvh;
		overflow-x: hidden;
	}

	:global(a) {
		color: inherit;
		text-decoration: none;
	}

	:global(button) {
		font: inherit;
		color: inherit;
		cursor: pointer;
		border: none;
		background: none;
	}

	:global(img) {
		max-width: 100%;
		height: auto;
		display: block;
	}

	.app-shell {
		max-width: 480px;
		margin: 0 auto;
		min-height: 100dvh;
		position: relative;
	}
</style>
