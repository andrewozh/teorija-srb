<script lang="ts">
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { loadQuestions, getActiveQuestions } from '$lib/data.js';
	import {
		getTotalCompletedCount,
		getMistakeQuestionKeys,
		getPassedExamCount,
		getExams,
		subscribe,
		getSettings,
		importState,
		updateSettings,
		isOnboarded,
		setOnboarded
	} from '$lib/store.js';
	import { t } from '$lib/i18n.js';
	import type { Lang } from '$lib/types.js';
	import Header from '$lib/components/Header.svelte';
	import Icon from '$lib/components/Icon.svelte';

	let completed = $state(getTotalCompletedCount());
	let mistakeCount = $state(getMistakeQuestionKeys().length);
	let passedExams = $state(getPassedExamCount());
	let totalExams = $state(getExams().length);
	let lang = $state<Lang>(getSettings().lang);
	let totalQuestions = $state(2288);

	onMount(async () => {
		const data = await loadQuestions();
		totalQuestions = getActiveQuestions(data).length;
	});

	$effect(() => {
		const unsub = subscribe(async () => {
			completed = getTotalCompletedCount();
			mistakeCount = getMistakeQuestionKeys().length;
			passedExams = getPassedExamCount();
			totalExams = getExams().length;
			lang = getSettings().lang;
			onboarded = isOnboarded();
			// Recount when category changes
			const data = await loadQuestions();
			totalQuestions = getActiveQuestions(data).length;
		});
		return unsub;
	});

	let progressPercent = $derived(Math.round((completed / totalQuestions) * 100));
	let onboarded = $state(isOnboarded());
	let showHome = $derived(onboarded);

	function handleImport() {
		const input = document.createElement('input');
		input.type = 'file';
		input.accept = '.json';
		input.onchange = async () => {
			const file = input.files?.[0];
			if (!file) return;
			try {
				const text = await file.text();
				importState(text);
			} catch { /* ignore */ }
		};
		input.click();
	}
</script>

