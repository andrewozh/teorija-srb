<script lang="ts">
	import { base } from '$app/paths';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { loadQuestions, getSections, getQuestionsBySection } from '$lib/data.js';
	import { getQuestionProgress, getMistakeStatus, getMistakeQuestionKeys, subscribe, getSettings, updateSettings } from '$lib/store.js';
	import { sectionName } from '$lib/i18n.js';
	import type { Lang, SectionMeta } from '$lib/types.js';
	import Icon from './Icon.svelte';

	let lang = $state<Lang>(getSettings().lang);
	let category = $state(getSettings().category);
	let sections = $state<SectionMeta[]>([]);
	let sectionPct = $state<Record<string, number>>({});
	let mistakeCount = $state(0);
	let currentPath = $derived($page.url.pathname);

	const nav = [
		{ key: 'home',     path: `${base}/`,           label_sr: 'Почетна',    label_ru: 'Главная',    icon: 'home' },
		{ key: 'learn',    path: `${base}/learn`,      label_sr: 'Препоручено', label_ru: 'Обучение',  icon: 'bolt' },
		{ key: 'practice', path: `${base}/practice`,   label_sr: 'Учење',      label_ru: 'Учебник',    icon: 'book' },
		{ key: 'exam',     path: `${base}/exam`,       label_sr: 'Испит',      label_ru: 'Экзамен',    icon: 'target' },
		{ key: 'stats',    path: `${base}/statistics`, label_sr: 'Статистика', label_ru: 'Статистика', icon: 'chart' },
		{ key: 'mistakes', path: `${base}/mistakes`,   label_sr: 'Грешке',     label_ru: 'Ошибки',     icon: 'flag' },
	];

	function isActive(navPath: string): boolean {
		if (navPath === `${base}/`) return currentPath === navPath;
		return currentPath.startsWith(navPath);
	}

	let _data: any = null;

	function recalc() {
		lang = getSettings().lang;
		category = getSettings().category;
		mistakeCount = getMistakeQuestionKeys().length;
		if (!_data) return;
		for (const s of sections) {
			const qs = getQuestionsBySection(_data, s.id);
			if (qs.length === 0) { sectionPct[s.id] = 0; continue; }
			let correct = 0;
			for (const q of qs) {
				const prog = getQuestionProgress(q.section, q.id);
				const m = getMistakeStatus(q.section, q.id);
				if (prog && m === 'none' && prog.correct > 0) correct++;
			}
			sectionPct[s.id] = Math.round((correct / qs.length) * 100);
		}
	}

	onMount(async () => {
		_data = await loadQuestions();
		sections = getSections(_data);
		recalc();
		const unsub = subscribe(recalc);
		return unsub;
	});
</script>

