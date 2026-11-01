---
title: เอกสาร API Spec
subtitle: Acme Order Service v1.1
author: ทีมพัฒนา Acme
date: 13/10/2569
---

**ประวัติการแก้ไข**

| Version | วันที่ | ผู้เขียน | รายละเอียด |
|---|---|---|---|
| 1.0.0 | 01/09/2569 | ทีมพัฒนา | สร้างเอกสาร |
| [~] 1.1.0 | 13/10/2569 | ทีมพัฒนา | เพิ่มฟิลด์ `note` และเลิกใช้ `legacy_code` |

| สถานะ | ความหมาย |
|---|---|
| [+] เพิ่มใหม่ | added in this version |
| [~] แก้ไข | changed in this version |
| [-] นำออก | removed in this version |

# API สำหรับดึงรายการคำสั่งซื้อ

| | |
|---|------|
| System Name | Get Orders - Acme Order Service |
| Service Name | API สำหรับดึงรายการคำสั่งซื้อ |
| Service Type | RESTful |
| Service Protocol | HTTP |
| Service URL Non-Production | `https://api.example.com/api/orders/{order_no}` |
| Service URL Production | - |
| HTTP Method | Get |
| Request Content Type | application/json |
| Request Char Encoding | UTF-8 |
| Response Content Type | application/json |
| Response Char Encoding | UTF-8 |

## รูปแบบข้อมูล Request

| ลำดับ | ชื่อข้อมูล | จำเป็น | ชนิดข้อมูล | คำอธิบาย |
|---|----|---|----|------|
| 1 | order_no | Y | varchar | เลขที่คำสั่งซื้อ |

ตัวอย่างข้อมูล Request

```json
{ "order_no": "SO-0001" }
```

## รูปแบบข้อมูล Response

| ลำดับ | ชื่อข้อมูล | ชนิดข้อมูล | คำอธิบาย |
|---|----|----|------|
| 1 | status | string | Success / Fail |
| 2 | data | Order[] | รายการคำสั่งซื้อ |
| 3 | Order | | |
| 3.1 | order_no | varchar | เลขที่คำสั่งซื้อ |
| 3.2 | amount | decimal(10,2) | ยอดรวม |
| [+] 3.3 | note | string | หมายเหตุ |
| [-] 3.4 | legacy_code | varchar | รหัสเดิม (เลิกใช้) |

ตัวอย่างข้อมูล Response

```json
{
  "status": "Success",
  "data": [{ "order_no": "SO-0001", "amount": 1250.00, "note": null }]
}
```

# ผลการทดสอบ

| รายการ | ผล | หลักฐาน |
|---|---|---|
| เรียก API บน Non-Production | ผ่าน | HTTP 200 |
| เรียก API บน Production | ยังไม่มีหลักฐาน | - |
