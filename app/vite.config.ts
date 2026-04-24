import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { execSync } from 'node:child_process';

function getAppVersion(): string {
	try {
		// Get the latest tag reachable from HEAD
		const tag = execSync('git describe --tags --abbrev=0', { encoding: 'utf-8' }).trim();
		// Check if HEAD itself is tagged
		const headTags = execSync('git tag --points-at HEAD', { encoding: 'utf-8' }).trim();
		if (headTags.split('\n').includes(tag)) {
			// HEAD is tagged — clean version
			return tag;
		}
		// HEAD is ahead of tag — append short hash before -beta
		const hash = execSync('git rev-parse --short HEAD', { encoding: 'utf-8' }).trim();
		if (tag.endsWith('-beta')) {
			return tag.replace(/-beta$/, `-${hash}-beta`);
		}
		return `${tag}-${hash}`;
	} catch {
		// No tags at all — fallback
		try {
			const hash = execSync('git rev-parse --short HEAD', { encoding: 'utf-8' }).trim();
			return `0.0.0-${hash}-beta`;
		} catch {
			return '0.0.0-dev';
		}
	}
}

export default defineConfig({
	plugins: [sveltekit()],
	define: {
		__APP_VERSION__: JSON.stringify(getAppVersion())
	}
});
