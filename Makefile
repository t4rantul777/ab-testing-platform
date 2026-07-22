.PHONY: install test figures app lint clean

install:
	pip install -e ".[dev]"

test:
	pytest

figures:
	python scripts/make_figures.py

app:
	streamlit run app/streamlit_app.py

clean:
	rm -rf .pytest_cache __pycache__ */__pycache__ */*/__pycache__ \
	       src/*.egg-info build dist experiments.db
