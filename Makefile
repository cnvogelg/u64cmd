all:
	pip3 install -r dev_req.txt
	pip3 install -e .

format:
	black .

release:
	python3 -m build

upload: release
	twine upload dist/*

clean:
	rm -rf dist