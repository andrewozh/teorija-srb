<script lang="ts">
	import '$lib/tokens.css';
	import { getSettings, subscribe } from '$lib/store.js';
	import type { Snippet } from 'svelte';
	import Sidebar from '$lib/components/Sidebar.svelte';

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

<div class="app-root">
	<div class="app-sidebar">
		<Sidebar />
	</div>
	<div class="app-shell">
		{@render children()}
	</div>
</div>

<style>
	.app-root {
		display: flex;
		min-height: 100dvh;
	}

	/* Sidebar: hidden on mobile, visible on desktop */
	.app-sidebar {
		display: none;
	}

	/* Covers the safe-area zone so scrolled content never bleeds behind the notch */
	.app-shell::before {
		content: '';
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		height: env(safe-area-inset-top);
		background: var(--bg);
		z-index: 50;
	}

	/* Mobile shell: unchanged */
	.app-shell {
		max-width: 480px;
		min-height: 100dvh;
		margin: 0 auto;
		position: relative;
		display: flex;
		flex-direction: column;
		flex: 1;
		padding-top: env(safe-area-inset-top);
		padding-bottom: env(safe-area-inset-bottom);
		padding-left: env(safe-area-inset-left);
		padding-right: env(safe-area-inset-right);
	}

	/* Desktop: ≥1024px */
	@media (min-width: 1024px) {
		.app-sidebar {
			display: block;
		}
		.app-shell {
			max-width: none;
			margin: 0;
			padding: 0;
		}
	}
</style>
