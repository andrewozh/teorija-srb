<script lang="ts">
	import type { Snippet } from 'svelte';

	let { tone = 'neutral', size = 'sm', children }: {
		tone?: 'neutral' | 'accent' | 'correct' | 'wrong';
		size?: 'xs' | 'sm';
		children: Snippet;
	} = $props();
</script>

<span class="tag tag-{tone} tag-{size}">
	{@render children()}
</span>

<style>
	.tag {
		border-radius: 999px;
		font-family: var(--font-mono);
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.5px;
		display: inline-flex;
		align-items: center;
		gap: 4px;
	}
	.tag-sm { padding: 4px 9px; font-size: 10px; }
	.tag-xs { padding: 3px 7px; font-size: 9px; }
	.tag-neutral { background: var(--neutral); color: var(--ink2); }
	.tag-accent { background: var(--accent-wash); color: var(--accent); }
	.tag-correct { background: var(--correct-wash); color: var(--correct); }
	.tag-wrong { background: var(--wrong-wash); color: var(--wrong); }
</style>
