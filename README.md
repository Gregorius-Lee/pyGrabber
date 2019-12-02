# pyGrabber
## pyGrabber 프로젝트 목적
pyGrabber는 `웹 크롤링`으로 문화와 관련된 정보를 수집하며  
수집되는 정보는 아래와 같음

대상사이트 | 수집주소 | 수집정보
:---:|:---|:---
*네이버쇼핑인사이트* | https://datalab.naver.com/shoppingInsight/sCategory.naver | 15가지 카테고리에 대한 성별/연령별 Top 20 순위
*KOPIS* | http://www.kopis.or.kr/por/boxoffice/boxoffice.do?menuId=MNU_00024&searchWord=&searchType=total | 연극, 뮤지컬 등 공연 Top 50 순위
*KOBIS* | http://www.kobis.or.kr/kobis/business/stat/boxs/findWeeklyBoxOfficeList.do | 영화 Top 20 순위

> 네이버 쇼핑인사이트의 15가지 문화 카테고리
>> 뮤지컬, 콘서트, 연극, 전시/행사, 클래식, 오페라, 발레/무용, 국악/전통예술, 스포츠,  
>> 국내여행, 국내숙박, 체험, 강좌, 구기스포츠, 아웃도어스포츠

네이버 쇼핑인사이트의 검색 API를 활용하여 성별/연령별 검색량 측정

