PYTHON=python

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

data:
	$(PYTHON) src/augment_dataset.py

analysis:
	$(PYTHON) src/run_analysis.py

report:
	$(PYTHON) src/run_analysis.py

all: data analysis report

clean:
	rm -f data/processed/*.csv
	rm -f reports/figures/*.png
	rm -f reports/final_report.md
