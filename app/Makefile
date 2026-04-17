.PHONY: help install dev build preview deploy clean sync-data

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	npm install

dev: ## Start dev server
	npm run dev -- --open

build: sync-data ## Build static site for production
	npm run build

preview: build ## Preview production build locally
	npm run preview -- --open

deploy: build ## Deploy to GitHub Pages
	npx gh-pages -d build --nojekyll

clean: ## Remove build output
	rm -rf build .svelte-kit

sync-data: ## Copy latest database to static/
	cp ../database/questions.json static/
	rm -rf static/images
	cp -r ../database/images static/
