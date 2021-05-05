# flaskblog_dgraph
Implementation of [Corey Schafer's Flask Blog](https://www.youtube.com/playlist?list=PL-osiE80TeTs4UjLw5MM6OjgkjFeUxCYH) with DGraph as backend.

# Getting started

First clone repository, then install requirements:

```bash
pip install -r requirements.txt
```

Make sure dgraph is installed or you have an access to the cloud.
You can edit your dgraph settings either in `flaskblog/config.py` or in `flaskblog/config.py`
The default settings are:

```python
DGRAPH_ENDPOINT = "localhost:9080"
DGRAPH_CREDENTIALS = None
DGRAPH_OPTIONS = None
```

Then you can import the schema to your instance of dgraph. Just copy the contents of `schema.dgraph` and paste it to your schema declaration. 

Make sure you are in the repository root folder and now you can run the app via:

```
python run.py
```

# Disclaimer

This is a repository for learning and education purposes. I do not claim any credit in the design of the flaskblog, it belongs to [CoreyMS](https://coreyms.com/). The only part was developed by me is the DGraph class and the corresponding functions. I share this code, because it might be useful for others. Friendly pull requests, issues and forks are welcome. 


# Todos

- Tags for posts
- Category for posts
- Template to list user posts / categories
- Search function