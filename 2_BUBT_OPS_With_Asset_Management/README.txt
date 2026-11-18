BUBT-OPS - Full Starter Project
================================
Requirements: Python 3.9+ (Tkinter is usually included with Python)
Database: SQLite (built into Python)
Run: python main.py

Features:
- Dashboard
- Asset Management: Add, View, Search, Update, Delete
- Asset operations automatically create Asset Configuration History records
- Settings with persistent left sidebar and one visible section at a time:
  General, Account, Asset Configuration History, Appearance, Database
- Separate About Application page
- SQLite database is created automatically as bubt_ops.db

Important notes:
- Account Settings stores the admin profile and password hash, but this starter version has no login screen.
- Language/default dashboard/theme/font preferences are saved; not every preference is fully applied to all widgets.
- Database restore replaces the current database. Make a backup first.
- Permanent deletion in History deletes only the selected history record, not the asset.
- Syntax checked; GUI should be tested on your own computer before final submission.
