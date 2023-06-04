from serving.outlet import abstract_outlet as ao


def new_outlet(configs):
    return SyncOutlet(configs)

class SyncOutlet(ao.AbstractOutlet):
    def _init_outlet(self):
        self.outlet_object = self.configs['queue']

    def post_result(self, task, data):
        self.outlet_object.put({task.task_id: data})
