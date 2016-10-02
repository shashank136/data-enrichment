# Usage :
python main.py


# Superlist Bulk import Preprocessor

This project is a part of Step 2 of our Directory Listing project. Here we pre process all the scrapped entry to make it meaningful for us. 

This pre processing script that will run before data is fed inside WP All Import plugin. This pre processing script will convert input data into a format that is compatible with Superlist.

Also this script will help us in decreasing manual effort of our Operations team, thus saving a lot of time and causing less number of errors.

# Running Python script in background:

```python
python <filename>.py &

```
## Running Python script in background and directing the console messages to log file:

```python
python <filename>.py > {datetime}.log 2>&1 &
```

* Specifically tested on linux systems
* In our case substitute \<filename> with main
