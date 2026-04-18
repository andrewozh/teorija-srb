<script lang="ts">
	import 'bootstrap/dist/css/bootstrap.min.css';
	import { getSettings, subscribe, updateSettings } from '$lib/store.js';
	import { getPageTitle, onTitleChange } from '$lib/nav.js';
	import { t } from '$lib/i18n.js';
	import type { Lang } from '$lib/types.js';
	import type { Snippet } from 'svelte';
	import { page } from '$app/stores';

	let { children }: { children: Snippet } = $props();

	let theme = $state(getSettings().theme);
	let fontSize = $state(getSettings().fontSize);
	let lang = $state<Lang>(getSettings().lang);
	let pageTitle = $state(getPageTitle());
	let currentPath = $derived($page.url.pathname);
	let isHome = $derived(currentPath === '/');

	$effect(() => {
		const unsub = subscribe(() => {
			theme = getSettings().theme;
			fontSize = getSettings().fontSize;
			lang = getSettings().lang;
		});
		return unsub;
	});

	$effect(() => {
		const unsub = onTitleChange(() => {
			pageTitle = getPageTitle();
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

	function toggleLang() {
		const next: Lang = lang === 'sr' ? 'ru' : 'sr';
		updateSettings({ lang: next });
	}
</script>

<div class="container app-shell">
	<!-- Global header -->
	<nav class="d-flex align-items-center justify-content-between px-3 py-2 sticky-top bg-body border-bottom">
		<div class="d-flex align-items-center gap-1" style="min-width:80px;">
			{#if !isHome}
				<button onclick={() => history.back()} class="btn btn-sm btn-outline-secondary d-flex align-items-center justify-content-center" style="width:36px;height:36px;">
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<polyline points="15 18 9 12 15 6"/>
					</svg>
				</button>
			{/if}
			<button onclick={toggleLang} class="btn btn-outline-secondary btn-sm fw-bold" style="min-width:42px;">
				{lang === 'sr' ? 'RU' : 'SR'}
			</button>
		</div>

		<span class="fw-semibold text-truncate px-2 text-center">
			{isHome ? '🚗 ' + t('app.title', lang) : pageTitle}
		</span>

		<div style="min-width:80px;" class="d-flex justify-content-end">
			<a href="/settings" class="btn btn-outline-secondary btn-sm d-flex align-items-center justify-content-center" style="width:36px;height:36px;" aria-label={t('settings.title', lang)}>
				<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<line x1="3" y1="6" x2="21" y2="6"/>
					<line x1="3" y1="12" x2="21" y2="12"/>
					<line x1="3" y1="18" x2="21" y2="18"/>
				</svg>
			</a>
		</div>
	</nav>

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
