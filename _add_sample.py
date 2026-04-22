"""Add the 升排长__照相馆 sample to benchmark_data_complete.json"""
import json

with open("benchmark_data_complete.json", "r", encoding="utf-8-sig") as f:
    data = json.load(f)

new_sample = {
    "interview_path": "d:/desktop/Tencent Capstone Project/访谈数据库/升排长__照相馆访谈.txt",
    "memoir_path": "d:/desktop/Tencent Capstone Project/成文数据库/升排长__照相馆.txt",
    "image_path": "d:/desktop/Tencent Capstone Project/照片数据库/升排长__照相馆.png",
    "image_description": "这是一张在广州照相馆拍摄的彩色军装肖像照。画面中一位20岁出头的年轻军人坐在木椅上，身穿绿色65式解放军军装，头戴缀有红色五角星的绿色军帽，领口佩有红色领章。他胸前佩戴着三枚军功章/荣誉奖章，面带自信的微笑。他的右手搭在一张小木方桌上，桌上放着一本红色封面的书籍和一只青花盖碗茶杯。背景是典型的照相馆手绘布景——一座古塔矗立在绿树掩映的山丘之上。照片底部印有'广州照相馆'五个白色大字，照片边缘微微泛黄，具有上世纪70年代初的年代感。",
    "mme_tasks": [
        {"q": "照片中的军人头上是否戴着一顶带有红色五角星的绿色军帽？", "a": "yes"},
        {"q": "军人胸前是否佩戴着三枚以上的奖章或勋章？", "a": "no"},
        {"q": "军人的领口是否可以看到红色的领章？", "a": "yes"},
        {"q": "桌上放着的茶杯是否是一只西式咖啡杯？", "a": "no"},
        {"q": "照片的背景中是否出现了一座塔的画面？", "a": "yes"},
        {"q": "照片底部是否印有'广州照相馆'的文字？", "a": "yes"},
        {"q": "军人是否站立在室外的操场上？", "a": "no"},
        {"q": "桌面上是否放着一本书籍？", "a": "yes"}
    ],
    "mmbench_tasks": [
        {
            "q": "根据军人佩戴的65式军装、红色领章和五角星军帽的样式，以及照相馆的拍摄风格，这张照片最可能拍摄于哪个年代？",
            "options": {
                "A": "20世纪50年代，抗美援朝刚结束的恢复时期",
                "B": "20世纪70年代初，解放军仍穿着65式军装的时期",
                "C": "20世纪90年代，军装已改为87式的时期",
                "D": "21世纪10年代，现代化数码迷彩已普及的时期"
            },
            "a": "B"
        },
        {
            "q": "结合军人胸前佩戴的多枚奖章、自信的微笑以及在照相馆正式拍照的行为，以下哪项推断最为合理？",
            "options": {
                "A": "这名军人是一位刚入伍的新兵，在照相馆拍摄入伍纪念照。",
                "B": "这名军人因表现优异获得多项荣誉，可能刚获得提拔或表彰，特意到照相馆拍照留念。",
                "C": "这名军人即将退伍，在照相馆拍摄的是退役纪念照。",
                "D": "这名军人是一位文艺兵，正在照相馆为部队宣传册拍摄形象照。"
            },
            "a": "B"
        }
    ],
    "hooks": [
        "65式绿军装",
        "红五星军帽",
        "军功章",
        "广州照相馆",
        "盖碗茶杯"
    ]
}

data.append(new_sample)

with open("benchmark_data_complete.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"Done. Total samples: {len(data)}")
