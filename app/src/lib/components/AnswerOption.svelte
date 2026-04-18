<script lang="ts">
	import Icon from './Icon.svelte';

	let { letter, text, state = 'idle', multi = true, onclick }: {
		letter: string;
		text: string;
		state?: 'idle' | 'selected' | 'correct' | 'wrong' | 'muted';
		multi?: boolean;
		onclick?: () => void;
	} = $props();
</script>

<button class="answer-option answer-{state}" onclick={onclick} class:multi>
	<div class="answer-dot" class:round={!multi}>
		{#if state === 'correct'}
			<Icon name="check" size={14} color="#fff" stroke={2.5} />
		{:else if state === 'wrong'}
			<Icon name="x" size={13} color="#fff" stroke={2.5} />
		{:else}
			{letter}
		{/if}
	</div>
	<div class="answer-text">{text}</div>
</button>

<style>
	.answer-option {
		display: flex;
		align-items: flex-start;
		gap: 12px;
		padding: 10px 12px;
		border-radius: 16px;
		background: var(--surface);
		border: 1px solid var(--hairline);
		cursor: pointer;
		transition: all 0.15s ease;
		text-align: left;
		width: 100%;
		font-family: var(--font-ui);
	}
	.answer-idle { background: var(--surface); border-color: var(--hairline); }
	.answer-selected { background: var(--accent-wash); border-color: var(--accent); }
	.answer-correct { background: var(--correct-wash); border-color: var(--correct); }
	.answer-wrong { background: var(--wrong-wash); border-color: var(--wrong); }
	.answer-muted { background: var(--surface); border-color: var(--hairline); }
	.answer-muted .answer-text { color: var(--ink3); }

	.answer-dot {
		width: 26px;
		height: 26px;
		border-radius: 6px;
		flex-shrink: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		font-family: var(--font-mono);
		font-size: 11px;
		font-weight: 500;
		margin-top: 1px;
		background: var(--surface2);
		color: var(--ink3);
		border: 1px solid var(--hairline);
	}
	.answer-dot.round { border-radius: 13px; }

	.answer-selected .answer-dot {
		background: var(--accent);
		color: var(--accent-ink);
		border-color: transparent;
	}
	.answer-correct .answer-dot {
		background: var(--correct);
		color: #fff;
		border-color: transparent;
	}
	.answer-wrong .answer-dot {
		background: var(--wrong);
		color: #fff;
		border-color: transparent;
	}

	.answer-text {
		flex: 1;
		font-size: 14px;
		color: var(--ink);
		line-height: 1.45;
		letter-spacing: -0.1px;
		padding-top: 4px;
	}
</style>
