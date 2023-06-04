from serving.outlet import abstract_outlet as ao


def new_outlet(configs):
    return RedisOutlet(configs)

# TODO(): might not be the best way to use redis.ConnectionPool
class RedisOutlet(ao.AbstractOutlet):
    """Redis Outlet
    Required:
        host:
        port: by default, set to 6379
    Optional:
        db: by default, set to 5
        nx: by default, if nx and px all not given, set to 5
        px:
    """

    def __init__(self, configs):
        self.pool = None
        super().__init__(configs)
        self.nx = configs.get('nx')
        self.px = configs.get('px')
        if self.nx is None and self.px is None:
            self.nx = 5

    def _init_outlet(self):
        import redis
        conf_host = self.configs.get('host')
        if conf_host is None:
            conf_host = 'localhost'
        conf_port = self.configs.get('port')
        if conf_port is None:
            conf_port = 6379
        conf_db = self.configs.get('db')
        if conf_db is None:
            conf_db = 5
        self.pool = redis.ConnectionPool(host=conf_host, port=conf_port, db=conf_db)
        self.outlet_object = redis.Redis(connection_pool=self.pool)

    def post_result(self, task, data):
        self.outlet_object.set(task.task_id, data, nx=self.nx, px=self.px)
