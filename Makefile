all:
	pip3 install -r dev_req.txt
	pip3 install -e .

format:
	black .

build:
	python3 -m build

clean:
	rm -rf dist