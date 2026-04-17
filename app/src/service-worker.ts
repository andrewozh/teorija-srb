/// <reference types="@sveltejs/kit" />
/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />

import { build, files, version } from '$service-worker';

const sw = self as unknown as ServiceWorkerGlobalScope;

const CACHE_NAME = `driving-exam-v${version}`;

// App shell: built JS/CSS files
const APP_SHELL = build;

// Static files: images, questions.json, etc.
const STATIC_FILES = files;

// All resources to cache
const ALL_ASSETS = [...APP_SHELL, ...STATIC_FILES];

sw.addEventListener('install', (event) => {
	event.waitUntil(
		caches
			.open(CACHE_NAME)
			.then((cache) => {
				// Cache app shell immediately, static files progressively
				return cache.addAll(APP_SHELL);
			})
			.then(() => {
				sw.skipWaiting();
			})
	);
});

sw.addEventListener('activate', (event) => {
	event.waitUntil(
		caches
			.keys()
			.then((keys) => {
				return Promise.all(
					keys
						.filter((key) => key !== CACHE_NAME)
						.map((key) => caches.delete(key))
				);
			})
			.then(() => {
				sw.clients.claim();
			})
	);
});

sw.addEventListener('fetch', (event) => {
	const url = new URL(event.request.url);

	// Only handle same-origin requests
	if (url.origin !== location.origin) return;

	// For navigation requests, serve the app shell
	if (event.request.mode === 'navigate') {
		event.respondWith(
			caches.match('/index.html').then((cached) => {
				return cached || fetch(event.request);
			})
		);
		return;
	}

	// Cache-first for built assets and static files
	event.respondWith(
		caches.match(event.request).then((cached) => {
			if (cached) return cached;

			return fetch(event.request).then((response) => {
				// Cache successful responses for static assets
				if (response.ok && (url.pathname.startsWith('/images/') || url.pathname === '/questions.json')) {
					const clone = response.clone();
					caches.open(CACHE_NAME).then((cache) => {
						cache.put(event.request, clone);
					});
				}
				return response;
			});
		})
	);
});
