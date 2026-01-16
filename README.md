# PAC-Comp

A repository that houses my comp experiment that is based on the pac website and stats

---

## Description of Project

For this project, I am creating a scraping tool that collects its data directly from the PAC website. This makes the stats more accessible and easier to find. Initially, the project focuses on baseball, but it will be expanded to other sports later.  

The reason for this experiment is to address the difficulty of finding PAC stats in one place. The final outcome will be a tool that automatically collects stats from the PAC website and stores them in a database, making data access and discoverability much easier.  

By organizing all PAC stats into a single dataset, this project creates opportunities for analysis, comparison, and visualization. Coaches, players, and researchers can more easily track performance over multiple years, identify trends, and make data-driven decisions.

---

## Tools

- BeautifulSoup  
- Python  
- Selenium  
- Pandas  
- SQLAlchemy  
- Matplotlib  
- Streamlit  

---
## Notice

Everything was ran from terminal/VS Code

## Steps to Run
### 1. Make sure UV is installed, after run

```
uv init
```

### 2. Install Dependencies

After creating and activating your virtual environment, install the required packages:

```bash
pip install -r requirements.txt
```
Other options below

### Using Toml (use when in root location of toml)
```
pip install .
```
```
python -m pip install .
```
### 3. Scrape and Store data
```
uv run grabber.py
```
### 4. Website/player search creation
```
streamlit run seeker.py
```
## Success
You will know you have done everything correct if you greeted with a seach bar that lets you type playes stats in after running step 3. 


