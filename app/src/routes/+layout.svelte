<script lang="ts">
	import 'bootstrap/dist/css/bootstrap.min.css';
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
		document.documentElement.setAttribute('data-bs-theme', resolvedTheme);
		document.documentElement.setAttribute('data-font-size', fontSize);
	});
</script>

<div class="container app-shell">
	{@render children()}
</div>

<style>
	:global(html[data-font-size='small']) {
		font-size: 14px;
	}
	:global(html[data-font-size='medium']) {
		font-size: 16px;
	}
	:global(html[data-font-size='large']) {
		font-size: 18px;
	}

	:global(body) {
		min-height: 100dvh;
		overflow-x: hidden;
	}

	:global(img) {
		max-width: 100%;
		height: auto;
		display: block;
	}

	.app-shell {
		max-width: 480px;
		min-height: 100dvh;
		position: relative;
		padding-left: 0;
		padding-right: 0;
	}
</style>
