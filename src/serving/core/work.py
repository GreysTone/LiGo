"""
  Core.Work

  Contact: arthur.r.song@gmail.com
"""

import hashlib

from serving.core import debug
from serving.core import config
from serving.core import exception
from serving.core import regulator
from serving.core.memory import WORK_FACTORY, WORK


@debug.flow("core.create_work")
def create_work(configs):
    #TODO: check whether work is already exist
    #TODO: let system run with work
    whash = _generate_work_hash(configs['wtype'], configs['configs'])
    work = WORK_FACTORY[configs['wtype']].new_work(
        whash=whash,
        wtype=configs['wtype'],
        configs=configs['configs'],
        links=configs['link']
    )
    WORK[whash] = work
    return {'code': 0, 'msg': whash}

def _generate_work_hash(wtype, configs):
    hash_string = "{}{}".format(wtype, configs)
    return 'W'+hashlib.md5(hash_string.encode('utf-8')).hexdigest()

@debug.flow("core.delete_work")
@regulator.validate(regulator.work_whash)
def delete_work(configs):
    stop_work(configs)
    if config.exist_persist_work(configs['whash']):
        disable_work(configs)
    del WORK[configs['whash']]
    return {'code': 0, 'msg': configs['whash']}

@debug.flow("core.list_all_works")
def list_all_works(configs):
    _work = []
    for w in WORK:
        ret = WORK[w].report()
        #ret['configs'] = json.dumps(ret['configs'])
        _work.append(ret)
    return {'works': _work}

@debug.flow("core.inspect_work")
@regulator.validate(regulator.work_whash)
def inspect_work(configs):
    w = WORK.get(configs['whash'])
    if w is None:
        raise exception.ParamValidationError(": invalid work id")
    return w.report()

@debug.flow("core.enable_work")
@regulator.validate(regulator.work_whash)
def enable_work(configs):
    w = WORK.get(configs['whash'])
    if w is None:
        raise exception.ParamValidationError(": invalid work id")
    return w.enable_persist()

@debug.flow("core.disable_work")
@regulator.validate(regulator.work_whash)
def disable_work(configs):
    w = WORK.get(configs['whash'])
    if w is None:
        raise exception.ParamValidationError(": invalid work id")
    return w.disable_persist()

@debug.flow("core.run_work")
@regulator.validate(regulator.work_whash)
def run_work(configs):
    w = WORK.get(configs['whash'])
    if w is None:
        raise exception.ParamValidationError(": invalid work id")
    w.run()
    return {'code': 0, 'msg': configs['whash']}

@debug.flow("core.stop_work")
@regulator.validate(regulator.work_whash)
def stop_work(configs):
    w = WORK.get(configs['whash'])
    if w is None:
        raise exception.ParamValidationError(": invalid work id")
    w.stop()
    return {'code': 0, 'msg': configs['whash']}
