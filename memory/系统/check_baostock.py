import baostock as bs
bs.login()
# Check latest data for 000001
rs = bs.query_history_k_data_plus('sz.000001', 'date,close', start_date='2026-06-10', end_date='2026-06-17', frequency='d')
while rs.next():
    print(rs.get_row_data())
bs.logout()
