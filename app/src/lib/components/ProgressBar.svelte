<script lang="ts">
	let { value, total, color, height = 3, showMeta = false, label = '', wrong = 0, recovering = 0 }: {
		value: number;
		total: number;
		color?: string;
		height?: number;
		showMeta?: boolean;
		label?: string;
		wrong?: number;
		recovering?: number;
	} = $props();

	let pctCorrect = $derived(total > 0 ? Math.min(100, (value / total) * 100) : 0);
	let pctRecovering = $derived(total > 0 ? Math.min(100 - pctCorrect, (recovering / total) * 100) : 0);
	let pctWrong = $derived(total > 0 ? Math.min(100 - pctCorrect - pctRecovering, (wrong / total) * 100) : 0);
	let c = $derived(color || 'var(--accent)');
	let isMulti = $derived(wrong > 0 || recovering > 0);
</script>

<div class="progress-wrap">
	{#if showMeta}
		<div class="progress-meta">
			<span>{label}</span>
			<span>{value}/{total}</span>
		</div>
	{/if}
	<div class="progress-track" style:height="{height}px" style:border-radius="{height}px">
		{#if isMulti}
			<div class="progress-fill" style:width="{pctCorrect + pctRecovering + pctWrong}%" style:background="var(--wrong)"></div>
			<div class="progress-fill" style:width="{pctCorrect + pctRecovering}%" style:background="var(--recovering)"></div>
			<div class="progress-fill" style:width="{pctCorrect}%" style:background="var(--correct)"></div>
		{:else}
			<div class="progress-fill" style:width="{pctCorrect}%" style:background={c}></div>
		{/if}
	</div>
</div>

<style>
	.progress-wrap { width: 100%; }
	.progress-meta {
		display: flex;
		justify-content: space-between;
		font-family: var(--font-mono);
		font-size: 10px;
		color: var(--ink3);
		margin-bottom: 6px;
		letter-spacing: 0.5px;
		text-transform: uppercase;
	}
	.progress-track {
		width: 100%;
		background: var(--neutral);
		overflow: hidden;
		position: relative;
	}
	.progress-fill {
		position: absolute;
		left: 0;
		top: 0;
		bottom: 0;
		transition: width 0.3s ease;
	}
</style>
