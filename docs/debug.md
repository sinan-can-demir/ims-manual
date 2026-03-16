# Debug Notes

This document tracks debugging issues encountered during development and their solutions.

## 3/14/2026

### BUG #1

[x] sqlalchemy.exc.CompileError: PostgreSQL ENUM type requires a name.

- This is a very common SQLAlchemy + PostgreSQL Enum issue. PostgreSQL requires names for Enums but SQLAlchemy doesn't create them unless you make it.
    
- To solve this we added this to `app/models/inventory_event.py`
    
```py
    event_type = Column(
    Enum(EventType, name="event_type_enum"),
    nullable=False)
```

This solves the problm, docker composes up successfully.

## 3/15/2026

### BUG #1

[?] `test_scripts/test_sc.sh` had a bug that couses an internal server errpr

- the error points the product creation:

```bash
Waiting for API to start...
Testing POST /api/products
Status: 500
Body: Internal Server Error
FAIL: Create product
```

- The very first thing to do is to run:

```bash 
docker logs ims_api
```

the output:

```bash
DETAIL:  Key (sku)=(test-sku) already exists.

[SQL: INSERT INTO products (name, sku) VALUES (%(name)s, %(sku)s) RETURNING products.id, products.created_at]
[parameters: {'name': 'test-product', 'sku': 'test-sku'}]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
```

- This shows that I already used the sku `test-sku` and this variable is unique.

- To prevent duplicates I added:

```bash
SKU="test-sku-$(date +%s)"
```

- This ensures that the test SKU will have a unique number following this pattern test-sku-XXXXX

[✓] Status: Solved. The test doesn't signal SKU errors now.

### BUG #2

- Inventory didn't update for test script `test_scripts/test_sc.sh`

- The error code:

```bash
Inventory response: {"product_id":9,"inventory":50}
FAIL: Expected inventory 50, got null
```
- ChatGPT said actual api response didn't match with the test script

- I replaced this

```bash
quantity=$(echo "$inventory" | jq -r '.quantity')
```

with this:

```bash
quantity=$(echo "$inventory" | jq -r '.inventory')
```

- Sent the code to chatgpt to have it fixed for the entire test

- The test passed.

[✓] Status: Solved. All the tests run successfully now.

## 3/16/2026

### BUG #1: Alembic Migration bug

- This bug happened because I ran the command in fedora terminal not in the docker

