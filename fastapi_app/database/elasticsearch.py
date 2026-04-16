from elasticsearch import AsyncElasticsearch
import os


ES_URL = os.getenv('ELASTICSEARCH_URL')
ES_TICKERS_MAPPING = {
    "properties": {
        "symbol": {"type": "keyword"},
        "name": {"type": "text"},
    }
}


es = AsyncElasticsearch(hosts=[ES_URL])


async def get_es_client() -> AsyncElasticsearch:
    return es