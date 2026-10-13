# Source Code & Repositories

**Project Name:** Bluestock Mutual Fund Analytics Platform  
**Author:** Manish Kumar (B23082@students.iitmandi.ac.in)  
**GitHub Repository:** [https://github.com/Manish-66/BlueStock](https://github.com/Manish-66/BlueStock)  

### Commit History
- **Day 1 Commit (`1c5457d`):** `"Day 1: Data ingestion complete"`
- **Day 2 Commit (`11683b0`):** `"Day 2: Cleaned data + SQLite DB loaded"`

### Python Modules
1. `data_ingestion.py`: Ingestion, schema inspection, referential integrity check.
2. `live_nav_fetch.py`: Automated `mfapi.in` API ingestion for HDFC Top 100 + 5 major bluechip schemes.
3. `data_cleaning.py`: Missing values imputation, forward filling, daily return computation, and type normalization.
4. `load_db.py`: SQLAlchemy database builder populating SQLite relational database (`bluestock_mf.db`).
5. `sql/schema.sql`: 10-table normalized Star Schema DDL.
6. `sql/queries.sql`: 10 analytical SQL queries.
7. `notebooks/`: Interactive Jupyter exploration and cleaning notebooks (`01_data_ingestion.ipynb`, `02_data_cleaning.ipynb`).
