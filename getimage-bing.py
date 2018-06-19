# -*- coding: utf-8 -*-
import os
import http.client
import urllib.parse
import requests
import json

# -------------------------------------------------------------------------------
# settings (変更要)
# -------------------------------------------------------------------------------
subscription_key = "API_KEY"  # Bing Images Search v7 Key (32 桁の文字列)
search_terms = "SEARCH_WORDS"  # 検索ワード (複数ワードの場合は空白で区切る)
img_total_cnt = 300  # 取得枚数 (整数)
img_dir = "C:/Users/PATH"  # 画像検索結果保管用ディレクトリ (PATH)

# -------------------------------------------------------------------------------
# settings (変更不要)
# -------------------------------------------------------------------------------
conn_host = "api.cognitive.microsoft.com"
conn_path = "/bing/v7.0/images/search"
img_onetime_maxcnt = 150  # 1 接続あたりの最大取得可能枚数 (API の制限)
if img_total_cnt > img_onetime_maxcnt:    # 1 接続あたりの取得枚数を決定
    img_cnt = img_onetime_maxcnt
else:
    img_cnt = img_total_cnt

# -------------------------------------------------------------------------------
# functions
# -------------------------------------------------------------------------------
# 画像検索結果保管用ディレクトリ作成
#  @param none
#  @return none
def create_imgdir():
    if not os.path.isdir(img_dir):
        os.mkdir(img_dir)


# 画像検索結果(URL)を取得する
#  @param integer 画像検索時のオフセット値 (0 の場合は一番初めの検索結果を返す)
#  @return array 画像検索結果URL一覧
def search_img(offset_cnt):
    # Bing 画像検索実行
    conn = http.client.HTTPSConnection(conn_host)
    search_url = conn_path + "?" + \
        "q=" + urllib.parse.quote(search_terms) + "&" + \
        "count=" + str(img_cnt) + "&" + \
        "offset=" + str(offset_cnt) + "&" + \
        "imageType=photo" + "&" + \
        "mkt=ja-JP"
    request_headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    conn.request("GET", search_url, headers=request_headers)

    response = conn.getresponse()
    response_data = response.read()
    response_code = response.status
    conn.close()

    # 応答データを JSON 形式に変換
    response_data_json = json.loads(response_data.decode("utf8"))

    # 画像検索結果から URL を取得
    #   resp_data_json["value"]: A list of images that are relevant to the query.
    #     https://docs.microsoft.com/en-us/rest/api/cognitiveservices/bing-images-api-v7-reference#images
    #   resp_img["contentUrl"]: The URL to the image on the source website.
    #     https://docs.microsoft.com/en-us/rest/api/cognitiveservices/bing-images-api-v7-reference#image
    urls = []
    if response_code == 200:
        for img_list in response_data_json["value"]:
            url = urllib.parse.unquote(img_list["contentUrl"])
            urls.append(url)

    return urls


# 画像検索結果(URL)に接続し、画像を取得する
#  @param string 画像のURL
#  @return object Responseオブジェクト
#                 http://docs.python-requests.org/en/master/api/#requests.Response
def get_img(url):
    response = requests.get(url, allow_redirects=True, timeout=10)

    return response


# -------------------------------------------------------------------------------
# __main__
# -------------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        # 画像検索結果保管用ディレクトリ作成
        create_imgdir()

        # 画像検索＆取得処理
        prefix = 1  # 保存画像ファイル名 prefix (incremental number: +1)
        offset = 0  # 画像取得時のオフセット
        while offset < img_total_cnt:
            # 画像検索
            response_urls = search_img(offset)

            # 画像取得＆保存
            for img_url in response_urls:
                # 画像取得
                response_img = get_img(img_url)
                if response_img.status_code != 200:
                    continue
                if "image" not in response_img.headers["content-type"]:
                    continue

                # 画像保存
                suffix = os.path.splitext(img_url)[-1]
                if suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp"):
                    file_path = os.path.join(img_dir, str(prefix) + suffix.lower())
                else:
                    continue

                with open(file_path, "wb") as fout:
                    fout.write(response_img.content)
                    print(img_url + " > " + str(prefix) + suffix.lower())

                    prefix += 1

            offset += img_cnt

    except Exception as e:
        print(e.args)

