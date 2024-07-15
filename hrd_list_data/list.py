import requests
import xml.etree.ElementTree as ET
import json
import chardet
import os

def parse_scn_list(scn_list):
    """Extract data from scn_list elements."""
    fields = [
        'address', 'courseMan','instCd', 'ncsCd', 'realMan', 'regCourseMan', 'subTitle', 'subTitleLink', 'telNo',
        'title', 'titleLink', 'traEndDate', 'traStartDate', 'trainTarget', 'trainTargetCd',
        'trainstCstId', 'trngAreaCd', 'trprDegr', 'trprId', 'yardMan'
    ]
    data_list = []
    for scn in scn_list:
        data = {field: scn.find(field).text if scn.find(field) is not None else None for field in fields}
        data_list.append(data)
    return data_list

# API 요청 URL 및 기본 파라미터 설정
api_url = "https://www.hrd.go.kr/jsp/HRDP/HRDPO00/HRDPOA60/HRDPOA60_1.jsp"
base_params = {
    'authKey': 'w5PONwCLXEnBrSqIzeCxUfyC4odk4xPB',  # 인증키 입력
    'returnType': 'XML',
    'outType': '1',
    'pageSize': '100',
    'sort': 'ASC',
    'sortCol': 'TRNG_BGDE',
    'srchNcs1' : '19',
    'srchNcs1' : '20',
}

years = ['2024']
regions = {
    '서울': '11', '부산': '26', '대구': '27', '인천': '28', '광주': '29', '대전': '30', '울산': '31', 
    '세종': '36', '경기': '41', '강원': '51', '충북': '43', '충남': '44', '전북': '52', '전남': '46', 
    '경북': '47', '경남': '48', '제주': '50'
}

# 데이터 저장 폴더 생성
data_folder = 'hrdnet_data'
if not os.path.exists(data_folder):
    os.makedirs(data_folder)

for year in years:
    for region_name, region_code in regions.items():
        all_data = []
        page = 1
        params = base_params.copy()
        params['srchTraStDt'] = f'{year}0101'
        params['srchTraEndDt'] = f'{year}1231'
        params['srchTraArea1'] = region_code

        # 첫 페이지 요청으로 총 레코드 수 확인
        params['pageNum'] = str(page)
        response = requests.get(api_url, params=params)

        if response.status_code != 200:
            print(f"Failed to retrieve data for year {year}, region {region_name}, page {page}: {response.status_code}")
            continue

        # 인코딩 감지
        detected_encoding = chardet.detect(response.content)['encoding']
        root = ET.fromstring(response.content.decode(detected_encoding))

        # 총 레코드 수 확인
        total_records = int(root.find(".//scn_cnt").text)
        page_size = int(params['pageSize'])
        total_pages = (total_records + page_size - 1) // page_size  # 총 페이지 수 계산
        print(f"Total records for year {year}, region {region_name}: {total_records}, Total pages: {total_pages}")

        # 필요한 데이터 추출
        scn_list = root.findall(".//scn_list")
        data_list = parse_scn_list(scn_list)
        all_data.extend(data_list)
        print(f"Year {year}, region {region_name}, page {page} processed.")
        page += 1

        # 이후 페이지 처리
        while page <= total_pages:
            params['pageNum'] = str(page)
            response = requests.get(api_url, params=params)

            if response.status_code != 200:
                print(f"Failed to retrieve data for year {year}, region {region_name}, page {page}: {response.status_code}")
                break

            root = ET.fromstring(response.content.decode(detected_encoding))

            # 필요한 데이터 추출
            scn_list = root.findall(".//scn_list")
            if not scn_list:  # 더 이상 데이터가 없으면 종료
                print(f"No more data found for year {year}, region {region_name} on page {page}.")
                break

            data_list = parse_scn_list(scn_list)
            all_data.extend(data_list)
            print(f"Year {year}, region {region_name}, page {page} processed.")
            page += 1

        # 연도별, 지역별 JSON 파일로 저장
        output_data = {
            'total_records': total_records,
            'total_pages': total_pages,
            'data': all_data
        }
        
        file_path = os.path.join(data_folder, f'hrdnet_data_{year}_{region_name}.json')
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(output_data, json_file, ensure_ascii=False, indent=4)

        print(f"Data for year {year}, region {region_name} has been successfully saved to {file_path}")
