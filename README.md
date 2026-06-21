# bio_papers_recommend

## 论文爬取
命令行操作 
```python
python -m crwaling.crawler [--keywords KEYWORDS [KEYWORDS ...]] [--max-results MAX_RESULTS] [--output OUTPUT]
```
默认对爬取得到的json文件转换为xlsx。如果需要单独输入json文件，将其转化为xlsx文件
```python
python -m crawling.crawler [--input-json INPUT]
```

## 论文解析
论文解析
```python
python content_parsing\main.py [--input-json INPUT] [--db-path DB_PATH]
```

查询结果
```python
python content_parsing\query_papers.py
```