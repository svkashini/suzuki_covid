#ライブラリのインポート
import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import streamlit as st

import matplotlib.pyplot as plt
import plotly.express as px
import pydeck as pdk

####
#ここからデータの取得
####

#スズキ各拠点の緯度経度情報
location = pd.DataFrame([
    ['本社（静岡県浜松市南区）', 34.692419958984466, 137.68810529817713],
    ['工場（静岡県湖西市）', 34.70056416105026, 137.5044475374429],
    ['事業所（静岡県湖西市）', 34.70056416105026, 137.5044475374429],
    ['工場（静岡県牧之原市）', 34.73401794429481, 138.17318891352258],
    ['事業所（静岡県牧之原市）', 34.73401794429481, 138.17318891352258],
    ['工場（静岡県磐田市）', 34.742965335849085, 137.87492658865304],
    ['工場（静岡県浜松市北区）', 34.80683127454381, 137.73895557490206],
    ['事業所（静岡県浜松市北区）', 34.80683127454381, 137.73895557490206],
    ['工場（静岡県掛川市）', 34.68886908396566, 137.98902904421084],
    ['事業所（東京都練馬区）', 35.6630485838581, 139.75786500182355]
], columns=['拠点', 'lat', 'long'])

#グラフ表示の設定
color_class = {
    '本社（静岡県浜松市南区）':'red',
    '工場（静岡県湖西市）':'blue',
    '事業所（静岡県湖西市）':'lightgreen',
    '事業所（静岡県牧之原市）':'limegreen',
    '工場（静岡県牧之原市）':'orange',
    '工場（静岡県磐田市）':'yellow',
    '工場（静岡県浜松市北区）':'green',
    '工場（静岡県掛川市）':'gray',
    '事業所（東京都練馬区）':'pink',
    '事業所（静岡県浜松市北区）': 'lightblue'
}


#スズキ株式会社のコロナ感染者公表ページ
year_hp = ['20', '21', '22']
df2 = pd.DataFrame() #空のデータフレーム
url1 = 'https://www.suzuki.co.jp/release/d/20'
url2 = '/covid19/'

for y in year_hp:
    url = url1 + y + url2
    res = requests.get(url)

    #データの抜き出し
    html_doc = res.content
    soup = BeautifulSoup(html_doc, 'html.parser')

    #感染者情報の表を読み込み
    div_box = soup.find_all('div', class_='scroll')

    #Beautiful soupで取得したデータをpandas DataFrameに格納する

    df = pd.DataFrame() #空のデータフレームを準備

    #データフレームのカラム名を辞書で定義
    columns = {0:'拠点',
            1:'陽性確定',
            2:'最終出社',
            3:'職場消毒',
            4:'工場稼働への影響',
            5:'特記事項'}

    #各要素をデータフレームに格納
    for i in div_box:
        temp = []
        for x in i.find_all(['th', 'td']):
            if x.name == 'td':
                temp.append(x.get_text())
        df_temp = pd.DataFrame(temp).T
        
        df = pd.concat([df, df_temp], axis=0)

    df2 = pd.concat([df2, df], axis=0)

#不要なインデックスを削除し、カラム名を変更する
suzuki_covid = df2.reset_index().drop(columns='index', axis=1).rename(columns=columns)

#2020年の公表データには月日しか記載がないため、2021年データと書式を揃えるために「2020年」を追加するスクリプト
temp = suzuki_covid[~suzuki_covid['陽性確定'].str.contains('年')]
temp['陽性確定'] = temp['陽性確定'].apply(lambda x: '2020年' + x )
temp1 = suzuki_covid[suzuki_covid['陽性確定'].str.contains('年')]
suzuki_covid2 = pd.concat([temp1, temp], axis=0)


#相良クラスターの別カウント
#9/14確認数
cluster = 28

for i in range(cluster):
    df_cluster = pd.DataFrame.from_dict({
        '拠点':['工場（静岡県牧之原市）'],
        '陽性確定':['2021年9月14日'],
        '工場稼働への影響': ['あり'],
        '特記事項':['クラスター']
        }
    )

    suzuki_covid2 = pd.concat([suzuki_covid2, df_cluster], axis=0)


