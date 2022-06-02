class OpenseaAPI():
    def __init__(self, config: dict) -> None:
        self.api = config['OPENSEA_API_URL']
        self.key = config['OPENSEA_API_KEY']
        self.collection_endpoint = 'collection'
        self.stats_endpoint= 'stats'

    def urljoin(*parts: str) -> str:
        base = self.api
        for part in filter(None, parts):
            base = '{}/{}'.format(base.rstrip('/'), part.lstrip('/'))
        return base

    def get_collection(self, slugLstr ) -> tuple:
        url = self.urljoin(self.collection_endpoint, slug)
        headers = {"X-API-KEY": self.key, "Accept": "application/json"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            LOGGER.error(f'Problems with opensea -> code: {response.status_code}')
            return (False, None, None)
        name = response.json()['collection']['name']
        stats =  response.json()['collection']
        return (True, name, stats)

    def get_collection_stats(self, slug: str) -> dict:
        url = self.urljoin(self.collection_endpoint, slug)
        headers = {"X-API-KEY": self.key, "Accept": "application/json"}
        response = requests.get(url, headers=headers)
        LOGGER.info(f'Code {response.status_code} - {url}')
        return response.json()['collection']

    def get_collection_stats(name):
        url = self.urljoin(self.stats_endpoint, slug)
        headers = {"X-API-KEY": self.key, "Accept": "application/json"}
        code = 429
        LOGGER.info(f'Code {code} - {url}')
        while code  == 429:
            response = requests.get(url, headers=headers)
            code = response.status_code
            if code == 429:
                logger.info(f'gooing to sleep for 30')
                time.sleep(30)

        if code == 200:
            ok = True
            stats = response.json()['stats']
        else:
            ok = False
            stats = None

