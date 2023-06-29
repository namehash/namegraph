

def get_names_script(limit_names=100) -> str:
    return f"params['_source'].data.names.stream()" \
          + f".limit({limit_names})" \
          + ".map(p -> p.normalized_name)" \
          + ".collect(Collectors.toList())"

def get_namehashes_script(limit_names=100) -> str:
    return f"params['_source'].data.names.stream()" \
          + f".limit({limit_names})" \
          + ".map(p -> p.normalized_name)" \
          + ".collect(Collectors.toList())"
