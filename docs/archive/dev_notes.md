# Developer Notes

This file serves as a reference and informal documentation

## 3/13/2026

Today, I learned the difference between service, api and schema layers. I implemented my first schema for fastapi in `app/schemas/product.py` file. It consists of 2 components:
  - `ProductCreate`
  - `ProductResponse`

The layer of the project as follows:

```bash
Client (HTTP request)
      ↓
API / Router
      ↓
Service Layer
      ↓
Database / Models
```

I implemented a service layer. In `app/services/product_service.py`. it contains the business logic.  

**Key note**: The routers don't need to import models. They should remain separate.

Now, we have a working minimal FASTAPI structure.

Next steps will be 
      - configuring `docker-compose.yml` file
      - setting up a postgresql db

for minimal start I use this configs

```yml
version: "3.9"

services:

  db:
    image: postgres:15
    container_name: ims_db
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: ims
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  api:
    build: .
    container_name: ims_api
    depends_on:
      - db
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  postgres_data:
```

Database url config in `app/database.py` must match the service name `db`.


## Bugs

After the build attempts I encountered following bugs:
```bash
sinan@fedora:~/Desktop/projects/ims-manual$ docker compose up --build
WARN[0000] /home/sinan/Desktop/projects/ims-manual/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion 
[+] up 17/17
 ✔ Image postgres:15 Pulled                                                                                                                                                              21.4s
[+] Building 0.3s (2/2) FINISHED                                                                                                                                                              
 => [internal] load local bake definitions                                                                                                                                               0.0s
 => => reading from stdin 524B                                                                                                                                                           0.0s
[+] up 17/18l] load build definition from Dockerfile                                                                                                                                     0.1s
 ✔ Image postgres:15    Pulled                                                                                                                                                           21.4s
 ⠙ Image ims-manual-api Building                                                                                                                                                         0.5s
failed to solve: failed to read dockerfile: open Dockerfile: no such file or directory
```

### solution:

[X] Change the configuration path for docker file to mach with actual Dockerfile path. 

```bash 
  api:
    build: 
      context: .
      dockerfile: docker/dockerfile
    container_name: ims_api
```
- Updated this section, still didn't work since I didn't actually create a `Dockerfile` :D

[X] Created Docker file with following configs

