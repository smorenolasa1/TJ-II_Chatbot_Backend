python -m venv .venv

. .venv/bin/activate

./.venv/bin/pip install -r requirements.txt

./.venv/bin/python -m spacy download xx_sent_ud_sm
./.venv/bin/python -m spacy download es_core_news_sm

./.venv/bin/python database_downloader.py

./.venv/bin/python main.py