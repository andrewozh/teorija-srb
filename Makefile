.PHONY: help install parse stats validate clean clean-images clean-all

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip3 install --break-system-packages pymupdf

parse: ## Parse PDF into questions.json + images/
	python3 parse_v3.py

stats: ## Show stats for parsed questions
	@python3 -c " \
	import json; \
	d = json.load(open('questions.json')); qs = d['questions']; \
	print(f'Total:         {len(qs)}'); \
	print(f'Good:          {sum(1 for q in qs if len(q[\"options\"]) >= 2 and len(q[\"text\"]) > 10)} ({sum(1 for q in qs if len(q[\"options\"]) >= 2 and len(q[\"text\"]) > 10)*100//len(qs)}%)'); \
	print(f'No options:    {sum(1 for q in qs if len(q[\"options\"]) == 0)}'); \
	print(f'With images:   {sum(1 for q in qs if q[\"has_image\"])}'); \
	print(f'Multi-answer:  {sum(1 for q in qs if q[\"correct_answers_count\"] > 1)}'); \
	print(f'Categories:    {sum(1 for q in qs if \"categories\" in q)}'); \
	print(f'2 pts / 3 pts: {sum(1 for q in qs if q[\"points\"]==2)} / {sum(1 for q in qs if q[\"points\"]==3)}'); \
	"

validate: ## Validate questions.json integrity
	@python3 -c " \
	import json, sys; \
	d = json.load(open('questions.json')); qs = d['questions']; \
	ids = [q['id'] for q in qs]; errs = 0; \
	dups = len(ids) - len(set(ids)); \
	[print('❌ Duplicate IDs found') or setattr(sys, '_e', 1) for _ in [1] if dups]; \
	missing = sorted(set(range(1, max(ids)+1)) - set(ids)); \
	[print(f'❌ Missing IDs: {missing[:20]}') for _ in [1] if missing]; \
	errs = dups + len(missing); \
	no_opts = [q['id'] for q in qs if len(q['options']) == 0]; \
	[print(f'⚠️  No options: {no_opts[:20]}') for _ in [1] if no_opts]; \
	no_text = [q['id'] for q in qs if len(q['text']) <= 10]; \
	[print(f'⚠️  Short text: {no_text[:20]}') for _ in [1] if no_text]; \
	[print(f'✅ All {len(qs)} questions valid, IDs 1-{max(ids)} complete') for _ in [1] if not errs]; \
	sys.exit(1 if errs else 0); \
	"

clean: ## Remove generated output (keeps PDFs and images)
	rm -f questions.json

clean-images: ## Remove extracted images
	rm -rf images/

clean-all: clean clean-images ## Remove all generated files
