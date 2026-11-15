# หัวข้อและ hook: เบื้องหลังแบนเนอร์ Fastwork

Prompt (EN): "Help me come up with titles for a blog post about the banner made most recently in this
session. I want to tell how it was made, with the steps and the method, and close with: if you
want ..., if you're interested <a hook to continue>, hire me on Fastwork."

## หัวข้อ

1. ทำแบนเนอร์ด้วย AI Agent ให้ script ตรวจก่อนโพสต์
2. 3 จุดที่ผมพลาดตอนทำแบนเนอร์ และแก้ยังไง
3. จาก README บน GitHub มาเป็นแบนเนอร์ 1920 x 1080 บน Fastwork
4. แบนเนอร์ใบเดียว ไฟล์ spec ไฟล์เดียว ได้สามสไตล์
5. Interface ถึง Platform: เล่าการทำแบนเนอร์ฟรีแลนซ์แบบที่ dev ทำ

ใช้ข้อ 1 เป็นหัวข้อหลัก ส่วนปกใช้ข้อความสั้นกว่า (ดู `post.banner.json`)

## Hook (บรรทัดเปิดโพสต์ แยกตามแบบ)

1. ตัวเลขนำ
   แบนเนอร์ 1920 x 1080 ใบนี้ไม่ได้วาดในโปรแกรมกราฟิก
   ทั้งใบมาจากไฟล์ JSON ไฟล์เดียว
2. สวนความเชื่อ
   ดีไซน์ผ่านหรือยัง อย่าถามคนทำ
   ให้ script วัดแทน ตาคนทำหลอกตัวเองเก่ง
3. ก่อนกับหลัง
   รอบแรกชื่อผมล้นเข้าขอบ 96px
   รอบสองผ่าน bench ทุกข้อ
4. อ้างเครื่องมือ
   Claude Code ช่วยผมทำแบนเนอร์
   แต่คนตัดสินว่าผ่านคือ bench.py
5. ยอมรับพลาด
   แบนเนอร์ผมเกือบพูดเกินจริง
   มีคำว่า Remote ทั้งที่ผมไม่เคยบอกที่ไหน
6. ต่อจากนี้
   แบนเนอร์ใบต่อไปของผม
   เริ่มจากไฟล์ spec ที่มีอยู่แล้ว เปลี่ยนแค่ข้อความ
