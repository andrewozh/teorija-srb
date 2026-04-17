.PHONY: help install download parse answers stats validate clean clean-images clean-all

SRC = source_17042026

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip3 install pymupdf pikepdf

BASE_URL = http://prezentacije.mup.gov.rs/usp/Vozacki%20ispit

download: ## Download source PDFs from official sources
	mkdir -p $(SRC)
	wget -nc -P $(SRC) "$(BASE_URL)/1.Uvodno%20objasnjenje/Objasnjenje%20ispitnih%20zadataka%20PDF.pdf"
	wget -nc -P $(SRC) "$(BASE_URL)/2.Pravila%20saobracaja/Pravila%20saobracaja%20PDF.pdf"
	wget -nc -P $(SRC) "$(BASE_URL)/3.Saobracajna%20signalizacija/Saobracajna%20signalizacija%20PDF.pdf"
	wget -nc -P $(SRC) "$(BASE_URL)/4.Vozaci/Vozaci%20PDF.pdf"
	wget -nc -P $(SRC) "$(BASE_URL)/5.Vozila/Vozila%20PDF.pdf"
	wget -nc -P $(SRC) "$(BASE_URL)/6.Osnove%20bezbednosti%20saobracaja%20i%20pojmovi/Osnove%20bezbednosti%20saobracaja%20i%20pojmovi%20i%20izrazi%20PDF.pdf"
	wget -nc -P $(SRC) "$(BASE_URL)/7.Posebne%20mere%20i%20ovlascenja/Posebne%20mere%20i%20ovlascenja%20PDF.pdf"
	wget -nc -P $(SRC) "$(BASE_URL)/8.Posledice%20nepostovanja%20propisa/Posledice%20nepostovanja%20propisa%20PDF.pdf"
	wget -nc -P $(SRC) "$(BASE_URL)/Objasnjenje%20izmene%20ispitnih%20pitanja%20PDF.pdf"
	wget -nc -P $(SRC) "https://autoskolasljivic.com/wp-content/uploads/2020/09/SVA-PITANJA-sa-resenjima.pdf"

parse: ## Parse questions PDF into questions.json + images/
	python3 parse_v3.py

answers: ## Extract correct answers and merge into questions.json
	python3 extract_answers.py

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
	print(f'Answers:       {sum(1 for q in qs if \"correct_answers\" in q)}/{len(qs)}'); \
	print(f'Removed:       {sum(1 for q in qs if q.get(\"is_removed\"))}'); \
	print(f'Changed:       {sum(1 for q in qs if q.get(\"is_changed\"))}'); \
	print(f'New:           {sum(1 for q in qs if q.get(\"is_new\"))}'); \
	"

validate: ## Validate questions.json integrity
	@python3 -c " \
	import json, sys; \
	d = json.load(open('questions.json')); qs = d['questions']; errs = 0; \
	sections = {}; \
	[sections.setdefault(q.get('section','?'), []).append(q['id']) for q in qs]; \
	[print(f'  {s}: {len(ids)} questions, IDs {min(ids)}-{max(ids)}') for s, ids in sorted(sections.items())]; \
	dups = [(s, len(ids)-len(set(ids))) for s, ids in sections.items() if len(ids) != len(set(ids))]; \
	[print(f'❌ Duplicate IDs in {s}: {n}') for s, n in dups]; errs += len(dups); \
	no_opts = [(q.get('section'), q['id']) for q in qs if len(q['options']) == 0]; \
	[print(f'⚠️  No options: {no_opts[:10]}') for _ in [1] if no_opts]; \
	[print(f'✅ {len(qs)} questions across {len(sections)} sections') for _ in [1] if not errs]; \
	sys.exit(1 if errs else 0); \
	"

clean: ## Remove generated output (keeps source PDFs and images)
	rm -f questions.json

clean-images: ## Remove extracted images
	rm -rf images/

clean-all: clean clean-images ## Remove all generated files
