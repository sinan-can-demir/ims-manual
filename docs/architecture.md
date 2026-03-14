# Project Architecture Design Notes

## 3/14/2026

I ran the test api for `post/api/products` (create product route) and it works. This shows the following pipeline is working successfully.

```bash
Client
 ↓
FastAPI Router
 ↓
Schema validation
 ↓
Service layer
 ↓
SQLAlchemy ORM
 ↓
Postgres container
 ↓
Commit success
 ↓
Response returned
```