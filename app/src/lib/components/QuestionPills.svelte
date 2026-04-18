<script lang="ts">
	let { current, states, onclick }: {
		current: number;
		states: string[];
		onclick?: (index: number) => void;
	} = $props();

	let scrollEl = $state<HTMLDivElement | undefined>(undefined);

	$effect(() => {
		if (scrollEl && current >= 0) {
			const active = scrollEl.querySelector('[data-active="true"]') as HTMLElement;
			if (active) {
				const l = active.offsetLeft - scrollEl.offsetWidth / 2 + active.offsetWidth / 2;
				scrollEl.scrollTo({ left: l, behavior: 'instant' });
			}
		}
	});
</script>

<div class="pills-row" bind:this={scrollEl}>
	{#each states as state, i}
		{@const isCur = i === current}
		<button
			class="pill"
			class:pill-current={isCur}
			class:pill-correct={!isCur && state === 'correct'}
			class:pill-wrong={!isCur && state === 'wrong'}
			class:pill-unanswered={!isCur && state !== 'correct' && state !== 'wrong'}
			data-active={isCur}
			onclick={() => onclick?.(i)}
		>
			{String(i + 1).padStart(2, '0')}
		</button>
	{/each}
</div>

<style>
	.pills-row {
		display: flex;
		gap: 6px;
		padding: 6px 16px 7px;
		overflow-x: auto;
		scrollbar-width: none;
		border-bottom: 0.5px solid var(--hairline);
		flex-shrink: 0;
	}
	.pills-row::-webkit-scrollbar { display: none; }

	.pill {
		flex-shrink: 0;
		min-width: 36px;
		height: 30px;
		padding: 0 10px;
		border-radius: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-family: var(--font-mono);
		font-size: 12px;
		font-weight: 500;
		letter-spacing: 0.3px;
		cursor: pointer;
		border: 0.5px solid var(--hairline);
	}
	.pill-current {
		background: var(--ink);
		color: var(--bg);
		border-color: transparent;
	}
	.pill-correct {
		background: var(--correct-wash);
		color: var(--correct);
	}
	.pill-wrong {
		background: var(--wrong-wash);
		color: var(--wrong);
	}
	.pill-unanswered {
		background: var(--surface2);
		color: var(--ink3);
	}
</style>
