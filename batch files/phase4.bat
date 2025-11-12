@echo on
REM Step 4 - import invoices
"C:\Apps\BukkuOps\.venv\Scripts\python.exe" "C:\Apps\BukkuOps\goods_received.py"
"C:\Apps\BukkuOps\.venv\Scripts\python.exe" "C:\Apps\BukkuOps\invoice.py"
"C:\Apps\BukkuOps\.venv\Scripts\python.exe" "C:\Apps\BukkuOps\service_bill.py"
"C:\Apps\BukkuOps\.venv\Scripts\python.exe" "C:\Apps\BukkuOps\purchase_bill.py"
"C:\Apps\BukkuOps\.venv\Scripts\python.exe" "C:\Apps\BukkuOps\purchase_payment.py"
