import xlrd

book = xlrd.open_workbook("data/raw/taco_4a_edicao_2011.xls")
sheet = book.sheet_by_index(0)
print(sheet.nrows)

for i in range(15):
    print(sheet.row_values(i))