<nav class="sidebar">
	<div class="sidebar-brand">
		<img src="{base}/icon-192.png" alt="Teorija" class="brand-icon" />
		<div class="brand-text">
			<div class="brand-name">Teorija</div>
			<div class="brand-sub">возачки испит · {category}</div>
		</div>
	</div>

	<div class="sidebar-nav">
		{#each nav as item}
			{@const active = isActive(item.path)}
			<a href={item.path} class="nav-item" class:nav-active={active}>
				<Icon name={item.icon} size={17} color={active ? 'var(--ink)' : 'var(--ink2)'} stroke={1.6} />
				<span class="nav-label">{lang === 'sr' ? item.label_sr : item.label_ru}</span>
				{#if item.key === 'mistakes' && mistakeCount > 0}
					<span class="nav-badge">{mistakeCount}</span>
				{/if}
			</a>
		{/each}

		{#if sections.length > 0}
			<div class="sections-label">{lang === 'sr' ? 'Области' : 'Разделы'}</div>
			{#each sections as s, i}
				<a href="{base}/practice/{s.id}" class="section-item" class:nav-active={currentPath.includes(s.id)} style:opacity={sectionPct[s.id] === 0 ? 0.45 : 1}>
					<span class="section-num">{i + 1}</span>
					<span class="section-name">{sectionName(s.id, lang)}</span>
					<span class="section-pct">{sectionPct[s.id] || 0}%</span>
				</a>
			{/each}
		{/if}
	</div>

	<div class="sidebar-footer">
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<div class="nav-item lang-toggle" onclick={() => updateSettings({ lang: lang === 'sr' ? 'ru' : 'sr' })}>
			<Icon name="language" size={16} color="var(--ink3)" stroke={1.5} />
			<span class="nav-label">{lang === 'sr' ? 'Језик' : 'Язык'}</span>
		</div>
		<a href="{base}/settings" class="nav-item" class:nav-active={currentPath.includes('settings')}>
			<Icon name="settings" size={16} color="var(--ink3)" stroke={1.5} />
			<span class="nav-label">{lang === 'sr' ? 'Подешавања' : 'Настройки'}</span>
		</a>
	</div>
</nav>

<style>
	.sidebar {
		width: 240px;
		height: 100dvh;
		position: sticky;
		top: 0;
		display: flex;
		flex-direction: column;
		background: var(--surface2);
		border-right: 1px solid var(--hairline);
		flex-shrink: 0;
		overflow: hidden;
	}

	.sidebar-brand {
		padding: 20px 20px 14px;
		display: flex;
		align-items: center;
		gap: 10px;
	}
	.brand-icon {
		width: 32px; height: 32px; border-radius: 9px;
		flex-shrink: 0;
		object-fit: cover;
	}
	.brand-name { font-size: 14px; font-weight: 600; color: var(--ink); letter-spacing: -0.1px; }
	.brand-sub {
		font-family: var(--font-mono); font-size: 10px;
		color: var(--ink3); letter-spacing: 0.5px; text-transform: uppercase;
	}

	.sidebar-nav {
		flex: 1; padding: 8px 12px; overflow-y: auto;
		display: flex; flex-direction: column; gap: 1px;
	}

	.nav-item {
		display: flex; align-items: center; gap: 12px;
		padding: 9px 12px; border-radius: 10px;
		color: var(--ink2); text-decoration: none;
		font-size: 13.5px; letter-spacing: -0.1px;
		transition: background 0.1s;
	}
	.nav-item:hover { background: var(--surface); }
	.nav-active {
		background: var(--surface) !important;
		color: var(--ink);
		font-weight: 500;
		box-shadow: 0 1px 2px rgba(0,0,0,0.04);
	}
	.nav-label { flex: 1; }
	.nav-badge {
		font-family: var(--font-mono); font-size: 10px;
		padding: 2px 7px; background: var(--wrong-wash);
		color: var(--wrong); border-radius: 6px; letter-spacing: 0.3px;
	}

	.sections-label {
		font-family: var(--font-mono); font-size: 9px;
		color: var(--ink3); letter-spacing: 1.2px;
		text-transform: uppercase; padding: 20px 12px 6px;
	}

	.section-item {
		display: flex; align-items: center; gap: 10px;
		padding: 6px 12px; border-radius: 8px;
		text-decoration: none; color: var(--ink2);
		transition: background 0.1s;
	}
	.section-item:hover { background: var(--surface); }
	.section-num {
		width: 18px; height: 18px; border-radius: 5px;
		background: var(--surface); color: var(--ink3);
		display: flex; align-items: center; justify-content: center;
		font-family: var(--font-mono); font-size: 9px;
		border: 0.5px solid var(--hairline);
	}
	.section-name {
		flex: 1; font-size: 12px; overflow: hidden;
		text-overflow: ellipsis; white-space: nowrap;
	}
	.section-pct {
		font-family: var(--font-mono); font-size: 9px;
		color: var(--ink3); letter-spacing: 0.2px;
	}

	.sidebar-footer {
		padding: 8px 12px 12px;
		border-top: 1px solid var(--hairline);
	}
	.lang-toggle {
		cursor: pointer;
	}
</style>
