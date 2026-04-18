<script lang="ts">
	let { value, total, color, height = 3, showMeta = false, label = '' }: {
		value: number;
		total: number;
		color?: string;
		height?: number;
		showMeta?: boolean;
		label?: string;
	} = $props();

	let pct = $derived(total > 0 ? Math.min(100, (value / total) * 100) : 0);
	let c = $derived(color || 'var(--accent)');
</script>

<div class="progress-wrap">
	{#if showMeta}
		<div class="progress-meta">
			<span>{label}</span>
			<span>{value}/{total}</span>
		</div>
	{/if}
	<div class="progress-track" style:height="{height}px" style:border-radius="{height}px">
		<div class="progress-fill" style:width="{pct}%" style:background={c} style:border-radius="{height}px"></div>
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