```
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

[X] Create requirements.txt file

 - The error is still raising.

!!!! [X] The mismatch in config name `docker/dockerfile` is the culprit here. I changed it to `docker/Dockerfile` and it is running now

### STATUS = SOLVED

-------

## App Path Bug- API doesn't load correctly (Module not found)

```bash
ims_api  | INFO:     Will watch for changes in these directories: ['/app']
ims_api  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
ims_api  | INFO:     Started reloader process [1] using WatchFiles
ims_api  | Process SpawnProcess-1:
ims_api  | Traceback (most recent call last):
ims_api  |   File "/usr/local/lib/python3.11/multiprocessing/process.py", line 314, in _bootstrap
ims_api  |     self.run()
ims_api  |   File "/usr/local/lib/python3.11/multiprocessing/process.py", line 108, in run
ims_api  |     self._target(*self._args, **self._kwargs)
ims_api  |   File "/usr/local/lib/python3.11/site-packages/uvicorn/_subprocess.py", line 80, in subprocess_started
ims_api  |     target(sockets=sockets)
ims_api  |   File "/usr/local/lib/python3.11/site-packages/uvicorn/server.py", line 75, in run
ims_api  |     return asyncio_run(self.serve(sockets=sockets), loop_factory=self.config.get_loop_factory())
ims_api  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ims_api  |   File "/usr/local/lib/python3.11/site-packages/uvicorn/_compat.py", line 30, in asyncio_run
ims_api  |     return runner.run(main)
ims_api  |            ^^^^^^^^^^^^^^^^
ims_api  |   File "/usr/local/lib/python3.11/asyncio/runners.py", line 118, in run
ims_api  |     return self._loop.run_until_complete(task)
ims_api  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ims_api  |   File "uvloop/loop.pyx", line 1518, in uvloop.loop.Loop.run_until_complete
ims_api  |   File "/usr/local/lib/python3.11/site-packages/uvicorn/server.py", line 79, in serve
ims_api  |     await self._serve(sockets)
ims_api  |   File "/usr/local/lib/python3.11/site-packages/uvicorn/server.py", line 86, in _serve
ims_api  |     config.load()
ims_api  |   File "/usr/local/lib/python3.11/site-packages/uvicorn/config.py", line 441, in load
ims_api  |     self.loaded_app = import_from_string(self.app)
ims_api  |                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ims_api  |   File "/usr/local/lib/python3.11/site-packages/uvicorn/importer.py", line 22, in import_from_string
ims_api  |     raise exc from None
ims_api  |   File "/usr/local/lib/python3.11/site-packages/uvicorn/importer.py", line 19, in import_from_string
ims_api  |     module = importlib.import_module(module_str)
ims_api  |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ims_api  |   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
ims_api  |     return _bootstrap._gcd_import(name[level:], package, level)
ims_api  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ims_api  |   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
ims_api  |   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
ims_api  |   File "<frozen importlib._bootstrap>", line 1126, in _find_and_load_unlocked
ims_api  |   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
ims_api  |   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
ims_api  |   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
ims_api  |   File "<frozen importlib._bootstrap>", line 1140, in _find_and_load_unlocked
ims_api  | ModuleNotFoundError: No module named 'app'
```

### solution

[X] `ENV PYTHONPATH=/app` added this line to `docker-compose.yml` but the result didn't change.

[X] I forgot to create module files `__init__.py` in each directory. 

```bash
touch app/__init__.py
touch app/api/__init__.py
touch app/models/__init__.py
touch app/schemas/__init__.py
touch app/services/__init__.py
```

I ran this block, created the modules. but the error remains unchanged.

[X] Volume Configuration is set to `.:app` it might overwrite all app directory. Try to rename it.

- change this`command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` 
  to this `command: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` in `docker-compose.yml` 

unfortunately this didn't work either.

[X] the API dockerfile path was `docker/Dockerfile` but it needed to be `./docker/Dockerfile`. Let's see if this is the problem.

- No, this wasn't the problem.

[?] Instead of running the app from `/app` let's run it inside the `app/app` directory.

```yml
api:
  build:
    context: .
    dockerfile: ./docker/Dockerfile
  container_name: ims_api
  depends_on:
    - db
  ports:
    - "8000:8000"
  volumes:
    - .:/app
  working_dir: /app/app
  command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
  ```

  - Let's try if this works.

  - When I built the docker, the api didn't break this time however said:

```bash
ims_api  | INFO:     Will watch for changes in these directories: ['/app/app']
ims_api  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
ims_api  | INFO:     Started reloader process [1] using WatchFiles
ims_api  | ERROR:    Error loading ASGI app. Could not import module "main".
```

  - this means docker found the directory but failed to import `main.py` module. I am actually close to debug the issue.

  - To find the issue I removed --reload command from api service command line: `command: uvicorn main:app --host 0.0.0.0 --port 8000`

```bash
ims_api  | ERROR:    Error loading ASGI app. Could not import module "main".
ims_api exited with code 1
```

  - I will now check the `app/main.py` file

[?] I changed `main.py` import paths from this

```py
from fastapi import FastAPI
from app.database import Base, engine
from app.models import product
from app.models import inventory_event
from app.api.products import router as products_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(products_router, prefix="/api")
```

to that

```py
from fastapi import FastAPI
from database import Base, engine
from models import product
from models import inventory_event
from api.products import router as products_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(products_router, prefix="/api")
```

Because apparently the config in `docker-compose.yml` make the modules relative to `main.py`

  - Let's run and see if it works.

  - It didn't work.

  - Recovered the old imports

  -> I will continue this later since I am tired now. I worked all night and now it is 8.19 am.

[?] the problem is working directory

  - the new configs

```yml
  api:
    build:
      context: .
      dockerfile: ./docker/Dockerfile
    container_name: ims_api
    depends_on:
      - db
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - PYTHONPATH=/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

```

- added this service with environment component, let's see if it works. 

- not working. I will add this command `command: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

- not working

[?] I run a sanity check in docker. This gave me the following results:

```py
root@0cb452a11494:/app# python
Python 3.11.15 (main, Mar  3 2026, 20:22:58) [GCC 14.2.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import sys
>>> print(sys.path)
['', '/app', '/usr/local/lib/python311.zip', '/usr/local/lib/python3.11', '/usr/local/lib/python3.11/lib-dynload', '/usr/local/lib/python3.11/site-packages']
>>> import app
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ModuleNotFoundError: No module named 'app'
>>> 
>>> import app
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ModuleNotFoundError: No module named 'app'
>>> 
```

- As we can see `/app` is a sys path however it is not importable as a *module*

[?] The issue can be a linux problem because I run this command in bash shell and it said the following:

```bash
root@10344b11c554:/app# ls
ls /app
ls /app/app
ls: cannot open directory '.': Permission denied
ls: cannot open directory '/app': Permission denied
ls: cannot open directory '/app/app': Permission denied
root@10344b11c554:/app# 
```

- When I sent the error to CHATGPT it said it is a linux permission problem which disables container access to host directories by default.

- to address this issue we add this block

```yml
api:
  build:
    context: .
    dockerfile: ./docker/Dockerfile
  container_name: ims_api
  depends_on:
    - db
  ports:
    - "8000:8000"
  volumes:
    - .:/app:Z
  working_dir: /app
  command: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  ```

- after Volumes: we add an uppercase Z as follows:
          - .:app:Z

- Let's see if it works now

- IT WORKED. This is a milestone since I see the application running.

- **The solution is the fedora access deny for container. IT needs to be configured in docker-compose.yml and usually with :Z in the end**

NOTE: Apparently this is a common bug on fedora so it is definitely useful to keep in mind. 

- Next time don't forget to run sanity checks in the container using shell.

-------

## 3/14/2026

Today I will implement the events. Events controls the changes. We don't wanna hardcode the changes, therefore the sum of events will give the total quantity.