#9/15確認数
cluster = 30

for i in range(cluster):
    df_cluster = pd.DataFrame.from_dict({
        '拠点':['工場（静岡県牧之原市）'],
        '陽性確定':['2021年9月15日'],
        '工場稼働への影響': ['あり'],
        '特記事項':['クラスター']
        }
    )

    suzuki_covid2 = pd.concat([suzuki_covid2, df_cluster], axis=0)
    
#9/16確認数
cluster = 21

for i in range(cluster):
    df_cluster = pd.DataFrame.from_dict({
        '拠点':['工場（静岡県牧之原市）'],
        '陽性確定':['2021年9月16日'],
        '工場稼働への影響': ['あり'],
        '特記事項':['クラスター']
        }
    )

    suzuki_covid2 = pd.concat([suzuki_covid2, df_cluster], axis=0)


#陽性確定日をDatetime型で格納したカラムを新規作成
suzuki_covid2['陽性確定日'] = pd.to_datetime(suzuki_covid2['陽性確定'],  format='%Y年%m月%d日')
suzuki_covid3 = suzuki_covid2[['拠点','陽性確定日']]

#拠点名称のリストを取得
places = suzuki_covid3['拠点'].unique()

#拠点ごとの累計感染者数を集計
cumsum_data = pd.DataFrame()
for place in places:
    temp = suzuki_covid3[suzuki_covid3['拠点'] == place].groupby('陽性確定日').count().sort_values('陽性確定日').cumsum().rename(columns={'拠点': place})
    cumsum_data = pd.concat([cumsum_data, temp], axis=1)



#####
#ここからstreamlit表示内容
#####
st.header('スズキ株式会社　コロナ感染者データ')
st.text('出典: スズキ株式会社HP内「当社における新型コロナウイルス感染者の発生について」')
st.text('参照URL: https://www.suzuki.co.jp/release/d/2020/covid19/')
st.text('注意: 掲載データは作成者が独自に集計したものでありスズキ株式会社の公式発表ではありません')

add_checkbox = st.sidebar.multiselect(
    '表示対象とする事業所を選択',
    places.tolist(),
    places.tolist()
)

output_data = suzuki_covid2[suzuki_covid2['拠点'].isin(add_checkbox)]

start_date = st.sidebar.date_input(
    '集計期間の起点を選択',
    datetime.datetime.today() - datetime.timedelta(days=60)
)

end_date = st.sidebar.date_input(
    '集計期間の終点を選択',
    datetime.date.today()
)

#日当たりの感染者数推移
fig = px.bar(
    title = '日当たりの感染者数推移',
    data_frame = output_data.groupby(['陽性確定日','拠点'], as_index=False).count()[['陽性確定日','拠点','陽性確定']].sort_values('陽性確定日'),
    x = '陽性確定日',
    y = '陽性確定',
    color = '拠点',
    labels = {'陽性確定':'陽性者数(人)'},
    range_x = [start_date, end_date],
    color_discrete_map = color_class
)
st.plotly_chart(fig)

output_data_range = output_data[(output_data['陽性確定日']>= datetime.datetime.combine(start_date, datetime.time())) & (output_data['陽性確定日']<=datetime.datetime.combine(end_date, datetime.time()))]
cumsum_data = output_data_range.groupby(['拠点'], as_index=False).count()[['拠点','陽性確定']].sort_values('陽性確定', ascending=False)

#集計期間中の累計感染者数
fig = px.bar(
    title = '集計期間中の累計感染者数',
    data_frame = cumsum_data,
    x = '陽性確定',
    y = '拠点',
    text = '陽性確定',
    color = '拠点',
    labels = {'陽性確定':'累計感染者数（人）'},
    color_discrete_map = color_class
)
st.plotly_chart(fig)

display_data = output_data_range.sort_values('陽性確定日').reset_index(drop=True)

st.subheader('感染者データ')
st.dataframe(display_data[['拠点', '陽性確定', '最終出社','職場消毒']])
st.download_button(
    label='データをcsvでダウンロード',
    data=display_data[['拠点', '陽性確定', '最終出社','職場消毒']].to_csv(),
    file_name='suzuki_covid.csv',
    mime='text/csv'
)