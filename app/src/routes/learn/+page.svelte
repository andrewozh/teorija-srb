<script lang="ts">
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { loadQuestions, getSrsStats, getSrsSessionQuestions } from '$lib/data.js';
	import {
		getSettings,
		updateSettings,
		subscribe
	} from '$lib/store.js';
	import type { Lang, Question, QuestionsData } from '$lib/types.js';
	import Header from '$lib/components/Header.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import QuestionCarousel from '$lib/components/QuestionCarousel.svelte';

	let lang = $state<Lang>(getSettings().lang);
	let count = $state(getSettings().learnCount || 20);
	let learned = $state(0);
	let review = $state(0);
	let learning = $state(0);
	let newCount = $state(0);
	let data = $state<QuestionsData | null>(null);
	let sessionQuestions = $state<Question[]>([]);
	let inSession = $state(false);

	async function refreshStats() {
		if (!data) return;
		const stats = getSrsStats(data);
		learned = stats.learned;
		review = stats.review;
		learning = stats.learning;
		newCount = stats.newCount;
	}

	onMount(async () => {
		data = await loadQuestions();
		refreshStats();

		const unsub = subscribe(() => {
			lang = getSettings().lang;
		});
		return unsub;
	});

	function startSession() {
		if (!data) return;
		sessionQuestions = getSrsSessionQuestions(data, count);
		if (sessionQuestions.length > 0) {
			inSession = true;
		}
	}

	function endSession() {
		inSession = false;
		refreshStats();
	}
</script>