First things first, I started by testing the container to see if it actually works and responses were as following:

```bash
ims_api  | INFO:     Will watch for changes in these directories: ['/app']
ims_api  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
ims_api  | INFO:     Started reloader process [1] using WatchFiles
ims_api  | INFO:     Started server process [9]
ims_api  | INFO:     Waiting for application startup.
ims_api  | INFO:     Application startup complete.
ims_api  | INFO:     172.18.0.1:40682 - "GET /docs HTTP/1.1" 200 OK
ims_api  | INFO:     172.18.0.1:40682 - "GET /openapi.json HTTP/1.1" 200 OK
ims_api  | INFO:     172.18.0.1:49230 - "POST /api/products HTTP/1.1" 200 OK
```

The Backend is successfully running.

Now, I start designing the architecture of events components. I added the inventory events apis and tested them they are working fine.

[X] need to add quantity restraint to sell and buy negative quantities. Inventory quantity however could be negative since it could be the issue if we get products damaged or perished.

I added an enum class to prevent possible typos,

I also added new event types such as return, damage and assignment

## 3/15/2026

I added event based inventory api. This unified all product and inventory related apis with one variable event. IT uses the enum I created yesterday. For details check architectrue notes.

I added a test_scripts directory to create test scripts in bash, since each time I don't wanna write the tests one by one or go to swagger to click execute :D this is more mature.

The entire pipeline of my IMS is working now. The testing script also runs automated tests.

## 3/16/2026

What We Will Do 

Today’s milestone: Phase 2 
- [✓] Install Alembic 
  - This part is pretty easy and it comes with preconfigurations, so all you have to do is match your db address and import your models.
  
  '''bash
  pip install alembic
  ```

- [✓] Initialize migrations 

  ```bash
  alembic init migrations
  ```

After a short bug I successfuly created a version

```py
"""initial schema

Revision ID: c173b45f6a16
Revises: 
Create Date: 2026-03-16 04:49:54.111472

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c173b45f6a16'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('inventory_events', 'event_type',
               existing_type=sa.VARCHAR(),
               type_=sa.Enum('PURCHASE', 'SALE', 'DAMAGE', 'ADJUSTMENT', 'RETURN', name='event_type_enum'),
               nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('inventory_events', 'event_type',
               existing_type=sa.Enum('PURCHASE', 'SALE', 'DAMAGE', 'ADJUSTMENT', 'RETURN', name='event_type_enum'),
               type_=sa.VARCHAR(),
               nullable=True)
    # ### end Alembic commands ###
```

- According to chatGPT this is not we should have at the moment. It said we initially have an empty database prior to inital migration. It recommends removing old tables and creating a fresh database.

- We also delete `Base.metadata.create_all(bind=engine)` line in `app/main.py` because once we use alembic we won't need this line again.

Now my alembic schema seems like this:

```py
"""initial schema

Revision ID: d6e00aa295e6
Revises: 
Create Date: 2026-03-16 05:05:56.154328

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6e00aa295e6'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('products',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('sku', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_index(op.f('ix_products_sku'), 'products', ['sku'], unique=True)
    op.create_table('inventory_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=True),
    sa.Column('event_type', sa.Enum('PURCHASE', 'SALE', 'DAMAGE', 'ADJUSTMENT', 'RETURN', name='event_type_enum'), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('inventory_state',
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.PrimaryKeyConstraint('product_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('inventory_state')
    op.drop_table('inventory_events')
    op.drop_index(op.f('ix_products_sku'), table_name='products')
    op.drop_index(op.f('ix_products_id'), table_name='products')
    op.drop_table('products')
    # ### end Alembic commands ###
```

This will create the tables instead of sqlalchemy.


- [✓] Create first migration 

The following creates the first migration.

```bash
alembic upgrade head
```

With this I ensure that it creates the files:

```bash
docker compose exec db psql -U postgres -d ims -c "\dt"
```

The output:

```bash
              List of relations
 Schema |       Name       | Type  |  Owner   
--------+------------------+-------+----------
 public | alembic_version  | table | postgres
 public | inventory_events | table | postgres
 public | inventory_state  | table | postgres
 public | products         | table | postgres
(4 rows)
```

- [✓] Document migration workflow

saved in `docs/migrations.md`

Todays Milestone: Complete!


## 3/19/2026

I decided to use in memory test DB because it will reset each time when we run the test and then remove it.

Today, we added concurrency safety, event replay features. 

Concurrency safety will ensure that two different transaction cannot be made on the same row. It is critical to keep data consistent.

Event replay will help with:

- Reconstructuring projection
- Testing/Debugging
- Replication: (in distributed systems)
- Auditing

These are essential for data analytics and development operations.


## 3/26/2026

I added tests for export functions. All of the passed except the following:

```bash
FAILED tests/test_export.py::test_incremental_export_only_new_events - AssertionError: Expected 1 new row, got 0
```

It doesn'y get a parameter as intended. I think it is a timestamp mismatch between postgresql and sqllite.

I made the changes in export service and then it got fixed. (lines 46/68-71/164)

The export pipeline now has full test coverage.