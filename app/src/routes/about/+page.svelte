<script lang="ts">
	import { base } from '$app/paths';
	import { getSettings, subscribe } from '$lib/store.js';
	import { t } from '$lib/i18n.js';
	import type { Lang } from '$lib/types.js';
	import Header from '$lib/components/Header.svelte';
	import Icon from '$lib/components/Icon.svelte';

	let lang = $state<Lang>(getSettings().lang);

	$effect(() => {
		const unsub = subscribe(() => { lang = getSettings().lang; });
		return unsub;
	});
</script>

<div class="page">
	<Header title={t('settings.about', lang)} settings={false} onback={() => history.back()} />

	<div class="scroll-area">
		<div class="about-hero">
			<div class="about-icon">
				<img src="{base}/icon-192.png" alt="Teorija" width="96" height="96" style="border-radius: 22px; box-shadow: 0 2px 12px rgba(0,0,0,0.25), 0 0 0 0.5px var(--hairline);" />
			</div>
			<div class="about-name">Teorija</div>
			<div class="about-version">0.1.1-alpha</div>
		</div>

		<div class="alpha-warning">
			⚠️ {lang === 'sr'
				? 'Алфа верзија — апликација је у развоју и није у потпуности тестирана. Могу постојати грешке у преводу и одговорима.'
				: 'Альфа-версия — приложение в разработке и не полностью протестировано. Возможны ошибки в переводе и ответах.'}
		</div>

		<div class="about-card">
			<div class="about-row">
				<span class="about-label">{lang === 'sr' ? 'База ажурирана' : 'База обновлена'}</span>
				<span class="about-val">12. април 2026.</span>
			</div>
			<div class="about-row">
				<span class="about-label">{lang === 'sr' ? 'Број питања' : 'Кол-во вопросов'}</span>
				<span class="about-val">1,780</span>
			</div>
			<div class="about-row">
				<span class="about-label">{lang === 'sr' ? 'Извор питања' : 'Источник'}</span>
				<span class="about-val">АМСС →</span>
			</div>
			<div class="about-row about-row-last">
				<span class="about-label">{lang === 'sr' ? 'Извор одговора' : 'Ответы'}</span>
				<span class="about-val">АМСС →</span>
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
	.about-label { font-size: 13px; color: var(--ink3); }
	.about-val { font-size: 13px; color: var(--ink); font-family: var(--font-mono); text-align: right; }

	.coffee-btn {
		width: 100%; height: 52px; border-radius: 16px;
		background: var(--surface); color: var(--ink);
		border: 1px solid var(--hairline);
		font-family: var(--font-ui); font-size: 14px; font-weight: 500;
		cursor: pointer;
		display: flex; align-items: center; justify-content: center; gap: 8px;
	}
</style>
