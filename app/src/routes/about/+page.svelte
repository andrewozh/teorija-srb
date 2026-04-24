<script lang="ts">
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { loadQuestions } from '$lib/data.js';
	import { getSettings, subscribe } from '$lib/store.js';
	import { t } from '$lib/i18n.js';
	import type { Lang, QuestionsData } from '$lib/types.js';
	import Header from '$lib/components/Header.svelte';
	import Icon from '$lib/components/Icon.svelte';

	let lang = $state<Lang>(getSettings().lang);
	let showBreakdown = $state(false);
	let sectionCounts = $state<{name: string, count: number, newCount: number, changed: number, removed: number}[]>([]);

	$effect(() => {
		const unsub = subscribe(() => { lang = getSettings().lang; });
		return unsub;
	});

	onMount(async () => {
		const data = await loadQuestions();
		sectionCounts = data.metadata.sections.map(s => {
			const qs = data.questions.filter(q => q.section === s.id);
			return {
				name: s.name,
				count: qs.length,
				newCount: qs.filter(q => q.is_new).length,
				changed: qs.filter(q => q.is_changed).length,
				removed: qs.filter(q => q.is_removed).length,
			};
		});
	});
</script>

<div class="page">
	<Header title={t('settings.about', lang)} settings={false} onback={() => goto(`${base}/settings`)} />

	<div class="scroll-area">
		<div class="about-hero">
			<div class="about-icon">
				<img src="{base}/icon-192.png" alt="Teorija" width="96" height="96" style="border-radius: 22px; box-shadow: 0 2px 12px rgba(0,0,0,0.25), 0 0 0 0.5px var(--hairline);" />
			</div>
			<div class="about-name">Teorija <span class="beta-badge">beta</span></div>
			<div class="about-version">0.8.3-beta</div>
		</div>

		<div class="about-card">
			<div class="about-row">
				<span class="about-label">{lang === 'sr' ? 'База ажурирана' : 'База обновлена'}</span>
				<span class="about-val">12. април 2026.</span>
			</div>
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div class="about-row about-row-clickable" onclick={() => showBreakdown = !showBreakdown}>
				<span class="about-label">{lang === 'sr' ? 'Број питања' : 'Кол-во вопросов'}</span>
				<span class="about-val">2,315 {showBreakdown ? '▾' : '▸'}</span>
			</div>
			{#if showBreakdown}
				{#each sectionCounts as { name, count, newCount, changed, removed }}
					<div class="about-row about-row-sub">
						<span class="about-label">{name}</span>
						<span class="about-val-group">
							{#if newCount}<span class="tag-new">+{newCount}</span>{/if}
							{#if changed}<span class="tag-changed">~{changed}</span>{/if}
							{#if removed}<span class="tag-removed">-{removed}</span>{/if}
							<span class="about-val">{count}</span>
						</span>
					</div>
				{/each}
			{/if}
			<div class="about-row">
				<span class="about-label">{lang === 'sr' ? 'Извор питања' : 'Источник вопросов'}</span>
				<a href="https://www.mup.gov.rs/wps/portal/sr/gradjani/dokumenta/vozacka%20dozvola/ispitna%20pitanja%20i%20ostala%20dokumenta%20za%20osposobljavanje%20kandidata/" target="_blank" class="about-link">МУП Србије →</a>
			</div>
			<div class="about-row about-row-last">
				<span class="about-label">{lang === 'sr' ? 'Извор одговора' : 'Источник ответов'}</span>
				<a href="https://autoskolasljivic.com/wp-content/uploads/2020/09/SVA-PITANJA-sa-resenjima.pdf" target="_blank" class="about-link">Auto škola Šljivić (PDF) →</a>
			</div>
		</div>

		<div class="about-card">
			<div class="about-row about-row-last">
				<span class="about-label">{lang === 'sr' ? 'Отворени код' : 'Открытый код'}</span>
				<a href="https://github.com/andrewozh/teorija-srb" target="_blank" class="about-link">GitHub →</a>
			</div>
		</div>

		<div class="author-card">
			<img src="https://github.com/andrewozh.png" alt="Andrew Ozhegov" class="author-avatar" />
			<div class="author-info">
				<div class="author-label">{lang === 'sr' ? 'Направио' : 'Сделал'}</div>
				<div class="author-name">Andrew Ozhegov</div>
				<div class="author-links">
					<a href="https://github.com/andrewozh" target="_blank" title="GitHub">
						<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
					</a>
					<a href="https://t.me/andrewozh" target="_blank" title="Telegram">
						<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M11.944 0A12 12 0 000 12a12 12 0 0012 12 12 12 0 0012-12A12 12 0 0012.056 0h-.112zM17.5 7.39l-1.976 9.322c-.145.658-.537.818-1.092.508l-3.016-2.222-1.455 1.4c-.16.16-.295.295-.605.295l.213-3.054 5.56-5.022c.242-.213-.054-.334-.373-.12L8.32 13.617l-2.96-.924c-.64-.203-.658-.64.136-.95l11.566-4.458c.537-.194 1.006.13.832.95l.005.054z"/></svg>
					</a>
					<a href="https://andrewozh.github.io" target="_blank" title="Website">
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg>
					</a>
				</div>
			</div>
		</div>


	</div>
</div>

<style>
	.page { height: 100%; display: flex; flex-direction: column; }
	.scroll-area { flex: 1; overflow: auto; padding: 24px 16px; }

	.about-hero { text-align: center; padding: 16px 0 28px; }
	.about-icon {
		margin: 0 auto 14px;
		display: flex;
		justify-content: center;
	}
	.about-name { font-size: 20px; font-weight: 500; letter-spacing: -0.3px; }
	.about-version { font-size: 12px; color: var(--ink3); font-family: var(--font-mono); margin-top: 4px; }

	.alpha-warning {
		font-size: 12px; color: var(--wrong); text-align: center;
		line-height: 1.5; padding: 10px 16px; margin-bottom: 16px;
		border-radius: 12px; background: var(--wrong-wash);
	}
	.about-card {
		background: var(--surface);
		border-radius: 18px;
		border: 0.5px solid var(--hairline);
		margin-bottom: 18px;
		overflow: hidden;
	}
	.about-row {
		padding: 14px 16px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 12px;
		border-bottom: 0.5px solid var(--hairline);
	}
	.about-row-last { border-bottom: none; }
	.about-row-clickable { cursor: pointer; }
	.about-row-clickable:active { background: var(--surface2); }
	.about-row-sub { padding-left: 32px; background: var(--surface2); }
	.about-val-group { display: flex; align-items: center; gap: 6px; }
	.about-val-group span:not(.about-val) {
		font-family: var(--font-mono); font-size: 10px;
		padding: 1px 5px; border-radius: 4px;
	}
	.tag-new { background: #e8f5e8; color: #2d6a2d; }
	.tag-changed { background: #fdf3dc; color: #8b6914; }
	.tag-removed { background: #fce8e8; color: #aa3333; }
	.about-label { font-size: 13px; color: var(--ink3); }
	.about-val { font-size: 13px; color: var(--ink); font-family: var(--font-mono); text-align: right; }
	.about-link { font-size: 13px; color: var(--accent); font-family: var(--font-mono); text-decoration: none; }

	/* Author card */
	.author-card {
		background: var(--surface);
		border-radius: 18px;
		border: 0.5px solid var(--hairline);
		margin-bottom: 18px;
		padding: 20px;
		display: flex;
		align-items: center;
		gap: 16px;
	}
	.author-avatar {
		width: 72px; height: 72px; border-radius: 50%;
		border: 2px solid var(--hairline);
		flex-shrink: 0;
	}
	.author-info { flex: 1; }
	.author-label {
		font-family: var(--font-mono); font-size: 10px;
		color: var(--ink3); letter-spacing: 1px;
		text-transform: uppercase; margin-bottom: 2px;
	}
	.author-name {
		font-size: 16px; font-weight: 600;
		letter-spacing: -0.2px; margin-bottom: 8px;
	}
	.author-links {
		display: flex; gap: 12px;
	}
	.author-links a {
		color: var(--ink3);
		transition: color 0.15s;
		display: flex; align-items: center;
	}
	.author-links a:hover { color: var(--accent); }


</style>
