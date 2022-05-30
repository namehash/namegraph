# Usage

The application can be run with

```
python ./utils/generator.py
```

It will generate suggestions for the default query.

The default parameteras are defined in `conf/config.yaml`. Any of the parameters might be substituted with a path to the
parameter, with dot-seprated fragments, e.g.

```
python ./utils/generator.py generator.query=firepower
```

will substitute the default query with the provided one.

The parameters are documented in the config.
