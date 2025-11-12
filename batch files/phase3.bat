@echo on
REM Step 3 - import orders first
"C:\Apps\BukkuOps\.venv\Scripts\python.exe" "C:\Apps\BukkuOps\credit_note.py"
"C:\Apps\BukkuOps\.venv\Scripts\python.exe" "C:\Apps\BukkuOps\debit_note.py"
"C:\Apps\BukkuOps\.venv\Scripts\python.exe" "C:\Apps\BukkuOps\delivery_order.py"
"C:\Apps\BukkuOps\.venv\Scripts\python.exe" "C:\Apps\BukkuOps\purchase_order.py"
"C:\Apps\BukkuOps\.venv\Scripts\python.exe" "C:\Apps\BukkuOps\sales_order.py"
