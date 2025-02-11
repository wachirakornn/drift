from fastapi import FastAPI, UploadFile, File, Form
import pandas as pd
from pyproj import Proj
import io
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_utm_zone(lon):
    return int((lon + 180) / 6) + 1  # ✅ คำนวณ UTM Zone อัตโนมัติ

def latlong_to_utm(lat, lon):
    zone = get_utm_zone(lon)  # ✅ ใช้ค่าที่คำนวณได้
    proj_utm = Proj(proj="utm", zone=zone, ellps="WGS84", south=False)
    easting, northing = proj_utm(lon, lat)
    return zone, easting, northing

@app.post("/convert")
async def convert_csv(file: UploadFile = File(...), skip_first_row: bool = Form(False)):
    skip_rows = 1 if skip_first_row else 0
    df = pd.read_csv(file.file, encoding="utf-8", delimiter=",", skiprows=skip_rows)

    print("📌 DataFrame ก่อนแปลงค่า:\n", df.head())

    if "lat" in df.columns and "lng" in df.columns:
        df["utm_zone"], df["Easting"], df["Northing"] = zip(*df.apply(lambda row: latlong_to_utm(row["lat"], row["lng"]), axis=1))

    print("📌 DataFrame หลังแปลงค่า:\n", df.head())

    # ใช้ StringIO + utf-8-sig เพื่อรองรับภาษาไทยใน Excel
    output = io.StringIO()
    df.to_csv(output, index=False, encoding="utf-8-sig")
    output.seek(0)

    # ส่งออกเป็นไฟล์ CSV จริง ไม่ใช่แค่ข้อความ
    return {
        "filename": "converted.csv",
        "content": output.getvalue(),
    }