{#if inSession && sessionQuestions.length > 0}
<QuestionCarousel
	questions={sessionQuestions}
	headerTitle={lang === 'sr' ? 'СЕСИЈА' : 'СЕССИЯ'}
	onBack={endSession}
	onComplete={endSession}
/>
{:else}
<div class="page">
	<Header
		title={lang === 'sr' ? 'Препоручено' : 'Рекомендовано'}
		home
		onback={() => goto(`${base}/`)}
		onsettings={() => goto(`${base}/settings`)}
	/>
	<div class="scroll-area">
		<div class="label">{lang === 'sr' ? 'данашње стање' : 'текущее состояние'}</div>
		<div class="title">
			<span class="accent">{review}</span> {lang === 'sr' ? 'питања' : 'вопросов'}<br/>
			{lang === 'sr' ? 'чекају понављање.' : 'ждут повторения.'}
		</div>

		<!-- Stat strip -->
		<div class="stat-strip">
			{#each [
				{ v: learned, l: lang === 'sr' ? 'Научено' : 'Изучено' },
				{ v: review + learning, l: lang === 'sr' ? 'Понављање' : 'Повторение' },
				{ v: newCount, l: lang === 'sr' ? 'Ново' : 'Новые' },
			] as stat, i}
				{#if i > 0}<div class="stat-divider"></div>{/if}
				<div class="stat-item">
					<div class="stat-value">{stat.v}</div>
					<div class="stat-label">{stat.l}</div>
				</div>
			{/each}
		</div>

		<!-- Question count stepper -->
		<div class="stepper-card">
			<div class="stepper-header">
				<div class="stepper-title">{lang === 'sr' ? 'Питања по сесији' : 'Вопросов за сессию'}</div>
				<div class="stepper-value">{count}</div>
			</div>
			<div class="slider-wrap">
				<input
					type="range"
					min="20" max="60" step="10"
					bind:value={count}
					oninput={() => updateSettings({ learnCount: count })}
					class="slider"
				/>
			</div>
			<div class="slider-labels">
				<span>20</span><span>40</span><span>60</span>
			</div>
			<div class="estimate">
				~{Math.round(2700 / count)} {lang === 'sr' ? 'дана' : 'дней'}
				({Math.round(2700 / count / 7)} {lang === 'sr' ? 'нед.' : 'нед.'})
				<span class="estimate-hint">{lang === 'sr' ? 'при 2 сесије дневно' : 'при 2 сессиях в день'}</span>
			</div>
		</div>

		<!-- Algorithm explanation -->
		<div class="algo-card">
			<div class="algo-header">
				<Icon name="info" size={13} color="var(--accent)" stroke={1.8} />
				{lang === 'sr' ? 'АЛГОРИТАМ' : 'АЛГОРИТМ'}
			</div>
			<div class="algo-text">
				{lang === 'sr'
					? 'Спаја нова питања са онима која сте раније погрешили. Интервали понављања расту са сваким тачним одговором (1д · 3д · 7д · 21д).'
					: 'Объединяет новые вопросы с теми, на которые вы ранее ответили неправильно. Интервалы повторения растут с каждым правильным ответом (1д · 3д · 7д · 21д).'}
			</div>
		</div>

		<button class="start-btn" onclick={startSession}>
			{lang === 'sr' ? 'Почни сесију' : 'Начать сессию'} · {count} {lang === 'sr' ? 'питања' : 'вопросов'}
		</button>
	</div>
</div>
{/if}

<style>
	.page { height: 100%; display: flex; flex-direction: column; }
	.scroll-area { flex: 1; overflow: auto; padding: 20px 16px 24px; }

	.label {
		font-family: var(--font-mono); font-size: 10px; color: var(--ink3);
		letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px;
	}
	.title {
		font-size: 26px; font-weight: 500; letter-spacing: -0.4px;
		margin-bottom: 18px; line-height: 1.15;
	}
	.accent { color: var(--accent); }

	/* Stat strip */
	.stat-strip {
		background: var(--surface); border-radius: 18px;
		padding: 14px 16px; margin-bottom: 18px;
		display: flex; border: 0.5px solid var(--hairline);
	}
	.stat-divider { width: 0.5px; background: var(--hairline); }
	.stat-item { flex: 1; text-align: center; padding: 0 4px; }
	.stat-value {
		font-family: var(--font-mono); font-size: 20px;
		color: var(--ink); letter-spacing: -0.3px;
	}
	.stat-label { font-size: 11px; color: var(--ink3); margin-top: 2px; letter-spacing: 0.2px; }

	/* Stepper */
	.stepper-card {
		background: var(--surface); border-radius: 18px;
		padding: 16px 18px; border: 0.5px solid var(--hairline);
		margin-bottom: 14px;
	}
	.stepper-header {
		display: flex; justify-content: space-between;
		align-items: baseline; margin-bottom: 14px;
	}
	.stepper-title { font-size: 14px; font-weight: 500; }
	.stepper-value {
		font-family: var(--font-mono); font-size: 22px;
		color: var(--accent); letter-spacing: -0.3px;
	}
	.slider-wrap { padding: 0 2px; }
	.slider {
		width: 100%; height: 2px; -webkit-appearance: none; appearance: none;
		background: var(--neutral); border-radius: 2px; outline: none;
	}
	.slider::-webkit-slider-thumb {
		-webkit-appearance: none; appearance: none;
		width: 16px; height: 16px; border-radius: 8px;
		background: var(--accent); border: 3px solid var(--bg);
		box-shadow: 0 1px 3px rgba(0,0,0,0.2); cursor: pointer;
	}
	.slider-labels {
		display: flex; justify-content: space-between; margin-top: 8px;
		font-family: var(--font-mono); font-size: 10px; color: var(--ink3);
	}
	.estimate {
		margin-top: 12px; padding-top: 12px;
		border-top: 0.5px solid var(--hairline);
		font-family: var(--font-mono); font-size: 13px;
		color: var(--ink); letter-spacing: -0.2px;
	}
	.estimate-hint {
		font-size: 11px; color: var(--ink3); margin-left: 4px;
	}

	/* Algorithm card */
	.algo-card {
		padding: 16px 18px; border-radius: 18px;
		background: var(--accent-wash); margin-bottom: 18px;
	}
	.algo-header {
		display: flex; align-items: center; gap: 8px; margin-bottom: 6px;
		font-family: var(--font-mono); font-size: 10px; color: var(--accent);
		letter-spacing: 1px; text-transform: uppercase;
	}
	.algo-text { font-size: 13px; color: var(--ink); line-height: 1.5; }

	/* Start button */
	.start-btn {
		width: 100%; height: 54px; border-radius: 18px;
		background: var(--accent); color: var(--accent-ink); border: none;
		font-family: var(--font-ui); font-size: 15px; font-weight: 600;
		letter-spacing: -0.1px; cursor: pointer;
	}
</style>
