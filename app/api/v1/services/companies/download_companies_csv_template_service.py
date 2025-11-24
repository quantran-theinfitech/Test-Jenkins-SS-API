import io

import pandas as pd
from fastapi.responses import StreamingResponse


def download_companies_csv_template():
    temp_df = pd.DataFrame(
        data={
            "法人番号": ["1234567890123"],
            "企業名": ["サンプル株式会社"],
            "ウェブサイトURL(@を除く)": ["https://www.example.com"],
            "大業界": ["製造業"],
            "中業界": ["電子機器"],
            "決算月": ["3"],
            "住所": ["東京都千代田区1-1-1"],
            "事業内容": ["電子機器の製造・販売"],
            "郵便番号": ["1000001"],
            "設立年月日": ["2000-01-01"],
            "上場区分": ["未上場"],
            "代表者名": ["山田 太郎"],
            "代表電話番号": ["03-1234-5678"],
            "FAX番号": ["03-1234-5679"],
            "代表メールアドレス": ["info@example.com"],
            "採用電話番号": ["03-9876-5432"],
            "採用メールアドレス": ["recruit@example.com"],
            "問い合わせフォーム": ["https://www.example.com/contact"],
            "Facebook": ["https://facebook.com/example"],
            "Twitter": ["https://twitter.com/example"],
            "Youtube": ["https://youtube.com/example"],
            "従業員数": [100],
            "資本金 (万円)": [5000],
        }
    )
    csv_buffer = io.StringIO()
    temp_df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    return StreamingResponse(
        csv_buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=template_companies.csv"},
    )
