<script lang="ts">
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { getSettings, updateSettings, exportState, importState, resetState, subscribe } from '$lib/store.js';
	import { t } from '$lib/i18n.js';
	import type { Settings, Lang, Accent, Category } from '$lib/types.js';
	import Header from '$lib/components/Header.svelte';
	import Icon from '$lib/components/Icon.svelte';

	let settings = $state<Settings>(getSettings());
	let showResetConfirm = $state(false);
	let importMessage = $state('');
	let lang = $state<Lang>(getSettings().lang);

	$effect(() => {
		const unsub = subscribe(() => {
			settings = getSettings();
			lang = getSettings().lang;
		});
		return unsub;
	});

	const categories: Category[] = ['A', 'B', 'C', 'D', 'F'];

	function setCategory(cat: Category) {
		updateSettings({ category: cat });
	}

	function setTheme(theme: Settings['theme']) {
		updateSettings({ theme });
	}

	function handleExport() {
		const data = exportState();
		const blob = new Blob([data], { type: 'application/json' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `vozacki-ispit-backup-${new Date().toISOString().split('T')[0]}.json`;
		a.click();
		URL.revokeObjectURL(url);
	}

	function handleImport() {
		const input = document.createElement('input');
		input.type = 'file';
		input.accept = '.json';
		input.onchange = async () => {
			const file = input.files?.[0];
			if (!file) return;
			try {
				const text = await file.text();
				const success = importState(text);
				importMessage = success ? '✓' : '✗';
				setTimeout(() => { importMessage = ''; }, 3000);
			} catch {
				importMessage = '✗';
				setTimeout(() => { importMessage = ''; }, 3000);
			}
		};
		input.click();
	}

	function handleReset() {
		resetState();
		showResetConfirm = false;
	}

	function toggleLang() {
		const next: Lang = lang === 'sr' ? 'ru' : 'sr';
		updateSettings({ lang: next });
	}

	function resolvedThemeLabel(): string {
		if (settings.theme === 'dark') return lang === 'sr' ? 'Тамна' : 'Тёмная';
		if (settings.theme === 'light') return lang === 'sr' ? 'Светла' : 'Светлая';
		return lang === 'sr' ? 'Систем' : 'Система';
	}

	function cycleTheme() {
		const order: Settings['theme'][] = ['dark', 'light', 'system'];
		const idx = order.indexOf(settings.theme);
		setTheme(order[(idx + 1) % order.length]);
	}
</script>

{#snippet trailing()}
	<button class="done-btn" onclick={() => goto(`${base}/`)}>
		{lang === 'sr' ? 'Готово' : 'Готово'}
	</button>
{/snippet}

<div class="page">
	<Header
		title={t('settings.title', lang)}
		settings={false}
		onback={() => history.back()}
		{trailing}
	/>

	<div class="scroll-area">
		<!-- Category -->
		<div class="section-header">{lang === 'sr' ? 'Категорија возила' : 'Категория ТС'}</div>
		<div class="section-card">
			<div class="cat-row">
				{#each categories as cat}
					<button
						class="cat-btn"
						class:cat-active={settings.category === cat}
						onclick={() => setCategory(cat)}
					>
						{cat}
					</button>
				{/each}
			</div>
			<div class="cat-desc">
				{settings.category} · {lang === 'sr' ? '1780 питања' : '1780 вопросов'}
			</div>
		</div>

		<!-- Language -->
		<div class="section-header">{lang === 'sr' ? 'Језик' : 'Язык'}</div>
		<div class="section-card">
			<button class="row-item" onclick={toggleLang}>
				<span class="row-label">{lang === 'sr' ? 'Језик апликације' : 'Язык приложения'}</span>
				<span class="row-value">{lang === 'sr' ? 'Српски' : 'Русский'}</span>
				<Icon name="chev-right" size={14} color="var(--ink4)" stroke={2} />
				<div class="row-divider"></div>
			</button>
			<button class="row-item" onclick={toggleLang}>
				<span class="row-label">{lang === 'sr' ? 'Језик питања' : 'Язык вопросов'}</span>
				<span class="row-value">{lang === 'sr' ? 'Српски' : 'Русский'}</span>
				<Icon name="chev-right" size={14} color="var(--ink4)" stroke={2} />
			</button>
		</div>

		<!-- Appearance -->
		<div class="section-header">{lang === 'sr' ? 'Изглед' : 'Внешний вид'}</div>
		<div class="section-card">
			<button class="row-item" onclick={cycleTheme}>
				<span class="row-label">{t('settings.theme', lang)}</span>
				<span class="row-value">{resolvedThemeLabel()}</span>
				<Icon name="chev-right" size={14} color="var(--ink4)" stroke={2} />
			</button>
		</div>

		<!-- Progress -->
		<div class="section-header">{lang === 'sr' ? 'Напредак' : 'Прогресс'}</div>
		<div class="section-card">
			<button class="row-item" onclick={handleImport}>
				<span class="row-label">{lang === 'sr' ? 'Увези из датотеке' : 'Импорт из файла'}</span>
				<Icon name="upload" size={17} color="var(--ink2)" stroke={1.6} />
				<div class="row-divider"></div>
			</button>
			<button class="row-item" onclick={handleExport}>
				<span class="row-label">{lang === 'sr' ? 'Извези као датотеку' : 'Экспорт в файл'}</span>
				<Icon name="download" size={17} color="var(--ink2)" stroke={1.6} />
				<div class="row-divider"></div>
			</button>
			<button class="row-item" onclick={() => { showResetConfirm = true; }}>
				<span class="row-label">{lang === 'sr' ? 'Поништи сав напредак' : 'Сбросить прогресс'}</span>
				<span class="row-danger">{lang === 'sr' ? 'Обриши' : 'Удалить'}</span>
			</button>
		</div>

		{#if showResetConfirm}
			<div class="reset-confirm">
				<p>{t('settings.reset.confirm', lang)}</p>
				<div class="reset-btns">
					<button class="reset-cancel" onclick={() => { showResetConfirm = false; }}>{t('common.back', lang)}</button>
					<button class="reset-delete" onclick={handleReset}>{t('settings.reset.yes', lang)}</button>
				</div>
			</div>
		{/if}

		{#if importMessage}
			<div class="import-msg" class:import-ok={importMessage === '✓'}>{importMessage}</div>
		{/if}

		<div class="settings-footer">
			Teorija 2.4.1 · Build 2026.04.12
		</div>
	</div>
</div>

<style>
	.page { height: 100%; display: flex; flex-direction: column; }
	.scroll-area { flex: 1; overflow: auto; padding-bottom: 24px; }

	.done-btn {
		width: 36px; height: 36px;
		background: transparent; border: none;
		color: var(--accent);
		font-family: var(--font-ui);
		font-size: 14px; font-weight: 500;
		cursor: pointer;
		display: flex; align-items: center; justify-content: center;
	}

	.section-header {
		font-family: var(--font-mono);
		font-size: 10px;
		color: var(--ink3);
		letter-spacing: 1px;
		text-transform: uppercase;
		padding: 22px 20px 8px;
	}
	.section-card {
		background: var(--surface);
		border-radius: 18px;
		margin: 0 14px;
		overflow: hidden;
		border: 0.5px solid var(--hairline);
	}

	/* Category */
	.cat-row {
		display: flex; gap: 6px;
		padding: 12px 16px;
	}
	.cat-btn {
		flex: 1; height: 44px; border-radius: 12px;
		display: flex; align-items: center; justify-content: center;
		background: var(--surface2); color: var(--ink2);
		font-family: var(--font-mono); font-size: 15px; font-weight: 500;
		letter-spacing: 0.5px; border: none; cursor: pointer;
	}
	.cat-active {
		background: var(--accent); color: var(--accent-ink);
	}
	.cat-desc {
		font-size: 12px; color: var(--ink3);
		padding: 2px 20px 14px;
	}

	/* Rows */
	.row-item {
		display: flex; align-items: center;
		min-height: 52px; padding: 0 16px;
		position: relative; gap: 12px;
		background: transparent; border: none;
		width: 100%; text-align: left;
		cursor: pointer;
	}
	.row-label { flex: 1; font-size: 15px; color: var(--ink); }
	.row-value { font-size: 13px; color: var(--ink3); font-family: var(--font-mono); }
	.row-danger { color: var(--wrong); font-size: 13px; font-family: var(--font-mono); }
	.row-divider {
		position: absolute; bottom: 0; left: 16px; right: 0;
		height: 0.5px; background: var(--hairline);
	}

	/* Reset confirm */
	.reset-confirm {
		margin: 12px 14px;
		padding: 16px;
		background: var(--wrong-wash);
		border-radius: 16px;
		border: 1px solid var(--wrong);
	}
	.reset-confirm p { font-size: 13px; margin-bottom: 12px; }
	.reset-btns { display: flex; gap: 8px; }
	.reset-cancel, .reset-delete {
		flex: 1; height: 40px; border-radius: 12px;
		font-family: var(--font-ui); font-size: 13px; font-weight: 500;
		cursor: pointer; border: none;
	}
	.reset-cancel { background: var(--surface2); color: var(--ink); }
	.reset-delete { background: var(--wrong); color: #fff; }

	.import-msg {
		margin: 12px 14px;
		padding: 10px 16px;
		border-radius: 12px;
		font-size: 13px;
		background: var(--wrong-wash);
		color: var(--wrong);
		text-align: center;
	}
	.import-ok { background: var(--correct-wash); color: var(--correct); }

	.settings-footer {
		padding: 22px 24px;
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--ink3);
		text-align: center;
		letter-spacing: 0.3px;
	}
</style>
