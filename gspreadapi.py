# KOBIS 랭킹 정보 입력
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class gspreadDocApi:
    def appendData(self, json_file_name, spreadsheet_url, startIndex, data):
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive',
        ]

        credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_name, scope)
        gc = gspread.authorize(credentials)

        # 스프레드시트 문서 가져오기
        doc = gc.open_by_url(spreadsheet_url)

        # 시트 선택하기
        worksheet = doc.get_worksheet(0)

        column_data = worksheet.col_values(1)

        startindex = len(column_data) + 1

        doc.values_update(
            startIndex,
            params = {
                'valueInputOption': 'USER_ENTERED'
            },
            body={
                'values': data
            }
        )