```bash
sinan@fedora:~/Desktop/projects/ims-manual$ alembic revision --autogenerate -m "initial schema"
Traceback (most recent call last):
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/engine/base.py", line 143, in __init__
    self._dbapi_connection = engine.raw_connection()
                             ~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/engine/base.py", line 3317, in raw_connection
    return self.pool.connect()
           ~~~~~~~~~~~~~~~~~^^
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/pool/base.py", line 448, in connect
    return _ConnectionFairy._checkout(self)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/pool/base.py", line 1272, in _checkout
    fairy = _ConnectionRecord.checkout(pool)
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/pool/base.py", line 712, in checkout
    rec = pool._do_get()
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/pool/impl.py", line 306, in _do_get
    return self._create_connection()
           ~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/pool/base.py", line 389, in _create_connection
    return _ConnectionRecord(self)
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/pool/base.py", line 674, in __init__
    self.__connect()
    ~~~~~~~~~~~~~~^^
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/pool/base.py", line 900, in __connect
    with util.safe_reraise():
         ~~~~~~~~~~~~~~~~~^^
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/util/langhelpers.py", line 121, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/pool/base.py", line 896, in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/engine/create.py", line 667, in connect
    return dialect.connect(*cargs_tup, **cparams)
           ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/engine/default.py", line 630, in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)  # type: ignore[no-any-return]  # NOQA: E501
           ~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/usr/lib64/python3.14/site-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
psycopg2.OperationalError: could not translate host name "db" to address: Name or service not known


The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/sinan/.local/bin/alembic", line 8, in <module>
    sys.exit(main())
             ~~~~^^
  File "/home/sinan/.local/lib/python3.14/site-packages/alembic/config.py", line 1047, in main
    CommandLine(prog=prog).main(argv=argv)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "/home/sinan/.local/lib/python3.14/site-packages/alembic/config.py", line 1037, in main
    self.run_cmd(cfg, options)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/home/sinan/.local/lib/python3.14/site-packages/alembic/config.py", line 971, in run_cmd
    fn(
    ~~^
        config,
        ^^^^^^^
        *[getattr(options, k, None) for k in positional],
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        **{k: getattr(options, k, None) for k in kwarg},
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/sinan/.local/lib/python3.14/site-packages/alembic/command.py", line 309, in revision
    script_directory.run_env()
    ~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/home/sinan/.local/lib/python3.14/site-packages/alembic/script/base.py", line 545, in run_env
    util.load_python_file(self.dir, "env.py")
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/home/sinan/.local/lib/python3.14/site-packages/alembic/util/pyfiles.py", line 116, in load_python_file
    module = load_module_py(module_id, path)
  File "/home/sinan/.local/lib/python3.14/site-packages/alembic/util/pyfiles.py", line 136, in load_module_py
    spec.loader.exec_module(module)  # type: ignore
    ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
  File "<frozen importlib._bootstrap_external>", line 759, in exec_module
  File "<frozen importlib._bootstrap>", line 491, in _call_with_frames_removed
  File "/home/sinan/Desktop/projects/ims-manual/migrations/env.py", line 80, in <module>
    run_migrations_online()
    ~~~~~~~~~~~~~~~~~~~~~^^
  File "/home/sinan/Desktop/projects/ims-manual/migrations/env.py", line 68, in run_migrations_online
    with connectable.connect() as connection:
         ~~~~~~~~~~~~~~~~~~~^^
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/engine/base.py", line 3293, in connect
    return self._connection_cls(self)
           ~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/engine/base.py", line 145, in __init__
    Connection._handle_dbapi_exception_noconnection(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        err, dialect, engine
        ^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/engine/base.py", line 2448, in _handle_dbapi_exception_noconnection
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/engine/base.py", line 143, in __init__
    self._dbapi_connection = engine.raw_connection()
                             ~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/engine/base.py", line 3317, in raw_connection
    return self.pool.connect()
           ~~~~~~~~~~~~~~~~~^^
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/pool/base.py", line 448, in connect
    return _ConnectionFairy._checkout(self)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/pool/base.py", line 1272, in _checkout
    fairy = _ConnectionRecord.checkout(pool)
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/pool/base.py", line 712, in checkout
    rec = pool._do_get()
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/pool/impl.py", line 306, in _do_get
    return self._create_connection()
           ~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/pool/base.py", line 389, in _create_connection
    return _ConnectionRecord(self)
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/pool/base.py", line 674, in __init__
    self.__connect()
    ~~~~~~~~~~~~~~^^
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/pool/base.py", line 900, in __connect
    with util.safe_reraise():
         ~~~~~~~~~~~~~~~~~^^
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/util/langhelpers.py", line 121, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/pool/base.py", line 896, in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/engine/create.py", line 667, in connect
    return dialect.connect(*cargs_tup, **cparams)
           ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib64/python3.14/site-packages/sqlalchemy/engine/default.py", line 630, in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)  # type: ignore[no-any-return]  # NOQA: E501
           ~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/usr/lib64/python3.14/site-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not translate host name "db" to address: Name or service not known

(Background on this error at: https://sqlalche.me/e/20/e3q8)
```

### Solution

- I changed the sqlurl in `alembic.ini` to this:

```ini
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/ims
```

The migration command was executed on the host machine.
Docker service names like "db" are only resolvable inside the docker network.

Therefore the connection URL must use localhost instead of db.

[✓] Status: Solved. The migrations run successfully.