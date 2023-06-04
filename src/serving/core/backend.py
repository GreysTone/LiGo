"""
  Core.Backend: Backend Manager

  Contact: arthur.r.song@gmail.com
"""

import logging

from serving.core import debug
from serving.core import exception
from serving.core import regulator
from serving.core.memory import BACKEND, BACKEND_FACTORY


@debug.flow("core.supported_backend")
def supported_backend():
    loaded = []
    for key in BACKEND_FACTORY:
        loaded.append(key)
    return ', '.join(loaded)

@debug.flow("core.create_backend")
def create_backend(configs):
    b = BACKEND_FACTORY[configs['btype']].new_backend(configs)
    BACKEND[b.hash()] = b
    return {'code': 0, 'msg': b.hash()}

@debug.flow("core.delete_backend")
def delete_backend(configs):
    stop_backend(configs)
    #if configs.exist_persist_backend(configs['bhash']):
    #    disable_backend(configs)
    del BACKEND[configs['bhash']]
    return {'code': 0, 'msg': configs['bhash']}

@debug.flow("core.list_all_backends")
def list_all_backends():
    status_list = []
    for h in BACKEND:
        status_list.append(inspect_backend({'bhash': h}))
    return {'backends': status_list}

@debug.flow("core.inspect_backend")
def inspect_backend(configs):
    b = BACKEND.get(configs['bhash'])
    if b is None:
        raise exception.ParamValidationError(": invalid backend id")
    return b.report()

@debug.flow("core.enable_backend")
def enable_backend(configs):
    b = BACKEND.get(configs['bhash'])
    if b is None:
        raise exception.ParamValidationError(": invalid backend id")
    return b.enable_persist()

@debug.flow("core.disable_backend")
def disable_backend(configs):
    b = BACKEND.get(configs['bhash'])
    if b is None:
        raise exception.ParamValidationError(": invalid backend id")
    return b.disable_persist()

@debug.flow("core.run_backend")
def run_backend(configs):
    b = BACKEND.get(configs['bhash'])
    if b is None:
        raise exception.ParamValidationError(": invalid backend id")
    return b.run()

@debug.flow("core.stop_backend")
def stop_backend(configs):
    b = BACKEND.get(configs['bhash'])
    if b is None:
        raise exception.ParamValidationError(": invalid backend id")
    return b.stop()

@debug.flow("core.reload_model_on_backend")
@regulator.validate(regulator.backend_bid)
@regulator.validate(regulator.backend_load)
def reload_model_on_backend(configs):
    """Load or reload a model on a specific backend

    Required field:
        bid: backend id
        model:
            implhash: hash value of labels, head, bone, impl and version
            OR labels, head, bone, impl and version
        encrypted: encrypted model, either 1 or 0, otherwise regard as 0
        a64key: if encrypted model, provide access code
        pvtkey: if encrypted model, provide decrypt private key path
    Optional field:
        model:
            modelext: preserved, not use
    """
    raise NotImplementedError()
    """
    logging.debug("   configs: %s", configs)
    backend_instance = BACKEND.get(configs['bid'])
    if backend_instance is None:
        raise exception.ReloadModelOnBackendError
    backend_instance.load(configs)
    return {'code': 0, 'msg': str(configs['bid'])}
    """

@debug.flow("core.terminate_backend")
@regulator.validate(regulator.backend_bid)
def terminate_backend(configs):
    """Terminate the given backend

    Required field:
        bid: backend id
    """
    raise NotImplementedError()
    """
    logging.debug("   configs: %s", configs)
    backend_instance = BACKEND.get(configs['bid'])
    if backend_instance is None:
        raise exception.ParamValidationError(": invalid backend id")
    backend_instance.terminate()
    del BACKEND[configs['bid']]
    try:
        numeric_id = int(configs['bid'])
        BACKEND_SLOT[numeric_id] = False
    except ValueError:
        logging.debug("given backend id is not inside SLOT")
    return {'code': 0, 'msg': str(configs['bid'])}
    """

@debug.flow("core.append_outlet")
@regulator.validate(regulator.backend_bid)
@regulator.validate(regulator.backend_append_outlet)
def append_outlet(configs):
    raise NotImplementedError()
    """
    outlet_instance = outlet.outlet_factory(configs['type'], configs['configs'])
    backend_instance = BACKEND.get(configs['bid'])
    if backend_instance is None:
        raise exception.ParamValidationError(": invalid backend id")
    ret = backend_instance.append_outlet({'instance': outlet_instance})
    logging.debug("append outlet to %s(%s): %s", configs['bid'], backend_instance, outlet_instance)
    return {'code': 0, 'msg': ret}
    """

@debug.flow("core.list_all_outlets")
@regulator.validate(regulator.backend_bid)
def list_all_outlets(configs):
    raise NotImplementedError()
    """
    backend_instance = BACKEND.get(configs['bid'])
    if backend_instance is None:
        raise exception.ParamValidationError(": invalid backend id")
    status_list = backend_instance.list_outlets()
    return {'outlets': status_list}
    """

@debug.flow("core.remove_outlet")
@regulator.validate(regulator.backend_bid)
@regulator.validate(regulator.backend_remove_outlet)
def remove_outlet(configs):
    raise NotImplementedError()
    """
    backend_instance = BACKEND.get(configs['bid'])
    if backend_instance is None:
        raise exception.ParamValidationError(": invalid backend id")
    backend_instance.remove_outlet(configs['key'])
    return {'code': 0, 'msg':""}
    """

@debug.flow("core.create_and_load_model")
@regulator.validate(regulator.outlets_option)
def create_and_load_model(configs):
    """One function call to create backend and load model

    Required field:
        backend:
            impl: backend implementation (e.g. `tensorflow.frozen`)
        model:
            implhash: hash value of labels, head, bone, impl and version
            OR labels, head, bone, impl and version
        encrypted: encrypted model, either 1 or 0, otherwise regard as 0
        a64key: if encrypted model, provide access code
        pvtkey: if encrypted model, provide decrypt private key path
    Optional field:
        backend:
            storage: preserved, not use
            preheat: preserved, not use
            batchsize: inference batch size
            inferprocnum: inference process number
            exporter: preserved, not use (e.g. `redis`)
            backendext: preserved
        model:
            modelext: preserved, not use
    """
    pass
    """
    logging.debug("   configs: %s", configs)
    created_backend_bid = None
    try:
        backend_request = configs.get('backend')
        if BACKEND.get(backend_request.get('bid')) is not None:
            logging.warning("ignore the given bid and create a new one")
        ret = initialize_backend(backend_request)
        created_backend_bid = ret['msg']
        configs['bid'] = created_backend_bid
        for out_conf in configs['outlets']:
            out_conf['bid'] = created_backend_bid
            append_outlet(out_conf)
        return reload_model_on_backend(configs)
    except exception.LiGoException as err:
        if created_backend_bid is not None:
            terminate_backend({'bid': created_backend_bid})
        raise err
    """
