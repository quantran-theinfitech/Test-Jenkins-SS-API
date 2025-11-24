import io

import pandas as pd
from fastapi.responses import StreamingResponse


def download_persons_csv_template():
    temp_df = pd.DataFrame(
        data={
            "氏名(必須)": ["山田 太郎"],
            "メール": ["(sample@example.com"],
            "リンクインのURL": ["https://linkedin.com/in/sample"],
            "法人番号": ["1234567890123"],
            "企業名": ["サンプル株式会社"],
            "役職グループ": ["エンジニア"],
            "役職": ["ソフトウェアエンジニア"],
            "自己紹介": ["ITエンジニアとして働いています。"],
            "住所": ["東京都新宿区1-1-1"],
            "情報": ["データ分析に関心があります。"],
            "ツイッターのURL": ["https://twitter.com/sample"],
            "ギットハブのURL": ["https://github.com/sample"],
            "フェイスブックのURL": ["https://facebook.com/sample"],
            "ワンテドリーのURL": ["https://www.wantedly.com/users/sample"],
        }
    )
    csv_buffer = io.StringIO()
    temp_df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    return StreamingResponse(
        csv_buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=template_persons.csv"},
    )
