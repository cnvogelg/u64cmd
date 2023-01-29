all:
	pip install -r dev_req.txt
	pip install -e .

format:
	black .
