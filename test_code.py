from pykrx import stock
# 현재 사용 가능한 지수 목록 출력
indices = stock.get_index_ticker_list()
print(indices)