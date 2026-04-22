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
			<div class="about-version">0.2.0</div>
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
			<div class="about-row">
				<span class="about-label">{lang === 'sr' ? 'Политика приватности' : 'Политика конфиденциальности'}</span>
				<span class="about-val">→</span>
			</div>
			<div class="about-row about-row-last">
				<span class="about-label">{lang === 'sr' ? 'Отворени код' : 'Открытый код'}</span>
				<span class="about-val">GitHub →</span>
			</div>
		</div>

		<button class="coffee-btn">
			<Icon name="coffee" size={16} stroke={1.6} />
			{lang === 'sr' ? 'Купи ми кафу' : 'Купи мне кофе'}
		</button>
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

	.coffee-btn {
		width: 100%; height: 52px; border-radius: 16px;
		background: var(--surface); color: var(--ink);
		border: 1px solid var(--hairline);
		font-family: var(--font-ui); font-size: 14px; font-weight: 500;
		cursor: pointer;
		display: flex; align-items: center; justify-content: center; gap: 8px;
	}
</style>