<div class="page">
	<Header
		title="Teorija"
		back={false}
		onsettings={() => goto(`${base}/settings`)}
	>
		{#snippet leading()}
			<button class="lang-btn" onclick={() => updateSettings({ lang: lang === 'sr' ? 'ru' : 'sr' })}>
				<Icon name="language" size={20} />
			</button>
		{/snippet}
	</Header>

	{#if showHome}
		<!-- HOME WITH PROGRESS -->
		<div class="scroll-area">
			<!-- Greeting -->
			<div class="greeting">
				<div class="greeting-label">
					{lang === 'sr' ? 'Добро дошли назад' : 'Добро пожаловать'}
				</div>
				<div class="greeting-title">
					{lang === 'sr' ? 'Спремни сте' : 'Вы готовы'}<br/>
					{lang === 'sr' ? 'за' : 'к'} <span class="accent-text">{progressPercent}%</span> {lang === 'sr' ? 'испита.' : 'экзамена.'}
				</div>
			</div>

			<!-- Hero card — assisted learning -->
			<a href="{base}/learn" class="hero-card">
				<div class="hero-top">
					<div>
						<div class="hero-label">{lang === 'sr' ? 'Данашња сесија' : 'Сегодняшняя сессия'}</div>
						<div class="hero-title">{lang === 'sr' ? 'Обучење' : 'Обучение'}</div>
						<div class="hero-sub">{getSettings().learnCount || 20} {lang === 'sr' ? 'питања по сесији' : 'вопросов за сессию'}</div>
					</div>
					<div class="hero-icon-wrap">
						<Icon name="bolt" size={20} color="var(--accent-ink)" stroke={2} />
					</div>
				</div>
				<div class="hero-bottom">
					<div class="hero-time">~{Math.round((getSettings().learnCount || 20) * 20 / 60)} {lang === 'sr' ? 'минута' : 'минут'}</div>
					<div class="hero-cta">
						{lang === 'sr' ? 'Почни' : 'Начать'} <Icon name="chev-right" size={14} color="var(--accent-ink)" />
					</div>
				</div>
			</a>

			<!-- Secondary cards -->
			<a href="{base}/practice" class="sec-card">
				<div class="sec-icon"><Icon name="book" size={18} stroke={1.6} /></div>
				<div class="sec-body">
					<div class="sec-title">{lang === 'sr' ? 'Сва питања' : 'Все вопросы'}</div>
					<div class="sec-sub">{lang === 'sr' ? '7 области' : '7 разделов'} · {totalQuestions} {lang === 'sr' ? 'питања' : 'вопросов'}</div>
				</div>
				<div class="sec-count">{progressPercent}%</div>
			</a>

			<a href="{base}/exam" class="sec-card">
				<div class="sec-icon"><Icon name="target" size={18} stroke={1.6} /></div>
				<div class="sec-body">
					<div class="sec-title">{t('home.exam', lang)}</div>
					<div class="sec-sub">{lang === 'sr' ? 'Симулација стварног теста' : 'Симуляция реального теста'}</div>
				</div>
				<div class="sec-count">{lang === 'sr' ? '41 питање' : '41 вопрос'}</div>
			</a>

			<!-- Mini row -->
			<div class="mini-row">
				<a href="{base}/mistakes" class="mini-card">
					<div class="mini-top">
						<Icon name="warn" size={18} color="var(--ink2)" stroke={1.6} />
						<Icon name="chev-right" size={14} color="var(--ink4)" stroke={2} />
					</div>
					<div class="mini-bottom">
						{#if mistakeCount > 0}
							<div class="mini-count">{mistakeCount}</div>
						{/if}
						<div class="mini-label" class:mini-label-push={mistakeCount === 0}>{t('home.mistakes', lang)}</div>
					</div>
				</a>
				<a href="{base}/statistics" class="mini-card">
					<div class="mini-top">
						<Icon name="chart" size={18} color="var(--ink2)" stroke={1.6} />
						<Icon name="chev-right" size={14} color="var(--ink4)" stroke={2} />
					</div>
					<div class="mini-bottom">
						<div class="mini-label mini-label-push">{t('home.stats', lang)}</div>
					</div>
				</a>
			</div>

			<!-- Footer -->
			<div class="home-footer">
				<a href="{base}/about">Teorija v0.8.1-beta</a>
			</div>
		</div>
	{:else}
		<!-- FIRST LAUNCH -->
		<div class="empty-state">
			<div class="empty-icon">
				<img src="{base}/icon-192.png" alt="Teorija" width="72" height="72" style="border-radius: 18px; box-shadow: 0 2px 12px rgba(0,0,0,0.25), 0 0 0 0.5px var(--hairline);" />
			</div>
			<div class="empty-title">
				{lang === 'sr' ? 'Добро дошли' : 'Добро пожаловать'}<br/>{lang === 'sr' ? 'у' : 'в'} Teorija <span class="beta-badge">beta</span>
			</div>
			<div class="empty-desc">
				{lang === 'sr'
					? '2315 питања из 7 области за полагање возачког испита. Ради офлајн. Сав напредак остаје на уређају.'
					: '2315 вопросов из 7 разделов для сдачи экзамена по вождению. Работает офлайн. Весь прогресс хранится на устройстве.'}
			</div>
	
			<div class="empty-actions">
				<button class="btn-primary-full" onclick={() => setOnboarded()}>
					{lang === 'sr' ? 'Започни учење' : 'Начать обучение'}
				</button>
				<button class="btn-outline-full" onclick={handleImport}>
					<Icon name="upload" size={16} stroke={1.6} />
					{lang === 'sr' ? 'Увези постојећи напредак' : 'Импортировать прогресс'}
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	.lang-btn {
		width: 36px; height: 36px; border-radius: 12px;
		border: none; background: transparent; color: var(--ink);
		display: flex; align-items: center; justify-content: center;
		cursor: pointer;
	}
	.page { height: 100%; display: flex; flex-direction: column; }
	.scroll-area { flex: 1; overflow: auto; padding: 20px 16px 24px; }

	/* Greeting */
	.greeting { padding: 4px 4px 20px; }
	.greeting-label {
		font-family: var(--font-mono);
		font-size: 10px;
		color: var(--ink3);
		letter-spacing: 1px;
		text-transform: uppercase;
		margin-bottom: 8px;
	}
	.greeting-title {
		font-family: var(--font-ui);
		font-size: 28px;
		font-weight: 500;
		letter-spacing: -0.6px;
		line-height: 1.1;
		color: var(--ink);
	}
	.accent-text { color: var(--accent); }

	/* Hero card */
	.hero-card {
		display: block;
		background: var(--accent);
		color: var(--accent-ink);
		border-radius: 22px;
		padding: 18px 18px 16px;
		margin-bottom: 18px;
		position: relative;
		overflow: hidden;
	}
	.hero-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
	.hero-label {
		font-family: var(--font-mono);
		font-size: 10px;
		letter-spacing: 1px;
		text-transform: uppercase;
		opacity: 0.65;
		margin-bottom: 6px;
	}
	.hero-title { font-size: 22px; font-weight: 500; letter-spacing: -0.4px; margin-bottom: 2px; }
	.hero-sub { font-size: 13px; opacity: 0.72; line-height: 1.4; }
	.hero-icon-wrap {
		width: 40px; height: 40px; border-radius: 12px;
		background: rgba(0,0,0,0.10);
		display: flex; align-items: center; justify-content: center;
		flex-shrink: 0;
	}
	.hero-bottom {
		display: flex; align-items: center; gap: 10px;
		margin-top: 18px; padding-top: 14px;
		border-top: 1px solid rgba(0,0,0,0.12);
	}
	.hero-time {
		font-family: var(--font-mono);
		font-size: 11px;
		letter-spacing: 0.5px;
		opacity: 0.7;
		flex: 1;
	}
	.hero-cta {
		font-size: 13px; font-weight: 600;
		display: flex; align-items: center; gap: 4px;
	}

	/* Secondary cards */
	.sec-card {
		display: flex;
		align-items: center;
		gap: 14px;
		background: var(--surface);
		border-radius: 18px;
		padding: 14px 16px;
		margin-bottom: 8px;
		border: 0.5px solid var(--hairline);
	}
	.sec-icon {
		width: 36px; height: 36px; border-radius: 11px;
		background: var(--surface2); color: var(--ink);
		display: flex; align-items: center; justify-content: center;
		flex-shrink: 0;
	}
	.sec-body { flex: 1; min-width: 0; }
	.sec-title { font-size: 15px; font-weight: 500; letter-spacing: -0.1px; }
	.sec-sub { font-size: 12px; color: var(--ink3); margin-top: 2px; }
	.sec-count { font-family: var(--font-mono); font-size: 11px; color: var(--ink3); letter-spacing: 0.3px; flex-shrink: 0; }

	/* Mini row */
	.mini-row { display: flex; gap: 8px; margin-top: 14px; }
	.mini-card {
		flex: 1;
		background: var(--surface);
		border-radius: 18px;
		padding: 14px;
		border: 0.5px solid var(--hairline);
		display: flex;
		flex-direction: column;
		gap: 16px;
	}
	.mini-top { display: flex; justify-content: space-between; align-items: center; }
	.mini-bottom {}
	.mini-count { font-family: var(--font-mono); font-size: 22px; letter-spacing: -0.5px; color: var(--ink); }
	.mini-label { font-size: 12px; color: var(--ink3); }
	.mini-label-push { margin-top: 18px; }

	/* Footer */
	.home-footer {
		margin-top: 20px;
		padding: 14px 4px;
		text-align: center;
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--ink3);
		letter-spacing: 0.3px;
	}

	/* Empty state */
	.empty-state {
		flex: 1;
		padding: 40px 24px;
		display: flex;
		flex-direction: column;
	}
	.empty-icon {
		display: flex; align-items: center; justify-content: center;
		margin: 28px auto 26px;
	}
	.empty-title {
		font-size: 26px; font-weight: 500; letter-spacing: -0.4px;
		text-align: center; line-height: 1.15; margin-bottom: 10px;
	}
	.empty-desc {
		font-size: 14px; color: var(--ink2); text-align: center;
		line-height: 1.5; margin-bottom: 36px; padding: 0 12px;
	}
	.alpha-warning {
		font-size: 12px; color: var(--wrong); text-align: center;
		line-height: 1.5; padding: 10px 16px; margin: 0 12px 20px;
		border-radius: 12px; background: var(--wrong-wash);
	}
	.empty-actions {
		margin-top: auto;
		display: flex;
		flex-direction: column;
		gap: 10px;
	}
	.btn-primary-full {
		display: flex; align-items: center; justify-content: center;
		background: var(--accent); color: var(--accent-ink); border: none;
		height: 52px; border-radius: 16px;
		font-family: var(--font-ui); font-size: 15px; font-weight: 600;
		letter-spacing: -0.1px; cursor: pointer;
	}
	.btn-outline-full {
		display: flex; align-items: center; justify-content: center; gap: 8px;
		background: transparent; color: var(--ink);
		border: 1px solid var(--hairline);
		height: 52px; border-radius: 16px;
		font-family: var(--font-ui); font-size: 14px; font-weight: 500;
		letter-spacing: -0.1px; cursor: pointer;
	}
</style>
