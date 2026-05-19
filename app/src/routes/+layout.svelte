<script lang="ts">
	import '$lib/tokens.css';
	import { getSettings, subscribe, updateSettings } from '$lib/store.js';
	import type { Lang } from '$lib/types.js';
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();

	let theme = $state(getSettings().theme);
	let accent = $state(getSettings().accent || 'gold');
	let systemDark = $state(typeof window !== 'undefined' ? window.matchMedia('(prefers-color-scheme: dark)').matches : true);

	$effect(() => {
		const unsub = subscribe(() => {
			theme = getSettings().theme;
			accent = getSettings().accent || 'gold';
		});
		return unsub;
	});

	$effect(() => {
		const mq = window.matchMedia('(prefers-color-scheme: dark)');
		const handler = (e: MediaQueryListEvent) => { systemDark = e.matches; };
		mq.addEventListener('change', handler);
		return () => mq.removeEventListener('change', handler);
	});

	let resolvedTheme = $derived(theme === 'system' ? (systemDark ? 'dark' : 'light') : theme);

	$effect(() => {
		document.documentElement.setAttribute('data-theme', resolvedTheme);
		document.documentElement.setAttribute('data-accent', accent);
	});
</script>

<div class="app-shell">
	{@render children()}
</div>

<style>
	.app-shell {
		max-width: 480px;
		min-height: 100dvh;
		margin: 0 auto;
		position: relative;
		display: flex;
		flex-direction: column;
		padding-top: env(safe-area-inset-top);
		padding-bottom: env(safe-area-inset-bottom);
		padding-left: env(safe-area-inset-left);
		padding-right: env(safe-area-inset-right);
	}
</style>
